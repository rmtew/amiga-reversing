#include "m68k_ir.h"
#include "m68k_c_unit_test.h"
#include "platform_file_lib.h"

#include <string.h>

static int test_register_seeds_growth_copy_and_count_bound(void) {
  M68kAnalysisPolicy source = {0}, copy = {0};
  M68kAnalysisRegisterSeed *saved;
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_register_seeds(&source, 256U));
  M68K_C_ASSERT(source.register_seeds == source.register_seeds_inline);
  source.register_seed_count = 256U;
  source.register_seeds[255].entry_offset = 510U;
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT(copy.register_seeds == copy.register_seeds_inline);
  M68K_C_ASSERT_U32(510U, copy.register_seeds[255].entry_offset);
  m68k_analysis_policy_destroy(&copy);
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_register_seeds(&source, 262U));
  M68K_C_ASSERT(source.register_seeds != source.register_seeds_inline);
  M68K_C_ASSERT_U32(510U, source.register_seeds[255].entry_offset);
  source.register_seed_count = 262U;
  source.register_seeds[261].entry_offset = 522U;
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT(copy.register_seeds != source.register_seeds);
  m68k_analysis_policy_destroy(&source);
  M68K_C_ASSERT_U32(262U, copy.register_seed_count);
  M68K_C_ASSERT_U32(522U, copy.register_seeds[261].entry_offset);
  saved = copy.register_seeds;
  M68K_C_ASSERT_INT(M68K_ANALYSIS_POLICY_CAPACITY_EXCEEDED,
    m68k_analysis_policy_reserve_register_seeds(&copy, (size_t)UINT16_MAX + 1U));
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STORAGE_CAPACITY_REGISTER_SEEDS, copy.storage_capacity_status);
  M68K_C_ASSERT(copy.register_seeds == saved);
  M68K_C_ASSERT_U32(262U, copy.register_seed_count);
  M68K_C_ASSERT_INT(M68K_ANALYSIS_POLICY_CAPACITY_EXCEEDED,
    m68k_analysis_policy_reserve_register_seeds(&copy, SIZE_MAX));
  m68k_analysis_policy_destroy(&copy);
  m68k_analysis_policy_destroy(&copy);
  m68k_analysis_policy_init_default(&source);
  source.register_seed_count = 257U; /* Claimed facts exceed inline storage. */
  copy.max_cpu = 42U;
  M68K_C_ASSERT_INT(-1, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT_U32(42U, copy.max_cpu);
  source.register_seed_count = 0U;
  source.register_seed_capacity = 512U;
  M68K_C_ASSERT_INT(-1, m68k_analysis_policy_reserve_register_seeds(&source, 262U));
  m68k_analysis_policy_destroy(&source);
  return 0;
}

static int test_rsset_regions_inline_growth_clone_and_identity_bound(void) {
  M68kAnalysisPolicy source = {0}, copy = {0};
  M68kAnalysisRssetLayoutRegion *saved;
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_rsset_layout_regions(&source, 4U));
  source.rsset_layout_region_count = 4U;
  strcpy(source.rsset_layout_regions[3].symbol, "inline_last");
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT(copy.rsset_layout_regions == copy.rsset_layout_regions_inline);
  source.rsset_layout_regions[3].offset = 9U;
  M68K_C_ASSERT_U32(0U, copy.rsset_layout_regions[3].offset);
  m68k_analysis_policy_destroy(&copy);
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_rsset_layout_regions(&source, 300U));
  M68K_C_ASSERT(source.rsset_layout_regions != source.rsset_layout_regions_inline);
  M68K_C_ASSERT_STR("inline_last", source.rsset_layout_regions[3].symbol);
  source.rsset_layout_region_count = 300U;
  strcpy(source.rsset_layout_regions[299].symbol, "after_former_fixed_limit");
  source.rsset_layout_regions[299].offset = 1234U;
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT(copy.rsset_layout_regions != source.rsset_layout_regions);
  m68k_analysis_policy_destroy(&source);
  M68K_C_ASSERT_U32(300U, copy.rsset_layout_region_count);
  M68K_C_ASSERT_STR("after_former_fixed_limit", copy.rsset_layout_regions[299].symbol);
  M68K_C_ASSERT_U32(1234U, copy.rsset_layout_regions[299].offset);
  saved = copy.rsset_layout_regions;
  size_t oversized[] = {(size_t)M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT + 1U, SIZE_MAX};
  for (size_t index = 0U; index < sizeof(oversized)/sizeof(oversized[0]); ++index) {
    M68K_C_ASSERT_INT(M68K_ANALYSIS_POLICY_CAPACITY_EXCEEDED,
      m68k_analysis_policy_reserve_rsset_layout_regions(&copy, oversized[index]));
    M68K_C_ASSERT_U32(M68K_ANALYSIS_STORAGE_CAPACITY_RSSET_LAYOUT_REGIONS, copy.storage_capacity_status);
    M68K_C_ASSERT(copy.rsset_layout_regions == saved);
    M68K_C_ASSERT_U32(300U, copy.rsset_layout_region_count);
  }
  m68k_analysis_policy_destroy(&copy);
  m68k_analysis_policy_destroy(&copy);
  M68K_C_ASSERT(copy.rsset_layout_regions == copy.rsset_layout_regions_inline);
  M68K_C_ASSERT_U32(0U, copy.rsset_layout_region_count);
  M68K_C_ASSERT_U32(4U, copy.rsset_layout_region_capacity);
  m68k_analysis_policy_init_default(&source);
  source.rsset_layout_region_count = 5U; /* Inline storage cannot claim five facts. */
  copy.max_cpu = 42U;
  M68K_C_ASSERT_INT(-1, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT_U32(42U, copy.max_cpu);
  source.rsset_layout_region_count = 0U;
  source.rsset_layout_region_capacity = 300U;
  M68K_C_ASSERT_INT(-1, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT_U32(42U, copy.max_cpu);
  m68k_analysis_policy_destroy(&source);
  m68k_analysis_policy_destroy(&copy);
  return 0;
}

static int test_manual_data_references_required_family_and_capacity_clone(void) {
  M68kAnalysisPolicy source = {0}, copy = {0};
  uint16_t index;
  M68K_C_ASSERT_U32(512U, platform_file_manual_data_reference_count_capacity());
  for (index = 0U; index < M68K_ANALYSIS_MANUAL_DATA_REFERENCE_LIMIT; ++index) {
    M68kAnalysisManualDataReference *ref = &source.manual_data_references[index];
    ref->offset = (uint32_t)index * 2U;
    ref->size = 2U;
    ref->raw_value = 1U;
    ref->base_offset = 1024U;
    ref->target_offset = 1025U;
    ref->owner_element_offset = (uint32_t)index * 2U;
    snprintf(ref->owner_kind, sizeof(ref->owner_kind), "data_block_element");
    snprintf(ref->owner_id, sizeof(ref->owner_id), "reference_%u", (unsigned)index);
    snprintf(ref->owner_layout_id, sizeof(ref->owner_layout_id), "reference_family");
    snprintf(ref->xref_generation_mode, sizeof(ref->xref_generation_mode), "bidirectional");
  }
  source.manual_data_reference_count = 244U; /* Six existing and 238 remaining references. */
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT_U32(244U, copy.manual_data_reference_count);
  M68K_C_ASSERT_STR("reference_243", copy.manual_data_references[243U].owner_id);
  m68k_analysis_policy_destroy(&copy);
  source.manual_data_reference_count = M68K_ANALYSIS_MANUAL_DATA_REFERENCE_LIMIT;
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT(memcmp(source.manual_data_references, copy.manual_data_references,
    sizeof(source.manual_data_references)) == 0);
  memset(source.manual_data_references, 0, sizeof(source.manual_data_references));
  m68k_analysis_policy_destroy(&source);
  M68K_C_ASSERT_U32(512U, copy.manual_data_reference_count);
  M68K_C_ASSERT_STR("reference_511", copy.manual_data_references[511U].owner_id);
  m68k_analysis_policy_destroy(&copy);
  source = (M68kAnalysisPolicy){0};
  copy = (M68kAnalysisPolicy){0};
  source.manual_data_reference_count = M68K_ANALYSIS_MANUAL_DATA_REFERENCE_LIMIT + 1U;
  copy.max_cpu = 42U;
  M68K_C_ASSERT_INT(-1, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT_U32(42U, copy.max_cpu);
  M68K_C_ASSERT_U32(0U, copy.manual_data_reference_count);
  source.manual_data_reference_count = UINT16_MAX;
  M68K_C_ASSERT_INT(-1, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT_U32(42U, copy.max_cpu);
  m68k_analysis_policy_destroy(&source);
  m68k_analysis_policy_destroy(&copy);
  return 0;
}

static int test_data_and_labels_capacity_clone_and_wide_bounds(void) {
  M68kAnalysisPolicy source = {0}, copy = {0};
  M68kAnalysisStructuredDataItem *saved_data;
  M68kAnalysisNamedLabel *saved_labels;
  size_t oversized[] = {32769U, (size_t)UINT16_MAX + 1U, SIZE_MAX};
  size_t index;
  M68K_C_ASSERT_U32(32768U, platform_file_structured_data_item_count_capacity());
  M68K_C_ASSERT_U32(32768U, platform_file_named_label_count_capacity());
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_structured_data_items(&source, 4U));
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_named_labels(&source, 4U));
  M68K_C_ASSERT(source.structured_data_items == source.structured_data_items_inline);
  M68K_C_ASSERT(source.named_labels == source.named_labels_inline);
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_structured_data_items(&source, 32768U));
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_named_labels(&source, 32768U));
  source.structured_data_item_count = 32768U;
  source.named_label_count = 32768U;
  source.structured_data_items[32767U].offset = 12345U;
  snprintf(source.named_labels[32767U].name, sizeof(source.named_labels[32767U].name), "last_label");
  source.named_labels[32767U].is_source_declaration = 1U;
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT(copy.structured_data_items != source.structured_data_items);
  M68K_C_ASSERT(copy.named_labels != source.named_labels);
  source.structured_data_items[32767U].offset = 0U;
  source.named_labels[32767U].name[0] = '\0';
  m68k_analysis_policy_destroy(&source);
  M68K_C_ASSERT_U32(32768U, copy.structured_data_item_count);
  M68K_C_ASSERT_U32(32768U, copy.named_label_count);
  M68K_C_ASSERT_U32(12345U, copy.structured_data_items[32767U].offset);
  M68K_C_ASSERT_STR("last_label", copy.named_labels[32767U].name);
  M68K_C_ASSERT_U32(1U, copy.named_labels[32767U].is_source_declaration);
  saved_data = copy.structured_data_items;
  saved_labels = copy.named_labels;
  for (index = 0U; index < sizeof(oversized) / sizeof(oversized[0]); ++index) {
    M68K_C_ASSERT_INT(M68K_ANALYSIS_POLICY_CAPACITY_EXCEEDED,
      m68k_analysis_policy_reserve_structured_data_items(&copy, oversized[index]));
    M68K_C_ASSERT_U32(M68K_ANALYSIS_STORAGE_CAPACITY_STRUCTURED_DATA, copy.storage_capacity_status);
    M68K_C_ASSERT_INT(M68K_ANALYSIS_POLICY_CAPACITY_EXCEEDED,
      m68k_analysis_policy_reserve_named_labels(&copy, oversized[index]));
    M68K_C_ASSERT_U32(M68K_ANALYSIS_STORAGE_CAPACITY_NAMED_LABELS, copy.storage_capacity_status);
    M68K_C_ASSERT(copy.structured_data_items == saved_data && copy.named_labels == saved_labels);
    M68K_C_ASSERT_U32(32768U, copy.structured_data_item_count);
    M68K_C_ASSERT_U32(32768U, copy.named_label_count);
    M68K_C_ASSERT_U32(32768U, copy.structured_data_item_capacity);
    M68K_C_ASSERT_U32(32768U, copy.named_label_capacity);
  }
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_copy(&source, &copy));
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STORAGE_CAPACITY_NAMED_LABELS, source.storage_capacity_status);
  m68k_analysis_policy_destroy(&source);
  m68k_analysis_policy_destroy(&copy);
  m68k_analysis_policy_destroy(&copy);
  M68K_C_ASSERT(copy.structured_data_items == copy.structured_data_items_inline);
  M68K_C_ASSERT(copy.named_labels == copy.named_labels_inline);
  M68K_C_ASSERT_U32(4U, copy.structured_data_item_capacity);
  M68K_C_ASSERT_U32(4U, copy.named_label_capacity);
  M68K_C_ASSERT_U32(0U, copy.storage_capacity_status);
  return 0;
}

static int test_auto_data_exceeds_optional_policy_mirror(void) {
  M68kSourceAnalysisIR analysis;
  M68kAnalysisPolicy policy = {0}, copy = {0};
  M68kAnalysisStructuredDataItem item = {0};
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_create(&analysis));
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_structured_data_items(&policy, 32768U));
  policy.structured_data_item_count = 32768U;
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_set_policy(&analysis, &policy));
  item.offset = 123456U;
  item.size = 2U;
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_append_structured_data_item(&analysis, &item));
  M68K_C_ASSERT_U32(32769U, m68k_ir_source_analysis_structured_data_item_count(&analysis));
  M68K_C_ASSERT_U32(123456U, m68k_ir_source_analysis_structured_data_item_at(&analysis, 32768U)->offset);
  M68K_C_ASSERT_U32(32768U, analysis.policy.structured_data_item_count);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STORAGE_STRUCTURED_MIRROR_INCOMPLETE,
    analysis.policy.storage_capacity_status);
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_copy(&copy, &analysis.policy));
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STORAGE_STRUCTURED_MIRROR_INCOMPLETE, copy.storage_capacity_status);
  m68k_analysis_policy_destroy(&copy);
  m68k_analysis_policy_destroy(&policy);
  m68k_ir_source_analysis_destroy(&analysis);
  return 0;
}

static int test_data_and_labels_invalid_storage_preserves_destination(void) {
  M68kAnalysisPolicy source = {0}, copy = {0};
  copy.max_cpu = 42U;
  source.structured_data_item_count = 1U;
  M68K_C_ASSERT_INT(-1, m68k_analysis_policy_reserve_structured_data_items(&source, 1U));
  M68K_C_ASSERT_INT(-1, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT_U32(42U, copy.max_cpu);
  source.structured_data_item_count = 0U;
  source.named_labels = source.named_labels_inline;
  source.named_label_capacity = 5U;
  M68K_C_ASSERT_INT(-1, m68k_analysis_policy_reserve_named_labels(&source, 1U));
  M68K_C_ASSERT_INT(-1, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT_U32(42U, copy.max_cpu);
  m68k_analysis_policy_destroy(&source);
  m68k_analysis_policy_destroy(&copy);
  return 0;
}

static int test_target_equates_full_capacity_clone(void) {
  M68kAnalysisPolicy source = {0}, copy = {0};
  uint16_t index;
  M68K_C_ASSERT_U32(M68K_ANALYSIS_TARGET_EQUATE_LIMIT, platform_file_target_equate_count_capacity());
  source.target_equate_count = M68K_ANALYSIS_TARGET_EQUATE_LIMIT;
  for (index = 0U; index < source.target_equate_count; ++index) {
    snprintf(source.target_equates[index].name, sizeof(source.target_equates[index].name),
      "constant_%u", (unsigned)index);
    source.target_equates[index].value = index;
  }
  source.target_equates[source.target_equate_count - 1U].value_style_id =
    M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL;
  snprintf(source.target_equates[source.target_equate_count - 1U].value_expr,
    sizeof(source.target_equates[0].value_expr), "constant_0+%u", (unsigned)(M68K_ANALYSIS_TARGET_EQUATE_LIMIT - 1U));
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT_U32(source.target_equate_count, copy.target_equate_count);
  M68K_C_ASSERT(memcmp(source.target_equates, copy.target_equates, sizeof(source.target_equates)) == 0);
  memset(source.target_equates, 0, sizeof(source.target_equates));
  m68k_analysis_policy_destroy(&source);
  M68K_C_ASSERT_STR("constant_1023", copy.target_equates[copy.target_equate_count - 1U].name);
  M68K_C_ASSERT_STR("constant_0+1023", copy.target_equates[copy.target_equate_count - 1U].value_expr);
  M68K_C_ASSERT_INT(1023, copy.target_equates[copy.target_equate_count - 1U].value);
  m68k_analysis_policy_destroy(&copy);
  return 0;
}

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

static int test_comments_grow_clone_and_representable_boundary(void) {
  M68kAnalysisPolicy source = {0}, copy = {0};
  M68kAnalysisEntryComment *saved;
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_entry_comments(&source, 4U));
  M68K_C_ASSERT(source.entry_comments == source.entry_comments_inline);
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_entry_comments(&source, 513U));
  source.entry_comment_count = 513U;
  snprintf(source.entry_comments[512].comment, sizeof(source.entry_comments[512].comment), "last ] } \" annotation");
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT(source.entry_comments != copy.entry_comments);
  source.entry_comments[512].comment[0] = 0;
  m68k_analysis_policy_destroy(&source);
  M68K_C_ASSERT_STR("last ] } \" annotation", copy.entry_comments[512].comment);
  saved = copy.entry_comments;
  M68K_C_ASSERT_INT(M68K_ANALYSIS_POLICY_CAPACITY_EXCEEDED,
    m68k_analysis_policy_reserve_entry_comments(&copy, (size_t)UINT16_MAX + 1U));
  M68K_C_ASSERT(copy.entry_comments == saved);
  M68K_C_ASSERT_U32(513U, copy.entry_comment_count);
  M68K_C_ASSERT_INT(0, m68k_analysis_policy_reserve_entry_comments(&copy, UINT16_MAX));
  M68K_C_ASSERT_U32(UINT16_MAX, copy.entry_comment_capacity);
  m68k_analysis_policy_destroy(&copy);
  m68k_analysis_policy_destroy(&copy);
  M68K_C_ASSERT(copy.entry_comments == copy.entry_comments_inline);
  copy.max_cpu = 42U;
  source.entry_comment_count = 5U; /* Inline storage cannot hold this count. */
  M68K_C_ASSERT_INT(-1, m68k_analysis_policy_copy(&copy, &source));
  M68K_C_ASSERT_U32(42U, copy.max_cpu);
  source.entry_comment_count = 0U;
  m68k_analysis_policy_destroy(&source);
  return 0;
}

int m68k_c_policy_storage_tests(void) {
  static const M68kCTestCase cases[] = {
    {"comments_grow_clone_and_representable_boundary", test_comments_grow_clone_and_representable_boundary},
    {"register_seeds_growth_copy_and_count_bound", test_register_seeds_growth_copy_and_count_bound},
    {"rsset_regions_inline_growth_clone_and_identity_bound", test_rsset_regions_inline_growth_clone_and_identity_bound},
    {"manual_data_references_required_family_and_capacity_clone", test_manual_data_references_required_family_and_capacity_clone},
    {"data_and_labels_capacity_clone_and_wide_bounds", test_data_and_labels_capacity_clone_and_wide_bounds},
    {"auto_data_exceeds_optional_policy_mirror", test_auto_data_exceeds_optional_policy_mirror},
    {"data_and_labels_invalid_storage_preserves_destination", test_data_and_labels_invalid_storage_preserves_destination},
    {"target_equates_full_capacity_clone", test_target_equates_full_capacity_clone},
    {"manual_representations_inline_and_zero_init", test_manual_representations_inline_and_zero_init},
    {"manual_representations_heap_clone_growth_and_bound", test_manual_representations_heap_clone_growth_and_bound},
    {"manual_representations_invalid_copy_preserves_destination", test_manual_representations_invalid_copy_preserves_destination},
  };
  return m68k_c_test_run_suite("m68k_policy_storage", cases, sizeof(cases) / sizeof(cases[0]));
}
