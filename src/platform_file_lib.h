#ifndef PLATFORM_FILE_LIB_H
#define PLATFORM_FILE_LIB_H

#include "m68k_diagnostics.h"
#include "m68k_ir.h"

#include <stddef.h>
#include <stdint.h>

#ifdef _WIN32
#define PLATFORM_FILE_API __declspec(dllexport)
#else
#define PLATFORM_FILE_API
#endif

typedef struct PlatformFileTextResult {
  char *text;
  M68kDiagList diagnostics;
} PlatformFileTextResult;

typedef struct PlatformFileBufferResult {
  unsigned char *data;
  size_t size;
  M68kDiagList diagnostics;
} PlatformFileBufferResult;

typedef struct PlatformFileListingArtifact PlatformFileListingArtifact;

PLATFORM_FILE_API PlatformFileTextResult platform_file_inspect_path_json(const char *backend_name, const char *path);
PLATFORM_FILE_API PlatformFileTextResult platform_file_inspect_buffer_json(const char *backend_name,
  const unsigned char *data, size_t size);
PLATFORM_FILE_API PlatformFileBufferResult platform_file_roundtrip_buffer(const char *backend_name,
  const unsigned char *data, size_t size);
PLATFORM_FILE_API PlatformFileTextResult platform_file_facts_v2_analysis_buffer_json(const char *backend_name,
  const unsigned char *data, size_t size, const M68kAnalysisPolicy *analysis_policy);
PLATFORM_FILE_API PlatformFileTextResult platform_file_facts_v2_analysis_path_json(const char *backend_name,
  const char *path, const M68kAnalysisPolicy *analysis_policy);
PLATFORM_FILE_API PlatformFileTextResult platform_file_facts_v2_analysis_raw_path_json(const char *platform_name,
  const char *path, uint32_t entry_address, uint8_t has_runtime_load_address, uint32_t runtime_load_address,
  const M68kAnalysisPolicy *analysis_policy);
PLATFORM_FILE_API PlatformFileTextResult platform_file_type_catalog_json(const char *backend_name);
PLATFORM_FILE_API PlatformFileTextResult platform_file_naming_catalog_json(const char *backend_name);
PLATFORM_FILE_API PlatformFileTextResult platform_file_os_metadata_catalog_json(const char *backend_name);
PLATFORM_FILE_API PlatformFileTextResult platform_file_api_input_struct_json(const char *backend_name,
  const char *library_name, const char *function_name, const char *input_name, const char *struct_name);
PLATFORM_FILE_API int platform_file_inspect_path_json_alloc(const char *backend_name, const char *path,
  char **out_text);
PLATFORM_FILE_API int platform_file_facts_v2_analysis_path_json_alloc(const char *backend_name, const char *path,
  const char *metadata_path, const char *entry_offsets, char **out_text);
PLATFORM_FILE_API int platform_file_facts_v2_analysis_raw_path_json_alloc(const char *platform_name,
  const char *path, uint32_t entry_address, uint32_t has_runtime_load_address, uint32_t runtime_load_address,
  const char *metadata_path, const char *entry_offsets, char **out_text);
PLATFORM_FILE_API int platform_file_effective_policy_path_json_alloc(const char *backend_name, const char *path,
  const char *metadata_path, const char *entry_offsets, char **out_text);
PLATFORM_FILE_API int platform_file_effective_policy_raw_path_json_alloc(const char *platform_name, const char *path,
  uint32_t entry_address, uint32_t has_runtime_load_address, uint32_t runtime_load_address,
  const char *metadata_path, const char *entry_offsets, char **out_text);
PLATFORM_FILE_API int platform_file_facts_v2_direct_rebuild_path_bytes_profile_alloc(const char *backend_name,
    const char *path, const char *metadata_path, const char *output_path, unsigned char **out_data,
    size_t *out_size, char **out_source_profile_json, char **out_direct_profile_json, char **out_error);
PLATFORM_FILE_API int platform_file_facts_v2_direct_rebuild_compare_path_bytes_profile_alloc(const char *backend_name,
    const char *path, const char *metadata_path, const char *output_path,
    unsigned char **out_data, size_t *out_size, char **out_source_profile_json, char **out_direct_profile_json,
    char **out_error);
PLATFORM_FILE_API int platform_file_facts_v2_direct_rebuild_buffer_bytes_profile_alloc(const char *backend_name,
    const unsigned char *data, size_t size, const char *metadata_path, const char *display_path,
    const char *output_path, unsigned char **out_data, size_t *out_size, char **out_source_profile_json,
    char **out_direct_profile_json, char **out_error);
PLATFORM_FILE_API int platform_file_facts_v2_direct_rebuild_compare_buffer_bytes_profile_alloc(const char *backend_name,
    const unsigned char *data, size_t size, const char *metadata_path,
    const char *display_path, const char *output_path, unsigned char **out_data, size_t *out_size,
    char **out_source_profile_json, char **out_direct_profile_json, char **out_error);
PLATFORM_FILE_API int platform_file_reproduction_compare_path_bytes_profile_alloc(const char *backend_name,
    const char *path, const char *metadata_path, const unsigned char *rebuilt_data, size_t rebuilt_size,
    char **out_compare_profile_json, char **out_error);
PLATFORM_FILE_API int platform_file_reproduction_compare_buffer_bytes_profile_alloc(const char *backend_name,
    const unsigned char *data, size_t size, const char *metadata_path, const char *display_path,
    const unsigned char *rebuilt_data, size_t rebuilt_size, char **out_compare_profile_json, char **out_error);
PLATFORM_FILE_API int platform_file_facts_v2_listing_artifact_path_create(const char *backend_name,
    const char *path, const char *metadata_path, const char *include_dir,
    PlatformFileListingArtifact **out_artifact, char **out_error);
PLATFORM_FILE_API int platform_file_facts_v2_listing_artifact_raw_path_create(const char *platform_name,
    const char *path, uint32_t entry_address, uint32_t has_runtime_load_address, uint32_t runtime_load_address,
    const char *metadata_path, const char *include_dir, PlatformFileListingArtifact **out_artifact,
    char **out_error);
PLATFORM_FILE_API int platform_file_facts_v2_listing_artifact_flat_m68k_buffer_create(
    const unsigned char *data, size_t size, const char *display_path, const char *metadata_path,
    const char *include_dir, PlatformFileListingArtifact **out_artifact, char **out_error);
PLATFORM_FILE_API int platform_file_facts_v2_listing_artifact_macos_code_buffer_create(
    const unsigned char *data, size_t size, const char *display_path, const char *metadata_path,
    const char *include_dir, PlatformFileListingArtifact **out_artifact, char **out_error);
PLATFORM_FILE_API int platform_file_facts_v2_listing_artifact_macos_hfs_code_resource_create(
    const unsigned char *data, size_t size, const char *hfs_path, int32_t resource_id,
    const char *metadata_path, const char *include_dir, PlatformFileListingArtifact **out_artifact,
    char **out_error);
PLATFORM_FILE_API int platform_file_facts_v2_listing_artifact_window_json_alloc(
    PlatformFileListingArtifact *artifact, uint32_t start, uint32_t count, char **out_text);
PLATFORM_FILE_API int platform_file_facts_v2_listing_artifact_addr_window_json_alloc(
    PlatformFileListingArtifact *artifact, int has_addr, uint32_t addr, uint32_t before, uint32_t after,
    char **out_text);
PLATFORM_FILE_API int platform_file_facts_v2_listing_artifact_source_offset_row_json_alloc(
    PlatformFileListingArtifact *artifact, int has_section, uint32_t section_index, uint32_t offset,
    char **out_text);
PLATFORM_FILE_API int platform_file_facts_v2_listing_artifact_runtime_address_row_json_alloc(
    PlatformFileListingArtifact *artifact, uint32_t address, char **out_text);
PLATFORM_FILE_API int platform_file_facts_v2_listing_artifact_anchor_window_json_alloc(
    PlatformFileListingArtifact *artifact, const char *anchor_code, uint32_t count, char **out_text);
PLATFORM_FILE_API int platform_file_facts_v2_listing_artifact_source_text_profile_alloc(
    PlatformFileListingArtifact *artifact, char **out_text, char **out_profile_json);
PLATFORM_FILE_API int platform_file_facts_v2_listing_artifact_summary_json_alloc(PlatformFileListingArtifact *artifact,
    char **out_text);
PLATFORM_FILE_API int platform_file_facts_v2_listing_artifact_analysis_json_alloc(PlatformFileListingArtifact *artifact,
    char **out_text);
PLATFORM_FILE_API int platform_file_facts_v2_listing_artifact_navigation_json_alloc(PlatformFileListingArtifact *artifact,
    char **out_text);
PLATFORM_FILE_API void platform_file_facts_v2_listing_artifact_destroy(PlatformFileListingArtifact *artifact);
PLATFORM_FILE_API int platform_file_type_catalog_json_alloc(const char *backend_name, char **out_text);
PLATFORM_FILE_API int platform_file_naming_catalog_json_alloc(const char *backend_name, char **out_text);
PLATFORM_FILE_API int platform_file_os_metadata_catalog_json_alloc(const char *backend_name, char **out_text);
PLATFORM_FILE_API int platform_file_api_input_struct_json_alloc(const char *backend_name, const char *library_name,
    const char *function_name, const char *input_name, const char *struct_name, char **out_text);
PLATFORM_FILE_API int platform_file_macos_hfs_code_summary_json_alloc(const unsigned char *data, size_t size,
    const char *hfs_path, char **out_text);
PLATFORM_FILE_API int platform_file_macos_hfs_code_resource_bytes_alloc(const unsigned char *data, size_t size,
    const char *hfs_path, int32_t resource_id, unsigned char **out_data, size_t *out_size, char **out_error);
PLATFORM_FILE_API int platform_file_macos_hfs_code_resource_payload_bytes_alloc(const unsigned char *data, size_t size,
    const char *hfs_path, int32_t resource_id, unsigned char **out_data, size_t *out_size, char **out_error);
PLATFORM_FILE_API int platform_file_decompression_identify_path_range_json_alloc(const char *provider_id,
    const char *provider_path, const char *path, uint32_t offset, uint32_t size, char **out_text);
PLATFORM_FILE_API int platform_file_decompression_decompress_path_range_json_alloc(const char *provider_id,
    const char *provider_path, const char *path, uint32_t offset, uint32_t size, const char *output_path,
    char **out_text);
PLATFORM_FILE_API int platform_file_decompression_decompress_section_range_json_alloc(const char *backend_name,
    const char *path, uint32_t section_index, uint32_t offset, uint32_t size, const char *output_path,
    char **out_text);
PLATFORM_FILE_API int platform_file_decompression_materialize_self_decrunch_event_json_alloc(const char *backend_name,
    const char *path, const char *event_id, const char *output_path, char **out_text);
PLATFORM_FILE_API int platform_file_decompression_materialize_recognized_unpacker_event_json_alloc(
    const char *backend_name, const char *path, const char *event_id, const char *output_path, char **out_text);
PLATFORM_FILE_API int platform_file_assemble_source_path_bytes_profile_alloc(const char *backend_name,
    const char *include_dir, const char *path, const char *target_cpu_name, unsigned char **out_data,
    size_t *out_size, char **out_profile_json, char **out_error);
PLATFORM_FILE_API int platform_file_assemble_source_path_to_output_bytes_profile_alloc(const char *backend_name,
    const char *include_dir, const char *path, const char *output_path, const char *target_cpu_name,
    unsigned char **out_data, size_t *out_size, char **out_profile_json, char **out_error);
PLATFORM_FILE_API int platform_file_assemble_source_text_bytes_profile_alloc(const char *backend_name,
    const char *include_dir, const char *source_text, const char *target_cpu_name, unsigned char **out_data,
    size_t *out_size, char **out_profile_json, char **out_error);
PLATFORM_FILE_API int platform_file_assemble_source_text_to_output_bytes_profile_alloc(const char *backend_name,
    const char *include_dir, const char *source_text, const char *output_path, const char *target_cpu_name,
    unsigned char **out_data, size_t *out_size, char **out_profile_json, char **out_error);
PLATFORM_FILE_API int platform_file_analysis_policy_add_register_seed_arg(M68kAnalysisPolicy *policy,
  const char *text);
PLATFORM_FILE_API int platform_file_analysis_policy_add_entry_point_arg(M68kAnalysisPolicy *policy, const char *text);
PLATFORM_FILE_API M68kAnalysisPolicy *platform_file_analysis_policy_create(uint8_t max_cpu);
PLATFORM_FILE_API void platform_file_analysis_policy_destroy(M68kAnalysisPolicy *policy);
/* Generic metadata only. Platform-derived policy must use the platform-aware loader. */
PLATFORM_FILE_API int platform_file_analysis_policy_load_target_metadata(M68kAnalysisPolicy *policy, const char *path,
  M68kDiagSink diagnostics);
PLATFORM_FILE_API int platform_file_analysis_policy_load_target_metadata_for_platform(M68kAnalysisPolicy *policy,
  const char *path, const char *platform_name, M68kDiagSink diagnostics);
PLATFORM_FILE_API void platform_file_free_text(char *text);
PLATFORM_FILE_API void platform_file_free_bytes(unsigned char *data);

#endif
