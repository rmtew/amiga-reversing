#include "m68k_symbolic_parse.h"

#include "m68k_parse_util.h"
#include "m68k_plain_parse.h"
#include "m68k_source_constant_expr.h"
#include "m68k_source_text_util.h"

#include <ctype.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

static int is_register_like_symbol(const char *text, uint8_t target_cpu) {
  uint8_t reg = 0;
  uint8_t control_id = 0;
  uint32_t control_value = 0;
  return m68k_parse_register_token(text, 'd', &reg) || m68k_parse_register_token(text, 'a', &reg) ||
    _stricmp(text, "sp") == 0 || _stricmp(text, "pc") == 0 ||
    m68k_parse_control_register_token(text, target_cpu, &control_id, &control_value);
}

static int mnemonic_uses_relative_label_operand(const char *mnemonic) {
  static const char *const LABEL_MNEMONICS[] = {
      "bra",  "bsr",  "bhi",  "bls",  "bcc",  "bcs",  "bne",  "beq",
      "bvc",  "bvs",  "bpl",  "bmi",  "bge",  "blt",  "bgt",  "ble",
      "dbt",  "dbf",  "dbhi", "dbls", "dbcc", "dbcs", "dbne", "dbeq",
      "dbvc", "dbvs", "dbpl", "dbmi", "dbge", "dblt", "dbgt", "dble"};
  size_t index;
  for (index = 0; index < sizeof(LABEL_MNEMONICS) / sizeof(LABEL_MNEMONICS[0]); ++index) {
    if (_stricmp(mnemonic, LABEL_MNEMONICS[index]) == 0)
      return 1;
  }
  return 0;
}

static int lookup_constant_symbol_for_expression(const char *name, uint32_t *out_value, void *user_data) {
  const M68kSymbolicParseContext *context = (const M68kSymbolicParseContext *)user_data;
  if (context == NULL || context->lookup_symbol == NULL) return 0;
  return context->lookup_symbol(name, out_value, 1, context->user_data);
}

static void mark_ir_symbol_ref_kind(M68kOperandIR *operand) {
  if (operand == NULL || !operand->symbol_ref.has_name) return;
  if (operand->kind == M68K_ASM_OPERAND_LABEL) {
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_PC_REL;
  } else if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 7 &&
      (operand->value.ea_reg == 2 || operand->value.ea_reg == 3)) {
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_PC_REL;
  } else {
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_ABS;
  }
}

static int parse_symbol_plus_addend(const M68kSymbolicParseContext *context, const char *text,
    char *out_symbolic_name, size_t out_symbolic_name_size, int32_t *out_addend) {
  const char *cursor = text;
  const char *sign_pos = NULL;
  char symbol[M68K_INSTRUCTION_SPEC_MAX_LABEL_NAME];
  int32_t value = 0;
  if (context == NULL || text == NULL || out_symbolic_name == NULL || out_addend == NULL) return 0;
  if (*cursor == '\0') return 0;
  while (*cursor != '\0') {
    if ((*cursor == '+' || *cursor == '-') && cursor != text) {
      sign_pos = cursor;
      break;
    }
    ++cursor;
  }
  if (sign_pos == NULL) {
    if (context->is_symbol_name == NULL || !context->is_symbol_name(text, context->user_data)) return 0;
    if (is_register_like_symbol(text, context->target_cpu)) return 0;
    snprintf(out_symbolic_name, out_symbolic_name_size, "%s", text);
    *out_addend = 0;
    return 1;
  }
  if ((size_t)(sign_pos - text) >= sizeof(symbol)) return 0;
  snprintf(symbol, sizeof(symbol), "%.*s", (int)(sign_pos - text), text);
  if (context->is_symbol_name == NULL || !context->is_symbol_name(symbol, context->user_data)) return 0;
  if (is_register_like_symbol(symbol, context->target_cpu)) return 0;
  if (*(sign_pos + 1) == '\0') return 0;
  value = (int32_t)strtol(sign_pos + 1, NULL, 0);
  if (*sign_pos == '-') value = -value;
  snprintf(out_symbolic_name, out_symbolic_name_size, "%s", symbol);
  *out_addend = (int32_t)value;
  return 1;
}

static int rewrite_pc_relative_symbol_operand( const M68kSymbolicParseContext *context, const char *operand, char *out_rewritten,
    size_t out_rewritten_size, char *out_symbolic_name, size_t out_symbolic_name_size, int32_t *out_addend) {
  const char *paren = NULL;
  size_t prefix_len;
  char prefix[M68K_INSTRUCTION_SPEC_MAX_LABEL_NAME];
  if (context == NULL || operand == NULL || out_rewritten == NULL || out_symbolic_name == NULL || out_addend == NULL)
    return 0;
  paren = strchr(operand, '(');
  if (paren == NULL || paren == operand) return 0;
  if (_strnicmp(paren, "(pc", 3) != 0) return 0;
  prefix_len = (size_t)(paren - operand);
  if (prefix_len == 0U || prefix_len >= sizeof(prefix)) return 0;
  snprintf(prefix, sizeof(prefix), "%.*s", (int)prefix_len, operand);
  if (!parse_symbol_plus_addend(context, prefix, out_symbolic_name, out_symbolic_name_size, out_addend)) return 0;
  snprintf(out_rewritten, out_rewritten_size, "$0%s", paren);
  return 1;
}

static int rewrite_base_relative_symbol_operand(const M68kSymbolicParseContext *context, const char *operand,
    char *out_rewritten, size_t out_rewritten_size, char *out_symbolic_name, size_t out_symbolic_name_size) {
  const char *paren = NULL;
  uint32_t symbol_value = 0;
  size_t prefix_len;
  char prefix[M68K_INSTRUCTION_SPEC_MAX_LABEL_NAME];
  if (context == NULL || operand == NULL || out_rewritten == NULL || out_symbolic_name == NULL) return 0;
  paren = strchr(operand, '(');
  if (paren == NULL || paren == operand) return 0;
  if (_strnicmp(paren, "(a", 2) != 0) return 0;
  prefix_len = (size_t)(paren - operand);
  if (prefix_len == 0U || prefix_len >= sizeof(prefix)) return 0;
  snprintf(prefix, sizeof(prefix), "%.*s", (int)prefix_len, operand);
  if (context->lookup_symbol != NULL &&
      m68k_source_parse_constant_expression(prefix, lookup_constant_symbol_for_expression,
        (void *)context, &symbol_value)) {
    snprintf(out_rewritten, out_rewritten_size, "%d%s", (int32_t)symbol_value, paren);
    out_symbolic_name[0] = '\0';
    return 1;
  }
  if (context->is_symbol_name == NULL || !context->is_symbol_name(prefix, context->user_data)) return 0;
  if (is_register_like_symbol(prefix, context->target_cpu)) return 0;
  snprintf(out_rewritten, out_rewritten_size, "0%s", paren);
  snprintf(out_symbolic_name, out_symbolic_name_size, "%s", prefix);
  return 1;
}

static int rewrite_absolute_constant_operand(const M68kSymbolicParseContext *context, const char *operand,
    char *out_rewritten, size_t out_rewritten_size) {
  const char *suffix = strrchr(operand, '.');
  uint32_t value = 0;
  char expr[128];
  size_t expr_len;
  if (context == NULL || operand == NULL || out_rewritten == NULL) return 0;
  if (strchr(operand, '(') != NULL || strchr(operand, ',') != NULL) return 0;
  if (suffix == NULL || (_stricmp(suffix, ".w") != 0 && _stricmp(suffix, ".l") != 0)) return 0;
  expr_len = (size_t)(suffix - operand);
  if (expr_len == 0U || expr_len >= sizeof(expr)) return 0;
  snprintf(expr, sizeof(expr), "%.*s", (int)expr_len, operand);
  if (!m68k_source_parse_constant_expression(expr, lookup_constant_symbol_for_expression, (void *)context, &value))
    return 0;
  snprintf(out_rewritten, out_rewritten_size, "$%x%s", value, suffix);
  return 1;
}

static int rewrite_absolute_symbol_operand(const M68kSymbolicParseContext *context, const char *operand,
    char *out_rewritten, size_t out_rewritten_size, char *out_symbolic_name, size_t out_symbolic_name_size) {
  const char *suffix = strrchr(operand, '.');
  char symbol[M68K_INSTRUCTION_SPEC_MAX_LABEL_NAME];
  size_t symbol_len;
  if (context == NULL || operand == NULL || out_rewritten == NULL || out_symbolic_name == NULL) return 0;
  if (strchr(operand, '(') != NULL || strchr(operand, ',') != NULL || operand[0] == '#') return 0;
  if (suffix == NULL || (_stricmp(suffix, ".w") != 0 && _stricmp(suffix, ".l") != 0)) return 0;
  symbol_len = (size_t)(suffix - operand);
  if (symbol_len == 0U || symbol_len >= sizeof(symbol)) return 0;
  snprintf(symbol, sizeof(symbol), "%.*s", (int)symbol_len, operand);
  if (context->is_symbol_name == NULL || !context->is_symbol_name(symbol, context->user_data)) return 0;
  if (is_register_like_symbol(symbol, context->target_cpu)) return 0;
  snprintf(out_rewritten, out_rewritten_size, "$0%s", suffix);
  snprintf(out_symbolic_name, out_symbolic_name_size, "%s", symbol);
  return 1;
}

static int rewrite_current_relative_label_operand(const char *mnemonic, const char *operand, char *out_rewritten,
    size_t out_rewritten_size) {
  const char *cursor = operand;
  int sign = 1;
  int32_t signed_value = 0;
  if (mnemonic == NULL || operand == NULL || out_rewritten == NULL) return 0;
  if (!mnemonic_uses_relative_label_operand(mnemonic)) return 0;
  if (*cursor != '*') return 0;
  ++cursor;
  if (*cursor == '\0') {
    snprintf(out_rewritten, out_rewritten_size, "%d", -2);
    return 1;
  }
  if (*cursor == '+') {
    ++cursor;
  } else if (*cursor == '-') {
    sign = -1;
    ++cursor;
  } else {
    return 0;
  }
  if (!isdigit((unsigned char)*cursor)) return 0;
  while (isdigit((unsigned char)*cursor)) {
    signed_value = signed_value * 10 + (int32_t)(*cursor - '0');
    ++cursor;
  }
  signed_value *= sign;
  if (*cursor != '\0') return 0;
  snprintf(out_rewritten, out_rewritten_size, "%d", (int)(signed_value - 2));
  return 1;
}

int m68k_parse_instruction_with_symbol_fallback_spec(const M68kSymbolicParseContext *context, const char *line_text,
    InstructionSpec *out_instruction, char *out_fallback_line, size_t out_fallback_line_size) {
  char line[256];
  char mnemonic_text[64];
  char rebuilt[256];
  char *space = NULL;
  char *operand_text = NULL;
  char *operands[M68K_INSTRUCTION_SPEC_MAX_OPERANDS] = {NULL, NULL, NULL, NULL};
  char rewritten_operands[M68K_INSTRUCTION_SPEC_MAX_OPERANDS][64];
  char symbolic_names[M68K_INSTRUCTION_SPEC_MAX_OPERANDS][M68K_INSTRUCTION_SPEC_MAX_LABEL_NAME];
  int32_t symbolic_addends[M68K_INSTRUCTION_SPEC_MAX_OPERANDS] = {0, 0, 0, 0};
  size_t operand_count = 0;
  size_t operand_index;
  char *dot = NULL;
  int parse_ok = 0;
  if (out_fallback_line != NULL && out_fallback_line_size != 0U) out_fallback_line[0] = '\0';
  if (context == NULL || line_text == NULL || out_instruction == NULL) return 0;
  snprintf(line, sizeof(line), "%s", line_text);
  m68k_strip_comment_in_place(line);
  strcpy(line, m68k_trim_in_place(line));
  m68k_normalize_register_alias_tokens_in_place(line);
  m68k_normalize_pc_current_expr_in_place(line);
  if (context->enable_vasm_compat_rewrites) m68k_normalize_zero_base_displacement_in_place(line);
  space = strchr(line, ' ');
  if (space != NULL) {
    *space = '\0';
    operand_text = m68k_trim_in_place(space + 1);
    if (*operand_text != '\0' && !m68k_split_operands_in_place(operand_text, operands,
        M68K_INSTRUCTION_SPEC_MAX_OPERANDS, &operand_count)) {
      return 0;
    }
  }
  snprintf(mnemonic_text, sizeof(mnemonic_text), "%s", line);
  dot = strchr(mnemonic_text, '.');
  if (dot != NULL) *dot = '\0';
  for (operand_index = 0; operand_index < operand_count; ++operand_index) {
    const char *operand = operands[operand_index];
    symbolic_names[operand_index][0] = '\0';
    symbolic_addends[operand_index] = 0;
    if (operand[0] == '#') {
      uint32_t immediate_value = 0;
      if (m68k_source_parse_constant_expression(operand + 1, lookup_constant_symbol_for_expression,
          (void *)context, &immediate_value)) {
        snprintf(rewritten_operands[operand_index], sizeof(rewritten_operands[operand_index]), "#%d",
          (int32_t)immediate_value);
      } else if (context->is_symbol_name != NULL && context->is_symbol_name(operand + 1, context->user_data)) {
        snprintf(rewritten_operands[operand_index], sizeof(rewritten_operands[operand_index]), "#0");
        snprintf(symbolic_names[operand_index], sizeof(symbolic_names[operand_index]), "%s", operand + 1);
      } else {
        snprintf(rewritten_operands[operand_index], sizeof(rewritten_operands[operand_index]), "%s", operand);
      }
    } else if (rewrite_absolute_constant_operand(context, operand, rewritten_operands[operand_index],
        sizeof(rewritten_operands[operand_index]))) {
    } else if (rewrite_absolute_symbol_operand(context, operand, rewritten_operands[operand_index],
        sizeof(rewritten_operands[operand_index]), symbolic_names[operand_index],
        sizeof(symbolic_names[operand_index]))) {
    } else if (rewrite_current_relative_label_operand(mnemonic_text, operand, rewritten_operands[operand_index],
        sizeof(rewritten_operands[operand_index]))) {
    } else if (context->is_symbol_name != NULL && context->is_symbol_name(operand, context->user_data) &&
        !is_register_like_symbol(operand, context->target_cpu) &&
        !context->lookup_symbol(operand, NULL, 1, context->user_data)) {
      snprintf(rewritten_operands[operand_index], sizeof(rewritten_operands[operand_index]), "%s",
               mnemonic_uses_relative_label_operand(mnemonic_text) ? "2" : "$0.l");
      snprintf(symbolic_names[operand_index], sizeof(symbolic_names[operand_index]), "%s", operand);
    } else if (rewrite_pc_relative_symbol_operand(context, operand, rewritten_operands[operand_index],
        sizeof(rewritten_operands[operand_index]), symbolic_names[operand_index], sizeof(symbolic_names[operand_index]),
        &symbolic_addends[operand_index])) {
    } else if (rewrite_base_relative_symbol_operand(context, operand, rewritten_operands[operand_index],
        sizeof(rewritten_operands[operand_index]), symbolic_names[operand_index],
        sizeof(symbolic_names[operand_index]))) {
    } else {
      snprintf(rewritten_operands[operand_index], sizeof(rewritten_operands[operand_index]), "%s", operand);
    }
  }
  snprintf(rebuilt, sizeof(rebuilt), "%s", line);
  if (operand_count != 0U) {
    size_t offset = strlen(rebuilt);
    rebuilt[offset++] = ' ';
    rebuilt[offset] = '\0';
    for (operand_index = 0; operand_index < operand_count; ++operand_index) {
      if (operand_index != 0U) strcat(rebuilt, ",");
      strcat(rebuilt, rewritten_operands[operand_index]);
    }
  }
  if (out_fallback_line != NULL && out_fallback_line_size != 0U) {
    snprintf(out_fallback_line, out_fallback_line_size, "%s", rebuilt);
  }
  parse_ok = m68k_plain_parse_instruction_to_spec(rebuilt, context->target_cpu, out_instruction);
  if (!parse_ok) return 0;
  for (operand_index = 0; operand_index < operand_count; ++operand_index) {
    if (symbolic_names[operand_index][0] == '\0') continue;
    snprintf(out_instruction->operand_label_names[operand_index],
      sizeof(out_instruction->operand_label_names[operand_index]), "%s", symbolic_names[operand_index]);
    out_instruction->operand_label_addends[operand_index] = symbolic_addends[operand_index];
  }
  return 1;
}

int m68k_parse_instruction_with_symbol_fallback_ir( const M68kSymbolicParseContext *context, const char *line_text,
    M68kInstructionIR *out_instruction, char *out_fallback_line, size_t out_fallback_line_size) {
  InstructionSpec parsed;
  size_t operand_index;
  if (!m68k_parse_instruction_with_symbol_fallback_spec(context, line_text, &parsed, out_fallback_line,
      out_fallback_line_size)) {
    return 0;
  }
  m68k_instruction_spec_to_ir(&parsed, out_instruction);
  for (operand_index = 0; operand_index < out_instruction->operand_count &&
      operand_index < M68K_INSTRUCTION_SPEC_MAX_OPERANDS; ++operand_index) {
    if (parsed.operand_label_names[operand_index][0] == '\0') continue;
    out_instruction->operands[operand_index].symbol_ref.has_name = 1;
    out_instruction->operands[operand_index].symbol_ref.name_is_generated = 0U;
    out_instruction->operands[operand_index].symbol_ref.addend = parsed.operand_label_addends[operand_index];
    snprintf(out_instruction->operands[operand_index].symbol_ref.name,
             sizeof(out_instruction->operands[operand_index].symbol_ref.name),
             "%s", parsed.operand_label_names[operand_index]);
    mark_ir_symbol_ref_kind(&out_instruction->operands[operand_index]);
  }
  return 1;
}
