#include "m68k_parse_util.h"

#include "generated/amiga_os_runtime.h"
#include "m68k_assembler.h"

#include <ctype.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef struct M68kSourceDirectiveEntry {
  const char *name;
  M68kSourceDirectiveToken token;
} M68kSourceDirectiveEntry;

static const M68kSourceDirectiveEntry g_m68k_source_directives[] = {
  {"ALIGNLONG", M68K_SOURCE_DIRECTIVE_ALIGNLONG},
  {"ALIGNWORD", M68K_SOURCE_DIRECTIVE_ALIGNWORD},
  {"APTR", M68K_SOURCE_DIRECTIVE_APTR},
  {"BITDEF", M68K_SOURCE_DIRECTIVE_BITDEF},
  {"BOOL", M68K_SOURCE_DIRECTIVE_BOOL},
  {"BPTR", M68K_SOURCE_DIRECTIVE_BPTR},
  {"BSTR", M68K_SOURCE_DIRECTIVE_BSTR},
  {"BYTE", M68K_SOURCE_DIRECTIVE_BYTE},
  {"COMMENT", M68K_SOURCE_DIRECTIVE_COMMENT},
  {"CPTR", M68K_SOURCE_DIRECTIVE_CPTR},
  {"DC.B", M68K_SOURCE_DIRECTIVE_DC_B},
  {"DC.L", M68K_SOURCE_DIRECTIVE_DC_L},
  {"DC.W", M68K_SOURCE_DIRECTIVE_DC_W},
  {"DCB.B", M68K_SOURCE_DIRECTIVE_DCB_B},
  {"DCB.L", M68K_SOURCE_DIRECTIVE_DCB_L},
  {"DCB.W", M68K_SOURCE_DIRECTIVE_DCB_W},
  {"DEVCMD", M68K_SOURCE_DIRECTIVE_DEVCMD},
  {"DEVINIT", M68K_SOURCE_DIRECTIVE_DEVINIT},
  {"DOUBLE", M68K_SOURCE_DIRECTIVE_DOUBLE},
  {"END", M68K_SOURCE_DIRECTIVE_END},
  {"ENDC", M68K_SOURCE_DIRECTIVE_ENDC},
  {"ENDM", M68K_SOURCE_DIRECTIVE_ENDM},
  {"EQU", M68K_SOURCE_DIRECTIVE_EQU},
  {"EVEN", M68K_SOURCE_DIRECTIVE_EVEN},
  {"FLOAT", M68K_SOURCE_DIRECTIVE_FLOAT},
  {"FPTR", M68K_SOURCE_DIRECTIVE_FPTR},
  {"IFC", M68K_SOURCE_DIRECTIVE_IFC},
  {"IFNC", M68K_SOURCE_DIRECTIVE_IFNC},
  {"IFND", M68K_SOURCE_DIRECTIVE_IFND},
  {"INCLUDE", M68K_SOURCE_DIRECTIVE_INCLUDE},
  {"LABEL", M68K_SOURCE_DIRECTIVE_LABEL},
  {"LIBDEF", M68K_SOURCE_DIRECTIVE_LIBDEF},
  {"LIBENT", M68K_SOURCE_DIRECTIVE_LIBENT},
  {"LIBINIT", M68K_SOURCE_DIRECTIVE_LIBINIT},
  {"LONG", M68K_SOURCE_DIRECTIVE_LONG},
  {"MACRO", M68K_SOURCE_DIRECTIVE_MACRO},
  {"RPTR", M68K_SOURCE_DIRECTIVE_RPTR},
  {"SECTION", M68K_SOURCE_DIRECTIVE_SECTION},
  {"SET", M68K_SOURCE_DIRECTIVE_SET},
  {"SHORT", M68K_SOURCE_DIRECTIVE_SHORT},
  {"STRUCT", M68K_SOURCE_DIRECTIVE_STRUCT},
  {"STRUCTURE", M68K_SOURCE_DIRECTIVE_STRUCTURE},
  {"UBYTE", M68K_SOURCE_DIRECTIVE_UBYTE},
  {"ULONG", M68K_SOURCE_DIRECTIVE_ULONG},
  {"USHORT", M68K_SOURCE_DIRECTIVE_USHORT},
  {"UWORD", M68K_SOURCE_DIRECTIVE_UWORD},
  {"WORD", M68K_SOURCE_DIRECTIVE_WORD}
};

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

unsigned m68k_popcount16(uint16_t value) {
#if defined(__clang__) || defined(__GNUC__)
  return (unsigned)__builtin_popcount((unsigned)value);
#else
  unsigned count = 0U;
  while (value != 0U) {
    value &= (uint16_t)(value - 1U);
    ++count;
  }
  return count;
#endif
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

int m68k_ascii_equal_ci(const char *left, const char *right) {
  size_t index = 0U;
  if (left == NULL || right == NULL) return 0;
  for (;;) {
    unsigned char left_ch = (unsigned char)left[index];
    unsigned char right_ch = (unsigned char)right[index];
    if (left_ch >= 'A' && left_ch <= 'Z') left_ch = (unsigned char)(left_ch - 'A' + 'a');
    if (right_ch >= 'A' && right_ch <= 'Z') right_ch = (unsigned char)(right_ch - 'A' + 'a');
    if (left_ch != right_ch) return 0;
    if (left_ch == '\0') return 1;
    ++index;
  }
}

int m68k_ascii_prefix_equal_ci(const char *text, const char *prefix) {
  size_t index = 0U;
  if (text == NULL || prefix == NULL) return 0;
  for (;;) {
    unsigned char text_ch = (unsigned char)text[index];
    unsigned char prefix_ch = (unsigned char)prefix[index];
    if (prefix_ch >= 'A' && prefix_ch <= 'Z') prefix_ch = (unsigned char)(prefix_ch - 'A' + 'a');
    if (text_ch >= 'A' && text_ch <= 'Z') text_ch = (unsigned char)(text_ch - 'A' + 'a');
    if (prefix_ch == '\0') return 1;
    if (text_ch != prefix_ch) return 0;
    if (text_ch == '\0') return 0;
    ++index;
  }
}

M68kParseMnemonicResult m68k_parse_mnemonic_token(const char *token) {
  M68kParseMnemonicResult result = {0};
  char normalized[32];
  char *dot;
  if (token == NULL || token[0] == '\0') return result;
  if (m68k_lower_copy(normalized, sizeof(normalized), token) != 0) return result;
  dot = strchr(normalized, '.');
  if (dot != NULL) {
    char size_suffix;
    if (dot[1] == '\0' || dot[2] != '\0') return result;
    size_suffix = (char)tolower((unsigned char)dot[1]);
    if (size_suffix == 's') size_suffix = 'b';
    result.size_suffix = size_suffix;
    *dot = '\0';
  }
  result.mnemonic_id = m68k_asm_mnemonic_id_from_name(normalized);
  return result;
}

uint8_t m68k_parse_special_register_token(const char *text) {
  if (text == NULL) return M68K_ASM_OPERAND_NONE;
  if (m68k_ascii_equal_ci(text, "ccr")) return M68K_ASM_OPERAND_CCR;
  if (m68k_ascii_equal_ci(text, "sr")) return M68K_ASM_OPERAND_SR;
  if (m68k_ascii_equal_ci(text, "usp")) return M68K_ASM_OPERAND_USP;
  return M68K_ASM_OPERAND_NONE;
}

M68kParseU32Result m68k_parse_cache_selector_token(const char *text) {
  M68kParseU32Result result = {0};
  if (text == NULL) return result;
  if (m68k_ascii_equal_ci(text, "nc")) {
    result.ok = 1U;
    result.value = 0U;
    return result;
  }
  if (m68k_ascii_equal_ci(text, "dc")) {
    result.ok = 1U;
    result.value = 1U;
    return result;
  }
  if (m68k_ascii_equal_ci(text, "ic")) {
    result.ok = 1U;
    result.value = 2U;
    return result;
  }
  if (m68k_ascii_equal_ci(text, "bc")) {
    result.ok = 1U;
    result.value = 3U;
    return result;
  }
  return result;
}

M68kSourceDirectiveToken m68k_parse_source_directive_token(const char *text) {
  size_t index;
  if (text == NULL || text[0] == '\0') return M68K_SOURCE_DIRECTIVE_NONE;
  for (index = 0U; index < sizeof(g_m68k_source_directives) / sizeof(g_m68k_source_directives[0]); ++index) {
    if (m68k_ascii_equal_ci(text, g_m68k_source_directives[index].name)) return g_m68k_source_directives[index].token;
  }
  return M68K_SOURCE_DIRECTIVE_NONE;
}

M68kParseDataDirectiveResult m68k_parse_data_directive_token(M68kSourceDirectiveToken token) {
  M68kParseDataDirectiveResult result = {0};
  switch (token) {
  case M68K_SOURCE_DIRECTIVE_DC_B:
  case M68K_SOURCE_DIRECTIVE_DCB_B:
    result.width_bytes = 1U;
    result.is_repeat = (token == M68K_SOURCE_DIRECTIVE_DCB_B);
    break;
  case M68K_SOURCE_DIRECTIVE_DC_W:
  case M68K_SOURCE_DIRECTIVE_DCB_W:
    result.width_bytes = 2U;
    result.is_repeat = (token == M68K_SOURCE_DIRECTIVE_DCB_W);
    break;
  case M68K_SOURCE_DIRECTIVE_DC_L:
  case M68K_SOURCE_DIRECTIVE_DCB_L:
    result.width_bytes = 4U;
    result.is_repeat = (token == M68K_SOURCE_DIRECTIVE_DCB_L);
    break;
  default:
    return result;
  }
  result.ok = 1U;
  return result;
}

M68kParseOffsetDirectiveResult m68k_parse_offset_directive_token(M68kSourceDirectiveToken token) {
  M68kParseOffsetDirectiveResult result = {0};
  switch (token) {
  case M68K_SOURCE_DIRECTIVE_BYTE:
  case M68K_SOURCE_DIRECTIVE_UBYTE:
    result.delta = 1U;
    break;
  case M68K_SOURCE_DIRECTIVE_WORD:
  case M68K_SOURCE_DIRECTIVE_UWORD:
  case M68K_SOURCE_DIRECTIVE_BOOL:
  case M68K_SOURCE_DIRECTIVE_SHORT:
  case M68K_SOURCE_DIRECTIVE_USHORT:
  case M68K_SOURCE_DIRECTIVE_RPTR:
    result.delta = 2U;
    break;
  case M68K_SOURCE_DIRECTIVE_LONG:
  case M68K_SOURCE_DIRECTIVE_ULONG:
  case M68K_SOURCE_DIRECTIVE_FLOAT:
  case M68K_SOURCE_DIRECTIVE_APTR:
  case M68K_SOURCE_DIRECTIVE_BPTR:
  case M68K_SOURCE_DIRECTIVE_BSTR:
  case M68K_SOURCE_DIRECTIVE_CPTR:
  case M68K_SOURCE_DIRECTIVE_FPTR:
    result.delta = 4U;
    break;
  case M68K_SOURCE_DIRECTIVE_DOUBLE:
    result.delta = 8U;
    break;
  default:
    return result;
  }
  result.ok = 1U;
  return result;
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
  if (mnemonic_len >= 2U && m68k_ascii_prefix_equal_ci(text, "bf")) return 0;
  return m68k_ascii_prefix_equal_ci(text, "b");
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
      (void)has_digits;
      (void)sign;
      (void)value;
    }
    buffer[dst++] = text[src++];
  }
  buffer[dst] = '\0';
  strcpy(text, buffer);
}

M68kParseU32Result m68k_parse_number_u32(const char *text) {
  M68kParseU32Result result = {0};
  char *endptr;
  uint64_t magnitude;
  int negative = 0;
  int base = 10;
  if (text == NULL || *text == '\0') return result;
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
  if (*text == '\0') return result;
  magnitude = (uint64_t)strtoull(text, &endptr, base);
  if (*endptr != '\0' || magnitude > 0xFFFFFFFFULL) return result;
  result.ok = 1U;
  result.value = negative ? (uint32_t)(0U - (uint32_t)magnitude) : (uint32_t)magnitude;
  return result;
}

M68kParseRegisterResult m68k_parse_register_token(const char *text, char prefix) {
  M68kParseRegisterResult result = {0};
  const char *canonical = m68k_asm_resolve_register_alias(text);
  char *endptr;
  int32_t value;
  if (canonical == NULL) return result;
  if (tolower((unsigned char)canonical[0]) != (int)prefix) return result;
  value = (int32_t)strtol(canonical + 1, &endptr, 10);
  if (*endptr != '\0' || value < 0 || value > 7) return result;
  result.ok = 1U;
  result.reg = (uint8_t)value;
  return result;
}

M68kParseRegisterResult m68k_parse_register_pair_token(const char *text, char first_prefix, char second_prefix) {
  M68kParseRegisterResult result = {0};
  M68kParseRegisterResult left_result;
  M68kParseRegisterResult right_result;
  const char *separator = strchr(text, ':');
  char left[32];
  char right[32];
  size_t left_len;
  if (separator == NULL) return result;
  left_len = (size_t)(separator - text);
  if (left_len == 0 || left_len >= sizeof(left) || strlen(separator + 1) >= sizeof(right)) return result;
  memcpy(left, text, left_len);
  left[left_len] = '\0';
  strcpy(right, separator + 1);
  left_result = m68k_parse_register_token(left, first_prefix);
  right_result = m68k_parse_register_token(right, second_prefix);
  if (!left_result.ok || !right_result.ok) return result;
  result.ok = 1U;
  result.reg = left_result.reg;
  result.pair_reg = right_result.reg;
  return result;
}

M68kParseRegisterResult m68k_parse_rn_pair_token(const char *text) {
  M68kParseRegisterResult result = {0};
  uint8_t reg0 = 0;
  uint8_t reg1 = 0;
  if (sscanf(text, "(a%hhu):(a%hhu)", &reg0, &reg1) == 2 && reg0 < 8 && reg1 < 8) {
    result.ok = 1U; result.reg = reg0; result.pair_reg = reg1; result.reg_is_address = 1U; result.pair_reg_is_address = 1U; return result;
  }
  if (sscanf(text, "(d%hhu):(a%hhu)", &reg0, &reg1) == 2 && reg0 < 8 && reg1 < 8) {
    result.ok = 1U; result.reg = reg0; result.pair_reg = reg1; result.reg_is_address = 0U; result.pair_reg_is_address = 1U; return result;
  }
  if (sscanf(text, "(a%hhu):(d%hhu)", &reg0, &reg1) == 2 && reg0 < 8 && reg1 < 8) {
    result.ok = 1U; result.reg = reg0; result.pair_reg = reg1; result.reg_is_address = 1U; result.pair_reg_is_address = 0U; return result;
  }
  if (sscanf(text, "(d%hhu):(d%hhu)", &reg0, &reg1) == 2 && reg0 < 8 && reg1 < 8) {
    result.ok = 1U; result.reg = reg0; result.pair_reg = reg1; result.reg_is_address = 0U; result.pair_reg_is_address = 0U; return result;
  }
  return result;
}

M68kParseControlRegisterResult m68k_parse_control_register_token(const char *text, uint8_t target_cpu) {
  M68kParseControlRegisterResult result = {0};
  const M68kAsmControlRegisterDef *entry = m68k_asm_find_control_register(text, target_cpu);
  if (entry == NULL) return result;
  result.ok = 1U;
  result.id = (uint8_t)entry->id;
  result.value = entry->value;
  return result;
}

M68kParseCpuResult m68k_parse_cpu_name(const char *text) {
  M68kParseCpuResult result = {0};
  if (m68k_ascii_equal_ci(text, "68000")) { result.ok = 1U; result.cpu = M68K_ASM_CPU_68000; return result; }
  if (m68k_ascii_equal_ci(text, "68010")) { result.ok = 1U; result.cpu = M68K_ASM_CPU_68010; return result; }
  if (m68k_ascii_equal_ci(text, "68020")) { result.ok = 1U; result.cpu = M68K_ASM_CPU_68020; return result; }
  if (m68k_ascii_equal_ci(text, "68030")) { result.ok = 1U; result.cpu = M68K_ASM_CPU_68030; return result; }
  if (m68k_ascii_equal_ci(text, "68040")) { result.ok = 1U; result.cpu = M68K_ASM_CPU_68040; return result; }
  if (m68k_ascii_equal_ci(text, "68060")) { result.ok = 1U; result.cpu = M68K_ASM_CPU_68060; return result; }
  return result;
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
  M68kRenderPolicy *policy, M68kDiagSink diagnostics) {
  int argi;
  AmigaOsCompatVersion compat_version;
  if (io_argi == NULL || policy == NULL) return 0;
  argi = *io_argi;
  if (strcmp(argv[argi], "--syntax") == 0) {
    if (argi + 1 >= argc
      || !m68k_ir_parse_syntax_mode_name(argv[argi + 1], &policy->syntax.syntax_mode)) {
      m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PARSE_FAILED, "unknown syntax: %s",
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
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PARSE_FAILED, "bad code label prefix");
      return -1;
    }
    *io_argi = argi + 1;
    return 1;
  }
  if (strcmp(argv[argi], "--call-label-prefix") == 0) {
    if (argi + 1 >= argc || !m68k_set_bounded_string(policy->presentation.call_label_prefix,
        sizeof(policy->presentation.call_label_prefix), argv[argi + 1])) {
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PARSE_FAILED, "bad call label prefix");
      return -1;
    }
    *io_argi = argi + 1;
    return 1;
  }
  if (strcmp(argv[argi], "--data-label-prefix") == 0) {
    if (argi + 1 >= argc || !m68k_set_bounded_string(policy->presentation.data_label_prefix,
        sizeof(policy->presentation.data_label_prefix), argv[argi + 1])) {
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PARSE_FAILED, "bad data label prefix");
      return -1;
    }
    *io_argi = argi + 1;
    return 1;
  }
  if (strcmp(argv[argi], "--min-os-version") == 0) {
    compat_version = (argi + 1 < argc) ? amiga_os_parse_compatibility_version(argv[argi + 1])
                                       : AMIGA_OS_COMPAT_VERSION_NONE;
    if (argi + 1 >= argc || compat_version == AMIGA_OS_COMPAT_VERSION_NONE) {
      m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PARSE_FAILED,
        "unknown minimum os version: %s",
        (argi + 1 < argc) ? argv[argi + 1] : "");
      return -1;
    }
    policy->os.compatibility_kind = M68K_OS_COMPATIBILITY_AMIGA;
    policy->os.compatibility_level = (uint16_t)compat_version;
    *io_argi = argi + 1;
    return 1;
  }
  return 0;
}
