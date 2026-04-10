#include "platform_file_lib.h"
#include "platform_file_internal.h"
#include "json_builder.h"
#include "m68k_assembler.h"
#include "m68k_backend.h"
#include "m68k_instruction_spec.h"
#include "m68k_ir_codec.h"
#include "m68k_object.h"
#include "m68k_parse_util.h"
#include "m68k_plain_parse.h"
#include "m68k_simulator.h"
#include "m68k_source_ir_render.h"
#include "platform_atari_st.h"
#include "platform_common.h"
#include "util_arena.h"

#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int make_temp_output_path(char *path_buf, size_t path_buf_size) {
  char temp_name[L_tmpnam];
  if (tmpnam_s(temp_name, sizeof(temp_name)) != 0)
    return -1;
  if (strlen(temp_name) + 4U >= path_buf_size)
    return -1;
  strcpy(path_buf, temp_name);
  strcat(path_buf, ".bin");
  return 0;
}

static const M68kRenderPolicy *resolve_render_policy(const M68kRenderPolicy *policy,
    M68kRenderPolicy *default_policy) {
  if (policy != NULL) return policy;
  m68k_render_policy_init_for_syntax(default_policy, M68K_IR_SYNTAX_CANONICAL);
  return default_policy;
}

static const M68kAnalysisPolicy *resolve_analysis_policy(const M68kAnalysisPolicy *policy,
    M68kAnalysisPolicy *default_policy) {
  if (policy != NULL) return policy;
  m68k_analysis_policy_init_default(default_policy);
  return default_policy;
}

static int load_object_from_path(const M68kBackend *backend, const char *path, M68kObject *object, char *error_buf,
    size_t error_buf_size) {
  char error[256];
  if (object == NULL || path == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "bad arguments");
    return -1;
  }
  if (backend == NULL || backend->read_file == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "unknown platform file backend");
    return -1;
  }
  if (m68k_object_create(object) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, "out of memory");
    return -1;
  }
  if (backend->read_file(path, object, error, sizeof(error)) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, error);
    m68k_object_destroy(object);
    return -1;
  }
  return 0;
}

static int load_object_from_buffer(const M68kBackend *backend, const unsigned char *data, size_t size,
    M68kObject *object, char *error_buf, size_t error_buf_size) {
  char error[256];
  if (object == NULL || data == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "bad arguments");
    return -1;
  }
  if (backend == NULL || backend->read_buffer == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "unknown platform file backend");
    return -1;
  }
  if (m68k_object_create(object) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, "out of memory");
    return -1;
  }
  if (backend->read_buffer(data, size, object, error, sizeof(error)) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, error);
    m68k_object_destroy(object);
    return -1;
  }
  return 0;
}

static int read_file_to_buffer(const char *path, unsigned char **out_data, size_t *out_size, char *error_buf,
    size_t error_buf_size) {
  FILE *input = NULL;
  int64_t file_size_value;
  size_t file_size;
  unsigned char *buffer = NULL;
  if (path == NULL || out_data == NULL || out_size == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "bad arguments");
    return -1;
  }
  input = fopen(path, "rb");
  if (input == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "failed opening roundtrip output");
    return -1;
  }
  if (fseek(input, 0, SEEK_END) != 0) {
    fclose(input);
    m68k_platform_set_error(error_buf, error_buf_size, "failed sizing roundtrip output");
    return -1;
  }
  file_size_value = (int64_t)ftell(input);
  if (file_size_value < 0) {
    fclose(input);
    m68k_platform_set_error(error_buf, error_buf_size, "failed sizing roundtrip output");
    return -1;
  }
  if (fseek(input, 0, SEEK_SET) != 0) {
    fclose(input);
    m68k_platform_set_error(error_buf, error_buf_size, "failed seeking roundtrip output");
    return -1;
  }
  file_size = (size_t)file_size_value;
  buffer = (unsigned char *)malloc(file_size != 0U ? file_size : 1U);
  if (buffer == NULL) {
    fclose(input);
    m68k_platform_set_error(error_buf, error_buf_size, "out of memory");
    return -1;
  }
  if (file_size != 0U && fread(buffer, 1, file_size, input) != file_size) {
    fclose(input);
    free(buffer);
    m68k_platform_set_error(error_buf, error_buf_size, "failed reading roundtrip output");
    return -1;
  }
  fclose(input);
  *out_data = buffer;
  *out_size = file_size;
  return 0;
}

static int write_object_to_temp_file(const M68kBackend *backend, const M68kObject *object, char *temp_path,
    size_t temp_path_size, char *error_buf, size_t error_buf_size) {
  char error[256];
  if (backend == NULL || backend->write_file == NULL || object == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "unknown platform file backend");
    return -1;
  }
  if (make_temp_output_path(temp_path, temp_path_size) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, "failed creating temp path");
    return -1;
  }
  if (backend->write_file(temp_path, object, error, sizeof(error)) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, error);
    remove(temp_path);
    return -1;
  }
  return 0;
}

int platform_file_inspect_path_json(const char *backend_name, const char *path, char **out_json, char *error_buf,
    size_t error_buf_size) {
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  if (out_json == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "null output");
    return -1;
  }
  if (load_object_from_path(backend, path, &object, error_buf, error_buf_size) != 0)
    return -1;
  if (inspect_object_json(backend, &object, out_json) != 0) {
    if (error_buf != NULL && error_buf_size != 0U && error_buf[0] == '\0')
      m68k_platform_set_error(error_buf, error_buf_size, "out of memory");
    m68k_object_destroy(&object);
    return -1;
  }
  m68k_object_destroy(&object);
  return 0;
}

int platform_file_inspect_buffer_json(const char *backend_name, const unsigned char *data, size_t size,
    char **out_json, char *error_buf, size_t error_buf_size) {
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  if (out_json == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "null output");
    return -1;
  }
  if (load_object_from_buffer(backend, data, size, &object, error_buf, error_buf_size) != 0)
    return -1;
  if (inspect_object_json(backend, &object, out_json) != 0) {
    if (error_buf != NULL && error_buf_size != 0U && error_buf[0] == '\0')
      m68k_platform_set_error(error_buf, error_buf_size, "out of memory");
    m68k_object_destroy(&object);
    return -1;
  }
  m68k_object_destroy(&object);
  return 0;
}

int platform_file_roundtrip_buffer(const char *backend_name, const unsigned char *data, size_t size,
    unsigned char **out_data, size_t *out_size, char *error_buf, size_t error_buf_size) {
  char temp_path[512];
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  if (backend == NULL || backend->read_buffer == NULL || backend->write_file == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "unknown platform file backend");
    return -1;
  }
  if (load_object_from_buffer(backend, data, size, &object, error_buf, error_buf_size) != 0)
    return -1;
  if (write_object_to_temp_file(backend, &object, temp_path, sizeof(temp_path), error_buf, error_buf_size) != 0) {
    m68k_object_destroy(&object);
    return -1;
  }
  m68k_object_destroy(&object);
  if (read_file_to_buffer(temp_path, out_data, out_size, error_buf, error_buf_size) != 0) {
    remove(temp_path);
    return -1;
  }
  remove(temp_path);
  return 0;
}

void platform_file_free_text(char *text) { free(text); }
void platform_file_free_buffer(unsigned char *data) { free(data); }

int platform_file_to_ir_with_policy(const char *backend_name, const char *path, const M68kRenderPolicy *policy,
    const M68kAnalysisPolicy *analysis_policy, M68kSourceFileIR *out_source_file, char *error_buf,
    size_t error_buf_size) {
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  M68kRenderPolicy default_policy;
  M68kAnalysisPolicy default_analysis_policy;
  const M68kRenderPolicy *active_policy = resolve_render_policy(policy, &default_policy);
  const M68kAnalysisPolicy *active_analysis_policy = resolve_analysis_policy(analysis_policy, &default_analysis_policy);
  int result;
  if (out_source_file == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "null output");
    return -1;
  }
  if (load_object_from_path(backend, path, &object, error_buf, error_buf_size) != 0)
    return -1;
  result = populate_source_ir_from_object(backend, &object, active_policy, active_analysis_policy,
    out_source_file, error_buf, error_buf_size);
  m68k_object_destroy(&object);
  return result;
}

int platform_file_to_ir_buffer_with_policy(const char *backend_name, const unsigned char *data, size_t size,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy, M68kSourceFileIR *out_source_file,
    char *error_buf, size_t error_buf_size) {
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  M68kRenderPolicy default_policy;
  M68kAnalysisPolicy default_analysis_policy;
  const M68kRenderPolicy *active_policy = resolve_render_policy(policy, &default_policy);
  const M68kAnalysisPolicy *active_analysis_policy = resolve_analysis_policy(analysis_policy, &default_analysis_policy);
  int result;
  if (out_source_file == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "null output");
    return -1;
  }
  if (load_object_from_buffer(backend, data, size, &object, error_buf, error_buf_size) != 0)
    return -1;
  result = populate_source_ir_from_object(backend, &object, active_policy, active_analysis_policy,
    out_source_file, error_buf, error_buf_size);
  m68k_object_destroy(&object);
  return result;
}

int platform_file_analyze_path(const char *backend_name, const char *path, const M68kAnalysisPolicy *analysis_policy,
    M68kSourceAnalysisIR *out_source_analysis, char *error_buf, size_t error_buf_size) {
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  M68kAnalysisPolicy default_analysis_policy;
  const M68kAnalysisPolicy *active_analysis_policy = resolve_analysis_policy(analysis_policy, &default_analysis_policy);
  int result;
  if (out_source_analysis == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "null output");
    return -1;
  }
  if (load_object_from_path(backend, path, &object, error_buf, error_buf_size) != 0)
    return -1;
  result = populate_source_analysis_from_object(&object, active_analysis_policy, out_source_analysis,
    error_buf, error_buf_size);
  m68k_object_destroy(&object);
  return result;
}

int platform_file_analyze_buffer(const char *backend_name, const unsigned char *data, size_t size,
    const M68kAnalysisPolicy *analysis_policy, M68kSourceAnalysisIR *out_source_analysis, char *error_buf,
    size_t error_buf_size) {
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  M68kAnalysisPolicy default_analysis_policy;
  const M68kAnalysisPolicy *active_analysis_policy = resolve_analysis_policy(analysis_policy, &default_analysis_policy);
  int result;
  if (out_source_analysis == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "null output");
    return -1;
  }
  if (load_object_from_buffer(backend, data, size, &object, error_buf, error_buf_size) != 0)
    return -1;
  result = populate_source_analysis_from_object(&object, active_analysis_policy, out_source_analysis,
    error_buf, error_buf_size);
  m68k_object_destroy(&object);
  return result;
}

int platform_file_analyze_path_json(const char *backend_name, const char *path,
    const M68kAnalysisPolicy *analysis_policy, char **out_json, char *error_buf, size_t error_buf_size) {
  M68kSourceAnalysisIR source_analysis;
  int result;
  if (out_json == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "null output");
    return -1;
  }
  *out_json = NULL;
  result = platform_file_analyze_path(backend_name, path, analysis_policy, &source_analysis, error_buf, error_buf_size);
  if (result != 0)
    return result;
  result = source_analysis_to_json(&source_analysis, out_json, error_buf, error_buf_size);
  m68k_ir_source_analysis_destroy(&source_analysis);
  return result;
}

int platform_file_analyze_buffer_json(const char *backend_name, const unsigned char *data, size_t size,
    const M68kAnalysisPolicy *analysis_policy, char **out_json, char *error_buf, size_t error_buf_size) {
  M68kSourceAnalysisIR source_analysis;
  int result;
  if (out_json == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "null output");
    return -1;
  }
  *out_json = NULL;
  result = platform_file_analyze_buffer(backend_name, data, size, analysis_policy, &source_analysis,
    error_buf, error_buf_size);
  if (result != 0)
    return result;
  result = source_analysis_to_json(&source_analysis, out_json, error_buf, error_buf_size);
  m68k_ir_source_analysis_destroy(&source_analysis);
  return result;
}

int platform_file_render_ir_with_policy(const M68kSourceFileIR *source_file, const M68kRenderPolicy *policy,
    char **out_text, char *error_buf, size_t error_buf_size) {
  return m68k_source_ir_render_text_with_policy(source_file, policy, out_text, error_buf, error_buf_size);
}

void platform_file_source_ir_free(M68kSourceFileIR *source_file) {
  m68k_ir_source_file_destroy(source_file);
}

void platform_file_source_analysis_free(M68kSourceAnalysisIR *source_analysis) {
  m68k_ir_source_analysis_destroy(source_analysis);
}
