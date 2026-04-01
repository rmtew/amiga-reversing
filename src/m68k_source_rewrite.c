#include "m68k_source_rewrite.h"

#include "m68k_parse_util.h"
#include "m68k_source_text_util.h"

#include <stdio.h>
#include <string.h>

static int parse_rewrite_preamble(const char *line_text, char *line, size_t line_size,
    char *mnemonic, size_t mnemonic_size, char **out_operand_text) {
    char *space;
    snprintf(line, line_size, "%s", line_text);
    m68k_strip_comment_in_place(line);
    strcpy(line, m68k_trim_in_place(line));
    m68k_normalize_register_alias_tokens_in_place(line);
    space = strchr(line, ' ');
    if (space == NULL) return 0;
    *space = '\0';
    *out_operand_text = m68k_trim_in_place(space + 1);
    if (**out_operand_text == '\0') return 0;
    snprintf(mnemonic, mnemonic_size, "%s", line);
    return 1;
}

int m68k_rewrite_movea_symbolic_immediate_to_lea(const M68kSourceRewriteContext *context,
    const char *line_text, char *out_text, size_t out_text_size) {
    char line[256];
    char mnemonic[32];
    char *operand_text = NULL;
    char *operands[4] = {NULL, NULL, NULL, NULL};
    size_t operand_count = 0;
    uint8_t reg = 0;
    const char *inner = NULL;
    if (context == NULL) return 0;
    snprintf(out_text, out_text_size, "%s", line_text);
    if (!parse_rewrite_preamble(line_text, line, sizeof(line), mnemonic, sizeof(mnemonic), &operand_text)) return 0;
    if (_stricmp(mnemonic, "movea.l") != 0) return 0;
    if (!m68k_split_operands_in_place(operand_text, operands, 4U, &operand_count) || operand_count != 2U) return 0;
    if (operands[0][0] != '#') return 0;
    inner = m68k_trim_in_place(operands[0] + 1);
    if (!context->is_symbol_name(inner, context->user_data)) return 0;
    if (!m68k_parse_register_token(m68k_trim_in_place(operands[1]), 'a', &reg)) return 0;
    if (context->is_constant_symbol(inner, context->user_data)) return 0;
    snprintf(out_text, out_text_size, "lea %s,%s", inner, m68k_trim_in_place(operands[1]));
    return 1;
}

int m68k_rewrite_move_immediate_to_moveq(const M68kSourceRewriteContext *context,
    const char *line_text, char *out_text, size_t out_text_size) {
    char line[256];
    char mnemonic[32];
    char *operand_text = NULL;
    char *operands[4] = {NULL, NULL, NULL, NULL};
    size_t operand_count = 0;
    uint8_t reg = 0;
    uint32_t value = 0;
    int32_t signed_value = 0;
    if (context == NULL) return 0;
    if (!parse_rewrite_preamble(line_text, line, sizeof(line), mnemonic, sizeof(mnemonic), &operand_text)) return 0;
    if (_stricmp(mnemonic, "move.l") != 0) return 0;
    if (!m68k_split_operands_in_place(operand_text, operands, 4U, &operand_count) || operand_count != 2U) return 0;
    if (operands[0][0] != '#' || !m68k_parse_register_token(m68k_trim_in_place(operands[1]), 'd', &reg)) return 0;
    if (!context->parse_constant(m68k_trim_in_place(operands[0] + 1), &value, context->user_data)) return 0;
    signed_value = (int32_t)value;
    if (signed_value < -128 || signed_value > 127) return 0;
    snprintf(out_text, out_text_size, "moveq #%d,%s", (int)signed_value, m68k_trim_in_place(operands[1]));
    return 1;
}
