#include "m68k_source_rewrite.h"

#include "m68k_parse_util.h"
#include "m68k_source_text_util.h"

#include <stdio.h>
#include <string.h>

static int parse_rewrite_preamble(const char *line_text, char *line, size_t line_size,
    uint8_t *out_mnemonic_id, char *out_size_suffix, char **out_operand_text) {
  char *space;
  M68kParseMnemonicResult mnemonic_result;
  snprintf(line, line_size, "%s", line_text);
  m68k_strip_comment_in_place(line);
  strcpy(line, m68k_trim_in_place(line));
  m68k_normalize_register_alias_tokens_in_place(line);
  space = strchr(line, ' ');
  if (space == NULL) return 0;
  *space = '\0';
  *out_operand_text = m68k_trim_in_place(space + 1);
  if (**out_operand_text == '\0') return 0;
  mnemonic_result = m68k_parse_mnemonic_token(line);
  if (out_size_suffix != NULL) *out_size_suffix = mnemonic_result.size_suffix;
  if (out_mnemonic_id != NULL) *out_mnemonic_id = mnemonic_result.mnemonic_id;
  return mnemonic_result.mnemonic_id != M68K_ASM_MNEMONIC_NONE;
}

int m68k_rewrite_movea_symbolic_immediate_to_lea(const M68kSourceRewriteContext *context,
    const char *line_text, char *out_text, size_t out_text_size) {
  char line[256];
  uint8_t mnemonic_id = M68K_ASM_MNEMONIC_NONE;
  char size_suffix = '\0';
  char *operand_text = NULL;
  char *operands[4] = {NULL, NULL, NULL, NULL};
  size_t operand_count = 0;
  M68kParseRegisterResult reg_result;
  const char *inner = NULL;
  if (context == NULL) return 0;
  snprintf(out_text, out_text_size, "%s", line_text);
  if (!parse_rewrite_preamble(line_text, line, sizeof(line), &mnemonic_id, &size_suffix, &operand_text)) return 0;
  if (mnemonic_id != M68K_ASM_MNEMONIC_MOVEA || size_suffix != 'l') return 0;
  if (!m68k_split_operands_in_place(operand_text, operands, 4U, &operand_count) || operand_count != 2U) return 0;
  if (operands[0][0] != '#') return 0;
  inner = m68k_trim_in_place(operands[0] + 1);
  if (!context->is_symbol_name(inner, context->user_data)) return 0;
  reg_result = m68k_parse_register_token(m68k_trim_in_place(operands[1]), 'a');
  if (!reg_result.ok) return 0;
  if (context->is_constant_symbol(inner, context->user_data)) return 0;
  snprintf(out_text, out_text_size, "lea %s,%s", inner, m68k_trim_in_place(operands[1]));
  return 1;
}

int m68k_rewrite_move_immediate_to_moveq(const M68kSourceRewriteContext *context,
    const char *line_text, char *out_text, size_t out_text_size) {
  char line[256];
  uint8_t mnemonic_id = M68K_ASM_MNEMONIC_NONE;
  char size_suffix = '\0';
  char *operand_text = NULL;
  char *operands[4] = {NULL, NULL, NULL, NULL};
  size_t operand_count = 0;
  M68kParseRegisterResult reg_result;
  M68kSourceConstantResult value_result;
  int32_t signed_value = 0;
  if (context == NULL) return 0;
  if (!parse_rewrite_preamble(line_text, line, sizeof(line), &mnemonic_id, &size_suffix, &operand_text)) return 0;
  if (mnemonic_id != M68K_ASM_MNEMONIC_MOVE || size_suffix != 'l') return 0;
  if (!m68k_split_operands_in_place(operand_text, operands, 4U, &operand_count) || operand_count != 2U) return 0;
  if (operands[0][0] != '#') return 0;
  reg_result = m68k_parse_register_token(m68k_trim_in_place(operands[1]), 'd');
  if (!reg_result.ok) return 0;
  value_result = context->parse_constant(m68k_trim_in_place(operands[0] + 1), context->user_data);
  if (!value_result.ok) return 0;
  signed_value = (int32_t)value_result.value;
  if (signed_value < -128 || signed_value > 127) return 0;
  snprintf(out_text, out_text_size, "moveq #%d,%s", (int)signed_value, m68k_trim_in_place(operands[1]));
  return 1;
}
