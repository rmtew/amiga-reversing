#ifndef M68K_ASSEMBLER_APP_H
#define M68K_ASSEMBLER_APP_H

#include "m68k_diagnostics.h"
#include "m68k_ir.h"

#include <stdint.h>
#include <stddef.h>

typedef struct M68kPlatformAssembleProfile {
  double parse_layout_seconds;
  double emit_object_seconds;
  double platform_finalize_seconds;
  double write_buffer_seconds;
  double write_file_seconds;
  double read_output_seconds;
  double total_seconds;
  uint32_t source_bytes;
  uint32_t rebuilt_bytes;
} M68kPlatformAssembleProfile;

int m68k_assemble_line_to_stdout(const char *line_text, uint8_t target_cpu);
int m68k_assemble_file_to_binary(const char *input_path, const char *output_path, uint8_t target_cpu);
int m68k_assemble_platform_file_to_output(const char *backend_name, const char *include_dir, const char *input_path,
  const char *output_path, uint8_t target_cpu, int enable_vasm_compat_rewrites);
int m68k_assemble_platform_file_to_buffer_alloc(const char *backend_name, const char *include_dir,
  const char *input_path, uint8_t target_cpu, int enable_vasm_compat_rewrites, unsigned char **out_data,
  size_t *out_size, M68kPlatformAssembleProfile *out_profile, M68kDiagSink diagnostics);
int m68k_assemble_platform_file_to_output_buffer_alloc(const char *backend_name, const char *include_dir,
  const char *input_path, const char *output_path, uint8_t target_cpu, int enable_vasm_compat_rewrites,
  unsigned char **out_data, size_t *out_size, M68kPlatformAssembleProfile *out_profile, M68kDiagSink diagnostics);
int m68k_assemble_platform_source_text_to_buffer_alloc(const char *backend_name, const char *include_dir,
  const char *source_text, uint8_t target_cpu, int enable_vasm_compat_rewrites, unsigned char **out_data,
  size_t *out_size, M68kPlatformAssembleProfile *out_profile, M68kDiagSink diagnostics);
int m68k_assemble_platform_source_text_to_output_buffer_alloc(const char *backend_name, const char *include_dir,
  const char *source_text, const char *output_path, uint8_t target_cpu, int enable_vasm_compat_rewrites,
  unsigned char **out_data, size_t *out_size, M68kPlatformAssembleProfile *out_profile, M68kDiagSink diagnostics);
int m68k_render_source_file_to_stdout(const char *input_path, const char *include_dir, uint8_t target_cpu,
  int enable_vasm_compat_rewrites, const M68kRenderPolicy *policy);

#endif
