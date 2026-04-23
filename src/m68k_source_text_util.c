#include "m68k_source_text_util.h"

#include "m68k_parse_util.h"

#include <ctype.h>
#include <stdio.h>
#include <string.h>

char *m68k_trim_in_place(char *text) {
  char *end;
  while (*text != '\0' && isspace((unsigned char)*text)) ++text;
  end = text + strlen(text);
  while (end > text && isspace((unsigned char)end[-1])) --end;
  *end = '\0';
  return text;
}

void m68k_strip_comment_in_place(char *line) {
  size_t index;
  int in_string = 0;
  char string_quote = '\0';
  for (index = 0; line[index] != '\0'; ++index) {
    if (in_string) {
      if (line[index] == string_quote) in_string = 0;
      continue;
    }
    if (line[index] == '"' || line[index] == '\'') {
      in_string = 1;
      string_quote = line[index];
      continue;
    }
    if (line[index] == ';') {
      line[index] = '\0';
      break;
    }
    if (line[index] == '*'
      && index > 0U
      && isspace((unsigned char)line[index - 1U])
      && (line[index + 1U] == '\0'
        || isspace((unsigned char)line[index + 1U]))) {
      line[index] = '\0';
      break;
    }
  }
}

size_t m68k_split_delimited_in_place(char *text, char delimiter, char **parts, size_t max_parts) {
  size_t count = 0;
  char *part_start = text;
  char *cursor = text;
  while (1) {
    if (*cursor == delimiter) {
      if (count >= max_parts) return 0;
      *cursor = '\0';
      parts[count++] = part_start;
      part_start = cursor + 1;
    } else if (*cursor == '\0') {
      if (count >= max_parts) return 0;
      parts[count++] = part_start;
      return count;
    }
    ++cursor;
  }
}

char *m68k_next_token_in_place(char **text) {
  char *start = m68k_trim_in_place(*text);
  char *cursor = start;
  while (*cursor != '\0' && !isspace((unsigned char)*cursor)) ++cursor;
  if (*cursor != '\0') {
    *cursor = '\0';
    ++cursor;
  }
  *text = cursor;
  return start;
}

int m68k_split_operands_in_place(char *text, char **operands, size_t max_operands, size_t *out_count) {
  size_t count = 0;
  char *segment_start = text;
  int paren_depth = 0;
  int bracket_depth = 0;
  int brace_depth = 0;
  int in_string = 0;
  char string_quote = '\0';
  char *cursor = text;
  while (*cursor != '\0') {
    if (in_string) {
      if (*cursor == string_quote) in_string = 0;
    } else if (*cursor == '"' || *cursor == '\'') {
      in_string = 1;
      string_quote = *cursor;
    } else if (*cursor == '(') {
      ++paren_depth;
    } else if (*cursor == ')') {
      if (paren_depth == 0) return 0;
      --paren_depth;
    } else if (*cursor == '[') {
      ++bracket_depth;
    } else if (*cursor == ']') {
      if (bracket_depth == 0) return 0;
      --bracket_depth;
    } else if (*cursor == '{') {
      ++brace_depth;
    } else if (*cursor == '}') {
      if (brace_depth == 0) return 0;
      --brace_depth;
    } else if (*cursor == ',' && paren_depth == 0 && bracket_depth == 0 &&
           brace_depth == 0) {
      *cursor = '\0';
      if (count >= max_operands) return 0;
      operands[count++] = m68k_trim_in_place(segment_start);
      segment_start = cursor + 1;
    }
    ++cursor;
  }
  if (in_string || paren_depth != 0 || bracket_depth != 0 || brace_depth != 0)
    return 0;
  if (*m68k_trim_in_place(segment_start) != '\0') {
    if (count >= max_operands) return 0;
    operands[count++] = m68k_trim_in_place(segment_start);
  }
  *out_count = count;
  return 1;
}

void m68k_normalize_zero_base_displacement_in_place(char *text) {
  char buffer[256];
  size_t src = 0;
  size_t dst = 0;
  while (text[src] != '\0' && dst + 1U < sizeof(buffer)) {
    if (text[src] == '0' && text[src + 1U] == '('
      && tolower((unsigned char)text[src + 2U]) == 'a'
      && text[src + 3U] >= '0' && text[src + 3U] <= '7'
      && text[src + 4U] == ')') {
      buffer[dst++] = '(';
      buffer[dst++] = text[src + 2U];
      buffer[dst++] = text[src + 3U];
      buffer[dst++] = ')';
      src += 5U;
      continue;
    }
    buffer[dst++] = text[src++];
  }
  buffer[dst] = '\0';
  strcpy(text, buffer);
}

int m68k_is_elided_lea_noop(const char *line_text) {
  char line[256];
  char size_suffix = '\0';
  char src_token[4];
  char *space = NULL;
  char *operand_text = NULL;
  char *operands[4] = {NULL, NULL, NULL, NULL};
  size_t operand_count = 0;
  M68kParseRegisterResult src_reg;
  M68kParseRegisterResult dst_reg;
  M68kParseMnemonicResult mnemonic_result;
  uint8_t mnemonic_id = M68K_ASM_MNEMONIC_NONE;
  snprintf(line, sizeof(line), "%s", line_text);
  m68k_strip_comment_in_place(line);
  strcpy(line, m68k_trim_in_place(line));
  m68k_normalize_register_alias_tokens_in_place(line);
  m68k_normalize_zero_base_displacement_in_place(line);
  space = strchr(line, ' ');
  if (space == NULL) return 0;
  *space = '\0';
  operand_text = m68k_trim_in_place(space + 1);
  mnemonic_result = m68k_parse_mnemonic_token(line);
  mnemonic_id = mnemonic_result.mnemonic_id;
  size_suffix = mnemonic_result.size_suffix;
  if (mnemonic_id != M68K_ASM_MNEMONIC_LEA || size_suffix != '\0' || *operand_text == '\0') return 0;
  if (!m68k_split_operands_in_place(operand_text, operands, 4U, &operand_count)
    || operand_count != 2U) {
    return 0;
  }
  dst_reg = m68k_parse_register_token(m68k_trim_in_place(operands[1]), 'a');
  if (!dst_reg.ok) return 0;
  if (operands[0][0] != '(' || operands[0][3] != ')' || operands[0][4] != '\0')
    return 0;
  src_token[0] = operands[0][1];
  src_token[1] = operands[0][2];
  src_token[2] = '\0';
  src_reg = m68k_parse_register_token(src_token, 'a');
  if (!src_reg.ok) return 0;
  return src_reg.reg == dst_reg.reg;
}

static int source_text_is_zero_immediate_local(const char *text) {
  return m68k_ascii_equal_ci(text, "#0") ||
    m68k_ascii_equal_ci(text, "#$0") ||
    m68k_ascii_equal_ci(text, "#$0000") ||
    m68k_ascii_equal_ci(text, "#$00000000");
}

int m68k_rewrite_cmp_zero_to_tst(const char *line_text, char *out_text, size_t out_text_size) {
  char line[256];
  char size_suffix = '\0';
  char *space = NULL;
  char *operand_text = NULL;
  char *operands[4] = {NULL, NULL, NULL, NULL};
  size_t operand_count = 0;
  M68kParseMnemonicResult mnemonic_result;
  uint8_t mnemonic_id = M68K_ASM_MNEMONIC_NONE;
  snprintf(line, sizeof(line), "%s", line_text);
  m68k_strip_comment_in_place(line);
  strcpy(line, m68k_trim_in_place(line));
  m68k_normalize_register_alias_tokens_in_place(line);
  space = strchr(line, ' ');
  if (space == NULL) return 0;
  *space = '\0';
  operand_text = m68k_trim_in_place(space + 1);
  if (*operand_text == '\0') return 0;
  mnemonic_result = m68k_parse_mnemonic_token(line);
  mnemonic_id = mnemonic_result.mnemonic_id;
  size_suffix = mnemonic_result.size_suffix;
  if (mnemonic_id != M68K_ASM_MNEMONIC_CMP) return 0;
  if (size_suffix != 'b' && size_suffix != 'w' && size_suffix != 'l') return 0;
  if (!m68k_split_operands_in_place(operand_text, operands, 4U, &operand_count) || operand_count != 2U) return 0;
  if (!source_text_is_zero_immediate_local(m68k_trim_in_place(operands[0]))) return 0;
  snprintf(out_text, out_text_size, "tst.%c %s", size_suffix, m68k_trim_in_place(operands[1]));
  return 1;
}

char m68k_requested_size_suffix_from_text(const char *line_text) {
  char line[256];
  char *space;
  char *dot;
  snprintf(line, sizeof(line), "%s", line_text);
  m68k_strip_comment_in_place(line);
  strcpy(line, m68k_trim_in_place(line));
  space = strchr(line, ' ');
  if (space != NULL) *space = '\0';
  dot = strchr(line, '.');
  if (dot == NULL || dot[1] == '\0') return '\0';
  return (char)((tolower((unsigned char)dot[1]) == 's') ? 'b' : tolower((unsigned char)dot[1]));
}

int m68k_parse_section_kind(const char *text, M68kSectionKind *out_kind) {
  uint8_t mem_type;
  uint32_t mem_attrs;
  return m68k_parse_section_spec(text, out_kind, &mem_type, &mem_attrs);
}

static int parse_section_base_kind(const char *text, size_t length, M68kSectionKind *out_kind) {
  if (length == 4U && _strnicmp(text, "code", length) == 0) {
    *out_kind = M68K_SECTION_CODE;
    return 1;
  }
  if (length == 4U && _strnicmp(text, "data", length) == 0) {
    *out_kind = M68K_SECTION_DATA;
    return 1;
  }
  if (length == 3U && _strnicmp(text, "bss", length) == 0) {
    *out_kind = M68K_SECTION_BSS;
    return 1;
  }
  return 0;
}

int m68k_parse_section_spec(const char *text, M68kSectionKind *out_kind, uint8_t *out_platform_mem_type,
                            uint32_t *out_platform_mem_attrs) {
  const char *suffix;
  size_t base_len;
  M68kSectionKind kind;
  if (text == NULL || out_kind == NULL || out_platform_mem_type == NULL || out_platform_mem_attrs == NULL) return 0;
  suffix = strchr(text, '_');
  base_len = suffix != NULL ? (size_t)(suffix - text) : strlen(text);
  if (!parse_section_base_kind(text, base_len, &kind)) return 0;
  *out_kind = kind;
  *out_platform_mem_type = 0U;
  *out_platform_mem_attrs = 0U;
  if (suffix == NULL) return 1;
  ++suffix;
  if (m68k_ascii_equal_ci(suffix, "c") || m68k_ascii_equal_ci(suffix, "chip")) {
    *out_platform_mem_type = 1U;
    return 1;
  }
  if (m68k_ascii_equal_ci(suffix, "f") || m68k_ascii_equal_ci(suffix, "fast")) {
    *out_platform_mem_type = 2U;
    return 1;
  }
  if ((suffix[0] == 'x' || suffix[0] == 'X') && suffix[1] != '\0') {
    M68kParseU32Result value = m68k_parse_number_u32(suffix + 1);
    if (!value.ok) return 0;
    *out_platform_mem_type = 3U;
    *out_platform_mem_attrs = value.value;
    return 1;
  }
  return 0;
}

int m68k_format_section_spec(M68kSectionKind kind, uint8_t platform_mem_type, uint32_t platform_mem_attrs,
                             char *out_text, size_t out_text_size) {
  const char *base = (kind == M68K_SECTION_CODE) ? "code" : (kind == M68K_SECTION_DATA) ? "data" : "bss";
  if (out_text == NULL || out_text_size == 0U) return 0;
  if (platform_mem_type == 0U) return snprintf(out_text, out_text_size, "%s", base) >= 0;
  if (platform_mem_type == 1U) return snprintf(out_text, out_text_size, "%s_c", base) >= 0;
  if (platform_mem_type == 2U) return snprintf(out_text, out_text_size, "%s_f", base) >= 0;
  if (platform_mem_type == 3U) return snprintf(out_text, out_text_size, "%s_x$%08X", base, platform_mem_attrs) >= 0;
  return 0;
}

char *m68k_find_label_delimiter(char *text) {
  char *cursor = text;
  while (*cursor != '\0') {
    if (*cursor == ':') return cursor;
    if (isspace((unsigned char)*cursor) || *cursor == '"' || *cursor == '\'') return NULL;
    ++cursor;
  }
  return NULL;
}
