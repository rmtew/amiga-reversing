#ifndef M68K_SOURCE_CONSTANT_EXPR_H
#define M68K_SOURCE_CONSTANT_EXPR_H

#include <stdint.h>

typedef int (*M68kSourceConstantLookupFn)(const char *name, uint32_t *out_value, void *user_data);

int m68k_source_parse_constant_expression(const char *text, M68kSourceConstantLookupFn lookup, void *user_data,
    uint32_t *out_value);

#endif
