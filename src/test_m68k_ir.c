#include "m68k_c_unit_test.h"
#include "m68k_ir.h"

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

  m68k_ir_section_init(&section);
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

  m68k_ir_section_free(&section);
  return 0;
}

static int test_section_analysis_label_dedupes(void) {
  M68kSectionAnalysisIR analysis;
  m68k_ir_section_analysis_init(&analysis);
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_add_label(&analysis, 0x20u));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_add_label(&analysis, 0x20u));
  M68K_C_ASSERT_INT(1, (int)analysis.label_count);
  M68K_C_ASSERT_U32(0x20u, analysis.label_offsets[0]);
  m68k_ir_section_analysis_free(&analysis);
  return 0;
}

int m68k_c_ir_tests(void) {
  static const M68kCTestCase cases[] = {
    {"render_policy_defaults", test_render_policy_defaults},
    {"parse_syntax_mode_name", test_parse_syntax_mode_name},
    {"analysis_defaults_and_inits", test_analysis_defaults_and_inits},
    {"section_append_statement_copies_data", test_section_append_statement_copies_data},
    {"section_analysis_label_dedupes", test_section_analysis_label_dedupes},
  };
  return m68k_c_test_run_suite("m68k_ir", cases, sizeof(cases) / sizeof(cases[0]));
}
