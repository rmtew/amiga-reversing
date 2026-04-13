#include "m68k_source_model.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int grow_items(void **items, size_t item_size, size_t *capacity, size_t count_needed) {
  size_t next_capacity = (*capacity == 0U) ? 16U : *capacity;
  void *grown = NULL;
  while (next_capacity < count_needed) next_capacity *= 2U;
  grown = realloc(*items, item_size * next_capacity);
  if (grown == NULL) return 0;
  *items = grown;
  *capacity = next_capacity;
  return 1;
}

int m68k_source_model_find_symbol_index(const AsmSourceFile *source, const char *name, size_t *out_index) {
  size_t index;
  for (index = 0; index < source->symbol_count; ++index) {
    if (_stricmp(source->symbols[index].name, name) == 0) {
      if (out_index != NULL) *out_index = index;
      return 1;
    }
  }
  return 0;
}

int m68k_source_model_lookup_symbol(const char *name, uint32_t *out_value, size_t *out_section_index, int *out_defined,
    void *user_data) {
  const AsmSourceFile *source = (const AsmSourceFile *)user_data;
  size_t symbol_index = 0;
  if (!m68k_source_model_find_symbol_index(source, name, &symbol_index)) return 0;
  if (out_value != NULL) *out_value = source->symbols[symbol_index].value;
  if (out_section_index != NULL) *out_section_index = source->symbols[symbol_index].section_index;
  if (out_defined != NULL) *out_defined = source->symbols[symbol_index].defined;
  return 1;
}

int m68k_source_model_expr_lookup_symbol(const char *name, int *out_defined, int *out_is_constant, uint32_t *out_value,
    size_t *out_symbol_id, size_t *out_section_index, void *user_data) {
  const AsmSourceFile *source = (const AsmSourceFile *)user_data;
  size_t symbol_index = 0;
  if (!m68k_source_model_find_symbol_index(source, name, &symbol_index)) return 0;
  if (out_defined != NULL) *out_defined = source->symbols[symbol_index].defined;
  if (out_is_constant != NULL) *out_is_constant = (source->symbols[symbol_index].kind == ASM_SOURCE_SYMBOL_CONSTANT);
  if (out_value != NULL) *out_value = source->symbols[symbol_index].value;
  if (out_symbol_id != NULL) *out_symbol_id = symbol_index;
  if (out_section_index != NULL) *out_section_index = source->symbols[symbol_index].section_index;
  return 1;
}

int m68k_source_model_append_section(AsmSourceFile *source, const char *name, M68kSectionKind kind, size_t *out_index) {
  size_t index;
  for (index = 0; index < source->section_count; ++index) {
    if (_stricmp(source->sections[index].name, name) == 0) {
      if (source->sections[index].kind != kind) return 0;
      *out_index = index;
      return 1;
    }
  }
  if (!grow_items((void **)&source->sections, sizeof(*source->sections), &source->section_capacity,
    source->section_count + 1U)) return 0;
  memset(&source->sections[source->section_count], 0, sizeof(*source->sections));
  snprintf(source->sections[source->section_count].name, sizeof(source->sections[source->section_count].name), "%s", name);
  source->sections[source->section_count].kind = kind;
  *out_index = source->section_count;
  source->section_count += 1U;
  return 1;
}

int m68k_source_model_ensure_symbol(AsmSourceFile *source, const char *name, AsmSourceSymbolKind kind, size_t *out_index) {
      size_t index = 0;
  if (m68k_source_model_find_symbol_index(source, name, &index)) {
    if (source->symbols[index].kind != kind) return 0;
    if (out_index != NULL) *out_index = index;
    return 1;
  }
  if (!grow_items((void **)&source->symbols, sizeof(*source->symbols), &source->symbol_capacity,
    source->symbol_count + 1U)) return 0;
  memset(&source->symbols[source->symbol_count], 0, sizeof(*source->symbols));
  snprintf(source->symbols[source->symbol_count].name, sizeof(source->symbols[source->symbol_count].name), "%s", name);
  source->symbols[source->symbol_count].kind = kind;
  if (out_index != NULL) *out_index = source->symbol_count;
  source->symbol_count += 1U;
  return 1;
}

int m68k_source_model_set_constant(AsmSourceFile *source, const char *name, uint32_t value, int allow_redefine) {
  size_t index = 0;
  if (!m68k_source_model_ensure_symbol(source, name, ASM_SOURCE_SYMBOL_CONSTANT, &index)) return 0;
  if (source->symbols[index].defined && !allow_redefine && source->symbols[index].value != value) return 0;
  source->symbols[index].defined = 1;
  source->symbols[index].section_index = (size_t)-1;
  source->symbols[index].value = value;
  return 1;
}

int m68k_source_model_set_label_value(AsmSourceFile *source, const char *name, size_t section_index, uint32_t value) {
  size_t index = 0;
  if (!m68k_source_model_ensure_symbol(source, name, ASM_SOURCE_SYMBOL_LABEL, &index)) return 0;
  source->symbols[index].defined = 1;
  source->symbols[index].section_index = section_index;
  source->symbols[index].value = value;
  return 1;
}

int m68k_source_model_append_statement(AsmSourceFile *source, AsmSourceStmtKind kind, size_t line_number, AsmSourceStmt **out_stmt) {
  if (!grow_items((void **)&source->statements, sizeof(*source->statements), &source->statement_capacity,
    source->statement_count + 1U)) return 0;
  memset(&source->statements[source->statement_count], 0, sizeof(*source->statements));
  source->statements[source->statement_count].kind = kind;
  source->statements[source->statement_count].line_number = line_number;
  *out_stmt = &source->statements[source->statement_count];
  source->statement_count += 1U;
  return 1;
}

int m68k_source_model_append_data_item(AsmSourceDataStmt *data_stmt, const AsmDataItem *item) {
  if (!grow_items((void **)&data_stmt->items, sizeof(*data_stmt->items), &data_stmt->item_capacity,
    data_stmt->item_count + 1U)) return 0;
  data_stmt->items[data_stmt->item_count] = *item;
  data_stmt->item_count += 1U;
  return 1;
}

void m68k_source_model_free(AsmSourceFile *source) {
  size_t index;
  for (index = 0; index < source->statement_count; ++index) {
    AsmSourceStmt *stmt = &source->statements[index];
    if (stmt->kind != ASM_SOURCE_STMT_DATA) continue;
    if (stmt->u.data.items != NULL) {
      size_t item_index;
      for (item_index = 0; item_index < stmt->u.data.item_count; ++item_index) {
        free(stmt->u.data.items[item_index].bytes);
      }
      free(stmt->u.data.items);
    }
  }
  free(source->sections);
  free(source->symbols);
  free(source->statements);
  memset(source, 0, sizeof(*source));
}
