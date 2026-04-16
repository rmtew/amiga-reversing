#ifndef M68K_SOURCE_REWRITE_H
#define M68K_SOURCE_REWRITE_H

#include "m68k_source_lookup.h"

#include <stddef.h>
#include <stdint.h>

typedef int (*M68kSourceRewriteIsSymbolNameFn)(const char *text, void *user_data);
typedef int (*M68kSourceRewriteIsConstantSymbolFn)(const char *name, void *user_data);
typedef M68kSourceConstantResult (*M68kSourceRewriteParseConstantFn)(const char *text, void *user_data);

typedef struct M68kSourceRewriteContext {
    void *user_data;
    M68kSourceRewriteIsSymbolNameFn is_symbol_name;
    M68kSourceRewriteIsConstantSymbolFn is_constant_symbol;
    M68kSourceRewriteParseConstantFn parse_constant;
} M68kSourceRewriteContext;

int m68k_rewrite_movea_symbolic_immediate_to_lea(const M68kSourceRewriteContext *context,
    const char *line_text, char *out_text, size_t out_text_size);
int m68k_rewrite_move_immediate_to_moveq(const M68kSourceRewriteContext *context,
    const char *line_text, char *out_text, size_t out_text_size);

#endif
