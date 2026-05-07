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
  size_t dst = 0U;
  int in_string = 0;
  char string_quote = '\0';
  for (index = 0; line[index] != '\0'; ++index) {
    if (in_string) {
      if (line[index] == string_quote) in_string = 0;
      line[dst++] = line[index];
      continue;
    }
    if (line[index] == '"' || line[index] == '\'') {
      in_string = 1;
      string_quote = line[index];
      line[dst++] = line[index];
      continue;
    }
    if (line[index] == '/' && line[index + 1U] == '*') {
      index += 2U;
      while (line[index] != '\0' && !(line[index] == '*' && line[index + 1U] == '/')) ++index;
      if (line[index] == '\0') break;
      ++index;
      continue;
    }
    if (line[index] == ';') break;
    if (line[index] == '*'
      && index > 0U
      && isspace((unsigned char)line[index - 1U])
      && (line[index + 1U] == '\0'
        || isspace((unsigned char)line[index + 1U]))) {
      break;
    }
    line[dst++] = line[index];
  }
  line[dst] = '\0';
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
