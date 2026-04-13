#include "m68k_source_pipeline.h"

#include "m68k_source_file_emit.h"
#include "m68k_source_file_parse.h"
#include "m68k_source_instruction_resolve.h"

#include <string.h>

static int resolve_instruction_symbol_operands(const AsmSourceFile *source, const AsmSourceStmt *stmt,
    const M68kAsmFormDef **out_form, M68kInstructionIR *out_instruction, uint32_t instruction_offset,
    int *out_abs_fixup_operands, size_t *out_abs_fixup_count, int allow_undefined,
    char *out_error, size_t out_error_size) {
  M68kSourceInstructionResolveContext context;
  memset(&context, 0, sizeof(context));
  context.user_data = (void *)source;
  context.enable_vasm_compat_rewrites = source->enable_vasm_compat_rewrites;
  context.lookup_symbol = m68k_source_model_lookup_symbol;
  return m68k_source_resolve_instruction_operands(&context,
    stmt->section_index,
    stmt->line_number,
    stmt->u.instruction.requested_size_suffix,
    instruction_offset,
    allow_undefined,
    &stmt->u.instruction.parsed_ir,
    out_form,
    out_instruction,
    out_abs_fixup_operands,
    out_abs_fixup_count,
    out_error,
    out_error_size);
}

static void init_source_file_emit_context(M68kSourceFileEmitContext *context) {
  memset(context, 0, sizeof(*context));
  context->set_label_value = m68k_source_model_set_label_value;
  context->find_symbol_index = m68k_source_model_find_symbol_index;
  context->resolve_instruction = resolve_instruction_symbol_operands;
  context->expr_lookup_symbol = m68k_source_model_expr_lookup_symbol;
}

int m68k_source_pipeline_parse_and_layout(AsmSourceFile *source, const char *path, char *out_error,
    size_t out_error_size) {
  M68kSourceFileEmitContext emit_context;
  init_source_file_emit_context(&emit_context);
  return m68k_source_file_parse(source, path, out_error, out_error_size)
    && m68k_source_file_layout(source, &emit_context, out_error, out_error_size);
}

int m68k_source_pipeline_emit_object(AsmSourceFile *source, M68kObject *out_object, char *out_error,
    size_t out_error_size) {
  M68kSourceFileEmitContext emit_context;
  init_source_file_emit_context(&emit_context);
  return m68k_source_file_emit_object(source, &emit_context, out_object, out_error, out_error_size);
}

int m68k_source_pipeline_build_ir(AsmSourceFile *source, M68kSourceFileIR *out_source_file, char *out_error,
    size_t out_error_size) {
  return m68k_source_file_build_ir(source, m68k_source_model_expr_lookup_symbol, source, out_source_file,
    out_error, out_error_size);
}
