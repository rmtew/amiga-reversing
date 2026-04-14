#include "m68k_ir.h"

#include "platform_common.h"

#include <string.h>

#define M68K_IR_SECTION_ARENA_SIZE 4096U
#define M68K_IR_SOURCE_FILE_ARENA_SIZE 16384U
#define M68K_IR_SECTION_ANALYSIS_ARENA_SIZE 16384U
#define M68K_IR_SOURCE_ANALYSIS_ARENA_SIZE 16384U

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

void m68k_ir_instruction_init(M68kInstructionIR *instruction) {
  if (instruction == NULL) return;

  memset(instruction, 0, sizeof(*instruction));
  instruction->form_index = M68K_IR_INVALID_FORM_INDEX;
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
  copy.size = section->size;
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

int m68k_ir_section_analysis_append_recovered_platform_base_slot(M68kSectionAnalysisIR *section_analysis,
    int16_t displacement, const char *base_name) {
  size_t index;
  char *copy_name;
  if (section_analysis == NULL || base_name == NULL) return -1;
  if (section_analysis->arena == NULL) return -1;
  for (index = 0; index < section_analysis->recovered_platform_base_slot_count; ++index) {
    M68kRecoveredPlatformBaseSlotIR *existing = &section_analysis->recovered_platform_base_slots[index];
    if (existing->displacement == displacement) {
      if (strcmp(existing->base_name, base_name) == 0) return 0;
      return -1;
    }
  }
  section_analysis->recovered_platform_base_slots = (M68kRecoveredPlatformBaseSlotIR *)arena_grow_array(
    section_analysis->arena, section_analysis->recovered_platform_base_slots,
    section_analysis->recovered_platform_base_slot_count, &section_analysis->recovered_platform_base_slot_capacity,
    8U, sizeof(*section_analysis->recovered_platform_base_slots));
  if (section_analysis->recovered_platform_base_slots == NULL) return -1;
  copy_name = arena_strdup(section_analysis->arena, base_name);
  if (copy_name == NULL) return -1;
  section_analysis->recovered_platform_base_slots[section_analysis->recovered_platform_base_slot_count].displacement =
    displacement;
  section_analysis->recovered_platform_base_slots[section_analysis->recovered_platform_base_slot_count].base_name =
    copy_name;
  section_analysis->recovered_platform_base_slot_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_platform_effect(M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint8_t kind, uint8_t reg_kind, uint8_t reg_index, int16_t displacement, int16_t field_disp,
    const char *base_name, const char *symbol_name, const char *type_name) {
  size_t index;
  char *copy_name;
  char *copy_symbol_name;
  char *copy_type_name;
  if (section_analysis == NULL || kind == M68K_PLATFORM_EFFECT_NONE) return -1;
  if (section_analysis->arena == NULL) return -1;
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    M68kRecoveredPlatformEffectIR *existing = &section_analysis->recovered_platform_effects[index];
    if (existing->offset == offset && existing->kind == kind && existing->reg_kind == reg_kind &&
        existing->reg_index == reg_index && existing->displacement == displacement && existing->field_disp == field_disp) {
      const char *existing_base_name = NULL;
      const char *existing_symbol_name = NULL;
      const char *existing_type_name = NULL;
      if (existing->kind == M68K_PLATFORM_EFFECT_SET_BASE_REG || existing->kind == M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT) {
        existing_base_name = existing->payload.named_base.base_name;
      } else if (existing->kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG) {
        existing_symbol_name = existing->payload.code_ptr.field_symbol_name;
        existing_type_name = existing->payload.code_ptr.owner_type_name;
      } else if (existing->kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG || existing->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT) {
        existing_type_name = existing->payload.typed.type_name;
      }
      if (((existing_base_name == NULL && base_name == NULL) ||
              (existing_base_name != NULL && base_name != NULL && strcmp(existing_base_name, base_name) == 0)) &&
          ((existing_symbol_name == NULL && symbol_name == NULL) ||
              (existing_symbol_name != NULL && symbol_name != NULL && strcmp(existing_symbol_name, symbol_name) == 0)) &&
          ((existing_type_name == NULL && type_name == NULL) ||
              (existing_type_name != NULL && type_name != NULL && strcmp(existing_type_name, type_name) == 0))) return 0;
      return -1;
    }
  }
  section_analysis->recovered_platform_effects = (M68kRecoveredPlatformEffectIR *)arena_grow_array(
    section_analysis->arena, section_analysis->recovered_platform_effects,
    section_analysis->recovered_platform_effect_count, &section_analysis->recovered_platform_effect_capacity,
    8U, sizeof(*section_analysis->recovered_platform_effects));
  if (section_analysis->recovered_platform_effects == NULL) return -1;
  copy_name = base_name != NULL ? arena_strdup(section_analysis->arena, base_name) : NULL;
  if (base_name != NULL && copy_name == NULL) return -1;
  copy_symbol_name = symbol_name != NULL ? arena_strdup(section_analysis->arena, symbol_name) : NULL;
  if (symbol_name != NULL && copy_symbol_name == NULL) return -1;
  copy_type_name = type_name != NULL ? arena_strdup(section_analysis->arena, type_name) : NULL;
  if (type_name != NULL && copy_type_name == NULL) return -1;
  section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].offset = offset;
  section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].kind = kind;
  section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].reg_kind = reg_kind;
  section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].reg_index = reg_index;
  section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].displacement =
    displacement;
  section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].field_disp =
    field_disp;
  memset(&section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload, 0,
    sizeof(section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload));
  if (kind == M68K_PLATFORM_EFFECT_SET_BASE_REG || kind == M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT) {
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.named_base.base_name =
      copy_name;
  } else if (kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG) {
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.code_ptr.field_symbol_name =
      copy_symbol_name;
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.code_ptr.owner_type_name =
      copy_type_name;
  } else if (kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG || kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT) {
    section_analysis->recovered_platform_effects[section_analysis->recovered_platform_effect_count].payload.typed.type_name =
      copy_type_name;
  }
  section_analysis->recovered_platform_effect_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_local_call_summary(M68kSectionAnalysisIR *section_analysis,
    uint32_t target_offset, uint8_t effect_kind, uint8_t reg_kind, uint8_t reg_index,
    uint8_t success_reg_kind, uint8_t success_reg_index, uint8_t success_value_known, int32_t success_reg_value,
    const char *base_name, const char *type_name) {
  size_t index;
  char *copy_base_name;
  char *copy_type_name;
  if (section_analysis == NULL || effect_kind == M68K_PLATFORM_EFFECT_NONE) return -1;
  if (section_analysis->arena == NULL) return -1;
  for (index = 0; index < section_analysis->recovered_local_call_summary_count; ++index) {
    M68kRecoveredLocalCallSummaryIR *existing = &section_analysis->recovered_local_call_summaries[index];
    const char *existing_base_name = NULL;
    const char *existing_type_name = NULL;
    if (existing->target_offset != target_offset || existing->effect_kind != effect_kind ||
        existing->reg_kind != reg_kind || existing->reg_index != reg_index ||
        existing->success_reg_kind != success_reg_kind || existing->success_reg_index != success_reg_index ||
        existing->success_value_known != success_value_known || existing->success_reg_value != success_reg_value) {
      continue;
    }
    if (existing->effect_kind == M68K_PLATFORM_EFFECT_SET_BASE_REG) {
      existing_base_name = existing->payload.named_base.base_name;
    } else if (existing->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG) {
      existing_type_name = existing->payload.typed.type_name;
    }
    if (((existing_base_name == NULL && base_name == NULL) ||
            (existing_base_name != NULL && base_name != NULL && strcmp(existing_base_name, base_name) == 0)) &&
        ((existing_type_name == NULL && type_name == NULL) ||
            (existing_type_name != NULL && type_name != NULL && strcmp(existing_type_name, type_name) == 0))) {
      return 0;
    }
    return -1;
  }
  section_analysis->recovered_local_call_summaries = (M68kRecoveredLocalCallSummaryIR *)arena_grow_array(
    section_analysis->arena, section_analysis->recovered_local_call_summaries,
    section_analysis->recovered_local_call_summary_count, &section_analysis->recovered_local_call_summary_capacity,
    8U, sizeof(*section_analysis->recovered_local_call_summaries));
  if (section_analysis->recovered_local_call_summaries == NULL) return -1;
  copy_base_name = base_name != NULL ? arena_strdup(section_analysis->arena, base_name) : NULL;
  if (base_name != NULL && copy_base_name == NULL) return -1;
  copy_type_name = type_name != NULL ? arena_strdup(section_analysis->arena, type_name) : NULL;
  if (type_name != NULL && copy_type_name == NULL) return -1;
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
  } else if (effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG) {
    section_analysis->recovered_local_call_summaries[section_analysis->recovered_local_call_summary_count]
      .payload.typed.type_name = copy_type_name;
  }
  section_analysis->recovered_local_call_summary_count += 1U;
  return 0;
}

int m68k_ir_section_analysis_append_recovered_platform_call(M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint8_t kind, const char *symbol_name, uint8_t note_kind, const char *note_base_name,
    const char *note_symbol_name, uint8_t note_reg, int16_t note_disp, int16_t note_field_disp,
    uint8_t note_stack_cleanup_known, uint16_t note_stack_cleanup_bytes, uint8_t note_return_kind) {
  size_t index;
  char *copy_name;
  char *copy_base_name;
  char *copy_note_symbol_name;
  if (section_analysis == NULL) return -1;
  if (symbol_name == NULL && note_kind == M68K_PLATFORM_CALL_NOTE_NONE) return -1;
  if (section_analysis->arena == NULL) return -1;
  for (index = 0; index < section_analysis->recovered_platform_call_count; ++index) {
    M68kRecoveredPlatformCallIR *existing = &section_analysis->recovered_platform_calls[index];
    if (existing->offset == offset && existing->kind == kind) {
      if (((existing->symbol_name == NULL && symbol_name == NULL) ||
              (existing->symbol_name != NULL && symbol_name != NULL &&
               strcmp(existing->symbol_name, symbol_name) == 0)) &&
            existing->note_kind == note_kind &&
            existing->note_reg == note_reg &&
            existing->note_stack_cleanup_known == note_stack_cleanup_known &&
            existing->note_return_kind == note_return_kind &&
            existing->note_disp == note_disp &&
            existing->note_field_disp == note_field_disp &&
            existing->note_stack_cleanup_bytes == note_stack_cleanup_bytes &&
            ((existing->note_base_name == NULL && note_base_name == NULL) ||
                (existing->note_base_name != NULL && note_base_name != NULL &&
                 strcmp(existing->note_base_name, note_base_name) == 0)) &&
          ((existing->note_symbol_name == NULL && note_symbol_name == NULL) ||
              (existing->note_symbol_name != NULL && note_symbol_name != NULL &&
               strcmp(existing->note_symbol_name, note_symbol_name) == 0))) return 0;
      return -1;
    }
  }
  section_analysis->recovered_platform_calls = (M68kRecoveredPlatformCallIR *)arena_grow_array(
    section_analysis->arena, section_analysis->recovered_platform_calls,
    section_analysis->recovered_platform_call_count, &section_analysis->recovered_platform_call_capacity,
    8U, sizeof(*section_analysis->recovered_platform_calls));
  if (section_analysis->recovered_platform_calls == NULL) return -1;
  copy_name = symbol_name != NULL ? arena_strdup(section_analysis->arena, symbol_name) : NULL;
  if (symbol_name != NULL && copy_name == NULL) return -1;
  copy_base_name = note_base_name != NULL ? arena_strdup(section_analysis->arena, note_base_name) : NULL;
  if (note_base_name != NULL && copy_base_name == NULL) return -1;
  copy_note_symbol_name = note_symbol_name != NULL ? arena_strdup(section_analysis->arena, note_symbol_name) : NULL;
  if (note_symbol_name != NULL && copy_note_symbol_name == NULL) return -1;
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
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].note_base_name =
    copy_base_name;
  section_analysis->recovered_platform_calls[section_analysis->recovered_platform_call_count].note_symbol_name =
    copy_note_symbol_name;
  section_analysis->recovered_platform_call_count += 1U;
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
  for (index = 0; index < section_analysis->recovered_platform_base_slot_count; ++index) {
    const M68kRecoveredPlatformBaseSlotIR *slot = &section_analysis->recovered_platform_base_slots[index];
    if (m68k_ir_section_analysis_append_recovered_platform_base_slot(&copy, slot->displacement, slot->base_name) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    if (m68k_ir_section_analysis_append_recovered_platform_effect(&copy, effect->offset, effect->kind,
        effect->reg_kind, effect->reg_index, effect->displacement, effect->field_disp,
        (effect->kind == M68K_PLATFORM_EFFECT_SET_BASE_REG || effect->kind == M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT)
            ? effect->payload.named_base.base_name : NULL,
          effect->kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG ? effect->payload.code_ptr.field_symbol_name : NULL,
          (effect->kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG) ? effect->payload.code_ptr.owner_type_name :
              ((effect->kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG || effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT)
                ? effect->payload.typed.type_name : NULL)) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_local_call_summary_count; ++index) {
    const M68kRecoveredLocalCallSummaryIR *summary = &section_analysis->recovered_local_call_summaries[index];
    if (m68k_ir_section_analysis_append_recovered_local_call_summary(&copy, summary->target_offset, summary->effect_kind,
          summary->reg_kind, summary->reg_index, summary->success_reg_kind, summary->success_reg_index,
          summary->success_value_known, summary->success_reg_value,
          summary->effect_kind == M68K_PLATFORM_EFFECT_SET_BASE_REG ? summary->payload.named_base.base_name : NULL,
          summary->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG ? summary->payload.typed.type_name : NULL) != 0) {
      m68k_ir_section_analysis_destroy(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_platform_call_count; ++index) {
    const M68kRecoveredPlatformCallIR *call = &section_analysis->recovered_platform_calls[index];
      if (m68k_ir_section_analysis_append_recovered_platform_call(&copy,
          call->offset, call->kind, call->symbol_name, call->note_kind, call->note_base_name,
          call->note_symbol_name, call->note_reg, call->note_disp, call->note_field_disp,
          call->note_stack_cleanup_known, call->note_stack_cleanup_bytes, call->note_return_kind) != 0) {
          m68k_ir_section_analysis_destroy(&copy);
          return -1;
        }
  }
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
