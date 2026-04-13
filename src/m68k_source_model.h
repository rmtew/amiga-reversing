#ifndef M68K_SOURCE_MODEL_H
#define M68K_SOURCE_MODEL_H

#include "m68k_ir.h"
#include "m68k_source_data.h"

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
    ASM_SOURCE_STMT_END = 6
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
        } section;
        struct {
            char name[M68K_SOURCE_MAX_LABEL_NAME];
        } label;
        AsmSourceInstructionStmt instruction;
        AsmSourceDataStmt data;
    } u;
} AsmSourceStmt;

typedef struct AsmSectionDef {
    char name[64];
    M68kSectionKind kind;
} AsmSectionDef;

typedef struct AsmSourceFile {
    AsmSectionDef *sections;
    size_t section_count;
    size_t section_capacity;
    AsmSourceSymbol *symbols;
    size_t symbol_count;
    size_t symbol_capacity;
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
} AsmSourceFile;

int m68k_source_model_find_symbol_index(const AsmSourceFile *source, const char *name, size_t *out_index);
int m68k_source_model_lookup_symbol(const char *name, uint32_t *out_value, size_t *out_section_index, int *out_defined,
    void *user_data);
int m68k_source_model_expr_lookup_symbol(const char *name, int *out_defined, int *out_is_constant, uint32_t *out_value,
    size_t *out_symbol_id, size_t *out_section_index, void *user_data);
int m68k_source_model_append_section(AsmSourceFile *source, const char *name, M68kSectionKind kind, size_t *out_index);
int m68k_source_model_ensure_symbol(AsmSourceFile *source, const char *name, AsmSourceSymbolKind kind, size_t *out_index);
int m68k_source_model_set_constant(AsmSourceFile *source, const char *name, uint32_t value, int allow_redefine);
int m68k_source_model_set_label_value(AsmSourceFile *source, const char *name, size_t section_index, uint32_t value);
int m68k_source_model_append_statement(AsmSourceFile *source, AsmSourceStmtKind kind, size_t line_number, AsmSourceStmt **out_stmt);
int m68k_source_model_append_data_item(AsmSourceDataStmt *data_stmt, const AsmDataItem *item);
void m68k_source_model_free(AsmSourceFile *source);

#endif
