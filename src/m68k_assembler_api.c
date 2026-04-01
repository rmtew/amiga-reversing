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


static int simple_source_lookup_symbol(const char *name, uint32_t *out_value, int require_constant, void *user_data) {
  (void)name; (void)out_value; (void)require_constant; (void)user_data;
  return 0;
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
    context.enable_vasm_compat_rewrites = 0;
    context.user_data = NULL;
    context.lookup_symbol = simple_source_lookup_symbol;
    context.is_symbol_name = simple_source_is_symbol_name;
    if (m68k_parse_instruction_with_symbol_fallback_spec(&context, line_text, out_instruction, NULL, 0U)) return 1;
  }
  return m68k_plain_parse_instruction_to_spec(line_text, target_cpu, out_instruction);
}

static int assemble_line_text_for_cpu(const char *line_text, uint8_t target_cpu, uint8_t *out_bytes, size_t max_bytes,
    size_t *out_byte_count, char *out_error, size_t out_error_size) {
  M68kInstructionIR instruction;
  size_t byte_count = 0;
  m68k_ir_instruction_init(&instruction);
  if (m68k_plain_parse_instruction_to_ir(line_text, target_cpu, &instruction, out_error, out_error_size) != 0) {
    if (out_byte_count != NULL) *out_byte_count = 0U;
    return -1;
  }
  if (m68k_ir_encode_one(&instruction, out_bytes, max_bytes, &byte_count, out_error, out_error_size) != 0) {
    if (out_byte_count != NULL) *out_byte_count = 0U;
    return -1;
  }
  m68k_platform_set_error(out_error, out_error_size, "");
  if (out_byte_count != NULL) *out_byte_count = byte_count;
  return 0;
}

static int assemble_source_text_for_cpu(const char *source_text, uint8_t target_cpu, uint8_t *out_bytes,
    size_t max_bytes, size_t *out_byte_count, char *out_error, size_t out_error_size) {
  return m68k_simple_source_assemble_text(source_text, target_cpu, out_bytes, max_bytes, out_byte_count, out_error,
    out_error_size, simple_source_parse_instruction_callback);
}

int m68k_assemble(const char *text, const M68kAsmOptions *options, uint8_t *out_bytes, size_t max_bytes,
    size_t *out_byte_count, char *out_error, size_t out_error_size) {
  if (options == NULL) {
    m68k_platform_set_error(out_error, out_error_size, "assembler options are null");
    if (out_byte_count != NULL) *out_byte_count = 0U;
    return -1;
  }
  if (options->input_mode == M68K_ASM_INPUT_LINE)
    return assemble_line_text_for_cpu(text, options->target_cpu, out_bytes, max_bytes, out_byte_count, out_error,
      out_error_size);
  if (options->input_mode == M68K_ASM_INPUT_SOURCE)
    return assemble_source_text_for_cpu(text, options->target_cpu, out_bytes, max_bytes, out_byte_count, out_error,
      out_error_size);
  m68k_platform_set_error(out_error, out_error_size, "unknown assembler input mode");
  if (out_byte_count != NULL) *out_byte_count = 0U;
  return -1;
}


