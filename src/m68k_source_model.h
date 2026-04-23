#ifndef M68K_SOURCE_MODEL_H
#define M68K_SOURCE_MODEL_H

#include "m68k_ir.h"
#include "m68k_source_data.h"
#include "m68k_source_lookup.h"

#include <stddef.h>
#include <stdint.h>

#define M68K_SOURCE_MAX_LABEL_NAME 64

typedef enum AsmSourceSymbolKind {
    ASM_SOURCE_SYMBOL_CONSTANT = 1,
    ASM_SOURCE_SYMBOL_LABEL = 2
} AsmSourceSymbolKind;

typedef struct AsmSourceSymbol {
    char name[M68K_SOURCE_MAX_LABEL_NAME];
    AsmSourceSymbolKind kind;
    int defined;
    size_t section_index;
    uint32_t value;
} AsmSourceSymbol;

typedef enum AsmSourceStmtKind {
    ASM_SOURCE_STMT_SECTION = 1,
    ASM_SOURCE_STMT_LABEL = 2,
    ASM_SOURCE_STMT_INSTRUCTION = 3,
    ASM_SOURCE_STMT_DATA = 4,
    ASM_SOURCE_STMT_EVEN = 5,
    ASM_SOURCE_STMT_END = 6,
    ASM_SOURCE_STMT_RESERVE = 7
} AsmSourceStmtKind;

typedef struct AsmSourceInstructionStmt {
    M68kInstructionIR parsed_ir;
    char requested_size_suffix;
} AsmSourceInstructionStmt;

typedef struct AsmSourceStmt {
    AsmSourceStmtKind kind;
    size_t line_number;
    size_t section_index;
    uint32_t offset;
    uint32_t size;
    union {
        struct {
            char name[64];
            M68kSectionKind kind;
            uint8_t platform_mem_type;
            uint32_t platform_mem_attrs;
            uint8_t has_alloc_size;
            uint32_t alloc_size;
        } section;
        struct {
            char name[M68K_SOURCE_MAX_LABEL_NAME];
        } label;
        AsmSourceInstructionStmt instruction;
        AsmSourceDataStmt data;
        uint32_t reserve_size;
    } u;
} AsmSourceStmt;

typedef struct AsmSectionDef {
    char name[64];
    M68kSectionKind kind;
    uint8_t platform_mem_type;
    uint32_t platform_mem_attrs;
    uint8_t has_alloc_size;
    uint32_t alloc_size;
} AsmSectionDef;

typedef struct AsmSourceFile {
    AsmSectionDef *sections;
    size_t section_count;
    size_t section_capacity;
    AsmSourceSymbol *symbols;
    size_t symbol_count;
    size_t symbol_capacity;
    size_t *symbol_index_slots;
    size_t symbol_index_capacity;
    AsmSourceStmt *statements;
    size_t statement_count;
    size_t statement_capacity;
    char include_dir[512];
    uint8_t target_cpu;
    M68kPlatformBackendKind platform_backend_kind;
    M68kPlatformFileKind file_kind;
    int enable_vasm_compat_rewrites;
    int has_atari_st_program_flags;
    uint32_t atari_st_program_flags;
    int has_atari_st_relocation_flag;
    uint32_t atari_st_relocation_flag;
    int has_atari_st_symbol_table;
    uint32_t atari_st_symbol_table_type;
    uint8_t *atari_st_symbol_table_data;
    uint32_t atari_st_symbol_table_size;
    int has_atari_st_relocation_stream;
    uint8_t *atari_st_relocation_stream_data;
    uint32_t atari_st_relocation_stream_size;
} AsmSourceFile;

typedef struct M68kSourceModelIndexResult {
    uint8_t ok;
    size_t index;
} M68kSourceModelIndexResult;

M68kSourceModelIndexResult m68k_source_model_find_symbol_index(const AsmSourceFile *source, const char *name);
M68kSourceLookupResult m68k_source_model_lookup_symbol(const char *name, void *user_data);
M68kSourceLookupResult m68k_source_model_expr_lookup_symbol(const char *name, void *user_data);
M68kSourceModelIndexResult m68k_source_model_append_section(AsmSourceFile *source, const char *name,
    M68kSectionKind kind, uint8_t platform_mem_type, uint32_t platform_mem_attrs, uint8_t has_alloc_size,
    uint32_t alloc_size);
M68kSourceModelIndexResult m68k_source_model_ensure_symbol(AsmSourceFile *source, const char *name,
    AsmSourceSymbolKind kind);
int m68k_source_model_set_constant(AsmSourceFile *source, const char *name, uint32_t value, int allow_redefine);
int m68k_source_model_set_label_value(AsmSourceFile *source, const char *name, size_t section_index, uint32_t value);
M68kSourceModelIndexResult m68k_source_model_append_statement(AsmSourceFile *source, AsmSourceStmtKind kind,
    size_t line_number);
int m68k_source_model_append_data_item(AsmSourceDataStmt *data_stmt, const AsmDataItem *item);
void m68k_source_model_free(AsmSourceFile *source);

#endif
