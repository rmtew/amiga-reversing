#ifndef M68K_IR_SYMBOL_RESOLVE_H
#define M68K_IR_SYMBOL_RESOLVE_H

#include "m68k_ir.h"

#include <stddef.h>
#include <stdint.h>

typedef int (*M68kIrResolveLookupFn)(const char *name, uint32_t *out_value, size_t *out_section_index, int *out_defined,
  void *user_data);

typedef struct M68kIrResolveContext {
  void *user_data;
  M68kIrResolveLookupFn lookup_symbol;
} M68kIrResolveContext;

int m68k_ir_apply_symbol_refs(const M68kIrResolveContext *context, M68kInstructionIR *instruction,
  const M68kAsmFormDef *form, uint32_t instruction_offset, size_t line_number, int allow_undefined,
  int *out_abs_fixup_operands, size_t *out_abs_fixup_count, char *out_error, size_t out_error_size);

#endif
