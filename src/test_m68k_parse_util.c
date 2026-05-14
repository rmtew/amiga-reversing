#include "m68k_c_unit_test.h"
#include "json_builder.h"
#include "m68k_bitset.h"
#include "m68k_parse_util.h"
#include "m68k_source_constant_expr.h"
#include "m68k_source_expr.h"
#include "m68k_source_text_util.h"

#include <string.h>
#include <stdlib.h>

static int test_sign_extend32(void) {
  M68K_C_ASSERT_U32(0xFFFFFFFFu, m68k_sign_extend32(0xFFu, 8));
  M68K_C_ASSERT_U32(0xFFFFFF80u, m68k_sign_extend32(0x80u, 8));
  M68K_C_ASSERT_U32(0x0000007Fu, m68k_sign_extend32(0x7Fu, 8));
  M68K_C_ASSERT_U32(0xFFFFFFF8u, m68k_sign_extend32(0xFFF8u, 16));
  return 0;
}

static int test_popcount16(void) {
  M68K_C_ASSERT_INT(0, (int)m68k_popcount16(0x0000u));
  M68K_C_ASSERT_INT(1, (int)m68k_popcount16(0x8000u));
  M68K_C_ASSERT_INT(8, (int)m68k_popcount16(0xF0F0u));
  M68K_C_ASSERT_INT(16, (int)m68k_popcount16(0xFFFFu));
  return 0;
}

static int test_parse_number_u32(void) {
  M68kParseU32Result result = m68k_parse_number_u32("$FF");
  M68K_C_ASSERT(result.ok);
  M68K_C_ASSERT_U32(0x000000FFu, result.value);
  result = m68k_parse_number_u32("-8");
  M68K_C_ASSERT(result.ok);
  M68K_C_ASSERT_U32(0xFFFFFFF8u, result.value);
  result = m68k_parse_number_u32("");
  M68K_C_ASSERT(!result.ok);
  return 0;
}

static int test_parse_cpu_name(void) {
  M68kParseCpuResult result = m68k_parse_cpu_name("68020");
  M68K_C_ASSERT(result.ok);
  M68K_C_ASSERT_INT(M68K_ASM_CPU_68020, result.cpu);
  result = m68k_parse_cpu_name("68060");
  M68K_C_ASSERT(result.ok);
  M68K_C_ASSERT_INT(M68K_ASM_CPU_68060, result.cpu);
  result = m68k_parse_cpu_name("any");
  M68K_C_ASSERT(result.ok);
  M68K_C_ASSERT_INT(M68K_ASM_CPU_ANY, result.cpu);
  result = m68k_parse_cpu_name("68008");
  M68K_C_ASSERT(!result.ok);
  return 0;
}

static int test_bitset_u32_helpers(void) {
  uint32_t bits = 0U;
  M68K_C_ASSERT_INT(0, m68k_bitset_u32_has(bits, 3U));
  m68k_bitset_u32_set(&bits, 3U);
  m68k_bitset_u32_set(&bits, 7U);
  M68K_C_ASSERT_U32((1U << 3U) | (1U << 7U), bits);
  M68K_C_ASSERT_INT(1, m68k_bitset_u32_has(bits, 3U));
  M68K_C_ASSERT_INT(1, m68k_bitset_u32_has(bits, 7U));
  m68k_bitset_u32_clear(&bits, 3U);
  M68K_C_ASSERT_INT(0, m68k_bitset_u32_has(bits, 3U));
  M68K_C_ASSERT_INT(1, m68k_bitset_u32_has(bits, 7U));
  m68k_bitset_u32_set(&bits, 32U);
  M68K_C_ASSERT_INT(0, m68k_bitset_u32_has(bits, 32U));
  M68K_C_ASSERT_U32(1U << 7U, bits);
  return 0;
}

static int test_parse_section_spec(void) {
  M68kSectionKind kind = M68K_SECTION_BSS;
  uint8_t mem_type = 0U;
  uint32_t mem_attrs = 0U;
  char text[32];
  M68K_C_ASSERT(m68k_parse_section_spec("code_c", &kind, &mem_type, &mem_attrs));
  M68K_C_ASSERT_INT(M68K_SECTION_CODE, kind);
  M68K_C_ASSERT_INT(1, mem_type);
  M68K_C_ASSERT_U32(0, mem_attrs);
  M68K_C_ASSERT(m68k_parse_section_spec("data_x$12345678", &kind, &mem_type, &mem_attrs));
  M68K_C_ASSERT_INT(M68K_SECTION_DATA, kind);
  M68K_C_ASSERT_INT(3, mem_type);
  M68K_C_ASSERT_U32(0x12345678U, mem_attrs);
  M68K_C_ASSERT(m68k_format_section_spec(M68K_SECTION_CODE, 2U, 0U, text, sizeof(text)));
  M68K_C_ASSERT_STR("code_f", text);
  return 0;
}

static int test_parse_mnemonic_token(void) {
  M68kParseMnemonicResult result = m68k_parse_mnemonic_token("movea.l");
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_MOVEA, result.mnemonic_id);
  M68K_C_ASSERT_INT('l', result.size_suffix);
  result = m68k_parse_mnemonic_token("BRA.S");
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_BRA, result.mnemonic_id);
  M68K_C_ASSERT_INT('b', result.size_suffix);
  result = m68k_parse_mnemonic_token("dbne");
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_DBNE, result.mnemonic_id);
  M68K_C_ASSERT_INT('\0', result.size_suffix);
  result = m68k_parse_mnemonic_token("move.l.extra");
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_NONE, result.mnemonic_id);
  return 0;
}

static int test_parse_special_register_token(void) {
  M68K_C_ASSERT_INT(M68K_ASM_OPERAND_CCR, m68k_parse_special_register_token("CCR"));
  M68K_C_ASSERT_INT(M68K_ASM_OPERAND_SR, m68k_parse_special_register_token("sr"));
  M68K_C_ASSERT_INT(M68K_ASM_OPERAND_USP, m68k_parse_special_register_token("Usp"));
  M68K_C_ASSERT_INT(M68K_ASM_OPERAND_NONE, m68k_parse_special_register_token("d0"));
  return 0;
}

static int test_parse_cache_selector_token(void) {
  M68kParseU32Result result = m68k_parse_cache_selector_token("dc");
  M68K_C_ASSERT(result.ok);
  M68K_C_ASSERT_U32(1u, result.value);
  result = m68k_parse_cache_selector_token("BC");
  M68K_C_ASSERT(result.ok);
  M68K_C_ASSERT_U32(3u, result.value);
  result = m68k_parse_cache_selector_token("xx");
  M68K_C_ASSERT(!result.ok);
  return 0;
}

static int test_parse_source_directive_token(void) {
  M68K_C_ASSERT_INT(M68K_SOURCE_DIRECTIVE_INCLUDE, m68k_parse_source_directive_token("include"));
  M68K_C_ASSERT_INT(M68K_SOURCE_DIRECTIVE_IFD, m68k_parse_source_directive_token("IFD"));
  M68K_C_ASSERT_INT(M68K_SOURCE_DIRECTIVE_SECTION, m68k_parse_source_directive_token("SECTION"));
  M68K_C_ASSERT_INT(M68K_SOURCE_DIRECTIVE_DCB_W, m68k_parse_source_directive_token("dcb.w"));
  M68K_C_ASSERT_INT(M68K_SOURCE_DIRECTIVE_DS_W, m68k_parse_source_directive_token("ds.w"));
  M68K_C_ASSERT_INT(M68K_SOURCE_DIRECTIVE_DS_L, m68k_parse_source_directive_token("DS.L"));
  M68K_C_ASSERT_INT(M68K_SOURCE_DIRECTIVE_ALIGNLONG, m68k_parse_source_directive_token("AlignLong"));
  M68K_C_ASSERT_INT(M68K_SOURCE_DIRECTIVE_NONE, m68k_parse_source_directive_token("move"));
  return 0;
}

static int test_parse_data_directive_token(void) {
  M68kParseDataDirectiveResult result = m68k_parse_data_directive_token(M68K_SOURCE_DIRECTIVE_DC_W);
  M68K_C_ASSERT(result.ok);
  M68K_C_ASSERT_INT(2, result.width_bytes);
  M68K_C_ASSERT_INT(0, result.is_repeat);
  result = m68k_parse_data_directive_token(M68K_SOURCE_DIRECTIVE_DCB_L);
  M68K_C_ASSERT(result.ok);
  M68K_C_ASSERT_INT(4, result.width_bytes);
  M68K_C_ASSERT_INT(1, result.is_repeat);
  result = m68k_parse_data_directive_token(M68K_SOURCE_DIRECTIVE_INCLUDE);
  M68K_C_ASSERT(!result.ok);
  return 0;
}

static int test_parse_offset_directive_token(void) {
  M68kParseOffsetDirectiveResult result = m68k_parse_offset_directive_token(M68K_SOURCE_DIRECTIVE_BYTE);
  M68K_C_ASSERT(result.ok);
  M68K_C_ASSERT_U32(1u, result.delta);
  result = m68k_parse_offset_directive_token(M68K_SOURCE_DIRECTIVE_APTR);
  M68K_C_ASSERT(result.ok);
  M68K_C_ASSERT_U32(4u, result.delta);
  result = m68k_parse_offset_directive_token(M68K_SOURCE_DIRECTIVE_DOUBLE);
  M68K_C_ASSERT(result.ok);
  M68K_C_ASSERT_U32(8u, result.delta);
  result = m68k_parse_offset_directive_token(M68K_SOURCE_DIRECTIVE_LIBENT);
  M68K_C_ASSERT(!result.ok);
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
  strcpy(text, "*-6");
  m68k_normalize_pc_current_expr_in_place(text);
  M68K_C_ASSERT_STR("*-6", text);
  return 0;
}

static M68kSourceLookupResult test_source_expr_lookup(const char *name, void *user_data) {
  M68kSourceLookupResult result = {0};
  (void)user_data;
  if (strcmp(name, "RTF_COLDSTART") == 0) {
    result.ok = 1U;
    result.defined = 1U;
    result.is_constant = 1U;
    result.value = 0x01U;
  } else if (strcmp(name, "RTF_AUTOINIT") == 0) {
    result.ok = 1U;
    result.defined = 1U;
    result.is_constant = 1U;
    result.value = 0x80U;
  }
  return result;
}

static int test_source_linear_expr_accepts_constant_or(void) {
  M68kSourceLinearExprParseResult parsed =
    m68k_source_parse_linear_expression("RTF_COLDSTART|RTF_AUTOINIT", 0, test_source_expr_lookup, NULL);
  M68kSourceLinearExprEvalResult evaluated = m68k_source_evaluate_linear_expression(parsed.expr);
  M68K_C_ASSERT(parsed.ok);
  M68K_C_ASSERT(evaluated.ok);
  M68K_C_ASSERT_U32(0x81U, evaluated.value);
  return 0;
}

static M68kSourceConstantResult test_constant_expr_lookup(const char *name, void *user_data) {
  M68kSourceConstantResult result = {0};
  (void)user_data;
  if (strcmp(name, "PMB_AWM") == 0) {
    result.ok = 1U;
    result.value = 1U;
  }
  return result;
}

static int test_source_constant_expr_accepts_division(void) {
  M68kSourceConstantResult result =
    m68k_source_parse_constant_expression("(PMB_AWM+7)/8", test_constant_expr_lookup, NULL);
  M68K_C_ASSERT(result.ok);
  M68K_C_ASSERT_U32(1U, result.value);
  M68K_C_ASSERT(!m68k_source_parse_constant_expression("8/0", test_constant_expr_lookup, NULL).ok);
  return 0;
}

static int test_json_builder_escapes_string_spans(void) {
  JsonBuilder builder = {0};
  char *text = NULL;
  M68K_C_ASSERT_INT(0, json_builder_create(&builder));
  M68K_C_ASSERT_INT(0, json_builder_append_json_string(&builder, "plain \"quote\" \\ slash\n\x01 end"));
  text = json_builder_build(&builder);
  M68K_C_ASSERT(text != NULL);
  M68K_C_ASSERT_STR("\"plain \\\"quote\\\" \\\\ slash\\u000A\\u0001 end\"", text);
  free(text);
  json_builder_destroy(&builder);
  return 0;
}

static int test_json_builder_appends_builder_without_building_source(void) {
  JsonBuilder outer = {0};
  JsonBuilder inner = {0};
  char *text = NULL;
  M68K_C_ASSERT_INT(0, json_builder_create(&outer));
  M68K_C_ASSERT_INT(0, json_builder_create(&inner));
  M68K_C_ASSERT_INT(0, json_builder_append(&outer, "{\"group\":"));
  M68K_C_ASSERT_INT(0, json_builder_append(&inner, "["));
  M68K_C_ASSERT_INT(0, json_builder_append_json_string(&inner, "a"));
  M68K_C_ASSERT_INT(0, json_builder_append(&inner, ","));
  M68K_C_ASSERT_INT(0, json_builder_append_json_string(&inner, "b"));
  M68K_C_ASSERT_INT(0, json_builder_append(&inner, "]"));
  M68K_C_ASSERT_INT(0, json_builder_append_builder(&outer, &inner));
  M68K_C_ASSERT_INT(0, json_builder_append(&outer, "}"));
  text = json_builder_build(&outer);
  M68K_C_ASSERT(text != NULL);
  M68K_C_ASSERT_STR("{\"group\":[\"a\",\"b\"]}", text);
  free(text);
  json_builder_destroy(&inner);
  json_builder_destroy(&outer);
  return 0;
}

static int test_json_builder_builds_into_caller_arena(void) {
  JsonBuilder builder = {0};
  Arena *arena = arena_create(128U);
  char *text = NULL;
  M68K_C_ASSERT(arena != NULL);
  M68K_C_ASSERT_INT(0, json_builder_create(&builder));
  M68K_C_ASSERT_INT(0, json_builder_append(&builder, "arena text"));
  text = json_builder_build_arena(&builder, arena);
  M68K_C_ASSERT(text != NULL);
  json_builder_destroy(&builder);
  M68K_C_ASSERT_STR("arena text", text);
  arena_destroy(arena);
  return 0;
}

int m68k_c_parse_util_tests(void) {
  static const M68kCTestCase cases[] = {
    {"sign_extend32", test_sign_extend32},
    {"popcount16", test_popcount16},
    {"bitset_u32_helpers", test_bitset_u32_helpers},
    {"parse_number_u32", test_parse_number_u32},
    {"parse_cpu_name", test_parse_cpu_name},
    {"parse_section_spec", test_parse_section_spec},
    {"parse_mnemonic_token", test_parse_mnemonic_token},
    {"parse_special_register_token", test_parse_special_register_token},
    {"parse_cache_selector_token", test_parse_cache_selector_token},
    {"parse_source_directive_token", test_parse_source_directive_token},
    {"parse_data_directive_token", test_parse_data_directive_token},
    {"parse_offset_directive_token", test_parse_offset_directive_token},
    {"normalize_pc_current_expr", test_normalize_pc_current_expr},
    {"source_linear_expr_accepts_constant_or", test_source_linear_expr_accepts_constant_or},
    {"source_constant_expr_accepts_division", test_source_constant_expr_accepts_division},
    {"json_builder_escapes_string_spans", test_json_builder_escapes_string_spans},
    {"json_builder_appends_builder_without_building_source", test_json_builder_appends_builder_without_building_source},
    {"json_builder_builds_into_caller_arena", test_json_builder_builds_into_caller_arena},
  };
  return m68k_c_test_run_suite("m68k_parse_util", cases, sizeof(cases) / sizeof(cases[0]));
}
