#ifndef M68K_ASSEMBLER_APP_H
#define M68K_ASSEMBLER_APP_H

#include "m68k_ir.h"

#include <stdint.h>

int m68k_assemble_line_to_stdout(const char *line_text, uint8_t target_cpu);
int m68k_assemble_file_to_binary(const char *input_path, const char *output_path, uint8_t target_cpu);
int m68k_assemble_platform_file_to_output(const char *backend_name, const char *include_dir, const char *input_path,
  const char *output_path, uint8_t target_cpu, int enable_vasm_compat_rewrites);
int m68k_render_source_file_to_stdout(const char *input_path, const char *include_dir, uint8_t target_cpu,
  int enable_vasm_compat_rewrites, const M68kRenderPolicy *policy);

#endif
