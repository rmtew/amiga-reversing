#include "m68k_ir.h"

#include "platform_common.h"

#include <stdlib.h>
#include <string.h>

/* Grow a dynamic array by doubling. ptr/count/capacity must be lvalues on the same struct. On allocation failure,
   returns -1 from the enclosing function. */
#define GROW_ARRAY(ptr, count, capacity, initial) do { \
  if ((count) == (capacity)) { \
    size_t _cap = ((capacity) == 0U) ? (size_t)(initial) : (capacity) * 2U; \
    void *_grown = realloc((ptr), _cap * sizeof(*(ptr))); \
    if (_grown == NULL) return -1; \
    (ptr) = _grown; \
    (capacity) = _cap; \
  } \
} while (0)

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

  free(statement->label_name);
  statement->label_name = NULL;
  free(statement->comment);
  statement->comment = NULL;

  if (statement->kind == M68K_STATEMENT_DATA) {
    free(statement->u.data.data);
    statement->u.data.data = NULL;
    free(statement->u.data.expr_text);
    statement->u.data.expr_text = NULL;
    statement->u.data.size = 0U;
  }

  memset(statement, 0, sizeof(*statement));
}

void m68k_ir_section_init(M68kSectionIR *section) {
  if (section == NULL) return;

  memset(section, 0, sizeof(*section));
}

void m68k_ir_section_free(M68kSectionIR *section) {
  size_t index;
  if (section == NULL) return;

  free(section->name);
  section->name = NULL;

  for (index = 0; index < section->statement_count; ++index)
    m68k_ir_statement_free(&section->statements[index]);

  free(section->statements);
  memset(section, 0, sizeof(*section));
}

int m68k_ir_section_append_statement(M68kSectionIR *section, const M68kStatementIR *statement) {
  M68kStatementIR copy;
  if (section == NULL || statement == NULL) return -1;

  GROW_ARRAY(section->statements, section->statement_count, section->statement_capacity, 16U);
  copy = *statement;
  copy.label_name = m68k_platform_dup_string(statement->label_name);
  if (statement->label_name != NULL && copy.label_name == NULL) return -1;

  copy.comment = m68k_platform_dup_string(statement->comment);
  if (statement->comment != NULL && copy.comment == NULL) {
    free(copy.label_name);
    return -1;
  }

  if (statement->kind == M68K_STATEMENT_DATA && statement->u.data.size != 0U) {
    copy.u.data.data = (uint8_t *)malloc(statement->u.data.size);
    if (copy.u.data.data == NULL) {
      free(copy.label_name);
      free(copy.comment);
      return -1;
    }
    memcpy(copy.u.data.data, statement->u.data.data, statement->u.data.size);
  }

  if (statement->kind == M68K_STATEMENT_DATA) {
    copy.u.data.expr_text = m68k_platform_dup_string(statement->u.data.expr_text);
    if (statement->u.data.expr_text != NULL && copy.u.data.expr_text == NULL) {
      free(copy.u.data.data);
      free(copy.label_name);
      free(copy.comment);
      return -1;
    }
  }

  section->statements[section->statement_count++] = copy;
  return 0;
}

void m68k_ir_source_file_init(M68kSourceFileIR *source_file) {
  if (source_file == NULL) return;

  memset(source_file, 0, sizeof(*source_file));
}

void m68k_ir_source_file_free(M68kSourceFileIR *source_file) {
  size_t index;
  if (source_file == NULL) return;

  for (index = 0; index < source_file->section_count; ++index)
    m68k_ir_section_free(&source_file->sections[index]);

  free(source_file->sections);
  memset(source_file, 0, sizeof(*source_file));
}

int m68k_ir_source_file_append_section(M68kSourceFileIR *source_file, const M68kSectionIR *section) {
  M68kSectionIR copy;
  size_t statement_index;
  if (source_file == NULL || section == NULL) return -1;

  GROW_ARRAY(source_file->sections, source_file->section_count, source_file->section_capacity, 4U);
  m68k_ir_section_init(&copy);
  copy.name = m68k_platform_dup_string(section->name);

  if (section->name != NULL && copy.name == NULL) return -1;

  copy.kind = section->kind;
  copy.size = section->size;

  for (statement_index = 0; statement_index < section->statement_count; ++statement_index)
    if (m68k_ir_section_append_statement( &copy, &section->statements[statement_index]) != 0) {
      m68k_ir_section_free(&copy);
      return -1;
    }

  source_file->sections[source_file->section_count++] = copy;
  return 0;
}

void m68k_ir_section_analysis_init(M68kSectionAnalysisIR *section_analysis) {
  if (section_analysis == NULL) return;

  memset(section_analysis, 0, sizeof(*section_analysis));
}

void m68k_ir_section_analysis_free(M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (section_analysis == NULL) return;

  free(section_analysis->section_name);
  free(section_analysis->certain_code_start);
  free(section_analysis->certain_code_byte);
  free(section_analysis->generated_label_kinds);
  free(section_analysis->generated_label_flags);
  if (section_analysis->word_exprs != NULL) {
    for (index = 0; index < section_analysis->word_expr_count; ++index)
      free(section_analysis->word_exprs[index]);
  }
  free(section_analysis->word_exprs);
  if (section_analysis->long_exprs != NULL) {
    for (index = 0; index < section_analysis->long_expr_count; ++index)
      free(section_analysis->long_exprs[index]);
  }
  free(section_analysis->long_exprs);
  free(section_analysis->label_offsets);
  free(section_analysis->blocks);
  free(section_analysis->edges);
  for (index = 0; index < section_analysis->violation_count; ++index)
    free(section_analysis->violations[index].message);

  free(section_analysis->violations);
  memset(section_analysis, 0, sizeof(*section_analysis));
}

int m68k_ir_section_analysis_set_code_map(M68kSectionAnalysisIR *section_analysis, const uint8_t *code_start,
    const uint8_t *code_byte, size_t size) {
  if (section_analysis == NULL) return -1;

  free(section_analysis->certain_code_start);
  free(section_analysis->certain_code_byte);
  section_analysis->certain_code_start = NULL;
  section_analysis->certain_code_byte = NULL;
  section_analysis->certain_code_size = size;
  if (size == 0U) return 0;

  section_analysis->certain_code_start = (uint8_t *)malloc(size);
  section_analysis->certain_code_byte = (uint8_t *)malloc(size);
  if (section_analysis->certain_code_start == NULL || section_analysis->certain_code_byte == NULL) {
    free(section_analysis->certain_code_start);
    free(section_analysis->certain_code_byte);
    section_analysis->certain_code_start = NULL;
    section_analysis->certain_code_byte = NULL;
    section_analysis->certain_code_size = 0U;
    return -1;
  }

  if (code_start != NULL) memcpy(section_analysis->certain_code_start, code_start, size);
  else                    memset(section_analysis->certain_code_start, 0, size);
  if (code_byte != NULL) memcpy(section_analysis->certain_code_byte, code_byte, size);
  else                   memset(section_analysis->certain_code_byte, 0, size);
  return 0;
}

int m68k_ir_section_analysis_set_generated_labels(M68kSectionAnalysisIR *section_analysis, const uint8_t *label_kinds,
    const uint8_t *label_flags, size_t size) {
  if (section_analysis == NULL) return -1;

  free(section_analysis->generated_label_kinds);
  free(section_analysis->generated_label_flags);
  section_analysis->generated_label_kinds = NULL;
  section_analysis->generated_label_flags = NULL;
  section_analysis->generated_label_size = size;
  if (size == 0U) return 0;

  section_analysis->generated_label_kinds = (uint8_t *)malloc(size);
  section_analysis->generated_label_flags = (uint8_t *)malloc(size);
  if (section_analysis->generated_label_kinds == NULL || section_analysis->generated_label_flags == NULL) {
    free(section_analysis->generated_label_kinds);
    free(section_analysis->generated_label_flags);
    section_analysis->generated_label_kinds = NULL;
    section_analysis->generated_label_flags = NULL;
    section_analysis->generated_label_size = 0U;
    return -1;
  }

  if (label_kinds != NULL) memcpy(section_analysis->generated_label_kinds, label_kinds, size);
  else                     memset(section_analysis->generated_label_kinds, 0, size);
  if (label_flags != NULL) memcpy(section_analysis->generated_label_flags, label_flags, size);
  else                     memset(section_analysis->generated_label_flags, 0, size);
  return 0;
}

int m68k_ir_section_analysis_set_word_exprs(M68kSectionAnalysisIR *section_analysis, char *const *word_exprs, size_t count) {
  size_t index;
  if (section_analysis == NULL) return -1;

  if (section_analysis->word_exprs != NULL) {
    for (index = 0; index < section_analysis->word_expr_count; ++index)
      free(section_analysis->word_exprs[index]);
  }
  free(section_analysis->word_exprs);
  section_analysis->word_exprs = NULL;
  section_analysis->word_expr_count = count;
  if (count == 0U) return 0;

  section_analysis->word_exprs = (char **)calloc(count, sizeof(*section_analysis->word_exprs));
  if (section_analysis->word_exprs == NULL) {
    section_analysis->word_expr_count = 0U;
    return -1;
  }
  if (word_exprs == NULL) return 0;
  for (index = 0; index < count; ++index) {
    if (word_exprs[index] == NULL) continue;
    section_analysis->word_exprs[index] = m68k_platform_dup_string(word_exprs[index]);
    if (section_analysis->word_exprs[index] == NULL) {
      size_t cleanup_index;
      for (cleanup_index = 0; cleanup_index < index; ++cleanup_index)
        free(section_analysis->word_exprs[cleanup_index]);
      free(section_analysis->word_exprs);
      section_analysis->word_exprs = NULL;
      section_analysis->word_expr_count = 0U;
      return -1;
    }
  }
  return 0;
}

int m68k_ir_section_analysis_set_long_exprs(M68kSectionAnalysisIR *section_analysis, char *const *long_exprs, size_t count) {
  size_t index;
  if (section_analysis == NULL) return -1;

  if (section_analysis->long_exprs != NULL) {
    for (index = 0; index < section_analysis->long_expr_count; ++index)
      free(section_analysis->long_exprs[index]);
  }
  free(section_analysis->long_exprs);
  section_analysis->long_exprs = NULL;
  section_analysis->long_expr_count = count;
  if (count == 0U) return 0;

  section_analysis->long_exprs = (char **)calloc(count, sizeof(*section_analysis->long_exprs));
  if (section_analysis->long_exprs == NULL) {
    section_analysis->long_expr_count = 0U;
    return -1;
  }
  if (long_exprs == NULL) return 0;
  for (index = 0; index < count; ++index) {
    if (long_exprs[index] == NULL) continue;
    section_analysis->long_exprs[index] = m68k_platform_dup_string(long_exprs[index]);
    if (section_analysis->long_exprs[index] == NULL) {
      size_t cleanup_index;
      for (cleanup_index = 0; cleanup_index < index; ++cleanup_index)
        free(section_analysis->long_exprs[cleanup_index]);
      free(section_analysis->long_exprs);
      section_analysis->long_exprs = NULL;
      section_analysis->long_expr_count = 0U;
      return -1;
    }
  }
  return 0;
}

int m68k_ir_section_analysis_add_label(M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  size_t index;
  if (section_analysis == NULL) return -1;

  for (index = 0; index < section_analysis->label_count; ++index)
    if (section_analysis->label_offsets[index] == offset) return 0;

  GROW_ARRAY(section_analysis->label_offsets, section_analysis->label_count, section_analysis->label_capacity, 16U);
  section_analysis->label_offsets[section_analysis->label_count++] = offset;
  return 0;
}

int m68k_ir_section_analysis_append_block(M68kSectionAnalysisIR *section_analysis, const M68kCfgBlockIR *block) {
  if (section_analysis == NULL || block == NULL) return -1;

  GROW_ARRAY(section_analysis->blocks, section_analysis->block_count, section_analysis->block_capacity, 16U);
  section_analysis->blocks[section_analysis->block_count++] = *block;
  return 0;
}

int m68k_ir_section_analysis_append_edge(M68kSectionAnalysisIR *section_analysis, const M68kCfgEdgeIR *edge) {
  if (section_analysis == NULL || edge == NULL) return -1;

  GROW_ARRAY(section_analysis->edges, section_analysis->edge_count, section_analysis->edge_capacity, 16U);
  section_analysis->edges[section_analysis->edge_count++] = *edge;
  return 0;
}

int m68k_ir_section_analysis_add_violation(M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t kind,
    const char *message) {
  char *copy;
  size_t index;
  if (section_analysis == NULL || message == NULL) return -1;

  for (index = 0; index < section_analysis->violation_count; ++index) {
    const M68kViolationIR *violation = &section_analysis->violations[index];
    if (violation->offset == offset && violation->kind == kind && violation->message != NULL &&
        strcmp(violation->message, message) == 0)
      return 0;
  }

  GROW_ARRAY(section_analysis->violations, section_analysis->violation_count, section_analysis->violation_capacity, 8U);
  copy = m68k_platform_dup_string(message);
  if (copy == NULL) return -1;

  section_analysis->violations[section_analysis->violation_count].offset = offset;
  section_analysis->violations[section_analysis->violation_count].kind = kind;
  section_analysis->violations[section_analysis->violation_count].message = copy;
  section_analysis->violation_count += 1U;
  return 0;
}

void m68k_ir_source_analysis_init(M68kSourceAnalysisIR *source_analysis) {
  if (source_analysis == NULL)
    return;
  memset(source_analysis, 0, sizeof(*source_analysis));
  m68k_analysis_policy_init_default(&source_analysis->policy);
  m68k_analysis_findings_init(&source_analysis->findings);
}

void m68k_ir_source_analysis_free(M68kSourceAnalysisIR *source_analysis) {
  size_t index;
  if (source_analysis == NULL)
    return;
  for (index = 0; index < source_analysis->section_count; ++index) {
    m68k_ir_section_analysis_free(&source_analysis->sections[index]);
  }
  free(source_analysis->sections);
  memset(source_analysis, 0, sizeof(*source_analysis));
}

int m68k_ir_source_analysis_append_section(M68kSourceAnalysisIR *source_analysis,
                                           const M68kSectionAnalysisIR *section_analysis) {
  M68kSectionAnalysisIR copy;
  size_t index;
  if (source_analysis == NULL || section_analysis == NULL)
    return -1;
  GROW_ARRAY(source_analysis->sections, source_analysis->section_count, source_analysis->section_capacity, 4U);
  m68k_ir_section_analysis_init(&copy);
  copy.section_index = section_analysis->section_index;
  copy.section_name = m68k_platform_dup_string(section_analysis->section_name);
  if (section_analysis->section_name != NULL && copy.section_name == NULL) return -1;
  copy.section_kind = section_analysis->section_kind;
  copy.section_size = section_analysis->section_size;
  if (m68k_ir_section_analysis_set_code_map( &copy, section_analysis->certain_code_start,
          section_analysis->certain_code_byte,
          section_analysis->certain_code_size) != 0) {
    m68k_ir_section_analysis_free(&copy);
    return -1;
  }
  if (m68k_ir_section_analysis_set_generated_labels(&copy, section_analysis->generated_label_kinds,
          section_analysis->generated_label_flags, section_analysis->generated_label_size) != 0) {
    m68k_ir_section_analysis_free(&copy);
    return -1;
  }
  if (m68k_ir_section_analysis_set_word_exprs(&copy, section_analysis->word_exprs,
          section_analysis->word_expr_count) != 0) {
    m68k_ir_section_analysis_free(&copy);
    return -1;
  }
  for (index = 0; index < section_analysis->label_count; ++index) {
    if (m68k_ir_section_analysis_add_label( &copy, section_analysis->label_offsets[index]) != 0) {
      m68k_ir_section_analysis_free(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->block_count; ++index) {
    if (m68k_ir_section_analysis_append_block( &copy, &section_analysis->blocks[index]) != 0) {
      m68k_ir_section_analysis_free(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->edge_count; ++index) {
    if (m68k_ir_section_analysis_append_edge( &copy, &section_analysis->edges[index]) != 0) {
      m68k_ir_section_analysis_free(&copy);
      return -1;
    }
  }
  for (index = 0; index < section_analysis->violation_count; ++index) {
    const M68kViolationIR *violation = &section_analysis->violations[index];
    if (m68k_ir_section_analysis_add_violation(&copy, violation->offset,
                                               violation->kind,
                                               violation->message) != 0) {
      m68k_ir_section_analysis_free(&copy);
      return -1;
    }
  }
  source_analysis->sections[source_analysis->section_count++] = copy;
  return 0;
}
