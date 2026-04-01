#ifndef M68K_SOURCE_FILE_EMIT_H
#define M68K_SOURCE_FILE_EMIT_H

#include "m68k_object.h"
#include "m68k_source_expr.h"
#include "m68k_source_model.h"

#include <stddef.h>
#include <stdint.h>

typedef int (*M68kSourceFileSetLabelFn)(AsmSourceFile *source, const char *name, size_t section_index, uint32_t value);
typedef int (*M68kSourceFileLookupSymbolIndexFn)(const AsmSourceFile *source, const char *name, size_t *out_index);
typedef int (*M68kSourceFileResolveInstructionFn)(const AsmSourceFile *source, const AsmSourceStmt *stmt,
    const M68kAsmFormDef **out_form, M68kInstructionIR *out_instruction, uint32_t instruction_offset,
    int *out_abs_fixup_operands, size_t *out_abs_fixup_count, int allow_undefined, char *out_error, size_t out_error_size);

typedef struct M68kSourceFileEmitContext {
    M68kSourceFileSetLabelFn set_label_value;
    M68kSourceFileLookupSymbolIndexFn find_symbol_index;
    M68kSourceFileResolveInstructionFn resolve_instruction;
    M68kSourceExprLookupFn expr_lookup_symbol;
} M68kSourceFileEmitContext;

int m68k_source_file_layout(AsmSourceFile *source, const M68kSourceFileEmitContext *context,
    char *out_error, size_t out_error_size);
int m68k_source_file_emit_object(const AsmSourceFile *source, const M68kSourceFileEmitContext *context,
    M68kObject *out_object, char *out_error, size_t out_error_size);
int m68k_source_file_build_ir(const AsmSourceFile *source, M68kSourceExprLookupFn expr_lookup_symbol,
    void *expr_lookup_user_data, M68kSourceFileIR *out_source_file, char *out_error, size_t out_error_size);

#endif
