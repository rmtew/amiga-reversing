#include "m68k_c_unit_test.h"
#include "m68k_source_package.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void package_fixture(M68kObject *object, M68kSection *section, uint8_t *bytes, M68kRenderPlan *plan) {
  memset(object, 0, sizeof(*object));
  memset(section, 0, sizeof(*section));
  section->kind = M68K_SECTION_DATA;
  section->data = bytes;
  section->size = section->data_size = 8U;
  object->sections = section;
  object->section_count = 1U;
  m68k_render_plan_init(plan);
}

static M68kRenderPlanRow *package_row(M68kRenderPlan *plan, uint32_t offset, uint32_t size, uint32_t flags) {
  M68kRenderPlanRow *row = NULL;
  if (m68k_render_plan_append_text_row(plan, M68K_RENDER_PLAN_ROW_DATA, 0U,
      "\tdc.b $01,$02,$03,$04\n", &row) != 0) return NULL;
  m68k_render_plan_row_set_source_range(row, 0U, offset, size);
  m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_DATA, NULL, NULL, 0U);
  m68k_render_plan_row_set_data_class_flags(row, flags);
  return row;
}

static int test_multiple_assets_are_deterministic_original_bytes(void) {
  M68kObject object;
  M68kSection section;
  M68kRenderPlan plan;
  uint8_t bytes[] = {1,2,3,4,5,6,7,8};
  char *first = NULL, *second = NULL;
  package_fixture(&object, &section, bytes, &plan);
  M68K_C_ASSERT(package_row(&plan, 0U, 4U, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP) != NULL);
  M68K_C_ASSERT(package_row(&plan, 4U, 4U, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SOUND_SAMPLE) != NULL);
  M68K_C_ASSERT_INT(0, m68k_source_package_json_alloc(&object, &plan, 4U, &first));
  M68K_C_ASSERT_INT(0, m68k_source_package_json_alloc(&object, &plan, 4U, &second));
  M68K_C_ASSERT(strcmp(first, second) == 0);
  M68K_C_ASSERT(strstr(first, "assets/provisional_asset_s0000_o00000000_n00000004.bin") != NULL);
  M68K_C_ASSERT(strstr(first, "assets/provisional_asset_s0000_o00000004_n00000004.bin") != NULL);
  M68K_C_ASSERT(strstr(first, "\"data_hex\":\"05060708\"") != NULL);
  M68K_C_ASSERT(strstr(first, "INCBIN") != NULL);
  M68K_C_ASSERT(strstr(first, "provisional_asset_s0000_o00000000_n00000004:\\u000A") != NULL);
  M68K_C_ASSERT(strstr(first, "\"name_is_generated\":true") != NULL);
  free(first); free(second);
  m68k_render_plan_destroy(&plan);
  return 0;
}

static int test_conservative_ineligibility(void) {
  M68kObject object;
  M68kSection section;
  M68kRenderPlan plan;
  M68kRenderPlanRow *row;
  M68kFixup fixup = {0};
  M68kRenderPlannedExpression expression = {0};
  M68kRenderPlannedLabel label = {0};
  uint8_t bytes[] = {1,2,3,4,5,6,7,8};
  char *json = NULL;
  unsigned scenario;
  for (scenario = 0; scenario < 11U; ++scenario) {
    package_fixture(&object, &section, bytes, &plan);
    row = package_row(&plan, 2U, 4U, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP);
    M68K_C_ASSERT(row != NULL);
    switch (scenario) {
      case 0: row->data_class_flags = 0U; break;
      case 1: row->data_class_flags |= M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE; break;
      case 2: row->statement_kind = M68K_STATEMENT_INSTRUCTION; break;
      case 3: section.data_size = 4U; break;
      case 4: row->has_statement_metadata = 0U; break;
      case 5: row->label_line_mask = 1U; break;
      case 6:
        fixup.offset = 0U; fixup.width = M68K_FIXUP_WIDTH_32;
        object.fixups = &fixup; object.fixup_count = 1U; break;
      case 7:
        expression.source_offset = 3U; expression.kind = M68K_RENDER_PLANNED_EXPRESSION_DATA_POINTER;
        expression.outcome = M68K_RENDER_PLANNED_EXPRESSION_NUMERIC;
        M68K_C_ASSERT_INT(0, m68k_render_plan_append_expression(&plan, &expression)); break;
      case 8:
        label.source_offset = 3U; strcpy(label.name, "interior");
        M68K_C_ASSERT_INT(0, m68k_render_plan_append_label(&plan, &label)); break;
      case 9: section.kind = M68K_SECTION_BSS; break;
      case 10: row->data_class_flags = M68K_ANALYSIS_STRUCTURED_DATA_ROLE_PALETTE; break;
    }
    M68K_C_ASSERT_INT(0, m68k_source_package_json_alloc(&object, &plan, 4U, &json));
    M68K_C_ASSERT(strstr(json, "\"assets\":[]") != NULL);
    M68K_C_ASSERT(strstr(json, "INCBIN") == NULL);
    free(json); json = NULL;
    m68k_render_plan_destroy(&plan);
  }
  return 0;
}

static int test_comments_and_leading_org_survive(void) {
  M68kObject object;
  M68kSection section;
  M68kRenderPlan plan;
  M68kRenderPlanRow *row;
  uint8_t bytes[] = {1,2,3,4,5,6,7,8};
  char *json = NULL;
  package_fixture(&object, &section, bytes, &plan);
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_DATA, 0U,
    "\tORG $1000\n; asset annotation\n\tdc.b $01,$02,$03,$04 ; preserved\n", &row));
  m68k_render_plan_row_set_source_range(row, 0U, 0U, 4U);
  m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_DATA, NULL, NULL, 0U);
  m68k_render_plan_row_set_data_class_flags(row, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP);
  row->directive_line_mask = 1U;
  M68K_C_ASSERT_INT(0, m68k_source_package_json_alloc(&object, &plan, 4U, &json));
  M68K_C_ASSERT(strstr(json, "ORG $1000") != NULL);
  M68K_C_ASSERT(strstr(json, "; asset annotation") != NULL);
  M68K_C_ASSERT(strstr(json, "ORG $1000") <
    strstr(json, "provisional_asset_s0000_o00000000_n00000004:"));
  M68K_C_ASSERT(strstr(json, "provisional_asset_s0000_o00000000_n00000004:\\u000A\\u0009INCBIN") != NULL);
  M68K_C_ASSERT(strstr(json, "; preserved") != NULL);
  M68K_C_ASSERT(strstr(json, "INCBIN") != NULL);
  free(json);
  m68k_render_plan_destroy(&plan);
  return 0;
}

static int test_coalesced_role_comments_are_compact(void) {
  M68kObject object;
  M68kSection section;
  M68kRenderPlan plan;
  M68kRenderPlanRow *row;
  uint8_t bytes[] = {1,2,3,4,5,6,7,8};
  char *json = NULL;
  const char *first;
  unsigned index;
  package_fixture(&object, &section, bytes, &plan);
  for (index = 0U; index < 2U; ++index) {
    M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_DATA, 0U,
      "\tdc.b $01,$02 ; bitmap\n\tdc.b $03,$04 ; bitmap consumer bound\n", &row));
    m68k_render_plan_row_set_source_range(row, 0U, index * 4U, 4U);
    m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_DATA, NULL, NULL, 0U);
    m68k_render_plan_row_set_data_class_flags(row, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP);
  }
  M68K_C_ASSERT_INT(0, m68k_source_package_json_alloc(&object, &plan, 8U, &json));
  first = strstr(json, "; bitmap\\u000A");
  M68K_C_ASSERT(first != NULL);
  M68K_C_ASSERT(strstr(first + 1, "; bitmap\\u000A") == NULL);
  first = strstr(json, "; bitmap consumer bound");
  M68K_C_ASSERT(first != NULL);
  M68K_C_ASSERT(strstr(first + 1, "; bitmap consumer bound") != NULL);
  M68K_C_ASSERT(strstr(json, "INCBIN") != NULL);
  free(json);
  m68k_render_plan_destroy(&plan);
  return 0;
}

static int test_large_asset_and_unfamiliar_layout(void) {
  M68kObject object;
  M68kSection section;
  M68kRenderPlan plan;
  M68kRenderPlanRow *row;
  uint8_t bytes[4096];
  char text[22000];
  char *json = NULL;
  size_t index;
  const char *line = "\tdc.b $01,$02,$03,$04,$05,$06,$07,$08,$09,$0a,$0b,$0c,$0d,$0e,$0f,$10\n";
  for (index = 0; index < sizeof(bytes); ++index) bytes[index] = (uint8_t)(index % 16U + 1U);
  text[0] = '\0';
  for (index = 0; index < 256U; ++index) strcat(text, line);
  package_fixture(&object, &section, bytes, &plan);
  section.size = section.data_size = sizeof(bytes);
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_DATA, 0U, text, &row));
  m68k_render_plan_row_set_source_range(row, 0U, 0U, sizeof(bytes));
  m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_DATA, NULL, NULL, 0U);
  m68k_render_plan_row_set_data_class_flags(row, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP);
  M68K_C_ASSERT_INT(0, m68k_source_package_json_alloc(&object, &plan, 256U, &json));
  M68K_C_ASSERT(strstr(json, "INCBIN") != NULL);
  M68K_C_ASSERT(strstr(json, "dc.b") == NULL);
  M68K_C_ASSERT(strstr(json, "\"size\":4096") != NULL);
  free(json);
  /* An unfamiliar expression at a late line must retain the entire row even
   * when the native expression table does not yet describe that spelling. */
  strcat(text, "\tdc.l hidden_pointer+4\n");
  m68k_render_plan_destroy(&plan);
  m68k_render_plan_init(&plan);
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_DATA, 0U, text, &row));
  m68k_render_plan_row_set_source_range(row, 0U, 0U, sizeof(bytes));
  m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_DATA, NULL, NULL, 0U);
  m68k_render_plan_row_set_data_class_flags(row, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP);
  M68K_C_ASSERT_INT(0, m68k_source_package_json_alloc(&object, &plan, 256U, &json));
  M68K_C_ASSERT(strstr(json, "INCBIN") == NULL);
  M68K_C_ASSERT(strstr(json, "hidden_pointer+4") != NULL);
  free(json);
  m68k_render_plan_destroy(&plan);
  return 0;
}

static int test_coalesces_small_rows_and_respects_boundaries(void) {
  unsigned scenario;
  for (scenario = 0U; scenario < 5U; ++scenario) {
    M68kObject object;
    M68kSection section;
    M68kRenderPlan plan;
    M68kRenderPlanRow *row;
    M68kRenderPlannedLabel label = {0};
    uint8_t bytes[] = {1,2,3,4,5,6,7,8};
    char *json = NULL;
    package_fixture(&object, &section, bytes, &plan);
    M68K_C_ASSERT(package_row(&plan, 0U, 4U, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP) != NULL);
    if (scenario == 4U)
      M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&plan, M68K_RENDER_PLAN_ROW_LABEL,
        0U, "separate_asset:\n", NULL));
    row = package_row(&plan, 4U, 4U, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP);
    M68K_C_ASSERT(row != NULL);
    if (scenario == 1U) row->region_id = 1U;
    if (scenario == 2U) m68k_render_plan_row_set_data_class_flags(row, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SOUND_SAMPLE);
    if (scenario == 3U) {
      label.source_offset = 4U; strcpy(label.name, "native_boundary");
      M68K_C_ASSERT_INT(0, m68k_render_plan_append_label(&plan, &label));
    }
    M68K_C_ASSERT_INT(0, m68k_source_package_json_alloc(&object, &plan, 8U, &json));
    if (scenario == 0U) {
      M68K_C_ASSERT(strstr(json, "INCBIN") != NULL);
      M68K_C_ASSERT(strstr(json, "\"size\":8") != NULL);
      M68K_C_ASSERT(strstr(json, "\"data_hex\":\"0102030405060708\"") != NULL);
      M68K_C_ASSERT(strstr(json, "\"source_row_count\":2") != NULL);
    } else {
      M68K_C_ASSERT(strstr(json, "INCBIN") == NULL);
      M68K_C_ASSERT(strstr(json, "\"assets\":[]") != NULL);
    }
    free(json);
    m68k_render_plan_destroy(&plan);
  }
  return 0;
}

static int package_label(M68kRenderPlan *plan, uint32_t offset, const char *name, int generated) {
  M68kRenderPlannedLabel label = {0};
  char text[104];
  label.source_offset = offset;
  label.name_is_generated = (uint8_t)generated;
  strcpy(label.name, name);
  snprintf(text, sizeof(text), "%s:\n", name);
  if (m68k_render_plan_append_label(plan, &label) != 0) return -1;
  return m68k_render_plan_append_text_row(plan, M68K_RENDER_PLAN_ROW_LABEL, 0U, text, NULL);
}

static int test_native_names_and_stable_identity(void) {
  M68kObject object;
  M68kSection section;
  M68kRenderPlan plan;
  uint8_t bytes[] = {1,2,3,4,5,6,7,8};
  char *json = NULL;
  unsigned pass;
  for (pass = 0U; pass < 2U; ++pass) {
    const char *name = pass ? "scene_pixel_cells_for_mask_bank_00" : "reviewed_pixel_cells";
    char expected[160];
    package_fixture(&object, &section, bytes, &plan);
    M68K_C_ASSERT_INT(0, package_label(&plan, 0U, name, 0));
    M68K_C_ASSERT(package_row(&plan, 0U, 4U, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP) != NULL);
    M68K_C_ASSERT_INT(0, m68k_source_package_json_alloc(&object, &plan, 4U, &json));
    snprintf(expected, sizeof(expected), "assets/%s.bin", name);
    M68K_C_ASSERT(strstr(json, expected) != NULL);
    snprintf(expected, sizeof(expected), "%s:\\u000A", name);
    M68K_C_ASSERT(strstr(json, expected) != NULL);
    M68K_C_ASSERT(strstr(json, "\"asset_id\":\"section-0000-offset-00000000-size-00000004\"") != NULL);
    M68K_C_ASSERT(strstr(json, "\"name_is_generated\":false") != NULL);
    M68K_C_ASSERT(strstr(json, "provisional_asset") == NULL);
    free(json); json = NULL;
    m68k_render_plan_destroy(&plan);
  }
  return 0;
}

static int test_provisional_and_portable_aliases(void) {
  const char *names[] = {"generated_0000", ".local_pixels", "unsafe/pixels", "CON"};
  unsigned scenario;
  for (scenario = 0U; scenario < sizeof(names) / sizeof(names[0]); ++scenario) {
    M68kObject object;
    M68kSection section;
    M68kRenderPlan plan;
    uint8_t bytes[] = {1,2,3,4,5,6,7,8};
    char *json = NULL;
    package_fixture(&object, &section, bytes, &plan);
    M68K_C_ASSERT_INT(0, package_label(&plan, 0U, names[scenario], scenario == 0U));
    M68K_C_ASSERT(package_row(&plan, 0U, 4U, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP) != NULL);
    M68K_C_ASSERT_INT(0, m68k_source_package_json_alloc(&object, &plan, 4U, &json));
    M68K_C_ASSERT(strstr(json, names[scenario]) != NULL);
    if (scenario == 1U) {
      M68K_C_ASSERT(strstr(json, "INCBIN") == NULL);
      M68K_C_ASSERT(strstr(json, "\"assets\":[]") != NULL);
      free(json);
      m68k_render_plan_destroy(&plan);
      continue;
    }
    if (scenario == 0U) {
      M68K_C_ASSERT(strstr(json, "assets/generated_0000.bin") != NULL);
      M68K_C_ASSERT(strstr(json, "\"name_is_generated\":true") != NULL);
      free(json);
      m68k_render_plan_destroy(&plan);
      continue;
    }
    M68K_C_ASSERT(strstr(json, "provisional_asset_s0000_o00000000_n00000004:\\u000A") != NULL);
    M68K_C_ASSERT(strstr(json, "assets/provisional_asset_s0000_o00000000_n00000004.bin") != NULL);
    M68K_C_ASSERT(strstr(json, "\"name_is_generated\":true") != NULL);
    free(json);
    m68k_render_plan_destroy(&plan);
  }
  return 0;
}

static int test_case_collision_and_symbol_reservations(void) {
  unsigned reverse;
  for (reverse = 0U; reverse < 2U; ++reverse) {
    M68kObject object;
    M68kSection section;
    M68kRenderPlan plan;
    M68kRenderPlannedDeclaration declaration = {0};
    M68kRenderPlannedRuntimeAlias runtime_alias = {0};
    uint8_t bytes[] = {1,2,3,4,5,6,7,8};
    char *json = NULL, *again = NULL;
    unsigned index;
    package_fixture(&object, &section, bytes, &plan);
    /* Both exact source spellings survive; every filesystem collision gets a
     * global alias. Native non-asset declarations and runtime aliases reserve
     * spellings too, even when they match the first disambiguation attempt. */
    strcpy(declaration.name, "Pixels__asset_s0000_o00000000_n00000004_0");
    M68K_C_ASSERT_INT(0, m68k_render_plan_append_declaration(&plan, &declaration));
    strcpy(runtime_alias.name, "pixels__asset_s0000_o00000004_n00000004_0");
    M68K_C_ASSERT_INT(0, m68k_render_plan_append_runtime_alias(&plan, &runtime_alias));
    for (index = 0U; index < 2U; ++index) {
      unsigned slot = reverse ? 1U - index : index;
      M68K_C_ASSERT_INT(0, package_label(&plan, slot * 4U, slot ? "pixels" : "Pixels", 0));
      M68K_C_ASSERT(package_row(&plan, slot * 4U, 4U, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP) != NULL);
    }
    M68K_C_ASSERT_INT(0, m68k_source_package_json_alloc(&object, &plan, 4U, &json));
    M68K_C_ASSERT_INT(0, m68k_source_package_json_alloc(&object, &plan, 4U, &again));
    M68K_C_ASSERT(strcmp(json, again) == 0);
    M68K_C_ASSERT(strstr(json, "assets/Pixels__asset_s0000_o00000000_n00000004_1.bin") != NULL);
    M68K_C_ASSERT(strstr(json, "assets/pixels__asset_s0000_o00000004_n00000004_1.bin") != NULL);
    M68K_C_ASSERT(strstr(json, "Pixels:\\u000A") != NULL);
    M68K_C_ASSERT(strstr(json, "pixels:\\u000A") != NULL);
    free(json); free(again);
    m68k_render_plan_destroy(&plan);
  }
  return 0;
}

static int test_full_native_basename_is_not_truncated(void) {
  M68kObject object;
  M68kSection section;
  M68kRenderPlan plan;
  uint8_t bytes[] = {1,2,3,4,5,6,7,8};
  char name[96], expected[112];
  char *json = NULL;
  memset(name, 'a', sizeof(name) - 1U);
  name[sizeof(name) - 1U] = '\0';
  package_fixture(&object, &section, bytes, &plan);
  M68K_C_ASSERT_INT(0, package_label(&plan, 0U, name, 0));
  M68K_C_ASSERT(package_row(&plan, 0U, 4U, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP) != NULL);
  M68K_C_ASSERT_INT(0, m68k_source_package_json_alloc(&object, &plan, 4U, &json));
  snprintf(expected, sizeof(expected), "assets/%s.bin", name);
  M68K_C_ASSERT(strstr(json, expected) != NULL);
  M68K_C_ASSERT(strstr(json, "\"name_is_generated\":false") != NULL);
  free(json);
  m68k_render_plan_destroy(&plan);
  return 0;
}

static int test_local_symbol_scope_blocks_new_alias_only(void) {
  unsigned scenario;
  for (scenario = 0U; scenario < 6U; ++scenario) {
    M68kObject object;
    M68kSection section;
    M68kRenderPlan plan;
    M68kRenderPlannedDeclaration declaration = {0};
    M68kRenderPlannedExpression expression = {0};
    M68kRenderPlannedInstruction instruction = {0};
    uint8_t bytes[] = {1,2,3,4,5,6,7,8};
    char *json = NULL;
    package_fixture(&object, &section, bytes, &plan);
    if (scenario == 0U || scenario >= 4U) {
      M68K_C_ASSERT_INT(0, package_label(&plan, 7U, ".later_local", 0));
    } else if (scenario == 1U) {
      strcpy(declaration.name, ".local_decl");
      M68K_C_ASSERT_INT(0, m68k_render_plan_append_declaration(&plan, &declaration));
    } else if (scenario == 2U) {
      instruction.instruction.operand_count = 1U;
      strcpy(instruction.instruction.operands[0].symbol_ref.name, ".local_operand");
      M68K_C_ASSERT_INT(0, m68k_render_plan_append_instruction(&plan, &instruction));
    } else {
      expression.source_offset = 7U;
      strcpy(expression.base_symbol, ".local_base");
      M68K_C_ASSERT_INT(0, m68k_render_plan_append_expression(&plan, &expression));
    }
    if (scenario >= 4U) M68K_C_ASSERT_INT(0, package_label(&plan, 0U, "known_pixels", scenario == 5U));
    M68K_C_ASSERT(package_row(&plan, 0U, 4U, M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP) != NULL);
    M68K_C_ASSERT_INT(0, m68k_source_package_json_alloc(&object, &plan, 4U, &json));
    if (scenario >= 4U) {
      M68K_C_ASSERT(strstr(json, "assets/known_pixels.bin") != NULL);
    } else {
      M68K_C_ASSERT(strstr(json, "INCBIN") == NULL);
      M68K_C_ASSERT(strstr(json, "\"assets\":[]") != NULL);
      M68K_C_ASSERT(strstr(json, "dc.b") != NULL);
    }
    free(json);
    m68k_render_plan_destroy(&plan);
  }
  return 0;
}

int m68k_c_source_package_tests(void) {
  static const M68kCTestCase cases[] = {
    {"local_symbol_scope_blocks_new_alias_only", test_local_symbol_scope_blocks_new_alias_only},
    {"full_native_basename_is_not_truncated", test_full_native_basename_is_not_truncated},
    {"native_names_and_stable_identity", test_native_names_and_stable_identity},
    {"provisional_and_portable_aliases", test_provisional_and_portable_aliases},
    {"case_collision_and_symbol_reservations", test_case_collision_and_symbol_reservations},
    {"multiple_assets_are_deterministic_original_bytes", test_multiple_assets_are_deterministic_original_bytes},
    {"conservative_ineligibility", test_conservative_ineligibility},
    {"comments_and_leading_org_survive", test_comments_and_leading_org_survive},
    {"coalesced_role_comments_are_compact", test_coalesced_role_comments_are_compact},
    {"large_asset_and_unfamiliar_layout", test_large_asset_and_unfamiliar_layout},
    {"coalesces_small_rows_and_respects_boundaries", test_coalesces_small_rows_and_respects_boundaries}
  };
  return m68k_c_test_run_suite("m68k_source_package", cases, sizeof(cases) / sizeof(cases[0]));
}
