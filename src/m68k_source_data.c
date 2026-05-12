#include "m68k_source_data.h"
#include "m68k_parse_util.h"
#include "m68k_source_text_util.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int parse_data_item_text_local(const char *text, AsmDataItem *out_item) {
  size_t length = strlen(text);
  memset(out_item, 0, sizeof(*out_item));
  if (length >= 2U && ((text[0] == '"' && text[length - 1U] == '"') || (text[0] == '\'' && text[length - 1U] == '\''))) {
    out_item->kind = ASM_DATA_ITEM_STRING;
    out_item->byte_count = length - 2U;
    out_item->bytes = (uint8_t *)malloc(out_item->byte_count == 0U ? 1U : out_item->byte_count);
    if (out_item->bytes == NULL) return 0;
    if (out_item->byte_count != 0U) memcpy(out_item->bytes, text + 1, out_item->byte_count);
    return 1;
  }
  out_item->kind = ASM_DATA_ITEM_EXPR;
  if (length >= sizeof(out_item->expr)) return 0;
  snprintf(out_item->expr, sizeof(out_item->expr), "%s", text);
  return 1;
}

int m68k_source_parse_data_statement(const char *directive, char *rest, AsmSourceDataStmt *out_data,
    const M68kSourceDataParseContext *context) {
  char *buffer;
  char *items[64];
  size_t count = 0;
  size_t index;
  M68kParseDataDirectiveResult data_directive = m68k_parse_data_directive_token(m68k_parse_source_directive_token(directive));
  if (!data_directive.ok || data_directive.is_repeat != 0U) return 0;
  out_data->width_bytes = data_directive.width_bytes;
  buffer = (char *)malloc(strlen(rest) + 1U);
  if (buffer == NULL) return 0;
  strcpy(buffer, rest);
  if (!m68k_split_operands_in_place(buffer, items, 64U, &count)) {
    free(buffer);
    return 0;
  }
  for (index = 0; index < count; ++index) {
    AsmDataItem item;
    if (!parse_data_item_text_local(items[index], &item)) {
      free(buffer);
      return 0;
    }
    if (!context->append_item(out_data, &item, context->user_data)) {
      free(item.bytes);
      free(buffer);
      return 0;
    }
    free(item.bytes);
  }
  free(buffer);
  return 1;
}

int m68k_source_parse_dcb_statement(const char *directive, char *rest, AsmSourceDataStmt *out_data,
    const M68kSourceDataParseContext *context) {
  char *buffer;
  char *parts[2];
  size_t count = 0;
  uint32_t repeat_count = 0;
  uint32_t index = 0;
  AsmDataItem item;
  M68kSourceConstantResult repeat_result;
  M68kParseDataDirectiveResult data_directive = m68k_parse_data_directive_token(m68k_parse_source_directive_token(directive));
  if (!data_directive.ok || data_directive.is_repeat == 0U) return 0;
  out_data->width_bytes = data_directive.width_bytes;
  buffer = (char *)malloc(strlen(rest) + 1U);
  if (buffer == NULL) return 0;
  strcpy(buffer, rest);
  count = m68k_split_delimited_in_place(buffer, ',', parts, sizeof(parts) / sizeof(parts[0]));
  if (count != 1U && count != 2U) {
    free(buffer);
    return 0;
  }
  repeat_result = context->parse_constant(m68k_trim_in_place(parts[0]), context->user_data);
  if (!repeat_result.ok) {
    free(buffer);
    return 0;
  }
  repeat_count = repeat_result.value;
  if (!parse_data_item_text_local(count == 2U ? m68k_trim_in_place(parts[1]) : "0", &item)) {
    free(buffer);
    return 0;
  }
  for (index = 0; index < repeat_count; ++index) {
    if (!context->append_item(out_data, &item, context->user_data)) {
      free(item.bytes);
      free(buffer);
      return 0;
    }
  }
  free(item.bytes);
  free(buffer);
  return 1;
}
