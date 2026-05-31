#ifndef M68K_SOURCE_IR_RENDER_H
#define M68K_SOURCE_IR_RENDER_H

#include "m68k_diagnostics.h"
#include "m68k_ir.h"
#include "util_arena.h"

#include <stddef.h>
#include <stdint.h>

typedef struct M68kSourceRenderLineProvenance {
  uint32_t line_index;
  uint32_t source_offset;
  uint32_t source_size;
  uint8_t has_source_range;
  uint8_t reserved[3];
} M68kSourceRenderLineProvenance;

int m68k_source_ir_render_text_with_policy(const M68kSourceFileIR *source_file, const M68kRenderPolicy *policy,
    char **out_text, M68kDiagSink diagnostics);
int m68k_source_ir_render_statement_text_with_policy(const M68kStatementIR *stmt, const M68kRenderPolicy *policy,
    char **out_text, M68kDiagSink diagnostics);
int m68k_source_ir_render_statement_text_with_policy_arena(const M68kStatementIR *stmt,
    const M68kRenderPolicy *policy, Arena *arena, char **out_text, M68kDiagSink diagnostics);
int m68k_source_ir_render_statement_text_with_policy_arena_detail(const M68kStatementIR *stmt,
    const M68kRenderPolicy *policy, Arena *arena, char **out_text,
    M68kSourceRenderLineProvenance *line_provenance, size_t line_provenance_capacity,
    size_t *out_line_provenance_count, M68kDiagSink diagnostics);

#endif
