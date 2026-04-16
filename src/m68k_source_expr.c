#include "m68k_source_expr.h"

#include "m68k_parse_util.h"

#include <ctype.h>
#include <string.h>

M68kSourceLinearExprParseResult m68k_source_parse_linear_expression(const char *text, int constants_only,
    M68kSourceExprLookupFn lookup, void *user_data) {
  M68kSourceLinearExprParseResult result;
  const char *cursor = text;
  int sign = 1;
  memset(&result, 0, sizeof(result));
  result.expr.valid = 1;
  while (1) {
    char token[128];
    size_t token_length = 0;
    M68kParseU32Result parse_result;
    while (*cursor != '\0' && isspace((unsigned char)*cursor)) ++cursor;
    if (*cursor == '+') {
      sign = 1;
      ++cursor;
      continue;
    }
    if (*cursor == '-') {
      sign = -1;
      ++cursor;
      continue;
    }
    if (*cursor == '\0') break;
    while (cursor[token_length] != '\0'
      && cursor[token_length] != '+'
      && cursor[token_length] != '-'
      && !isspace((unsigned char)cursor[token_length])) {
      ++token_length;
    }
    if (token_length == 0U || token_length >= sizeof(token)) return result;
    memcpy(token, cursor, token_length);
    token[token_length] = '\0';
    cursor += token_length;
    parse_result = m68k_parse_number_u32(token);
    if (parse_result.ok) {
      result.expr.constant += sign * (int32_t)parse_result.value;
    } else {
      M68kSourceLookupResult lookup_result = lookup(token, user_data);
      if (!lookup_result.ok || !lookup_result.defined) return result;
      if (lookup_result.is_constant) {
        result.expr.constant += sign * (int32_t)lookup_result.value;
      } else {
        if (constants_only || result.expr.symbol_count >= 2U) return result;
        result.expr.symbol_ids[result.expr.symbol_count] = lookup_result.symbol_id;
        result.expr.section_indices[result.expr.symbol_count] = lookup_result.section_index;
        result.expr.symbol_signs[result.expr.symbol_count] = sign;
        result.expr.constant += sign * (int32_t)lookup_result.value;
        result.expr.symbol_count += 1U;
      }
    }
    sign = 1;
  }
  result.ok = 1;
  return result;
}

M68kSourceLinearExprEvalResult m68k_source_evaluate_linear_expression(M68kSourceLinearExpr expr) {
  M68kSourceLinearExprEvalResult result;
  int32_t value = expr.constant;
  memset(&result, 0, sizeof(result));
  if (!expr.valid) return result;
  result.value = (uint32_t)value;
  if (expr.symbol_count == 0U) {
    result.ok = 1;
    return result;
  }
  if (expr.symbol_count == 1U && expr.symbol_signs[0] == 1) {
    result.ok = 1;
    result.reloc.ok = 1;
    result.reloc.target_section = expr.section_indices[0];
    return result;
  }
  if (expr.symbol_count == 2U && expr.symbol_signs[0] == 1 && expr.symbol_signs[1] == -1) {
    if (expr.section_indices[0] != expr.section_indices[1]) return result;
    result.ok = 1;
    return result;
  }
  memset(&result, 0, sizeof(result));
  return result;
}
