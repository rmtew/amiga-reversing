/* Static assembler runtime interface over generated KB-derived tables. */
#ifndef M68K_ASSEMBLER_H
#define M68K_ASSEMBLER_H

#include "m68k_asm_tables.h"

const char *m68k_asm_resolve_register_alias(const char *name);
size_t m68k_asm_operand_extension_word_count(const M68kAsmFormDef *form, const M68kAsmOperandValue *operand,
  char size_suffix);

#endif
