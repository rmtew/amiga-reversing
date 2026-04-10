#include "m68k_ir_codec.h"

#include "m68k_disassembler.h"
#include "m68k_instruction_spec.h"
#include "m68k_parse_util.h"
#include "platform_common.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>


static int operand_matches_form_kind(const M68kOperandIR *operand, uint8_t form_kind) {
  if (operand == NULL) return 0;
  switch (form_kind) {
  case M68K_ASM_OPERAND_IND:
    return operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 2U;
  case M68K_ASM_OPERAND_POSTINC:
    return operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 3U;
  case M68K_ASM_OPERAND_ABSL:
    return operand->kind == M68K_ASM_OPERAND_EA &&
      operand->value.ea_mode == 7U && operand->value.ea_reg == 1U;
  case M68K_ASM_OPERAND_EA:
    return operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_IND ||
      operand->kind == M68K_ASM_OPERAND_POSTINC || operand->kind == M68K_ASM_OPERAND_ABSL;
  default:
    return operand->kind == form_kind;
  }
}

static const M68kAsmFormDef *instruction_form(const M68kInstructionIR *instruction) {
  if (instruction == NULL) return NULL;
  if (instruction->form_index == M68K_IR_INVALID_FORM_INDEX) return NULL;
  if ((size_t)instruction->form_index < m68k_asm_form_count()) return &g_m68k_asm_forms[instruction->form_index];
  return NULL;
}

static int append_format(char *out_text, size_t out_text_size, size_t *inout_used, const char *format, ...) {
  int written;
  va_list args;
  if (out_text == NULL || out_text_size == 0U || inout_used == NULL || format == NULL) return -1;
  if (*inout_used >= out_text_size) return -1;
  va_start(args, format);
  written = vsnprintf(out_text + *inout_used, out_text_size - *inout_used, format, args);
  va_end(args);
  if (written < 0 || (size_t)written >= out_text_size - *inout_used) return -1;
  *inout_used += (size_t)written;
  return 0;
}

static int append_text(char *out_text, size_t out_text_size, size_t *inout_used, const char *text) {
  return append_format(out_text, out_text_size, inout_used, "%s", text);
}

static int append_current_relative_expr(char *out_text, size_t out_text_size, size_t *inout_used, int32_t delta) {
  if (delta == 0) return append_text(out_text, out_text_size, inout_used, "*");
  if (delta > 0) return append_format(out_text, out_text_size, inout_used, "*+%d", (int)delta);
  return append_format(out_text, out_text_size, inout_used, "*%d", (int)delta);
}

static int append_signed_hex(char *out_text, size_t out_text_size, size_t *inout_used, int32_t value) {
  if (value < 0)
    return append_format(out_text, out_text_size, inout_used, "-$%X", (unsigned)(0u - (uint32_t)value));
  return append_format(out_text, out_text_size, inout_used, "$%X", (unsigned)value);
}

static int append_signed_hex_width(char *out_text, size_t out_text_size, size_t *inout_used, int32_t value,
    unsigned width) {
  if (value < 0)
    return append_format(out_text, out_text_size, inout_used, "-$%0*X", (int)width, (unsigned)(0u - (uint32_t)value));
  return append_format(out_text, out_text_size, inout_used, "$%0*X", (int)width, (unsigned)value);
}

static int append_immediate_text(char *out_text, size_t out_text_size, size_t *inout_used, uint32_t value,
    char size_suffix) {
  if (size_suffix == 'b') value &= 0xFFU;
  else if (size_suffix == 'w') value &= 0xFFFFU;
  return append_format(out_text, out_text_size, inout_used, "#%u", (unsigned)value);
}

static int append_register_text(char *out_text, size_t out_text_size, size_t *inout_used, int is_address, uint8_t reg) {
  return append_format(out_text, out_text_size, inout_used, "%c%u", is_address ? 'a' : 'd', (unsigned)reg);
}

static int append_index_register_text(char *out_text, size_t out_text_size, size_t *inout_used,
    const M68kAsmOperandValue *operand) {
  if (append_format(out_text, out_text_size, inout_used, "%c%u.%c", operand->index_is_address ? 'a' : 'd',
      (unsigned)operand->index_reg, operand->index_long ? 'l' : 'w') != 0)
    return -1;
  if (operand->scale > 1U)
    return append_format(out_text, out_text_size, inout_used, "*%u", (unsigned)operand->scale);
  return 0;
}

static int append_bitfield_value_text(char *out_text, size_t out_text_size, size_t *inout_used, uint8_t is_register,
  uint8_t value, uint8_t is_width) {
  if (is_register)
    return append_format(out_text, out_text_size, inout_used, "d%u", (unsigned)value);
  if (is_width && value == 0U)
    return append_text(out_text, out_text_size, inout_used, "32");
  return append_format(out_text, out_text_size, inout_used, "%u", (unsigned)value);
}

static int append_cache_selector_text(char *out_text, size_t out_text_size, size_t *inout_used, uint32_t value) {
  switch (value & 3U) {
  case 0:
    return append_text(out_text, out_text_size, inout_used, "nc");
  case 1:
    return append_text(out_text, out_text_size, inout_used, "dc");
  case 2:
    return append_text(out_text, out_text_size, inout_used, "ic");
  case 3:
    return append_text(out_text, out_text_size, inout_used, "bc");
  default:
    return -1;
  }
}

static const char *control_register_name_from_value(const M68kInstructionIR *instruction, uint32_t value,
    uint8_t reg_index) {
  size_t index;
  const M68kAsmFormDef *form = instruction_form(instruction);
  if (form != NULL && form->control_register_count != 0U) {
    for (index = 0; index < form->control_register_count; ++index) {
      const M68kAsmControlRegisterDef *entry = &g_m68k_asm_control_registers
        [g_m68k_asm_form_control_register_ids[form->control_register_start + index]];
      if (entry->value == value) return entry->name;
    }
  }
  if (reg_index < g_m68k_asm_control_register_count && g_m68k_asm_control_registers[reg_index].value == value) {
    return g_m68k_asm_control_registers[reg_index].name;
  }
  for (index = 0; index < g_m68k_asm_control_register_count; ++index) {
    if (g_m68k_asm_control_registers[index].value == value)
      return g_m68k_asm_control_registers[index].name;
  }
  return NULL;
}

static int append_reglist_text(char *out_text, size_t out_text_size, size_t *inout_used, uint16_t mask) {
  unsigned reg_index = 0;
  int emitted = 0;
  while (reg_index < 16U) {
    unsigned run_end = reg_index;
    unsigned start_reg;
    unsigned end_reg;
    int is_address;
    if ((mask & (1u << reg_index)) == 0u) {
      ++reg_index;
      continue;
    }
    while (run_end + 1U < 16U && (mask & (1u << (run_end + 1U))) != 0u && ((run_end + 1U) >= 8U) == (reg_index >= 8U))
      ++run_end;
    start_reg = reg_index & 7U;
    end_reg = run_end & 7U;
    is_address = reg_index >= 8U;
    if (emitted && append_text(out_text, out_text_size, inout_used, "/") != 0)
      return -1;
    if (run_end > reg_index) {
      if (append_format(out_text, out_text_size, inout_used, "%c%u-%c%u", is_address ? 'a' : 'd', start_reg,
          is_address ? 'a' : 'd', end_reg) != 0)
        return -1;
    } else if (append_register_text(out_text, out_text_size, inout_used, is_address, (uint8_t)start_reg) != 0) {
      return -1;
    }
    emitted = 1;
    reg_index = run_end + 1U;
  }
  return emitted ? 0 : append_text(out_text, out_text_size, inout_used, "0");
}

static int instruction_uses_movem_predecrement_mask(const M68kInstructionIR *instruction, const M68kAsmFormDef *form) {
  if (instruction == NULL || form == NULL) return 0;
  if (_stricmp(form->mnemonic, "movem") != 0 || instruction->operand_count != 2U) return 0;
  if (instruction->operands[0].kind != M68K_ASM_OPERAND_REGLIST) return 0;
  if (instruction->operands[1].kind != M68K_ASM_OPERAND_EA) return 0;
  return instruction->operands[1].value.ea_mode == 4U;
}

static int append_ea_text(char *out_text, size_t out_text_size, size_t *inout_used,
    const M68kAsmOperandValue *operand, char size_suffix) {
  int32_t disp = (int32_t)operand->value;
  switch (operand->ea_mode) {
  case 0:
    return append_register_text(out_text, out_text_size, inout_used, 0, operand->ea_reg);
  case 1:
    return append_register_text(out_text, out_text_size, inout_used, 1, operand->ea_reg);
  case 2:
    return append_format(out_text, out_text_size, inout_used, "(a%u)", (unsigned)operand->ea_reg);
  case 3:
    return append_format(out_text, out_text_size, inout_used, "(a%u)+", (unsigned)operand->ea_reg);
  case 4:
    return append_format(out_text, out_text_size, inout_used, "-(a%u)", (unsigned)operand->ea_reg);
  case 5:
    disp = (int32_t)m68k_sign_extend32(operand->value, 16U);
    if (append_signed_hex_width(out_text, out_text_size, inout_used, disp, 4U) != 0)
      return -1;
    return append_format(out_text, out_text_size, inout_used, "(a%u)", (unsigned)operand->ea_reg);
  case 6:
    disp = (int32_t)m68k_sign_extend32(operand->value, 8U);
    if (operand->full_ext_base_suppress != 0U || operand->full_ext_index_suppress != 0U ||
        operand->full_ext_base_disp_size != 0U || operand->full_ext_outer_disp_size != 0U ||
        operand->full_ext_iis != 0U) {
      if (append_text(out_text, out_text_size, inout_used, "$0") != 0)
        return -1;
      if (append_format(out_text, out_text_size, inout_used, "(a%u,", (unsigned)operand->ea_reg) != 0)
        return -1;
      if (append_index_register_text(out_text, out_text_size, inout_used, operand) != 0)
        return -1;
      if (append_text(out_text, out_text_size, inout_used, "){full") != 0)
        return -1;
      if (operand->full_ext_base_suppress != 0U &&
          append_text(out_text, out_text_size, inout_used, ",bs") != 0)
        return -1;
      if (operand->full_ext_index_suppress != 0U &&
          append_text(out_text, out_text_size, inout_used, ",is") != 0)
        return -1;
      if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_WORD &&
          append_text(out_text, out_text_size, inout_used, ",bdw=") != 0)
        return -1;
      if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_WORD &&
          append_signed_hex_width(out_text, out_text_size, inout_used,
            (int32_t)m68k_sign_extend32(operand->full_ext_base_disp_value, 16U), 4U) != 0)
        return -1;
      if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_LONG &&
          append_text(out_text, out_text_size, inout_used, ",bdl=") != 0)
        return -1;
      if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_LONG &&
          append_signed_hex_width(out_text, out_text_size, inout_used,
            (int32_t)operand->full_ext_base_disp_value, 8U) != 0)
        return -1;
      if (operand->full_ext_outer_disp_size == M68K_ASM_FULL_EXT_BD_WORD &&
          append_text(out_text, out_text_size, inout_used, ",odw=") != 0)
        return -1;
      if (operand->full_ext_outer_disp_size == M68K_ASM_FULL_EXT_BD_WORD &&
          append_signed_hex_width(out_text, out_text_size, inout_used,
            (int32_t)m68k_sign_extend32(operand->full_ext_outer_disp_value, 16U), 4U) != 0)
        return -1;
      if (operand->full_ext_outer_disp_size == M68K_ASM_FULL_EXT_BD_LONG &&
          append_text(out_text, out_text_size, inout_used, ",odl=") != 0)
        return -1;
      if (operand->full_ext_outer_disp_size == M68K_ASM_FULL_EXT_BD_LONG &&
          append_signed_hex_width(out_text, out_text_size, inout_used,
            (int32_t)operand->full_ext_outer_disp_value, 8U) != 0)
        return -1;
      if (operand->full_ext_iis != 0U &&
          append_format(out_text, out_text_size, inout_used, ",iis=%u",
            (unsigned)operand->full_ext_iis) != 0)
        return -1;
      return append_text(out_text, out_text_size, inout_used, "}");
    }
    if (append_signed_hex(out_text, out_text_size, inout_used, disp) != 0)
      return -1;
    if (append_format(out_text, out_text_size, inout_used, "(a%u,", (unsigned)operand->ea_reg) != 0)
      return -1;
    if (append_index_register_text(out_text, out_text_size, inout_used, operand) != 0)
      return -1;
    return append_text(out_text, out_text_size, inout_used, ")");
  case 7:
    switch (operand->ea_reg) {
    case 0:
      return append_format(out_text, out_text_size, inout_used, "$%04X.w", (unsigned)(operand->value & 0xFFFFU));
    case 1:
      return append_format(out_text, out_text_size, inout_used, "$%08X.l", (unsigned)operand->value);
    case 2:
      if (append_signed_hex(out_text, out_text_size, inout_used, (int32_t)operand->value) != 0)
        return -1;
      return append_text(out_text, out_text_size, inout_used, "(pc)");
    case 3:
      if (operand->full_ext_base_suppress != 0U || operand->full_ext_index_suppress != 0U ||
          operand->full_ext_base_disp_size != 0U || operand->full_ext_outer_disp_size != 0U ||
          operand->full_ext_iis != 0U) {
        if (append_signed_hex(out_text, out_text_size, inout_used, (int32_t)operand->value) != 0)
          return -1;
        if (append_text(out_text, out_text_size, inout_used, "(pc,") != 0)
          return -1;
        if (append_index_register_text(out_text, out_text_size, inout_used, operand) != 0)
          return -1;
        if (append_text(out_text, out_text_size, inout_used, "){full") != 0)
          return -1;
        if (operand->full_ext_base_suppress != 0U && append_text(out_text, out_text_size, inout_used, ",bs") != 0)
          return -1;
        if (operand->full_ext_index_suppress != 0U && append_text(out_text, out_text_size, inout_used, ",is") != 0)
          return -1;
        if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_WORD &&
            append_text(out_text, out_text_size, inout_used, ",bdw=") != 0)
          return -1;
        if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_WORD &&
            append_signed_hex_width(out_text, out_text_size, inout_used,
              (int32_t)m68k_sign_extend32(operand->full_ext_base_disp_value, 16U), 4U) != 0)
          return -1;
        if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_LONG &&
            append_text(out_text, out_text_size, inout_used, ",bdl=") != 0)
          return -1;
        if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_LONG &&
            append_signed_hex_width(out_text, out_text_size, inout_used,
              (int32_t)operand->full_ext_base_disp_value, 8U) != 0)
          return -1;
        if (operand->full_ext_outer_disp_size == M68K_ASM_FULL_EXT_BD_WORD &&
            append_text(out_text, out_text_size, inout_used, ",odw=") != 0)
          return -1;
        if (operand->full_ext_outer_disp_size == M68K_ASM_FULL_EXT_BD_WORD &&
            append_signed_hex_width(out_text, out_text_size, inout_used,
              (int32_t)m68k_sign_extend32(operand->full_ext_outer_disp_value, 16U), 4U) != 0)
          return -1;
        if (operand->full_ext_outer_disp_size == M68K_ASM_FULL_EXT_BD_LONG &&
            append_text(out_text, out_text_size, inout_used, ",odl=") != 0)
          return -1;
        if (operand->full_ext_outer_disp_size == M68K_ASM_FULL_EXT_BD_LONG &&
            append_signed_hex_width(out_text, out_text_size, inout_used,
              (int32_t)operand->full_ext_outer_disp_value, 8U) != 0)
          return -1;
        if (operand->full_ext_iis != 0U &&
            append_format(out_text, out_text_size, inout_used, ",iis=%u", (unsigned)operand->full_ext_iis) != 0)
          return -1;
        return append_text(out_text, out_text_size, inout_used, "}");
      }
      if (append_signed_hex(out_text, out_text_size, inout_used, (int32_t)operand->value) != 0)
        return -1;
      if (append_text(out_text, out_text_size, inout_used, "(pc,") != 0)
        return -1;
      if (append_index_register_text(out_text, out_text_size, inout_used, operand) != 0)
        return -1;
      return append_text(out_text, out_text_size, inout_used, ")");
    case 4:
      if (size_suffix == 'b')
        return append_format(out_text, out_text_size, inout_used, "#$%X", (unsigned)(operand->value & 0xFFU));
      if (size_suffix == 'w')
        return append_format(out_text, out_text_size, inout_used, "#$%X", (unsigned)(operand->value & 0xFFFFU));
      return append_format(out_text, out_text_size, inout_used, "#$%X", (unsigned)operand->value);
    default:
      return -1;
    }
  default:
    return -1;
  }
}

static int append_symbolic_ea_text(char *out_text, size_t out_text_size, size_t *inout_used,
    const M68kOperandIR *operand) {
  char name_with_addend[96];
  const char *name = NULL;
  if (operand == NULL || !operand->symbol_ref.has_name) return -1;
  name = operand->symbol_ref.name;
  if (operand->symbol_ref.addend != 0) {
    snprintf(name_with_addend, sizeof(name_with_addend), "%s%+d", operand->symbol_ref.name,
      (int)operand->symbol_ref.addend);
    name = name_with_addend;
  }
  if (operand->value.ea_mode == 7 && operand->value.ea_reg == 4)
    return append_format(out_text, out_text_size, inout_used, "#%s", name);
  if (operand->value.ea_mode == 7 && operand->value.ea_reg == 0)
    return append_format(out_text, out_text_size, inout_used, "%s.w", name);
  if (operand->value.ea_mode == 7 && operand->value.ea_reg == 1)
    return append_format(out_text, out_text_size, inout_used, "%s.l", name);
  if (operand->value.ea_mode == 7 && operand->value.ea_reg == 2)
    return append_format(out_text, out_text_size, inout_used, "%s(pc)", name);
  if (operand->value.ea_mode == 7 && operand->value.ea_reg == 3) {
    if (append_format(out_text, out_text_size, inout_used, "%s(pc,", name) != 0)
      return -1;
    if (append_index_register_text(out_text, out_text_size, inout_used, &operand->value) != 0)
      return -1;
    return append_text(out_text, out_text_size, inout_used, ")");
  }
  return append_text(out_text, out_text_size, inout_used, name);
}

static int operand_has_renderable_symbol_name(const M68kOperandIR *operand, const M68kRenderPolicy *policy) {
  if (operand == NULL || !operand->symbol_ref.has_name) return 0;
  if (operand->symbol_ref.name_is_generated == 0U) return 1;
  return policy == NULL || policy->presentation.prefer_generated_names != 0U;
}

static int instruction_uses_short_branch_suffix(const M68kInstructionIR *instruction) {
  if (instruction == NULL || instruction->size_suffix != 'b' || instruction->operand_count == 0U) return 0;
  if (_strnicmp(instruction->mnemonic, "b", 1) != 0) return 0;
  if (_stricmp(instruction->mnemonic, "bchg") == 0 || _stricmp(instruction->mnemonic, "bclr") == 0 ||
      _stricmp(instruction->mnemonic, "bset") == 0 || _stricmp(instruction->mnemonic, "btst") == 0 ||
      _strnicmp(instruction->mnemonic, "bf", 2) == 0) {
    return 0;
  }
  return instruction->operand_count == 1U;
}

static int instruction_requires_explicit_size_suffix( const M68kInstructionIR *instruction) {
  if (instruction == NULL) return 0;
  if (_strnicmp(instruction->mnemonic, "b", 1) == 0 && _stricmp(instruction->mnemonic, "bchg") != 0 &&
        _stricmp(instruction->mnemonic, "bclr") != 0 && _stricmp(instruction->mnemonic, "bset") != 0 &&
        _stricmp(instruction->mnemonic, "btst") != 0 && instruction->operand_count == 1U) {
    return 1;
  }
  if (_stricmp(instruction->mnemonic, "bchg") == 0 || _stricmp(instruction->mnemonic, "bclr") == 0 ||
      _stricmp(instruction->mnemonic, "bset") == 0 || _stricmp(instruction->mnemonic, "btst") == 0 ||
      _stricmp(instruction->mnemonic, "mulu") == 0 || _stricmp(instruction->mnemonic, "muls") == 0 ||
      _stricmp(instruction->mnemonic, "divu") == 0 || _stricmp(instruction->mnemonic, "divs") == 0) {
    return 1;
  }
  if (_strnicmp(instruction->mnemonic, "trap", 4) == 0 && instruction->operand_count != 0U) return 1;
  return 0;
}

static char instruction_render_size_suffix(const M68kInstructionIR *instruction, const M68kAsmFormDef *form) {
  if (instruction == NULL) return '\0';
  if ((_stricmp(instruction->mnemonic, "bchg") == 0 || _stricmp(instruction->mnemonic, "bclr") == 0 ||
      _stricmp(instruction->mnemonic, "bset") == 0 || _stricmp(instruction->mnemonic, "btst") == 0) &&
      instruction->operand_count == 2U) {
    const M68kOperandIR *target = &instruction->operands[1];
    int target_is_memory = 0;
    if (target->kind == M68K_ASM_OPERAND_EA) {
      target_is_memory = target->value.ea_mode != 0;
    } else if (target->kind == M68K_ASM_OPERAND_IND || target->kind == M68K_ASM_OPERAND_POSTINC ||
        target->kind == M68K_ASM_OPERAND_ABSL) {
      target_is_memory = 1;
    }
    if (target_is_memory) return 'b';
    return '\0';
  }
  if (instruction->size_suffix != '\0') return instruction->size_suffix;
  if (_stricmp(instruction->mnemonic, "mulu") == 0 ||
      _stricmp(instruction->mnemonic, "muls") == 0 ||
      _stricmp(instruction->mnemonic, "divu") == 0 ||
      _stricmp(instruction->mnemonic, "divs") == 0) {
    return 'w';
  }
  (void)form;
  return '\0';
}

static char instruction_operand_size_suffix(const M68kInstructionIR *instruction, const M68kAsmFormDef *form) {
  M68kAsmOperandValue operands[4];
  size_t operand_index;
  char size_suffix;
  if (instruction == NULL) return '\0';
  if (form != NULL) {
    for (operand_index = 0; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
      operands[operand_index] = instruction->operands[operand_index].value;
    }
    size_suffix = m68k_asm_choose_size_suffix(form, operands, instruction->operand_count, instruction->size_suffix);
    if (size_suffix != '\0') return size_suffix;
  }
  return instruction_render_size_suffix(instruction, form);
}

static int instruction_should_render_size_suffix(const M68kInstructionIR *instruction, const M68kAsmFormDef *form) {
  M68kAsmOperandValue operands[4];
  size_t operand_index;
  uint8_t mask;
  if (instruction == NULL) return 0;
  if (instruction_render_size_suffix(instruction, form) == '\0') return 0;
  if (instruction_requires_explicit_size_suffix(instruction)) return 1;
  if (form == NULL) return 1;
  for (operand_index = 0; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    operands[operand_index] = instruction->operands[operand_index].value;
  }
  mask = m68k_asm_form_effective_size_mask_for_operands( form, operands, instruction->operand_count);
  if (mask == M68K_ASM_SIZE_B || mask == M68K_ASM_SIZE_W || mask == M68K_ASM_SIZE_L)
    return 0;
  return 1;
}

int m68k_ir_decode_one(const uint8_t *data, size_t size, uint8_t target_cpu, M68kInstructionIR *out_instruction,
      char *out_error, size_t out_error_size) {
  M68kAsmOperandValue match_operands[4];
  M68kDisasmResult result;
  size_t operand_index;
  if (out_instruction == NULL) {
    m68k_platform_set_error(out_error, out_error_size, "null output");
    return -1;
  }
  m68k_ir_instruction_init(out_instruction);
  if (m68k_disassemble_one_for_cpu(data, size, target_cpu, &result) != 0) {
    m68k_platform_set_error(out_error, out_error_size, result.error);
    return -1;
  }
  out_instruction->mnemonic_id = result.mnemonic_id;
  out_instruction->target_cpu = result.target_cpu;
  out_instruction->byte_count = result.byte_count;
  out_instruction->size_suffix = result.size_suffix;
  out_instruction->operand_count = result.operand_count;
  out_instruction->form_index = result.form_index;
  snprintf(out_instruction->mnemonic, sizeof(out_instruction->mnemonic), "%s", result.mnemonic);
  for (operand_index = 0; operand_index < result.operand_count && operand_index < 4U; ++operand_index) {
    out_instruction->operands[operand_index].kind = result.operand_kinds[operand_index];
    out_instruction->operands[operand_index].value = result.operands[operand_index];
    m68k_ir_symbol_ref_init(&out_instruction->operands[operand_index].symbol_ref);
    match_operands[operand_index] = result.operands[operand_index];
    match_operands[operand_index].kind = result.operand_kinds[operand_index];
    if (match_operands[operand_index].kind == M68K_ASM_OPERAND_IND ||
        match_operands[operand_index].kind == M68K_ASM_OPERAND_POSTINC ||
        match_operands[operand_index].kind == M68K_ASM_OPERAND_ABSL) {
      match_operands[operand_index].kind = M68K_ASM_OPERAND_EA;
    }
  }
    m68k_platform_set_error(out_error, out_error_size, "");
    return 0;
  }

int m68k_ir_encode_one(const M68kInstructionIR *instruction, uint8_t *out_bytes, size_t max_bytes,
    size_t *out_byte_count, char *out_error, size_t out_error_size) {
  const M68kAsmFormDef *form = instruction_form(instruction);
  M68kAsmInstructionSpec spec;
  M68kAsmOperandValue operands[4];
  char chosen_size;
  uint16_t patch_values[32];
  size_t operand_index;
  if (instruction == NULL || out_bytes == NULL || out_byte_count == NULL) {
    m68k_platform_set_error(out_error, out_error_size, "bad arguments");
    if (out_byte_count != NULL)
      *out_byte_count = 0U;
    return -1;
  }
  for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
    operands[operand_index] = instruction->operands[operand_index].value;
  }
  if (form == NULL) {
    form = m68k_asm_find_form_for_operands( instruction->mnemonic, operands, instruction->operand_count,
        instruction->size_suffix, instruction->target_cpu);
  }
  if (form == NULL) {
    m68k_platform_set_error(out_error, out_error_size, "unable to find form");
    *out_byte_count = 0U;
    return -1;
  }
  for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
    if (!operand_matches_form_kind(&instruction->operands[operand_index], form->operand_kinds[operand_index])) {
      m68k_platform_set_error(out_error, out_error_size, "operand kind mismatch");
      *out_byte_count = 0U;
      return -1;
    }
  }
  if (instruction_uses_movem_predecrement_mask(instruction, form)) {
    operands[0].value = m68k_reverse_reglist_mask((uint16_t)operands[0].value);
  }
  chosen_size = m68k_asm_choose_size_suffix(form, operands, instruction->operand_count, instruction->size_suffix);
  if (chosen_size == '\0') chosen_size = instruction->size_suffix;
  if (form->patch_count > (sizeof(patch_values) / sizeof(patch_values[0]))) {
    m68k_platform_set_error(out_error, out_error_size, "patch overflow");
    *out_byte_count = 0U;
    return -1;
  }
  if (m68k_asm_build_patch_values(form, chosen_size, operands, instruction->operand_count, patch_values,
      sizeof(patch_values) / sizeof(patch_values[0])) != 0) {
    m68k_platform_set_error(out_error, out_error_size, "unable to build patch values");
    *out_byte_count = 0U;
    return -1;
  }
  memset(&spec, 0, sizeof(spec));
  spec.mnemonic = form->mnemonic;
  spec.size_suffix = chosen_size;
  spec.target_cpu = instruction->target_cpu;
  spec.operand_count = instruction->operand_count;
  spec.patch_values = patch_values;
  spec.patch_value_count = form->patch_count;
  spec.operands = operands;
  if (m68k_asm_assemble_instruction(&spec, out_bytes, max_bytes, out_byte_count) != 0) {
    m68k_platform_set_error(out_error, out_error_size, "unable to encode instruction");
    *out_byte_count = 0U;
    return -1;
  }
  m68k_platform_set_error(out_error, out_error_size, "");
  return 0;
}

static int render_one_with_policy_internal(const M68kInstructionIR *instruction, uint32_t offset,
    int render_unresolved_current_relative, const M68kRenderPolicy *policy, char *out_text, size_t out_text_size,
    char *out_error, size_t out_error_size) {
  uint8_t syntax_mode;
  size_t used = 0;
  size_t operand_index;
  const M68kAsmFormDef *form = instruction_form(instruction);
  char operand_size_suffix;
  syntax_mode = (policy != NULL) ? policy->syntax.syntax_mode : M68K_IR_SYNTAX_CANONICAL;
  (void)syntax_mode;
  if (instruction == NULL || out_text == NULL || out_text_size == 0U) {
    m68k_platform_set_error(out_error, out_error_size, "bad arguments");
    return -1;
  }
  out_text[0] = '\0';
  if (append_text(out_text, out_text_size, &used, instruction->mnemonic) != 0)
    goto overflow;
  if (instruction_should_render_size_suffix(instruction, form)) {
    char rendered_size = instruction_render_size_suffix(instruction, form);
    if ((syntax_mode == M68K_IR_SYNTAX_GENAM || syntax_mode == M68K_IR_SYNTAX_VASM) &&
        instruction_uses_short_branch_suffix(instruction)) {
      rendered_size = 's';
    }
    if (append_format(out_text, out_text_size, &used, ".%c", rendered_size) != 0)
      goto overflow;
  }
  operand_size_suffix = instruction_operand_size_suffix(instruction, form);
  if (operand_size_suffix == '\0') operand_size_suffix = instruction->size_suffix;
  if (instruction->operand_count != 0U &&
      append_text(out_text, out_text_size, &used, " ") != 0)
    goto overflow;
  for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (operand_index != 0U && append_text(out_text, out_text_size, &used, ",") != 0)
      goto overflow;
    switch (operand->kind) {
    case M68K_ASM_OPERAND_DN:
    case M68K_ASM_OPERAND_AN:
      if (append_register_text(out_text, out_text_size, &used, operand->kind == M68K_ASM_OPERAND_AN,
          operand->value.reg) != 0)
        goto overflow;
      break;
    case M68K_ASM_OPERAND_DN_PAIR:
      if (append_register_text(out_text, out_text_size, &used, 0, operand->value.reg) != 0 ||
          append_text(out_text, out_text_size, &used, ":") != 0 ||
          append_register_text(out_text, out_text_size, &used, 0, operand->value.pair_reg) != 0)
        goto overflow;
      break;
    case M68K_ASM_OPERAND_RN:
      if (append_register_text(out_text, out_text_size, &used, operand->value.reg_is_address, operand->value.reg) != 0)
        goto overflow;
      break;
    case M68K_ASM_OPERAND_RN_PAIR:
      if (append_text(out_text, out_text_size, &used, "(") != 0 ||
          append_register_text(out_text, out_text_size, &used, operand->value.reg_is_address, operand->value.reg) != 0 ||
          append_text(out_text, out_text_size, &used, "):(") != 0 ||
          append_register_text(out_text, out_text_size, &used, operand->value.pair_reg_is_address,
            operand->value.pair_reg) != 0 ||
          append_text(out_text, out_text_size, &used, ")") != 0)
        goto overflow;
      break;
    case M68K_ASM_OPERAND_IMM:
      if (append_immediate_text(out_text, out_text_size, &used, operand->value.value, operand_size_suffix) != 0)
        goto overflow;
      break;
    case M68K_ASM_OPERAND_LABEL:
      if (operand_has_renderable_symbol_name(operand, policy)) {
        if (append_text(out_text, out_text_size, &used, operand->symbol_ref.name) != 0)
          goto overflow;
      } else if (!render_unresolved_current_relative) {
        if (append_text(out_text, out_text_size, &used, "target") != 0)
          goto overflow;
      } else {
        uint32_t target = offset + 2U + (uint32_t)((int32_t)operand->value.value);
        if (append_current_relative_expr(out_text, out_text_size, &used, (int32_t)(target - offset)) != 0)
          goto overflow;
      }
      break;
    case M68K_ASM_OPERAND_EA:
    case M68K_ASM_OPERAND_BF_EA:
      if ((operand_has_renderable_symbol_name(operand, policy) == 0 ||
          append_symbolic_ea_text(out_text, out_text_size, &used, operand) != 0) &&
          append_ea_text(out_text, out_text_size, &used, &operand->value, operand_size_suffix) != 0)
        goto overflow;
      if (operand->kind == M68K_ASM_OPERAND_BF_EA) {
        if (append_text(out_text, out_text_size, &used, "{") != 0)
          goto overflow;
        if (append_bitfield_value_text(out_text, out_text_size, &used, operand->value.bf_offset_is_register,
            operand->value.bf_offset, 0) != 0)
          goto overflow;
        if (append_text(out_text, out_text_size, &used, ":") != 0)
          goto overflow;
        if (append_bitfield_value_text(out_text, out_text_size, &used, operand->value.bf_width_is_register,
            operand->value.bf_width, 1) != 0)
          goto overflow;
        if (append_text(out_text, out_text_size, &used, "}") != 0)
          goto overflow;
      }
      break;
    case M68K_ASM_OPERAND_IND:
      if (append_format(out_text, out_text_size, &used, "(a%u)",
                        (unsigned)operand->value.ea_reg) != 0)
        goto overflow;
      break;
    case M68K_ASM_OPERAND_POSTINC:
      if (append_format(out_text, out_text_size, &used, "(a%u)+",
                        (unsigned)operand->value.ea_reg) != 0)
        goto overflow;
      break;
    case M68K_ASM_OPERAND_ABSL:
      if (append_format(out_text, out_text_size, &used, "$%08X.l",
                        (unsigned)operand->value.value) != 0)
        goto overflow;
      break;
    case M68K_ASM_OPERAND_REGLIST:
      if (append_reglist_text(out_text, out_text_size, &used,
                              (uint16_t)operand->value.value) != 0)
        goto overflow;
      break;
    case M68K_ASM_OPERAND_CCR:
      if (append_text(out_text, out_text_size, &used, "ccr") != 0)
        goto overflow;
      break;
    case M68K_ASM_OPERAND_SR:
      if (append_text(out_text, out_text_size, &used, "sr") != 0)
        goto overflow;
      break;
    case M68K_ASM_OPERAND_USP:
      if (append_text(out_text, out_text_size, &used, "usp") != 0)
        goto overflow;
      break;
      case M68K_ASM_OPERAND_CTRL_REG: {
        const char *control_name = control_register_name_from_value(instruction, operand->value.value,
          operand->value.reg);
        if (control_name != NULL) {
          if (append_text(out_text, out_text_size, &used, control_name) != 0)
            goto overflow;
      } else {
        if (append_format(out_text, out_text_size, &used, "$%X", (unsigned)operand->value.value) != 0)
          goto overflow;
      }
    } break;
    case M68K_ASM_OPERAND_CACHE_SEL:
      if (append_cache_selector_text(out_text, out_text_size, &used, operand->value.value) != 0)
        goto overflow;
      break;
    default:
      m68k_platform_set_error(out_error, out_error_size, "unsupported operand render");
      return -1;
    }
  }
  m68k_platform_set_error(out_error, out_error_size, "");
  return 0;

overflow:
  m68k_platform_set_error(out_error, out_error_size, "render overflow");
  return -1;
}

int m68k_ir_render_one_at_with_policy(const M68kInstructionIR *instruction, uint32_t offset,
    const M68kRenderPolicy *policy, char *out_text, size_t out_text_size, char *out_error, size_t out_error_size) {
  return render_one_with_policy_internal(instruction, offset, 1, policy, out_text, out_text_size, out_error,
    out_error_size);
}

int m68k_ir_render_one_with_policy(const M68kInstructionIR *instruction, const M68kRenderPolicy *policy, char *out_text,
    size_t out_text_size, char *out_error, size_t out_error_size) {
  return render_one_with_policy_internal(instruction, 0U, 0, policy, out_text, out_text_size, out_error,
    out_error_size);
}


