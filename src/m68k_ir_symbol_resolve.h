#ifndef M68K_IR_SYMBOL_RESOLVE_H
#define M68K_IR_SYMBOL_RESOLVE_H

#include "m68k_diagnostics.h"
#include "m68k_ir.h"
#include "m68k_source_lookup.h"

#include <stddef.h>
#include <stdint.h>

typedef M68kSourceLookupResult (*M68kIrResolveLookupFn)(const char *name, void *user_data);

typedef struct M68kIrResolveContext {
  void *user_data;
  M68kIrResolveLookupFn lookup_symbol;
} M68kIrResolveContext;

typedef struct M68kIrSymbolApplyResult {
  uint8_t ok;
  M68kInstructionIR instruction;
} M68kIrSymbolApplyResult;

M68kIrSymbolApplyResult m68k_ir_apply_symbol_refs(const M68kIrResolveContext *context,
  M68kInstructionIR instruction, const M68kAsmFormDef *form, uint32_t instruction_offset,
  size_t line_number, int allow_undefined, M68kDiagSink diagnostics);

#endif
