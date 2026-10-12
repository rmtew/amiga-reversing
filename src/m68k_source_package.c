#include "m68k_source_package.h"
#include "json_builder.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int overlaps(uint32_t left, uint32_t left_size, uint32_t right, uint32_t right_size) {
  return (uint64_t)left < (uint64_t)right + right_size &&
    (uint64_t)right < (uint64_t)left + left_size;
}

static int contains(const M68kRenderPlanRow *row, uint32_t offset) {
  return offset >= row->source_offset && (uint64_t)offset < (uint64_t)row->source_offset + row->source_size;
}

/* Text is consulted only to preserve comments and validate an already native-
 * classified row's layout, never to infer asset classification or boundaries. */
static int data_line(const char *line, size_t size) {
  while (size && (*line == ' ' || *line == '\t')) { ++line; --size; }
  return (size >= 5U && (!memcmp(line, "dc.b ", 5U) || !memcmp(line, "dc.w ", 5U) ||
    !memcmp(line, "dc.l ", 5U))) ||
    (size >= 6U && (!memcmp(line, "dcb.b ", 6U) || !memcmp(line, "dcb.w ", 6U) ||
    !memcmp(line, "dcb.l ", 6U)));
}

/* Numeric dc/dcb payloads only. A native expression projection should already
 * exclude symbolic uses; this rejection guard also protects render spellings
 * that are not yet represented in that projection. */
static int plain_data_line(const char *line, size_t size) {
  const char *end = line + size;
  if (!data_line(line, size)) return 0;
  while (line < end && (*line == ' ' || *line == '\t')) ++line;
  while (line < end && *line != ' ') ++line;
  for (;;) {
    const char *digits;
    while (line < end && (*line == ' ' || *line == '\t')) ++line;
    if (line < end && (*line == '-' || *line == '+')) ++line;
    if (line < end && *line == '$') {
      digits = ++line;
      while (line < end && ((*line >= '0' && *line <= '9') ||
          (*line >= 'a' && *line <= 'f') || (*line >= 'A' && *line <= 'F'))) ++line;
    } else {
      digits = line;
      while (line < end && *line >= '0' && *line <= '9') ++line;
    }
    if (line == digits) return 0;
    while (line < end && (*line == ' ' || *line == '\t' || *line == '\r')) ++line;
    if (line == end || *line == ';') return 1;
    if (*line++ != ',') return 0;
  }
}

static int eligible(const M68kObject *object, const M68kRenderPlan *plan,
    const M68kRenderPlanRow *row, uint32_t minimum) {
  const M68kSection *section;
  size_t index;
  const char *cursor;
  unsigned line_index = 0U;
  int saw_data = 0;
  if (row->kind != M68K_RENDER_PLAN_ROW_DATA || !row->has_statement_metadata ||
      row->statement_kind != M68K_STATEMENT_DATA || !row->has_source_range ||
      row->source_size < minimum || row->source_section_index >= object->section_count ||
      row->label_line_mask || !row->text ||
      (row->data_class_flags != M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP &&
       row->data_class_flags != M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SOUND_SAMPLE)) return 0;
  section = &object->sections[row->source_section_index];
  if (section->kind == M68K_SECTION_BSS || !section->data ||
      row->source_offset > section->data_size || row->source_size > section->data_size - row->source_offset ||
      row->source_offset > section->size || row->source_size > section->size - row->source_offset) return 0;
  for (index = 0; index < object->fixup_count; ++index) {
    const M68kFixup *fixup = &object->fixups[index];
    if (fixup->section_index == row->source_section_index &&
        overlaps(row->source_offset, row->source_size, fixup->offset, (uint32_t)fixup->width)) return 0;
  }
  for (index = 0; index < plan->expression_count; ++index) {
    const M68kRenderPlannedExpression *expression = &plan->expressions[index];
    if (expression->source_section_index == row->source_section_index && contains(row, expression->source_offset))
      return 0;
  }
  for (index = 0; index < plan->label_count; ++index) {
    const M68kRenderPlannedLabel *label = &plan->labels[index];
    if (label->source_section_index == row->source_section_index &&
        label->source_offset != row->source_offset && contains(row, label->source_offset)) return 0;
  }
  for (index = 0; index < plan->row_count; ++index) {
    const M68kRenderPlanRow *other = &plan->rows[index];
    if (other != row && other->has_source_range && other->source_section_index == row->source_section_index &&
        overlaps(row->source_offset, row->source_size, other->source_offset, other->source_size)) return 0;
  }
  cursor = row->text;
  while (*cursor) {
    const char *end = strchr(cursor, '\n');
    const char *trim = cursor;
    size_t length;
    if (!end) return 0;
    length = (size_t)(end - cursor);
    while (trim < end && (*trim == ' ' || *trim == '\t' || *trim == '\r')) ++trim;
    if (line_index < 32U && (row->directive_line_mask & (1U << line_index))) {
      /* Moving an interior ORG past an INCBIN would change addresses. */
      if (saw_data) return 0;
    } else if (trim < end && *trim != ';') {
      if (!plain_data_line(cursor, length)) return 0;
      saw_data = 1;
    }
    ++line_index;
    cursor = end + 1;
  }
  return saw_data;
}

static int append_asset_source(JsonBuilder *source, const M68kRenderPlanRow *row, const char *path, int *emitted) {
  const char *cursor = row->text;
  while (*cursor) {
    const char *end = strchr(cursor, '\n');
    size_t length = (size_t)(end - cursor) + 1U;
    if (data_line(cursor, length)) {
      const char *comment = memchr(cursor, ';', length);
      if (!*emitted && json_builder_appendf(source, "\tINCBIN \"%s\"\n", path) != 0) return -1;
      *emitted = 1;
      if (comment && json_builder_append_len(source, comment, length - (size_t)(comment - cursor)) != 0) return -1;
    } else if (json_builder_append_len(source, cursor, length) != 0) return -1;
    cursor = end + 1;
  }
  return 0;
}

static int joins_asset_run(const M68kRenderPlan *plan, const M68kRenderPlanRow *first,
    uint32_t size, const M68kRenderPlanRow *next) {
  size_t index;
  if (next->source_section_index != first->source_section_index ||
      next->data_class_flags != first->data_class_flags || next->region_id != first->region_id ||
      (uint64_t)first->source_offset + size != next->source_offset ||
      (uint64_t)size + next->source_size > UINT32_MAX || next->directive_line_mask != 0U) return 0;
  /* A label at the next row's start is not interior to that row, but would
   * become interior to the combined asset. Preserve this native boundary. */
  for (index = 0U; index < plan->label_count; ++index)
    if (plan->labels[index].source_section_index == next->source_section_index &&
        plan->labels[index].source_offset == next->source_offset) return 0;
  return 1;
}

int m68k_source_package_json_alloc(const M68kObject *object, const M68kRenderPlan *plan,
    uint32_t minimum_asset_size, char **out_json) {
  JsonBuilder source = {0}, assets = {0}, result = {0};
  char *source_text = NULL;
  uint8_t *eligible_rows = NULL;
  size_t index, count = 0U;
  int status = -1;
  if (!out_json) return -1;
  *out_json = NULL;
  if (!object || !plan || minimum_asset_size == 0U) return -1;
  if (json_builder_create(&source) || json_builder_create(&assets) || json_builder_create(&result)) goto done;
  eligible_rows = (uint8_t *)calloc(plan->row_count ? plan->row_count : 1U, 1U);
  if (!eligible_rows) goto done;
  for (index = 0U; index < plan->row_count; ++index)
    eligible_rows[index] = (uint8_t)eligible(object, plan, &plan->rows[index], 1U);
  for (index = 0U; index < plan->row_count; ++index) {
    const M68kRenderPlanRow *row = &plan->rows[index];
    size_t end = index + 1U, run_index;
    uint32_t run_size = row->source_size;
    if (eligible_rows[index]) {
      while (end < plan->row_count && eligible_rows[end] &&
          joins_asset_run(plan, row, run_size, &plan->rows[end])) {
        run_size += plan->rows[end].source_size;
        ++end;
      }
    }
    if (eligible_rows[index] && run_size >= minimum_asset_size) {
      char path[96];
      uint32_t byte_index;
      int emitted = 0;
      const uint8_t *bytes = object->sections[row->source_section_index].data + row->source_offset;
      const char *classification = row->data_class_flags == M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP
        ? "bitmap" : "sound_sample";
      snprintf(path, sizeof(path), "assets/section-%04u-offset-%08x-size-%08x.bin",
        (unsigned)row->source_section_index, (unsigned)row->source_offset, (unsigned)run_size);
      for (run_index = index; run_index < end; ++run_index)
        if (append_asset_source(&source, &plan->rows[run_index], path, &emitted) != 0) goto done;
      if ((count && json_builder_append(&assets, ",") != 0) ||
          json_builder_appendf(&assets, "{\"path\":\"%s\",\"source_section_index\":%u,\"source_offset\":%u,"
            "\"size\":%u,\"classification\":\"%s\",\"data_class_flags\":%u,\"source_row_id\":%u,\"source_row_count\":%u,\"data_hex\":\"",
            path, (unsigned)row->source_section_index, (unsigned)row->source_offset, (unsigned)run_size,
            classification, (unsigned)row->data_class_flags, (unsigned)row->id, (unsigned)(end - index)) != 0) goto done;
      for (byte_index = 0; byte_index < run_size; ++byte_index)
        if (json_builder_appendf(&assets, "%02x", bytes[byte_index]) != 0) goto done;
      if (json_builder_append(&assets, "\"}") != 0) goto done;
      ++count;
    } else {
      for (run_index = index; run_index < end; ++run_index)
        if (!plan->rows[run_index].text || json_builder_append(&source, plan->rows[run_index].text) != 0) goto done;
    }
    index = end - 1U;
  }
  source_text = json_builder_build(&source);
  if (!source_text || json_builder_append(&result, "{\"source_text\":") ||
      json_builder_append_json_string(&result, source_text) || json_builder_append(&result, ",\"assets\":[") ||
      json_builder_append_builder(&result, &assets) || json_builder_append(&result, "]}")) goto done;
  *out_json = json_builder_build(&result);
  status = *out_json ? 0 : -1;
done:
  free(eligible_rows);
  free(source_text);
  json_builder_destroy(&source);
  json_builder_destroy(&assets);
  json_builder_destroy(&result);
  return status;
}
