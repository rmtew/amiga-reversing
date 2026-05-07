#include "m68k_assembler_lib.h"

#include "m68k_instruction_spec.h"
#include "m68k_ir.h"
#include "m68k_ir_codec.h"
#include "m68k_parse_util.h"
#include "m68k_plain_parse.h"
#include "m68k_simple_source.h"
#include "m68k_symbolic_parse.h"

#include "platform_common.h"

#include <stdio.h>
#include <string.h>


static M68kSourceLookupResult simple_source_lookup_symbol(const char *name, int require_constant, void *user_data) {
  M68kSourceLookupResult result = {0};
  (void)name; (void)require_constant; (void)user_data;
  return result;
}

static int simple_source_is_symbol_name(const char *text, void *user_data) {
  (void)user_data;
  return m68k_is_symbol_name(text);
}

static int simple_source_parse_instruction_callback(const char *line_text, InstructionSpec *out_instruction,
    int allow_label_symbols, uint8_t target_cpu) {
  if (allow_label_symbols) {
    M68kSymbolicParseContext context;
    context.target_cpu = target_cpu;
    context.user_data = NULL;
    context.lookup_symbol = simple_source_lookup_symbol;
    context.is_symbol_name = simple_source_is_symbol_name;
    if (m68k_parse_instruction_with_symbol_fallback_spec(&context, line_text, out_instruction, NULL, 0U)) return 1;
  }
  return m68k_plain_parse_instruction_to_spec(line_text, target_cpu, out_instruction);
}

static M68kAssembleResult assemble_line_text_for_cpu(const char *line_text, uint8_t target_cpu, uint8_t *out_bytes,
    size_t max_bytes) {
  M68kAssembleResult result;
  M68kInstructionIR instruction;
  M68kIrEncodeResult encoded;
  memset(&result, 0, sizeof(result));
  instruction = m68k_plain_parse_instruction_to_ir(line_text, target_cpu, m68k_diag_sink(&result.diagnostics));
  if (m68k_diag_has_errors(&result.diagnostics)) return result;
  encoded = m68k_ir_encode_one(&instruction, out_bytes, max_bytes, m68k_diag_sink(&result.diagnostics));
  result.byte_count = encoded.byte_count;
  return result;
}

static M68kAssembleResult assemble_source_text_for_cpu(const char *source_text, uint8_t target_cpu,
    uint8_t *out_bytes, size_t max_bytes) {
  M68kAssembleResult result;
  M68kSimpleSourceAssembleResult assembled;
  memset(&result, 0, sizeof(result));
  assembled = m68k_simple_source_assemble_text(source_text, target_cpu, out_bytes, max_bytes,
    m68k_diag_sink(&result.diagnostics), simple_source_parse_instruction_callback);
  result.byte_count = assembled.byte_count;
  return result;
}

M68kAssembleResult m68k_assemble(const char *text, const M68kAsmOptions *options, uint8_t *out_bytes,
    size_t max_bytes) {
  M68kAssembleResult result;
  memset(&result, 0, sizeof(result));
  if (options == NULL) {
    m68k_diag_add(m68k_diag_sink(&result.diagnostics), M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_BAD_ARGUMENT,
      "assembler options are null");
    return result;
  }
  if (options->input_mode == M68K_ASM_INPUT_LINE)
    return assemble_line_text_for_cpu(text, options->target_cpu, out_bytes, max_bytes);
  if (options->input_mode == M68K_ASM_INPUT_SOURCE)
    return assemble_source_text_for_cpu(text, options->target_cpu, out_bytes, max_bytes);
  m68k_diag_add(m68k_diag_sink(&result.diagnostics), M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_BAD_ARGUMENT,
    "unknown assembler input mode");
  return result;
}


