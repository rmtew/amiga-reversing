#include "m68k_ir.h"

#include "generated/amiga_os_runtime.h"
#include "generated/atari_st_os_runtime.h"
#include "m68k_assembler.h"
#include "platform_common.h"

#include <string.h>

#define M68K_IR_SECTION_ARENA_SIZE 4096U
#define M68K_IR_SOURCE_FILE_ARENA_SIZE 16384U
#define M68K_IR_SECTION_ANALYSIS_ARENA_SIZE 16384U
#define M68K_IR_SOURCE_ANALYSIS_ARENA_SIZE 16384U

const M68kInstructionIR g_m68k_ir_instruction_none = {
  M68K_ASM_FORM_NONE,
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

static void m68k_ir_section_init_shared(M68kSectionIR *section, Arena *arena) {
  memset(section, 0, sizeof(*section));
  section->arena = arena;
  section->owns_arena = 0U;
}

static void m68k_ir_section_analysis_init_shared(M68kSectionAnalysisIR *section_analysis, Arena *arena) {
  memset(section_analysis, 0, sizeof(*section_analysis));
  section_analysis->arena = arena;
  section_analysis->owns_arena = 0U;
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

int m68k_ir_section_create(M68kSectionIR *section) {
  if (section == NULL) return -1;
  memset(section, 0, sizeof(*section));
  section->arena = arena_create(M68K_IR_SECTION_ARENA_SIZE);
  if (section->arena == NULL) return -1;
  section->owns_arena = 1U;
  return 0;
}

int m68k_ir_source_file_create(M68kSourceFileIR *source_file) {
  if (source_file == NULL) return -1;
  memset(source_file, 0, sizeof(*source_file));
  source_file->arena = arena_create(M68K_IR_SOURCE_FILE_ARENA_SIZE);
  return source_file->arena != NULL ? 0 : -1;
}

int m68k_ir_section_analysis_create(M68kSectionAnalysisIR *section_analysis) {
  if (section_analysis == NULL) return -1;
  memset(section_analysis, 0, sizeof(*section_analysis));
  section_analysis->arena = arena_create(M68K_IR_SECTION_ANALYSIS_ARENA_SIZE);
  if (section_analysis->arena == NULL) return -1;
  section_analysis->owns_arena = 1U;
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

void m68k_ir_instruction_init(M68kInstructionIR *instruction) {
  memset(instruction, 0, sizeof(*instruction));
  instruction->asm_form_index = M68K_ASM_FORM_NONE;
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
  if (section->owns_arena != 0U) arena_destroy(section->arena);
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
  if (section_analysis->owns_arena != 0U) arena_destroy(section_analysis->arena);
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
    existing->target = site->target;
    existing->target_count = site->target_count;
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
    int16_t field_offset, const char *root_struct_name, const char *owner_struct_name, const char *field_name,
    const char *field_expr, uint8_t inherited, uint8_t nested) {
  size_t index;
  char *copy_root_struct_name, *copy_owner_struct_name, *copy_field_name, *copy_field_expr;
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
        existing->field_offset == field_offset && existing->inherited == (uint8_t)(inherited != 0U) &&
        existing->nested == (uint8_t)(nested != 0U) &&
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
  section_analysis->recovered_platform_typed_accesses[section_analysis->recovered_platform_typed_access_count].offset =
    offset;
  section_analysis->recovered_platform_typed_accesses[section_analysis->recovered_platform_typed_access_count].operand_index =
    operand_index;
  section_analysis->recovered_platform_typed_accesses[section_analysis->recovered_platform_typed_access_count].base_reg =
    base_reg;
  section_analysis->recovered_platform_typed_accesses[section_analysis->recovered_platform_typed_access_count].inherited =
    (uint8_t)(inherited != 0U);
  section_analysis->recovered_platform_typed_accesses[section_analysis->recovered_platform_typed_access_count].nested =
    (uint8_t)(nested != 0U);
  section_analysis->recovered_platform_typed_accesses[section_analysis->recovered_platform_typed_access_count].displacement =
    displacement;
  section_analysis->recovered_platform_typed_accesses[section_analysis->recovered_platform_typed_access_count].field_offset =
    field_offset;
  section_analysis->recovered_platform_typed_accesses[section_analysis->recovered_platform_typed_access_count].root_struct_name =
    copy_root_struct_name;
  section_analysis->recovered_platform_typed_accesses[section_analysis->recovered_platform_typed_access_count].owner_struct_name =
    copy_owner_struct_name;
  section_analysis->recovered_platform_typed_accesses[section_analysis->recovered_platform_typed_access_count].field_name =
    copy_field_name;
  section_analysis->recovered_platform_typed_accesses[section_analysis->recovered_platform_typed_access_count].field_expr =
    copy_field_expr;
  section_analysis->recovered_platform_typed_accesses[section_analysis->recovered_platform_typed_access_count].root_struct_ref =
    root_struct_ref;
  section_analysis->recovered_platform_typed_accesses[section_analysis->recovered_platform_typed_access_count].owner_struct_ref =
    owner_struct_ref;
  section_analysis->recovered_platform_typed_accesses[section_analysis->recovered_platform_typed_access_count].field_ref =
    field_ref;
  section_analysis->recovered_platform_typed_access_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_platform_unresolved_typed_access(
    M68kSectionAnalysisIR *section_analysis, uint8_t platform_kind, uint32_t offset, uint8_t operand_index,
    uint8_t base_reg, int16_t displacement, uint16_t struct_size, const char *root_struct_name) {
  size_t index;
  char *copy_root_struct_name;
  M68kPlatformNameRef root_struct_ref = {0};
  if (section_analysis == NULL || section_analysis->arena == NULL ||
      root_struct_name == NULL || root_struct_name[0] == '\0' ||
      operand_index >= 4U || base_reg >= 8U) {
    return -1;
  }
  root_struct_ref.platform_kind = platform_kind;
  root_struct_ref.domain_kind = M68K_PLATFORM_NAME_STRUCT;
  root_struct_ref.id = m68k_platform_name_id_from_text(platform_kind, M68K_PLATFORM_NAME_STRUCT, root_struct_name);
  for (index = 0; index < section_analysis->recovered_platform_unresolved_typed_access_count; ++index) {
    M68kRecoveredPlatformUnresolvedTypedAccessIR *existing =
      &section_analysis->recovered_platform_unresolved_typed_accesses[index];
    if (existing->offset == offset && existing->operand_index == operand_index &&
        existing->base_reg == base_reg && existing->displacement == displacement &&
        existing->struct_size == struct_size &&
        m68k_platform_name_matches(&existing->root_struct_ref, existing->root_struct_name, &root_struct_ref,
          root_struct_name)) {
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
    section_analysis->recovered_platform_unresolved_typed_access_count].root_struct_name = copy_root_struct_name;
  section_analysis->recovered_platform_unresolved_typed_accesses[
    section_analysis->recovered_platform_unresolved_typed_access_count].root_struct_ref = root_struct_ref;
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
    const char *value_domain_name, uint8_t has_constant_value, int32_t constant_value) {
  size_t index;
  char *copy_context_name, *copy_symbol_name, *copy_type_name, *copy_semantic_kind, *copy_value_domain_name;
  M68kPlatformNameRef context_ref = {0}, symbol_ref = {0}, type_ref = {0};
  M68kPlatformNameRef semantic_kind_ref = {0}, value_domain_ref = {0};
  if (section_analysis == NULL || stack_offset == 0U || reg_kind == 0U || reg_index >= 8U) return -1;
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
        (!has_constant_value || existing->typed.constant_value == constant_value)) {
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
    available_since_version = (uint16_t)amiga_os_parse_compatibility_version(available_since);
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
  arena_destroy(source_analysis->arena);
  memset(source_analysis, 0, sizeof(*source_analysis));
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
          access->field_offset, root_struct_name, owner_struct_name, field_name, access->field_expr,
          access->inherited, access->nested) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_platform_unresolved_typed_access_count; ++index) {
    const M68kRecoveredPlatformUnresolvedTypedAccessIR *access =
      &section_analysis->recovered_platform_unresolved_typed_accesses[index];
    const char *root_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref,
      access->root_struct_name);
    uint8_t platform_kind = m68k_platform_kind_from_ref_or_text(&access->root_struct_ref,
      M68K_PLATFORM_NAME_STRUCT, root_struct_name);
    if (m68k_ir_section_analysis_append_recovered_platform_unresolved_typed_access(&copy, platform_kind,
          access->offset, access->operand_index, access->base_reg, access->displacement,
          access->struct_size, root_struct_name) != 0) {
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
          value_domain_name, arg->typed.has_constant_value, arg->typed.constant_value) != 0) {
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
