/* Static disassembler runtime over generated KB-derived tables. */
#include "m68k_disassembler.h"
#include "m68k_asm_metadata.h"
#include "m68k_parse_util.h"
#include "platform_common.h"

#include <stdio.h>
#include <string.h>

typedef struct {
  uint16_t start;
  uint16_t count;
} M68kDisasmBucket;

#include "generated/m68k_disassembler_tables.h"

static uint16_t extract_bits16(uint16_t value, uint8_t bit_hi, uint8_t bit_lo) {
  uint16_t width = (uint16_t)(bit_hi - bit_lo + 1U);
  uint16_t mask = (uint16_t)((1U << width) - 1U);
  return (uint16_t)((value >> bit_lo) & mask);
}

static int syntax_has_explicit_size(const char *syntax) {
  size_t index = 0;
  if (syntax == NULL) return 0;
  while (syntax[index] != '\0' && syntax[index] != ' ') {
    if (syntax[index] == '.') return 1;
    ++index;
  }
  return 0;
}

static unsigned size_variant_count(uint8_t mask) {
  unsigned count = 0U;
  if ((mask & M68K_ASM_SIZE_B) != 0U) ++count;
  if ((mask & M68K_ASM_SIZE_W) != 0U) ++count;
  if ((mask & M68K_ASM_SIZE_L) != 0U) ++count;
  return count;
}

static int disasm_requires_explicit_size_suffix(const M68kAsmFormDef *form, char size_suffix) {
  if (size_suffix == '\0') return 0;
  return form->mnemonic_id == M68K_ASM_MNEMONIC_LINK && size_suffix == 'l';
}

static char choose_size_suffix(const M68kAsmFormDef *form, const M68kAsmOperandValue *operands, size_t operand_count,
    char explicit_suffix) {
  size_t patch_index;
  uint8_t mask;
  if (explicit_suffix != '\0') return explicit_suffix;
  for (patch_index = 0; patch_index < form->patch_count; ++patch_index) {
    const M68kAsmFieldPatch *patch = &g_m68k_disasm_patches[form->patch_start + patch_index];
    if (patch->field_kind == M68K_ASM_FIELD_SIZE || patch->field_kind == M68K_ASM_FIELD_DISPLACEMENT_8) return 'w';
  }
  if (form->size_value_l != M68K_ASM_FIELD_VALUE_UNSET &&
    form->size_value_b == M68K_ASM_FIELD_VALUE_UNSET &&
    form->size_value_w == M68K_ASM_FIELD_VALUE_UNSET) {
    return 'l';
  }
  mask = m68k_asm_form_effective_size_mask_for_operands(form, operands, operand_count);
  if (mask == M68K_ASM_SIZE_B) return 'b';
  if (mask == M68K_ASM_SIZE_W) return 'w';
  if (mask == M68K_ASM_SIZE_L) return 'l';
  return '\0';
}

static const M68kAsmFieldPatch *find_patch_for_field(const M68kAsmFormDef *form, uint8_t field_kind) {
  size_t index;
  for (index = 0; index < form->patch_count; ++index) {
    const M68kAsmFieldPatch *patch = &g_m68k_disasm_patches[form->patch_start + index];
    if (patch->field_kind == field_kind) return patch;
  }
  return NULL;
}

static char resolve_size_suffix(const M68kAsmFormDef *form, const uint16_t *field_values) {
  const M68kAsmFieldPatch *size_patch;
  const M68kAsmFieldPatch *opmode_patch;
  const M68kAsmFieldPatch *branch_patch;
  uint8_t mask;
  if (field_values == NULL) return '\0';
  branch_patch = find_patch_for_field(form, M68K_ASM_FIELD_DISPLACEMENT_8);
  if (branch_patch != NULL) {
    uint16_t value = field_values[branch_patch - &g_m68k_disasm_patches[form->patch_start]];
    if ((uint8_t)value == form->branch_word_signal) return 'w';
    if ((uint8_t)value == form->branch_long_signal) return 'l';
    return 'b';
  }
  size_patch = find_patch_for_field(form, M68K_ASM_FIELD_SIZE);
  if (size_patch != NULL) {
    uint16_t value = field_values[size_patch - &g_m68k_disasm_patches[form->patch_start]];
    if (form->size_value_b != M68K_ASM_FIELD_VALUE_UNSET && value == form->size_value_b) return 'b';
    if (form->size_value_w != M68K_ASM_FIELD_VALUE_UNSET && value == form->size_value_w) return 'w';
    if (form->size_value_l != M68K_ASM_FIELD_VALUE_UNSET && value == form->size_value_l) return 'l';
  }
  opmode_patch = find_patch_for_field(form, M68K_ASM_FIELD_OPMODE);
  if (opmode_patch != NULL) {
    uint16_t value = field_values[opmode_patch - &g_m68k_disasm_patches[form->patch_start]];
    if (form->opmode_value_b != M68K_ASM_FIELD_VALUE_UNSET && value == form->opmode_value_b) return 'b';
    if (form->opmode_value_w != M68K_ASM_FIELD_VALUE_UNSET && value == form->opmode_value_w) return 'w';
    if (form->opmode_value_l != M68K_ASM_FIELD_VALUE_UNSET && value == form->opmode_value_l) return 'l';
  }
  mask = m68k_asm_form_effective_size_mask(form);
  if (size_variant_count(mask) == 1U) {
    if ((mask & M68K_ASM_SIZE_B) != 0U) return 'b';
    if ((mask & M68K_ASM_SIZE_W) != 0U) return 'w';
    if ((mask & M68K_ASM_SIZE_L) != 0U) return 'l';
  }
  return '\0';
}

static int m68k_disasm_match_form(uint16_t disasm_form_index, const uint8_t *data, size_t size) {
  const M68kAsmFormDef *form = &g_m68k_disasm_forms[disasm_form_index];
  size_t word_index;
  uint16_t opword;
  if (data == NULL || size < 2U) return 0;
  opword = m68k_read_u16be(data);
  if ((opword & form->opword_mask) != form->opword_base) return 0;
  if (size < 2U + ((size_t)form->bound_word_count * 2U)) return 0;
  for (word_index = 0; word_index < form->bound_word_count; ++word_index) {
    uint16_t bound_word = m68k_read_u16be(data + 2U + (word_index * 2U));
    if ((bound_word & form->bound_word_masks[word_index]) != form->bound_word_bases[word_index]) return 0;
  }
  return 1;
}

static M68kDisasmResult make_result(size_t byte_count, const char *text, uint16_t disasm_form_index,
    const M68kAsmOperandValue *operands, char size_suffix, uint8_t target_cpu) {
  M68kDisasmResult result;
  const M68kAsmFormDef *form = &g_m68k_disasm_forms[disasm_form_index];
  const M68kAsmFormDef *canonical_form;
  const M68kAsmFormDef *result_form;
  memset(&result, 0, sizeof(result));
  canonical_form = &g_m68k_asm_forms[form->asm_form_index];
  result_form = canonical_form->mnemonic_id != M68K_ASM_MNEMONIC_NONE ? canonical_form : form;
  result.byte_count = byte_count;
  result.asm_form_index = canonical_form->asm_form_index;
  result.disasm_form_index = disasm_form_index;
  result.target_cpu = target_cpu;
  result.mnemonic_id = form->mnemonic_id;
  snprintf(result.mnemonic, sizeof(result.mnemonic), "%s", result_form->mnemonic);
  result.size_suffix = size_suffix;
  {
    size_t operand_index;
    result.operand_count = result_form->operand_count;
    for (operand_index = 0; operand_index < result_form->operand_count && operand_index < 4U; ++operand_index) {
      result.operand_kinds[operand_index] = result_form->operand_kinds[operand_index];
      result.operands[operand_index] = operands[operand_index];
    }
  }
  if (text != NULL) snprintf(result.text, sizeof(result.text), "%s", text);
  return result;
}

static int extract_patch_values(uint16_t disasm_form_index, const uint8_t *data, uint16_t *field_values) {
  const M68kAsmFormDef *form = &g_m68k_disasm_forms[disasm_form_index];
  size_t patch_index;
  if (data == NULL || field_values == NULL) return -1;
  for (patch_index = 0; patch_index < form->patch_count; ++patch_index) {
    const M68kAsmFieldPatch *patch = &g_m68k_disasm_patches[form->patch_start + patch_index];
    uint16_t word;
    if (patch->word_index == 0U) {
      word = m68k_read_u16be(data);
    } else if ((size_t)patch->word_index <= form->bound_word_count) {
      word = m68k_read_u16be(data + ((size_t)patch->word_index * 2U));
    } else {
      return -1;
    }
    field_values[patch_index] = extract_bits16(word, patch->bit_hi, patch->bit_lo);
  }
  return 0;
}

static int value_matches_form_sizes(uint16_t value, uint8_t b, uint8_t w, uint8_t l) {
  return ((b != M68K_ASM_FIELD_VALUE_UNSET && value == b) || (w != M68K_ASM_FIELD_VALUE_UNSET && value == w) ||
    (l != M68K_ASM_FIELD_VALUE_UNSET && value == l));
}

static int validate_patch_values(uint16_t disasm_form_index, const uint16_t *field_values) {
  const M68kAsmFormDef *form = &g_m68k_disasm_forms[disasm_form_index];
  size_t patch_index;
  if (field_values == NULL) return -1;
  for (patch_index = 0; patch_index < form->patch_count; ++patch_index) {
    const M68kAsmFieldPatch *patch = &g_m68k_disasm_patches[form->patch_start + patch_index];
    uint16_t value = field_values[patch_index];
    if (patch->field_kind == M68K_ASM_FIELD_SIZE &&
      !value_matches_form_sizes(value, form->size_value_b, form->size_value_w, form->size_value_l)) return -1;
    if (patch->field_kind == M68K_ASM_FIELD_OPMODE &&
      !value_matches_form_sizes(value, form->opmode_value_b, form->opmode_value_w, form->opmode_value_l)) return -1;
  }
  return 0;
}

static int minimum_remaining_extension_bytes(uint16_t disasm_form_index, size_t start_extension_index,
    const M68kAsmOperandValue *operands, char size_suffix) {
  const M68kAsmFormDef *form = &g_m68k_disasm_forms[disasm_form_index];
  size_t extension_index;
  int total = 0;
  if (operands == NULL) return -1;
  for (extension_index = start_extension_index; extension_index < form->extension_count; ++extension_index) {
    const M68kAsmExtensionDef *extension = &g_m68k_disasm_extensions[form->extension_start + extension_index];
    const M68kAsmOperandValue *operand = &operands[extension->operand_index];
    switch (extension->kind) {
      case M68K_ASM_EXTENSION_EA_SINGLE_WORD:
        if ((operand->ea_mode == 5U) || (operand->ea_mode == 7U && operand->ea_reg == 0U) ||
          (operand->ea_mode == 7U && operand->ea_reg == 2U)) total += 2;
        break;
      case M68K_ASM_EXTENSION_EA_LONG_ADDRESS:
        if (operand->ea_mode == 7U && operand->ea_reg == 1U) total += 4;
        break;
      case M68K_ASM_EXTENSION_EA_IMMEDIATE:
        if (operand->kind == M68K_ASM_OPERAND_IMM ||
          (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 7U && operand->ea_reg == 4U)) {
          total += (size_suffix == 'l') ? 4 : 2;
        }
        break;
      case M68K_ASM_EXTENSION_EA_INDEX:
        if ((operand->ea_mode == 6U) || (operand->ea_mode == 7U && operand->ea_reg == 3U)) total += 2;
        break;
      case M68K_ASM_EXTENSION_LABEL_DISP16_IF_ZERO:
        if ((uint8_t)operand->value == form->branch_word_signal) total += (int)form->branch_word_bytes;
        else if ((uint8_t)operand->value == form->branch_long_signal) total += (int)form->branch_long_bytes;
        break;
      case M68K_ASM_EXTENSION_LABEL_DISP16_ALWAYS:
        total += (int)form->branch_word_bytes;
        break;
      case M68K_ASM_EXTENSION_DISP16_ALWAYS:
        total += 2;
        break;
      default:
        return -1;
    }
  }
  return total;
}

static int decode_index_extension(const uint8_t *data, size_t size, M68kAsmOperandValue *operand, size_t *io_offset,
    int allow_full_extension) {
  uint16_t ext;
  size_t offset;
  if (data == NULL || operand == NULL || io_offset == NULL) return -1;
  offset = *io_offset;
  if (offset + 2U > size) return -1;
  ext = m68k_read_u16be(data + offset);
  offset += 2U;
  operand->index_is_address = (uint8_t)((ext >> M68K_ASM_BRIEF_EXT_DA_BIT_LO) & 0x1U);
  operand->index_reg = (uint8_t)((ext >> M68K_ASM_BRIEF_EXT_REGISTER_BIT_LO) & 0x7U);
  operand->index_long = (uint8_t)((ext >> M68K_ASM_BRIEF_EXT_WL_BIT_LO) & 0x1U);
  operand->scale = (uint8_t)((ext >> M68K_ASM_BRIEF_EXT_SCALE_BIT_LO) & 0x3U);
  operand->value = m68k_sign_extend32((uint32_t)(ext & 0xFFU), 8U);
  if (allow_full_extension && ((ext >> M68K_ASM_FULL_EXT_FORMAT_BIT_LO) & 0x1U) != 0U) {
    size_t remaining;
    operand->value = 0U;
    operand->full_ext_base_suppress = (uint8_t)((ext >> M68K_ASM_FULL_EXT_BS_BIT_LO) & 0x1U);
    operand->full_ext_index_suppress = (uint8_t)((ext >> M68K_ASM_FULL_EXT_IS_BIT_LO) & 0x1U);
    operand->full_ext_base_disp_size = (uint8_t)((ext >> M68K_ASM_FULL_EXT_BD_SIZE_BIT_LO) & 0x3U);
    operand->full_ext_iis = (uint8_t)((ext >> M68K_ASM_FULL_EXT_IIS_BIT_LO) & 0x7U);
    if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_WORD) {
      if (offset + 2U > size) return -1;
      operand->full_ext_base_disp_value = m68k_sign_extend32((uint32_t)m68k_read_u16be(data + offset), 16U);
      offset += 2U;
    } else if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_LONG) {
      if (offset + 4U > size) return -1;
      operand->full_ext_base_disp_value = m68k_read_u32be(data + offset);
      offset += 4U;
    }
    remaining = size - offset;
    if (remaining == 2U) {
      operand->full_ext_outer_disp_size = M68K_ASM_FULL_EXT_BD_WORD;
      operand->full_ext_outer_disp_value = m68k_sign_extend32((uint32_t)m68k_read_u16be(data + offset), 16U);
      offset += 2U;
    } else if (remaining == 4U) {
      operand->full_ext_outer_disp_size = M68K_ASM_FULL_EXT_BD_LONG;
      operand->full_ext_outer_disp_value = m68k_read_u32be(data + offset);
      offset += 4U;
    }
  }
  *io_offset = offset;
  return 0;
}

static int decode_extensions(uint16_t disasm_form_index, const uint8_t *data, size_t size,
    M68kAsmOperandValue *operands, char size_suffix, size_t *out_byte_count) {
  const M68kAsmFormDef *form = &g_m68k_disasm_forms[disasm_form_index];
  size_t offset;
  size_t extension_index;
  if (data == NULL || operands == NULL || out_byte_count == NULL) return -1;
  offset = 2U + ((size_t)form->bound_word_count * 2U);
  for (extension_index = 0; extension_index < form->extension_count; ++extension_index) {
    const M68kAsmExtensionDef *extension = &g_m68k_disasm_extensions[form->extension_start + extension_index];
    M68kAsmOperandValue *operand = &operands[extension->operand_index];
    switch (extension->kind) {
      case M68K_ASM_EXTENSION_EA_SINGLE_WORD:
        if ((operand->ea_mode == 5U) || (operand->ea_mode == 7U && operand->ea_reg == 0U) ||
          (operand->ea_mode == 7U && operand->ea_reg == 2U)) {
          if (offset + 2U > size) return -1;
          operand->value = m68k_sign_extend32((uint32_t)m68k_read_u16be(data + offset), 16U);
          offset += 2U;
        }
        break;
      case M68K_ASM_EXTENSION_EA_LONG_ADDRESS:
        if (operand->ea_mode == 7U && operand->ea_reg == 1U) {
          if (offset + 4U > size) return -1;
          operand->value = m68k_read_u32be(data + offset);
          offset += 4U;
        }
        break;
      case M68K_ASM_EXTENSION_EA_IMMEDIATE:
        if (operand->kind == M68K_ASM_OPERAND_IMM ||
          (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 7U && operand->ea_reg == 4U)) {
          if (offset + 2U > size) return -1;
          if (size_suffix == 'l') {
            if (offset + 4U > size) return -1;
            operand->value = m68k_read_u32be(data + offset);
            offset += 4U;
          } else {
            operand->value = (uint32_t)m68k_read_u16be(data + offset);
            offset += 2U;
          }
        }
        break;
      case M68K_ASM_EXTENSION_EA_INDEX:
        if ((operand->ea_mode == 6U) || (operand->ea_mode == 7U && operand->ea_reg == 3U)) {
          int remaining_min = minimum_remaining_extension_bytes(disasm_form_index, extension_index + 1U, operands, size_suffix);
          if (remaining_min < 0) return -1;
          if (decode_index_extension(data, size - (size_t)remaining_min, operand, &offset,
            size > offset + (size_t)remaining_min) != 0) return -1;
        }
        break;
      case M68K_ASM_EXTENSION_LABEL_DISP16_IF_ZERO:
        if ((uint8_t)operand->value == form->branch_word_signal) {
          if (form->branch_word_bytes == 2U) {
            if (offset + 2U > size) return -1;
            operand->value = m68k_sign_extend32((uint32_t)m68k_read_u16be(data + offset), 16U);
            offset += 2U;
          } else if (form->branch_word_bytes == 4U) {
            if (offset + 4U > size) return -1;
            operand->value = m68k_read_u32be(data + offset);
            offset += 4U;
          }
        } else if ((uint8_t)operand->value == form->branch_long_signal) {
          if (form->branch_long_bytes == 2U) {
            if (offset + 2U > size) return -1;
            operand->value = m68k_sign_extend32((uint32_t)m68k_read_u16be(data + offset), 16U);
            offset += 2U;
          } else if (form->branch_long_bytes == 4U) {
            if (offset + 4U > size) return -1;
            operand->value = m68k_read_u32be(data + offset);
            offset += 4U;
          }
        }
        break;
      case M68K_ASM_EXTENSION_LABEL_DISP16_ALWAYS:
        if (form->branch_word_bytes == 2U) {
          if (offset + 2U > size) return -1;
          operand->value = m68k_sign_extend32((uint32_t)m68k_read_u16be(data + offset), 16U);
          offset += 2U;
        } else if (form->branch_word_bytes == 4U) {
          if (offset + 4U > size) return -1;
          operand->value = m68k_read_u32be(data + offset);
          offset += 4U;
        }
        break;
      case M68K_ASM_EXTENSION_DISP16_ALWAYS:
        if (offset + 2U > size) return -1;
        operand->value = m68k_sign_extend32((uint32_t)m68k_read_u16be(data + offset), 16U);
        offset += 2U;
        break;
      default:
        return -1;
    }
  }
  *out_byte_count = offset;
  return 0;
}

static void init_operand(M68kAsmOperandValue *operand, uint16_t disasm_form_index, uint8_t operand_index, uint8_t kind) {
  uint8_t shape;
  memset(operand, 0, sizeof(*operand));
  shape = g_m68k_disasm_operand_shapes[disasm_form_index][operand_index];
  switch (kind) {
    case M68K_ASM_OPERAND_DN:
      operand->kind = M68K_ASM_OPERAND_DN;
      break;
    case M68K_ASM_OPERAND_DN_PAIR:
      operand->kind = M68K_ASM_OPERAND_DN_PAIR;
      break;
    case M68K_ASM_OPERAND_AN:
      operand->kind = M68K_ASM_OPERAND_AN;
      operand->reg_is_address = 1U;
      break;
    case M68K_ASM_OPERAND_BF_EA:
      operand->kind = M68K_ASM_OPERAND_BF_EA;
      break;
    case M68K_ASM_OPERAND_IND:
      operand->kind = M68K_ASM_OPERAND_EA;
      break;
    case M68K_ASM_OPERAND_RN:
      operand->kind = M68K_ASM_OPERAND_RN;
      break;
    case M68K_ASM_OPERAND_RN_PAIR:
      operand->kind = M68K_ASM_OPERAND_RN_PAIR;
      break;
    case M68K_ASM_OPERAND_EA:
    case M68K_ASM_OPERAND_ABSL:
    case M68K_ASM_OPERAND_POSTINC:
      operand->kind = M68K_ASM_OPERAND_EA;
      break;
    case M68K_ASM_OPERAND_IMM:
      operand->kind = M68K_ASM_OPERAND_IMM;
      break;
    case M68K_ASM_OPERAND_LABEL:
      operand->kind = M68K_ASM_OPERAND_LABEL;
      break;
    case M68K_ASM_OPERAND_REGLIST:
      operand->kind = M68K_ASM_OPERAND_REGLIST;
      break;
    case M68K_ASM_OPERAND_CCR:
      operand->kind = M68K_ASM_OPERAND_CCR;
      break;
    case M68K_ASM_OPERAND_CACHE_SEL:
      operand->kind = M68K_ASM_OPERAND_CACHE_SEL;
      break;
    case M68K_ASM_OPERAND_CTRL_REG:
      operand->kind = M68K_ASM_OPERAND_CTRL_REG;
      break;
    case M68K_ASM_OPERAND_SR:
      operand->kind = M68K_ASM_OPERAND_SR;
      break;
    case M68K_ASM_OPERAND_USP:
      operand->kind = M68K_ASM_OPERAND_USP;
      break;
    default:
      operand->kind = M68K_ASM_OPERAND_NONE;
      break;
  }
  if (kind == M68K_ASM_OPERAND_ABSL) {
    operand->ea_mode = 7U;
    operand->ea_reg = 1U;
  }
  if (kind == M68K_ASM_OPERAND_IND) operand->ea_mode = 2U;
  if (operand->kind == M68K_ASM_OPERAND_EA && shape == 1U) operand->ea_mode = 4U;
  if (operand->kind == M68K_ASM_OPERAND_EA && shape == 2U) operand->ea_mode = 5U;
}

static int decode_operands(uint16_t disasm_form_index, const uint16_t *field_values, char size_suffix,
    const uint8_t *data, size_t size, M68kAsmOperandValue *operands, size_t *out_byte_count) {
  const M68kAsmFormDef *form = &g_m68k_disasm_forms[disasm_form_index];
  size_t operand_index;
  size_t patch_index;
  if (field_values == NULL || data == NULL || operands == NULL || out_byte_count == NULL) return -1;
  for (operand_index = 0; operand_index < form->operand_count; ++operand_index) {
    init_operand(&operands[operand_index], disasm_form_index, (uint8_t)operand_index, form->operand_kinds[operand_index]);
  }
  for (patch_index = 0; patch_index < form->patch_count; ++patch_index) {
    const M68kAsmFieldPatch *patch = &g_m68k_disasm_patches[form->patch_start + patch_index];
    uint16_t value = field_values[patch_index];
    uint8_t width = (uint8_t)(patch->bit_hi - patch->bit_lo + 1U);
    if (patch->operand_index < 0 || (size_t)patch->operand_index >= form->operand_count) continue;
    {
      M68kAsmOperandValue *operand = &operands[patch->operand_index];
      switch (patch->value_source) {
        case M68K_ASM_VALUE_REG:
        case M68K_ASM_VALUE_REG_FIRST:
          operand->reg = (uint8_t)value;
          if (operand->kind == M68K_ASM_OPERAND_EA) operand->ea_reg = (uint8_t)value;
          break;
        case M68K_ASM_VALUE_REG_SECOND:
          operand->pair_reg = (uint8_t)value;
          break;
        case M68K_ASM_VALUE_REG_KIND:
        case M68K_ASM_VALUE_REG_KIND_FIRST:
          operand->reg_is_address = (uint8_t)(value != 0U);
          break;
        case M68K_ASM_VALUE_REG_KIND_SECOND:
          operand->pair_reg_is_address = (uint8_t)(value != 0U);
          break;
        case M68K_ASM_VALUE_BF_OFFSET:
          operand->bf_offset = (uint8_t)value;
          break;
        case M68K_ASM_VALUE_BF_OFFSET_KIND:
          operand->bf_offset_is_register = (uint8_t)(value != 0U);
          break;
        case M68K_ASM_VALUE_BF_WIDTH:
          operand->bf_width = (uint8_t)value;
          break;
        case M68K_ASM_VALUE_BF_WIDTH_KIND:
          operand->bf_width_is_register = (uint8_t)(value != 0U);
          break;
        case M68K_ASM_VALUE_EA_MODE:
          operand->ea_mode = (uint8_t)value;
          break;
        case M68K_ASM_VALUE_EA_REG:
          operand->ea_reg = (uint8_t)value;
          if (operand->kind == M68K_ASM_OPERAND_RN) operand->reg = (uint8_t)value;
          break;
        case M68K_ASM_VALUE_VALUE_HI16:
          operand->value = (operand->value & 0x0000FFFFU) | ((uint32_t)value << 16);
          break;
        case M68K_ASM_VALUE_VALUE_LO16:
          operand->value = (operand->value & 0xFFFF0000U) | (uint32_t)value;
          break;
        case M68K_ASM_VALUE_VALUE:
          if (operand->kind == M68K_ASM_OPERAND_LABEL && patch->field_kind == M68K_ASM_FIELD_DISPLACEMENT_8) {
            if ((uint8_t)value != form->branch_word_signal && (uint8_t)value != form->branch_long_signal)
              operand->value = m68k_sign_extend32((uint32_t)(value & 0xFFU), 8U);
          } else if (patch->field_kind == M68K_ASM_FIELD_DISPLACEMENT_8) {
            operand->value = m68k_sign_extend32((uint32_t)(value & 0xFFU), 8U);
          } else if (patch->field_kind == M68K_ASM_FIELD_DISPLACEMENT_16) {
            operand->value = m68k_sign_extend32((uint32_t)value, 16U);
          } else if (operand->kind == M68K_ASM_OPERAND_IMM && width == 3U &&
            g_m68k_disasm_inline_zero_means_eight[disasm_form_index] != 0U && value == 0U) {
            operand->value = 8U;
          } else {
            operand->value = value;
          }
          break;
        default:
          break;
      }
    }
  }
  if (decode_extensions(disasm_form_index, data, size, operands, size_suffix, out_byte_count) != 0) return -1;
  for (operand_index = 0; operand_index < form->operand_count; ++operand_index) {
    M68kAsmOperandValue *operand = &operands[operand_index];
    if (operand->kind == M68K_ASM_OPERAND_CTRL_REG) {
      size_t control_index;
      operand->reg = M68K_ASM_CONTROL_REGISTER_NONE;
      for (control_index = 0; control_index < form->control_register_count; ++control_index) {
        uint16_t control_id = g_m68k_disasm_form_control_register_ids[form->control_register_start + control_index];
        const M68kAsmControlRegisterDef *entry = &g_m68k_asm_control_registers[control_id];
        if (entry->value != operand->value) continue;
        operand->reg = (uint8_t)entry->id;
        break;
      }
      if (operand->reg == M68K_ASM_CONTROL_REGISTER_NONE) {
        for (control_index = 0; control_index < g_m68k_asm_control_register_count; ++control_index) {
          const M68kAsmControlRegisterDef *entry = &g_m68k_asm_control_registers[control_index];
          if (entry->value != operand->value) continue;
          operand->reg = (uint8_t)entry->id;
          break;
        }
      }
    }
  }
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && form->operand_count >= 2U &&
    operands[0].kind == M68K_ASM_OPERAND_REGLIST && ((m68k_read_u16be(data) >> 3U) & 0x7U) == 4U) {
    uint16_t mask = (uint16_t)operands[0].value;
    uint16_t reversed = 0U;
    unsigned bit;
    for (bit = 0; bit < 16U; ++bit) {
      if ((mask & (1U << bit)) == 0U) continue;
      reversed |= (uint16_t)(1U << (15U - bit));
    }
    operands[0].value = reversed;
  }
  return 0;
}

static int format_register(char *out, size_t out_size, int is_address, uint8_t reg) {
  return snprintf(out, out_size, "%c%u", is_address ? 'a' : 'd', reg) >= 0 ? 0 : -1;
}

static int format_register_pair(char *out, size_t out_size, int first_is_address, uint8_t first_reg,
    int second_is_address, uint8_t second_reg, int wrap_each) {
  if (wrap_each) {
    return snprintf(out, out_size, "(%c%u):(%c%u)", first_is_address ? 'a' : 'd', first_reg,
      second_is_address ? 'a' : 'd', second_reg) >= 0 ? 0 : -1;
  }
  return snprintf(out, out_size, "%c%u:%c%u", first_is_address ? 'a' : 'd', first_reg,
    second_is_address ? 'a' : 'd', second_reg) >= 0 ? 0 : -1;
}

static int format_control_register(uint16_t disasm_form_index, const M68kAsmOperandValue *operand, char *out,
    size_t out_size) {
  const M68kAsmFormDef *form = &g_m68k_disasm_forms[disasm_form_index];
  size_t index;
  if (operand == NULL || out == NULL || out_size == 0U) return -1;
  if (form->control_register_count != 0U) {
    for (index = 0; index < form->control_register_count; ++index) {
      const M68kAsmControlRegisterDef *entry;
      entry = &g_m68k_asm_control_registers[g_m68k_disasm_form_control_register_ids[form->control_register_start + index]];
      if (entry->value == operand->value) return snprintf(out, out_size, "%s", entry->name) >= 0 ? 0 : -1;
    }
    if (form->control_register_count == 1U) {
      const M68kAsmControlRegisterDef *entry;
      entry = &g_m68k_asm_control_registers[g_m68k_disasm_form_control_register_ids[form->control_register_start]];
      return snprintf(out, out_size, "%s", entry->name) >= 0 ? 0 : -1;
    }
    return -1;
  }
  for (index = 0; index < g_m68k_asm_control_register_count; ++index) {
    const M68kAsmControlRegisterDef *entry = &g_m68k_asm_control_registers[index];
    if (entry->value == operand->value) return snprintf(out, out_size, "%s", entry->name) >= 0 ? 0 : -1;
  }
  return -1;
}

static int format_cache_selector(const M68kAsmOperandValue *operand, char *out, size_t out_size) {
  const char *name;
  if (operand == NULL || out == NULL || out_size == 0U) return -1;
  switch (operand->value & 3U) {
    case 0: name = "nc"; break;
    case 1: name = "dc"; break;
    case 2: name = "ic"; break;
    case 3: name = "bc"; break;
    default: return -1;
  }
  return snprintf(out, out_size, "%s", name) >= 0 ? 0 : -1;
}

static int format_immediate(uint16_t disasm_form_index, const M68kAsmOperandValue *operand, char size_suffix, char *out,
    size_t out_size) {
  const M68kAsmFormDef *form = &g_m68k_disasm_forms[disasm_form_index];
  uint32_t value;
  int32_t signed_value;
  if (operand == NULL || out == NULL || out_size == 0U) return -1;
  value = operand->value;
  if (value == 0U && g_m68k_disasm_inline_zero_means_eight[disasm_form_index] != 0U) value = 8U;
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ) return snprintf(out, out_size, "#%d",
    (int32_t)m68k_sign_extend32(value, 8U)) >= 0 ? 0 : -1;
  if (strstr(form->syntax, "<displacement>") != NULL) {
    if (size_suffix == 'b') signed_value = (int32_t)m68k_sign_extend32(value, 8U);
    else if (size_suffix == 'w') signed_value = (int32_t)m68k_sign_extend32(value, 16U);
    else signed_value = (int32_t)value;
    return snprintf(out, out_size, "#%d", signed_value) >= 0 ? 0 : -1;
  }
  if (size_suffix == 'b') value &= 0xFFU;
  else if (size_suffix == 'w') value &= 0xFFFFU;
  return snprintf(out, out_size, "#%u", value) >= 0 ? 0 : -1;
}

static int format_reglist(const M68kAsmOperandValue *operands, size_t operand_count, const M68kAsmOperandValue *operand,
    char *out, size_t out_size) {
  const char *name;
  const char *const *table;
  unsigned bit;
  if (operand == NULL || out == NULL || out_size == 0U) return -1;
  (void)operands;
  (void)operand_count;
  table = g_m68k_asm_movem_mask_normal;
  out[0] = '\0';
  for (bit = 0; bit < 16U; ++bit) {
    unsigned range_end = bit;
    if ((operand->value & (1U << bit)) == 0U) continue;
    while (range_end + 1U < 16U && (operand->value & (1U << (range_end + 1U))) != 0U &&
      table[range_end][0] == table[range_end + 1U][0]) ++range_end;
    name = table[bit];
    if (out[0] != '\0' && m68k_appendf(out, out_size, "/") != 0) return -1;
    if (m68k_appendf(out, out_size, "%s", name) != 0) return -1;
    if (range_end != bit && m68k_appendf(out, out_size, "-%s", table[range_end]) != 0) return -1;
    bit = range_end;
  }
  return out[0] == '\0' ? -1 : 0;
}

static int format_index_register(const M68kAsmOperandValue *operand, char *out, size_t out_size) {
  return snprintf(out, out_size, "%c%u.%c", operand->index_is_address ? 'a' : 'd', operand->index_reg,
    operand->index_long ? 'l' : 'w') >= 0 ? 0 : -1;
}

static int format_bitfield_value(int is_register, int is_width, uint8_t value, char *out, size_t out_size) {
  unsigned display_value = value;
  if (!is_register && is_width && value == 0U) display_value = 32U;
  return is_register ? snprintf(out, out_size, "d%u", value) >= 0 ? 0 : -1 :
    snprintf(out, out_size, "%u", display_value) >= 0 ? 0 : -1;
}

static int format_signed_hex_value(int32_t value, unsigned width, char *out, size_t out_size) {
  if (value < 0) {
    uint32_t magnitude = 0U - (uint32_t)value;
    return width != 0U
      ? snprintf(out, out_size, "-$%0*x", (int)width, (unsigned)magnitude) >= 0 ? 0 : -1
      : snprintf(out, out_size, "-$%x", (unsigned)magnitude) >= 0 ? 0 : -1;
  }
  return width != 0U
    ? snprintf(out, out_size, "$%0*x", (int)width, (unsigned)value) >= 0 ? 0 : -1
    : snprintf(out, out_size, "$%x", (unsigned)value) >= 0 ? 0 : -1;
}

static int format_ea(const M68kAsmOperandValue *operand, char size_suffix, char *out, size_t out_size) {
  char index_text[32];
  char disp_text[24];
  char extra[64];
  if (operand == NULL || out == NULL || out_size == 0U) return -1;
  switch (operand->ea_mode) {
    case 0:
      return snprintf(out, out_size, "d%u", operand->ea_reg) >= 0 ? 0 : -1;
    case 1:
      return snprintf(out, out_size, "a%u", operand->ea_reg) >= 0 ? 0 : -1;
    case 2:
      return snprintf(out, out_size, "(a%u)", operand->ea_reg) >= 0 ? 0 : -1;
    case 3:
      return snprintf(out, out_size, "(a%u)+", operand->ea_reg) >= 0 ? 0 : -1;
    case 4:
      return snprintf(out, out_size, "-(a%u)", operand->ea_reg) >= 0 ? 0 : -1;
    case 5:
      if (format_signed_hex_value((int32_t)m68k_sign_extend32(operand->value, 16U), 4U, disp_text, sizeof(disp_text)) != 0) return -1;
      return snprintf(out, out_size, "%s(a%u)", disp_text, operand->ea_reg) >= 0 ? 0 : -1;
    case 6:
      if (format_index_register(operand, index_text, sizeof(index_text)) != 0) return -1;
      extra[0] = '\0';
      if (operand->full_ext_base_suppress != 0U || operand->full_ext_index_suppress != 0U || operand->full_ext_base_disp_size != 0U ||
        operand->full_ext_outer_disp_size != 0U || operand->full_ext_iis != 0U) {
        if (m68k_appendf(extra, sizeof(extra), "{full") != 0) return -1;
        if (operand->full_ext_base_suppress != 0U && m68k_appendf(extra, sizeof(extra), ",bs") != 0) return -1;
        if (operand->full_ext_index_suppress != 0U && m68k_appendf(extra, sizeof(extra), ",is") != 0) return -1;
        if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_WORD) {
          if (format_signed_hex_value((int32_t)m68k_sign_extend32(operand->full_ext_base_disp_value, 16U), 4U,
              disp_text, sizeof(disp_text)) != 0) return -1;
          if (m68k_appendf(extra, sizeof(extra), ",bdw=%s", disp_text) != 0) return -1;
        }
        if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_LONG) {
          if (format_signed_hex_value((int32_t)operand->full_ext_base_disp_value, 8U, disp_text, sizeof(disp_text)) != 0)
            return -1;
          if (m68k_appendf(extra, sizeof(extra), ",bdl=%s", disp_text) != 0) return -1;
        }
        if (operand->full_ext_outer_disp_size == M68K_ASM_FULL_EXT_BD_WORD) {
          if (format_signed_hex_value((int32_t)m68k_sign_extend32(operand->full_ext_outer_disp_value, 16U), 4U,
              disp_text, sizeof(disp_text)) != 0) return -1;
          if (m68k_appendf(extra, sizeof(extra), ",odw=%s", disp_text) != 0) return -1;
        }
        if (operand->full_ext_outer_disp_size == M68K_ASM_FULL_EXT_BD_LONG) {
          if (format_signed_hex_value((int32_t)operand->full_ext_outer_disp_value, 8U, disp_text, sizeof(disp_text)) != 0)
            return -1;
          if (m68k_appendf(extra, sizeof(extra), ",odl=%s", disp_text) != 0) return -1;
        }
        if (operand->full_ext_iis != 0U && m68k_appendf(extra, sizeof(extra), ",iis=%u", operand->full_ext_iis) != 0) return -1;
        if (m68k_appendf(extra, sizeof(extra), "}") != 0) return -1;
        return snprintf(out, out_size, "$%x(a%u,%s)%s", 0u,
          operand->ea_reg, index_text, extra) >= 0 ? 0 : -1;
      }
      if (format_signed_hex_value((int32_t)m68k_sign_extend32(operand->value, 8U), 0U, disp_text, sizeof(disp_text)) != 0) return -1;
      return snprintf(out, out_size, "%s(a%u,%s)", disp_text, operand->ea_reg, index_text) >= 0 ? 0 : -1;
    case 7:
      switch (operand->ea_reg) {
        case 0:
          return snprintf(out, out_size, "$%04x.w", (unsigned)(operand->value & 0xFFFFU)) >= 0 ? 0 : -1;
        case 1:
          return snprintf(out, out_size, "$%08x.l", (unsigned)operand->value) >= 0 ? 0 : -1;
        case 2:
          return snprintf(out, out_size, "target(pc)") >= 0 ? 0 : -1;
        case 3:
          if (format_index_register(operand, index_text, sizeof(index_text)) != 0) return -1;
          return snprintf(out, out_size, "target(pc,%s)", index_text) >= 0 ? 0 : -1;
        case 4:
          if (size_suffix == 'b')
            return snprintf(out, out_size, "#%u", (unsigned)(operand->value & 0xFFU)) >= 0 ? 0 : -1;
          if (size_suffix == 'w')
            return snprintf(out, out_size, "#%u", (unsigned)(operand->value & 0xFFFFU)) >= 0 ? 0 : -1;
          return snprintf(out, out_size, "#%u", (unsigned)operand->value) >= 0 ? 0 : -1;
        default:
          return -1;
      }
    default:
      return -1;
  }
}

static int format_bf_ea(const M68kAsmOperandValue *operand, char size_suffix, char *out, size_t out_size) {
  char ea_text[128];
  char offset_text[16];
  char width_text[16];
  if (operand == NULL || out == NULL || out_size == 0U) return -1;
  if (format_ea(operand, size_suffix, ea_text, sizeof(ea_text)) != 0) return -1;
  if (format_bitfield_value(operand->bf_offset_is_register != 0U,
    0, operand->bf_offset, offset_text, sizeof(offset_text)) != 0) return -1;
  if (format_bitfield_value(operand->bf_width_is_register != 0U,
    1, operand->bf_width, width_text, sizeof(width_text)) != 0) return -1;
  return snprintf(out, out_size, "%s{%s:%s}", ea_text, offset_text, width_text) >= 0 ? 0 : -1;
}

static int format_operand(uint16_t disasm_form_index, const M68kAsmOperandValue *operands, size_t operand_count,
    size_t operand_index, char size_suffix, char *out, size_t out_size) {
  const M68kAsmFormDef *form = &g_m68k_disasm_forms[disasm_form_index];
  const M68kAsmOperandValue *operand;
  if (operands == NULL || out == NULL || operand_index >= operand_count) return -1;
  operand = &operands[operand_index];
  switch (form->operand_kinds[operand_index]) {
    case M68K_ASM_OPERAND_DN:
      return format_register(out, out_size, 0, operand->reg);
    case M68K_ASM_OPERAND_DN_PAIR:
      return format_register_pair(out, out_size, 0, operand->reg, 0, operand->pair_reg, 0);
    case M68K_ASM_OPERAND_AN:
      return format_register(out, out_size, 1, operand->reg);
    case M68K_ASM_OPERAND_RN:
      return format_register(out, out_size, operand->reg_is_address, operand->reg);
    case M68K_ASM_OPERAND_RN_PAIR:
      return format_register_pair(out, out_size, operand->reg_is_address, operand->reg,
        operand->pair_reg_is_address, operand->pair_reg, 1);
    case M68K_ASM_OPERAND_POSTINC:
      return snprintf(out, out_size, "(a%u)+", operand->reg) >= 0 ? 0 : -1;
    case M68K_ASM_OPERAND_IND:
    case M68K_ASM_OPERAND_ABSL:
    case M68K_ASM_OPERAND_EA:
      return format_ea(operand, size_suffix, out, out_size);
    case M68K_ASM_OPERAND_BF_EA:
      return format_bf_ea(operand, size_suffix, out, out_size);
    case M68K_ASM_OPERAND_IMM:
      return format_immediate(disasm_form_index, operand, size_suffix, out, out_size);
    case M68K_ASM_OPERAND_LABEL:
      return snprintf(out, out_size, "target") >= 0 ? 0 : -1;
    case M68K_ASM_OPERAND_REGLIST:
      return format_reglist(operands, operand_count, operand, out, out_size);
    case M68K_ASM_OPERAND_CCR:
      return snprintf(out, out_size, "ccr") >= 0 ? 0 : -1;
    case M68K_ASM_OPERAND_CACHE_SEL:
      return format_cache_selector(operand, out, out_size);
    case M68K_ASM_OPERAND_CTRL_REG:
      return format_control_register(disasm_form_index, operand, out, out_size);
    case M68K_ASM_OPERAND_SR:
      return snprintf(out, out_size, "sr") >= 0 ? 0 : -1;
    case M68K_ASM_OPERAND_USP:
      return snprintf(out, out_size, "usp") >= 0 ? 0 : -1;
    default:
      return -1;
  }
}

static int render_instruction(uint16_t disasm_form_index, const M68kAsmOperandValue *operands, size_t operand_count,
    char size_suffix, char *out, size_t out_size) {
  const M68kAsmFormDef *form = &g_m68k_disasm_forms[disasm_form_index];
  char mnemonic[32];
  char operand_text[4][128];
  char display_suffix;
  uint8_t effective_mask;
  size_t operand_index;
  if (operands == NULL || out == NULL || out_size == 0U) return -1;
  if (m68k_lower_copy(mnemonic, sizeof(mnemonic), form->mnemonic) != 0) return -1;
  out[0] = '\0';
  effective_mask = m68k_asm_form_effective_size_mask_for_operands(form, operands, operand_count);
  display_suffix = choose_size_suffix(form, operands, operand_count, size_suffix);
  if (m68k_appendf(out, out_size, "%s", mnemonic) != 0) return -1;
  if (display_suffix != '\0' &&
    (syntax_has_explicit_size(form->syntax) || size_variant_count(effective_mask) > 1U || display_suffix != size_suffix ||
      disasm_requires_explicit_size_suffix(form, display_suffix))) {
    if (m68k_appendf(out, out_size, ".%c", display_suffix) != 0) return -1;
  }
  if (operand_count == 0U) return 0;
  if (m68k_appendf(out, out_size, " ") != 0) return -1;
  for (operand_index = 0; operand_index < operand_count; ++operand_index) {
    if (format_operand(disasm_form_index, operands, operand_count, operand_index, size_suffix, operand_text[operand_index],
      sizeof(operand_text[operand_index])) != 0) return -1;
    if (operand_index != 0U && m68k_appendf(out, out_size, ",") != 0) return -1;
    if (m68k_appendf(out, out_size, "%s", operand_text[operand_index]) != 0) return -1;
  }
  return 0;
}

static unsigned disasm_form_specificity(uint16_t disasm_form_index) {
  const M68kAsmFormDef *form = &g_m68k_disasm_forms[disasm_form_index];
  unsigned score;
  uint8_t word_index;
  score = m68k_popcount16(form->opword_mask);
  for (word_index = 0; word_index < form->bound_word_count &&
      word_index < (sizeof(form->bound_word_masks) / sizeof(form->bound_word_masks[0])); ++word_index) {
    score += m68k_popcount16(form->bound_word_masks[word_index]);
  }
  return score;
}

static M68kDisasmResult m68k_disassemble_one_impl(const uint8_t *data, size_t size, uint8_t target_cpu,
    M68kDiagSink diagnostics) {
  uint16_t bucket_index;
  size_t candidate_index;
  M68kDisasmResult best_result;
  unsigned best_specificity = 0U;
  int have_match = 0;
  memset(&best_result, 0, sizeof(best_result));
  best_result.asm_form_index = M68K_ASM_FORM_NONE;
  best_result.disasm_form_index = M68K_DISASM_FORM_NONE;
  if (data == NULL || size < 2U) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_DECODE_FAILED, "empty input");
    best_result.target_cpu = target_cpu;
    return best_result;
  }
  bucket_index = (uint16_t)(m68k_read_u16be(data) >> 4);
  for (candidate_index = 0; candidate_index < g_m68k_disasm_buckets[bucket_index].count; ++candidate_index) {
    uint16_t disasm_form_index = g_m68k_disasm_bucket_candidates[g_m68k_disasm_buckets[bucket_index].start + candidate_index];
    const M68kAsmFormDef *form = &g_m68k_disasm_forms[disasm_form_index];
    M68kAsmOperandValue operands[4];
    char rendered_text[128];
    uint16_t field_values[32];
    size_t byte_count = 0U;
    char size_suffix;
    unsigned specificity;
    if (target_cpu != M68K_ASM_CPU_ANY && (form->cpu_mask & (1u << target_cpu)) == 0u) continue;
    if (!m68k_disasm_match_form(disasm_form_index, data, size)) continue;
    if (form->patch_count > (sizeof(field_values) / sizeof(field_values[0]))) continue;
    if (extract_patch_values(disasm_form_index, data, field_values) != 0) continue;
    if (validate_patch_values(disasm_form_index, field_values) != 0) continue;
    size_suffix = resolve_size_suffix(form, field_values);
    if (decode_operands(disasm_form_index, field_values, size_suffix, data, size, operands, &byte_count) != 0) continue;
    if (render_instruction(disasm_form_index, operands, form->operand_count, size_suffix, rendered_text,
        sizeof(rendered_text)) != 0) continue;
    specificity = disasm_form_specificity(disasm_form_index);
    if (!have_match || specificity > best_specificity) {
      best_result = make_result(byte_count, rendered_text, disasm_form_index, operands, size_suffix, target_cpu);
      have_match = 1;
      best_specificity = specificity;
    }
  }
  if (have_match) return best_result;
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_DECODE_FAILED, "unknown instruction bytes");
  best_result.target_cpu = target_cpu;
  return best_result;
}

M68kDisasmResult m68k_disassemble_one(const uint8_t *data, size_t size, M68kDiagSink diagnostics) {
  return m68k_disassemble_one_impl(data, size, M68K_ASM_CPU_68000, diagnostics);
}

M68kDisasmResult m68k_disassemble_one_for_cpu(const uint8_t *data, size_t size, uint8_t target_cpu,
    M68kDiagSink diagnostics) {
  return m68k_disassemble_one_impl(data, size, target_cpu, diagnostics);
}

