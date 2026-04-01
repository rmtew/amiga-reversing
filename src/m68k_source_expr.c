#include "m68k_source_expr.h"

#include "m68k_parse_util.h"

#include <ctype.h>
#include <string.h>

int m68k_source_parse_linear_expression(const char *text, int constants_only, M68kSourceExprLookupFn lookup,
    void *user_data, M68kSourceLinearExpr *out_expr) {
    const char *cursor = text;
    int sign = 1;
    memset(out_expr, 0, sizeof(*out_expr));
    out_expr->valid = 1;
    while (1) {
        char token[128];
        size_t token_length = 0;
        uint32_t value = 0;
        while (*cursor != '\0' && isspace((unsigned char)*cursor)) ++cursor;
        if (*cursor == '+') {
            sign = 1;
            ++cursor;
            continue;
        }
        if (*cursor == '-') {
            sign = -1;
            ++cursor;
            continue;
        }
        if (*cursor == '\0') break;
        while (cursor[token_length] != '\0'
            && cursor[token_length] != '+'
            && cursor[token_length] != '-'
            && !isspace((unsigned char)cursor[token_length])) {
            ++token_length;
        }
        if (token_length == 0U || token_length >= sizeof(token)) return 0;
        memcpy(token, cursor, token_length);
        token[token_length] = '\0';
        cursor += token_length;
        if (m68k_parse_number_u32(token, &value)) {
            out_expr->constant += sign * (int32_t)value;
        } else {
            int defined = 0;
            int is_constant = 0;
            size_t symbol_id = (size_t)-1;
            size_t section_index = (size_t)-1;
            if (!lookup(token, &defined, &is_constant, &value, &symbol_id, &section_index, user_data)) return 0;
            if (!defined) return 0;
            if (is_constant) {
                out_expr->constant += sign * (int32_t)value;
            } else {
                if (constants_only || out_expr->symbol_count >= 2U) return 0;
                out_expr->symbol_ids[out_expr->symbol_count] = symbol_id;
                out_expr->section_indices[out_expr->symbol_count] = section_index;
                out_expr->symbol_signs[out_expr->symbol_count] = sign;
                out_expr->constant += sign * (int32_t)value;
                out_expr->symbol_count += 1U;
            }
        }
        sign = 1;
    }
    return 1;
}

int m68k_source_evaluate_linear_expression(const M68kSourceLinearExpr *expr, uint32_t *out_value, int *out_is_reloc,
    size_t *out_target_section) {
    int32_t value = expr->constant;
    *out_is_reloc = 0;
    *out_target_section = (size_t)-1;
    if (!expr->valid) return 0;
    if (expr->symbol_count == 0U) {
        *out_value = (uint32_t)value;
        return 1;
    }
    if (expr->symbol_count == 1U && expr->symbol_signs[0] == 1) {
        *out_value = (uint32_t)value;
        *out_is_reloc = 1;
        *out_target_section = expr->section_indices[0];
        return 1;
    }
    if (expr->symbol_count == 2U && expr->symbol_signs[0] == 1 && expr->symbol_signs[1] == -1) {
        if (expr->section_indices[0] != expr->section_indices[1]) return 0;
        *out_value = (uint32_t)value;
        return 1;
    }
    return 0;
}
