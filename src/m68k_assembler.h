/* Static assembler runtime interface over generated KB-derived tables. */
#ifndef M68K_ASSEMBLER_H
#define M68K_ASSEMBLER_H

#include "m68k_asm_metadata.h"

uint8_t m68k_asm_mnemonic_id_from_name(const char *mnemonic);
const char *m68k_asm_mnemonic_name(uint8_t mnemonic_id);
const M68kAsmControlRegisterDef *m68k_asm_find_control_register_by_id(uint8_t id);
const M68kAsmFormDef *m68k_asm_find_form_id(uint8_t mnemonic_id, size_t operand_count);
const M68kAsmFormDef *m68k_asm_find_form_for_operands_id(uint8_t mnemonic_id,
  const M68kAsmOperandValue *operands, size_t operand_count, char size_suffix, uint8_t target_cpu);
const char *m68k_asm_resolve_register_alias(const char *name);
size_t m68k_asm_operand_extension_word_count(const M68kAsmFormDef *form, const M68kAsmOperandValue *operand,
  char size_suffix);
size_t m68k_asm_operand_relative_base_offset(const M68kAsmFormDef *form, const M68kAsmOperandValue *operands,
  size_t operand_count, char size_suffix, size_t operand_index, int include_current_operand);

#endif
