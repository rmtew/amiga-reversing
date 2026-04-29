#ifndef M68K_SOURCE_FILE_EMIT_H
#define M68K_SOURCE_FILE_EMIT_H

#include "m68k_diagnostics.h"
#include "m68k_object.h"
#include "m68k_source_expr.h"
#include "m68k_source_instruction_resolve.h"
#include "m68k_source_model.h"

#include <stddef.h>
#include <stdint.h>

typedef int (*M68kSourceFileSetLabelFn)(AsmSourceFile *source, const char *name, size_t section_index, uint32_t value,
    uint8_t is_absolute);
typedef M68kSourceModelIndexResult (*M68kSourceFileLookupSymbolIndexFn)(const AsmSourceFile *source,
    const char *name);
typedef M68kSourceResolvedInstruction (*M68kSourceFileResolveInstructionFn)(const AsmSourceFile *source,
    const AsmSourceStmt *stmt, uint32_t instruction_offset, int allow_undefined, M68kDiagSink diagnostics);

typedef struct M68kSourceFileEmitContext {
    M68kSourceFileSetLabelFn set_label_value;
    M68kSourceFileLookupSymbolIndexFn find_symbol_index;
    M68kSourceFileResolveInstructionFn resolve_instruction;
    M68kSourceExprLookupFn expr_lookup_symbol;
} M68kSourceFileEmitContext;

int m68k_source_file_layout(AsmSourceFile *source, const M68kSourceFileEmitContext *context,
    M68kDiagSink diagnostics);
int m68k_source_file_emit_object(const AsmSourceFile *source, const M68kSourceFileEmitContext *context,
    M68kObject *out_object, M68kDiagSink diagnostics);
int m68k_source_file_build_ir(const AsmSourceFile *source, M68kSourceExprLookupFn expr_lookup_symbol,
    void *expr_lookup_user_data, M68kSourceFileIR *out_source_file, M68kDiagSink diagnostics);

#endif
