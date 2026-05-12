#include "m68k_source_model.h"

#include <stdio.h>
#include <string.h>

static int grow_items(Arena *arena, void **items, size_t item_size, size_t *capacity, size_t count_needed) {
  size_t next_capacity = (*capacity == 0U) ? 16U : *capacity;
  size_t old_size = item_size * *capacity;
  void *grown = NULL;
  if (arena == NULL) return 0;
  while (next_capacity < count_needed) next_capacity *= 2U;
  grown = arena_realloc_copy(arena, *items, old_size, item_size * next_capacity);
  if (grown == NULL) return 0;
  *items = grown;
  *capacity = next_capacity;
  return 1;
}

static size_t source_symbol_hash(const char *name) {
  size_t hash = (size_t)1469598103934665603ULL;
  const unsigned char *cursor = (const unsigned char *)name;
  while (*cursor != '\0') {
    hash ^= (size_t)*cursor++;
    hash *= (size_t)1099511628211ULL;
  }
  return hash != 0U ? hash : 1U;
}

static int source_symbol_index_insert(AsmSourceFile *source, size_t symbol_index) {
  size_t mask;
  size_t slot;
  if (source == NULL || source->symbol_index_slots == NULL || source->symbol_index_capacity == 0U) return 0;
  mask = source->symbol_index_capacity - 1U;
  slot = source_symbol_hash(source->symbols[symbol_index].name) & mask;
  for (;;) {
    size_t stored = source->symbol_index_slots[slot];
    if (stored == 0U) {
      source->symbol_index_slots[slot] = symbol_index + 1U;
      return 1;
    }
    if (stored == symbol_index + 1U) return 1;
    slot = (slot + 1U) & mask;
  }
}

static int source_symbol_index_reserve(AsmSourceFile *source, size_t count_needed) {
  size_t next_capacity = 16U;
  size_t index;
  size_t *slots;
  if (source == NULL || source->arena == NULL) return 0;
  while (next_capacity < count_needed * 2U) next_capacity *= 2U;
  if (source->symbol_index_capacity >= next_capacity) return 1;
  slots = (size_t *)arena_calloc(source->arena, next_capacity, sizeof(*slots));
  if (slots == NULL) return 0;
  source->symbol_index_slots = slots;
  source->symbol_index_capacity = next_capacity;
  for (index = 0U; index < source->symbol_count; ++index) {
    if (!source_symbol_index_insert(source, index)) return 0;
  }
  return 1;
}

static M68kSourceModelIndexResult m68k_source_model_find_symbol_index_exact(const AsmSourceFile *source,
    const char *name) {
  M68kSourceModelIndexResult result = {0};
  size_t index;
  if (source->symbol_index_slots != NULL && source->symbol_index_capacity != 0U) {
    size_t mask = source->symbol_index_capacity - 1U;
    size_t slot = source_symbol_hash(name) & mask;
    for (;;) {
      size_t stored = source->symbol_index_slots[slot];
      if (stored == 0U) return result;
      index = stored - 1U;
      if (strcmp(source->symbols[index].name, name) == 0) {
        result.ok = 1U;
        result.index = index;
        return result;
      }
      slot = (slot + 1U) & mask;
    }
  }
  for (index = 0; index < source->symbol_count; ++index) {
    if (strcmp(source->symbols[index].name, name) == 0) {
      result.ok = 1U;
      result.index = index;
      return result;
    }
  }
  return result;
}

M68kSourceModelIndexResult m68k_source_model_find_symbol_index(const AsmSourceFile *source, const char *name) {
  M68kSourceModelIndexResult result = m68k_source_model_find_symbol_index_exact(source, name);
  size_t index;
  size_t match_count = 0U;
  if (result.ok) return result;
  for (index = 0; index < source->symbol_count; ++index) {
    if (_stricmp(source->symbols[index].name, name) == 0) {
      result.ok = 1U;
      result.index = index;
      ++match_count;
    }
  }
  if (match_count == 1U) return result;
  result.ok = 0U;
  result.index = 0U;
  return result;
}

int m68k_source_model_format_section_base_symbol(char *buffer, size_t buffer_size, size_t section_index) {
  int written;
  if (buffer == NULL || buffer_size == 0U || section_index > UINT32_MAX) return 0;
  written = snprintf(buffer, buffer_size, "__section_%u_base", (unsigned)section_index);
  return written > 0 && (size_t)written < buffer_size;
}

static int source_model_parse_section_base_symbol(const char *name, size_t *out_section_index) {
  const char *prefix = "__section_";
  const char *suffix = "_base";
  const char *cursor;
  size_t value = 0U;
  size_t suffix_index = 0U;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (name == NULL || strncmp(name, prefix, strlen(prefix)) != 0) return 0;
  cursor = name + strlen(prefix);
  if (*cursor < '0' || *cursor > '9') return 0;
  while (*cursor >= '0' && *cursor <= '9') {
    size_t digit = (size_t)(*cursor - '0');
    if (value > (SIZE_MAX - digit) / 10U) return 0;
    value = value * 10U + digit;
    ++cursor;
  }
  while (suffix[suffix_index] != '\0') {
    if (cursor[suffix_index] != suffix[suffix_index]) return 0;
    ++suffix_index;
  }
  if (cursor[suffix_index] != '\0') return 0;
  if (out_section_index != NULL) *out_section_index = value;
  return 1;
}

int m68k_source_model_create(AsmSourceFile *source) {
  Arena *arena;
  if (source == NULL) return -1;
  memset(source, 0, sizeof(*source));
  arena = arena_create(4096U);
  if (arena == NULL) return -1;
  source->arena = arena;
  return 0;
}

M68kSourceLookupResult m68k_source_model_lookup_symbol(const char *name, void *user_data) {
  M68kSourceLookupResult result = {0};
  const AsmSourceFile *source = (const AsmSourceFile *)user_data;
  M68kSourceModelIndexResult symbol_result = m68k_source_model_find_symbol_index(source, name);
  if (!symbol_result.ok) {
    size_t section_index = 0U;
    if (source_model_parse_section_base_symbol(name, &section_index) && section_index < source->section_count) {
      result.ok = 1U;
      result.defined = 1U;
      result.is_absolute = 0U;
      result.is_constant = 0U;
      result.value = 0U;
      result.symbol_id = (size_t)-1;
      result.section_index = section_index;
    }
    return result;
  }
  result.ok = 1U;
  result.defined = (uint8_t)(source->symbols[symbol_result.index].defined != 0);
  result.is_absolute = source->symbols[symbol_result.index].is_absolute;
  result.is_constant = (uint8_t)(source->symbols[symbol_result.index].kind == ASM_SOURCE_SYMBOL_CONSTANT ||
    source->symbols[symbol_result.index].is_absolute);
  result.value = source->symbols[symbol_result.index].value;
  result.symbol_id = symbol_result.index;
  result.section_index = source->symbols[symbol_result.index].is_absolute
    ? (size_t)-1 : source->symbols[symbol_result.index].section_index;
  return result;
}

M68kSourceLookupResult m68k_source_model_expr_lookup_symbol(const char *name, void *user_data) {
  return m68k_source_model_lookup_symbol(name, user_data);
}

M68kSourceModelIndexResult m68k_source_model_append_section(AsmSourceFile *source, const char *name,
    M68kSectionKind kind, uint8_t platform_mem_type, uint32_t platform_mem_attrs, uint8_t has_alloc_size,
    uint32_t alloc_size) {
  M68kSourceModelIndexResult result = {0};
  size_t index;
  for (index = 0; index < source->section_count; ++index) {
    if (_stricmp(source->sections[index].name, name) == 0) {
      if (source->sections[index].kind != kind ||
          source->sections[index].platform_mem_type != platform_mem_type ||
          source->sections[index].platform_mem_attrs != platform_mem_attrs ||
          source->sections[index].has_alloc_size != has_alloc_size ||
          source->sections[index].alloc_size != alloc_size)
        return result;
      result.ok = 1U;
      result.index = index;
      return result;
    }
  }
  if (!grow_items(source->arena, (void **)&source->sections, sizeof(*source->sections), &source->section_capacity,
    source->section_count + 1U)) return result;
  memset(&source->sections[source->section_count], 0, sizeof(*source->sections));
  snprintf(source->sections[source->section_count].name, sizeof(source->sections[source->section_count].name), "%s", name);
  source->sections[source->section_count].kind = kind;
  source->sections[source->section_count].platform_mem_type = platform_mem_type;
  source->sections[source->section_count].platform_mem_attrs = platform_mem_attrs;
  source->sections[source->section_count].has_alloc_size = has_alloc_size;
  source->sections[source->section_count].alloc_size = alloc_size;
  result.ok = 1U;
  result.index = source->section_count;
  source->section_count += 1U;
  return result;
}

M68kSourceModelIndexResult m68k_source_model_ensure_symbol(AsmSourceFile *source, const char *name,
    AsmSourceSymbolKind kind) {
  M68kSourceModelIndexResult result = {0};
  size_t index = 0;
  M68kSourceModelIndexResult found_result = m68k_source_model_find_symbol_index_exact(source, name);
  if (found_result.ok) {
    index = found_result.index;
    if (source->symbols[index].kind != kind) return result;
    result.ok = 1U;
    result.index = index;
    return result;
  }
  if (!source_symbol_index_reserve(source, source->symbol_count + 1U)) return result;
  if (!grow_items(source->arena, (void **)&source->symbols, sizeof(*source->symbols), &source->symbol_capacity,
    source->symbol_count + 1U)) return result;
  memset(&source->symbols[source->symbol_count], 0, sizeof(*source->symbols));
  snprintf(source->symbols[source->symbol_count].name, sizeof(source->symbols[source->symbol_count].name), "%s", name);
  source->symbols[source->symbol_count].kind = kind;
  result.ok = 1U;
  result.index = source->symbol_count;
  source->symbol_count += 1U;
  if (!source_symbol_index_insert(source, result.index)) {
    source->symbol_count -= 1U;
    result.ok = 0U;
    result.index = 0U;
    return result;
  }
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
  source->symbols[index].is_absolute = 0U;
  source->symbols[index].section_index = (size_t)-1;
  source->symbols[index].value = value;
  return 1;
}

int m68k_source_model_set_label_value(AsmSourceFile *source, const char *name, size_t section_index, uint32_t value,
    uint8_t is_absolute) {
  M68kSourceModelIndexResult symbol_result = m68k_source_model_ensure_symbol(source, name, ASM_SOURCE_SYMBOL_LABEL);
  size_t index;
  if (!symbol_result.ok) return 0;
  index = symbol_result.index;
  source->symbols[index].defined = 1;
  source->symbols[index].is_absolute = is_absolute;
  source->symbols[index].section_index = section_index;
  source->symbols[index].value = value;
  return 1;
}

M68kSourceModelIndexResult m68k_source_model_append_statement(AsmSourceFile *source, AsmSourceStmtKind kind,
    size_t line_number) {
  M68kSourceModelIndexResult result = {0};
  if (!grow_items(source->arena, (void **)&source->statements, sizeof(*source->statements), &source->statement_capacity,
    source->statement_count + 1U)) return result;
  memset(&source->statements[source->statement_count], 0, sizeof(*source->statements));
  source->statements[source->statement_count].kind = kind;
  source->statements[source->statement_count].line_number = line_number;
  result.ok = 1U;
  result.index = source->statement_count;
  source->statement_count += 1U;
  return result;
}

int m68k_source_model_append_data_item(AsmSourceFile *source, AsmSourceDataStmt *data_stmt,
    const AsmDataItem *item) {
  AsmDataItem copy;
  if (source == NULL || source->arena == NULL || data_stmt == NULL || item == NULL) return 0;
  if (!grow_items(source->arena, (void **)&data_stmt->items, sizeof(*data_stmt->items), &data_stmt->item_capacity,
    data_stmt->item_count + 1U)) return 0;
  copy = *item;
  if (item->kind == ASM_DATA_ITEM_STRING) {
    copy.bytes = (uint8_t *)arena_memdup(source->arena, item->bytes, item->byte_count);
    if (copy.bytes == NULL) return 0;
  }
  data_stmt->items[data_stmt->item_count] = copy;
  data_stmt->item_count += 1U;
  return 1;
}

void m68k_source_model_free(AsmSourceFile *source) {
  Arena *arena;
  if (source == NULL) return;
  arena = source->arena;
  memset(source, 0, sizeof(*source));
  arena_destroy(arena);
}
