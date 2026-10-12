#include "m68k_ir.h"
#include "m68k_c_unit_test.h"

static int test_manual_representations_inline_and_zero_init(void) {
  M68kAnalysisPolicy source = {0}, copy = {0};
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_manual_representations(&source, 4U));
  M68K_C_ASSERT(source.manual_representations == source.manual_representations_inline);
  source.manual_representation_count = 1U;
  source.manual_representations[0].offset = 123U;
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT(copy.manual_representations == copy.manual_representations_inline);
  M68K_C_ASSERT(copy.manual_representations != source.manual_representations);
  source.manual_representations[0].offset = 456U;
  M68K_C_ASSERT_U32(123U, copy.manual_representations[0].offset);
  m68k_analysis_policy_destroy(&source);
  m68k_analysis_policy_destroy(&copy);
  m68k_analysis_policy_destroy(&copy);
  source = (M68kAnalysisPolicy){0};
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT(copy.manual_representations == copy.manual_representations_inline);
  m68k_analysis_policy_destroy(&copy);
  m68k_analysis_policy_destroy(&source);
  return 0;
}

static int test_manual_representations_heap_clone_growth_and_bound(void) {
  M68kAnalysisPolicy source, copy = {0};
  M68kAnalysisManualRepresentation *saved;
  uint16_t index;
  m68k_analysis_policy_init_default(&source);
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_manual_representations(&source, 129U));
  source.manual_representation_count = 129U;
  for (index = 0U; index < source.manual_representation_count; ++index)
    source.manual_representations[index].offset = index * 2U;
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT(copy.manual_representations_owner && copy.manual_representations != source.manual_representations);
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_manual_representations(&source, 4096U));
  M68K_C_ASSERT_U32(256U, source.manual_representations[128].offset);
  source.manual_representations[128].offset = 999U;
  m68k_analysis_policy_destroy(&source);
  M68K_C_ASSERT_U32(256U, copy.manual_representations[128].offset);
  saved = copy.manual_representations;
  M68K_C_ASSERT_INT(-1, m68k_analysis_policy_reserve_manual_representations(&copy, 4097U));
  M68K_C_ASSERT(copy.manual_representations == saved);
  M68K_C_ASSERT_U32(129U, copy.manual_representation_count);
  m68k_analysis_policy_destroy(&copy);
  return 0;
}

static int test_manual_representations_invalid_copy_preserves_destination(void) {
  M68kAnalysisPolicy source = {0}, copy = {0};
  /* Force copy to allocate earlier collections before it rejects bad storage. */
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_named_labels(&source, 5U));
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_structured_data_items(&source, 5U));
  source.named_label_count = 5U;
  source.structured_data_item_count = 5U;
  source.manual_representation_count = 1U;
  copy.max_cpu = 42U;
  M68K_C_ASSERT_INT(-1, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT_INT(42, copy.max_cpu);
  M68K_C_ASSERT(copy.manual_representations == NULL);
  M68K_C_ASSERT_INT(-1, m68k_analysis_policy_reserve_manual_representations(&source, 4U));
  m68k_analysis_policy_destroy(&source);
  m68k_analysis_policy_init_default(&source);
  source.manual_representation_capacity = 129U; /* Inline storage cannot claim heap capacity. */
  M68K_C_ASSERT_INT(-1, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT_INT(42, copy.max_cpu);
  m68k_analysis_policy_destroy(&source);
  m68k_analysis_policy_destroy(&copy);
  return 0;
}

int m68k_c_policy_storage_tests(void) {
  static const M68kCTestCase cases[] = {
    {"manual_representations_inline_and_zero_init", test_manual_representations_inline_and_zero_init},
    {"manual_representations_heap_clone_growth_and_bound", test_manual_representations_heap_clone_growth_and_bound},
    {"manual_representations_invalid_copy_preserves_destination", test_manual_representations_invalid_copy_preserves_destination},
  };
  return m68k_c_test_run_suite("m68k_policy_storage", cases, sizeof(cases) / sizeof(cases[0]));
}
