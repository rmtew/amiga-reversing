#ifndef M68K_SOURCE_EXPR_H
#define M68K_SOURCE_EXPR_H

#include "m68k_source_lookup.h"

#include <stddef.h>
#include <stdint.h>

typedef struct M68kSourceLinearExpr {
    int valid;
    int32_t constant;
    size_t symbol_count;
    size_t symbol_ids[2];
    size_t section_indices[2];
    int symbol_signs[2];
} M68kSourceLinearExpr;

typedef struct M68kSourceLinearExprParseResult {
    uint8_t ok;
    M68kSourceLinearExpr expr;
} M68kSourceLinearExprParseResult;

typedef struct M68kSourceRelocRef {
    uint8_t ok;
    size_t target_section;
} M68kSourceRelocRef;

typedef struct M68kSourceLinearExprEvalResult {
    uint8_t ok;
    uint32_t value;
    M68kSourceRelocRef reloc;
} M68kSourceLinearExprEvalResult;

typedef M68kSourceLookupResult (*M68kSourceExprLookupFn)(const char *name, void *user_data);

M68kSourceLinearExprParseResult m68k_source_parse_linear_expression(const char *text, int constants_only,
    M68kSourceExprLookupFn lookup, void *user_data);

M68kSourceLinearExprEvalResult m68k_source_evaluate_linear_expression(M68kSourceLinearExpr expr);

#endif
