#ifndef M68K_C_UNIT_TEST_H
#define M68K_C_UNIT_TEST_H

#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef int (*M68kCTestFn)(void);

typedef struct {
  const char *name;
  M68kCTestFn fn;
} M68kCTestCase;

int m68k_c_test_run_suite(const char *suite_name, const M68kCTestCase *cases, size_t case_count);
int m68k_c_test_fail_expr(const char *file, int line, const char *expr);
int m68k_c_test_fail_u32(const char *file, int line, uint32_t expected, uint32_t actual);
int m68k_c_test_fail_int(const char *file, int line, int expected, int actual);
int m68k_c_test_fail_str(const char *file, int line, const char *expected, const char *actual);

#define M68K_C_ASSERT(expr) \
  do { \
    if (!(expr)) return m68k_c_test_fail_expr(__FILE__, __LINE__, #expr); \
  } while (0)

#define M68K_C_ASSERT_U32(expected, actual) \
  do { \
    uint32_t m68k_c_expected_ = (uint32_t)(expected); \
    uint32_t m68k_c_actual_ = (uint32_t)(actual); \
    if (m68k_c_expected_ != m68k_c_actual_) \
      return m68k_c_test_fail_u32(__FILE__, __LINE__, m68k_c_expected_, m68k_c_actual_); \
  } while (0)

#define M68K_C_ASSERT_INT(expected, actual) \
  do { \
    int m68k_c_expected_ = (int)(expected); \
    int m68k_c_actual_ = (int)(actual); \
    if (m68k_c_expected_ != m68k_c_actual_) \
      return m68k_c_test_fail_int(__FILE__, __LINE__, m68k_c_expected_, m68k_c_actual_); \
  } while (0)

#define M68K_C_ASSERT_STR(expected, actual) \
  do { \
    const char *m68k_c_expected_ = (expected); \
    const char *m68k_c_actual_ = (actual); \
    if ((m68k_c_expected_ == NULL) != (m68k_c_actual_ == NULL) || \
        (m68k_c_expected_ != NULL && m68k_c_actual_ != NULL && strcmp(m68k_c_expected_, m68k_c_actual_) != 0)) \
      return m68k_c_test_fail_str(__FILE__, __LINE__, m68k_c_expected_, m68k_c_actual_); \
  } while (0)

int m68k_c_parse_util_tests(void);
int m68k_c_instruction_spec_tests(void);
int m68k_c_ir_tests(void);
int m68k_c_render_plan_tests(void);
int m68k_c_diagnostics_tests(void);
int m68k_c_platform_decompression_tests(void);

#endif
