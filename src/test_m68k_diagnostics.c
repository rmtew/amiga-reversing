#include "m68k_c_unit_test.h"
#include "m68k_diagnostics.h"

static int test_zero_initialized_list_is_empty(void) {
  M68kDiagList diagnostics = {0};
  M68K_C_ASSERT_INT(0, m68k_diag_has_errors(&diagnostics));
  M68K_C_ASSERT_STR("", m68k_diag_first_message(&diagnostics));
  M68K_C_ASSERT(diagnostics.count == 0U);
  return 0;
}

static int test_nil_sink_discards_diagnostics(void) {
  M68kDiagSink sink = {0};
  m68k_diag_add(sink, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_BAD_ARGUMENT, "discarded");
  return 0;
}

static int test_records_multiple_diagnostics(void) {
  M68kDiagList diagnostics = {0};
  M68kDiagSink sink = m68k_diag_sink(&diagnostics);
  m68k_diag_add(sink, M68K_DIAG_SEVERITY_WARNING, M68K_DIAG_CODE_NONE, "warning");
  m68k_diag_addf(sink, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_DECODE_FAILED, "decode %u", 7U);
  M68K_C_ASSERT(diagnostics.count == 2U);
  M68K_C_ASSERT_INT(1, m68k_diag_has_errors(&diagnostics));
  M68K_C_ASSERT_STR("decode 7", m68k_diag_first_message(&diagnostics));
  M68K_C_ASSERT_INT(M68K_DIAG_CODE_DECODE_FAILED, diagnostics.items[1].code);
  return 0;
}

int m68k_c_diagnostics_tests(void) {
  static const M68kCTestCase cases[] = {
    {"zero_initialized_list_is_empty", test_zero_initialized_list_is_empty},
    {"nil_sink_discards_diagnostics", test_nil_sink_discards_diagnostics},
    {"records_multiple_diagnostics", test_records_multiple_diagnostics},
  };
  return m68k_c_test_run_suite("m68k_diagnostics", cases, sizeof(cases) / sizeof(cases[0]));
}
