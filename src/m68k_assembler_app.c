#include "m68k_assembler_app.h"
#include "m68k_assembler_lib.h"
#include "m68k_backend.h"
#include "m68k_instruction_spec.h"
#include "m68k_ir.h"
#include "m68k_ir_codec.h"
#include "m68k_plain_parse.h"
#include "m68k_simple_source.h"
#include "m68k_source_ir_render.h"
#include "m68k_source_model.h"
#include "m68k_source_pipeline.h"
#include "platform_atari_st.h"
#include "platform_common.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_CASE_BYTES 64

static int simple_source_parse_instruction_callback(const char *line_text, InstructionSpec *out_instruction,
    int allow_label_symbols, uint8_t target_cpu) {
  (void)allow_label_symbols;
  return m68k_plain_parse_instruction_to_spec(line_text, target_cpu, out_instruction);
}

static int assemble_line_text_for_cpu(const char *line_text, uint8_t target_cpu, uint8_t *out_bytes, size_t max_bytes,
    size_t *out_byte_count, M68kDiagSink diagnostics) {
  M68kInstructionIR instruction;
  M68kIrEncodeResult encoded;
  instruction = m68k_plain_parse_instruction_to_ir(line_text, target_cpu, diagnostics);
  if (m68k_diag_has_errors(diagnostics.list)) {
    if (out_byte_count != NULL) *out_byte_count = 0U;
    return -1;
  }
  encoded = m68k_ir_encode_one(&instruction, out_bytes, max_bytes, diagnostics);
  if (m68k_diag_has_errors(diagnostics.list)) {
    if (out_byte_count != NULL) *out_byte_count = 0U;
    return -1;
  }
  if (out_byte_count != NULL) *out_byte_count = encoded.byte_count;
  return 0;
}

int m68k_assemble_line_to_stdout(const char *line_text, uint8_t target_cpu) {
  unsigned char bytes[MAX_CASE_BYTES];
  size_t size = 0;
  size_t index;
  M68kDiagList diagnostics;
  m68k_diag_list_reset(&diagnostics);
  if (assemble_line_text_for_cpu(line_text, target_cpu, bytes, sizeof(bytes), &size,
      m68k_diag_sink(&diagnostics)) != 0) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&diagnostics)[0] != '\0'
      ? m68k_diag_first_message(&diagnostics) : "unable to parse line");
    return 1;
  }
  for (index = 0; index < size; ++index) printf("%02x", bytes[index]);
  printf("\n");
  return 0;
}

int m68k_assemble_file_to_binary(const char *input_path, const char *output_path, uint8_t target_cpu) {
  return m68k_simple_source_assemble_file_to_binary(input_path, output_path, target_cpu,
    simple_source_parse_instruction_callback);
}

static int assemble_platform_source_to_object(const char *input_path, const char *include_dir, uint8_t target_cpu,
    int enable_vasm_compat_rewrites, M68kPlatformBackendKind platform_backend_kind,
    M68kObject *out_object, M68kDiagSink diagnostics) {
  AsmSourceFile source;
  size_t index;
  memset(&source, 0, sizeof(source));
  snprintf(source.include_dir, sizeof(source.include_dir), "%s", include_dir);
  source.target_cpu = target_cpu;
  source.platform_backend_kind = platform_backend_kind;
  source.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  source.enable_vasm_compat_rewrites = enable_vasm_compat_rewrites;
  if (!m68k_source_pipeline_parse_and_layout(&source, input_path, diagnostics)) {
    m68k_source_model_free(&source);
    return 0;
  }
  if (getenv("M68K_ASM_DUMP_LABELS") != NULL) {
    for (index = 0; index < source.symbol_count; ++index) {
      if (source.symbols[index].defined && source.symbols[index].kind == ASM_SOURCE_SYMBOL_LABEL) {
        fprintf(stderr, "%08x %s\n", (unsigned)source.symbols[index].value, source.symbols[index].name);
      }
    }
  }
  if (!m68k_source_pipeline_emit_object(&source, out_object, diagnostics)) {
    m68k_source_model_free(&source);
    return 0;
  }
  if (source.has_atari_st_program_flags && m68k_atari_st_set_program_flags(out_object, source.atari_st_program_flags) != 0) {
    m68k_source_model_free(&source);
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
      "failed setting Atari ST program flags");
    return 0;
  }
  m68k_source_model_free(&source);
  return 1;
}

int m68k_assemble_platform_file_to_output(const char *backend_name, const char *include_dir, const char *input_path,
    const char *output_path, uint8_t target_cpu, int enable_vasm_compat_rewrites) {
  const M68kBackend *backend = NULL;
  M68kObject object;
  M68kDiagList diagnostics;
  M68kPlatformBackendKind platform_backend_kind = M68K_PLATFORM_BACKEND_UNKNOWN;
  m68k_diag_list_reset(&diagnostics);
  backend = m68k_backend_by_name(backend_name);
  if (backend == NULL || backend->write_file == NULL) {
    fprintf(stderr, "backend unavailable: %s\n", backend_name);
    return 2;
  }
  if (strcmp(backend_name, M68K_BACKEND_AMIGA_HUNK.name) == 0)
    platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  else if (strcmp(backend_name, M68K_BACKEND_ATARI_ST.name) == 0)
    platform_backend_kind = M68K_PLATFORM_BACKEND_ATARI_ST;
  if (!assemble_platform_source_to_object(input_path, include_dir, target_cpu,
      enable_vasm_compat_rewrites, platform_backend_kind, &object, m68k_diag_sink(&diagnostics))) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&diagnostics));
    return 1;
  }
  m68k_diag_list_reset(&diagnostics);
  if (backend->write_file(output_path, &object, m68k_diag_sink(&diagnostics)) != 0) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&diagnostics));
    m68k_object_destroy(&object);
    return 1;
  }
  m68k_object_destroy(&object);
  return 0;
}

int m68k_render_source_file_to_stdout(const char *input_path, const char *include_dir, uint8_t target_cpu,
    int enable_vasm_compat_rewrites, const M68kRenderPolicy *policy) {
  M68kSourceIrParseResult parsed;
  M68kSourceIrRenderResult rendered;
  M68kSourceFileIR source_file;
  parsed = m68k_source_ir_parse_file(input_path, include_dir, target_cpu, enable_vasm_compat_rewrites);
  if (m68k_diag_has_errors(&parsed.diagnostics)) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&parsed.diagnostics));
    return 1;
  }
  source_file = parsed.source_file;
  if (source_file.section_count == 0U) {
    fprintf(stderr, "empty source ir\n");
    m68k_ir_source_file_destroy(&source_file);
    return 1;
  }
  rendered = m68k_source_ir_render_with_policy(&source_file, policy);
  m68k_ir_source_file_destroy(&source_file);
  if (m68k_diag_has_errors(&rendered.diagnostics)) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&rendered.diagnostics));
    return 1;
  }
  if (rendered.text == NULL || rendered.text[0] == '\0') {
    fprintf(stderr, "empty rendered source ir\n");
    free(rendered.text);
    return 1;
  }
  puts(rendered.text);
  free(rendered.text);
  return 0;
}
