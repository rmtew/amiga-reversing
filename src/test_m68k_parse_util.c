#include "m68k_c_unit_test.h"
#include "m68k_parse_util.h"

#include <string.h>

static int test_sign_extend32(void) {
  M68K_C_ASSERT_U32(0xFFFFFFFFu, m68k_sign_extend32(0xFFu, 8));
  M68K_C_ASSERT_U32(0xFFFFFF80u, m68k_sign_extend32(0x80u, 8));
  M68K_C_ASSERT_U32(0x0000007Fu, m68k_sign_extend32(0x7Fu, 8));
  M68K_C_ASSERT_U32(0xFFFFFFF8u, m68k_sign_extend32(0xFFF8u, 16));
  return 0;
}

static int test_parse_number_u32(void) {
  uint32_t value = 0;
  M68K_C_ASSERT(m68k_parse_number_u32("$FF", &value));
  M68K_C_ASSERT_U32(0x000000FFu, value);
  M68K_C_ASSERT(m68k_parse_number_u32("-8", &value));
  M68K_C_ASSERT_U32(0xFFFFFFF8u, value);
  M68K_C_ASSERT(!m68k_parse_number_u32("", &value));
  return 0;
}

static int test_parse_cpu_name(void) {
  uint8_t cpu = 0xFFu;
  M68K_C_ASSERT(m68k_parse_cpu_name("68020", &cpu));
  M68K_C_ASSERT_INT(M68K_ASM_CPU_68020, cpu);
  M68K_C_ASSERT(m68k_parse_cpu_name("68060", &cpu));
  M68K_C_ASSERT_INT(M68K_ASM_CPU_68060, cpu);
  M68K_C_ASSERT(!m68k_parse_cpu_name("68008", &cpu));
  return 0;
}

static int test_normalize_pc_current_expr(void) {
  char text[64];
  strcpy(text, "*+10(pc)");
  m68k_normalize_pc_current_expr_in_place(text);
  M68K_C_ASSERT_STR("8(pc)", text);
  strcpy(text, "*-6(pc)");
  m68k_normalize_pc_current_expr_in_place(text);
  M68K_C_ASSERT_STR("-8(pc)", text);
  return 0;
}

int m68k_c_parse_util_tests(void) {
  static const M68kCTestCase cases[] = {
    {"sign_extend32", test_sign_extend32},
    {"parse_number_u32", test_parse_number_u32},
    {"parse_cpu_name", test_parse_cpu_name},
    {"normalize_pc_current_expr", test_normalize_pc_current_expr},
  };
  return m68k_c_test_run_suite("m68k_parse_util", cases, sizeof(cases) / sizeof(cases[0]));
}
