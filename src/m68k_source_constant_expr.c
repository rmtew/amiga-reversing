#include "m68k_source_constant_expr.h"

#include "m68k_parse_util.h"

#include <ctype.h>
#include <string.h>

static void skip_expression_spaces(const char **cursor) {
  while (**cursor != '\0' && isspace((unsigned char)**cursor)) ++(*cursor);
}

static int parse_constant_expression_or(const char **cursor, M68kSourceConstantLookupFn lookup, void *user_data,
  int32_t *out_value);

static int parse_constant_expression_primary(const char **cursor, M68kSourceConstantLookupFn lookup, void *user_data,
    int32_t *out_value) {
  char token[128];
  size_t length = 0;
  M68kParseU32Result parse_result;
  skip_expression_spaces(cursor);
  if (**cursor == '(') {
    ++(*cursor);
    if (!parse_constant_expression_or(cursor, lookup, user_data, out_value)) return 0;
    skip_expression_spaces(cursor);
    if (**cursor != ')') return 0;
    ++(*cursor);
    return 1;
  }
  if (**cursor == '\'') {
    ++(*cursor);
    if (**cursor == '\0' || (*cursor)[1] != '\'') return 0;
    *out_value = (unsigned char)**cursor;
    *cursor += 2;
    return 1;
  }
  if (**cursor == '+' || **cursor == '-') {
    int sign = (**cursor == '-') ? -1 : 1;
    ++(*cursor);
    if (!parse_constant_expression_primary(cursor, lookup, user_data, out_value)) return 0;
    *out_value *= sign;
    return 1;
  }
  while ((*cursor)[length] != '\0'
    && !isspace((unsigned char)(*cursor)[length])
    && (*cursor)[length] != '+'
    && (*cursor)[length] != '-'
    && (*cursor)[length] != '*'
    && (*cursor)[length] != '('
    && (*cursor)[length] != ')'
    && (*cursor)[length] != '|'
    && (*cursor)[length] != '!'
    && (*cursor)[length] != '<'
    && (*cursor)[length] != '>') {
    ++length;
  }
  if (length == 0U || length >= sizeof(token)) return 0;
  memcpy(token, *cursor, length);
  token[length] = '\0';
  *cursor += length;
  parse_result = m68k_parse_number_u32(token);
  if (parse_result.ok) {
    *out_value = (int32_t)parse_result.value;
    return 1;
  }
  {
    M68kSourceConstantResult lookup_result = lookup(token, user_data);
    if (!lookup_result.ok) return 0;
    *out_value = (int32_t)lookup_result.value;
  }
  return 1;
}

static int parse_constant_expression_mul(const char **cursor, M68kSourceConstantLookupFn lookup, void *user_data,
    int32_t *out_value) {
  int32_t value = 0;
  if (!parse_constant_expression_primary(cursor, lookup, user_data, &value)) return 0;
  while (1) {
    int32_t rhs = 0;
    skip_expression_spaces(cursor);
    if (**cursor != '*') break;
    ++(*cursor);
    if (!parse_constant_expression_primary(cursor, lookup, user_data, &rhs)) return 0;
    value *= rhs;
  }
  *out_value = value;
  return 1;
}

static int parse_constant_expression_add(const char **cursor, M68kSourceConstantLookupFn lookup, void *user_data,
    int32_t *out_value) {
  int32_t value = 0;
  if (!parse_constant_expression_mul(cursor, lookup, user_data, &value)) return 0;
  while (1) {
    int32_t rhs = 0;
    int op = 0;
    skip_expression_spaces(cursor);
    if (**cursor != '+' && **cursor != '-') break;
    op = **cursor;
    ++(*cursor);
    if (!parse_constant_expression_mul(cursor, lookup, user_data, &rhs)) return 0;
    value = (op == '+') ? (value + rhs) : (value - rhs);
  }
  *out_value = value;
  return 1;
}

static int parse_constant_expression_shift(const char **cursor, M68kSourceConstantLookupFn lookup, void *user_data,
    int32_t *out_value) {
  int32_t value = 0;
  if (!parse_constant_expression_add(cursor, lookup, user_data, &value)) return 0;
  while (1) {
    int32_t rhs = 0;
    skip_expression_spaces(cursor);
    if ((*cursor)[0] != '<' || (*cursor)[1] != '<') break;
    *cursor += 2;
    if (!parse_constant_expression_add(cursor, lookup, user_data, &rhs)) return 0;
    value = (int32_t)((uint32_t)value << rhs);
  }
  *out_value = value;
  return 1;
}

static int parse_constant_expression_or(const char **cursor, M68kSourceConstantLookupFn lookup, void *user_data,
    int32_t *out_value) {
  int32_t value = 0;
  if (!parse_constant_expression_shift(cursor, lookup, user_data, &value)) return 0;
  while (1) {
    int32_t rhs = 0;
    skip_expression_spaces(cursor);
    if (**cursor != '|' && **cursor != '!') break;
    ++(*cursor);
    if (!parse_constant_expression_shift(cursor, lookup, user_data, &rhs)) return 0;
    value = (int32_t)((uint32_t)value | (uint32_t)rhs);
  }
  *out_value = value;
  return 1;
}

M68kSourceConstantResult m68k_source_parse_constant_expression(const char *text, M68kSourceConstantLookupFn lookup,
    void *user_data) {
  M68kSourceConstantResult result = {0};
  const char *cursor = text;
  int32_t value = 0;
  if (text == NULL || lookup == NULL) return result;
  if (!parse_constant_expression_or(&cursor, lookup, user_data, &value)) return result;
  skip_expression_spaces(&cursor);
  if (*cursor != '\0') return result;
  result.ok = 1U;
  result.value = (uint32_t)value;
  return result;
}
