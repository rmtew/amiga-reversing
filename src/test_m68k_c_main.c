#include "m68k_c_unit_test.h"

int main(void) {
  int failures = 0;
  failures += m68k_c_parse_util_tests();
  failures += m68k_c_instruction_spec_tests();
  failures += m68k_c_ir_tests();
  failures += m68k_c_render_plan_tests();
  failures += m68k_c_diagnostics_tests();
  failures += m68k_c_platform_decompression_tests();
  return failures == 0 ? 0 : 1;
}
