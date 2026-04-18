#ifndef PLATFORM_FILE_LIB_H
#define PLATFORM_FILE_LIB_H

#include "m68k_diagnostics.h"
#include "m68k_ir.h"

#include <stddef.h>

#ifdef _WIN32
#define PLATFORM_FILE_API __declspec(dllexport)
#else
#define PLATFORM_FILE_API
#endif

typedef struct PlatformFileRunSectionMetrics {
  char name[64];
  uint8_t kind;
  uint32_t size;
  uint32_t certain_code_bytes;
  uint32_t label_count;
  uint32_t block_count;
  uint32_t edge_count;
  uint32_t violation_count;
  uint32_t cpu_policy_violation_count;
  uint32_t decode_failed_reachable_violation_count;
  uint32_t invalid_interior_reference_violation_count;
  uint32_t unresolved_indirect_violation_count;
  uint32_t pc_relative_data_span_anchor_violation_count;
  uint32_t pc_relative_data_code_overlap_violation_count;
  uint32_t absolute_in_section_without_relocation_violation_count;
  uint32_t unproven_label_addend_violation_count;
  uint32_t unresolved_relocation_symbol_violation_count;
  uint32_t branch_target_unstable_violation_count;
  uint32_t orphaned_code_violation_count;
  uint32_t emitted_instruction_count;
  uint32_t emitted_data_count;
  uint32_t emitted_label_count;
  double analysis_cache_seconds;
  double analysis_finalize_seconds;
  double analysis_rebuild_seconds;
  double ir_build_seconds;
  double ir_append_seconds;
  double ir_preseed_seconds;
  double ir_label_plan_seconds;
  double ir_label_comment_seconds;
  double ir_label_emit_seconds;
  double ir_code_decode_seconds;
  double ir_code_annotate_seconds;
  double ir_label_annotation_seconds;
  double ir_control_stabilize_seconds;
  double ir_platform_symbol_seconds;
  double ir_code_comment_seconds;
  double ir_instruction_append_seconds;
  double ir_data_span_seconds;
} PlatformFileRunSectionMetrics;

typedef struct PlatformFileRunMetrics {
  M68kPlatformFileKind file_kind;
  M68kAnalysisFindings findings;
  double analysis_seconds;
  double ir_build_seconds;
  double render_seconds;
  double total_seconds;
  uint32_t section_bytes;
  uint32_t code_section_bytes;
  uint32_t data_section_bytes;
  uint32_t bss_section_bytes;
  uint32_t certain_code_bytes;
  uint32_t label_count;
  uint32_t generated_label_count;
  uint32_t block_count;
  uint32_t edge_count;
  uint32_t violation_count;
  uint32_t cpu_policy_violation_count;
  uint32_t decode_failed_reachable_violation_count;
  uint32_t invalid_interior_reference_violation_count;
  uint32_t unresolved_indirect_violation_count;
  uint32_t pc_relative_data_span_anchor_violation_count;
  uint32_t pc_relative_data_code_overlap_violation_count;
  uint32_t absolute_in_section_without_relocation_violation_count;
  uint32_t unproven_label_addend_violation_count;
  uint32_t unresolved_relocation_symbol_violation_count;
  uint32_t branch_target_unstable_violation_count;
  uint32_t orphaned_code_violation_count;
  uint32_t recovered_word_dispatch_count;
  uint32_t recovered_inline_dispatch_count;
  uint32_t recovered_string_dispatch_count;
  uint32_t recovered_platform_base_slot_count;
  uint32_t recovered_platform_effect_count;
  uint32_t recovered_platform_call_count;
  uint32_t statement_count;
  uint32_t label_statement_count;
  uint32_t generated_label_statement_count;
  uint32_t instruction_statement_count;
  uint32_t data_statement_count;
  uint32_t align_statement_count;
  uint32_t instruction_bytes;
  uint32_t data_bytes;
  uint32_t symbol_ref_count;
  uint32_t symbol_ref_abs_count;
  uint32_t symbol_ref_pc_relative_count;
  uint32_t symbol_ref_section_relative_count;
  uint32_t vasm_normalized_count;
  size_t text_bytes;
  PlatformFileRunSectionMetrics *sections;
  size_t section_count;
  size_t section_capacity;
} PlatformFileRunMetrics;

typedef struct PlatformFileTextResult {
  char *text;
  M68kDiagList diagnostics;
} PlatformFileTextResult;

typedef struct PlatformFileBufferResult {
  unsigned char *data;
  size_t size;
  M68kDiagList diagnostics;
} PlatformFileBufferResult;

typedef struct PlatformFileSourceIrResult {
  M68kSourceFileIR source_file;
  M68kDiagList diagnostics;
} PlatformFileSourceIrResult;

typedef struct PlatformFileSourceAnalysisResult {
  M68kSourceAnalysisIR *source_analysis;
  M68kDiagList diagnostics;
} PlatformFileSourceAnalysisResult;

typedef struct PlatformFileRunResult {
  M68kSourceFileIR source_file;
  char *text;
  PlatformFileRunMetrics metrics;
  M68kDiagList diagnostics;
} PlatformFileRunResult;

PLATFORM_FILE_API PlatformFileTextResult platform_file_inspect_path_json(const char *backend_name, const char *path);
PLATFORM_FILE_API PlatformFileTextResult platform_file_inspect_buffer_json(const char *backend_name,
  const unsigned char *data, size_t size);
PLATFORM_FILE_API PlatformFileBufferResult platform_file_roundtrip_buffer(const char *backend_name,
  const unsigned char *data, size_t size);
PLATFORM_FILE_API PlatformFileSourceIrResult platform_file_to_ir_buffer_with_policy(const char *backend_name,
  const unsigned char *data, size_t size, const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy);
PLATFORM_FILE_API PlatformFileSourceIrResult platform_file_to_ir_with_policy(const char *backend_name, const char *path,
  const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy);
PLATFORM_FILE_API PlatformFileSourceAnalysisResult platform_file_analyze_buffer(const char *backend_name,
  const unsigned char *data, size_t size, const M68kAnalysisPolicy *analysis_policy);
PLATFORM_FILE_API PlatformFileSourceAnalysisResult platform_file_analyze_path(const char *backend_name, const char *path,
  const M68kAnalysisPolicy *analysis_policy);
PLATFORM_FILE_API void platform_file_source_analysis_result_destroy(PlatformFileSourceAnalysisResult *result);
PLATFORM_FILE_API PlatformFileTextResult platform_file_analyze_buffer_json(const char *backend_name,
  const unsigned char *data, size_t size, const M68kAnalysisPolicy *analysis_policy);
PLATFORM_FILE_API PlatformFileTextResult platform_file_analyze_path_json(const char *backend_name, const char *path,
  const M68kAnalysisPolicy *analysis_policy);
PLATFORM_FILE_API PlatformFileTextResult platform_file_analyze_raw_path_json(const char *platform_name,
  const char *path, uint32_t entry_offset, const M68kAnalysisPolicy *analysis_policy);
PLATFORM_FILE_API PlatformFileTextResult platform_file_source_map_path_json(const char *backend_name, const char *path,
  const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy);
PLATFORM_FILE_API PlatformFileTextResult platform_file_listing_rows_path_json(const char *backend_name, const char *path,
  const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy);
PLATFORM_FILE_API PlatformFileTextResult platform_file_listing_rows_raw_path_json(const char *platform_name,
  const char *path, uint32_t entry_offset, const M68kRenderPolicy *policy,
  const M68kAnalysisPolicy *analysis_policy);
PLATFORM_FILE_API PlatformFileTextResult platform_file_type_catalog_json(const char *backend_name);
PLATFORM_FILE_API PlatformFileTextResult platform_file_naming_catalog_json(const char *backend_name);
PLATFORM_FILE_API PlatformFileTextResult platform_file_os_metadata_catalog_json(const char *backend_name);
PLATFORM_FILE_API PlatformFileTextResult platform_file_api_input_struct_json(const char *backend_name,
  const char *library_name, const char *function_name, const char *input_name, const char *struct_name);
PLATFORM_FILE_API int platform_file_inspect_path_json_alloc(const char *backend_name, const char *path,
  char **out_text);
PLATFORM_FILE_API int platform_file_disassemble_path_text_alloc(const char *backend_name, const char *path,
  const char *syntax, const char *metadata_path, char **out_text);
PLATFORM_FILE_API int platform_file_disassemble_raw_path_text_alloc(const char *platform_name, const char *path,
  uint32_t entry_offset, const char *syntax, const char *metadata_path, char **out_text);
PLATFORM_FILE_API int platform_file_analyze_path_json_alloc(const char *backend_name, const char *path,
  const char *metadata_path, const char *entry_offsets, char **out_text);
PLATFORM_FILE_API int platform_file_analyze_raw_path_json_alloc(const char *platform_name, const char *path,
  uint32_t entry_offset, const char *metadata_path, const char *entry_offsets, char **out_text);
PLATFORM_FILE_API int platform_file_effective_policy_path_json_alloc(const char *backend_name, const char *path,
  const char *metadata_path, const char *entry_offsets, char **out_text);
PLATFORM_FILE_API int platform_file_effective_policy_raw_path_json_alloc(const char *platform_name, const char *path,
  uint32_t entry_offset, const char *metadata_path, const char *entry_offsets, char **out_text);
PLATFORM_FILE_API int platform_file_benchmark_with_text_path_json_alloc(const char *backend_name, const char *path,
  const char *syntax, const char *metadata_path, char **out_text);
PLATFORM_FILE_API int platform_file_benchmark_with_text_raw_path_json_alloc(const char *platform_name, const char *path,
  uint32_t entry_offset, const char *syntax, const char *metadata_path, char **out_text);
PLATFORM_FILE_API int platform_file_listing_rows_path_json_alloc(const char *backend_name, const char *path,
  const char *metadata_path, char **out_text);
PLATFORM_FILE_API int platform_file_basic_listing_rows_path_json_alloc(const char *backend_name, const char *path,
  const char *metadata_path, char **out_text);
PLATFORM_FILE_API int platform_file_listing_rows_with_analysis_path_json_alloc(const char *backend_name, const char *path,
  const char *metadata_path, char **out_text);
PLATFORM_FILE_API int platform_file_listing_rows_raw_path_json_alloc(const char *platform_name, const char *path,
  uint32_t entry_offset, const char *metadata_path, char **out_text);
PLATFORM_FILE_API int platform_file_listing_rows_with_analysis_raw_path_json_alloc(const char *platform_name,
  const char *path, uint32_t entry_offset, const char *metadata_path, char **out_text);
PLATFORM_FILE_API int platform_file_basic_listing_rows_raw_path_json_alloc(const char *platform_name, const char *path,
  uint32_t entry_offset, const char *metadata_path, char **out_text);
PLATFORM_FILE_API int platform_file_type_catalog_json_alloc(const char *backend_name, char **out_text);
PLATFORM_FILE_API int platform_file_naming_catalog_json_alloc(const char *backend_name, char **out_text);
PLATFORM_FILE_API int platform_file_os_metadata_catalog_json_alloc(const char *backend_name, char **out_text);
PLATFORM_FILE_API int platform_file_api_input_struct_json_alloc(const char *backend_name, const char *library_name,
  const char *function_name, const char *input_name, const char *struct_name, char **out_text);
PLATFORM_FILE_API PlatformFileTextResult platform_file_render_ir_with_policy(const M68kSourceFileIR *source_file,
  const M68kRenderPolicy *policy);
PLATFORM_FILE_API PlatformFileRunResult platform_file_run_path_with_policy(const char *backend_name, const char *path,
  const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy);
PLATFORM_FILE_API PlatformFileRunResult platform_file_run_raw_path_with_policy(const char *platform_name,
  const char *path, uint32_t entry_offset, const M68kRenderPolicy *policy,
  const M68kAnalysisPolicy *analysis_policy);
PLATFORM_FILE_API int platform_file_analysis_policy_add_register_seed_arg(M68kAnalysisPolicy *policy,
  const char *text);
PLATFORM_FILE_API int platform_file_analysis_policy_add_entry_point_arg(M68kAnalysisPolicy *policy, const char *text);
/* Generic metadata only. Platform-derived policy must use the platform-aware loader. */
PLATFORM_FILE_API int platform_file_analysis_policy_load_target_metadata(M68kAnalysisPolicy *policy, const char *path,
  M68kDiagSink diagnostics);
PLATFORM_FILE_API int platform_file_analysis_policy_load_target_metadata_for_platform(M68kAnalysisPolicy *policy,
  const char *path, const char *platform_name, M68kDiagSink diagnostics);
PLATFORM_FILE_API PlatformFileTextResult platform_file_run_metrics_json(const char *backend_name, const char *path,
  const PlatformFileRunMetrics *metrics);
PLATFORM_FILE_API void platform_file_run_metrics_init(PlatformFileRunMetrics *metrics);
PLATFORM_FILE_API void platform_file_run_metrics_free(PlatformFileRunMetrics *metrics);
PLATFORM_FILE_API void platform_file_source_ir_free(M68kSourceFileIR *source_file);
PLATFORM_FILE_API void platform_file_source_analysis_free(M68kSourceAnalysisIR *source_analysis);
PLATFORM_FILE_API void platform_file_free_text(char *text);
PLATFORM_FILE_API void platform_file_free_bytes(unsigned char *data);

#endif
