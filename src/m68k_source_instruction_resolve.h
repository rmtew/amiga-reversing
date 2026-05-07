#ifndef M68K_SOURCE_INSTRUCTION_RESOLVE_H
#define M68K_SOURCE_INSTRUCTION_RESOLVE_H

#include "m68k_diagnostics.h"
#include "m68k_instruction_spec.h"
#include "m68k_ir.h"
#include "m68k_source_lookup.h"

#include <stddef.h>
#include <stdint.h>

typedef M68kSourceLookupResult (*M68kSourceInstructionResolveLookupFn)(const char *name, void *user_data);

typedef struct M68kSourceInstructionResolveContext {
    void *user_data;
    M68kSourceInstructionResolveLookupFn lookup_symbol;
} M68kSourceInstructionResolveContext;

#define M68K_SOURCE_RESOLVE_MAX_ABS_FIXUP_OPERANDS 4

typedef struct M68kSourceAbsFixupList {
    uint8_t count;
    uint8_t operands[M68K_SOURCE_RESOLVE_MAX_ABS_FIXUP_OPERANDS];
} M68kSourceAbsFixupList;

typedef struct M68kSourceResolvedInstruction {
    uint8_t ok;
    M68kInstructionIR instruction;
    M68kSourceAbsFixupList abs_fixups;
} M68kSourceResolvedInstruction;

M68kSourceResolvedInstruction m68k_source_resolve_instruction_operands(const M68kSourceInstructionResolveContext *context,
    size_t line_number, char requested_size_suffix, uint32_t instruction_offset, int allow_undefined,
    const M68kInstructionIR *parsed_instruction, M68kDiagSink diagnostics);

#endif
