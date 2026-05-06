#include "m68k_c_unit_test.h"
#include "m68k_render_plan.h"

#include <stdio.h>
#include <string.h>

static int test_render_plan_line_counts_and_order(void) {
  M68kRenderPlan plan;
  const M68kRenderPlanRow *row;
  m68k_render_plan_init(&plan);

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_INCLUDE, 1U,
    "\tINCLUDE \"hardware/cia.i\"\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_BLANK, 1U, "\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_RSSET, 2U,
    "\tRSSET 0\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_EQUATE, 3U,
    "_custom EQU $DFF000\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_SECTION, 4U,
    "\tSECTION section_0,code\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_BLANK, 4U, "\n", NULL));

  M68K_C_ASSERT_U32(6U, (uint32_t)plan.row_count);
  M68K_C_ASSERT_U32(6U, plan.total_lines);
  M68K_C_ASSERT_U32(81U, (uint32_t)plan.total_bytes);
  row = m68k_render_plan_row_at(&plan, 4U);
  M68K_C_ASSERT(row != NULL);
  M68K_C_ASSERT_U32(M68K_RENDER_PLAN_ROW_SECTION, row->kind);
  M68K_C_ASSERT_U32(4U, row->start_line);
  M68K_C_ASSERT_U32(1U, row->line_count);
  M68K_C_ASSERT_U32(56U, (uint32_t)row->start_byte);
  M68K_C_ASSERT_U32(24U, (uint32_t)row->byte_count);

  m68k_render_plan_destroy(&plan);
  return 0;
}

static int test_render_plan_line_and_address_lookup(void) {
  M68kRenderPlan plan;
  M68kRenderPlanRow *mutable_row;
  const M68kRenderPlanRow *row;
  uint32_t subline = 99U;
  m68k_render_plan_init(&plan);

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_LABEL, 10U,
    "loc_0_00000000:\n", &mutable_row));
  m68k_render_plan_row_set_source_range(mutable_row, 0U, 0U, 0U);
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_INSTRUCTION, 10U,
    "\tmoveq.l #0,d0\n", &mutable_row));
  m68k_render_plan_row_set_source_range(mutable_row, 0U, 0U, 2U);
  m68k_render_plan_row_set_runtime_range(mutable_row, 0x400U, 2U);
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_DATA, 10U,
    "\tdc.b $01,$02,$03,$04\n\tdc.b $05,$06,$07,$08\n", &mutable_row));
  m68k_render_plan_row_set_source_range(mutable_row, 0U, 2U, 8U);

  row = m68k_render_plan_find_row_for_line(&plan, 2U, &subline);
  M68K_C_ASSERT(row != NULL);
  M68K_C_ASSERT_U32(M68K_RENDER_PLAN_ROW_DATA, row->kind);
  M68K_C_ASSERT_U32(0U, subline);
  row = m68k_render_plan_find_row_for_line(&plan, 3U, &subline);
  M68K_C_ASSERT(row != NULL);
  M68K_C_ASSERT_U32(M68K_RENDER_PLAN_ROW_DATA, row->kind);
  M68K_C_ASSERT_U32(1U, subline);
  M68K_C_ASSERT(m68k_render_plan_find_row_for_line(&plan, 4U, NULL) == NULL);

  row = m68k_render_plan_find_row_for_source_offset(&plan, 0U, 6U);
  M68K_C_ASSERT(row != NULL);
  M68K_C_ASSERT_U32(M68K_RENDER_PLAN_ROW_DATA, row->kind);
  row = m68k_render_plan_find_row_for_runtime_address(&plan, 0x401U);
  M68K_C_ASSERT(row != NULL);
  M68K_C_ASSERT_U32(M68K_RENDER_PLAN_ROW_INSTRUCTION, row->kind);
  M68K_C_ASSERT(m68k_render_plan_find_row_for_runtime_address(&plan, 0x402U) == NULL);

  m68k_render_plan_destroy(&plan);
  return 0;
}

static int test_render_plan_row_builder_commits_fragmented_row(void) {
  M68kRenderPlan plan;
  M68kRenderPlanRowBuilder builder;
  M68kRenderPlanRow *row = NULL;
  char *full_text = NULL;
  m68k_render_plan_init(&plan);
  m68k_render_plan_row_builder_init(&builder);
  M68K_C_ASSERT_INT(0, m68k_render_plan_row_builder_begin(&builder, &plan, M68K_RENDER_PLAN_ROW_INSTRUCTION, 2U));
  M68K_C_ASSERT_INT(0, m68k_render_plan_row_builder_append(&builder, "    moveq.l "));
  M68K_C_ASSERT_INT(0, m68k_render_plan_row_builder_append_span(&builder, "#", 1U));
  M68K_C_ASSERT_INT(0, m68k_render_plan_row_builder_appendf(&builder, "%u,d0\n", 7U));
  M68K_C_ASSERT_INT(0, m68k_render_plan_row_builder_commit(&builder, &row));
  M68K_C_ASSERT(row != NULL);
  M68K_C_ASSERT_U32(M68K_RENDER_PLAN_ROW_INSTRUCTION, row->kind);
  M68K_C_ASSERT_U32(1U, plan.total_lines);
  M68K_C_ASSERT_U32(18U, (uint32_t)plan.total_bytes);
  M68K_C_ASSERT_INT(0, m68k_render_plan_emit_all_alloc(&plan, &full_text));
  M68K_C_ASSERT_STR("    moveq.l #7,d0\n", full_text);
  m68k_render_plan_free_text(full_text);
  m68k_render_plan_row_builder_destroy(&builder);
  m68k_render_plan_destroy(&plan);
  return 0;
}

static int test_render_plan_builds_text_line_rows(void) {
  M68kRenderPlan plan;
  char *full_text = NULL;
  M68K_C_ASSERT_INT(0, m68k_render_plan_build_text_lines("A\nB\n", M68K_RENDER_PLAN_ROW_DIAGNOSTIC, 9U, &plan));
  M68K_C_ASSERT_U32(2U, (uint32_t)plan.row_count);
  M68K_C_ASSERT_U32(2U, plan.total_lines);
  M68K_C_ASSERT_U32(4U, (uint32_t)plan.total_bytes);
  M68K_C_ASSERT_U32(9U, plan.rows[1].region_id);
  M68K_C_ASSERT_INT(0, m68k_render_plan_emit_all_alloc(&plan, &full_text));
  M68K_C_ASSERT_STR("A\nB\n", full_text);
  m68k_render_plan_free_text(full_text);
  m68k_render_plan_destroy(&plan);
  M68K_C_ASSERT_INT(-1, m68k_render_plan_build_text_lines("A\nB", M68K_RENDER_PLAN_ROW_DIAGNOSTIC, 9U, &plan));
  return 0;
}

static int test_render_plan_window_emission_matches_full_slice(void) {
  M68kRenderPlan plan;
  char *full_text = NULL, *window_text = NULL, *line_window_text = NULL;
  const char *expected_full = "A\nB1\nB2\nC\n";
  const char *expected_window = "B1\nB2\n";
  const char *expected_line_window = "B2\nC\n";
  m68k_render_plan_init(&plan);

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_INCLUDE, 1U, "A\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_DATA, 2U, "B1\nB2\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_SECTION, 3U, "C\n", NULL));

  M68K_C_ASSERT_INT(0, m68k_render_plan_emit_all_alloc(&plan, &full_text));
  M68K_C_ASSERT_INT(0, m68k_render_plan_emit_rows_alloc(&plan, 1U, 1U, &window_text));
  M68K_C_ASSERT_INT(0, m68k_render_plan_emit_line_window_alloc(&plan, 2U, 2U, &line_window_text));
  M68K_C_ASSERT_STR(expected_full, full_text);
  M68K_C_ASSERT_STR(expected_window, window_text);
  M68K_C_ASSERT_STR(expected_line_window, line_window_text);
  M68K_C_ASSERT(strstr(full_text, window_text) == full_text + 2U);
  M68K_C_ASSERT(strstr(full_text, line_window_text) == full_text + 5U);

  m68k_render_plan_free_text(full_text);
  m68k_render_plan_free_text(window_text);
  m68k_render_plan_free_text(line_window_text);
  m68k_render_plan_destroy(&plan);
  return 0;
}

typedef struct RenderPlanLineVisitCapture {
  uint32_t count;
  uint32_t lines[4];
  uint32_t sublines[4];
  uint32_t kinds[4];
  char text[64];
} RenderPlanLineVisitCapture;

static int capture_render_plan_line(const M68kRenderPlanRow *row, uint32_t subline, uint32_t line,
    const char *line_start, size_t line_length, void *user) {
  RenderPlanLineVisitCapture *capture = (RenderPlanLineVisitCapture *)user;
  if (capture->count >= 4U) return -1;
  capture->lines[capture->count] = line;
  capture->sublines[capture->count] = subline;
  capture->kinds[capture->count] = row->kind;
  if (strlen(capture->text) + line_length + 1U >= sizeof(capture->text)) return -1;
  strncat(capture->text, line_start, line_length);
  ++capture->count;
  return 0;
}

static int test_render_plan_visits_physical_lines_with_owner_row(void) {
  M68kRenderPlan plan;
  RenderPlanLineVisitCapture capture;
  memset(&capture, 0, sizeof(capture));
  m68k_render_plan_init(&plan);
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_SECTION, 1U, "A\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_DATA, 1U, "B1\nB2\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_visit_row_lines(&plan, 0U, plan.row_count,
    capture_render_plan_line, &capture));
  M68K_C_ASSERT_U32(3U, capture.count);
  M68K_C_ASSERT_U32(0U, capture.lines[0]);
  M68K_C_ASSERT_U32(1U, capture.lines[1]);
  M68K_C_ASSERT_U32(2U, capture.lines[2]);
  M68K_C_ASSERT_U32(0U, capture.sublines[1]);
  M68K_C_ASSERT_U32(1U, capture.sublines[2]);
  M68K_C_ASSERT_U32(M68K_RENDER_PLAN_ROW_DATA, capture.kinds[2]);
  M68K_C_ASSERT_STR("A\nB1\nB2\n", capture.text);
  m68k_render_plan_destroy(&plan);
  return 0;
}

static int test_render_plan_rejects_rows_without_complete_lines(void) {
  M68kRenderPlan plan;
  m68k_render_plan_init(&plan);
  M68K_C_ASSERT_INT(-1, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_INCLUDE, 1U,
    "missing newline", NULL));
  M68K_C_ASSERT_U32(0U, (uint32_t)plan.row_count);
  M68K_C_ASSERT_U32(0U, (uint32_t)plan.total_bytes);
  m68k_render_plan_destroy(&plan);
  return 0;
}

static int test_render_plan_hoists_typed_header_rows(void) {
  M68kRenderPlan plan;
  M68kRenderPlanRow *row = NULL;
  const M68kRenderPlanRow *found = NULL;
  char *full_text = NULL;
  const char *expected =
    "    INCLUDE \"hardware/cia.i\"\n"
    "    INCLUDE \"hardware/custom.i\"\n"
    "    RSSET 0\n"
    "app_0000 RS.L 1\n"
    "_custom EQU $DFF000\n"
    "    SECTION section_0,code\n"
    "loc_0_00000000:\n"
    "\trts\n";
  m68k_render_plan_init(&plan);
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_SECTION, 0U,
    "    SECTION section_0,code\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_LABEL, 0U,
    "loc_0_00000000:\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_INCLUDE, 0U,
    "    INCLUDE \"hardware/custom.i\"\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_EQUATE, 0U,
    "_custom EQU $DFF000\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_INCLUDE, 0U,
    "    INCLUDE \"hardware/cia.i\"\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_RSSET, 0U,
    "    RSSET 0\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_RS_FIELD, 0U,
    "app_0000 RS.L 1\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_INSTRUCTION, 0U,
    "\trts\n", &row));
  m68k_render_plan_row_set_source_range(row, 0U, 0U, 2U);

  M68K_C_ASSERT_INT(0, m68k_render_plan_hoist_header_rows(&plan));
  M68K_C_ASSERT_INT(0, m68k_render_plan_emit_all_alloc(&plan, &full_text));
  M68K_C_ASSERT_STR(expected, full_text);
  M68K_C_ASSERT_U32(0U, plan.rows[0].start_line);
  M68K_C_ASSERT_U32(5U, plan.rows[5].start_line);
  found = m68k_render_plan_find_row_for_source_offset(&plan, 0U, 0U);
  M68K_C_ASSERT(found != NULL);
  M68K_C_ASSERT_U32(M68K_RENDER_PLAN_ROW_INSTRUCTION, found->kind);

  m68k_render_plan_free_text(full_text);
  m68k_render_plan_destroy(&plan);
  return 0;
}

static int test_render_plan_move_transfers_arena_owned_rows(void) {
  M68kRenderPlan source;
  M68kRenderPlan dest;
  char *full_text = NULL;
  m68k_render_plan_init(&source);
  m68k_render_plan_init(&dest);

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&source, M68K_RENDER_PLAN_ROW_SECTION, 0U,
    "    SECTION section_0,code\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&source, M68K_RENDER_PLAN_ROW_INSTRUCTION, 0U,
    "\trts\n", NULL));
  m68k_render_plan_move(&dest, &source);

  M68K_C_ASSERT_U32(0U, (uint32_t)source.row_count);
  M68K_C_ASSERT_U32(0U, source.total_lines);
  M68K_C_ASSERT_U32(2U, (uint32_t)dest.row_count);
  M68K_C_ASSERT_INT(0, m68k_render_plan_emit_all_alloc(&dest, &full_text));
  M68K_C_ASSERT_STR("    SECTION section_0,code\n\trts\n", full_text);

  m68k_render_plan_free_text(full_text);
  m68k_render_plan_destroy(&source);
  m68k_render_plan_destroy(&dest);
  return 0;
}

static int test_render_plan_arena_owned_rows_survive_growth(void) {
  M68kRenderPlan plan;
  char line[32];
  size_t index;
  char *full_text = NULL;
  m68k_render_plan_init(&plan);

  for (index = 0U; index < 40U; ++index) {
    snprintf(line, sizeof(line), "row_%02u\n", (unsigned)index);
    M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_DATA, 0U, line, NULL));
  }

  M68K_C_ASSERT_U32(40U, (uint32_t)plan.row_count);
  M68K_C_ASSERT_U32(40U, plan.total_lines);
  M68K_C_ASSERT_STR("row_00\n", plan.rows[0].text);
  M68K_C_ASSERT_STR("row_39\n", plan.rows[39].text);
  M68K_C_ASSERT_INT(0, m68k_render_plan_emit_all_alloc(&plan, &full_text));
  M68K_C_ASSERT(strstr(full_text, "row_00\nrow_01\n") == full_text);
  M68K_C_ASSERT(strstr(full_text, "row_38\nrow_39\n") != NULL);

  m68k_render_plan_free_text(full_text);
  m68k_render_plan_destroy(&plan);
  return 0;
}

static int test_render_plan_builds_source_file_body_genam_fixture(void) {
  M68kSourceFileIR source_file;
  M68kSectionIR section;
  M68kStatementIR stmt;
  M68kRenderPolicy policy;
  M68kRenderPlan plan;
  M68kRenderPlanRow *row;
  const M68kRenderPlanRow *found;
  char *full_text = NULL;
  uint8_t bytes[3] = {0x01U, 0x02U, 0x03U};
  const char *expected =
    "    SECTION section_0,code,$7\n"
    "start:\n"
    "    DC.B    $01,$02,$03\n"
    "    DS.B    $4\n";
  m68k_ir_source_file_create(&source_file);
  m68k_ir_section_create(&section);
  m68k_render_policy_init_for_syntax(&policy, M68K_IR_SYNTAX_GENAM);
  M68K_C_ASSERT_INT(0, m68k_ir_section_set_name(&section, "section_0"));
  section.kind = M68K_SECTION_CODE;
  section.size = 7U;
  section.data_size = 3U;

  m68k_ir_statement_init(&stmt);
  stmt.kind = M68K_STATEMENT_LABEL;
  stmt.offset = 0U;
  stmt.label_name = "start";
  M68K_C_ASSERT_INT(0, m68k_ir_section_append_statement(&section, &stmt));

  m68k_ir_statement_init(&stmt);
  stmt.kind = M68K_STATEMENT_DATA;
  stmt.offset = 0U;
  stmt.u.data.kind = M68K_DATA_ITEM_BYTES;
  stmt.u.data.data = bytes;
  stmt.u.data.size = sizeof(bytes);
  M68K_C_ASSERT_INT(0, m68k_ir_section_append_statement(&section, &stmt));

  m68k_ir_statement_init(&stmt);
  stmt.kind = M68K_STATEMENT_RESERVE;
  stmt.offset = 3U;
  stmt.u.reserve_size = 4U;
  M68K_C_ASSERT_INT(0, m68k_ir_section_append_statement(&section, &stmt));

  M68K_C_ASSERT_INT(0, m68k_ir_source_file_append_section(&source_file, &section));
  m68k_ir_section_destroy(&section);
  M68K_C_ASSERT_INT(0, m68k_render_plan_build_source_file_body(&source_file, &policy, &plan, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(0, m68k_render_plan_emit_all_alloc(&plan, &full_text));
  M68K_C_ASSERT_STR(expected, full_text);
  M68K_C_ASSERT_U32(4U, (uint32_t)plan.row_count);
  row = &plan.rows[2];
  M68K_C_ASSERT_U32(M68K_RENDER_PLAN_ROW_DATA, row->kind);
  M68K_C_ASSERT_U32(0U, row->source_offset);
  M68K_C_ASSERT_U32(3U, row->source_size);
  found = m68k_render_plan_find_row_for_source_offset(&plan, 0U, 2U);
  M68K_C_ASSERT(found != NULL);
  M68K_C_ASSERT_U32(M68K_RENDER_PLAN_ROW_DATA, found->kind);

  m68k_render_plan_free_text(full_text);
  m68k_render_plan_destroy(&plan);
  m68k_ir_source_file_destroy(&source_file);
  return 0;
}

int m68k_c_render_plan_tests(void) {
  static const M68kCTestCase cases[] = {
    {"line_counts_and_order", test_render_plan_line_counts_and_order},
    {"line_and_address_lookup", test_render_plan_line_and_address_lookup},
    {"row_builder_commits_fragmented_row", test_render_plan_row_builder_commits_fragmented_row},
    {"builds_text_line_rows", test_render_plan_builds_text_line_rows},
    {"window_emission_matches_full_slice", test_render_plan_window_emission_matches_full_slice},
    {"visits_physical_lines_with_owner_row", test_render_plan_visits_physical_lines_with_owner_row},
    {"rejects_rows_without_complete_lines", test_render_plan_rejects_rows_without_complete_lines},
    {"hoists_typed_header_rows", test_render_plan_hoists_typed_header_rows},
    {"move_transfers_arena_owned_rows", test_render_plan_move_transfers_arena_owned_rows},
    {"arena_owned_rows_survive_growth", test_render_plan_arena_owned_rows_survive_growth},
    {"builds_source_file_body_genam_fixture", test_render_plan_builds_source_file_body_genam_fixture}
  };
  return m68k_c_test_run_suite("m68k_render_plan", cases, sizeof(cases) / sizeof(cases[0]));
}
