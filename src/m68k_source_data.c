#include "m68k_source_data.h"
#include "m68k_source_text_util.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int parse_data_item_text_local(const char *text, AsmDataItem *out_item) {
    size_t length = strlen(text);
    memset(out_item, 0, sizeof(*out_item));
    if (length >= 2U && ((text[0] == '"' && text[length - 1U] == '"') || (text[0] == '\'' && text[length - 1U] == '\''))) {
        out_item->kind = ASM_DATA_ITEM_STRING;
        out_item->byte_count = length - 2U;
        out_item->bytes = (uint8_t *)malloc(out_item->byte_count == 0U ? 1U : out_item->byte_count);
        if (out_item->bytes == NULL) return 0;
        if (out_item->byte_count != 0U) memcpy(out_item->bytes, text + 1, out_item->byte_count);
        return 1;
    }
    out_item->kind = ASM_DATA_ITEM_EXPR;
    if (length >= sizeof(out_item->expr)) return 0;
    snprintf(out_item->expr, sizeof(out_item->expr), "%s", text);
    return 1;
}

int m68k_source_parse_data_statement(const char *directive, char *rest, AsmSourceDataStmt *out_data,
    const M68kSourceDataParseContext *context) {
    char buffer[256];
    char *items[64];
    size_t count = 0;
    size_t index;
    out_data->width_bytes = (_stricmp(directive, "DC.B") == 0) ? 1U : (_stricmp(directive, "DC.W") == 0) ? 2U : 4U;
    snprintf(buffer, sizeof(buffer), "%s", rest);
    if (!m68k_split_operands_in_place(buffer, items, 64U, &count)) return 0;
    for (index = 0; index < count; ++index) {
        AsmDataItem item;
        if (!parse_data_item_text_local(items[index], &item)) return 0;
        if (!context->append_item(out_data, &item, context->user_data)) return 0;
    }
    return 1;
}

int m68k_source_parse_dcb_statement(const char *directive, char *rest, AsmSourceDataStmt *out_data,
    const M68kSourceDataParseContext *context) {
    char buffer[256];
    char *parts[2];
    size_t count = 0;
    uint32_t repeat_count = 0;
    uint32_t index = 0;
    AsmDataItem item;
    out_data->width_bytes = (_stricmp(directive, "DCB.B") == 0) ? 1U : (_stricmp(directive, "DCB.W") == 0) ? 2U : 4U;
    snprintf(buffer, sizeof(buffer), "%s", rest);
    count = m68k_split_delimited_in_place(buffer, ',', parts,
                                          sizeof(parts) / sizeof(parts[0]));
    if (count != 2U) return 0;
    if (!context->parse_constant(m68k_trim_in_place(parts[0]), &repeat_count,
                                 context->user_data)) {
        return 0;
    }
    if (!parse_data_item_text_local(m68k_trim_in_place(parts[1]), &item)) return 0;
    for (index = 0; index < repeat_count; ++index) {
        AsmDataItem copy = item;
        if (item.kind == ASM_DATA_ITEM_STRING && item.byte_count != 0U) {
            copy.bytes = (uint8_t *)malloc(item.byte_count);
            if (copy.bytes == NULL) {
                free(item.bytes);
                return 0;
            }
            memcpy(copy.bytes, item.bytes, item.byte_count);
        }
        if (!context->append_item(out_data, &copy, context->user_data)) {
            free(copy.bytes);
            free(item.bytes);
            return 0;
        }
    }
    free(item.bytes);
    return 1;
}
