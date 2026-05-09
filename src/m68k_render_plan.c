#include "m68k_render_plan.h"

#include "m68k_source_ir_render.h"
#include "m68k_source_text_util.h"
#include "util_arena.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static Arena *render_plan_arena(M68kRenderPlan *plan) {
  if (plan == NULL) return NULL;
  if (plan->arena == NULL) {
    plan->arena = arena_create(4096U);
    if (plan->arena == NULL) return NULL;
  }
  return plan->arena;
}

static char *render_plan_strdup(M68kRenderPlan *plan, const char *text) {
  Arena *arena;
  if (text == NULL) return NULL;
  arena = render_plan_arena(plan);
  if (arena == NULL) return NULL;
  return arena_strdup(arena, text);
}

static uint32_t render_plan_count_lines(const char *text) {
  uint32_t count = 0U;
  const char *cursor;
  if (text == NULL || text[0] == '\0') return 0U;
  for (cursor = text; *cursor != '\0'; ++cursor) {
    if (*cursor == '\n') ++count;
  }
  return count;
}

static int render_plan_text_has_complete_lines(const char *text) {
  size_t length;
  if (text == NULL) return 0;
  length = strlen(text);
  return length != 0U && text[length - 1U] == '\n';
}

static int render_plan_reserve_rows(M68kRenderPlan *plan, size_t needed) {
  Arena *arena;
  M68kRenderPlanRow *rows;
  size_t capacity;
  size_t old_size;
  size_t new_size;
  if (plan == NULL) return -1;
  if (needed <= plan->row_capacity) return 0;
  arena = render_plan_arena(plan);
  if (arena == NULL) return -1;
  capacity = plan->row_capacity != 0U ? plan->row_capacity : 8U;
  while (capacity < needed) {
    if (capacity > ((size_t)-1) / 2U) return -1;
    capacity *= 2U;
  }
  if (capacity > ((size_t)-1) / sizeof(*rows)) return -1;
  old_size = plan->row_count * sizeof(*rows);
  new_size = capacity * sizeof(*rows);
  rows = (M68kRenderPlanRow *)arena_realloc_copy(arena, plan->rows, old_size, new_size);
  if (rows == NULL) return -1;
  plan->rows = rows;
  plan->row_capacity = capacity;
  return 0;
}

static int render_plan_row_builder_reserve(M68kRenderPlanRowBuilder *builder, size_t needed) {
  char *text;
  size_t capacity;
  if (builder == NULL) return -1;
  if (needed <= builder->capacity) return 0;
  capacity = builder->capacity != 0U ? builder->capacity : 128U;
  while (capacity < needed) {
    if (capacity > ((size_t)-1) / 2U) return -1;
    capacity *= 2U;
  }
  text = (char *)realloc(builder->text, capacity);
  if (text == NULL) return -1;
  builder->text = text;
  builder->capacity = capacity;
  return 0;
}

static int render_plan_range_contains(uint32_t start, uint32_t size, uint32_t value) {
  uint32_t end;
  if (size == 0U || value < start) return 0;
  end = start + size;
  if (end < start) return 0;
  return value < end;
}

void m68k_render_plan_init(M68kRenderPlan *plan) {
  if (plan == NULL) return;
  memset(plan, 0, sizeof(*plan));
  plan->next_row_id = 1U;
}

void m68k_render_plan_destroy(M68kRenderPlan *plan) {
  if (plan == NULL) return;
  arena_destroy(plan->arena);
  memset(plan, 0, sizeof(*plan));
}

void m68k_render_plan_move(M68kRenderPlan *dest, M68kRenderPlan *src) {
  if (dest == NULL || src == NULL || dest == src) return;
  m68k_render_plan_destroy(dest);
  *dest = *src;
  m68k_render_plan_init(src);
}

static int render_plan_append_text_row_impl(M68kRenderPlan *plan, uint32_t kind, uint32_t region_id,
    const char *text, int copy_text, M68kRenderPlanRow **out_row) {
  M68kRenderPlanRow *row;
  uint32_t line_count = render_plan_count_lines(text);
  size_t byte_count;
  char *row_text;
  if (out_row != NULL) *out_row = NULL;
  if (plan == NULL || line_count == 0U || !render_plan_text_has_complete_lines(text)) return -1;
  if (UINT32_MAX - plan->total_lines < line_count) return -1;
  byte_count = strlen(text);
  if (((size_t)-1) - plan->total_bytes < byte_count) return -1;
  if (render_plan_reserve_rows(plan, plan->row_count + 1U) != 0) return -1;
  row_text = copy_text ? render_plan_strdup(plan, text) : (char *)text;
  if (row_text == NULL) return -1;
  row = &plan->rows[plan->row_count++];
  memset(row, 0, sizeof(*row));
  row->id = plan->next_row_id++;
  row->kind = kind;
  row->region_id = region_id;
  row->start_line = plan->total_lines;
  row->line_count = line_count;
  row->start_byte = plan->total_bytes;
  row->byte_count = byte_count;
  row->source_section_index = M68K_RENDER_PLAN_NO_SECTION;
  row->text = row_text;
  plan->total_lines += line_count;
  plan->total_bytes += byte_count;
  if (out_row != NULL) *out_row = row;
  return 0;
}

int m68k_render_plan_append_text_row(M68kRenderPlan *plan, uint32_t kind, uint32_t region_id,
    const char *text, M68kRenderPlanRow **out_row) {
  return render_plan_append_text_row_impl(plan, kind, region_id, text, 1, out_row);
}

static int render_plan_append_arena_text_row(M68kRenderPlan *plan, uint32_t kind, uint32_t region_id,
    const char *text, M68kRenderPlanRow **out_row) {
  return render_plan_append_text_row_impl(plan, kind, region_id, text, 0, out_row);
}

void m68k_render_plan_row_builder_init(M68kRenderPlanRowBuilder *builder) {
  if (builder == NULL) return;
  memset(builder, 0, sizeof(*builder));
}

void m68k_render_plan_row_builder_destroy(M68kRenderPlanRowBuilder *builder) {
  if (builder == NULL) return;
  free(builder->text);
  memset(builder, 0, sizeof(*builder));
}

int m68k_render_plan_row_builder_begin(M68kRenderPlanRowBuilder *builder, M68kRenderPlan *plan,
    uint32_t kind, uint32_t region_id) {
  if (builder == NULL || plan == NULL || builder->active) return -1;
  builder->plan = plan;
  builder->kind = kind;
  builder->region_id = region_id;
  builder->size = 0U;
  builder->current_line = 0U;
  builder->directive_line_mask = 0U;
  builder->label_line_mask = 0U;
  memset(builder->label_line_source_offsets, 0, sizeof(builder->label_line_source_offsets));
  builder->label_line_runtime_mask = 0U;
  memset(builder->label_line_runtime_addresses, 0, sizeof(builder->label_line_runtime_addresses));
  builder->active = 1U;
  if (render_plan_row_builder_reserve(builder, 1U) != 0) {
    builder->active = 0U;
    return -1;
  }
  builder->text[0] = '\0';
  return 0;
}

int m68k_render_plan_row_builder_append(M68kRenderPlanRowBuilder *builder, const char *text) {
  size_t length;
  if (builder == NULL || !builder->active || text == NULL) return -1;
  length = strlen(text);
  return m68k_render_plan_row_builder_append_span(builder, text, length);
}

int m68k_render_plan_row_builder_append_span(M68kRenderPlanRowBuilder *builder, const char *text, size_t length) {
  size_t index;
  if (builder == NULL || !builder->active || (text == NULL && length != 0U)) return -1;
  if (length > ((size_t)-1) - builder->size - 1U) return -1;
  if (render_plan_row_builder_reserve(builder, builder->size + length + 1U) != 0) return -1;
  if (length != 0U) memcpy(builder->text + builder->size, text, length);
  for (index = 0U; index < length; ++index) {
    if (text[index] == '\n' && builder->current_line != UINT32_MAX) ++builder->current_line;
  }
  builder->size += length;
  builder->text[builder->size] = '\0';
  return 0;
}

int m68k_render_plan_row_builder_appendf(M68kRenderPlanRowBuilder *builder, const char *format, ...) {
  va_list args;
  va_list copy;
  int needed;
  if (builder == NULL || !builder->active || format == NULL) return -1;
  va_start(args, format);
  va_copy(copy, args);
  needed = vsnprintf(NULL, 0U, format, copy);
  va_end(copy);
  if (needed < 0 || (size_t)needed > ((size_t)-1) - builder->size - 1U) {
    va_end(args);
    return -1;
  }
  if (render_plan_row_builder_reserve(builder, builder->size + (size_t)needed + 1U) != 0) {
    va_end(args);
    return -1;
  }
  vsnprintf(builder->text + builder->size, builder->capacity - builder->size, format, args);
  va_end(args);
  builder->size += (size_t)needed;
  return 0;
}

void m68k_render_plan_row_builder_mark_current_line_directive(M68kRenderPlanRowBuilder *builder) {
  if (builder == NULL || !builder->active || builder->current_line >= 32U) return;
  builder->directive_line_mask |= 1U << builder->current_line;
}

void m68k_render_plan_row_builder_mark_current_line_label(M68kRenderPlanRowBuilder *builder,
    uint32_t source_offset, uint8_t has_runtime_address, uint32_t runtime_address) {
  if (builder == NULL || !builder->active || builder->current_line >= 32U) return;
  builder->label_line_mask |= 1U << builder->current_line;
  builder->label_line_source_offsets[builder->current_line] = source_offset;
  if (has_runtime_address) {
    builder->label_line_runtime_mask |= 1U << builder->current_line;
    builder->label_line_runtime_addresses[builder->current_line] = runtime_address;
  }
}

int m68k_render_plan_row_builder_commit(M68kRenderPlanRowBuilder *builder, M68kRenderPlanRow **out_row) {
  int result;
  if (out_row != NULL) *out_row = NULL;
  if (builder == NULL || !builder->active || builder->plan == NULL) return -1;
  result = m68k_render_plan_append_text_row(builder->plan, builder->kind, builder->region_id, builder->text, out_row);
  if (result == 0 && out_row != NULL && *out_row != NULL) {
    (*out_row)->directive_line_mask = builder->directive_line_mask;
    (*out_row)->label_line_mask = builder->label_line_mask;
    memcpy((*out_row)->label_line_source_offsets, builder->label_line_source_offsets,
      sizeof((*out_row)->label_line_source_offsets));
    (*out_row)->label_line_runtime_mask = builder->label_line_runtime_mask;
    memcpy((*out_row)->label_line_runtime_addresses, builder->label_line_runtime_addresses,
      sizeof((*out_row)->label_line_runtime_addresses));
  }
  builder->active = 0U;
  builder->plan = NULL;
  builder->size = 0U;
  builder->current_line = 0U;
  builder->directive_line_mask = 0U;
  builder->label_line_mask = 0U;
  memset(builder->label_line_source_offsets, 0, sizeof(builder->label_line_source_offsets));
  builder->label_line_runtime_mask = 0U;
  memset(builder->label_line_runtime_addresses, 0, sizeof(builder->label_line_runtime_addresses));
  if (builder->text != NULL) builder->text[0] = '\0';
  return result;
}

void m68k_render_plan_row_builder_cancel(M68kRenderPlanRowBuilder *builder) {
  if (builder == NULL) return;
  builder->active = 0U;
  builder->plan = NULL;
  builder->size = 0U;
  builder->current_line = 0U;
  builder->directive_line_mask = 0U;
  builder->label_line_mask = 0U;
  memset(builder->label_line_source_offsets, 0, sizeof(builder->label_line_source_offsets));
  builder->label_line_runtime_mask = 0U;
  memset(builder->label_line_runtime_addresses, 0, sizeof(builder->label_line_runtime_addresses));
  if (builder->text != NULL) builder->text[0] = '\0';
}

void m68k_render_plan_row_set_source_range(M68kRenderPlanRow *row, uint32_t section_index,
    uint32_t offset, uint32_t size) {
  if (row == NULL) return;
  row->has_source_range = 1U;
  row->source_section_index = section_index;
  row->source_offset = offset;
  row->source_size = size;
}

void m68k_render_plan_row_set_runtime_range(M68kRenderPlanRow *row, uint32_t address, uint32_t size) {
  if (row == NULL) return;
  row->has_runtime_range = 1U;
  row->runtime_address = address;
  row->runtime_size = size;
}

void m68k_render_plan_row_set_statement_metadata(M68kRenderPlanRow *row, uint8_t statement_kind,
    const M68kInstructionIR *instruction, const uint8_t *source_bytes, size_t source_byte_count) {
  size_t byte_count;
  if (row == NULL) return;
  row->has_statement_metadata = 1U;
  row->statement_kind = statement_kind;
  if (instruction != NULL) row->statement_instruction = *instruction;
  byte_count = source_byte_count;
  if (byte_count > M68K_STATEMENT_SOURCE_BYTES_MAX) byte_count = M68K_STATEMENT_SOURCE_BYTES_MAX;
  if (source_bytes != NULL && byte_count != 0U) {
    memcpy(row->source_bytes, source_bytes, byte_count);
    row->source_byte_count = (uint8_t)byte_count;
  }
}

void m68k_render_plan_row_set_data_class(M68kRenderPlanRow *row, const char *data_class) {
  if (row == NULL) return;
  row->data_class[0] = '\0';
  row->data_class_flags = 0U;
  if (data_class == NULL || data_class[0] == '\0') return;
  snprintf(row->data_class, sizeof(row->data_class), "%s", data_class);
  row->data_class_flags = m68k_analysis_structured_data_role_flags_for_text(row->data_class);
}

void m68k_render_plan_row_set_data_class_flags(M68kRenderPlanRow *row, uint32_t data_class_flags) {
  const char *data_class;
  if (row == NULL) return;
  row->data_class[0] = '\0';
  row->data_class_flags = data_class_flags;
  data_class = m68k_analysis_structured_data_role_name_for_flags(data_class_flags);
  if (data_class != NULL) snprintf(row->data_class, sizeof(row->data_class), "%s", data_class);
}

const M68kRenderPlanRow *m68k_render_plan_row_at(const M68kRenderPlan *plan, size_t row_index) {
  if (plan == NULL || row_index >= plan->row_count) return NULL;
  return &plan->rows[row_index];
}

const M68kRenderPlanRow *m68k_render_plan_find_row_for_line(const M68kRenderPlan *plan, uint32_t line,
    uint32_t *out_subline) {
  size_t low;
  size_t high;
  if (out_subline != NULL) *out_subline = 0U;
  if (plan == NULL || line >= plan->total_lines) return NULL;
  low = 0U;
  high = plan->row_count;
  while (low < high) {
    size_t mid = low + ((high - low) / 2U);
    const M68kRenderPlanRow *row = &plan->rows[mid];
    if (line < row->start_line) {
      high = mid;
    } else if (line >= row->start_line + row->line_count) {
      low = mid + 1U;
    } else {
      if (out_subline != NULL) *out_subline = line - row->start_line;
      return row;
    }
  }
  return NULL;
}

const M68kRenderPlanRow *m68k_render_plan_find_row_for_source_offset(const M68kRenderPlan *plan,
    uint32_t section_index, uint32_t offset) {
  size_t index;
  if (plan == NULL) return NULL;
  for (index = 0U; index < plan->row_count; ++index) {
    const M68kRenderPlanRow *row = &plan->rows[index];
    if (row->has_source_range && row->source_section_index == section_index &&
        render_plan_range_contains(row->source_offset, row->source_size, offset)) {
      return row;
    }
  }
  return NULL;
}

const M68kRenderPlanRow *m68k_render_plan_find_row_for_runtime_address(const M68kRenderPlan *plan,
    uint32_t address) {
  size_t index;
  if (plan == NULL) return NULL;
  for (index = 0U; index < plan->row_count; ++index) {
    const M68kRenderPlanRow *row = &plan->rows[index];
    if (row->has_runtime_range && render_plan_range_contains(row->runtime_address, row->runtime_size, address))
      return row;
  }
  return NULL;
}

int m68k_render_plan_emit_rows_alloc(const M68kRenderPlan *plan, size_t first_row, size_t row_count,
    char **out_text) {
  size_t index;
  size_t end_row;
  size_t total_size = 1U;
  char *text;
  char *cursor;
  if (out_text == NULL) return -1;
  *out_text = NULL;
  if (plan == NULL || first_row > plan->row_count) return -1;
  end_row = first_row + row_count;
  if (end_row < first_row || end_row > plan->row_count) end_row = plan->row_count;
  for (index = first_row; index < end_row; ++index) {
    if (total_size > ((size_t)-1) - plan->rows[index].byte_count) return -1;
    total_size += plan->rows[index].byte_count;
  }
  text = (char *)malloc(total_size);
  if (text == NULL) return -1;
  cursor = text;
  for (index = first_row; index < end_row; ++index) {
    memcpy(cursor, plan->rows[index].text, plan->rows[index].byte_count);
    cursor += plan->rows[index].byte_count;
  }
  *cursor = '\0';
  *out_text = text;
  return 0;
}

static uint32_t render_plan_min_u32(uint32_t left, uint32_t right) {
  return left < right ? left : right;
}

static int render_plan_alloc_empty_text(char **out_text) {
  char *text;
  if (out_text == NULL) return -1;
  text = (char *)malloc(1U);
  if (text == NULL) return -1;
  text[0] = '\0';
  *out_text = text;
  return 0;
}

int m68k_render_plan_emit_line_window_alloc(const M68kRenderPlan *plan, uint32_t first_line,
    uint32_t line_count, char **out_text) {
  const M68kRenderPlanRow *first_row;
  size_t row_index;
  uint32_t end_line;
  size_t total_size = 1U;
  char *text;
  char *out_cursor;
  if (out_text == NULL) return -1;
  *out_text = NULL;
  if (plan == NULL || first_line > plan->total_lines) return -1;
  if (line_count == 0U || first_line == plan->total_lines) return render_plan_alloc_empty_text(out_text);
  if (line_count > UINT32_MAX - first_line) end_line = plan->total_lines;
  else end_line = render_plan_min_u32(first_line + line_count, plan->total_lines);
  first_row = m68k_render_plan_find_row_for_line(plan, first_line, NULL);
  if (first_row == NULL) return -1;
  for (row_index = (size_t)(first_row - plan->rows); row_index < plan->row_count; ++row_index) {
    const M68kRenderPlanRow *row = &plan->rows[row_index];
    const char *cursor;
    uint32_t subline = 0U;
    if (row->start_line + row->line_count <= first_line) continue;
    if (row->start_line >= end_line) break;
    cursor = row->text;
    while (*cursor != '\0') {
      const char *line_start = cursor;
      size_t line_length;
      uint32_t physical_line;
      while (*cursor != '\0' && *cursor != '\n') ++cursor;
      if (*cursor == '\n') ++cursor;
      line_length = (size_t)(cursor - line_start);
      physical_line = row->start_line + subline;
      if (physical_line >= first_line && physical_line < end_line) {
        if (total_size > ((size_t)-1) - line_length) return -1;
        total_size += line_length;
      }
      ++subline;
    }
  }
  text = (char *)malloc(total_size);
  if (text == NULL) return -1;
  out_cursor = text;
  for (row_index = (size_t)(first_row - plan->rows); row_index < plan->row_count; ++row_index) {
    const M68kRenderPlanRow *row = &plan->rows[row_index];
    const char *cursor;
    uint32_t subline = 0U;
    if (row->start_line + row->line_count <= first_line) continue;
    if (row->start_line >= end_line) break;
    cursor = row->text;
    while (*cursor != '\0') {
      const char *line_start = cursor;
      size_t line_length;
      uint32_t physical_line;
      while (*cursor != '\0' && *cursor != '\n') ++cursor;
      if (*cursor == '\n') ++cursor;
      line_length = (size_t)(cursor - line_start);
      physical_line = row->start_line + subline;
      if (physical_line >= first_line && physical_line < end_line) {
        memcpy(out_cursor, line_start, line_length);
        out_cursor += line_length;
      }
      ++subline;
    }
  }
  *out_cursor = '\0';
  *out_text = text;
  return 0;
}

int m68k_render_plan_emit_all_alloc(const M68kRenderPlan *plan, char **out_text) {
  if (plan == NULL) return -1;
  return m68k_render_plan_emit_rows_alloc(plan, 0U, plan->row_count, out_text);
}

static int render_plan_row_header_group(const M68kRenderPlanRow *row) {
  if (row == NULL) return -1;
  if (row->kind == M68K_RENDER_PLAN_ROW_INCLUDE) return 0;
  if (row->kind == M68K_RENDER_PLAN_ROW_RSSET || row->kind == M68K_RENDER_PLAN_ROW_RS_FIELD) return 1;
  if (row->kind == M68K_RENDER_PLAN_ROW_EQUATE) return 2;
  return -1;
}

static int render_plan_compare_include_rows(const M68kRenderPlanRow *left, const M68kRenderPlanRow *right) {
  const char *left_text = left != NULL && left->text != NULL ? left->text : "";
  const char *right_text = right != NULL && right->text != NULL ? right->text : "";
  return strcmp(left_text, right_text);
}

static void render_plan_recompute_layout(M68kRenderPlan *plan) {
  size_t index;
  uint32_t total_lines = 0U;
  size_t total_bytes = 0U;
  if (plan == NULL) return;
  for (index = 0U; index < plan->row_count; ++index) {
    M68kRenderPlanRow *row = &plan->rows[index];
    row->start_line = total_lines;
    row->start_byte = total_bytes;
    total_lines += row->line_count;
    total_bytes += row->byte_count;
  }
  plan->total_lines = total_lines;
  plan->total_bytes = total_bytes;
}

int m68k_render_plan_hoist_header_rows(M68kRenderPlan *plan) {
  Arena *arena;
  ArenaMark mark;
  M68kRenderPlanRow *ordered;
  size_t out_index = 0U;
  size_t row_index;
  int group;
  if (plan == NULL) return -1;
  if (plan->row_count == 0U) return 0;
  if (plan->row_count > ((size_t)-1) / sizeof(*ordered)) return -1;
  arena = render_plan_arena(plan);
  if (arena == NULL) return -1;
  mark = arena_mark(arena);
  ordered = (M68kRenderPlanRow *)arena_alloc(arena, plan->row_count * sizeof(*ordered));
  if (ordered == NULL) return -1;
  for (group = 0; group <= 2; ++group) {
    if (group == 0) {
      size_t include_start = out_index;
      size_t scan;
      for (row_index = 0U; row_index < plan->row_count; ++row_index) {
        if (render_plan_row_header_group(&plan->rows[row_index]) == group)
          ordered[out_index++] = plan->rows[row_index];
      }
      for (row_index = include_start + 1U; row_index < out_index; ++row_index) {
        M68kRenderPlanRow row = ordered[row_index];
        scan = row_index;
        while (scan > include_start && render_plan_compare_include_rows(&ordered[scan - 1U], &row) > 0) {
          ordered[scan] = ordered[scan - 1U];
          --scan;
        }
        ordered[scan] = row;
      }
    } else {
      for (row_index = 0U; row_index < plan->row_count; ++row_index) {
        if (render_plan_row_header_group(&plan->rows[row_index]) == group)
          ordered[out_index++] = plan->rows[row_index];
      }
    }
  }
  for (row_index = 0U; row_index < plan->row_count; ++row_index) {
    if (render_plan_row_header_group(&plan->rows[row_index]) < 0)
      ordered[out_index++] = plan->rows[row_index];
  }
  if (out_index != plan->row_count) {
    arena_rewind(arena, mark);
    return -1;
  }
  memcpy(plan->rows, ordered, plan->row_count * sizeof(*ordered));
  arena_rewind(arena, mark);
  render_plan_recompute_layout(plan);
  return 0;
}

int m68k_render_plan_visit_row_lines(const M68kRenderPlan *plan, size_t first_row, size_t row_count,
    M68kRenderPlanLineVisitor visitor, void *user) {
  size_t row_index;
  size_t end_row;
  if (plan == NULL || visitor == NULL || first_row > plan->row_count) return -1;
  end_row = first_row + row_count;
  if (end_row < first_row || end_row > plan->row_count) end_row = plan->row_count;
  for (row_index = first_row; row_index < end_row; ++row_index) {
    const M68kRenderPlanRow *row = &plan->rows[row_index];
    const char *cursor = row->text;
    uint32_t subline = 0U;
    while (*cursor != '\0') {
      const char *line_start = cursor;
      size_t line_length;
      while (*cursor != '\0' && *cursor != '\n') ++cursor;
      if (*cursor == '\n') ++cursor;
      line_length = (size_t)(cursor - line_start);
      if (visitor(row, subline, row->start_line + subline, line_start, line_length, user) != 0) return -1;
      ++subline;
    }
  }
  return 0;
}

int m68k_render_plan_build_text_lines(const char *text, uint32_t kind, uint32_t region_id,
    M68kRenderPlan *out_plan) {
  const char *cursor;
  M68kRenderPlanRowBuilder builder;
  if (text == NULL || out_plan == NULL) return -1;
  m68k_render_plan_init(out_plan);
  m68k_render_plan_row_builder_init(&builder);
  cursor = text;
  while (*cursor != '\0') {
    const char *line_start = cursor;
    size_t line_length;
    while (*cursor != '\0' && *cursor != '\n') ++cursor;
    if (*cursor != '\n') {
      m68k_render_plan_row_builder_destroy(&builder);
      m68k_render_plan_destroy(out_plan);
      return -1;
    }
    ++cursor;
    line_length = (size_t)(cursor - line_start);
    if (m68k_render_plan_row_builder_begin(&builder, out_plan, kind, region_id) != 0 ||
        m68k_render_plan_row_builder_append_span(&builder, line_start, line_length) != 0 ||
        m68k_render_plan_row_builder_commit(&builder, NULL) != 0) {
      m68k_render_plan_row_builder_destroy(&builder);
      m68k_render_plan_destroy(out_plan);
      return -1;
    }
  }
  m68k_render_plan_row_builder_destroy(&builder);
  return 0;
}

void m68k_render_plan_free_text(char *text) {
  free(text);
}

static const char *render_plan_section_name(const M68kSectionIR *section, size_t section_index,
    size_t section_count, char *buffer, size_t buffer_size) {
  const char *name = section != NULL && section->name != NULL && section->name[0] != '\0' ? section->name : "section";
  if (buffer != NULL && buffer_size != 0U) buffer[0] = '\0';
  if ((section == NULL || section->name == NULL || section->name[0] == '\0') && section_count > 1U) {
    if (buffer == NULL || buffer_size == 0U) return name;
    snprintf(buffer, buffer_size, "%s_%u", name, (unsigned)section_index);
    return buffer;
  }
  return name;
}

static uint32_t render_plan_row_kind_for_statement(const M68kStatementIR *stmt) {
  if (stmt == NULL) return M68K_RENDER_PLAN_ROW_DIAGNOSTIC;
  if (stmt->kind == M68K_STATEMENT_LABEL) return M68K_RENDER_PLAN_ROW_LABEL;
  if (stmt->kind == M68K_STATEMENT_INSTRUCTION) return M68K_RENDER_PLAN_ROW_INSTRUCTION;
  if (stmt->kind == M68K_STATEMENT_DATA) return M68K_RENDER_PLAN_ROW_DATA;
  if (stmt->kind == M68K_STATEMENT_RESERVE) return M68K_RENDER_PLAN_ROW_RESERVE;
  return M68K_RENDER_PLAN_ROW_PLATFORM_DIRECTIVE;
}

static uint32_t render_plan_statement_source_size(const M68kStatementIR *stmt) {
  if (stmt == NULL) return 0U;
  if (stmt->source_byte_count != 0U) return stmt->source_byte_count;
  if (stmt->kind == M68K_STATEMENT_INSTRUCTION) return (uint32_t)stmt->u.instruction.byte_count;
  if (stmt->kind == M68K_STATEMENT_DATA) return (uint32_t)stmt->u.data.size;
  if (stmt->kind == M68K_STATEMENT_RESERVE) return stmt->u.reserve_size;
  return 0U;
}

int m68k_render_plan_build_source_file_body(const M68kSourceFileIR *source_file, const M68kRenderPolicy *policy,
    M68kRenderPlan *out_plan, M68kDiagSink diagnostics) {
  Arena *plan_arena;
  size_t section_index;
  if (source_file == NULL || out_plan == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_BAD_ARGUMENT,
      "bad source file render plan request");
    return -1;
  }
  m68k_render_plan_init(out_plan);
  plan_arena = render_plan_arena(out_plan);
  if (plan_arena == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
    return -1;
  }
  for (section_index = 0U; section_index < source_file->section_count; ++section_index) {
    const M68kSectionIR *section = &source_file->sections[section_index];
    size_t statement_index;
    M68kRenderPlanRow *row;
    char section_name_buffer[96];
    char section_kind_buffer[32];
    char section_line[160];
    const char *section_name = render_plan_section_name(section, section_index, source_file->section_count,
      section_name_buffer, sizeof(section_name_buffer));
    if (!m68k_format_section_spec(section->kind, section->platform_mem_type, section->platform_mem_attrs,
        section_kind_buffer, sizeof(section_kind_buffer))) {
      m68k_render_plan_destroy(out_plan);
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_RENDER_FAILED,
        "failed formatting source section");
      return -1;
    }
    if (section->size != section->data_size)
      snprintf(section_line, sizeof(section_line), "    SECTION %s,%s,$%X\n", section_name, section_kind_buffer,
        (unsigned)section->size);
    else
      snprintf(section_line, sizeof(section_line), "    SECTION %s,%s\n", section_name, section_kind_buffer);
    if (m68k_render_plan_append_text_row(out_plan, M68K_RENDER_PLAN_ROW_SECTION, (uint32_t)section_index,
        section_line, &row) != 0) {
      m68k_render_plan_destroy(out_plan);
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
      return -1;
    }
    m68k_render_plan_row_set_source_range(row, (uint32_t)section_index, 0U, 0U);
    for (statement_index = 0U; statement_index < section->statement_count; ++statement_index) {
      const M68kStatementIR *stmt = &section->statements[statement_index];
      char *stmt_text = NULL;
      uint32_t source_size;
      if (m68k_source_ir_render_statement_text_with_policy_arena(stmt, policy, plan_arena, &stmt_text,
          diagnostics) != 0) {
        m68k_render_plan_destroy(out_plan);
        return -1;
      }
      if (render_plan_append_arena_text_row(out_plan, render_plan_row_kind_for_statement(stmt),
          (uint32_t)section_index, stmt_text, &row) != 0) {
        m68k_render_plan_destroy(out_plan);
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
        return -1;
      }
      source_size = render_plan_statement_source_size(stmt);
      m68k_render_plan_row_set_source_range(row, (uint32_t)section_index, stmt->offset, source_size);
      row->has_statement = 1U;
      row->statement_index = (uint32_t)statement_index;
      m68k_render_plan_row_set_statement_metadata(row, stmt->kind,
        stmt->kind == M68K_STATEMENT_INSTRUCTION ? &stmt->u.instruction : NULL,
        stmt->source_bytes, stmt->source_byte_count);
    }
  }
  return 0;
}
