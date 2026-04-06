#ifndef PLATFORM_FILE_LIB_H
#define PLATFORM_FILE_LIB_H

#include "m68k_ir.h"

#include <stddef.h>

#ifdef _WIN32
#define PLATFORM_FILE_API __declspec(dllexport)
#else
#define PLATFORM_FILE_API
#endif

PLATFORM_FILE_API int platform_file_inspect_path_json(const char *backend_name, const char *path, char **out_json,
  char *error_buf, size_t error_buf_size);
PLATFORM_FILE_API int platform_file_inspect_buffer_json(const char *backend_name, const unsigned char *data, size_t size,
  char **out_json, char *error_buf, size_t error_buf_size);
PLATFORM_FILE_API int platform_file_roundtrip_buffer(const char *backend_name, const unsigned char *data, size_t size,
  unsigned char **out_data, size_t *out_size, char *error_buf, size_t error_buf_size);
PLATFORM_FILE_API int platform_file_to_ir_buffer_with_policy(const char *backend_name, const unsigned char *data, size_t size,
  const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy, M68kSourceFileIR *out_source_file,
  char *error_buf, size_t error_buf_size);
PLATFORM_FILE_API int platform_file_to_ir_with_policy(const char *backend_name, const char *path, const M68kRenderPolicy *policy,
  const M68kAnalysisPolicy *analysis_policy, M68kSourceFileIR *out_source_file, char *error_buf, size_t error_buf_size);
PLATFORM_FILE_API int platform_file_analyze_buffer(const char *backend_name, const unsigned char *data, size_t size,
  const M68kAnalysisPolicy *analysis_policy, M68kSourceAnalysisIR *out_source_analysis, char *error_buf,
  size_t error_buf_size);
PLATFORM_FILE_API int platform_file_analyze_path(const char *backend_name, const char *path, const M68kAnalysisPolicy *analysis_policy,
  M68kSourceAnalysisIR *out_source_analysis, char *error_buf, size_t error_buf_size);
PLATFORM_FILE_API int platform_file_analyze_buffer_json(const char *backend_name, const unsigned char *data, size_t size,
  const M68kAnalysisPolicy *analysis_policy, char **out_json, char *error_buf, size_t error_buf_size);
PLATFORM_FILE_API int platform_file_analyze_path_json(const char *backend_name, const char *path,
  const M68kAnalysisPolicy *analysis_policy, char **out_json, char *error_buf, size_t error_buf_size);
PLATFORM_FILE_API int platform_file_render_ir_with_policy(const M68kSourceFileIR *source_file, const M68kRenderPolicy *policy,
  char **out_text, char *error_buf, size_t error_buf_size);
PLATFORM_FILE_API void platform_file_source_ir_free(M68kSourceFileIR *source_file);
PLATFORM_FILE_API void platform_file_source_analysis_free(M68kSourceAnalysisIR *source_analysis);
PLATFORM_FILE_API void platform_file_free_text(char *text);
PLATFORM_FILE_API void platform_file_free_buffer(unsigned char *data);

#endif
