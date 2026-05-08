#include "m68k_ir_codec.h"

#include "m68k_disassembler.h"
#include "m68k_instruction_spec.h"
#include "m68k_parse_util.h"
#include "platform_common.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>


static int mnemonic_id_is_bit_test_family(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_BCHG:
  case M68K_ASM_MNEMONIC_BCLR:
  case M68K_ASM_MNEMONIC_BSET:
  case M68K_ASM_MNEMONIC_BTST:
    return 1;
  default:
    return 0;
  }
}

static int mnemonic_id_is_branch_family(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_BHI:
  case M68K_ASM_MNEMONIC_BLS:
  case M68K_ASM_MNEMONIC_BCC:
  case M68K_ASM_MNEMONIC_BCS:
  case M68K_ASM_MNEMONIC_BNE:
  case M68K_ASM_MNEMONIC_BEQ:
  case M68K_ASM_MNEMONIC_BVC:
  case M68K_ASM_MNEMONIC_BVS:
  case M68K_ASM_MNEMONIC_BPL:
  case M68K_ASM_MNEMONIC_BMI:
  case M68K_ASM_MNEMONIC_BGE:
  case M68K_ASM_MNEMONIC_BLT:
  case M68K_ASM_MNEMONIC_BGT:
  case M68K_ASM_MNEMONIC_BLE:
  case M68K_ASM_MNEMONIC_BRA:
  case M68K_ASM_MNEMONIC_BSR:
    return 1;
  default:
    return 0;
  }
}

static int mnemonic_id_is_dbcc_family(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_DBT:
  case M68K_ASM_MNEMONIC_DBF:
  case M68K_ASM_MNEMONIC_DBHI:
  case M68K_ASM_MNEMONIC_DBLS:
  case M68K_ASM_MNEMONIC_DBCC:
  case M68K_ASM_MNEMONIC_DBCS:
  case M68K_ASM_MNEMONIC_DBNE:
  case M68K_ASM_MNEMONIC_DBEQ:
  case M68K_ASM_MNEMONIC_DBVC:
  case M68K_ASM_MNEMONIC_DBVS:
  case M68K_ASM_MNEMONIC_DBPL:
  case M68K_ASM_MNEMONIC_DBMI:
  case M68K_ASM_MNEMONIC_DBGE:
  case M68K_ASM_MNEMONIC_DBLT:
  case M68K_ASM_MNEMONIC_DBGT:
  case M68K_ASM_MNEMONIC_DBLE:
    return 1;
  default:
    return 0;
  }
}

static int mnemonic_id_is_scc_family(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_ST:
  case M68K_ASM_MNEMONIC_SF:
  case M68K_ASM_MNEMONIC_SHI:
  case M68K_ASM_MNEMONIC_SLS:
  case M68K_ASM_MNEMONIC_SCC:
  case M68K_ASM_MNEMONIC_SCS:
  case M68K_ASM_MNEMONIC_SNE:
  case M68K_ASM_MNEMONIC_SEQ:
  case M68K_ASM_MNEMONIC_SVC:
  case M68K_ASM_MNEMONIC_SVS:
  case M68K_ASM_MNEMONIC_SPL:
  case M68K_ASM_MNEMONIC_SMI:
  case M68K_ASM_MNEMONIC_SGE:
  case M68K_ASM_MNEMONIC_SLT:
  case M68K_ASM_MNEMONIC_SGT:
  case M68K_ASM_MNEMONIC_SLE:
    return 1;
  default:
    return 0;
  }
}

static int mnemonic_id_is_trap_family(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_TRAPT:
  case M68K_ASM_MNEMONIC_TRAPF:
  case M68K_ASM_MNEMONIC_TRAPHI:
  case M68K_ASM_MNEMONIC_TRAPLS:
  case M68K_ASM_MNEMONIC_TRAPCC:
  case M68K_ASM_MNEMONIC_TRAPCS:
  case M68K_ASM_MNEMONIC_TRAPNE:
  case M68K_ASM_MNEMONIC_TRAPEQ:
  case M68K_ASM_MNEMONIC_TRAPVC:
  case M68K_ASM_MNEMONIC_TRAPVS:
  case M68K_ASM_MNEMONIC_TRAPPL:
  case M68K_ASM_MNEMONIC_TRAPMI:
  case M68K_ASM_MNEMONIC_TRAPGE:
  case M68K_ASM_MNEMONIC_TRAPLT:
  case M68K_ASM_MNEMONIC_TRAPGT:
  case M68K_ASM_MNEMONIC_TRAPLE:
  case M68K_ASM_MNEMONIC_TRAPV:
  case M68K_ASM_MNEMONIC_TRAP:
    return 1;
  default:
    return 0;
  }
}

static int mnemonic_id_is_mul_div_word_default(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_MULU:
  case M68K_ASM_MNEMONIC_MULS:
  case M68K_ASM_MNEMONIC_DIVU:
  case M68K_ASM_MNEMONIC_DIVS:
    return 1;
  default:
    return 0;
  }
}

static int mnemonic_id_requires_long_size_suffix(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_LEA:
  case M68K_ASM_MNEMONIC_LINK:
  case M68K_ASM_MNEMONIC_MOVEQ:
  case M68K_ASM_MNEMONIC_PEA:
    return 1;
  default:
    return 0;
  }
}

static int mnemonic_id_is_ext_family(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_EXT:
  case M68K_ASM_MNEMONIC_EXTB:
    return 1;
  default:
    return 0;
  }
}

static int mnemonic_id_requires_word_size_suffix(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_SWAP:
    return 1;
  default:
    return 0;
  }
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
    char size_suffix, uint8_t has_exact_render_value, uint32_t exact_render_value, uint8_t syntax_mode) {
  uint32_t mask = 0xFFFFFFFFU;
  if (has_exact_render_value != 0U && syntax_mode != M68K_IR_SYNTAX_VASM)
    return append_format(out_text, out_text_size, inout_used, "#$%X", (unsigned)exact_render_value);
  if (size_suffix == 'b') mask = 0xFFU;
  else if (size_suffix == 'w') mask = 0xFFFFU;
  value &= mask;
  if (value == mask && mask >= 0xFFFFU)
    return append_format(out_text, out_text_size, inout_used, "#$%X", (unsigned)value);
  return append_format(out_text, out_text_size, inout_used, "#%u", (unsigned)value);
}

static int append_signed_immediate_text(char *out_text, size_t out_text_size, size_t *inout_used, uint32_t value,
    char size_suffix, uint8_t has_exact_render_value, uint32_t exact_render_value, uint8_t syntax_mode) {
  int32_t signed_value;
  if (has_exact_render_value != 0U && syntax_mode != M68K_IR_SYNTAX_VASM)
    return append_format(out_text, out_text_size, inout_used, "#$%X", (unsigned)exact_render_value);
  if (size_suffix == 'b') signed_value = (int32_t)m68k_sign_extend32(value, 8U);
  else if (size_suffix == 'w') signed_value = (int32_t)m68k_sign_extend32(value, 16U);
  else signed_value = (int32_t)value;
  return append_format(out_text, out_text_size, inout_used, "#%d", signed_value);
}

static int append_register_text(char *out_text, size_t out_text_size, size_t *inout_used, int is_address, uint8_t reg) {
  return append_format(out_text, out_text_size, inout_used, "%c%u", is_address ? 'a' : 'd', (unsigned)reg);
}

static int append_index_register_text(char *out_text, size_t out_text_size, size_t *inout_used,
    const M68kAsmOperandValue *operand) {
  if (append_format(out_text, out_text_size, inout_used, "%c%u.%c", operand->index_is_address ? 'a' : 'd',
      (unsigned)operand->index_reg, operand->index_long ? 'l' : 'w') != 0)
    return -1;
  if (operand->scale != 0U)
    return append_format(out_text, out_text_size, inout_used, "*%u", (unsigned)(1U << (operand->scale & 0x3U)));
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
  const M68kAsmFormDef *form;
  form = &g_m68k_asm_forms[instruction->asm_form_index];
  if (form->control_register_count != 0U) {
    for (index = 0; index < form->control_register_count; ++index) {
      const M68kAsmControlRegisterDef *entry = &g_m68k_asm_control_registers
        [g_m68k_asm_form_control_register_ids[form->control_register_start + index]];
      if (entry->value == value) return entry->name;
    }
    if (form->control_register_count == 1U) {
      const M68kAsmControlRegisterDef *entry = &g_m68k_asm_control_registers
        [g_m68k_asm_form_control_register_ids[form->control_register_start]];
      return entry->name;
    }
    return NULL;
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
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) return 0;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEM) return 0;
  if (instruction->operand_count != 2U) return 0;
  if (instruction->operands[0].kind != M68K_ASM_OPERAND_REGLIST) return 0;
  if (instruction->operands[1].kind != M68K_ASM_OPERAND_EA) return 0;
  return instruction->operands[1].value.ea_mode == 4U;
}

static int append_ea_text(char *out_text, size_t out_text_size, size_t *inout_used,
    const M68kAsmOperandValue *operand, char size_suffix, uint8_t has_exact_render_value,
    uint32_t exact_render_value, uint8_t syntax_mode) {
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
      if (has_exact_render_value != 0U && syntax_mode != M68K_IR_SYNTAX_VASM)
        return append_format(out_text, out_text_size, inout_used, "#$%X", (unsigned)exact_render_value);
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
  if (operand->symbol_ref.has_symbolic_addend != 0U &&
      operand->symbol_ref.symbolic_addend_name[0] != '\0') {
    snprintf(name_with_addend, sizeof(name_with_addend), "%s%c%s", operand->symbol_ref.name,
      operand->symbol_ref.symbolic_addend_value < 0 ? '-' : '+', operand->symbol_ref.symbolic_addend_name);
    name = name_with_addend;
  } else if (operand->symbol_ref.addend != 0) {
    snprintf(name_with_addend, sizeof(name_with_addend), "%s%+d", operand->symbol_ref.name,
      (int)operand->symbol_ref.addend);
    name = name_with_addend;
  }
  if (operand->kind == M68K_ASM_OPERAND_IMM)
    return append_format(out_text, out_text_size, inout_used, "#%s", name);
  if (operand->value.ea_mode == 7 && operand->value.ea_reg == 4)
    return append_format(out_text, out_text_size, inout_used, "#%s", name);
  if (operand->value.ea_mode == 7 && operand->value.ea_reg == 0)
    return append_format(out_text, out_text_size, inout_used, "%s.w", name);
  if (operand->value.ea_mode == 7 && operand->value.ea_reg == 1)
    return append_format(out_text, out_text_size, inout_used, "%s.l", name);
  if (operand->value.ea_mode == 5)
    return append_format(out_text, out_text_size, inout_used, "%s(a%u)", name, (unsigned)operand->value.ea_reg);
  if (operand->value.ea_mode == 2)
    return append_format(out_text, out_text_size, inout_used, "%s(a%u)", name, (unsigned)operand->value.ea_reg);
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
  uint8_t mnemonic_id;
  if (instruction->size_suffix != 'b' || instruction->operand_count == 0U) return 0;
  mnemonic_id = instruction->mnemonic_id;
  if (!mnemonic_id_is_branch_family(mnemonic_id)) return 0;
  return instruction->operand_count == 1U;
}

static int instruction_requires_explicit_size_suffix( const M68kInstructionIR *instruction) {
  uint8_t mnemonic_id;
  mnemonic_id = instruction->mnemonic_id;
  if (mnemonic_id_requires_long_size_suffix(mnemonic_id) && instruction->size_suffix == 'l') return 1;
  if (mnemonic_id_is_ext_family(mnemonic_id) && instruction->size_suffix != '\0') return 1;
  if (mnemonic_id_requires_word_size_suffix(mnemonic_id) && instruction->size_suffix == 'w') return 1;
  if (mnemonic_id_is_scc_family(mnemonic_id) && instruction->size_suffix == 'b') return 1;
  if (mnemonic_id_is_dbcc_family(mnemonic_id) && instruction->size_suffix == 'w') return 1;
  if (mnemonic_id_is_branch_family(mnemonic_id) && instruction->operand_count == 1U) return 1;
  if (mnemonic_id_is_bit_test_family(mnemonic_id) || mnemonic_id_is_mul_div_word_default(mnemonic_id)) return 1;
  if (mnemonic_id_is_trap_family(mnemonic_id) && instruction->operand_count != 0U) return 1;
  return 0;
}

static char instruction_render_size_suffix(const M68kInstructionIR *instruction, const M68kAsmFormDef *form) {
  uint8_t mnemonic_id;
  mnemonic_id = instruction->mnemonic_id;
  if (mnemonic_id_is_bit_test_family(mnemonic_id)) {
    if (instruction->operand_count != 2U) return instruction->size_suffix;
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
  if (mnemonic_id_is_mul_div_word_default(mnemonic_id)) return 'w';
  (void)form;
  return '\0';
}

static char instruction_operand_size_suffix(const M68kInstructionIR *instruction, const M68kAsmFormDef *form) {
  M68kAsmOperandValue operands[4];
  size_t operand_index;
  char size_suffix;
  if (form->mnemonic_id != M68K_ASM_MNEMONIC_NONE) {
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
  if (instruction_render_size_suffix(instruction, form) == '\0') return 0;
  if (instruction_requires_explicit_size_suffix(instruction)) return 1;
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) return 1;
  for (operand_index = 0; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    operands[operand_index] = instruction->operands[operand_index].value;
  }
  mask = m68k_asm_form_effective_size_mask_for_operands( form, operands, instruction->operand_count);
  if (mask == M68K_ASM_SIZE_B || mask == M68K_ASM_SIZE_W || mask == M68K_ASM_SIZE_L)
    return 0;
  return 1;
}

M68kInstructionIR m68k_ir_decode_one(const uint8_t *data, size_t size, uint8_t target_cpu,
      M68kDiagSink diagnostics) {
  M68kAsmOperandValue match_operands[4];
  M68kDisasmResult result;
  M68kInstructionIR instruction;
  size_t operand_index;
  m68k_ir_instruction_init(&instruction);
  result = m68k_disassemble_one_for_cpu(data, size, target_cpu, diagnostics);
  if (result.byte_count == 0U) return instruction;
  instruction.mnemonic_id = result.mnemonic_id;
  instruction.target_cpu = result.target_cpu;
  instruction.has_coprocessor_id = result.has_coprocessor_id;
  instruction.coprocessor_id = result.coprocessor_id;
  instruction.byte_count = result.byte_count;
  instruction.size_suffix = result.size_suffix;
  instruction.operand_count = result.operand_count;
  instruction.asm_form_index = result.asm_form_index;
  for (operand_index = 0; operand_index < result.operand_count && operand_index < 4U; ++operand_index) {
    instruction.operands[operand_index].kind = result.operand_kinds[operand_index];
    instruction.operands[operand_index].value = result.operands[operand_index];
    m68k_ir_symbol_ref_init(&instruction.operands[operand_index].symbol_ref);
    match_operands[operand_index] = result.operands[operand_index];
    match_operands[operand_index].kind = result.operand_kinds[operand_index];
    if (match_operands[operand_index].kind == M68K_ASM_OPERAND_IND ||
        match_operands[operand_index].kind == M68K_ASM_OPERAND_POSTINC ||
        match_operands[operand_index].kind == M68K_ASM_OPERAND_ABSL) {
      match_operands[operand_index].kind = M68K_ASM_OPERAND_EA;
    }
  }
  return instruction;
}

M68kIrEncodeResult m68k_ir_encode_one(const M68kInstructionIR *instruction, uint8_t *out_bytes, size_t max_bytes,
    M68kDiagSink diagnostics) {
  M68kIrEncodeResult result;
  const M68kAsmFormDef *form;
  M68kAsmInstructionSpec spec;
  M68kAsmOperandValue operands[4];
  char chosen_size;
  uint16_t patch_values[32];
  size_t operand_index;
  size_t byte_count = 0U;
  memset(&result, 0, sizeof(result));
  if (out_bytes == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_BAD_ARGUMENT, "bad arguments");
    return result;
  }
  form = &g_m68k_asm_forms[instruction->asm_form_index];
  for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
    m68k_instruction_operand_to_asm_value(&instruction->operands[operand_index], &operands[operand_index]);
  }
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) {
    uint16_t asm_form_index = m68k_asm_form_index_for_operands_id(instruction->mnemonic_id, operands,
        instruction->operand_count, instruction->size_suffix, instruction->target_cpu);
    form = &g_m68k_asm_forms[asm_form_index];
  }
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_ENCODE_FAILED, "unable to find form");
    return result;
  }
  for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
    if (!m68k_instruction_operand_matches_form_kind(&instruction->operands[operand_index],
        form->operand_kinds[operand_index])) {
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_ENCODE_FAILED, "operand kind mismatch");
      return result;
    }
  }
  if (instruction_uses_movem_predecrement_mask(instruction, form)) {
    operands[0].value = m68k_reverse_reglist_mask((uint16_t)operands[0].value);
  }
  chosen_size = m68k_asm_choose_size_suffix(form, operands, instruction->operand_count, instruction->size_suffix);
  if (chosen_size == '\0') chosen_size = instruction->size_suffix;
  if (form->patch_count > (sizeof(patch_values) / sizeof(patch_values[0]))) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_ENCODE_FAILED, "patch overflow");
    return result;
  }
  if (m68k_asm_build_patch_values(form->asm_form_index, chosen_size, operands, instruction->operand_count, patch_values,
      sizeof(patch_values) / sizeof(patch_values[0])) != 0) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_ENCODE_FAILED,
      "unable to build patch values");
    return result;
  }
  if (instruction->has_coprocessor_id != 0U) {
    size_t patch_index;
    for (patch_index = 0U; patch_index < form->patch_count; ++patch_index) {
      const M68kAsmFieldPatch *patch = &g_m68k_asm_patches[form->patch_start + patch_index];
      if (patch->field_kind == M68K_ASM_FIELD_ID) {
        patch_values[patch_index] = (uint16_t)(instruction->coprocessor_id & 0x7U);
      }
    }
  }
  memset(&spec, 0, sizeof(spec));
  spec.mnemonic_id = form->mnemonic_id;
  spec.size_suffix = chosen_size;
  spec.target_cpu = instruction->target_cpu;
  spec.operand_count = instruction->operand_count;
  spec.patch_values = patch_values;
  spec.patch_value_count = form->patch_count;
  spec.operands = operands;
  if (m68k_asm_assemble_instruction(&spec, out_bytes, max_bytes, &byte_count) != 0) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_ENCODE_FAILED,
      "unable to encode instruction");
    return result;
  }
  result.byte_count = byte_count;
  return result;
}

static M68kIrRenderResult render_one_with_policy_internal(const M68kInstructionIR *instruction, uint32_t offset,
    int render_unresolved_current_relative, const M68kRenderPolicy *policy, M68kDiagSink diagnostics) {
  M68kIrRenderResult result;
  char *out_text = result.text;
  size_t out_text_size = sizeof(result.text);
  uint8_t syntax_mode;
  size_t used = 0;
  size_t operand_index;
  const M68kAsmFormDef *form;
  memset(&result, 0, sizeof(result));
  char operand_size_suffix;
  syntax_mode = (policy != NULL) ? policy->syntax.syntax_mode : M68K_IR_SYNTAX_CANONICAL;
  (void)syntax_mode;
  form = &g_m68k_asm_forms[instruction->asm_form_index];
  if (append_text(out_text, out_text_size, &used, m68k_ir_instruction_mnemonic_name(instruction)) != 0)
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
      if (operand_has_renderable_symbol_name(operand, policy)) {
        if (append_symbolic_ea_text(out_text, out_text_size, &used, operand) != 0)
          goto overflow;
      } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ) {
        if (append_format(out_text, out_text_size, &used, "#%d",
              (int32_t)m68k_sign_extend32(operand->value.value, 8U)) != 0)
          goto overflow;
      } else if (strstr(form->syntax, "<displacement>") != NULL) {
        if (append_signed_immediate_text(out_text, out_text_size, &used, operand->value.value,
              operand_size_suffix, operand->has_exact_render_value, operand->exact_render_value, syntax_mode) != 0)
          goto overflow;
      } else if (append_immediate_text(out_text, out_text_size, &used, operand->value.value, operand_size_suffix,
            operand->has_exact_render_value, operand->exact_render_value, syntax_mode) != 0)
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
          append_ea_text(out_text, out_text_size, &used, &operand->value, operand_size_suffix,
            operand->has_exact_render_value, operand->exact_render_value, syntax_mode) != 0)
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
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_RENDER_FAILED,
        "unsupported operand render");
      result.text[0] = '\0';
      return result;
    }
  }
  return result;

overflow:
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_RENDER_FAILED, "render overflow");
  result.text[0] = '\0';
  return result;
}

M68kIrRenderResult m68k_ir_render_one_at_with_policy(const M68kInstructionIR *instruction, uint32_t offset,
    const M68kRenderPolicy *policy, M68kDiagSink diagnostics) {
  return render_one_with_policy_internal(instruction, offset, 1, policy, diagnostics);
}

M68kIrRenderResult m68k_ir_render_one_with_policy(const M68kInstructionIR *instruction,
    const M68kRenderPolicy *policy, M68kDiagSink diagnostics) {
  return render_one_with_policy_internal(instruction, 0U, 0, policy, diagnostics);
}


