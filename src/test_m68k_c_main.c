#include "m68k_c_unit_test.h"

int main(void) {
  int failures = 0;
  failures += m68k_c_parse_util_tests();
  failures += m68k_c_instruction_spec_tests();
  failures += m68k_c_ir_tests();
  return failures == 0 ? 0 : 1;
}
