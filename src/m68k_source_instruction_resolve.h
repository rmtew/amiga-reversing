#ifndef M68K_SOURCE_INSTRUCTION_RESOLVE_H
#define M68K_SOURCE_INSTRUCTION_RESOLVE_H

#include "m68k_instruction_spec.h"
#include "m68k_ir.h"

#include <stddef.h>
#include <stdint.h>

typedef int (*M68kSourceInstructionResolveLookupFn)(const char *name, uint32_t *out_value, size_t *out_section_index,
    int *out_defined, void *user_data);

typedef struct M68kSourceInstructionResolveContext {
    void *user_data;
    int enable_vasm_compat_rewrites;
    M68kSourceInstructionResolveLookupFn lookup_symbol;
} M68kSourceInstructionResolveContext;

int m68k_source_resolve_instruction_operands(const M68kSourceInstructionResolveContext *context,
    size_t stmt_section_index, size_t line_number, char requested_size_suffix, uint32_t instruction_offset,
    int allow_undefined, const M68kInstructionIR *parsed_instruction, const M68kAsmFormDef **out_form,
    M68kInstructionIR *out_instruction, int *out_abs_fixup_operands, size_t *out_abs_fixup_count,
    char *out_error, size_t out_error_size);

#endif
