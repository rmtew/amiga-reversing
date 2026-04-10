/* Source IR API surface for parse/render/free entrypoints. */
#include "m68k_assembler_lib.h"
#include "m68k_source_ir_render.h"
#include "m68k_source_model.h"
#include "m68k_source_pipeline.h"

#include "platform_common.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

M68K_ASM_EXPORT int m68k_source_ir_parse_file(const char *path,
                                              const char *include_dir,
                                              uint8_t target_cpu,
                                              int enable_vasm_compat_rewrites,
                                              M68kSourceFileIR *out_source_file,
                                              char *out_error,
                                              size_t out_error_size) {
  AsmSourceFile source;
  memset(&source, 0, sizeof(source));
  if (path == NULL || include_dir == NULL || out_source_file == NULL) {
    m68k_platform_set_error(out_error, out_error_size, "bad arguments");
    return -1;
  }
  snprintf(source.include_dir, sizeof(source.include_dir), "%s", include_dir);
  source.target_cpu = target_cpu;
  source.enable_vasm_compat_rewrites = enable_vasm_compat_rewrites;
  if (!m68k_source_pipeline_parse_and_layout(&source, path, out_error,
                                             out_error_size) ||
      !m68k_source_pipeline_build_ir(&source, out_source_file, out_error,
                                     out_error_size)) {
    m68k_source_model_free(&source);
    return -1;
  }
  m68k_source_model_free(&source);
  return 0;
}

M68K_ASM_EXPORT int m68k_source_ir_render_with_policy( const M68kSourceFileIR *source_file, const M68kRenderPolicy *policy,
    char **out_text, char *out_error, size_t out_error_size) {
  return m68k_source_ir_render_text_with_policy(source_file, policy, out_text,
                                                out_error, out_error_size);
}

M68K_ASM_EXPORT void m68k_source_ir_free(M68kSourceFileIR *source_file) {
  m68k_ir_source_file_destroy(source_file);
}

M68K_ASM_EXPORT void m68k_free_text(char *text) { free(text); }
