#include "m68k_plain_parse.h"

#include "m68k_instruction_spec.h"
#include "m68k_parse_util.h"
#include "m68k_source_text_util.h"

#include "platform_common.h"

#include <ctype.h>
#include <stdio.h>
#include <string.h>

#define MAX_FORM_OPERANDS 4

static const M68kAsmEaTextFormDef *find_ea_text_form(uint8_t syntax_family, char size_suffix, char register_prefix,
    uint8_t target_cpu) {
  return m68k_asm_find_ea_text_form(syntax_family, size_suffix, register_prefix, target_cpu);
}

static int init_ea_operand_from_form(M68kAsmOperandValue *out_operand, uint8_t syntax_family, char size_suffix,
    char register_prefix, uint8_t target_cpu) {
  const M68kAsmEaTextFormDef *form = find_ea_text_form(syntax_family, size_suffix, register_prefix, target_cpu);
  if (form == NULL) return 0;
  out_operand->kind = M68K_ASM_OPERAND_EA;
  out_operand->ea_mode = form->ea_mode;
  out_operand->ea_reg = (uint8_t)(form->ea_reg >= 0 ? form->ea_reg : 0);
  return 1;
}

static int parse_signed_hex_option(const char *text, const char *prefix, uint32_t *out_value) {
  size_t prefix_len = strlen(prefix);
  uint32_t magnitude = 0;
  M68kParseU32Result parse_result;
  if (!m68k_ascii_prefix_equal_ci(text, prefix)) return 0;
  text += prefix_len;
  if (text[0] == '-') {
    parse_result = m68k_parse_number_u32(text + 1);
    if (!parse_result.ok) return 0;
    magnitude = parse_result.value;
    *out_value = (uint32_t)(0u - magnitude);
    return 1;
  }
  parse_result = m68k_parse_number_u32(text);
  if (!parse_result.ok) return 0;
  *out_value = parse_result.value;
  return 1;
}

static void parse_ea_options(char *option_text, M68kAsmOperandValue *out_operand, int *out_use_full) {
  char *parts[16];
  size_t part_count;
  size_t part_index;
  unsigned option_value = 0;
  *out_use_full = 0;
  part_count = m68k_split_delimited_in_place(option_text, ',', parts, sizeof(parts) / sizeof(parts[0]));
  if (part_count == 0) {
    *out_use_full = -1;
    return;
  }
  for (part_index = 0; part_index < part_count; ++part_index) {
    char *trimmed = m68k_trim_in_place(parts[part_index]);
    if (m68k_ascii_equal_ci(trimmed, "full")) {
      *out_use_full = 1;
    } else if (m68k_ascii_equal_ci(trimmed, "bs")) {
      *out_use_full = 1;
      out_operand->full_ext_base_suppress = 1;
    } else if (m68k_ascii_equal_ci(trimmed, "is")) {
      *out_use_full = 1;
      out_operand->full_ext_index_suppress = 1;
    } else if (parse_signed_hex_option(trimmed, "bdw=", &option_value)) {
      *out_use_full = 1;
      out_operand->full_ext_base_disp_size = M68K_ASM_FULL_EXT_BD_WORD;
      out_operand->full_ext_base_disp_value = option_value;
    } else if (parse_signed_hex_option(trimmed, "bdl=", &option_value)) {
      *out_use_full = 1;
      out_operand->full_ext_base_disp_size = M68K_ASM_FULL_EXT_BD_LONG;
      out_operand->full_ext_base_disp_value = option_value;
    } else if (parse_signed_hex_option(trimmed, "odw=", &option_value)) {
      *out_use_full = 1;
      out_operand->full_ext_outer_disp_size = M68K_ASM_FULL_EXT_BD_WORD;
      out_operand->full_ext_outer_disp_value = option_value;
    } else if (parse_signed_hex_option(trimmed, "odl=", &option_value)) {
      *out_use_full = 1;
      out_operand->full_ext_outer_disp_size = M68K_ASM_FULL_EXT_BD_LONG;
      out_operand->full_ext_outer_disp_value = option_value;
    } else if (sscanf(trimmed, "iis=%u", &option_value) == 1) {
      *out_use_full = 1;
      out_operand->full_ext_iis = (uint8_t)option_value;
    } else {
      *out_use_full = -1;
      return;
    }
  }
}

static void apply_full_extension_default(M68kAsmOperandValue *operand, int use_full) {
  if (use_full && operand->full_ext_base_disp_size == 0) {
    if (operand->value <= 0xFFFFU) {
      operand->full_ext_base_disp_size = operand->value == 0U ? M68K_ASM_FULL_EXT_BD_NULL : M68K_ASM_FULL_EXT_BD_WORD;
      operand->full_ext_base_disp_value = operand->value;
    } else {
      operand->full_ext_base_disp_size = M68K_ASM_FULL_EXT_BD_LONG;
      operand->full_ext_base_disp_value = operand->value;
    }
  }
}

static uint8_t indexed_scale_bits(unsigned scale) {
  return (uint8_t)(scale == 1 ? 0 : scale == 2 ? 1 : scale == 4 ? 2 : 3);
}

static void assign_indexed_ea_fields(char index_reg_kind, unsigned index_reg, char index_size, unsigned scale,
    uint8_t *out_index_is_address, uint8_t *out_index_reg, uint8_t *out_index_long, uint8_t *out_scale) {
  *out_index_is_address = (uint8_t)(tolower((unsigned char)index_reg_kind) == 'a');
  *out_index_reg = (uint8_t)index_reg;
  *out_index_long = (uint8_t)(tolower((unsigned char)index_size) == 'l');
  *out_scale = indexed_scale_bits(scale);
}

static int parse_indexed_ea_suffix(const char *text, const char *base_token, int uses_base_register,
    int has_value_prefix, uint32_t *out_value, uint8_t *out_base_reg, uint8_t *out_index_is_address,
    uint8_t *out_index_reg, uint8_t *out_index_long, uint8_t *out_scale) {
  unsigned value = 0, reg = 0, index_reg = 0, scale = 1;
  int consumed = 0;
  char index_reg_kind = '\0', index_size = '\0';
  char pattern_with_scale[40];
  char pattern_no_scale[40];
  if (uses_base_register) {
    snprintf(pattern_with_scale, sizeof(pattern_with_scale), "%s(%s%%u,%%c%%u.%%c*%%u)%%n",
      has_value_prefix ? "$%x" : "", base_token);
    snprintf(pattern_no_scale, sizeof(pattern_no_scale), "%s(%s%%u,%%c%%u.%%c)%%n", has_value_prefix ? "$%x" : "",
      base_token);
  } else {
    snprintf(pattern_with_scale, sizeof(pattern_with_scale), "%s(%s,%%c%%u.%%c*%%u)%%n", has_value_prefix ? "$%x" : "",
      base_token);
    snprintf(pattern_no_scale, sizeof(pattern_no_scale), "%s(%s,%%c%%u.%%c)%%n",
      has_value_prefix ? "$%x" : "", base_token);
  }
  if (uses_base_register) {
    if (has_value_prefix) {
      if (sscanf(text, pattern_with_scale, &value, &reg, &index_reg_kind,
                 &index_reg, &index_size, &scale, &consumed) == 6 &&
          text[consumed] == '\0' && reg <= 7 && index_reg <= 7) {
        *out_value = value;
        *out_base_reg = (uint8_t)reg;
        assign_indexed_ea_fields(index_reg_kind, index_reg, index_size, scale, out_index_is_address, out_index_reg,
          out_index_long, out_scale);
        return 1;
      }
      if (sscanf(text, pattern_no_scale, &value, &reg, &index_reg_kind, &index_reg, &index_size, &consumed) == 5 &&
          text[consumed] == '\0' && reg <= 7 && index_reg <= 7) {
        *out_value = value;
        *out_base_reg = (uint8_t)reg;
        assign_indexed_ea_fields(index_reg_kind, index_reg, index_size, 1, out_index_is_address, out_index_reg,
          out_index_long, out_scale);
        *out_scale = 0;
        return 1;
      }
    } else {
      if (sscanf(text, pattern_with_scale, &reg, &index_reg_kind, &index_reg, &index_size, &scale, &consumed) == 5 &&
          text[consumed] == '\0' && reg <= 7 && index_reg <= 7) {
        *out_base_reg = (uint8_t)reg;
        assign_indexed_ea_fields(index_reg_kind, index_reg, index_size, scale, out_index_is_address, out_index_reg,
          out_index_long, out_scale);
        return 1;
      }
      if (sscanf(text, pattern_no_scale, &reg, &index_reg_kind, &index_reg, &index_size, &consumed) == 4 &&
          text[consumed] == '\0' && reg <= 7 && index_reg <= 7) {
        *out_base_reg = (uint8_t)reg;
        assign_indexed_ea_fields(index_reg_kind, index_reg, index_size, 1, out_index_is_address, out_index_reg,
          out_index_long, out_scale);
        *out_scale = 0;
        return 1;
      }
    }
  } else {
    if (has_value_prefix) {
      if (sscanf(text, pattern_with_scale, &value, &index_reg_kind, &index_reg, &index_size, &scale, &consumed) == 5 &&
          text[consumed] == '\0' && index_reg <= 7) {
        *out_value = value;
        *out_base_reg = 0;
        assign_indexed_ea_fields(index_reg_kind, index_reg, index_size, scale, out_index_is_address, out_index_reg,
          out_index_long, out_scale);
        return 1;
      }
      if (sscanf(text, pattern_no_scale, &value, &index_reg_kind, &index_reg, &index_size, &consumed) == 4 &&
          text[consumed] == '\0' && index_reg <= 7) {
        *out_value = value;
        *out_base_reg = 0;
        assign_indexed_ea_fields(index_reg_kind, index_reg, index_size, 1, out_index_is_address, out_index_reg,
          out_index_long, out_scale);
        *out_scale = 0;
        return 1;
      }
    } else {
      if (sscanf(text, pattern_with_scale, &index_reg_kind, &index_reg, &index_size, &scale, &consumed) == 4 &&
          text[consumed] == '\0' && index_reg <= 7) {
        *out_base_reg = 0;
        assign_indexed_ea_fields(index_reg_kind, index_reg, index_size, scale, out_index_is_address, out_index_reg,
          out_index_long, out_scale);
        return 1;
      }
      if (sscanf(text, pattern_no_scale, &index_reg_kind, &index_reg, &index_size, &consumed) == 3 &&
          text[consumed] == '\0' && index_reg <= 7) {
        *out_base_reg = 0;
        assign_indexed_ea_fields(index_reg_kind, index_reg, index_size, 1, out_index_is_address, out_index_reg,
          out_index_long, out_scale);
        *out_scale = 0;
        return 1;
      }
    }
  }
  return 0;
}

static int parse_value(const M68kAsmEaTextFormDef *text_form, const char *text, uint32_t *out_value) {
  if (text_form->value_kind == M68K_ASM_EA_VALUE_NONE) return *text == '\0';
  {
    M68kParseU32Result parse_result = m68k_parse_number_u32(text);
    if (!parse_result.ok) return 0;
    *out_value = parse_result.value;
    return 1;
  }
}

static int parse_base_register_wrapped(const M68kAsmEaTextFormDef *text_form, const char *text, uint8_t *out_reg) {
  char pattern[32];
  unsigned reg = 0;
  int consumed = 0;
  snprintf(pattern, sizeof(pattern), "%s%s%%u%s%%n", text_form->prefix_token, text_form->base_token,
    text_form->suffix_token);
  if (sscanf(text, pattern, &reg, &consumed) != 1 || reg > 7 || text[consumed] != '\0') return 0;
  *out_reg = (uint8_t)reg;
  return 1;
}

static int parse_displacement_ea(const M68kAsmEaTextFormDef *text_form, const char *text, uint32_t *out_value,
    uint8_t *out_reg) {
  char buffer[128];
  char suffix_buffer[64];
  const char *suffix;
  snprintf(buffer, sizeof(buffer), "%s", text);
  {
    char base_pattern[32];
    snprintf(base_pattern, sizeof(base_pattern), "(%s", text_form->base_token);
    suffix = strstr(buffer, base_pattern);
  }
  if (suffix == NULL) return 0;
  snprintf(suffix_buffer, sizeof(suffix_buffer), "%s", suffix);
  buffer[suffix - buffer] = '\0';
  {
    char *force_word_suffix = strrchr(buffer, '.');
    if (force_word_suffix != NULL) {
      if (!m68k_ascii_equal_ci(force_word_suffix, ".w")) return 0;
      *force_word_suffix = '\0';
    }
  }
  if (!parse_value(text_form, m68k_trim_in_place(buffer), out_value)) return 0;
  if (text_form->uses_base_register) {
    unsigned reg = 0;
    int consumed = 0;
    if (sscanf(suffix_buffer, "(a%u)%n", &reg, &consumed) != 1 || reg > 7 || suffix_buffer[consumed] != '\0') return 0;
    *out_reg = (uint8_t)reg;
  } else {
    char expected[16];
    snprintf(expected, sizeof(expected), "(%s)", text_form->base_token);
    if (!m68k_ascii_equal_ci(suffix_buffer, expected)) return 0;
    *out_reg = 0;
  }
  return 1;
}

static int parse_indexed_ea(const M68kAsmEaTextFormDef *text_form, const char *text, uint32_t *out_value,
    uint8_t *out_base_reg, uint8_t *out_index_is_address, uint8_t *out_index_reg, uint8_t *out_index_long,
    uint8_t *out_scale) {
  char converted[128];
  if (parse_indexed_ea_suffix(text, text_form->base_token, text_form->uses_base_register, 1, out_value,
      out_base_reg, out_index_is_address, out_index_reg, out_index_long, out_scale)) return 1;
  {
    const char *paren = strchr(text, '(');
    if (paren != NULL && paren != text) {
      char prefix[32];
      uint32_t numeric_value = 0;
      size_t prefix_len = (size_t)(paren - text);
      if (prefix_len < sizeof(prefix)) {
        memcpy(prefix, text, prefix_len);
        prefix[prefix_len] = '\0';
        M68kParseU32Result parse_result = m68k_parse_number_u32(m68k_trim_in_place(prefix));
        if (parse_result.ok) {
          numeric_value = parse_result.value;
          snprintf(converted, sizeof(converted), "$%x%s", numeric_value, paren);
          if (parse_indexed_ea_suffix(converted, text_form->base_token, text_form->uses_base_register, 1,
              out_value, out_base_reg, out_index_is_address, out_index_reg, out_index_long, out_scale)) return 1;
        }
      }
    }
  }
  return parse_indexed_ea_suffix(text, text_form->base_token, text_form->uses_base_register, 0, out_value,
    out_base_reg, out_index_is_address, out_index_reg, out_index_long, out_scale);
}

static int parse_ea_by_family(const M68kAsmEaTextFormDef *text_form, const char *text,
    M68kAsmOperandValue *out_operand, int use_full, uint8_t target_cpu) {
  uint32_t value = 0;
  uint8_t reg = 0, base_reg = 0, index_is_address = 0, index_reg = 0, index_long = 0, scale = 0;
  if (!init_ea_operand_from_form(out_operand, text_form->syntax_family, text_form->size_suffix,
      text_form->register_prefix, target_cpu)) return 0;
  switch (text_form->syntax_family) {
  case M68K_ASM_EA_TEXT_IMMEDIATE:
    if (strncmp(text, text_form->prefix_token, strlen(text_form->prefix_token)) != 0) return 0;
    if (!parse_value(text_form, text + strlen(text_form->prefix_token), &value)) return 0;
    out_operand->value = value;
    return 1;
  case M68K_ASM_EA_TEXT_REG_DIRECT:
    {
      M68kParseRegisterResult reg_result = m68k_parse_register_token(text, text_form->register_prefix);
      if (!reg_result.ok) return 0;
      out_operand->reg = reg_result.reg;
    }
    out_operand->ea_reg = out_operand->reg;
    return 1;
  case M68K_ASM_EA_TEXT_AN_INDIRECT:
  case M68K_ASM_EA_TEXT_AN_POSTINC:
  case M68K_ASM_EA_TEXT_AN_PREDEC:
    if (!parse_base_register_wrapped(text_form, text, &reg)) return 0;
    out_operand->ea_reg = reg;
    return 1;
  case M68K_ASM_EA_TEXT_AN_DISP:
  case M68K_ASM_EA_TEXT_PC_DISP:
    if (!parse_displacement_ea(text_form, text, &value, &reg)) return 0;
    if (text_form->uses_base_register) out_operand->ea_reg = reg;
    out_operand->value = value;
    return 1;
  case M68K_ASM_EA_TEXT_AN_INDEX:
  case M68K_ASM_EA_TEXT_PC_INDEX:
    if (!parse_indexed_ea(text_form, text, &value, &base_reg, &index_is_address, &index_reg, &index_long, &scale))
      return 0;
    if (text_form->uses_base_register) out_operand->ea_reg = base_reg;
    out_operand->value = value;
    out_operand->index_is_address = index_is_address;
    out_operand->index_reg = index_reg;
    out_operand->index_long = index_long;
    out_operand->scale = scale;
    apply_full_extension_default(out_operand, use_full);
    return 1;
  case M68K_ASM_EA_TEXT_ABSOLUTE: {
    char buffer[128];
    char *suffix;
    snprintf(buffer, sizeof(buffer), "%s", text);
    if (strchr(buffer, ',') != NULL) return 0;
    if (buffer[0] == '(') {
      size_t length = strlen(buffer);
      char *close = strrchr(buffer, ')');
      if (close != NULL && close < buffer + length - 1 && close[1] == '.') {
        memmove(close, close + 1, strlen(close + 1) + 1);
        memmove(buffer, buffer + 1, strlen(buffer));
      }
    }
    if (strchr(buffer, '(') != NULL || strchr(buffer, ')') != NULL) return 0;
    suffix = strrchr(buffer, '.');
    if (suffix == NULL) return 0;
    if ((text_form->size_suffix == 'w' && !m68k_ascii_equal_ci(suffix, ".w")) ||
        (text_form->size_suffix == 'l' && !m68k_ascii_equal_ci(suffix, ".l"))) return 0;
    *suffix = '\0';
    if (!parse_value(text_form, m68k_trim_in_place(buffer), &value)) return 0;
    out_operand->value = value;
    return 1;
  }
  default:
    return 0;
  }
}

static int parse_ea_text(const char *text, uint8_t target_cpu, M68kAsmOperandValue *out_operand) {
  char base_buffer[128];
  char option_buffer[128];
  char *option_suffix;
  int use_full = 0;
  size_t asm_form_index;
  memset(out_operand, 0, sizeof(*out_operand));
  out_operand->kind = M68K_ASM_OPERAND_EA;
  option_suffix = strchr(text, '{');
  if (option_suffix != NULL) {
    char *option_end;
    size_t base_len = (size_t)(option_suffix - text);
    if (base_len >= sizeof(base_buffer)) return 0;
    memcpy(base_buffer, text, base_len);
    base_buffer[base_len] = '\0';
    text = base_buffer;
    option_end = strchr(option_suffix, '}');
    if (option_end == NULL) return 0;
    {
      size_t option_len = (size_t)(option_end - option_suffix - 1);
      if (option_len >= sizeof(option_buffer)) return 0;
      memcpy(option_buffer, option_suffix + 1, option_len);
      option_buffer[option_len] = '\0';
      parse_ea_options(option_buffer, out_operand, &use_full);
      if (use_full < 0) return 0;
      if (use_full > 0 && target_cpu != M68K_ASM_CPU_ANY && target_cpu < M68K_ASM_EA_FULL_EXTENSION_CPU_MIN) return 0;
    }
  }
  for (asm_form_index = 0; asm_form_index < g_m68k_asm_ea_text_form_count; ++asm_form_index) {
    const M68kAsmEaTextFormDef *text_form = &g_m68k_asm_ea_text_forms[asm_form_index];
    M68kAsmOperandValue candidate = *out_operand;
    if (!parse_ea_by_family(text_form, text, &candidate, use_full, target_cpu)) continue;
    *out_operand = candidate;
    return 1;
  }
  return 0;
}

static int parse_restricted_ea(const char *text, uint8_t target_cpu, char required_mode, int required_reg,
    M68kAsmOperandValue *out_operand) {
  if (!parse_ea_text(text, target_cpu, out_operand)) return 0;
  if (out_operand->kind != M68K_ASM_OPERAND_EA) return 0;
  if (out_operand->ea_mode != required_mode) return 0;
  if (required_reg >= 0 && out_operand->ea_reg != (uint8_t)required_reg) return 0;
  return 1;
}

static int parse_bitfield_value_token(const char *text, uint8_t *out_is_register, uint32_t *out_value) {
  M68kParseRegisterResult reg_result = m68k_parse_register_token(text, 'd');
  M68kParseU32Result value_result;
  if (reg_result.ok) {
    *out_is_register = 1;
    *out_value = reg_result.reg;
    return 1;
  }
  value_result = m68k_parse_number_u32(text);
  if (!value_result.ok) return 0;
  *out_is_register = 0;
  *out_value = value_result.value;
  return 1;
}

static int parse_bitfield_spec(const char *text, M68kAsmOperandValue *out_operand) {
  char buffer[64];
  char *separator, *offset_text, *width_text;
  uint8_t offset_is_register = 0, width_is_register = 0;
  uint32_t offset_value = 0, width_value = 0;
  if (strlen(text) >= sizeof(buffer)) return 0;
  strcpy(buffer, text);
  separator = strchr(buffer, ':');
  if (separator == NULL || strchr(separator + 1, ':') != NULL) return 0;
  *separator = '\0';
  offset_text = m68k_trim_in_place(buffer);
  width_text = m68k_trim_in_place(separator + 1);
  if (*offset_text == '\0' || *width_text == '\0') return 0;
  if (!parse_bitfield_value_token(offset_text, &offset_is_register, &offset_value)) return 0;
  if (!parse_bitfield_value_token(width_text, &width_is_register, &width_value)) return 0;
  if (!offset_is_register && offset_value > 31U) return 0;
  if (!width_is_register && (width_value == 0U || width_value > 32U)) return 0;
  out_operand->bf_offset_is_register = offset_is_register;
  out_operand->bf_offset = (uint8_t)offset_value;
  out_operand->bf_width_is_register = width_is_register;
  out_operand->bf_width = (uint8_t)width_value;
  return 1;
}

static int parse_bf_ea_text(const char *text, uint8_t target_cpu, M68kAsmOperandValue *out_operand) {
  const char *spec_open = strrchr(text, '{');
  const char *spec_close = strrchr(text, '}');
  char base_text[128];
  char spec_text[64];
  size_t base_len;
  size_t spec_len;
  M68kAsmOperandValue base_operand;
  if (spec_open == NULL || spec_close == NULL || spec_close < spec_open || spec_close[1] != '\0') return 0;
  if (strchr(spec_open + 1, '{') != NULL) return 0;
  if (strchr(spec_open + 1, ':') == NULL) return 0;
  base_len = (size_t)(spec_open - text);
  spec_len = (size_t)(spec_close - spec_open - 1);
  if (base_len == 0 || base_len >= sizeof(base_text) || spec_len == 0 || spec_len >= sizeof(spec_text)) return 0;
  memcpy(base_text, text, base_len);
  base_text[base_len] = '\0';
  memcpy(spec_text, spec_open + 1, spec_len);
  spec_text[spec_len] = '\0';
  if (!parse_ea_text(base_text, target_cpu, &base_operand)) return 0;
  if (base_operand.kind != M68K_ASM_OPERAND_EA) return 0;
  *out_operand = base_operand;
  out_operand->kind = M68K_ASM_OPERAND_BF_EA;
  return parse_bitfield_spec(spec_text, out_operand);
}

static int parse_operand_by_kind(const char *text, uint8_t operand_kind, uint8_t target_cpu,
    M68kAsmOperandValue *out_operand) {
  M68kParseRegisterResult reg_result;
  M68kParseControlRegisterResult control_result;
  M68kParseU32Result value_result;
  memset(out_operand, 0, sizeof(*out_operand));
  out_operand->kind = operand_kind;
  switch (operand_kind) {
  case M68K_ASM_OPERAND_DN:
    reg_result = m68k_parse_register_token(text, 'd');
    if (!reg_result.ok) return 0;
    out_operand->reg = reg_result.reg;
    return 1;
  case M68K_ASM_OPERAND_DN_PAIR:
    reg_result = m68k_parse_register_pair_token(text, 'd', 'd');
    if (!reg_result.ok) return 0;
    out_operand->reg = reg_result.reg;
    out_operand->pair_reg = reg_result.pair_reg;
    return 1;
  case M68K_ASM_OPERAND_AN:
    reg_result = m68k_parse_register_token(text, 'a');
    if (!reg_result.ok) return 0;
    out_operand->reg = reg_result.reg;
    return 1;
  case M68K_ASM_OPERAND_IND:
    return parse_restricted_ea(text, target_cpu, 2, -1, out_operand);
  case M68K_ASM_OPERAND_POSTINC:
    return parse_restricted_ea(text, target_cpu, 3, -1, out_operand);
  case M68K_ASM_OPERAND_ABSL:
    return parse_restricted_ea(text, target_cpu, 7, 1, out_operand);
  case M68K_ASM_OPERAND_REGLIST:
    return 0;
  case M68K_ASM_OPERAND_RN:
    reg_result = m68k_parse_register_token(text, 'd');
    if (reg_result.ok) {
      out_operand->reg = reg_result.reg;
      out_operand->reg_is_address = 0;
      return 1;
    }
    reg_result = m68k_parse_register_token(text, 'a');
    if (reg_result.ok) {
      out_operand->reg = reg_result.reg;
      out_operand->reg_is_address = 1;
      return 1;
    }
    return 0;
  case M68K_ASM_OPERAND_RN_PAIR:
    reg_result = m68k_parse_rn_pair_token(text);
    if (!reg_result.ok) return 0;
    out_operand->reg = reg_result.reg;
    out_operand->pair_reg = reg_result.pair_reg;
    out_operand->reg_is_address = reg_result.reg_is_address;
    out_operand->pair_reg_is_address = reg_result.pair_reg_is_address;
    return 1;
  case M68K_ASM_OPERAND_CCR:
  case M68K_ASM_OPERAND_SR:
  case M68K_ASM_OPERAND_USP:
    return m68k_parse_special_register_token(text) == operand_kind;
  case M68K_ASM_OPERAND_CTRL_REG:
    control_result = m68k_parse_control_register_token(text, target_cpu);
    if (!control_result.ok) return 0;
    out_operand->reg = control_result.id;
    out_operand->value = control_result.value;
    return 1;
  case M68K_ASM_OPERAND_CACHE_SEL:
    value_result = m68k_parse_cache_selector_token(text);
    if (!value_result.ok) return 0;
    out_operand->value = value_result.value;
    return 1;
  case M68K_ASM_OPERAND_IMM:
    if (*text != '#') return 0;
    value_result = m68k_parse_number_u32(text + 1);
    if (!value_result.ok) return 0;
    out_operand->value = value_result.value;
    return 1;
  case M68K_ASM_OPERAND_EA:
    return parse_ea_text(text, target_cpu, out_operand);
  case M68K_ASM_OPERAND_BF_EA:
    return parse_bf_ea_text(text, target_cpu, out_operand);
  case M68K_ASM_OPERAND_LABEL:
    value_result = m68k_parse_number_u32(text);
    if (!value_result.ok) return 0;
    out_operand->value = value_result.value;
    return 1;
  default:
    return 0;
  }
}

static int movem_reglist_token_index(const char *token, int use_predecrement_order, size_t *out_index) {
  M68kParseRegisterResult reg_result = m68k_parse_register_token(token, 'd');
  size_t index;
  if (reg_result.ok) {
    index = reg_result.reg;
  } else if ((reg_result = m68k_parse_register_token(token, 'a')).ok) {
    index = 8u + reg_result.reg;
  } else {
    return 0;
  }
  if (use_predecrement_order) index = 15u - index;
  *out_index = index;
  return 1;
}

static int movem_reglist_find_bit(const char *token, int use_predecrement_order, uint16_t *out_mask) {
  size_t index;
  if (!movem_reglist_token_index(token, use_predecrement_order, &index)) return 0;
  *out_mask = (uint16_t)(1u << index);
  return 1;
}

static uint16_t movem_reglist_mask_from_text(const char *text, int use_predecrement_order, int *out_ok) {
  char buffer[128];
  char *parts[16];
  size_t part_count;
  size_t part_index;
  uint16_t mask = 0;
  *out_ok = 0;
  if (*text == '\0') return 0;
  strcpy(buffer, text);
  part_count = m68k_split_delimited_in_place(buffer, '/', parts, sizeof(parts) / sizeof(parts[0]));
  if (part_count == 0) return 0;
  for (part_index = 0; part_index < part_count; ++part_index) {
    char *part = m68k_trim_in_place(parts[part_index]);
    char *dash = strchr(part, '-');
    if (dash != NULL) {
      uint16_t start_mask = 0;
      uint16_t end_mask = 0;
      size_t start_index;
      size_t end_index;
      *dash = '\0';
      if (!movem_reglist_find_bit(m68k_trim_in_place(part), use_predecrement_order, &start_mask) ||
          !movem_reglist_find_bit(m68k_trim_in_place(dash + 1), use_predecrement_order, &end_mask))
        return 0;
      for (start_index = 0; start_index < 16; ++start_index) if (start_mask == (uint16_t)(1u << start_index)) break;
      for (end_index = 0; end_index < 16; ++end_index) if (end_mask == (uint16_t)(1u << end_index)) break;
      if (start_index >= 16 || end_index >= 16) return 0;
      if (start_index > end_index) {
        size_t tmp = start_index;
        start_index = end_index;
        end_index = tmp;
      }
      for (; start_index <= end_index; ++start_index) mask |= (uint16_t)(1u << start_index);
    } else {
      uint16_t bit_mask = 0;
      if (!movem_reglist_find_bit(part, use_predecrement_order, &bit_mask)) return 0;
      mask |= bit_mask;
    }
  }
  *out_ok = 1;
  return mask;
}

static int candidate_form_allows_control_register(const M68kAsmFormDef *form,
    const M68kAsmOperandValue *operand) {
  size_t index;
  if (form == NULL || operand == NULL || operand->kind != M68K_ASM_OPERAND_CTRL_REG) return 0;
  if (form->control_register_count == 0U) return 1;
  for (index = 0; index < form->control_register_count; ++index) {
    if (g_m68k_asm_form_control_register_ids[form->control_register_start + index] == operand->reg)
      return 1;
  }
  return 0;
}

static int parse_instruction_text_to_spec(const char *line_text, InstructionSpec *out_instruction, uint8_t target_cpu) {
  char line[256];
  char *comment;
  char *space;
  char *operand_text = NULL;
  char *operands[MAX_FORM_OPERANDS] = {NULL, NULL, NULL, NULL};
  size_t operand_count = 0;
  char mnemonic_token[64];
  uint16_t best_form_index = M68K_ASM_FORM_NONE;
  InstructionSpec best_instruction;
  int best_score = -1;
  uint8_t mnemonic_id;
  M68kParseMnemonicResult mnemonic_result;
  size_t index;
  strcpy(line, line_text);
  comment = strchr(line, ';');
  if (comment != NULL) *comment = '\0';
  strcpy(line, m68k_trim_in_place(line));
  m68k_normalize_register_alias_tokens_in_place(line);
  m68k_normalize_pc_current_expr_in_place(line);
  if (line[0] == '\0') return 0;
  if (line[strlen(line) - 1] == ':') return 0;
  space = strchr(line, ' ');
  if (space != NULL) {
    *space = '\0';
    operand_text = m68k_trim_in_place(space + 1);
    if (*operand_text == '\0') operand_text = NULL;
  }
  memset(out_instruction, 0, sizeof(*out_instruction));
  out_instruction->target_cpu = target_cpu;
  out_instruction->asm_form_index = M68K_ASM_FORM_NONE;
  mnemonic_result = m68k_parse_mnemonic_token(line);
  mnemonic_id = mnemonic_result.mnemonic_id;
  out_instruction->size_suffix = mnemonic_result.size_suffix;
  if (mnemonic_id == M68K_ASM_MNEMONIC_NONE) return 0;
  strcpy(mnemonic_token, m68k_asm_mnemonic_name(mnemonic_id));
  if (operand_text != NULL) {
    if (!m68k_split_operands_in_place(operand_text, operands, MAX_FORM_OPERANDS, &operand_count))
      return 0;
  }
  out_instruction->mnemonic_id = mnemonic_id;
  out_instruction->operand_count = operand_count;
  memset(&best_instruction, 0, sizeof(best_instruction));
  for (index = 0; index < m68k_asm_form_count(); ++index) {
    const M68kAsmFormDef *candidate = &g_m68k_asm_forms[index];
    InstructionSpec candidate_instruction;
    char size_suffix;
    M68kAsmOperandValue patch_operands[MAX_FORM_OPERANDS];
    size_t operand_index;
    int use_movem_predecrement = 0;
    int candidate_score = 0;
    if (candidate->operand_count != operand_count) continue;
    if (candidate->mnemonic_id != mnemonic_id) continue;
    if (!m68k_asm_form_supports_cpu(candidate, out_instruction->target_cpu))
      continue;
    memset(&candidate_instruction, 0, sizeof(candidate_instruction));
    candidate_instruction.mnemonic_id = candidate->mnemonic_id;
    candidate_instruction.target_cpu = target_cpu;
    candidate_instruction.asm_form_index = M68K_ASM_FORM_NONE;
    candidate_instruction.size_suffix = out_instruction->size_suffix;
    candidate_instruction.operand_count = operand_count;
    for (operand_index = 0; operand_index < MAX_FORM_OPERANDS; ++operand_index) {
      memset(&candidate_instruction.operands[operand_index], 0, sizeof(candidate_instruction.operands[operand_index]));
      candidate_instruction.operand_label_names[operand_index][0] = '\0';
      candidate_instruction.operands[operand_index].kind = M68K_ASM_OPERAND_NONE;
    }
    for (operand_index = 0; operand_index < operand_count; ++operand_index) {
      if (candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_REGLIST) continue;
      if (!parse_operand_by_kind(operands[operand_index], candidate->operand_kinds[operand_index],
          candidate_instruction.target_cpu, &candidate_instruction.operands[operand_index])) {
        break;
      }
    }
    if (operand_index != operand_count) continue;
    for (operand_index = 0; operand_index < operand_count; ++operand_index) {
      if (candidate->operand_kinds[operand_index] != M68K_ASM_OPERAND_REGLIST) continue;
      if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVEM || operand_count != 2) break;
      if (operand_index == 0) {
        const M68kAsmOperandValue *ea_operand = &candidate_instruction.operands[1];
        use_movem_predecrement = (ea_operand->ea_mode == 4);
      } else {
        use_movem_predecrement = 0;
      }
      {
        int ok = 0;
        uint16_t mask = movem_reglist_mask_from_text(operands[operand_index], use_movem_predecrement, &ok);
        if (!ok)
          break;
        if (use_movem_predecrement) mask = m68k_reverse_reglist_mask(mask);
        candidate_instruction.operands[operand_index].kind = M68K_ASM_OPERAND_REGLIST;
        candidate_instruction.operands[operand_index].value = mask;
      }
    }
    if (operand_index != operand_count) continue;
    for (operand_index = 0; operand_index < operand_count; ++operand_index) {
      if (candidate_instruction.operands[operand_index].kind != M68K_ASM_OPERAND_CTRL_REG) continue;
      if (candidate_instruction.operands[operand_index].reg >= g_m68k_asm_control_register_count) continue;
      if (!candidate_form_allows_control_register(candidate, &candidate_instruction.operands[operand_index])) break;
      candidate_instruction.operands[operand_index].value =
          g_m68k_asm_control_registers[candidate_instruction.operands[operand_index].reg].value;
    }
    if (operand_index != operand_count) continue;
    size_suffix = m68k_asm_choose_size_suffix(candidate, candidate_instruction.operands, candidate_instruction.operand_count,
        candidate_instruction.size_suffix);
    if (size_suffix == '\0' && candidate_instruction.size_suffix != '\0')
      continue;
    for (operand_index = 0; operand_index < operand_count && operand_index < MAX_FORM_OPERANDS; ++operand_index) {
      patch_operands[operand_index] = candidate_instruction.operands[operand_index];
    }
    if (m68k_instruction_spec_uses_movem_predecrement_mask(&candidate_instruction)) {
      patch_operands[0].value = m68k_reverse_reglist_mask((uint16_t)patch_operands[0].value);
    }
    if (m68k_asm_build_patch_values((uint16_t)index, size_suffix, patch_operands, operand_count,
        candidate_instruction.patch_values, M68K_INSTRUCTION_SPEC_MAX_PATCH_VALUES) != 0) {
      continue;
    }
    for (operand_index = 0; operand_index < operand_count; ++operand_index) {
      switch (candidate->operand_kinds[operand_index]) {
      case M68K_ASM_OPERAND_DN:
      case M68K_ASM_OPERAND_AN:
      case M68K_ASM_OPERAND_DN_PAIR:
      case M68K_ASM_OPERAND_RN:
      case M68K_ASM_OPERAND_RN_PAIR:
      case M68K_ASM_OPERAND_CTRL_REG:
      case M68K_ASM_OPERAND_CACHE_SEL:
      case M68K_ASM_OPERAND_CCR:
      case M68K_ASM_OPERAND_SR:
      case M68K_ASM_OPERAND_USP:
        candidate_score += 4;
        break;
      case M68K_ASM_OPERAND_IND:
      case M68K_ASM_OPERAND_POSTINC:
      case M68K_ASM_OPERAND_ABSL:
      case M68K_ASM_OPERAND_BF_EA:
        candidate_score += 3;
        break;
      case M68K_ASM_OPERAND_EA:
      case M68K_ASM_OPERAND_LABEL:
      case M68K_ASM_OPERAND_IMM:
      case M68K_ASM_OPERAND_REGLIST:
        candidate_score += 1;
        break;
      default:
        break;
      }
    }
    candidate_instruction.asm_form_index = (uint16_t)index;
    candidate_instruction.size_suffix = size_suffix;
    if (candidate->mnemonic_id == M68K_ASM_MNEMONIC_PEA && candidate_instruction.size_suffix == 'l')
      candidate_instruction.size_suffix = '\0';
    candidate_instruction.patch_value_count = candidate->patch_count;
    if (candidate_score > best_score) {
      best_score = candidate_score;
      best_instruction = candidate_instruction;
      best_form_index = (uint16_t)index;
    }
  }
  if (best_form_index == M68K_ASM_FORM_NONE) return 0;
  *out_instruction = best_instruction;
  return 1;
}

int m68k_plain_parse_instruction_to_spec(const char *text, uint8_t target_cpu, InstructionSpec *out_instruction) {
  return parse_instruction_text_to_spec(text, out_instruction, target_cpu);
}

M68kInstructionIR m68k_plain_parse_instruction_to_ir(const char *text, uint8_t target_cpu,
    M68kDiagSink diagnostics) {
  InstructionSpec parsed;
  M68kInstructionIR instruction;
  m68k_ir_instruction_init(&instruction);
  if (text == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_BAD_ARGUMENT, "bad arguments");
    return instruction;
  }
  if (!m68k_plain_parse_instruction_to_spec(text, target_cpu, &parsed)) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_DECODE_FAILED, "unable to parse line");
    return instruction;
  }
  m68k_instruction_spec_to_ir(&parsed, &instruction);
  return instruction;
}


