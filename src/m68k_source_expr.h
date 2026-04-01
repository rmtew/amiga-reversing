#ifndef M68K_SOURCE_EXPR_H
#define M68K_SOURCE_EXPR_H

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

typedef int (*M68kSourceExprLookupFn)(const char *name, int *out_defined, int *out_is_constant, uint32_t *out_value,
    size_t *out_symbol_id, size_t *out_section_index, void *user_data);

int m68k_source_parse_linear_expression(const char *text, int constants_only, M68kSourceExprLookupFn lookup,
    void *user_data, M68kSourceLinearExpr *out_expr);

int m68k_source_evaluate_linear_expression(const M68kSourceLinearExpr *expr, uint32_t *out_value, int *out_is_reloc,
    size_t *out_target_section);

#endif
