/* Stable assembler metadata runtime interface over generated KB-derived ids and tables. */
#ifndef M68K_ASM_METADATA_H
#define M68K_ASM_METADATA_H

#include "generated/m68k_asm_tables.h"
#include "generated/m68k_form_model.h"

#include <stddef.h>
#include <stdint.h>

typedef struct {
  uint8_t field_kind;
  uint8_t word_index;
  uint8_t occurrence;
  uint8_t bit_hi;
  uint8_t bit_lo;
  int8_t operand_index;
  uint8_t value_source;
} M68kAsmFieldPatch;

typedef struct {
  uint8_t kind;
  uint8_t operand_index;
  uint8_t patch_index;
} M68kAsmExtensionDef;

typedef struct {
  const char *name;
  uint16_t id;
  uint16_t value;
  uint8_t cpu_mask;
} M68kAsmControlRegisterDef;

typedef struct {
  const char *name;
  uint8_t syntax_family;
  uint8_t ea_mode;
  int8_t ea_reg;
  uint8_t cpu_mask;
  const char *base_token;
  uint8_t uses_base_register;
  const char *prefix_token;
  const char *suffix_token;
  char register_prefix;
  char size_suffix;
  uint8_t allow_label;
  uint8_t value_kind;
  uint8_t index_required;
} M68kAsmEaTextFormDef;

typedef struct {
  uint8_t kind;
  uint8_t reg;
  uint8_t pair_reg;
  uint8_t reg_is_address;
  uint8_t pair_reg_is_address;
  uint8_t bf_offset_is_register;
  uint8_t bf_offset;
  uint8_t bf_width_is_register;
  uint8_t bf_width;
  uint8_t ea_mode;
  uint8_t ea_reg;
  uint32_t value;
  uint8_t index_is_address;
  uint8_t index_reg;
  uint8_t index_long;
  uint8_t scale;
  uint8_t full_ext_base_suppress;
  uint8_t full_ext_index_suppress;
  uint8_t full_ext_base_disp_size;
  uint8_t full_ext_outer_disp_size;
  uint8_t full_ext_iis;
  uint32_t full_ext_base_disp_value;
  uint32_t full_ext_outer_disp_value;
} M68kAsmOperandValue;

typedef struct {
  uint8_t mnemonic_id;
  char size_suffix;
  uint8_t target_cpu;
  size_t operand_count;
  const uint16_t *patch_values;
  size_t patch_value_count;
  const M68kAsmOperandValue *operands;
} M68kAsmInstructionSpec;

typedef struct {
  const char *mnemonic;
  const char *syntax;
  uint8_t mnemonic_id;
  uint16_t asm_form_index;
  M68kFormId canonical_form_id;
  uint8_t operand_count;
  uint8_t operand_kinds[4];
  uint8_t size_mask;
  uint8_t size_mask_68000;
  uint8_t ea_dn_size_mask;
  uint8_t ea_memory_size_mask;
  uint8_t cpu_mask;
  uint16_t control_register_start;
  uint8_t control_register_count;
  uint16_t opword_base;
  uint16_t opword_mask;
  uint16_t patch_start;
  uint8_t patch_count;
  uint8_t bound_word_count;
  uint16_t extension_start;
  uint8_t extension_count;
  uint16_t bound_word_bases[2];
  uint16_t bound_word_masks[2];
  uint8_t size_value_b;
  uint8_t size_value_w;
  uint8_t size_value_l;
  uint8_t opmode_value_b;
  uint8_t opmode_value_w;
  uint8_t opmode_value_l;
  uint8_t branch_word_signal;
  uint8_t branch_word_bytes;
  uint8_t branch_long_signal;
  uint8_t branch_long_bytes;
  uint8_t has_bound_word_extension;
} M68kAsmFormDef;

typedef struct {
  const char *name;
  uint8_t mnemonic_id;
} M68kAsmMnemonicLookupEntry;

typedef struct {
  uint8_t family;
  uint16_t render_size_flags;
  uint8_t fpu_alias_target_mnemonic_id;
  uint8_t fpu_coprocessor_mnemonic_id;
} M68kAsmMnemonicMetadata;

typedef struct {
  uint16_t start;
  uint16_t count;
} M68kAsmFormRange;

extern const M68kAsmFormDef g_m68k_asm_forms[M68K_ASM_FORM_SLOT_COUNT];
extern const M68kAsmFieldPatch g_m68k_asm_patches[M68K_ASM_PATCH_COUNT];
extern const M68kAsmExtensionDef g_m68k_asm_extensions[M68K_ASM_EXTENSION_DEF_COUNT];
extern const M68kAsmControlRegisterDef g_m68k_asm_control_registers[];
extern const uint16_t g_m68k_asm_form_control_register_ids[];
extern const M68kAsmEaTextFormDef g_m68k_asm_ea_text_forms[M68K_ASM_EA_TEXT_FORM_COUNT];
extern const char *const g_m68k_asm_mnemonic_names[M68K_ASM_MNEMONIC_COUNT];
extern const M68kAsmMnemonicMetadata g_m68k_asm_mnemonic_metadata[M68K_ASM_MNEMONIC_COUNT];
extern const M68kAsmMnemonicLookupEntry g_m68k_asm_mnemonic_lookup[];
extern const M68kAsmFormRange g_m68k_asm_mnemonic_form_ranges[M68K_ASM_MNEMONIC_COUNT];
extern const uint16_t g_m68k_asm_form_index_by_canonical_id[M68K_CANONICAL_FORM_COUNT + 1u];
extern const size_t g_m68k_asm_mnemonic_lookup_count;
extern const size_t g_m68k_asm_control_register_count;
extern const size_t g_m68k_asm_ea_text_form_count;
extern const char *const g_m68k_asm_movem_mask_normal[16];
extern const char *const g_m68k_asm_movem_mask_predecrement[16];

size_t m68k_asm_form_count(void);
const M68kAsmControlRegisterDef *m68k_asm_find_control_register(const char *name, uint8_t target_cpu);
const M68kAsmEaTextFormDef *m68k_asm_find_ea_text_form(uint8_t syntax_family, char size_suffix,
  char register_prefix, uint8_t target_cpu);
uint16_t m68k_asm_form_index_for_id(uint8_t mnemonic_id, size_t operand_count);
uint16_t m68k_asm_form_index_for_canonical_id(M68kFormId form_id);
M68kFormId m68k_asm_canonical_form_id_for_operands_id(uint8_t mnemonic_id,
  const M68kAsmOperandValue *operands, size_t operand_count, char size_suffix, uint8_t target_cpu);
uint8_t m68k_asm_form_effective_size_mask(const M68kAsmFormDef *form);
uint8_t m68k_asm_form_effective_size_mask_for_operands(const M68kAsmFormDef *form,
  const M68kAsmOperandValue *operands, size_t operand_count);
int m68k_asm_form_supports_size_suffix(const M68kAsmFormDef *form, char size_suffix);
int m68k_asm_form_supports_cpu(const M68kAsmFormDef *form, uint8_t target_cpu);
char m68k_asm_choose_size_suffix(const M68kAsmFormDef *form, const M68kAsmOperandValue *operands,
  size_t operand_count, char explicit_suffix);
uint16_t m68k_asm_form_index_for_operands_id(uint8_t mnemonic_id,
  const M68kAsmOperandValue *operands, size_t operand_count, char size_suffix, uint8_t target_cpu);
size_t m68k_asm_operand_extension_word_count(uint16_t asm_form_index, const M68kAsmOperandValue *operand,
  char size_suffix);
int m68k_asm_encode_opword(uint16_t asm_form_index, const uint16_t *field_values,
  size_t field_value_count, uint16_t *out_opword);
int m68k_asm_emit_extensions(uint16_t asm_form_index, const uint16_t *field_values,
  size_t field_value_count, const M68kAsmOperandValue *operands, size_t operand_count, uint16_t *out_words,
  size_t max_words, size_t *out_word_count);
int m68k_asm_build_patch_values(uint16_t asm_form_index, char size_suffix,
  const M68kAsmOperandValue *operands, size_t operand_count, uint16_t *out_field_values,
  size_t max_field_values);
int m68k_asm_assemble_instruction(const M68kAsmInstructionSpec *spec, uint8_t *out_bytes,
  size_t max_bytes, size_t *out_byte_count);
uint16_t m68k_asm_encode_full_ext_word(const M68kAsmOperandValue *operand);

#endif
