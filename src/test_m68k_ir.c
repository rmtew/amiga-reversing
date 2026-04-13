#include "m68k_c_unit_test.h"
#include "m68k_ir.h"
#include "util_arena.h"

#include <string.h>

static int test_render_policy_defaults(void) {
  M68kRenderPolicy policy;
  memset(&policy, 0xA5, sizeof(policy));
  m68k_render_policy_init_default(&policy);
  M68K_C_ASSERT_INT(M68K_IR_SYNTAX_CANONICAL, policy.syntax.syntax_mode);
  M68K_C_ASSERT_INT(1, policy.presentation.prefer_generated_names);
  M68K_C_ASSERT_INT(1, policy.presentation.prefer_strings);
  M68K_C_ASSERT_INT(1, policy.presentation.prefer_long_data);
  M68K_C_ASSERT_STR("loc", policy.presentation.code_label_prefix);
  M68K_C_ASSERT_STR("sub", policy.presentation.call_label_prefix);
  M68K_C_ASSERT_STR("dat", policy.presentation.data_label_prefix);
  return 0;
}

static int test_parse_syntax_mode_name(void) {
  uint8_t mode = 0xFFu;
  M68K_C_ASSERT(m68k_ir_parse_syntax_mode_name("canonical", &mode));
  M68K_C_ASSERT_INT(M68K_IR_SYNTAX_CANONICAL, mode);
  M68K_C_ASSERT(m68k_ir_parse_syntax_mode_name("GENAM", &mode));
  M68K_C_ASSERT_INT(M68K_IR_SYNTAX_GENAM, mode);
  M68K_C_ASSERT(m68k_ir_parse_syntax_mode_name("vasm", &mode));
  M68K_C_ASSERT_INT(M68K_IR_SYNTAX_VASM, mode);
  M68K_C_ASSERT(!m68k_ir_parse_syntax_mode_name("other", &mode));
  return 0;
}

static int test_analysis_defaults_and_inits(void) {
  M68kAnalysisPolicy policy;
  M68kAnalysisFindings findings;
  M68kInstructionIR instruction;
  M68kSymbolRefIR symbol_ref;
  memset(&policy, 0xA5, sizeof(policy));
  memset(&findings, 0xA5, sizeof(findings));
  memset(&instruction, 0xA5, sizeof(instruction));
  memset(&symbol_ref, 0xA5, sizeof(symbol_ref));
  m68k_analysis_policy_init_default(&policy);
  m68k_analysis_findings_init(&findings);
  m68k_ir_instruction_init(&instruction);
  m68k_ir_symbol_ref_init(&symbol_ref);
  M68K_C_ASSERT_INT(M68K_ASM_CPU_68060, policy.max_cpu);
  M68K_C_ASSERT_INT(M68K_ASM_CPU_68000, findings.required_cpu);
  M68K_C_ASSERT_INT(0, findings.cpu_violation_count);
  M68K_C_ASSERT_U32(M68K_IR_INVALID_FORM_INDEX, instruction.form_index);
  M68K_C_ASSERT_INT(0, symbol_ref.kind);
  M68K_C_ASSERT_INT(0, symbol_ref.has_name);
  return 0;
}

static int test_section_append_statement_copies_data(void) {
  M68kSectionIR section;
  M68kStatementIR statement;
  uint8_t bytes[2] = {0x12u, 0x34u};

  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));
  m68k_ir_statement_init(&statement);
  statement.kind = M68K_STATEMENT_DATA;
  statement.label_name = "lbl";
  statement.comment = "comment";
  statement.u.data.kind = M68K_DATA_ITEM_BYTES;
  statement.u.data.data = bytes;
  statement.u.data.size = sizeof(bytes);
  statement.u.data.expr_text = "expr";

  M68K_C_ASSERT_INT(0, m68k_ir_section_append_statement(&section, &statement));
  M68K_C_ASSERT_INT(1, (int)section.statement_count);
  M68K_C_ASSERT(section.statements[0].label_name != statement.label_name);
  M68K_C_ASSERT(section.statements[0].comment != statement.comment);
  M68K_C_ASSERT(section.statements[0].u.data.data != statement.u.data.data);
  M68K_C_ASSERT(section.statements[0].u.data.expr_text != statement.u.data.expr_text);
  M68K_C_ASSERT_STR("lbl", section.statements[0].label_name);
  M68K_C_ASSERT_STR("comment", section.statements[0].comment);
  M68K_C_ASSERT_STR("expr", section.statements[0].u.data.expr_text);
  M68K_C_ASSERT_U32(0x12u, section.statements[0].u.data.data[0]);
  M68K_C_ASSERT_U32(0x34u, section.statements[0].u.data.data[1]);

  m68k_ir_section_destroy(&section);
  return 0;
}

static int test_section_analysis_label_dedupes(void) {
  M68kSectionAnalysisIR analysis;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_create(&analysis));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_add_label(&analysis, 0x20u));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_add_label(&analysis, 0x20u));
  M68K_C_ASSERT_INT(1, (int)analysis.label_count);
  M68K_C_ASSERT_U32(0x20u, analysis.label_offsets[0]);
  m68k_ir_section_analysis_destroy(&analysis);
  return 0;
}

static int test_source_analysis_append_section_copies_recovered_dispatches(void) {
  M68kSectionAnalysisIR section;
  M68kSourceAnalysisIR source;
  M68kRecoveredWordDispatchIR word_dispatch;
  M68kRecoveredInlineDispatchIR inline_dispatch;
  int16_t word_entries[2] = {0x0010, 0x0000};
  uint32_t word_targets[2] = {0x120u, 0x000u};
  uint8_t word_valid[2] = {1u, 0u};
  uint32_t inline_entries[2] = {0x200u, 0x202u};
  uint32_t inline_targets[2] = {0x300u, 0x320u};

  memset(&word_dispatch, 0, sizeof(word_dispatch));
  memset(&inline_dispatch, 0, sizeof(inline_dispatch));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_create(&section));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_create(&source));

  word_dispatch.pattern = 1u;
  word_dispatch.table_base = 0x100u;
  word_dispatch.base_target = 0x110u;
  word_dispatch.scanned_bytes = 4u;
  word_dispatch.slot_count = 2u;
  word_dispatch.entry_words = word_entries;
  word_dispatch.targets = word_targets;
  word_dispatch.target_valid = word_valid;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_word_dispatch(&section, &word_dispatch));

  inline_dispatch.table_base = 0x200u;
  inline_dispatch.scanned_bytes = 4u;
  inline_dispatch.entry_count = 2u;
  inline_dispatch.entry_offsets = inline_entries;
  inline_dispatch.targets = inline_targets;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_inline_dispatch(&section, &inline_dispatch));

  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_append_section(&source, &section));
  M68K_C_ASSERT_INT(1, (int)source.section_count);
  M68K_C_ASSERT_INT(1, (int)source.sections[0].recovered_word_dispatch_count);
  M68K_C_ASSERT_INT(1, (int)source.sections[0].recovered_inline_dispatch_count);
  M68K_C_ASSERT(source.sections[0].recovered_word_dispatches[0].entry_words != word_entries);
  M68K_C_ASSERT(source.sections[0].recovered_inline_dispatches[0].entry_offsets != inline_entries);
  M68K_C_ASSERT_U32(0x120u, source.sections[0].recovered_word_dispatches[0].targets[0]);
  M68K_C_ASSERT_U32(0x320u, source.sections[0].recovered_inline_dispatches[0].targets[1]);

  m68k_ir_source_analysis_destroy(&source);
  m68k_ir_section_analysis_destroy(&section);
  return 0;
}

static int test_section_many_interleaved_labels_and_data(void) {
  M68kSectionIR section;
  size_t index;
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));

  for (index = 0; index < 70000; ++index) {
    M68kStatementIR label_stmt;
    M68kStatementIR data_stmt;
    char label_name[32];
    uint8_t byte = (uint8_t)(index & 0xFFu);

    m68k_ir_statement_init(&label_stmt);
    label_stmt.kind = M68K_STATEMENT_LABEL;
    snprintf(label_name, sizeof(label_name), "dat_%04X", (unsigned)index);
    label_stmt.label_name = label_name;
    M68K_C_ASSERT_INT(0, m68k_ir_section_append_statement(&section, &label_stmt));

    m68k_ir_statement_init(&data_stmt);
    data_stmt.kind = M68K_STATEMENT_DATA;
    data_stmt.u.data.kind = M68K_DATA_ITEM_BYTES;
    data_stmt.u.data.data = &byte;
    data_stmt.u.data.size = 1U;
    M68K_C_ASSERT_INT(0, m68k_ir_section_append_statement(&section, &data_stmt));
  }

  M68K_C_ASSERT_INT(140000, (int)section.statement_count);
  m68k_ir_section_destroy(&section);
  return 0;
}

static int test_section_many_interleaved_labels_and_expr_data(void) {
  M68kSectionIR section;
  size_t index;
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));

  for (index = 0; index < 70000; ++index) {
    M68kStatementIR label_stmt;
    M68kStatementIR data_stmt;
    char label_name[32];
    uint8_t word_bytes[2];
    char expr[48];

    m68k_ir_statement_init(&label_stmt);
    label_stmt.kind = M68K_STATEMENT_LABEL;
    snprintf(label_name, sizeof(label_name), "dat_%04X", (unsigned)index);
    label_stmt.label_name = label_name;
    M68K_C_ASSERT_INT(0, m68k_ir_section_append_statement(&section, &label_stmt));

    word_bytes[0] = (uint8_t)((index >> 8) & 0xFFu);
    word_bytes[1] = (uint8_t)(index & 0xFFu);
    snprintf(expr, sizeof(expr), "loc_%04X-dat_%04X", (unsigned)(index + 2U), (unsigned)index);

    m68k_ir_statement_init(&data_stmt);
    data_stmt.kind = M68K_STATEMENT_DATA;
    data_stmt.u.data.kind = M68K_DATA_ITEM_WORDS;
    data_stmt.u.data.data = word_bytes;
    data_stmt.u.data.size = 2U;
    data_stmt.u.data.expr_text = expr;
    M68K_C_ASSERT_INT(0, m68k_ir_section_append_statement(&section, &data_stmt));
  }

  M68K_C_ASSERT_INT(140000, (int)section.statement_count);
  m68k_ir_section_destroy(&section);
  return 0;
}

static int test_arena_mark_rewind_reuses_same_block_range(void) {
  Arena *arena = arena_create(64U);
  char *first;
  ArenaMark mark;
  char *second;
  char *third;
  M68K_C_ASSERT(arena != NULL);
  first = (char *)arena_alloc(arena, 16U);
  M68K_C_ASSERT(first != NULL);
  mark = arena_mark(arena);
  second = (char *)arena_alloc(arena, 24U);
  M68K_C_ASSERT(second != NULL);
  memset(second, 0x11, 24U);
  arena_rewind(arena, mark);
#if defined(_DEBUG)
  {
    size_t index;
    for (index = 0; index < 24U; ++index) M68K_C_ASSERT_U32(0xDDu, (unsigned char)second[index]);
  }
#endif
  third = (char *)arena_alloc(arena, 24U);
  M68K_C_ASSERT(third != NULL);
  M68K_C_ASSERT(second == third);
  arena_destroy(arena);
  return 0;
}

static int test_arena_rewind_discards_later_blocks(void) {
  Arena *arena = arena_create(64U);
  char *first;
  ArenaMark mark;
  char *large;
  char *again;
  M68K_C_ASSERT(arena != NULL);
  first = (char *)arena_alloc(arena, 32U);
  M68K_C_ASSERT(first != NULL);
  mark = arena_mark(arena);
  large = (char *)arena_alloc(arena, 5000U);
  M68K_C_ASSERT(large != NULL);
  arena_rewind(arena, mark);
  again = (char *)arena_alloc(arena, 32U);
  M68K_C_ASSERT(again != NULL);
  M68K_C_ASSERT(again == first + 32);
  arena_destroy(arena);
  return 0;
}

static int test_arena_reset_poisons_head_block_range(void) {
  Arena *arena = arena_create(64U);
  char *data;
  size_t index;
  M68K_C_ASSERT(arena != NULL);
  data = (char *)arena_alloc(arena, 32U);
  M68K_C_ASSERT(data != NULL);
  memset(data, 0x22, 32U);
  arena_reset(arena);
#if defined(_DEBUG)
  for (index = 0; index < 32U; ++index) M68K_C_ASSERT_U32(0xDDu, (unsigned char)data[index]);
#else
  (void)index;
#endif
  arena_destroy(arena);
  return 0;
}

int m68k_c_ir_tests(void) {
  static const M68kCTestCase cases[] = {
    {"render_policy_defaults", test_render_policy_defaults},
    {"parse_syntax_mode_name", test_parse_syntax_mode_name},
    {"analysis_defaults_and_inits", test_analysis_defaults_and_inits},
    {"section_append_statement_copies_data", test_section_append_statement_copies_data},
    {"section_analysis_label_dedupes", test_section_analysis_label_dedupes},
    {"source_analysis_append_section_copies_recovered_dispatches",
      test_source_analysis_append_section_copies_recovered_dispatches},
    {"section_many_interleaved_labels_and_data", test_section_many_interleaved_labels_and_data},
    {"section_many_interleaved_labels_and_expr_data", test_section_many_interleaved_labels_and_expr_data},
    {"arena_mark_rewind_reuses_same_block_range", test_arena_mark_rewind_reuses_same_block_range},
    {"arena_rewind_discards_later_blocks", test_arena_rewind_discards_later_blocks},
    {"arena_reset_poisons_head_block_range", test_arena_reset_poisons_head_block_range},
  };
  return m68k_c_test_run_suite("m68k_ir", cases, sizeof(cases) / sizeof(cases[0]));
}
