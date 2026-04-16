/* Static assembler runtime over generated KB-derived tables. */
#include "m68k_assembler.h"

#include <string.h>

static unsigned char m68k_ascii_tolower_local(unsigned char ch) {
  if (ch >= 'A' && ch <= 'Z') return (unsigned char)(ch - 'A' + 'a');
  return ch;
}

static int m68k_ascii_icompare_local(const char *left, const char *right) {
  size_t index = 0U;
  unsigned char left_ch;
  unsigned char right_ch;
  if (left == NULL) left = "";
  if (right == NULL) right = "";
  for (;;) {
    left_ch = m68k_ascii_tolower_local((unsigned char)left[index]);
    right_ch = m68k_ascii_tolower_local((unsigned char)right[index]);
    if (left_ch != right_ch || left_ch == '\0' || right_ch == '\0') break;
    ++index;
  }
  return (int)left_ch - (int)right_ch;
}

static size_t m68k_asm_form_size_bytes(uint16_t asm_form_index, const uint16_t *field_values,
    size_t field_value_count) {
  const M68kAsmFormDef *form = &g_m68k_asm_forms[asm_form_index];
  size_t patch_index;
  char size_suffix = '\0';
  if (field_value_count != form->patch_count) return 0;
  for (patch_index = 0; patch_index < form->patch_count; ++patch_index) {
    const M68kAsmFieldPatch *patch = &g_m68k_asm_patches[form->patch_start + patch_index];
    if (patch->field_kind != M68K_ASM_FIELD_SIZE && patch->field_kind != M68K_ASM_FIELD_OPMODE) continue;
    if (field_values[patch_index] == form->size_value_b || field_values[patch_index] == form->opmode_value_b) {
      size_suffix = 'b';
      break;
    }
    if (field_values[patch_index] == form->size_value_w || field_values[patch_index] == form->opmode_value_w) {
      size_suffix = 'w';
      break;
    }
    if (field_values[patch_index] == form->size_value_l || field_values[patch_index] == form->opmode_value_l) {
      size_suffix = 'l';
      break;
    }
  }
  if (size_suffix == 'b') return 1;
  if (size_suffix == 'w') return 2;
  if (size_suffix == 'l') return 4;
  {
    uint8_t mask = m68k_asm_form_effective_size_mask(form);
    if (mask == M68K_ASM_SIZE_B) return 1;
    if (mask == M68K_ASM_SIZE_W) return 2;
    if (mask == M68K_ASM_SIZE_L) return 4;
    return 0;
  }
}

static int m68k_asm_operand_uses_full_extension(const M68kAsmOperandValue *operand) {
  if (operand == NULL || operand->kind != M68K_ASM_OPERAND_EA) return 0;
  return operand->full_ext_base_suppress != 0 || operand->full_ext_index_suppress != 0 ||
    operand->full_ext_base_disp_size != 0 || operand->full_ext_outer_disp_size != 0 || operand->full_ext_iis != 0;
}

static int m68k_asm_operand_supports_cpu(const M68kAsmOperandValue *operand, uint8_t target_cpu) {
  if (target_cpu == M68K_ASM_CPU_ANY) return 1;
  if (!m68k_asm_operand_uses_full_extension(operand)) return 1;
  return target_cpu >= M68K_ASM_EA_FULL_EXTENSION_CPU_MIN;
}

size_t m68k_asm_form_count(void) {
  return M68K_ASM_FORM_COUNT;
}

uint8_t m68k_asm_mnemonic_id_from_name(const char *mnemonic) {
  size_t low = 0U;
  size_t high = g_m68k_asm_mnemonic_lookup_count;
  if (mnemonic == NULL || mnemonic[0] == '\0') return M68K_ASM_MNEMONIC_NONE;
  while (low < high) {
    size_t mid = low + ((high - low) / 2U);
    int compare = m68k_ascii_icompare_local(mnemonic, g_m68k_asm_mnemonic_lookup[mid].name);
    if (compare == 0) return g_m68k_asm_mnemonic_lookup[mid].mnemonic_id;
    if (compare < 0) high = mid;
    else low = mid + 1U;
  }
  return M68K_ASM_MNEMONIC_NONE;
}

const char *m68k_asm_mnemonic_name(uint8_t mnemonic_id) {
  if (mnemonic_id >= M68K_ASM_MNEMONIC_COUNT) mnemonic_id = M68K_ASM_MNEMONIC_NONE;
  return g_m68k_asm_mnemonic_names[mnemonic_id];
}

const char *m68k_asm_resolve_register_alias(const char *name) {
  if (name == NULL) return NULL;
  if (m68k_ascii_icompare_local(name, "sp") == 0) return "a7";
  return name;
}

static size_t m68k_asm_find_control_register_name_index(const char *name) {
  size_t index;
  if (name == NULL || name[0] == '\0') return SIZE_MAX;
  for (index = 0U; index < g_m68k_asm_control_register_count; ++index) {
    if (m68k_ascii_icompare_local(name, g_m68k_asm_control_registers[index].name) == 0) return index;
  }
  return SIZE_MAX;
}

const M68kAsmControlRegisterDef *m68k_asm_find_control_register(const char *name, uint8_t target_cpu) {
  size_t index = m68k_asm_find_control_register_name_index(name);
  if (index == SIZE_MAX) return NULL;
  for (; index < g_m68k_asm_control_register_count; ++index) {
    const M68kAsmControlRegisterDef *entry = &g_m68k_asm_control_registers[index];
    if (m68k_ascii_icompare_local(entry->name, name) != 0) break;
    if (target_cpu != M68K_ASM_CPU_ANY && (entry->cpu_mask & (1u << target_cpu)) == 0u) continue;
    return entry;
  }
  return NULL;
}

const M68kAsmControlRegisterDef *m68k_asm_find_control_register_by_id(uint8_t id) {
  return (id == M68K_ASM_CONTROL_REGISTER_NONE || id >= g_m68k_asm_control_register_count)
    ? NULL
    : &g_m68k_asm_control_registers[id];
}

static int m68k_asm_form_allows_control_register(uint16_t asm_form_index, const M68kAsmOperandValue *operand) {
  const M68kAsmFormDef *form = &g_m68k_asm_forms[asm_form_index];
  size_t index;
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE || operand == NULL || operand->kind != M68K_ASM_OPERAND_CTRL_REG)
    return 0;
  if (form->control_register_count == 0) return 1;
  for (index = 0; index < form->control_register_count; ++index) {
    if (g_m68k_asm_form_control_register_ids[form->control_register_start + index] == operand->reg) return 1;
  }
  return 0;
}

const M68kAsmEaTextFormDef *m68k_asm_find_ea_text_form(uint8_t syntax_family, char size_suffix, char register_prefix,
    uint8_t target_cpu) {
  size_t index;
  for (index = 0; index < g_m68k_asm_ea_text_form_count; ++index) {
    const M68kAsmEaTextFormDef *form = &g_m68k_asm_ea_text_forms[index];
    if (form->syntax_family != syntax_family) continue;
    if (target_cpu != M68K_ASM_CPU_ANY && (form->cpu_mask & (1u << target_cpu)) == 0u) continue;
    if (size_suffix != '\0' && form->size_suffix != '\0' && form->size_suffix != size_suffix) continue;
    if (register_prefix != '\0' && form->register_prefix != '\0' && form->register_prefix != register_prefix) continue;
    return form;
  }
  return NULL;
}

uint16_t m68k_asm_form_index_for_id(uint8_t mnemonic_id, size_t operand_count) {
  size_t index;
  if (mnemonic_id == M68K_ASM_MNEMONIC_NONE) return M68K_ASM_FORM_NONE;
  for (index = 0; index < m68k_asm_form_count(); ++index) {
    const M68kAsmFormDef *form = &g_m68k_asm_forms[index];
    if (form->operand_count != operand_count) continue;
    if (form->mnemonic_id == mnemonic_id) return (uint16_t)index;
  }
  return M68K_ASM_FORM_NONE;
}

uint8_t m68k_asm_form_effective_size_mask(const M68kAsmFormDef *form) {
  return form->size_mask != 0 ? form->size_mask : form->size_mask_68000;
}

static uint8_t m68k_asm_form_effective_size_mask_for_cpu(const M68kAsmFormDef *form, uint8_t target_cpu) {
  if (target_cpu == M68K_ASM_CPU_68000 && form->size_mask_68000 != 0) return form->size_mask_68000;
  return m68k_asm_form_effective_size_mask(form);
}

uint8_t m68k_asm_form_effective_size_mask_for_operands(const M68kAsmFormDef *form, const M68kAsmOperandValue *operands,
  size_t operand_count) {
  size_t operand_index;
  uint8_t mask = m68k_asm_form_effective_size_mask(form);
  if (operands == NULL ||
    operand_count == 0 ||
    (form->ea_dn_size_mask == 0 && form->ea_memory_size_mask == 0)) {
    return mask;
  }
  for (operand_index = 0; operand_index < operand_count && operand_index < form->operand_count; ++operand_index) {
    const M68kAsmOperandValue *operand;
    if (form->operand_kinds[operand_index] != M68K_ASM_OPERAND_EA) {
      if (form->operand_kinds[operand_index] != M68K_ASM_OPERAND_BF_EA) continue;
    }
    operand = &operands[operand_index];
    if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) continue;
    if (operand->ea_mode == 0 && form->ea_dn_size_mask != 0) return form->ea_dn_size_mask;
    if (operand->ea_mode != 0 && form->ea_memory_size_mask != 0) return form->ea_memory_size_mask;
  }
  return mask;
}

static uint8_t m68k_asm_form_effective_size_mask_for_operands_and_cpu(const M68kAsmFormDef *form,
    const M68kAsmOperandValue *operands, size_t operand_count, uint8_t target_cpu) {
  size_t operand_index;
  uint8_t mask = m68k_asm_form_effective_size_mask_for_cpu(form, target_cpu);
  if (operands == NULL || operand_count == 0 ||
      (form->ea_dn_size_mask == 0 && form->ea_memory_size_mask == 0)) {
    return mask;
  }
  for (operand_index = 0; operand_index < operand_count && operand_index < form->operand_count; ++operand_index) {
    const M68kAsmOperandValue *operand;
    if (form->operand_kinds[operand_index] != M68K_ASM_OPERAND_EA) {
      if (form->operand_kinds[operand_index] != M68K_ASM_OPERAND_BF_EA) continue;
    }
    operand = &operands[operand_index];
    if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) continue;
    if (operand->ea_mode == 0 && form->ea_dn_size_mask != 0) return form->ea_dn_size_mask;
    if (operand->ea_mode != 0 && form->ea_memory_size_mask != 0) return form->ea_memory_size_mask;
  }
  return mask;
}

static uint8_t m68k_asm_form_size_value(const M68kAsmFormDef *form, char size_suffix) {
  switch (size_suffix) {
    case 'b': return form->size_value_b;
    case 'w': return form->size_value_w;
    case 'l': return form->size_value_l;
    default:  return M68K_ASM_FIELD_VALUE_UNSET;
  }
}

static uint8_t m68k_asm_form_opmode_value(const M68kAsmFormDef *form, char size_suffix) {
  switch (size_suffix) {
    case 'b': return form->opmode_value_b;
    case 'w': return form->opmode_value_w;
    case 'l': return form->opmode_value_l;
    default:  return M68K_ASM_FIELD_VALUE_UNSET;
  }
}

static char m68k_asm_suffix_from_mask(uint8_t mask) {
  if (mask == M68K_ASM_SIZE_B) return 'b';
  if (mask == M68K_ASM_SIZE_W) return 'w';
  if (mask == M68K_ASM_SIZE_L) return 'l';
  return '\0';
}

static size_t m68k_asm_size_bytes_from_suffix(char size_suffix) {
  switch (size_suffix) {
    case 'b': return 1;
    case 'w': return 2;
    case 'l': return 4;
    default: return 0;
  }
}

static char m68k_asm_resolve_size_suffix(const M68kAsmFormDef *form, const M68kAsmOperandValue *operands,
    size_t operand_count, char explicit_suffix, uint8_t target_cpu) {
  size_t patch_index;
  if (explicit_suffix != '\0') return explicit_suffix;
  for (patch_index = 0; patch_index < form->patch_count; ++patch_index) {
    const M68kAsmFieldPatch *patch = &g_m68k_asm_patches[form->patch_start + patch_index];
    if (patch->field_kind == M68K_ASM_FIELD_SIZE || patch->field_kind == M68K_ASM_FIELD_DISPLACEMENT_8) return 'w';
  }
  if (m68k_asm_form_size_value(form, 'l') != M68K_ASM_FIELD_VALUE_UNSET &&
      m68k_asm_form_size_value(form, 'b') == M68K_ASM_FIELD_VALUE_UNSET &&
      m68k_asm_form_size_value(form, 'w') == M68K_ASM_FIELD_VALUE_UNSET) {
    return 'l';
  }
  return m68k_asm_suffix_from_mask(m68k_asm_form_effective_size_mask_for_operands_and_cpu(form, operands, operand_count, target_cpu));
}

static int m68k_asm_operand_matches_kind(const M68kAsmOperandValue *operand, uint8_t operand_kind) {
  switch (operand_kind) {
    case M68K_ASM_OPERAND_DN:
      return operand->kind == M68K_ASM_OPERAND_DN;
    case M68K_ASM_OPERAND_DN_PAIR:
      return operand->kind == M68K_ASM_OPERAND_DN_PAIR;
    case M68K_ASM_OPERAND_AN:
      return operand->kind == M68K_ASM_OPERAND_AN;
    case M68K_ASM_OPERAND_IND:
      return operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 2;
    case M68K_ASM_OPERAND_POSTINC:
      return operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 3;
    case M68K_ASM_OPERAND_PREDEC:
      return operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 4;
    case M68K_ASM_OPERAND_ABSL:
      return operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 7 && operand->ea_reg == 1;
    case M68K_ASM_OPERAND_BF_EA:
      return operand->kind == M68K_ASM_OPERAND_BF_EA;
    case M68K_ASM_OPERAND_REGLIST:
      return operand->kind == M68K_ASM_OPERAND_REGLIST;
    case M68K_ASM_OPERAND_RN:
      return operand->kind == M68K_ASM_OPERAND_RN;
    case M68K_ASM_OPERAND_RN_PAIR:
      return operand->kind == M68K_ASM_OPERAND_RN_PAIR;
    case M68K_ASM_OPERAND_CCR:
      return operand->kind == M68K_ASM_OPERAND_CCR;
    case M68K_ASM_OPERAND_CACHE_SEL:
      return operand->kind == M68K_ASM_OPERAND_CACHE_SEL;
    case M68K_ASM_OPERAND_CTRL_REG:
      return operand->kind == M68K_ASM_OPERAND_CTRL_REG;
    case M68K_ASM_OPERAND_EA:
      return operand->kind == M68K_ASM_OPERAND_EA;
    case M68K_ASM_OPERAND_IMM:
      return operand->kind == M68K_ASM_OPERAND_IMM;
    case M68K_ASM_OPERAND_LABEL:
      return operand->kind == M68K_ASM_OPERAND_LABEL;
    case M68K_ASM_OPERAND_SR:
      return operand->kind == M68K_ASM_OPERAND_SR;
    case M68K_ASM_OPERAND_USP:
      return operand->kind == M68K_ASM_OPERAND_USP;
    case M68K_ASM_OPERAND_NONE:
      return operand->kind == M68K_ASM_OPERAND_NONE;
    default:
      return 0;
  }
}

int m68k_asm_form_supports_size_suffix(const M68kAsmFormDef *form, char size_suffix) {
  uint8_t mask;
  if (size_suffix == '\0') return 1;
  mask = m68k_asm_form_effective_size_mask(form);
  switch (size_suffix) {
    case 'b': return (mask & M68K_ASM_SIZE_B) != 0;
    case 'w': return (mask & M68K_ASM_SIZE_W) != 0;
    case 'l': return (mask & M68K_ASM_SIZE_L) != 0;
    default:  return 0;
  }
}

int m68k_asm_form_supports_cpu(const M68kAsmFormDef *form, uint8_t target_cpu) {
  if (target_cpu == M68K_ASM_CPU_ANY) return 1;
  return (form->cpu_mask & (1u << target_cpu)) != 0u;
}

char m68k_asm_choose_size_suffix(const M68kAsmFormDef *form, const M68kAsmOperandValue *operands, size_t operand_count,
  char explicit_suffix) {
  return m68k_asm_resolve_size_suffix(form, operands, operand_count, explicit_suffix, M68K_ASM_CPU_ANY);
}

uint16_t m68k_asm_form_index_for_operands_id(uint8_t mnemonic_id, const M68kAsmOperandValue *operands,
    size_t operand_count, char size_suffix, uint8_t target_cpu) {
  size_t index;
  if (mnemonic_id == M68K_ASM_MNEMONIC_NONE) return M68K_ASM_FORM_NONE;
  for (index = 0; index < m68k_asm_form_count(); ++index) {
    const M68kAsmFormDef *form = &g_m68k_asm_forms[index];
    size_t operand_index;
    if (form->operand_count != operand_count) continue;
    if (form->mnemonic_id != mnemonic_id) continue;
    if (!m68k_asm_form_supports_cpu(form, target_cpu)) continue;
    for (operand_index = 0; operand_index < operand_count; ++operand_index) {
      if (!m68k_asm_operand_supports_cpu(&operands[operand_index], target_cpu)) break;
      if (!m68k_asm_operand_matches_kind(&operands[operand_index], form->operand_kinds[operand_index])) break;
      if (form->operand_kinds[operand_index] == M68K_ASM_OPERAND_CTRL_REG &&
        !m68k_asm_form_allows_control_register((uint16_t)index, &operands[operand_index])) {
        break;
      }
    }
    if (operand_index == operand_count) {
      uint8_t mask = m68k_asm_form_effective_size_mask_for_operands_and_cpu(form, operands, operand_count, target_cpu);
      if (size_suffix == '\0') return (uint16_t)index;
      if ((size_suffix == 'b' && (mask & M68K_ASM_SIZE_B) != 0) ||
        (size_suffix == 'w' && (mask & M68K_ASM_SIZE_W) != 0) ||
        (size_suffix == 'l' && (mask & M68K_ASM_SIZE_L) != 0)) {
        return (uint16_t)index;
      }
    }
  }
  return M68K_ASM_FORM_NONE;
}

size_t m68k_asm_operand_extension_word_count(uint16_t asm_form_index, const M68kAsmOperandValue *operand,
    char size_suffix) {
  (void)asm_form_index;
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_LABEL) return size_suffix == 'b' ? 0 : 1;
  if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) return 0;
  if (operand->ea_mode == 5 || (operand->ea_mode == 7 && operand->ea_reg == 0) ||
    (operand->ea_mode == 7 && operand->ea_reg == 2)) return 1;
  if (operand->ea_mode == 7 && operand->ea_reg == 1) return 2;
  if (operand->ea_mode == 7 && operand->ea_reg == 4) return size_suffix == 'l' ? 2 : 1;
  if (operand->ea_mode == 6 || (operand->ea_mode == 7 && operand->ea_reg == 3)) {
    int use_full = operand->full_ext_base_suppress != 0 || operand->full_ext_index_suppress != 0 ||
      operand->full_ext_base_disp_size != 0 || operand->full_ext_outer_disp_size != 0 || operand->full_ext_iis != 0;
    if (!use_full) return 1;
    {
      size_t count = 1;
      if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_WORD) count += 1;
      else if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_LONG) count += 2;
      if (operand->full_ext_outer_disp_size == M68K_ASM_FULL_EXT_BD_WORD) count += 1;
      else if (operand->full_ext_outer_disp_size == M68K_ASM_FULL_EXT_BD_LONG) count += 2;
      return count;
    }
  }
  return 0;
}

size_t m68k_asm_operand_relative_base_offset(uint16_t asm_form_index, const M68kAsmOperandValue *operands,
    size_t operand_count, char size_suffix, size_t operand_index, int include_current_operand) {
  const M68kAsmFormDef *form = &g_m68k_asm_forms[asm_form_index];
  size_t base_offset = 2U;
  size_t index;
  base_offset += (size_t)form->bound_word_count * 2U;
  if (operands == NULL) return base_offset;
  for (index = 0; index < operand_index && index < operand_count; ++index) {
    base_offset += m68k_asm_operand_extension_word_count(asm_form_index, &operands[index], size_suffix) * 2U;
  }
  if (include_current_operand && operand_index < operand_count) {
    base_offset += m68k_asm_operand_extension_word_count(asm_form_index, &operands[operand_index], size_suffix) * 2U;
  }
  return base_offset;
}

int m68k_asm_encode_opword(uint16_t asm_form_index, const uint16_t *field_values, size_t field_value_count,
    uint16_t *out_opword) {
  const M68kAsmFormDef *form = &g_m68k_asm_forms[asm_form_index];
  size_t patch_index;
  uint16_t opword;
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE || out_opword == NULL) return -1;
  if (field_value_count < form->patch_count) return -2;
  opword = (uint16_t)(form->opword_base & form->opword_mask);
  for (patch_index = 0; patch_index < form->patch_count; ++patch_index) {
    const M68kAsmFieldPatch *patch = &g_m68k_asm_patches[form->patch_start + patch_index];
    if (patch->word_index != 0) continue;
    uint16_t width = (uint16_t)(patch->bit_hi - patch->bit_lo + 1);
    uint16_t mask = (uint16_t)(((uint16_t)1U << width) - 1U);
    uint16_t value = (uint16_t)(field_values[patch_index] & mask);
    opword = (uint16_t)(opword | (uint16_t)(value << patch->bit_lo));
  }
  *out_opword = opword;
  return 0;
}

static int m68k_asm_append_word(uint16_t *out_words, size_t max_words, size_t *word_count, uint16_t word) {
  if (*word_count >= max_words) return -4;
  out_words[(*word_count)++] = word;
  return 0;
}

static int m68k_asm_append_long_words(uint16_t *out_words, size_t max_words, size_t *word_count, uint32_t value) {
  if ((*word_count + 1) >= max_words) return -4;
  out_words[(*word_count)++] = (uint16_t)((value >> 16) & 0xFFFF);
  out_words[(*word_count)++] = (uint16_t)(value & 0xFFFF);
  return 0;
}

static int m68k_asm_emit_bound_extension_word(const M68kAsmFormDef *form, uint8_t word_index,
    const uint16_t *field_values, uint16_t *out_words, size_t max_words, size_t *word_count) {
  size_t patch_index;
  uint16_t extword;
  if (word_index == 0 || word_index > form->bound_word_count) return -4;
  extword = (uint16_t)(form->bound_word_bases[word_index - 1] & form->bound_word_masks[word_index - 1]);
  for (patch_index = 0; patch_index < form->patch_count; ++patch_index) {
    const M68kAsmFieldPatch *patch = &g_m68k_asm_patches[form->patch_start + patch_index];
    if (patch->word_index != word_index) continue;
    uint16_t width = (uint16_t)(patch->bit_hi - patch->bit_lo + 1);
    uint16_t mask = (uint16_t)(((uint16_t)1U << width) - 1U);
    uint16_t value = (uint16_t)(field_values[patch_index] & mask);
    extword = (uint16_t)(extword | (uint16_t)(value << patch->bit_lo));
  }
  return m68k_asm_append_word(out_words, max_words, word_count, extword);
}

static int m68k_asm_emit_immediate_extension(uint16_t asm_form_index, const uint16_t *field_values,
    size_t field_value_count, const M68kAsmOperandValue *operands, size_t operand_count,
    const M68kAsmOperandValue *operand, uint16_t *out_words, size_t max_words, size_t *word_count) {
  const M68kAsmFormDef *form = &g_m68k_asm_forms[asm_form_index];
  size_t size_bytes = m68k_asm_form_size_bytes(asm_form_index, field_values, field_value_count);
  if (size_bytes == 0)
    size_bytes = m68k_asm_size_bytes_from_suffix(m68k_asm_resolve_size_suffix(form, operands, operand_count, '\0',
      M68K_ASM_CPU_ANY));
  if (size_bytes == 0) size_bytes = 2;
  if (size_bytes <= 2) return m68k_asm_append_word(out_words, max_words, word_count, (uint16_t)(operand->value & 0xFFFF));
  return m68k_asm_append_long_words(out_words, max_words, word_count, operand->value);
}

static int m68k_asm_emit_index_extension(const M68kAsmOperandValue *operand, uint16_t *out_words, size_t max_words,
    size_t *word_count) {
  int use_full = operand->full_ext_base_suppress != 0 || operand->full_ext_index_suppress != 0 ||
    operand->full_ext_base_disp_size != 0 || operand->full_ext_outer_disp_size != 0 || operand->full_ext_iis != 0;
  if (!use_full) {
    uint16_t ext = 0;
    ext |= (uint16_t)((operand->index_is_address & 0x1U) << M68K_ASM_BRIEF_EXT_DA_BIT_LO);
    ext |= (uint16_t)((operand->index_reg & 0x7U) << M68K_ASM_BRIEF_EXT_REGISTER_BIT_LO);
    ext |= (uint16_t)((operand->index_long & 0x1U) << M68K_ASM_BRIEF_EXT_WL_BIT_LO);
    ext |= (uint16_t)((operand->scale & 0x3U) << M68K_ASM_BRIEF_EXT_SCALE_BIT_LO);
    ext |= (uint16_t)(operand->value & 0xFFU);
    return m68k_asm_append_word(out_words, max_words, word_count, ext);
  }
  if (m68k_asm_append_word(out_words, max_words, word_count, m68k_asm_encode_full_ext_word(operand)) != 0) return -4;
  if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_WORD) {
    if (m68k_asm_append_word(out_words, max_words, word_count, (uint16_t)(operand->full_ext_base_disp_value & 0xFFFF)) != 0) return -4;
  } else if (operand->full_ext_base_disp_size == M68K_ASM_FULL_EXT_BD_LONG) {
    if (m68k_asm_append_long_words(out_words, max_words, word_count, operand->full_ext_base_disp_value) != 0) return -4;
  }
  if (operand->full_ext_outer_disp_size == M68K_ASM_FULL_EXT_BD_WORD) {
    if (m68k_asm_append_word(out_words, max_words, word_count, (uint16_t)(operand->full_ext_outer_disp_value & 0xFFFF)) != 0) return -4;
  } else if (operand->full_ext_outer_disp_size == M68K_ASM_FULL_EXT_BD_LONG) {
    if (m68k_asm_append_long_words(out_words, max_words, word_count, operand->full_ext_outer_disp_value) != 0) return -4;
  }
  return 0;
}

static int m68k_asm_emit_one_extension(uint16_t asm_form_index, const M68kAsmExtensionDef *extension,
    const uint16_t *field_values, size_t field_value_count, const M68kAsmOperandValue *operands, size_t operand_count,
    uint16_t *out_words, size_t max_words, size_t *word_count) {
  const M68kAsmOperandValue *operand = &operands[extension->operand_index];
  switch (extension->kind) {
    case M68K_ASM_EXTENSION_EA_SINGLE_WORD:
      if (((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
          ((operand->ea_mode == 5) || (operand->ea_mode == 7 && operand->ea_reg == 0) ||
          (operand->ea_mode == 7 && operand->ea_reg == 2))))
        return m68k_asm_append_word(out_words, max_words, word_count, (uint16_t)(operand->value & 0xFFFF));
      return 0;
    case M68K_ASM_EXTENSION_EA_LONG_ADDRESS:
      if ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
          operand->ea_mode == 7 && operand->ea_reg == 1)
        return m68k_asm_append_long_words(out_words, max_words, word_count, operand->value);
      return 0;
    case M68K_ASM_EXTENSION_EA_IMMEDIATE:
      if ((operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 7 && operand->ea_reg == 4) ||
          operand->kind == M68K_ASM_OPERAND_IMM)
        return m68k_asm_emit_immediate_extension(asm_form_index, field_values, field_value_count, operands, operand_count,
          operand, out_words, max_words, word_count);
      return 0;
    case M68K_ASM_EXTENSION_EA_INDEX:
      if ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
        ((operand->ea_mode == 6) || (operand->ea_mode == 7 && operand->ea_reg == 3)))
        return m68k_asm_emit_index_extension(operand, out_words, max_words, word_count);
      return 0;
    case M68K_ASM_EXTENSION_LABEL_DISP16_IF_ZERO:
      if (field_values[extension->patch_index] == 0)
        return m68k_asm_append_word(out_words, max_words, word_count, (uint16_t)(operand->value & 0xFFFF));
      return 0;
    case M68K_ASM_EXTENSION_LABEL_DISP16_ALWAYS:
    case M68K_ASM_EXTENSION_DISP16_ALWAYS:
      return m68k_asm_append_word(out_words, max_words, word_count, (uint16_t)(operand->value & 0xFFFF));
    default:
      return -6;
  }
}

int m68k_asm_emit_extensions(uint16_t asm_form_index, const uint16_t *field_values, size_t field_value_count,
    const M68kAsmOperandValue *operands, size_t operand_count, uint16_t *out_words, size_t max_words,
    size_t *out_word_count) {
  const M68kAsmFormDef *form = &g_m68k_asm_forms[asm_form_index];
  size_t extension_index;
  uint8_t bound_word_index;
  size_t word_count = 0;
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE || out_word_count == NULL) return -1;
  if (field_value_count != form->patch_count) return -2;
  if (operand_count != form->operand_count) return -3;
  for (bound_word_index = 1; bound_word_index <= form->bound_word_count; ++bound_word_index) {
    if (m68k_asm_emit_bound_extension_word(form, bound_word_index, field_values, out_words, max_words, &word_count) != 0) return -4;
  }
  for (extension_index = 0; extension_index < form->extension_count; ++extension_index) {
    const M68kAsmExtensionDef *extension = &g_m68k_asm_extensions[form->extension_start + extension_index];
    int result = m68k_asm_emit_one_extension(asm_form_index, extension, field_values, field_value_count, operands,
      operand_count, out_words, max_words, &word_count);
    if (result != 0) return result;
  }
  *out_word_count = word_count;
  return 0;
}

int m68k_asm_build_patch_values(uint16_t asm_form_index, char size_suffix, const M68kAsmOperandValue *operands,
    size_t operand_count, uint16_t *out_field_values, size_t max_field_values) {
  const M68kAsmFormDef *form = &g_m68k_asm_forms[asm_form_index];
  size_t patch_index;
  char resolved_size_suffix;
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE || out_field_values == NULL) return -1;
  if (operand_count != form->operand_count || max_field_values < form->patch_count) return -2;
  resolved_size_suffix = m68k_asm_resolve_size_suffix(form, operands, operand_count, size_suffix, M68K_ASM_CPU_ANY);
  for (patch_index = 0; patch_index < form->patch_count; ++patch_index) {
    const M68kAsmFieldPatch *patch = &g_m68k_asm_patches[form->patch_start + patch_index];
    switch (patch->field_kind) {
      case M68K_ASM_FIELD_SIZE: {
          uint8_t size_value = m68k_asm_form_size_value(form, resolved_size_suffix);
          if (size_value == M68K_ASM_FIELD_VALUE_UNSET) return -3;
          out_field_values[patch_index] = size_value;
        }
        break;
      case M68K_ASM_FIELD_OPMODE: {
          uint8_t opmode_value = m68k_asm_form_opmode_value(form, resolved_size_suffix);
          if (opmode_value == M68K_ASM_FIELD_VALUE_UNSET) return -3;
          out_field_values[patch_index] = opmode_value;
        }
        break;
      case M68K_ASM_FIELD_REGISTER:
      case M68K_ASM_FIELD_BITFIELD_OFFSET_DA:
      case M68K_ASM_FIELD_BITFIELD_WIDTH_DA:
      case M68K_ASM_FIELD_CACHE:
      case M68K_ASM_FIELD_DA:
      case M68K_ASM_FIELD_MODE:
      case M68K_ASM_FIELD_DATA:
      case M68K_ASM_FIELD_DISPLACEMENT_8:
      case M68K_ASM_FIELD_DISPLACEMENT_16:
      case M68K_ASM_FIELD_OFFSET:
      case M68K_ASM_FIELD_REGLIST_MASK:
      case M68K_ASM_FIELD_WIDTH: {
        const M68kAsmOperandValue *operand;
        if (patch->value_source == M68K_ASM_VALUE_NONE) {
          out_field_values[patch_index] = 0;
          break;
        }
        if (patch->operand_index < 0 || (size_t)patch->operand_index >= operand_count) return -4;
        operand = &operands[patch->operand_index];
        switch (patch->value_source) {
          case M68K_ASM_VALUE_OPMODE:
            return -8;
          case M68K_ASM_VALUE_REG:
            out_field_values[patch_index] =
              (operand->kind == M68K_ASM_OPERAND_EA ||
               operand->kind == M68K_ASM_OPERAND_BF_EA)
                ? operand->ea_reg
                : operand->reg;
            break;
          case M68K_ASM_VALUE_REG_FIRST:
            out_field_values[patch_index] =
              (operand->kind == M68K_ASM_OPERAND_EA ||
               operand->kind == M68K_ASM_OPERAND_BF_EA)
                ? operand->ea_reg
                : operand->reg;
            break;
          case M68K_ASM_VALUE_REG_SECOND:
            out_field_values[patch_index] = operand->pair_reg;
            break;
          case M68K_ASM_VALUE_REG_KIND:
            out_field_values[patch_index] =
              (operand->kind == M68K_ASM_OPERAND_EA ||
               operand->kind == M68K_ASM_OPERAND_BF_EA)
                ? (operand->ea_mode != 0U ? 1U : 0U)
                : (operand->reg_is_address ? 1U : 0U);
            break;
          case M68K_ASM_VALUE_REG_KIND_FIRST:
            out_field_values[patch_index] =
              (operand->kind == M68K_ASM_OPERAND_EA ||
               operand->kind == M68K_ASM_OPERAND_BF_EA)
                ? (operand->ea_mode != 0U ? 1U : 0U)
                : (operand->reg_is_address ? 1U : 0U);
            break;
          case M68K_ASM_VALUE_REG_KIND_SECOND:
            out_field_values[patch_index] = operand->pair_reg_is_address ? 1 : 0;
            break;
          case M68K_ASM_VALUE_BF_OFFSET:
            out_field_values[patch_index] = operand->bf_offset == 32 ? 0 : operand->bf_offset;
            break;
          case M68K_ASM_VALUE_BF_OFFSET_KIND:
            out_field_values[patch_index] = operand->bf_offset_is_register ? 1 : 0;
            break;
          case M68K_ASM_VALUE_BF_WIDTH:
            out_field_values[patch_index] = operand->bf_width == 32 ? 0 : operand->bf_width;
            break;
          case M68K_ASM_VALUE_BF_WIDTH_KIND:
            out_field_values[patch_index] = operand->bf_width_is_register ? 1 : 0;
            break;
          case M68K_ASM_VALUE_EA_REG:
            out_field_values[patch_index] = operand->ea_reg;
            break;
          case M68K_ASM_VALUE_EA_MODE:
            out_field_values[patch_index] = operand->ea_mode;
            break;
          case M68K_ASM_VALUE_VALUE_HI16:
            out_field_values[patch_index] = (uint16_t)((operand->value >> 16) & 0xFFFF);
            break;
          case M68K_ASM_VALUE_VALUE_LO16:
            out_field_values[patch_index] = (uint16_t)(operand->value & 0xFFFF);
            break;
          case M68K_ASM_VALUE_VALUE:
            if (patch->field_kind == M68K_ASM_FIELD_DISPLACEMENT_8) {
              if (resolved_size_suffix == 'b') {
                out_field_values[patch_index] = (uint16_t)(operand->value & 0xFF);
              } else {
                if (resolved_size_suffix == 'w') out_field_values[patch_index] = form->branch_word_signal;
                else if (resolved_size_suffix == 'l') out_field_values[patch_index] = form->branch_long_signal;
                else return -7;
              }
            } else {
              out_field_values[patch_index] = (uint16_t)(operand->value & 0xFFFF);
            }
            break;
          default:
            return -8;
        }
        break;
      }
      default:
        return -9;
    }
  }
  return 0;
}

int m68k_asm_assemble_instruction(const M68kAsmInstructionSpec *spec, uint8_t *out_bytes, size_t max_bytes,
    size_t *out_byte_count) {
  const M68kAsmFormDef *form;
  uint16_t asm_form_index;
  uint16_t opword = 0;
  uint16_t ext_words[8];
  size_t ext_word_count = 0;
  size_t byte_count = 0;
  size_t index;
  if (spec == NULL || out_byte_count == NULL) return -1;
  asm_form_index = m68k_asm_form_index_for_operands_id(spec->mnemonic_id, spec->operands, spec->operand_count, spec->size_suffix,
    spec->target_cpu);
  form = &g_m68k_asm_forms[asm_form_index];
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) return -2;
  if (m68k_asm_encode_opword(asm_form_index, spec->patch_values, spec->patch_value_count, &opword) != 0) return -3;
  if (m68k_asm_emit_extensions(asm_form_index, spec->patch_values, spec->patch_value_count, spec->operands,
      spec->operand_count, ext_words, sizeof(ext_words) / sizeof(ext_words[0]), &ext_word_count) != 0) return -4;
  if (out_bytes == NULL || max_bytes < (2 + (ext_word_count * 2))) return -5;
  out_bytes[byte_count++] = (uint8_t)((opword >> 8) & 0xFF);
  out_bytes[byte_count++] = (uint8_t)(opword & 0xFF);
  for (index = 0; index < ext_word_count; ++index) {
    out_bytes[byte_count++] = (uint8_t)((ext_words[index] >> 8) & 0xFF);
    out_bytes[byte_count++] = (uint8_t)(ext_words[index] & 0xFF);
  }
  *out_byte_count = byte_count;
  return 0;
}

uint16_t m68k_asm_encode_full_ext_word(const M68kAsmOperandValue *operand) {
  uint16_t ext = 0;
  if (operand == NULL) return 0;
  ext |= (uint16_t)(1U << M68K_ASM_FULL_EXT_FORMAT_BIT_LO);
  ext |= (uint16_t)((operand->index_is_address & 0x1U) << M68K_ASM_FULL_EXT_DA_BIT_LO);
  ext |= (uint16_t)((operand->index_reg & 0x7U) << M68K_ASM_FULL_EXT_REGISTER_BIT_LO);
  ext |= (uint16_t)((operand->index_long & 0x1U) << M68K_ASM_FULL_EXT_WL_BIT_LO);
  ext |= (uint16_t)((operand->scale & 0x3U) << M68K_ASM_FULL_EXT_SCALE_BIT_LO);
  ext |= (uint16_t)((operand->full_ext_base_suppress & 0x1U) << M68K_ASM_FULL_EXT_BS_BIT_LO);
  ext |= (uint16_t)((operand->full_ext_index_suppress & 0x1U) << M68K_ASM_FULL_EXT_IS_BIT_LO);
  ext |= (uint16_t)((operand->full_ext_base_disp_size & 0x3U) << M68K_ASM_FULL_EXT_BD_SIZE_BIT_LO);
  ext |= (uint16_t)((operand->full_ext_iis & 0x7U) << M68K_ASM_FULL_EXT_IIS_BIT_LO);
  return ext;
}

