#include "m68k_c_unit_test.h"
#include "m68k_render_plan.h"

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

static int test_render_plan_window_emission_matches_full_slice(void) {
  M68kRenderPlan plan;
  char *full_text = NULL;
  char *window_text = NULL;
  const char *expected_full = "A\nB1\nB2\nC\n";
  const char *expected_window = "B1\nB2\n";
  m68k_render_plan_init(&plan);

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_INCLUDE, 1U, "A\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_DATA, 2U, "B1\nB2\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_SECTION, 3U, "C\n", NULL));

  M68K_C_ASSERT_INT(0, m68k_render_plan_emit_all_alloc(&plan, &full_text));
  M68K_C_ASSERT_INT(0, m68k_render_plan_emit_rows_alloc(&plan, 1U, 1U, &window_text));
  M68K_C_ASSERT_STR(expected_full, full_text);
  M68K_C_ASSERT_STR(expected_window, window_text);
  M68K_C_ASSERT(strstr(full_text, window_text) == full_text + 2U);

  m68k_render_plan_free_text(full_text);
  m68k_render_plan_free_text(window_text);
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
    {"window_emission_matches_full_slice", test_render_plan_window_emission_matches_full_slice},
    {"rejects_rows_without_complete_lines", test_render_plan_rejects_rows_without_complete_lines},
    {"builds_source_file_body_genam_fixture", test_render_plan_builds_source_file_body_genam_fixture}
  };
  return m68k_c_test_run_suite("m68k_render_plan", cases, sizeof(cases) / sizeof(cases[0]));
}
