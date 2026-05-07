/* Source IR API surface for parse/render/free entrypoints. */
#include "m68k_assembler_lib.h"
#include "m68k_source_ir_render.h"
#include "m68k_source_model.h"
#include "m68k_source_pipeline.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

M68K_ASM_EXPORT M68kSourceIrParseResult m68k_source_ir_parse_file(const char *path, const char *include_dir,
    uint8_t target_cpu) {
  M68kSourceIrParseResult result;
  AsmSourceFile source;
  M68kDiagList diagnostics;
  memset(&result, 0, sizeof(result));
  memset(&source, 0, sizeof(source));
  m68k_diag_list_reset(&diagnostics);
  if (path == NULL || include_dir == NULL) {
    m68k_diag_add(m68k_diag_sink(&result.diagnostics), M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_BAD_ARGUMENT,
        "bad arguments");
    return result;
  }
  snprintf(source.include_dir, sizeof(source.include_dir), "%s", include_dir);
  source.target_cpu = target_cpu;
  source.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  if (!m68k_source_pipeline_parse_and_layout(&source, path, m68k_diag_sink(&diagnostics)) ||
      !m68k_source_pipeline_build_ir(&source, &result.source_file, m68k_diag_sink(&diagnostics))) {
    result.diagnostics = diagnostics;
    m68k_source_model_free(&source);
    return result;
  }
  m68k_source_model_free(&source);
  return result;
}

M68K_ASM_EXPORT M68kSourceIrRenderResult m68k_source_ir_render_with_policy(const M68kSourceFileIR *source_file,
    const M68kRenderPolicy *policy) {
  M68kSourceIrRenderResult result;
  M68kDiagList diagnostics;
  memset(&result, 0, sizeof(result));
  m68k_diag_list_reset(&diagnostics);
  if (m68k_source_ir_render_text_with_policy(source_file, policy, &result.text, m68k_diag_sink(&diagnostics)) != 0)
    result.diagnostics = diagnostics;
  return result;
}

M68K_ASM_EXPORT void m68k_source_ir_free(M68kSourceFileIR *source_file) {
  m68k_ir_source_file_destroy(source_file);
}

M68K_ASM_EXPORT void m68k_free_text(char *text) { free(text); }
