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

M68kSourceModelIndexResult m68k_source_model_find_symbol_index(const AsmSourceFile *source, const char *name) {
  M68kSourceModelIndexResult result = {0};
  size_t index;
  for (index = 0; index < source->symbol_count; ++index) {
    if (_stricmp(source->symbols[index].name, name) == 0) {
      result.ok = 1U;
      result.index = index;
      return result;
    }
  }
  return result;
}

M68kSourceLookupResult m68k_source_model_lookup_symbol(const char *name, void *user_data) {
  M68kSourceLookupResult result = {0};
  const AsmSourceFile *source = (const AsmSourceFile *)user_data;
  M68kSourceModelIndexResult symbol_result = m68k_source_model_find_symbol_index(source, name);
  if (!symbol_result.ok) return result;
  result.ok = 1U;
  result.defined = (uint8_t)(source->symbols[symbol_result.index].defined != 0);
  result.is_constant = (uint8_t)(source->symbols[symbol_result.index].kind == ASM_SOURCE_SYMBOL_CONSTANT);
  result.value = source->symbols[symbol_result.index].value;
  result.symbol_id = symbol_result.index;
  result.section_index = source->symbols[symbol_result.index].section_index;
  return result;
}

M68kSourceLookupResult m68k_source_model_expr_lookup_symbol(const char *name, void *user_data) {
  return m68k_source_model_lookup_symbol(name, user_data);
}

M68kSourceModelIndexResult m68k_source_model_append_section(AsmSourceFile *source, const char *name,
    M68kSectionKind kind) {
  M68kSourceModelIndexResult result = {0};
  size_t index;
  for (index = 0; index < source->section_count; ++index) {
    if (_stricmp(source->sections[index].name, name) == 0) {
      if (source->sections[index].kind != kind) return result;
      result.ok = 1U;
      result.index = index;
      return result;
    }
  }
  if (!grow_items((void **)&source->sections, sizeof(*source->sections), &source->section_capacity,
    source->section_count + 1U)) return result;
  memset(&source->sections[source->section_count], 0, sizeof(*source->sections));
  snprintf(source->sections[source->section_count].name, sizeof(source->sections[source->section_count].name), "%s", name);
  source->sections[source->section_count].kind = kind;
  result.ok = 1U;
  result.index = source->section_count;
  source->section_count += 1U;
  return result;
}

M68kSourceModelIndexResult m68k_source_model_ensure_symbol(AsmSourceFile *source, const char *name,
    AsmSourceSymbolKind kind) {
  M68kSourceModelIndexResult result = {0};
  size_t index = 0;
  M68kSourceModelIndexResult found_result = m68k_source_model_find_symbol_index(source, name);
  if (found_result.ok) {
    index = found_result.index;
    if (source->symbols[index].kind != kind) return result;
    result.ok = 1U;
    result.index = index;
    return result;
  }
  if (!grow_items((void **)&source->symbols, sizeof(*source->symbols), &source->symbol_capacity,
    source->symbol_count + 1U)) return result;
  memset(&source->symbols[source->symbol_count], 0, sizeof(*source->symbols));
  snprintf(source->symbols[source->symbol_count].name, sizeof(source->symbols[source->symbol_count].name), "%s", name);
  source->symbols[source->symbol_count].kind = kind;
  result.ok = 1U;
  result.index = source->symbol_count;
  source->symbol_count += 1U;
  return result;
}

int m68k_source_model_set_constant(AsmSourceFile *source, const char *name, uint32_t value, int allow_redefine) {
  M68kSourceModelIndexResult symbol_result = m68k_source_model_ensure_symbol(source, name,
    ASM_SOURCE_SYMBOL_CONSTANT);
  size_t index;
  if (!symbol_result.ok) return 0;
  index = symbol_result.index;
  if (source->symbols[index].defined && !allow_redefine && source->symbols[index].value != value) return 0;
  source->symbols[index].defined = 1;
  source->symbols[index].section_index = (size_t)-1;
  source->symbols[index].value = value;
  return 1;
}

int m68k_source_model_set_label_value(AsmSourceFile *source, const char *name, size_t section_index, uint32_t value) {
  M68kSourceModelIndexResult symbol_result = m68k_source_model_ensure_symbol(source, name, ASM_SOURCE_SYMBOL_LABEL);
  size_t index;
  if (!symbol_result.ok) return 0;
  index = symbol_result.index;
  source->symbols[index].defined = 1;
  source->symbols[index].section_index = section_index;
  source->symbols[index].value = value;
  return 1;
}

M68kSourceModelIndexResult m68k_source_model_append_statement(AsmSourceFile *source, AsmSourceStmtKind kind,
    size_t line_number) {
  M68kSourceModelIndexResult result = {0};
  if (!grow_items((void **)&source->statements, sizeof(*source->statements), &source->statement_capacity,
    source->statement_count + 1U)) return result;
  memset(&source->statements[source->statement_count], 0, sizeof(*source->statements));
  source->statements[source->statement_count].kind = kind;
  source->statements[source->statement_count].line_number = line_number;
  result.ok = 1U;
  result.index = source->statement_count;
  source->statement_count += 1U;
  return result;
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
