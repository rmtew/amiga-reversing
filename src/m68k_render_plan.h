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

typedef enum M68kRenderPlannedExpressionKind {
  M68K_RENDER_PLANNED_EXPRESSION_INSTRUCTION_OPERAND = 1,
  M68K_RENDER_PLANNED_EXPRESSION_RELOCATION = 2,
  M68K_RENDER_PLANNED_EXPRESSION_DATA_POINTER = 3,
  M68K_RENDER_PLANNED_EXPRESSION_TABLE_ENTRY = 4,
  M68K_RENDER_PLANNED_EXPRESSION_RELATIVE = 5,
  M68K_RENDER_PLANNED_EXPRESSION_EQUATE = 6
} M68kRenderPlannedExpressionKind;

typedef enum M68kRenderPlannedExpressionOutcome {
  M68K_RENDER_PLANNED_EXPRESSION_SYMBOLIC = 1,
  M68K_RENDER_PLANNED_EXPRESSION_NUMERIC = 2,
  M68K_RENDER_PLANNED_EXPRESSION_INVALID = 3
} M68kRenderPlannedExpressionOutcome;

typedef enum M68kRenderPlannedDeclarationKind {
  M68K_RENDER_PLANNED_DECLARATION_LABEL = 1,
  M68K_RENDER_PLANNED_DECLARATION_EQUATE = 2,
  M68K_RENDER_PLANNED_DECLARATION_LAYOUT = 3,
  M68K_RENDER_PLANNED_DECLARATION_INCLUDE = 4
} M68kRenderPlannedDeclarationKind;

typedef struct M68kRenderPlannedExpression {
  uint32_t source_section_index;
  uint32_t source_offset;
  uint32_t address_value_section_index;
  uint32_t address_value_id;
  uint32_t target_section_index;
  uint32_t target_offset;
  uint32_t base_section_index;
  uint32_t base_offset;
  uint32_t logical_address;
  int32_t addend;
  uint32_t operand_index;
  uint8_t kind;
  uint8_t outcome;
  uint8_t has_target;
  uint8_t has_address_value;
  uint8_t has_base_target;
  uint8_t requires_declaration;
  uint8_t has_relative_key;
  char expression[96];
  char target_symbol[96];
  char base_symbol[96];
  char reason[96];
} M68kRenderPlannedExpression;

typedef struct M68kRenderPlannedDeclaration {
  uint32_t section_index;
  uint32_t offset;
  uint32_t logical_address;
  uint32_t runtime_address;
  uint8_t kind;
  uint8_t has_source_target;
  uint8_t has_runtime_target;
  uint8_t emits_header_text;
  char name[96];
  char expression[96];
} M68kRenderPlannedDeclaration;

typedef struct M68kRenderPlannedSymbolAccess {
  uint32_t target_section_index;
  uint32_t target_offset;
  uint32_t operand_index;
  uint8_t access_kind;
  uint8_t has_target;
  uint8_t comment_only;
  uint8_t reserved;
  char symbol_name[96];
} M68kRenderPlannedSymbolAccess;

typedef struct M68kRenderPlannedInstruction {
  uint32_t source_section_index;
  uint32_t source_offset;
  uint8_t rendered_operand_symbol_mask;
  uint8_t has_noncanonical_byte_immediate;
  uint8_t symbol_access_count;
  uint8_t reserved;
  M68kInstructionIR instruction;
  M68kInstructionIR render_instruction;
  char comment[640];
  M68kRenderPlannedSymbolAccess symbol_accesses[4];
} M68kRenderPlannedInstruction;

typedef struct M68kRenderPlannedLabel {
  uint32_t source_section_index;
  uint32_t source_offset;
  uint32_t runtime_address;
  uint8_t has_runtime_address;
  uint8_t has_storage_label;
  uint8_t reserved[2];
  char name[96];
  char storage_name[96];
} M68kRenderPlannedLabel;

typedef struct M68kRenderPlannedRuntimeAlias {
  uint32_t source_section_index;
  uint32_t source_offset;
  uint32_t runtime_address;
  char name[96];
} M68kRenderPlannedRuntimeAlias;

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
  uint32_t source_line_mask;
  uint32_t source_line_offsets[32];
  uint32_t source_line_sizes[32];
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
  M68kRenderPlannedExpression *expressions;
  size_t expression_count;
  size_t expression_capacity;
  M68kRenderPlannedDeclaration *declarations;
  size_t declaration_count;
  size_t declaration_capacity;
  M68kRenderPlannedInstruction *instructions;
  size_t instruction_count;
  size_t instruction_capacity;
  M68kRenderPlannedLabel *labels;
  size_t label_count;
  size_t label_capacity;
  M68kRenderPlannedRuntimeAlias *runtime_aliases;
  size_t runtime_alias_count;
  size_t runtime_alias_capacity;
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
  uint32_t source_line_mask;
  uint32_t source_line_offsets[32];
  uint32_t source_line_sizes[32];
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
int m68k_render_plan_append_expression(M68kRenderPlan *plan,
  const M68kRenderPlannedExpression *expression);
const M68kRenderPlannedExpression *m68k_render_plan_find_expression(const M68kRenderPlan *plan,
  uint32_t source_section_index, uint32_t source_offset, uint32_t operand_index, uint8_t kind);
int m68k_render_plan_append_declaration(M68kRenderPlan *plan,
  const M68kRenderPlannedDeclaration *declaration);
int m68k_render_plan_append_instruction(M68kRenderPlan *plan,
  const M68kRenderPlannedInstruction *instruction);
const M68kRenderPlannedInstruction *m68k_render_plan_find_instruction(const M68kRenderPlan *plan,
  uint32_t source_section_index, uint32_t source_offset);
int m68k_render_plan_append_label(M68kRenderPlan *plan, const M68kRenderPlannedLabel *label);
const M68kRenderPlannedLabel *m68k_render_plan_find_label(const M68kRenderPlan *plan,
  uint32_t source_section_index, uint32_t source_offset);
int m68k_render_plan_append_runtime_alias(M68kRenderPlan *plan,
  const M68kRenderPlannedRuntimeAlias *runtime_alias);
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
void m68k_render_plan_row_builder_mark_current_line_source_range(M68kRenderPlanRowBuilder *builder,
  uint32_t source_offset, uint32_t source_size);
void m68k_render_plan_row_builder_mark_current_line_label(M68kRenderPlanRowBuilder *builder,
  uint32_t source_offset, uint8_t has_runtime_address, uint32_t runtime_address);
int m68k_render_plan_row_builder_commit(M68kRenderPlanRowBuilder *builder, M68kRenderPlanRow **out_row);
void m68k_render_plan_row_builder_cancel(M68kRenderPlanRowBuilder *builder);
void m68k_render_plan_row_set_source_range(M68kRenderPlanRow *row, uint32_t section_index,
  uint32_t offset, uint32_t size);
void m68k_render_plan_row_mark_source_line_range(M68kRenderPlanRow *row, uint32_t subline,
  uint32_t source_offset, uint32_t source_size);
uint8_t m68k_render_plan_row_source_line_range(const M68kRenderPlanRow *row, uint32_t subline,
  uint32_t *out_source_offset, uint32_t *out_source_size);
void m68k_render_plan_row_set_runtime_range(M68kRenderPlanRow *row, uint32_t address, uint32_t size);
void m68k_render_plan_row_set_statement_metadata(M68kRenderPlanRow *row, uint8_t statement_kind,
  const M68kInstructionIR *instruction, const uint8_t *source_bytes, size_t source_byte_count);
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
