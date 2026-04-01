#ifndef M68K_SOURCE_DATA_H
#define M68K_SOURCE_DATA_H

#include <stddef.h>
#include <stdint.h>

typedef enum AsmDataItemKind {
    ASM_DATA_ITEM_EXPR = 1,
    ASM_DATA_ITEM_STRING = 2
} AsmDataItemKind;

typedef struct AsmDataItem {
    AsmDataItemKind kind;
    char expr[128];
    uint8_t *bytes;
    size_t byte_count;
} AsmDataItem;

typedef struct AsmSourceDataStmt {
    uint8_t width_bytes;
    AsmDataItem *items;
    size_t item_count;
    size_t item_capacity;
} AsmSourceDataStmt;

typedef int (*M68kSourceDataParseConstantFn)(const char *text, uint32_t *out_value, void *user_data);
typedef int (*M68kSourceDataAppendItemFn)(AsmSourceDataStmt *data_stmt, const AsmDataItem *item, void *user_data);

typedef struct M68kSourceDataParseContext {
    void *user_data;
    M68kSourceDataParseConstantFn parse_constant;
    M68kSourceDataAppendItemFn append_item;
} M68kSourceDataParseContext;

int m68k_source_parse_data_statement(const char *directive, char *rest, AsmSourceDataStmt *out_data,
    const M68kSourceDataParseContext *context);
int m68k_source_parse_dcb_statement(const char *directive, char *rest, AsmSourceDataStmt *out_data,
    const M68kSourceDataParseContext *context);

#endif
