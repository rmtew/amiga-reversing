#include "m68k_render_plan.h"

#include "m68k_source_ir_render.h"
#include "m68k_source_text_util.h"

#include <stdio.h>
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
  size_t section_index;
  if (source_file == NULL || out_plan == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_BAD_ARGUMENT,
      "bad source file render plan request");
    return -1;
  }
  m68k_render_plan_init(out_plan);
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
      if (m68k_source_ir_render_statement_text_with_policy(stmt, policy, &stmt_text, diagnostics) != 0) {
        m68k_render_plan_destroy(out_plan);
        return -1;
      }
      if (m68k_render_plan_append_text_row(out_plan, render_plan_row_kind_for_statement(stmt),
          (uint32_t)section_index, stmt_text, &row) != 0) {
        free(stmt_text);
        m68k_render_plan_destroy(out_plan);
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
        return -1;
      }
      source_size = render_plan_statement_source_size(stmt);
      m68k_render_plan_row_set_source_range(row, (uint32_t)section_index, stmt->offset, source_size);
      free(stmt_text);
    }
  }
  return 0;
}
