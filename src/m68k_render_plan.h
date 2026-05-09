#ifndef M68K_RENDER_PLAN_H
#define M68K_RENDER_PLAN_H

#include "m68k_diagnostics.h"
#include "m68k_ir.h"

#include <stddef.h>
#include <stdint.h>

#define M68K_RENDER_PLAN_NO_SECTION UINT32_MAX

typedef struct Arena Arena;

typedef enum M68kRenderPlanRowKind {
  M68K_RENDER_PLAN_ROW_INCLUDE = 1,
  M68K_RENDER_PLAN_ROW_BLANK = 2,
  M68K_RENDER_PLAN_ROW_RSSET = 3,
  M68K_RENDER_PLAN_ROW_RS_FIELD = 4,
  M68K_RENDER_PLAN_ROW_EQUATE = 5,
  M68K_RENDER_PLAN_ROW_SECTION = 6,
  M68K_RENDER_PLAN_ROW_ORG = 7,
  M68K_RENDER_PLAN_ROW_LABEL = 8,
  M68K_RENDER_PLAN_ROW_INSTRUCTION = 9,
  M68K_RENDER_PLAN_ROW_DATA = 10,
  M68K_RENDER_PLAN_ROW_RESERVE = 11,
  M68K_RENDER_PLAN_ROW_PLATFORM_DIRECTIVE = 12,
  M68K_RENDER_PLAN_ROW_DIAGNOSTIC = 13
} M68kRenderPlanRowKind;

typedef struct M68kRenderPlanRow {
  uint32_t id;
  uint32_t kind;
  uint32_t region_id;
  uint32_t start_line;
  uint32_t line_count;
  size_t start_byte;
  size_t byte_count;
  uint32_t source_section_index;
  uint32_t source_offset;
  uint32_t source_size;
  uint32_t statement_index;
  uint32_t runtime_address;
  uint32_t runtime_size;
  uint32_t directive_line_mask;
  uint32_t label_line_mask;
  uint32_t label_line_source_offsets[32];
  uint32_t label_line_runtime_mask;
  uint32_t label_line_runtime_addresses[32];
  M68kInstructionIR statement_instruction;
  uint8_t statement_kind;
  uint8_t source_byte_count;
  uint8_t source_bytes[M68K_STATEMENT_SOURCE_BYTES_MAX];
  uint8_t has_source_range;
  uint8_t has_statement;
  uint8_t has_statement_metadata;
  uint8_t has_runtime_range;
  uint8_t reserved[3];
  uint32_t data_class_flags;
  char data_class[32];
  char *text;
} M68kRenderPlanRow;

typedef struct M68kRenderPlan {
  M68kRenderPlanRow *rows;
  Arena *arena;
  size_t row_count;
  size_t row_capacity;
  uint32_t next_row_id;
  uint32_t total_lines;
  size_t total_bytes;
} M68kRenderPlan;

typedef struct M68kRenderPlanRowBuilder {
  M68kRenderPlan *plan;
  char *text;
  size_t size;
  size_t capacity;
  uint32_t kind;
  uint32_t region_id;
  uint32_t current_line;
  uint32_t directive_line_mask;
  uint32_t label_line_mask;
  uint32_t label_line_source_offsets[32];
  uint32_t label_line_runtime_mask;
  uint32_t label_line_runtime_addresses[32];
  uint8_t active;
} M68kRenderPlanRowBuilder;

typedef int (*M68kRenderPlanLineVisitor)(const M68kRenderPlanRow *row, uint32_t subline, uint32_t line,
  const char *line_start, size_t line_length, void *user);

void m68k_render_plan_init(M68kRenderPlan *plan);
void m68k_render_plan_destroy(M68kRenderPlan *plan);
void m68k_render_plan_move(M68kRenderPlan *dest, M68kRenderPlan *src);
int m68k_render_plan_append_text_row(M68kRenderPlan *plan, uint32_t kind, uint32_t region_id,
  const char *text, M68kRenderPlanRow **out_row);
void m68k_render_plan_row_builder_init(M68kRenderPlanRowBuilder *builder);
void m68k_render_plan_row_builder_destroy(M68kRenderPlanRowBuilder *builder);
int m68k_render_plan_row_builder_begin(M68kRenderPlanRowBuilder *builder, M68kRenderPlan *plan,
  uint32_t kind, uint32_t region_id);
int m68k_render_plan_row_builder_append(M68kRenderPlanRowBuilder *builder, const char *text);
int m68k_render_plan_row_builder_append_span(M68kRenderPlanRowBuilder *builder, const char *text, size_t length);
int m68k_render_plan_row_builder_appendf(M68kRenderPlanRowBuilder *builder, const char *format, ...);
void m68k_render_plan_row_builder_mark_current_line_directive(M68kRenderPlanRowBuilder *builder);
void m68k_render_plan_row_builder_mark_current_line_label(M68kRenderPlanRowBuilder *builder,
  uint32_t source_offset, uint8_t has_runtime_address, uint32_t runtime_address);
int m68k_render_plan_row_builder_commit(M68kRenderPlanRowBuilder *builder, M68kRenderPlanRow **out_row);
void m68k_render_plan_row_builder_cancel(M68kRenderPlanRowBuilder *builder);
void m68k_render_plan_row_set_source_range(M68kRenderPlanRow *row, uint32_t section_index,
  uint32_t offset, uint32_t size);
void m68k_render_plan_row_set_runtime_range(M68kRenderPlanRow *row, uint32_t address, uint32_t size);
void m68k_render_plan_row_set_statement_metadata(M68kRenderPlanRow *row, uint8_t statement_kind,
  const M68kInstructionIR *instruction, const uint8_t *source_bytes, size_t source_byte_count);
void m68k_render_plan_row_set_data_class(M68kRenderPlanRow *row, const char *data_class);
void m68k_render_plan_row_set_data_class_flags(M68kRenderPlanRow *row, uint32_t data_class_flags);
const M68kRenderPlanRow *m68k_render_plan_row_at(const M68kRenderPlan *plan, size_t row_index);
const M68kRenderPlanRow *m68k_render_plan_find_row_for_line(const M68kRenderPlan *plan, uint32_t line,
  uint32_t *out_subline);
const M68kRenderPlanRow *m68k_render_plan_find_row_for_source_offset(const M68kRenderPlan *plan,
  uint32_t section_index, uint32_t offset);
const M68kRenderPlanRow *m68k_render_plan_find_row_for_runtime_address(const M68kRenderPlan *plan,
  uint32_t address);
int m68k_render_plan_emit_rows_alloc(const M68kRenderPlan *plan, size_t first_row, size_t row_count,
  char **out_text);
int m68k_render_plan_emit_line_window_alloc(const M68kRenderPlan *plan, uint32_t first_line,
  uint32_t line_count, char **out_text);
int m68k_render_plan_emit_all_alloc(const M68kRenderPlan *plan, char **out_text);
int m68k_render_plan_hoist_header_rows(M68kRenderPlan *plan);
int m68k_render_plan_visit_row_lines(const M68kRenderPlan *plan, size_t first_row, size_t row_count,
  M68kRenderPlanLineVisitor visitor, void *user);
int m68k_render_plan_build_text_lines(const char *text, uint32_t kind, uint32_t region_id,
  M68kRenderPlan *out_plan);
int m68k_render_plan_build_source_file_body(const M68kSourceFileIR *source_file, const M68kRenderPolicy *policy,
  M68kRenderPlan *out_plan, M68kDiagSink diagnostics);
void m68k_render_plan_free_text(char *text);

#endif
