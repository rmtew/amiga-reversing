#include "m68k_c_unit_test.h"

#include <string.h>

int m68k_c_test_fail_expr(const char *file, int line, const char *expr) {
  fprintf(stderr, "%s:%d: assertion failed: %s\n", file, line, expr);
  return 1;
}

int m68k_c_test_fail_u32(const char *file, int line, uint32_t expected, uint32_t actual) {
  fprintf(stderr, "%s:%d: expected 0x%08X got 0x%08X\n", file, line, (unsigned)expected, (unsigned)actual);
  return 1;
}

int m68k_c_test_fail_int(const char *file, int line, int expected, int actual) {
  fprintf(stderr, "%s:%d: expected %d got %d\n", file, line, expected, actual);
  return 1;
}

int m68k_c_test_fail_str(const char *file, int line, const char *expected, const char *actual) {
  fprintf(stderr, "%s:%d: expected \"%s\" got \"%s\"\n", file, line,
    expected != NULL ? expected : "(null)", actual != NULL ? actual : "(null)");
  return 1;
}

int m68k_c_test_run_suite(const char *suite_name, const M68kCTestCase *cases, size_t case_count) {
  size_t index;
  int failures = 0;
  printf("%s\n", suite_name);
  for (index = 0; index < case_count; ++index) {
    int result = cases[index].fn();
    if (result == 0) {
      printf("  ok  %s\n", cases[index].name);
      continue;
    }
    printf("  FAIL %s\n", cases[index].name);
    failures += result;
  }
  if (failures == 0) printf("%s: all %u passed\n", suite_name, (unsigned)case_count);
  return failures;
}
