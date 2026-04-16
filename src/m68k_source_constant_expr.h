#ifndef M68K_SOURCE_CONSTANT_EXPR_H
#define M68K_SOURCE_CONSTANT_EXPR_H

#include "m68k_source_lookup.h"

#include <stdint.h>

typedef M68kSourceConstantResult (*M68kSourceConstantLookupFn)(const char *name, void *user_data);

M68kSourceConstantResult m68k_source_parse_constant_expression(const char *text, M68kSourceConstantLookupFn lookup,
    void *user_data);

#endif
