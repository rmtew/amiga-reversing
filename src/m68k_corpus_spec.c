#include "m68k_corpus_spec.h"
#include "m68k_parse_util.h"
#include "m68k_source_text_util.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static size_t parse_u16_list(const char *text, uint16_t *out_values, int hex_mode) {
  char buffer[256];
  char *parts[32];
  size_t count = 0;
  size_t part_count;
  size_t part_index;
  if (*text == '\0' || strcmp(text, "-") == 0) return 0;
  strcpy(buffer, text);
  part_count = m68k_split_delimited_in_place(buffer, ',', parts, sizeof(parts) / sizeof(parts[0]));
  if (part_count == 0) return 0;
  for (part_index = 0; part_index < part_count; ++part_index) {
    char *endptr;
    uint32_t value = (uint32_t)strtoul(parts[part_index], &endptr, hex_mode ? 16 : 10);
    if (*endptr != '\0') return 0;
    out_values[count++] = (uint16_t)value;
  }
  return count;
}

static int parse_operand_spec(const char *text, M68kAsmOperandValue *out_operand) {
  unsigned value0 = 0, value1 = 0, value2 = 0, value3 = 0, value4 = 0, value5 = 0;
  unsigned value6 = 0, value7 = 0, value8 = 0, value9 = 0, value10 = 0, value11 = 0;
  unsigned value12 = 0, value13 = 0, value14 = 0, value15 = 0, value16 = 0, value17 = 0;
  uint8_t special_register_kind;
  memset(out_operand, 0, sizeof(*out_operand));
  if (strcmp(text, "-") == 0) {
    out_operand->kind = M68K_ASM_OPERAND_NONE;
    return 1;
  }
  if (sscanf(text, "dn:%u", &value0) == 1) {
    out_operand->kind = M68K_ASM_OPERAND_DN;
    out_operand->reg = (uint8_t)value0;
    return 1;
  }
  if (sscanf(text, "dnpair:%u:%u", &value0, &value1) == 2) {
    out_operand->kind = M68K_ASM_OPERAND_DN_PAIR;
    out_operand->reg = (uint8_t)value0;
    out_operand->pair_reg = (uint8_t)value1;
    return 1;
  }
  if (sscanf(text, "an:%u", &value0) == 1) {
    out_operand->kind = M68K_ASM_OPERAND_AN;
    out_operand->reg = (uint8_t)value0;
    return 1;
  }
  if (sscanf(text, "disp:%u:%x", &value0, &value1) == 2) {
    out_operand->kind = M68K_ASM_OPERAND_EA;
    out_operand->ea_mode = 5;
    out_operand->ea_reg = (uint8_t)value0;
    out_operand->value = value1;
    return 1;
  }
  if (sscanf(text, "predec:%u", &value0) == 1) {
    out_operand->kind = M68K_ASM_OPERAND_EA;
    out_operand->ea_mode = 4;
    out_operand->ea_reg = (uint8_t)value0;
    return 1;
  }
  if (sscanf(text, "postinc:%u", &value0) == 1) {
    out_operand->kind = M68K_ASM_OPERAND_EA;
    out_operand->ea_mode = 3;
    out_operand->ea_reg = (uint8_t)value0;
    return 1;
  }
  if (sscanf(text, "reglist:%x", &value0) == 1) {
    out_operand->kind = M68K_ASM_OPERAND_REGLIST;
    out_operand->value = value0;
    return 1;
  }
  if (sscanf(text, "rn:%u:%u", &value0, &value1) == 2) {
    out_operand->kind = M68K_ASM_OPERAND_RN;
    out_operand->reg_is_address = (uint8_t)value0;
    out_operand->reg = (uint8_t)value1;
    return 1;
  }
  if (sscanf(text, "rnpair:%u:%u:%u:%u", &value0, &value1, &value2, &value3) == 4) {
    out_operand->kind = M68K_ASM_OPERAND_RN_PAIR;
    out_operand->reg_is_address = (uint8_t)value0;
    out_operand->reg = (uint8_t)value1;
    out_operand->pair_reg_is_address = (uint8_t)value2;
    out_operand->pair_reg = (uint8_t)value3;
    return 1;
  }
  special_register_kind = m68k_parse_special_register_token(text);
  if (special_register_kind != M68K_ASM_OPERAND_NONE) {
    out_operand->kind = special_register_kind;
    return 1;
  }
  if (sscanf(text, "ctrlreg:%u:%x", &value0, &value1) == 2) {
    out_operand->kind = M68K_ASM_OPERAND_CTRL_REG;
    out_operand->reg = (uint8_t)value0;
    out_operand->value = value1;
    return 1;
  }
  if (sscanf(text, "cache:%u", &value0) == 1 && value0 <= 3U) {
    out_operand->kind = M68K_ASM_OPERAND_CACHE_SEL;
    out_operand->value = value0;
    return 1;
  }
  if (sscanf(text, "bfeaf:%u:%u:%x:%u:%u:%u:%u:%u:%u:%u:%u:%u:%x:%x:%u:%u:%u:%u", &value0, &value1, &value2, &value3,
      &value4, &value5, &value6, &value7, &value8, &value9, &value10, &value11, &value12, &value13, &value14, &value15,
      &value16, &value17) == 18) {
    out_operand->kind = M68K_ASM_OPERAND_BF_EA;
    out_operand->ea_mode = (uint8_t)value0;
    out_operand->ea_reg = (uint8_t)value1;
    out_operand->value = value2;
    out_operand->index_is_address = (uint8_t)value3;
    out_operand->index_reg = (uint8_t)value4;
    out_operand->index_long = (uint8_t)value5;
    out_operand->scale = (uint8_t)value6;
    out_operand->full_ext_base_suppress = (uint8_t)value7;
    out_operand->full_ext_index_suppress = (uint8_t)value8;
    out_operand->full_ext_base_disp_size = (uint8_t)value9;
    out_operand->full_ext_outer_disp_size = (uint8_t)value10;
    out_operand->full_ext_iis = (uint8_t)value11;
    out_operand->full_ext_base_disp_value = value12;
    out_operand->full_ext_outer_disp_value = value13;
    out_operand->bf_offset_is_register = (uint8_t)value14;
    out_operand->bf_offset = (uint8_t)value15;
    out_operand->bf_width_is_register = (uint8_t)value16;
    out_operand->bf_width = (uint8_t)value17;
    return 1;
  }
  if (sscanf(text, "bfea:%u:%u:%x:%u:%u:%u:%u:%u:%u:%u", &value0, &value1, &value2, &value3, &value4, &value5, &value6,
      &value7, &value8, &value9) == 10) {
    out_operand->kind = M68K_ASM_OPERAND_BF_EA;
    out_operand->ea_mode = (uint8_t)value0;
    out_operand->ea_reg = (uint8_t)value1;
    out_operand->value = value2;
    out_operand->bf_offset_is_register = (uint8_t)value6;
    out_operand->bf_offset = (uint8_t)value7;
    out_operand->bf_width_is_register = (uint8_t)value8;
    out_operand->bf_width = (uint8_t)value9;
    if (value3 <= 1U && value4 <= 7U && value5 <= 1U) {
      out_operand->index_is_address = (uint8_t)value3;
      out_operand->index_reg = (uint8_t)value4;
      out_operand->index_long = (uint8_t)value5;
    }
    return 1;
  }
  if (sscanf(text, "imm:%x", &value0) == 1) {
    out_operand->kind = M68K_ASM_OPERAND_IMM;
    out_operand->value = value0;
    return 1;
  }
  if (sscanf(text, "label:%x", &value0) == 1) {
    out_operand->kind = M68K_ASM_OPERAND_LABEL;
    out_operand->value = value0;
    return 1;
  }
  if (sscanf(text, "eaf:%u:%u:%x:%u:%u:%u:%u:%u:%u:%u:%u:%u:%x:%x", &value0, &value1, &value2, &value3, &value4,
      &value5, &value6, &value7, &value8, &value9, &value10, &value11, &value12, &value13) == 14) {
    out_operand->kind = M68K_ASM_OPERAND_EA;
    out_operand->ea_mode = (uint8_t)value0;
    out_operand->ea_reg = (uint8_t)value1;
    out_operand->value = value2;
    out_operand->index_is_address = (uint8_t)value3;
    out_operand->index_reg = (uint8_t)value4;
    out_operand->index_long = (uint8_t)value5;
    out_operand->scale = (uint8_t)value6;
    out_operand->full_ext_base_suppress = (uint8_t)value7;
    out_operand->full_ext_index_suppress = (uint8_t)value8;
    out_operand->full_ext_base_disp_size = (uint8_t)value9;
    out_operand->full_ext_outer_disp_size = (uint8_t)value10;
    out_operand->full_ext_iis = (uint8_t)value11;
    out_operand->full_ext_base_disp_value = value12;
    out_operand->full_ext_outer_disp_value = value13;
    return 1;
  }
  if (sscanf(text, "ea:%u:%u:%x:%u:%u:%u:%u", &value0, &value1, &value2, &value3, &value4, &value5, &value6) == 7) {
    out_operand->kind = M68K_ASM_OPERAND_EA;
    out_operand->ea_mode = (uint8_t)value0;
    out_operand->ea_reg = (uint8_t)value1;
    out_operand->value = value2;
    out_operand->index_is_address = (uint8_t)value3;
    out_operand->index_reg = (uint8_t)value4;
    out_operand->index_long = (uint8_t)value5;
    out_operand->scale = (uint8_t)value6;
    return 1;
  }
  if (sscanf(text, "ea:%u:%u:%x", &value0, &value1, &value2) == 3) {
    out_operand->kind = M68K_ASM_OPERAND_EA;
    out_operand->ea_mode = (uint8_t)value0;
    out_operand->ea_reg = (uint8_t)value1;
    out_operand->value = value2;
    return 1;
  }
  if (sscanf(text, "ea:%u:%u", &value0, &value1) == 2) {
    out_operand->kind = M68K_ASM_OPERAND_EA;
    out_operand->ea_mode = (uint8_t)value0;
    out_operand->ea_reg = (uint8_t)value1;
    return 1;
  }
  return 0;
}

static int parse_operand_list(const char *text, M68kAsmOperandValue *out_operands, size_t operand_count) {
  char buffer[256];
  char *parts[M68K_INSTRUCTION_SPEC_MAX_OPERANDS];
  size_t count = 0;
  size_t index;
  if (strcmp(text, "-") == 0) {
    for (index = 0; index < operand_count; ++index) {
      memset(&out_operands[index], 0, sizeof(out_operands[index]));
      out_operands[index].kind = M68K_ASM_OPERAND_NONE;
    }
    return operand_count == 0;
  }
  strcpy(buffer, text);
  count = m68k_split_delimited_in_place(buffer, ';', parts, sizeof(parts) / sizeof(parts[0]));
  if (count != operand_count) return 0;
  for (index = 0; index < count; ++index) {
    if (!parse_operand_spec(parts[index], &out_operands[index])) return 0;
  }
  return 1;
}

int m68k_corpus_parse_instruction_spec(char *text, InstructionSpec *out_spec) {
  char *parts[5];
  size_t count = m68k_split_delimited_in_place(text, '^', parts, sizeof(parts) / sizeof(parts[0]));
  if (count != 5) return 0;
  memset(out_spec, 0, sizeof(*out_spec));
  out_spec->asm_form_index = M68K_ASM_FORM_NONE;
  out_spec->mnemonic_id = m68k_asm_mnemonic_id_from_name(parts[0]);
  out_spec->size_suffix = (strcmp(parts[1], "-") == 0 || parts[1][0] == '\0') ? '\0' : (char)tolower((unsigned char)parts[1][0]);
  out_spec->target_cpu = M68K_ASM_CPU_ANY;
  out_spec->operand_count = (size_t)strtoul(parts[2], NULL, 10);
  out_spec->patch_value_count = parse_u16_list(parts[3], out_spec->patch_values, 0);
  if (!parse_operand_list(parts[4], out_spec->operands, out_spec->operand_count)) return 0;
  return 1;
}
