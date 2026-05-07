#ifndef M68K_SYMBOLIC_PARSE_H
#define M68K_SYMBOLIC_PARSE_H

#include "m68k_instruction_spec.h"
#include "m68k_ir.h"
#include "m68k_source_lookup.h"

#include <stddef.h>
#include <stdint.h>

typedef M68kSourceLookupResult (*M68kSymbolicLookupFn)(const char *name, int require_constant, void *user_data);
typedef int (*M68kSymbolicIsNameFn)(const char *text, void *user_data);

typedef struct {
    uint8_t target_cpu;
    void *user_data;
    M68kSymbolicLookupFn lookup_symbol;
    M68kSymbolicIsNameFn is_symbol_name;
} M68kSymbolicParseContext;

int m68k_parse_instruction_with_symbol_fallback_spec(const M68kSymbolicParseContext *context, const char *line_text,
    InstructionSpec *out_instruction, char *out_fallback_line, size_t out_fallback_line_size);
int m68k_parse_instruction_with_symbol_fallback_ir(const M68kSymbolicParseContext *context, const char *line_text,
    M68kInstructionIR *out_instruction, char *out_fallback_line, size_t out_fallback_line_size);

#endif
