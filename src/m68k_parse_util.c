#include "m68k_parse_util.h"

#include "m68k_assembler.h"

#include <ctype.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

uint32_t m68k_sign_extend32(uint32_t value, unsigned bits) {
  uint32_t sign_bit;
  uint32_t mask;
  if (bits == 0U || bits >= 32U) return value;
  sign_bit = 1U << (bits - 1U);
  mask = (1U << bits) - 1U;
  value &= mask;
  if ((value & sign_bit) != 0U) value |= ~mask;
  return value;
}

int m68k_appendf(char *buffer, size_t buffer_size, const char *format, ...) {
  size_t length;
  int written;
  va_list args;
  if (buffer == NULL || buffer_size == 0U || format == NULL) return -1;
  length = strlen(buffer);
  if (length >= buffer_size) return -1;
  va_start(args, format);
  written = vsnprintf(buffer + length, buffer_size - length, format, args);
  va_end(args);
  if (written < 0) return -1;
  return (size_t)written >= (buffer_size - length) ? -1 : 0;
}

int m68k_lower_copy(char *out, size_t out_size, const char *text) {
  size_t index = 0;
  if (out == NULL || out_size == 0U || text == NULL) return -1;
  while (text[index] != '\0') {
    char ch = text[index];
    if (index + 1U >= out_size) return -1;
    if (ch >= 'A' && ch <= 'Z') ch = (char)(ch - 'A' + 'a');
    out[index++] = ch;
  }
  out[index] = '\0';
  return 0;
}

int m68k_text_uses_short_branch_suffix(const char *text) {
  const char *dot;
  const char *space;
  size_t mnemonic_len;
  if (text == NULL) return 0;
  dot = strchr(text, '.');
  if (dot == NULL || (dot[1] != 's' && dot[1] != 'S')) return 0;
  space = strchr(text, ' ');
  if (space == NULL || space <= text) return 0;
  mnemonic_len = (size_t)(dot - text);
  if (mnemonic_len == 0U) return 0;
  if (mnemonic_len >= 2U && _strnicmp(text, "bf", 2) == 0) return 0;
  return _strnicmp(text, "b", 1) == 0;
}

int m68k_is_symbol_name(const char *text) {
  size_t index;
  if (text == NULL || !(isalpha((unsigned char)text[0]) || text[0] == '_')) return 0;
  for (index = 1; text[index] != '\0'; ++index) {
    if (!(isalnum((unsigned char)text[index]) || text[index] == '_')) return 0;
  }
  return 1;
}

void m68k_normalize_register_alias_tokens_in_place(char *text) {
  char buffer[256];
  size_t src = 0;
  size_t dst = 0;
  while (text[src] != '\0' && dst + 1U < sizeof(buffer)) {
    if (isalpha((unsigned char)text[src]) || text[src] == '_') {
      char token[64];
      size_t token_len = 0;
      const char *canonical = NULL;
      while ((isalnum((unsigned char)text[src]) || text[src] == '_') && token_len + 1U < sizeof(token)) {
        token[token_len++] = text[src++];
      }
      token[token_len] = '\0';
      canonical = m68k_asm_resolve_register_alias(token);
      if (canonical == NULL) canonical = token;
      while (*canonical != '\0' && dst + 1U < sizeof(buffer)) buffer[dst++] = *canonical++;
      continue;
    }
    buffer[dst++] = text[src++];
  }
  buffer[dst] = '\0';
  strcpy(text, buffer);
}

void m68k_normalize_pc_current_expr_in_place(char *text) {
  char buffer[256];
  size_t src = 0;
  size_t dst = 0;
  while (text[src] != '\0' && dst + 1U < sizeof(buffer)) {
    if (text[src] == '*') {
      size_t cursor = src + 1U;
      int sign = 1;
      uint32_t value = 0;
      int has_digits = 0;
      if (text[cursor] == '+') ++cursor;
      else if (text[cursor] == '-') {
        sign = -1;
        ++cursor;
      }
      while (isdigit((unsigned char)text[cursor])) {
        has_digits = 1;
        value = value * 10U + (uint32_t)(text[cursor] - '0');
        ++cursor;
      }
      if (text[cursor] == '('
        && tolower((unsigned char)text[cursor + 1U]) == 'p'
        && tolower((unsigned char)text[cursor + 2U]) == 'c') {
        int32_t signed_value = has_digits ? (int32_t)value * sign : 0;
        char number[32];
        size_t num_index = 0;
        signed_value -= 2;
        snprintf(number, sizeof(number), "%d", (int)signed_value);
        number[sizeof(number) - 1U] = '\0';
        while (number[num_index] != '\0' && dst + 1U < sizeof(buffer)) buffer[dst++] = number[num_index++];
        src = cursor;
        continue;
      }
    }
    buffer[dst++] = text[src++];
  }
  buffer[dst] = '\0';
  strcpy(text, buffer);
}

int m68k_parse_number_u32(const char *text, uint32_t *out_value) {
  char *endptr;
  uint64_t magnitude;
  int negative = 0;
  int base = 10;
  if (text == NULL || out_value == NULL || *text == '\0') return 0;
  if (*text == '-') {
    negative = 1;
    ++text;
  }
  else if (*text == '+') {
    ++text;
  }
  if (*text == '$') {
    base = 16;
    ++text;
  }
  if (*text == '\0') return 0;
  magnitude = (uint64_t)strtoull(text, &endptr, base);
  if (*endptr != '\0' || magnitude > 0xFFFFFFFFULL) return 0;
  *out_value = negative ? (uint32_t)(0U - (uint32_t)magnitude) : (uint32_t)magnitude;
  return 1;
}

int m68k_parse_register_token(const char *text, char prefix, uint8_t *out_reg) {
  const char *canonical = m68k_asm_resolve_register_alias(text);
  char *endptr;
  int32_t value;
  if (canonical == NULL) return 0;
  if (tolower((unsigned char)canonical[0]) != (int)prefix) return 0;
  value = (int32_t)strtol(canonical + 1, &endptr, 10);
  if (*endptr != '\0' || value < 0 || value > 7) return 0;
  *out_reg = (uint8_t)value;
  return 1;
}

int m68k_parse_register_pair_token(const char *text, char first_prefix, char second_prefix, uint8_t *out_reg,
  uint8_t *out_pair_reg) {
  const char *separator = strchr(text, ':');
  char left[32];
  char right[32];
  size_t left_len;
  if (separator == NULL) return 0;
  left_len = (size_t)(separator - text);
  if (left_len == 0 || left_len >= sizeof(left) || strlen(separator + 1) >= sizeof(right)) return 0;
  memcpy(left, text, left_len);
  left[left_len] = '\0';
  strcpy(right, separator + 1);
  if (!m68k_parse_register_token(left, first_prefix, out_reg)) return 0;
  if (!m68k_parse_register_token(right, second_prefix, out_pair_reg)) return 0;
  return 1;
}

int m68k_parse_rn_pair_token(const char *text, uint8_t *out_reg, uint8_t *out_pair_reg,
  uint8_t *out_reg_is_address, uint8_t *out_pair_reg_is_address) {
  uint8_t reg0 = 0;
  uint8_t reg1 = 0;
  if (sscanf(text, "(a%hhu):(a%hhu)", &reg0, &reg1) == 2 && reg0 < 8 && reg1 < 8) {
    *out_reg = reg0; *out_pair_reg = reg1; *out_reg_is_address = 1; *out_pair_reg_is_address = 1; return 1;
  }
  if (sscanf(text, "(d%hhu):(a%hhu)", &reg0, &reg1) == 2 && reg0 < 8 && reg1 < 8) {
    *out_reg = reg0; *out_pair_reg = reg1; *out_reg_is_address = 0; *out_pair_reg_is_address = 1; return 1;
  }
  if (sscanf(text, "(a%hhu):(d%hhu)", &reg0, &reg1) == 2 && reg0 < 8 && reg1 < 8) {
    *out_reg = reg0; *out_pair_reg = reg1; *out_reg_is_address = 1; *out_pair_reg_is_address = 0; return 1;
  }
  if (sscanf(text, "(d%hhu):(d%hhu)", &reg0, &reg1) == 2 && reg0 < 8 && reg1 < 8) {
    *out_reg = reg0; *out_pair_reg = reg1; *out_reg_is_address = 0; *out_pair_reg_is_address = 0; return 1;
  }
  return 0;
}

int m68k_parse_control_register_token(const char *text, uint8_t target_cpu, uint8_t *out_id, uint32_t *out_value) {
  const M68kAsmControlRegisterDef *entry = m68k_asm_find_control_register(text, target_cpu);
  if (entry == NULL) return 0;
  *out_id = (uint8_t)entry->id;
  *out_value = entry->value;
  return 1;
}

int m68k_parse_cpu_name(const char *text, uint8_t *out_cpu) {
  if (_stricmp(text, "68000") == 0) { *out_cpu = M68K_ASM_CPU_68000; return 1; }
  if (_stricmp(text, "68010") == 0) { *out_cpu = M68K_ASM_CPU_68010; return 1; }
  if (_stricmp(text, "68020") == 0) { *out_cpu = M68K_ASM_CPU_68020; return 1; }
  if (_stricmp(text, "68030") == 0) { *out_cpu = M68K_ASM_CPU_68030; return 1; }
  if (_stricmp(text, "68040") == 0) { *out_cpu = M68K_ASM_CPU_68040; return 1; }
  if (_stricmp(text, "68060") == 0) { *out_cpu = M68K_ASM_CPU_68060; return 1; }
  return 0;
}

int m68k_set_bounded_string(char *dest, size_t dest_size, const char *value) {
  size_t length;
  if (dest == NULL || dest_size == 0U || value == NULL) return 0;
  length = strlen(value);
  if (length == 0U || length + 1U > dest_size) return 0;
  memcpy(dest, value, length + 1U);
  return 1;
}

int m68k_parse_render_policy_option(int argc, char **argv, int *io_argi,
  M68kRenderPolicy *policy, char *error_buf, size_t error_buf_size) {
  int argi;
  if (io_argi == NULL || policy == NULL) return 0;
  argi = *io_argi;
  if (strcmp(argv[argi], "--syntax") == 0) {
    if (argi + 1 >= argc
      || !m68k_ir_parse_syntax_mode_name(argv[argi + 1], &policy->syntax.syntax_mode)) {
      snprintf(error_buf, error_buf_size, "unknown syntax: %s",
        (argi + 1 < argc) ? argv[argi + 1] : "");
      return -1;
    }
    *io_argi = argi + 1;
    return 1;
  }
  if (strcmp(argv[argi], "--no-strings") == 0) {
    policy->presentation.prefer_strings = 0U;
    return 1;
  }
  if (strcmp(argv[argi], "--no-longs") == 0) {
    policy->presentation.prefer_long_data = 0U;
    return 1;
  }
  if (strcmp(argv[argi], "--no-generated-names") == 0) {
    policy->presentation.prefer_generated_names = 0U;
    return 1;
  }
  if (strcmp(argv[argi], "--code-label-prefix") == 0) {
    if (argi + 1 >= argc || !m68k_set_bounded_string(policy->presentation.code_label_prefix,
        sizeof(policy->presentation.code_label_prefix), argv[argi + 1])) {
      snprintf(error_buf, error_buf_size, "bad code label prefix");
      return -1;
    }
    *io_argi = argi + 1;
    return 1;
  }
  if (strcmp(argv[argi], "--call-label-prefix") == 0) {
    if (argi + 1 >= argc || !m68k_set_bounded_string(policy->presentation.call_label_prefix,
        sizeof(policy->presentation.call_label_prefix), argv[argi + 1])) {
      snprintf(error_buf, error_buf_size, "bad call label prefix");
      return -1;
    }
    *io_argi = argi + 1;
    return 1;
  }
  if (strcmp(argv[argi], "--data-label-prefix") == 0) {
    if (argi + 1 >= argc || !m68k_set_bounded_string(policy->presentation.data_label_prefix,
        sizeof(policy->presentation.data_label_prefix), argv[argi + 1])) {
      snprintf(error_buf, error_buf_size, "bad data label prefix");
      return -1;
    }
    *io_argi = argi + 1;
    return 1;
  }
  return 0;
}
