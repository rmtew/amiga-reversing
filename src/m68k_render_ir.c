#include "m68k_render_lookup_internal.h"

#include "m68k_assembler.h"
#include "m68k_bitset.h"
#include "m68k_disassembler.h"
#include "m68k_instruction_spec.h"
#include "m68k_ir.h"
#include "m68k_ir_codec.h"
#include "m68k_parse_util.h"
#include "m68k_plain_parse.h"
#include "m68k_simulator.h"
#include "m68k_source_model.h"
#include "m68k_source_pipeline.h"
#include "m68k_source_text_util.h"
#include "platform_atari_st.h"
#include "platform_common.h"
#include "util_arena.h"
#include "generated/amiga_hunk_file_runtime.h"
#include "generated/m68k_cpu_runtime.h"
#include "generated/amiga_os_runtime.h"
#include "generated/mac_os_runtime.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <time.h>


static const char *manual_representation_symbol_name(const M68kRenderLookup *lookup,
    const M68kAnalysisManualRepresentation *representation);
static void render_asm_dc_symbol_expr(M68kRenderIRPreview *preview, uint32_t size, const char *expr,
    const char *comment);
static void render_lookup_set_label(M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
static const M68kFact *lookup_anchor_at(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t offset);
static int lookup_storage_label_has_inbound_target_ref(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset);
static const M68kSectionAnalysisIR *source_analysis_section_for_render(const M68kSourceAnalysisIR *source_analysis,
    size_t section_index);
static int attach_platform_semantic_note_comment_for_render(const M68kSourceAnalysisIR *source_analysis,
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset, char *comment, size_t comment_size);
static int attach_platform_semantic_kind_note_comment_for_render(const M68kSourceAnalysisIR *source_analysis,
    size_t section_index, uint32_t offset, uint8_t kind, char *comment, size_t comment_size);

static double elapsed_seconds_local(clock_t start, clock_t end) {
  return (double)(end - start) / (double)CLOCKS_PER_SEC;
}

char ascii_lower_local(char c) {
  return (c >= 'A' && c <= 'Z') ? (char)(c - 'A' + 'a') : c;
}

int ascii_char_is_symbol_local(char c, int first) {
  if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || c == '_' || c == '.') return 1;
  if (!first && c >= '0' && c <= '9') return 1;
  return 0;
}

int asm_symbol_name_is_safe_local(const char *name) {
  size_t index;
  if (name == NULL || name[0] == '\0') return 0;
  for (index = 0U; name[index] != '\0'; ++index) {
    if (!ascii_char_is_symbol_local(name[index], index == 0U)) return 0;
  }
  return 1;
}

int ascii_contains_case_local(const char *text, const char *needle) {
  size_t text_index;
  size_t needle_len;
  if (text == NULL || needle == NULL || needle[0] == '\0') return 0;
  needle_len = strlen(needle);
  for (text_index = 0U; text[text_index] != '\0'; ++text_index) {
    size_t needle_index;
    for (needle_index = 0U; needle_index < needle_len; ++needle_index) {
      if (text[text_index + needle_index] == '\0') return 0;
      if (ascii_lower_local(text[text_index + needle_index]) != ascii_lower_local(needle[needle_index])) break;
    }
    if (needle_index == needle_len) return 1;
  }
  return 0;
}

static uint64_t hash_step(uint64_t hash, uint64_t value) {
  hash ^= value;
  hash *= 1099511628211ULL;
  return hash;
}

static void hash_statement(M68kRenderIRPreview *preview, uint8_t kind, size_t section_index, uint32_t offset,
    uint32_t size, uint32_t aux) {
  preview->structural_hash = hash_step(preview->structural_hash, kind);
  preview->structural_hash = hash_step(preview->structural_hash, (uint64_t)section_index);
  preview->structural_hash = hash_step(preview->structural_hash, offset);
  preview->structural_hash = hash_step(preview->structural_hash, size);
  preview->structural_hash = hash_step(preview->structural_hash, aux);
}

static void render_text_line(M68kRenderIRPreview *preview, char kind, size_t section_index, uint32_t offset,
    uint32_t size, uint32_t aux) {
  char line[96];
  int length;
  size_t index;
  if (preview == NULL) return;
  length = snprintf(line, sizeof(line), "%c %u %08X %u %u\n", kind, (unsigned)section_index,
    (unsigned)offset, (unsigned)size, (unsigned)aux);
  if (length <= 0) return;
  preview->text_bytes += (uint32_t)length;
  for (index = 0U; index < (size_t)length && index < sizeof(line); ++index)
    preview->text_hash = hash_step(preview->text_hash, (unsigned char)line[index]);
}

static void hash_asm_text(M68kRenderIRPreview *preview, const char *text) {
  size_t index;
  size_t length;
  if (preview == NULL || text == NULL) return;
  length = strlen(text);
  if (preview->collect_asm_source_text) {
    if (length > (size_t)UINT32_MAX - (size_t)preview->asm_source_bytes) {
      preview->asm_source_allocation_failed = 1U;
    } else if (!preview->asm_source_row_builder.active) {
      preview->asm_source_allocation_failed = 1U;
    }
  }
  if (preview->collect_asm_source_hash) {
    for (index = 0U; index < length; ++index)
      preview->asm_source_hash = hash_step(preview->asm_source_hash, (unsigned char)text[index]);
  }
  if (preview->asm_source_row_builder.active &&
      m68k_render_plan_row_builder_append_span(&preview->asm_source_row_builder, text, length) != 0) {
    preview->asm_source_allocation_failed = 1U;
  }
  preview->asm_source_bytes += (uint32_t)length;
}

static int flush_transient_asm_source_row(M68kRenderIRPreview *preview) {
  if (preview == NULL || !preview->transient_row_live) return 0;
  if (preview->transient_row_sink == NULL ||
      preview->transient_row_sink(&preview->transient_row, preview->transient_row_sink_user) != 0) {
    return -1;
  }
  memset(&preview->transient_row, 0, sizeof(preview->transient_row));
  preview->transient_row_live = 0U;
  return 0;
}

static void begin_asm_source_plan_row(M68kRenderIRPreview *preview, uint32_t kind, uint32_t region_id) {
  if (preview == NULL || !preview->collect_asm_source_text || preview->asm_source_row_builder.active) return;
  if (flush_transient_asm_source_row(preview) != 0) {
    preview->asm_source_allocation_failed = 1U;
    return;
  }
  if (m68k_render_plan_row_builder_begin(&preview->asm_source_row_builder, &preview->asm_source_rows,
      kind, region_id) != 0) {
    preview->asm_source_allocation_failed = 1U;
  }
}

static M68kRenderPlanRow *finish_asm_source_plan_row(M68kRenderIRPreview *preview, size_t section_index,
    uint32_t source_offset, uint32_t source_size, int has_source_range) {
  M68kRenderPlanRow *row = NULL;
  if (preview == NULL || !preview->asm_source_row_builder.active) return NULL;
  if (preview->asm_source_row_builder.size == 0U) {
    m68k_render_plan_row_builder_cancel(&preview->asm_source_row_builder);
    return NULL;
  }
  if (preview->transient_row_sink != NULL) {
    M68kRenderPlanRowBuilder *builder = &preview->asm_source_row_builder;
    memset(&preview->transient_row, 0, sizeof(preview->transient_row));
    preview->transient_row.kind = builder->kind;
    preview->transient_row.region_id = builder->region_id;
    preview->transient_row.start_line = preview->asm_source_lines;
    preview->transient_row.line_count = builder->current_line;
    preview->transient_row.start_byte = preview->asm_source_bytes - builder->size;
    preview->transient_row.byte_count = builder->size;
    preview->transient_row.directive_line_mask = builder->directive_line_mask;
    preview->transient_row.source_line_mask = builder->source_line_mask;
    memcpy(preview->transient_row.source_line_offsets, builder->source_line_offsets,
      sizeof(preview->transient_row.source_line_offsets));
    memcpy(preview->transient_row.source_line_sizes, builder->source_line_sizes,
      sizeof(preview->transient_row.source_line_sizes));
    preview->transient_row.label_line_mask = builder->label_line_mask;
    memcpy(preview->transient_row.label_line_source_offsets, builder->label_line_source_offsets,
      sizeof(preview->transient_row.label_line_source_offsets));
    preview->transient_row.label_line_runtime_mask = builder->label_line_runtime_mask;
    memcpy(preview->transient_row.label_line_runtime_addresses, builder->label_line_runtime_addresses,
      sizeof(preview->transient_row.label_line_runtime_addresses));
    preview->transient_row.text = builder->text;
    preview->transient_row_live = 1U;
    preview->asm_source_lines += builder->current_line;
    builder->active = 0U;
    builder->plan = NULL;
    row = &preview->transient_row;
  } else if (m68k_render_plan_row_builder_commit(&preview->asm_source_row_builder, &row) != 0) {
    preview->asm_source_allocation_failed = 1U;
    return NULL;
  }
  if (has_source_range && row != NULL) {
    m68k_render_plan_row_set_source_range(row, (uint32_t)section_index, source_offset, source_size);
  }
  return row;
}

static void cancel_asm_source_plan_row(M68kRenderIRPreview *preview) {
  if (preview == NULL || !preview->asm_source_row_builder.active) return;
  m68k_render_plan_row_builder_cancel(&preview->asm_source_row_builder);
}

static void set_asm_source_plan_row_statement_from_section(M68kRenderPlanRow *row, uint8_t statement_kind,
    const M68kInstructionIR *instruction, const M68kDecodeSectionIR *section, uint32_t offset, uint32_t size) {
  const uint8_t *source_bytes = NULL;
  size_t source_byte_count = 0U;
  if (row == NULL) return;
  if (section != NULL && section->data != NULL && size != 0U && offset < section->size) {
    source_byte_count = size;
    if (source_byte_count > section->size - offset) source_byte_count = section->size - offset;
    source_bytes = section->data + offset;
  }
  m68k_render_plan_row_set_statement_metadata(row, statement_kind, instruction, source_bytes, source_byte_count);
}

static int asm_source_symbol_is_declared_equate(const M68kRenderIRPreview *preview, const char *symbol_name) {
  size_t index;
  if (preview == NULL || symbol_name == NULL || symbol_name[0] == '\0') return 0;
  for (index = 0U; index < preview->asm_source_plan.declaration_count; ++index) {
    const M68kRenderPlannedDeclaration *declaration = &preview->asm_source_plan.declarations[index];
    if (declaration->kind == M68K_RENDER_PLANNED_DECLARATION_EQUATE &&
        strcmp(declaration->name, symbol_name) == 0) {
      return 1;
    }
  }
  return 0;
}

static Arena *render_preview_scratch_arena(M68kRenderIRPreview *preview) {
  if (preview == NULL) return NULL;
  if (preview->scratch_arena == NULL) {
    preview->scratch_arena = arena_create(4096U);
    if (preview->scratch_arena == NULL) return NULL;
  }
  return preview->scratch_arena;
}

static void recompute_asm_source_plan_metrics(M68kRenderIRPreview *preview, const M68kRenderPlan *plan);
static int asm_source_plan_row_is_late_header(const M68kRenderPlanRow *row, size_t body_start_byte);

static void copy_asm_source_plan_row_metadata(M68kRenderPlanRow *row, const M68kRenderPlanRow *source) {
  if (row == NULL || source == NULL) return;
  row->directive_line_mask = source->directive_line_mask;
  row->label_line_mask = source->label_line_mask;
  memcpy(row->label_line_source_offsets, source->label_line_source_offsets,
    sizeof(row->label_line_source_offsets));
  row->label_line_runtime_mask = source->label_line_runtime_mask;
  memcpy(row->label_line_runtime_addresses, source->label_line_runtime_addresses,
    sizeof(row->label_line_runtime_addresses));
  if (source->data_class_flags != 0U) m68k_render_plan_row_set_data_class_flags(row, source->data_class_flags);
  memcpy(row->generated_field_comment, source->generated_field_comment, sizeof(row->generated_field_comment));
  if (source->has_source_range)
    m68k_render_plan_row_set_source_range(row, source->source_section_index, source->source_offset,
      source->source_size);
  if (source->has_runtime_range)
    m68k_render_plan_row_set_runtime_range(row, source->runtime_address, source->runtime_size);
  if (source->has_statement) {
    row->has_statement = 1U;
    row->statement_index = source->statement_index;
  }
  if (source->has_statement_metadata) {
    m68k_render_plan_row_set_statement_metadata(row, source->statement_kind,
      source->statement_kind == M68K_STATEMENT_INSTRUCTION ? &source->statement_instruction : NULL,
      source->source_bytes, source->source_byte_count);
  }
}

static int data_plan_parse_unsigned_expr(const char *text, size_t length, uint32_t *out_value) {
  char buffer[32];
  M68kParseU32Result parsed;
  while (length != 0U && (*text == ' ' || *text == '\t')) {
    ++text;
    --length;
  }
  while (length != 0U && (text[length - 1U] == ' ' || text[length - 1U] == '\t')) --length;
  if (length == 0U || length >= sizeof(buffer)) return 0;
  memcpy(buffer, text, length);
  buffer[length] = '\0';
  parsed = m68k_parse_number_u32(buffer);
  if (!parsed.ok) return 0;
  if (out_value != NULL) *out_value = parsed.value;
  return 1;
}

static int data_plan_line_dc_source_size(const char *cursor, const char *line_end, uint32_t width,
    uint32_t *out_size) {
  uint32_t size = 0U;
  int saw_value = 0;
  if (cursor == NULL || line_end == NULL || out_size == NULL || width == 0U) return 0;
  while (cursor < line_end) {
    while (cursor < line_end && (*cursor == ' ' || *cursor == '\t')) ++cursor;
    if (cursor >= line_end || *cursor == ';') break;
    saw_value = 1;
    if (*cursor == '"') {
      ++cursor;
      while (cursor < line_end && *cursor != '"') {
        if (width != 1U || size > UINT32_MAX - 1U) return 0;
        ++size;
        ++cursor;
      }
      if (cursor >= line_end || *cursor != '"') return 0;
      ++cursor;
    } else {
      if (size > UINT32_MAX - width) return 0;
      size += width;
      while (cursor < line_end && *cursor != ',' && *cursor != ';') ++cursor;
    }
    while (cursor < line_end && (*cursor == ' ' || *cursor == '\t')) ++cursor;
    if (cursor < line_end && *cursor == ',') {
      ++cursor;
      continue;
    }
    if (cursor < line_end && *cursor == ';') break;
    if (cursor < line_end) return 0;
  }
  if (!saw_value) return 0;
  *out_size = size;
  return 1;
}

static int data_plan_line_dcb_source_size(const char *cursor, const char *line_end, uint32_t width,
    uint32_t *out_size) {
  const char *repeat_start;
  uint32_t repeat = 0U;
  if (cursor == NULL || line_end == NULL || out_size == NULL || width == 0U) return 0;
  while (cursor < line_end && (*cursor == ' ' || *cursor == '\t')) ++cursor;
  repeat_start = cursor;
  while (cursor < line_end && *cursor != ',' && *cursor != ';') ++cursor;
  if (cursor >= line_end || *cursor != ',') return 0;
  if (!data_plan_parse_unsigned_expr(repeat_start, (size_t)(cursor - repeat_start), &repeat)) return 0;
  if (repeat > UINT32_MAX / width) return 0;
  *out_size = repeat * width;
  return 1;
}

static int data_plan_line_source_size(const char *line_start, size_t line_length, uint32_t *out_size) {
  const char *cursor;
  const char *line_end;
  uint32_t width;
  int dcb = 0;
  if (out_size != NULL) *out_size = 0U;
  if (line_start == NULL || out_size == NULL) return 0;
  cursor = line_start;
  line_end = line_start + line_length;
  while (cursor < line_end && (*cursor == ' ' || *cursor == '\t')) ++cursor;
  while (line_end > cursor && (line_end[-1] == ' ' || line_end[-1] == '\t')) --line_end;
  if (cursor >= line_end || *cursor == ';') return 1;
  if (line_end[-1] == ':') return 1;
  if (line_end - cursor >= 5 && cursor[0] == 'd' && cursor[1] == 'c' && cursor[2] == 'b' && cursor[3] == '.') {
    dcb = 1;
    cursor += 4;
  } else if (line_end - cursor >= 4 && cursor[0] == 'd' && cursor[1] == 'c' && cursor[2] == '.') {
    cursor += 3;
  } else {
    return 0;
  }
  switch (*cursor) {
  case 'b': width = 1U; break;
  case 'w': width = 2U; break;
  case 'l': width = 4U; break;
  default: return 0;
  }
  ++cursor;
  return dcb
    ? data_plan_line_dcb_source_size(cursor, line_end, width, out_size)
    : data_plan_line_dc_source_size(cursor, line_end, width, out_size);
}

static int asm_source_plan_data_row_has_split_source_lines(const M68kRenderPlanRow *source) {
  const char *cursor;
  uint32_t total_size = 0U;
  if (source == NULL || source->kind != M68K_RENDER_PLAN_ROW_DATA || !source->has_source_range ||
      source->line_count <= 1U || source->source_size == 0U || source->directive_line_mask != 0U ||
      source->text == NULL) {
    return 0;
  }
  cursor = source->text;
  while (*cursor != '\0') {
    const char *line_start = cursor;
    const char *line_end = strchr(cursor, '\n');
    size_t line_length;
    uint32_t line_size = 0U;
    if (line_end == NULL) return 0;
    line_length = (size_t)(line_end - line_start);
    if (!data_plan_line_source_size(line_start, line_length, &line_size)) return 0;
    if (line_size > UINT32_MAX - total_size) return 0;
    total_size += line_size;
    cursor = line_end + 1;
  }
  return total_size == source->source_size;
}

static int append_asm_source_plan_split_data_row_copies(M68kRenderPlan *dest, Arena *scratch_arena,
    const M68kRenderPlanRow *source) {
  const char *cursor;
  uint32_t consumed_size = 0U;
  uint32_t line_count = 0U;
  if (dest == NULL || scratch_arena == NULL || source == NULL || source->text == NULL)
    return 0;
  cursor = source->text;
  while (*cursor != '\0') {
    const char *line_start = cursor;
    const char *line_end = strchr(cursor, '\n');
    size_t line_length;
    size_t content_length;
    uint32_t line_size = 0U;
    ArenaMark mark;
    char *line_text;
    M68kRenderPlanRow *row = NULL;
    if (line_end == NULL) return 0;
    content_length = (size_t)(line_end - line_start);
    if (!data_plan_line_source_size(line_start, content_length, &line_size)) return 0;
    line_length = (size_t)(line_end - line_start) + 1U;
    mark = arena_mark(scratch_arena);
    line_text = (char *)arena_alloc(scratch_arena, line_length + 1U);
    if (line_text == NULL) return 0;
    memcpy(line_text, line_start, line_length);
    line_text[line_length] = '\0';
    if (m68k_render_plan_append_text_row(dest, source->kind, source->region_id, line_text, &row) != 0) {
      arena_rewind(scratch_arena, mark);
      return 0;
    }
    arena_rewind(scratch_arena, mark);
    copy_asm_source_plan_row_metadata(row, source);
    m68k_render_plan_row_set_source_range(row, source->source_section_index,
      source->source_offset + consumed_size, line_size);
    memset(row->source_line_offsets, 0, sizeof(row->source_line_offsets));
    memset(row->source_line_sizes, 0, sizeof(row->source_line_sizes));
    memset(row->label_line_source_offsets, 0, sizeof(row->label_line_source_offsets));
    memset(row->label_line_runtime_addresses, 0, sizeof(row->label_line_runtime_addresses));
    row->directive_line_mask = (line_count < 32U && (source->directive_line_mask & (1U << line_count)) != 0U)
      ? 1U : 0U;
    row->source_line_mask = 1U;
    row->source_line_offsets[0] = source->source_offset + consumed_size;
    row->source_line_sizes[0] = line_size;
    row->label_line_mask = 0U;
    row->label_line_runtime_mask = 0U;
    if (line_count < 32U && (source->label_line_mask & (1U << line_count)) != 0U) {
      row->label_line_mask = 1U;
      row->label_line_source_offsets[0] = source->label_line_source_offsets[line_count];
      if ((source->label_line_runtime_mask & (1U << line_count)) != 0U) {
        row->label_line_runtime_mask = 1U;
        row->label_line_runtime_addresses[0] = source->label_line_runtime_addresses[line_count];
      }
    }
    if (source->has_statement_metadata && source->statement_kind == M68K_STATEMENT_DATA) {
      const uint8_t *line_bytes = NULL;
      uint32_t line_byte_count = 0U;
      if (line_size != 0U && line_size <= M68K_STATEMENT_SOURCE_BYTES_MAX &&
          source->source_byte_count >= consumed_size + line_size) {
        line_bytes = source->source_bytes + consumed_size;
        line_byte_count = line_size;
      }
      m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_DATA, NULL, line_bytes, line_byte_count);
    }
    consumed_size += line_size;
    ++line_count;
    cursor = line_end + 1;
  }
  return line_count == source->line_count && consumed_size == source->source_size;
}

static int append_asm_source_plan_row_copy(M68kRenderPlan *dest, Arena *scratch_arena,
    const M68kRenderPlanRow *source) {
  M68kRenderPlanRow *row = NULL;
  if (dest == NULL || source == NULL) return 0;
  if (asm_source_plan_data_row_has_split_source_lines(source))
    return append_asm_source_plan_split_data_row_copies(dest, scratch_arena, source);
  if (m68k_render_plan_append_text_row(dest, source->kind, source->region_id, source->text, &row) != 0)
    return 0;
  copy_asm_source_plan_row_metadata(row, source);
  return 1;
}

/* Emit dependencies before consumers while retaining alphabetical root order.
 * Literal text must not be mistaken for a symbol dependency. */
static int append_planned_equate(M68kRenderPlan *dest, const M68kRenderPlan *source,
    size_t index, uint8_t *states, uint32_t row_kind, uint32_t *count) {
  const M68kRenderPlannedDeclaration *item = &source->declarations[index];
  const char *cursor = item->expression;
  char line[224];
  M68kRenderPlanRow *emitted_row = NULL;
  int length;
  if (states[index] == 2U) return 1;
  if (states[index] == 1U) return 0;
  states[index] = 1U;
  while (*cursor != '\0') {
    const char *start;
    size_t token_length, dependency;
    if (*cursor == '\'' || *cursor == '"') {
      char quote = *cursor++;
      while (*cursor != '\0' && *cursor != quote) ++cursor;
      if (*cursor != '\0') ++cursor;
      continue;
    }
    if (*cursor == '$' || *cursor == '%' || (*cursor >= '0' && *cursor <= '9')) {
      ++cursor;
      while (ascii_char_is_symbol_local(*cursor, 0)) ++cursor;
      continue;
    }
    if (!ascii_char_is_symbol_local(*cursor, 1)) { ++cursor; continue; }
    start = cursor++;
    while (ascii_char_is_symbol_local(*cursor, 0)) ++cursor;
    token_length = (size_t)(cursor - start);
    for (dependency = 0U; dependency < source->declaration_count; ++dependency) {
      const M68kRenderPlannedDeclaration *candidate = &source->declarations[dependency];
      if (candidate->kind == M68K_RENDER_PLANNED_DECLARATION_EQUATE && candidate->emits_header_text &&
          strlen(candidate->name) == token_length && strncmp(start, candidate->name, token_length) == 0 &&
          !append_planned_equate(dest, source, dependency, states, row_kind, count)) return 0;
    }
  }
  length = snprintf(line, sizeof(line), "%s\tEQU\t%s\n", item->name, item->expression);
  if (length <= 0 || (size_t)length >= sizeof(line) ||
      m68k_render_plan_append_text_row(dest, row_kind, 0U, line, &emitted_row) != 0) return 0;
  emitted_row->layout_region_index_plus_one = item->layout_region_index_plus_one;
  states[index] = 2U;
  ++*count;
  return 1;
}

static int append_planned_header_declarations(M68kRenderPlan *dest, const M68kRenderPlan *source,
    uint8_t kind, uint32_t row_kind, uint32_t *out_count) {
  char previous_name[sizeof(source->declarations[0].name)];
  uint32_t count = 0U;
  int have_previous = 0;
  uint8_t *states;
  if (out_count != NULL) *out_count = 0U;
  if (dest == NULL || source == NULL) return 0;
  states = calloc(source->declaration_count + 1U, sizeof(*states));
  if (states == NULL) return 0;
  for (;;) {
    const M68kRenderPlannedDeclaration *selected = NULL;
    size_t index;
    for (index = 0U; index < source->declaration_count; ++index) {
      const M68kRenderPlannedDeclaration *candidate = &source->declarations[index];
      if (candidate->kind != kind || candidate->emits_header_text == 0U ||
          (have_previous && strcmp(candidate->name, previous_name) <= 0)) continue;
      if (selected == NULL || strcmp(candidate->name, selected->name) < 0) selected = candidate;
    }
    if (selected == NULL) break;
    if (kind == M68K_RENDER_PLANNED_DECLARATION_INCLUDE) {
      char line[128];
      int length = snprintf(line, sizeof(line), "    INCLUDE \"%s\"\n", selected->name);
      if (length <= 0 || (size_t)length >= sizeof(line) ||
          m68k_render_plan_append_text_row(dest, row_kind, 0U, line, NULL) != 0) { free(states); return 0; }
      ++count;
    } else if (kind == M68K_RENDER_PLANNED_DECLARATION_EQUATE) {
      if (!append_planned_equate(dest, source, (size_t)(selected - source->declarations),
          states, row_kind, &count)) { free(states); return 0; }
    } else {
      free(states);
      return 0;
    }
    snprintf(previous_name, sizeof(previous_name), "%s", selected->name);
    have_previous = 1;
  }
  free(states);
  if (out_count != NULL) *out_count = count;
  return 1;
}

static int assemble_asm_source_plan_regions(M68kRenderIRPreview *preview, const M68kDecodeIR *decode,
    int emit_source_text) {
  M68kRenderPlan final_plan;
  Arena *scratch_arena;
  char *source_text = NULL;
  size_t row_index;
  uint32_t include_count = 0U;
  uint32_t equate_count = 0U;
  if (preview == NULL) return 0;
  scratch_arena = render_preview_scratch_arena(preview);
  if (scratch_arena == NULL) return 0;
  if (preview->asm_source_row_builder.active) cancel_asm_source_plan_row(preview);
  if (preview->asm_source_rows.total_bytes != (size_t)preview->asm_source_bytes) return 0;
  m68k_render_plan_init(&final_plan);
  for (row_index = 0U; row_index < preview->asm_source_plan.expression_count; ++row_index) {
    if (m68k_render_plan_append_expression(&final_plan,
        &preview->asm_source_plan.expressions[row_index]) != 0) {
      m68k_render_plan_destroy(&final_plan);
      return 0;
    }
  }
  for (row_index = 0U; row_index < preview->asm_source_plan.declaration_count; ++row_index) {
    if (m68k_render_plan_append_declaration(&final_plan,
        &preview->asm_source_plan.declarations[row_index]) != 0) {
      m68k_render_plan_destroy(&final_plan);
      return 0;
    }
  }
  for (row_index = 0U; row_index < preview->asm_source_plan.instruction_count; ++row_index) {
    if (m68k_render_plan_append_instruction(&final_plan,
        &preview->asm_source_plan.instructions[row_index]) != 0) {
      m68k_render_plan_destroy(&final_plan);
      return 0;
    }
  }
  for (row_index = 0U; row_index < preview->asm_source_plan.label_count; ++row_index) {
    if (m68k_render_plan_append_label(&final_plan, &preview->asm_source_plan.labels[row_index]) != 0) {
      m68k_render_plan_destroy(&final_plan);
      return 0;
    }
  }
  for (row_index = 0U; row_index < preview->asm_source_plan.runtime_alias_count; ++row_index) {
    if (m68k_render_plan_append_runtime_alias(&final_plan,
        &preview->asm_source_plan.runtime_aliases[row_index]) != 0) {
      m68k_render_plan_destroy(&final_plan);
      return 0;
    }
  }
  for (row_index = 0U; row_index < preview->asm_source_rows.row_count; ++row_index) {
    const M68kRenderPlanRow *row = &preview->asm_source_rows.rows[row_index];
    if ((row->start_byte >= (size_t)preview->asm_source_body_start_byte &&
          !asm_source_plan_row_is_late_header(row, (size_t)preview->asm_source_body_start_byte)) ||
        row->kind != M68K_RENDER_PLAN_ROW_DIAGNOSTIC) {
      continue;
    }
    if (!append_asm_source_plan_row_copy(&final_plan, scratch_arena, row)) {
      m68k_render_plan_destroy(&final_plan);
      return 0;
    }
  }
  if (!append_planned_header_declarations(&final_plan, &preview->asm_source_plan,
      M68K_RENDER_PLANNED_DECLARATION_INCLUDE, M68K_RENDER_PLAN_ROW_INCLUDE, &include_count)) {
    m68k_render_plan_destroy(&final_plan);
    return 0;
  }
  if (include_count != 0U &&
      m68k_render_plan_append_text_row(&final_plan, M68K_RENDER_PLAN_ROW_BLANK, 0U, "\n", NULL) != 0) {
    m68k_render_plan_destroy(&final_plan);
    return 0;
  }
  for (row_index = 0U; row_index < preview->asm_source_rows.row_count; ++row_index) {
    const M68kRenderPlanRow *row = &preview->asm_source_rows.rows[row_index];
    if (row->start_byte >= (size_t)preview->asm_source_body_start_byte) continue;
    if (row->kind == M68K_RENDER_PLAN_ROW_DIAGNOSTIC) continue;
    if (!append_asm_source_plan_row_copy(&final_plan, scratch_arena, row)) {
      m68k_render_plan_destroy(&final_plan);
      return 0;
    }
  }
  if (!append_planned_header_declarations(&final_plan, &preview->asm_source_plan,
      M68K_RENDER_PLANNED_DECLARATION_EQUATE, M68K_RENDER_PLAN_ROW_EQUATE, &equate_count)) {
    m68k_render_plan_destroy(&final_plan);
    return 0;
  }
  if ((include_count != 0U || equate_count != 0U) &&
      m68k_render_plan_append_text_row(&final_plan, M68K_RENDER_PLAN_ROW_BLANK, 0U, "\n", NULL) != 0) {
    m68k_render_plan_destroy(&final_plan);
    return 0;
  }
  for (row_index = 0U; row_index < preview->asm_source_rows.row_count; ++row_index) {
    const M68kRenderPlanRow *row = &preview->asm_source_rows.rows[row_index];
    if (asm_source_plan_row_is_late_header(row, (size_t)preview->asm_source_body_start_byte)) continue;
    if (row->start_byte < (size_t)preview->asm_source_body_start_byte) continue;
    if (!append_asm_source_plan_row_copy(&final_plan, scratch_arena, row)) {
      m68k_render_plan_destroy(&final_plan);
      return 0;
    }
  }
  /* Split rows have their own canonical span; the parent's bounded byte cache
   * cannot supply later lines. Refill each data row from decoded source bytes. */
  for (row_index = 0U; decode != NULL && row_index < final_plan.row_count; ++row_index) {
    M68kRenderPlanRow *row = &final_plan.rows[row_index];
    size_t section_index;
    if (!row->has_source_range || !row->has_statement_metadata ||
        row->statement_kind != M68K_STATEMENT_DATA) continue;
    /* Unknown/no-source spans (including empty rows) carry no byte claim.
     * In particular, never retain a copied parent cache on a missing section. */
    row->source_byte_count = 0U;
    m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_DATA, NULL, NULL, 0U);
    for (section_index = 0U; section_index < decode->section_count; ++section_index) {
      const M68kDecodeSectionIR *section = &decode->sections[section_index];
      if (section->section_index != row->source_section_index) continue;
      if (section->data != NULL && row->source_offset <= section->size &&
          row->source_size <= section->size - row->source_offset) {
        m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_DATA, NULL,
          section->data + row->source_offset, row->source_size);
      }
      break;
    }
  }
  m68k_render_plan_free_text(preview->asm_source_text);
  preview->asm_source_text = NULL;
  preview->asm_source_text_capacity = 0U;
  if (emit_source_text) {
    if (m68k_render_plan_emit_all_alloc(&final_plan, &source_text) != 0) {
      m68k_render_plan_destroy(&final_plan);
      return 0;
    }
    preview->asm_source_text = source_text;
    preview->asm_source_text_capacity = final_plan.total_bytes + 1U;
  }
  if (m68k_render_plan_finalize(&final_plan) != 0) {
    m68k_render_plan_destroy(&final_plan);
    return 0;
  }
  recompute_asm_source_plan_metrics(preview, &final_plan);
  m68k_render_plan_destroy(&preview->asm_source_rows);
  m68k_render_plan_destroy(&preview->asm_source_plan);
  m68k_render_plan_move(&preview->asm_source_plan, &final_plan);
  return 1;
}

static void recompute_asm_source_plan_metrics(M68kRenderIRPreview *preview, const M68kRenderPlan *plan) {
  size_t row_index;
  if (preview == NULL || plan == NULL) return;
  preview->asm_source_bytes = 0U;
  preview->asm_source_lines = 0U;
  preview->asm_source_hash = 1469598103934665603ULL;
  for (row_index = 0U; row_index < plan->row_count; ++row_index) {
    const char *cursor = plan->rows[row_index].text;
    if (cursor == NULL) continue;
    while (*cursor != '\0') {
      if (preview->collect_asm_source_hash)
        preview->asm_source_hash = hash_step(preview->asm_source_hash, (unsigned char)*cursor);
      if (*cursor == '\n') ++preview->asm_source_lines;
      ++preview->asm_source_bytes;
      ++cursor;
    }
  }
}

static void format_asm_label(char *buf, size_t buf_size, size_t section_index, uint32_t offset) {
  if (buf == NULL || buf_size == 0U) return;
  snprintf(buf, buf_size, "loc_%u_%08X", (unsigned)section_index, (unsigned)offset);
}

static const char *lookup_policy_label_name(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint8_t domain);

static void format_runtime_asm_label(const M68kRenderLookup *lookup, char *buf, size_t buf_size,
    size_t section_index, uint32_t source_offset, uint32_t runtime_address) {
  const char *policy_name;
  if (buf == NULL || buf_size == 0U) return;
  policy_name = lookup_policy_label_name(lookup, section_index, runtime_address,
    M68K_ANALYSIS_LABEL_DOMAIN_RUNTIME);
  if (policy_name != NULL && policy_name[0] != '\0') {
    snprintf(buf, buf_size, "%s", policy_name);
    return;
  }
  if (source_offset == runtime_address) {
    format_asm_label(buf, buf_size, section_index, runtime_address);
    return;
  }
  snprintf(buf, buf_size, "abs_%u_%08X", (unsigned)section_index, (unsigned)runtime_address);
}

static uint8_t format_runtime_operand_asm_label_with_generation(const M68kRenderLookup *lookup,
    char *buf, size_t buf_size, size_t section_index, uint32_t source_offset, uint32_t runtime_address) {
  const char *policy_name;
  if (buf == NULL || buf_size == 0U) return 1U;
  policy_name = lookup_policy_label_name(lookup, section_index, source_offset, M68K_ANALYSIS_LABEL_DOMAIN_SOURCE);
  /* Materialized range starts have a separate source/storage label before
   * ORG. Runtime operands must name the label on the runtime side. */
  if (policy_name != NULL && policy_name[0] != '\0' &&
      !(source_offset != runtime_address &&
        lookup_source_offset_is_materialized_runtime_range_start(lookup, section_index, source_offset))) {
    snprintf(buf, buf_size, "%s", policy_name);
    return 0U;
  }
  policy_name = lookup_policy_label_name(lookup, section_index, runtime_address, M68K_ANALYSIS_LABEL_DOMAIN_RUNTIME);
  format_runtime_asm_label(lookup, buf, buf_size, section_index, source_offset, runtime_address);
  return policy_name != NULL && policy_name[0] != '\0' ? 0U : 1U;
}

static uint8_t format_rendered_asm_label_with_generation(const M68kRenderLookup *lookup, char *buf, size_t buf_size,
    size_t section_index, uint32_t offset) {
  uint32_t runtime_address = 0U;
  uint8_t generated;
  if (buf == NULL || buf_size == 0U) return 1U;
  if (lookup_source_should_render_runtime_label(lookup, section_index, offset, &runtime_address) &&
      runtime_address != offset && lookup_source_offset_is_materialized_runtime_range_start(lookup, section_index,
        offset)) {
    const char *policy_name = lookup_policy_label_name(lookup, section_index, runtime_address,
      M68K_ANALYSIS_LABEL_DOMAIN_RUNTIME);
    if (policy_name != NULL && policy_name[0] != '\0') {
      snprintf(buf, buf_size, "%s", policy_name);
      return 0U;
    }
    format_runtime_asm_label(lookup, buf, buf_size, section_index, offset, runtime_address);
    return 1U;
  }
  generated = format_lookup_asm_label_with_generation(lookup, buf, buf_size, section_index, offset);
  if (generated && lookup_source_should_render_runtime_label(lookup, section_index, offset, &runtime_address)) {
    const char *policy_name = lookup_policy_label_name(lookup, section_index, runtime_address,
      M68K_ANALYSIS_LABEL_DOMAIN_RUNTIME);
    format_runtime_asm_label(lookup, buf, buf_size, section_index, offset, runtime_address);
    if (policy_name != NULL && policy_name[0] != '\0') return 0U;
  }
  return generated;
}

static uint8_t format_storage_asm_label_with_generation(const M68kRenderLookup *lookup, char *buf, size_t buf_size,
    size_t section_index, uint32_t offset) {
  return format_lookup_asm_label_with_generation(lookup, buf, buf_size, section_index, offset);
}

static int runtime_range_is_materialized(const M68kRenderLookup *lookup, const M68kFact *range);
static int runtime_address_ref_targets_policy_materialized_source(const M68kRenderLookup *lookup,
    const M68kFact *ref);

static int render_asm_include_once(M68kRenderIRPreview *preview, const char *include_path) {
  M68kRenderPlannedDeclaration declaration;
  if (preview == NULL || include_path == NULL || include_path[0] == '\0') return 1;
  if (preview->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK &&
      preview->platform_backend_kind != M68K_PLATFORM_BACKEND_MACOS) return 1;
  memset(&declaration, 0, sizeof(declaration));
  declaration.kind = M68K_RENDER_PLANNED_DECLARATION_INCLUDE;
  declaration.emits_header_text = 1U;
  snprintf(declaration.name, sizeof(declaration.name), "%s", include_path);
  if (m68k_render_plan_append_declaration(&preview->asm_source_plan, &declaration) == 0) return 1;
  ++preview->asm_source_instruction_render_failures;
  record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, 0U, 0U, 0U);
  return 0;
}

static int render_asm_declare_symbol_expr_once(M68kRenderIRPreview *preview, const char *symbol_name,
    const char *expr) {
  M68kRenderPlannedDeclaration declaration;
  if (preview == NULL || symbol_name == NULL || symbol_name[0] == '\0') return 1;
  if (expr == NULL || expr[0] == '\0') return 0;
  if (!asm_symbol_name_is_safe_local(symbol_name)) {
    ++preview->asm_source_instruction_render_failures;
    record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, 0U, 0U, 0U);
    return 0;
  }
  memset(&declaration, 0, sizeof(declaration));
  declaration.kind = M68K_RENDER_PLANNED_DECLARATION_EQUATE;
  declaration.emits_header_text = 1U;
  snprintf(declaration.name, sizeof(declaration.name), "%s", symbol_name);
  snprintf(declaration.expression, sizeof(declaration.expression), "%s", expr);
  if (m68k_render_plan_append_declaration(&preview->asm_source_plan, &declaration) != 0) {
    ++preview->asm_source_instruction_render_failures;
    record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, 0U, 0U, 0U);
    return 0;
  }
  return 1;
}

static int render_asm_declare_symbol_once(M68kRenderIRPreview *preview, const char *symbol_name, int32_t value) {
  char expression[32];
  if (preview != NULL && preview->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 1;
  snprintf(expression, sizeof(expression), "%d", (int)value);
  return render_asm_declare_symbol_expr_once(preview, symbol_name, expression);
}

static int render_asm_declare_symbol_hex_once(M68kRenderIRPreview *preview, const char *symbol_name, uint32_t value) {
  char expression[32];
  snprintf(expression, sizeof(expression), "$%X", (unsigned)value);
  return render_asm_declare_symbol_expr_once(preview, symbol_name, expression);
}

static int plan_asm_layout_symbol_once(M68kRenderIRPreview *preview, const char *symbol_name) {
  M68kRenderPlannedDeclaration declaration;
  if (preview == NULL || symbol_name == NULL || symbol_name[0] == '\0') return 0;
  if (!asm_symbol_name_is_safe_local(symbol_name)) return 0;
  memset(&declaration, 0, sizeof(declaration));
  declaration.kind = M68K_RENDER_PLANNED_DECLARATION_LAYOUT;
  snprintf(declaration.name, sizeof(declaration.name), "%s", symbol_name);
  return m68k_render_plan_append_declaration(&preview->asm_source_plan, &declaration) == 0;
}

static int byte_is_quoted_character_safe(uint8_t value);

static void format_binary_value_expr(uint32_t value, char *out, size_t out_size) {
  char *cursor = out;
  size_t remaining = out_size;
  int high_bit = value <= 0xFFU ? 7 : value <= 0xFFFFU ? 15 : 31;
  int bit;
  if (out == NULL || out_size == 0U) return;
  out[0] = '\0';
  if (remaining < 2U) return;
  *cursor++ = '%';
  --remaining;
  for (bit = high_bit; bit >= 0 && remaining > 1U; --bit) {
    *cursor++ = ((value >> (uint32_t)bit) & 1U) ? '1' : '0';
    --remaining;
  }
  *cursor = '\0';
}

static int layout_runtime_expression(M68kRenderIRPreview *preview,uint32_t address,uint32_t width,
    char *out,size_t capacity,uint32_t *placed) {
  if(!preview->memory_layout_enabled) return 0;
  return m68k_memory_layout_reference(preview->analysis_policy,&preview->memory_layout,
    address,width,out,capacity,placed);
}

static int declare_layout_runtime_symbol(M68kRenderIRPreview *preview,const char *name,uint32_t address) {
  char expression[128];
  int rc=layout_runtime_expression(preview,address,1,expression,sizeof(expression),NULL);
  if(rc<0) return 0;
  return rc ? render_asm_declare_symbol_expr_once(preview,name,expression) :
    render_asm_declare_symbol_hex_once(preview,name,address);
}

static void render_asm_runtime_org(M68kRenderIRPreview *preview,uint32_t address) {
  char expression[128],line[160];
  int rc=layout_runtime_expression(preview,address,1,expression,sizeof(expression),NULL);
  if(rc<0) {
    ++preview->asm_source_instruction_render_failures;
    record_source_export_failure(preview,M68K_SOURCE_EXPORT_FAILURE_RENDER,0,0,0);return;
  }
  if(!rc) {render_asm_org(preview,address);return;}
  snprintf(line,sizeof(line),"    ORG %s\n",expression);
  if(preview->asm_source_row_builder.active)
    m68k_render_plan_row_builder_mark_current_line_directive(&preview->asm_source_row_builder);
  hash_asm_text(preview,line);++preview->asm_source_lines;
}

static int declare_layout_region(M68kRenderIRPreview *preview,size_t i,uint8_t *done) {
  const M68kAnalysisPolicy *p=preview->analysis_policy;
  const M68kMemoryRegionIR *r=&p->memory_regions[i];char expression[128];
  if(done[i]) return 1;
  if(!asm_symbol_name_is_safe_local(r->name)) return 0;
  int parent=preview->memory_layout.parents[i];
  if(parent>=0) {
    if(!declare_layout_region(preview,(size_t)parent,done)) return 0;
    snprintf(expression,sizeof(expression),"%s+$%X",p->memory_regions[parent].name,
      r->runtime_address-p->memory_regions[parent].runtime_address);
  } else snprintf(expression,sizeof(expression),"$%X",preview->memory_layout.addresses[i]);
  if(!render_asm_declare_symbol_expr_once(preview,r->name,expression)) return 0;
  for(size_t d=0;d<preview->asm_source_plan.declaration_count;d++) {
    M68kRenderPlannedDeclaration *decl=&preview->asm_source_plan.declarations[d];
    if(strcmp(decl->name,r->name)) continue;
    if(decl->layout_region_index_plus_one && decl->layout_region_index_plus_one!=i+1) return 0;
    decl->layout_region_index_plus_one=(uint16_t)(i+1);
  }
  done[i]=1;return 1;
}

static int format_target_equate_value_expr(M68kRenderIRPreview *preview,
    const M68kAnalysisTargetEquate *equate, char *out, size_t out_size) {
  uint32_t value;
  if (equate == NULL || out == NULL || out_size == 0U) return 0;
  out[0] = '\0';
  if(equate->address_domain && preview->memory_layout_enabled) {
    int rc=layout_runtime_expression(preview,(uint32_t)equate->value,equate->extent_bytes,out,out_size,NULL);
    if(rc) return rc>0;
  }
  value = (uint32_t)equate->value;
  if (equate->address_domain) {
    snprintf(out, out_size, "$%X", (unsigned)value);
    return 1;
  }
  if (equate->value_style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_DECIMAL) {
    snprintf(out, out_size, "%d", (int)equate->value);
    return 1;
  }
  if (equate->value_style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_BINARY) {
    format_binary_value_expr(value, out, out_size);
    return 1;
  }
  if (equate->value_style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_CHARACTER && equate->value >= 0 &&
      equate->value <= 255 && byte_is_quoted_character_safe((uint8_t)equate->value)) {
    snprintf(out, out_size, "'%c'", (char)equate->value);
    return 1;
  }
  if (equate->value_style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL && equate->value_expr[0] != '\0') {
    snprintf(out, out_size, "%s", equate->value_expr);
    return 1;
  }
  snprintf(out, out_size, "$%X", (unsigned)value);
  return 1;
}

static int render_asm_define_amiga_lvo_symbol_once(M68kRenderIRPreview *preview, const char *symbol_name) {
  int16_t lvo;
  if (!platform_facts_v2_library_vector_lvo_for_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK, symbol_name, &lvo)) {
    if (preview != NULL) {
      ++preview->asm_source_instruction_render_failures;
      record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, 0U, 0U, 0U);
    }
    return 0;
  }
  return render_asm_declare_symbol_once(preview, symbol_name, (int32_t)lvo);
}

static int render_asm_define_amiga_hardware_base_once(M68kRenderIRPreview *preview, const char *symbol_name) {
  uint32_t address;
  if (symbol_name == NULL || symbol_name[0] == '\0') return 1;
  if (!platform_facts_v2_hardware_base_address_for_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK, symbol_name, &address))
    return 1;
  if (address > (uint32_t)INT32_MAX) return 0;
  return render_asm_declare_symbol_hex_once(preview, symbol_name, address);
}

static int render_asm_define_amiga_constant_once(M68kRenderIRPreview *preview, const char *symbol_name) {
  int32_t value;
  if (symbol_name == NULL || symbol_name[0] == '\0') return 1;
  if (platform_facts_v2_symbol_include(M68K_PLATFORM_BACKEND_AMIGA_HUNK, symbol_name) != NULL) return 1;
  if (!platform_facts_v2_symbol_constant_value(M68K_PLATFORM_BACKEND_AMIGA_HUNK, symbol_name, &value)) return 1;
  if (value >= 0) return render_asm_declare_symbol_hex_once(preview, symbol_name, (uint32_t)value);
  return render_asm_declare_symbol_once(preview, symbol_name, value);
}

static int render_asm_define_m68k_vector_symbol_once(M68kRenderIRPreview *preview, const char *symbol_name) {
  const M68kCpuExceptionVectorInfo *vector;
  if (symbol_name == NULL || symbol_name[0] == '\0') return 1;
  vector = m68k_cpu_find_exception_vector_by_symbol_name(symbol_name);
  if (vector == NULL) return 1;
  return render_asm_declare_symbol_hex_once(preview, symbol_name, vector->address);
}

static int render_plan_has_source_label_definition(const M68kRenderPlan *plan,
    const char *symbol_name, uint32_t logical_address) {
  size_t declaration_index;
  if (plan == NULL) return 0;
  for (declaration_index = 0U; declaration_index < plan->declaration_count; ++declaration_index) {
    const M68kRenderPlannedDeclaration *declaration = &plan->declarations[declaration_index];
    if (declaration->kind == M68K_RENDER_PLANNED_DECLARATION_LABEL &&
        declaration->has_source_target != 0U && declaration->logical_address == logical_address &&
        strcmp(declaration->name, symbol_name) == 0) return 1;
  }
  return 0;
}

static int render_asm_declare_target_equates(M68kRenderIRPreview *preview, const M68kRenderPlan *plan,
    const M68kAnalysisPolicy *policy) {
  uint16_t index;
  if (preview == NULL || policy == NULL) return 1;
  if(preview->memory_layout_enabled) {
    uint8_t done[M68K_ANALYSIS_MEMORY_REGION_LIMIT]={0};
    for(size_t i=0;i<policy->memory_region_count;i++) if(!declare_layout_region(preview,i,done)) return 0;
  }
  for (index = 0U; index < policy->target_equate_count && index < M68K_ANALYSIS_TARGET_EQUATE_LIMIT; ++index) {
    const M68kAnalysisTargetEquate *equate = &policy->target_equates[index];
    if (equate->name[0] == '\0') continue;
    if(preview->memory_layout_enabled && equate->address_domain) {
      int same=0;
      for(size_t i=0;i<policy->memory_region_count;i++) {
        const M68kMemoryRegionIR *r=&policy->memory_regions[i];
        if(!strcmp(equate->name,r->name) && (uint32_t)equate->value==r->runtime_address &&
            equate->extent_bytes<=r->size) same=1;
      }
      if(same) continue;
    }
    /* A different label at the same address does not define this EQU's name.
     * Manual symbol representations can still refer to that exact name. */
    if (equate->value >= 0 && render_plan_has_source_label_definition(plan, equate->name,
        (uint32_t)equate->value)) {
      continue;
    }
    if (equate->address_domain || equate->value_style_id != M68K_ANALYSIS_REPRESENTATION_STYLE_NONE) {
      char expr[128];
      if (!format_target_equate_value_expr(preview,equate, expr, sizeof(expr)) ||
          !render_asm_declare_symbol_expr_once(preview, equate->name, expr)) {
        return 0;
      }
    } else if (equate->value >= 0) {
      if (!render_asm_declare_symbol_hex_once(preview, equate->name, (uint32_t)equate->value)) return 0;
    } else if (!render_asm_declare_symbol_once(preview, equate->name, equate->value)) {
      return 0;
    }
  }
  return 1;
}

/*
 * Custom layouts are source declarations, not a sequence of unrelated data
 * labels.  RSRESET keeps each layout independent from the app/base RSSET
 * space emitted immediately above it, while the qualified field names are the
 * same expressions used by typed address-register accesses.
 */
static int render_asm_declare_custom_struct_layouts(M68kRenderIRPreview *preview,
    const M68kAnalysisPolicy *policy) {
  uint16_t struct_index;
  if (preview == NULL || policy == NULL || policy->custom_structs == NULL) return 1;
  for (struct_index = 0U; struct_index < policy->custom_struct_count &&
       struct_index < M68K_ANALYSIS_CUSTOM_STRUCT_LIMIT; ++struct_index) {
    const M68kAnalysisCustomStruct *custom_struct = &policy->custom_structs[struct_index];
    uint16_t field_index;
    uint16_t sorted_field_indices[M68K_ANALYSIS_CUSTOM_STRUCT_FIELD_LIMIT];
    uint16_t sorted_field_count = 0U;
    uint32_t cursor = 0U;
    char line[192];
    if (custom_struct->name[0] == '\0' || custom_struct->size == 0U) continue;
    snprintf(line, sizeof(line), "%s_SIZEOF", custom_struct->name);
    if (!plan_asm_layout_symbol_once(preview, line)) return 0;
    hash_asm_text(preview, "; STRUCT ");
    hash_asm_text(preview, custom_struct->name);
    hash_asm_text(preview, "\n    RSRESET\n");
    preview->asm_source_lines += 2U;
    for (field_index = 0U; field_index < custom_struct->field_count &&
         field_index < M68K_ANALYSIS_CUSTOM_STRUCT_FIELD_LIMIT; ++field_index) {
      uint16_t insert_index = sorted_field_count;
      while (insert_index > 0U &&
          custom_struct->fields[field_index].offset < custom_struct->fields[sorted_field_indices[insert_index - 1U]].offset) {
        sorted_field_indices[insert_index] = sorted_field_indices[insert_index - 1U];
        --insert_index;
      }
      sorted_field_indices[insert_index] = field_index;
      ++sorted_field_count;
    }
    for (field_index = 0U; field_index < sorted_field_count; ++field_index) {
      const M68kAnalysisCustomStructField *field = &custom_struct->fields[sorted_field_indices[field_index]];
      const char *directive;
      if (field->name[0] == '\0' || field->size == 0U || field->offset < cursor ||
          field->offset > custom_struct->size || field->size > custom_struct->size - field->offset) {
        continue;
      }
      if (field->offset > cursor) {
        snprintf(line, sizeof(line), "    RS.B %u\n", (unsigned)(field->offset - cursor));
        hash_asm_text(preview, line);
        ++preview->asm_source_lines;
      }
      directive = field->size == 4U ? "RS.L" : field->size == 2U ? "RS.W" : "RS.B";
      snprintf(line, sizeof(line), "%s_%s", custom_struct->name, field->name);
      if (!plan_asm_layout_symbol_once(preview, line)) return 0;
      snprintf(line, sizeof(line), "%s_%s %s %u\n", custom_struct->name, field->name, directive,
        (unsigned)(field->size == 4U || field->size == 2U ? 1U : field->size));
      hash_asm_text(preview, line);
      ++preview->asm_source_lines;
      cursor = field->offset + field->size;
    }
    if (custom_struct->size > cursor) {
      snprintf(line, sizeof(line), "    RS.B %u\n", (unsigned)(custom_struct->size - cursor));
      hash_asm_text(preview, line);
      ++preview->asm_source_lines;
    }
    snprintf(line, sizeof(line), "%s_SIZEOF EQU __RS\n\n", custom_struct->name);
    hash_asm_text(preview, line);
    preview->asm_source_lines += 2U;
  }
  return 1;
}

static int render_asm_include_for_symbol_expr(M68kRenderIRPreview *preview, const char *expr);

static int render_asm_define_amiga_hardware_instance_alias_once(M68kRenderIRPreview *preview,
    const char *symbol_name) {
  const char *expr;
  if (preview == NULL || symbol_name == NULL || symbol_name[0] == '\0') return 1;
  if (preview->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 1;
  expr = platform_facts_v2_hardware_register_instance_alias_expr(M68K_PLATFORM_BACKEND_AMIGA_HUNK, symbol_name);
  if (expr == NULL || expr[0] == '\0') return 1;
  if (!render_asm_include_for_symbol_expr(preview, expr)) return 0;
  return render_asm_declare_symbol_expr_once(preview, symbol_name, expr);
}

static int render_asm_include_for_amiga_symbol(M68kRenderIRPreview *preview, const char *symbol_name) {
  const char *include_path;
  if (symbol_name == NULL || symbol_name[0] == '\0') return 1;
  include_path = platform_facts_v2_symbol_include(M68K_PLATFORM_BACKEND_AMIGA_HUNK, symbol_name);
  if (include_path != NULL && include_path[0] != '\0') return render_asm_include_once(preview, include_path);
  if (platform_facts_v2_library_vector_lvo_for_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK, symbol_name, NULL))
    return render_asm_define_amiga_lvo_symbol_once(preview, symbol_name);
  return 1;
}

static int render_asm_include_for_symbol_expr(M68kRenderIRPreview *preview, const char *expr) {
  const char *cursor;
  if (expr == NULL || expr[0] == '\0') return 1;
  cursor = expr;
  while (*cursor != '\0') {
    char token[64];
    size_t token_len = 0U;
    if (!((*cursor >= 'A' && *cursor <= 'Z') || (*cursor >= 'a' && *cursor <= 'z') || *cursor == '_')) {
      ++cursor;
      continue;
    }
    while ((*cursor >= 'A' && *cursor <= 'Z') || (*cursor >= 'a' && *cursor <= 'z') ||
           (*cursor >= '0' && *cursor <= '9') || *cursor == '_') {
      if (token_len + 1U >= sizeof(token)) return 0;
      token[token_len++] = *cursor;
      ++cursor;
    }
    token[token_len] = '\0';
    if (!asm_symbol_name_is_safe_local(token)) return 0;
    if (!render_asm_include_for_amiga_symbol(preview, token)) return 0;
    if (!render_asm_define_amiga_hardware_base_once(preview, token)) return 0;
    if (!render_asm_define_amiga_constant_once(preview, token)) return 0;
    if (!render_asm_define_m68k_vector_symbol_once(preview, token)) return 0;
    if (!render_asm_define_amiga_hardware_instance_alias_once(preview, token)) return 0;
  }
  return 1;
}

static int render_asm_includes_for_structured_data_item(M68kRenderIRPreview *preview,
    const M68kAnalysisStructuredDataItem *item) {
  if (item == NULL) return 1;
  return render_asm_include_for_amiga_symbol(preview, item->field_name) &&
    render_asm_include_for_amiga_symbol(preview, item->constant_name);
}

static int lookup_label_has_inbound_target_ref(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t offset);

static const M68kAnalysisCustomStruct *policy_custom_struct_named(
    const M68kAnalysisPolicy *policy, const char *struct_name) {
  uint16_t index;
  if (policy == NULL || policy->custom_structs == NULL || struct_name == NULL || struct_name[0] == '\0') return NULL;
  for (index = 0U; index < policy->custom_struct_count && index < M68K_ANALYSIS_CUSTOM_STRUCT_LIMIT; ++index) {
    if (strcmp(policy->custom_structs[index].name, struct_name) == 0) return &policy->custom_structs[index];
  }
  return NULL;
}

static int policy_has_custom_struct_named(const M68kAnalysisPolicy *policy, const char *struct_name) {
  return policy_custom_struct_named(policy, struct_name) != NULL;
}

/* Data-block expansion gives internal array fields generated labels such as
 * table_flags_3.  They are not symbols in the original program: the sole
 * table/instance label plus its RS layout is sufficient. */
static int structured_item_has_generated_custom_field_label(const M68kAnalysisStructuredDataItem *item) {
  const char *suffix;
  const char *search;
  const char *digits;
  if (item == NULL || item->label[0] == '\0' || item->field_name[0] == '\0') return 0;
  search = item->label;
  /* The owner may contain the field name too. Only a complete trailing field
   * suffix (optionally followed by an array index) identifies this alias. */
  while ((suffix = strstr(search, item->field_name)) != NULL) {
    search = suffix + 1;
    if (suffix == item->label || suffix[-1] != '_') continue;
    suffix += strlen(item->field_name);
    if (*suffix == '\0') return 1;
    if (*suffix != '_') continue;
    digits = suffix + 1;
    if (*digits == '\0') continue;
    while (*digits >= '0' && *digits <= '9') ++digits;
    if (*digits == '\0') return 1;
  }
  return 0;
}

static const M68kAnalysisStructuredDataItem *lookup_generated_custom_field_item_at(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  size_t index;
  if (lookup == NULL) return NULL;
  if (lookup->policy != NULL) {
    for (index = 0U; index < lookup->policy->structured_data_item_count &&
         index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
      const M68kAnalysisStructuredDataItem *item = &lookup->policy->structured_data_items[index];
      if (item->has_section_index && item->section_index == section_index && item->offset == offset &&
          policy_has_custom_struct_named(lookup->policy, item->struct_name) &&
          structured_item_has_generated_custom_field_label(item)) {
        return item;
      }
    }
  }
  for (index = 0U; index < lookup->auto_structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &lookup->auto_structured_data_items[index];
    if (item->has_section_index && item->section_index == section_index && item->offset == offset &&
        policy_has_custom_struct_named(lookup->policy, item->struct_name) &&
        structured_item_has_generated_custom_field_label(item)) {
      return item;
    }
  }
  return NULL;
}

static int render_asm_should_emit_label_statement(const M68kRenderIRPreview *preview,
    const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    size_t section_index, uint32_t offset) {
  const M68kAnalysisStructuredDataItem *item;
  (void)preview;
  if (!lookup_should_emit_label_statement(lookup, section, accepted_start, section_index, offset)) return 0;
  item = lookup_generated_custom_field_item_at(lookup, section_index, offset);
  if (item == NULL || lookup_structured_field_has_explicit_label(lookup, item, section_index, offset)) {
    return 1;
  }
  return lookup_label_has_statement_ref(lookup, section_index, offset);
}

static int record_rendered_symbol_access(M68kRenderIRPreview *preview, size_t source_section_index,
    const M68kRenderedSymbolAccessIR *access) {
  M68kRenderedSymbolAccessIR ordered_access;
  if (source_section_index > UINT32_MAX || access == NULL) return 0;
  ordered_access = *access;
  if (preview == NULL || preview->render_evidence == NULL) return 0;
  if (preview->precomputing_planned_evidence) {
    ordered_access.emission_order = preview->planned_evidence_next_order++;
    return m68k_ir_render_evidence_append_unique_rendered_symbol_access(preview->render_evidence,
      (uint32_t)source_section_index, &ordered_access);
  }
  if (m68k_ir_render_evidence_append_rendered_symbol_access(preview->render_evidence,
        (uint32_t)source_section_index, &ordered_access) != 0) return -1;
  return 0;
}

static int record_planned_instruction_symbol_accesses(M68kRenderIRPreview *preview, size_t section_index,
    const M68kRenderPlannedInstruction *instruction) {
  size_t access_index;
  if (preview == NULL || instruction == NULL) return -1;
  if (preview->planned_evidence_precomputed) return 0;
  for (access_index = 0U; access_index < instruction->symbol_access_count; ++access_index) {
    const M68kRenderPlannedSymbolAccess *planned_access = &instruction->symbol_accesses[access_index];
    M68kRenderedSymbolAccessIR access;
    memset(&access, 0, sizeof(access));
    access.symbol_name = (char *)planned_access->symbol_name;
    access.offset = instruction->source_offset;
    access.target_section_index = planned_access->target_section_index;
    access.target_offset = planned_access->target_offset;
    access.operand_index = planned_access->operand_index;
    access.access_kind = planned_access->access_kind;
    access.has_target = planned_access->has_target;
    access.comment_only = planned_access->comment_only;
    access.source_order_class = M68K_RENDERED_SYMBOL_ACCESS_SOURCE_ORDER_BODY;
    if (record_rendered_symbol_access(preview, section_index, &access) != 0) return -1;
  }
  return 0;
}

static int record_planned_expression_target_access(M68kRenderIRPreview *preview, size_t source_section_index,
    const M68kRenderPlannedExpression *expression, int use_base_target) {
  M68kRenderedSymbolAccessIR access;
  const char *name;
  if (preview == NULL || expression == NULL ||
      expression->outcome != M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC) return -1;
  if (preview->planned_evidence_precomputed) return 0;
  if (use_base_target) {
    if (expression->has_base_target == 0U || expression->base_symbol[0] == '\0') return -1;
    name = expression->base_symbol;
  } else {
    if (expression->target_symbol[0] == '\0') return -1;
    name = expression->target_symbol;
  }
  memset(&access, 0, sizeof(access));
  access.symbol_name = (char *)name;
  access.offset = expression->source_offset;
  access.target_section_index = use_base_target ? expression->base_section_index : expression->target_section_index;
  access.target_offset = use_base_target ? expression->base_offset : expression->target_offset;
  access.operand_index = expression->operand_index;
  access.access_kind = M68K_RENDERED_SYMBOL_ACCESS_OPERAND;
  access.has_target = use_base_target ? expression->has_base_target : expression->has_target;
  if (!access.has_target) access.access_kind = M68K_RENDERED_SYMBOL_ACCESS_EQUATE;
  access.source_order_class = M68K_RENDERED_SYMBOL_ACCESS_SOURCE_ORDER_BODY;
  return record_rendered_symbol_access(preview, source_section_index, &access);
}

static int record_planned_equate_expression_access(M68kRenderIRPreview *preview, size_t source_section_index,
    const M68kRenderPlannedExpression *expression) {
  M68kRenderedSymbolAccessIR access;
  if (preview == NULL || expression == NULL ||
      expression->outcome != M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC ||
      expression->kind != M68K_RENDER_PLANNED_EXPRESSION_EQUATE) return -1;
  if (preview->planned_evidence_precomputed) return 0;
  memset(&access, 0, sizeof(access));
  access.symbol_name = (char *)expression->expression;
  access.offset = expression->source_offset;
  access.operand_index = UINT32_MAX;
  access.access_kind = M68K_RENDERED_SYMBOL_ACCESS_EQUATE;
  access.source_order_class = M68K_RENDERED_SYMBOL_ACCESS_SOURCE_ORDER_BODY;
  return record_rendered_symbol_access(preview, source_section_index, &access);
}

static int record_planned_label_statement_access(M68kRenderIRPreview *preview, size_t source_section_index,
    const M68kRenderPlannedLabel *label, int storage_label) {
  M68kRenderedSymbolAccessIR access;
  const char *name;
  if (preview == NULL || label == NULL) return -1;
  if (preview->planned_evidence_precomputed) return 0;
  name = storage_label ? label->storage_name : label->name;
  if (name[0] == '\0') return -1;
  memset(&access, 0, sizeof(access));
  access.symbol_name = (char *)name;
  access.offset = label->source_offset;
  access.target_section_index = label->source_section_index;
  access.target_offset = label->source_offset;
  access.operand_index = UINT32_MAX;
  access.access_kind = storage_label ? M68K_RENDERED_SYMBOL_ACCESS_STORAGE_LABEL :
    M68K_RENDERED_SYMBOL_ACCESS_LABEL_STATEMENT;
  access.source_order_class = storage_label ? M68K_RENDERED_SYMBOL_ACCESS_SOURCE_ORDER_STORAGE_LABEL :
    M68K_RENDERED_SYMBOL_ACCESS_SOURCE_ORDER_LABEL;
  access.has_target = 1U;
  return record_rendered_symbol_access(preview, source_section_index, &access);
}

/* Runtime aliases are semantic planning decisions. The stream records them
 * before row delivery; the row renderer then only materializes their text. */
static int render_planned_runtime_alias_labels(M68kRenderIRPreview *preview, size_t section_index,
    uint32_t offset) {
  size_t alias_index;
  int emitted = 0;
  if (preview == NULL || section_index > UINT32_MAX) return 0;
  for (alias_index = 0U; alias_index < preview->asm_source_plan.runtime_alias_count; ++alias_index) {
    const M68kRenderPlannedRuntimeAlias *runtime_alias =
      &preview->asm_source_plan.runtime_aliases[alias_index];
    M68kRenderedSymbolAccessIR access;
    char line[160];
    if (runtime_alias->source_section_index != (uint32_t)section_index ||
        runtime_alias->source_offset != offset) continue;
    render_asm_runtime_org(preview, runtime_alias->runtime_address);
    snprintf(line, sizeof(line), "%s:\n", runtime_alias->name);
    if (preview->asm_source_row_builder.active)
      m68k_render_plan_row_builder_mark_current_line_label(&preview->asm_source_row_builder, offset, 1U,
        runtime_alias->runtime_address);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
    memset(&access, 0, sizeof(access));
    access.symbol_name = (char *)runtime_alias->name;
    access.offset = offset;
    access.target_section_index = runtime_alias->source_section_index;
    access.target_offset = offset;
    access.operand_index = UINT32_MAX;
    access.access_kind = M68K_RENDERED_SYMBOL_ACCESS_LABEL_STATEMENT;
    access.has_target = 1U;
    if (!preview->planned_evidence_precomputed &&
        record_rendered_symbol_access(preview, section_index, &access) != 0) return 0;
    emitted = 1;
  }
  return emitted;
}

static void render_asm_label(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset, uint32_t *io_logical_pc) {
  const M68kAnalysisStructuredDataItem *item =
    lookup_structured_data_item_at_offset(lookup, section_index, offset);
  const M68kAnalysisCustomStruct *range_struct = item != NULL && item->field_name[0] == '\0' ?
    policy_custom_struct_named(preview->analysis_policy, item->struct_name) : NULL;
  char line[sizeof(((M68kRenderPlannedLabel *)0)->name) +
    sizeof(((M68kAnalysisStructuredDataItem *)0)->struct_name) + 32U];
  char name[sizeof(((M68kRenderPlannedLabel *)0)->name)];
  char storage_name[sizeof(((M68kRenderPlannedLabel *)0)->storage_name)];
  const M68kRenderPlannedLabel *planned_label;
  uint32_t runtime_address;
  int has_runtime_address;
  int needs_storage_label;
  planned_label = m68k_render_plan_find_label(&preview->asm_source_plan, (uint32_t)section_index, offset);
  if (planned_label == NULL) {
    preview->asm_source_allocation_failed = 1U;
    return;
  }
  if (!render_asm_includes_for_structured_data_item(preview, item)) return;
  runtime_address = planned_label->runtime_address;
  has_runtime_address = planned_label->has_runtime_address != 0U;
  needs_storage_label = planned_label->has_storage_label != 0U;
  if (needs_storage_label && io_logical_pc != NULL) {
    snprintf(storage_name, sizeof(storage_name), "%s", planned_label->storage_name);
    if (*io_logical_pc != offset) {
      render_asm_org(preview, offset);
      *io_logical_pc = offset;
    }
    snprintf(line, sizeof(line), "%s:\n", storage_name);
    if (preview->asm_source_row_builder.active)
      m68k_render_plan_row_builder_mark_current_line_label(&preview->asm_source_row_builder, offset, 1U,
        runtime_address);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
    if (record_planned_label_statement_access(preview, section_index, planned_label, 1) != 0) {
      preview->asm_source_allocation_failed = 1U;
    }
    render_asm_runtime_org(preview, runtime_address);
    *io_logical_pc = runtime_address;
  } else if (io_logical_pc != NULL) {
    render_asm_sync_logical_pc(preview, lookup, section_index, offset, io_logical_pc);
  }
  if (render_planned_runtime_alias_labels(preview, section_index, offset) && has_runtime_address) {
    render_asm_runtime_org(preview, runtime_address);
    if (io_logical_pc != NULL) *io_logical_pc = runtime_address;
  }
  snprintf(name, sizeof(name), "%s", planned_label->name);
  if (preview->asm_source_row_builder.active)
    m68k_render_plan_row_builder_mark_current_line_label(&preview->asm_source_row_builder, offset,
      has_runtime_address ? 1U : 0U, runtime_address);
  if (range_struct != NULL && range_struct->size != 0U &&
      item->size > range_struct->size && item->size % range_struct->size == 0U) {
    snprintf(line, sizeof(line), "%s:\t; ARRAY %s[%u]\n", name, item->struct_name,
      (unsigned)(item->size / range_struct->size));
  } else if (range_struct != NULL && range_struct->size != 0U && item->size == range_struct->size &&
      item->field_name[0] == '\0' && item->has_source_owner_span &&
      item->source_owner_start == item->offset && item->source_owner_size == item->size) {
    /* A compact one-record array has no expanded field comments. Retain its
     * declared format at the public label, just as for a repeated array. */
    snprintf(line, sizeof(line), "%s:\t; ARRAY %s[1]\n", name, item->struct_name);
  } else if (item != NULL && item->struct_name[0] != '\0' &&
      !policy_has_custom_struct_named(preview != NULL ? preview->analysis_policy : NULL, item->struct_name)) {
    snprintf(line, sizeof(line), "%s:\t; STRUCT %s\n", name, item->struct_name);
  } else {
    snprintf(line, sizeof(line), "%s:\n", name);
  }
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  if (record_planned_label_statement_access(preview, section_index, planned_label, 0) != 0) {
    preview->asm_source_allocation_failed = 1U;
  }
}

static void platform_state_clear_register(M68kRenderPlatformState *state, uint8_t reg_index) {
  size_t index;
  if (state == NULL || reg_index >= 8U) return;
  m68k_bitset_u32_clear(&state->address_base_known, reg_index);
  state->address_base_id[reg_index] = 0U;
  state->address_base_library[reg_index][0] = '\0';
  m68k_bitset_u32_clear(&state->address_hardware_base_known, reg_index);
  state->address_hardware_base_id[reg_index] = PLATFORM_FACTS_V2_HARDWARE_BASE_ID_NONE;
  m68k_bitset_u32_clear(&state->address_app_base_known, reg_index);
  m68k_bitset_u32_clear(&state->address_layout_base_known, reg_index);
  state->address_layout_base_symbol[reg_index][0] = '\0';
  for (index = 0U; index < sizeof(state->local_base_slots) / sizeof(state->local_base_slots[0]); ++index) {
    if (state->local_base_slots[index].valid && state->local_base_slots[index].base_reg == reg_index)
      state->local_base_slots[index].valid = 0U;
  }
}

static void platform_state_clear_data_library(M68kRenderPlatformState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  m68k_bitset_u32_clear(&state->data_base_known, reg_index);
  state->data_base_id[reg_index] = 0U;
  state->data_base_library[reg_index][0] = '\0';
  m68k_bitset_u32_clear(&state->data_hardware_base_known, reg_index);
  state->data_hardware_base_id[reg_index] = PLATFORM_FACTS_V2_HARDWARE_BASE_ID_NONE;
  m68k_bitset_u32_clear(&state->data_layout_base_known, reg_index);
  state->data_layout_base_symbol[reg_index][0] = '\0';
  platform_state_clear_data_lvo(state, reg_index);
}

static void platform_state_clear_all_data_libraries(M68kRenderPlatformState *state) {
  if (state == NULL) return;
  state->data_base_known = 0U;
  state->data_hardware_base_known = 0U;
  memset(state->data_hardware_base_id, 0, sizeof(state->data_hardware_base_id));
  memset(state->data_base_id, 0, sizeof(state->data_base_id));
  memset(state->data_base_library, 0, sizeof(state->data_base_library));
  state->data_layout_base_known = 0U;
  memset(state->data_layout_base_symbol, 0, sizeof(state->data_layout_base_symbol));
  state->data_lvo_known = 0U;
  memset(state->data_lvo, 0, sizeof(state->data_lvo));
}

static void platform_state_clear_all_local_base_slots(M68kRenderPlatformState *state) {
  if (state == NULL) return;
  memset(state->local_base_slots, 0, sizeof(state->local_base_slots));
}

static void platform_state_clear_address_app_base(M68kRenderPlatformState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  m68k_bitset_u32_clear(&state->address_app_base_known, reg_index);
}

static void platform_state_clear_address_layout_base(M68kRenderPlatformState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  m68k_bitset_u32_clear(&state->address_layout_base_known, reg_index);
  state->address_layout_base_symbol[reg_index][0] = '\0';
}

static void platform_state_clear_address_hardware_base(M68kRenderPlatformState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  m68k_bitset_u32_clear(&state->address_hardware_base_known, reg_index);
  state->address_hardware_base_id[reg_index] = PLATFORM_FACTS_V2_HARDWARE_BASE_ID_NONE;
}

static void platform_state_clear_all_hardware_bases(M68kRenderPlatformState *state) {
  if (state == NULL) return;
  state->address_hardware_base_known = 0U;
  state->data_hardware_base_known = 0U;
  memset(state->data_hardware_base_id, 0, sizeof(state->data_hardware_base_id));
  memset(state->address_hardware_base_id, 0, sizeof(state->address_hardware_base_id));
}

static void platform_state_clear_data_app_base(M68kRenderPlatformState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  m68k_bitset_u32_clear(&state->data_app_base_known, reg_index);
  platform_state_clear_data_lvo(state, reg_index);
}

static void platform_state_clear_data_layout_base(M68kRenderPlatformState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  m68k_bitset_u32_clear(&state->data_layout_base_known, reg_index);
  state->data_layout_base_symbol[reg_index][0] = '\0';
  platform_state_clear_data_lvo(state, reg_index);
}

static void platform_state_clear_all_app_bases(M68kRenderPlatformState *state) {
  if (state == NULL) return;
  state->data_app_base_known = 0U;
  state->address_app_base_known = 0U;
  state->data_lvo_known = 0U;
  memset(state->data_lvo, 0, sizeof(state->data_lvo));
}

static void platform_state_clear_all_layout_bases(M68kRenderPlatformState *state) {
  if (state == NULL) return;
  state->data_layout_base_known = 0U;
  memset(state->data_layout_base_symbol, 0, sizeof(state->data_layout_base_symbol));
  state->address_layout_base_known = 0U;
  memset(state->address_layout_base_symbol, 0, sizeof(state->address_layout_base_symbol));
  state->data_lvo_known = 0U;
  memset(state->data_lvo, 0, sizeof(state->data_lvo));
}

void platform_state_clear_data_lvo(M68kRenderPlatformState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  m68k_bitset_u32_clear(&state->data_lvo_known, reg_index);
  state->data_lvo[reg_index] = 0;
}

static uint16_t platform_base_id_from_name(const char *name) {
  uint16_t base_id = AMIGA_OS_BASE_ID_NONE;
  const char *library_name;
  if (name == NULL || name[0] == '\0') return AMIGA_OS_BASE_ID_NONE;
  if (platform_facts_v2_library_base_id_for_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK, name, &base_id)) return base_id;
  library_name = platform_facts_v2_library_name_from_base_symbol_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK, name);
  if (library_name == NULL || library_name[0] == '\0') return AMIGA_OS_BASE_ID_NONE;
  return platform_facts_v2_library_base_id_for_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK, library_name, &base_id) ?
    base_id : AMIGA_OS_BASE_ID_NONE;
}

static const char *platform_library_name_from_base_id(uint16_t base_id) {
  return platform_facts_v2_library_name_for_base_id(M68K_PLATFORM_BACKEND_AMIGA_HUNK, base_id);
}

void platform_state_set_register_library(M68kRenderPlatformState *state, uint8_t reg_index,
    const char *library_name) {
  size_t index;
  uint16_t base_id = platform_base_id_from_name(library_name);
  const char *canonical_library_name = platform_library_name_from_base_id(base_id);
  if (state == NULL || reg_index >= 8U || library_name == NULL || library_name[0] == '\0') return;
  if (canonical_library_name == NULL || canonical_library_name[0] == '\0') return;
  for (index = 0U; index < sizeof(state->local_base_slots) / sizeof(state->local_base_slots[0]); ++index) {
    if (state->local_base_slots[index].valid && state->local_base_slots[index].base_reg == reg_index)
      state->local_base_slots[index].valid = 0U;
  }
  m68k_bitset_u32_set(&state->address_base_known, reg_index);
  state->address_base_id[reg_index] = base_id;
  m68k_bitset_u32_clear(&state->address_app_base_known, reg_index);
  platform_state_clear_address_layout_base(state, reg_index);
  platform_state_clear_address_hardware_base(state, reg_index);
  snprintf(state->address_base_library[reg_index], sizeof(state->address_base_library[reg_index]), "%s",
    canonical_library_name);
}

static void platform_state_set_data_library(M68kRenderPlatformState *state, uint8_t reg_index,
    const char *library_name) {
  uint16_t base_id = platform_base_id_from_name(library_name);
  const char *canonical_library_name = platform_library_name_from_base_id(base_id);
  if (state == NULL || reg_index >= 8U || library_name == NULL || library_name[0] == '\0') return;
  if (canonical_library_name == NULL || canonical_library_name[0] == '\0') return;
  m68k_bitset_u32_clear(&state->data_hardware_base_known, reg_index);
  state->data_hardware_base_id[reg_index] = PLATFORM_FACTS_V2_HARDWARE_BASE_ID_NONE;
  m68k_bitset_u32_set(&state->data_base_known, reg_index);
  state->data_base_id[reg_index] = base_id;
  snprintf(state->data_base_library[reg_index], sizeof(state->data_base_library[reg_index]), "%s",
    canonical_library_name);
}

int amiga_unknown_base_register_owner_name(uint8_t base_reg, char *buf, size_t buf_size) {
  int written;
  if (buf != NULL && buf_size != 0U) buf[0] = '\0';
  if (buf == NULL || buf_size == 0U || base_reg >= 8U || base_reg == 6U || base_reg == 7U) return 0;
  written = snprintf(buf, buf_size, "__amiga_local_base_a%u__", (unsigned)base_reg);
  return written > 0 && (size_t)written < buf_size;
}

static int amiga_unknown_base_owner_name_is_internal(const char *owner_name) {
  static const char prefix[] = "__amiga_local_base_a";
  size_t prefix_len = sizeof(prefix) - 1U;
  if (owner_name == NULL) return 0;
  if (strncmp(owner_name, prefix, prefix_len) != 0) return 0;
  if (owner_name[prefix_len] < '0' || owner_name[prefix_len] > '7') return 0;
  return owner_name[prefix_len + 1U] == '_' &&
    owner_name[prefix_len + 2U] == '_' &&
    owner_name[prefix_len + 3U] == '\0';
}

static int amiga_vector_is_open_library_result(const AmigaOsLibraryVectorInfo *vector);

static const char *platform_state_local_base_slot_library(const M68kRenderPlatformState *state, uint8_t base_reg,
    int16_t displacement) {
  size_t index;
  if (state == NULL || base_reg >= 8U) return NULL;
  for (index = 0U; index < sizeof(state->local_base_slots) / sizeof(state->local_base_slots[0]); ++index) {
    const M68kRenderPlatformLocalBaseSlot *slot = &state->local_base_slots[index];
    if (slot->valid && slot->base_reg == base_reg && slot->displacement == displacement)
      return platform_library_name_from_base_id(slot->base_id);
  }
  return NULL;
}

static void platform_state_set_local_base_slot(M68kRenderPlatformState *state, uint8_t base_reg,
    int16_t displacement, const char *library_name) {
  size_t index;
  uint16_t base_id = platform_base_id_from_name(library_name);
  const char *canonical_library_name = platform_library_name_from_base_id(base_id);
  if (state == NULL || base_reg >= 8U || library_name == NULL || library_name[0] == '\0') return;
  if (canonical_library_name == NULL || canonical_library_name[0] == '\0') return;
  for (index = 0U; index < sizeof(state->local_base_slots) / sizeof(state->local_base_slots[0]); ++index) {
    M68kRenderPlatformLocalBaseSlot *slot = &state->local_base_slots[index];
    if (slot->valid && slot->base_reg == base_reg && slot->displacement == displacement) {
      slot->base_id = base_id;
      snprintf(slot->library_name, sizeof(slot->library_name), "%s", canonical_library_name);
      return;
    }
  }
  for (index = 0U; index < sizeof(state->local_base_slots) / sizeof(state->local_base_slots[0]); ++index) {
    M68kRenderPlatformLocalBaseSlot *slot = &state->local_base_slots[index];
    if (slot->valid) continue;
    slot->valid = 1U;
    slot->base_reg = base_reg;
    slot->base_id = base_id;
    slot->displacement = displacement;
    snprintf(slot->library_name, sizeof(slot->library_name), "%s", canonical_library_name);
    return;
  }
}

static void platform_state_clear_local_base_slot(M68kRenderPlatformState *state, uint8_t base_reg,
    int16_t displacement) {
  size_t index;
  if (state == NULL || base_reg >= 8U) return;
  for (index = 0U; index < sizeof(state->local_base_slots) / sizeof(state->local_base_slots[0]); ++index) {
    M68kRenderPlatformLocalBaseSlot *slot = &state->local_base_slots[index];
    if (slot->valid && slot->base_reg == base_reg && slot->displacement == displacement)
      slot->valid = 0U;
  }
}

static const char *platform_state_operand_library(const M68kRenderPlatformState *state,
    const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  if (state == NULL || operand == NULL) return NULL;
  if (operand_is_data_register_local(operand, &reg) && m68k_bitset_u32_has(state->data_base_known, reg))
    return platform_library_name_from_base_id(state->data_base_id[reg]);
  if (operand_address_register_index_local(operand, &reg) && m68k_bitset_u32_has(state->address_base_known, reg))
    return platform_library_name_from_base_id(state->address_base_id[reg]);
  return NULL;
}

int platform_state_name_is_app_base(const char *name) {
  return name != NULL && strcmp(name, M68K_APP_BASE_SYMBOL) == 0;
}

static int policy_has_layout_base_symbol(const M68kAnalysisPolicy *policy, const char *name) {
  uint16_t index;
  if (policy == NULL || name == NULL || name[0] == '\0') return 0;
  for (index = 0U; index < policy->rsset_layout_region_count && index < M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT; ++index) {
    const M68kAnalysisRssetLayoutRegion *region = &policy->rsset_layout_regions[index];
    const char *base_symbol = region->base_symbol[0] != '\0' ? region->base_symbol : M68K_APP_BASE_SYMBOL;
    if (strcmp(base_symbol, name) == 0) return 1;
  }
  return 0;
}

static void platform_state_set_register_app_base(M68kRenderPlatformState *state, uint8_t reg_kind,
    uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == M68K_ANALYSIS_REGISTER_DATA) {
    platform_state_clear_data_library(state, reg_index);
    m68k_bitset_u32_set(&state->data_app_base_known, reg_index);
  } else if (reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS) {
    platform_state_clear_register(state, reg_index);
    m68k_bitset_u32_set(&state->address_app_base_known, reg_index);
  }
}

static void platform_state_set_register_layout_base(M68kRenderPlatformState *state, uint8_t reg_kind,
    uint8_t reg_index, const char *base_symbol) {
  if (state == NULL || reg_index >= 8U || base_symbol == NULL || base_symbol[0] == '\0') return;
  if (reg_kind == M68K_ANALYSIS_REGISTER_DATA) {
    platform_state_clear_data_library(state, reg_index);
    platform_state_clear_data_app_base(state, reg_index);
    m68k_bitset_u32_set(&state->data_layout_base_known, reg_index);
    snprintf(state->data_layout_base_symbol[reg_index], sizeof(state->data_layout_base_symbol[reg_index]), "%s",
      base_symbol);
  } else if (reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS) {
    platform_state_clear_register(state, reg_index);
    m68k_bitset_u32_set(&state->address_layout_base_known, reg_index);
    snprintf(state->address_layout_base_symbol[reg_index], sizeof(state->address_layout_base_symbol[reg_index]),
      "%s", base_symbol);
  }
}

static int platform_state_set_register_hardware_base(M68kRenderPlatformState *state, uint8_t reg_index,
    const char *base_symbol) {
  uint16_t base_id;
  if (state == NULL || reg_index >= 8U || base_symbol == NULL || base_symbol[0] == '\0') return 0;
  if (!platform_facts_v2_hardware_base_id_for_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK, base_symbol, &base_id))
    return 0;
  platform_state_clear_register(state, reg_index);
  m68k_bitset_u32_set(&state->address_hardware_base_known, reg_index);
  state->address_hardware_base_id[reg_index] = base_id;
  return 1;
}

static void platform_state_set_data_hardware_base(M68kRenderPlatformState *state, uint8_t reg_index,
    const char *base_symbol) {
  uint16_t base_id;
  if (state == NULL || reg_index >= 8U || base_symbol == NULL ||
      !platform_facts_v2_hardware_base_id_for_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK, base_symbol, &base_id))
    return;
  platform_state_clear_data_library(state, reg_index);
  platform_state_clear_data_app_base(state, reg_index);
  m68k_bitset_u32_set(&state->data_hardware_base_known, reg_index);
  state->data_hardware_base_id[reg_index] = base_id;
}

void platform_state_apply_policy_register_seeds(M68kRenderPlatformState *state,
    const M68kAnalysisPolicy *policy, size_t section_index, uint32_t offset) {
  uint16_t index;
  if (state == NULL || policy == NULL) return;
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    if (seed->has_section_index && seed->section_index != (uint32_t)section_index) continue;
    if (seed->has_entry_offset) {
      if (seed->entry_offset != offset) continue;
    } else if (!policy->has_entry_offset || section_index != 0U || policy->entry_offset != offset) continue;
    if (seed->kind != M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE &&
        seed->kind != M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR) {
      continue;
    }
    /* An explicit pointer input replaces the register's incoming identity.
     * A game struct need not resolve to a platform library or hardware base;
     * leaving the old identity alive would mislabel its fields as registers. */
    if (seed->reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS) {
      platform_state_clear_register(state, seed->reg_index);
    } else if (seed->reg_kind == M68K_ANALYSIS_REGISTER_DATA) {
      platform_state_clear_data_library(state, seed->reg_index);
      platform_state_clear_data_app_base(state, seed->reg_index);
    }
    if (platform_state_name_is_app_base(seed->name)) {
      platform_state_set_register_app_base(state, seed->reg_kind, seed->reg_index);
      continue;
    }
    if (policy_has_layout_base_symbol(policy, seed->name)) {
      platform_state_set_register_layout_base(state, seed->reg_kind, seed->reg_index, seed->name);
      continue;
    }
    if (seed->reg_kind == M68K_ANALYSIS_REGISTER_DATA) {
      platform_state_set_data_hardware_base(state, seed->reg_index, seed->name);
      continue;
    }
    if (seed->reg_kind != M68K_ANALYSIS_REGISTER_ADDRESS || seed->reg_index >= 8U) continue;
    if (platform_state_set_register_hardware_base(state, seed->reg_index, seed->name)) {
      continue;
    }
    platform_state_set_register_library(state, seed->reg_index, seed->name);
  }
}

static void render_asm_policy_entry_comments(M68kRenderIRPreview *preview, const M68kAnalysisPolicy *policy,
    size_t section_index, uint32_t offset) {
  uint16_t index;
  if (preview == NULL || policy == NULL) return;
  for (index = 0U; index < policy->entry_comment_count && index < M68K_ANALYSIS_ENTRY_COMMENT_LIMIT; ++index) {
    const M68kAnalysisEntryComment *comment = &policy->entry_comments[index];
    char line[256];
    if (comment->has_section_index && comment->section_index != (uint32_t)section_index) continue;
    if (comment->offset != offset || comment->comment[0] == '\0') continue;
    snprintf(line, sizeof(line), "    ; %s\n", comment->comment);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
  }
}

static void render_asm_comment_line(M68kRenderIRPreview *preview, const char *comment) {
  char line[512];
  if (preview == NULL || comment == NULL || comment[0] == '\0') return;
  snprintf(line, sizeof(line), "    ; %s\n", comment);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static void render_asm_file_comment_line(M68kRenderIRPreview *preview, const char *comment) {
  char line[512];
  if (preview == NULL || comment == NULL || comment[0] == '\0') return;
  snprintf(line, sizeof(line), "; %s\n", comment);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static int format_policy_register_seed_comment_local(const M68kAnalysisPolicy *policy, size_t section_index,
    uint32_t offset, char *message, size_t message_size) {
  size_t used = 0U;
  uint32_t emitted[2] = {0U, 0U};
  uint16_t index;
  if (message == NULL || message_size == 0U) return 0;
  message[0] = '\0';
  if (policy == NULL) return 0;
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    char reg_name[4];
    const char *kind_text;
    if (seed->has_section_index && seed->section_index != (uint32_t)section_index) continue;
    if (seed->has_entry_offset) {
      if (seed->entry_offset != offset) continue;
    } else if (!policy->has_entry_offset || section_index != 0U || policy->entry_offset != offset) continue;
    if (seed->reg_kind != M68K_ANALYSIS_REGISTER_DATA && seed->reg_kind != M68K_ANALYSIS_REGISTER_ADDRESS) continue;
    if (seed->reg_index >= 8U || seed->name[0] == '\0') continue;
    if (seed->kind == M68K_ANALYSIS_REGISTER_SEED_HARDWARE_INDEXED) continue;
    if (m68k_bitset_u32_has(emitted[seed->reg_kind - 1U], seed->reg_index)) continue;
    m68k_bitset_u32_set(&emitted[seed->reg_kind - 1U], seed->reg_index);
    snprintf(reg_name, sizeof(reg_name), "%c%u",
      seed->reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS ? 'A' : 'D', (unsigned)seed->reg_index);
    kind_text = seed->kind == M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE ? "base" : "type";
    if (used == 0U) {
      int wrote = snprintf(message, message_size, "KNOWN: %s %s=%s", kind_text, reg_name, seed->name);
      if (wrote < 0) return 0;
      used = (size_t)wrote < message_size ? (size_t)wrote : message_size - 1U;
    } else if (used + 4U < message_size) {
      int wrote = snprintf(message + used, message_size - used, "; %s %s=%s", kind_text, reg_name, seed->name);
      if (wrote < 0) return 0;
      used += (size_t)wrote < message_size - used ? (size_t)wrote : message_size - used - 1U;
    }
    if (seed->type_name[0] != '\0' && used + strlen(seed->type_name) + 2U < message_size) {
      message[used++] = ':';
      snprintf(message + used, message_size - used, "%s", seed->type_name);
      used = strlen(message);
    }
  }
  return used != 0U;
}

static int format_hardware_indexed_input_comment(const M68kAnalysisRegisterSeed *seed,
    char *message, size_t message_size) {
  size_t used = 0U;
  uint8_t value_index;
  size_t available = message_size - used;
  int wrote = snprintf(message + used, available, "%sINPUT contract: A%u=%s+%u*D%u.w; D%u.w in {",
    used == 0U ? "" : "; ", (unsigned)seed->reg_index, seed->name, (unsigned)seed->hardware_stride,
    (unsigned)seed->hardware_index_register, (unsigned)seed->hardware_index_register);
  if (wrote < 0) return 0;
  used += (size_t)wrote < available ? (size_t)wrote : available - 1U;
  for (value_index = 0U; value_index < seed->hardware_index_count && used + 1U < message_size; ++value_index) {
    available = message_size - used;
    wrote = snprintf(message + used, available, "%s%u", value_index == 0U ? "" : ",",
      (unsigned)seed->hardware_index_values[value_index]);
    if (wrote < 0) return 0;
    used += (size_t)wrote < available ? (size_t)wrote : available - 1U;
  }
  if (used + 1U < message_size) {
    message[used++] = '}';
    message[used] = '\0';
  }
  return used != 0U;
}

static void render_asm_policy_register_seed_comment(M68kRenderIRPreview *preview, const M68kAnalysisPolicy *policy,
    size_t section_index, uint32_t offset) {
  char comment[256], line[320];
  uint16_t index;
  if (preview == NULL || policy == NULL) return;
  if (format_policy_register_seed_comment_local(policy, section_index, offset, comment, sizeof(comment))) {
    snprintf(line, sizeof(line), "    ; %s\n", comment);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
  }
  for (index = 0U; index < policy->register_seed_count; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    if (seed->kind != M68K_ANALYSIS_REGISTER_SEED_HARDWARE_INDEXED || !seed->has_entry_offset ||
        seed->entry_offset != offset || (seed->has_section_index && seed->section_index != section_index)) continue;
    if (!format_hardware_indexed_input_comment(seed, comment, sizeof(comment))) continue;
    snprintf(line, sizeof(line), "    ; %s\n", comment);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
  }
}

void record_source_export_failure(M68kRenderIRPreview *preview, M68kSourceExportFailureKind kind,
    size_t section_index, uint32_t offset, uint32_t aux_offset) {
  if (preview == NULL || preview->asm_source_first_failure_kind != M68K_SOURCE_EXPORT_FAILURE_NONE) return;
  preview->asm_source_first_failure_kind = kind;
  preview->asm_source_first_failure_section = (uint32_t)section_index;
  preview->asm_source_first_failure_offset = offset;
  preview->asm_source_first_failure_aux_offset = aux_offset;
}

void record_numeric_runtime_ref(M68kRenderIRPreview *preview, const M68kFact *fact) {
  if (preview == NULL || fact == NULL) return;
  if (preview->asm_source_numeric_runtime_refs == 0U) {
    preview->asm_source_first_numeric_runtime_ref_section = (uint32_t)fact->section_index;
    preview->asm_source_first_numeric_runtime_ref_offset = fact->offset;
    preview->asm_source_first_numeric_runtime_ref_target_section = (uint32_t)fact->target_section_index;
    preview->asm_source_first_numeric_runtime_ref_target_offset = fact->target_offset;
    preview->asm_source_first_numeric_runtime_ref_runtime_address = fact->runtime_address;
  }
  ++preview->asm_source_numeric_runtime_refs;
}

static const char *section_base_name(const M68kDecodeSectionIR *section) {
  return section != NULL && section->name != NULL && section->name[0] != '\0' ? section->name : "section";
}

static int section_name_needs_suffix(const M68kDecodeIR *decode, size_t section_index) {
  const char *base_name;
  size_t index;
  if (decode == NULL || section_index >= decode->section_count) return 0;
  base_name = section_base_name(&decode->sections[section_index]);
  if ((decode->sections[section_index].name == NULL || decode->sections[section_index].name[0] == '\0') &&
      decode->section_count > 1U) {
    return 1;
  }
  for (index = 0U; index < decode->section_count; ++index) {
    if (index == section_index) continue;
    if (m68k_ascii_equal_ci(section_base_name(&decode->sections[index]), base_name)) return 1;
  }
  return 0;
}

static const char *rendered_section_name(const M68kDecodeIR *decode, size_t section_index, char *buffer,
    size_t buffer_size) {
  const char *base_name;
  if (buffer != NULL && buffer_size != 0U) buffer[0] = '\0';
  if (decode == NULL || section_index >= decode->section_count) return "section";
  base_name = section_base_name(&decode->sections[section_index]);
  if (!section_name_needs_suffix(decode, section_index)) return base_name;
  if (buffer == NULL || buffer_size == 0U) return base_name;
  snprintf(buffer, buffer_size, "%s_%u", base_name, (unsigned)section_index);
  return buffer;
}

static void render_asm_section_header(M68kRenderIRPreview *preview, const M68kDecodeIR *decode,
    size_t section_index) {
  char line[160];
  char name_buffer[96];
  char kind_buffer[32];
  const M68kDecodeSectionIR *section;
  const char *name;
  uint32_t allocation_size;
  if (preview == NULL || decode == NULL || section_index >= decode->section_count) return;
  section = &decode->sections[section_index];
  name = rendered_section_name(decode, section_index, name_buffer, sizeof(name_buffer));
  if (!m68k_format_section_spec(section->kind, section->platform_mem_type, section->platform_mem_attrs,
      kind_buffer, sizeof(kind_buffer))) {
    ++preview->asm_source_instruction_render_failures;
    record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, section_index, 0U, 0U);
    return;
  }
  allocation_size = section->allocation_size != 0U ? section->allocation_size : section->size;
  if (allocation_size != section->size) {
    snprintf(line, sizeof(line), "    SECTION %s,%s,$%X\n", name, kind_buffer, (unsigned)allocation_size);
  } else {
    snprintf(line, sizeof(line), "    SECTION %s,%s\n", name, kind_buffer);
  }
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static const char *render_runtime_range_kind_name(uint8_t kind) {
  switch (kind) {
  case M68K_FACT_RUNTIME_RANGE_KIND_POLICY: return "policy";
  case M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY: return "discovered_copy";
  case M68K_FACT_RUNTIME_RANGE_KIND_CONFLICTING_DISCOVERED_COPY: return "conflicting_discovered_copy";
  default: return "unknown";
  }
}

static int lookup_materialized_runtime_address_source_offset(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t runtime_address, uint32_t *out_source_offset);
static int render_absolute_ref_access_kind(uint8_t access_kind);
static uint32_t render_instruction_access_width(const M68kInstructionIR *instruction, uint8_t access_kind);
static const M68kDecodeCandidate *accepted_candidate_covering_offset_local(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, uint32_t offset);

static void render_asm_absolute_memory_header(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kSourceAnalysisIR *source_analysis, int *io_emitted_header) {
  size_t index;
  size_t emitted_count = 0U;
  if (preview == NULL || io_emitted_header == NULL) return;
  if (lookup == NULL || source_analysis == NULL || source_analysis->absolute_address_range_count == 0U) return;
  for (index = 0U; index < source_analysis->absolute_address_range_count; ++index) {
    const M68kAbsoluteAddressRangeIR *range = &source_analysis->absolute_address_ranges[index];
    char comment[160];
    char access[32];
    uint32_t end;
    if (range->status != M68K_ABSOLUTE_ADDRESS_RANGE_STATUS_UNOWNED_ONE_OFF &&
        range->status != M68K_ABSOLUTE_ADDRESS_RANGE_STATUS_UNOWNED_SPARSE) {
      continue;
    }
    if (range->owner_kind != M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY &&
        range->owner_kind != M68K_ABSOLUTE_MEMORY_OWNER_UNKNOWN) {
      continue;
    }
    if (emitted_count == 0U) {
      if (!*io_emitted_header) {
        render_asm_file_comment_line(preview, "Memory map");
        *io_emitted_header = 1;
      }
      render_asm_file_comment_line(preview, "  Absolute memory refs:");
    }
    access[0] = '\0';
    if (range->read_count != 0U) strcat(access, "r");
    if (range->write_count != 0U) strcat(access, "w");
    if (range->access_count > range->read_count + range->write_count) strcat(access, "a");
    if (access[0] == '\0') snprintf(access, sizeof(access), "-");
    end = range->range_size != 0U && range->start_address <= UINT32_MAX - range->range_size ?
      range->start_address + range->range_size : range->start_address;
    if (range->start_address == end) {
      snprintf(comment, sizeof(comment), "    absolute[$%08X] refs=%u access=%s",
        (unsigned)range->start_address, (unsigned)range->observation_count, access);
    } else {
      snprintf(comment, sizeof(comment), "    absolute[$%08X-$%08X] refs=%u access=%s",
        (unsigned)range->start_address, (unsigned)end, (unsigned)range->observation_count, access);
    }
    render_asm_file_comment_line(preview, comment);
    ++emitted_count;
  }
}

static void render_asm_memory_map_header(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, const M68kSourceAnalysisIR *source_analysis) {
  size_t index;
  int emitted_header = 0;
  if (preview == NULL || lookup == NULL || decode == NULL) return;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_ranges[index].fact;
    uint32_t storage_end;
    uint32_t runtime_end;
    uint8_t materialized = 0U;
    char section_name_buffer[96];
    char comment[384];
    const char *section_name;
    if (fact == NULL || fact->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
        fact->section_index >= decode->section_count || fact->size == 0U || !fact->has_runtime_address) {
      continue;
    }
    storage_end = fact->size <= UINT32_MAX - fact->offset ? fact->offset + fact->size : UINT32_MAX;
    runtime_end = fact->size <= UINT32_MAX - fact->runtime_address
      ? fact->runtime_address + fact->size
      : UINT32_MAX;
    if (!emitted_header) {
      render_asm_file_comment_line(preview, "Memory map");
      emitted_header = 1;
    }
    section_name = rendered_section_name(decode, fact->section_index, section_name_buffer,
      sizeof(section_name_buffer));
    (void)lookup_runtime_range_materialization(lookup, fact, &materialized, NULL, NULL);
    snprintf(comment, sizeof(comment),
      "  %s[$%08X-$%08X] -> runtime[$%08X-$%08X] %s %s",
      section_name, (unsigned)fact->offset, (unsigned)storage_end,
      (unsigned)fact->runtime_address, (unsigned)runtime_end,
      render_runtime_range_kind_name(fact->runtime_kind), materialized ? "materialized" : "suppressed");
    render_asm_file_comment_line(preview, comment);
  }
  render_asm_absolute_memory_header(preview, lookup, source_analysis, &emitted_header);
  if (emitted_header) {
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
  }
}

static int asm_source_plan_row_is_late_header(const M68kRenderPlanRow *row, size_t body_start_byte) {
  return row != NULL && row->start_byte >= body_start_byte &&
    row->region_id == M68K_RENDER_PLAN_NO_SECTION &&
    row->kind == M68K_RENDER_PLAN_ROW_DIAGNOSTIC;
}

static int append_summary_text(char *buf, size_t buf_size, size_t *io_size, const char *format, ...) {
  va_list args;
  int written;
  if (buf == NULL || io_size == NULL || *io_size >= buf_size) return -1;
  va_start(args, format);
  written = vsnprintf(buf + *io_size, buf_size - *io_size, format, args);
  va_end(args);
  if (written < 0 || (size_t)written >= buf_size - *io_size) return -1;
  *io_size += (size_t)written;
  return 0;
}

static int format_asm_os_compatibility_group_name(char *buf, size_t buf_size,
    const M68kTargetOsRequirementGroup *group) {
  int written;
  if (buf == NULL || buf_size == 0U || group == NULL) return -1;
  if (group->has_owner) {
    if (group->count > 1U) {
      written = snprintf(buf, buf_size, "%s/%s x%u", group->owner, group->call, (unsigned)group->count);
    } else {
      written = snprintf(buf, buf_size, "%s/%s", group->owner, group->call);
    }
  } else if (group->count > 1U) {
    written = snprintf(buf, buf_size, "%s x%u", group->call, (unsigned)group->count);
  } else {
    written = snprintf(buf, buf_size, "%s", group->call);
  }
  if (written < 0 || (size_t)written >= buf_size) return -1;
  return 0;
}

static int render_asm_os_compatibility_requirement_groups(char *text, size_t text_size, size_t *text_size_io,
    const M68kTargetOsCompatibilitySummary *os_summary) {
  size_t version_index;
  int emitted_header = 0;
  const size_t source_group_display_limit = 8U;
  if (os_summary == NULL) return -1;
  for (version_index = 0U; version_index < os_summary->observed_available_since_count; ++version_index) {
    const char *version = os_summary->observed_available_since[version_index];
    size_t group_index;
    size_t matching_group_count = 0U;
    uint32_t matching_call_count = 0U;
    size_t displayed_group_count = 0U;
    int emitted_version = 0;
    int emitted_group_item = 0;
    size_t rendered_line_size = 0U;
    if (strcmp(version, os_summary->minimum_required) != 0) continue;
    for (group_index = 0U; group_index < os_summary->requirement_group_count; ++group_index) {
      const M68kTargetOsRequirementGroup *group = &os_summary->requirement_groups[group_index];
      if (strcmp(group->available_since, version) != 0) continue;
      ++matching_group_count;
      matching_call_count += group->count;
    }
    if (!emitted_header) {
      if (append_summary_text(text, text_size, text_size_io, ";   requirement drivers:\n") != 0)
        return -1;
      emitted_header = 1;
    }
    if (matching_group_count > source_group_display_limit) {
      if (append_summary_text(text, text_size, text_size_io,
          ";     %s: %u recovered call sites across %u API groups\n;          first observed: ",
          version, (unsigned)matching_call_count, (unsigned)matching_group_count) != 0)
        return -1;
      emitted_version = 1;
      rendered_line_size = strlen(";          first observed: ");
    }
    for (group_index = 0U; group_index < os_summary->requirement_group_count; ++group_index) {
      const M68kTargetOsRequirementGroup *group = &os_summary->requirement_groups[group_index];
      char group_name[256];
      size_t group_name_size;
      size_t separator_size;
      if (strcmp(group->available_since, version) != 0) continue;
      if (matching_group_count > source_group_display_limit && displayed_group_count >= source_group_display_limit)
        continue;
      if (format_asm_os_compatibility_group_name(group_name, sizeof(group_name), group) != 0)
        return -1;
      group_name_size = strlen(group_name);
      if (!emitted_version) {
        if (append_summary_text(text, text_size, text_size_io, ";     %s: ", version) != 0)
          return -1;
        emitted_version = 1;
        rendered_line_size = strlen(";     ") + strlen(version) + strlen(": ");
      }
      separator_size = emitted_group_item ? 2U : 0U;
      if (rendered_line_size + separator_size + group_name_size > 118U) {
        if (append_summary_text(text, text_size, text_size_io, "\n;          ") != 0) return -1;
        rendered_line_size = strlen(";          ");
        separator_size = 0U;
        emitted_group_item = 0;
      } else if (separator_size != 0U && append_summary_text(text, text_size, text_size_io, ", ") != 0) {
        return -1;
      }
      if (append_summary_text(text, text_size, text_size_io, "%s", group_name) != 0) return -1;
      rendered_line_size += separator_size + group_name_size;
      ++displayed_group_count;
      emitted_group_item = 1;
    }
    if (emitted_version) {
      if (matching_group_count > source_group_display_limit) {
        if (append_summary_text(text, text_size, text_size_io, "\n;          remaining groups: %u; inspect JSON report\n",
            (unsigned)(matching_group_count - source_group_display_limit)) != 0)
          return -1;
      } else if (append_summary_text(text, text_size, text_size_io, "\n") != 0) {
        return -1;
      }
    }
  }
  return 0;
}

static int render_asm_os_compatibility_summary_row(M68kRenderIRPreview *preview,
    const M68kSourceAnalysisIR *source_analysis, uint8_t platform_backend_kind) {
  M68kTargetPlatformSummary summary;
  const M68kTargetOsCompatibilitySummary *os_summary;
  char text[8192];
  size_t text_size = 0U;
  if (preview == NULL || source_analysis == NULL ||
      platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  if (m68k_target_platform_summary_build(source_analysis, platform_backend_kind, &summary) != 0) return -1;
  os_summary = &summary.os_compatibility;
  if (append_summary_text(text, sizeof(text), &text_size,
      os_summary->status == M68K_TARGET_OS_COMPATIBILITY_OBSERVED
        ? "; AmigaOS compatibility, inferred from recovered OS calls\n"
        : "; AmigaOS compatibility\n") != 0) return -1;
  if (os_summary->status == M68K_TARGET_OS_COMPATIBILITY_NO_OS_CALLS) {
    if (append_summary_text(text, sizeof(text), &text_size,
        ";   required OS floor: unknown\n;   evidence: no recovered OS calls\n\n") != 0) return -1;
  } else if (os_summary->status == M68K_TARGET_OS_COMPATIBILITY_UNKNOWN) {
    if (append_summary_text(text, sizeof(text), &text_size,
        ";   required OS floor: unknown\n;   evidence: recovered OS calls lack version metadata\n\n") != 0)
      return -1;
  } else {
    size_t index;
    if (append_summary_text(text, sizeof(text), &text_size, ";   required OS floor: %s\n",
        os_summary->minimum_required) != 0)
      return -1;
    if (append_summary_text(text, sizeof(text), &text_size,
        ";   evidence: highest recovered API requirement is %s\n", os_summary->minimum_required) != 0)
      return -1;
    if (render_asm_os_compatibility_requirement_groups(text, sizeof(text), &text_size, os_summary) != 0)
      return -1;
    if (os_summary->lower_observed_available_since_count != 0U) {
      if (append_summary_text(text, sizeof(text), &text_size, ";   lower-version APIs also observed: ") != 0)
        return -1;
      for (index = 0U; index < os_summary->lower_observed_available_since_count; ++index) {
        if (append_summary_text(text, sizeof(text), &text_size, "%s%s", index == 0U ? "" : ", ",
            os_summary->lower_observed_available_since[index]) != 0)
          return -1;
      }
      if (append_summary_text(text, sizeof(text), &text_size, "\n") != 0) return -1;
    }
    if (os_summary->observed_fd_version_count != 0U) {
      if (append_summary_text(text, sizeof(text), &text_size, ";   interface metadata: ") != 0)
        return -1;
      for (index = 0U; index < os_summary->observed_fd_version_count; ++index) {
        if (append_summary_text(text, sizeof(text), &text_size, "%sFD v%s", index == 0U ? "" : ", ",
            os_summary->observed_fd_versions[index]) != 0)
          return -1;
      }
      if (append_summary_text(text, sizeof(text), &text_size, "\n") != 0) return -1;
    }
    if (os_summary->raw_requirement_drivers_truncated || os_summary->requirement_groups_truncated) {
      if (append_summary_text(text, sizeof(text), &text_size,
          ";   review: compatibility evidence truncated in summary; inspect JSON report\n") != 0)
        return -1;
    }
    if (append_summary_text(text, sizeof(text), &text_size, "\n") != 0) return -1;
  }
  if (preview->transient_row_sink != NULL) {
    const char *cursor;
    hash_asm_text(preview, text);
    for (cursor = text; *cursor != '\0'; ++cursor) {
      if (*cursor == '\n') ++preview->asm_source_lines;
    }
    return preview->asm_source_allocation_failed ? -1 : 0;
  }
  if (m68k_render_plan_append_text_row(&preview->asm_source_rows, M68K_RENDER_PLAN_ROW_DIAGNOSTIC,
      M68K_RENDER_PLAN_NO_SECTION, text, NULL) != 0) return -1;
  if (text_size > (size_t)UINT32_MAX - (size_t)preview->asm_source_bytes) return -1;
  preview->asm_source_bytes += (uint32_t)text_size;
  return 0;
}

void render_asm_org(M68kRenderIRPreview *preview, uint32_t logical_address) {
  char line[64];
  if (preview == NULL) return;
  snprintf(line, sizeof(line), "    ORG $%X\n", (unsigned)logical_address);
  if (preview->asm_source_row_builder.active)
    m68k_render_plan_row_builder_mark_current_line_directive(&preview->asm_source_row_builder);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

void render_asm_sync_logical_pc(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    size_t section_index, uint32_t source_offset, uint32_t *io_logical_pc) {
  uint32_t desired = source_offset;
  if (preview == NULL || io_logical_pc == NULL) return;
  (void)lookup_source_logical_address(lookup, section_index, source_offset, &desired);
  if (*io_logical_pc != desired) {
    uint32_t runtime=0;
    if(lookup_source_should_render_runtime_label(lookup,section_index,source_offset,&runtime))
      render_asm_runtime_org(preview,desired);
    else render_asm_org(preview,desired);
  }
  *io_logical_pc = desired;
}

static void render_asm_hex_blob_comments(M68kRenderIRPreview *preview, const char *first_prefix,
    const char *append_prefix, const uint8_t *data, uint32_t size) {
  enum { BYTES_PER_COMMENT = 64U };
  uint32_t chunk_start = 0U;
  if (preview == NULL || first_prefix == NULL || append_prefix == NULL || data == NULL || size == 0U) return;
  while (chunk_start < size) {
    uint32_t index;
    uint32_t chunk_end = chunk_start + BYTES_PER_COMMENT;
    if (chunk_end > size) chunk_end = size;
    hash_asm_text(preview, chunk_start == 0U ? first_prefix : append_prefix);
    for (index = chunk_start; index < chunk_end; ++index) {
      char token[3];
      snprintf(token, sizeof(token), "%02X", (unsigned)data[index]);
      hash_asm_text(preview, token);
    }
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
    chunk_start = chunk_end;
  }
}

static void render_asm_platform_header(M68kRenderIRPreview *preview, const M68kObject *object) {
  uint32_t program_flags = 0U;
  uint16_t relocation_flag = 0U;
  uint32_t symbol_table_type = 0U;
  const uint8_t *symbol_table = NULL, *relocation_stream = NULL;
  uint32_t symbol_table_size = 0U, relocation_stream_size = 0U;
  char line[64];
  if (preview == NULL || object == NULL) return;
  if (object->platform_backend_kind != M68K_PLATFORM_BACKEND_ATARI_ST) return;
  if (m68k_atari_st_get_program_flags(object, &program_flags) == 0) {
    snprintf(line, sizeof(line), "    COMMENT HEAD=$%x\n", (unsigned)program_flags);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
  }
  if (m68k_atari_st_get_relocation_flag(object, &relocation_flag) == 0 && relocation_flag != 0U) {
    snprintf(line, sizeof(line), "    COMMENT ATARI_RELOC_FLAG=$%04X\n", (unsigned)relocation_flag);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
  }
  if (m68k_atari_st_get_raw_symbol_table(object, &symbol_table_type, &symbol_table, &symbol_table_size) == 0) {
    if (symbol_table_type != 0U || symbol_table_size != 0U) {
      snprintf(line, sizeof(line), "    COMMENT ATARI_SYMBOL_TYPE=$%x\n", (unsigned)symbol_table_type);
      hash_asm_text(preview, line);
      ++preview->asm_source_lines;
    }
    if (symbol_table != NULL && symbol_table_size != 0U) {
      render_asm_hex_blob_comments(preview, "    COMMENT ATARI_SYMBOLS=$", "    COMMENT ATARI_SYMBOLS+=$",
        symbol_table, symbol_table_size);
    }
  }
  if (m68k_atari_st_get_raw_relocation_stream(object, &relocation_stream, &relocation_stream_size) == 0 &&
      relocation_stream != NULL && relocation_stream_size != 0U) {
    render_asm_hex_blob_comments(preview, "    COMMENT ATARI_RELOC=$", "    COMMENT ATARI_RELOC+=$",
      relocation_stream, relocation_stream_size);
  }
}

static void render_asm_relocation_expr(M68kRenderIRPreview *preview, M68kRenderLookup *lookup,
    const M68kFact *fact) {
  char line[256];
  char name[64];
  char value[32];
  char structured_comment[128];
  const char *directive;
  const M68kRenderPlannedExpression *expression;
  uint32_t numeric_value;
  if (preview == NULL || lookup == NULL || fact == NULL) return;
  if (fact->size == 4U) directive = "dc.l";
  else if (fact->size == 2U) directive = "dc.w";
  else directive = "dc.b";
  expression = m68k_render_plan_find_expression(&preview->asm_source_plan, (uint32_t)fact->section_index,
    fact->offset, UINT32_MAX, M68K_RENDER_PLANNED_EXPRESSION_RELOCATION);
  if (expression == NULL) {
    ++preview->asm_source_instruction_relocation_failures;
    record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RELOCATION,
      fact->section_index, fact->offset, fact->target_offset);
    return;
  }
  snprintf(name, sizeof(name), "%s", expression->expression);
  if (expression->outcome != M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC) {
    numeric_value = fact->target_addend >= 0 && fact->target_addend <= UINT32_MAX
      ? (uint32_t)fact->target_addend : fact->target_offset;
    format_numeric_value(value, sizeof(value), fact->size, numeric_value);
    if (fact->platform_record_kind == AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32) {
      const char *reason = lookup_offset_is_inside_relocation_payload(lookup, fact->target_section_index,
        fact->target_offset) ? "is inside another relocation payload" : "has no renderable statement boundary";
      snprintf(line, sizeof(line),
        "\t%s %s\t; facts_v2 HUNK_RELOC32 numeric: target label %s %s; left numeric\n",
        directive, value, name, reason);
      ++preview->asm_source_lossy_numeric_hunk_relocations;
    } else {
      snprintf(line, sizeof(line),
        "\t%s %s\t; facts_v2 relocation numeric: target label %s is not renderable\n",
        directive, value, name);
      ++preview->asm_source_instruction_relocation_failures;
      record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RELOCATION,
        fact->section_index, fact->offset, fact->target_offset);
    }
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
    return;
  }
  if (structured_data_item_comment(lookup_structured_data_item_at_offset(lookup, fact->section_index, fact->offset),
      structured_comment, sizeof(structured_comment))) {
    snprintf(line, sizeof(line), "\t%s %s\t; %s\n", directive, name, structured_comment);
  } else {
    snprintf(line, sizeof(line), "\t%s %s\n", directive, name);
  }
  if (record_planned_expression_target_access(preview, fact->section_index, expression, 0) != 0) {
    preview->asm_source_allocation_failed = 1U;
    return;
  }
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  ++preview->asm_source_relocation_exprs;
}

static uint32_t repeated_byte_run_length(const uint8_t *data, uint32_t offset, uint32_t size) {
  uint32_t count = 1U;
  uint8_t value;
  if (data == NULL || size == 0U) return 0U;
  value = data[offset];
  while (count < size && data[offset + count] == value) ++count;
  return count;
}

static uint32_t render_asm_dc_b_chunk_size(const uint8_t *data, uint32_t offset, uint32_t size,
    uint8_t *out_dcb) {
  enum { DCB_MIN_REPEAT = 8U };
  uint32_t line_count = size;
  uint32_t index;
  uint32_t repeat_count;
  if (out_dcb != NULL) *out_dcb = 0U;
  if (data == NULL || size == 0U) return 0U;
  repeat_count = repeated_byte_run_length(data, offset, size);
  if (repeat_count >= DCB_MIN_REPEAT) {
    if (out_dcb != NULL) *out_dcb = 1U;
    return repeat_count;
  }
  if (line_count > 16U) line_count = 16U;
  for (index = 1U; index < line_count; ++index) {
    if (repeated_byte_run_length(data, offset + index, size - index) >= DCB_MIN_REPEAT) return index;
  }
  return line_count;
}

static void render_asm_dcb_b(M68kRenderIRPreview *preview, uint32_t count, uint8_t value,
    const char *comment) {
  char line[128];
  if (preview == NULL || count == 0U) return;
  if (comment != NULL && comment[0] != '\0')
    snprintf(line, sizeof(line), "\tdcb.b $%X,$%02X\t; %s\n", (unsigned)count, (unsigned)value, comment);
  else
    snprintf(line, sizeof(line), "\tdcb.b $%X,$%02X\n", (unsigned)count, (unsigned)value);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static void render_asm_dc_b_values_line(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t count, const char *comment) {
  uint32_t index;
  if (preview == NULL || data == NULL || count == 0U) return;
  hash_asm_text(preview, "\tdc.b ");
  for (index = 0U; index < count; ++index) {
    char token[8];
    if (index != 0U) hash_asm_text(preview, ",");
    snprintf(token, sizeof(token), "$%02X", (unsigned)data[offset + index]);
    hash_asm_text(preview, token);
  }
  if (comment != NULL && comment[0] != '\0') {
    hash_asm_text(preview, "\t; ");
    hash_asm_text(preview, comment);
  }
  hash_asm_text(preview, "\n");
  ++preview->asm_source_lines;
}

static void render_asm_dc_b(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t size, const char *comment) {
  uint32_t cursor = 0U;
  if (preview == NULL || data == NULL) return;
  while (cursor < size) {
    uint8_t is_dcb = 0U;
    uint32_t chunk_size = render_asm_dc_b_chunk_size(data, offset + cursor, size - cursor, &is_dcb);
    if (chunk_size == 0U) return;
    if (is_dcb) render_asm_dcb_b(preview, chunk_size, data[offset + cursor], comment);
    else render_asm_dc_b_values_line(preview, data, offset + cursor, chunk_size, comment);
    cursor += chunk_size;
  }
}

static void render_asm_dc_w_values(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t size, const char *comment);

static void render_asm_data_dc_b_plan_rows(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    size_t section_index, const M68kDecodeSectionIR *section, uint32_t offset, uint32_t size, const char *comment,
    uint32_t *io_logical_pc) {
  uint32_t cursor = 0U;
  if (preview == NULL || section == NULL || section->data == NULL) return;
  if ((offset & 1U) == 0U && size == 2U && section->data[offset] == 0U && section->data[offset + 1U] == 0U &&
      !lookup_has_label(lookup, section->section_index, offset + 1U)) {
    M68kRenderPlanRow *row;
    begin_asm_source_plan_row(preview, M68K_RENDER_PLAN_ROW_DATA, (uint32_t)section_index);
    render_asm_dc_w_values(preview, section->data, offset, size, comment);
    row = finish_asm_source_plan_row(preview, section->section_index, offset, size, 1);
    set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_DATA, NULL, section, offset, size);
    return;
  }
  while (cursor < size) {
    M68kRenderPlanRow *row;
    uint8_t is_dcb = 0U;
    uint32_t probe;
    uint32_t chunk_size = render_asm_dc_b_chunk_size(section->data, offset + cursor, size - cursor, &is_dcb);
    if (chunk_size == 0U) return;
    if (cursor != 0U &&
        (lookup_has_label(lookup, section->section_index, offset + cursor) ||
         lookup_structured_long_table_targets_offset(lookup, section->section_index, offset + cursor))) {
      begin_asm_source_plan_row(preview, M68K_RENDER_PLAN_ROW_LABEL, (uint32_t)section_index);
      render_asm_label(preview, lookup, section->section_index, offset + cursor, io_logical_pc);
      row = finish_asm_source_plan_row(preview, section->section_index, offset + cursor, 0U, 1);
      set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_LABEL, NULL, section, offset + cursor, 0U);
    }
    for (probe = 1U; probe < chunk_size; ++probe) {
      if (lookup_has_label(lookup, section->section_index, offset + cursor + probe) ||
          lookup_structured_long_table_targets_offset(lookup, section->section_index, offset + cursor + probe)) {
        chunk_size = probe;
        break;
      }
    }
    begin_asm_source_plan_row(preview, M68K_RENDER_PLAN_ROW_DATA, (uint32_t)section_index);
    if (is_dcb) render_asm_dcb_b(preview, chunk_size, section->data[offset + cursor], comment);
    else render_asm_dc_b_values_line(preview, section->data, offset + cursor, chunk_size, comment);
    row = finish_asm_source_plan_row(preview, section->section_index, offset + cursor, chunk_size, 1);
    set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_DATA, NULL, section, offset + cursor,
      chunk_size);
    cursor += chunk_size;
  }
}

static int byte_is_quoted_character_safe(uint8_t value) {
  return value >= 0x20U && value <= 0x7eU && value != '\'' && value != '\\';
}

static void render_asm_dc_b_string_slice(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t size, const char *comment) {
  uint32_t cursor;
  int wrote = 0;
  if (preview == NULL || data == NULL || size == 0U) return;
  hash_asm_text(preview, "\tdc.b ");
  cursor = 0U;
  while (cursor < size) {
    if (m68k_ir_byte_is_quoted_string_safe(data[offset + cursor])) {
      char byte_text[2];
      if (wrote) hash_asm_text(preview, ",");
      hash_asm_text(preview, "\"");
      while (cursor < size && m68k_ir_byte_is_quoted_string_safe(data[offset + cursor])) {
        byte_text[0] = (char)data[offset + cursor];
        byte_text[1] = '\0';
        hash_asm_text(preview, byte_text);
        ++cursor;
      }
      hash_asm_text(preview, "\"");
      wrote = 1;
    } else {
      char token[8];
      if (wrote) hash_asm_text(preview, ",");
      snprintf(token, sizeof(token), "$%02X", (unsigned)data[offset + cursor]);
      hash_asm_text(preview, token);
      ++cursor;
      wrote = 1;
    }
  }
  if (comment != NULL && comment[0] != '\0') {
    hash_asm_text(preview, "\t; ");
    hash_asm_text(preview, comment);
  }
  hash_asm_text(preview, "\n");
  ++preview->asm_source_lines;
}

static int string_span_has_line_break(const uint8_t *data, uint32_t offset, uint32_t size) {
  uint32_t cursor;
  if (data == NULL) return 0;
  for (cursor = 0U; cursor < size; ++cursor) {
    uint8_t value = data[offset + cursor];
    if (value == 0x0dU || value == 0x0aU) return 1;
  }
  return 0;
}

static int structured_data_item_is_multiline_text(const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_STRING &&
    item->source_pattern_id == M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_MULTILINE_TEXT;
}

static void render_asm_dc_b_string(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t size, const char *comment) {
  uint32_t cursor = 0U;
  if (preview == NULL || data == NULL || size == 0U) return;
  if (!string_span_has_line_break(data, offset, size)) {
    render_asm_dc_b_string_slice(preview, data, offset, size, comment);
    return;
  }
  while (cursor < size) {
    uint32_t line_start = cursor;
    uint32_t line_size;
    while (cursor < size && data[offset + cursor] != 0x0dU && data[offset + cursor] != 0x0aU) ++cursor;
    if (cursor < size) {
      do {
        ++cursor;
      } while (cursor < size && (data[offset + cursor] == 0x0dU || data[offset + cursor] == 0x0aU));
    }
    line_size = cursor - line_start;
    if (line_size == 0U) line_size = size - line_start;
    render_asm_dc_b_string_slice(preview, data, offset + line_start, line_size,
      line_start == 0U ? comment : NULL);
  }
}

static const M68kAnalysisManualRepresentation *lookup_manual_representation_at(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  uint16_t index;
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  if (!m68k_analysis_policy_manual_representations_valid(policy)) return NULL;
  for (index = 0U; index < policy->manual_representation_count; ++index) {
    const M68kAnalysisManualRepresentation *representation = &policy->manual_representations[index];
    if (representation->has_section_index && representation->section_index == section_index &&
        !representation->has_operand_index && representation->offset == offset && representation->size != 0U) {
      return representation;
    }
  }
  return NULL;
}

const M68kAnalysisManualRepresentation *lookup_manual_operand_representation(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset, size_t operand_index) {
  uint16_t index;
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  if (!m68k_analysis_policy_manual_representations_valid(policy) || operand_index > 3U) return NULL;
  for (index = 0U; index < policy->manual_representation_count; ++index) {
    const M68kAnalysisManualRepresentation *representation = &policy->manual_representations[index];
    if (representation->has_section_index && representation->section_index == section_index &&
        representation->has_operand_index && representation->operand_index == operand_index &&
        representation->offset == offset && representation->size != 0U) {
      return representation;
    }
  }
  return NULL;
}

static uint32_t next_manual_representation_offset(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint32_t limit) {
  uint16_t index;
  uint32_t next = limit;
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  if (!m68k_analysis_policy_manual_representations_valid(policy)) return limit;
  for (index = 0U; index < policy->manual_representation_count; ++index) {
    const M68kAnalysisManualRepresentation *representation = &policy->manual_representations[index];
    if (representation->has_section_index && representation->section_index == section_index &&
        !representation->has_operand_index && representation->offset > offset && representation->offset < next) {
      next = representation->offset;
    }
  }
  return next;
}

static void render_asm_dc_b_binary_line(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t count, const char *comment) {
  uint32_t index;
  if (preview == NULL || data == NULL || count == 0U) return;
  hash_asm_text(preview, "\tdc.b ");
  for (index = 0U; index < count; ++index) {
    char token[12];
    uint8_t value = data[offset + index];
    if (index != 0U) hash_asm_text(preview, ",");
    snprintf(token, sizeof(token), "%%%u%u%u%u%u%u%u%u",
      (unsigned)((value >> 7U) & 1U), (unsigned)((value >> 6U) & 1U),
      (unsigned)((value >> 5U) & 1U), (unsigned)((value >> 4U) & 1U),
      (unsigned)((value >> 3U) & 1U), (unsigned)((value >> 2U) & 1U),
      (unsigned)((value >> 1U) & 1U), (unsigned)(value & 1U));
    hash_asm_text(preview, token);
  }
  if (comment != NULL && comment[0] != '\0') {
    hash_asm_text(preview, "\t; ");
    hash_asm_text(preview, comment);
  }
  hash_asm_text(preview, "\n");
  ++preview->asm_source_lines;
}

static void render_asm_dc_b_character_line(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t count, const char *comment) {
  uint32_t index;
  if (preview == NULL || data == NULL || count == 0U) return;
  hash_asm_text(preview, "\tdc.b ");
  for (index = 0U; index < count; ++index) {
    char token[12];
    uint8_t value = data[offset + index];
    if (index != 0U) hash_asm_text(preview, ",");
    if (byte_is_quoted_character_safe(value))
      snprintf(token, sizeof(token), "'%c'", (char)value);
    else
      snprintf(token, sizeof(token), "$%02X", (unsigned)value);
    hash_asm_text(preview, token);
  }
  if (comment != NULL && comment[0] != '\0') {
    hash_asm_text(preview, "\t; ");
    hash_asm_text(preview, comment);
  }
  hash_asm_text(preview, "\n");
  ++preview->asm_source_lines;
}

static int render_plan_should_emit_data_label_statement(const M68kRenderIRPreview *preview,
    const M68kDecodeSectionIR *section, uint32_t offset) {
  return preview != NULL && section != NULL && section->section_index <= UINT32_MAX &&
    m68k_render_plan_find_label(&preview->asm_source_plan, (uint32_t)section->section_index, offset) != NULL;
}

static void render_asm_manual_representation_dc_b(M68kRenderIRPreview *preview,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t offset, uint32_t size,
    const M68kRenderLookup *lookup, const M68kAnalysisManualRepresentation *representation, const char *comment) {
  uint32_t cursor = 0U;
  const uint8_t *data = section != NULL ? section->data : NULL;
  uint8_t style_id = representation != NULL ? representation->style_id : M68K_ANALYSIS_REPRESENTATION_STYLE_NONE;
  (void)accepted_start;
  if (preview == NULL || data == NULL || size == 0U) return;
  if (style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL && (size == 1U || size == 2U || size == 4U)) {
    const char *symbol_name = manual_representation_symbol_name(lookup, representation);
    if (symbol_name != NULL && asm_symbol_name_is_safe_local(symbol_name)) {
      render_asm_dc_symbol_expr(preview, size, symbol_name, comment);
      return;
    }
  }
  if (style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_STRING) {
    cursor = 0U;
    while (cursor < size) {
      uint32_t chunk_size = size - cursor;
      uint32_t probe;
      if (cursor != 0U && render_plan_should_emit_data_label_statement(preview, section, offset + cursor)) {
        render_asm_label(preview, lookup, section->section_index, offset + cursor, NULL);
      }
      for (probe = 1U; probe < chunk_size; ++probe) {
        if (render_plan_should_emit_data_label_statement(preview, section, offset + cursor + probe)) {
          chunk_size = probe;
          break;
        }
      }
      render_asm_dc_b_string(preview, data, offset + cursor, chunk_size, cursor == 0U ? comment : NULL);
      cursor += chunk_size;
    }
    return;
  }
  while (cursor < size) {
    uint32_t chunk_size = size - cursor;
    if (chunk_size > 16U) chunk_size = 16U;
    if (style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_BINARY)
      render_asm_dc_b_binary_line(preview, data, offset + cursor, chunk_size, cursor == 0U ? comment : NULL);
    else if (style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_CHARACTER)
      render_asm_dc_b_character_line(preview, data, offset + cursor, chunk_size, cursor == 0U ? comment : NULL);
    else
      render_asm_dc_b(preview, data, offset + cursor, chunk_size, cursor == 0U ? comment : NULL);
    cursor += chunk_size;
  }
}

static void render_asm_dc_b_with_policy(M68kRenderIRPreview *preview, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kRenderLookup *lookup, uint32_t offset, uint32_t size,
    const char *comment) {
  uint32_t cursor = 0U;
  uint32_t limit;
  if (preview == NULL || section == NULL || section->data == NULL || size == 0U) return;
  limit = offset + size;
  while (cursor < size) {
    uint32_t current = offset + cursor;
    uint32_t probe;
    const M68kAnalysisManualRepresentation *representation =
      lookup_manual_representation_at(lookup, section->section_index, current);
    if (cursor != 0U && render_plan_should_emit_data_label_statement(preview, section, current)) {
      render_asm_label(preview, lookup, section->section_index, current, NULL);
    }
    if (representation != NULL) {
      uint32_t chunk_size = representation->size;
      if (chunk_size > size - cursor) chunk_size = size - cursor;
      for (probe = 1U; probe < chunk_size; ++probe) {
        if (render_plan_should_emit_data_label_statement(preview, section, current + probe)) {
          chunk_size = probe;
          break;
        }
      }
      render_asm_manual_representation_dc_b(preview, section, accepted_start, current, chunk_size, lookup,
        representation, cursor == 0U ? comment : NULL);
      cursor += chunk_size;
    } else {
      uint32_t next = next_manual_representation_offset(lookup, section->section_index, current, limit);
      uint32_t chunk_size = next > current ? next - current : size - cursor;
      if (chunk_size > size - cursor) chunk_size = size - cursor;
      for (probe = 1U; probe < chunk_size; ++probe) {
        if (render_plan_should_emit_data_label_statement(preview, section, current + probe)) {
          chunk_size = probe;
          break;
        }
      }
      render_asm_dc_b(preview, section->data, current, chunk_size, cursor == 0U ? comment : NULL);
      cursor += chunk_size;
    }
  }
}

static int render_asm_manual_symbol_representation(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset, uint32_t size, const char *comment) {
  const M68kAnalysisManualRepresentation *representation;
  const char *symbol_name;
  if (size != 1U && size != 2U && size != 4U) return 0;
  representation = lookup_manual_representation_at(lookup, section_index, offset);
  if (representation == NULL || representation->size != size ||
      representation->style_id != M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL) {
    return 0;
  }
  symbol_name = manual_representation_symbol_name(lookup, representation);
  if (symbol_name == NULL || !asm_symbol_name_is_safe_local(symbol_name)) return 0;
  render_asm_dc_symbol_expr(preview, size, symbol_name, comment);
  return 1;
}

static void render_asm_dc_b_length_prefixed_string(M68kRenderIRPreview *preview, const uint8_t *data,
    uint32_t offset, uint32_t size, const char *comment) {
  char token[16];
  uint32_t cursor;
  if (preview == NULL || data == NULL || size == 0U) return;
  snprintf(token, sizeof(token), "\tdc.b $%02X", (unsigned)data[offset]);
  hash_asm_text(preview, token);
  if (size > 1U) {
    hash_asm_text(preview, ",\"");
    for (cursor = 1U; cursor < size && m68k_ir_byte_is_quoted_string_safe(data[offset + cursor]); ++cursor) {
      char byte_text[2];
      byte_text[0] = (char)data[offset + cursor];
      byte_text[1] = '\0';
      hash_asm_text(preview, byte_text);
    }
    hash_asm_text(preview, "\"");
    if (cursor < size) {
      for (; cursor < size; ++cursor) {
        snprintf(token, sizeof(token), ",$%02X", (unsigned)data[offset + cursor]);
        hash_asm_text(preview, token);
      }
    }
  }
  if (comment != NULL && comment[0] != '\0') {
    hash_asm_text(preview, "\t; ");
    hash_asm_text(preview, comment);
  }
  hash_asm_text(preview, "\n");
  ++preview->asm_source_lines;
}

static void render_asm_ds_b(M68kRenderIRPreview *preview, uint32_t size, const char *comment) {
  char line[96];
  if (preview == NULL || size == 0U) return;
  if (comment != NULL && comment[0] != '\0')
    snprintf(line, sizeof(line), "\tDS.B $%X\t; %s\n", (unsigned)size, comment);
  else
    snprintf(line, sizeof(line), "\tDS.B $%X\n", (unsigned)size);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static void render_asm_dc_w_values(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t size, const char *comment) {
  uint32_t cursor = 0U;
  if (preview == NULL || data == NULL || size == 0U) return;
  while (cursor + 2U <= size) {
    uint32_t line_count = (size - cursor) / 2U;
    uint32_t index;
    if (line_count > 8U) line_count = 8U;
    hash_asm_text(preview, "\tdc.w ");
    for (index = 0U; index < line_count; ++index) {
      char token[16];
      if (index != 0U) hash_asm_text(preview, ",");
      snprintf(token, sizeof(token), "$%04X", (unsigned)m68k_read_u16be(data + offset + cursor + (index * 2U)));
      hash_asm_text(preview, token);
    }
    if (comment != NULL && comment[0] != '\0') {
      hash_asm_text(preview, "\t; ");
      hash_asm_text(preview, comment);
    }
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
    cursor += line_count * 2U;
  }
  if (cursor < size) render_asm_dc_b(preview, data, offset + cursor, size - cursor, comment);
}

static void render_asm_dc_l_values(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t size, const char *comment) {
  uint32_t cursor = 0U;
  if (preview == NULL || data == NULL || size == 0U) return;
  while (cursor + 4U <= size) {
    uint32_t line_count = (size - cursor) / 4U;
    uint32_t index;
    if (line_count > 4U) line_count = 4U;
    hash_asm_text(preview, "\tdc.l ");
    for (index = 0U; index < line_count; ++index) {
      char token[16];
      if (index != 0U) hash_asm_text(preview, ",");
      snprintf(token, sizeof(token), "$%08X", (unsigned)m68k_read_u32be(data + offset + cursor + (index * 4U)));
      hash_asm_text(preview, token);
    }
    if (comment != NULL && comment[0] != '\0') {
      hash_asm_text(preview, "\t; ");
      hash_asm_text(preview, comment);
    }
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
    cursor += line_count * 4U;
  }
  if (cursor < size) render_asm_dc_b(preview, data, offset + cursor, size - cursor, comment);
}

static int structured_data_item_is_pointer_table(const M68kAnalysisStructuredDataItem *item);
static int structured_data_item_is_absolute_long_lookup_table(const M68kAnalysisStructuredDataItem *item);
static int lookup_any_runtime_address_source_offset(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t runtime_address, uint32_t section_size, uint32_t *out_source_offset);
static int lookup_exact_pointer_value_label_offset(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t section_size, uint32_t value, uint8_t allow_in_section_source_offset, uint32_t *out_source_offset);
static int lookup_structured_item_probe_has_blocking_boundary(const M68kRenderLookup *lookup,
    const M68kAnalysisStructuredDataItem *structured_item, size_t section_index, uint32_t probe, int include_labels);
static int accepted_byte_at(const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes, uint32_t offset);

/* Only compact literal units within one already-bounded leaf. Pointer tables,
 * domains and authored expressions keep their individual semantic entries. */
static int render_asm_uniform_literal_array(M68kRenderIRPreview *preview,
    const M68kDecodeSectionIR *section, const M68kRenderLookup *lookup,
    const M68kAnalysisStructuredDataItem *item, uint32_t offset, uint32_t size,
    uint32_t width, const char *comment) {
  uint32_t cursor, value;
  size_t index;
  char line[192], token[16];
  const char *suffix;
  const M68kAnalysisManualRepresentation *representation;
  if (preview == NULL || section == NULL || section->data == NULL || lookup == NULL || item == NULL ||
      (item->kind != M68K_ANALYSIS_STRUCTURED_DATA_BYTES && item->kind != M68K_ANALYSIS_STRUCTURED_DATA_WORDS &&
       item->kind != M68K_ANALYSIS_STRUCTURED_DATA_LONGS) ||
      (width != 1U && width != 2U && width != 4U) || size % width != 0U || size / width < 8U ||
      item->is_pointer || item->has_target || item->pointer_struct[0] != '\0' || item->has_constant_value ||
      item->constant_name[0] != '\0' || item->value_domain[0] != '\0' ||
      offset > section->size || size > section->size - offset) return 0;
  representation = lookup_manual_representation_at(lookup, section->section_index, offset);
  if (representation != NULL && representation->style_id != M68K_ANALYSIS_REPRESENTATION_STYLE_HEX) return 0;
  for (cursor = width; cursor < size; cursor += width) {
    if (memcmp(section->data + offset, section->data + offset + cursor, width) != 0) return 0;
  }
  for (index = 0U; index < preview->asm_source_plan.expression_count; ++index) {
    const M68kRenderPlannedExpression *expression = &preview->asm_source_plan.expressions[index];
    if (expression->source_section_index == section->section_index && expression->source_offset >= offset &&
        expression->source_offset - offset < size) return 0;
  }
  value = width == 4U ? m68k_read_u32be(section->data + offset) :
    width == 2U ? m68k_read_u16be(section->data + offset) : section->data[offset];
  suffix = width == 4U ? "l" : width == 2U ? "w" : "b";
  format_numeric_value(token, sizeof(token), width, value);
  /* Suppress only the synthesized generic role, never an authored comment or
   * a named structure member, even when its text happens to be 'data'. */
  if (comment != NULL && strcmp(comment, "data") == 0 && item->comment[0] == '\0' &&
      item->struct_name[0] == '\0') comment = NULL;
  if (comment != NULL && comment[0] != '\0')
    snprintf(line, sizeof(line), "\tdcb.%s $%X,%s\t; %s\n", suffix, (unsigned)(size / width), token, comment);
  else
    snprintf(line, sizeof(line), "\tdcb.%s $%X,%s\n", suffix, (unsigned)(size / width), token);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  return 1;
}

static void render_asm_structured_raw_data_with_labels(M68kRenderIRPreview *preview,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const M68kRenderLookup *lookup,
    const M68kAnalysisStructuredDataItem *item, uint32_t offset, uint32_t size, uint32_t width,
    const char *comment, uint32_t *io_logical_pc) {
  uint32_t cursor = 0U;
  if (preview == NULL || section == NULL || lookup == NULL || item == NULL || section->data == NULL || size == 0U)
    return;
  while (cursor < size) {
    uint32_t current = offset + cursor;
    uint32_t chunk_size = size - cursor;
    uint32_t probe;
    if (cursor != 0U && render_plan_should_emit_data_label_statement(preview, section, current)) {
      render_asm_label(preview, lookup, section->section_index, current, io_logical_pc);
    }
    if (cursor != 0U) {
      render_asm_policy_entry_comments(preview, lookup->policy, section->section_index, current);
      render_asm_comment_line(preview, lookup_instruction_comment(lookup, section->section_index, current));
    }
    if (lookup->policy != NULL) {
      uint16_t index;
      for (index = 0U; index < lookup->policy->entry_comment_count && index < M68K_ANALYSIS_ENTRY_COMMENT_LIMIT; ++index) {
        const M68kAnalysisEntryComment *entry = &lookup->policy->entry_comments[index];
        if ((!entry->has_section_index || entry->section_index == section->section_index) &&
            entry->comment[0] != '\0' && entry->offset > current && entry->offset - current < chunk_size)
          chunk_size = entry->offset - current;
      }
    }
    for (probe = 1U; probe < chunk_size; ++probe) {
      if (render_plan_should_emit_data_label_statement(preview, section, current + probe) ||
          lookup_instruction_comment(lookup, section->section_index, current + probe) != NULL) {
        chunk_size = probe;
        break;
      }
    }
    {
      const M68kAnalysisManualRepresentation *representation = lookup_manual_representation_at(
        lookup, section->section_index, current);
      if (representation != NULL && representation->size <= chunk_size &&
          render_asm_manual_symbol_representation(preview, lookup, section->section_index, current,
            representation->size, cursor == 0U ? comment : NULL)) {
        if (io_logical_pc != NULL) *io_logical_pc += representation->size;
        cursor += representation->size;
        continue;
      }
      /* A later scalar interpretation is a boundary within the same owner. */
      chunk_size = next_manual_representation_offset(lookup, section->section_index,
        current, current + chunk_size) - current;
    }
    if (width == 2U) {
      const M68kRenderPlannedExpression *expression = m68k_render_plan_find_expression(
        &preview->asm_source_plan, (uint32_t)section->section_index, current, UINT32_MAX,
        M68K_RENDER_PLANNED_EXPRESSION_RELATIVE);
      if (expression != NULL && expression->outcome == M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC && chunk_size >= 2U) {
        render_asm_dc_symbol_expr(preview, 2U, expression->expression, cursor == 0U ? comment : NULL);
        if (record_planned_expression_target_access(preview, section->section_index, expression, 0) != 0 ||
            record_planned_expression_target_access(preview, section->section_index, expression, 1) != 0)
          preview->asm_source_allocation_failed = 1U;
        if (io_logical_pc != NULL) *io_logical_pc += 2U;
        cursor += 2U;
        continue;
      }
      for (probe = 2U; probe + 2U <= chunk_size; probe += 2U) {
        expression = m68k_render_plan_find_expression(&preview->asm_source_plan,
          (uint32_t)section->section_index, current + probe, UINT32_MAX, M68K_RENDER_PLANNED_EXPRESSION_RELATIVE);
        if (expression != NULL && expression->outcome == M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC) {
          chunk_size = probe;
          break;
        }
      }
    }
    if (render_asm_uniform_literal_array(preview, section, lookup, item, current, chunk_size, width,
        cursor == 0U ? comment : NULL)) {
      /* The shared logical-PC update below accounts for every repeated unit. */
    } else if (width == 4U && chunk_size >= 4U && (chunk_size & 3U) == 0U) {
      render_asm_dc_l_values(preview, section->data, current, chunk_size, cursor == 0U ? comment : NULL);
    } else if (width >= 2U && chunk_size >= 2U && (chunk_size & 1U) == 0U) {
      render_asm_dc_w_values(preview, section->data, current, chunk_size, cursor == 0U ? comment : NULL);
    } else {
      render_asm_dc_b_with_policy(preview, section, accepted_start, lookup, current, chunk_size,
        cursor == 0U ? comment : NULL);
    }
    if (io_logical_pc != NULL) *io_logical_pc += chunk_size;
    cursor += chunk_size;
  }
}

static int lookup_exact_pointer_value_label_offset(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t section_size, uint32_t value, uint8_t allow_in_section_source_offset, uint32_t *out_source_offset) {
  size_t index;
  uint32_t logical_address = 0U;
  int value_is_in_section_source_offset = 0;
  if (out_source_offset != NULL) *out_source_offset = 0U;
  if (lookup == NULL) return 0;
  if (lookup->runtime_address_ranges != NULL) {
    for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
      const M68kFact *fact = lookup->runtime_address_ranges[index].fact;
      uint32_t delta;
      uint32_t source_offset;
      logical_address = 0U;
      if (!runtime_range_is_materialized(lookup, fact) || fact->section_index != section_index ||
          !fact->has_runtime_address || value < fact->runtime_address) {
        continue;
      }
      delta = value - fact->runtime_address;
      if (delta >= fact->size || fact->offset > UINT32_MAX - delta) continue;
      source_offset = fact->offset + delta;
      if (source_offset >= section_size) continue;
      if (!lookup_source_logical_address(lookup, section_index, source_offset, &logical_address) ||
          logical_address != value) {
        continue;
      }
      if (out_source_offset != NULL) *out_source_offset = source_offset;
      return 1;
    }
  }
  if (value < section_size &&
      lookup_source_logical_address(lookup, section_index, value, &logical_address)) {
    value_is_in_section_source_offset = 1;
    if (allow_in_section_source_offset ||
        (logical_address == value && lookup_has_renderable_label(lookup, section_index, value))) {
      if (out_source_offset != NULL) *out_source_offset = value;
      return 1;
    }
  }
  if (!value_is_in_section_source_offset &&
      lookup_any_runtime_address_source_offset(lookup, section_index, value, section_size, out_source_offset)) {
    return 1;
  }
  return 0;
}

static uint8_t resolve_runtime_only_pointer_expression(const M68kRenderLookup *lookup,
    const M68kAnalysisStructuredDataItem *item, uint32_t value, M68kRenderPlannedExpression *expression) {
  const M68kAnalysisTargetEquate *selected = NULL;
  uint16_t index;
  for (index = 0U; lookup->policy != NULL && index < lookup->policy->target_equate_count; ++index) {
    const M68kAnalysisTargetEquate *candidate = &lookup->policy->target_equates[index];
    uint32_t base = (uint32_t)candidate->value;
    if (!candidate->address_domain || candidate->extent_bytes == 0U || value < base ||
        value - base >= candidate->extent_bytes || strcmp(candidate->group, item->pointer_symbol_group) != 0) continue;
    if (selected != NULL) {
      expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_NUMERIC;
      snprintf(expression->reason, sizeof(expression->reason), "ambiguous_runtime_symbol");
      return expression->outcome;
    }
    selected = candidate;
  }
  if (selected == NULL) {
    expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_NUMERIC;
    snprintf(expression->reason, sizeof(expression->reason), "unmapped_runtime_symbol");
    return expression->outcome;
  }
  if (value - (uint32_t)selected->value > INT32_MAX) {
    expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_NUMERIC;
    snprintf(expression->reason, sizeof(expression->reason), "unsupported_addend");
    return expression->outcome;
  }
  expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC;
  expression->requires_declaration = 0U;
  expression->addend = (int32_t)(value - (uint32_t)selected->value);
  snprintf(expression->target_symbol, sizeof(expression->target_symbol), "%s", selected->name);
  if (value == (uint32_t)selected->value)
    snprintf(expression->expression, sizeof(expression->expression), "%s", selected->name);
  else
    snprintf(expression->expression, sizeof(expression->expression), "%s+$%X", selected->name,
      (unsigned)(value - (uint32_t)selected->value));
  snprintf(expression->reason, sizeof(expression->reason), "resolved_runtime_symbol");
  return expression->outcome;
}

static uint8_t resolve_owned_source_pointer_expression(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start,
    uint32_t value, uint32_t section, uint32_t offset, int require_owner,
    M68kRenderPlannedExpression *expression) {
  uint32_t logical = 0U;
  const M68kDecodeSectionIR *target_section = NULL;
  const uint8_t *target_accepted_start = NULL;
  const M68kAnalysisStructuredDataItem *owner = NULL;
  uint32_t owner_start = 0U, owner_size = 0U;
  size_t decode_index;
  uint16_t index;
  expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_NUMERIC;
  if (section >= lookup->section_count || offset >= lookup->label_extents[section]) {
    snprintf(expression->reason, sizeof(expression->reason), "unmapped_source");
    return expression->outcome;
  }
  for (decode_index = 0U; decode != NULL && accepted_start != NULL && decode_index < decode->section_count; ++decode_index) {
    if (decode->sections[decode_index].section_index == section) {
      target_section = &decode->sections[decode_index];
      target_accepted_start = accepted_start[decode_index];
      break;
    }
  }
  for (index = 0U; lookup->policy != NULL && index < lookup->policy->structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *candidate = &lookup->policy->structured_data_items[index];
    uint32_t candidate_start = candidate->has_source_owner_span ? candidate->source_owner_start : candidate->offset;
    uint32_t candidate_size = candidate->has_source_owner_span ? candidate->source_owner_size : candidate->size;
    if ((candidate->has_section_index && candidate->section_index != section) || candidate->label[0] == '\0' ||
        candidate->table_conflicted || candidate->size == 0U || candidate_size < candidate->size ||
        candidate_start != candidate->offset || offset < candidate_start ||
        offset - candidate_start >= candidate_size || target_section == NULL ||
        candidate_start > target_section->size || candidate_size > target_section->size - candidate_start ||
        !render_asm_should_emit_label_statement(NULL, lookup, target_section, target_accepted_start,
          section, candidate->offset)) continue;
    if (owner == NULL || candidate_size < owner_size) {
      owner = candidate;
      owner_start = candidate_start;
      owner_size = candidate_size;
    }
  }
  if (require_owner && owner == NULL) {
    snprintf(expression->reason, sizeof(expression->reason), "missing_source_owner");
    return expression->outcome;
  }
  expression->target_section_index = section;
  expression->target_offset = offset;
  if (target_section != NULL && lookup_label_has_explicit_name(lookup, section, offset) &&
      render_asm_should_emit_label_statement(NULL, lookup, target_section, target_accepted_start, section, offset) &&
      lookup_source_logical_address(lookup, section, offset, &logical) && logical == value) {
    (void)format_rendered_asm_label_with_generation(lookup, expression->target_symbol,
      sizeof(expression->target_symbol), section, offset);
    snprintf(expression->expression, sizeof(expression->expression), "%s", expression->target_symbol);
  } else if (owner != NULL) {
    uint32_t delta = offset - owner_start;
    if (delta > INT32_MAX || !lookup_source_logical_address(lookup, section, owner_start, &logical) ||
        (uint64_t)logical + delta != value) {
      snprintf(expression->reason, sizeof(expression->reason), "encoded_value_mismatch");
      return expression->outcome;
    }
    (void)format_rendered_asm_label_with_generation(lookup, expression->target_symbol,
      sizeof(expression->target_symbol), section, owner_start);
    expression->addend = (int32_t)delta;
    if (delta == 0U) snprintf(expression->expression, sizeof(expression->expression), "%s", expression->target_symbol);
    else snprintf(expression->expression, sizeof(expression->expression), "%s+$%X", expression->target_symbol, (unsigned)delta);
  } else if (target_section != NULL &&
      render_asm_should_emit_label_statement(NULL, lookup, target_section, target_accepted_start, section, offset) &&
      lookup_source_logical_address(lookup, section, offset, &logical) && logical == value) {
    (void)format_rendered_asm_label_with_generation(lookup, expression->target_symbol,
      sizeof(expression->target_symbol), section, offset);
    snprintf(expression->expression, sizeof(expression->expression), "%s", expression->target_symbol);
  } else {
    snprintf(expression->reason, sizeof(expression->reason), "missing_source_owner");
    return expression->outcome;
  }
  if (expression->target_symbol[0] == '\0') {
    snprintf(expression->reason, sizeof(expression->reason), "missing_source_owner");
    return expression->outcome;
  }
  expression->has_target = 1U;
  expression->requires_declaration = 0U;
  expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC;
  snprintf(expression->reason, sizeof(expression->reason), "resolved_source");
  return expression->outcome;
}

static uint8_t resolve_mapped_source_pointer_expression(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start,
    uint32_t value, M68kRenderPlannedExpression *expression) {
  uint32_t section = 0U, offset = 0U;
  int resolution = m68k_analysis_policy_resolve_pointer_address(lookup->policy, value, &section, &offset);
  if (resolution != 1) {
    expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_NUMERIC;
    snprintf(expression->reason, sizeof(expression->reason), "%s", resolution == 2 ? "ambiguous_source" : "unmapped_source");
    return expression->outcome;
  }
  return resolve_owned_source_pointer_expression(lookup, decode, accepted_start, value, section, offset, 0, expression);
}

static uint8_t resolve_rendered_data_pointer_expression(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const M68kAnalysisStructuredDataItem *item, uint32_t offset,
    uint8_t allow_in_section_source_offset, const M68kDecodeIR *decode, uint8_t *const *accepted_start,
    M68kRenderPlannedExpression *out_expression) {
  uint32_t value;
  uint32_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  char name[96];
  int bounded_typed_table = item != NULL && item->pointer_struct[0] != '\0' &&
    (item->semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE) != 0U;
  if (out_expression == NULL) return M68K_RENDER_PLANNED_EXPRESSION_INVALID;
  memset(out_expression, 0, sizeof(*out_expression));
  if (lookup == NULL || section == NULL || section->data == NULL || offset > section->size ||
      section->size - offset < 4U) {
    out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_INVALID;
    snprintf(out_expression->reason, sizeof(out_expression->reason), "invalid pointer render candidate");
    return out_expression->outcome;
  }
  out_expression->source_section_index = (uint32_t)section->section_index;
  out_expression->source_offset = offset;
  out_expression->operand_index = UINT32_MAX;
  out_expression->kind = (structured_data_item_is_pointer_table(item) ||
      structured_data_item_is_absolute_long_lookup_table(item))
    ? M68K_RENDER_PLANNED_EXPRESSION_TABLE_ENTRY : M68K_RENDER_PLANNED_EXPRESSION_DATA_POINTER;
  value = m68k_read_u32be(section->data + offset);
  out_expression->logical_address = value;
  out_expression->pointer_width = 4U;
  out_expression->pointer_address_domain = item != NULL ? item->pointer_address_domain :
    M68K_ANALYSIS_POINTER_DOMAIN_LEGACY;
  if (value == 0U) {
    out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_NUMERIC;
    snprintf(out_expression->reason, sizeof(out_expression->reason), "null_pointer");
    return out_expression->outcome;
  }
  if (item != NULL && item->pointer_address_domain == M68K_ANALYSIS_POINTER_DOMAIN_RUNTIME_ONLY)
    return resolve_runtime_only_pointer_expression(lookup, item, value, out_expression);
  /* Interior references use the bounded-owner projection. Preserve the
   * existing scalar pointer/domain path for exact-width owners. */
  if (lookup->policy != NULL && item != NULL && item->size > 4U) {
    uint16_t index;
    for (index = 0U; index < lookup->policy->manual_runtime_address_ref_count &&
        index < M68K_ANALYSIS_MANUAL_RUNTIME_ADDRESS_REF_LIMIT; ++index) {
      const M68kAnalysisManualRuntimeAddressRef *ref = &lookup->policy->manual_runtime_address_refs[index];
      uint32_t logical = 0U;
      if (!ref->has_section_index || ref->section_index != section->section_index || ref->offset != offset ||
          ref->size != 4U || !ref->has_target || !ref->has_runtime_address || ref->runtime_address != value ||
          strcmp(ref->owner_kind, "data_block_interpreted_ref") != 0) continue;
      if (!lookup_source_logical_address(lookup, ref->target_section_index, ref->target_offset, &logical) ||
          logical != value) {
        out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_NUMERIC;
        snprintf(out_expression->reason, sizeof(out_expression->reason), "unmapped_reference_target");
        return out_expression->outcome;
      }
    }
  }
  if (item != NULL && item->pointer_address_domain == M68K_ANALYSIS_POINTER_DOMAIN_MAPPED_SOURCE)
    return resolve_mapped_source_pointer_expression(lookup, decode, accepted_start, value, out_expression);
  if (bounded_typed_table) {
    uint32_t owner_offset;
    /* A bounded typed owner can name an interior local-offset target even
     * when no standalone label remains after source-plan pruning. The owner
     * resolver still requires the expression to reproduce the stored value. */
    if (lookup_exact_pointer_value_label_offset(lookup, section->section_index, section->size,
          value, 1U, &owner_offset) &&
        resolve_owned_source_pointer_expression(lookup, decode, accepted_start, value,
          (uint32_t)section->section_index, owner_offset, 1, out_expression) ==
            M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC)
      return out_expression->outcome;
  }
  if (item != NULL && item->is_pointer != 0U && item->size == 4U && item->has_target != 0U &&
      item->table_kind_id == M68K_ANALYSIS_TABLE_KIND_UNKNOWN) {
    target_section_index = item->target_section;
    target_offset = item->target_offset;
  } else if (!lookup_exact_pointer_value_label_offset(lookup, section->section_index, section->size, value,
      allow_in_section_source_offset,
      &target_offset)) {
    out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_NUMERIC;
    snprintf(out_expression->reason, sizeof(out_expression->reason), "unmapped_source");
    return out_expression->outcome;
  } else {
    target_section_index = (uint32_t)section->section_index;
  }
  if (target_section_index >= lookup->section_count || target_offset > lookup->label_extents[target_section_index]) {
    out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_INVALID;
    snprintf(out_expression->reason, sizeof(out_expression->reason), "pointer target is outside source storage");
    return out_expression->outcome;
  }
  /* Typed table targets retain their real source identity, but an automatic
   * interior label must not split an existing bounded data owner. Explicit
   * interior names are preserved by the shared owner-expression resolver. */
  if (bounded_typed_table &&
      resolve_owned_source_pointer_expression(lookup, decode, accepted_start, value,
        target_section_index, target_offset, 1, out_expression) == M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC)
    return out_expression->outcome;
  out_expression->addend = 0;
  name[0] = '\0';
  (void)format_rendered_asm_label_with_generation(lookup, name, sizeof(name), target_section_index, target_offset);
  if (name[0] == '\0') {
    out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_INVALID;
    snprintf(out_expression->reason, sizeof(out_expression->reason), "pointer target has no source symbol name");
    return out_expression->outcome;
  }
  out_expression->target_section_index = target_section_index;
  out_expression->target_offset = target_offset;
  out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC;
  out_expression->has_target = 1U;
  snprintf(out_expression->reason, sizeof(out_expression->reason), "resolved_source");
  out_expression->requires_declaration = 1U;
  snprintf(out_expression->expression, sizeof(out_expression->expression), "%s", name);
  snprintf(out_expression->target_symbol, sizeof(out_expression->target_symbol), "%s", name);
  return out_expression->outcome;
}

static uint8_t resolve_rendered_relocation_expression(const M68kRenderLookup *lookup, const M68kFact *fact,
    M68kRenderPlannedExpression *out_expression) {
  char name[96];
  if (out_expression == NULL) return M68K_RENDER_PLANNED_EXPRESSION_INVALID;
  memset(out_expression, 0, sizeof(*out_expression));
  if (lookup == NULL || fact == NULL || fact->section_index > UINT32_MAX) {
    out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_INVALID;
    snprintf(out_expression->reason, sizeof(out_expression->reason), "invalid relocation render candidate");
    return out_expression->outcome;
  }
  out_expression->source_section_index = (uint32_t)fact->section_index;
  out_expression->source_offset = fact->offset;
  out_expression->operand_index = UINT32_MAX;
  out_expression->kind = M68K_RENDER_PLANNED_EXPRESSION_RELOCATION;
  if (fact->target_section_index >= lookup->section_count ||
      fact->target_offset > lookup->label_extents[fact->target_section_index]) {
    out_expression->outcome = fact->platform_record_kind == AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32
      ? M68K_RENDER_PLANNED_EXPRESSION_NUMERIC : M68K_RENDER_PLANNED_EXPRESSION_INVALID;
    snprintf(out_expression->reason, sizeof(out_expression->reason), "relocation target is outside source storage");
    return out_expression->outcome;
  }
  if (lookup_offset_is_inside_relocation_payload(lookup, fact->target_section_index, fact->target_offset)) {
    out_expression->outcome = fact->platform_record_kind == AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32
      ? M68K_RENDER_PLANNED_EXPRESSION_NUMERIC : M68K_RENDER_PLANNED_EXPRESSION_INVALID;
    snprintf(out_expression->reason, sizeof(out_expression->reason), "relocation target is inside relocation payload");
    return out_expression->outcome;
  }
  name[0] = '\0';
  (void)format_rendered_asm_label_with_generation(lookup, name, sizeof(name), fact->target_section_index,
    fact->target_offset);
  if (name[0] == '\0') {
    out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_INVALID;
    snprintf(out_expression->reason, sizeof(out_expression->reason), "relocation target has no source symbol name");
    return out_expression->outcome;
  }
  out_expression->target_section_index = (uint32_t)fact->target_section_index;
  out_expression->target_offset = fact->target_offset;
  out_expression->has_target = 1U;
  out_expression->requires_declaration = 1U;
  out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC;
  snprintf(out_expression->expression, sizeof(out_expression->expression), "%s", name);
  snprintf(out_expression->target_symbol, sizeof(out_expression->target_symbol), "%s", name);
  return out_expression->outcome;
}

static int render_asm_pointer_table_raw_long(M68kRenderIRPreview *preview, const M68kDecodeSectionIR *section,
    M68kRenderLookup *lookup, const M68kAnalysisStructuredDataItem *item, uint32_t offset, const char *comment) {
  char line[256];
  char name[M68K_RENDER_PLANNED_EXPRESSION_TEXT_CAPACITY];
  const M68kRenderPlannedExpression *expression;
  if (preview == NULL || section == NULL || lookup == NULL || section->data == NULL ||
      offset > section->size || section->size - offset < 4U) {
    return 0;
  }
  expression = m68k_render_plan_find_expression(&preview->asm_source_plan, (uint32_t)section->section_index,
    offset, UINT32_MAX, structured_data_item_is_pointer_table(item) ? M68K_RENDER_PLANNED_EXPRESSION_TABLE_ENTRY :
      M68K_RENDER_PLANNED_EXPRESSION_DATA_POINTER);
  if (expression == NULL || expression->outcome != M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC) return 0;
  snprintf(name, sizeof(name), "%s", expression->expression);
  if (record_planned_expression_target_access(preview, section->section_index, expression, 0) != 0) {
    preview->asm_source_allocation_failed = 1U;
    return 0;
  }
  if (comment != NULL && comment[0] != '\0')
    snprintf(line, sizeof(line), "\tdc.l %s\t; %s\n", name, comment);
  else
    snprintf(line, sizeof(line), "\tdc.l %s\n", name);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  return 1;
}

static void render_asm_dc_symbol_expr(M68kRenderIRPreview *preview, uint32_t size, const char *expr,
    const char *comment) {
  const char *directive = size == 4U ? "dc.l" : size == 2U ? "dc.w" : "dc.b";
  char line[M68K_RENDER_PLANNED_EXPRESSION_TEXT_CAPACITY + 128U + 16U];
  if (preview == NULL || expr == NULL || expr[0] == '\0') return;
  if (comment != NULL && comment[0] != '\0')
    snprintf(line, sizeof(line), "\t%s %s\t; %s\n", directive, expr, comment);
  else
    snprintf(line, sizeof(line), "\t%s %s\n", directive, expr);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static const char *path_basename_local(const char *path) {
  const char *last_slash;
  const char *last_backslash;
  if (path == NULL) return NULL;
  last_slash = strrchr(path, '/');
  last_backslash = strrchr(path, '\\');
  if (last_backslash != NULL && (last_slash == NULL || last_backslash > last_slash)) last_slash = last_backslash;
  return last_slash != NULL ? last_slash + 1 : path;
}

static int render_asm_platform_opcode_call(M68kRenderIRPreview *preview, uint16_t opcode,
    const PlatformFactsV2ResolvedCall *call_info) {
  const MacOsCallInfo *mac_call;
  const char *include_path;
  char line[128];
  if (preview == NULL || call_info == NULL || call_info->platform_kind != M68K_PLATFORM_BACKEND_MACOS ||
      call_info->note_symbol_name[0] == '\0') {
    return 0;
  }
  if (!asm_symbol_name_is_safe_local(call_info->note_symbol_name)) return 0;
  mac_call = mac_os_find_call_by_opword(opcode);
  include_path = mac_call != NULL ? path_basename_local(mac_call->source_path) : NULL;
  if (!render_asm_include_once(preview, include_path)) return 0;
  snprintf(line, sizeof(line), "\t%s\n", call_info->note_symbol_name);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  return 1;
}

static void render_asm_ds_best_fit(M68kRenderIRPreview *preview, uint32_t offset, uint32_t size) {
  char line[96];
  const char *directive = "DS.B";
  uint32_t count = size;
  if (preview == NULL || size == 0U) return;
  if ((offset & 3U) == 0U && (size & 3U) == 0U) {
    directive = "DS.L";
    count = size / 4U;
  } else if ((offset & 1U) == 0U && (size & 1U) == 0U) {
    directive = "DS.W";
    count = size / 2U;
  }
  snprintf(line, sizeof(line), "\t%s $%X\n", directive, (unsigned)count);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static uint32_t structured_data_item_role_flags(const M68kAnalysisStructuredDataItem *item) {
  if (item == NULL) return 0U;
  return item->semantic_role_flags;
}

static int structured_data_item_is_copper_list(const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS &&
    (structured_data_item_role_flags(item) & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_COPPER_LIST) != 0U;
}

static int structured_data_item_is_palette(const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS &&
    (structured_data_item_role_flags(item) & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_PALETTE) != 0U;
}

static int structured_data_item_is_pointer_table(const M68kAnalysisStructuredDataItem *item) {
  if (item == NULL) return 0;
  if ((structured_data_item_role_flags(item) & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE) != 0U)
    return item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS;
  /* A typed custom-structure pointer can start at an odd record stride.  It
     is still one 32-bit stored address and must be rendered as such. */
  return item->is_pointer != 0U && item->size == 4U;
}

static int structured_data_item_is_word_relative_lookup_table(const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS && item->has_target &&
    (structured_data_item_role_flags(item) & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE) != 0U;
}

static int structured_data_item_is_keyed_long_relative_lookup_table(const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS && item->has_target &&
    item->source_pattern_id == M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_KEYED_LONG_RELATIVE_DISPATCH &&
    (structured_data_item_role_flags(item) & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE) != 0U;
}

static int structured_data_item_is_absolute_long_lookup_table(const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS &&
    item->table_kind_id == M68K_ANALYSIS_TABLE_KIND_ABSOLUTE_CODE_DISPATCH &&
    (structured_data_item_role_flags(item) & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE) != 0U;
}

static int lookup_any_runtime_address_source_offset(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t runtime_address, uint32_t section_size, uint32_t *out_source_offset) {
  size_t index;
  if (out_source_offset != NULL) *out_source_offset = 0U;
  if (lookup == NULL || lookup->runtime_address_ranges == NULL) return 0;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *range = lookup->runtime_address_ranges[index].fact;
    uint32_t delta;
    uint32_t source_offset;
    if (range == NULL || range->section_index != section_index || !range->has_runtime_address ||
        runtime_address < range->runtime_address) {
      continue;
    }
    delta = runtime_address - range->runtime_address;
    if (delta >= range->size || range->offset > UINT32_MAX - delta) continue;
    source_offset = range->offset + delta;
    if (source_offset >= section_size) continue;
    if (out_source_offset != NULL) *out_source_offset = source_offset;
    return 1;
  }
  return 0;
}

static int render_asm_absolute_long_lookup_table(M68kRenderIRPreview *preview,
    const M68kDecodeSectionIR *section, M68kRenderLookup *lookup,
    const M68kAnalysisStructuredDataItem *item, uint32_t available, const char *comment) {
  uint32_t cursor = 0U;
  if (preview == NULL || section == NULL || lookup == NULL || item == NULL || section->data == NULL ||
      item->offset >= section->size || (available & 3U) != 0U) {
    return 0;
  }
  while (cursor + 4U <= available) {
    uint32_t line_count = (available - cursor) / 4U;
    uint32_t index;
    if (line_count > 4U) line_count = 4U;
    hash_asm_text(preview, "\tdc.l ");
    for (index = 0U; index < line_count; ++index) {
      char expr[96];
      uint32_t entry_offset = item->offset + cursor + (index * 4U);
      uint32_t raw_long = m68k_read_u32be(section->data + entry_offset);
      const M68kRenderPlannedExpression *expression = m68k_render_plan_find_expression(
        &preview->asm_source_plan, (uint32_t)section->section_index, entry_offset, UINT32_MAX,
        M68K_RENDER_PLANNED_EXPRESSION_TABLE_ENTRY);
      if (expression != NULL && expression->outcome == M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC) {
        snprintf(expr, sizeof(expr), "%s", expression->expression);
        if (record_planned_expression_target_access(preview, section->section_index, expression, 0) != 0) {
          preview->asm_source_allocation_failed = 1U;
          return 0;
        }
      } else {
        snprintf(expr, sizeof(expr), "$%08X", (unsigned)raw_long);
      }
      if (index != 0U) hash_asm_text(preview, ",");
      hash_asm_text(preview, expr);
    }
    if (comment != NULL && comment[0] != '\0') {
      hash_asm_text(preview, "\t; ");
      hash_asm_text(preview, comment);
    }
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
    cursor += line_count * 4U;
  }
  return cursor == available;
}

static int lookup_source_offset_is_block_start(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset);

static uint8_t resolve_rendered_canonical_relative_expression(const M68kRenderLookup *lookup,
    uint32_t base_section_index, uint32_t base_offset, uint32_t target_offset, uint16_t key,
    uint8_t keyed_long, M68kRenderPlannedExpression *out_expression) {
  (void)format_rendered_asm_label_with_generation(lookup, out_expression->base_symbol,
    sizeof(out_expression->base_symbol), base_section_index, base_offset);
  (void)format_rendered_asm_label_with_generation(lookup, out_expression->target_symbol,
    sizeof(out_expression->target_symbol), base_section_index, target_offset);
  if (out_expression->base_symbol[0] == '\0' || out_expression->target_symbol[0] == '\0') {
    out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_INVALID;
    snprintf(out_expression->reason, sizeof(out_expression->reason), "relative target has no source symbol name");
    return out_expression->outcome;
  }
  out_expression->target_section_index = base_section_index;
  out_expression->target_offset = target_offset;
  out_expression->base_section_index = base_section_index;
  out_expression->base_offset = base_offset;
  if (strlen(out_expression->target_symbol) + strlen(out_expression->base_symbol) +
      (keyed_long ? 8U : 1U) >= sizeof(out_expression->expression)) {
    out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_NUMERIC;
    snprintf(out_expression->reason, sizeof(out_expression->reason), "relative expression exceeds render capacity");
    return out_expression->outcome;
  }
  out_expression->has_target = 1U;
  out_expression->has_base_target = 1U;
  out_expression->requires_declaration = 1U;
  out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC;
  out_expression->addend = (int32_t)key;
  out_expression->has_relative_key = keyed_long;
  if (keyed_long)
    snprintf(out_expression->expression, sizeof(out_expression->expression), "%s-%s,$%04X",
      out_expression->target_symbol, out_expression->base_symbol, (unsigned)key);
  else
    snprintf(out_expression->expression, sizeof(out_expression->expression), "%s-%s",
      out_expression->target_symbol, out_expression->base_symbol);
  return out_expression->outcome;
}

static int inferred_relative_label_names_share_address_domain(const M68kRenderLookup *lookup,
    uint32_t section_index, uint32_t base_offset, uint32_t target_offset,
    const M68kRenderPlannedExpression *expression) {
  char target_storage_name[96];
  char base_storage_name[96];
  (void)format_storage_asm_label_with_generation(lookup, target_storage_name, sizeof(target_storage_name),
    section_index, target_offset);
  (void)format_storage_asm_label_with_generation(lookup, base_storage_name, sizeof(base_storage_name),
    section_index, base_offset);
  return (strcmp(expression->target_symbol, target_storage_name) != 0) ==
    (strcmp(expression->base_symbol, base_storage_name) != 0);
}

static uint8_t resolve_rendered_relative_lookup_expression(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kAnalysisStructuredDataItem *item, uint32_t offset, uint8_t keyed_long,
    M68kRenderPlannedExpression *out_expression) {
  int64_t target_offset;
  uint32_t raw_value;
  int32_t displacement;
  uint16_t key = 0U;
  if (out_expression == NULL) return M68K_RENDER_PLANNED_EXPRESSION_INVALID;
  memset(out_expression, 0, sizeof(*out_expression));
  if (lookup == NULL || section == NULL || item == NULL || section->data == NULL ||
      offset > section->size || section->size - offset < (keyed_long ? 4U : 2U) ||
      item->target_section >= lookup->section_count) {
    out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_INVALID;
    snprintf(out_expression->reason, sizeof(out_expression->reason), "invalid relative lookup candidate");
    return out_expression->outcome;
  }
  raw_value = keyed_long ? m68k_read_u32be(section->data + offset) : m68k_read_u16be(section->data + offset);
  displacement = keyed_long ? (int32_t)(int16_t)((raw_value >> 16U) & 0xFFFFU) :
    (int32_t)(int16_t)raw_value;
  if (keyed_long) key = (uint16_t)(raw_value & 0xFFFFU);
  out_expression->source_section_index = (uint32_t)section->section_index;
  out_expression->source_offset = offset;
  out_expression->operand_index = UINT32_MAX;
  out_expression->kind = M68K_RENDER_PLANNED_EXPRESSION_RELATIVE;
  target_offset = (int64_t)item->target_offset + displacement;
  if (target_offset < 0 || target_offset > UINT32_MAX || item->target_offset > lookup->label_extents[item->target_section] ||
      (uint32_t)target_offset > lookup->label_extents[item->target_section]) {
    out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_NUMERIC;
    snprintf(out_expression->reason, sizeof(out_expression->reason), "relative target outside source storage");
    return out_expression->outcome;
  }
  if (item->table_kind_id == M68K_ANALYSIS_TABLE_KIND_RELATIVE_CODE_DISPATCH &&
      ((item->target_section == section->section_index &&
        !accepted_start_at(section, accepted_start, (uint32_t)target_offset)) ||
       (item->target_section != section->section_index &&
        !lookup_source_offset_is_block_start(lookup, item->target_section, (uint32_t)target_offset)))) {
    out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_NUMERIC;
    snprintf(out_expression->reason, sizeof(out_expression->reason), "relative code target is not an entry");
    return out_expression->outcome;
  }
  /* A backward relative address needs a label that was independently
   * established before this table.  Without that evidence it may denote a
   * runtime-only or interior source view; retain the exact numeric payload
   * rather than inventing a declaration the body cannot emit. */
  if (item->target_section == section->section_index &&
      ((item->target_offset < item->offset &&
        !lookup_has_renderable_label(lookup, item->target_section, item->target_offset)) ||
       ((uint32_t)target_offset < item->offset &&
        !lookup_has_renderable_label(lookup, item->target_section, (uint32_t)target_offset)))) {
    out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_NUMERIC;
    snprintf(out_expression->reason, sizeof(out_expression->reason), "backward relative target lacks source label");
    return out_expression->outcome;
  }
  /* Same-section source labels are validated by the body label-emission
   * predicate after declarations are derived.  Cross-section labels have no
   * local body walk to establish that safety, so they must already be block
   * starts. */
  if (item->target_section != section->section_index &&
      (!lookup_source_offset_is_block_start(lookup, item->target_section, item->target_offset) ||
       !lookup_source_offset_is_block_start(lookup, item->target_section, (uint32_t)target_offset))) {
    out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_NUMERIC;
    snprintf(out_expression->reason, sizeof(out_expression->reason), "relative target is not a source block boundary");
    return out_expression->outcome;
  }
  {
    uint8_t outcome = resolve_rendered_canonical_relative_expression(lookup, item->target_section,
      item->target_offset, (uint32_t)target_offset, key, keyed_long, out_expression);
    /* Preserve the inference lane's existing conservative spelling check.
     * Explicit manual relations instead validate canonical coordinates and
     * encoded values before entering the shared expression formatter. */
    if (outcome == M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC &&
        !inferred_relative_label_names_share_address_domain(lookup, item->target_section,
          item->target_offset, (uint32_t)target_offset, out_expression)) {
      out_expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_NUMERIC;
      out_expression->has_target = 0U;
      out_expression->has_base_target = 0U;
      out_expression->requires_declaration = 0U;
      out_expression->has_relative_key = 0U;
      out_expression->addend = 0;
      out_expression->expression[0] = '\0';
      snprintf(out_expression->reason, sizeof(out_expression->reason), "relative operands use different address domains");
    }
    return out_expression->outcome;
  }
}

static uint8_t resolve_rendered_manual_base_displacement(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start,
    const M68kDecodeSectionIR *section, const M68kDataReferenceIR *ref,
    M68kRenderPlannedExpression *expression) {
  memset(expression, 0, sizeof(*expression));
  expression->source_section_index = (uint32_t)section->section_index;
  expression->source_offset = ref->source_offset;
  expression->operand_index = UINT32_MAX;
  expression->kind = M68K_RENDER_PLANNED_EXPRESSION_RELATIVE;
  expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_NUMERIC;
  if (ref->reference_kind == M68K_DATA_REFERENCE_KIND_BASE_DISPLACEMENT_RANGE) {
    M68kRenderPlannedExpression base, target;
    uint32_t base_logical = 0U, target_logical = 0U;
    char numerator[M68K_RENDER_PLANNED_EXPRESSION_TEXT_CAPACITY];
    int64_t delta = (ref->raw_value_signed ? (int16_t)ref->raw_value : (int64_t)ref->raw_value) * ref->value_scale;
    int length;
    memset(&base, 0, sizeof(base));
    memset(&target, 0, sizeof(target));
    if (!ref->has_base || ref->raw_value_width != 2U || ref->raw_value > UINT16_MAX || !ref->value_scale ||
        ref->base_section_index != ref->target_section_index ||
        ref->base_section_index != section->section_index || ref->source_offset > section->size ||
        2U > section->size - ref->source_offset ||
        m68k_read_u16be(section->data + ref->source_offset) != ref->raw_value ||
        (int64_t)ref->base_offset + delta != ref->target_offset ||
        !lookup_source_logical_address(lookup, ref->base_section_index, ref->base_offset, &base_logical) ||
        !lookup_source_logical_address(lookup, ref->target_section_index, ref->target_offset, &target_logical) ||
        (int64_t)target_logical - base_logical != delta ||
        resolve_owned_source_pointer_expression(lookup, decode, accepted_start, base_logical,
          ref->base_section_index, ref->base_offset, 1, &base) != M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC ||
        resolve_owned_source_pointer_expression(lookup, decode, accepted_start, target_logical,
          ref->target_section_index, ref->target_offset, 1, &target) != M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC) {
      snprintf(expression->reason, sizeof(expression->reason), "range relation lacks compatible bounded source owners");
      return expression->outcome;
    }
    /* A record index within one owner would spell owner-owner+offset/stride.
     * Keep that packed index readable as its original WORD. The canonical
     * relation and both precise coordinates remain available in native facts.
     * An independently named record or a different owner can render normally. */
    if (ref->value_scale > 1U && !strcmp(target.target_symbol, base.target_symbol)) {
      snprintf(expression->reason, sizeof(expression->reason), "same-owner record index retains encoded WORD");
      return expression->outcome;
    }
    if (delta < INT32_MIN || delta > INT32_MAX) {
      snprintf(expression->reason, sizeof(expression->reason), "range difference exceeds expression arithmetic");
      return expression->outcome;
    }
    length = snprintf(numerator, sizeof(numerator), "%s-%s", target.target_symbol, base.target_symbol);
    if (length > 0 && (size_t)length < sizeof(numerator) && target.addend != 0)
      length += snprintf(numerator + length, sizeof(numerator) - (size_t)length, "+$%X", (unsigned)target.addend);
    if (length > 0 && (size_t)length < sizeof(numerator) && base.addend != 0)
      length += snprintf(numerator + length, sizeof(numerator) - (size_t)length, "-$%X", (unsigned)base.addend);
    if (length < 0 || (size_t)length >= sizeof(numerator)) {
      snprintf(expression->reason, sizeof(expression->reason), "range expression exceeds render capacity");
      return expression->outcome;
    }
    if (ref->value_scale == 1U)
      length = snprintf(expression->expression, sizeof(expression->expression), "%s", numerator);
    else
      length = snprintf(expression->expression, sizeof(expression->expression), "(%s)/%u", numerator, (unsigned)ref->value_scale);
    if (length < 0 || (size_t)length >= sizeof(expression->expression)) {
      expression->expression[0] = '\0';
      snprintf(expression->reason, sizeof(expression->reason), "range expression exceeds render capacity");
      return expression->outcome;
    }
    expression->target_section_index = ref->target_section_index;
    expression->target_offset = ref->target_offset;
    expression->base_section_index = ref->base_section_index;
    expression->base_offset = ref->base_offset;
    snprintf(expression->target_symbol, sizeof(expression->target_symbol), "%s", target.target_symbol);
    snprintf(expression->base_symbol, sizeof(expression->base_symbol), "%s", base.target_symbol);
    expression->has_target = expression->has_base_target = 1U;
    expression->requires_declaration = 0U;
    expression->outcome = M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC;
    snprintf(expression->reason, sizeof(expression->reason), "exact packed source-coordinate relation");
    return expression->outcome;
  }
  if (ref->reference_kind != M68K_DATA_REFERENCE_KIND_BASE_DISPLACEMENT || !ref->has_base ||
      ref->raw_value_width != 2U || !ref->raw_value_signed || ref->raw_value > UINT16_MAX ||
      ref->base_section_index != ref->target_section_index || ref->base_section_index >= lookup->section_count ||
      ref->source_offset > section->size || 2U > section->size - ref->source_offset ||
      m68k_read_u16be(section->data + ref->source_offset) != ref->raw_value ||
      (int64_t)ref->base_offset + (int16_t)ref->raw_value != (int64_t)ref->target_offset ||
      !lookup_has_renderable_label(lookup, ref->base_section_index, ref->base_offset) ||
      !lookup_has_renderable_label(lookup, ref->target_section_index, ref->target_offset)) {
    snprintf(expression->reason, sizeof(expression->reason), "manual relative relation lacks exact source labels");
    return expression->outcome;
  }
  {
    uint32_t base_runtime = 0U, target_runtime = 0U;
    int base_mapped = lookup_source_should_render_runtime_label(lookup, ref->base_section_index,
      ref->base_offset, &base_runtime);
    int target_mapped = lookup_source_should_render_runtime_label(lookup, ref->target_section_index,
      ref->target_offset, &target_runtime);
    if (base_mapped != target_mapped || (base_mapped &&
        (int64_t)target_runtime - (int64_t)base_runtime != (int16_t)ref->raw_value)) {
      snprintf(expression->reason, sizeof(expression->reason), "relative operands use different address mappings");
      return expression->outcome;
    }
  }
  return resolve_rendered_canonical_relative_expression(lookup, ref->base_section_index, ref->base_offset,
    ref->target_offset, 0U, 0U, expression);
}

static int render_asm_keyed_long_relative_lookup_table(M68kRenderIRPreview *preview,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, M68kRenderLookup *lookup,
    const M68kAnalysisStructuredDataItem *item, uint32_t available, const char *comment) {
  uint32_t cursor = 0U;
  (void)accepted_start;
  if (preview == NULL || section == NULL || lookup == NULL || item == NULL || section->data == NULL ||
      item->offset >= section->size || (available & 3U) != 0U) {
    return 0;
  }
  while (cursor + 4U <= available) {
    char expr[224];
    uint32_t entry_offset = item->offset + cursor;
    uint32_t raw_long = m68k_read_u32be(section->data + entry_offset);
    const M68kRenderPlannedExpression *expression = m68k_render_plan_find_expression(
      &preview->asm_source_plan, (uint32_t)section->section_index, entry_offset, UINT32_MAX,
      M68K_RENDER_PLANNED_EXPRESSION_RELATIVE);
    hash_asm_text(preview, "\tdc.w ");
    if (expression != NULL && expression->outcome == M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC) {
      snprintf(expr, sizeof(expr), "%s", expression->expression);
      if (record_planned_expression_target_access(preview, section->section_index, expression, 0) != 0 ||
          record_planned_expression_target_access(preview, section->section_index, expression, 1) != 0) {
        preview->asm_source_allocation_failed = 1U;
        return 0;
      }
    } else {
      snprintf(expr, sizeof(expr), "$%04X,$%04X", (unsigned)((raw_long >> 16U) & 0xFFFFU),
        (unsigned)(raw_long & 0xFFFFU));
    }
    hash_asm_text(preview, expr);
    if (comment != NULL && comment[0] != '\0') {
      hash_asm_text(preview, "\t; ");
      hash_asm_text(preview, comment);
    }
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
    cursor += 4U;
  }
  return cursor == available;
}

static int render_asm_word_relative_lookup_table(M68kRenderIRPreview *preview,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, M68kRenderLookup *lookup,
    const M68kAnalysisStructuredDataItem *item, uint32_t available, const char *comment) {
  uint32_t cursor = 0U;
  (void)accepted_start;
  if (preview == NULL || section == NULL || lookup == NULL || item == NULL || section->data == NULL ||
      item->offset >= section->size || (available & 1U) != 0U) {
    return 0;
  }
  while (cursor + 2U <= available) {
    char expr[192];
    uint32_t entry_offset = item->offset + cursor;
    uint16_t raw_word = m68k_read_u16be(section->data + entry_offset);
    const M68kRenderPlannedExpression *expression = m68k_render_plan_find_expression(
      &preview->asm_source_plan, (uint32_t)section->section_index, entry_offset, UINT32_MAX,
      M68K_RENDER_PLANNED_EXPRESSION_RELATIVE);
    hash_asm_text(preview, "\tdc.w ");
    if (expression != NULL && expression->outcome == M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC) {
      snprintf(expr, sizeof(expr), "%s", expression->expression);
      if (record_planned_expression_target_access(preview, section->section_index, expression, 0) != 0 ||
          record_planned_expression_target_access(preview, section->section_index, expression, 1) != 0) {
        preview->asm_source_allocation_failed = 1U;
        return 0;
      }
    } else {
      snprintf(expr, sizeof(expr), "$%04X", (unsigned)raw_word);
    }
    hash_asm_text(preview, expr);
    if (cursor == 0U && comment != NULL && comment[0] != '\0') {
      hash_asm_text(preview, "\t; ");
      hash_asm_text(preview, comment);
    }
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
    cursor += 2U;
  }
  return cursor == available;
}

static int format_copper_register_symbol(uint16_t copper_register_word, char *buf, size_t buf_size) {
  const char *symbol;
  uint32_t offset = (uint32_t)(copper_register_word & 0x01FEU);
  uint16_t custom_base_id = PLATFORM_FACTS_V2_HARDWARE_BASE_ID_NONE;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if ((copper_register_word & 1U) != 0U) return 0;
  if (!platform_facts_v2_custom_hardware_base_id(M68K_PLATFORM_BACKEND_AMIGA_HUNK, &custom_base_id)) return 0;
  symbol = platform_facts_v2_hardware_base_offset_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
    custom_base_id, offset, buf, buf_size);
  if (symbol == NULL || symbol[0] == '\0') return 0;
  if (symbol != buf) {
    snprintf(buf, buf_size, "%s", symbol);
    return strlen(buf) + 1U < buf_size;
  }
  return 1;
}

static int format_copper_register_value_expr(uint16_t copper_register_word, uint16_t value, char *buf,
    size_t buf_size) {
  uint32_t offset = (uint32_t)(copper_register_word & 0x01FEU);
  uint16_t custom_base_id = PLATFORM_FACTS_V2_HARDWARE_BASE_ID_NONE;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if ((copper_register_word & 1U) != 0U) return 0;
  if (!platform_facts_v2_custom_hardware_base_id(M68K_PLATFORM_BACKEND_AMIGA_HUNK, &custom_base_id)) return 0;
  return platform_facts_v2_hardware_base_offset_value_expr(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
    custom_base_id, offset, value, buf, buf_size);
}

static int render_asm_define_runtime_address_word_symbols_once(M68kRenderIRPreview *preview,
    const char *role, uint32_t address, char *high_symbol, size_t high_symbol_size,
    char *low_symbol, size_t low_symbol_size) {
  char base_symbol[80];
  char high_expr[112];
  char low_expr[160];
  if (high_symbol != NULL && high_symbol_size != 0U) high_symbol[0] = '\0';
  if (low_symbol != NULL && low_symbol_size != 0U) low_symbol[0] = '\0';
  if (preview == NULL || address == 0U) return 0;
  platform_format_runtime_address_symbol_name(role, address, "", base_symbol, sizeof(base_symbol));
  platform_format_runtime_address_symbol_name(role, address, "_hi", high_symbol, high_symbol_size);
  platform_format_runtime_address_symbol_name(role, address, "_lo", low_symbol, low_symbol_size);
  if (high_symbol == NULL || high_symbol[0] == '\0' || low_symbol == NULL || low_symbol[0] == '\0') return 0;
  snprintf(high_expr, sizeof(high_expr), "%s/$10000", base_symbol);
  snprintf(low_expr, sizeof(low_expr), "%s-(%s*$10000)", base_symbol, high_symbol);
  return declare_layout_runtime_symbol(preview, base_symbol, address) &&
    render_asm_declare_symbol_expr_once(preview, high_symbol, high_expr) &&
    render_asm_declare_symbol_expr_once(preview, low_symbol, low_expr);
}

static int render_asm_define_runtime_address_symbol_once(M68kRenderIRPreview *preview,
    const char *role, uint32_t address, char *symbol, size_t symbol_size) {
  if (symbol != NULL && symbol_size != 0U) symbol[0] = '\0';
  if (preview == NULL || symbol == NULL || symbol_size == 0U || address == 0U) return 0;
  platform_format_runtime_address_symbol_name(role, address, "", symbol, symbol_size);
  if (symbol[0] == '\0') return 0;
  return declare_layout_runtime_symbol(preview, symbol, address);
}

static int format_copper_semantic_operand_expr_for_render(M68kRenderIRPreview *preview,
    const M68kSourceAnalysisIR *source_analysis, size_t section_index, uint32_t offset, char *buf,
    size_t buf_size) {
  const M68kSectionAnalysisIR *section;
  size_t index;
  char high_symbol[80];
  char low_symbol[80];
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  section = source_analysis_section_for_render(source_analysis, section_index);
  if (preview == NULL || section == NULL) return 0;
  for (index = 0U; index < section->platform_semantic_use_count; ++index) {
    const M68kPlatformSemanticUseIR *use = &section->platform_semantic_uses[index];
    const char *role;
    if (use->offset != offset || use->kind != M68K_PLATFORM_SEMANTIC_USE_COPPER_ROW ||
        !use->has_operand_expr || use->operand_expr == NULL || use->operand_expr[0] == '\0') {
      continue;
    }
    if (use->has_runtime_address) {
      role = m68k_analysis_structured_data_role_name_for_flags(use->role_flags);
      if (role == NULL || role[0] == '\0') return 0;
      if (!render_asm_define_runtime_address_word_symbols_once(preview, role, use->runtime_address,
          high_symbol, sizeof(high_symbol), low_symbol, sizeof(low_symbol))) {
        return 0;
      }
      if (strcmp(use->operand_expr, high_symbol) != 0 && strcmp(use->operand_expr, low_symbol) != 0) return 0;
    } else if (!render_asm_include_for_symbol_expr(preview, use->operand_expr)) {
      ++preview->asm_source_instruction_render_failures;
      record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, (uint32_t)section_index, offset, 0U);
      return 0;
    }
    snprintf(buf, buf_size, "%s", use->operand_expr);
    return strlen(buf) + 1U < buf_size;
  }
  return 0;
}

static void render_asm_copper_list_words(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kSourceAnalysisIR *source_analysis, const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const uint8_t *data, uint32_t offset, uint32_t size, const char *comment, uint32_t *io_logical_pc) {
  uint32_t cursor = 0U;
  int raw_word_mode = 0;
  if (preview == NULL || data == NULL || size == 0U) return;
  while (cursor + 4U <= size) {
    char left[64];
    char right[96];
    char row_comment[96];
    char line[256];
    uint16_t first = m68k_read_u16be(data + offset + cursor);
    uint16_t second = m68k_read_u16be(data + offset + cursor + 2U);
    int copper_move = 0;
    int right_is_semantic_equate_symbol = 0;
    if (cursor != 0U &&
        render_plan_should_emit_data_label_statement(preview, section, offset + cursor)) {
      render_asm_label(preview, lookup, section->section_index, offset + cursor, io_logical_pc);
    }
    if (raw_word_mode) {
      render_asm_dc_w_values(preview, data, offset + cursor, 2U, NULL);
      if (io_logical_pc != NULL) *io_logical_pc += 2U;
      cursor += 2U;
      continue;
    }
    if (cursor + 2U < size &&
        render_plan_should_emit_data_label_statement(preview, section, offset + cursor + 2U)) {
      render_asm_dc_w_values(preview, data, offset + cursor, 2U, cursor == 0U ? comment : NULL);
      if (io_logical_pc != NULL) *io_logical_pc += 2U;
      cursor += 2U;
      raw_word_mode = 1;
      continue;
    }
    if (first == 0xFFFFU && second == 0xFFFEU) {
      snprintf(left, sizeof(left), "$FFFF");
    } else if ((first & 1U) != 0U && (second & 1U) == 0U) {
      snprintf(left, sizeof(left), "COPPER_WAIT|$%04X", (unsigned)(first & 0xFFFEU));
      if (!render_asm_include_for_symbol_expr(preview, left)) {
        ++preview->asm_source_instruction_render_failures;
        record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, 0U, offset + cursor, 0U);
        return;
      }
    } else if (!format_copper_register_symbol(first, left, sizeof(left))) {
      snprintf(left, sizeof(left), "$%04X", (unsigned)first);
    } else if (!render_asm_include_for_symbol_expr(preview, left)) {
      ++preview->asm_source_instruction_render_failures;
      record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, 0U, offset + cursor, 0U);
      return;
    } else {
      copper_move = 1;
    }
    {
      const M68kRenderPlannedExpression *planned_equate = copper_move ? m68k_render_plan_find_expression(
        &preview->asm_source_plan, (uint32_t)section->section_index, offset + cursor, UINT32_MAX,
        M68K_RENDER_PLANNED_EXPRESSION_EQUATE) : NULL;
      if (planned_equate != NULL && planned_equate->outcome == M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC) {
        snprintf(right, sizeof(right), "%s", planned_equate->expression);
        right_is_semantic_equate_symbol = 1;
      } else if (!copper_move || !format_copper_register_value_expr(first, second, right, sizeof(right))) {
      snprintf(right, sizeof(right), "$%04X", (unsigned)second);
      } else if (!render_asm_include_for_symbol_expr(preview, right)) {
      ++preview->asm_source_instruction_render_failures;
      record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, 0U, offset + cursor, 0U);
      return;
      }
    }
    row_comment[0] = '\0';
    (void)attach_platform_semantic_note_comment_for_render(source_analysis, lookup, section->section_index,
      offset + cursor, row_comment, sizeof(row_comment));
    if (comment != NULL && comment[0] != '\0' && row_comment[0] != '\0')
      snprintf(line, sizeof(line), "\tdc.w %s,%s\t; %s; %s\n", left, right, comment, row_comment);
    else if (comment != NULL && comment[0] != '\0')
      snprintf(line, sizeof(line), "\tdc.w %s,%s\t; %s\n", left, right, comment);
    else if (row_comment[0] != '\0')
      snprintf(line, sizeof(line), "\tdc.w %s,%s\t; %s\n", left, right, row_comment);
    else
      snprintf(line, sizeof(line), "\tdc.w %s,%s\n", left, right);
    hash_asm_text(preview, line);
    if (right_is_semantic_equate_symbol && record_planned_equate_expression_access(preview,
        section->section_index, m68k_render_plan_find_expression(&preview->asm_source_plan,
          (uint32_t)section->section_index, offset + cursor, UINT32_MAX,
          M68K_RENDER_PLANNED_EXPRESSION_EQUATE)) != 0) {
      ++preview->asm_source_instruction_render_failures;
      record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, 0U, offset + cursor, 0U);
      return;
    }
    ++preview->asm_source_lines;
    if (io_logical_pc != NULL) *io_logical_pc += 4U;
    cursor += 4U;
  }
  if (cursor + 2U <= size) {
    render_asm_dc_w_values(preview, data, offset + cursor, 2U, comment);
    if (io_logical_pc != NULL) *io_logical_pc += 2U;
    cursor += 2U;
  }
  if (cursor < size) {
    render_asm_dc_b_with_policy(preview, section, accepted_start, lookup, offset + cursor, size - cursor, comment);
    if (io_logical_pc != NULL) *io_logical_pc += size - cursor;
  }
}

static void render_asm_palette_words(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const uint8_t *data, uint32_t offset,
    uint32_t size, const char *comment, uint32_t *io_logical_pc) {
  uint32_t cursor = 0U;
  if (preview == NULL || lookup == NULL || section == NULL || data == NULL || size == 0U) return;
  while (cursor + 2U <= size) {
    uint32_t start = cursor;
    uint32_t span;
    if (cursor != 0U &&
        render_plan_should_emit_data_label_statement(preview, section, offset + cursor)) {
      render_asm_label(preview, lookup, section->section_index, offset + cursor, io_logical_pc);
    }
    cursor += 2U;
    while (cursor + 2U <= size &&
           !render_plan_should_emit_data_label_statement(preview, section, offset + cursor))
      cursor += 2U;
    span = cursor - start;
    render_asm_dc_w_values(preview, data, offset + start, span, start == 0U ? comment : NULL);
    if (io_logical_pc != NULL) *io_logical_pc += span;
  }
  if (cursor < size) {
    render_asm_dc_b_with_policy(preview, section, accepted_start, lookup, offset + cursor, size - cursor, NULL);
    if (io_logical_pc != NULL) *io_logical_pc += size - cursor;
  }
}

static void render_asm_dc_b_string_with_labels(M68kRenderIRPreview *preview, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, M68kRenderLookup *lookup, uint32_t offset, uint32_t size, const char *comment,
    uint32_t *io_logical_pc) {
  uint32_t cursor = 0U;
  (void)accepted_start;
  if (preview == NULL || section == NULL || lookup == NULL || section->data == NULL || size == 0U) return;
  while (cursor < size) {
    uint32_t chunk_size = size - cursor;
    uint32_t probe;
    if (cursor != 0U && render_plan_should_emit_data_label_statement(preview, section, offset + cursor)) {
      render_asm_label(preview, lookup, section->section_index, offset + cursor, io_logical_pc);
    }
    for (probe = 1U; probe < chunk_size; ++probe) {
      if (render_plan_should_emit_data_label_statement(preview, section, offset + cursor + probe)) {
        chunk_size = probe;
        break;
      }
    }
    render_asm_dc_b_string(preview, section->data, offset + cursor, chunk_size,
      cursor == 0U ? comment : NULL);
    if (io_logical_pc != NULL) *io_logical_pc += chunk_size;
    cursor += chunk_size;
  }
}

static void render_asm_structured_data_item(M68kRenderIRPreview *preview, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, M68kRenderLookup *lookup, const M68kSourceAnalysisIR *source_analysis,
    const M68kAnalysisStructuredDataItem *item, uint32_t *io_logical_pc, int *out_updated_logical_pc) {
  char comment[128];
  char expr[96];
  const char *comment_text;
  uint32_t available;
  if (out_updated_logical_pc != NULL) *out_updated_logical_pc = 0;
  if (preview == NULL || section == NULL || item == NULL || item->size == 0U) return;
  if (!render_asm_includes_for_structured_data_item(preview, item)) return;
  comment[0] = '\0';
  comment_text = structured_data_item_render_comment(section, item, comment, sizeof(comment)) ? comment : NULL;
  if (item->offset >= section->size || section->data == NULL) {
    render_asm_ds_b(preview, item->size, comment_text);
    return;
  }
  available = section->size - item->offset;
  if (available > item->size) available = item->size;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_STRING && available == item->size &&
      (structured_data_item_role_flags(item) &
        M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LENGTH_PREFIXED_STRING) != 0U) {
    render_asm_dc_b_length_prefixed_string(preview, section->data, item->offset, available, comment_text);
    return;
  }
  if (structured_data_item_is_multiline_text(item) && available == item->size) {
    render_asm_dc_b_string(preview, section->data, item->offset, available, comment_text);
    if (out_updated_logical_pc != NULL && io_logical_pc != NULL) {
      *io_logical_pc += available;
      *out_updated_logical_pc = 1;
    }
    return;
  }
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_STRING && available == item->size) {
    render_asm_dc_b_string_with_labels(preview, section, accepted_start, lookup, item->offset, available, comment_text,
      io_logical_pc);
    if (out_updated_logical_pc != NULL && io_logical_pc != NULL) *out_updated_logical_pc = 1;
    return;
  }
  if (available == item->size && structured_data_item_is_copper_list(item)) {
    const char *copper_comment = item->comment[0] != '\0' ? comment_text : NULL;
    char semantic_comment[160];
    semantic_comment[0] = '\0';
    if (attach_platform_semantic_kind_note_comment_for_render(source_analysis, section->section_index, item->offset,
        M68K_PLATFORM_SEMANTIC_USE_COPPER_DISPLAY_LAYOUT, semantic_comment, sizeof(semantic_comment))) {
      render_asm_comment_line(preview, semantic_comment);
    }
    if (attach_platform_semantic_kind_note_comment_for_render(source_analysis, section->section_index, item->offset,
        M68K_PLATFORM_SEMANTIC_USE_DISPLAY_SETUP, semantic_comment, sizeof(semantic_comment))) {
      render_asm_comment_line(preview, semantic_comment);
    }
    render_asm_copper_list_words(preview, lookup, source_analysis, section, accepted_start, section->data,
      item->offset, available, copper_comment, io_logical_pc);
    if (out_updated_logical_pc != NULL && io_logical_pc != NULL) *out_updated_logical_pc = 1;
    return;
  }
  if (available == item->size && structured_data_item_is_palette(item)) {
    render_asm_palette_words(preview, lookup, section, accepted_start, section->data, item->offset, available, comment_text,
      io_logical_pc);
    if (out_updated_logical_pc != NULL && io_logical_pc != NULL) *out_updated_logical_pc = 1;
    return;
  }
  if (available == item->size && structured_data_item_is_pointer_table(item)) {
    uint32_t cursor;
    for (cursor = 0U; cursor + 4U <= available; cursor += 4U) {
      const M68kFact *relocation = lookup_relocation_at(lookup, section->section_index, item->offset + cursor);
      if (relocation != NULL && relocation->size == 4U) {
        render_asm_relocation_expr(preview, lookup, relocation);
      } else if (render_asm_pointer_table_raw_long(preview, section, lookup, item, item->offset + cursor,
          cursor == 0U ? comment_text : NULL)) {
        ;
      } else if (render_asm_manual_symbol_representation(preview, lookup, section->section_index,
          item->offset + cursor, 4U, cursor == 0U ? comment_text : NULL)) {
        ;
      } else {
        render_asm_dc_l_values(preview, section->data, item->offset + cursor, 4U,
          cursor == 0U ? comment_text : NULL);
      }
    }
    if (cursor < available) {
      uint32_t tail_offset = item->offset + cursor;
      uint32_t tail_size = available - cursor;
      if ((tail_offset & 1U) == 0U && (tail_size & 1U) == 0U)
        render_asm_dc_w_values(preview, section->data, tail_offset, tail_size, NULL);
      else
        render_asm_dc_b_with_policy(preview, section, accepted_start, lookup, tail_offset, tail_size, NULL);
    }
    return;
  }
  if (available == item->size && item->is_pointer != 0U && item->size == 4U &&
      render_asm_pointer_table_raw_long(preview, section, lookup, item, item->offset, comment_text)) {
    return;
  }
  if (available == item->size && structured_data_item_is_word_relative_lookup_table(item) &&
      render_asm_word_relative_lookup_table(preview, section, accepted_start, lookup, item, available,
        comment_text)) {
    return;
  }
  if (available == item->size && structured_data_item_is_keyed_long_relative_lookup_table(item) &&
      render_asm_keyed_long_relative_lookup_table(preview, section, accepted_start, lookup, item, available,
        comment_text)) {
    return;
  }
  if (available == item->size && structured_data_item_is_absolute_long_lookup_table(item) &&
      render_asm_absolute_long_lookup_table(preview, section, lookup, item, available, comment_text)) {
    return;
  }
  if (available == item->size && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS && available == 2U) {
    const M68kRenderPlannedExpression *expression = m68k_render_plan_find_expression(
      &preview->asm_source_plan, (uint32_t)section->section_index, item->offset, UINT32_MAX,
      M68K_RENDER_PLANNED_EXPRESSION_RELATIVE);
    if (expression != NULL && expression->outcome == M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC) {
      render_asm_dc_symbol_expr(preview, 2U, expression->expression, comment_text);
      if (record_planned_expression_target_access(preview, section->section_index, expression, 0) != 0 ||
          record_planned_expression_target_access(preview, section->section_index, expression, 1) != 0)
        preview->asm_source_allocation_failed = 1U;
      return;
    }
  }
  if (available == item->size &&
      render_asm_manual_symbol_representation(preview, lookup, section->section_index, item->offset, item->size,
        comment_text)) {
    return;
  }
  if (available == item->size &&
      structured_data_item_symbolic_operand_expr(section, item, expr, sizeof(expr))) {
    if (!render_asm_include_for_symbol_expr(preview, expr)) {
      ++preview->asm_source_instruction_render_failures;
      record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER,
        item->has_section_index ? item->section_index : 0U, item->offset, 0U);
      return;
    }
    render_asm_dc_symbol_expr(preview, item->size, expr, comment_text);
    return;
  }
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS && available >= 4U) {
    render_asm_structured_raw_data_with_labels(preview, section, accepted_start, lookup, item, item->offset,
      available, 4U, comment_text, io_logical_pc);
    if (out_updated_logical_pc != NULL && io_logical_pc != NULL) *out_updated_logical_pc = 1;
  } else if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS && available >= 2U) {
    render_asm_structured_raw_data_with_labels(preview, section, accepted_start, lookup, item, item->offset,
      available, 2U, comment_text, io_logical_pc);
    if (out_updated_logical_pc != NULL && io_logical_pc != NULL) *out_updated_logical_pc = 1;
  } else {
    render_asm_structured_raw_data_with_labels(preview, section, accepted_start, lookup, item, item->offset,
      available, 1U, comment_text, io_logical_pc);
    if (out_updated_logical_pc != NULL && io_logical_pc != NULL) *out_updated_logical_pc = 1;
  }
  if (available < item->size) render_asm_ds_b(preview, item->size - available, comment_text);
}

const M68kDecodeCandidate *find_candidate_at_offset_local(const M68kDecodeSectionIR *section,
    uint32_t offset) {
  size_t lo = 0U;
  size_t hi;
  if (section == NULL) return NULL;
  hi = section->candidate_count;
  while (lo < hi) {
    size_t mid = lo + ((hi - lo) / 2U);
    uint32_t candidate_offset = section->candidates[mid].offset;
    if (candidate_offset == offset) return &section->candidates[mid];
    if (candidate_offset < offset) lo = mid + 1U;
    else hi = mid;
  }
  return NULL;
}

static int operand_uses_single_word_extension_local(const M68kAsmOperandValue *operand) {
  if (operand == NULL) return 0;
  return (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
    (operand->ea_mode == 5U || (operand->ea_mode == 7U && operand->ea_reg == 0U) ||
      (operand->ea_mode == 7U && operand->ea_reg == 2U));
}

static int operand_uses_long_address_extension_local(const M68kAsmOperandValue *operand) {
  if (operand == NULL) return 0;
  return (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
    operand->ea_mode == 7U && operand->ea_reg == 1U;
}

static int operand_uses_immediate_extension_local(const M68kAsmOperandValue *operand) {
  if (operand == NULL) return 0;
  return ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->ea_mode == 7U && operand->ea_reg == 4U) || operand->kind == M68K_ASM_OPERAND_IMM;
}

typedef struct ByteImmediateExtensionSite {
  size_t byte_offset;
  uint8_t operand_index;
} ByteImmediateExtensionSite;

static uint16_t instruction_asm_form_index_local(const M68kInstructionIR *instruction,
    M68kAsmOperandValue *out_operands, size_t max_operands) {
  size_t operand_index;
  uint16_t asm_form_index;
  if (instruction == NULL || out_operands == NULL || max_operands < instruction->operand_count)
    return M68K_ASM_FORM_NONE;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index)
    out_operands[operand_index] = instruction->operands[operand_index].value;
  asm_form_index = instruction->asm_form_index;
  if (asm_form_index < M68K_ASM_FORM_SLOT_COUNT &&
      g_m68k_asm_forms[asm_form_index].mnemonic_id != M68K_ASM_MNEMONIC_NONE) {
    return asm_form_index;
  }
  return m68k_asm_form_index_for_operands_id(instruction->mnemonic_id, out_operands,
    instruction->operand_count, instruction->size_suffix, instruction->target_cpu);
}

static size_t collect_byte_immediate_extension_sites(const M68kInstructionIR *instruction,
    ByteImmediateExtensionSite *out_sites, size_t max_sites) {
  M68kAsmOperandValue operands[4];
  uint16_t asm_form_index;
  const M68kAsmFormDef *form;
  char size_suffix;
  size_t site_count = 0U;
  size_t word_index;
  size_t extension_index;
  if (instruction == NULL || instruction->operand_count > 4U) return 0U;
  asm_form_index = instruction_asm_form_index_local(instruction, operands, sizeof(operands) / sizeof(operands[0]));
  if (asm_form_index >= M68K_ASM_FORM_SLOT_COUNT) return 0U;
  form = &g_m68k_asm_forms[asm_form_index];
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) return 0U;
  size_suffix = m68k_asm_choose_size_suffix(form, operands, instruction->operand_count, instruction->size_suffix);
  if (size_suffix == '\0') size_suffix = instruction->size_suffix;
  word_index = 1U + form->bound_word_count;
  for (extension_index = 0U; extension_index < form->extension_count; ++extension_index) {
    const M68kAsmExtensionDef *extension = &g_m68k_asm_extensions[form->extension_start + extension_index];
    const M68kAsmOperandValue *operand;
    if (extension->operand_index >= instruction->operand_count) continue;
    operand = &operands[extension->operand_index];
    switch (extension->kind) {
    case M68K_ASM_EXTENSION_EA_SINGLE_WORD:
      if (operand_uses_single_word_extension_local(operand)) ++word_index;
      break;
    case M68K_ASM_EXTENSION_EA_LONG_ADDRESS:
      if (operand_uses_long_address_extension_local(operand)) word_index += 2U;
      break;
    case M68K_ASM_EXTENSION_EA_IMMEDIATE:
      if (operand_uses_immediate_extension_local(operand)) {
        if (size_suffix == 'b') {
          if (site_count < max_sites) {
            out_sites[site_count].byte_offset = word_index * 2U;
            out_sites[site_count].operand_index = extension->operand_index;
          }
          ++site_count;
        }
        word_index += size_suffix == 'l' ? 2U : 1U;
      }
      break;
    case M68K_ASM_EXTENSION_EA_INDEX:
      word_index += m68k_asm_operand_extension_word_count(asm_form_index, operand, size_suffix);
      break;
    case M68K_ASM_EXTENSION_LABEL_DISP16_IF_ZERO:
    case M68K_ASM_EXTENSION_LABEL_DISP16_ALWAYS:
    case M68K_ASM_EXTENSION_DISP16_ALWAYS:
      ++word_index;
      break;
    default:
      break;
    }
  }
  return site_count;
}

static void apply_exact_byte_immediate_render_values(M68kInstructionIR *instruction, const uint8_t *raw_bytes,
    size_t raw_size) {
  ByteImmediateExtensionSite sites[4];
  size_t site_count;
  size_t site_index;
  if (instruction == NULL || raw_bytes == NULL || raw_size == 0U) return;
  site_count = collect_byte_immediate_extension_sites(instruction, sites, sizeof(sites) / sizeof(sites[0]));
  for (site_index = 0U; site_index < site_count; ++site_index) {
    uint8_t operand_index = sites[site_index].operand_index;
    uint16_t raw_word;
    if (sites[site_index].byte_offset + 1U >= raw_size) continue;
    if (operand_index >= instruction->operand_count) continue;
    if (instruction->operands[operand_index].symbol_ref.has_name != 0U) continue;
    raw_word = m68k_read_u16be(raw_bytes + sites[site_index].byte_offset);
    if ((raw_word & 0xFF00U) == 0U) continue;
    if ((raw_word & 0x00FFU) != (instruction->operands[operand_index].value.value & 0xFFU)) continue;
    instruction->operands[operand_index].has_exact_render_value = 1U;
    instruction->operands[operand_index].exact_render_value = raw_word;
  }
}

static int encoded_bytes_match_with_exact_byte_immediates(const M68kInstructionIR *instruction,
    const uint8_t *encoded_bytes, const uint8_t *raw_bytes, size_t raw_size) {
  ByteImmediateExtensionSite sites[4];
  size_t site_count;
  size_t byte_index;
  if (instruction == NULL || encoded_bytes == NULL || raw_bytes == NULL) return 0;
  if (memcmp(encoded_bytes, raw_bytes, raw_size) == 0) return 1;
  site_count = collect_byte_immediate_extension_sites(instruction, sites, sizeof(sites) / sizeof(sites[0]));
  for (byte_index = 0U; byte_index < raw_size; ++byte_index) {
    size_t site_index;
    int allowed_exact_high_byte = 0;
    if (encoded_bytes[byte_index] == raw_bytes[byte_index]) continue;
    for (site_index = 0U; site_index < site_count; ++site_index) {
      uint8_t operand_index = sites[site_index].operand_index;
      uint16_t raw_word;
      uint16_t encoded_word;
      if (sites[site_index].byte_offset != byte_index) continue;
      if (sites[site_index].byte_offset + 1U >= raw_size) continue;
      if (operand_index >= instruction->operand_count) continue;
      if (instruction->operands[operand_index].has_exact_render_value == 0U) continue;
      raw_word = m68k_read_u16be(raw_bytes + sites[site_index].byte_offset);
      encoded_word = m68k_read_u16be(encoded_bytes + sites[site_index].byte_offset);
      if ((uint16_t)instruction->operands[operand_index].exact_render_value == raw_word &&
          (encoded_word & 0x00FFU) == (raw_word & 0x00FFU)) {
        allowed_exact_high_byte = 1;
        break;
      }
    }
    if (!allowed_exact_high_byte) return 0;
  }
  return 1;
}

static int instruction_has_symbolic_or_relative_text(const M68kInstructionIR *instruction) {
  size_t operand_index;
  if (instruction == NULL) return 1;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (operand->kind == M68K_ASM_OPERAND_LABEL) return 1;
    if (operand->symbol_ref.has_name != 0U || operand->symbol_ref.has_symbol != 0 ||
        operand->symbol_ref.has_symbolic_addend != 0U) {
      return 1;
    }
  }
  return 0;
}

int operand_is_address_register_local(const M68kOperandIR *operand, uint8_t reg_index) {
  if (operand == NULL) return 0;
  return operand->kind == M68K_ASM_OPERAND_AN && operand->value.reg == reg_index;
}

int operand_is_absolute_address_local(const M68kOperandIR *operand, uint32_t address) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_ABSL) return operand->value.value == address;
  if (operand->kind != M68K_ASM_OPERAND_EA) return 0;
  return operand->value.value == address &&
    operand->value.ea_mode == 7U && (operand->value.ea_reg == 0U || operand->value.ea_reg == 1U);
}

int operand_absolute_offset_local(const M68kOperandIR *operand, uint32_t *out_offset) {
  if (operand == NULL || out_offset == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_ABSL) {
    *out_offset = operand->value.value;
    return 1;
  }
  if (operand->kind != M68K_ASM_OPERAND_EA) return 0;
  if (operand->value.ea_mode == 7U && (operand->value.ea_reg == 0U || operand->value.ea_reg == 1U)) {
    *out_offset = operand->value.value;
    return 1;
  }
  return 0;
}

static int candidate_operand_is_absolute_word_local(const M68kDecodeCandidate *candidate, size_t operand_index) {
  return candidate != NULL && operand_index < candidate->operand_count &&
    candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_EA &&
    candidate->operands[operand_index].ea_mode == 7U && candidate->operands[operand_index].ea_reg == 0U;
}

int reglist_contains_address_register_local(const M68kOperandIR *operand, uint8_t reg_index) {
  uint32_t mask;
  if (operand == NULL || operand->kind != M68K_ASM_OPERAND_REGLIST || reg_index >= 8U) return 0;
  mask = operand->value.value;
  return (mask & (1UL << (8U + reg_index))) != 0U;
}

static int platform_state_operand_is_app_base(const M68kRenderPlatformState *state,
    const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  if (state == NULL || operand == NULL) return 0;
  if (operand_is_data_register_local(operand, &reg) && reg < 8U &&
      m68k_bitset_u32_has(state->data_app_base_known, reg)) return 1;
  if (operand_address_register_index_local(operand, &reg) && reg < 8U &&
      m68k_bitset_u32_has(state->address_app_base_known, reg))
    return 1;
  return 0;
}

static const char *platform_state_operand_layout_base_symbol(const M68kRenderPlatformState *state,
    const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  if (state == NULL || operand == NULL) return NULL;
  if (operand_is_data_register_local(operand, &reg) && reg < 8U &&
      m68k_bitset_u32_has(state->data_layout_base_known, reg))
    return state->data_layout_base_symbol[reg];
  if (operand_address_register_index_local(operand, &reg) && reg < 8U &&
      m68k_bitset_u32_has(state->address_layout_base_known, reg))
    return state->address_layout_base_symbol[reg];
  return NULL;
}

static const char *platform_state_operand_hardware_base_symbol(const M68kRenderPlatformState *state,
    const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  uint32_t value = 0U;
  const char *base_symbol;
  if (operand == NULL) return NULL;
  if (operand_is_data_register_local(operand, &reg) && reg < 8U && state != NULL &&
      m68k_bitset_u32_has(state->data_hardware_base_known, reg)) {
    return platform_facts_v2_hardware_base_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
      state->data_hardware_base_id[reg]);
  }
  if (operand_address_register_index_local(operand, &reg) && reg < 8U &&
      state != NULL && m68k_bitset_u32_has(state->address_hardware_base_known, reg)) {
    return platform_facts_v2_hardware_base_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
      state->address_hardware_base_id[reg]);
  }
  if (operand->symbol_ref.has_name != 0U) {
    uint32_t base_address;
    if (platform_facts_v2_hardware_base_address_for_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
        operand->symbol_ref.name, &base_address))
      return operand->symbol_ref.name;
  }
  if (m68k_ir_operand_immediate_value(operand, &value) || operand_absolute_offset_local(operand, &value)) {
    base_symbol = platform_facts_v2_hardware_base_symbol_for_address(M68K_PLATFORM_BACKEND_AMIGA_HUNK, value);
    if (base_symbol != NULL && base_symbol[0] != '\0') return base_symbol;
  }
  return NULL;
}

static int instruction_has_call_flow(const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  if (instruction == NULL) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  return metadata != NULL && metadata->flow_kind == M68K_SIM_FLOW_CALL;
}

static int instruction_has_call_or_jump_flow(const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  if (instruction == NULL) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  return metadata != NULL &&
    (metadata->flow_kind == M68K_SIM_FLOW_CALL || metadata->flow_kind == M68K_SIM_FLOW_JUMP);
}

static int candidate_has_call_flow(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  if (candidate == NULL || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  return instruction_has_call_flow(&instruction);
}

static int candidate_has_call_or_jump_flow(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  if (candidate == NULL || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  return instruction_has_call_or_jump_flow(&instruction);
}

static void platform_state_update_hardware_base_after_instruction(M68kRenderPlatformState *state,
    const M68kInstructionIR *instruction, const char *source_base_symbol) {
  uint8_t dest_reg = 0U;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (state == NULL || instruction == NULL) return;
  if (platform_instruction_has_terminal_state_flow(instruction)) {
    platform_state_clear_all_hardware_bases(state);
    return;
  }
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata != NULL && metadata->flow_kind == M68K_SIM_FLOW_CALL) {
    platform_state_clear_all_hardware_bases(state);
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    if (instruction->operand_count >= 2U && instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
      for (dest_reg = 0U; dest_reg < 8U; ++dest_reg) {
        if (reglist_contains_address_register_local(&instruction->operands[1], dest_reg))
          platform_state_clear_address_hardware_base(state, dest_reg);
        if (reglist_contains_data_register_local(&instruction->operands[1], dest_reg)) {
          m68k_bitset_u32_clear(&state->data_hardware_base_known, dest_reg);
          state->data_hardware_base_id[dest_reg] = PLATFORM_FACTS_V2_HARDWARE_BASE_ID_NONE;
        }
      }
    }
    for (operand_index = 0U; metadata != NULL && operand_index < instruction->operand_count &&
         operand_index < 4U; ++operand_index) {
      if (platform_operand_updates_address_register(instruction, operand_index) &&
          instruction->operands[operand_index].value.ea_reg < 8U)
        platform_state_clear_address_hardware_base(state, instruction->operands[operand_index].value.ea_reg);
    }
    return;
  }
  /* Reading a hardware register is not loading the hardware base address. */
  if (metadata != NULL && metadata->operand_access_kinds[0] == M68K_SIM_ACCESS_MEMORY_READ) {
    const M68kOperandIR *source = &instruction->operands[0];
    uint32_t immediate = 0U;
    uint8_t source_reg = 0U;
    if (!operand_is_data_register_local(source, &source_reg) &&
        !operand_address_register_index_local(source, &source_reg) &&
        !m68k_ir_operand_immediate_value(source, &immediate)) source_base_symbol = NULL;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (metadata == NULL || metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE ||
        metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_WRITE) {
      if (operand_is_data_register_local(operand, &dest_reg)) {
        m68k_bitset_u32_clear(&state->data_hardware_base_known, dest_reg);
        state->data_hardware_base_id[dest_reg] = PLATFORM_FACTS_V2_HARDWARE_BASE_ID_NONE;
      } else if (operand_address_register_index_local(operand, &dest_reg)) {
        platform_state_clear_address_hardware_base(state, dest_reg);
      }
    }
    if (platform_operand_updates_address_register(instruction, operand_index)) {
      uint8_t base_reg = operand->value.ea_reg;
      if (base_reg < 8U) platform_state_clear_address_hardware_base(state, base_reg);
    }
  }
  if (instruction->operand_count < 2U) return;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA) {
    const M68kOperandIR *dest = &instruction->operands[instruction->operand_count - 1U];
    /* A partial register write does not establish the full hardware address. */
    if (instruction->size_suffix != 'l' && instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA) return;
    if (operand_address_register_index_local(dest, &dest_reg)) {
      if (source_base_symbol != NULL) platform_state_set_register_hardware_base(state, dest_reg, source_base_symbol);
      else platform_state_clear_address_hardware_base(state, dest_reg);
    } else if (operand_is_data_register_local(dest, &dest_reg) && source_base_symbol != NULL) {
      platform_state_set_data_hardware_base(state, dest_reg, source_base_symbol);
    }
  }
}

static void platform_state_update_app_base_after_instruction(M68kRenderPlatformState *state,
    const M68kInstructionIR *instruction) {
  uint8_t dest_reg = 0U;
  int source_is_app_base;
  if (state == NULL || instruction == NULL) return;
  if (platform_instruction_has_terminal_state_flow(instruction)) {
    platform_state_clear_all_app_bases(state);
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    if (instruction->operand_count >= 2U && instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
      for (dest_reg = 0U; dest_reg < 8U; ++dest_reg) {
        if (reglist_contains_data_register_local(&instruction->operands[1], dest_reg))
          platform_state_clear_data_app_base(state, dest_reg);
        if (reglist_contains_address_register_local(&instruction->operands[1], dest_reg))
          platform_state_clear_address_app_base(state, dest_reg);
      }
    }
    return;
  }
  if (instruction->operand_count < 2U) return;
  source_is_app_base = platform_state_operand_is_app_base(state, &instruction->operands[0]);
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) {
    const M68kOperandIR *dest = &instruction->operands[instruction->operand_count - 1U];
    if (operand_is_data_register_local(dest, &dest_reg)) {
      if (source_is_app_base) platform_state_set_register_app_base(state, M68K_ANALYSIS_REGISTER_DATA, dest_reg);
      else platform_state_clear_data_app_base(state, dest_reg);
    } else if (operand_address_register_index_local(dest, &dest_reg)) {
      if (source_is_app_base) platform_state_set_register_app_base(state, M68K_ANALYSIS_REGISTER_ADDRESS, dest_reg);
      else platform_state_clear_address_app_base(state, dest_reg);
    }
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
      operand_address_register_index_local(&instruction->operands[instruction->operand_count - 1U], &dest_reg)) {
    platform_state_clear_address_app_base(state, dest_reg);
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ &&
      operand_is_data_register_local(&instruction->operands[instruction->operand_count - 1U], &dest_reg)) {
    platform_state_clear_data_app_base(state, dest_reg);
  }
}

static void platform_state_update_layout_base_after_instruction(M68kRenderPlatformState *state,
    const M68kInstructionIR *instruction) {
  uint8_t dest_reg = 0U;
  const char *source_layout_base;
  if (state == NULL || instruction == NULL) return;
  if (platform_instruction_has_terminal_state_flow(instruction)) {
    platform_state_clear_all_layout_bases(state);
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    if (instruction->operand_count >= 2U && instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
      for (dest_reg = 0U; dest_reg < 8U; ++dest_reg) {
        if (reglist_contains_data_register_local(&instruction->operands[1], dest_reg))
          platform_state_clear_data_layout_base(state, dest_reg);
        if (reglist_contains_address_register_local(&instruction->operands[1], dest_reg))
          platform_state_clear_address_layout_base(state, dest_reg);
      }
    }
    return;
  }
  if (instruction->operand_count < 2U) return;
  source_layout_base = platform_state_operand_layout_base_symbol(state, &instruction->operands[0]);
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) {
    const M68kOperandIR *dest = &instruction->operands[instruction->operand_count - 1U];
    if (operand_is_data_register_local(dest, &dest_reg)) {
      if (source_layout_base != NULL)
        platform_state_set_register_layout_base(state, M68K_ANALYSIS_REGISTER_DATA, dest_reg, source_layout_base);
      else
        platform_state_clear_data_layout_base(state, dest_reg);
    } else if (operand_address_register_index_local(dest, &dest_reg)) {
      if (source_layout_base != NULL)
        platform_state_set_register_layout_base(state, M68K_ANALYSIS_REGISTER_ADDRESS, dest_reg, source_layout_base);
      else
        platform_state_clear_address_layout_base(state, dest_reg);
    }
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
      operand_address_register_index_local(&instruction->operands[instruction->operand_count - 1U], &dest_reg)) {
    platform_state_clear_address_layout_base(state, dest_reg);
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ &&
      operand_is_data_register_local(&instruction->operands[instruction->operand_count - 1U], &dest_reg)) {
    platform_state_clear_data_layout_base(state, dest_reg);
  }
}

static void platform_state_update_library_slots_after_instruction(M68kRenderPlatformState *state,
    const M68kInstructionIR *instruction) {
  const M68kOperandIR *source;
  const M68kOperandIR *dest;
  const char *source_library;
  uint8_t dest_reg = 0U;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  if (state == NULL || instruction == NULL || instruction->operand_count < 2U) return;
  source = &instruction->operands[0];
  dest = &instruction->operands[instruction->operand_count - 1U];
  source_library = platform_state_operand_library(state, source);
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) {
    if (operand_is_data_register_local(dest, &dest_reg)) {
      if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction->size_suffix == 'l' &&
          source_library != NULL) {
        platform_state_set_data_library(state, dest_reg, source_library);
      } else {
        platform_state_clear_data_library(state, dest_reg);
      }
    } else if (operand_address_register_index_local(dest, &dest_reg)) {
      const char *slot_library = NULL;
      if (operand_is_address_displacement_local(source, &base_reg, &displacement))
        slot_library = platform_state_local_base_slot_library(state, base_reg, displacement);
      if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && slot_library != NULL) {
        platform_state_set_register_library(state, dest_reg, slot_library);
      } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && source_library != NULL) {
        platform_state_set_register_library(state, dest_reg, source_library);
      } else if (dest_reg != 6U) {
        platform_state_clear_register(state, dest_reg);
      }
    } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction->size_suffix == 'l' &&
        operand_is_address_displacement_local(dest, &base_reg, &displacement)) {
      if (source_library != NULL) platform_state_set_local_base_slot(state, base_reg, displacement, source_library);
      else platform_state_clear_local_base_slot(state, base_reg, displacement);
    }
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ &&
      operand_is_data_register_local(dest, &dest_reg)) {
    platform_state_clear_data_library(state, dest_reg);
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
      operand_address_register_index_local(dest, &dest_reg) && dest_reg != 6U) {
    platform_state_clear_register(state, dest_reg);
  }
}

static void platform_state_copy_exchanged_register(M68kRenderPlatformState *state,
    const M68kRenderPlatformState *previous, const M68kOperandIR *dest, const M68kOperandIR *source) {
  uint8_t reg = 0U;
  uint8_t source_reg = 0U;
  int is_data = operand_is_data_register_local(dest, &reg);
  const char *library = platform_state_operand_library(previous, source);
  const char *hardware = platform_state_operand_hardware_base_symbol(previous, source);
  const char *layout = platform_state_operand_layout_base_symbol(previous, source);
  int app = platform_state_operand_is_app_base(previous, source);
  uint8_t kind = is_data ? M68K_ANALYSIS_REGISTER_DATA : M68K_ANALYSIS_REGISTER_ADDRESS;
  if (!is_data && !operand_address_register_index_local(dest, &reg)) return;
  if (is_data) {
    platform_state_clear_data_library(state, reg);
    platform_state_clear_data_app_base(state, reg);
  } else {
    platform_state_clear_register(state, reg);
  }
  if (library != NULL) {
    if (is_data) platform_state_set_data_library(state, reg, library);
    else platform_state_set_register_library(state, reg, library);
  }
  if (app) platform_state_set_register_app_base(state, kind, reg);
  if (layout != NULL) platform_state_set_register_layout_base(state, kind, reg, layout);
  if (hardware != NULL) {
    if (is_data) platform_state_set_data_hardware_base(state, reg, hardware);
    else platform_state_set_register_hardware_base(state, reg, hardware);
  }
  if (is_data && operand_is_data_register_local(source, &source_reg) &&
      m68k_bitset_u32_has(previous->data_lvo_known, source_reg)) {
    m68k_bitset_u32_set(&state->data_lvo_known, reg);
    state->data_lvo[reg] = previous->data_lvo[source_reg];
  }
}

void platform_state_update_after_instruction(M68kRenderPlatformState *state, const M68kRenderLookup *lookup,
    const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  const char *hardware_source;
  if (state == NULL || instruction == NULL) return;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata != NULL && metadata->operation_type == M68K_SIM_OP_SWAP && instruction->operand_count == 2U) {
    M68kRenderPlatformState previous = *state;
    platform_state_copy_exchanged_register(state, &previous, &instruction->operands[0], &instruction->operands[1]);
    platform_state_copy_exchanged_register(state, &previous, &instruction->operands[1], &instruction->operands[0]);
    return;
  }
  hardware_source = instruction->operand_count != 0U
    ? platform_state_operand_hardware_base_symbol(state, &instruction->operands[0]) : NULL;
  if (platform_instruction_has_terminal_state_flow(instruction)) {
    platform_state_clear_register(state, 6U);
    platform_state_clear_all_data_libraries(state);
    platform_state_clear_all_local_base_slots(state);
    platform_state_update_hardware_base_after_instruction(state, instruction, hardware_source);
    platform_state_update_app_base_after_instruction(state, instruction);
    platform_state_update_layout_base_after_instruction(state, instruction);
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    if (instruction->operand_count >= 2U) {
      uint8_t reg_index;
      if (reglist_contains_address_register_local(&instruction->operands[1], 6U))
        platform_state_clear_register(state, 6U);
      for (reg_index = 0U; reg_index < 8U; ++reg_index) {
        if (reglist_contains_data_register_local(&instruction->operands[1], reg_index))
          platform_state_clear_data_library(state, reg_index);
        if (reg_index != 6U && reglist_contains_address_register_local(&instruction->operands[1], reg_index))
          platform_state_clear_register(state, reg_index);
      }
    }
    platform_state_update_hardware_base_after_instruction(state, instruction, hardware_source);
    platform_state_update_app_base_after_instruction(state, instruction);
    platform_state_update_layout_base_after_instruction(state, instruction);
    return;
  }
  platform_state_update_library_slots_after_instruction(state, instruction);
  if (instruction->operand_count >= 2U && operand_is_address_register_local(&instruction->operands[1], 6U)) {
    uint32_t absolute_offset = 0U;
    const char *library_name = platform_state_operand_library(state, &instruction->operands[0]);
    if (library_name == NULL && instruction->operands[0].symbol_ref.has_name)
      library_name = platform_facts_v2_library_name_from_base_symbol_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
        instruction->operands[0].symbol_ref.name);
    if (library_name == NULL && instruction->operands[0].symbol_ref.has_section &&
        operand_absolute_offset_local(&instruction->operands[0], &absolute_offset)) {
      library_name = lookup_global_base_slot_library(lookup, instruction->operands[0].symbol_ref.section_index,
        absolute_offset);
    }
    if (library_name == NULL) {
      uint8_t base_reg = 0U;
      int16_t displacement = 0;
      if (operand_is_address_displacement_local(&instruction->operands[0], &base_reg, &displacement) &&
          m68k_bitset_u32_has(state->address_base_known, base_reg)) {
        library_name = lookup_base_field_slot_library(lookup, state->address_base_library[base_reg], displacement);
      }
      if (library_name == NULL && operand_is_address_displacement_local(&instruction->operands[0], &base_reg,
          &displacement)) {
        library_name = platform_state_local_base_slot_library(state, base_reg, displacement);
      }
      if (library_name == NULL && operand_is_address_displacement_local(&instruction->operands[0], &base_reg,
          &displacement)) {
        char owner_name[32];
        if (amiga_unknown_base_register_owner_name(base_reg, owner_name, sizeof(owner_name)))
          library_name = lookup_base_field_slot_library(lookup, owner_name, displacement);
      }
    }
    if (library_name == NULL && instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) {
      uint8_t base_reg = 0U;
      int16_t displacement = 0;
      if (!m68k_bitset_u32_has(state->address_base_known, 6U) &&
          operand_is_address_displacement_local(&instruction->operands[0], &base_reg, &displacement) &&
          base_reg == 6U) {
        library_name = lookup_app_base_field_slot_library(lookup, displacement);
      }
    }
    if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA &&
        library_name != NULL) {
      platform_state_set_register_library(state, 6U, library_name);
    } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA &&
        operand_is_absolute_address_local(&instruction->operands[0], 4U)) {
      platform_state_set_register_library(state, 6U, amiga_os_exec_base_library_name());
    } else {
      platform_state_clear_register(state, 6U);
    }
  }
  platform_state_update_hardware_base_after_instruction(state, instruction, hardware_source);
  platform_state_update_app_base_after_instruction(state, instruction);
  platform_state_update_layout_base_after_instruction(state, instruction);
}

void platform_state_note_call_result_after_instruction(M68kRenderPlatformState *state,
    const M68kInstructionIR *instruction, const AmigaOsLibraryVectorInfo *vector) {
  if (state == NULL || instruction == NULL) return;
  if (!instruction_has_call_or_jump_flow(instruction)) return;
  platform_state_clear_data_library(state, 0U);
  if (amiga_vector_is_open_library_result(vector) && m68k_bitset_u32_has(state->address_base_known, 1U))
    platform_state_set_data_library(state, 0U, state->address_base_library[1U]);
}

const AmigaOsLibraryVectorInfo *attach_amiga_lvo_symbol_if_known(const M68kRenderPlatformState *state,
    M68kInstructionIR *instruction) {
  M68kOperandIR *operand;
  const AmigaOsLibraryVectorInfo *vector;
  const char *symbol_name;
  int16_t displacement;
  if (state == NULL || instruction == NULL) return NULL;
  if (!instruction_has_call_or_jump_flow(instruction)) return NULL;
  if (instruction->operand_count != 1U) return NULL;
  if (!m68k_bitset_u32_has(state->address_base_known, 6U)) return NULL;
  operand = &instruction->operands[0];
  if (operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_mode != 5U || operand->value.ea_reg != 6U)
    return NULL;
  displacement = (int16_t)(operand->value.value & 0xFFFFU);
  if (displacement >= 0) return NULL;
  if (state->address_base_id[6] == AMIGA_OS_BASE_ID_NONE) return NULL;
  vector = amiga_os_find_library_vector_by_base_id(state->address_base_id[6], displacement);
  if (vector == NULL) return NULL;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, vector->lvo_symbol_id);
  if (symbol_name == NULL || symbol_name[0] == '\0') return NULL;
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
  operand->symbol_ref.has_name = 1U;
  operand->symbol_ref.name_is_generated = 0U;
  operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
  operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
  snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol_name);
  return vector;
}

static void attach_amiga_platform_symbol(M68kOperandIR *operand, const char *symbol_name) {
  if (operand == NULL || symbol_name == NULL || symbol_name[0] == '\0') return;
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
  operand->symbol_ref.has_name = 1U;
  operand->symbol_ref.name_is_generated = 0U;
  operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
  operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
  snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol_name);
}

static void attach_generic_symbol(M68kOperandIR *operand, const char *symbol_name) {
  if (operand == NULL || symbol_name == NULL || symbol_name[0] == '\0') return;
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
  operand->symbol_ref.has_name = 1U;
  operand->symbol_ref.name_is_generated = 0U;
  operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_NONE;
  operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
  snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol_name);
}

static const M68kPlatformAddressUseIR *source_analysis_platform_address_use_for_operand(
    const M68kSourceAnalysisIR *source_analysis, size_t section_index, uint32_t offset, size_t operand_index,
    uint32_t address, uint8_t use_shape) {
  const M68kSectionAnalysisIR *section_analysis;
  size_t index;
  if (source_analysis == NULL || section_index > UINT32_MAX) return NULL;
  section_analysis = NULL;
  for (index = 0U; index < source_analysis->section_count; ++index) {
    if (source_analysis->sections[index].section_index == (uint32_t)section_index) {
      section_analysis = &source_analysis->sections[index];
      break;
    }
  }
  if (section_analysis == NULL) return NULL;
  for (index = 0U; index < section_analysis->platform_address_use_count; ++index) {
    const M68kPlatformAddressUseIR *use = &section_analysis->platform_address_uses[index];
    if (use->offset == offset &&
        use->operand_index == operand_index &&
        use->address == address &&
        use->use_shape == use_shape) {
      return use;
    }
  }
  return NULL;
}

static int structured_data_item_is_render_candidate(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes, uint32_t render_extent,
    uint32_t offset, const M68kAnalysisStructuredDataItem *item, const M68kRenderPlan *plan) {
  uint32_t probe;
  M68kRenderRangeOwnershipView ownership;
  if (lookup == NULL || section == NULL || item == NULL || item->size == 0U ||
      item->size > render_extent - offset || accepted_byte_at(section, accepted_bytes, offset) ||
      !lookup_range_ownership_at_offset(lookup, section->section_index, offset, &ownership) ||
      ownership.structured_item != item) {
    return 0;
  }
  /* Once labels are planned, only emitted declarations split presentation.
   * Keep non-emitting analysis labels as evidence without making them hidden
   * source boundaries. Relocations, code and structured owners still block. */
  for (probe = offset + 1U; probe < offset + item->size; ++probe) {
    if (accepted_byte_at(section, accepted_bytes, probe) ||
        lookup_structured_item_probe_has_blocking_boundary(lookup, item, section->section_index, probe, plan == NULL)) {
      return 0;
    }
    if (plan != NULL && m68k_render_plan_find_label(plan, (uint32_t)section->section_index, probe) != NULL) {
      int internal_copper_label = structured_data_item_is_copper_list(item) &&
        ((probe - item->offset) % 2U) == 0U;
      int internal_palette_label = structured_data_item_is_palette(item) &&
        ((probe - item->offset) % 2U) == 0U;
      if (!internal_copper_label && !internal_palette_label) return 0;
    }
  }
  return 1;
}

/* A required interior boundary may split a valid typed field into raw rows.
 * Preserve its identity on the first fragment without bypassing that boundary
 * or claiming that the fragment is the complete field. */
static const char *structured_data_fragment_comment(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section,
    const uint8_t *accepted_bytes, uint32_t render_extent,
    const M68kAnalysisStructuredDataItem *item, uint32_t start, uint32_t size,
    char *comment, size_t comment_size) {
  uint32_t probe;
  M68kRenderRangeOwnershipView ownership;
  if (lookup == NULL || section == NULL || item == NULL || comment == NULL || comment_size == 0U ||
      size == 0U || item->offset != start || item->size <= size || item->table_conflicted ||
      item->struct_name[0] == '\0' || item->field_name[0] == '\0' ||
      start >= render_extent || item->size > render_extent - start ||
      start >= section->size || item->size > section->size - start ||
      !lookup_range_ownership_at_offset(lookup, section->section_index, start, &ownership) ||
      ownership.structured_item != item) return NULL;
  for (probe = start; probe < start + item->size; ++probe) {
    if (accepted_byte_at(section, accepted_bytes, probe)) return NULL;
  }
  snprintf(comment, comment_size, "%s (first %u of %u bytes)", item->field_name,
    (unsigned)size, (unsigned)item->size);
  return comment;
}

static int append_planned_source_label_declaration(const M68kRenderLookup *lookup, M68kRenderPlan *plan,
    uint32_t section_index, uint32_t offset, const char *name) {
  M68kRenderPlannedDeclaration declaration;
  size_t declaration_index;
  if (lookup == NULL || plan == NULL || name == NULL || name[0] == '\0' || section_index >= lookup->section_count)
    return -1;
  memset(&declaration, 0, sizeof(declaration));
  declaration.section_index = section_index;
  declaration.offset = offset;
  declaration.kind = M68K_RENDER_PLANNED_DECLARATION_LABEL;
  declaration.has_source_target = 1U;
  (void)lookup_source_logical_address(lookup, section_index, offset, &declaration.logical_address);
  snprintf(declaration.name, sizeof(declaration.name), "%s", name);
  for (declaration_index = 0U; declaration_index < plan->declaration_count; ++declaration_index) {
    const M68kRenderPlannedDeclaration *existing = &plan->declarations[declaration_index];
    if (strcmp(existing->name, declaration.name) == 0) {
      return existing->kind == declaration.kind && existing->section_index == declaration.section_index &&
        existing->offset == declaration.offset ? 0 : -1;
    }
    if (existing->kind == declaration.kind && existing->section_index == declaration.section_index &&
        existing->offset == declaration.offset && strcmp(existing->name, declaration.name) != 0) {
      return -1;
    }
  }
  return m68k_render_plan_append_declaration(plan, &declaration);
}

static int derive_rendered_pointer_declarations(M68kRenderIRPreview *preview, M68kRenderLookup *lookup) {
  size_t expression_index;
  M68kRenderPlan *plan;
  if (preview == NULL || lookup == NULL) return -1;
  plan = &preview->asm_source_plan;
  for (expression_index = 0U; expression_index < plan->expression_count; ++expression_index) {
    M68kRenderPlannedExpression *expression = &plan->expressions[expression_index];
    if (expression->outcome != M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC) continue;
    if (expression->requires_declaration == 0U) {
      if (preview->precomputing_planned_evidence &&
          record_planned_expression_target_access(preview, expression->source_section_index, expression, 0) != 0) return -1;
      continue;
    }
    if (expression->has_target == 0U) continue;
    (void)format_rendered_asm_label_with_generation(lookup, expression->target_symbol,
      sizeof(expression->target_symbol), expression->target_section_index, expression->target_offset);
    if (expression->target_symbol[0] == '\0') return -1;
    if (expression->has_base_target != 0U) {
      (void)format_rendered_asm_label_with_generation(lookup, expression->base_symbol,
        sizeof(expression->base_symbol), expression->base_section_index, expression->base_offset);
      if (expression->base_symbol[0] == '\0') return -1;
    }
    if (expression->requires_declaration != 0U && expression->has_base_target != 0U) {
      if (expression->has_base_addend != 0U)
        snprintf(expression->expression, sizeof(expression->expression), "%s%+d",
          expression->base_symbol, expression->addend);
      else if (expression->has_relative_key != 0U)
        snprintf(expression->expression, sizeof(expression->expression), "%s-%s,$%04X",
          expression->target_symbol, expression->base_symbol, (unsigned)(uint16_t)expression->addend);
      else
        snprintf(expression->expression, sizeof(expression->expression), "%s-%s",
          expression->target_symbol, expression->base_symbol);
    } else if (expression->requires_declaration != 0U) {
      snprintf(expression->expression, sizeof(expression->expression), "%s", expression->target_symbol);
    }
    if (expression->requires_declaration != 0U && expression->has_base_addend == 0U &&
        append_planned_source_label_declaration(lookup, plan, expression->target_section_index,
          expression->target_offset, expression->target_symbol) != 0) return -1;
    if (expression->requires_declaration != 0U && expression->has_base_target != 0U &&
        append_planned_source_label_declaration(lookup, plan, expression->base_section_index,
          expression->base_offset, expression->base_symbol) != 0) return -1;
    if (!preview->precomputing_planned_evidence ||
        expression->kind == M68K_RENDER_PLANNED_EXPRESSION_INSTRUCTION_OPERAND) continue;
    if (record_planned_expression_target_access(preview, expression->source_section_index,
          expression, 0) != 0 ||
        (expression->kind == M68K_RENDER_PLANNED_EXPRESSION_RELATIVE &&
         record_planned_expression_target_access(preview, expression->source_section_index,
           expression, 1) != 0)) return -1;
  }
  return 0;
}

static int render_plan_has_source_label_declaration(const M68kRenderPlan *plan,
    size_t section_index, uint32_t offset) {
  size_t declaration_index;
  if (plan == NULL || section_index > UINT32_MAX) return 0;
  for (declaration_index = 0U; declaration_index < plan->declaration_count; ++declaration_index) {
    const M68kRenderPlannedDeclaration *declaration = &plan->declarations[declaration_index];
    if (declaration->kind == M68K_RENDER_PLANNED_DECLARATION_LABEL &&
        declaration->has_source_target != 0U && declaration->section_index == (uint32_t)section_index &&
        declaration->offset == offset) return 1;
  }
  return 0;
}

static int append_planned_label_statement(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, size_t section_index, uint32_t offset, M68kRenderPlan *plan) {
  M68kRenderPlannedLabel label;
  uint32_t runtime_address = 0U;
  int has_runtime_address;
  if (preview == NULL || lookup == NULL || section == NULL || plan == NULL || section_index > UINT32_MAX ||
      offset > render_section_extent(section)) return -1;
  if (m68k_render_plan_find_label(plan, (uint32_t)section_index, offset) != NULL) return 0;
  memset(&label, 0, sizeof(label));
  label.source_section_index = (uint32_t)section_index;
  label.source_offset = offset;
  has_runtime_address = lookup_source_should_render_runtime_label(lookup, section_index, offset, &runtime_address);
  label.has_runtime_address = has_runtime_address ? 1U : 0U;
  label.runtime_address = runtime_address;
  label.has_storage_label = has_runtime_address && runtime_address != offset &&
    (lookup_source_offset_is_materialized_runtime_range_start(lookup, section_index, offset) ||
     lookup_storage_label_has_inbound_target_ref(lookup, section_index, offset));
  label.name_is_generated = format_rendered_asm_label_with_generation(lookup, label.name,
    sizeof(label.name), section_index, offset);
  if (label.has_storage_label != 0U) {
    (void)format_storage_asm_label_with_generation(lookup, label.storage_name, sizeof(label.storage_name),
      section_index, offset);
  }
  if (label.name[0] == '\0' || (label.has_storage_label != 0U && label.storage_name[0] == '\0')) return -1;
  if (append_planned_source_label_declaration(lookup, plan, label.source_section_index,
        label.source_offset, label.name) != 0) return -1;
  if (m68k_render_plan_append_label(plan, &label) != 0) return -1;
  if (!preview->precomputing_planned_evidence) return 0;
  if (label.has_storage_label != 0U &&
      record_planned_label_statement_access(preview, label.source_section_index, &label, 1) != 0) return -1;
  return record_planned_label_statement_access(preview, label.source_section_index, &label, 0);
}

static int plan_rendered_label_statements(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, M68kRenderPlan *plan) {
  size_t section_index;
  if (preview == NULL || lookup == NULL || decode == NULL || accepted_start == NULL || plan == NULL) return -1;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t source_section_index = section->section_index;
    uint32_t offset;
    if (source_section_index > UINT32_MAX) return -1;
    for (offset = 0U; offset < render_section_extent(section); ++offset) {
      if (!render_asm_should_emit_label_statement(NULL, lookup, section, accepted_start[section_index],
            source_section_index, offset) &&
          !render_plan_has_source_label_declaration(plan, source_section_index, offset)) {
        continue;
      }
      if (append_planned_label_statement(preview, lookup, section, source_section_index, offset, plan) != 0)
        return -1;
    }
  }
  /* A symbolic source expression makes a declaration obligation.  Close it
   * directly here instead of relying on lookup mutation or a renderer walk
   * side effect to rediscover the label position. */
  for (section_index = 0U; section_index < plan->declaration_count; ++section_index) {
    const M68kRenderPlannedDeclaration *declaration = &plan->declarations[section_index];
    const M68kDecodeSectionIR *target_section = NULL;
    size_t decode_section_index;
    if (declaration->kind != M68K_RENDER_PLANNED_DECLARATION_LABEL ||
        declaration->has_source_target == 0U) continue;
    for (decode_section_index = 0U; decode_section_index < decode->section_count; ++decode_section_index) {
      if (decode->sections[decode_section_index].section_index == declaration->section_index) {
        target_section = &decode->sections[decode_section_index];
        break;
      }
    }
    if (target_section == NULL || append_planned_label_statement(preview, lookup, target_section,
          declaration->section_index, declaration->offset, plan) != 0) return -1;
  }
  return 0;
}

static int plan_rendered_runtime_aliases(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    M68kRenderPlan *plan) {
  size_t label_index;
  if (preview == NULL || lookup == NULL || plan == NULL) return -1;
  for (label_index = 0U; label_index < plan->label_count; ++label_index) {
    const M68kRenderPlannedLabel *label = &plan->labels[label_index];
    size_t ref_index;
    for (ref_index = 0U; ref_index < lookup->runtime_address_ref_count; ++ref_index) {
      const M68kFact *fact = lookup->runtime_address_refs[ref_index].fact;
      M68kRenderPlannedRuntimeAlias runtime_alias;
      if (fact == NULL || fact->target_section_index != label->source_section_index ||
          fact->target_offset != label->source_offset || fact->has_runtime_address == 0U ||
          (label->has_runtime_address != 0U && fact->runtime_address == label->runtime_address) ||
          !lookup_source_has_materialized_runtime_address(lookup, label->source_section_index,
            label->source_offset, fact->runtime_address)) {
        continue;
      }
      memset(&runtime_alias, 0, sizeof(runtime_alias));
      runtime_alias.source_section_index = label->source_section_index;
      runtime_alias.source_offset = label->source_offset;
      runtime_alias.runtime_address = fact->runtime_address;
      format_runtime_asm_label(lookup, runtime_alias.name, sizeof(runtime_alias.name),
        runtime_alias.source_section_index, runtime_alias.source_offset, runtime_alias.runtime_address);
      if (runtime_alias.name[0] == '\0' ||
          m68k_render_plan_append_runtime_alias(plan, &runtime_alias) != 0) return -1;
      if (preview->precomputing_planned_evidence) {
        M68kRenderedSymbolAccessIR access;
        memset(&access, 0, sizeof(access));
        access.symbol_name = runtime_alias.name;
        access.offset = runtime_alias.source_offset;
        access.target_section_index = runtime_alias.source_section_index;
        access.target_offset = runtime_alias.source_offset;
        access.operand_index = UINT32_MAX;
        access.access_kind = M68K_RENDERED_SYMBOL_ACCESS_LABEL_STATEMENT;
        access.has_target = 1U;
        access.source_order_class = M68K_RENDERED_SYMBOL_ACCESS_SOURCE_ORDER_RUNTIME_ALIAS;
        if (record_rendered_symbol_access(preview, runtime_alias.source_section_index, &access) != 0) return -1;
      }
    }
  }
  return 0;
}

static int plan_rendered_copper_equate_expressions(M68kRenderIRPreview *preview,
    const M68kRenderLookup *lookup, const M68kDecodeIR *decode, uint8_t **accepted_bytes,
    const M68kSourceAnalysisIR *source_analysis) {
  size_t decode_index;
  if (preview == NULL || lookup == NULL || decode == NULL || accepted_bytes == NULL || source_analysis == NULL)
    return -1;
  for (decode_index = 0U; decode_index < decode->section_count; ++decode_index) {
    const M68kDecodeSectionIR *decode_section = &decode->sections[decode_index];
    const M68kSectionAnalysisIR *analysis_section = source_analysis_section_for_render(source_analysis,
      decode_section->section_index);
    size_t use_index;
    if (analysis_section == NULL) continue;
    for (use_index = 0U; use_index < analysis_section->platform_semantic_use_count; ++use_index) {
      const M68kPlatformSemanticUseIR *use = &analysis_section->platform_semantic_uses[use_index];
      const M68kAnalysisStructuredDataItem *item;
      M68kRenderRangeOwnershipView ownership;
      M68kRenderPlannedExpression expression;
      char symbol[96];
      if (use->kind != M68K_PLATFORM_SEMANTIC_USE_COPPER_ROW || use->has_operand_expr == 0U ||
          use->operand_expr == NULL || use->operand_expr[0] == '\0' || use->offset > decode_section->size ||
          decode_section->size - use->offset < 4U ||
          m68k_render_plan_find_label(&preview->asm_source_plan, (uint32_t)decode_section->section_index,
            use->offset + 2U) != NULL) continue;
      if (!lookup_range_ownership_covering_offset(lookup, decode_section->section_index, use->offset,
            &ownership)) continue;
      item = ownership.structured_item;
      if (item == NULL || !structured_data_item_is_copper_list(item) ||
          !structured_data_item_is_render_candidate(lookup, decode_section, accepted_bytes[decode_index],
            render_section_extent(decode_section), item->offset, item, &preview->asm_source_plan)) continue;
      symbol[0] = '\0';
      if (!format_copper_semantic_operand_expr_for_render(preview, source_analysis, decode_section->section_index,
            use->offset, symbol, sizeof(symbol))) return -1;
      memset(&expression, 0, sizeof(expression));
      expression.source_section_index = (uint32_t)decode_section->section_index;
      expression.source_offset = use->offset;
      expression.operand_index = UINT32_MAX;
      expression.kind = M68K_RENDER_PLANNED_EXPRESSION_EQUATE;
      expression.outcome = M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC;
      snprintf(expression.expression, sizeof(expression.expression), "%s", symbol);
      if (m68k_render_plan_append_expression(&preview->asm_source_plan, &expression) != 0 ||
          (preview->precomputing_planned_evidence &&
           record_planned_equate_expression_access(preview, expression.source_section_index, &expression) != 0))
        return -1;
    }
  }
  return 0;
}

/* This walk deliberately mirrors the data branch of the body renderer.  A
 * structured-data fact is not enough to justify a source symbol: it must win
 * the same instruction, anchor, relocation, and ownership precedence that it
 * will win during source emission. */
static int plan_rendered_structured_pointer_expressions(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, uint8_t **accepted_bytes,
    const M68kSourceAnalysisIR *source_analysis, M68kRenderPlan *plan) {
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || accepted_bytes == NULL || plan == NULL)
    return -1;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    uint32_t render_extent = render_section_extent(section);
    uint32_t offset = 0U;
    while (offset < render_extent) {
      const M68kDecodeCandidate *candidate = NULL;
      const M68kFact *anchor;
      const M68kFact *relocation;
      const M68kAnalysisStructuredDataItem *item;
      if (accepted_start_at(section, accepted_start[section_index], offset)) {
        candidate = find_candidate_at_offset_local(section, offset);
        if (candidate != NULL && candidate->byte_count != 0U) {
          offset += candidate->byte_count;
          continue;
        }
      }
      anchor = lookup_anchor_at(lookup, section->section_index, offset);
      if (anchor != NULL && offset + anchor->size <= section->size &&
          !accepted_byte_at(section, accepted_bytes[section_index], offset)) {
        offset += anchor->size;
        continue;
      }
      relocation = lookup_relocation_at(lookup, section->section_index, offset);
      if (relocation != NULL && offset + relocation->size <= section->size &&
          !accepted_byte_at(section, accepted_bytes[section_index], offset)) {
        M68kRenderPlannedExpression expression;
        if (resolve_rendered_relocation_expression(lookup, relocation, &expression) ==
            M68K_RENDER_PLANNED_EXPRESSION_INVALID) return -1;
        if (m68k_render_plan_append_expression(plan, &expression) != 0) return -1;
        offset += relocation->size;
        continue;
      }
      item = lookup_structured_data_item_at_offset(lookup, section->section_index, offset);
      if (structured_data_item_is_render_candidate(lookup, section, accepted_bytes[section_index], render_extent,
          offset, item, NULL)) {
        uint32_t cursor;
        if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS &&
            !structured_data_item_is_word_relative_lookup_table(item) &&
            !structured_data_item_is_keyed_long_relative_lookup_table(item) &&
            !structured_data_item_is_palette(item)) {
          const M68kSectionAnalysisIR *analysis = source_analysis_section_for_render(source_analysis,
            section->section_index);
          size_t ref_index;
          for (ref_index = 0U; analysis != NULL && ref_index < analysis->data_reference_count; ++ref_index) {
            const M68kDataReferenceIR *ref = &analysis->data_references[ref_index];
            M68kRenderPlannedExpression expression;
            char operand_expr[192];
            if (ref->source_kind != M68K_DATA_REFERENCE_SOURCE_MANUAL || ref->source_offset < item->offset ||
                ref->source_offset - item->offset > item->size ||
                2U > item->size - (ref->source_offset - item->offset) ||
                ((ref->source_offset - item->offset) & 1U) != 0U ||
                lookup_relocation_at(lookup, section->section_index, ref->source_offset) != NULL ||
                lookup_anchor_at(lookup, section->section_index, ref->source_offset) != NULL ||
                accepted_byte_at(section, accepted_bytes[section_index], ref->source_offset) ||
                accepted_byte_at(section, accepted_bytes[section_index], ref->source_offset + 1U) ||
                lookup_has_renderable_label(lookup, section->section_index, ref->source_offset + 1U) ||
                structured_data_item_symbolic_operand_expr(section, item, operand_expr, sizeof(operand_expr))) continue;
            if (resolve_rendered_manual_base_displacement(lookup, decode, accepted_start, section, ref, &expression) ==
                M68K_RENDER_PLANNED_EXPRESSION_INVALID) return -1;
            if (m68k_render_plan_append_expression(plan, &expression) != 0) return -1;
          }
        }
        if (structured_data_item_is_pointer_table(item)) {
          for (cursor = 0U; cursor + 4U <= item->size; cursor += 4U) {
            M68kRenderPlannedExpression expression;
            if (lookup_relocation_at(lookup, section->section_index, offset + cursor) != NULL) continue;
            if (resolve_rendered_data_pointer_expression(lookup, section, item, offset + cursor, 0U,
                decode, accepted_start, &expression) ==
                M68K_RENDER_PLANNED_EXPRESSION_INVALID) return -1;
            if (m68k_render_plan_append_expression(plan, &expression) != 0) return -1;
          }
        } else if (structured_data_item_is_absolute_long_lookup_table(item)) {
          for (cursor = 0U; cursor + 4U <= item->size; cursor += 4U) {
            M68kRenderPlannedExpression expression;
            if (resolve_rendered_data_pointer_expression(lookup, section, item, offset + cursor, 1U,
                decode, accepted_start, &expression) ==
                M68K_RENDER_PLANNED_EXPRESSION_INVALID) return -1;
            if (m68k_render_plan_append_expression(plan, &expression) != 0) return -1;
          }
        } else if (structured_data_item_is_word_relative_lookup_table(item)) {
          for (cursor = 0U; cursor + 2U <= item->size; cursor += 2U) {
            M68kRenderPlannedExpression expression;
            if (resolve_rendered_relative_lookup_expression(lookup, section, accepted_start[section_index], item,
                offset + cursor, 0U, &expression) == M68K_RENDER_PLANNED_EXPRESSION_INVALID) return -1;
            if (m68k_render_plan_append_expression(plan, &expression) != 0) return -1;
          }
        } else if (structured_data_item_is_keyed_long_relative_lookup_table(item)) {
          for (cursor = 0U; cursor + 4U <= item->size; cursor += 4U) {
            M68kRenderPlannedExpression expression;
            if (resolve_rendered_relative_lookup_expression(lookup, section, accepted_start[section_index], item,
                offset + cursor, 1U, &expression) == M68K_RENDER_PLANNED_EXPRESSION_INVALID) return -1;
            if (m68k_render_plan_append_expression(plan, &expression) != 0) return -1;
          }
        }
        offset += item->size;
        continue;
      }
      ++offset;
    }
  }
  /* Plan explicit scalar pointer contracts independently of covering ranges.
   * Anchors and inferred tables may advance the ownership walk past these
   * fields, but must not erase their domain-aware resolution decisions. */
  if (lookup->policy != NULL) {
    size_t item_index;
    for (item_index = 0U; item_index < lookup->policy->structured_data_item_count; ++item_index) {
      const M68kAnalysisStructuredDataItem *field = &lookup->policy->structured_data_items[item_index];
      const M68kDecodeSectionIR *section;
      const M68kRenderPlannedExpression *existing;
      M68kRenderPlannedExpression expression;
      uint32_t field_section = field->has_section_index ? field->section_index : 0U;
      uint32_t byte_index;
      int code_overlap = 0;
      if (!field->is_pointer || field->size != 4U || field_section >= decode->section_count) continue;
      section = &decode->sections[field_section];
      if (field->offset > section->size || section->size - field->offset < 4U ||
          lookup_relocation_at(lookup, field_section, field->offset) != NULL) continue;
      for (byte_index = 0U; byte_index < 4U; ++byte_index) {
        if (accepted_byte_at(section, accepted_bytes[field_section], field->offset + byte_index)) code_overlap = 1;
      }
      if (code_overlap) continue;
      if (resolve_rendered_data_pointer_expression(lookup, section, field, field->offset, 0U,
          decode, accepted_start, &expression) == M68K_RENDER_PLANNED_EXPRESSION_INVALID) return -1;
      existing = m68k_render_plan_find_expression(plan, field_section, field->offset, UINT32_MAX,
        M68K_RENDER_PLANNED_EXPRESSION_TABLE_ENTRY);
      if (existing == NULL) existing = m68k_render_plan_find_expression(plan, field_section, field->offset,
        UINT32_MAX, M68K_RENDER_PLANNED_EXPRESSION_DATA_POINTER);
      if (existing != NULL) {
        size_t expression_index = (size_t)(existing - plan->expressions);
        expression.kind = existing->kind;
        plan->expressions[expression_index] = expression;
      } else if (m68k_render_plan_append_expression(plan, &expression) != 0) return -1;
    }
  }
  return 0;
}

static const M68kPlatformAddressUseIR *source_analysis_hardware_register_use_for_base_relative_operand(
    const M68kSourceAnalysisIR *source_analysis, size_t section_index, uint32_t offset, size_t operand_index,
    uint32_t displacement) {
  const M68kSectionAnalysisIR *section_analysis;
  size_t index;
  if (source_analysis == NULL || section_index > UINT32_MAX) return NULL;
  section_analysis = NULL;
  for (index = 0U; index < source_analysis->section_count; ++index) {
    if (source_analysis->sections[index].section_index == (uint32_t)section_index) {
      section_analysis = &source_analysis->sections[index];
      break;
    }
  }
  if (section_analysis == NULL) return NULL;
  for (index = 0U; index < section_analysis->platform_address_use_count; ++index) {
    const M68kPlatformAddressUseIR *use = &section_analysis->platform_address_uses[index];
    uint16_t base_id = PLATFORM_FACTS_V2_HARDWARE_BASE_ID_NONE;
    uint32_t register_offset = 0U;
    if (use->offset == offset && use->operand_index == operand_index &&
        use->use_shape == M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_REGISTER_FAMILY &&
        use->relative_register_offset == displacement && use->relative_base_offset_count != 0U)
      return use;
    if (use->offset != offset ||
        use->operand_index != operand_index ||
        use->use_shape != M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_REGISTER_ACCESS ||
        use->symbol_name == NULL ||
        use->symbol_name[0] == '\0' ||
        !platform_facts_v2_hardware_base_offset_for_address(M68K_PLATFORM_BACKEND_AMIGA_HUNK, use->address,
          &base_id, &register_offset) ||
        base_id == PLATFORM_FACTS_V2_HARDWARE_BASE_ID_NONE ||
        register_offset != displacement) {
      continue;
    }
    return use;
  }
  return NULL;
}

static int attach_amiga_hardware_register_symbols(const M68kRenderPlatformState *state,
    const M68kSourceAnalysisIR *source_analysis, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *source_instruction,
    M68kInstructionIR *instruction) {
  size_t operand_index;
  int attached = 0;
  if (instruction == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    int may_replace_generated_symbol =
      operand->symbol_ref.has_name != 0U && source_analysis != NULL &&
      (operand->symbol_ref.name_is_generated != 0U ||
       strncmp(operand->symbol_ref.name, "runtime_code_", 13U) == 0 ||
       strncmp(operand->symbol_ref.name, "runtime_address_", 16U) == 0);
    uint32_t value = 0U;
    uint8_t base_reg = 0U;
    int16_t displacement = 0;
    const char *base_symbol = NULL;
    char symbol_name[64];
    if (operand->symbol_ref.has_name != 0U && !may_replace_generated_symbol) continue;
    if (operand_is_address_displacement_local(operand, &base_reg, &displacement) &&
        displacement >= 0) {
      const M68kPlatformAddressUseIR *hardware_register_use = NULL;
      const char *hardware_base_symbol = NULL;
      uint32_t hardware_base_address = 0U;
      if (section != NULL && candidate != NULL) {
        hardware_register_use = source_analysis_hardware_register_use_for_base_relative_operand(source_analysis,
          section->section_index, candidate->offset, operand_index, (uint32_t)(uint16_t)displacement);
      }
      if (hardware_register_use == NULL &&
          state != NULL && base_reg < 8U && m68k_bitset_u32_has(state->address_hardware_base_known, base_reg)) {
        hardware_base_symbol = platform_facts_v2_hardware_base_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
          state->address_hardware_base_id[base_reg]);
        if (section != NULL && candidate != NULL && hardware_base_symbol != NULL &&
            platform_facts_v2_hardware_base_address(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
              state->address_hardware_base_id[base_reg], &hardware_base_address)) {
          hardware_register_use = source_analysis_platform_address_use_for_operand(source_analysis,
            section->section_index, candidate->offset, operand_index,
            hardware_base_address + (uint32_t)(uint16_t)displacement,
            M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_REGISTER_ACCESS);
        }
      }
      if (hardware_register_use != NULL && hardware_register_use->symbol_name != NULL &&
          hardware_register_use->symbol_name[0] != '\0') {
        attach_amiga_platform_symbol(operand, hardware_register_use->symbol_name);
        attached = 1;
        continue;
      }
      if (operand->symbol_ref.has_name != 0U) continue;
      if (source_analysis != NULL) continue;
      if (state == NULL || base_reg >= 8U || !m68k_bitset_u32_has(state->address_hardware_base_known, base_reg))
        continue;
      base_symbol = platform_facts_v2_hardware_base_offset_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
        state->address_hardware_base_id[base_reg], (uint32_t)(uint16_t)displacement, symbol_name,
        sizeof(symbol_name));
      if (base_symbol != NULL && base_symbol[0] != '\0') {
        attach_amiga_platform_symbol(operand, base_symbol);
        attached = 1;
        continue;
      }
      continue;
    }
    if (operand_absolute_offset_local(operand, &value)) {
      const M68kPlatformAddressUseIR *hardware_base_use;
      const M68kPlatformAddressUseIR *hardware_register_use;
      if (section == NULL || candidate == NULL) continue;
      hardware_base_use = source_analysis_platform_address_use_for_operand(source_analysis,
        section->section_index, candidate->offset, operand_index, value,
        M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_BASE_ADDRESS);
      if (source_instruction != NULL && source_instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
          hardware_base_use != NULL && hardware_base_use->symbol_name != NULL &&
          hardware_base_use->symbol_name[0] != '\0') {
        attach_amiga_platform_symbol(operand, hardware_base_use->symbol_name);
        attached = 1;
        continue;
      }
      hardware_register_use = source_analysis_platform_address_use_for_operand(source_analysis,
        section->section_index, candidate->offset, operand_index, value,
        M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_REGISTER_ACCESS);
      if (hardware_register_use == NULL) continue;
      if (hardware_register_use->symbol_name != NULL && hardware_register_use->symbol_name[0] != '\0') {
        attach_amiga_platform_symbol(operand, hardware_register_use->symbol_name);
        attached = 1;
        continue;
      }
      continue;
    }
    if (m68k_ir_operand_immediate_value(operand, &value)) {
      const M68kPlatformAddressUseIR *hardware_base_use;
      if (section == NULL || candidate == NULL) continue;
      base_symbol = platform_facts_v2_hardware_base_symbol_for_address(M68K_PLATFORM_BACKEND_AMIGA_HUNK, value);
      if (base_symbol == NULL || base_symbol[0] == '\0') continue;
      hardware_base_use = source_analysis_platform_address_use_for_operand(source_analysis,
        section->section_index, candidate->offset, operand_index, value,
        M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_BASE_ADDRESS);
      if (hardware_base_use == NULL) continue;
      if (hardware_base_use->symbol_name == NULL || hardware_base_use->symbol_name[0] == '\0') continue;
      attach_amiga_platform_symbol(operand, hardware_base_use->symbol_name);
      attached = 1;
    }
  }
  return attached;
}

static const char *manual_representation_symbol_name(const M68kRenderLookup *lookup,
    const M68kAnalysisManualRepresentation *representation) {
  const M68kAnalysisPolicy *policy;
  if (representation == NULL) return NULL;
  if (representation->symbol_id != 0U) return amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, representation->symbol_id);
  if (lookup == NULL || lookup->policy == NULL || representation->target_equate_index == 0U) return NULL;
  policy = lookup->policy;
  if (representation->target_equate_index > policy->target_equate_count ||
      representation->target_equate_index > M68K_ANALYSIS_TARGET_EQUATE_LIMIT)
    return NULL;
  return policy->target_equates[representation->target_equate_index - 1U].name;
}

static int apply_manual_operand_representations(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, M68kInstructionIR *instruction) {
  size_t operand_index;
  if (instruction == NULL) return -1;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    const M68kAnalysisManualRepresentation *representation;
    uint32_t value = 0U;
    uint8_t base_reg = 0U;
    int16_t displacement = 0;
    int32_t indexed_displacement = 0;
    int is_indexed_displacement = m68k_ir_operand_brief_index_displacement(operand, &indexed_displacement);
    int is_immediate = m68k_ir_operand_immediate_value(operand, &value);
    int is_base_displacement = operand_is_address_displacement_local(operand, &base_reg, &displacement);
    int is_absolute = operand_absolute_offset_local(operand, &value);
    int manual_displacement_symbol;
    representation = lookup_manual_operand_representation(lookup, section_index, offset, operand_index);
    manual_displacement_symbol = representation != NULL &&
      representation->style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL &&
      lookup != NULL && lookup->policy != NULL && representation->target_equate_index != 0U &&
      representation->target_equate_index <= lookup->policy->target_equate_count &&
      ((is_base_displacement && m68k_instruction_operand_decoded_ea_shape(operand) ==
          M68K_SIM_EA_SHAPE_DISPLACEMENT &&
        lookup->policy->target_equates[representation->target_equate_index - 1U].value == displacement) ||
       (is_indexed_displacement &&
        lookup->policy->target_equates[representation->target_equate_index - 1U].value == indexed_displacement));
    if (representation != NULL && representation->style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_HARDWARE_OFFSET) {
      char field[96];
      const char *symbol;
      if (!is_base_displacement || displacement < 0 ||
          representation->hardware_offset_base_id > UINT16_MAX ||
          (uint32_t)displacement != representation->hardware_register_offset) return -1;
      symbol = platform_facts_v2_hardware_base_offset_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
        (uint16_t)representation->hardware_offset_base_id, representation->hardware_register_offset,
        field, sizeof(field));
      if (symbol == NULL) return -1;
      m68k_ir_symbol_ref_init(&operand->symbol_ref);
      operand->symbol_ref.has_name = 1U;
      snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol);
      continue;
    }
    if (representation != NULL && representation->has_source_symbol) {
      uint32_t rendered_value = representation->source_symbol_offset;
      uint32_t runtime_value = 0U;
      int runtime_view;
      if ((!is_immediate && !is_absolute) || lookup == NULL ||
          representation->source_symbol_section >= lookup->section_count ||
          representation->source_symbol_offset >= lookup->label_extents[representation->source_symbol_section]) return -1;
      runtime_view = lookup_source_should_render_runtime_label(lookup, representation->source_symbol_section,
        representation->source_symbol_offset, &runtime_value);
      if (runtime_view) rendered_value = runtime_value;
      if (!!runtime_view != !!representation->source_symbol_runtime_view ||
          rendered_value != representation->source_symbol_value || value != rendered_value) return -1;
      m68k_ir_symbol_ref_init(&operand->symbol_ref);
      operand->symbol_ref.has_name = 1U;
      operand->symbol_ref.has_section = 1U;
      operand->symbol_ref.has_section_offset = 1U;
      operand->symbol_ref.section_index = representation->source_symbol_section;
      operand->symbol_ref.section_offset = representation->source_symbol_offset;
      operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
      (void)format_rendered_asm_label_with_generation(lookup, operand->symbol_ref.name,
        sizeof(operand->symbol_ref.name), representation->source_symbol_section, representation->source_symbol_offset);
      continue;
    }
    /* A validated displacement EQU remains the explicit presentation when
     * improved typing supplies an automatic field/array expression. Its exact
     * value and EA width are checked below. Other source/SDK names retain the
     * existing precedence, including immediate pointer storage. */
    if ((operand->symbol_ref.has_name != 0U && !manual_displacement_symbol &&
          ((!is_absolute && !is_immediate) || operand->symbol_ref.name_is_generated == 0U)) ||
        (!is_immediate && !is_base_displacement && !is_absolute && !is_indexed_displacement)) continue;
    representation = lookup_manual_operand_representation(lookup, section_index, offset, operand_index);
    if (representation == NULL) continue;
    if (representation->style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL) {
      const char *symbol_name = manual_representation_symbol_name(lookup, representation);
      if (symbol_name == NULL || !asm_symbol_name_is_safe_local(symbol_name)) continue;
      if (is_indexed_displacement && (lookup == NULL || lookup->policy == NULL ||
          representation->target_equate_index == 0U ||
          representation->target_equate_index > lookup->policy->target_equate_count ||
          lookup->policy->target_equates[representation->target_equate_index - 1U].value != indexed_displacement)) return -1;
      if (is_base_displacement && (m68k_instruction_operand_decoded_ea_shape(operand) != M68K_SIM_EA_SHAPE_DISPLACEMENT ||
          lookup == NULL || lookup->policy == NULL || representation->target_equate_index == 0U ||
          representation->target_equate_index > lookup->policy->target_equate_count ||
          lookup->policy->target_equates[representation->target_equate_index - 1U].value != displacement)) return -1;
      if (is_absolute && (lookup == NULL || lookup->policy == NULL ||
          representation->target_equate_index == 0U ||
          representation->target_equate_index > lookup->policy->target_equate_count ||
          lookup->policy->target_equates[representation->target_equate_index - 1U].value != (int64_t)value)) continue;
      m68k_ir_symbol_ref_init(&operand->symbol_ref);
      operand->symbol_ref.has_name = 1U;
      operand->symbol_ref.name_is_generated = 0U;
      operand->symbol_ref.name_provenance = representation->symbol_id != 0U ?
        M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA : M68K_IR_SYMBOL_PROVENANCE_NONE;
      operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
      snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol_name);
      continue;
    }
    if (!is_immediate) continue;
    operand->manual_representation_style_id = representation->style_id;
  }
  return 0;
}

static uint16_t render_amiga_struct_size_for_struct_id(uint16_t struct_id);

static int lookup_typed_app_slot_region_contains_auto_offset(const M68kRenderLookup *lookup,
    int16_t displacement) {
  size_t index;
  if (lookup == NULL) return 0;
  for (index = 0U; index < lookup->typed_app_slot_count; ++index) {
    const M68kRenderTypedAppSlot *slot = &lookup->typed_app_slots[index];
    uint16_t struct_size;
    int32_t region_start;
    int32_t region_end;
    if (slot->conflicted != 0U || slot->inline_region == 0U ||
        slot->struct_id == AMIGA_OS_STRUCT_ID_NONE) {
      continue;
    }
    struct_size = render_amiga_struct_size_for_struct_id(slot->struct_id);
    if (struct_size == 0U) continue;
    region_start = (int32_t)slot->displacement;
    region_end = region_start + (int32_t)struct_size;
    if ((int32_t)displacement > region_start && (int32_t)displacement < region_end) return 1;
  }
  return 0;
}

static int lookup_typed_app_slot_field_symbol_name(const M68kRenderLookup *lookup, int16_t displacement,
    char *base_symbol, size_t base_symbol_size, char *field_expr, size_t field_expr_size,
    int32_t *out_field_offset) {
  size_t index;
  int found = 0;
  char found_base_symbol[64];
  char found_field_expr[96];
  int32_t found_field_offset = 0;
  if (base_symbol != NULL && base_symbol_size > 0U) base_symbol[0] = '\0';
  if (field_expr != NULL && field_expr_size > 0U) field_expr[0] = '\0';
  if (out_field_offset != NULL) *out_field_offset = 0;
  if (lookup == NULL) return 0;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    if (slot->conflicted == 0U && render_base_field_slot_owner_is_app_base(slot) &&
        slot->displacement == displacement && slot->value_kind != M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS) {
      return 0;
    }
  }
  for (index = 0U; index < lookup->typed_app_slot_count; ++index) {
    const M68kRenderTypedAppSlot *slot = &lookup->typed_app_slots[index];
    uint16_t struct_size;
    int32_t field_offset;
    char candidate_base_symbol[64];
    char candidate_field_expr[96];
    if (slot->conflicted != 0U || slot->inline_region == 0U ||
        slot->struct_id == AMIGA_OS_STRUCT_ID_NONE) {
      continue;
    }
    struct_size = render_amiga_struct_size_for_struct_id(slot->struct_id);
    field_offset = (int32_t)displacement - (int32_t)slot->displacement;
    if (struct_size == 0U || field_offset <= 0 || field_offset >= (int32_t)struct_size ||
        field_offset < INT16_MIN || field_offset > INT16_MAX) {
      continue;
    }
    if (!lookup_app_base_field_slot_symbol_name(lookup, slot->displacement, candidate_base_symbol,
        sizeof(candidate_base_symbol)) ||
        !amiga_os_resolve_struct_field_symbol_expr_by_struct_id(slot->struct_id, (int16_t)field_offset, 0,
          candidate_field_expr, sizeof(candidate_field_expr))) {
      continue;
    }
    if (found != 0) {
      if (strcmp(found_base_symbol, candidate_base_symbol) != 0 ||
          strcmp(found_field_expr, candidate_field_expr) != 0 ||
          found_field_offset != field_offset) {
        return 0;
      }
      continue;
    }
    snprintf(found_base_symbol, sizeof(found_base_symbol), "%s", candidate_base_symbol);
    snprintf(found_field_expr, sizeof(found_field_expr), "%s", candidate_field_expr);
    found_field_offset = field_offset;
    found = 1;
  }
  if (found == 0) return 0;
  if (base_symbol != NULL && base_symbol_size > 0U)
    snprintf(base_symbol, base_symbol_size, "%s", found_base_symbol);
  if (field_expr != NULL && field_expr_size > 0U)
    snprintf(field_expr, field_expr_size, "%s", found_field_expr);
  if (out_field_offset != NULL) *out_field_offset = found_field_offset;
  return 1;
}

static uint16_t render_amiga_struct_size_for_struct_id(uint16_t struct_id) {
  int32_t max_end = 0;
  size_t index;
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE || amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id) == NULL)
    return 0U;
  for (index = 0U; index < AMIGA_OS_STRUCT_FIELD_COUNT; ++index) {
    const AmigaOsStructFieldInfo *field = amiga_os_struct_field_at(index);
    int32_t end;
    if (field == NULL || field->struct_id != struct_id) continue;
    end = (int32_t)field->offset + (int32_t)field->size;
    if (field->size == 0U) end = field->offset;
    if (end > max_end) max_end = end;
  }
  if (max_end <= 0) return 0U;
  return max_end > UINT16_MAX ? UINT16_MAX : (uint16_t)max_end;
}

static int32_t lookup_typed_app_slot_region_size(const M68kRenderLookup *lookup, int16_t displacement,
    char *owner_struct_name, size_t owner_struct_name_size) {
  size_t index;
  int32_t found_size = 0;
  uint16_t found_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  if (owner_struct_name != NULL && owner_struct_name_size > 0U) owner_struct_name[0] = '\0';
  if (lookup == NULL) return 0;
  for (index = 0U; index < lookup->typed_app_slot_count; ++index) {
    const M68kRenderTypedAppSlot *slot = &lookup->typed_app_slots[index];
    uint16_t struct_size;
    if (slot->conflicted != 0U || slot->inline_region == 0U || slot->displacement != displacement ||
        slot->struct_id == AMIGA_OS_STRUCT_ID_NONE) {
      continue;
    }
    struct_size = render_amiga_struct_size_for_struct_id(slot->struct_id);
    if (struct_size == 0U) continue;
    if (found_size != 0 && found_size != (int32_t)struct_size) return 0;
    if (found_struct_id != AMIGA_OS_STRUCT_ID_NONE && found_struct_id != slot->struct_id) return 0;
    found_size = (int32_t)struct_size;
    found_struct_id = slot->struct_id;
  }
  if (found_struct_id != AMIGA_OS_STRUCT_ID_NONE && owner_struct_name != NULL && owner_struct_name_size > 0U) {
    const char *struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, found_struct_id);
    if (struct_name != NULL) snprintf(owner_struct_name, owner_struct_name_size, "%s", struct_name);
  }
  return found_size;
}

static int lookup_rsset_use_site_binding_symbol_name(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint8_t operand_index, uint8_t base_reg, int16_t displacement,
    char *symbol_name, size_t symbol_name_size, int32_t *out_addend);

static int attach_amiga_app_base_slot_symbols(const M68kRenderLookup *lookup,
    const M68kRenderPlatformState *state, size_t section_index, uint32_t offset,
    M68kInstructionIR *instruction) {
  size_t operand_index;
  int attached = 0;
  if (lookup == NULL || state == NULL || instruction == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    uint8_t base_reg = 0U;
    int16_t displacement = 0;
    char symbol_name[64], field_expr[96];
    int32_t field_offset = 0;
    int32_t symbol_addend = 0;
    if (operand->symbol_ref.has_name != 0U) continue;
    if (!operand_is_address_displacement_local(operand, &base_reg, &displacement)) continue;
    if (lookup_rsset_use_site_binding_symbol_name(lookup, section_index, offset, (uint8_t)operand_index,
        base_reg, displacement, symbol_name, sizeof(symbol_name), &symbol_addend)) {
      m68k_ir_symbol_ref_init(&operand->symbol_ref);
      operand->symbol_ref.has_name = 1U;
      operand->symbol_ref.name_is_generated = 0U;
      operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
      operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
      operand->symbol_ref.addend = symbol_addend;
      snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol_name);
      attached = 1;
      continue;
    }
    if (m68k_bitset_u32_has(state->address_hardware_base_known, base_reg)) continue;
    if (m68k_bitset_u32_has(state->address_app_base_known, base_reg)) {
      if (!lookup_typed_app_slot_field_symbol_name(lookup, displacement, symbol_name, sizeof(symbol_name),
          field_expr, sizeof(field_expr), &field_offset) &&
          !lookup_app_base_field_slot_symbol_name(lookup, displacement, symbol_name, sizeof(symbol_name))) {
        continue;
      }
    } else if (m68k_bitset_u32_has(state->address_base_known, base_reg)) {
      if (!library_base_can_use_app_extension_slot(state->address_base_library[base_reg], displacement) ||
          (!lookup_typed_app_slot_field_symbol_name(lookup, displacement, symbol_name, sizeof(symbol_name),
            field_expr, sizeof(field_expr), &field_offset) &&
          !lookup_app_base_field_slot_symbol_name(lookup, displacement, symbol_name, sizeof(symbol_name)))) {
        if (!lookup_base_field_slot_symbol_name(lookup, state->address_base_library[base_reg], displacement,
            symbol_name, sizeof(symbol_name))) {
          continue;
        }
      }
    } else if (m68k_bitset_u32_has(state->address_layout_base_known, base_reg)) {
      if (!lookup_base_field_slot_symbol_name(lookup, state->address_layout_base_symbol[base_reg], displacement,
          symbol_name, sizeof(symbol_name))) {
        continue;
      }
    } else if (base_reg == 6U) {
      if (!lookup_typed_app_slot_field_symbol_name(lookup, displacement, symbol_name, sizeof(symbol_name),
          field_expr, sizeof(field_expr), &field_offset) &&
          !lookup_app_base_field_slot_symbol_name(lookup, displacement, symbol_name, sizeof(symbol_name))) {
        continue;
      }
    } else {
      continue;
    }
    m68k_ir_symbol_ref_init(&operand->symbol_ref);
    operand->symbol_ref.has_name = 1U;
    operand->symbol_ref.name_is_generated = 0U;
    operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
    snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol_name);
    if (field_offset != 0 && field_expr[0] != '\0') {
      operand->symbol_ref.has_symbolic_addend = 1U;
      operand->symbol_ref.symbolic_addend_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
      operand->symbol_ref.symbolic_addend_value = field_offset;
      snprintf(operand->symbol_ref.symbolic_addend_name, sizeof(operand->symbol_ref.symbolic_addend_name),
        "%s", field_expr);
    }
    attached = 1;
  }
  return attached;
}

static const M68kRenderTypedAccess *lookup_typed_access_for_operand(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset, uint8_t operand_index) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->typed_access_count; ++index) {
    const M68kRenderTypedAccess *access = &lookup->typed_accesses[index];
    if (access->section_index == section_index && access->offset == offset &&
        access->operand_index == operand_index) {
      return access;
    }
  }
  return NULL;
}

static int attach_amiga_typed_struct_field_symbols(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, M68kInstructionIR *instruction) {
  size_t operand_index;
  int attached = 0;
  if (lookup == NULL || instruction == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    const M68kRenderTypedAccess *access;
    if (operand->symbol_ref.has_name != 0U) continue;
    access = lookup_typed_access_for_operand(lookup, section_index, offset, (uint8_t)operand_index);
    if (access == NULL || access->field_expr[0] == '\0') continue;
    m68k_ir_symbol_ref_init(&operand->symbol_ref);
    operand->symbol_ref.has_name = 1U;
    operand->symbol_ref.name_is_generated = 0U;
    operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
    snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", access->field_expr);
    operand->symbol_ref.addend = -access->base_cursor;
    if (access->array_element_addend != 0 || access->field_byte_offset != 0U) {
      operand->symbol_ref.has_symbolic_addend = 1U;
      operand->symbol_ref.symbolic_addend_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
      operand->symbol_ref.symbolic_addend_value = 1;
      if (access->array_element_addend == 0) {
        snprintf(operand->symbol_ref.symbolic_addend_name, sizeof(operand->symbol_ref.symbolic_addend_name), "%u",
          (unsigned)access->field_byte_offset);
      } else if (access->field_byte_offset != 0U) {
        if (access->array_element_addend == 1 || access->array_element_addend == -1) {
          snprintf(operand->symbol_ref.symbolic_addend_name, sizeof(operand->symbol_ref.symbolic_addend_name),
            "%u%c%s_SIZEOF", (unsigned)access->field_byte_offset,
            access->array_element_addend < 0 ? '-' : '+', access->root_struct_name);
        } else {
          snprintf(operand->symbol_ref.symbolic_addend_name, sizeof(operand->symbol_ref.symbolic_addend_name),
            "%u%c%u*%s_SIZEOF", (unsigned)access->field_byte_offset,
            access->array_element_addend < 0 ? '-' : '+',
            (unsigned)(access->array_element_addend < 0 ? -access->array_element_addend : access->array_element_addend),
            access->root_struct_name);
        }
      } else if (access->array_element_addend == 1 || access->array_element_addend == -1) {
        snprintf(operand->symbol_ref.symbolic_addend_name, sizeof(operand->symbol_ref.symbolic_addend_name), "%s_SIZEOF",
          access->root_struct_name);
      } else {
        snprintf(operand->symbol_ref.symbolic_addend_name, sizeof(operand->symbol_ref.symbolic_addend_name), "%u*%s_SIZEOF",
          (unsigned)(access->array_element_addend < 0 ? -access->array_element_addend : access->array_element_addend),
          access->root_struct_name);
      }
    }
    attached = 1;
  }
  return attached;
}

static int render_asm_include_for_instruction_platform_symbols(M68kRenderIRPreview *preview,
    const M68kInstructionIR *instruction) {
  size_t operand_index;
  if (instruction == NULL) return 1;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (operand->symbol_ref.has_name == 0U) continue;
    if (!render_asm_include_for_symbol_expr(preview, operand->symbol_ref.name)) return 0;
    if (operand->symbol_ref.has_symbolic_addend != 0U &&
        operand->symbol_ref.symbolic_addend_name[0] != '\0' &&
        !render_asm_include_for_symbol_expr(preview, operand->symbol_ref.symbolic_addend_name)) {
      return 0;
    }
  }
  return 1;
}

static int instruction_loads_data_immediate(const M68kInstructionIR *instruction, uint8_t *out_reg,
    int16_t *out_value) {
  int32_t value;
  uint32_t immediate = 0U;
  uint8_t dest_reg = 0U;
  if (out_reg != NULL) *out_reg = 0U;
  if (out_value != NULL) *out_value = 0;
  if (instruction == NULL || out_reg == NULL || out_value == NULL || instruction->operand_count != 2U) return 0;
  if (!m68k_ir_operand_immediate_value(&instruction->operands[0], &immediate)) return 0;
  if (!operand_is_data_register_local(&instruction->operands[1], &dest_reg)) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ) {
    value = (int8_t)(immediate & 0xFFU);
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE) {
    value = (int32_t)immediate;
  } else {
    return 0;
  }
  if ((value < INT16_MIN || value > INT16_MAX) && instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE &&
      ((immediate & 0x8000U) != 0U)) {
    value = (int16_t)(immediate & 0xFFFFU);
  }
  if (value < INT16_MIN || value > INT16_MAX) return 0;
  *out_reg = dest_reg;
  *out_value = (int16_t)value;
  return 1;
}

static int instruction_writes_data_unknown_for_state(const M68kInstructionIR *instruction, uint8_t reg_index) {
  const M68kOperandIR *dest;
  uint8_t reg = 0U;
  if (instruction == NULL || reg_index >= 8U) return 0;
  if (instruction_has_call_flow(instruction)) return 1;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    return instruction->operand_count >= 2U &&
      reglist_contains_data_register_local(&instruction->operands[1], reg_index);
  }
  if (instruction->operand_count == 0U) return 0;
  dest = &instruction->operands[instruction->operand_count - 1U];
  return operand_is_data_register_local(dest, &reg) && reg == reg_index;
}

void platform_state_update_data_lvo_after_instruction(M68kRenderPlatformState *state,
    const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  int16_t lvo = 0;
  uint8_t reg = 0U;
  uint8_t reg_index;
  if (state == NULL || instruction == NULL) return;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  /* The following platform-state transfer exchanges all register contexts
   * together. Do not erase one source before that simultaneous transfer. */
  if (metadata != NULL && metadata->operation_type == M68K_SIM_OP_SWAP) return;
  if (instruction_loads_data_immediate(instruction, &reg, &lvo) && lvo < 0) {
    m68k_bitset_u32_set(&state->data_lvo_known, reg);
    state->data_lvo[reg] = lvo;
    return;
  }
  for (reg_index = 0U; reg_index < 8U; ++reg_index) {
    if (instruction_writes_data_unknown_for_state(instruction, reg_index))
      platform_state_clear_data_lvo(state, reg_index);
  }
}

static int lookup_indexed_vector_wrapper_index_reg(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint8_t *out_index_reg);
static int candidate_any_same_section_target(const M68kDecodeCandidate *candidate, size_t section_index,
    uint32_t *out_target);

const AmigaOsLibraryVectorInfo *attach_amiga_lvo_immediate_if_known(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  uint32_t next_offset;
  uint32_t wrapper_offset = 0U;
  int16_t lvo = 0;
  uint8_t reg = 0U;
  uint8_t wrapper_reg = 0U;
  const M68kDecodeCandidate *next_candidate;
  const char *library_name;
  const char *base_name;
  const AmigaOsLibraryVectorInfo *vector;
  const char *symbol_name;
  M68kOperandIR *operand;
  if (lookup == NULL || section == NULL || accepted_start == NULL || candidate == NULL || instruction == NULL)
    return NULL;
  if (!instruction_loads_data_immediate(instruction, &reg, &lvo)) return NULL;
  if (lvo >= 0) return NULL;
  next_offset = candidate->offset + candidate->byte_count;
  if (!accepted_start_at(section, accepted_start, next_offset)) return NULL;
  next_candidate = find_candidate_at_offset_local(section, next_offset);
  if (!candidate_direct_same_section_target(next_candidate, section->section_index, &wrapper_offset) &&
      !candidate_any_same_section_target(next_candidate, section->section_index, &wrapper_offset)) {
    wrapper_offset = next_offset;
  }
  if (!lookup_indexed_vector_wrapper_index_reg(lookup, section->section_index, wrapper_offset, &wrapper_reg) ||
      wrapper_reg != reg) {
    return NULL;
  }
  library_name = lookup_indexed_vector_wrapper_library(lookup, section->section_index, wrapper_offset);
  if (library_name == NULL) return NULL;
  base_name = platform_facts_v2_library_base_name_for_library_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK, library_name);
  if (base_name == NULL) return NULL;
  vector = amiga_os_find_library_vector(base_name, lvo);
  if (vector == NULL) return NULL;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, vector->lvo_symbol_id);
  if (symbol_name == NULL || symbol_name[0] == '\0') return NULL;
  operand = &instruction->operands[0];
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
  operand->symbol_ref.has_name = 1U;
  operand->symbol_ref.name_is_generated = 0U;
  operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
  operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
  snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol_name);
  return vector;
}

const AmigaOsLibraryVectorInfo *resolve_amiga_indexed_wrapper_call_vector(
    const M68kRenderLookup *lookup, const M68kRenderPlatformState *state, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate) {
  uint32_t wrapper_offset = 0U;
  const char *library_name;
  const char *base_name;
  uint8_t index_reg = 0U;
  if (lookup == NULL || state == NULL || section == NULL || candidate == NULL) return NULL;
  if (!candidate_has_call_flow(candidate)) return NULL;
  size_t wrapper_section_index = 0U;
  if (!candidate_direct_control_target(lookup, section->section_index, candidate, &wrapper_section_index,
      &wrapper_offset)) {
    return NULL;
  }
  library_name = lookup_indexed_vector_wrapper_library(lookup, wrapper_section_index, wrapper_offset);
  if (library_name == NULL || library_name[0] == '\0') return NULL;
  base_name = platform_facts_v2_library_base_name_for_library_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK, library_name);
  if (base_name == NULL || base_name[0] == '\0') return NULL;
  if (!lookup_indexed_vector_wrapper_index_reg(lookup, wrapper_section_index, wrapper_offset, &index_reg))
    return NULL;
  if (!m68k_bitset_u32_has(state->data_lvo_known, index_reg)) return NULL;
  return amiga_os_find_library_vector(base_name, state->data_lvo[index_reg]);
}

static int rendered_text_reencodes_original_bytes(const char *text, const M68kInstructionIR *source_instruction,
    const M68kInstructionIR *render_instruction, const uint8_t *raw_bytes, size_t raw_size) {
  M68kInstructionIR parsed;
  M68kDiagList parse_diagnostics;
  M68kDiagList encode_diagnostics;
  M68kIrEncodeResult encoded;
  uint8_t encoded_bytes[32];
  uint8_t parse_cpu;
  if (text == NULL || source_instruction == NULL || raw_bytes == NULL || raw_size > sizeof(encoded_bytes)) return 0;
  if (instruction_has_symbolic_or_relative_text(source_instruction)) return 1;
  if (m68k_instruction_needs_fpu_id_directive(source_instruction)) {
    AsmSourceFile source;
    M68kObject object;
    char source_text[512];
    int ok = 0;
    if (m68k_source_model_create(&source) != 0) return 0;
    memset(&object, 0, sizeof(object));
    snprintf(source_text, sizeof(source_text), "SECTION section_0,code\n\tFPU %u\n\t%s\n\tFPU 1\n",
      (unsigned)source_instruction->coprocessor_id, text);
    source.target_cpu = source_instruction->target_cpu;
    m68k_diag_list_reset(&parse_diagnostics);
    if (m68k_source_pipeline_parse_text_and_layout(&source, source_text, m68k_diag_sink(&parse_diagnostics)) &&
        !m68k_diag_has_errors(&parse_diagnostics)) {
      m68k_diag_list_reset(&encode_diagnostics);
      if (m68k_source_pipeline_emit_object(&source, &object, m68k_diag_sink(&encode_diagnostics)) &&
          !m68k_diag_has_errors(&encode_diagnostics) && object.section_count == 1U &&
          object.sections[0].data_size == raw_size && object.sections[0].data != NULL) {
        ok = memcmp(object.sections[0].data, raw_bytes, raw_size) == 0;
      }
    }
    m68k_object_destroy(&object);
    m68k_source_model_free(&source);
    return ok;
  }
  parse_cpu = render_instruction != NULL ? render_instruction->target_cpu : source_instruction->target_cpu;
  m68k_diag_list_reset(&parse_diagnostics);
  parsed = m68k_plain_parse_instruction_to_ir(text, parse_cpu, m68k_diag_sink(&parse_diagnostics));
  if (m68k_diag_has_errors(&parse_diagnostics)) return 0;
  m68k_diag_list_reset(&encode_diagnostics);
  encoded = m68k_ir_encode_one(&parsed, encoded_bytes, sizeof(encoded_bytes), m68k_diag_sink(&encode_diagnostics));
  if (m68k_diag_has_errors(&encode_diagnostics) || encoded.byte_count != raw_size) return 0;
  return memcmp(encoded_bytes, raw_bytes, raw_size) == 0;
}

Arena *render_lookup_arena(M68kRenderLookup *lookup) {
  if (lookup == NULL) return NULL;
  if (lookup->arena == NULL) {
    lookup->arena = arena_create(16384U);
    if (lookup->arena == NULL) return NULL;
  }
  return lookup->arena;
}

void *render_lookup_calloc(M68kRenderLookup *lookup, size_t count, size_t size) {
  Arena *arena = render_lookup_arena(lookup);
  if (arena == NULL) return NULL;
  return arena_calloc(arena, count, size);
}

void *render_lookup_grow_array(M68kRenderLookup *lookup, const void *old_items, size_t old_count,
    size_t item_size, size_t new_capacity) {
  Arena *arena;
  size_t old_size;
  size_t new_size;
  if (item_size == 0U || new_capacity == 0U) return NULL;
  if (old_count > ((size_t)-1) / item_size || new_capacity > ((size_t)-1) / item_size) return NULL;
  arena = render_lookup_arena(lookup);
  if (arena == NULL) return NULL;
  old_size = old_count * item_size;
  new_size = new_capacity * item_size;
  return arena_realloc_copy(arena, old_items, old_size, new_size);
}

void render_lookup_mark_boundary_flag(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint16_t flag) {
  if (lookup == NULL || flag == M68K_RENDER_BOUNDARY_NONE || section_index >= lookup->section_count ||
      lookup->render_boundary_flags == NULL || lookup->render_boundary_extents == NULL ||
      offset > lookup->render_boundary_extents[section_index] ||
      lookup->render_boundary_flags[section_index] == NULL) {
    return;
  }
  lookup->render_boundary_flags[section_index][offset] |= flag;
}

uint16_t render_lookup_boundary_flags(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->render_boundary_flags == NULL ||
      lookup->render_boundary_extents == NULL || offset > lookup->render_boundary_extents[section_index] ||
      lookup->render_boundary_flags[section_index] == NULL) {
    return M68K_RENDER_BOUNDARY_NONE;
  }
  return lookup->render_boundary_flags[section_index][offset];
}

static void render_lookup_set_label(M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->labels == NULL ||
      lookup->label_extents == NULL || offset > lookup->label_extents[section_index] ||
      lookup->labels[section_index] == NULL) {
    return;
  }
  lookup->labels[section_index][offset] = 1U;
  render_lookup_mark_boundary_flag(lookup, section_index, offset, M68K_RENDER_BOUNDARY_LABEL);
}

void m68k_render_lookup_destroy(M68kRenderLookup *lookup) {
  if (lookup == NULL) return;
  arena_destroy(lookup->arena);
  memset(lookup, 0, sizeof(*lookup));
}

static const char *lookup_policy_label_name(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint8_t domain) {
  uint16_t index;
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  if (policy == NULL) return NULL;
  for (index = 0U; index < policy->named_label_count && index < M68K_ANALYSIS_NAMED_LABEL_LIMIT; ++index) {
    const M68kAnalysisNamedLabel *label = &policy->named_labels[index];
    if (label->name[0] == '\0' || label->offset != offset) continue;
    if (label->domain != domain) continue;
    if (label->has_section_index) {
      if (label->section_index != (uint32_t)section_index) continue;
    } else if (section_index != 0U) {
      continue;
    }
    return label->name;
  }
  return NULL;
}

static const char *lookup_object_symbol_label_name(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  size_t index;
  const M68kObject *object = lookup != NULL ? lookup->object : NULL;
  if (lookup != NULL && section_index < lookup->section_count && lookup->object_symbol_labels != NULL &&
      lookup->object_symbol_label_extents != NULL && offset <= lookup->object_symbol_label_extents[section_index] &&
      lookup->object_symbol_labels[section_index] != NULL) {
    return lookup->object_symbol_labels[section_index][offset];
  }
  if (object == NULL) return NULL;
  for (index = 0U; index < object->symbol_count; ++index) {
    const M68kSymbol *symbol = &object->symbols[index];
    if (!symbol->defined || symbol->section_index != section_index || symbol->value != offset) continue;
    if (!asm_symbol_name_is_safe_local(symbol->name)) continue;
    return symbol->name;
  }
  return NULL;
}

uint8_t format_lookup_asm_label_with_generation(const M68kRenderLookup *lookup, char *buf, size_t buf_size,
    size_t section_index, uint32_t offset) {
  const char *policy_name = lookup_policy_label_name(
    lookup, section_index, offset, M68K_ANALYSIS_LABEL_DOMAIN_SOURCE);
  const char *object_name = NULL;
  if (buf == NULL || buf_size == 0U) return 1U;
  if (policy_name != NULL && policy_name[0] != '\0') {
    snprintf(buf, buf_size, "%s", policy_name);
    return 0U;
  }
  object_name = lookup_object_symbol_label_name(lookup, section_index, offset);
  if (object_name != NULL && object_name[0] != '\0') {
    snprintf(buf, buf_size, "%s", object_name);
    return 0U;
  }
  if (lookup != NULL && lookup->object != NULL &&
      lookup->object->platform_backend_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    const char *library_name = lookup_global_base_slot_library(lookup, section_index, offset);
    const char *base_name = platform_facts_v2_library_base_name_for_library_name(
      lookup->object->platform_backend_kind, library_name);
    if (base_name == NULL) base_name = library_name;
    if (base_name != NULL &&
        platform_amiga_format_global_base_slot_label(section_index, 'l', base_name, buf, buf_size)) {
      return 0U;
    }
  }
  format_asm_label(buf, buf_size, section_index, offset);
  return 1U;
}

static int structured_data_item_is_untyped_bytes_placeholder_local(const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_BYTES &&
    item->semantic_role_flags == 0U && item->source_pattern_id == 0U && item->size != 0U;
}

const M68kAnalysisStructuredDataItem *lookup_structured_data_item_at_offset(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  M68kRenderRangeOwnershipView range;
  if (lookup_range_ownership_at_offset(lookup, section_index, offset, &range)) return range.structured_item;
  return NULL;
}

const M68kAnalysisStructuredDataItem *lookup_structured_data_item_covering_offset(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  M68kRenderRangeOwnershipView range;
  if (lookup_range_ownership_covering_offset(lookup, section_index, offset, &range))
    return range.structured_item;
  return NULL;
}

static const M68kAnalysisStructuredDataItem *range_ownership_structured_item(
    const M68kRenderLookup *lookup, const M68kRenderRangeOwnershipView *range) {
  if (lookup == NULL || range == NULL) return NULL;
  if (range->structured_item_source == M68K_RENDER_RANGE_STRUCTURED_ITEM_POLICY) {
    if (lookup->policy == NULL || range->structured_item_index >= lookup->policy->structured_data_item_count ||
        range->structured_item_index >= M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT) {
      return NULL;
    }
    return &lookup->policy->structured_data_items[range->structured_item_index];
  }
  if (range->structured_item_source == M68K_RENDER_RANGE_STRUCTURED_ITEM_AUTO) {
    if (range->structured_item_index >= lookup->auto_structured_data_item_count) return NULL;
    return &lookup->auto_structured_data_items[range->structured_item_index];
  }
  return NULL;
}

static int hydrate_range_ownership_view(const M68kRenderLookup *lookup,
    const M68kRenderRangeOwnershipView *stored, M68kRenderRangeOwnershipView *out_range) {
  const M68kAnalysisStructuredDataItem *item;
  if (out_range != NULL) memset(out_range, 0, sizeof(*out_range));
  if (lookup == NULL || stored == NULL || out_range == NULL || stored->end_offset <= stored->start_offset) return 0;
  *out_range = *stored;
  item = range_ownership_structured_item(lookup, stored);
  if (item != NULL) {
    out_range->kind = m68k_analysis_structured_data_range_ownership_kind(item);
    out_range->status = item->table_conflicted ? M68K_RANGE_OWNERSHIP_STATUS_CONFLICT :
      M68K_RANGE_OWNERSHIP_STATUS_ACCEPTED;
    out_range->positive_evidence_flags = m68k_analysis_structured_data_range_ownership_evidence_flags(item);
    out_range->structured_item = item;
  }
  return 1;
}

int render_lookup_add_range_ownership_for_structured_item(M68kRenderLookup *lookup, size_t section_index,
    uint8_t structured_item_source, size_t structured_item_index, const M68kAnalysisStructuredDataItem *item) {
  M68kRenderRangeOwnershipView *grown;
  M68kRenderRangeOwnershipView *range;
  size_t next_capacity;
  size_t index;
  if (lookup == NULL || item == NULL || item->size == 0U || item->offset > UINT32_MAX - item->size) return 0;
  if (structured_item_source == M68K_RENDER_RANGE_STRUCTURED_ITEM_NONE) return 0;
  for (index = 0U; index < lookup->range_ownership_count; ++index) {
    const M68kRenderRangeOwnershipView *existing = &lookup->range_ownerships[index];
    if (existing->structured_item_source == structured_item_source &&
        existing->structured_item_index == structured_item_index) {
      return 0;
    }
  }
  if (lookup->range_ownership_count == lookup->range_ownership_capacity) {
    next_capacity = lookup->range_ownership_capacity == 0U ? 32U : lookup->range_ownership_capacity * 2U;
    grown = (M68kRenderRangeOwnershipView *)render_lookup_grow_array(lookup, lookup->range_ownerships,
      lookup->range_ownership_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->range_ownerships = grown;
    lookup->range_ownership_capacity = next_capacity;
  }
  range = &lookup->range_ownerships[lookup->range_ownership_count];
  memset(range, 0, sizeof(*range));
  range->section_index = section_index;
  range->start_offset = item->offset;
  range->end_offset = item->offset + item->size;
  range->structured_item_source = structured_item_source;
  range->structured_item_index = structured_item_index;
  ++lookup->range_ownership_count;
  return 0;
}

int lookup_range_ownership_at_offset(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    M68kRenderRangeOwnershipView *out_range) {
  M68kRenderRangeOwnershipView placeholder;
  int has_placeholder = 0;
  size_t index;
  if (lookup == NULL) return 0;
  memset(&placeholder, 0, sizeof(placeholder));
  for (index = 0U; index < lookup->range_ownership_count; ++index) {
    const M68kRenderRangeOwnershipView *range = &lookup->range_ownerships[index];
    M68kRenderRangeOwnershipView hydrated;
    if (range->section_index != section_index || range->start_offset != offset) continue;
    if (!hydrate_range_ownership_view(lookup, range, &hydrated)) continue;
    if (structured_data_item_is_untyped_bytes_placeholder_local(hydrated.structured_item)) {
      if (!has_placeholder) {
        placeholder = hydrated;
        has_placeholder = 1;
      }
      continue;
    }
    if (out_range != NULL) *out_range = hydrated;
    return 1;
  }
  if (has_placeholder) {
    if (out_range != NULL) *out_range = placeholder;
    return 1;
  }
  if (out_range != NULL) memset(out_range, 0, sizeof(*out_range));
  return 0;
}

int lookup_range_ownership_covering_offset(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    M68kRenderRangeOwnershipView *out_range) {
  M68kRenderRangeOwnershipView placeholder;
  int has_placeholder = 0;
  size_t index;
  if (lookup == NULL) return 0;
  memset(&placeholder, 0, sizeof(placeholder));
  for (index = 0U; index < lookup->range_ownership_count; ++index) {
    const M68kRenderRangeOwnershipView *range = &lookup->range_ownerships[index];
    M68kRenderRangeOwnershipView hydrated;
    if (range->section_index != section_index || offset < range->start_offset || offset >= range->end_offset)
      continue;
    if (!hydrate_range_ownership_view(lookup, range, &hydrated)) continue;
    if (structured_data_item_is_untyped_bytes_placeholder_local(hydrated.structured_item)) {
      if (!has_placeholder) {
        placeholder = hydrated;
        has_placeholder = 1;
      }
      continue;
    }
    if (out_range != NULL) *out_range = hydrated;
    return 1;
  }
  if (has_placeholder) {
    if (out_range != NULL) *out_range = placeholder;
    return 1;
  }
  if (out_range != NULL) memset(out_range, 0, sizeof(*out_range));
  return 0;
}

int lookup_range_ownership_at_index(const M68kRenderLookup *lookup, size_t index,
    M68kRenderRangeOwnershipView *out_range) {
  if (out_range != NULL) memset(out_range, 0, sizeof(*out_range));
  if (lookup == NULL || index >= lookup->range_ownership_count) return 0;
  return hydrate_range_ownership_view(lookup, &lookup->range_ownerships[index], out_range);
}

int structured_data_item_comment(const M68kAnalysisStructuredDataItem *item, char *comment,
    size_t comment_size) {
  const char *field_name;
  if (comment == NULL || comment_size == 0U) return 0;
  comment[0] = '\0';
  if (item == NULL) return 0;
  /* A range's public owner label is not a field annotation. In particular it
   * must not be repeated on every data row and retained thousands of times
   * when those rows are collected into one INCBIN. */
  field_name = item->field_name;
  if (item->struct_name[0] != '\0' && field_name != NULL && field_name[0] != '\0') {
    snprintf(comment, comment_size, "%s", field_name);
    return 1;
  }
  if (item->comment[0] != '\0') {
    snprintf(comment, comment_size, "%s", item->comment);
    return 1;
  }
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_STRING) return 0;
  {
    const char *role_name = m68k_analysis_structured_data_role_name_for_flags(structured_data_item_role_flags(item));
    if (role_name != NULL) {
      snprintf(comment, comment_size, "%s", role_name);
      return 1;
    }
  }
  return 0;
}

static int structured_data_item_constant_matches_bytes(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item) {
  uint32_t value = 0U;
  uint32_t mask = 0xFFFFFFFFU;
  if (section == NULL || section->data == NULL || item == NULL || item->has_constant_value == 0U ||
      item->constant_name[0] == '\0' || item->offset >= section->size) {
    return 0;
  }
  if (item->size == 1U && item->offset + 1U <= section->size) {
    value = section->data[item->offset];
    mask = 0xFFU;
  } else if (item->size == 2U && item->offset + 2U <= section->size) {
    value = m68k_read_u16be(section->data + item->offset);
    mask = 0xFFFFU;
  } else if (item->size == 4U && item->offset + 4U <= section->size) {
    value = m68k_read_u32be(section->data + item->offset);
  } else {
    return 0;
  }
  return value == ((uint32_t)item->constant_value & mask);
}

static int structured_data_item_raw_value(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, uint32_t *out_value) {
  if (out_value != NULL) *out_value = 0U;
  if (section == NULL || section->data == NULL || item == NULL || item->offset >= section->size) return 0;
  if (item->size == 1U && item->offset + 1U <= section->size) {
    if (out_value != NULL) *out_value = section->data[item->offset];
    return 1;
  }
  if (item->size == 2U && item->offset + 2U <= section->size) {
    if (out_value != NULL) *out_value = m68k_read_u16be(section->data + item->offset);
    return 1;
  }
  if (item->size == 4U && item->offset + 4U <= section->size) {
    if (out_value != NULL) *out_value = m68k_read_u32be(section->data + item->offset);
    return 1;
  }
  return 0;
}

static int structured_data_item_value_domain_expr(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, char *expr, size_t expr_size) {
  uint32_t value;
  if (expr == NULL || expr_size == 0U || item == NULL) return 0;
  expr[0] = '\0';
  if (item->value_domain[0] == '\0' || !structured_data_item_raw_value(section, item, &value)) return 0;
  return amiga_value_domain_symbolic_expr(item->value_domain, value, expr, expr_size);
}

int structured_data_item_symbolic_operand_expr(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, char *expr, size_t expr_size) {
  int32_t lib_size = 0;
  if (expr == NULL || expr_size == 0U || item == NULL) return 0;
  expr[0] = '\0';
  if (!((item->size == 1U && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_BYTES) ||
        (item->size == 2U && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS) ||
        (item->size == 4U && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS))) {
    return 0;
  }
  if (item->size == 4U &&
      item->platform_kind_id == M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_KIND_AMIGA_RESIDENT_AUTOINIT &&
      item->platform_field_id == M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_AMIGA_RESIDENT_BASE_SIZE) {
    if (section != NULL && section->data != NULL && item->offset <= section->size &&
        section->size - item->offset >= 4U &&
        render_amiga_constant_value_by_symbol_id(AMIGA_OS_SYMBOL_ID_LIB_SIZE, &lib_size) &&
        lib_size > 0 && (int32_t)m68k_read_u32be(section->data + item->offset) == lib_size) {
      snprintf(expr, expr_size, "LIB_SIZE");
      return 1;
    }
    snprintf(expr, expr_size, "app_SIZEOF");
    return 1;
  }
  if (structured_data_item_constant_matches_bytes(section, item)) {
    if (!asm_symbol_name_is_safe_local(item->constant_name)) return 0;
    snprintf(expr, expr_size, "%s", item->constant_name);
    return 1;
  }
  if (!structured_data_item_value_domain_expr(section, item, expr, expr_size)) return 0;
  return render_asm_include_for_symbol_expr(NULL, expr);
}

int structured_data_item_render_comment(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, char *comment, size_t comment_size) {
  char expr[96];
  size_t used;
  if (!structured_data_item_comment(item, comment, comment_size)) return 0;
  if (structured_data_item_constant_matches_bytes(section, item)) {
    snprintf(expr, sizeof(expr), "%s", item->constant_name);
  } else if (!structured_data_item_value_domain_expr(section, item, expr, sizeof(expr))) {
    return 1;
  }
  used = strlen(comment);
  if (used + strlen(expr) + 4U >= comment_size) return 1;
  snprintf(comment + used, comment_size - used, " = %s", expr);
  return 1;
}

static int runtime_address_maps_to_materialized_source(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t runtime_address);
static const char *runtime_address_ref_sink_role(const M68kRenderLookup *lookup, const M68kFact *fact);
static const char *lookup_runtime_address_value_semantic_role(const M68kRenderLookup *lookup,
  uint32_t runtime_address);
static int amiga_abs_exec_base_load_should_stay_absolute(const M68kRenderLookup *lookup,
    const M68kInstructionIR *instruction, size_t operand_index, const M68kOperandIR *operand,
    const M68kFact *fact);
static int runtime_address_ref_operand_can_render_materialized_label(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, const M68kFact *fact);
static void render_lookup_build_block_start_before_maps(M68kRenderLookup *lookup) {
  size_t section_index;
  if (lookup == NULL || lookup->block_starts == NULL || lookup->block_start_before_or_at == NULL ||
      lookup->block_start_before_or_at_extents == NULL) {
    return;
  }
  for (section_index = 0U; section_index < lookup->section_count; ++section_index) {
    uint32_t offset;
    uint32_t current = 0U;
    uint32_t extent = lookup->block_start_before_or_at_extents[section_index];
    if (extent == 0U || lookup->block_starts[section_index] == NULL ||
        lookup->block_start_before_or_at[section_index] == NULL) {
      continue;
    }
    for (offset = 0U; offset < extent; ++offset) {
      if (lookup->block_starts[section_index][offset] != 0U) current = offset;
      lookup->block_start_before_or_at[section_index][offset] = current;
    }
  }
}

static int materialized_runtime_code_operand_patch_anchor_offset(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t source_offset,
    uint32_t access_width, uint32_t *out_anchor_offset) {
  const M68kDecodeCandidate *anchor;
  uint32_t anchor_end;
  if (out_anchor_offset != NULL) *out_anchor_offset = 0U;
  if (lookup == NULL || section == NULL || accepted_start == NULL ||
      access_width == 0U || source_offset > UINT32_MAX - access_width) {
    return 0;
  }
  anchor = accepted_candidate_covering_offset_local(section, accepted_start, source_offset);
  if (anchor == NULL || anchor->byte_count == 0U || anchor->offset > UINT32_MAX - anchor->byte_count) return 0;
  anchor_end = anchor->offset + anchor->byte_count;
  if (source_offset <= anchor->offset || source_offset + access_width > anchor_end) return 0;
  if (out_anchor_offset != NULL) *out_anchor_offset = anchor->offset;
  return 1;
}

static void render_lookup_mark_materialized_runtime_code_operand_patch_labels(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  size_t section_index;
  uint8_t platform_kind = M68K_PLATFORM_BACKEND_UNKNOWN;
  if (lookup == NULL || decode == NULL || accepted_start == NULL) return;
  if (lookup->object != NULL) platform_kind = lookup->object->platform_backend_kind;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    const uint8_t *section_accepted_start = accepted_start[section_index];
    size_t candidate_index;
    if (section_accepted_start == NULL) continue;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      const M68kSimFormMetadata *metadata;
      size_t operand_index;
      if (candidate->offset >= section->size || section_accepted_start[candidate->offset] == 0U) continue;
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      metadata = m68k_sim_metadata_for_instruction(&instruction);
      if (metadata == NULL) continue;
      for (operand_index = 0U; operand_index < instruction.operand_count && operand_index < 4U; ++operand_index) {
        M68kOperandIR *operand = &instruction.operands[operand_index];
        uint32_t runtime_address = 0U;
        uint32_t source_offset = 0U;
        uint32_t access_width = 0U;
        uint32_t anchor_offset = 0U;
        if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_MEMORY_WRITE ||
            operand->symbol_ref.has_name != 0U ||
            !operand_absolute_offset_local(operand, &runtime_address)) {
          continue;
        }
        if (platform_facts_v2_address_has_symbolic_owner(platform_kind, runtime_address) ||
            !lookup_materialized_runtime_address_source_offset(lookup, section->section_index, runtime_address,
              &source_offset)) {
          continue;
        }
        access_width = render_instruction_access_width(&instruction, metadata->operand_access_kinds[operand_index]);
        if (!materialized_runtime_code_operand_patch_anchor_offset(lookup, section, section_accepted_start,
            source_offset, access_width, &anchor_offset)) {
          continue;
        }
        render_lookup_set_label(lookup, section->section_index, anchor_offset);
        render_lookup_mark_label_target_ref(lookup, section->section_index, anchor_offset);
      }
    }
  }
}

int m68k_render_lookup_build(M68kRenderLookup *lookup, const M68kObject *object, const M68kDecodeIR *decode,
    const M68kFactIR *facts, const M68kAnalysisPolicy *policy, uint8_t **accepted_start,
    const M68kAnalysisLabelPoint *analysis_labels, size_t analysis_label_count) {
  size_t section_index;
  size_t fact_index;
  size_t analysis_label_index;
  if (lookup == NULL || decode == NULL || facts == NULL) return -1;
  memset(lookup, 0, sizeof(*lookup));
  lookup->section_count = decode->section_count;
  lookup->object = object;
  lookup->policy = policy;
  lookup->labels = (uint8_t **)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->labels));
  lookup->label_target_refs =
    (uint8_t **)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->label_target_refs));
  lookup->label_statement_refs =
    (uint8_t **)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->label_statement_refs));
  lookup->storage_label_target_refs =
    (uint8_t **)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->storage_label_target_refs));
  lookup->object_symbol_labels =
    (const char ***)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->object_symbol_labels));
  lookup->relocations = (const M68kFact ***)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->relocations));
  lookup->anchors = (const M68kFact ***)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->anchors));
  lookup->block_starts = (uint8_t **)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->block_starts));
  lookup->block_start_before_or_at = (uint32_t **)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->block_start_before_or_at));
  lookup->render_boundary_flags = (uint16_t **)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->render_boundary_flags));
  lookup->label_extents = (uint32_t *)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->label_extents));
  lookup->label_target_ref_extents =
    (uint32_t *)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->label_target_ref_extents));
  lookup->label_statement_ref_extents =
    (uint32_t *)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->label_statement_ref_extents));
  lookup->storage_label_target_ref_extents =
    (uint32_t *)render_lookup_calloc(lookup, decode->section_count,
      sizeof(*lookup->storage_label_target_ref_extents));
  lookup->object_symbol_label_extents =
    (uint32_t *)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->object_symbol_label_extents));
  lookup->relocation_extents = (uint32_t *)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->relocation_extents));
  lookup->anchor_extents = (uint32_t *)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->anchor_extents));
  lookup->block_start_extents = (uint32_t *)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->block_start_extents));
  lookup->block_start_before_or_at_extents = (uint32_t *)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->block_start_before_or_at_extents));
  lookup->render_boundary_extents =
    (uint32_t *)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->render_boundary_extents));
  lookup->instruction_comment_indices =
    (size_t **)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->instruction_comment_indices));
  lookup->instruction_comment_extents =
    (uint32_t *)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->instruction_comment_extents));
  lookup->auto_structured_data_item_indices = (size_t **)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->auto_structured_data_item_indices));
  lookup->auto_structured_data_item_index_extents = (uint32_t *)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->auto_structured_data_item_index_extents));
  lookup->string_span_indices =
    (size_t **)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->string_span_indices));
  lookup->string_span_index_extents =
    (uint32_t *)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->string_span_index_extents));
  lookup->runtime_address_ref_indices =
    (M68kRenderRuntimeAddressRefIndex **)render_lookup_calloc(lookup, decode->section_count,
      sizeof(*lookup->runtime_address_ref_indices));
  lookup->runtime_address_ref_index_extents =
    (uint32_t *)render_lookup_calloc(lookup, decode->section_count,
      sizeof(*lookup->runtime_address_ref_index_extents));
  if (lookup->labels == NULL || lookup->label_target_refs == NULL || lookup->label_statement_refs == NULL ||
      lookup->storage_label_target_refs == NULL ||
      lookup->object_symbol_labels == NULL ||
      lookup->relocations == NULL || lookup->anchors == NULL || lookup->block_starts == NULL ||
      lookup->block_start_before_or_at == NULL || lookup->render_boundary_flags == NULL ||
      lookup->label_extents == NULL || lookup->label_target_ref_extents == NULL ||
      lookup->label_statement_ref_extents == NULL ||
      lookup->storage_label_target_ref_extents == NULL ||
      lookup->object_symbol_label_extents == NULL || lookup->relocation_extents == NULL ||
      lookup->anchor_extents == NULL || lookup->block_start_extents == NULL ||
      lookup->block_start_before_or_at_extents == NULL ||
      lookup->render_boundary_extents == NULL ||
      lookup->instruction_comment_indices == NULL || lookup->instruction_comment_extents == NULL ||
      lookup->auto_structured_data_item_indices == NULL ||
      lookup->auto_structured_data_item_index_extents == NULL ||
      lookup->string_span_indices == NULL || lookup->string_span_index_extents == NULL ||
      lookup->runtime_address_ref_indices == NULL || lookup->runtime_address_ref_index_extents == NULL)
    goto oom;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    uint32_t label_extent = render_section_extent(&decode->sections[section_index]);
    uint32_t block_start_extent = label_extent;
    uint32_t relocation_extent = decode->sections[section_index].size;
    uint32_t anchor_extent = relocation_extent, comment_extent = relocation_extent;
    uint32_t runtime_ref_extent = relocation_extent;
    lookup->label_extents[section_index] = label_extent;
    lookup->label_target_ref_extents[section_index] = label_extent;
    lookup->label_statement_ref_extents[section_index] = label_extent;
    lookup->storage_label_target_ref_extents[section_index] = label_extent;
    lookup->object_symbol_label_extents[section_index] = label_extent;
    lookup->relocation_extents[section_index] = relocation_extent;
    lookup->anchor_extents[section_index] = anchor_extent;
    lookup->block_start_extents[section_index] = block_start_extent;
    lookup->block_start_before_or_at_extents[section_index] = block_start_extent;
    lookup->render_boundary_extents[section_index] = label_extent;
    lookup->instruction_comment_extents[section_index] = comment_extent;
    lookup->auto_structured_data_item_index_extents[section_index] = label_extent;
    lookup->string_span_index_extents[section_index] = label_extent;
    lookup->runtime_address_ref_index_extents[section_index] = runtime_ref_extent;
    lookup->labels[section_index] =
      (uint8_t *)render_lookup_calloc(lookup, (size_t)label_extent + 1U, sizeof(*lookup->labels[section_index]));
    lookup->label_target_refs[section_index] =
      (uint8_t *)render_lookup_calloc(lookup, (size_t)label_extent + 1U,
        sizeof(*lookup->label_target_refs[section_index]));
    lookup->label_statement_refs[section_index] =
      (uint8_t *)render_lookup_calloc(lookup, (size_t)label_extent + 1U,
        sizeof(*lookup->label_statement_refs[section_index]));
    lookup->storage_label_target_refs[section_index] =
      (uint8_t *)render_lookup_calloc(lookup, (size_t)label_extent + 1U,
        sizeof(*lookup->storage_label_target_refs[section_index]));
    lookup->object_symbol_labels[section_index] =
      (const char **)render_lookup_calloc(lookup, (size_t)label_extent + 1U,
        sizeof(*lookup->object_symbol_labels[section_index]));
    if (relocation_extent != 0U) {
      lookup->relocations[section_index] =
        (const M68kFact **)render_lookup_calloc(lookup, relocation_extent,
          sizeof(*lookup->relocations[section_index]));
    }
    if (anchor_extent != 0U) {
      lookup->anchors[section_index] =
        (const M68kFact **)render_lookup_calloc(lookup, anchor_extent, sizeof(*lookup->anchors[section_index]));
    }
    if (block_start_extent != 0U) {
      lookup->block_starts[section_index] =
        (uint8_t *)render_lookup_calloc(lookup, block_start_extent, sizeof(*lookup->block_starts[section_index]));
      lookup->block_start_before_or_at[section_index] =
        (uint32_t *)render_lookup_calloc(lookup, block_start_extent,
          sizeof(*lookup->block_start_before_or_at[section_index]));
    }
    lookup->render_boundary_flags[section_index] =
      (uint16_t *)render_lookup_calloc(lookup, (size_t)label_extent + 1U,
        sizeof(*lookup->render_boundary_flags[section_index]));
    if (comment_extent != 0U) {
      lookup->instruction_comment_indices[section_index] =
        (size_t *)render_lookup_calloc(lookup, comment_extent,
          sizeof(*lookup->instruction_comment_indices[section_index]));
    }
    lookup->auto_structured_data_item_indices[section_index] =
      (size_t *)render_lookup_calloc(lookup, (size_t)label_extent + 1U,
        sizeof(*lookup->auto_structured_data_item_indices[section_index]));
    lookup->string_span_indices[section_index] =
      (size_t *)render_lookup_calloc(lookup, (size_t)label_extent + 1U,
        sizeof(*lookup->string_span_indices[section_index]));
    if (runtime_ref_extent != 0U) {
      lookup->runtime_address_ref_indices[section_index] =
        (M68kRenderRuntimeAddressRefIndex *)render_lookup_calloc(lookup, runtime_ref_extent,
          sizeof(*lookup->runtime_address_ref_indices[section_index]));
    }
    if (lookup->labels[section_index] == NULL || lookup->label_target_refs[section_index] == NULL ||
        lookup->label_statement_refs[section_index] == NULL ||
        lookup->storage_label_target_refs[section_index] == NULL ||
        lookup->object_symbol_labels[section_index] == NULL ||
        (relocation_extent != 0U && lookup->relocations[section_index] == NULL) ||
        (anchor_extent != 0U && lookup->anchors[section_index] == NULL) ||
        (block_start_extent != 0U && lookup->block_starts[section_index] == NULL) ||
        (block_start_extent != 0U && lookup->block_start_before_or_at[section_index] == NULL) ||
        lookup->render_boundary_flags[section_index] == NULL ||
        (comment_extent != 0U && lookup->instruction_comment_indices[section_index] == NULL) ||
        lookup->auto_structured_data_item_indices[section_index] == NULL ||
        lookup->string_span_indices[section_index] == NULL ||
        (runtime_ref_extent != 0U && lookup->runtime_address_ref_indices[section_index] == NULL))
      goto oom;
  }
  if (object != NULL) {
    size_t symbol_index;
    for (symbol_index = 0U; symbol_index < object->symbol_count; ++symbol_index) {
      const M68kSymbol *symbol = &object->symbols[symbol_index];
      if (!symbol->defined || symbol->section_index >= decode->section_count ||
          symbol->value > lookup->object_symbol_label_extents[symbol->section_index] ||
          !asm_symbol_name_is_safe_local(symbol->name)) {
        continue;
      }
      if (lookup->object_symbol_labels[symbol->section_index][symbol->value] == NULL) {
        lookup->object_symbol_labels[symbol->section_index][symbol->value] = symbol->name;
      }
    }
  }
  if (policy != NULL) {
    uint16_t label_index;
    uint16_t item_index;
    for (label_index = 0U; label_index < policy->named_label_count &&
         label_index < M68K_ANALYSIS_NAMED_LABEL_LIMIT; ++label_index) {
      const M68kAnalysisNamedLabel *label = &policy->named_labels[label_index];
      size_t label_section_index = label->has_section_index ? (size_t)label->section_index : 0U;
      if (label->name[0] == '\0' || label->domain != M68K_ANALYSIS_LABEL_DOMAIN_SOURCE ||
          label_section_index >= decode->section_count ||
          label->offset > lookup->label_extents[label_section_index]) {
        continue;
      }
      render_lookup_set_label(lookup, label_section_index, label->offset);
    }
    for (item_index = 0U; item_index < policy->structured_data_item_count &&
         item_index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++item_index) {
      const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[item_index];
      size_t item_section_index = item->has_section_index ? (size_t)item->section_index : 0U;
      if (item->size == 0U || item_section_index >= decode->section_count ||
          item->offset > lookup->render_boundary_extents[item_section_index]) {
        continue;
      }
      render_lookup_mark_boundary_flag(lookup, item_section_index, item->offset,
        M68K_RENDER_BOUNDARY_STRUCTURED_DATA);
      if (render_lookup_add_range_ownership_for_structured_item(lookup, item_section_index,
          M68K_RENDER_RANGE_STRUCTURED_ITEM_POLICY, item_index, item) != 0) {
        goto oom;
      }
    }
  }
  for (analysis_label_index = 0U; analysis_label_index < analysis_label_count; ++analysis_label_index) {
    const M68kAnalysisLabelPoint *label = &analysis_labels[analysis_label_index];
    if (label->section_index < decode->section_count &&
        label->offset <= lookup->label_extents[label->section_index]) {
      render_lookup_set_label(lookup, label->section_index, label->offset);
    }
  }
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *fact = &facts->facts[fact_index];
    if (fact->section_index >= decode->section_count) continue;
    if (fact->kind == M68K_FACT_CODE_START &&
        fact->reason != M68K_FACT_CODE_START_REASON_FALLTHROUGH &&
        fact->offset < lookup->block_start_extents[fact->section_index]) {
      lookup->block_starts[fact->section_index][fact->offset] = 1U;
      render_lookup_mark_boundary_flag(lookup, fact->section_index, fact->offset, M68K_RENDER_BOUNDARY_BLOCK_START);
      if (render_lookup_add_code_start_ref(lookup, fact) != 0) goto oom;
    } else if (fact->kind == M68K_FACT_RELOCATION_REF &&
        fact->offset < lookup->relocation_extents[fact->section_index] && fact->size != 0U) {
      lookup->relocations[fact->section_index][fact->offset] = fact;
      render_lookup_mark_boundary_flag(lookup, fact->section_index, fact->offset, M68K_RENDER_BOUNDARY_RELOCATION);
      render_lookup_mark_label_target_ref(lookup, fact->target_section_index, fact->target_offset);
      render_lookup_mark_label_statement_ref(lookup, fact->target_section_index, fact->target_offset);
      if (fact->target_section_index < decode->section_count &&
          fact->target_offset <= lookup->label_extents[fact->target_section_index]) {
        render_lookup_set_label(lookup, fact->target_section_index, fact->target_offset);
      }
    } else if (fact->kind == M68K_FACT_RELOCATION_ANCHOR &&
        fact->offset < lookup->anchor_extents[fact->section_index] && fact->size != 0U) {
      lookup->anchors[fact->section_index][fact->offset] = fact;
      render_lookup_mark_boundary_flag(lookup, fact->section_index, fact->offset, M68K_RENDER_BOUNDARY_ANCHOR);
    } else if (fact->kind == M68K_FACT_RUNTIME_ADDRESS_REF) {
      if (render_lookup_add_runtime_address_ref(lookup, fact) != 0) goto oom;
      if (fact->target_section_index < lookup->section_count &&
          fact->target_offset <= lookup->label_extents[fact->target_section_index]) {
        render_lookup_set_label(lookup, fact->target_section_index, fact->target_offset);
        render_lookup_mark_label_target_ref(lookup, fact->target_section_index, fact->target_offset);
        /* Source labels are planned only for a concrete operand which the
         * renderer will emit symbolically.  Runtime facts describing values
         * held in registers, slots, or memory never create source labels. */
        if (runtime_address_ref_operand_can_render_materialized_label(lookup, decode, fact)) {
          render_lookup_mark_label_statement_ref(lookup, fact->target_section_index, fact->target_offset);
        }
      }
    } else if (fact->kind == M68K_FACT_RUNTIME_ADDRESS_RANGE) {
      if (render_lookup_add_runtime_address_range(lookup, fact) != 0) goto oom;
    } else if (fact->kind == M68K_FACT_XREF) {
      render_lookup_mark_label_target_ref(lookup, fact->target_section_index, fact->target_offset);
    } else if (fact->kind == M68K_FACT_CODE_ACCEPTED) {
      if (render_lookup_add_code_start_ref(lookup, fact) != 0) goto oom;
    } else if (fact->kind == M68K_FACT_VIOLATION) {
      if (render_lookup_add_violation_ref(lookup, fact) != 0) goto oom;
      const M68kAnalysisStructuredDataItem *item =
        lookup_structured_data_item_covering_offset(lookup, fact->section_index, fact->offset);
      uint32_t comment_offset = fact->offset;
      char comment[192];
      comment[0] = '\0';
      if (item != NULL) {
        if (fact->offset == item->offset) {
          comment_offset = item->offset;
          snprintf(comment, sizeof(comment),
            "invalid overlap: decoded code at $%04X starts at structured data; emitted as data",
            (unsigned)fact->offset);
        }
      } else if (fact->target_section_index < decode->section_count) {
        item = lookup_structured_data_item_covering_offset(lookup, fact->target_section_index,
          fact->target_offset);
        if (item != NULL && fact->target_section_index == fact->section_index) {
          comment_offset = item->offset;
          snprintf(comment, sizeof(comment),
            "invalid overlap: decoded code at $%04X crosses structured data at $%04X; emitted as data",
            (unsigned)fact->offset, (unsigned)fact->target_offset);
        }
      }
      if (comment[0] != '\0' &&
          render_lookup_add_instruction_comment(lookup, fact->section_index, comment_offset, comment) != 0) {
        goto oom;
      }
    }
  }
  render_lookup_mark_materialized_runtime_code_operand_patch_labels(lookup, decode, accepted_start);
  render_lookup_build_block_start_before_maps(lookup);
  if (render_lookup_add_pc_relative_xrefs(lookup, decode, accepted_start) != 0) goto oom;
  lookup->build_complete = 1U;
  return 0;
oom:
  m68k_render_lookup_destroy(lookup);
  return -1;
}

int lookup_has_label(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  if ((render_lookup_boundary_flags(lookup, section_index, offset) & M68K_RENDER_BOUNDARY_LABEL) == 0U)
    return 0;
  if (lookup == NULL || section_index >= lookup->section_count || lookup->labels == NULL ||
      lookup->label_extents == NULL || offset > lookup->label_extents[section_index] ||
      lookup->labels[section_index] == NULL) {
    return 0;
  }
  return lookup->labels[section_index][offset] != 0U;
}

void m68k_render_lookup_materialize_relocation_target_labels(M68kRenderLookup *lookup) {
  size_t section_index;
  if (lookup == NULL || lookup->relocations == NULL || lookup->relocation_extents == NULL) return;
  for (section_index = 0U; section_index < lookup->section_count; ++section_index) {
    uint32_t offset;
    if (lookup->relocations[section_index] == NULL) continue;
    for (offset = 0U; offset < lookup->relocation_extents[section_index]; ++offset) {
      const M68kFact *fact = lookup->relocations[section_index][offset];
      if (fact == NULL || fact->target_section_index >= lookup->section_count ||
          fact->target_offset > lookup->label_extents[fact->target_section_index]) {
        continue;
      }
      render_lookup_set_label(lookup, fact->target_section_index, fact->target_offset);
      render_lookup_mark_label_target_ref(lookup, fact->target_section_index, fact->target_offset);
      render_lookup_mark_label_statement_ref(lookup, fact->target_section_index, fact->target_offset);
    }
  }
}

/* A byte-sized immediate consumes a word extension, but only its low byte is
 * architectural.  Some originals retain non-zero bits in the ignored high
 * byte.  No vasm instruction spelling can preserve those bits, so emit the
 * complete instruction words explicitly instead of presenting an invalid
 * immediate literal. */
static int instruction_has_noncanonical_byte_immediate_extension(const M68kInstructionIR *instruction,
    const uint8_t *raw_bytes, size_t raw_size) {
  ByteImmediateExtensionSite sites[4];
  size_t site_count;
  size_t site_index;
  if (instruction == NULL || raw_bytes == NULL) return 0;
  site_count = collect_byte_immediate_extension_sites(instruction, sites, sizeof(sites) / sizeof(sites[0]));
  for (site_index = 0U; site_index < site_count; ++site_index) {
    uint8_t operand_index = sites[site_index].operand_index;
    uint16_t raw_word;
    if (sites[site_index].byte_offset + 1U >= raw_size || operand_index >= instruction->operand_count) continue;
    raw_word = m68k_read_u16be(raw_bytes + sites[site_index].byte_offset);
    if ((raw_word & 0xFF00U) != 0U &&
        (raw_word & 0x00FFU) == (instruction->operands[operand_index].value.value & 0xFFU)) return 1;
  }
  return 0;
}

static int format_raw_instruction_words(char *out_text, size_t out_text_size, const uint8_t *raw_bytes,
    size_t raw_size) {
  size_t used = 0U;
  size_t byte_offset;
  int written;
  if (out_text == NULL || out_text_size == 0U || raw_bytes == NULL || raw_size == 0U || (raw_size & 1U) != 0U)
    return -1;
  written = snprintf(out_text, out_text_size, "dc.w ");
  if (written < 0 || (size_t)written >= out_text_size) return -1;
  used = (size_t)written;
  for (byte_offset = 0U; byte_offset < raw_size; byte_offset += 2U) {
    written = snprintf(out_text + used, out_text_size - used, "%s$%04X", byte_offset == 0U ? "" : ",",
        (unsigned)m68k_read_u16be(raw_bytes + byte_offset));
    if (written < 0 || (size_t)written >= out_text_size - used) return -1;
    used += (size_t)written;
  }
  return 0;
}

const M68kFact *lookup_relocation_at(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  if ((render_lookup_boundary_flags(lookup, section_index, offset) & M68K_RENDER_BOUNDARY_RELOCATION) == 0U)
    return NULL;
  if (lookup == NULL || section_index >= lookup->section_count || lookup->relocations == NULL ||
      lookup->relocation_extents == NULL || offset >= lookup->relocation_extents[section_index] ||
      lookup->relocations[section_index] == NULL) {
    return NULL;
  }
  return lookup->relocations[section_index][offset];
}

static const M68kFact *lookup_anchor_at(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  if ((render_lookup_boundary_flags(lookup, section_index, offset) & M68K_RENDER_BOUNDARY_ANCHOR) == 0U)
    return NULL;
  if (lookup == NULL || section_index >= lookup->section_count || lookup->anchors == NULL ||
      lookup->anchor_extents == NULL || offset >= lookup->anchor_extents[section_index] ||
      lookup->anchors[section_index] == NULL) {
    return NULL;
  }
  return lookup->anchors[section_index][offset];
}

static int runtime_range_contains_source(const M68kFact *range, size_t section_index, uint32_t source_offset,
    uint32_t *out_runtime_address) {
  uint32_t delta;
  if (out_runtime_address != NULL) *out_runtime_address = 0U;
  if (range == NULL || range->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE || !range->has_runtime_address ||
      range->section_index != section_index || source_offset < range->offset) {
    return 0;
  }
  delta = source_offset - range->offset;
  if (delta >= range->size || range->runtime_address > UINT32_MAX - delta) return 0;
  if (out_runtime_address != NULL) *out_runtime_address = range->runtime_address + delta;
  return 1;
}

static int runtime_range_contains_runtime_ref_target(const M68kFact *range, const M68kFact *ref) {
  uint32_t expected_runtime = 0U;
  if (range == NULL || ref == NULL || ref->kind != M68K_FACT_RUNTIME_ADDRESS_REF ||
      !ref->has_runtime_address || ref->target_section_index != range->section_index) {
    return 0;
  }
  if (!runtime_range_contains_source(range, ref->target_section_index, ref->target_offset, &expected_runtime))
    return 0;
  return expected_runtime == ref->runtime_address;
}

static int runtime_range_contains_policy_entry_point(const M68kRenderLookup *lookup, const M68kFact *range) {
  uint16_t index;
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  if (policy == NULL || range == NULL || range->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_POLICY) return 0;
  for (index = 0U; index < policy->runtime_entry_point_count &&
       index < M68K_ANALYSIS_RUNTIME_ENTRY_POINT_LIMIT; ++index) {
    const M68kAnalysisRuntimeEntryPoint *entry = &policy->runtime_entry_points[index];
    uint32_t delta;
    if ((entry->has_section_index ? entry->section_index : 0U) != (uint32_t)range->section_index) continue;
    if (entry->runtime_address < range->runtime_address) continue;
    delta = entry->runtime_address - range->runtime_address;
    if (delta < range->size) return 1;
  }
  return 0;
}

static void runtime_view_relationship_clear(M68kRuntimeViewRelationshipIR *relationship) {
  if (relationship != NULL) memset(relationship, 0, sizeof(*relationship));
}

static void runtime_view_relationship_set_range(const M68kRenderLookup *lookup, const M68kFact *related,
    uint8_t kind, M68kRuntimeViewRelationshipIR *relationship) {
  size_t index;
  if (relationship == NULL) return;
  runtime_view_relationship_clear(relationship);
  if (lookup == NULL || related == NULL || kind == M68K_RUNTIME_VIEW_RELATIONSHIP_NONE) return;
  relationship->kind = kind;
  relationship->runtime_view_id = UINT32_MAX;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    if (lookup->runtime_address_ranges[index].fact == related) {
      relationship->runtime_view_id = (uint32_t)index;
      break;
    }
  }
  relationship->storage_offset = related->offset;
  relationship->runtime_address = related->runtime_address;
  relationship->size = related->size;
}

static int runtime_range_is_crossed_by_storage_xref(const M68kRenderLookup *lookup, const M68kFact *range) {
  size_t index;
  uint32_t range_end;
  if (lookup == NULL || range == NULL || range->size == 0U || range->offset > UINT32_MAX - range->size)
    return 1;
  range_end = range->offset + range->size;
  for (index = 0U; index < lookup->xref_count; ++index) {
    const M68kRenderXref *xref = &lookup->xrefs[index];
    uint32_t lo, hi;
    if (xref->section_index != range->section_index || xref->target_section_index != range->section_index ||
        xref->offset == xref->target_offset) {
      continue;
    }
    if (xref->offset < xref->target_offset) {
      lo = xref->offset;
      hi = xref->target_offset;
    } else {
      lo = xref->target_offset;
      hi = xref->offset;
    }
    if (lo >= range->offset && hi < range_end) continue;
    if (lo < range_end && range->offset < hi) return 1;
  }
  return 0;
}

static int runtime_range_is_exited_to_larger_runtime_range(const M68kRenderLookup *lookup,
    const M68kFact *range, const M68kFact **out_related) {
  size_t ref_index;
  uint32_t range_end;
  if (out_related != NULL) *out_related = NULL;
  if (lookup == NULL || range == NULL || range->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
      range->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY ||
      range->confidence >= M68K_FACT_CONFIDENCE_REQUIRED || range->size == 0U ||
      range->offset > UINT32_MAX - range->size) {
    return 0;
  }
  range_end = range->offset + range->size;
  for (ref_index = 0U; ref_index < lookup->runtime_address_ref_count; ++ref_index) {
    const M68kFact *ref = lookup->runtime_address_refs[ref_index].fact;
    size_t other_index;
    if (ref == NULL || ref->section_index != range->section_index ||
        ref->target_section_index != range->section_index || ref->offset < range->offset ||
        ref->offset >= range_end) {
      continue;
    }
    if (ref->target_offset >= range->offset && ref->target_offset < range_end) continue;
    for (other_index = 0U; other_index < lookup->runtime_address_range_count; ++other_index) {
      const M68kFact *other = lookup->runtime_address_ranges[other_index].fact;
      uint32_t other_runtime = 0U;
      if (other == NULL || other == range || other->section_index != range->section_index ||
          other->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE || other->size <= range->size) {
        continue;
      }
      if (other->runtime_kind == M68K_FACT_RUNTIME_RANGE_KIND_POLICY && other->offset == range->offset &&
          other->offset == 0U && other->has_runtime_address && range->has_runtime_address &&
          range->runtime_address < other->runtime_address) {
        continue;
      }
      if (runtime_range_contains_source(other, ref->target_section_index, ref->target_offset,
          &other_runtime) && other_runtime == ref->runtime_address) {
        if (out_related != NULL) *out_related = other;
        return 1;
      }
    }
  }
  return 0;
}

static int runtime_range_is_redundant_contained_view(const M68kRenderLookup *lookup, const M68kFact *range,
    const M68kFact **out_related) {
  size_t index;
  uint32_t range_end;
  if (out_related != NULL) *out_related = NULL;
  if (lookup == NULL || range == NULL || range->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
      !range->has_runtime_address || range->size == 0U || range->offset > UINT32_MAX - range->size) {
    return 0;
  }
  range_end = range->offset + range->size;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *other = lookup->runtime_address_ranges[index].fact;
    uint32_t other_end;
    uint32_t delta;
    if (other == NULL || other == range || other->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
        other->runtime_kind == M68K_FACT_RUNTIME_RANGE_KIND_CONFLICTING_DISCOVERED_COPY ||
        !other->has_runtime_address || other->section_index != range->section_index ||
        other->size == 0U || other->offset > UINT32_MAX - other->size ||
        range->offset < other->offset) {
      continue;
    }
    other_end = other->offset + other->size;
    if (range_end > other_end) continue;
    delta = range->offset - other->offset;
    if (delta > UINT32_MAX - other->runtime_address) continue;
    if (other->runtime_address + delta != range->runtime_address) continue;
    if (other->offset < range->offset || other->size > range->size) {
      if (out_related != NULL) *out_related = other;
      return 1;
    }
  }
  return 0;
}

static int runtime_range_has_storage_continuation(const M68kRenderLookup *lookup, const M68kFact *range) {
  const M68kSection *section;
  uint32_t extent, range_end;
  if (lookup == NULL || lookup->object == NULL || range == NULL ||
      range->section_index >= lookup->object->section_count || range->size == 0U ||
      range->offset > UINT32_MAX - range->size) {
    return 1;
  }
  section = &lookup->object->sections[range->section_index];
  extent = section->size != 0U ? section->size : section->data_size;
  range_end = range->offset + range->size;
  return range_end < extent;
}

static int runtime_range_has_incomplete_source_range(const M68kRenderLookup *lookup, const M68kFact *range) {
  const M68kSection *section;
  uint32_t extent;
  if (lookup == NULL || lookup->object == NULL || range == NULL ||
      range->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
      range->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY ||
      range->section_index >= lookup->object->section_count || range->size == 0U) {
    return 0;
  }
  section = &lookup->object->sections[range->section_index];
  extent = section->size != 0U ? section->size : section->data_size;
  return range->offset > extent || range->size > extent - range->offset;
}

static int runtime_range_contains_nested_runtime_range(const M68kRenderLookup *lookup, const M68kFact *range) {
  size_t index;
  uint64_t range_end;
  if (lookup == NULL || range == NULL || range->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
      range->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY || range->size == 0U ||
      range->offset > UINT32_MAX - range->size) {
    return 0;
  }
  range_end = (uint64_t)range->offset + range->size;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *other = lookup->runtime_address_ranges[index].fact;
    if (other == NULL || other == range || other->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
        other->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY ||
        other->section_index != range->section_index || other->offset <= range->offset ||
        (other->offset & 1U) != 0U || (other->runtime_address & 1U) != 0U ||
        (uint64_t)other->offset >= range_end) {
      continue;
    }
    return 1;
  }
  return 0;
}

static int runtime_range_is_full_source_policy_load_view(const M68kRenderLookup *lookup, const M68kFact *range) {
  const M68kSection *section;
  uint32_t extent;
  if (lookup == NULL || lookup->object == NULL || range == NULL ||
      range->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_POLICY || range->section_index >= lookup->object->section_count ||
      range->offset != 0U || !range->has_runtime_address) {
    return 0;
  }
  section = &lookup->object->sections[range->section_index];
  extent = section->size != 0U ? section->size : section->data_size;
  return extent != 0U && range->size == extent && range->runtime_address != 0U;
}

static int runtime_range_has_code_start_ref(const M68kRenderLookup *lookup, const M68kFact *range) {
  size_t index;
  uint64_t range_start, range_end;
  if (lookup == NULL || range == NULL || range->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
      !range->has_runtime_address || range->size == 0U) {
    return 0;
  }
  range_start = range->runtime_address;
  range_end = range_start + range->size;
  for (index = 0U; index < lookup->code_start_ref_count; ++index) {
    const M68kFact *ref = lookup->code_start_refs[index].fact;
    if (ref == NULL || ref->kind != M68K_FACT_CODE_START || ref->section_index != range->section_index ||
        ref->confidence < M68K_FACT_CONFIDENCE_TOOL_INFERRED || !ref->has_runtime_address) {
      continue;
    }
    if (ref->runtime_address >= range_start && (uint64_t)ref->runtime_address < range_end) return 1;
  }
  return 0;
}

static int runtime_range_has_start_entry_and_internal_code_ref(const M68kRenderLookup *lookup,
    const M68kFact *range) {
  size_t index;
  uint64_t range_start, range_end;
  int has_start_entry = 0;
  int has_start_control_target = 0;
  int has_internal_entry = 0;
  if (lookup == NULL || range == NULL || range->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
      range->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY ||
      !range->has_runtime_address || range->size == 0U) {
    return 0;
  }
  range_start = range->runtime_address;
  range_end = range_start + range->size;
  for (index = 0U; index < lookup->code_start_ref_count; ++index) {
    const M68kFact *ref = lookup->code_start_refs[index].fact;
    if (ref == NULL || (ref->kind != M68K_FACT_CODE_START && ref->kind != M68K_FACT_CODE_ACCEPTED) ||
        ref->section_index != range->section_index ||
        ref->confidence < M68K_FACT_CONFIDENCE_TOOL_INFERRED || !ref->has_runtime_address ||
        ref->runtime_address < range_start || (uint64_t)ref->runtime_address >= range_end) {
      continue;
    }
    if (ref->offset == range->offset && ref->runtime_address == range->runtime_address) {
      if (ref->reason == M68K_FACT_CODE_START_REASON_RUNTIME_VIEW_ENTRY) has_start_entry = 1;
      if (ref->reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET) has_start_control_target = 1;
    } else {
      has_internal_entry = 1;
    }
  }
  return has_start_entry && has_internal_entry && !has_start_control_target;
}

static int runtime_range_has_start_entry_without_start_control(const M68kRenderLookup *lookup,
    const M68kFact *range) {
  size_t index;
  uint64_t range_start, range_end;
  int has_start_entry = 0;
  int has_start_control_target = 0;
  if (lookup == NULL || range == NULL || range->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
      range->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY ||
      !range->has_runtime_address || range->size == 0U) {
    return 0;
  }
  range_start = range->runtime_address;
  range_end = range_start + range->size;
  for (index = 0U; index < lookup->code_start_ref_count; ++index) {
    const M68kFact *ref = lookup->code_start_refs[index].fact;
    if (ref == NULL || ref->kind != M68K_FACT_CODE_START ||
        ref->section_index != range->section_index ||
        ref->confidence < M68K_FACT_CONFIDENCE_TOOL_INFERRED || !ref->has_runtime_address ||
        ref->runtime_address < range_start || (uint64_t)ref->runtime_address >= range_end ||
        ref->offset != range->offset || ref->runtime_address != range->runtime_address) {
      continue;
    }
    if (ref->reason == M68K_FACT_CODE_START_REASON_RUNTIME_VIEW_ENTRY) has_start_entry = 1;
    if (ref->reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET) has_start_control_target = 1;
  }
  return has_start_entry && !has_start_control_target;
}

static int runtime_range_has_internal_control_entry_without_start_control(const M68kRenderLookup *lookup,
    const M68kFact *range) {
  size_t index;
  uint64_t range_start, range_end;
  int has_start_control_target = 0;
  int has_internal_control_target = 0;
  if (lookup == NULL || range == NULL || range->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
      range->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY ||
      !range->has_runtime_address || range->size == 0U) {
    return 0;
  }
  range_start = range->runtime_address;
  range_end = range_start + range->size;
  for (index = 0U; index < lookup->code_start_ref_count; ++index) {
    const M68kFact *ref = lookup->code_start_refs[index].fact;
    if (ref == NULL || ref->kind != M68K_FACT_CODE_START ||
        ref->reason != M68K_FACT_CODE_START_REASON_CONTROL_TARGET ||
        ref->section_index != range->section_index ||
        ref->confidence < M68K_FACT_CONFIDENCE_TOOL_INFERRED || !ref->has_runtime_address ||
        ref->runtime_address < range_start || (uint64_t)ref->runtime_address >= range_end) {
      continue;
    }
    if (ref->offset == range->offset && ref->runtime_address == range->runtime_address) {
      has_start_control_target = 1;
    } else {
      has_internal_control_target = 1;
    }
  }
  return has_internal_control_target && !has_start_control_target;
}

static int runtime_range_is_overlaid_by_runtime_copy(const M68kRenderLookup *lookup, const M68kFact *range,
    const M68kFact **out_related) {
  size_t index;
  uint64_t range_source_start, range_source_end;
  if (out_related != NULL) *out_related = NULL;
  if (lookup == NULL || range == NULL || range->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
      range->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_POLICY || !range->has_runtime_address ||
      range->offset != 0U || range->size == 0U) {
    return 0;
  }
  range_source_start = range->offset;
  range_source_end = range_source_start + range->size;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *other = lookup->runtime_address_ranges[index].fact;
    uint64_t other_source_start, other_source_end;
    if (other == NULL || other == range || other->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
        other->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY ||
        other->section_index != range->section_index || other->offset != 0U ||
        !other->has_runtime_address || other->runtime_address >= range->runtime_address ||
        other->size == 0U || !runtime_range_has_code_start_ref(lookup, other)) {
      continue;
    }
    other_source_start = other->offset;
    other_source_end = other_source_start + other->size;
    if (range_source_start < other_source_end && other_source_start < range_source_end) {
      if (out_related != NULL) *out_related = other;
      return 1;
    }
  }
  return 0;
}

static M68kRenderRuntimeAddressRange *lookup_runtime_range_slot_for_fact(const M68kRenderLookup *lookup,
    const M68kFact *range) {
  size_t index;
  if (lookup == NULL || range == NULL || lookup->runtime_address_ranges == NULL) return NULL;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    if (lookup->runtime_address_ranges[index].fact == range) {
      return (M68kRenderRuntimeAddressRange *)&lookup->runtime_address_ranges[index];
    }
  }
  return NULL;
}

static int lookup_runtime_range_materialization_uncached(const M68kRenderLookup *lookup, const M68kFact *range,
    uint8_t *out_materialized, uint8_t *out_reason, M68kRuntimeViewRelationshipIR *out_relationship) {
  size_t index;
  const M68kFact *related = NULL;
  if (out_materialized != NULL) *out_materialized = 0U;
  if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_MATERIALIZATION_REASON_NONE;
  runtime_view_relationship_clear(out_relationship);
  if (lookup == NULL || range == NULL) return 0;
  if (range->runtime_kind == M68K_FACT_RUNTIME_RANGE_KIND_CONFLICTING_DISCOVERED_COPY) {
    if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_SUPPRESSED_CONFLICTING_DISCOVERED_COPY;
    return 0;
  }
  if (runtime_range_is_exited_to_larger_runtime_range(lookup, range, &related)) {
    if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_SUPPRESSED_EXIT_TO_LARGER_RUNTIME_RANGE;
    runtime_view_relationship_set_range(lookup, related,
      M68K_RUNTIME_VIEW_RELATIONSHIP_EXITS_TO_LARGER_RUNTIME_RANGE, out_relationship);
    return 0;
  }
  if (runtime_range_is_redundant_contained_view(lookup, range, &related)) {
    if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_SUPPRESSED_REDUNDANT_CONTAINED_VIEW;
    runtime_view_relationship_set_range(lookup, related,
      M68K_RUNTIME_VIEW_RELATIONSHIP_CONTAINED_BY_RUNTIME_RANGE, out_relationship);
    return 0;
  }
  if (runtime_range_has_incomplete_source_range(lookup, range)) {
    if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_SUPPRESSED_INCOMPLETE_SOURCE_RANGE;
    return 0;
  }
  if (range->runtime_kind == M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY && range->offset == 0U &&
      runtime_range_has_code_start_ref(lookup, range)) {
    if (out_materialized != NULL) *out_materialized = 1U;
    if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_MATERIALIZED_DISCOVERED_COPY_ENTRY;
    return 0;
  }
  if (runtime_range_has_start_entry_and_internal_code_ref(lookup, range)) {
    if (out_materialized != NULL) *out_materialized = 1U;
    if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_MATERIALIZED_DISCOVERED_COPY_ENTRY;
    return 0;
  }
  if (runtime_range_has_start_entry_without_start_control(lookup, range) &&
      runtime_range_contains_nested_runtime_range(lookup, range)) {
    if (out_materialized != NULL) *out_materialized = 1U;
    if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_MATERIALIZED_DISCOVERED_COPY_ENTRY;
    return 0;
  }
  if (runtime_range_contains_nested_runtime_range(lookup, range)) {
    if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_SUPPRESSED_CONTAINS_NESTED_RUNTIME_RANGE;
    return 0;
  }
  if (runtime_range_has_internal_control_entry_without_start_control(lookup, range)) {
    if (out_materialized != NULL) *out_materialized = 1U;
    if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_MATERIALIZED_DISCOVERED_COPY_ENTRY;
    return 0;
  }
  if (runtime_range_is_crossed_by_storage_xref(lookup, range)) {
    if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_SUPPRESSED_CROSSED_BY_STORAGE_XREF;
    return 0;
  }
  if (runtime_range_has_storage_continuation(lookup, range)) {
    if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_SUPPRESSED_STORAGE_CONTINUATION;
    return 0;
  }
  if (runtime_range_is_overlaid_by_runtime_copy(lookup, range, &related)) {
    if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_SUPPRESSED_OVERLAID_BY_RUNTIME_COPY;
    runtime_view_relationship_set_range(lookup, related,
      M68K_RUNTIME_VIEW_RELATIONSHIP_OVERLAID_BY_RUNTIME_COPY, out_relationship);
    return 0;
  }
  if (runtime_range_is_full_source_policy_load_view(lookup, range)) {
    if (out_materialized != NULL) *out_materialized = 1U;
    if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_MATERIALIZED_FULL_SOURCE_POLICY_LOAD_VIEW;
    return 0;
  }
  if (runtime_range_contains_policy_entry_point(lookup, range)) {
    if (out_materialized != NULL) *out_materialized = 1U;
    if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_MATERIALIZED_POLICY_ENTRY_POINT;
    return 0;
  }
  for (index = 0U; index < lookup->runtime_address_ref_count; ++index) {
    if (runtime_range_contains_runtime_ref_target(range, lookup->runtime_address_refs[index].fact)) {
      if (out_materialized != NULL) *out_materialized = 1U;
      if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_MATERIALIZED_RUNTIME_REF_TARGET;
      return 0;
    }
  }
  if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_SUPPRESSED_NO_MATERIALIZING_EVIDENCE;
  return 0;
}

int lookup_runtime_range_materialization(const M68kRenderLookup *lookup, const M68kFact *range,
    uint8_t *out_materialized, uint8_t *out_reason, M68kRuntimeViewRelationshipIR *out_relationship) {
  M68kRenderRuntimeAddressRange *slot = lookup_runtime_range_slot_for_fact(lookup, range);
  if (out_materialized != NULL) *out_materialized = 0U;
  if (out_reason != NULL) *out_reason = M68K_RUNTIME_VIEW_MATERIALIZATION_REASON_NONE;
  runtime_view_relationship_clear(out_relationship);
  if (slot != NULL && lookup != NULL && lookup->build_complete && slot->materialization_cached) {
    if (out_materialized != NULL) *out_materialized = slot->materialized;
    if (out_reason != NULL) *out_reason = slot->materialization_reason;
    if (out_relationship != NULL) *out_relationship = slot->relationship;
    return 0;
  }
  {
    uint8_t materialized = 0U;
    uint8_t reason = M68K_RUNTIME_VIEW_MATERIALIZATION_REASON_NONE;
    M68kRuntimeViewRelationshipIR relationship;
    int result;
    runtime_view_relationship_clear(&relationship);
    result = lookup_runtime_range_materialization_uncached(lookup, range, &materialized, &reason, &relationship);
    if (result != 0) return result;
    if (slot != NULL && lookup != NULL && lookup->build_complete) {
      slot->materialization_cached = 1U;
      slot->materialized = materialized;
      slot->materialization_reason = reason;
      slot->relationship = relationship;
    }
    if (out_materialized != NULL) *out_materialized = materialized;
    if (out_reason != NULL) *out_reason = reason;
    if (out_relationship != NULL) *out_relationship = relationship;
  }
  return 0;
}

static int runtime_range_is_materialized(const M68kRenderLookup *lookup, const M68kFact *range) {
  uint8_t materialized = 0U;
  (void)lookup_runtime_range_materialization(lookup, range, &materialized, NULL, NULL);
  return materialized != 0U;
}

static int lookup_source_runtime_continuation_address(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset, uint32_t *out_runtime_address) {
  size_t index;
  uint32_t best_end = 0U;
  uint32_t best_runtime_address = 0U;
  int found = 0;
  if (lookup == NULL || lookup->runtime_address_ranges == NULL) return 0;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_ranges[index].fact;
    uint32_t end;
    uint32_t delta;
    uint32_t runtime_address;
    if (fact == NULL || fact->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
        fact->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY ||
        fact->section_index != section_index || fact->offset != 0U || fact->size == 0U ||
        !fact->has_runtime_address || !runtime_range_is_materialized(lookup, fact)) {
      continue;
    }
    if (fact->size > UINT32_MAX - fact->offset) continue;
    end = fact->offset + fact->size;
    if (source_offset < end || end < best_end) continue;
    delta = source_offset - fact->offset;
    if (delta > UINT32_MAX - fact->runtime_address) continue;
    runtime_address = fact->runtime_address + delta;
    best_end = end;
    best_runtime_address = runtime_address;
    found = 1;
  }
  if (!found) return 0;
  if (out_runtime_address != NULL) *out_runtime_address = best_runtime_address;
  return 1;
}

int lookup_source_runtime_address(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset, uint32_t *out_runtime_address) {
  size_t index;
  if (out_runtime_address != NULL) *out_runtime_address = 0U;
  if (lookup == NULL || lookup->runtime_address_ranges == NULL) return 0;
  for (index = lookup->runtime_address_ref_count; index > 0U; --index) {
    const M68kFact *ref = lookup->runtime_address_refs[index - 1U].fact;
    size_t range_index;
    if (ref == NULL || ref->target_section_index != section_index || ref->target_offset != source_offset ||
        !ref->has_runtime_address) {
      continue;
    }
    for (range_index = lookup->runtime_address_range_count; range_index > 0U; --range_index) {
      const M68kFact *range = lookup->runtime_address_ranges[range_index - 1U].fact;
      uint32_t mapped_runtime_address = 0U;
      if (!runtime_range_is_materialized(lookup, range)) continue;
      if (!runtime_range_contains_source(range, section_index, source_offset, &mapped_runtime_address)) continue;
      if (mapped_runtime_address == ref->runtime_address) {
        if (out_runtime_address != NULL) *out_runtime_address = ref->runtime_address;
        return 1;
      }
    }
  }
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_ranges[index].fact;
    if (!runtime_range_is_materialized(lookup, fact)) continue;
    if (runtime_range_contains_source(fact, section_index, source_offset, out_runtime_address)) return 1;
  }
  if (lookup_source_runtime_continuation_address(lookup, section_index, source_offset, out_runtime_address)) {
    return 1;
  }
  return 0;
}

int lookup_source_has_materialized_runtime_address(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset, uint32_t runtime_address) {
  size_t index;
  if (lookup == NULL || lookup->runtime_address_ranges == NULL) return 0;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_ranges[index].fact;
    uint32_t mapped_runtime_address = 0U;
    if (!runtime_range_is_materialized(lookup, fact)) continue;
    if (!runtime_range_contains_source(fact, section_index, source_offset, &mapped_runtime_address)) continue;
    if (mapped_runtime_address == runtime_address) return 1;
  }
  return 0;
}

static int runtime_address_ref_targets_policy_materialized_source(const M68kRenderLookup *lookup,
    const M68kFact *ref) {
  size_t index;
  if (lookup == NULL || ref == NULL || ref->kind != M68K_FACT_RUNTIME_ADDRESS_REF ||
      !ref->has_runtime_address || lookup->runtime_address_ranges == NULL) {
    return 0;
  }
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *range = lookup->runtime_address_ranges[index].fact;
    uint32_t mapped_runtime_address = 0U;
    if (range == NULL || range->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_POLICY ||
        !runtime_range_is_materialized(lookup, range)) {
      continue;
    }
    if (!runtime_range_contains_source(range, ref->target_section_index, ref->target_offset,
        &mapped_runtime_address)) {
      continue;
    }
    if (mapped_runtime_address == ref->runtime_address) return 1;
  }
  return 0;
}

int lookup_source_should_render_runtime_label(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset, uint32_t *out_runtime_address) {
  return lookup_source_runtime_address(lookup, section_index, source_offset, out_runtime_address);
}

static int lookup_source_offsets_share_runtime_view(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset, uint32_t target_offset) {
  size_t index;
  int source_has_runtime_view = 0;
  int target_has_runtime_view = 0;
  if (lookup == NULL || lookup->runtime_address_ranges == NULL || lookup->runtime_address_range_count == 0U) return 1;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_ranges[index].fact;
    uint32_t source_delta, target_delta;
    if (!runtime_range_is_materialized(lookup, fact) ||
        fact->section_index != section_index || source_offset < fact->offset || target_offset < fact->offset) {
      continue;
    }
    source_delta = source_offset - fact->offset;
    target_delta = target_offset - fact->offset;
    if (source_delta < fact->size) source_has_runtime_view = 1;
    if (target_delta < fact->size) target_has_runtime_view = 1;
    if (source_delta < fact->size && target_delta < fact->size) return 1;
  }
  return source_has_runtime_view == 0 && target_has_runtime_view == 0;
}

int lookup_source_offset_is_materialized_runtime_range_start(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset) {
  size_t index;
  if (lookup == NULL || lookup->runtime_address_ranges == NULL) return 0;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_ranges[index].fact;
    if (runtime_range_is_materialized(lookup, fact) && fact->section_index == section_index &&
        fact->offset == source_offset) {
      return 1;
    }
  }
  return 0;
}

static int lookup_source_offset_is_block_start(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->block_starts == NULL ||
      lookup->block_start_extents == NULL || lookup->block_starts[section_index] == NULL ||
      source_offset >= lookup->block_start_extents[section_index]) {
    return 0;
  }
  return lookup->block_starts[section_index][source_offset] != 0U;
}

static int runtime_address_ref_targets_unmaterialized_discovered_code(const M68kRenderLookup *lookup,
    const M68kFact *ref) {
  size_t index;
  if (lookup == NULL || ref == NULL || ref->kind != M68K_FACT_RUNTIME_ADDRESS_REF ||
      !ref->has_runtime_address || ref->target_section_index >= lookup->section_count) {
    return 0;
  }
  if (!lookup_source_offset_is_block_start(lookup, ref->target_section_index, ref->target_offset)) return 0;
  if (lookup_source_has_materialized_runtime_address(lookup, ref->target_section_index, ref->target_offset,
      ref->runtime_address)) {
    return 0;
  }
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *range = lookup->runtime_address_ranges[index].fact;
    uint32_t mapped_runtime_address = 0U;
    if (range == NULL || range->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY) continue;
    if (!runtime_range_contains_source(range, ref->target_section_index, ref->target_offset,
        &mapped_runtime_address)) {
      continue;
    }
    if (mapped_runtime_address == ref->runtime_address) return 1;
  }
  return 0;
}

static int runtime_address_ref_targets_discovered_copy_range_start(const M68kRenderLookup *lookup,
    const M68kFact *ref) {
  size_t index;
  if (lookup == NULL || ref == NULL || ref->kind != M68K_FACT_RUNTIME_ADDRESS_REF ||
      !ref->has_runtime_address || ref->target_section_index >= lookup->section_count ||
      lookup_source_has_materialized_runtime_address(lookup, ref->target_section_index, ref->target_offset,
        ref->runtime_address)) {
    return 0;
  }
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *range = lookup->runtime_address_ranges[index].fact;
    if (range == NULL || range->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
        range->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY ||
        range->section_index != ref->target_section_index || range->offset != ref->target_offset ||
        !range->has_runtime_address || range->runtime_address != ref->runtime_address) {
      continue;
    }
    return 1;
  }
  return 0;
}

static int runtime_address_ref_operand_can_render_materialized_label(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, const M68kFact *fact) {
  const M68kDecodeSectionIR *section;
  const M68kDecodeCandidate *candidate;
  M68kInstructionIR instruction;
  const M68kOperandIR *operand;
  const M68kAnalysisManualRepresentation *representation;
  uint32_t value = 0U;
  if (lookup == NULL || decode == NULL || fact == NULL || !fact->has_runtime_address ||
      fact->has_sink_address || fact->reason >= M68K_DECODE_IR_MAX_OPERANDS ||
      fact->section_index >= decode->section_count || fact->target_section_index >= lookup->section_count ||
      !lookup_has_renderable_label(lookup, fact->target_section_index, fact->target_offset) ||
      (!lookup_source_has_materialized_runtime_address(lookup, fact->target_section_index,
         fact->target_offset, fact->runtime_address) && fact->runtime_address != fact->target_offset)) {
    return 0;
  }
  section = &decode->sections[fact->section_index];
  candidate = m68k_decode_ir_find_candidate_at_offset(section, fact->offset);
  if (candidate == NULL || fact->reason >= candidate->operand_count ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
      fact->reason >= instruction.operand_count) {
    return 0;
  }
  operand = &instruction.operands[fact->reason];
  if (!m68k_ir_operand_immediate_value(operand, &value) && !operand_absolute_offset_local(operand, &value))
    return 0;
  if (value != fact->runtime_address) return 0;
  representation = lookup_manual_operand_representation(lookup, fact->section_index,
    fact->offset, fact->reason);
  if (representation != NULL && representation->style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL &&
      representation->target_equate_index != 0U) return 0;
  return !amiga_abs_exec_base_load_should_stay_absolute(lookup, &instruction, fact->reason, operand, fact);
}

int lookup_source_logical_address(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset, uint32_t *out_logical_address) {
  uint32_t runtime_address = 0U;
  if (out_logical_address == NULL) return 0;
  if (lookup_source_should_render_runtime_label(lookup, section_index, source_offset, &runtime_address)) {
    *out_logical_address = runtime_address;
    return 1;
  }
  *out_logical_address = source_offset;
  return 1;
}

static const M68kFact *lookup_runtime_address_ref_for_operand(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset, size_t operand_index) {
  size_t index;
  if (lookup == NULL || operand_index > UINT32_MAX) return NULL;
  if (operand_index < M68K_DECODE_IR_MAX_OPERANDS && section_index < lookup->section_count &&
      lookup->runtime_address_ref_indices != NULL && lookup->runtime_address_ref_index_extents != NULL &&
      offset < lookup->runtime_address_ref_index_extents[section_index] &&
      lookup->runtime_address_ref_indices[section_index] != NULL) {
    return lookup->runtime_address_ref_indices[section_index][offset].operand_refs[operand_index];
  }
  for (index = lookup->runtime_address_ref_count; index > 0U; --index) {
    const M68kFact *fact = lookup->runtime_address_refs[index - 1U].fact;
    if (fact == NULL) continue;
    if (fact->section_index == section_index && fact->offset == offset &&
        fact->reason == (uint32_t)operand_index && fact->has_runtime_address) {
      return fact;
    }
  }
  return NULL;
}

static int runtime_address_maps_to_materialized_source(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t runtime_address) {
  size_t index;
  if (lookup == NULL) return 0;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *range = lookup->runtime_address_ranges[index].fact;
    uint32_t delta;
    if (!runtime_range_is_materialized(lookup, range) || range->section_index != section_index ||
        !range->has_runtime_address || runtime_address < range->runtime_address) {
      continue;
    }
    delta = runtime_address - range->runtime_address;
    if (delta >= range->size || range->offset > UINT32_MAX - delta) continue;
    return 1;
  }
  return 0;
}

static int lookup_materialized_runtime_address_source_offset(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t runtime_address, uint32_t *out_source_offset) {
  size_t index;
  if (out_source_offset != NULL) *out_source_offset = 0U;
  if (lookup == NULL || out_source_offset == NULL || section_index >= lookup->section_count) return 0;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *range = lookup->runtime_address_ranges[index].fact;
    uint32_t delta;
    uint32_t source_offset;
    if (!runtime_range_is_materialized(lookup, range) || range->section_index != section_index ||
        !range->has_runtime_address || runtime_address < range->runtime_address) {
      continue;
    }
    delta = runtime_address - range->runtime_address;
    if (delta >= range->size || range->offset > UINT32_MAX - delta) continue;
    source_offset = range->offset + delta;
    if (lookup->label_extents == NULL || source_offset >= lookup->label_extents[section_index]) continue;
    *out_source_offset = source_offset;
    return 1;
  }
  return 0;
}

static const M68kSectionAnalysisIR *source_analysis_section_for_render(const M68kSourceAnalysisIR *source_analysis,
    size_t section_index) {
  size_t index;
  if (source_analysis == NULL || section_index > UINT32_MAX) return NULL;
  for (index = 0U; index < source_analysis->section_count; ++index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[index];
    if (section->section_index == (uint32_t)section_index) return section;
  }
  return NULL;
}

static void format_platform_semantic_target_label_for_render(const M68kRenderLookup *lookup, char *buf,
    size_t buf_size, size_t section_index, uint32_t offset) {
  uint32_t runtime_address = 0U;
  if (buf == NULL || buf_size == 0U) return;
  if (lookup_source_should_render_runtime_label(lookup, section_index, offset, &runtime_address)) {
    snprintf(buf, buf_size, "loc_%u_%08X", (unsigned)section_index, (unsigned)runtime_address);
    return;
  }
  (void)format_lookup_asm_label_with_generation(lookup, buf, buf_size, section_index, offset);
}

static int append_audio_period_source_comment_for_render(const M68kPlatformSemanticUseIR *use,
    const M68kRenderLookup *lookup, char *comment, size_t comment_size) {
  char label[64];
  char note[128];
  if (use == NULL || lookup == NULL || comment == NULL || comment_size == 0U || !use->has_target) return 0;
  format_platform_semantic_target_label_for_render(lookup, label, sizeof(label), use->target_section_index,
    use->target_offset);
  snprintf(note, sizeof(note), "period from %s%s", label,
    use->note_text != NULL && strcmp(use->note_text, "transformed") == 0 ? " transformed" : "");
  (void)append_comment_part_local(comment, comment_size, note);
  return 1;
}

static int append_audio_pointer_source_comment_for_render(const M68kPlatformSemanticUseIR *use,
    const M68kRenderLookup *lookup, char *comment, size_t comment_size) {
  char label[64];
  char dynamic_label[64];
  char note[192];
  if (use == NULL || lookup == NULL || comment == NULL || comment_size == 0U || !use->has_target) return 0;
  (void)format_lookup_asm_label_with_generation(lookup, label, sizeof(label), use->target_section_index,
    use->target_offset);
  if (use->has_secondary_target) {
    format_platform_semantic_target_label_for_render(lookup, dynamic_label, sizeof(dynamic_label),
      use->secondary_target_section_index, use->secondary_target_offset);
    snprintf(note, sizeof(note), "source %s + dynamic offset from %s", label, dynamic_label);
  } else {
    snprintf(note, sizeof(note), "source %s%s", label,
      use->note_text != NULL && strcmp(use->note_text, "dynamic_offset") == 0 ? " + dynamic offset" : "");
  }
  (void)append_comment_part_local(comment, comment_size, note);
  return 1;
}

static int attach_platform_semantic_note_comment_for_render(const M68kSourceAnalysisIR *source_analysis,
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset, char *comment, size_t comment_size) {
  const M68kSectionAnalysisIR *section;
  size_t index;
  int appended_target_note = 0;
  if (comment == NULL || comment_size == 0U) return 0;
  section = source_analysis_section_for_render(source_analysis, section_index);
  if (section == NULL) return 0;
  for (index = 0U; index < section->platform_semantic_use_count; ++index) {
    const M68kPlatformSemanticUseIR *use = &section->platform_semantic_uses[index];
    if (use->offset != offset) continue;
    if (use->kind == M68K_PLATFORM_SEMANTIC_USE_COPPER_DISPLAY_LAYOUT) continue;
    if (use->kind == M68K_PLATFORM_SEMANTIC_USE_DISPLAY_SETUP) continue;
    if (use->kind == M68K_PLATFORM_SEMANTIC_USE_AUDIO_PERIOD_SOURCE) {
      if (append_audio_period_source_comment_for_render(use, lookup, comment, comment_size)) appended_target_note = 1;
      continue;
    }
    if (use->kind == M68K_PLATFORM_SEMANTIC_USE_AUDIO_POINTER_SOURCE) {
      if (append_audio_pointer_source_comment_for_render(use, lookup, comment, comment_size)) appended_target_note = 1;
      continue;
    }
    if (use->note_text == NULL || use->note_text[0] == '\0') continue;
    (void)append_comment_part_local(comment, comment_size, use->note_text);
  }
  return appended_target_note || comment[0] != '\0';
}

static int attach_platform_semantic_operand_expr_for_render(M68kRenderIRPreview *preview,
    const M68kSourceAnalysisIR *source_analysis, size_t section_index, uint32_t offset,
    M68kInstructionIR *instruction) {
  const M68kSectionAnalysisIR *section;
  size_t index;
  if (preview == NULL || instruction == NULL) return 0;
  section = source_analysis_section_for_render(source_analysis, section_index);
  if (section == NULL) return 0;
  for (index = 0U; index < section->platform_semantic_use_count; ++index) {
    const M68kPlatformSemanticUseIR *use = &section->platform_semantic_uses[index];
    if (use->offset != offset || !use->has_operand_expr || use->operand_expr == NULL ||
        use->operand_expr[0] == '\0' || use->operand_index >= instruction->operand_count) {
      continue;
    }
    if (instruction->operands[use->operand_index].symbol_ref.has_name != 0U) continue;
    if (use->has_runtime_address) {
      if (!declare_layout_runtime_symbol(preview, use->operand_expr, use->runtime_address)) {
        ++preview->asm_source_instruction_render_failures;
        record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, (uint32_t)section_index, offset, 0U);
        return -1;
      }
    } else if (!render_asm_include_for_symbol_expr(preview, use->operand_expr)) {
      ++preview->asm_source_instruction_render_failures;
      record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, (uint32_t)section_index, offset, 0U);
      return -1;
    }
    attach_amiga_platform_symbol(&instruction->operands[use->operand_index], use->operand_expr);
    return 1;
  }
  return 0;
}

static int attach_platform_semantic_target_operand_for_render(const M68kRenderLookup *lookup,
    const M68kSourceAnalysisIR *source_analysis, size_t section_index, uint32_t offset,
    M68kInstructionIR *instruction) {
  const M68kSectionAnalysisIR *section;
  size_t index;
  if (lookup == NULL || instruction == NULL) return 0;
  section = source_analysis_section_for_render(source_analysis, section_index);
  if (section == NULL) return 0;
  for (index = 0U; index < section->platform_semantic_use_count; ++index) {
    const M68kPlatformSemanticUseIR *use = &section->platform_semantic_uses[index];
    M68kOperandIR *operand;
    uint32_t value = 0U;
    if (use->offset != offset ||
        use->kind != M68K_PLATFORM_SEMANTIC_USE_RUNTIME_SINK_POINTER ||
        !use->has_target ||
        use->target_section_index >= lookup->section_count ||
        use->operand_index >= instruction->operand_count ||
        !lookup_has_renderable_label(lookup, use->target_section_index, use->target_offset)) {
      continue;
    }
    operand = &instruction->operands[use->operand_index];
    if (operand->symbol_ref.has_name != 0U || !m68k_ir_operand_immediate_value(operand, &value)) continue;
    m68k_ir_symbol_ref_init(&operand->symbol_ref);
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_ABS;
    operand->symbol_ref.has_name = 1U;
    operand->symbol_ref.has_section = 1;
    operand->symbol_ref.section_index = use->target_section_index;
    operand->symbol_ref.has_section_offset = 1;
    operand->symbol_ref.section_offset = use->target_offset;
    operand->symbol_ref.name_is_generated = format_rendered_asm_label_with_generation(lookup,
      operand->symbol_ref.name, sizeof(operand->symbol_ref.name), use->target_section_index, use->target_offset);
    return 1;
  }
  return 0;
}

static int attach_platform_semantic_kind_note_comment_for_render(const M68kSourceAnalysisIR *source_analysis,
    size_t section_index, uint32_t offset, uint8_t kind, char *comment, size_t comment_size) {
  const M68kSectionAnalysisIR *section;
  size_t index;
  if (comment == NULL || comment_size == 0U) return 0;
  comment[0] = '\0';
  section = source_analysis_section_for_render(source_analysis, section_index);
  if (section == NULL) return 0;
  for (index = 0U; index < section->platform_semantic_use_count; ++index) {
    const M68kPlatformSemanticUseIR *use = &section->platform_semantic_uses[index];
    if (use->kind != kind || use->offset != offset || use->note_text == NULL || use->note_text[0] == '\0') continue;
    (void)append_comment_part_local(comment, comment_size, use->note_text);
  }
  return comment[0] != '\0';
}

static void render_platform_semantic_header_comments_for_raw_data(M68kRenderIRPreview *preview,
    const M68kSourceAnalysisIR *source_analysis, size_t section_index, uint32_t offset) {
  char semantic_comment[160];
  semantic_comment[0] = '\0';
  if (attach_platform_semantic_kind_note_comment_for_render(source_analysis, section_index, offset,
      M68K_PLATFORM_SEMANTIC_USE_COPPER_DISPLAY_LAYOUT, semantic_comment, sizeof(semantic_comment))) {
    render_asm_comment_line(preview, semantic_comment);
  }
  if (attach_platform_semantic_kind_note_comment_for_render(source_analysis, section_index, offset,
      M68K_PLATFORM_SEMANTIC_USE_DISPLAY_SETUP, semantic_comment, sizeof(semantic_comment))) {
    render_asm_comment_line(preview, semantic_comment);
  }
}

static const char *external_runtime_address_ref_role(const M68kRenderLookup *lookup, const M68kFact *fact) {
  const M68kSection *section;
  const char *role;
  uint16_t custom_base_id = PLATFORM_FACTS_V2_HARDWARE_BASE_ID_NONE;
  if (lookup == NULL || fact == NULL || lookup->object == NULL) return NULL;
  if (fact->target_section_index == (size_t)-1 && fact->target_offset != 0U) {
    role = platform_facts_v2_runtime_address_sink_data_class(lookup->object->platform_backend_kind,
      fact->target_offset);
    if ((role == NULL || role[0] == '\0') &&
        platform_facts_v2_custom_hardware_base_id(lookup->object->platform_backend_kind, &custom_base_id)) {
      role = platform_facts_v2_hardware_base_offset_runtime_address_sink_data_class(
        lookup->object->platform_backend_kind, custom_base_id, fact->target_offset);
    }
    if (role != NULL && role[0] != '\0') return role;
  }
  if (fact->source_section_index >= lookup->object->section_count) return NULL;
  section = &lookup->object->sections[fact->source_section_index];
  role = platform_facts_v2_runtime_address_storage_sink_data_class(lookup->object->platform_backend_kind,
    section->data, section->data_size, fact->source_offset);
  return role != NULL && role[0] != '\0' ? role : NULL;
}

static const char *runtime_address_ref_sink_role(const M68kRenderLookup *lookup, const M68kFact *fact) {
  const char *role;
  if (lookup == NULL || lookup->object == NULL || fact == NULL || !fact->has_sink_address) return NULL;
  role = platform_facts_v2_runtime_address_sink_data_class(lookup->object->platform_backend_kind,
    fact->sink_address);
  return role != NULL && role[0] != '\0' ? role : NULL;
}

static const char *lookup_external_runtime_address_role_by_value(const M68kRenderLookup *lookup,
    uint32_t runtime_address) {
  size_t index;
  if (lookup == NULL || lookup->object == NULL || runtime_address == 0U) return NULL;
  for (index = 0U; index < lookup->runtime_address_ref_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_refs[index].fact;
    const char *role;
    if (fact == NULL || fact->target_section_index < lookup->section_count ||
        !fact->has_runtime_address || fact->runtime_address != runtime_address) {
      continue;
    }
    role = external_runtime_address_ref_role(lookup, fact);
    if (role != NULL && role[0] != '\0') return role;
  }
  return NULL;
}

static const char *lookup_sink_runtime_address_role_by_value(const M68kRenderLookup *lookup,
    uint32_t runtime_address) {
  size_t index;
  if (lookup == NULL || runtime_address == 0U) return NULL;
  for (index = 0U; index < lookup->runtime_address_ref_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_refs[index].fact;
    const char *role;
    if (fact == NULL || !fact->has_runtime_address || fact->runtime_address != runtime_address) continue;
    role = runtime_address_ref_sink_role(lookup, fact);
    if (role != NULL && role[0] != '\0') return role;
  }
  return NULL;
}

static const char *lookup_inferred_runtime_address_value_data_class(const M68kRenderLookup *lookup,
    uint32_t runtime_address) {
  size_t index;
  if (lookup == NULL || runtime_address == 0U) return NULL;
  for (index = 0U; index < lookup->inferred_runtime_address_ref_count; ++index) {
    const M68kRenderInferredRuntimeAddressRef *entry = &lookup->inferred_runtime_address_refs[index];
    if (entry->ref.has_runtime_address && entry->ref.runtime_address == runtime_address &&
        entry->data_class_flags != 0U) {
      const char *role = m68k_analysis_structured_data_role_name_for_flags(entry->data_class_flags);
      if (role != NULL && role[0] != '\0') return role;
    }
  }
  return NULL;
}

static const char *lookup_runtime_address_value_semantic_role(const M68kRenderLookup *lookup,
    uint32_t runtime_address) {
  const char *role = lookup_sink_runtime_address_role_by_value(lookup, runtime_address);
  if (role != NULL && role[0] != '\0') return role;
  role = lookup_external_runtime_address_role_by_value(lookup, runtime_address);
  if (role != NULL && role[0] != '\0') return role;
  role = lookup_inferred_runtime_address_value_data_class(lookup, runtime_address);
  return role != NULL && role[0] != '\0' ? role : NULL;
}

int lookup_offset_is_inside_relocation_payload(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  uint32_t back;
  if (lookup == NULL || offset == 0U) return 0;
  for (back = 1U; back <= 4U && back <= offset; ++back) {
    uint32_t start = offset - back;
    const M68kFact *relocation = lookup_relocation_at(lookup, section_index, start);
    const M68kFact *anchor = lookup_anchor_at(lookup, section_index, start);
    if (relocation != NULL && relocation->size > back) return 1;
    if (anchor != NULL && anchor->size > back) return 1;
  }
  return 0;
}

int lookup_label_has_explicit_name(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  char name[128];
  if (lookup == NULL) return 0;
  return format_lookup_asm_label_with_generation(lookup, name, sizeof(name), section_index, offset) == 0U;
}

static int lookup_label_has_inbound_target_ref(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->label_target_refs == NULL ||
      lookup->label_target_ref_extents == NULL || offset > lookup->label_target_ref_extents[section_index] ||
      lookup->label_target_refs[section_index] == NULL) {
    return 0;
  }
  return lookup->label_target_refs[section_index][offset] != 0U;
}

int lookup_label_has_statement_ref(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->label_statement_refs == NULL ||
      lookup->label_statement_ref_extents == NULL || offset > lookup->label_statement_ref_extents[section_index] ||
      lookup->label_statement_refs[section_index] == NULL) {
    return 0;
  }
  return lookup->label_statement_refs[section_index][offset] != 0U;
}

static int lookup_storage_label_has_inbound_target_ref(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->storage_label_target_refs == NULL ||
      lookup->storage_label_target_ref_extents == NULL ||
      offset > lookup->storage_label_target_ref_extents[section_index] ||
      lookup->storage_label_target_refs[section_index] == NULL) {
    return 0;
  }
  return lookup->storage_label_target_refs[section_index][offset] != 0U;
}

int lookup_has_renderable_label(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  M68kRenderRangeOwnershipView ownership_at_offset;
  M68kRenderRangeOwnershipView covering_ownership;
  const M68kAnalysisStructuredDataItem *covering_item = NULL;
  if (!lookup_has_label(lookup, section_index, offset)) return 0;
  if (lookup_range_ownership_at_offset(lookup, section_index, offset, &ownership_at_offset) &&
      !lookup_label_has_explicit_name(lookup, section_index, offset) &&
      !lookup_label_has_inbound_target_ref(lookup, section_index, offset) &&
      !lookup_label_has_statement_ref(lookup, section_index, offset)) {
    return 0;
  }
  if (lookup_range_ownership_covering_offset(lookup, section_index, offset, &covering_ownership)) {
    covering_item = covering_ownership.structured_item;
  }
  if (covering_item != NULL && covering_ownership.start_offset != offset &&
      !lookup_range_ownership_at_offset(lookup, section_index, offset, &ownership_at_offset) &&
      lookup_relocation_at(lookup, section_index, offset) == NULL &&
      lookup_anchor_at(lookup, section_index, offset) == NULL &&
      lookup_string_span_at_offset(lookup, section_index, offset) == NULL) {
    if (lookup_label_has_inbound_target_ref(lookup, section_index, offset) ||
        lookup_label_has_statement_ref(lookup, section_index, offset)) {
      return !lookup_offset_is_inside_relocation_payload(lookup, section_index, offset);
    }
    /* Authored source declarations inside a literal leaf remain boundaries.
     * Automatically expanded field names still follow their existing policy. */
    if (lookup->policy != NULL && covering_item->size > 4U &&
        (covering_item->kind == M68K_ANALYSIS_STRUCTURED_DATA_BYTES ||
         covering_item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS ||
         covering_item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS)) {
      uint16_t index;
      for (index = 0U; index < lookup->policy->named_label_count && index < M68K_ANALYSIS_NAMED_LABEL_LIMIT; ++index) {
        const M68kAnalysisNamedLabel *label = &lookup->policy->named_labels[index];
        if (label->is_source_declaration && label->domain == M68K_ANALYSIS_LABEL_DOMAIN_SOURCE &&
            label->offset == offset &&
            (label->has_section_index ? label->section_index == section_index : section_index == 0U))
          return !lookup_offset_is_inside_relocation_payload(lookup, section_index, offset);
      }
    }
    if ((structured_data_item_is_copper_list(covering_item) || structured_data_item_is_palette(covering_item)) &&
        offset > covering_item->offset && offset - covering_item->offset < covering_item->size &&
        ((offset - covering_item->offset) % 2U) == 0U) {
      return !lookup_offset_is_inside_relocation_payload(lookup, section_index, offset);
    }
    return 0;
  }
  return !lookup_offset_is_inside_relocation_payload(lookup, section_index, offset);
}

static int lookup_has_structured_data_start_boundary(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint16_t boundary_flags) {
  M68kRenderRangeOwnershipView range;
  return (boundary_flags & M68K_RENDER_BOUNDARY_STRUCTURED_DATA) != 0U &&
    lookup_range_ownership_at_offset(lookup, section_index, offset, &range);
}

static int lookup_has_string_span_start_boundary(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint16_t boundary_flags) {
  return (boundary_flags & M68K_RENDER_BOUNDARY_STRING_SPAN) != 0U &&
    lookup_string_span_at_offset(lookup, section_index, offset) != NULL;
}

static int lookup_has_instruction_comment_boundary(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint16_t boundary_flags) {
  return (boundary_flags & M68K_RENDER_BOUNDARY_COMMENT) != 0U &&
    lookup_instruction_comment(lookup, section_index, offset) != NULL;
}

static int lookup_has_render_walk_data_split_boundary(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, int include_label, int include_structured_data, int include_string_span,
    int include_comment) {
  uint16_t boundary_flags = render_lookup_boundary_flags(lookup, section_index, offset);
  if ((boundary_flags & (M68K_RENDER_BOUNDARY_RELOCATION | M68K_RENDER_BOUNDARY_ANCHOR)) != 0U)
    return 1;
  if (include_label && (boundary_flags & M68K_RENDER_BOUNDARY_LABEL) != 0U &&
      lookup_has_renderable_label(lookup, section_index, offset))
    return 1;
  if (include_structured_data &&
      lookup_has_structured_data_start_boundary(lookup, section_index, offset, boundary_flags))
    return 1;
  if (include_string_span && lookup_has_string_span_start_boundary(lookup, section_index, offset, boundary_flags))
    return 1;
  if (include_comment && lookup_has_instruction_comment_boundary(lookup, section_index, offset, boundary_flags))
    return 1;
  return 0;
}

static int lookup_structured_item_probe_has_blocking_boundary(const M68kRenderLookup *lookup,
    const M68kAnalysisStructuredDataItem *structured_item, size_t section_index, uint32_t probe, int include_labels) {
  uint16_t boundary_flags = render_lookup_boundary_flags(lookup, section_index, probe);
  if ((boundary_flags & (M68K_RENDER_BOUNDARY_RELOCATION | M68K_RENDER_BOUNDARY_ANCHOR |
        (structured_data_item_is_multiline_text(structured_item) ? 0U : M68K_RENDER_BOUNDARY_STRING_SPAN))) != 0U)
    return 1;
  if (lookup_has_structured_data_start_boundary(lookup, section_index, probe, boundary_flags))
    return 1;
  if (include_labels && (boundary_flags & M68K_RENDER_BOUNDARY_LABEL) != 0U &&
      lookup_has_renderable_label(lookup, section_index, probe)) {
    int internal_copper_label =
      structured_data_item_is_copper_list(structured_item) &&
      ((probe - structured_item->offset) % 2U) == 0U;
    int internal_palette_label =
      structured_data_item_is_palette(structured_item) &&
      ((probe - structured_item->offset) % 2U) == 0U;
    return !internal_copper_label && !internal_palette_label;
  }
  return 0;
}

const char *lookup_global_base_slot_library(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->global_base_slot_count; ++index) {
    const M68kRenderGlobalBaseSlot *slot = &lookup->global_base_slots[index];
    if (slot->section_index == section_index && slot->offset == offset &&
        slot->has_library_id != 0U && slot->conflicted == 0U) {
      return platform_facts_v2_library_name_for_id(M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->library_id);
    }
  }
  return NULL;
}

static int base_field_owner_matches(const M68kRenderBaseFieldSlot *slot, const char *owner_name) {
  if (slot == NULL || owner_name == NULL || owner_name[0] == '\0') return 0;
  if (render_base_field_slot_owner_is_app_base(slot)) {
    return platform_state_name_is_app_base(owner_name) ||
      platform_facts_v2_library_base_name_for_library_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK, owner_name) != NULL;
  }
  return slot->owner_name[0] != '\0' && strcmp(slot->owner_name, owner_name) == 0;
}

static int app_base_slot_symbol_name_from_library(const char *library_name, char *symbol_name,
    size_t symbol_name_size) {
  const char *base_name;
  if (symbol_name != NULL && symbol_name_size != 0U) symbol_name[0] = '\0';
  if (library_name == NULL || library_name[0] == '\0') return 0;
  base_name = platform_facts_v2_library_base_name_for_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK, library_name);
  if (base_name == NULL) return 0;
  return platform_amiga_format_app_base_slot_name(base_name, symbol_name, symbol_name_size);
}

static int format_generated_app_base_slot_symbol_name(int16_t displacement, char *symbol_name,
    size_t symbol_name_size) {
  int written;
  if (symbol_name == NULL || symbol_name_size == 0U) return 0;
  written = snprintf(symbol_name, symbol_name_size, "app_%04X", (unsigned)(uint16_t)displacement);
  return written > 0 && (size_t)written < symbol_name_size;
}

static int app_base_slot_symbol_name_from_slot(const M68kRenderBaseFieldSlot *slot, char *symbol_name,
    size_t symbol_name_size) {
  if (symbol_name != NULL && symbol_name_size != 0U) symbol_name[0] = '\0';
  if (slot == NULL || slot->conflicted != 0U) return 0;
  if (amiga_unknown_base_owner_name_is_internal(slot->owner_name)) return 0;
  if (slot->symbol_name[0] != '\0') {
    if (symbol_name == NULL || symbol_name_size == 0U) return 0;
    snprintf(symbol_name, symbol_name_size, "%s", slot->symbol_name);
    return strlen(slot->symbol_name) < symbol_name_size;
  }
  if (slot->library_name[0] == '\0') {
    if (render_base_field_slot_owner_is_app_base(slot)) {
      return format_generated_app_base_slot_symbol_name(slot->displacement, symbol_name, symbol_name_size);
    }
    return 0;
  }
  if (slot->value_kind != M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE &&
      slot->value_kind != M68K_RENDER_BASE_FIELD_SLOT_DEVICE_BASE)
    return 0;
  return app_base_slot_symbol_name_from_library(slot->library_name, symbol_name, symbol_name_size);
}

int base_field_slot_is_base_pointer(const M68kRenderBaseFieldSlot *slot) {
  return slot != NULL && (slot->value_kind == M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE ||
    slot->value_kind == M68K_RENDER_BASE_FIELD_SLOT_DEVICE_BASE);
}

static uint16_t library_base_struct_id_for_library_id(uint16_t library_id) {
  uint16_t struct_id;
  if (library_id == 0U) return AMIGA_OS_STRUCT_ID_NONE;
  struct_id = amiga_os_find_library_base_struct_id(library_id);
  return struct_id != AMIGA_OS_STRUCT_ID_NONE ? struct_id : AMIGA_OS_STRUCT_ID_LIB;
}

static uint16_t base_field_slot_struct_id(const M68kRenderBaseFieldSlot *slot) {
  if (slot == NULL || slot->conflicted != 0U || slot->has_library_id == 0U) return AMIGA_OS_STRUCT_ID_NONE;
  if (slot->value_kind == M68K_RENDER_BASE_FIELD_SLOT_DEVICE_BASE) return AMIGA_OS_STRUCT_ID_DD;
  if (slot->value_kind == M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE)
    return library_base_struct_id_for_library_id(slot->library_id);
  return AMIGA_OS_STRUCT_ID_NONE;
}

static int kb_library_base_field_symbol_name(const char *owner_name, int16_t displacement, char *symbol_name,
    size_t symbol_name_size) {
  return platform_facts_v2_library_base_field_symbol_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK, owner_name,
    displacement, symbol_name, symbol_name_size);
}

static int library_base_has_specific_struct_name(const char *owner_name) {
  return platform_facts_v2_library_base_has_specific_struct_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK, owner_name);
}

int library_base_can_use_app_extension_slot(const char *owner_name, int16_t displacement) {
  int32_t lib_size = 0;
  char kb_symbol[64];
  if (owner_name == NULL || owner_name[0] == '\0') return 0;
  if (!render_amiga_constant_value_by_symbol_id(AMIGA_OS_SYMBOL_ID_LIB_SIZE, &lib_size) ||
      displacement < lib_size)
    return 0;
  if (library_base_has_specific_struct_name(owner_name) &&
      kb_library_base_field_symbol_name(owner_name, displacement, kb_symbol, sizeof(kb_symbol))) {
    return 0;
  }
  return 1;
}

static int lookup_app_base_field_slot_symbol_has_other_displacement(const M68kRenderLookup *lookup,
    const char *symbol_name, int16_t displacement) {
  size_t index;
  if (lookup == NULL || symbol_name == NULL || symbol_name[0] == '\0') return 0;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    char other_symbol_name[64];
    if (slot->conflicted != 0U || !render_base_field_slot_owner_is_app_base(slot)) continue;
    if (!app_base_slot_symbol_name_from_slot(slot, other_symbol_name, sizeof(other_symbol_name))) continue;
    if (strcmp(symbol_name, other_symbol_name) == 0 && slot->displacement != displacement) return 1;
  }
  return 0;
}

const char *lookup_base_field_slot_library(const M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement) {
  uint8_t has_matched_library = 0U;
  uint16_t matched_library_id = 0U;
  size_t index;
  if (lookup == NULL || owner_name == NULL || owner_name[0] == '\0') return NULL;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    char symbol_name[64];
    if (slot->displacement != displacement || slot->conflicted || !slot->has_library_id ||
        !base_field_slot_is_base_pointer(slot)) {
      continue;
    }
    if (!base_field_owner_matches(slot, owner_name)) continue;
    if (render_base_field_slot_owner_is_app_base(slot) &&
        (!app_base_slot_symbol_name_from_slot(slot, symbol_name, sizeof(symbol_name)) ||
          lookup_app_base_field_slot_symbol_has_other_displacement(lookup, symbol_name, displacement))) {
      continue;
    }
    if (has_matched_library && matched_library_id != slot->library_id) return NULL;
    has_matched_library = 1U;
    matched_library_id = slot->library_id;
  }
  return has_matched_library ? platform_facts_v2_library_name_for_id(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
    matched_library_id) : NULL;
}

const char *lookup_app_base_field_slot_library(const M68kRenderLookup *lookup, int16_t displacement) {
  uint8_t has_matched_library = 0U;
  uint16_t matched_library_id = 0U;
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    char symbol_name[64];
    if (slot->displacement != displacement || slot->conflicted || !slot->has_library_id ||
        !base_field_slot_is_base_pointer(slot)) {
      continue;
    }
    if (!render_base_field_slot_owner_is_app_base(slot)) continue;
    if (!app_base_slot_symbol_name_from_slot(slot, symbol_name, sizeof(symbol_name)) ||
        lookup_app_base_field_slot_symbol_has_other_displacement(lookup, symbol_name, displacement)) {
      continue;
    }
    if (has_matched_library && matched_library_id != slot->library_id) return NULL;
    has_matched_library = 1U;
    matched_library_id = slot->library_id;
  }
  return has_matched_library ? platform_facts_v2_library_name_for_id(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
    matched_library_id) : NULL;
}

uint16_t lookup_base_field_slot_struct_id(const M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement) {
  uint16_t matched_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  size_t index;
  if (lookup == NULL || owner_name == NULL || owner_name[0] == '\0') return AMIGA_OS_STRUCT_ID_NONE;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    uint16_t struct_id;
    char symbol_name[64];
    if (slot->displacement != displacement || slot->conflicted || !base_field_slot_is_base_pointer(slot))
      continue;
    if (!base_field_owner_matches(slot, owner_name)) continue;
    if (render_base_field_slot_owner_is_app_base(slot) &&
        (!app_base_slot_symbol_name_from_slot(slot, symbol_name, sizeof(symbol_name)) ||
          lookup_app_base_field_slot_symbol_has_other_displacement(lookup, symbol_name, displacement))) {
      continue;
    }
    struct_id = base_field_slot_struct_id(slot);
    if (struct_id == AMIGA_OS_STRUCT_ID_NONE) continue;
    if (matched_struct_id != AMIGA_OS_STRUCT_ID_NONE && matched_struct_id != struct_id) return AMIGA_OS_STRUCT_ID_NONE;
    matched_struct_id = struct_id;
  }
  return matched_struct_id;
}

uint16_t lookup_app_base_field_slot_struct_id(const M68kRenderLookup *lookup, int16_t displacement) {
  uint16_t matched_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  size_t index;
  if (lookup == NULL) return AMIGA_OS_STRUCT_ID_NONE;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    uint16_t struct_id;
    char symbol_name[64];
    if (slot->displacement != displacement || slot->conflicted || !base_field_slot_is_base_pointer(slot))
      continue;
    if (!render_base_field_slot_owner_is_app_base(slot)) continue;
    if (!app_base_slot_symbol_name_from_slot(slot, symbol_name, sizeof(symbol_name)) ||
        lookup_app_base_field_slot_symbol_has_other_displacement(lookup, symbol_name, displacement)) {
      continue;
    }
    struct_id = base_field_slot_struct_id(slot);
    if (struct_id == AMIGA_OS_STRUCT_ID_NONE) continue;
    if (matched_struct_id != AMIGA_OS_STRUCT_ID_NONE && matched_struct_id != struct_id) return AMIGA_OS_STRUCT_ID_NONE;
    matched_struct_id = struct_id;
  }
  return matched_struct_id;
}

int lookup_base_field_slot_symbol_name(const M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement, char *symbol_name, size_t symbol_name_size) {
  int matched = 0;
  int blocked = 0;
  char matched_symbol[64];
  size_t index;
  int owner_is_app_base = platform_state_name_is_app_base(owner_name);
  if (symbol_name != NULL && symbol_name_size != 0U) symbol_name[0] = '\0';
  if (lookup == NULL || owner_name == NULL || owner_name[0] == '\0' ||
      symbol_name == NULL || symbol_name_size == 0U) {
    return 0;
  }
  if (amiga_unknown_base_owner_name_is_internal(owner_name)) return 0;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    char slot_symbol[64];
    if (slot->displacement != displacement) continue;
    if (owner_is_app_base) {
      if (!render_base_field_slot_owner_is_app_base(slot)) continue;
    } else if (render_base_field_slot_owner_is_app_base(slot) ||
        strcmp(slot->owner_name, owner_name) != 0) {
      continue;
    }
    if (slot->conflicted != 0U) {
      blocked = 1;
      continue;
    }
    if (slot->library_name[0] == '\0' && slot->symbol_name[0] == '\0' &&
        !render_base_field_slot_owner_is_app_base(slot)) {
      continue;
    }
    if (render_base_field_slot_owner_is_app_base(slot) &&
        slot->value_kind == M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS &&
        lookup_typed_app_slot_region_contains_auto_offset(lookup, displacement)) {
      continue;
    }
    if (render_base_field_slot_owner_is_app_base(slot) &&
        (!app_base_slot_symbol_name_from_slot(slot, slot_symbol, sizeof(slot_symbol)) ||
          lookup_app_base_field_slot_symbol_has_other_displacement(lookup, slot_symbol, displacement))) {
      continue;
    }
    if (!app_base_slot_symbol_name_from_slot(slot, slot_symbol, sizeof(slot_symbol))) continue;
    if (matched && strcmp(matched_symbol, slot_symbol) != 0) return 0;
    snprintf(matched_symbol, sizeof(matched_symbol), "%s", slot_symbol);
    matched = 1;
  }
  if (blocked) return 0;
  if (!matched) return kb_library_base_field_symbol_name(owner_name, displacement, symbol_name, symbol_name_size);
  snprintf(symbol_name, symbol_name_size, "%s", matched_symbol);
  return strlen(matched_symbol) < symbol_name_size;
}

int lookup_app_base_field_slot_symbol_name(const M68kRenderLookup *lookup, int16_t displacement,
    char *symbol_name, size_t symbol_name_size) {
  return lookup_base_field_slot_symbol_name(lookup, M68K_APP_BASE_SYMBOL, displacement, symbol_name,
    symbol_name_size);
}

static int lookup_rsset_use_site_binding_symbol_name(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint8_t operand_index, uint8_t base_reg, int16_t displacement,
    char *symbol_name, size_t symbol_name_size, int32_t *out_addend) {
  const M68kAnalysisPolicy *policy;
  uint16_t binding_index;
  int found = 0;
  char found_symbol[64];
  int32_t found_addend = 0;
  if (symbol_name != NULL && symbol_name_size > 0U) symbol_name[0] = '\0';
  if (out_addend != NULL) *out_addend = 0;
  if (lookup == NULL || lookup->policy == NULL || displacement < 0) return 0;
  policy = lookup->policy;
  found_symbol[0] = '\0';
  for (binding_index = 0U; binding_index < policy->rsset_use_site_binding_count &&
       binding_index < M68K_ANALYSIS_RSSET_USE_SITE_BINDING_LIMIT; ++binding_index) {
    const M68kAnalysisRssetUseSiteBinding *binding = &policy->rsset_use_site_bindings[binding_index];
    uint16_t region_index;
    if (binding->section_index != section_index || binding->offset != offset ||
        binding->operand_index != operand_index || binding->base_reg != base_reg ||
        binding->displacement != (uint32_t)(uint16_t)displacement ||
        binding->base_evidence_id[0] == '\0') {
      continue;
    }
    for (region_index = 0U; region_index < policy->rsset_layout_region_count &&
         region_index < M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT; ++region_index) {
      const M68kAnalysisRssetLayoutRegion *region = &policy->rsset_layout_regions[region_index];
      const char *region_layout = region->layout_name[0] != '\0' ? region->layout_name : M68K_APP_LAYOUT_NAME;
      const char *region_base = region->base_symbol[0] != '\0' ? region->base_symbol : M68K_APP_BASE_SYMBOL;
      uint32_t region_end;
      int32_t candidate_addend;
      if (region->symbol[0] == '\0' || region->size == 0U ||
          strcmp(region_layout, binding->layout_name) != 0 ||
          strcmp(region_base, binding->base_symbol) != 0) {
        continue;
      }
      region_end = region->size <= UINT32_MAX - region->offset ? region->offset + region->size : UINT32_MAX;
      if (binding->displacement < region->offset || binding->displacement >= region_end) continue;
      candidate_addend = (int32_t)(binding->displacement - region->offset);
      if (found != 0 && (strcmp(found_symbol, region->symbol) != 0 || found_addend != candidate_addend)) return 0;
      snprintf(found_symbol, sizeof(found_symbol), "%s", region->symbol);
      found_addend = candidate_addend;
      found = 1;
    }
  }
  if (found == 0 || symbol_name == NULL || symbol_name_size == 0U) return found;
  snprintf(symbol_name, symbol_name_size, "%s", found_symbol);
  if (out_addend != NULL) *out_addend = found_addend;
  return strlen(found_symbol) < symbol_name_size;
}

static int base_layout_kind_is_app(uint8_t layout_kind) {
  return layout_kind == (uint8_t)M68K_BASE_LAYOUT_KIND_APP;
}

static uint8_t base_layout_policy_layout_kind(const M68kAnalysisRssetLayoutRegion *region) {
  const char *layout_name;
  const char *base_symbol;
  if (region == NULL) return (uint8_t)M68K_BASE_LAYOUT_KIND_NAMED;
  layout_name = region->layout_name[0] != '\0' ? region->layout_name : M68K_APP_LAYOUT_NAME;
  base_symbol = region->base_symbol[0] != '\0' ? region->base_symbol : M68K_APP_BASE_SYMBOL;
  if ((region->flags & (uint8_t)M68K_ANALYSIS_RSSET_LAYOUT_REGION_FLAG_APP_LAYOUT) != 0U ||
      (strcmp(layout_name, M68K_APP_LAYOUT_NAME) == 0 &&
       strcmp(base_symbol, M68K_APP_BASE_SYMBOL) == 0)) {
    return (uint8_t)M68K_BASE_LAYOUT_KIND_APP;
  }
  return (uint8_t)M68K_BASE_LAYOUT_KIND_NAMED;
}

static int base_layout_policy_region_size_for_slot(const M68kAnalysisPolicy *policy, const char *symbol_name,
    int32_t displacement, int32_t *out_size) {
  uint16_t index;
  int found = 0;
  int32_t found_size = 0;
  if (out_size != NULL) *out_size = 0;
  if (policy == NULL || symbol_name == NULL || symbol_name[0] == '\0' || displacement < 0) return 0;
  for (index = 0U; index < policy->rsset_layout_region_count &&
       index < M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT; ++index) {
    const M68kAnalysisRssetLayoutRegion *region = &policy->rsset_layout_regions[index];
    const char *base_symbol = region->base_symbol[0] != '\0' ? region->base_symbol : M68K_APP_BASE_SYMBOL;
    if (!base_layout_kind_is_app(base_layout_policy_layout_kind(region)) ||
        strcmp(base_symbol, M68K_APP_BASE_SYMBOL) != 0 ||
        region->symbol[0] == '\0' || strcmp(region->symbol, symbol_name) != 0 ||
        region->offset != (uint32_t)displacement || region->size == 0U) {
      continue;
    }
    if (found != 0 && found_size != (int32_t)region->size) return 0;
    found = 1;
    found_size = (int32_t)region->size;
  }
  if (found == 0 || out_size == NULL) return found;
  *out_size = found_size;
  return 1;
}

static int base_layout_policy_region_storage_kind_for_slot(const M68kAnalysisPolicy *policy,
    const char *symbol_name, int32_t displacement, uint8_t *out_storage_kind) {
  uint16_t index;
  if (out_storage_kind != NULL) *out_storage_kind = M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_UNKNOWN;
  if (policy == NULL || symbol_name == NULL || symbol_name[0] == '\0' || displacement < 0) return 0;
  for (index = 0U; index < policy->rsset_layout_region_count &&
       index < M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT; ++index) {
    const M68kAnalysisRssetLayoutRegion *region = &policy->rsset_layout_regions[index];
    const char *base_symbol = region->base_symbol[0] != '\0' ? region->base_symbol : M68K_APP_BASE_SYMBOL;
    if (!base_layout_kind_is_app(base_layout_policy_layout_kind(region)) ||
        strcmp(base_symbol, M68K_APP_BASE_SYMBOL) != 0 ||
        region->symbol[0] == '\0' || strcmp(region->symbol, symbol_name) != 0 ||
        region->offset != (uint32_t)displacement) {
      continue;
    }
    if (out_storage_kind != NULL) *out_storage_kind = region->storage_kind_id;
    return 1;
  }
  return 0;
}

static int base_layout_slot_compare(const void *left, const void *right) {
  const M68kBaseLayoutSlot *left_slot = (const M68kBaseLayoutSlot *)left;
  const M68kBaseLayoutSlot *right_slot = (const M68kBaseLayoutSlot *)right;
  int layout_cmp;
  if (left_slot->layout_kind < right_slot->layout_kind) return -1;
  if (left_slot->layout_kind > right_slot->layout_kind) return 1;
  layout_cmp = strcmp(left_slot->layout_name, right_slot->layout_name);
  if (layout_cmp != 0) return layout_cmp;
  if (left_slot->displacement < right_slot->displacement) return -1;
  if (left_slot->displacement > right_slot->displacement) return 1;
  return strcmp(left_slot->name, right_slot->name);
}

int lookup_has_amiga_resident_library_context(const M68kRenderLookup *lookup) {
  size_t index;
  if (lookup == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->range_ownership_count; ++index) {
    M68kRenderRangeOwnershipView range;
    const M68kAnalysisStructuredDataItem *item;
    if (!lookup_range_ownership_at_index(lookup, index, &range)) continue;
    if (range.kind != M68K_RANGE_OWNERSHIP_PLATFORM_METADATA) continue;
    item = range.structured_item;
    if (item == NULL) continue;
    if (item->struct_id == AMIGA_OS_STRUCT_ID_RT ||
        item->platform_kind_id == M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_KIND_AMIGA_RESIDENT_AUTOINIT) {
      return 1;
    }
  }
  return 0;
}

static int base_layout_slot_exists(const M68kBaseLayoutSlot *slots, size_t slot_count, const char *name,
    const char *layout_name, int32_t displacement, int *out_conflict) {
  size_t index;
  if (out_conflict != NULL) *out_conflict = 0;
  for (index = 0U; index < slot_count; ++index) {
    if (strcmp(slots[index].layout_name, layout_name) != 0) continue;
    if (strcmp(slots[index].name, name) != 0) continue;
    if (slots[index].displacement != displacement && out_conflict != NULL) *out_conflict = 1;
    return 1;
  }
  return 0;
}

static void base_layout_default_sizeof_symbol(uint8_t layout_kind, const char *layout_name,
    char *symbol_name, size_t symbol_name_size) {
  if (symbol_name == NULL || symbol_name_size == 0U) return;
  if (base_layout_kind_is_app(layout_kind)) {
    snprintf(symbol_name, symbol_name_size, "app_SIZEOF");
  } else {
    snprintf(symbol_name, symbol_name_size, "%s_SIZEOF", layout_name);
  }
}

static void base_layout_effective_sizeof_symbol(uint8_t layout_kind, const char *layout_name,
    const char *metadata_symbol, char *symbol_name, size_t symbol_name_size) {
  if (symbol_name == NULL || symbol_name_size == 0U) return;
  if (metadata_symbol != NULL && metadata_symbol[0] != '\0') {
    snprintf(symbol_name, symbol_name_size, "%s", metadata_symbol);
  } else {
    base_layout_default_sizeof_symbol(layout_kind, layout_name, symbol_name, symbol_name_size);
  }
}

static void base_layout_mark_alias_target(M68kBaseLayoutSlot *slots, size_t layout_start, size_t slot_index) {
  size_t probe;
  if (slots == NULL || slot_index <= layout_start) return;
  for (probe = layout_start; probe < slot_index; ++probe) {
    int32_t probe_end;
    if (slots[probe].alias != 0U) continue;
    probe_end = slots[probe].displacement + slots[probe].size;
    if (slots[probe].displacement <= slots[slot_index].displacement &&
        slots[slot_index].displacement < probe_end) {
      slots[slot_index].has_alias_of = 1U;
      slots[slot_index].alias_of_displacement = slots[probe].displacement;
      snprintf(slots[slot_index].alias_of_name, sizeof(slots[slot_index].alias_of_name), "%s",
        slots[probe].name);
      return;
    }
  }
}

static int32_t base_layout_mark_group_aliases(M68kBaseLayoutSlot *slots, size_t layout_start,
    size_t layout_end, int32_t layout_base_offset) {
  size_t index;
  int32_t cursor = layout_base_offset;
  int32_t layout_sizeof = layout_base_offset;
  if (slots == NULL || layout_start >= layout_end) return layout_sizeof;
  for (index = layout_start; index < layout_end; ++index) {
    slots[index].alias = 0U;
    slots[index].has_alias_of = 0U;
    slots[index].alias_of_displacement = 0;
    slots[index].alias_of_name[0] = '\0';
    if (slots[index].displacement < cursor) {
      slots[index].alias = 1U;
      base_layout_mark_alias_target(slots, layout_start, index);
      continue;
    }
    cursor = slots[index].displacement + slots[index].size;
    if (cursor > layout_sizeof) layout_sizeof = cursor;
  }
  return layout_sizeof;
}

size_t base_layout_prepare_groups(M68kBaseLayoutSlot *slots, size_t slot_count,
    M68kBaseLayoutGroup *layouts, size_t layout_capacity, int32_t app_base_offset,
    int has_resident_context, int has_app_sizeof_value, int32_t app_sizeof_value) {
  size_t index;
  size_t layout_count = 0U;
  if (slots == NULL || layouts == NULL || slot_count == 0U) return 0U;
  qsort(slots, slot_count, sizeof(slots[0]), base_layout_slot_compare);
  for (index = 0U; index < slot_count; ++index) {
    size_t layout_end = index + 1U;
    uint8_t layout_kind = slots[index].layout_kind;
    int32_t layout_base_offset = base_layout_kind_is_app(layout_kind) ? app_base_offset : 0;
    int32_t layout_sizeof;
    while (layout_end < slot_count && slots[layout_end].layout_kind == layout_kind &&
        strcmp(slots[layout_end].layout_name, slots[index].layout_name) == 0) {
      ++layout_end;
    }
    if (layout_count >= layout_capacity) return SIZE_MAX;
    layout_sizeof = base_layout_mark_group_aliases(slots, index, layout_end, layout_base_offset);
    if (base_layout_kind_is_app(layout_kind) && has_app_sizeof_value != 0 &&
        app_sizeof_value > layout_sizeof) {
      layout_sizeof = app_sizeof_value;
    }
    layouts[layout_count].start_index = index;
    layouts[layout_count].end_index = layout_end;
    layouts[layout_count].base_offset = layout_base_offset;
    layouts[layout_count].sizeof_value = layout_sizeof;
    layouts[layout_count].layout_kind = layout_kind;
    layouts[layout_count].uses_lib_size = (uint8_t)(base_layout_kind_is_app(layout_kind) &&
      has_resident_context);
    snprintf(layouts[layout_count].sizeof_symbol, sizeof(layouts[layout_count].sizeof_symbol), "%s",
      slots[index].sizeof_symbol);
    ++layout_count;
    index = layout_end - 1U;
  }
  return layout_count;
}

static void render_asm_base_layout_format_slot_directive(const M68kBaseLayoutSlot *slot, char *line, size_t line_size) {
  if (slot == NULL || line == NULL || line_size == 0U) return;
  if (slot->storage_kind == M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_BYTE_ARRAY) {
    if (slot->size == 1) {
      snprintf(line, line_size, "%s RS.B 1\n", slot->name);
    } else {
      snprintf(line, line_size, "%s RS.B %d\n", slot->name, (int)slot->size);
    }
  } else if (slot->size == 4 && (slot->displacement & 1) == 0) {
    snprintf(line, line_size, "%s RS.L 1\n", slot->name);
  } else if (slot->size == 2 && (slot->displacement & 1) == 0) {
    snprintf(line, line_size, "%s RS.W 1\n", slot->name);
  } else if (slot->size == 1) {
    snprintf(line, line_size, "%s RS.B 1\n", slot->name);
  } else {
    snprintf(line, line_size, "%s RS.B %d\n", slot->name, (int)slot->size);
  }
}

static int base_layout_resident_sizeof_value(const M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    int32_t *out_value) {
  size_t index;
  if (out_value != NULL) *out_value = 0;
  if (lookup == NULL || decode == NULL) return 0;
  for (index = 0U; index < lookup->range_ownership_count; ++index) {
    M68kRenderRangeOwnershipView range;
    const M68kAnalysisStructuredDataItem *item;
    const M68kDecodeSectionIR *section;
    size_t section_index;
    if (!lookup_range_ownership_at_index(lookup, index, &range)) continue;
    if (range.kind != M68K_RANGE_OWNERSHIP_PLATFORM_METADATA) continue;
    item = range.structured_item;
    if (item == NULL) continue;
    if (item->size != 4U ||
        item->platform_kind_id != M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_KIND_AMIGA_RESIDENT_AUTOINIT ||
        item->platform_field_id != M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_AMIGA_RESIDENT_BASE_SIZE) {
      continue;
    }
    section_index = item->has_section_index ? (size_t)item->section_index : 0U;
    if (section_index >= decode->section_count) continue;
    section = &decode->sections[section_index];
    if (section->data == NULL || item->offset > section->size || section->size - item->offset < 4U) continue;
    if (out_value != NULL) *out_value = (int32_t)m68k_read_u32be(section->data + item->offset);
    return 1;
  }
  return 0;
}

size_t base_layout_slot_capacity_for_lookup(const M68kRenderLookup *lookup) {
  size_t slot_capacity;
  if (lookup == NULL) return 1U;
  slot_capacity = lookup->base_field_slot_count +
    (lookup->policy != NULL ? lookup->policy->rsset_layout_region_count : 0U);
  return slot_capacity == 0U ? 1U : slot_capacity;
}

int base_layout_collect_slots(const M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    M68kBaseLayoutSlot *slots, size_t slot_capacity, size_t *out_slot_count,
    int *out_has_resident_context, int *out_has_app_sizeof_value, int32_t *out_base_offset,
    int32_t *out_app_sizeof_value) {
  size_t slot_count = 0U;
  size_t index;
  int32_t lib_size = 0, base_offset = 0;
  int32_t app_sizeof_value = 0;
  int has_app_sizeof_value;
  int has_resident_context;
  if (out_slot_count != NULL) *out_slot_count = 0U;
  if (out_has_resident_context != NULL) *out_has_resident_context = 0;
  if (out_has_app_sizeof_value != NULL) *out_has_app_sizeof_value = 0;
  if (out_base_offset != NULL) *out_base_offset = 0;
  if (out_app_sizeof_value != NULL) *out_app_sizeof_value = 0;
  if (lookup == NULL || slots == NULL) return -1;
  has_resident_context = lookup_has_amiga_resident_library_context(lookup);
  has_app_sizeof_value = base_layout_resident_sizeof_value(lookup, decode, &app_sizeof_value);
  if (has_resident_context) {
    if (!render_amiga_constant_value_by_symbol_id(AMIGA_OS_SYMBOL_ID_LIB_SIZE, &lib_size) || lib_size <= 0) {
      return 0;
    }
    base_offset = lib_size;
  }
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    char symbol_name[64];
    char region_symbol_name[64], field_expr[96];
    int conflict = 0;
    int32_t policy_region_size;
    int32_t region_size;
    if (slot->conflicted != 0U || !render_base_field_slot_owner_is_app_base(slot)) continue;
    if ((int32_t)slot->displacement < base_offset) continue;
    if (slot->value_kind == M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS &&
        lookup_typed_app_slot_region_contains_auto_offset(lookup, slot->displacement)) {
      continue;
    }
    if (lookup_typed_app_slot_field_symbol_name(lookup, slot->displacement, region_symbol_name,
        sizeof(region_symbol_name), field_expr, sizeof(field_expr), NULL)) {
      continue;
    }
    if (!app_base_slot_symbol_name_from_slot(slot, symbol_name, sizeof(symbol_name)) ||
        lookup_app_base_field_slot_symbol_has_other_displacement(lookup, symbol_name, slot->displacement)) {
      continue;
    }
    if (base_layout_slot_exists(slots, slot_count, symbol_name, M68K_APP_LAYOUT_NAME,
        slot->displacement, &conflict)) {
      if (conflict) return -1;
      continue;
    }
    if (slot_count >= slot_capacity) return -1;
    slots[slot_count].displacement = slot->displacement;
    (void)base_layout_policy_region_size_for_slot(lookup->policy, symbol_name, slot->displacement,
      &policy_region_size);
    region_size = lookup_typed_app_slot_region_size(lookup, slot->displacement,
      slots[slot_count].owner_struct_name, sizeof(slots[slot_count].owner_struct_name));
    slots[slot_count].size = policy_region_size > 0
      ? policy_region_size
      : (region_size > 0
      ? region_size
      : (slot->observed_access_size != 0U ? slot->observed_access_size : ((slot->displacement & 1) == 0 ? 4 : 1)));
    (void)base_layout_policy_region_storage_kind_for_slot(lookup->policy, symbol_name, slot->displacement,
      &slots[slot_count].storage_kind);
    snprintf(slots[slot_count].layout_name, sizeof(slots[slot_count].layout_name), M68K_APP_LAYOUT_NAME);
    slots[slot_count].layout_kind = (uint8_t)M68K_BASE_LAYOUT_KIND_APP;
    slots[slot_count].base_kind = M68K_BASE_LAYOUT_BASE_KIND_APP;
    snprintf(slots[slot_count].base_symbol, sizeof(slots[slot_count].base_symbol), M68K_APP_BASE_SYMBOL);
    base_layout_default_sizeof_symbol(slots[slot_count].layout_kind, M68K_APP_LAYOUT_NAME,
      slots[slot_count].sizeof_symbol, sizeof(slots[slot_count].sizeof_symbol));
    snprintf(slots[slot_count].name, sizeof(slots[slot_count].name), "%s", symbol_name);
    slots[slot_count].has_source = slot->has_source;
    slots[slot_count].source_section_index = slot->source_section_index;
    slots[slot_count].source_offset = slot->source_offset;
    slots[slot_count].value_kind = slot->value_kind;
    slots[slot_count].source_kind = M68K_BASE_LAYOUT_FIELD_SOURCE_APP_SLOT_ACCESS;
    ++slot_count;
  }
  if (lookup->policy != NULL) {
    const M68kAnalysisPolicy *policy = lookup->policy;
    for (index = 0U; index < policy->rsset_layout_region_count && index < M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT; ++index) {
      const M68kAnalysisRssetLayoutRegion *region = &policy->rsset_layout_regions[index];
      const char *layout_name = region->layout_name[0] != '\0' ? region->layout_name : M68K_APP_LAYOUT_NAME;
      const char *base_symbol = region->base_symbol[0] != '\0' ? region->base_symbol : M68K_APP_BASE_SYMBOL;
      uint8_t layout_kind = base_layout_policy_layout_kind(region);
      int conflict = 0;
      if (base_layout_kind_is_app(layout_kind)) continue;
      if (region->symbol[0] == '\0' || region->offset > 0x7FFFU || region->size == 0U) continue;
      if (base_layout_slot_exists(slots, slot_count, region->symbol, layout_name, (int32_t)region->offset,
          &conflict)) {
        if (conflict) return -1;
        continue;
      }
      if (slot_count >= slot_capacity) return -1;
      snprintf(slots[slot_count].layout_name, sizeof(slots[slot_count].layout_name), "%s", layout_name);
      slots[slot_count].layout_kind = layout_kind;
      slots[slot_count].base_kind =
        (region->flags & (uint8_t)M68K_ANALYSIS_RSSET_LAYOUT_REGION_FLAG_APP_BASE) != 0U ?
        M68K_BASE_LAYOUT_BASE_KIND_APP : M68K_BASE_LAYOUT_BASE_KIND_UNKNOWN;
      snprintf(slots[slot_count].base_symbol, sizeof(slots[slot_count].base_symbol), "%s", base_symbol);
      base_layout_effective_sizeof_symbol(layout_kind, layout_name, region->sizeof_symbol,
        slots[slot_count].sizeof_symbol, sizeof(slots[slot_count].sizeof_symbol));
      snprintf(slots[slot_count].name, sizeof(slots[slot_count].name), "%s", region->symbol);
      slots[slot_count].displacement = (int32_t)region->offset;
      slots[slot_count].size = region->size;
      slots[slot_count].storage_kind = region->storage_kind_id;
      slots[slot_count].source_kind = M68K_BASE_LAYOUT_FIELD_SOURCE_POLICY_RSSET_REGION;
      ++slot_count;
    }
  }
  if (out_slot_count != NULL) *out_slot_count = slot_count;
  if (out_has_resident_context != NULL) *out_has_resident_context = has_resident_context;
  if (out_has_app_sizeof_value != NULL) *out_has_app_sizeof_value = has_app_sizeof_value;
  if (out_base_offset != NULL) *out_base_offset = base_offset;
  if (out_app_sizeof_value != NULL) *out_app_sizeof_value = app_sizeof_value;
  return 0;
}

void render_asm_base_layout_rs(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode) {
  Arena *scratch_arena;
  ArenaMark scratch_mark;
  M68kBaseLayoutSlot *slots = NULL;
  M68kBaseLayoutGroup *layouts = NULL;
  size_t slot_count = 0U;
  size_t slot_capacity = 0U;
  size_t layout_count = 0U;
  size_t index;
  int32_t base_offset = 0, cursor;
  int32_t app_sizeof_value = 0;
  int has_app_sizeof_value = 0;
  int has_resident_context = 0;
  char line[160];
  if (preview == NULL || lookup == NULL) return;
  slot_capacity = base_layout_slot_capacity_for_lookup(lookup);
  scratch_arena = render_preview_scratch_arena(preview);
  if (scratch_arena == NULL) {
    preview->asm_source_allocation_failed = 1U;
    return;
  }
  scratch_mark = arena_mark(scratch_arena);
  slots = (M68kBaseLayoutSlot *)arena_calloc(scratch_arena, slot_capacity, sizeof(*slots));
  if (slots == NULL) {
    preview->asm_source_allocation_failed = 1U;
    goto cleanup;
  }
  layouts = (M68kBaseLayoutGroup *)arena_calloc(scratch_arena, slot_capacity, sizeof(*layouts));
  if (layouts == NULL) {
    preview->asm_source_allocation_failed = 1U;
    goto cleanup;
  }
  if (base_layout_collect_slots(lookup, decode, slots, slot_capacity, &slot_count,
      &has_resident_context, &has_app_sizeof_value, &base_offset, &app_sizeof_value) != 0) {
    preview->asm_source_allocation_failed = 1U;
    goto cleanup;
  }
  if (slot_count == 0U && (has_app_sizeof_value == 0 || app_sizeof_value <= base_offset)) {
    goto cleanup;
  }
  if (slot_count == 0U) {
    if (has_resident_context) {
      if (!render_asm_include_for_amiga_symbol(preview, "LIB_SIZE")) {
        ++preview->asm_source_instruction_render_failures;
        record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, 0U, 0U, 0U);
        goto cleanup;
      }
      hash_asm_text(preview, "    RSSET LIB_SIZE\n");
      cursor = base_offset;
    } else {
      hash_asm_text(preview, "    RSSET 0\n");
      cursor = 0;
    }
    ++preview->asm_source_lines;
    if (app_sizeof_value > cursor) {
      snprintf(line, sizeof(line), "    RS.B %d\n", (int)(app_sizeof_value - cursor));
      hash_asm_text(preview, line);
      ++preview->asm_source_lines;
    }
    if (!plan_asm_layout_symbol_once(preview, "app_SIZEOF")) {
      preview->asm_source_allocation_failed = 1U;
      goto cleanup;
    }
    hash_asm_text(preview, "app_SIZEOF EQU __RS\n\n");
    preview->asm_source_lines += 2U;
    goto cleanup;
  }
  layout_count = base_layout_prepare_groups(slots, slot_count, layouts, slot_capacity, base_offset,
    has_resident_context, has_app_sizeof_value, app_sizeof_value);
  if (layout_count == SIZE_MAX) {
    preview->asm_source_allocation_failed = 1U;
    goto cleanup;
  }
  for (index = 0U; index < layout_count; ++index) {
    const M68kBaseLayoutGroup *layout = &layouts[index];
    size_t slot_index;
    int emitted_alias = 0;
    if (layout->uses_lib_size != 0U) {
      if (!render_asm_include_for_amiga_symbol(preview, "LIB_SIZE")) {
        ++preview->asm_source_instruction_render_failures;
        record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, 0U, 0U, 0U);
        goto cleanup;
      }
      hash_asm_text(preview, "    RSSET LIB_SIZE\n");
    } else {
      hash_asm_text(preview, "    RSSET 0\n");
    }
    ++preview->asm_source_lines;
    cursor = layout->base_offset;
    for (slot_index = layout->start_index; slot_index < layout->end_index; ++slot_index) {
      const M68kBaseLayoutSlot *slot = &slots[slot_index];
      if (slot->displacement > cursor) {
        snprintf(line, sizeof(line), "    RS.B %d\n", (int)(slot->displacement - cursor));
        hash_asm_text(preview, line);
        ++preview->asm_source_lines;
        cursor = slot->displacement;
      }
      if (slot->alias != 0U) {
        continue;
      } else {
        if (!plan_asm_layout_symbol_once(preview, slot->name)) {
          preview->asm_source_allocation_failed = 1U;
          goto cleanup;
        }
        render_asm_base_layout_format_slot_directive(slot, line, sizeof(line));
        cursor += slot->size;
      }
      hash_asm_text(preview, line);
      ++preview->asm_source_lines;
    }
    for (slot_index = layout->start_index; slot_index < layout->end_index; ++slot_index) {
      const M68kBaseLayoutSlot *slot = &slots[slot_index];
      if (slot->alias == 0U) continue;
      if (!plan_asm_layout_symbol_once(preview, slot->name)) {
        preview->asm_source_allocation_failed = 1U;
        goto cleanup;
      }
      snprintf(line, sizeof(line), "    RSSET $%04X\n",
        (unsigned)((uint32_t)slot->displacement & 0xFFFFU));
      hash_asm_text(preview, line);
      ++preview->asm_source_lines;
      render_asm_base_layout_format_slot_directive(slot, line, sizeof(line));
      hash_asm_text(preview, line);
      ++preview->asm_source_lines;
      emitted_alias = 1;
    }
    if (emitted_alias) {
      if (layout->uses_lib_size != 0U && cursor == layout->base_offset) {
        hash_asm_text(preview, "    RSSET LIB_SIZE\n");
      } else {
        snprintf(line, sizeof(line), "    RSSET $%04X\n", (unsigned)((uint32_t)cursor & 0xFFFFU));
        hash_asm_text(preview, line);
      }
      ++preview->asm_source_lines;
    }
    if (layout->sizeof_value > cursor) {
      snprintf(line, sizeof(line), "    RS.B %d\n", (int)(layout->sizeof_value - cursor));
      hash_asm_text(preview, line);
      ++preview->asm_source_lines;
    }
    if (!plan_asm_layout_symbol_once(preview, layout->sizeof_symbol)) {
      preview->asm_source_allocation_failed = 1U;
      goto cleanup;
    }
    snprintf(line, sizeof(line), "%s EQU __RS\n", layout->sizeof_symbol);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
    hash_asm_text(preview, "\n");
  }
cleanup:
  arena_rewind(scratch_arena, scratch_mark);
}

const char *lookup_indexed_vector_wrapper_library(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->indexed_vector_wrapper_count; ++index) {
    const M68kRenderIndexedVectorWrapper *wrapper = &lookup->indexed_vector_wrappers[index];
    if (wrapper->section_index == section_index && wrapper->offset == offset && wrapper->has_library_id)
      return platform_facts_v2_library_name_for_id(M68K_PLATFORM_BACKEND_AMIGA_HUNK, wrapper->library_id);
  }
  return NULL;
}

static int lookup_indexed_vector_wrapper_index_reg(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint8_t *out_index_reg) {
  size_t index;
  if (out_index_reg != NULL) *out_index_reg = 0U;
  if (lookup == NULL || out_index_reg == NULL) return 0;
  for (index = 0U; index < lookup->indexed_vector_wrapper_count; ++index) {
    const M68kRenderIndexedVectorWrapper *wrapper = &lookup->indexed_vector_wrappers[index];
    if (wrapper->section_index == section_index && wrapper->offset == offset) {
      *out_index_reg = wrapper->index_reg;
      return 1;
    }
  }
  return 0;
}

static const char *directive_for_data_size(uint32_t size) {
  if (size == 4U) return "dc.l";
  if (size == 2U) return "dc.w";
  return "dc.b";
}

void format_numeric_value(char *buffer, size_t buffer_size, uint32_t size, uint32_t value) {
  if (buffer == NULL || buffer_size == 0U) return;
  if (size == 4U) snprintf(buffer, buffer_size, "$%08X", (unsigned)value);
  else if (size == 2U) snprintf(buffer, buffer_size, "$%04X", (unsigned)(value & 0xFFFFU));
  else snprintf(buffer, buffer_size, "$%02X", (unsigned)(value & 0xFFU));
}

static void format_hunk_anchor_expression(char *buffer, size_t buffer_size, const M68kFact *anchor) {
  if (buffer == NULL || buffer_size == 0U) return;
  if (anchor == NULL) {
    buffer[0] = '\0';
    return;
  }
  if (anchor->target_addend < 0) {
    uint64_t magnitude = (uint64_t)(-anchor->target_addend);
    snprintf(buffer, buffer_size, "base(hunk %u)-$%08X",
      (unsigned)anchor->target_section_index, (unsigned)magnitude);
  } else {
    snprintf(buffer, buffer_size, "base(hunk %u)+$%08X",
      (unsigned)anchor->target_section_index, (unsigned)((uint64_t)anchor->target_addend & 0xFFFFFFFFULL));
  }
}

static void format_hunk_anchor_reason(char *buffer, size_t buffer_size, const M68kRenderLookup *lookup,
    const M68kFact *anchor) {
  uint32_t target_extent = 0U;
  if (buffer == NULL || buffer_size == 0U) return;
  if (lookup == NULL || anchor == NULL || anchor->target_section_index >= lookup->section_count ||
      lookup->label_extents == NULL) {
    snprintf(buffer, buffer_size, "target hunk unavailable; left numeric");
    return;
  }
  target_extent = lookup->label_extents[anchor->target_section_index];
  if (anchor->target_addend < 0) {
    snprintf(buffer, buffer_size, "negative addend points before target hunk; left numeric");
  } else if ((uint64_t)anchor->target_addend >= (uint64_t)target_extent) {
    snprintf(buffer, buffer_size, "addend outside target hunk real size $%08X; left numeric",
      (unsigned)target_extent);
  } else {
    snprintf(buffer, buffer_size, "unproven hunk relocation; left numeric");
  }
}

static void format_lossy_hunk_anchor_comment(char *buffer, size_t buffer_size, const M68kRenderLookup *lookup,
    const M68kFact *anchor) {
  char expr[96];
  char reason[160];
  if (buffer == NULL || buffer_size == 0U) return;
  if (anchor == NULL) {
    buffer[0] = '\0';
    return;
  }
  format_hunk_anchor_expression(expr, sizeof(expr), anchor);
  format_hunk_anchor_reason(reason, sizeof(reason), lookup, anchor);
  snprintf(buffer, buffer_size,
    "facts_v2 HUNK_RELOC32 numeric: source hunk %u offset $%08X, target hunk %u, loader result %s; %s",
    (unsigned)anchor->section_index, (unsigned)anchor->offset,
    (unsigned)anchor->target_section_index, expr, reason);
}

static int format_hunk_anchor_relocation_expr(char *buffer, size_t buffer_size, const M68kRenderLookup *lookup,
    const M68kFact *anchor) {
  char base_name[64];
  uint64_t magnitude;
  if (buffer == NULL || buffer_size == 0U) return 0;
  buffer[0] = '\0';
  if (lookup == NULL || anchor == NULL || anchor->target_section_index >= lookup->section_count ||
      anchor->platform_record_kind != AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32 ||
      anchor->size != 4U || anchor->target_addend < INT32_MIN || anchor->target_addend > INT32_MAX ||
      !m68k_source_model_format_section_base_symbol(base_name, sizeof(base_name), anchor->target_section_index)) {
    return 0;
  }
  if (anchor->target_addend == 0) {
    snprintf(buffer, buffer_size, "%s", base_name);
  } else if (anchor->target_addend < 0) {
    magnitude = (uint64_t)(-anchor->target_addend);
    snprintf(buffer, buffer_size, "%s-$%08X", base_name, (unsigned)magnitude);
  } else {
    snprintf(buffer, buffer_size, "%s+$%08X", base_name, (unsigned)anchor->target_addend);
  }
  return 1;
}

static void render_asm_hunk_anchor_relocation(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kFact *anchor) {
  char line[512];
  char expr[128];
  char value[32];
  char comment[384];
  const char *directive;
  if (preview == NULL || lookup == NULL || anchor == NULL) return;
  directive = directive_for_data_size(anchor->size);
  if (format_hunk_anchor_relocation_expr(expr, sizeof(expr), lookup, anchor)) {
    format_hunk_anchor_expression(comment, sizeof(comment), anchor);
    snprintf(line, sizeof(line), "\t%s %s\t; facts_v2 HUNK_RELOC32 anchor: %s\n",
      directive, expr, comment);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
    ++preview->asm_source_relocation_exprs;
    return;
  }
  format_numeric_value(value, sizeof(value), anchor->size, anchor->target_offset);
  format_lossy_hunk_anchor_comment(comment, sizeof(comment), lookup, anchor);
  snprintf(line, sizeof(line), "\t%s %s\t; %s\n", directive, value, comment);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  ++preview->asm_source_lossy_numeric_hunk_relocations;
}

int candidate_is_accepted_start(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kDecodeCandidate *candidate) {
  return candidate != NULL && candidate->byte_count != 0U &&
    accepted_start_at(section, accepted_start, candidate->offset) &&
    m68k_decode_ir_find_candidate_at_offset(section, candidate->offset) == candidate;
}

static int accepted_byte_at(const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes, uint32_t offset) {
  return section != NULL && accepted_bytes != NULL && offset < section->size && accepted_bytes[offset] != 0U;
}

static int accepted_byte_range_overlaps(const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes,
    uint32_t offset, uint32_t size) {
  uint32_t cursor;
  uint32_t end;
  if (section == NULL || accepted_bytes == NULL || offset >= section->size) return 0;
  if (size == 0U) size = 1U;
  end = section->size - offset < size ? section->size : offset + size;
  for (cursor = offset; cursor < end; ++cursor) {
    if (accepted_byte_at(section, accepted_bytes, cursor)) return 1;
  }
  return 0;
}

static const M68kSimFormMetadata *render_cfg_candidate_metadata(const M68kDecodeCandidate *candidate,
    M68kInstructionIR *instruction) {
  if (candidate == NULL || instruction == NULL) return NULL;
  if (m68k_decode_candidate_to_instruction(candidate, instruction) != 0) return NULL;
  return m68k_sim_metadata_for_instruction(instruction);
}

int render_cfg_candidate_has_fallthrough(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata = render_cfg_candidate_metadata(candidate, &instruction);
  if (metadata == NULL) return 1;
  if (metadata->flow_kind == M68K_SIM_FLOW_RETURN) return 0;
  if ((metadata->flow_kind == M68K_SIM_FLOW_JUMP || metadata->flow_kind == M68K_SIM_FLOW_BRANCH) &&
      !metadata->flow_conditional) {
    return 0;
  }
  return 1;
}

static int render_absolute_ref_access_kind(uint8_t access_kind) {
  return access_kind == M68K_SIM_ACCESS_MEMORY_READ ||
    access_kind == M68K_SIM_ACCESS_MEMORY_WRITE ||
    access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS ||
    access_kind == M68K_SIM_ACCESS_BRANCH_TARGET;
}

static uint32_t render_instruction_access_width(const M68kInstructionIR *instruction, uint8_t access_kind) {
  if (instruction == NULL || access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS ||
      access_kind == M68K_SIM_ACCESS_BRANCH_TARGET) {
    return 0U;
  }
  if (instruction->size_suffix == 'b') return 1U;
  if (instruction->size_suffix == 'w') return 2U;
  if (instruction->size_suffix == 'l') return 4U;
  return 0U;
}

uint8_t symbol_ref_kind_for_operand(const M68kOperandIR *operand) {
  if (operand == NULL) return M68K_IR_SYMBOL_REF_ABS;
  if (operand->kind == M68K_ASM_OPERAND_LABEL) return M68K_IR_SYMBOL_REF_PC_REL;
  if ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->value.ea_mode == 7U && (operand->value.ea_reg == 2U || operand->value.ea_reg == 3U)) {
    return M68K_IR_SYMBOL_REF_PC_REL;
  }
  return M68K_IR_SYMBOL_REF_ABS;
}

void attach_operand_label_symbol(const M68kRenderLookup *lookup, M68kInstructionIR *instruction,
    size_t operand_index, size_t source_section_index, uint32_t source_offset, size_t target_section_index,
    uint32_t target_offset) {
  M68kOperandIR *operand;
  uint8_t symbol_kind;
  if (instruction == NULL || operand_index >= instruction->operand_count) return;
  operand = &instruction->operands[operand_index];
  symbol_kind = symbol_ref_kind_for_operand(operand);
  if (symbol_kind == M68K_IR_SYMBOL_REF_PC_REL && source_section_index == target_section_index &&
      !lookup_source_offsets_share_runtime_view(lookup, source_section_index, source_offset, target_offset) &&
      !lookup_source_offset_is_materialized_runtime_range_start(lookup, target_section_index, target_offset)) {
    return;
  }
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
  operand->symbol_ref.kind = symbol_kind;
  operand->symbol_ref.has_name = 1U;
  if (symbol_kind == M68K_IR_SYMBOL_REF_PC_REL && source_section_index == target_section_index &&
      (!lookup_source_offsets_share_runtime_view(lookup, source_section_index, source_offset, target_offset) ||
       (source_offset < target_offset &&
        lookup_source_offset_is_materialized_runtime_range_start(lookup, target_section_index, target_offset)))) {
    operand->symbol_ref.name_is_generated = format_storage_asm_label_with_generation(lookup,
      operand->symbol_ref.name, sizeof(operand->symbol_ref.name), target_section_index, target_offset);
  } else {
    operand->symbol_ref.name_is_generated = format_rendered_asm_label_with_generation(lookup,
      operand->symbol_ref.name, sizeof(operand->symbol_ref.name), target_section_index, target_offset);
  }
  operand->symbol_ref.has_section = 1;
  operand->symbol_ref.section_index = target_section_index;
  operand->symbol_ref.has_section_offset = 1;
  operand->symbol_ref.section_offset = target_offset;
}

static void attach_operand_storage_label_symbol(const M68kRenderLookup *lookup, M68kInstructionIR *instruction,
    size_t operand_index, size_t target_section_index, uint32_t target_offset) {
  M68kOperandIR *operand;
  if (instruction == NULL || operand_index >= instruction->operand_count) return;
  operand = &instruction->operands[operand_index];
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
  operand->symbol_ref.kind = symbol_ref_kind_for_operand(operand);
  operand->symbol_ref.has_name = 1U;
  operand->symbol_ref.name_is_generated = format_storage_asm_label_with_generation(lookup,
    operand->symbol_ref.name, sizeof(operand->symbol_ref.name), target_section_index, target_offset);
  operand->symbol_ref.has_section = 1;
  operand->symbol_ref.section_index = target_section_index;
  operand->symbol_ref.has_section_offset = 1;
  operand->symbol_ref.section_offset = target_offset;
}

static void attach_operand_label_addend_symbol(const M68kRenderLookup *lookup, M68kInstructionIR *instruction,
    size_t operand_index, size_t target_section_index, uint32_t target_offset, int32_t addend) {
  M68kOperandIR *operand;
  if (instruction == NULL || operand_index >= instruction->operand_count) return;
  operand = &instruction->operands[operand_index];
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
  operand->symbol_ref.kind = symbol_ref_kind_for_operand(operand);
  operand->symbol_ref.has_name = 1U;
  operand->symbol_ref.name_is_generated = format_rendered_asm_label_with_generation(lookup,
    operand->symbol_ref.name, sizeof(operand->symbol_ref.name), target_section_index, target_offset);
  operand->symbol_ref.has_section = 1;
  operand->symbol_ref.section_index = target_section_index;
  operand->symbol_ref.has_section_offset = 1;
  operand->symbol_ref.section_offset = target_offset;
  operand->symbol_ref.addend = addend;
}

static int target_matches_relocation(const M68kDecodeTarget *target, const M68kFact *relocation) {
  return target != NULL && relocation != NULL && target->has_section != 0U &&
    target->section_index == relocation->target_section_index && target->offset == relocation->target_offset;
}

static int32_t signed_8(uint32_t value) {
  return (int8_t)(value & 0xFFU);
}

static int32_t signed_16(uint32_t value) {
  return (int16_t)(value & 0xFFFFU);
}

static int relocation_fits_operand_span(const M68kFact *relocation, uint32_t span_start, uint32_t span_size) {
  uint32_t span_end;
  uint32_t relocation_end;
  if (relocation == NULL || relocation->size == 0U || span_size == 0U) return 0;
  if (span_start > UINT32_MAX - span_size || relocation->offset > UINT32_MAX - relocation->size) return 0;
  span_end = span_start + span_size;
  relocation_end = relocation->offset + relocation->size;
  return relocation->offset == span_start && relocation_end == span_end;
}

static int absolute_operand_value_matches_relocation(const M68kAsmOperandValue *operand, const M68kFact *relocation,
    char size_suffix) {
  uint32_t encoded_value = 0U;
  int has_encoded_value = 0;
  if (operand == NULL || relocation == NULL) return 0;
  if (relocation->target_addend > 0 && relocation->target_addend <= UINT32_MAX) {
    encoded_value = (uint32_t)relocation->target_addend;
    has_encoded_value = 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_IMM) {
    if (size_suffix == 'l' && relocation->size != 4U) return 0;
    if (size_suffix != 'l' && relocation->size != 2U) return 0;
    return operand->value == relocation->target_offset ||
      (has_encoded_value && operand->value == encoded_value);
  }
  if (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) {
    if (operand->ea_mode == 7U && operand->ea_reg == 1U && relocation->size == 4U)
      return operand->value == relocation->target_offset ||
        (has_encoded_value && operand->value == encoded_value);
    if (operand->ea_mode == 7U && operand->ea_reg == 4U) {
      if (size_suffix == 'l' && relocation->size != 4U) return 0;
      if (size_suffix != 'l' && relocation->size != 2U) return 0;
      return operand->value == relocation->target_offset ||
        (has_encoded_value && operand->value == encoded_value);
    }
  }
  if (operand->kind == M68K_ASM_OPERAND_ABSL && relocation->size == 4U)
    return operand->value == relocation->target_offset ||
      (has_encoded_value && operand->value == encoded_value);
  return 0;
}

static int pc_relative_operand_value_matches_relocation(const M68kDecodeCandidate *candidate, size_t operand_index,
    const M68kAsmOperandValue *operand, const M68kFact *relocation) {
  M68kAsmOperandValue asm_operands[M68K_DECODE_IR_MAX_OPERANDS];
  size_t index;
  size_t relative_base;
  int64_t target;
  if (candidate == NULL || operand == NULL || relocation == NULL || operand_index >= candidate->operand_count)
    return 0;
  if (operand->kind == M68K_ASM_OPERAND_LABEL) {
    int32_t disp = relocation->size == 1U ? signed_8(operand->value) : signed_16(operand->value);
    target = (int64_t)candidate->offset + 2 + disp;
    return target >= 0 && target <= UINT32_MAX && (uint32_t)target == relocation->target_offset;
  }
  if (!((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->ea_mode == 7U && (operand->ea_reg == 2U || operand->ea_reg == 3U))) {
    return 0;
  }
  if (operand->ea_reg == 3U &&
      (operand->full_ext_base_suppress != 0U || operand->full_ext_index_suppress != 0U ||
       operand->full_ext_base_disp_size != 0U || operand->full_ext_outer_disp_size != 0U ||
       operand->full_ext_iis != 0U)) {
    return 0;
  }
  for (index = 0U; index < candidate->operand_count; ++index) {
    asm_operands[index] = candidate->operands[index];
    asm_operands[index].kind = candidate->operand_kinds[index];
  }
  relative_base = m68k_asm_operand_relative_base_offset(candidate->asm_form_index, asm_operands,
    candidate->operand_count, m68k_decode_candidate_effective_size_suffix(candidate), operand_index, 0);
  target = (int64_t)candidate->offset + (int64_t)relative_base + signed_16(operand->value);
  return target >= 0 && target <= UINT32_MAX && (uint32_t)target == relocation->target_offset;
}

static int operand_value_matches_relocation(const M68kDecodeCandidate *candidate, size_t operand_index,
    const M68kFact *relocation) {
  M68kAsmOperandValue operand;
  if (candidate == NULL || relocation == NULL || operand_index >= candidate->operand_count) return 0;
  operand = candidate->operands[operand_index];
  operand.kind = candidate->operand_kinds[operand_index];
  if (absolute_operand_value_matches_relocation(&operand, relocation, m68k_decode_candidate_effective_size_suffix(candidate)))
    return 1;
  return pc_relative_operand_value_matches_relocation(candidate, operand_index, &operand, relocation);
}

int find_unique_relocation_operand(const M68kDecodeCandidate *candidate, const M68kFact *relocation,
    size_t *out_operand_index) {
  size_t operand_index;
  size_t match_index = 0U;
  size_t match_count = 0U;
  if (candidate == NULL || relocation == NULL || out_operand_index == NULL) return 0;
  for (operand_index = 0U; operand_index < candidate->operand_count; ++operand_index) {
    uint32_t span_start = 0U;
    uint32_t span_size = 0U;
    if (!m68k_decode_candidate_operand_storage_span(candidate, operand_index, &span_start, &span_size)) continue;
    if (!relocation_fits_operand_span(relocation, span_start, span_size)) continue;
    if (!operand_value_matches_relocation(candidate, operand_index, relocation)) continue;
    match_index = operand_index;
    ++match_count;
  }
  if (match_count != 1U) return 0;
  *out_operand_index = match_index;
  return 1;
}

int candidate_loads_relocated_global_slot_to_a6(const M68kRenderLookup *lookup, size_t section_index,
    const M68kDecodeCandidate *candidate, size_t *out_target_section, uint32_t *out_target_offset) {
  M68kInstructionIR instruction;
  uint32_t offset;
  uint32_t end;
  if (lookup == NULL || candidate == NULL || out_target_section == NULL || out_target_offset == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!operand_is_address_register_local(&instruction.operands[1], 6U)) return 0;
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset + 2U; offset < end; ++offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section_index, offset);
    size_t operand_index = 0U;
    if (relocation == NULL) continue;
    if (!lookup_has_renderable_label(lookup, relocation->target_section_index, relocation->target_offset)) continue;
    if (!find_unique_relocation_operand(candidate, relocation, &operand_index) || operand_index != 0U) continue;
    *out_target_section = relocation->target_section_index;
    *out_target_offset = relocation->target_offset;
    return 1;
  }
  return 0;
}

int candidate_direct_control_target(const M68kRenderLookup *lookup, size_t source_section_index,
    const M68kDecodeCandidate *candidate, size_t *out_section_index, uint32_t *out_target) {
  uint32_t offset;
  uint32_t end;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_target != NULL) *out_target = 0U;
  if (candidate == NULL || out_section_index == NULL || out_target == NULL) return 0;
  if (!candidate_has_call_or_jump_flow(candidate)) return 0;
  if (lookup != NULL && candidate->operand_count == 1U) {
    end = candidate->offset + candidate->byte_count;
    for (offset = candidate->offset + 2U; offset < end; ++offset) {
      const M68kFact *relocation = lookup_relocation_at(lookup, source_section_index, offset);
      size_t operand_index = 0U;
      if (relocation == NULL) continue;
      if (!find_unique_relocation_operand(candidate, relocation, &operand_index) || operand_index != 0U) continue;
      *out_section_index = relocation->target_section_index;
      *out_target = relocation->target_offset;
      return 1;
    }
  }
  return candidate_direct_target(candidate, out_section_index, out_target);
}

int candidate_calls_a6_lvo(const M68kDecodeCandidate *candidate, int16_t *out_lvo) {
  M68kAsmOperandValue operand;
  int16_t displacement;
  if (candidate == NULL || out_lvo == NULL) return 0;
  if (!candidate_has_call_or_jump_flow(candidate)) return 0;
  if (candidate->operand_count != 1U) return 0;
  operand = candidate->operands[0];
  operand.kind = candidate->operand_kinds[0];
  if (operand.kind != M68K_ASM_OPERAND_EA || operand.ea_mode != 5U || operand.ea_reg != 6U) return 0;
  displacement = (int16_t)(operand.value & 0xFFFFU);
  if (displacement >= 0) return 0;
  *out_lvo = displacement;
  return 1;
}

int operand_is_postinc_a7_local(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_POSTINC) return operand->value.reg == 7U;
  return operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 3U && operand->value.ea_reg == 7U;
}

int instruction_is_local_wrapper_cleanup(const M68kInstructionIR *instruction) {
  if (instruction == NULL) return 0;
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDQ || instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADD) &&
      instruction->operand_count == 2U && operand_is_address_register_local(&instruction->operands[1], 7U)) {
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U &&
      operand_is_address_register_local(&instruction->operands[1], 7U)) {
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && instruction->operand_count == 2U &&
      operand_is_postinc_a7_local(&instruction->operands[0])) {
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count == 2U &&
      operand_is_postinc_a7_local(&instruction->operands[0])) {
    return 1;
  }
  return 0;
}

int candidate_has_non_call_control_target(const M68kDecodeCandidate *candidate) {
  size_t target_index;
  if (candidate == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_JUMP) return 1;
  }
  return 0;
}

int candidate_calls_a6_data_indexed_vector(const M68kDecodeCandidate *candidate, uint8_t *out_index_reg) {
  M68kAsmOperandValue operand;
  if (out_index_reg != NULL) *out_index_reg = 0U;
  if (candidate == NULL) return 0;
  if (out_index_reg == NULL) return 0;
  if (!candidate_has_call_or_jump_flow(candidate)) return 0;
  if (candidate->operand_count != 1U) return 0;
  operand = candidate->operands[0];
  operand.kind = candidate->operand_kinds[0];
  if (operand.kind != M68K_ASM_OPERAND_EA || operand.ea_mode != 6U || operand.ea_reg != 6U ||
      operand.index_is_address != 0U || operand.index_reg >= 8U || operand.value != 0U) {
    return 0;
  }
  *out_index_reg = operand.index_reg;
  return 1;
}

int candidate_direct_same_section_target(const M68kDecodeCandidate *candidate, size_t section_index,
    uint32_t *out_target) {
  size_t target_section_index = 0U;
  if (out_target != NULL) *out_target = 0U;
  if (!candidate_direct_target(candidate, &target_section_index, out_target)) return 0;
  return target_section_index == section_index;
}

int candidate_direct_target(const M68kDecodeCandidate *candidate, size_t *out_section_index,
    uint32_t *out_target) {
  size_t target_index;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_target != NULL) *out_target = 0U;
  if (candidate == NULL || out_section_index == NULL || out_target == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->has_section == 0U) continue;
    if (target->kind != M68K_DECODE_TARGET_CALL && target->kind != M68K_DECODE_TARGET_JUMP) continue;
    *out_section_index = target->section_index;
    *out_target = target->offset;
    return 1;
  }
  return 0;
}

static int candidate_any_same_section_target(const M68kDecodeCandidate *candidate, size_t section_index,
    uint32_t *out_target) {
  size_t target_index;
  if (out_target != NULL) *out_target = 0U;
  if (candidate == NULL || out_target == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->has_section == 0U || target->section_index != section_index) continue;
    if (target->kind != M68K_DECODE_TARGET_BRANCH && target->kind != M68K_DECODE_TARGET_CALL &&
        target->kind != M68K_DECODE_TARGET_JUMP) {
      continue;
    }
    *out_target = target->offset;
    return 1;
  }
  return 0;
}

int candidate_loads_data_lvo_immediate(const M68kDecodeCandidate *candidate, uint8_t *out_reg,
    int16_t *out_lvo) {
  M68kInstructionIR instruction;
  if (out_reg != NULL) *out_reg = 0U;
  if (out_lvo != NULL) *out_lvo = 0;
  if (candidate == NULL || out_reg == NULL || out_lvo == NULL) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!instruction_loads_data_immediate(&instruction, out_reg, out_lvo)) return 0;
  return *out_lvo < 0;
}

int render_lookup_add_indexed_vector_wrapper_branch_aliases(M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t indexed_entry,
    uint8_t index_reg, const char *library_name) {
  uint32_t offset = 0U;
  uint32_t segment_entry = 0U;
  int segment_valid = 0;
  if (lookup == NULL || section == NULL || accepted_start == NULL || library_name == NULL) return 0;
  while (offset < section->size) {
    const M68kDecodeCandidate *candidate;
    uint32_t target = 0U;
    if (!accepted_start_at(section, accepted_start, offset)) {
      segment_valid = 0;
      ++offset;
      continue;
    }
    candidate = find_candidate_at_offset_local(section, offset);
    if (candidate == NULL || candidate->byte_count == 0U) {
      segment_valid = 0;
      ++offset;
      continue;
    }
    if (!segment_valid) {
      segment_valid = 1;
      segment_entry = offset;
    }
    if (candidate_any_same_section_target(candidate, section->section_index, &target) && target == indexed_entry &&
        segment_entry != indexed_entry) {
      if (render_lookup_add_indexed_vector_wrapper(lookup, section->section_index, segment_entry, index_reg,
          library_name) != 0)
        return -1;
    }
    if (candidate_terminates_a6_state(candidate)) segment_valid = 0;
    offset += candidate->byte_count;
  }
  return 0;
}

int candidate_writes_a6_unknown(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  if (candidate == NULL) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    return instruction.operand_count >= 2U && reglist_contains_address_register_local(&instruction.operands[1], 6U);
  }
  return instruction.operand_count >= 2U && operand_is_address_register_local(&instruction.operands[1], 6U);
}

int candidate_terminates_a6_state(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  if (candidate == NULL || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  return metadata != NULL &&
    (metadata->flow_kind == M68K_SIM_FLOW_RETURN || metadata->flow_kind == M68K_SIM_FLOW_JUMP);
}

int candidate_has_local_helper_summary_fallthrough(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  if (candidate == NULL) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 1;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL) return 1;
  if (metadata->flow_kind == M68K_SIM_FLOW_RETURN || metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
      (metadata->flow_kind == M68K_SIM_FLOW_TRAP && metadata->flow_conditional == 0U) ||
      (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional == 0U)) {
    return 0;
  }
  return 1;
}

int amiga_vector_call_input_by_register(const AmigaOsLibraryVectorInfo *vector,
    uint8_t reg_kind, uint8_t reg_index, PlatformFactsV2CallInput *out_input) {
  const char *symbol_name;
  if (out_input != NULL) platform_facts_v2_call_input_init(out_input);
  if (vector == NULL) return 0;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, vector->lvo_symbol_id);
  return platform_facts_v2_call_input_by_register(M68K_PLATFORM_BACKEND_AMIGA_HUNK, symbol_name,
    reg_kind, reg_index, out_input);
}

static int attach_symbolic_targets(const M68kRenderLookup *lookup, size_t source_section_index,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const uint8_t *accepted_bytes,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  size_t target_index;
  if (lookup == NULL || candidate == NULL || instruction == NULL) return -1;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    M68kOperandIR *operand;
    uint8_t symbol_kind;
    if (target->has_section == 0U || target->has_operand == 0U ||
        target->operand_index >= instruction->operand_count) {
      continue;
    }
    if (!lookup_has_renderable_label(lookup, target->section_index, target->offset)) continue;
    operand = &instruction->operands[target->operand_index];
    symbol_kind = symbol_ref_kind_for_operand(operand);
    if (symbol_kind == M68K_IR_SYMBOL_REF_ABS &&
        ((target->kind != M68K_DECODE_TARGET_CALL && target->kind != M68K_DECODE_TARGET_JUMP) ||
         !candidate_operand_is_absolute_word_local(candidate, target->operand_index))) {
      continue;
    }
    if (symbol_kind == M68K_IR_SYMBOL_REF_PC_REL && section != NULL &&
        target->section_index == section->section_index && accepted_start != NULL && accepted_bytes != NULL &&
        accepted_byte_at(section, accepted_bytes, target->offset) &&
        !accepted_start_at(section, accepted_start, target->offset)) {
      continue;
    }
    attach_operand_label_symbol(lookup, instruction, target->operand_index, source_section_index,
      candidate->offset, target->section_index, target->offset);
  }
  return 0;
}

static int attach_absolute_word_control_symbols(const M68kRenderLookup *lookup, size_t source_section_index,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  uint32_t section_size;
  size_t operand_index;
  if (lookup == NULL || lookup->object == NULL || candidate == NULL || instruction == NULL ||
      source_section_index >= lookup->object->section_count) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL ||
      (metadata->flow_kind != M68K_SIM_FLOW_CALL && metadata->flow_kind != M68K_SIM_FLOW_JUMP)) {
    return 0;
  }
  section_size = lookup->object->sections[source_section_index].size;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    uint32_t absolute = 0U;
    uint32_t target_offset = 0U;
    if (operand->symbol_ref.has_name != 0U || !candidate_operand_is_absolute_word_local(candidate, operand_index) ||
        !operand_absolute_offset_local(operand, &absolute)) {
      continue;
    }
    if (!lookup_exact_pointer_value_label_offset(lookup, source_section_index, section_size, absolute, 0U,
        &target_offset)) {
      continue;
    }
    if (absolute != target_offset) continue;
    attach_operand_label_symbol(lookup, instruction, operand_index, source_section_index, candidate->offset,
      source_section_index, target_offset);
  }
  return 0;
}

static int attach_platform_pc_relative_section_anchor_symbols(const M68kRenderLookup *lookup, size_t section_index,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  size_t operand_index;
  if (lookup == NULL || lookup->object == NULL || candidate == NULL || instruction == NULL) return 0;
  if (section_index >= lookup->section_count) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count &&
       operand_index < candidate->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    M68kAsmOperandValue asm_operands[M68K_DECODE_IR_MAX_OPERANDS];
    uint32_t base_offset = 0U;
    int32_t addend = 0;
    uint8_t symbol_provenance = M68K_IR_SYMBOL_PROVENANCE_NONE;
    size_t index;
    size_t relative_base;
    int64_t target;
    if (operand->symbol_ref.has_name != 0U) continue;
    if (operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_mode != 7U || operand->value.ea_reg != 2U)
      continue;
    if (candidate->operand_kinds[operand_index] != M68K_ASM_OPERAND_EA ||
        candidate->operands[operand_index].ea_mode != 7U ||
        candidate->operands[operand_index].ea_reg != 2U) {
      continue;
    }
    for (index = 0U; index < candidate->operand_count; ++index) {
      asm_operands[index] = candidate->operands[index];
      asm_operands[index].kind = candidate->operand_kinds[index];
    }
    relative_base = m68k_asm_operand_relative_base_offset(candidate->asm_form_index, asm_operands,
      candidate->operand_count, m68k_decode_candidate_effective_size_suffix(candidate), operand_index, 0);
    target = (int64_t)candidate->offset + (int64_t)relative_base + signed_16(candidate->operands[operand_index].value);
    if (!platform_facts_v2_pc_relative_section_anchor_for_target(lookup->object->platform_backend_kind, target,
        &base_offset, &addend, &symbol_provenance) || lookup->label_extents == NULL ||
        base_offset >= lookup->label_extents[section_index] ||
        !lookup_has_renderable_label(lookup, section_index, base_offset)) {
      continue;
    }
    m68k_ir_symbol_ref_init(&operand->symbol_ref);
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_PC_REL;
    operand->symbol_ref.has_name = 1U;
    operand->symbol_ref.name_is_generated = format_rendered_asm_label_with_generation(lookup,
      operand->symbol_ref.name, sizeof(operand->symbol_ref.name), section_index, base_offset);
    operand->symbol_ref.has_section = 1;
    operand->symbol_ref.section_index = section_index;
    operand->symbol_ref.has_section_offset = 1;
    operand->symbol_ref.section_offset = base_offset;
    operand->symbol_ref.addend = addend;
    operand->symbol_ref.name_provenance = symbol_provenance;
  }
  return 0;
}

static const M68kDecodeCandidate *accepted_candidate_covering_offset_local(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, uint32_t offset) {
  size_t lo = 0U;
  size_t hi;
  const M68kDecodeCandidate *candidate;
  uint32_t candidate_end;
  if (section == NULL || accepted_start == NULL || offset >= section->size ||
      section->candidate_count == 0U) {
    return NULL;
  }
  hi = section->candidate_count;
  while (lo < hi) {
    size_t mid = lo + ((hi - lo) / 2U);
    if (section->candidates[mid].offset <= offset) lo = mid + 1U;
    else hi = mid;
  }
  while (lo > 0U) {
    --lo;
    candidate = &section->candidates[lo];
    if (candidate->offset >= section->size || !accepted_start[candidate->offset]) continue;
    if (candidate->offset > offset) continue;
    if (candidate->byte_count == 0U || candidate->offset > UINT32_MAX - candidate->byte_count) continue;
    candidate_end = candidate->offset + candidate->byte_count;
    if (offset > candidate->offset && offset < candidate_end) return candidate;
    if (candidate->offset + 32U < offset) break;
  }
  return NULL;
}

static const M68kDecodeCandidate *find_previous_accepted_candidate_local(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kDecodeCandidate *candidate);

static const M68kDecodeCandidate *find_previous_accepted_candidate_local(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kDecodeCandidate *candidate) {
  size_t index;
  if (section == NULL || accepted_start == NULL || candidate == NULL) return NULL;
  for (index = 0U; index < section->candidate_count; ++index) {
    const M68kDecodeCandidate *previous = &section->candidates[index];
    if (previous->offset >= section->size || accepted_start[previous->offset] == 0U) continue;
    if (previous->byte_count <= UINT32_MAX - previous->offset &&
        previous->offset + previous->byte_count == candidate->offset) {
      return previous;
    }
  }
  return NULL;
}

static int candidate_lea_pc_relative_section_base_to_reg(const M68kDecodeCandidate *candidate, uint8_t reg) {
  M68kInstructionIR instruction;
  M68kAsmOperandValue asm_operands[M68K_DECODE_IR_MAX_OPERANDS];
  size_t index;
  size_t relative_base;
  int64_t target;
  uint8_t dest_reg = 0U;
  if (candidate == NULL || candidate->mnemonic_id != M68K_ASM_MNEMONIC_LEA ||
      candidate->operand_count != 2U || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
      instruction.operand_count != 2U || !operand_address_register_index_local(&instruction.operands[1], &dest_reg) ||
      dest_reg != reg || instruction.operands[0].kind != M68K_ASM_OPERAND_EA ||
      instruction.operands[0].value.ea_mode != 7U || instruction.operands[0].value.ea_reg != 2U ||
      candidate->operand_kinds[0] != M68K_ASM_OPERAND_EA || candidate->operands[0].ea_mode != 7U ||
      candidate->operands[0].ea_reg != 2U) {
    return 0;
  }
  for (index = 0U; index < candidate->operand_count; ++index) {
    asm_operands[index] = candidate->operands[index];
    asm_operands[index].kind = candidate->operand_kinds[index];
  }
  relative_base = m68k_asm_operand_relative_base_offset(candidate->asm_form_index, asm_operands,
    candidate->operand_count, m68k_decode_candidate_effective_size_suffix(candidate), 0U, 0);
  target = (int64_t)candidate->offset + (int64_t)relative_base + signed_16(candidate->operands[0].value);
  return target == 0;
}

static int attach_amiga_loadseg_segment_link_slot_symbol(M68kRenderIRPreview *preview,
    const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  const M68kDecodeCandidate *previous;
  uint8_t base_reg = 0U;
  uint8_t dest_reg = 0U;
  int16_t displacement = 0;
  if (preview == NULL || lookup == NULL || lookup->object == NULL || section == NULL || accepted_start == NULL ||
      candidate == NULL || instruction == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK ||
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA || instruction->size_suffix != 'l' ||
      instruction->operand_count != 2U || instruction->operands[0].symbol_ref.has_name != 0U ||
      !operand_is_address_displacement_local(&instruction->operands[0], &base_reg, &displacement) ||
      displacement != -4 || !operand_address_register_index_local(&instruction->operands[1], &dest_reg) ||
      dest_reg != base_reg) {
    return 1;
  }
  previous = find_previous_accepted_candidate_local(section, accepted_start, candidate);
  if (previous == NULL || !candidate_lea_pc_relative_section_base_to_reg(previous, base_reg)) return 1;
  if (!render_asm_declare_symbol_once(preview, "amiga_loadseg_segment_link", -4)) return 0;
  attach_amiga_platform_symbol(&instruction->operands[0], "amiga_loadseg_segment_link");
  return 1;
}

static int amiga_abs_exec_base_load_should_stay_absolute(const M68kRenderLookup *lookup,
    const M68kInstructionIR *instruction, size_t operand_index, const M68kOperandIR *operand,
    const M68kFact *fact) {
  uint32_t absolute = 0U;
  if (lookup == NULL || lookup->object == NULL || instruction == NULL || operand == NULL || fact == NULL) return 0;
  if (!platform_facts_v2_absolute_memory_owner_stays_literal(lookup->object->platform_backend_kind,
      fact->runtime_address)) {
    return 0;
  }
  if (fact->target_section_index < lookup->section_count && fact->runtime_address == fact->target_offset &&
      lookup_has_renderable_label(lookup, fact->target_section_index, fact->target_offset)) {
    return 0;
  }
  if (operand_index != 0U || instruction->operand_count < 2U) return 0;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA) {
    return 0;
  }
  return operand_absolute_offset_local(operand, &absolute) && absolute == fact->runtime_address;
}

static int operand_is_memory_reference_for_overlap_guard(const M68kOperandIR *operand) {
  if (operand == NULL ||
      (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA)) {
    return 0;
  }
  if (operand->value.ea_mode == 0U || operand->value.ea_mode == 1U) return 0;
  return !(operand->value.ea_mode == 7U && operand->value.ea_reg == 4U);
}

static int attach_runtime_address_ref_symbols(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kSourceAnalysisIR *source_analysis, const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  size_t operand_index;
  const M68kSimFormMetadata *metadata;
  uint8_t has_source_analysis_section = 0U;
  if (lookup == NULL || section == NULL || candidate == NULL || instruction == NULL) return 0;
  has_source_analysis_section = source_analysis_section_for_render(source_analysis, section->section_index) != NULL;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kFact *fact;
    M68kOperandIR *operand;
    if (operand_index >= candidate->operand_count) break;
    operand = &instruction->operands[operand_index];
    if (operand->symbol_ref.has_name != 0U) continue;
    fact = lookup_runtime_address_ref_for_operand(lookup, section->section_index, candidate->offset, operand_index);
    if (fact == NULL) continue;
    if (!has_source_analysis_section && fact->has_sink_address && candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) {
      const char *role;
      uint32_t value = 0U;
      char symbol[80];
      if (m68k_ir_operand_immediate_value(operand, &value) && value == fact->runtime_address) {
        role = runtime_address_ref_sink_role(lookup, fact);
        if (role != NULL &&
            render_asm_define_runtime_address_symbol_once(preview, role, fact->runtime_address, symbol,
              sizeof(symbol))) {
          attach_amiga_platform_symbol(operand, symbol);
          continue;
        }
      }
    }
    if (!has_source_analysis_section && fact->target_section_index >= lookup->section_count) {
      const char *role;
      uint32_t value = 0U;
      char symbol[80];
      if (!m68k_ir_operand_immediate_value(operand, &value) || value != fact->runtime_address) continue;
      role = external_runtime_address_ref_role(lookup, fact);
      if (role == NULL) continue;
      if (!render_asm_define_runtime_address_symbol_once(preview, role, fact->runtime_address, symbol,
          sizeof(symbol))) {
        return 0;
      }
      attach_amiga_platform_symbol(operand, symbol);
      continue;
    }
    {
      uint32_t target_runtime_address = fact->runtime_address;
      int has_materialized_target = lookup_source_has_materialized_runtime_address(lookup,
        fact->target_section_index, fact->target_offset, fact->runtime_address) ||
        fact->runtime_address == fact->target_offset;
      if (!has_materialized_target &&
          lookup_source_runtime_address(lookup, fact->target_section_index, fact->target_offset,
            &target_runtime_address) && target_runtime_address != fact->runtime_address &&
          lookup_has_renderable_label(lookup, fact->target_section_index, fact->target_offset)) {
        if (runtime_address_maps_to_materialized_source(lookup, fact->target_section_index, fact->runtime_address)) {
          int64_t addend = (int64_t)(uint64_t)fact->runtime_address - (int64_t)(uint64_t)target_runtime_address;
          if (addend < INT32_MIN || addend > INT32_MAX) {
            record_numeric_runtime_ref(preview, fact);
            continue;
          }
        } else {
          char symbol[80];
          if (!amiga_abs_exec_base_load_should_stay_absolute(lookup, instruction, operand_index, operand, fact) &&
              (runtime_address_ref_targets_unmaterialized_discovered_code(lookup, fact) ||
               runtime_address_ref_targets_discovered_copy_range_start(lookup, fact)) &&
              render_asm_define_runtime_address_symbol_once(preview, "runtime_code", fact->runtime_address, symbol,
                sizeof(symbol))) {
            attach_generic_symbol(operand, symbol);
            continue;
          }
          record_numeric_runtime_ref(preview, fact);
          continue;
        }
      } else if (!has_materialized_target) {
        char symbol[80];
        if (!amiga_abs_exec_base_load_should_stay_absolute(lookup, instruction, operand_index, operand, fact) &&
            (runtime_address_ref_targets_unmaterialized_discovered_code(lookup, fact) ||
             runtime_address_ref_targets_discovered_copy_range_start(lookup, fact)) &&
            render_asm_define_runtime_address_symbol_once(preview, "runtime_code", fact->runtime_address, symbol,
              sizeof(symbol))) {
          attach_generic_symbol(operand, symbol);
          continue;
        }
        record_numeric_runtime_ref(preview, fact);
        continue;
      }
      if (amiga_abs_exec_base_load_should_stay_absolute(lookup, instruction, operand_index, operand, fact)) {
        record_numeric_runtime_ref(preview, fact);
        continue;
      }
      if (fact->target_section_index == section->section_index && metadata != NULL && operand_index < 4U &&
          operand_is_memory_reference_for_overlap_guard(operand) &&
          (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_READ ||
           metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_WRITE) &&
          accepted_byte_range_overlaps(section, accepted_bytes, fact->target_offset,
            render_instruction_access_width(instruction, metadata->operand_access_kinds[operand_index]))) {
        record_numeric_runtime_ref(preview, fact);
        continue;
      }
      {
        uint32_t absolute = 0U;
        if (operand_absolute_offset_local(operand, &absolute) && absolute == fact->target_offset &&
            lookup_has_renderable_label(lookup, fact->target_section_index, fact->target_offset) &&
            lookup_source_offset_is_materialized_runtime_range_start(lookup, fact->target_section_index,
              fact->target_offset)) {
          attach_operand_storage_label_symbol(lookup, instruction, operand_index, fact->target_section_index,
            fact->target_offset);
          continue;
        }
      }
      if (!lookup_has_renderable_label(lookup, fact->target_section_index, fact->target_offset)) {
        if (preview != NULL) {
          ++preview->asm_source_instruction_render_failures;
          record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, section->section_index,
            candidate->offset, fact->target_offset);
        }
        return 0;
      }
      {
        const char *role = lookup_runtime_address_value_semantic_role(lookup, fact->runtime_address);
        char symbol[80];
        if (role != NULL &&
            (fact->target_section_index >= lookup->section_count ||
             !runtime_address_maps_to_materialized_source(lookup, fact->target_section_index,
               fact->runtime_address)) &&
            render_asm_define_runtime_address_symbol_once(preview, role, fact->runtime_address, symbol,
              sizeof(symbol))) {
          attach_generic_symbol(operand, symbol);
          continue;
        }
      }
      m68k_ir_symbol_ref_init(&operand->symbol_ref);
      operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_ABS;
      operand->symbol_ref.has_name = 1U;
      operand->symbol_ref.has_section = 1;
      operand->symbol_ref.section_index = fact->target_section_index;
      operand->symbol_ref.has_section_offset = 1;
      operand->symbol_ref.section_offset = fact->target_offset;
      if (target_runtime_address != fact->runtime_address) {
        int64_t addend = (int64_t)(uint64_t)fact->runtime_address - (int64_t)(uint64_t)target_runtime_address;
        if (addend >= INT32_MIN && addend <= INT32_MAX) operand->symbol_ref.addend = (int32_t)addend;
      }
      operand->symbol_ref.name_is_generated = format_runtime_operand_asm_label_with_generation(lookup,
        operand->symbol_ref.name, sizeof(operand->symbol_ref.name), fact->target_section_index,
        fact->target_offset, target_runtime_address);
    }
  }
  return 1;
}

static int instruction_immediate_operand_is_address_like(const M68kInstructionIR *instruction,
    size_t operand_index) {
  const M68kSimFormMetadata *metadata;
  size_t dest_index;
  uint8_t dest_reg = 0U;
  if (instruction == NULL || operand_index >= instruction->operand_count) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL || operand_index >= 4U) return 0;
  if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_BRANCH_TARGET ||
      metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_COMPUTE_ADDRESS ||
      metadata->operand_result_kinds[operand_index] == M68K_SIM_RESULT_ADDRESS ||
      metadata->operand_result_kinds[operand_index] == M68K_SIM_RESULT_CONTROL_TARGET) {
    return 1;
  }
  if (metadata->source_operand_index != operand_index ||
      metadata->dest_operand_index >= instruction->operand_count ||
      metadata->dest_operand_index >= 4U) {
    return 0;
  }
  dest_index = metadata->dest_operand_index;
  return metadata->operand_result_kinds[dest_index] == M68K_SIM_RESULT_ADDRESS ||
    metadata->operand_result_kinds[dest_index] == M68K_SIM_RESULT_CONTROL_TARGET ||
    operand_address_register_index_local(&instruction->operands[dest_index], &dest_reg);
}

static int instruction_immediate_operand_stores_long_to_memory(const M68kInstructionIR *instruction,
    size_t operand_index) {
  const M68kSimFormMetadata *metadata;
  size_t dest_index;
  uint8_t reg = 0U;
  if (instruction == NULL || operand_index >= instruction->operand_count || instruction->size_suffix != 'l')
    return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL || metadata->source_operand_index != operand_index ||
      metadata->dest_operand_index >= instruction->operand_count || metadata->dest_operand_index >= 4U) {
    return 0;
  }
  dest_index = metadata->dest_operand_index;
  if (operand_is_data_register_local(&instruction->operands[dest_index], &reg) ||
      operand_address_register_index_local(&instruction->operands[dest_index], &reg)) {
    return 0;
  }
  return metadata->operand_access_kinds[dest_index] == M68K_SIM_ACCESS_MEMORY_WRITE;
}

static int attach_existing_materialized_runtime_immediate_symbols(M68kRenderIRPreview *preview,
    const M68kRenderLookup *lookup, size_t section_index, M68kInstructionIR *instruction) {
  size_t operand_index;
  (void)preview;
  if (lookup == NULL || instruction == NULL || section_index >= lookup->section_count) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    uint32_t runtime_address = 0U;
    uint32_t source_offset = 0U;
    if (operand->symbol_ref.has_name ||
        (!instruction_immediate_operand_is_address_like(instruction, operand_index) &&
         !instruction_immediate_operand_stores_long_to_memory(instruction, operand_index)) ||
        !m68k_ir_operand_immediate_value(operand, &runtime_address) ||
        !lookup_materialized_runtime_address_source_offset(lookup, section_index, runtime_address, &source_offset) ||
        !lookup_has_renderable_label(lookup, section_index, source_offset)) {
      continue;
    }
    m68k_ir_symbol_ref_init(&operand->symbol_ref);
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_ABS;
    operand->symbol_ref.has_name = 1U;
    operand->symbol_ref.has_section = 1;
    operand->symbol_ref.section_index = section_index;
    operand->symbol_ref.has_section_offset = 1;
    operand->symbol_ref.section_offset = source_offset;
    operand->symbol_ref.name_is_generated = format_rendered_asm_label_with_generation(lookup,
      operand->symbol_ref.name, sizeof(operand->symbol_ref.name), section_index, source_offset);
  }
  return 1;
}

/* Address-value facts identify the immediate that produced a typed pointer,
 * even when lossless register or storage transfers separate it from the typed
 * destination. Rendering consumes source analysis and attaches a symbol only
 * to that producer; it never rewrites an intervening register transfer. */
static void attach_planned_address_value_source_symbols(const M68kRenderLookup *lookup,
    const M68kSourceAnalysisIR *source_analysis, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  size_t section_index, index;
  uint32_t immediate_value;
  if (lookup == NULL || source_analysis == NULL || section == NULL || candidate == NULL || instruction == NULL)
    return;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *analysis_section = &source_analysis->sections[section_index];
    for (index = 0U; index < analysis_section->address_value_count; ++index) {
      const M68kAddressValueIR *fact = &analysis_section->address_values[index];
      const M68kAnalysisManualRepresentation *representation;
      if (fact->producer_section_index != section->section_index || fact->producer_offset != candidate->offset ||
          fact->terminal_kind != M68K_ADDRESS_VALUE_TERMINAL_RESOLVED || fact->has_target == 0U ||
          fact->render_outcome != M68K_ADDRESS_VALUE_RENDER_SYMBOLIC || fact->has_source_expression == 0U ||
          fact->producer_operand_index >= instruction->operand_count ||
          !m68k_ir_operand_immediate_value(&instruction->operands[fact->producer_operand_index], &immediate_value) ||
          immediate_value != fact->source_value) {
        continue;
      }
      representation = lookup_manual_operand_representation(lookup, section->section_index,
        candidate->offset, fact->producer_operand_index);
      /* A value EQU does not consume this automatic source label. Do not leave
       * an unused interior label behind when the final presentation replaces it. */
      if (representation != NULL && representation->style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL &&
          representation->target_equate_index != 0U) continue;
      attach_operand_label_symbol(lookup, instruction, fact->producer_operand_index, section->section_index,
        candidate->offset, fact->target_section_index, fact->target_offset);
    }
  }
}

static int attach_materialized_runtime_code_operand_patch_symbol(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, M68kInstructionIR *instruction,
    size_t operand_index, uint32_t source_offset, uint32_t access_width) {
  uint32_t anchor_offset = 0U;
  int64_t addend;
  if (lookup == NULL || section == NULL || accepted_start == NULL || instruction == NULL ||
      !materialized_runtime_code_operand_patch_anchor_offset(lookup, section, accepted_start, source_offset,
        access_width, &anchor_offset)) {
    return 0;
  }
  if (!lookup_has_renderable_label(lookup, section->section_index, anchor_offset)) return 0;
  addend = (int64_t)(uint64_t)source_offset - (int64_t)(uint64_t)anchor_offset;
  if (addend < INT32_MIN || addend > INT32_MAX) return 0;
  attach_operand_label_addend_symbol(lookup, instruction, operand_index, section->section_index,
    anchor_offset, (int32_t)addend);
  return 1;
}

static int attach_materialized_runtime_absolute_storage_symbols(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const uint8_t *accepted_bytes,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  uint8_t platform_kind = M68K_PLATFORM_BACKEND_UNKNOWN;
  if (lookup == NULL || section == NULL || candidate == NULL || instruction == NULL ||
      section->section_index >= lookup->section_count) {
    return 0;
  }
  if (lookup->object != NULL) platform_kind = lookup->object->platform_backend_kind;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return 1;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    uint32_t runtime_address = 0U;
    uint32_t source_offset = 0U;
    uint32_t access_width = 0U;
    if (operand->symbol_ref.has_name != 0U ||
        !render_absolute_ref_access_kind(metadata->operand_access_kinds[operand_index]) ||
        !operand_absolute_offset_local(operand, &runtime_address)) {
      continue;
    }
    if (platform_facts_v2_address_has_symbolic_owner(platform_kind, runtime_address) ||
        !lookup_materialized_runtime_address_source_offset(lookup, section->section_index, runtime_address,
          &source_offset)) {
      continue;
    }
    access_width = render_instruction_access_width(instruction, metadata->operand_access_kinds[operand_index]);
    if (accepted_byte_range_overlaps(section, accepted_bytes, source_offset, access_width)) {
      if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_WRITE) {
        (void)attach_materialized_runtime_code_operand_patch_symbol(lookup, section, accepted_start, instruction,
          operand_index, source_offset, access_width);
      }
      continue;
    }
    if (!lookup_has_renderable_label(lookup, section->section_index, source_offset)) continue;
    attach_operand_label_symbol(lookup, instruction, operand_index, section->section_index, candidate->offset,
      section->section_index, source_offset);
  }
  return 1;
}

static const M68kAddressObservationIR *source_analysis_absolute_observation_for_operand(
    const M68kSourceAnalysisIR *source_analysis, size_t section_index, uint32_t offset, size_t operand_index,
    uint32_t address, uint8_t access_kind) {
  const M68kSectionAnalysisIR *section_analysis;
  size_t index;
  if (source_analysis == NULL || section_index >= source_analysis->section_count) return NULL;
  section_analysis = &source_analysis->sections[section_index];
  for (index = 0U; index < section_analysis->address_observation_count; ++index) {
    const M68kAddressObservationIR *observation = &section_analysis->address_observations[index];
    if (observation->source != M68K_ADDRESS_OBSERVATION_SOURCE_ABSOLUTE_OPERAND ||
        observation->offset != offset ||
        observation->operand_index != operand_index ||
        observation->has_address == 0U ||
        observation->address != address ||
        observation->access_kind != access_kind ||
        observation->owner_kind != M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY) {
      continue;
    }
    return observation;
  }
  return NULL;
}

static const M68kAnalysisAbsoluteStorageSlot *render_absolute_storage_slot_for_address(
    const M68kRenderLookup *lookup, uint32_t address) {
  uint16_t index;
  if (lookup == NULL || lookup->policy == NULL) return NULL;
  for (index = 0U; index < lookup->policy->absolute_storage_slot_count &&
      index < M68K_ANALYSIS_ABSOLUTE_STORAGE_SLOT_LIMIT; ++index) {
    const M68kAnalysisAbsoluteStorageSlot *slot = &lookup->policy->absolute_storage_slots[index];
    if (slot->address == address && slot->symbol[0] != '\0') return slot;
  }
  return NULL;
}

static int attach_absolute_memory_slot_symbols(M68kRenderIRPreview *preview,
    const M68kRenderLookup *lookup, const M68kSourceAnalysisIR *source_analysis, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (preview == NULL || source_analysis == NULL || section == NULL || candidate == NULL || instruction == NULL)
    return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return 1;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    const M68kAddressObservationIR *observation;
    const M68kAnalysisAbsoluteStorageSlot *declared_slot;
    uint32_t address = 0U;
    uint32_t width;
    if (operand->symbol_ref.has_name != 0U ||
        !render_absolute_ref_access_kind(metadata->operand_access_kinds[operand_index]) ||
        !operand_absolute_offset_local(operand, &address)) {
      continue;
    }
    observation = source_analysis_absolute_observation_for_operand(source_analysis, section->section_index,
      candidate->offset, operand_index, address, metadata->operand_access_kinds[operand_index]);
    if (observation == NULL) continue;
    width = observation->access_width != 0U ? observation->access_width :
      render_instruction_access_width(instruction, metadata->operand_access_kinds[operand_index]);
    declared_slot = render_absolute_storage_slot_for_address(lookup, address);
    if (width == 0U || (address >= 0x10000U && declared_slot == NULL)) {
      continue;
    }
    if (observation->symbol_name == NULL || observation->symbol_name[0] == '\0') continue;
    if (!declare_layout_runtime_symbol(preview, observation->symbol_name, address)) return 0;
    attach_generic_symbol(operand, observation->symbol_name);
    operand->symbol_ref.name_is_generated = (uint8_t)(declared_slot == NULL &&
      observation->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY);
  }
  return 1;
}

static int attach_absolute_memory_address_use_symbols(M68kRenderIRPreview *preview,
    const M68kRenderLookup *lookup, const M68kSourceAnalysisIR *source_analysis, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction, const char *platform_comment,
    const char *instruction_comment) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (preview == NULL || source_analysis == NULL || section == NULL || candidate == NULL || instruction == NULL)
    return 0;
  if (platform_comment != NULL && platform_comment[0] != '\0') return 1;
  if (instruction_comment != NULL && instruction_comment[0] != '\0') return 1;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return 1;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    const M68kAddressObservationIR *observation;
    uint32_t address = 0U;
    if (operand->symbol_ref.has_name != 0U ||
        metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_COMPUTE_ADDRESS ||
        !operand_absolute_offset_local(operand, &address)) {
      continue;
    }
    observation = source_analysis_absolute_observation_for_operand(source_analysis, section->section_index,
      candidate->offset, operand_index, address, metadata->operand_access_kinds[operand_index]);
    if (observation == NULL) continue;
    if (observation->symbol_name == NULL || observation->symbol_name[0] == '\0') continue;
    if (!declare_layout_runtime_symbol(preview, observation->symbol_name, address)) return 0;
    attach_generic_symbol(operand, observation->symbol_name);
    operand->symbol_ref.name_is_generated = (uint8_t)(
      observation->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY &&
      render_absolute_storage_slot_for_address(lookup, address) == NULL);
  }
  return 1;
}

static int attach_vector_address_use_symbols(M68kRenderIRPreview *preview,
    const M68kSourceAnalysisIR *source_analysis, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  size_t operand_index;
  if (preview == NULL || source_analysis == NULL || section == NULL || candidate == NULL || instruction == NULL)
    return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    const M68kPlatformAddressUseIR *use;
    uint32_t address = 0U;
    if (operand->symbol_ref.has_name != 0U || !operand_absolute_offset_local(operand, &address)) continue;
    use = source_analysis_platform_address_use_for_operand(source_analysis, section->section_index,
      candidate->offset, operand_index, address, M68K_PLATFORM_ADDRESS_USE_SHAPE_TRUE_VECTOR_INSTALL);
    if (use == NULL) continue;
    if (use->symbol_name == NULL || use->symbol_name[0] == '\0') continue;
    if (!render_asm_define_m68k_vector_symbol_once(preview, use->symbol_name)) return 0;
    attach_generic_symbol(operand, use->symbol_name);
  }
  return 1;
}

static int pc_relative_target_crosses_runtime_org(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset, uint32_t target_offset) {
  size_t index;
  uint32_t low, high;
  if (lookup == NULL || lookup->runtime_address_ranges == NULL || source_offset == target_offset) return 0;
  if (source_offset < target_offset) {
    low = source_offset;
    high = target_offset;
  } else {
    low = target_offset;
    high = source_offset;
  }
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *range = lookup->runtime_address_ranges[index].fact;
    if (range == NULL || range->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
        range->section_index != section_index || !range->has_runtime_address ||
        range->runtime_address == range->offset || !runtime_range_is_materialized(lookup, range)) {
      continue;
    }
    if (range->offset > low && range->offset <= high) return 1;
  }
  return 0;
}

static void mark_cross_org_pc_relative_displacement_exprs(M68kRenderLookup *lookup, size_t section_index,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  M68kAsmOperandValue asm_operands[M68K_DECODE_IR_MAX_OPERANDS];
  size_t operand_index;
  if (lookup == NULL || candidate == NULL || instruction == NULL) return;
  if (candidate->operand_count > M68K_DECODE_IR_MAX_OPERANDS) return;
  for (operand_index = 0U; operand_index < candidate->operand_count; ++operand_index) {
    asm_operands[operand_index] = candidate->operands[operand_index];
    asm_operands[operand_index].kind = candidate->operand_kinds[operand_index];
  }
  for (operand_index = 0U; operand_index < instruction->operand_count &&
       operand_index < candidate->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    size_t relative_base;
    int64_t target;
    uint32_t target_runtime_address = 0U;
    if (operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_mode != 7U ||
        operand->value.ea_reg != 2U || operand->symbol_ref.has_name == 0U ||
        operand->symbol_ref.kind != M68K_IR_SYMBOL_REF_PC_REL || operand->symbol_ref.has_section == 0 ||
        operand->symbol_ref.section_index != section_index || candidate->operand_kinds[operand_index] != M68K_ASM_OPERAND_EA ||
        candidate->operands[operand_index].ea_mode != 7U || candidate->operands[operand_index].ea_reg != 2U) {
      continue;
    }
    relative_base = m68k_asm_operand_relative_base_offset(candidate->asm_form_index, asm_operands,
      candidate->operand_count, m68k_decode_candidate_effective_size_suffix(candidate), operand_index, 0);
    target = (int64_t)candidate->offset + (int64_t)relative_base + signed_16(candidate->operands[operand_index].value);
    if (relative_base > UINT32_MAX || target < 0 || target > UINT32_MAX) continue;
    if (!lookup_source_should_render_runtime_label(lookup, section_index, (uint32_t)target,
        &target_runtime_address) || target_runtime_address == (uint32_t)target) {
      continue;
    }
    if (!pc_relative_target_crosses_runtime_org(lookup, section_index, candidate->offset, (uint32_t)target)) continue;
    operand->symbol_ref.name_is_generated = format_storage_asm_label_with_generation(lookup,
      operand->symbol_ref.name, sizeof(operand->symbol_ref.name), section_index, (uint32_t)target);
    operand->symbol_ref.has_section = 1U;
    operand->symbol_ref.section_index = section_index;
    operand->symbol_ref.has_section_offset = 1U;
    operand->symbol_ref.section_offset = (uint32_t)target;
    operand->symbol_ref.render_pc_relative_displacement_expr = 1U;
    operand->symbol_ref.pc_relative_displacement_base_offset = (uint32_t)relative_base;
    render_lookup_mark_storage_label_target_ref(lookup, section_index, (uint32_t)target);
  }
}

static int attach_absolute_stack_top_symbol(M68kRenderIRPreview *preview, M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  uint8_t source_index;
  uint8_t dest_index;
  uint8_t dest_reg = 0U;
  uint32_t value = 0U;
  char symbol[80];
  if (preview == NULL || instruction == NULL) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL || instruction->operand_count == 0U) return 0;
  if (metadata->operation_type != M68K_SIM_OP_MOVE &&
      metadata->operation_class != M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS) {
    return 0;
  }
  source_index = metadata->source_operand_index;
  dest_index = metadata->dest_operand_index;
  if (source_index >= instruction->operand_count || dest_index >= instruction->operand_count) return 0;
  if (metadata->operand_access_kinds[dest_index] != M68K_SIM_ACCESS_REGISTER_WRITE ||
      !operand_address_register_index_local(&instruction->operands[dest_index], &dest_reg) || dest_reg != 7U ||
      instruction->operands[source_index].symbol_ref.has_name != 0U) {
    return 0;
  }
  if (!m68k_ir_operand_immediate_value(&instruction->operands[source_index], &value) &&
      !operand_absolute_offset_local(&instruction->operands[source_index], &value)) {
    return 0;
  }
  if (value == 0U || platform_facts_v2_address_has_symbolic_owner(preview->platform_backend_kind, value)) {
    return 0;
  }
  if (!render_asm_define_runtime_address_symbol_once(preview, "stack_top", value, symbol, sizeof(symbol)))
    return 0;
  attach_generic_symbol(&instruction->operands[source_index], symbol);
  return 1;
}

static int instruction_relocation_is_proven_operand(const M68kRenderLookup *lookup, size_t source_section_index,
    const M68kDecodeCandidate *candidate, const M68kFact *relocation, M68kInstructionIR *instruction) {
  size_t target_index;
  if (lookup == NULL || candidate == NULL || relocation == NULL || instruction == NULL) return 0;
  if (!lookup_has_renderable_label(lookup, relocation->target_section_index, relocation->target_offset)) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    M68kOperandIR *operand;
    uint32_t absolute = 0U;
    uint32_t runtime_address = 0U;
    if (target->has_operand == 0U || target->operand_index >= instruction->operand_count) continue;
    if (!target_matches_relocation(target, relocation)) continue;
    operand = &instruction->operands[target->operand_index];
    if (operand_absolute_offset_local(operand, &absolute) && absolute == relocation->target_offset &&
        lookup_source_should_render_runtime_label(lookup, relocation->target_section_index,
          relocation->target_offset, &runtime_address)) {
      attach_operand_storage_label_symbol(lookup, instruction, target->operand_index,
        relocation->target_section_index, relocation->target_offset);
    } else {
      attach_operand_label_symbol(lookup, instruction, target->operand_index, source_section_index,
        candidate->offset, relocation->target_section_index, relocation->target_offset);
    }
    return 1;
  }
  {
    size_t operand_index = 0U;
    M68kOperandIR *operand;
    uint32_t absolute = 0U;
    uint32_t runtime_address = 0U;
    if (find_unique_relocation_operand(candidate, relocation, &operand_index) &&
        operand_index < instruction->operand_count) {
      operand = &instruction->operands[operand_index];
      if (operand_absolute_offset_local(operand, &absolute) && absolute == relocation->target_offset &&
          lookup_source_should_render_runtime_label(lookup, relocation->target_section_index,
            relocation->target_offset, &runtime_address)) {
        attach_operand_storage_label_symbol(lookup, instruction, operand_index, relocation->target_section_index,
          relocation->target_offset);
      } else {
        attach_operand_label_symbol(lookup, instruction, operand_index, source_section_index, candidate->offset,
          relocation->target_section_index, relocation->target_offset);
      }
      return 1;
    }
  }
  return 0;
}

static int attach_proven_instruction_relocations(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    size_t section_index, const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  uint32_t offset;
  uint32_t end;
  int ok = 1;
  if (preview == NULL || lookup == NULL || candidate == NULL || instruction == NULL) return 0;
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset; offset < end; ++offset) {
    const M68kFact *fact = lookup_relocation_at(lookup, section_index, offset);
    if (fact == NULL) continue;
    if (!instruction_relocation_is_proven_operand(lookup, section_index, candidate, fact, instruction)) {
      ++preview->asm_source_instruction_relocation_failures;
      record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_INSTRUCTION_RELOCATION,
        section_index, candidate->offset, fact->offset);
      ok = 0;
    }
  }
  return ok;
}

static const M68kFact *first_anchor_in_candidate(const M68kRenderLookup *lookup, size_t section_index,
    const M68kDecodeCandidate *candidate, uint32_t *out_count) {
  uint32_t offset;
  uint32_t end;
  const M68kFact *first = NULL;
  uint32_t count = 0U;
  if (out_count != NULL) *out_count = 0U;
  if (lookup == NULL || candidate == NULL) return NULL;
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset; offset < end; ++offset) {
    const M68kFact *anchor = lookup_anchor_at(lookup, section_index, offset);
    if (anchor == NULL) continue;
    if (first == NULL) first = anchor;
    ++count;
  }
  if (out_count != NULL) *out_count = count;
  return first;
}

static int amiga_vector_is_open_library_result(const AmigaOsLibraryVectorInfo *vector) {
  if (vector == NULL) return 0;
  return vector->function_id == AMIGA_OS_FUNCTION_ID_OPENLIBRARY ||
    vector->function_id == AMIGA_OS_FUNCTION_ID_OLDOPENLIBRARY;
}

static void platform_state_update_known_library_load_after_candidate(M68kRenderPlatformState *platform_state,
    const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate) {
  uint8_t loaded_address_reg = 0U;
  char loaded_library_name[64];
  if (platform_state == NULL || lookup == NULL || section == NULL || candidate == NULL) return;
  if (candidate_lea_known_amiga_name_to_address_reg(lookup, section, candidate, &loaded_address_reg,
      loaded_library_name, sizeof(loaded_library_name))) {
    platform_state_set_register_library(platform_state, loaded_address_reg, loaded_library_name);
  }
}

static int plan_rendered_instruction_symbol_accesses(M68kRenderIRPreview *preview,
    M68kRenderLookup *lookup, size_t section_index, const M68kDecodeCandidate *candidate,
    const M68kSourceAnalysisIR *source_analysis, const M68kInstructionIR *instruction,
    uint8_t rendered_operand_symbol_mask,
    M68kRenderPlannedInstruction *out_planned_instruction);
static const M68kDecodeTarget *candidate_data_target_for_operand(const M68kDecodeCandidate *candidate,
    size_t operand_index);
static void attach_source_analysis_static_interior_expression_symbols(const M68kRenderLookup *lookup,
    const M68kSourceAnalysisIR *source_analysis, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction);
static void attach_source_analysis_indexed_table_expression_symbols(const M68kRenderLookup *lookup,
    const M68kSourceAnalysisIR *source_analysis, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction);

/* This is the planning counterpart of instruction emission.  It deliberately
 * follows the accepted-candidate walk, including platform-state transitions,
 * rather than deriving source obligations from analysis-wide fact arrays. */
static int plan_rendered_instruction_expressions(M68kRenderIRPreview *preview, M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, const M68kAnalysisPolicy *policy, uint8_t **accepted_start_all,
    uint8_t **accepted_bytes, const M68kSourceAnalysisIR *source_analysis) {
  M68kRenderPlatformState platform_state;
  M68kRenderIRPreview metric_baseline;
  size_t section_index;
  if (preview == NULL || lookup == NULL || decode == NULL || accepted_start_all == NULL ||
      accepted_bytes == NULL || source_analysis == NULL) return -1;
  metric_baseline = *preview;
  memset(&platform_state, 0, sizeof(platform_state));
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    uint32_t offset = 0U;
    uint32_t render_extent = render_section_extent(section);
    while (offset < render_extent) {
      const M68kDecodeCandidate *candidate;
      M68kInstructionIR instruction;
      M68kInstructionIR render_instruction;
      M68kRenderAmigaVectorResolution vector_resolution;
      M68kRenderPolicy render_policy;
      M68kDiagList diagnostics;
      M68kIrRenderResult rendered;
      M68kRenderPlannedInstruction planned_instruction;
      char platform_comment[160];
      if (!accepted_start_at(section, accepted_start_all[section_index], offset)) {
        ++offset;
        continue;
      }
      candidate = find_candidate_at_offset_local(section, offset);
      if (candidate == NULL || candidate->byte_count == 0U) {
        ++offset;
        continue;
      }
      platform_state_apply_policy_register_seeds(&platform_state, policy, section->section_index, offset);
      platform_comment[0] = '\0';
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
          attach_symbolic_targets(lookup, section->section_index, section, accepted_start_all[section_index],
            accepted_bytes[section_index], candidate, &instruction) != 0) {
        offset += candidate->byte_count;
        continue;
      }
      if (!attach_proven_instruction_relocations(preview, lookup, section->section_index, candidate,
            &instruction) ||
          attach_platform_semantic_operand_expr_for_render(preview, source_analysis, section->section_index,
            candidate->offset, &instruction) < 0) {
        offset += candidate->byte_count;
        continue;
      }
      (void)attach_absolute_word_control_symbols(lookup, section->section_index, candidate, &instruction);
      (void)attach_platform_pc_relative_section_anchor_symbols(lookup, section->section_index, candidate,
        &instruction);
      attach_source_analysis_static_interior_expression_symbols(lookup, source_analysis, section, candidate,
        &instruction);
      attach_source_analysis_indexed_table_expression_symbols(lookup, source_analysis, section, candidate,
        &instruction);
      if (!attach_amiga_loadseg_segment_link_slot_symbol(preview, lookup, section, accepted_start_all[section_index],
            candidate, &instruction) ||
          !attach_runtime_address_ref_symbols(preview, lookup, source_analysis, section, accepted_bytes[section_index],
            candidate, &instruction) ||
          !attach_existing_materialized_runtime_immediate_symbols(preview, lookup, section->section_index,
            &instruction)) return -1;
      attach_planned_address_value_source_symbols(lookup, source_analysis, section, candidate, &instruction);
      if (!attach_materialized_runtime_absolute_storage_symbols(lookup, section, accepted_start_all[section_index],
            accepted_bytes[section_index], candidate, &instruction) ||
          !attach_absolute_memory_slot_symbols(preview, lookup, source_analysis, section, candidate, &instruction)) {
        return -1;
      }
      m68k_analysis_render_lookup_resolve_amiga_instruction_platform_vectors(lookup, &platform_state, decode,
        accepted_start_all, section, accepted_start_all[section_index], candidate, &instruction, &vector_resolution);
      (void)attach_platform_semantic_target_operand_for_render(lookup, source_analysis, section->section_index,
        candidate->offset, &instruction);
      (void)attach_platform_semantic_note_comment_for_render(source_analysis, lookup, section->section_index,
        candidate->offset, platform_comment, sizeof(platform_comment));
      (void)attach_amiga_hardware_register_symbols(&platform_state, source_analysis, section, candidate,
        &instruction, &instruction);
      (void)attach_absolute_stack_top_symbol(preview, &instruction);
      if (!attach_absolute_memory_address_use_symbols(preview, lookup, source_analysis, section, candidate, &instruction,
            platform_comment, lookup_instruction_comment(lookup, section->section_index, candidate->offset)) ||
          !attach_vector_address_use_symbols(preview, source_analysis, section, candidate, &instruction)) return -1;
      (void)attach_amiga_app_base_slot_symbols(lookup, &platform_state, section->section_index, candidate->offset,
        &instruction);
      (void)attach_amiga_typed_struct_field_symbols(lookup, section->section_index, candidate->offset, &instruction);
      if (apply_manual_operand_representations(lookup, section->section_index, candidate->offset, &instruction) != 0) return -1;
      if (!render_asm_include_for_instruction_platform_symbols(preview, &instruction)) return -1;
      apply_exact_byte_immediate_render_values(&instruction, section->data + candidate->offset, candidate->byte_count);
      if (!instruction_has_noncanonical_byte_immediate_extension(&instruction, section->data + candidate->offset,
            candidate->byte_count)) {
        mark_cross_org_pc_relative_displacement_exprs(lookup, section->section_index, candidate, &instruction);
        render_instruction = instruction;
        uint8_t variant_bytes[2]={0};int has_variant=0;
        if(preview->bootstrap_forward_disjoint && section->section_index==0 &&
            candidate->offset==preview->bootstrap_contract->comparison_source_offset) {
          uint8_t is_address0=0,is_address1=0,reg0=0,reg1=0;
          if(candidate->byte_count!=2 || instruction.operand_count!=2 ||
              !m68k_instruction_operand_direct_register(&instruction.operands[0],&is_address0,&reg0) ||
              !m68k_instruction_operand_direct_register(&instruction.operands[1],&is_address1,&reg1) ||
              !is_address0 || !is_address1 || reg0==reg1) {
            preview->memory_layout.reason="bootstrap_comparison_requires_two_address_registers";return -1;
          }
          if(instruction.operands[0].kind==M68K_ASM_OPERAND_EA) instruction.operands[0].value.ea_reg=reg1;
          else instruction.operands[0].value.reg=reg1;
          if(instruction.operands[1].kind==M68K_ASM_OPERAND_EA) instruction.operands[1].value.ea_reg=reg0;
          else instruction.operands[1].value.reg=reg0;
          m68k_diag_list_reset(&diagnostics);
          M68kIrEncodeResult encoded=m68k_ir_encode_one(&instruction,variant_bytes,sizeof(variant_bytes),m68k_diag_sink(&diagnostics));
          if(m68k_diag_has_errors(&diagnostics) || encoded.byte_count!=2 ||
              !memcmp(variant_bytes,section->data+candidate->offset,2)) {
            preview->memory_layout.reason="bootstrap_variant_encoding_refused";return -1;
          }
          render_instruction=instruction;has_variant=1;
        }
        if (m68k_instruction_is_fpu_id_alias_instruction(&instruction) &&
            !m68k_instruction_make_fpu_id_render_instruction(&instruction, &render_instruction)) return -1;
        m68k_render_policy_init_default(&render_policy);
        m68k_diag_list_reset(&diagnostics);
        rendered = m68k_ir_render_one_at_with_policy(&render_instruction, candidate->offset, &render_policy,
          m68k_diag_sink(&diagnostics));
        memset(&planned_instruction, 0, sizeof(planned_instruction));
        planned_instruction.source_section_index = (uint32_t)section->section_index;
        planned_instruction.source_offset = candidate->offset;
        planned_instruction.has_bootstrap_variant=(uint8_t)has_variant;
        memcpy(planned_instruction.bootstrap_variant_bytes,variant_bytes,2);
        planned_instruction.rendered_operand_symbol_mask = rendered.rendered_operand_symbol_mask;
        planned_instruction.instruction = instruction;
        planned_instruction.render_instruction = render_instruction;
        (void)append_comment_part_local(planned_instruction.comment, sizeof(planned_instruction.comment),
          lookup_instruction_comment(lookup, section->section_index, candidate->offset));
        (void)append_comment_part_local(planned_instruction.comment, sizeof(planned_instruction.comment),
          platform_comment);
        if (m68k_diag_has_errors(&diagnostics) || rendered.text[0] == '\0' ||
            plan_rendered_instruction_symbol_accesses(preview, lookup, section->section_index, candidate,
              source_analysis, &render_instruction, rendered.rendered_operand_symbol_mask,
              &planned_instruction) != 0)
          return -1;
        if (m68k_render_plan_append_instruction(&preview->asm_source_plan, &planned_instruction) != 0 ||
            (preview->precomputing_planned_evidence &&
             record_planned_instruction_symbol_accesses(preview, planned_instruction.source_section_index,
               &planned_instruction) != 0))
          return -1;
      } else {
        memset(&planned_instruction, 0, sizeof(planned_instruction));
        planned_instruction.source_section_index = (uint32_t)section->section_index;
        planned_instruction.source_offset = candidate->offset;
        planned_instruction.has_noncanonical_byte_immediate = 1U;
        planned_instruction.instruction = instruction;
        planned_instruction.render_instruction = instruction;
        (void)append_comment_part_local(planned_instruction.comment, sizeof(planned_instruction.comment),
          lookup_instruction_comment(lookup, section->section_index, candidate->offset));
        (void)append_comment_part_local(planned_instruction.comment, sizeof(planned_instruction.comment),
          platform_comment);
        if (m68k_render_plan_append_instruction(&preview->asm_source_plan, &planned_instruction) != 0 ||
            (preview->precomputing_planned_evidence &&
             record_planned_instruction_symbol_accesses(preview, planned_instruction.source_section_index,
               &planned_instruction) != 0)) return -1;
      }
      platform_state_update_data_lvo_after_instruction(&platform_state, &instruction);
      platform_state_update_after_instruction(&platform_state, lookup, &instruction);
      platform_state_update_known_library_load_after_candidate(&platform_state, lookup, section, candidate);
      if (instruction_has_call_flow(&instruction))
        platform_state_note_call_result_after_instruction(&platform_state, &instruction, vector_resolution.chosen_vector);
      offset += candidate->byte_count;
    }
  }
  preview->asm_source_instruction_render_failures = metric_baseline.asm_source_instruction_render_failures;
  preview->asm_source_instruction_relocation_failures = metric_baseline.asm_source_instruction_relocation_failures;
  preview->asm_source_first_failure_kind = metric_baseline.asm_source_first_failure_kind;
  preview->asm_source_first_failure_section = metric_baseline.asm_source_first_failure_section;
  preview->asm_source_first_failure_offset = metric_baseline.asm_source_first_failure_offset;
  preview->asm_source_first_failure_aux_offset = metric_baseline.asm_source_first_failure_aux_offset;
  preview->asm_source_allocation_failed = metric_baseline.asm_source_allocation_failed;
  return 0;
}

/* A static interior reference is established by source analysis: one
 * structured-data owner, a strict interior target, and a signed addend. */
static void attach_source_analysis_static_interior_expression_symbols(const M68kRenderLookup *lookup,
    const M68kSourceAnalysisIR *source_analysis, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  const M68kSectionAnalysisIR *analysis_section;
  size_t index;
  if (lookup == NULL || source_analysis == NULL || section == NULL || candidate == NULL || instruction == NULL)
    return;
  analysis_section = source_analysis_section_for_render(source_analysis, section->section_index);
  if (analysis_section == NULL) return;
  for (index = 0U; index < analysis_section->address_expression_count; ++index) {
    const M68kAddressExpressionIR *expression = &analysis_section->address_expressions[index];
    const M68kDecodeTarget *target;
    M68kOperandIR *operand;
    int64_t resolved_target;
    if (expression->kind != M68K_ADDRESS_EXPRESSION_STATIC_INTERIOR ||
        expression->consumer_section_index != section->section_index ||
        expression->consumer_offset != candidate->offset ||
        expression->operand_index >= instruction->operand_count ||
        expression->base_section_index != section->section_index) continue;
    operand = &instruction->operands[expression->operand_index];
    if ((operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) ||
        operand->value.ea_mode != 7U || operand->value.ea_reg != 2U) continue;
    target = candidate_data_target_for_operand(candidate, expression->operand_index);
    resolved_target = (int64_t)expression->base_offset + (int64_t)expression->signed_addend;
    if (target == NULL || !target->has_section || target->section_index != section->section_index ||
        resolved_target < 0 || resolved_target > UINT32_MAX || target->offset != (uint32_t)resolved_target) continue;
    attach_operand_label_addend_symbol(lookup, instruction, expression->operand_index,
      expression->base_section_index, expression->base_offset, expression->signed_addend);
  }
}

/* The table descriptor remains the owner of bounds and index-domain proof.
 * This only turns its already canonical indexed expression into the operand's
 * source label; it does not select or enumerate a table entry. */
static void attach_source_analysis_indexed_table_expression_symbols(const M68kRenderLookup *lookup,
    const M68kSourceAnalysisIR *source_analysis, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  const M68kSectionAnalysisIR *analysis_section;
  size_t index;
  if (lookup == NULL || source_analysis == NULL || section == NULL || candidate == NULL || instruction == NULL)
    return;
  analysis_section = source_analysis_section_for_render(source_analysis, section->section_index);
  if (analysis_section == NULL) return;
  for (index = 0U; index < analysis_section->address_expression_count; ++index) {
    const M68kAddressExpressionIR *expression = &analysis_section->address_expressions[index];
    const M68kDecodeTarget *target;
    M68kOperandIR *operand;
    int64_t resolved_base;
    if (expression->kind != M68K_ADDRESS_EXPRESSION_INDEXED_TABLE ||
        expression->consumer_section_index != section->section_index ||
        expression->consumer_offset != candidate->offset ||
        expression->operand_index >= instruction->operand_count ||
        expression->base_section_index != section->section_index || expression->has_index_register == 0U) continue;
    operand = &instruction->operands[expression->operand_index];
    if ((operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) ||
        operand->value.ea_mode != 7U || operand->value.ea_reg != 3U ||
        operand->value.index_is_address !=
          (expression->index_register_kind == M68K_ANALYSIS_REGISTER_ADDRESS ? 1U : 0U) ||
        operand->value.index_reg != expression->index_register ||
        (operand->value.scale != 0U ? operand->value.scale : 1U) != expression->index_scale) continue;
    target = candidate_data_target_for_operand(candidate, expression->operand_index);
    resolved_base = (int64_t)expression->base_offset + (int64_t)expression->signed_addend;
    if (target == NULL || !target->has_section || target->section_index != section->section_index ||
        resolved_base < 0 || resolved_base > UINT32_MAX || target->offset != (uint32_t)resolved_base) continue;
    attach_operand_label_symbol(lookup, instruction, expression->operand_index, section->section_index,
      candidate->offset, expression->base_section_index, expression->base_offset);
  }
}

static int render_asm_instruction(M68kRenderIRPreview *preview, M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    M68kInstructionIR *out_listing_instruction) {
  M68kInstructionIR instruction;
  M68kInstructionIR render_instruction;
  M68kRenderPolicy policy;
  M68kDiagList render_diagnostics;
  M68kDiagList encode_diagnostics;
  M68kIrRenderResult rendered;
  M68kIrEncodeResult encoded;
  const M68kRenderPlannedInstruction *planned_instruction;
  uint8_t encoded_bytes[32];
  const uint8_t *expected_bytes;
  char instruction_comment[640];
  char line[1024];
  if (preview == NULL || lookup == NULL || section == NULL || candidate == NULL) return 0;
  planned_instruction = m68k_render_plan_find_instruction(&preview->asm_source_plan,
    (uint32_t)section->section_index, candidate->offset);
  if (planned_instruction == NULL) {
    uint32_t source_offset;
    for (source_offset = candidate->offset; source_offset < candidate->offset + candidate->byte_count;
        ++source_offset) {
      const M68kFact *relocation = lookup_relocation_at(lookup, section->section_index, source_offset);
      if (relocation == NULL) continue;
      ++preview->asm_source_instruction_relocation_failures;
      record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_INSTRUCTION_RELOCATION,
        section->section_index, candidate->offset, relocation->offset);
      return 0;
    }
    ++preview->asm_source_instruction_render_failures;
    record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, section->section_index,
      candidate->offset, 0U);
    return 0;
  }
  instruction = planned_instruction->instruction;
  expected_bytes=planned_instruction->has_bootstrap_variant ?
    planned_instruction->bootstrap_variant_bytes : section->data+candidate->offset;
  render_instruction = planned_instruction->render_instruction;
  snprintf(instruction_comment, sizeof(instruction_comment), "%s", planned_instruction->comment);
  if (planned_instruction->has_noncanonical_byte_immediate != 0U) {
    if (format_raw_instruction_words(line, sizeof(line), section->data + candidate->offset,
          candidate->byte_count) != 0) {
      ++preview->asm_source_instruction_render_failures;
      record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, section->section_index,
        candidate->offset, 0U);
      return 0;
    }
    {
      char raw_line[1200];
      if (instruction_comment[0] != '\0')
        snprintf(raw_line, sizeof(raw_line), "\t%s\t; non-canonical byte-immediate encoding; %s\n", line,
          instruction_comment);
      else
        snprintf(raw_line, sizeof(raw_line), "\t%s\t; non-canonical byte-immediate encoding\n", line);
      snprintf(line, sizeof(line), "%s", raw_line);
    }
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
    return 1;
  }
  m68k_render_policy_init_default(&policy);
  m68k_diag_list_reset(&render_diagnostics);
  rendered = m68k_ir_render_one_at_with_policy(&render_instruction, candidate->offset, &policy,
    m68k_diag_sink(&render_diagnostics));
  if (m68k_diag_has_errors(&render_diagnostics) || rendered.text[0] == '\0') {
    ++preview->asm_source_instruction_render_failures;
    record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER, section->section_index,
      candidate->offset, 0U);
    return 0;
  }
  m68k_diag_list_reset(&encode_diagnostics);
  encoded = m68k_ir_encode_one(&instruction, encoded_bytes, sizeof(encoded_bytes), m68k_diag_sink(&encode_diagnostics));
  if (m68k_diag_has_errors(&encode_diagnostics) || encoded.byte_count != candidate->byte_count ||
      !encoded_bytes_match_with_exact_byte_immediates(&instruction, encoded_bytes, expected_bytes,
        candidate->byte_count)) {
    ++preview->asm_source_instruction_byte_mismatches;
    record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_BYTE_MISMATCH, section->section_index,
      candidate->offset, 0U);
    return 0;
  }
  if (!rendered_text_reencodes_original_bytes(rendered.text, &instruction, &render_instruction, expected_bytes,
      candidate->byte_count)) {
    ++preview->asm_source_instruction_byte_mismatches;
    record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_BYTE_MISMATCH, section->section_index,
      candidate->offset, 0U);
    return 0;
  }
  {
    uint32_t anchor_count = 0U;
    const M68kFact *anchor = first_anchor_in_candidate(lookup, section->section_index, candidate, &anchor_count);
    if (anchor != NULL) {
      char comment[384];
      format_lossy_hunk_anchor_comment(comment, sizeof(comment), lookup, anchor);
      if (anchor_count > 1U) {
        char count_suffix[64];
        snprintf(count_suffix, sizeof(count_suffix), "; %u lossy hunk relocations in instruction",
          (unsigned)anchor_count);
        strncat(comment, count_suffix, sizeof(comment) - strlen(comment) - 1U);
      }
      if (instruction_comment[0] != '\0') {
        snprintf(line, sizeof(line), "\t%s\t; %s; %s\n", rendered.text, instruction_comment, comment);
      } else {
        snprintf(line, sizeof(line), "\t%s\t; %s\n", rendered.text, comment);
      }
      preview->asm_source_lossy_numeric_hunk_relocations += anchor_count;
    } else if (instruction_comment[0] != '\0') {
      snprintf(line, sizeof(line), "\t%s\t; %s\n", rendered.text, instruction_comment);
    } else {
      snprintf(line, sizeof(line), "\t%s\n", rendered.text);
    }
    if (m68k_instruction_needs_fpu_id_directive(&instruction)) {
      char scoped_line[1200];
      snprintf(scoped_line, sizeof(scoped_line), "\tFPU     %u\n%s\tFPU     1\n",
        (unsigned)instruction.coprocessor_id, line);
      snprintf(line, sizeof(line), "%s", scoped_line);
      preview->asm_source_lines += 2U;
    }
  }
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  ++preview->asm_source_symbolic_instructions;
  /* Emit evidence from the frozen plan only after this exact instruction
   * representation has passed the byte-preservation gate. */
  if (record_planned_instruction_symbol_accesses(preview, section->section_index,
        planned_instruction) != 0) {
    ++preview->asm_source_instruction_render_failures;
    record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_RENDER,
      section->section_index, candidate->offset, 0U);
    return 0;
  }
  if (out_listing_instruction != NULL) *out_listing_instruction = render_instruction;
  return 1;
}

static int decode_target_is_control_symbol_access(const M68kDecodeTarget *target) {
  return target != NULL &&
    (target->kind == M68K_DECODE_TARGET_BRANCH ||
     target->kind == M68K_DECODE_TARGET_CALL ||
     target->kind == M68K_DECODE_TARGET_JUMP);
}

static const M68kDecodeTarget *candidate_control_target_for_operand(const M68kDecodeCandidate *candidate,
    size_t operand_index) {
  size_t target_index;
  const M68kDecodeTarget *unique_unindexed_target = NULL;
  size_t unique_unindexed_count = 0U;
  if (candidate == NULL) return NULL;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (!decode_target_is_control_symbol_access(target) || !target->has_section) continue;
    if (target->has_operand) {
      if (target->operand_index == operand_index) return target;
      continue;
    }
    unique_unindexed_target = target;
    ++unique_unindexed_count;
  }
  return unique_unindexed_count == 1U ? unique_unindexed_target : NULL;
}

static const M68kDecodeTarget *candidate_data_target_for_operand(const M68kDecodeCandidate *candidate,
    size_t operand_index) {
  size_t target_index;
  const M68kDecodeTarget *unique_unindexed_target = NULL;
  size_t unique_unindexed_count = 0U;
  if (candidate == NULL) return NULL;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind != M68K_DECODE_TARGET_DATA || !target->has_section) continue;
    if (target->has_operand) {
      if (target->operand_index == operand_index) return target;
      continue;
    }
    unique_unindexed_target = target;
    ++unique_unindexed_count;
  }
  return unique_unindexed_count == 1U ? unique_unindexed_target : NULL;
}

static const M68kFact *candidate_relocation_for_operand(const M68kRenderLookup *lookup, size_t section_index,
    const M68kDecodeCandidate *candidate, size_t operand_index) {
  const M68kFact *match = NULL;
  uint32_t offset;
  uint32_t end;
  if (lookup == NULL || candidate == NULL) return NULL;
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset; offset < end; ++offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section_index, offset);
    size_t relocated_operand_index = 0U;
    size_t target_index;
    int operand_matches_relocation = 0;
    if (relocation == NULL) continue;
    for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
      const M68kDecodeTarget *target = &candidate->targets[target_index];
      if (target->has_operand != 0U && target->operand_index == operand_index &&
          target_matches_relocation(target, relocation)) {
        operand_matches_relocation = 1;
        break;
      }
    }
    if (!operand_matches_relocation &&
        (!find_unique_relocation_operand(candidate, relocation, &relocated_operand_index) ||
         relocated_operand_index != operand_index)) {
      continue;
    }
    if (match != NULL) return NULL;
    match = relocation;
  }
  return match;
}

static const M68kAddressValueIR *source_analysis_address_value_for_producer(
    const M68kSourceAnalysisIR *source_analysis, size_t producer_section_index, uint32_t producer_offset,
    uint32_t producer_operand_index, size_t *out_section_index) {
  size_t section_index, value_index;
  if (out_section_index != NULL) *out_section_index = SIZE_MAX;
  if (source_analysis == NULL) return NULL;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    for (value_index = 0U; value_index < section->address_value_count; ++value_index) {
      const M68kAddressValueIR *value = &section->address_values[value_index];
      if (value->producer_section_index == producer_section_index && value->producer_offset == producer_offset &&
          value->producer_operand_index == producer_operand_index &&
          value->render_outcome == M68K_ADDRESS_VALUE_RENDER_SYMBOLIC) {
        if (out_section_index != NULL) *out_section_index = section_index;
        return value;
      }
    }
  }
  return NULL;
}

static const M68kAddressExpressionIR *source_analysis_address_expression_for_consumer(
    const M68kSourceAnalysisIR *source_analysis, size_t consumer_section_index, uint32_t consumer_offset,
    uint32_t operand_index, size_t *out_section_index) {
  const M68kSectionAnalysisIR *section;
  size_t index;
  if (out_section_index != NULL) *out_section_index = SIZE_MAX;
  if (source_analysis == NULL) return NULL;
  section = source_analysis_section_for_render(source_analysis, consumer_section_index);
  if (section == NULL) return NULL;
  for (index = 0U; index < section->address_expression_count; ++index) {
    const M68kAddressExpressionIR *expression = &section->address_expressions[index];
    if (expression->consumer_section_index == consumer_section_index &&
        expression->consumer_offset == consumer_offset && expression->operand_index == operand_index) {
      if (out_section_index != NULL) *out_section_index = section->section_index;
      return expression;
    }
  }
  return NULL;
}

static const M68kAddressValueIR *source_analysis_address_value_for_table_origin(
    const M68kSourceAnalysisIR *source_analysis, uint32_t consumer_section_index,
    uint32_t consumer_offset, uint32_t address_expression_id, size_t *out_section_index) {
  size_t section_index, value_index;
  const M68kAddressValueIR *match = NULL;
  if (out_section_index != NULL) *out_section_index = SIZE_MAX;
  if (source_analysis == NULL || address_expression_id == 0U) return NULL;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    for (value_index = 0U; value_index < section->address_value_count; ++value_index) {
      const M68kAddressValueIR *value = &section->address_values[value_index];
      if (value->table_origin.has_origin == 0U ||
          value->table_origin.consumer_section_index != consumer_section_index ||
          value->table_origin.consumer_offset != consumer_offset ||
          value->table_origin.address_expression_id != address_expression_id ||
          value->render_outcome != M68K_ADDRESS_VALUE_RENDER_SYMBOLIC ||
          value->has_source_expression == 0U) continue;
      if (match != NULL) return NULL;
      match = value;
      if (out_section_index != NULL) *out_section_index = section_index;
    }
  }
  return match;
}

static int source_analysis_address_value_has_consumer(const M68kSectionAnalysisIR *section,
    const M68kAddressValueIR *value) {
  size_t consumer_index;
  if (section == NULL || value == NULL || value->id == 0U) return 0;
  for (consumer_index = 0U; consumer_index < section->address_value_consumer_count; ++consumer_index) {
    if (section->address_value_consumers[consumer_index].address_value_id == value->id) return 1;
  }
  return 0;
}

static const M68kAddressValueIR *source_analysis_address_value_by_id(
    const M68kSourceAnalysisIR *source_analysis, uint32_t section_index, uint32_t id) {
  const M68kSectionAnalysisIR *section;
  size_t value_index;
  if (source_analysis == NULL || section_index >= source_analysis->section_count || id == 0U) return NULL;
  section = &source_analysis->sections[section_index];
  for (value_index = 0U; value_index < section->address_value_count; ++value_index) {
    if (section->address_values[value_index].id == id) return &section->address_values[value_index];
  }
  return NULL;
}

static int validate_planned_address_value_expressions(M68kRenderIRPreview *preview,
    const M68kSourceAnalysisIR *source_analysis) {
  size_t section_index, value_index, expression_index;
  if (preview == NULL || source_analysis == NULL) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    for (value_index = 0U; value_index < section->address_value_count; ++value_index) {
      const M68kAddressValueIR *value = &section->address_values[value_index];
      int found = 0;
      if ((value->render_outcome == M68K_ADDRESS_VALUE_RENDER_INVALID && value->has_source_expression != 0U) ||
          (value->render_outcome == M68K_ADDRESS_VALUE_RENDER_SYMBOLIC &&
           !source_analysis_address_value_has_consumer(section, value))) {
        ++preview->asm_source_instruction_render_failures;
        record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_ADDRESS_VALUE,
          value->producer_section_index, value->producer_offset, value->source_value);
        return 0;
      }
      if (value->render_outcome != M68K_ADDRESS_VALUE_RENDER_SYMBOLIC) continue;
      for (expression_index = 0U; expression_index < preview->asm_source_plan.expression_count;
          ++expression_index) {
        const M68kRenderPlannedExpression *expression = &preview->asm_source_plan.expressions[expression_index];
        if (expression->outcome == M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC &&
            expression->has_address_value != 0U) {
          const M68kAddressValueIR *planned_value = source_analysis_address_value_by_id(source_analysis,
            expression->address_value_section_index, expression->address_value_id);
          if ((value->table_origin.has_origin != 0U && planned_value == value) ||
              (value->table_origin.has_origin == 0U && planned_value != NULL &&
               planned_value->producer_section_index == value->producer_section_index &&
               planned_value->producer_offset == value->producer_offset &&
               planned_value->producer_operand_index == value->producer_operand_index)) {
            found = 1;
            break;
          }
        }
      }
      if (!found) {
        ++preview->asm_source_instruction_render_failures;
        record_source_export_failure(preview, M68K_SOURCE_EXPORT_FAILURE_ADDRESS_VALUE,
          value->producer_section_index, value->producer_offset, value->source_value);
        return 0;
      }
    }
  }
  return 1;
}

static int append_rendered_instruction_expression(M68kRenderIRPreview *preview, size_t source_section_index,
    const M68kDecodeCandidate *candidate, const M68kSourceAnalysisIR *source_analysis,
    const M68kRenderedSymbolAccessIR *access, int is_relocation) {
  M68kRenderPlannedExpression expression;
  const M68kAddressValueIR *address_value;
  const M68kAddressExpressionIR *address_expression;
  if (preview == NULL || candidate == NULL || access == NULL || access->symbol_name == NULL ||
      access->symbol_name[0] == '\0') {
    return -1;
  }
  memset(&expression, 0, sizeof(expression));
  expression.source_section_index = (uint32_t)source_section_index;
  expression.source_offset = candidate->offset;
  expression.operand_index = access->operand_index;
  expression.kind = is_relocation ? M68K_RENDER_PLANNED_EXPRESSION_RELOCATION :
    M68K_RENDER_PLANNED_EXPRESSION_INSTRUCTION_OPERAND;
  expression.outcome = M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC;
  {
    size_t address_value_section_index = SIZE_MAX;
    address_value = source_analysis_address_value_for_producer(source_analysis, source_section_index,
      candidate->offset, access->operand_index, &address_value_section_index);
    if (address_value != NULL) {
      expression.address_value_section_index = (uint32_t)address_value_section_index;
      expression.address_value_id = address_value->id;
      expression.has_address_value = 1U;
    }
  }
  snprintf(expression.expression, sizeof(expression.expression), "%s", access->symbol_name);
  if (access->has_target != 0U) {
    expression.target_section_index = access->target_section_index;
    expression.target_offset = access->target_offset;
    expression.has_target = 1U;
    expression.requires_declaration = access->access_kind != M68K_RENDERED_SYMBOL_ACCESS_EQUATE;
    snprintf(expression.target_symbol, sizeof(expression.target_symbol), "%s", access->symbol_name);
  }
  {
    size_t address_expression_section_index = SIZE_MAX;
    address_expression = source_analysis_address_expression_for_consumer(source_analysis, source_section_index,
      candidate->offset, access->operand_index, &address_expression_section_index);
    if (address_expression != NULL) {
      expression.address_expression_section_index = (uint32_t)address_expression_section_index;
      expression.address_expression_id = address_expression->id;
      expression.has_address_expression = 1U;
    }
  }
  if (address_expression != NULL && address_expression->kind == M68K_ADDRESS_EXPRESSION_INDEXED_TABLE) {
    size_t table_value_section_index = SIZE_MAX;
    const M68kAddressValueIR *table_value = source_analysis_address_value_for_table_origin(source_analysis,
      address_expression->consumer_section_index, address_expression->consumer_offset,
      address_expression->id, &table_value_section_index);
    if (table_value != NULL) {
      expression.address_value_section_index = (uint32_t)table_value_section_index;
      expression.address_value_id = table_value->id;
      expression.has_address_value = 1U;
    }
  }
  if (address_expression != NULL && address_expression->kind == M68K_ADDRESS_EXPRESSION_STATIC_INTERIOR &&
      expression.has_target != 0U && expression.target_section_index == address_expression->base_section_index) {
    int64_t resolved_target = (int64_t)address_expression->base_offset + (int64_t)address_expression->signed_addend;
    if (resolved_target >= 0 && resolved_target <= UINT32_MAX && expression.target_offset == (uint32_t)resolved_target) {
      expression.base_section_index = address_expression->base_section_index;
      expression.base_offset = address_expression->base_offset;
      expression.addend = address_expression->signed_addend;
      expression.has_base_target = 1U;
      expression.has_base_addend = 1U;
    }
  }
  return m68k_render_plan_append_expression(&preview->asm_source_plan, &expression);
}

static int source_analysis_has_platform_operand_expression(const M68kSourceAnalysisIR *source_analysis,
    size_t section_index, uint32_t offset, size_t operand_index, const char *symbol_name) {
  const M68kSectionAnalysisIR *section;
  size_t index;
  if (source_analysis == NULL || symbol_name == NULL || symbol_name[0] == '\0') return 0;
  section = source_analysis_section_for_render(source_analysis, section_index);
  if (section == NULL) return 0;
  for (index = 0U; index < section->platform_semantic_use_count; ++index) {
    const M68kPlatformSemanticUseIR *use = &section->platform_semantic_uses[index];
    if (use->offset == offset && use->has_operand_expr != 0U &&
        use->operand_index == operand_index && use->operand_expr != NULL &&
        strcmp(use->operand_expr, symbol_name) == 0) return 1;
  }
  return 0;
}

static int plan_rendered_instruction_symbol_accesses(M68kRenderIRPreview *preview,
    M68kRenderLookup *lookup, size_t section_index, const M68kDecodeCandidate *candidate,
    const M68kSourceAnalysisIR *source_analysis, const M68kInstructionIR *instruction,
    uint8_t rendered_operand_symbol_mask,
    M68kRenderPlannedInstruction *out_planned_instruction) {
  size_t operand_index;
  if (candidate == NULL || instruction == NULL) return 0;
  /* The frozen operand representation is the render-plan contract. The
   * renderer's mask is telemetry, not authority for analysis expressions. */
  (void)rendered_operand_symbol_mask;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    const M68kDecodeTarget *control_target;
    const M68kDecodeTarget *data_target;
    const M68kAnalysisManualRepresentation *representation;
    const M68kFact *relocation;
    const M68kFact *runtime_ref;
    M68kRenderedSymbolAccessIR access;
    if (!operand->symbol_ref.has_name || operand->symbol_ref.name[0] == '\0') continue;
    memset(&access, 0, sizeof(access));
    access.symbol_name = (char *)operand->symbol_ref.name;
    access.offset = candidate->offset;
    access.operand_index = (uint32_t)operand_index;
    access.access_kind = M68K_RENDERED_SYMBOL_ACCESS_OPERAND;
    if ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
        (operand->value.ea_mode == 2U ||
         m68k_instruction_operand_decoded_ea_shape(operand) == M68K_SIM_EA_SHAPE_POSTINCREMENT ||
         m68k_instruction_operand_decoded_ea_shape(operand) == M68K_SIM_EA_SHAPE_PREDECREMENT)) {
      access.comment_only = 1U;
      if (out_planned_instruction != NULL) {
        char field_comment[512];
        snprintf(field_comment, sizeof(field_comment), "operand %u: %s at %s(a%u)%s",
          (unsigned)operand_index + 1U, operand->symbol_ref.name,
          m68k_instruction_operand_decoded_ea_shape(operand) == M68K_SIM_EA_SHAPE_PREDECREMENT ? "-" : "",
          (unsigned)operand->value.ea_reg,
          m68k_instruction_operand_decoded_ea_shape(operand) == M68K_SIM_EA_SHAPE_POSTINCREMENT ? "+" : "");
        if (append_comment_part_local(out_planned_instruction->comment,
            sizeof(out_planned_instruction->comment), field_comment) == 0) return -1;
      }
    }
    if (asm_source_symbol_is_declared_equate(preview, operand->symbol_ref.name) ||
        source_analysis_has_platform_operand_expression(source_analysis, section_index, candidate->offset,
          operand_index, operand->symbol_ref.name)) {
      access.access_kind = M68K_RENDERED_SYMBOL_ACCESS_EQUATE;
    }
    representation = lookup_manual_operand_representation(lookup, section_index, candidate->offset, operand_index);
    if (access.access_kind != M68K_RENDERED_SYMBOL_ACCESS_EQUATE && representation != NULL &&
        representation->style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL &&
        representation->target_equate_index != 0U) {
      access.access_kind = M68K_RENDERED_SYMBOL_ACCESS_EQUATE;
    }
    /* An EQU is a value identity, not a source-address assertion. In
     * particular, runtime-only scratch aliases must not inherit the decoder's
     * coincident numeric file offset from a suppressed load view. */
    relocation = NULL;
    if (access.access_kind != M68K_RENDERED_SYMBOL_ACCESS_EQUATE) {
      relocation = candidate_relocation_for_operand(lookup, section_index, candidate, operand_index);
      control_target = candidate_control_target_for_operand(candidate, operand_index);
      if (control_target != NULL) {
        access.access_kind = M68K_RENDERED_SYMBOL_ACCESS_BRANCH_TARGET;
        /* The attached operand has already resolved the execution view. Decode
         * targets retain their original coordinates and must not re-project an
         * encoded absolute address as a source offset in copied images. */
        if (operand->symbol_ref.has_section && operand->symbol_ref.has_section_offset &&
            operand->symbol_ref.section_index <= UINT32_MAX) {
          access.target_section_index = (uint32_t)operand->symbol_ref.section_index;
          access.target_offset = operand->symbol_ref.section_offset;
        } else if (relocation != NULL && relocation->target_section_index <= UINT32_MAX) {
          access.target_section_index = (uint32_t)relocation->target_section_index;
          access.target_offset = relocation->target_offset;
        } else {
          access.target_section_index = (uint32_t)control_target->section_index;
          access.target_offset = control_target->offset;
        }
        access.has_target = 1U;
      } else {
        data_target = candidate_data_target_for_operand(candidate, operand_index);
        if (data_target != NULL && data_target->section_index <= UINT32_MAX) {
          access.target_section_index = (uint32_t)data_target->section_index;
          access.target_offset = data_target->offset;
          access.has_target = 1U;
        }
        if (!access.has_target && relocation != NULL && relocation->target_section_index <= UINT32_MAX) {
          access.target_section_index = (uint32_t)relocation->target_section_index;
          access.target_offset = relocation->target_offset;
          access.has_target = 1U;
        }
      }
      if (!access.has_target && operand->symbol_ref.has_section && operand->symbol_ref.has_section_offset &&
          operand->symbol_ref.section_index <= UINT32_MAX) {
        access.target_section_index = (uint32_t)operand->symbol_ref.section_index;
        access.target_offset = operand->symbol_ref.section_offset;
        access.has_target = 1U;
      }
      runtime_ref = lookup_runtime_address_ref_for_operand(lookup, section_index, candidate->offset, operand_index);
      if (!access.has_target && runtime_ref != NULL && runtime_ref->target_section_index <= UINT32_MAX) {
        access.target_section_index = (uint32_t)runtime_ref->target_section_index;
        access.target_offset = runtime_ref->target_offset;
        access.has_target = 1U;
      }
    }
    if (append_rendered_instruction_expression(preview, section_index, candidate, source_analysis,
        &access, relocation != NULL) != 0)
      return -1;
    if (out_planned_instruction != NULL) {
      size_t access_index = out_planned_instruction->symbol_access_count;
      if (access_index >= sizeof(out_planned_instruction->symbol_accesses) /
          sizeof(out_planned_instruction->symbol_accesses[0])) return -1;
      out_planned_instruction->symbol_accesses[access_index].target_section_index = access.target_section_index;
      out_planned_instruction->symbol_accesses[access_index].target_offset = access.target_offset;
      out_planned_instruction->symbol_accesses[access_index].operand_index = access.operand_index;
      out_planned_instruction->symbol_accesses[access_index].access_kind = access.access_kind;
      out_planned_instruction->symbol_accesses[access_index].has_target = access.has_target;
      out_planned_instruction->symbol_accesses[access_index].comment_only = access.comment_only;
      snprintf(out_planned_instruction->symbol_accesses[access_index].symbol_name,
        sizeof(out_planned_instruction->symbol_accesses[access_index].symbol_name), "%s", access.symbol_name);
      ++out_planned_instruction->symbol_access_count;
    }
  }
  return 0;
}

void m68k_render_ir_preview_init(M68kRenderIRPreview *preview) {
  if (preview == NULL) return;
  memset(preview, 0, sizeof(*preview));
  preview->structural_hash = 1469598103934665603ULL;
  preview->text_hash = 1469598103934665603ULL;
  preview->asm_source_hash = 1469598103934665603ULL;
  preview->render_evidence = (M68kRenderEvidenceIR *)malloc(sizeof(*preview->render_evidence));
  if (preview->render_evidence != NULL &&
      m68k_ir_render_evidence_create(preview->render_evidence) != 0) {
    free(preview->render_evidence);
    preview->render_evidence = NULL;
  }
  m68k_render_plan_init(&preview->asm_source_plan);
  m68k_render_plan_init(&preview->asm_source_rows);
  m68k_render_plan_row_builder_init(&preview->asm_source_row_builder);
}

void m68k_render_ir_preview_destroy(M68kRenderIRPreview *preview) {
  if (preview == NULL) return;
  arena_destroy(preview->scratch_arena);
  if (preview->render_evidence != NULL) {
    m68k_ir_render_evidence_destroy(preview->render_evidence);
    free(preview->render_evidence);
  }
  m68k_render_plan_free_text(preview->asm_source_text);
  m68k_render_plan_row_builder_destroy(&preview->asm_source_row_builder);
  m68k_render_plan_destroy(&preview->asm_source_rows);
  m68k_render_plan_destroy(&preview->asm_source_plan);
  memset(preview, 0, sizeof(*preview));
}

static int prepare_layout_bootstrap(M68kRenderIRPreview *preview,const M68kDecodeIR *decode,
    const M68kSourceAnalysisIR *analysis,const M68kMemoryLayoutIR *layout) {
  if(!layout->bootstrap_contract_id[0]) return 0;
  const M68kAnalysisPolicy *policy=preview->analysis_policy;
  const M68kBootstrapContractIR *c=NULL;int image=-1;
  for(size_t i=0;i<policy->bootstrap_contract_count;i++)
    if(!strcmp(layout->bootstrap_contract_id,policy->bootstrap_contracts[i].contract_id)) c=&policy->bootstrap_contracts[i];
#define BOOT_REFUSE(reason_text) do {preview->memory_layout.reason=reason_text;return -1;} while(0)
  if(!c || !analysis || decode->section_count!=1 || analysis->section_count!=1)
    BOOT_REFUSE("bootstrap_requires_one_identity_bound_raw_section");
  const M68kDecodeSectionIR *section=&decode->sections[0];char digest[65];
  if(section->size!=c->file_size || m68k_platform_sha256_hex(section->data,section->size,digest) || strcmp(digest,c->input_sha256))
    BOOT_REFUSE("bootstrap_input_identity_mismatch");
  for(size_t i=0;i<policy->memory_region_count;i++)
    if(!strcmp(c->image_region_id,policy->memory_regions[i].region_id)) image=(int)i;
  if(image<0 || !policy->memory_regions[image].source_mapped || policy->memory_regions[image].region_kind!=1 ||
      policy->memory_regions[image].size!=c->copied_source_end || preview->memory_layout.parents[image]>=0)
    BOOT_REFUSE("bootstrap_image_extent_mismatch");
  if((uint64_t)c->load_address+c->file_size>layout->chip_bytes ||
      (uint64_t)c->helper_runtime_address+c->helper_source_end-c->helper_source_start>c->load_address)
    BOOT_REFUSE("bootstrap_loader_or_helper_bounds");
  int image_view=0,helper_view=0;
  for(size_t i=0;i<analysis->sections[0].runtime_view_count;i++) {
    const M68kRuntimeViewIR *view=&analysis->sections[0].runtime_views[i];
    if(view->materialized && view->storage_offset==0 && view->size==c->copied_source_end &&
        view->runtime_address==policy->memory_regions[image].runtime_address) image_view=1;
    /* A copied helper may be suppressed as a separate source ORG because its
     * bytes are already rendered in the image. That is not suppression of the
     * actual copy/execution. Bind its exact view and input identity separately. */
    if(view->storage_offset==c->helper_source_start && view->size==c->helper_source_end-c->helper_source_start &&
        view->runtime_address==c->helper_runtime_address) helper_view=1;
  }
  if(!image_view || !helper_view) BOOT_REFUSE("bootstrap_materialized_views_mismatch");
  uint32_t placed=preview->memory_layout.addresses[image];
  int moved=placed!=policy->memory_regions[image].runtime_address;
  if(moved && !layout->bootstrap_forward_disjoint) BOOT_REFUSE("bootstrap_move_requires_reviewed_direction_variant");
  if(layout->bootstrap_forward_disjoint && (!moved || placed<(uint64_t)c->load_address+c->file_size))
    BOOT_REFUSE("bootstrap_forward_variant_requires_disjoint_high_destination");
  preview->bootstrap_contract=c;
  preview->bootstrap_forward_disjoint=layout->bootstrap_forward_disjoint;
#undef BOOT_REFUSE
  return 0;
}

int m68k_render_ir_preview_emit_prepared(const M68kObject *object, const M68kDecodeIR *decode,
    M68kRenderLookup *lookup, const M68kAnalysisPolicy *policy, uint8_t **accepted_start,
    uint8_t **accepted_bytes, int render_text_preview, int render_asm_source, int collect_asm_source_text,
    int emit_asm_source_text, M68kRenderIRPreview *out_preview, const M68kSourceAnalysisIR *source_analysis) {
  size_t section_index;
  clock_t phase_start;
  clock_t phase_end;
  int result = -1;
  if (object == NULL || decode == NULL || lookup == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || out_preview == NULL)
    return -1;
  if (render_asm_source && source_analysis == NULL) return -1;
  if (render_asm_source && out_preview->render_evidence == NULL) return -1;
  out_preview->platform_backend_kind = object->platform_backend_kind;
  out_preview->analysis_policy = policy;
  if(policy && policy->selected_memory_layout_id[0]) {
    const M68kMemoryLayoutIR *layout=NULL;
    for(size_t i=0;i<policy->memory_layout_count;i++)
      if(!strcmp(policy->memory_layouts[i].layout_id,policy->selected_memory_layout_id)) layout=&policy->memory_layouts[i];
    if(!layout || m68k_memory_layout_resolve(policy,layout,&out_preview->memory_layout)) return -1;
    out_preview->memory_layout_enabled=1;
    if(prepare_layout_bootstrap(out_preview,decode,source_analysis,layout)) return -1;
    if(m68k_memory_layout_validate_source(policy,&out_preview->memory_layout,source_analysis)) return -1;
  }
  out_preview->collect_asm_source_text = render_asm_source && collect_asm_source_text ? 1U : 0U;
  out_preview->collect_asm_source_hash = out_preview->collect_asm_source_text;
  phase_start = clock();
  if (render_asm_source) {
    /* Semantic planning owns the complete rendered-symbol evidence.  The
     * planner's identities are unique, so avoid rediscovering them during the
     * later forward row walk. */
    out_preview->precomputing_planned_evidence = out_preview->prepared_sink != NULL ? 1U : 0U;
    /* Concrete data renderers create labels only for expressions selected by
     * the same ownership walk that emits the body.  Semantic pointer facts
     * alone never create source labels or source-reference obligations. */
    if (plan_rendered_structured_pointer_expressions(lookup, decode, accepted_start, accepted_bytes,
        source_analysis, &out_preview->asm_source_plan) != 0) {
      goto cleanup;
    }
    if (plan_rendered_instruction_expressions(out_preview, lookup, decode, policy, accepted_start,
        accepted_bytes, source_analysis) != 0) goto cleanup;
    if(out_preview->bootstrap_forward_disjoint) {
      const M68kRenderPlannedInstruction *comparison=m68k_render_plan_find_instruction(
        &out_preview->asm_source_plan,0,out_preview->bootstrap_contract->comparison_source_offset);
      if(!comparison || !comparison->has_bootstrap_variant) {
        out_preview->memory_layout.reason="bootstrap_comparison_not_an_admitted_instruction";goto cleanup;
      }
    }
    if (derive_rendered_pointer_declarations(out_preview, lookup) != 0) goto cleanup;
    if (plan_rendered_label_statements(out_preview, lookup, decode, accepted_start,
          &out_preview->asm_source_plan) != 0) goto cleanup;
    if (plan_rendered_runtime_aliases(out_preview, lookup, &out_preview->asm_source_plan) != 0) goto cleanup;
    if (plan_rendered_copper_equate_expressions(out_preview, lookup, decode, accepted_bytes,
          source_analysis) != 0) goto cleanup;
    if (out_preview->precomputing_planned_evidence) {
      out_preview->precomputing_planned_evidence = 0U;
      m68k_ir_render_evidence_sort_source_order(out_preview->render_evidence);
      out_preview->planned_evidence_precomputed = 1U;
    }
    if (out_preview->prepared_sink != NULL &&
        out_preview->prepared_sink(out_preview, out_preview->prepared_sink_user) != 0) {
      goto cleanup;
    }
    /* The normal random-access assembly hoists this late diagnostic while
     * finalizing its row plan.  A transient sink cannot retain body rows for
     * that final pass, so emit it before every other preamble row instead. */
    if (out_preview->transient_row_sink != NULL) {
      begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_DIAGNOSTIC, 0U);
      if (render_asm_os_compatibility_summary_row(out_preview, source_analysis,
          object->platform_backend_kind) != 0) {
        cancel_asm_source_plan_row(out_preview);
        goto cleanup;
      }
      finish_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_NO_SECTION, 0U, 0U, 0);
    }
    begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_DIAGNOSTIC, 0U);
    render_asm_memory_map_header(out_preview, lookup, decode, source_analysis);
    finish_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_NO_SECTION, 0U, 0U, 0);
    begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_PLATFORM_DIRECTIVE, 0U);
    render_asm_platform_header(out_preview, object);
    finish_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_NO_SECTION, 0U, 0U, 0);
    begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_RSSET, 0U);
    render_asm_base_layout_rs(out_preview, lookup, decode);
    finish_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_NO_SECTION, 0U, 0U, 0);
    if (!render_asm_declare_target_equates(out_preview, &out_preview->asm_source_plan, policy)) goto cleanup;
    begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_RSSET, 0U);
    if (!render_asm_declare_custom_struct_layouts(out_preview, policy)) {
      cancel_asm_source_plan_row(out_preview);
      goto cleanup;
    }
    finish_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_NO_SECTION, 0U, 0U, 0);
    out_preview->asm_source_body_start_byte = out_preview->asm_source_bytes;
  }
  phase_end = clock();
  out_preview->header_seconds = elapsed_seconds_local(phase_start, phase_end);
  phase_start = clock();
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    uint32_t offset = 0U;
    uint32_t asm_logical_pc = 0U;
    uint32_t render_extent = render_section_extent(section);
    size_t render_candidate_index = 0U;
    out_preview->structural_hash = hash_step(out_preview->structural_hash, section_index);
    out_preview->structural_hash = hash_step(out_preview->structural_hash, render_extent);
    if (render_asm_source) {
      begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_SECTION, (uint32_t)section_index);
      render_asm_section_header(out_preview, decode, section_index);
      finish_asm_source_plan_row(out_preview, section->section_index, 0U, 0U, 1);
    }
    while (offset < render_extent) {
      if (render_asm_source) {
        begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_DIAGNOSTIC, (uint32_t)section_index);
        render_asm_policy_entry_comments(out_preview, policy, section->section_index, offset);
        render_asm_policy_register_seed_comment(out_preview, policy, section->section_index, offset);
        finish_asm_source_plan_row(out_preview, section->section_index, offset, 0U, 1);
      }
      if ((render_asm_source && m68k_render_plan_find_label(&out_preview->asm_source_plan,
            (uint32_t)section->section_index, offset) != NULL) ||
          (!render_asm_source && render_asm_should_emit_label_statement(out_preview, lookup, section,
            accepted_start[section_index], section->section_index, offset))) {
        ++out_preview->statement_count;
        ++out_preview->label_statement_count;
        hash_statement(out_preview, 'L', section->section_index, offset, 0U, 0U);
        if (render_text_preview) render_text_line(out_preview, 'L', section->section_index, offset, 0U, 0U);
          if (render_asm_source) {
            M68kRenderPlanRow *row;
            begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_LABEL, (uint32_t)section_index);
            render_asm_label(out_preview, lookup, section->section_index, offset, &asm_logical_pc);
            row = finish_asm_source_plan_row(out_preview, section->section_index, offset, 0U, 1);
            set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_LABEL, NULL, section, offset, 0U);
          }
      }
      if (accepted_start_at(section, accepted_start[section_index], offset)) {
        const M68kDecodeCandidate *candidate = NULL;
        while (render_candidate_index < section->candidate_count &&
            section->candidates[render_candidate_index].offset < offset) {
          ++render_candidate_index;
        }
        if (render_candidate_index < section->candidate_count &&
            section->candidates[render_candidate_index].offset == offset) {
          candidate = &section->candidates[render_candidate_index];
        }
        if (candidate == NULL || candidate->byte_count == 0U) {
          PlatformFactsV2ResolvedCall call_info;
          uint16_t opcode = section->data != NULL && offset + 2U <= section->size
            ? m68k_read_u16be(section->data + offset) : 0U;
          if (platform_facts_v2_resolve_opcode_call(object->platform_backend_kind, opcode, &call_info) &&
              offset + 2U <= render_extent) {
            ++out_preview->statement_count;
            ++out_preview->data_statement_count;
            hash_statement(out_preview, 'I', section->section_index, offset, 2U, opcode);
            if (render_text_preview) render_text_line(out_preview, 'I', section->section_index, offset, 2U, opcode);
            if (render_asm_source) {
              M68kRenderPlanRow *row;
              begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_DATA, (uint32_t)section_index);
              render_asm_sync_logical_pc(out_preview, lookup, section->section_index, offset, &asm_logical_pc);
              if (!render_asm_platform_opcode_call(out_preview, opcode, &call_info)) {
                render_asm_dc_w_values(out_preview, section->data, offset, 2U, NULL);
              }
              row = finish_asm_source_plan_row(out_preview, section->section_index, offset, 2U, 1);
              set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_DATA, NULL, section, offset, 2U);
              asm_logical_pc += 2U;
            }
            offset += 2U;
            continue;
          }
          goto cleanup;
        }
        ++out_preview->statement_count;
        ++out_preview->instruction_statement_count;
        hash_statement(out_preview, 'I', section->section_index, offset, candidate->byte_count,
          candidate->mnemonic_id);
        if (render_text_preview) render_text_line(out_preview, 'I', section->section_index, offset,
          candidate->byte_count, candidate->mnemonic_id);
        if (render_asm_source) {
          M68kRenderPlanRow *row;
          M68kInstructionIR listing_instruction;
          int rendered_instruction;
          m68k_ir_instruction_init(&listing_instruction);
          begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_INSTRUCTION, (uint32_t)section_index);
          render_asm_sync_logical_pc(out_preview, lookup, section->section_index, offset, &asm_logical_pc);
          rendered_instruction = render_asm_instruction(out_preview, lookup, section, candidate,
            &listing_instruction);
          row = finish_asm_source_plan_row(out_preview, section->section_index, offset, candidate->byte_count, 1);
          if (rendered_instruction) {
            set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_INSTRUCTION, &listing_instruction,
              section, offset, candidate->byte_count);
          }
          asm_logical_pc += candidate->byte_count;
        }
        offset += candidate->byte_count;
      } else {
        const M68kFact *anchor = lookup_anchor_at(lookup, section->section_index, offset);
        const M68kFact *relocation = lookup_relocation_at(lookup, section->section_index, offset);
        if (anchor != NULL && offset + anchor->size <= section->size &&
            !accepted_byte_at(section, accepted_bytes[section_index], offset)) {
          ++out_preview->statement_count;
          ++out_preview->data_statement_count;
          hash_statement(out_preview, 'A', section->section_index, offset, anchor->size,
            (uint32_t)anchor->target_section_index ^ anchor->target_offset);
          if (render_text_preview) render_text_line(out_preview, 'A', section->section_index, offset,
            anchor->size, anchor->target_offset);
          if (render_asm_source) {
            M68kRenderPlanRow *row;
            begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_DATA, (uint32_t)section_index);
            render_asm_sync_logical_pc(out_preview, lookup, section->section_index, offset, &asm_logical_pc);
            render_asm_comment_line(out_preview,
              lookup_instruction_comment(lookup, section->section_index, offset));
            render_asm_hunk_anchor_relocation(out_preview, lookup, anchor);
            row = finish_asm_source_plan_row(out_preview, section->section_index, offset, anchor->size, 1);
            set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_DATA, NULL, section, offset,
              anchor->size);
            asm_logical_pc += anchor->size;
          }
          offset += anchor->size;
        } else if (relocation != NULL && offset + relocation->size <= section->size &&
            !accepted_byte_at(section, accepted_bytes[section_index], offset)) {
          ++out_preview->statement_count;
          ++out_preview->data_statement_count;
          hash_statement(out_preview, 'R', section->section_index, offset, relocation->size,
            (uint32_t)relocation->target_section_index ^ relocation->target_offset);
          if (render_text_preview) render_text_line(out_preview, 'R', section->section_index, offset,
            relocation->size, relocation->target_offset);
          if (render_asm_source) {
            M68kRenderPlanRow *row;
            begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_DATA, (uint32_t)section_index);
            render_asm_sync_logical_pc(out_preview, lookup, section->section_index, offset, &asm_logical_pc);
            render_asm_comment_line(out_preview,
              lookup_instruction_comment(lookup, section->section_index, offset));
            render_asm_relocation_expr(out_preview, lookup, relocation);
            row = finish_asm_source_plan_row(out_preview, section->section_index, offset, relocation->size, 1);
            set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_DATA, NULL, section, offset,
              relocation->size);
            asm_logical_pc += relocation->size;
          }
          offset += relocation->size;
        } else {
          const M68kAnalysisStructuredDataItem *structured_item =
            lookup_structured_data_item_at_offset(lookup, section->section_index, offset);
          int structured_item_clear = structured_data_item_is_render_candidate(lookup, section,
            accepted_bytes[section_index], render_extent, offset, structured_item, &out_preview->asm_source_plan);
          if (structured_item != NULL && structured_item_clear) {
            ++out_preview->statement_count;
            ++out_preview->data_statement_count;
            hash_statement(out_preview, 'S', section->section_index, offset, structured_item->size,
              structured_item->kind);
            if (render_text_preview) render_text_line(out_preview, 'S', section->section_index, offset,
              structured_item->size, structured_item->kind);
            if (render_asm_source) {
              M68kRenderPlanRow *row;
              int structured_item_updated_pc = 0;
              begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_DATA, (uint32_t)section_index);
              render_asm_sync_logical_pc(out_preview, lookup, section->section_index, offset, &asm_logical_pc);
              render_asm_comment_line(out_preview,
                lookup_instruction_comment(lookup, section->section_index, offset));
              render_asm_structured_data_item(out_preview, section, accepted_start[section_index], lookup,
                source_analysis, structured_item, &asm_logical_pc, &structured_item_updated_pc);
              row = finish_asm_source_plan_row(out_preview, section->section_index, offset, structured_item->size,
                1);
              set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_DATA, NULL, section, offset,
                structured_item->size);
              m68k_render_plan_row_set_data_class_flags(row, structured_data_item_role_flags(structured_item));
              if (row != NULL)
                snprintf(row->generated_field_comment, sizeof(row->generated_field_comment), "%s",
                  structured_item->field_name);
              if (!structured_item_updated_pc) asm_logical_pc += structured_item->size;
            }
            offset += structured_item->size;
          } else {
            const M68kRenderStringSpan *string_span =
              lookup_string_span_at_offset(lookup, section->section_index, offset);
            int string_span_clear = string_span != NULL && string_span->size != 0U &&
              string_span->size <= render_extent - offset && offset + string_span->size <= section->size &&
              section->data != NULL && !accepted_byte_at(section, accepted_bytes[section_index], offset);
            if (string_span_clear) {
              uint32_t probe;
              for (probe = offset + 1U; probe < offset + string_span->size; ++probe) {
                if (accepted_byte_at(section, accepted_bytes[section_index], probe) ||
                    lookup_has_render_walk_data_split_boundary(lookup, section->section_index, probe,
                      0, 1, 0, 1) ||
                    (render_asm_source && m68k_render_plan_find_label(&out_preview->asm_source_plan,
                      (uint32_t)section->section_index, probe) != NULL)) {
                  string_span_clear = 0;
                  break;
                }
              }
            }
            if (string_span != NULL && string_span_clear) {
              ++out_preview->statement_count;
              ++out_preview->data_statement_count;
              hash_statement(out_preview, 'D', section->section_index, offset, string_span->size, 0U);
              if (render_text_preview) render_text_line(out_preview, 'D', section->section_index, offset,
                string_span->size, 0U);
              if (render_asm_source) {
                M68kRenderPlanRow *row;
                begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_DATA, (uint32_t)section_index);
                render_asm_sync_logical_pc(out_preview, lookup, section->section_index, offset, &asm_logical_pc);
                render_asm_comment_line(out_preview,
                  lookup_instruction_comment(lookup, section->section_index, offset));
                render_asm_dc_b_string_with_labels(out_preview, section, accepted_start[section_index], lookup,
                  offset, string_span->size, NULL, &asm_logical_pc);
                row = finish_asm_source_plan_row(out_preview, section->section_index, offset, string_span->size, 1);
                set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_DATA, NULL, section, offset,
                  string_span->size);
                m68k_render_plan_row_set_data_class_flags(row, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING);
              }
              offset += string_span->size;
            } else {
              uint32_t start = offset;
              int initialized_span = section->data != NULL && start < section->size;
              while (offset < render_extent &&
                  !accepted_byte_at(section, accepted_bytes[section_index], offset) &&
                  !lookup_has_render_walk_data_split_boundary(lookup, section->section_index, offset,
                    offset != start, offset != start, offset != start, offset != start) &&
                  (!render_asm_source || offset == start || m68k_render_plan_find_label(
                    &out_preview->asm_source_plan, (uint32_t)section->section_index, offset) == NULL) &&
                  ((section->data != NULL && offset < section->size) == initialized_span)) {
                ++offset;
              }
              if (offset == start) ++offset;
              else {
              ++out_preview->statement_count;
              ++out_preview->data_statement_count;
              hash_statement(out_preview, 'D', section->section_index, start, offset - start, 0U);
              if (render_text_preview) render_text_line(out_preview, 'D', section->section_index, start,
                offset - start, 0U);
              if (render_asm_source) {
                M68kRenderPlanRow *row;
                begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_PLATFORM_DIRECTIVE,
                  (uint32_t)section_index);
                render_asm_sync_logical_pc(out_preview, lookup, section->section_index, start, &asm_logical_pc);
                finish_asm_source_plan_row(out_preview, section->section_index, start, 0U, 1);
                begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_DIAGNOSTIC, (uint32_t)section_index);
                render_asm_comment_line(out_preview,
                  lookup_instruction_comment(lookup, section->section_index, start));
                render_platform_semantic_header_comments_for_raw_data(out_preview, source_analysis,
                  section->section_index, start);
                finish_asm_source_plan_row(out_preview, section->section_index, start, 0U, 1);
                if (initialized_span) {
                  char fragment_comment[128];
                  render_asm_data_dc_b_plan_rows(out_preview, lookup, section_index, section, start, offset - start,
                    structured_data_fragment_comment(lookup, section, accepted_bytes[section_index], render_extent,
                      structured_item, start, offset - start, fragment_comment, sizeof(fragment_comment)),
                    &asm_logical_pc);
                } else {
                  begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_RESERVE, (uint32_t)section_index);
                  render_asm_ds_best_fit(out_preview, start, offset - start);
                  row = finish_asm_source_plan_row(out_preview, section->section_index, start, offset - start, 1);
                  set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_RESERVE, NULL, section, start,
                    offset - start);
                }
                asm_logical_pc += offset - start;
              }
              }
            }
          }
        }
      }
    }
    if ((render_asm_source && m68k_render_plan_find_label(&out_preview->asm_source_plan,
          (uint32_t)section->section_index, render_extent) != NULL) ||
        (!render_asm_source && lookup_has_renderable_label(lookup, section->section_index, render_extent))) {
      if (render_asm_source) {
        begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_DIAGNOSTIC, (uint32_t)section_index);
        render_asm_policy_entry_comments(out_preview, policy, section->section_index, render_extent);
        render_asm_policy_register_seed_comment(out_preview, policy, section->section_index, render_extent);
        finish_asm_source_plan_row(out_preview, section->section_index, render_extent, 0U, 1);
      }
      ++out_preview->statement_count;
      ++out_preview->label_statement_count;
      hash_statement(out_preview, 'L', section->section_index, render_extent, 0U, 0U);
      if (render_text_preview) render_text_line(out_preview, 'L', section->section_index, render_extent, 0U, 0U);
      if (render_asm_source) {
        M68kRenderPlanRow *row;
        begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_LABEL, (uint32_t)section_index);
        render_asm_label(out_preview, lookup, section->section_index, render_extent, &asm_logical_pc);
        row = finish_asm_source_plan_row(out_preview, section->section_index, render_extent, 0U, 1);
        set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_LABEL, NULL, section, render_extent,
          0U);
      }
    }
  }
  phase_end = clock();
  out_preview->walk_seconds = elapsed_seconds_local(phase_start, phase_end);
  if (out_preview->asm_source_allocation_failed) goto cleanup;
  if (render_asm_source && collect_asm_source_text && out_preview->transient_row_sink == NULL &&
      render_asm_os_compatibility_summary_row(out_preview, source_analysis,
        object->platform_backend_kind) != 0) {
    out_preview->asm_source_allocation_failed = 1U;
    goto cleanup;
  }
  if (render_asm_source && flush_transient_asm_source_row(out_preview) != 0) {
    out_preview->asm_source_allocation_failed = 1U;
    goto cleanup;
  }
  if (render_asm_source && collect_asm_source_text &&
      !validate_planned_address_value_expressions(out_preview, source_analysis)) {
    out_preview->asm_source_allocation_failed = 1U;
    goto cleanup;
  }
  phase_start = clock();
  /* Semantic declarations, labels, and expression decisions are useful on
   * their own to sequential consumers.  Finalize them even when row text is
   * deliberately not collected; this keeps the no-row semantic product from
   * retaining builder generations. */
  if (render_asm_source &&
      m68k_render_plan_finalize(&out_preview->asm_source_plan) != 0) {
    out_preview->asm_source_allocation_failed = 1U;
    goto cleanup;
  }
  if (render_asm_source && collect_asm_source_text && out_preview->transient_row_sink == NULL &&
      !assemble_asm_source_plan_regions(out_preview, decode, emit_asm_source_text)) {
    out_preview->asm_source_allocation_failed = 1U;
    goto cleanup;
  }
  out_preview->asm_source_plan_rows = (uint32_t)out_preview->asm_source_plan.row_count;
  out_preview->asm_source_plan_lines = out_preview->asm_source_plan.total_lines;
  out_preview->asm_source_plan_bytes = (uint32_t)out_preview->asm_source_plan.total_bytes;
  phase_end = clock();
  out_preview->footer_seconds = elapsed_seconds_local(phase_start, phase_end);
  result = 0;
cleanup:
  out_preview->precomputing_planned_evidence = 0U;
  return result;
}

void m68k_render_ir_preview_set_transient_row_sink(M68kRenderIRPreview *preview,
    M68kRenderTransientRowSink sink, void *user) {
  if (preview == NULL) return;
  preview->transient_row_sink = sink;
  preview->transient_row_sink_user = user;
}

void m68k_render_ir_preview_set_prepared_sink(M68kRenderIRPreview *preview,
    M68kRenderIRPreparedSink sink, void *user) {
  if (preview == NULL) return;
  preview->prepared_sink = sink;
  preview->prepared_sink_user = user;
}
