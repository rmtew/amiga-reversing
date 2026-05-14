#include "m68k_source_data.h"
#include "m68k_parse_util.h"
#include "m68k_source_text_util.h"
#include "util_arena.h"

#include <stdio.h>
#include <string.h>

static int data_item_text_is_quoted(const char *text) {
  size_t length = text != NULL ? strlen(text) : 0U;
  return length >= 2U && ((text[0] == '"' && text[length - 1U] == '"') ||
                          (text[0] == '\'' && text[length - 1U] == '\''));
}

static int parse_data_item_text_local(Arena *scratch_arena, const char *text, AsmDataItem *out_item) {
  size_t length = strlen(text);
  memset(out_item, 0, sizeof(*out_item));
  out_item->repeat_count = 1U;
  if (data_item_text_is_quoted(text)) {
    out_item->kind = ASM_DATA_ITEM_STRING;
    out_item->byte_count = length - 2U;
    out_item->bytes = (uint8_t *)arena_alloc(scratch_arena, out_item->byte_count == 0U ? 1U : out_item->byte_count);
    if (out_item->bytes == NULL) return 0;
    if (out_item->byte_count != 0U) memcpy(out_item->bytes, text + 1, out_item->byte_count);
    return 1;
  }
  out_item->kind = ASM_DATA_ITEM_EXPR;
  if (length >= sizeof(out_item->expr)) return 0;
  snprintf(out_item->expr, sizeof(out_item->expr), "%s", text);
  return 1;
}

static int append_byte_data_item(AsmSourceDataStmt *out_data, const uint8_t *bytes, size_t byte_count,
    const M68kSourceDataParseContext *context) {
  AsmDataItem item;
  memset(&item, 0, sizeof(item));
  item.kind = ASM_DATA_ITEM_STRING;
  item.bytes = (uint8_t *)bytes;
  item.byte_count = byte_count;
  item.repeat_count = 1U;
  return context->append_item(out_data, &item, context->user_data);
}

int m68k_source_parse_data_statement(const char *directive, char *rest, AsmSourceDataStmt *out_data,
    const M68kSourceDataParseContext *context) {
  Arena *scratch_arena = NULL;
  char *buffer;
  char *items[64];
  uint8_t *byte_buffer = NULL;
  size_t byte_count = 0U;
  size_t count = 0;
  size_t index;
  int result = 0;
  M68kParseDataDirectiveResult data_directive = m68k_parse_data_directive_token(m68k_parse_source_directive_token(directive));
  if (!data_directive.ok || data_directive.is_repeat != 0U) return 0;
  out_data->width_bytes = data_directive.width_bytes;
  scratch_arena = arena_create(4096U);
  if (scratch_arena == NULL) return 0;
  buffer = (char *)arena_alloc(scratch_arena, strlen(rest) + 1U);
  if (buffer == NULL) goto cleanup;
  byte_buffer = (uint8_t *)arena_alloc(scratch_arena, strlen(rest) + 1U);
  if (byte_buffer == NULL) goto cleanup;
  strcpy(buffer, rest);
  if (!m68k_split_operands_in_place(buffer, items, 64U, &count)) goto cleanup;
  for (index = 0; index < count; ++index) {
    AsmDataItem item;
    char *item_text = m68k_trim_in_place(items[index]);
    if (data_directive.width_bytes == 1U && !data_item_text_is_quoted(item_text) &&
        context->parse_constant != NULL) {
      M68kSourceConstantResult constant = context->parse_constant(item_text, context->user_data);
      if (constant.ok) {
        byte_buffer[byte_count++] = (uint8_t)constant.value;
        continue;
      }
    }
    if (!parse_data_item_text_local(scratch_arena, item_text, &item)) goto cleanup;
    if (data_directive.width_bytes == 1U && item.kind == ASM_DATA_ITEM_STRING) {
      if (item.byte_count != 0U) {
        memcpy(byte_buffer + byte_count, item.bytes, item.byte_count);
        byte_count += item.byte_count;
      }
      continue;
    }
    if (byte_count != 0U) {
      if (!append_byte_data_item(out_data, byte_buffer, byte_count, context)) goto cleanup;
      byte_count = 0U;
    }
    if (!context->append_item(out_data, &item, context->user_data)) goto cleanup;
  }
  if (byte_count != 0U && !append_byte_data_item(out_data, byte_buffer, byte_count, context)) goto cleanup;
  result = 1;
cleanup:
  arena_destroy(scratch_arena);
  return result;
}

int m68k_source_parse_dcb_statement(const char *directive, char *rest, AsmSourceDataStmt *out_data,
    const M68kSourceDataParseContext *context) {
  Arena *scratch_arena = NULL;
  char *buffer;
  char *parts[2];
  size_t count = 0;
  uint32_t repeat_count = 0;
  AsmDataItem item;
  M68kSourceConstantResult repeat_result;
  int result = 0;
  M68kParseDataDirectiveResult data_directive = m68k_parse_data_directive_token(m68k_parse_source_directive_token(directive));
  if (!data_directive.ok || data_directive.is_repeat == 0U) return 0;
  out_data->width_bytes = data_directive.width_bytes;
  scratch_arena = arena_create(4096U);
  if (scratch_arena == NULL) return 0;
  buffer = (char *)arena_alloc(scratch_arena, strlen(rest) + 1U);
  if (buffer == NULL) goto cleanup;
  strcpy(buffer, rest);
  count = m68k_split_delimited_in_place(buffer, ',', parts, sizeof(parts) / sizeof(parts[0]));
  if (count != 1U && count != 2U) goto cleanup;
  repeat_result = context->parse_constant(m68k_trim_in_place(parts[0]), context->user_data);
  if (!repeat_result.ok) goto cleanup;
  repeat_count = repeat_result.value;
  if (!parse_data_item_text_local(scratch_arena, count == 2U ? m68k_trim_in_place(parts[1]) : "0", &item))
    goto cleanup;
  item.repeat_count = repeat_count;
  if (!context->append_item(out_data, &item, context->user_data)) goto cleanup;
  result = 1;
cleanup:
  arena_destroy(scratch_arena);
  return result;
}
