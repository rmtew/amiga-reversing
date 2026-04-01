/* Static disassembler runtime over generated KB-derived tables. */
#include "m68k_disassembler.h"
#include "m68k_asm_tables.h"
#include "m68k_parse_util.h"

#include <stdio.h>
#include <string.h>

typedef struct {
  uint16_t start;
  uint16_t count;
} M68kDisasmBucket;

#include "m68k_disassembler_tables.inc"

static uint16_t read_u16be(const uint8_t *data) {
  return (uint16_t)(((uint16_t)data[0] << 8) | (uint16_t)data[1]);
}

static uint32_t read_u32be(const uint8_t *data) {
  return ((uint32_t)data[0] << 24) | ((uint32_t)data[1] << 16) | ((uint32_t)data[2] << 8) | (uint32_t)data[3];
}

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

static char choose_size_suffix(const M68kAsmFormDef *form, const M68kAsmOperandValue *operands, size_t operand_count,
    char explicit_suffix) {
  size_t patch_index;
  uint8_t mask;
  if (explicit_suffix != '\0') return explicit_suffix;
  if (form == NULL) return '\0';
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
  if (form == NULL) return NULL;
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
  if (form == NULL || field_values == NULL) return '\0';
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

static int m68k_disasm_match_form(const M68kAsmFormDef *form, const uint8_t *data, size_t size) {
  size_t word_index;
  uint16_t opword;
  if (form == NULL || data == NULL || size < 2U) return 0;
  opword = read_u16be(data);
  if ((opword & form->opword_mask) != form->opword_base) return 0;
  if (size < 2U + ((size_t)form->bound_word_count * 2U)) return 0;
  for (word_index = 0; word_index < form->bound_word_count; ++word_index) {
    uint16_t bound_word = read_u16be(data + 2U + (word_index * 2U));
    if ((bound_word & form->bound_word_masks[word_index]) != form->bound_word_bases[word_index]) return 0;
  }
  return 1;
}

static int set_result(M68kDisasmResult *out, int ok, size_t byte_count, const char *text, const char *error,
    const M68kAsmFormDef *form, uint16_t form_index, const M68kAsmOperandValue *operands, char size_suffix,
    uint8_t target_cpu) {
  if (out == NULL) return -1;
  memset(out, 0, sizeof(*out));
  out->ok = ok;
  out->byte_count = byte_count;
  out->form_index = form != NULL ? form->form_index : form_index;
  out->target_cpu = target_cpu;
  if (form != NULL && form->mnemonic != NULL) snprintf(out->mnemonic, sizeof(out->mnemonic), "%s", form->mnemonic);
  out->size_suffix = size_suffix;
  if (form != NULL) {
    size_t operand_index;
    out->mnemonic_id = form->mnemonic_id;
    out->operand_count = form->operand_count;
    for (operand_index = 0; operand_index < form->operand_count && operand_index < 4U; ++operand_index) {
      out->operand_kinds[operand_index] = form->operand_kinds[operand_index];
      if (operands != NULL) out->operands[operand_index] = operands[operand_index];
    }
  }
  if (text != NULL) snprintf(out->text, sizeof(out->text), "%s", text);
  if (error != NULL) snprintf(out->error, sizeof(out->error), "%s", error);
  return ok ? 0 : -1;
}

static int extract_patch_values(const M68kAsmFormDef *form, const uint8_t *data, uint16_t *field_values) {
  size_t patch_index;
  if (form == NULL || data == NULL || field_values == NULL) return -1;
  for (patch_index = 0; patch_index < form->patch_count; ++patch_index) {
    const M68kAsmFieldPatch *patch = &g_m68k_disasm_patches[form->patch_start + patch_index];
    uint16_t word;
    if (patch->word_index == 0U) {
      word = read_u16be(data);
    } else if ((size_t)patch->word_index <= form->bound_word_count) {
      word = read_u16be(data + ((size_t)patch->word_index * 2U));
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

static int validate_patch_values(const M68kAsmFormDef *form, const uint16_t *field_values) {
  size_t patch_index;
  if (form == NULL || field_values == NULL) return -1;
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

static int minimum_remaining_extension_bytes(const M68kAsmFormDef *form, size_t start_extension_index,
    const M68kAsmOperandValue *operands, char size_suffix) {
  size_t extension_index;
  int total = 0;
  if (form == NULL || operands == NULL) return -1;
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
  ext = read_u16be(data + offset);
  offset += 2U;
  operand->index_is_address = (uint8_t)((ext >> M68K_ASM_BRIEF_EXT_DA_BIT_LO) & 0x1U);
  operand->index_reg = (uint8_t)((ext >> M68K_ASM_BRIEF_EXT_REGISTER_BIT_LO) & 0x7U);
  operand->index_long = (uint8_t)((ext >> M68K_ASM_BRIEF_EXT_WL_BIT_LO) & 0x1U);
  operand->scale = (uint8_t)((ext >> M68K_ASM_BRIEF_EXT_SCALE_BIT_LO) & 0x3U);
  operand->value = (uint32_t)(ext & 0xFFU);
  if (allow_full_extension && ((ext >> M68K_ASM_FULL_EXT_FORMAT_BIT_LO) & 0x1U) != 0U) {
    size_t remaining;
    operand->value = 0U;
    operand->full_ext_base_suppress = (uint8_t)((ext >> M68K_ASM_FULL_EXT_BS_BIT_LO) & 0x1U);
    operand->full_ext_index_suppress = (uint8_t)((ext >> M68K_ASM_FULL_EXT_IS_BIT_LO) & 0x1U);
    operand->full_ext_base_disp_size = (uint8_t)((ext >> M68K_ASM_FULL_EXT_BD_SIZE_BIT_LO) & 0x3U);
    operand->full_ext_iis = (uint8_t)((ext >> M68K_ASM_FULL_EXT_IIS_BIT_LO) & 0x7U);
    if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_WORD) {
      if (offset + 2U > size) return -1;
      operand->full_ext_base_disp_value = (uint32_t)read_u16be(data + offset);
      offset += 2U;
    } else if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_LONG) {
      if (offset + 4U > size) return -1;
      operand->full_ext_base_disp_value = read_u32be(data + offset);
      offset += 4U;
    }
    remaining = size - offset;
    if (remaining == 2U) {
      operand->full_ext_outer_disp_size = M68K_ASM_FULL_EXT_BD_WORD;
      operand->full_ext_outer_disp_value = (uint32_t)read_u16be(data + offset);
      offset += 2U;
    } else if (remaining == 4U) {
      operand->full_ext_outer_disp_size = M68K_ASM_FULL_EXT_BD_LONG;
      operand->full_ext_outer_disp_value = read_u32be(data + offset);
      offset += 4U;
    }
  }
  *io_offset = offset;
  return 0;
}

static int decode_extensions(const M68kAsmFormDef *form, const uint8_t *data, size_t size,
    M68kAsmOperandValue *operands, char size_suffix, size_t *out_byte_count) {
  size_t offset;
  size_t extension_index;
  if (form == NULL || data == NULL || operands == NULL || out_byte_count == NULL) return -1;
  offset = 2U + ((size_t)form->bound_word_count * 2U);
  for (extension_index = 0; extension_index < form->extension_count; ++extension_index) {
    const M68kAsmExtensionDef *extension = &g_m68k_disasm_extensions[form->extension_start + extension_index];
    M68kAsmOperandValue *operand = &operands[extension->operand_index];
    switch (extension->kind) {
      case M68K_ASM_EXTENSION_EA_SINGLE_WORD:
        if ((operand->ea_mode == 5U) || (operand->ea_mode == 7U && operand->ea_reg == 0U) ||
          (operand->ea_mode == 7U && operand->ea_reg == 2U)) {
          if (offset + 2U > size) return -1;
          operand->value = (uint32_t)read_u16be(data + offset);
          offset += 2U;
        }
        break;
      case M68K_ASM_EXTENSION_EA_LONG_ADDRESS:
        if (operand->ea_mode == 7U && operand->ea_reg == 1U) {
          if (offset + 4U > size) return -1;
          operand->value = read_u32be(data + offset);
          offset += 4U;
        }
        break;
      case M68K_ASM_EXTENSION_EA_IMMEDIATE:
        if (operand->kind == M68K_ASM_OPERAND_IMM ||
          (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 7U && operand->ea_reg == 4U)) {
          if (offset + 2U > size) return -1;
          if (size_suffix == 'l') {
            if (offset + 4U > size) return -1;
            operand->value = read_u32be(data + offset);
            offset += 4U;
          } else {
            operand->value = (uint32_t)read_u16be(data + offset);
            offset += 2U;
          }
        }
        break;
      case M68K_ASM_EXTENSION_EA_INDEX:
        if ((operand->ea_mode == 6U) || (operand->ea_mode == 7U && operand->ea_reg == 3U)) {
          int remaining_min = minimum_remaining_extension_bytes(form, extension_index + 1U, operands, size_suffix);
          if (remaining_min < 0) return -1;
          if (decode_index_extension(data, size - (size_t)remaining_min, operand, &offset,
            size > offset + (size_t)remaining_min) != 0) return -1;
        }
        break;
      case M68K_ASM_EXTENSION_LABEL_DISP16_IF_ZERO:
        if ((uint8_t)operand->value == form->branch_word_signal) {
          if (form->branch_word_bytes == 2U) {
            if (offset + 2U > size) return -1;
            operand->value = m68k_sign_extend32((uint32_t)read_u16be(data + offset), 16U);
            offset += 2U;
          } else if (form->branch_word_bytes == 4U) {
            if (offset + 4U > size) return -1;
            operand->value = read_u32be(data + offset);
            offset += 4U;
          }
        } else if ((uint8_t)operand->value == form->branch_long_signal) {
          if (form->branch_long_bytes == 2U) {
            if (offset + 2U > size) return -1;
            operand->value = m68k_sign_extend32((uint32_t)read_u16be(data + offset), 16U);
            offset += 2U;
          } else if (form->branch_long_bytes == 4U) {
            if (offset + 4U > size) return -1;
            operand->value = read_u32be(data + offset);
            offset += 4U;
          }
        }
        break;
      case M68K_ASM_EXTENSION_LABEL_DISP16_ALWAYS:
        if (form->branch_word_bytes == 2U) {
          if (offset + 2U > size) return -1;
          operand->value = m68k_sign_extend32((uint32_t)read_u16be(data + offset), 16U);
          offset += 2U;
        } else if (form->branch_word_bytes == 4U) {
          if (offset + 4U > size) return -1;
          operand->value = read_u32be(data + offset);
          offset += 4U;
        }
        break;
      case M68K_ASM_EXTENSION_DISP16_ALWAYS:
        if (offset + 2U > size) return -1;
        operand->value = m68k_sign_extend32((uint32_t)read_u16be(data + offset), 16U);
        offset += 2U;
        break;
      default:
        return -1;
    }
  }
  *out_byte_count = offset;
  return 0;
}

static void init_operand(M68kAsmOperandValue *operand, uint16_t form_index, uint8_t operand_index, uint8_t kind) {
  uint8_t shape;
  memset(operand, 0, sizeof(*operand));
  shape = g_m68k_disasm_operand_shapes[form_index][operand_index];
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

static int decode_operands(const M68kAsmFormDef *form, const uint16_t *field_values, char size_suffix,
    const uint8_t *data, size_t size, M68kAsmOperandValue *operands, size_t *out_byte_count) {
  size_t operand_index;
  size_t patch_index;
  if (form == NULL || field_values == NULL || data == NULL || operands == NULL || out_byte_count == NULL) return -1;
  for (operand_index = 0; operand_index < form->operand_count; ++operand_index) {
    init_operand(&operands[operand_index], (uint16_t)(form - g_m68k_disasm_forms), (uint8_t)operand_index,
      form->operand_kinds[operand_index]);
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
            if ((uint8_t)value != form->branch_word_signal &&
              (uint8_t)value != form->branch_long_signal) operand->value = m68k_sign_extend32((uint32_t)(value & 0xFFU), 8U);
          } else if (operand->kind == M68K_ASM_OPERAND_LABEL && patch->field_kind == M68K_ASM_FIELD_DISPLACEMENT_16) {
            operand->value = m68k_sign_extend32((uint32_t)value, 16U);
          } else if (operand->kind == M68K_ASM_OPERAND_IMM && width == 3U &&
            g_m68k_disasm_inline_zero_means_eight[form - g_m68k_disasm_forms] != 0U && value == 0U) {
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
  if (decode_extensions(form, data, size, operands, size_suffix, out_byte_count) != 0) return -1;
  if (strcmp(form->mnemonic, "movem") == 0 && form->operand_count >= 2U &&
    operands[0].kind == M68K_ASM_OPERAND_REGLIST && ((read_u16be(data) >> 3U) & 0x7U) == 4U) {
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

static int format_control_register(const M68kAsmFormDef *form, const M68kAsmOperandValue *operand, char *out,
    size_t out_size) {
  size_t index;
  if (form == NULL || operand == NULL || out == NULL || out_size == 0U) return -1;
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

static int format_immediate(const M68kAsmFormDef *form, const M68kAsmOperandValue *operand, char size_suffix, char *out,
    size_t out_size) {
  uint32_t value;
  if (form == NULL || operand == NULL || out == NULL || out_size == 0U) return -1;
  value = operand->value;
  if (value == 0U && g_m68k_disasm_inline_zero_means_eight[form - g_m68k_disasm_forms] != 0U) value = 8U;
  if (strcmp(form->mnemonic, "moveq") == 0) return snprintf(out, out_size, "#%d",
    (int32_t)m68k_sign_extend32(value, 8U)) >= 0 ? 0 : -1;
  if (strstr(form->syntax, "<displacement>") != NULL) return snprintf(out, out_size, "#%d",
    (int32_t)m68k_sign_extend32(value, 16U)) >= 0 ? 0 : -1;
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

static int format_ea(const M68kAsmOperandValue *operand, char *out, size_t out_size) {
  char index_text[32];
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
      return snprintf(out, out_size, "$%04x(a%u)", (unsigned)(operand->value & 0xFFFFU), operand->ea_reg) >= 0 ? 0 : -1;
    case 6:
      if (format_index_register(operand, index_text, sizeof(index_text)) != 0) return -1;
      extra[0] = '\0';
      if (operand->full_ext_base_suppress != 0U || operand->full_ext_index_suppress != 0U || operand->full_ext_base_disp_size != 0U ||
        operand->full_ext_outer_disp_size != 0U || operand->full_ext_iis != 0U) {
        if (m68k_appendf(extra, sizeof(extra), "{full") != 0) return -1;
        if (operand->full_ext_base_suppress != 0U && m68k_appendf(extra, sizeof(extra), ",bs") != 0) return -1;
        if (operand->full_ext_index_suppress != 0U && m68k_appendf(extra, sizeof(extra), ",is") != 0) return -1;
        if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_WORD &&
          m68k_appendf(extra, sizeof(extra), ",bdw=$%04x",
          (unsigned)(operand->full_ext_base_disp_value & 0xFFFFU)) != 0) return -1;
        if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_LONG &&
          m68k_appendf(extra, sizeof(extra), ",bdl=$%08x", (unsigned)operand->full_ext_base_disp_value) != 0) return -1;
        if (operand->full_ext_outer_disp_size == M68K_ASM_FULL_EXT_BD_WORD &&
          m68k_appendf(extra, sizeof(extra), ",odw=$%04x",
          (unsigned)(operand->full_ext_outer_disp_value & 0xFFFFU)) != 0) return -1;
        if (operand->full_ext_outer_disp_size == M68K_ASM_FULL_EXT_BD_LONG &&
          m68k_appendf(extra, sizeof(extra), ",odl=$%08x", (unsigned)operand->full_ext_outer_disp_value) != 0) return -1;
        if (operand->full_ext_iis != 0U && m68k_appendf(extra, sizeof(extra), ",iis=%u", operand->full_ext_iis) != 0) return -1;
        if (m68k_appendf(extra, sizeof(extra), "}") != 0) return -1;
        return snprintf(out, out_size, "$%x(a%u,%s)%s", 0u,
          operand->ea_reg, index_text, extra) >= 0 ? 0 : -1;
      }
      return snprintf(out, out_size, "$%x(a%u,%s)", (unsigned)(operand->value & 0xFFU), operand->ea_reg, index_text) >= 0 ? 0 : -1;
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
          return snprintf(out, out_size, "#%u", (unsigned)operand->value) >= 0 ? 0 : -1;
        default:
          return -1;
      }
    default:
      return -1;
  }
}

static int format_bf_ea(const M68kAsmOperandValue *operand, char *out, size_t out_size) {
  char ea_text[128];
  char offset_text[16];
  char width_text[16];
  if (operand == NULL || out == NULL || out_size == 0U) return -1;
  if (format_ea(operand, ea_text, sizeof(ea_text)) != 0) return -1;
  if (format_bitfield_value(operand->bf_offset_is_register != 0U,
    0, operand->bf_offset, offset_text, sizeof(offset_text)) != 0) return -1;
  if (format_bitfield_value(operand->bf_width_is_register != 0U,
    1, operand->bf_width, width_text, sizeof(width_text)) != 0) return -1;
  return snprintf(out, out_size, "%s{%s:%s}", ea_text, offset_text, width_text) >= 0 ? 0 : -1;
}

static int format_operand(const M68kAsmFormDef *form, const M68kAsmOperandValue *operands, size_t operand_count,
    size_t operand_index, char size_suffix, char *out, size_t out_size) {
  const M68kAsmOperandValue *operand;
  if (form == NULL || operands == NULL || out == NULL || operand_index >= operand_count) return -1;
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
      return format_ea(operand, out, out_size);
    case M68K_ASM_OPERAND_BF_EA:
      return format_bf_ea(operand, out, out_size);
    case M68K_ASM_OPERAND_IMM:
      return format_immediate(form, operand, size_suffix, out, out_size);
    case M68K_ASM_OPERAND_LABEL:
      return snprintf(out, out_size, "target") >= 0 ? 0 : -1;
    case M68K_ASM_OPERAND_REGLIST:
      return format_reglist(operands, operand_count, operand, out, out_size);
    case M68K_ASM_OPERAND_CCR:
      return snprintf(out, out_size, "ccr") >= 0 ? 0 : -1;
    case M68K_ASM_OPERAND_CACHE_SEL:
      return format_cache_selector(operand, out, out_size);
    case M68K_ASM_OPERAND_CTRL_REG:
      return format_control_register(form, operand, out, out_size);
    case M68K_ASM_OPERAND_SR:
      return snprintf(out, out_size, "sr") >= 0 ? 0 : -1;
    case M68K_ASM_OPERAND_USP:
      return snprintf(out, out_size, "usp") >= 0 ? 0 : -1;
    default:
      return -1;
  }
}

static int render_instruction(const M68kAsmFormDef *form, const M68kAsmOperandValue *operands, size_t operand_count,
    char size_suffix, char *out, size_t out_size) {
  char mnemonic[32];
  char operand_text[4][128];
  char display_suffix;
  uint8_t effective_mask;
  size_t operand_index;
  if (form == NULL || operands == NULL || out == NULL || out_size == 0U) return -1;
  if (m68k_lower_copy(mnemonic, sizeof(mnemonic), form->mnemonic) != 0) return -1;
  out[0] = '\0';
  effective_mask = m68k_asm_form_effective_size_mask_for_operands(form, operands, operand_count);
  display_suffix = choose_size_suffix(form, operands, operand_count, size_suffix);
  if (m68k_appendf(out, out_size, "%s", mnemonic) != 0) return -1;
  if (display_suffix != '\0' &&
    (syntax_has_explicit_size(form->syntax) || size_variant_count(effective_mask) > 1U || display_suffix != size_suffix)) {
    if (m68k_appendf(out, out_size, ".%c", display_suffix) != 0) return -1;
  }
  if (operand_count == 0U) return 0;
  if (m68k_appendf(out, out_size, " ") != 0) return -1;
  for (operand_index = 0; operand_index < operand_count; ++operand_index) {
    if (format_operand(form, operands, operand_count, operand_index, size_suffix, operand_text[operand_index],
      sizeof(operand_text[operand_index])) != 0) return -1;
    if (operand_index != 0U && m68k_appendf(out, out_size, ",") != 0) return -1;
    if (m68k_appendf(out, out_size, "%s", operand_text[operand_index]) != 0) return -1;
  }
  return 0;
}

static int m68k_disassemble_one_impl(const uint8_t *data, size_t size, uint8_t target_cpu, M68kDisasmResult *out) {
  uint16_t bucket_index;
  size_t candidate_index;
  if (data == NULL || size == 0U) return set_result(out, 0, 0U, NULL, "empty input", NULL, 0U, NULL, '\0', target_cpu);
  if (size < 2U) return set_result(out, 0, 0U, NULL, "empty input", NULL, 0U, NULL, '\0', target_cpu);
  bucket_index = (uint16_t)(read_u16be(data) >> 4);
  for (candidate_index = 0; candidate_index < g_m68k_disasm_buckets[bucket_index].count; ++candidate_index) {
    uint16_t form_index = g_m68k_disasm_bucket_candidates[g_m68k_disasm_buckets[bucket_index].start + candidate_index];
    const M68kAsmFormDef *form = &g_m68k_disasm_forms[form_index];
    M68kAsmOperandValue operands[4];
    char rendered_text[128];
    uint16_t field_values[32];
    size_t byte_count = 0U;
    char size_suffix;
    if (target_cpu != M68K_ASM_CPU_ANY && (form->cpu_mask & (1u << target_cpu)) == 0u) continue;
    if (!m68k_disasm_match_form(form, data, size)) continue;
    if (form->patch_count > (sizeof(field_values) / sizeof(field_values[0]))) continue;
    if (extract_patch_values(form, data, field_values) != 0) continue;
    if (validate_patch_values(form, field_values) != 0) continue;
    size_suffix = resolve_size_suffix(form, field_values);
    if (decode_operands(form, field_values, size_suffix, data, size, operands, &byte_count) != 0) continue;
    if (render_instruction(form, operands, form->operand_count, size_suffix, rendered_text, sizeof(rendered_text)) != 0) continue;
    return set_result(out, 1, byte_count, rendered_text, NULL, form, form_index, operands, size_suffix, target_cpu);
  }
  return set_result(out, 0, 0U, NULL, "unknown instruction bytes", NULL, 0U, NULL, '\0', target_cpu);
}

int m68k_disassemble_one(const uint8_t *data, size_t size, M68kDisasmResult *out) {
  return m68k_disassemble_one_impl(data, size, M68K_ASM_CPU_68000, out);
}

int m68k_disassemble_one_for_cpu(const uint8_t *data, size_t size, uint8_t target_cpu, M68kDisasmResult *out) {
  return m68k_disassemble_one_impl(data, size, target_cpu, out);
}

