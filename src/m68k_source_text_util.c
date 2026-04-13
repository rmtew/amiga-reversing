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
  char src_token[4];
  char *space = NULL;
  char *operand_text = NULL;
  char *operands[4] = {NULL, NULL, NULL, NULL};
  size_t operand_count = 0;
  uint8_t src_reg = 0;
  uint8_t dst_reg = 0;
  snprintf(line, sizeof(line), "%s", line_text);
  m68k_strip_comment_in_place(line);
  strcpy(line, m68k_trim_in_place(line));
  m68k_normalize_register_alias_tokens_in_place(line);
  m68k_normalize_zero_base_displacement_in_place(line);
  space = strchr(line, ' ');
  if (space == NULL) return 0;
  *space = '\0';
  operand_text = m68k_trim_in_place(space + 1);
  if (_stricmp(line, "lea") != 0 || *operand_text == '\0') return 0;
  if (!m68k_split_operands_in_place(operand_text, operands, 4U, &operand_count)
    || operand_count != 2U) {
    return 0;
  }
  if (!m68k_parse_register_token(m68k_trim_in_place(operands[1]), 'a',
                   &dst_reg)) {
    return 0;
  }
  if (operands[0][0] != '(' || operands[0][3] != ')' || operands[0][4] != '\0')
    return 0;
  src_token[0] = operands[0][1];
  src_token[1] = operands[0][2];
  src_token[2] = '\0';
  if (!m68k_parse_register_token(src_token, 'a', &src_reg)) return 0;
  return src_reg == dst_reg;
}

int m68k_rewrite_cmp_zero_to_tst(const char *line_text, char *out_text, size_t out_text_size) {
  char line[256];
  char mnemonic[32];
  char *space = NULL;
  char *operand_text = NULL;
  char *operands[4] = {NULL, NULL, NULL, NULL};
  size_t operand_count = 0;
  snprintf(line, sizeof(line), "%s", line_text);
  m68k_strip_comment_in_place(line);
  strcpy(line, m68k_trim_in_place(line));
  m68k_normalize_register_alias_tokens_in_place(line);
  space = strchr(line, ' ');
  if (space == NULL) return 0;
  *space = '\0';
  operand_text = m68k_trim_in_place(space + 1);
  if (*operand_text == '\0') return 0;
  snprintf(mnemonic, sizeof(mnemonic), "%s", line);
  if (_stricmp(mnemonic, "cmp.b") != 0 && _stricmp(mnemonic, "cmp.w") != 0 &&
    _stricmp(mnemonic, "cmp.l") != 0) {
    return 0;
  }
  if (!m68k_split_operands_in_place(operand_text, operands, 4U, &operand_count)
    || operand_count != 2U) {
    return 0;
  }
  if (_stricmp(m68k_trim_in_place(operands[0]), "#0") != 0 &&
    _stricmp(m68k_trim_in_place(operands[0]), "#$0") != 0 &&
    _stricmp(m68k_trim_in_place(operands[0]), "#$0000") != 0 &&
    _stricmp(m68k_trim_in_place(operands[0]), "#$00000000") != 0) {
    return 0;
  }
  snprintf(out_text, out_text_size, "tst%s %s", mnemonic + 3,
       m68k_trim_in_place(operands[1]));
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
  if (_stricmp(text, "code") == 0) {
    *out_kind = M68K_SECTION_CODE;
    return 1;
  }
  if (_stricmp(text, "data") == 0) {
    *out_kind = M68K_SECTION_DATA;
    return 1;
  }
  if (_stricmp(text, "bss") == 0) {
    *out_kind = M68K_SECTION_BSS;
    return 1;
  }
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
