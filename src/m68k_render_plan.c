#include "m68k_render_plan.h"

#include <stdlib.h>
#include <string.h>

static char *render_plan_strdup(const char *text) {
  size_t size;
  char *copy;
  if (text == NULL) return NULL;
  size = strlen(text) + 1U;
  copy = (char *)malloc(size);
  if (copy == NULL) return NULL;
  memcpy(copy, text, size);
  return copy;
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
  M68kRenderPlanRow *rows;
  size_t capacity;
  if (plan == NULL) return -1;
  if (needed <= plan->row_capacity) return 0;
  capacity = plan->row_capacity != 0U ? plan->row_capacity : 8U;
  while (capacity < needed) {
    if (capacity > ((size_t)-1) / 2U) return -1;
    capacity *= 2U;
  }
  rows = (M68kRenderPlanRow *)realloc(plan->rows, capacity * sizeof(*rows));
  if (rows == NULL) return -1;
  plan->rows = rows;
  plan->row_capacity = capacity;
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
  size_t index;
  if (plan == NULL) return;
  for (index = 0U; index < plan->row_count; ++index) free(plan->rows[index].text);
  free(plan->rows);
  memset(plan, 0, sizeof(*plan));
}

int m68k_render_plan_append_text_row(M68kRenderPlan *plan, uint32_t kind, uint32_t region_id,
    const char *text, M68kRenderPlanRow **out_row) {
  M68kRenderPlanRow *row;
  uint32_t line_count = render_plan_count_lines(text);
  size_t byte_count;
  char *text_copy;
  if (out_row != NULL) *out_row = NULL;
  if (plan == NULL || line_count == 0U || !render_plan_text_has_complete_lines(text)) return -1;
  if (UINT32_MAX - plan->total_lines < line_count) return -1;
  byte_count = strlen(text);
  if (((size_t)-1) - plan->total_bytes < byte_count) return -1;
  text_copy = render_plan_strdup(text);
  if (text_copy == NULL) return -1;
  if (render_plan_reserve_rows(plan, plan->row_count + 1U) != 0) {
    free(text_copy);
    return -1;
  }
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
  row->text = text_copy;
  plan->total_lines += line_count;
  plan->total_bytes += byte_count;
  if (out_row != NULL) *out_row = row;
  return 0;
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
    size_t length = strlen(plan->rows[index].text);
    if (total_size > ((size_t)-1) - length) return -1;
    total_size += length;
  }
  text = (char *)malloc(total_size);
  if (text == NULL) return -1;
  cursor = text;
  for (index = first_row; index < end_row; ++index) {
    size_t length = strlen(plan->rows[index].text);
    memcpy(cursor, plan->rows[index].text, length);
    cursor += length;
  }
  *cursor = '\0';
  *out_text = text;
  return 0;
}

int m68k_render_plan_emit_all_alloc(const M68kRenderPlan *plan, char **out_text) {
  if (plan == NULL) return -1;
  return m68k_render_plan_emit_rows_alloc(plan, 0U, plan->row_count, out_text);
}

void m68k_render_plan_free_text(char *text) {
  free(text);
}
