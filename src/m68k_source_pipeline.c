#include "m68k_source_pipeline.h"

#include "m68k_source_file_emit.h"
#include "m68k_source_file_parse.h"
#include "m68k_source_instruction_resolve.h"

#include <string.h>

static M68kSourceResolvedInstruction resolve_instruction_symbol_operands(const AsmSourceFile *source,
    const AsmSourceStmt *stmt, uint32_t instruction_offset, int allow_undefined, M68kDiagSink diagnostics) {
  M68kSourceInstructionResolveContext context;
  memset(&context, 0, sizeof(context));
  context.user_data = (void *)source;
  context.lookup_symbol = m68k_source_model_lookup_symbol;
  return m68k_source_resolve_instruction_operands(&context,
    stmt->line_number,
    stmt->u.instruction.requested_size_suffix,
    instruction_offset,
    allow_undefined,
    &stmt->u.instruction.parsed_ir,
    diagnostics);
}

static void init_source_file_emit_context(M68kSourceFileEmitContext *context) {
  memset(context, 0, sizeof(*context));
  context->set_label_value = m68k_source_model_set_label_value;
  context->find_symbol_index = m68k_source_model_find_symbol_index;
  context->resolve_instruction = resolve_instruction_symbol_operands;
  context->expr_lookup_symbol = m68k_source_model_expr_lookup_symbol;
}

int m68k_source_pipeline_parse_and_layout(AsmSourceFile *source, const char *path, M68kDiagSink diagnostics) {
  M68kSourceFileEmitContext emit_context;
  init_source_file_emit_context(&emit_context);
  return m68k_source_file_parse(source, path, diagnostics)
    && m68k_source_file_layout(source, &emit_context, diagnostics);
}

int m68k_source_pipeline_parse_text_and_layout(AsmSourceFile *source, const char *source_text,
    M68kDiagSink diagnostics) {
  M68kSourceFileEmitContext emit_context;
  init_source_file_emit_context(&emit_context);
  return m68k_source_file_parse_text(source, source_text, diagnostics)
    && m68k_source_file_layout(source, &emit_context, diagnostics);
}

int m68k_source_pipeline_emit_object(AsmSourceFile *source, M68kObject *out_object, M68kDiagSink diagnostics) {
  M68kSourceFileEmitContext emit_context;
  init_source_file_emit_context(&emit_context);
  return m68k_source_file_emit_object(source, &emit_context, out_object, diagnostics);
}

int m68k_source_pipeline_build_ir(AsmSourceFile *source, M68kSourceFileIR *out_source_file,
    M68kDiagSink diagnostics) {
  return m68k_source_file_build_ir(source, m68k_source_model_expr_lookup_symbol, source, out_source_file,
    diagnostics);
}
