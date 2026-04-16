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
#include <time.h>

static void platform_file_add_error(M68kDiagList *diagnostics, const char *message);

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

static int load_object_from_path(const M68kBackend *backend, const char *path, M68kObject *object,
    M68kDiagSink diagnostics) {
  if (object == NULL || path == NULL) {
    platform_file_add_error(diagnostics.list, "bad arguments");
    return -1;
  }
  if (backend == NULL || backend->read_file == NULL) {
    platform_file_add_error(diagnostics.list, "unknown platform file backend");
    return -1;
  }
  if (m68k_object_create(object) != 0) {
    platform_file_add_error(diagnostics.list, "out of memory");
    return -1;
  }
  if (backend->read_file(path, object, diagnostics) != 0) {
    m68k_object_destroy(object);
    return -1;
  }
  return 0;
}

static int load_object_from_buffer(const M68kBackend *backend, const unsigned char *data, size_t size,
    M68kObject *object, M68kDiagSink diagnostics) {
  if (object == NULL || data == NULL) {
    platform_file_add_error(diagnostics.list, "bad arguments");
    return -1;
  }
  if (backend == NULL || backend->read_buffer == NULL) {
    platform_file_add_error(diagnostics.list, "unknown platform file backend");
    return -1;
  }
  if (m68k_object_create(object) != 0) {
    platform_file_add_error(diagnostics.list, "out of memory");
    return -1;
  }
  if (backend->read_buffer(data, size, object, diagnostics) != 0) {
    m68k_object_destroy(object);
    return -1;
  }
  return 0;
}

static int read_file_to_buffer(const char *path, unsigned char **out_data, size_t *out_size,
    M68kDiagSink diagnostics) {
  FILE *input = NULL;
  int64_t file_size_value;
  size_t file_size;
  unsigned char *buffer = NULL;
  if (path == NULL || out_data == NULL || out_size == NULL) {
    platform_file_add_error(diagnostics.list, "bad arguments");
    return -1;
  }
  input = fopen(path, "rb");
  if (input == NULL) {
    platform_file_add_error(diagnostics.list, "failed opening roundtrip output");
    return -1;
  }
  if (fseek(input, 0, SEEK_END) != 0) {
    fclose(input);
    platform_file_add_error(diagnostics.list, "failed sizing roundtrip output");
    return -1;
  }
  file_size_value = (int64_t)ftell(input);
  if (file_size_value < 0) {
    fclose(input);
    platform_file_add_error(diagnostics.list, "failed sizing roundtrip output");
    return -1;
  }
  if (fseek(input, 0, SEEK_SET) != 0) {
    fclose(input);
    platform_file_add_error(diagnostics.list, "failed seeking roundtrip output");
    return -1;
  }
  file_size = (size_t)file_size_value;
  buffer = (unsigned char *)malloc(file_size != 0U ? file_size : 1U);
  if (buffer == NULL) {
    fclose(input);
    platform_file_add_error(diagnostics.list, "out of memory");
    return -1;
  }
  if (file_size != 0U && fread(buffer, 1, file_size, input) != file_size) {
    fclose(input);
    free(buffer);
    platform_file_add_error(diagnostics.list, "failed reading roundtrip output");
    return -1;
  }
  fclose(input);
  *out_data = buffer;
  *out_size = file_size;
  return 0;
}

static int write_object_to_temp_file(const M68kBackend *backend, const M68kObject *object, char *temp_path,
    size_t temp_path_size, M68kDiagSink diagnostics) {
  if (backend == NULL || backend->write_file == NULL || object == NULL) {
    platform_file_add_error(diagnostics.list, "unknown platform file backend");
    return -1;
  }
  if (make_temp_output_path(temp_path, temp_path_size) != 0) {
    platform_file_add_error(diagnostics.list, "failed creating temp path");
    return -1;
  }
  if (backend->write_file(temp_path, object, diagnostics) != 0) {
    remove(temp_path);
    return -1;
  }
  return 0;
}

static double elapsed_seconds(clock_t start_ticks, clock_t end_ticks) {
  return ((double)(end_ticks - start_ticks)) / (double)CLOCKS_PER_SEC;
}

static void platform_file_add_error(M68kDiagList *diagnostics, const char *message) {
  if (message == NULL || message[0] == '\0') message = "platform file operation failed";
  m68k_diag_add(m68k_diag_sink(diagnostics), M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, message);
}

static const char *platform_file_run_section_kind_name(uint8_t kind) {
  switch (kind) {
    case M68K_SECTION_CODE:
      return "code";
    case M68K_SECTION_DATA:
      return "data";
    case M68K_SECTION_BSS:
      return "bss";
    default:
      return "unknown";
  }
}

static const char *platform_file_run_file_kind_name(uint8_t kind) {
  switch (kind) {
    case M68K_PLATFORM_FILE_EXECUTABLE:
      return "executable";
    case M68K_PLATFORM_FILE_OBJECT:
      return "object";
    default:
      return "unknown";
  }
}

PlatformFileTextResult platform_file_inspect_path_json(const char *backend_name, const char *path) {
  PlatformFileTextResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  memset(&result, 0, sizeof(result));
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) return result;
  if (inspect_object_json(backend, &object, &result.text) != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    m68k_object_destroy(&object);
    return result;
  }
  m68k_object_destroy(&object);
  return result;
}

PlatformFileTextResult platform_file_inspect_buffer_json(const char *backend_name, const unsigned char *data,
    size_t size) {
  PlatformFileTextResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  memset(&result, 0, sizeof(result));
  if (load_object_from_buffer(backend, data, size, &object, m68k_diag_sink(&result.diagnostics)) != 0) return result;
  if (inspect_object_json(backend, &object, &result.text) != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    m68k_object_destroy(&object);
    return result;
  }
  m68k_object_destroy(&object);
  return result;
}

PlatformFileBufferResult platform_file_roundtrip_buffer(const char *backend_name, const unsigned char *data,
    size_t size) {
  PlatformFileBufferResult result;
  char temp_path[512];
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  memset(&result, 0, sizeof(result));
  if (backend == NULL || backend->read_buffer == NULL || backend->write_file == NULL) {
    platform_file_add_error(&result.diagnostics, "unknown platform file backend");
    return result;
  }
  if (load_object_from_buffer(backend, data, size, &object, m68k_diag_sink(&result.diagnostics)) != 0) return result;
  if (write_object_to_temp_file(backend, &object, temp_path, sizeof(temp_path),
      m68k_diag_sink(&result.diagnostics)) != 0) {
    m68k_object_destroy(&object);
    return result;
  }
  m68k_object_destroy(&object);
  if (read_file_to_buffer(temp_path, &result.data, &result.size, m68k_diag_sink(&result.diagnostics)) != 0) {
    remove(temp_path);
    return result;
  }
  remove(temp_path);
  return result;
}

void platform_file_free_text(char *text) { free(text); }
void platform_file_free_buffer(unsigned char *data) { free(data); }

void platform_file_run_metrics_init(PlatformFileRunMetrics *metrics) {
  if (metrics == NULL) return;
  memset(metrics, 0, sizeof(*metrics));
  m68k_analysis_findings_init(&metrics->findings);
}

void platform_file_run_metrics_free(PlatformFileRunMetrics *metrics) {
  if (metrics == NULL) return;
  free(metrics->sections);
  memset(metrics, 0, sizeof(*metrics));
}

PlatformFileSourceIrResult platform_file_to_ir_with_policy(const char *backend_name, const char *path,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileSourceIrResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  M68kRenderPolicy default_policy;
  M68kAnalysisPolicy default_analysis_policy;
  const M68kRenderPolicy *active_policy = resolve_render_policy(policy, &default_policy);
  const M68kAnalysisPolicy *active_analysis_policy = resolve_analysis_policy(analysis_policy, &default_analysis_policy);
  int populate_result;
  memset(&result, 0, sizeof(result));
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) return result;
  populate_result = populate_source_ir_from_object(backend, &object, active_policy, active_analysis_policy,
    &result.source_file, m68k_diag_sink(&result.diagnostics));
  m68k_object_destroy(&object);
  if (populate_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building source ir");
  return result;
}

PlatformFileRunResult platform_file_run_path_with_policy(const char *backend_name, const char *path,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileRunResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  M68kRenderPolicy default_policy;
  M68kAnalysisPolicy default_analysis_policy;
  const M68kRenderPolicy *active_policy = resolve_render_policy(policy, &default_policy);
  const M68kAnalysisPolicy *active_analysis_policy = resolve_analysis_policy(analysis_policy, &default_analysis_policy);
  clock_t total_start, total_end, render_start, render_end;
  int populate_result;
  PlatformFileTextResult rendered;
  memset(&result, 0, sizeof(result));
  platform_file_run_metrics_init(&result.metrics);
  total_start = clock();
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    platform_file_run_metrics_free(&result.metrics);
    return result;
  }
  populate_result = populate_source_ir_from_object_with_metrics(backend, &object, active_policy, active_analysis_policy,
    &result.source_file, &result.metrics, m68k_diag_sink(&result.diagnostics));
  if (populate_result != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics)) platform_file_add_error(&result.diagnostics, "failed building source ir");
    m68k_object_destroy(&object);
    platform_file_run_metrics_free(&result.metrics);
    return result;
  }
  render_start = clock();
  rendered = platform_file_render_ir_with_policy(&result.source_file, active_policy);
  render_end = clock();
  m68k_object_destroy(&object);
  if (m68k_diag_has_errors(&rendered.diagnostics)) {
    result.diagnostics = rendered.diagnostics;
    platform_file_source_ir_free(&result.source_file);
    platform_file_run_metrics_free(&result.metrics);
    return result;
  }
  result.metrics.render_seconds = elapsed_seconds(render_start, render_end);
  result.metrics.text_bytes = strlen(rendered.text);
  total_end = clock();
  result.metrics.total_seconds = elapsed_seconds(total_start, total_end);
  result.text = rendered.text;
  return result;
}

PlatformFileTextResult platform_file_run_metrics_json(const char *backend_name, const char *path,
    const PlatformFileRunMetrics *metrics) {
  PlatformFileTextResult result;
  JsonBuilder builder = {0};
  size_t section_index;
  double certain_code_ratio;
  double instruction_byte_ratio;
  char *json = NULL;
  memset(&result, 0, sizeof(result));
  if (backend_name == NULL || path == NULL || metrics == NULL) {
    platform_file_add_error(&result.diagnostics, "bad arguments");
    return result;
  }
  certain_code_ratio = metrics->section_bytes == 0U ? 0.0
    : ((double)metrics->certain_code_bytes / (double)metrics->section_bytes);
  instruction_byte_ratio = (metrics->instruction_bytes + metrics->data_bytes) == 0U ? 0.0
    : ((double)metrics->instruction_bytes / (double)(metrics->instruction_bytes + metrics->data_bytes));
  if (json_builder_create(&builder) != 0) goto oom;
  if (json_builder_append(&builder, "{\n  \"benchmark_version\": 1,\n  \"platform\": ") != 0) goto oom;
  if (json_builder_append_json_string(&builder, backend_name) != 0) goto oom;
  if (json_builder_append(&builder, ",\n  \"path\": ") != 0) goto oom;
  if (json_builder_append_json_string(&builder, path) != 0) goto oom;
  if (json_builder_appendf(&builder,
      ",\n  \"timing\": {\n"
      "    \"analysis_seconds\": %.6f,\n"
      "    \"ir_build_seconds\": %.6f,\n"
      "    \"render_seconds\": %.6f,\n"
      "    \"total_seconds\": %.6f\n"
      "  },\n"
      "  \"file\": {\n"
      "    \"file_kind\": ",
      metrics->analysis_seconds, metrics->ir_build_seconds, metrics->render_seconds, metrics->total_seconds) != 0)
    goto oom;
  if (json_builder_append_json_string(&builder, platform_file_run_file_kind_name(metrics->file_kind)) != 0) goto oom;
  if (json_builder_appendf(&builder,
      ",\n"
      "    \"section_count\": %zu,\n"
      "    \"section_bytes\": %u,\n"
      "    \"code_section_bytes\": %u,\n"
      "    \"data_section_bytes\": %u,\n"
      "    \"bss_section_bytes\": %u\n"
      "  },\n"
      "  \"analysis\": {\n"
      "    \"required_cpu\": %u,\n"
      "    \"cpu_violation_count\": %u,\n"
      "    \"certain_code_bytes\": %u,\n"
      "    \"certain_code_ratio\": %.6f,\n"
      "    \"label_count\": %u,\n"
      "    \"generated_label_count\": %u,\n"
      "    \"block_count\": %u,\n"
      "    \"edge_count\": %u,\n"
      "    \"violation_count\": %u,\n"
      "    \"recovered_word_dispatch_count\": %u,\n"
      "    \"recovered_inline_dispatch_count\": %u,\n"
      "    \"recovered_string_dispatch_count\": %u,\n"
      "    \"recovered_platform_base_slot_count\": %u,\n"
      "    \"recovered_platform_effect_count\": %u,\n"
      "    \"recovered_platform_call_count\": %u\n"
      "  },\n"
      "  \"render\": {\n"
      "    \"statement_count\": %u,\n"
      "    \"label_statement_count\": %u,\n"
      "    \"generated_label_statement_count\": %u,\n"
      "    \"instruction_statement_count\": %u,\n"
      "    \"data_statement_count\": %u,\n"
      "    \"align_statement_count\": %u,\n"
      "    \"instruction_bytes\": %u,\n"
      "    \"data_bytes\": %u,\n"
      "    \"instruction_byte_ratio\": %.6f,\n"
      "    \"symbol_ref_count\": %u,\n"
      "    \"symbol_ref_abs_count\": %u,\n"
      "    \"symbol_ref_pc_relative_count\": %u,\n"
      "    \"symbol_ref_section_relative_count\": %u,\n"
      "    \"vasm_normalized_count\": %u,\n"
      "    \"text_bytes\": %zu\n"
      "  },\n"
      "  \"sections\": [\n",
      metrics->section_count,
      (unsigned)metrics->section_bytes,
      (unsigned)metrics->code_section_bytes,
      (unsigned)metrics->data_section_bytes,
      (unsigned)metrics->bss_section_bytes,
      (unsigned)metrics->findings.required_cpu,
      (unsigned)metrics->findings.cpu_violation_count,
      (unsigned)metrics->certain_code_bytes,
      certain_code_ratio,
      (unsigned)metrics->label_count,
      (unsigned)metrics->generated_label_count,
      (unsigned)metrics->block_count,
      (unsigned)metrics->edge_count,
      (unsigned)metrics->violation_count,
      (unsigned)metrics->recovered_word_dispatch_count,
      (unsigned)metrics->recovered_inline_dispatch_count,
      (unsigned)metrics->recovered_string_dispatch_count,
      (unsigned)metrics->recovered_platform_base_slot_count,
      (unsigned)metrics->recovered_platform_effect_count,
      (unsigned)metrics->recovered_platform_call_count,
      (unsigned)metrics->statement_count,
      (unsigned)metrics->label_statement_count,
      (unsigned)metrics->generated_label_statement_count,
      (unsigned)metrics->instruction_statement_count,
      (unsigned)metrics->data_statement_count,
      (unsigned)metrics->align_statement_count,
      (unsigned)metrics->instruction_bytes,
      (unsigned)metrics->data_bytes,
      instruction_byte_ratio,
      (unsigned)metrics->symbol_ref_count,
      (unsigned)metrics->symbol_ref_abs_count,
      (unsigned)metrics->symbol_ref_pc_relative_count,
      (unsigned)metrics->symbol_ref_section_relative_count,
      (unsigned)metrics->vasm_normalized_count,
      metrics->text_bytes) != 0)
    goto oom;
  for (section_index = 0; section_index < metrics->section_count; ++section_index) {
    const PlatformFileRunSectionMetrics *section = &metrics->sections[section_index];
    if (json_builder_append(&builder, "    {\n      \"name\": ") != 0) goto oom;
    if (json_builder_append_json_string(&builder, section->name) != 0) goto oom;
    if (json_builder_append(&builder, ",\n      \"kind\": ") != 0) goto oom;
    if (json_builder_append_json_string(&builder, platform_file_run_section_kind_name(section->kind)) != 0) goto oom;
    if (json_builder_appendf(&builder,
        ",\n"
        "      \"size\": %u,\n"
        "      \"certain_code_bytes\": %u,\n"
        "      \"label_count\": %u,\n"
        "      \"block_count\": %u,\n"
        "      \"edge_count\": %u,\n"
        "      \"violation_count\": %u,\n"
        "      \"emitted_instruction_count\": %u,\n"
        "      \"emitted_data_count\": %u,\n"
        "      \"emitted_label_count\": %u\n"
        "    }%s",
        (unsigned)section->size,
        (unsigned)section->certain_code_bytes,
        (unsigned)section->label_count,
        (unsigned)section->block_count,
        (unsigned)section->edge_count,
        (unsigned)section->violation_count,
        (unsigned)section->emitted_instruction_count,
        (unsigned)section->emitted_data_count,
        (unsigned)section->emitted_label_count,
        section_index + 1U < metrics->section_count ? ",\n" : "\n") != 0)
      goto oom;
  }
  if (json_builder_append(&builder, "  ]\n}\n") != 0) goto oom;
  json = json_builder_build(&builder);
  if (json == NULL) goto oom;
  json_builder_destroy(&builder);
  result.text = json;
  return result;

oom:
  json_builder_destroy(&builder);
  platform_file_add_error(&result.diagnostics, "out of memory");
  return result;
}

PlatformFileSourceIrResult platform_file_to_ir_buffer_with_policy(const char *backend_name, const unsigned char *data,
    size_t size, const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileSourceIrResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  M68kRenderPolicy default_policy;
  M68kAnalysisPolicy default_analysis_policy;
  const M68kRenderPolicy *active_policy = resolve_render_policy(policy, &default_policy);
  const M68kAnalysisPolicy *active_analysis_policy = resolve_analysis_policy(analysis_policy, &default_analysis_policy);
  int populate_result;
  memset(&result, 0, sizeof(result));
  if (load_object_from_buffer(backend, data, size, &object, m68k_diag_sink(&result.diagnostics)) != 0) return result;
  populate_result = populate_source_ir_from_object(backend, &object, active_policy, active_analysis_policy,
    &result.source_file, m68k_diag_sink(&result.diagnostics));
  m68k_object_destroy(&object);
  if (populate_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building source ir");
  return result;
}

PlatformFileSourceAnalysisResult platform_file_analyze_path(const char *backend_name, const char *path,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileSourceAnalysisResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  M68kAnalysisPolicy default_analysis_policy;
  const M68kAnalysisPolicy *active_analysis_policy = resolve_analysis_policy(analysis_policy, &default_analysis_policy);
  int populate_result;
  memset(&result, 0, sizeof(result));
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) return result;
  populate_result = populate_source_analysis_from_object(&object, active_analysis_policy, &result.source_analysis,
    m68k_diag_sink(&result.diagnostics));
  m68k_object_destroy(&object);
  if (populate_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building source analysis");
  return result;
}

PlatformFileSourceAnalysisResult platform_file_analyze_buffer(const char *backend_name, const unsigned char *data,
    size_t size, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileSourceAnalysisResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  M68kAnalysisPolicy default_analysis_policy;
  const M68kAnalysisPolicy *active_analysis_policy = resolve_analysis_policy(analysis_policy, &default_analysis_policy);
  int populate_result;
  memset(&result, 0, sizeof(result));
  if (load_object_from_buffer(backend, data, size, &object, m68k_diag_sink(&result.diagnostics)) != 0) return result;
  populate_result = populate_source_analysis_from_object(&object, active_analysis_policy, &result.source_analysis,
    m68k_diag_sink(&result.diagnostics));
  m68k_object_destroy(&object);
  if (populate_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building source analysis");
  return result;
}

PlatformFileTextResult platform_file_analyze_path_json(const char *backend_name, const char *path,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  PlatformFileSourceAnalysisResult analysis;
  int json_result;
  memset(&result, 0, sizeof(result));
  analysis = platform_file_analyze_path(backend_name, path, analysis_policy);
  if (m68k_diag_has_errors(&analysis.diagnostics)) {
    result.diagnostics = analysis.diagnostics;
    return result;
  }
  json_result = source_analysis_to_json(&analysis.source_analysis, &result.text, m68k_diag_sink(&result.diagnostics));
  m68k_ir_source_analysis_destroy(&analysis.source_analysis);
  if (json_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building analysis json");
  return result;
}

PlatformFileTextResult platform_file_analyze_buffer_json(const char *backend_name, const unsigned char *data,
    size_t size, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  PlatformFileSourceAnalysisResult analysis;
  int json_result;
  memset(&result, 0, sizeof(result));
  analysis = platform_file_analyze_buffer(backend_name, data, size, analysis_policy);
  if (m68k_diag_has_errors(&analysis.diagnostics)) {
    result.diagnostics = analysis.diagnostics;
    return result;
  }
  json_result = source_analysis_to_json(&analysis.source_analysis, &result.text, m68k_diag_sink(&result.diagnostics));
  m68k_ir_source_analysis_destroy(&analysis.source_analysis);
  if (json_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building analysis json");
  return result;
}

PlatformFileTextResult platform_file_render_ir_with_policy(const M68kSourceFileIR *source_file,
    const M68kRenderPolicy *policy) {
  PlatformFileTextResult result;
  M68kDiagList diagnostics;
  int render_result;
  memset(&result, 0, sizeof(result));
  m68k_diag_list_reset(&diagnostics);
  render_result = m68k_source_ir_render_text_with_policy(source_file, policy, &result.text,
    m68k_diag_sink(&diagnostics));
  if (render_result != 0) result.diagnostics = diagnostics;
  return result;
}

void platform_file_source_ir_free(M68kSourceFileIR *source_file) {
  m68k_ir_source_file_destroy(source_file);
}

void platform_file_source_analysis_free(M68kSourceAnalysisIR *source_analysis) {
  m68k_ir_source_analysis_destroy(source_analysis);
}
