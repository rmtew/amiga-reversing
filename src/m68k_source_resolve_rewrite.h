#ifndef M68K_SOURCE_RESOLVE_REWRITE_H
#define M68K_SOURCE_RESOLVE_REWRITE_H

#include "m68k_instruction_spec.h"

#include <stddef.h>
#include <stdint.h>

typedef int (*M68kSourceResolveLookupFn)(const char *name, uint32_t *out_value, size_t *out_section_index, int *out_defined,
    void *user_data);

typedef struct M68kSourceResolveRewriteContext {
    void *user_data;
    M68kSourceResolveLookupFn lookup_symbol;
} M68kSourceResolveRewriteContext;

int m68k_try_rewrite_local_call_to_branch(const M68kSourceResolveRewriteContext *context,
    size_t stmt_section_index, char requested_size_suffix, InstructionSpec *instruction,
    const M68kAsmFormDef **out_form, uint32_t instruction_offset, char *out_error, size_t out_error_size);

void m68k_try_rewrite_local_ea_symbols_to_pc_relative(const M68kSourceResolveRewriteContext *context,
    size_t stmt_section_index, char requested_size_suffix, InstructionSpec *instruction,
    const M68kAsmFormDef **out_form, uint32_t instruction_offset, char *out_error, size_t out_error_size);

#endif
