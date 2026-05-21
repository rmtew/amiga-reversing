#include "m68k_c_unit_test.h"

int main(void) {
  int failures = 0;
  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stderr, NULL, _IONBF, 0);
  failures += m68k_c_parse_util_tests();
  failures += m68k_c_instruction_spec_tests();
  failures += m68k_c_ir_tests();
  failures += m68k_c_simulator_tests();
  failures += m68k_c_render_plan_tests();
  failures += m68k_c_diagnostics_tests();
  failures += m68k_c_platform_decompression_tests();
  failures += m68k_c_container_metadata_tests();
  failures += m68k_c_mac_os_runtime_tests();
  failures += m68k_c_platform_macos_hfs_tests();
  failures += m68k_c_platform_macos_resource_tests();
  failures += m68k_c_util_arena_tests();
  return failures == 0 ? 0 : 1;
}
