#include "platform_file_lib.h"
#include "platform_file_internal.h"
#include "json_builder.h"
#include "m68k_analysis_facts_v2.h"
#include "m68k_assembler_app.h"
#include "m68k_assembler.h"
#include "m68k_assembler_policy.h"
#include "m68k_backend.h"
#include "m68k_bitset.h"
#include "m68k_decode_ir.h"
#include "m68k_fact_ir.h"
#include "m68k_instruction_spec.h"
#include "m68k_ir_codec.h"
#include "m68k_object.h"
#include "m68k_parse_util.h"
#include "m68k_reproduction_compare.h"
#include "m68k_render_lookup_internal.h"
#include "m68k_simulator.h"
#include "m68k_source_pipeline.h"
#include "m68k_source_ir_render.h"
#include "platform_atari_st.h"
#include "platform_amiga_disk.h"
#include "platform_common.h"
#include "platform_file_decompression.h"
#include "platform_macos_hfs.h"
#include "platform_macos_resource.h"
#include "platform_executable_summary.h"
#include "restored_source_model.h"
#include "util_arena.h"
#include "generated/amiga_hunk_file_runtime.h"
#include "generated/amiga_os_runtime.h"
#include "generated/mac_os_runtime.h"
#include "generated/platform_executable_formats.h"

#include <ctype.h>
#include <inttypes.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define PLATFORM_SELF_DECRUNCH_MEMORY_LIMIT (2U * 1024U * 1024U)
#define PLATFORM_SELF_DECRUNCH_RUNTIME_LITERAL_SLOP 65536U
#define PLATFORM_SELF_DECRUNCH_STEP_LIMIT (2U * 1024U * 1024U)
#define PLATFORM_PROVIDER_WRAPPER_STEP_LIMIT (32U * 1024U * 1024U)

static void platform_file_add_error(M68kDiagList *diagnostics, const char *message);
static double elapsed_seconds(clock_t start_ticks, clock_t end_ticks);

static size_t platform_self_decrunch_step_limit_for_output_local(uint32_t output_size) {
  size_t step_limit = output_size > PLATFORM_PROVIDER_WRAPPER_STEP_LIMIT / 64U ?
    PLATFORM_PROVIDER_WRAPPER_STEP_LIMIT : (size_t)output_size * 64U;
  if (step_limit < PLATFORM_SELF_DECRUNCH_STEP_LIMIT) step_limit = PLATFORM_SELF_DECRUNCH_STEP_LIMIT;
  return step_limit;
}
static void platform_file_add_warning(M68kDiagList *diagnostics, const char *message);
static int read_file_to_buffer(const char *path, unsigned char **out_data, size_t *out_size,
    M68kDiagSink diagnostics);
static int load_object_from_path(const M68kBackend *backend, const char *path, M68kObject *object,
    M68kDiagSink diagnostics);
static int load_raw_object_from_path(const char *platform_name, const char *path, M68kObject *object,
    M68kDiagSink diagnostics);
static int load_raw_object_from_buffer(const char *platform_name, const unsigned char *data, size_t size,
    M68kObject *object, M68kDiagSink diagnostics);
static int load_flat_m68k_object_from_buffer(const unsigned char *data, size_t size, M68kObject *object,
    M68kDiagSink diagnostics);
static int configure_flat_m68k_buffer_policy(M68kAnalysisPolicy *policy, const M68kObject *object,
    const char *metadata_path, M68kDiagList *diagnostics);
static int json_builder_append_facts_v2_profile(JsonBuilder *builder, const M68kFactsV2Profile *profile);
static int append_analysis_restored_source_model_json(JsonBuilder *builder, const char *backend_name,
    const M68kObject *object, const M68kRenderPlan *source_plan);
static uint32_t read_be32_local(const uint8_t *data);
static int write_bytes_to_path_local(const char *path, const unsigned char *data, size_t size,
    M68kDiagList *diagnostics);
static const char *self_decrunch_sim_stop_reason_name_local(uint8_t stop_reason);
static int platform_self_decrunch_external_write_allowed_local(void *user, uint32_t address, uint8_t width);
static int platform_self_decrunch_external_read_local(void *user, uint32_t address, uint8_t width,
    uint32_t *out_value);
static uint8_t platform_self_decrunch_execution_cpu_local(const M68kObject *object,
    const M68kSourceAnalysisIR *analysis);
static uint32_t reachable_decrunch_entry_root_local(const M68kSectionAnalysisIR *section, size_t section_index,
    uint32_t fallback_entry, uint32_t transfer_offset, Arena *arena);
static int concrete_write_ranges_cover_span_local(const M68kSimConcreteRunTraceResult *result,
    uint32_t start, uint32_t size);
static int text_result_to_alloc(PlatformFileTextResult *result, char **out_text) {
  const char *message;
  if (out_text == NULL) return -1;
  *out_text = NULL;
  if (result == NULL) {
    *out_text = m68k_platform_dup_string("platform file operation failed");
    return -1;
  }
  if (m68k_diag_has_errors(&result->diagnostics) || result->text == NULL) {
    message = m68k_diag_first_message(&result->diagnostics);
    if (message == NULL || message[0] == '\0') message = "platform file operation failed";
    *out_text = m68k_platform_dup_string(message);
    platform_file_free_text(result->text);
    result->text = NULL;
    return -1;
  }
  *out_text = result->text;
  result->text = NULL;
  return 0;
}

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

static int macos_hfs_path_matches(const PlatformMacosHFSVolume *volume, const char *candidate_path,
    const char *requested_path) {
  size_t volume_len;
  if (candidate_path == NULL || requested_path == NULL) return 0;
  if (strcmp(candidate_path, requested_path) == 0) return 1;
  if (volume == NULL) return 0;
  volume_len = strlen(volume->volume_name);
  if (volume_len == 0U) return 0;
  if (strncmp(requested_path, volume->volume_name, volume_len) != 0) return 0;
  if (requested_path[volume_len] != '/' && requested_path[volume_len] != ':') return 0;
  return strcmp(candidate_path, requested_path + volume_len + 1U) == 0;
}

static int macos_copy_fork_or_error(const unsigned char *image_data, size_t image_size,
    const PlatformMacosHFSVolume *volume, const PlatformMacosHFSExtent extents[PLATFORM_MACOS_HFS_EXTENT_COUNT],
    uint32_t fork_size, unsigned char **out_data, char **out_error) {
  unsigned char *data;
  int copy_status;
  if (out_data == NULL || out_error == NULL) return -1;
  *out_data = NULL;
  *out_error = NULL;
  if (fork_size == 0U) return 0;
  data = (unsigned char *)malloc(fork_size);
  if (data == NULL) {
    *out_error = m68k_platform_dup_string("out of memory");
    return -1;
  }
  copy_status = platform_macos_hfs_copy_fork(image_data, image_size, volume, extents, fork_size, data, fork_size);
  if (copy_status != 0) {
    free(data);
    if (copy_status > 0)
      *out_error = m68k_platform_dup_string("Mac HFS overflow extents are not supported yet");
    else
      *out_error = m68k_platform_dup_string("Mac HFS fork materialization failed");
    return -1;
  }
  *out_data = data;
  return 0;
}

static int macos_append_fork_summary(JsonBuilder *builder, const char *name,
    const unsigned char *fork_data, uint32_t fork_size) {
  char sha256[65];
  sha256[0] = '\0';
  if (fork_data != NULL && fork_size > 0U) {
    if (m68k_platform_sha256_hex(fork_data, fork_size, sha256) != 0) return -1;
  }
  if (json_builder_appendf(builder, "\"%s\":{\"size\":%u,\"sha256\":", name, (unsigned)fork_size) != 0 ||
      json_builder_append_json_string(builder, sha256) != 0 ||
      json_builder_append(builder, "}") != 0) {
    return -1;
  }
  return 0;
}

static uint16_t macos_read_u16be_local(const unsigned char *data, size_t offset) {
  return (uint16_t)(((uint16_t)data[offset] << 8) | (uint16_t)data[offset + 1U]);
}

static int macos_append_fact_ref(JsonBuilder *builder, const char *fact_id, const char *fact_status,
    const char *parser_use) {
  if (json_builder_append(builder, "\"fact_id\":") != 0 ||
      json_builder_append_json_string(builder, fact_id) != 0 ||
      json_builder_append(builder, ",\"fact_status\":") != 0 ||
      json_builder_append_json_string(builder, fact_status) != 0 ||
      json_builder_append(builder, ",\"parser_use\":") != 0 ||
      json_builder_append_json_string(builder, parser_use) != 0) {
    return -1;
  }
  return 0;
}

static int macos_append_relocation_fixup_placeholder(JsonBuilder *builder) {
  if (json_builder_append(builder,
        ",\"relocation_fixups\":{\"status\":\"deferred\",\"reason\":"
        "\"Segment Loader relocation/fixup interpretation is not yet represented by the parser\",") != 0 ||
      macos_append_fact_ref(builder, "macos.segment_loader.relocation_fixups.deferred", "deferred",
        "deferred_only") != 0 ||
      json_builder_append(builder, "}") != 0) {
    return -1;
  }
  return 0;
}

static const char *macos_restored_source_role_for_range(const PlatformMacosCodeRange *range) {
  if (range == NULL) return "unknown";
  switch (range->kind) {
  case PLATFORM_MACOS_CODE_RANGE_CODE:
  case PLATFORM_MACOS_CODE_RANGE_CONFIRMED_CODE:
    return "code";
  case PLATFORM_MACOS_CODE_RANGE_CANDIDATE_CODE:
    return "candidate_code";
  case PLATFORM_MACOS_CODE_RANGE_DATA:
    return "data";
  case PLATFORM_MACOS_CODE_RANGE_CANDIDATE_UNRESOLVED_PREFIX:
    return "candidate_unresolved_prefix";
  case PLATFORM_MACOS_CODE_RANGE_METADATA:
    return "metadata";
  case PLATFORM_MACOS_CODE_RANGE_DEFERRED:
  default:
    return "unknown";
  }
}

#define MACOS_RESTORED_SOURCE_RANGE_CAPACITY (PLATFORM_MACOS_CODE_LAYOUT_RANGE_CAPACITY * 2U + 1U)

typedef struct MacosRestoredSourceRangeRecord {
  PlatformMacosRestoredSourceRangeView view;
  const char *rendering_kind;
  const char *rendering_text;
  const char *kb_record_id;
  const char *fact_id;
  const char *fact_status;
  const char *parser_use;
  const char *layout_kind;
} MacosRestoredSourceRangeRecord;

static int macos_restored_source_add_unknown_range(MacosRestoredSourceRangeRecord *records, size_t *count,
    uint32_t start, uint32_t end) {
  MacosRestoredSourceRangeRecord *record;
  if (end <= start) return 0;
  if (records == NULL || count == NULL || *count >= MACOS_RESTORED_SOURCE_RANGE_CAPACITY) return -1;
  record = &records[(*count)++];
  memset(record, 0, sizeof(*record));
  record->view.role = "unknown";
  record->view.start = start;
  record->view.size = end - start;
  record->view.end = end;
  record->view.status = "deferred";
  record->view.reason = "No accepted or candidate Mac CODE layout evidence covers this payload span.";
  record->view.provenance = "platform_file_lib.macos_hfs_code_summary";
  record->view.source_visible = 1U;
  record->rendering_kind = "placeholder";
  record->rendering_text = "unknown CODE payload bytes";
  record->kb_record_id = "macos.hfs_resource_fork.code_resources.mpw_application";
  return 0;
}

static int macos_append_segment_loader_fixup_inventory_record(JsonBuilder *builder,
    const PlatformMacosResourceInfo *resource) {
  PlatformMacosSegmentLoaderFixupInventory inventory;
  const char *status_name;
  if (builder == NULL || resource == NULL) return -1;
  if (platform_macos_segment_loader_fixup_inventory_from_code_metadata(&resource->code, resource->resource_id,
      resource->payload_size, &inventory) != 0) {
    return -1;
  }
  status_name = platform_macos_segment_loader_fixup_inventory_status_name(inventory.status);
  if (json_builder_appendf(builder,
        "{\"resource_type\":\"CODE\",\"resource_id\":%d,\"byte_space\":\"code_resource_payload\","
        "\"source_offset\":%u,\"size\":%u,\"source_range\":{\"start\":%u,\"end\":%u,\"size\":%u},"
        "\"classification\":",
        (int)resource->resource_id, (unsigned)inventory.source_offset, (unsigned)inventory.size,
        (unsigned)inventory.source_offset, (unsigned)inventory.end, (unsigned)inventory.size) != 0 ||
      json_builder_append_json_string(builder, status_name) != 0 ||
      json_builder_appendf(builder,
        ",\"status\":\"deferred\",\"parseable\":%s,\"source_visible\":true,"
        "\"encoding_byte_provenance\":{\"known\":%s,\"byte_space\":",
        inventory.status == PLATFORM_MACOS_SEGMENT_LOADER_FIXUP_INVENTORY_PARSEABLE ? "true" : "false",
        inventory.encoding_byte_provenance_known ? "true" : "false") != 0 ||
      (inventory.encoding_byte_provenance_known
        ? json_builder_append_json_string(builder, "code_resource_payload")
        : json_builder_append(builder, "null")) != 0 ||
      json_builder_append(builder, ",\"source_range\":") != 0 ||
      (inventory.encoding_byte_provenance_known
        ? json_builder_appendf(builder, "{\"start\":%u,\"end\":%u,\"size\":%u}",
            (unsigned)inventory.source_offset, (unsigned)inventory.end, (unsigned)inventory.size)
        : json_builder_append(builder, "null")) != 0 ||
      json_builder_append(builder, "},\"reason\":") != 0 ||
      json_builder_append_json_string(builder, inventory.reason) != 0 ||
      json_builder_append(builder, ",\"provenance\":") != 0 ||
      json_builder_append_json_string(builder, inventory.provenance) != 0 ||
      json_builder_append(builder,
        ",\"kb_record_id\":\"macos.hfs_resource_fork.code_resources.mpw_application\","
        "\"fact_id\":\"macos.segment_loader.relocation_fixups.deferred\","
        "\"fact_status\":\"deferred\",\"parser_use\":\"deferred_only\"}") != 0) {
    return -1;
  }
  return 0;
}

static int macos_append_segment_loader_fixup_inventory(JsonBuilder *builder,
    const PlatformMacosResourceInfo *resources, size_t resource_count) {
  size_t index;
  int first = 1;
  uint32_t counts[PLATFORM_MACOS_SEGMENT_LOADER_FIXUP_INVENTORY_MALFORMED + 1U] = {0};
  PlatformMacosSegmentLoaderFixupInventoryAggregate aggregate;
  for (index = 0U; index < resource_count; ++index) {
    PlatformMacosSegmentLoaderFixupInventory inventory;
    const PlatformMacosResourceInfo *resource = &resources[index];
    if (strcmp(resource->type, "CODE") != 0) continue;
    if (platform_macos_segment_loader_fixup_inventory_from_code_metadata(&resource->code, resource->resource_id,
        resource->payload_size, &inventory) != 0) {
      return -1;
    }
    if (inventory.status <= PLATFORM_MACOS_SEGMENT_LOADER_FIXUP_INVENTORY_MALFORMED) {
      counts[inventory.status]++;
    }
  }
  if (platform_macos_segment_loader_fixup_inventory_aggregate_counts(counts,
      sizeof(counts) / sizeof(counts[0]), &aggregate) != 0) {
    return -1;
  }
  if (json_builder_append(builder,
        ",\"segment_loader_fixup_inventory\":{\"model\":\"segment_loader_fixup_inventory_v1\","
        "\"authority\":\"c_owned\",\"status\":") != 0 ||
      json_builder_append_json_string(builder,
        platform_macos_segment_loader_fixup_inventory_aggregate_status_name(aggregate.status)) != 0 ||
      json_builder_append(builder, ",\"summary\":") != 0 ||
      json_builder_append_json_string(builder, aggregate.summary) != 0 ||
      json_builder_appendf(builder,
        ",\"counts\":{\"absent\":%u,\"parseable\":%u,\"unsupported\":%u,"
        "\"custom_unknown\":%u,\"malformed\":%u}",
        (unsigned)aggregate.absent_count, (unsigned)aggregate.parseable_count,
        (unsigned)aggregate.unsupported_count, (unsigned)aggregate.custom_unknown_count,
        (unsigned)aggregate.malformed_count) != 0 ||
      json_builder_append(builder, ",\"records\":[") != 0) {
    return -1;
  }
  for (index = 0U; index < resource_count; ++index) {
    const PlatformMacosResourceInfo *resource = &resources[index];
    if (strcmp(resource->type, "CODE") != 0) continue;
    if (!first && json_builder_append(builder, ",") != 0) return -1;
    first = 0;
    if (macos_append_segment_loader_fixup_inventory_record(builder, resource) != 0) return -1;
  }
  return json_builder_append(builder, "]}");
}

static int macos_restored_source_add_layout_range(MacosRestoredSourceRangeRecord *records, size_t *count,
    const PlatformMacosCodeRange *range, uint32_t start, uint32_t end) {
  MacosRestoredSourceRangeRecord *record;
  if (records == NULL || count == NULL || range == NULL || *count >= MACOS_RESTORED_SOURCE_RANGE_CAPACITY) return -1;
  record = &records[(*count)++];
  memset(record, 0, sizeof(*record));
  record->view.role = macos_restored_source_role_for_range(range);
  record->view.start = start;
  record->view.size = end - start;
  record->view.end = end;
  record->view.status = platform_macos_code_range_fact_status(range->evidence);
  record->view.reason = platform_macos_code_range_evidence_name(range->evidence);
  record->view.provenance = "platform_file_lib.macos_hfs_code_summary";
  record->view.source_visible = 1U;
  record->view.contains_instruction =
    (range->kind == PLATFORM_MACOS_CODE_RANGE_CODE || range->kind == PLATFORM_MACOS_CODE_RANGE_CONFIRMED_CODE ||
      range->kind == PLATFORM_MACOS_CODE_RANGE_CANDIDATE_CODE)
      ? 1U
      : 0U;
  record->rendering_kind = "layout_range";
  record->rendering_text = platform_macos_code_range_kind_name(range->kind);
  record->kb_record_id = "macos.hfs_resource_fork.code_resources.mpw_application";
  record->fact_id = platform_macos_code_range_fact_id(range->evidence);
  record->fact_status = platform_macos_code_range_fact_status(range->evidence);
  record->parser_use = platform_macos_code_range_parser_use(range->evidence);
  record->layout_kind = platform_macos_code_range_kind_name(range->kind);
  return 0;
}

static int macos_collect_restored_source_ownership_ranges(const PlatformMacosCodeMetadata *code, uint32_t payload_size,
    MacosRestoredSourceRangeRecord *records, size_t *out_count, uint32_t *out_reference_range_index) {
  size_t index;
  uint32_t cursor = 0U;
  uint32_t reference_index = UINT32_MAX;
  size_t count = 0U;
  if (code != NULL) {
    for (index = 0U; index < code->layout_range_count; ++index) {
      const PlatformMacosCodeRange *range = &code->layout_ranges[index];
      uint32_t start = range->start_offset;
      uint32_t end = range->start_offset + range->size;
      if (range->size == 0U || start >= payload_size) continue;
      if (end > payload_size) end = payload_size;
      if (start > cursor) {
        if (macos_restored_source_add_unknown_range(records, &count, cursor, start) != 0) return -1;
      }
      if (strcmp(macos_restored_source_role_for_range(range), "candidate_code") == 0 && reference_index == UINT32_MAX)
        reference_index = (uint32_t)count;
      if (macos_restored_source_add_layout_range(records, &count, range, start, end) != 0) return -1;
      cursor = end > cursor ? end : cursor;
    }
  }
  if (payload_size > cursor) {
    if (macos_restored_source_add_unknown_range(records, &count, cursor, payload_size) != 0) return -1;
  }
  if (out_count != NULL) *out_count = count;
  if (out_reference_range_index != NULL) *out_reference_range_index = reference_index == UINT32_MAX ? 0U : reference_index;
  return 0;
}

static int macos_append_restored_source_ownership_ranges(JsonBuilder *builder,
    const MacosRestoredSourceRangeRecord *records, size_t count) {
  size_t index;
  if (json_builder_append(builder, "\"source_ownership_ranges\":[") != 0) return -1;
  for (index = 0U; index < count; ++index) {
    const MacosRestoredSourceRangeRecord *record = &records[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"role\":") != 0 ||
        json_builder_append_json_string(builder, record->view.role) != 0 ||
        json_builder_appendf(builder,
          ",\"byte_space\":\"code_resource_payload\",\"platform\":\"macos\",\"source_kind\":\"macos_code_resource\","
          "\"start\":%u,\"size\":%u,\"end\":%u,\"status\":",
          (unsigned)record->view.start, (unsigned)record->view.size, (unsigned)record->view.end) != 0 ||
        json_builder_append_json_string(builder, record->view.status) != 0 ||
        json_builder_append(builder, ",\"reason\":") != 0 ||
        json_builder_append_json_string(builder, record->view.reason) != 0 ||
        json_builder_append(builder,
          ",\"provenance\":\"platform_file_lib.macos_hfs_code_summary\",\"source_visible\":true,"
          "\"rendering\":{\"kind\":") != 0 ||
        json_builder_append_json_string(builder, record->rendering_kind) != 0 ||
        json_builder_append(builder, ",\"text\":") != 0 ||
        json_builder_append_json_string(builder, record->rendering_text) != 0 ||
        json_builder_append(builder, "},\"kb_record_id\":") != 0 ||
        json_builder_append_json_string(builder, record->kb_record_id) != 0) {
      return -1;
    }
    if (record->fact_id != NULL) {
      if (json_builder_append(builder, ",\"fact_id\":") != 0 ||
          json_builder_append_json_string(builder, record->fact_id) != 0 ||
          json_builder_append(builder, ",\"fact_status\":") != 0 ||
          json_builder_append_json_string(builder, record->fact_status) != 0 ||
          json_builder_append(builder, ",\"parser_use\":") != 0 ||
          json_builder_append_json_string(builder, record->parser_use) != 0 ||
          json_builder_append(builder, ",\"layout_kind\":") != 0 ||
          json_builder_append_json_string(builder, record->layout_kind) != 0) {
        return -1;
      }
    }
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  return json_builder_append(builder, "]");
}

static int macos_append_restored_source_coverage_verifier(JsonBuilder *builder,
    const PlatformMacosRestoredSourceCoverageVerifier *verifier) {
  if (builder == NULL || verifier == NULL) return -1;
  return json_builder_appendf(builder,
    ",\"source_coverage_verifier\":{\"ok\":%s,\"gap_count\":%u,\"overlap_count\":%u,"
    "\"invalid_instruction_ownership_count\":%u,\"explicit_unknown_missing_detail_count\":%u}",
    verifier->ok ? "true" : "false", (unsigned)verifier->gap_count, (unsigned)verifier->overlap_count,
    (unsigned)verifier->invalid_instruction_ownership_count,
    (unsigned)verifier->explicit_unknown_missing_detail_count);
}

static uint32_t macos_restored_source_reference_start(const MacosRestoredSourceRangeRecord *records, size_t count,
    uint32_t reference_range_index) {
  if (records == NULL || count == 0U || reference_range_index >= count) return 0U;
  return records[reference_range_index].view.start;
}

static uint32_t macos_restored_source_reference_size(const MacosRestoredSourceRangeRecord *records, size_t count,
    uint32_t reference_range_index) {
  if (records == NULL || count == 0U || reference_range_index >= count) return 0U;
  return records[reference_range_index].view.size;
}

static int macos_append_restored_source_reference_records(JsonBuilder *builder, const PlatformMacosResourceInfo *resource,
    const MacosRestoredSourceRangeRecord *records, size_t range_count, uint32_t reference_range_index) {
  uint32_t reference_start = macos_restored_source_reference_start(records, range_count, reference_range_index);
  uint32_t reference_size = macos_restored_source_reference_size(records, range_count, reference_range_index);
  uint32_t reference_end = reference_start + reference_size;
  uint32_t placeholder_ownership_index = reference_range_index;
  int emitted = 0;
  if (builder == NULL || resource == NULL) return -1;
  if (json_builder_append(builder, ",\"source_reference_records\":[") != 0) return -1;
  if (resource->resource_id != 0) {
    PlatformMacosSegmentLoaderFixupInventory inventory;
    if (platform_macos_segment_loader_fixup_inventory_from_code_metadata(&resource->code, resource->resource_id,
        resource->payload_size, &inventory) != 0) {
      return -1;
    }
    if (!inventory.encoding_byte_provenance_known) {
      reference_start = 0U;
      reference_size = 0U;
      reference_end = 0U;
      placeholder_ownership_index = 0U;
    } else {
      reference_start = inventory.source_offset;
      reference_size = inventory.size;
      reference_end = inventory.end;
    }
    if (json_builder_appendf(builder,
          "{\"kind\":\"segment_loader_fixup_placeholder\",\"ownership_range_index\":%u"
          ",\"resource_type\":\"CODE\",\"resource_id\":%d,\"byte_space\":\"code_resource_payload\","
          "\"source_offset\":%u,\"size\":%u,\"source_range\":{\"start\":%u,\"end\":%u,\"size\":%u},"
          "\"target\":\"unresolved_segment_loader_fixup\",\"status\":\"deferred\","
          "\"reason\":",
          (unsigned)placeholder_ownership_index, (int)resource->resource_id, (unsigned)reference_start,
          (unsigned)reference_size, (unsigned)reference_start, (unsigned)reference_end,
          (unsigned)reference_size) != 0 ||
        json_builder_append_json_string(builder, inventory.reason) != 0 ||
        json_builder_append(builder,
          ",\"provenance\":\"platform_file_lib.macos_hfs_code_summary\",\"source_visible\":true,"
          "\"rendering\":{\"kind\":\"placeholder\",\"text\":\"deferred Segment Loader relocation/fixup effect\"},"
          "\"kb_record_id\":\"macos.hfs_resource_fork.code_resources.mpw_application\","
          "\"fact_id\":\"macos.segment_loader.relocation_fixups.deferred\","
          "\"fact_status\":\"deferred\",\"parser_use\":\"deferred_only\"}") != 0) {
      return -1;
    }
    emitted = 1;
  }
  if (resource->resource_id == 0) {
    if (json_builder_appendf(builder,
          "%s{\"kind\":\"code0_routing_table\",\"resource_type\":\"CODE\",\"resource_id\":0,"
          "\"byte_space\":\"code_resource_payload\",\"source_offset\":%u,\"size\":%u,"
          "\"target\":\"CODE resource dispatch table\",\"status\":\"validated\","
          "\"reason\":\"CODE 0 jump-table metadata routes application CODE resources.\","
          "\"provenance\":\"platform_file_lib.macos_hfs_code_summary\",\"source_visible\":true,"
          "\"kb_record_id\":\"macos.hfs_resource_fork.code_resources.mpw_application\","
          "\"fact_id\":\"macos.jump_table.entries.accepted\","
          "\"fact_status\":\"validated\",\"parser_use\":\"accepted_parser_output\"}",
          emitted ? "," : "",
          (unsigned)resource->code.jump_table_offset_from_a5, (unsigned)resource->code.jump_table_length) != 0) {
      return -1;
    }
    emitted = 1;
  } else if (resource->code.first_jump_table_entry_offset != 0xffffU &&
      resource->code.jump_table_entry_count > 0U) {
    if (json_builder_appendf(builder,
          "%s{\"kind\":\"code0_dispatch_reference\",\"resource_type\":\"CODE\",\"resource_id\":%d,"
          "\"byte_space\":\"code0_jump_table\",\"source_offset\":%u,\"size\":%u,"
          "\"target\":\"CODE:%d\",\"status\":\"validated\","
          "\"reason\":\"CODE 0 segment jump-table span maps this CODE resource into the application dispatch table.\","
          "\"provenance\":\"platform_file_lib.macos_hfs_code_summary\",\"source_visible\":true,"
          "\"kb_record_id\":\"macos.hfs_resource_fork.code_resources.mpw_application\","
          "\"fact_id\":\"macos.code_resource.segment_jump_table_span.accepted\","
          "\"fact_status\":\"validated\",\"parser_use\":\"accepted_parser_output\"}",
          emitted ? "," : "", (int)resource->resource_id, (unsigned)resource->code.first_jump_table_entry_offset,
          (unsigned)((uint32_t)resource->code.jump_table_entry_count * 8U), (int)resource->resource_id) != 0) {
      return -1;
    }
    emitted = 1;
  }
  if (json_builder_appendf(builder,
        "%s{\"kind\":\"a5_world_context_placeholder\",\"ownership_range_index\":%u,"
        "\"resource_type\":\"CODE\",\"resource_id\":%d,\"byte_space\":\"code_resource_payload\","
        "\"source_offset\":%u,\"size\":0,\"target\":\"classic_mac_a5_world\","
        "\"status\":\"deferred\",\"reason\":\"Classic Mac A5/world lifetime and global-base context is visible but not proven accepted.\","
        "\"provenance\":\"platform_file_lib.macos_hfs_code_summary\",\"source_visible\":true,"
        "\"rendering\":{\"kind\":\"placeholder\",\"text\":\"deferred A5/world context\"},"
        "\"kb_record_id\":\"macos.hfs_resource_fork.code_resources.mpw_application\"}]",
        emitted ? "," : "", (unsigned)reference_range_index, (int)resource->resource_id,
        (unsigned)reference_start) != 0) {
    return -1;
  }
  return 0;
}

static int macos_append_a5_world_extension(JsonBuilder *builder, const PlatformMacosResourceInfo *resource) {
  if (resource == NULL) return -1;
  if (resource->resource_id == 0) {
    uint32_t jump_table_start = resource->code.jump_table_offset_from_a5;
    uint32_t jump_table_end = jump_table_start + resource->code.jump_table_length;
    uint32_t positive_global_start = jump_table_end;
    uint32_t positive_global_size = 0U;
    if (resource->code.above_a5_size > positive_global_start) {
      positive_global_size = resource->code.above_a5_size - positive_global_start;
    }
    return json_builder_appendf(builder,
      "\"a5_world\":{\"status\":\"layout_accepted_lifetime_deferred\",\"source_visible\":true,"
      "\"provenance\":\"platform_file_lib.macos_hfs_code_summary\","
      "\"fact_id\":\"macos.code_resource.0.jump_table_metadata\","
      "\"fact_status\":\"validated\",\"parser_use\":\"accepted_parser_output\","
      "\"reason\":\"CODE 0 records the Classic Mac A5-world layout; lifetime and type propagation remain deferred.\","
      "\"above_a5_size\":%u,\"below_a5_size\":%u,\"jump_table_offset_from_a5\":%u,"
      "\"jump_table_length\":%u,\"regions\":["
      "{\"kind\":\"a5_negative_globals\",\"base_register\":\"a5\",\"start\":-%u,\"end\":0,"
      "\"size\":%u,\"status\":\"layout_accepted_type_deferred\"},"
      "{\"kind\":\"code0_jump_table\",\"base_register\":\"a5\",\"start\":%u,\"end\":%u,"
      "\"size\":%u,\"status\":\"layout_accepted_targets_candidate\"},"
      "{\"kind\":\"a5_positive_globals\",\"base_register\":\"a5\",\"start\":%u,\"end\":%u,"
      "\"size\":%u,\"status\":\"layout_accepted_type_deferred\"}]}",
      (unsigned)resource->code.above_a5_size, (unsigned)resource->code.below_a5_size,
      (unsigned)jump_table_start, (unsigned)resource->code.jump_table_length,
      (unsigned)resource->code.below_a5_size, (unsigned)resource->code.below_a5_size,
      (unsigned)jump_table_start, (unsigned)jump_table_end, (unsigned)resource->code.jump_table_length,
      (unsigned)positive_global_start, (unsigned)resource->code.above_a5_size, (unsigned)positive_global_size);
  }
  return json_builder_append(builder,
    "\"a5_world\":{\"status\":\"context_in_code0_lifetime_deferred\",\"source_visible\":true,"
    "\"provenance\":\"platform_file_lib.macos_hfs_code_summary\","
    "\"fact_id\":\"macos.code_resource.0.jump_table_metadata\","
    "\"fact_status\":\"validated\",\"parser_use\":\"accepted_parser_output\","
    "\"reason\":\"A5-world layout is owned by CODE 0; this CODE resource may reference it but lifetime and slot types remain deferred.\","
    "\"layout_resource\":{\"resource_type\":\"CODE\",\"resource_id\":0}}");
}

static int macos_append_restored_source_packet(JsonBuilder *builder, const PlatformMacosResourceInfo *resource) {
  MacosRestoredSourceRangeRecord records[MACOS_RESTORED_SOURCE_RANGE_CAPACITY];
  PlatformMacosRestoredSourceRangeView views[MACOS_RESTORED_SOURCE_RANGE_CAPACITY];
  PlatformMacosRestoredSourceCoverageVerifier verifier;
  size_t range_count = 0U;
  size_t index;
  uint32_t reference_range_index = 0U;
  if (resource == NULL || strcmp(resource->type, "CODE") != 0) return json_builder_append(builder, "null");
  if (macos_collect_restored_source_ownership_ranges(&resource->code, resource->payload_size, records, &range_count,
        &reference_range_index) != 0)
    return -1;
  for (index = 0U; index < range_count; ++index) views[index] = records[index].view;
  if (platform_macos_restored_source_verify_ranges(views, range_count, resource->payload_size, &verifier) != 0)
    return -1;
  if (json_builder_append(builder,
        "{\"model\":\"restored_source_model_v1\",\"platform\":\"macos\","
        "\"source_kind\":\"macos_code_resource\",\"authority\":\"c_owned\","
        "\"round_trip_required\":false,") != 0 ||
      macos_append_restored_source_ownership_ranges(builder, records, range_count) != 0 ||
      macos_append_restored_source_coverage_verifier(builder, &verifier) != 0 ||
      macos_append_restored_source_reference_records(builder, resource, records, range_count, reference_range_index) != 0 ||
      json_builder_append(builder,
        ",\"platform_extensions\":{\"code_resource\":{\"resource_type\":\"CODE\",\"resource_id\":") != 0 ||
      json_builder_appendf(builder, "%d", (int)resource->resource_id) != 0 ||
      json_builder_appendf(builder,
        ",\"resource_name\":null,\"payload_size\":%u},"
        "\"address_model\":{\"payload_offset_space\":\"code_resource_payload\",\"local_source_offset_space\":\"selected_code_bytes\","
        "\"runtime_address_model\":\"classic_mac_segment_loader_deferred\",\"status\":\"deferred\","
        "\"provenance\":\"platform_file_lib.macos_hfs_code_summary\"},",
        (unsigned)resource->payload_size) != 0 ||
      macos_append_a5_world_extension(builder, resource) != 0 ||
      json_builder_append(builder, "}}") != 0) {
    return -1;
  }
  return 0;
}

static const char *macos_shared_executable_role(uint8_t kind) {
  switch (kind) {
  case PLATFORM_MACOS_CODE_RANGE_CODE:
  case PLATFORM_MACOS_CODE_RANGE_CONFIRMED_CODE:
    return "code";
  case PLATFORM_MACOS_CODE_RANGE_CANDIDATE_CODE:
    return "candidate_code";
  case PLATFORM_MACOS_CODE_RANGE_CANDIDATE_UNRESOLVED_PREFIX:
    return "candidate_unresolved_prefix";
  case PLATFORM_MACOS_CODE_RANGE_METADATA:
  case PLATFORM_MACOS_CODE_RANGE_DATA:
  case PLATFORM_MACOS_CODE_RANGE_DEFERRED:
  default:
    return "metadata";
  }
}

static int macos_append_shared_fact_fields(JsonBuilder *builder, const char *fact_id,
    const char *fact_status, const char *parser_use) {
  if (json_builder_append(builder,
        "\"kb_record_id\":\"macos.hfs_resource_fork.code_resources.mpw_application\",\"status\":") != 0 ||
      json_builder_append_json_string(builder, fact_status) != 0 ||
      json_builder_append(builder, ",") != 0 ||
      macos_append_fact_ref(builder, fact_id, fact_status, parser_use) != 0) {
    return -1;
  }
  return 0;
}

static int macos_append_shared_executable_ranges(JsonBuilder *builder,
    const PlatformMacosResourceInfo *resources, size_t resource_count) {
  size_t resource_index;
  int first = 1;
  if (json_builder_append(builder,
      "\"executable_model\":\"platform_executable_summary_v1\",\"executable_ranges\":[") != 0)
    return -1;
  for (resource_index = 0U; resource_index < resource_count; ++resource_index) {
    const PlatformMacosResourceInfo *resource = &resources[resource_index];
    const PlatformMacosCodeMetadata *code = &resource->code;
    size_t range_index;
    if (strcmp(resource->type, "CODE") != 0) continue;
    for (range_index = 0U; range_index < code->layout_range_count; ++range_index) {
      const PlatformMacosCodeRange *range = &code->layout_ranges[range_index];
      const char *fact_id = platform_macos_code_range_fact_id(range->evidence);
      const char *fact_status = platform_macos_code_range_fact_status(range->evidence);
      const char *parser_use = platform_macos_code_range_parser_use(range->evidence);
      if (!first && json_builder_append(builder, ",") != 0) return -1;
      first = 0;
      if (json_builder_append(builder, "{\"role\":") != 0 ||
          json_builder_append_json_string(builder, macos_shared_executable_role(range->kind)) != 0 ||
          json_builder_appendf(builder,
            ",\"resource_type\":\"CODE\",\"resource_id\":%d,"
            "\"stored_offset_space\":\"resource_fork_payload\",\"range_kind\":",
            (int)resource->resource_id) != 0 ||
          json_builder_append_json_string(builder, platform_macos_code_range_kind_name(range->kind)) != 0 ||
          json_builder_appendf(builder,
            ",\"load_offset\":%u,\"stored_offset\":%u,\"size\":%u,\"stored_size\":%u,"
            "\"entrypoint\":%s,\"evidence\":",
            (unsigned)range->start_offset, (unsigned)(resource->payload_offset + range->start_offset),
            (unsigned)range->size, (unsigned)range->size, range->entrypoint ? "true" : "false") != 0 ||
          json_builder_append_json_string(builder, platform_macos_code_range_evidence_name(range->evidence)) != 0 ||
          json_builder_append(builder, ",") != 0 ||
          macos_append_shared_fact_fields(builder, fact_id, fact_status, parser_use) != 0 ||
          json_builder_append(builder, "}") != 0) {
        return -1;
      }
    }
  }
  if (json_builder_append(builder, "],\"executable_deferred\":[{\"kind\":\"relocation_breadth\",") != 0 ||
      macos_append_shared_fact_fields(builder,
        PLATFORM_EXECUTABLE_FORMAT_FACT_MACOS_SEGMENT_LOADER_RELOCATION_FIXUPS_DEFERRED,
        "deferred", "deferred_only") != 0 ||
      json_builder_append(builder, "}]") != 0) {
    return -1;
  }
  return 0;
}

static int macos_append_orphan_ranges(JsonBuilder *builder, const PlatformMacosCodeMetadata *code) {
  size_t index;
  int first = 1;
  if (json_builder_append(builder, ",\"orphan_ranges\":[") != 0) return -1;
  for (index = 0U; index < code->layout_range_count; ++index) {
    const PlatformMacosCodeRange *range = &code->layout_ranges[index];
    const char *classification = NULL;
    const char *reason = NULL;
    const char *fact_id = "macos.code_resource.orphan_layout_ranges.candidate";
    const char *fact_status = "candidate";
    const char *parser_use = "candidate_only";
    if (range->kind == PLATFORM_MACOS_CODE_RANGE_CANDIDATE_UNRESOLVED_PREFIX) {
      classification = "candidate_unresolved_prefix";
      reason =
        "bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached through "
        "loader, stack, or fixup flow not yet modeled";
    } else if (range->kind == PLATFORM_MACOS_CODE_RANGE_DATA) {
      classification = "candidate_data_island";
      reason = "bytes before candidate byte-entry evidence; exact CODE entry rule remains deferred";
    } else if (range->kind == PLATFORM_MACOS_CODE_RANGE_DEFERRED) {
      classification = "deferred_code_or_data_island";
      reason = "no candidate byte-entry evidence found; code/data interpretation remains deferred";
      fact_id = "macos.code_resource.byte_entry_rule.unknown";
      fact_status = "deferred";
      parser_use = "deferred_only";
    } else {
      continue;
    }
    if (!first && json_builder_append(builder, ",") != 0) return -1;
    first = 0;
    if (json_builder_append(builder, "{\"classification\":") != 0 ||
        json_builder_append_json_string(builder, classification) != 0 ||
        json_builder_appendf(builder, ",\"start\":%u,\"size\":%u,\"end\":%u,\"evidence\":",
          (unsigned)range->start_offset, (unsigned)range->size,
          (unsigned)(range->start_offset + range->size)) != 0 ||
        json_builder_append_json_string(builder, platform_macos_code_range_evidence_name(range->evidence)) != 0 ||
        json_builder_append(builder, ",\"reason\":") != 0 ||
        json_builder_append_json_string(builder, reason) != 0 ||
        json_builder_append(builder, ",") != 0 ||
        macos_append_fact_ref(builder, fact_id, fact_status, parser_use) != 0 ||
        json_builder_append(builder, "}") != 0) {
      return -1;
    }
  }
  return json_builder_append(builder, "]");
}

static int macos_append_code0_jump_table(JsonBuilder *builder, const PlatformMacosCodeMetadata *code,
    uint32_t payload_size) {
  uint32_t entry_count;
  if (code->kind != PLATFORM_MACOS_CODE_RESOURCE_JUMP_TABLE_SEGMENT) return 0;
  if (payload_size < 16U) return 0;
  entry_count = code->jump_table_length / 8U;
  if (json_builder_appendf(builder,
        ",\"jump_table\":{\"kind\":\"code0_jump_table\",\"start\":16,\"size\":%u,\"end\":%u,"
        "\"entry_size\":8,\"entry_count\":%u,\"trailing_bytes\":%u,",
        (unsigned)code->jump_table_length, (unsigned)(16U + code->jump_table_length),
        (unsigned)entry_count, (unsigned)(code->jump_table_length % 8U)) != 0 ||
      macos_append_fact_ref(builder, "macos.jump_table.entries.accepted", "validated",
        "accepted_parser_output") != 0 ||
      json_builder_append(builder, "}") != 0) {
    return -1;
  }
  return 0;
}

static int macos_append_code_metadata(JsonBuilder *builder, const PlatformMacosResourceInfo *resource) {
  const PlatformMacosCodeMetadata *code;
  const char *kind = "none";
  const char *resource_fact_id = "";
  const char *resource_fact_status = "unsupported";
  const char *resource_parser_use = "unsupported_only";
  size_t index;
  if (resource == NULL) return -1;
  code = &resource->code;
  if (code->kind == PLATFORM_MACOS_CODE_RESOURCE_JUMP_TABLE_SEGMENT) {
    kind = "jump_table_segment";
    resource_fact_id = "macos.code_resource.0.jump_table_metadata";
    resource_fact_status = "validated";
    resource_parser_use = "accepted_parser_output";
  } else if (code->kind == PLATFORM_MACOS_CODE_RESOURCE_CODE_SEGMENT) {
    kind = "code_segment";
    resource_fact_id = "macos.resource_fork.code_resources.accepted";
    resource_fact_status = "validated";
    resource_parser_use = "accepted_parser_output";
  }
  if (json_builder_append(builder, "{\"kind\":") != 0 ||
      json_builder_append_json_string(builder, kind) != 0 ||
      json_builder_append(builder, ",\"kb_record_id\":\"macos.hfs_resource_fork.code_resources.mpw_application\","
        "\"fact_id\":") != 0 ||
      json_builder_append_json_string(builder, resource_fact_id) != 0 ||
      json_builder_append(builder, ",\"fact_status\":") != 0 ||
      json_builder_append_json_string(builder, resource_fact_status) != 0 ||
      json_builder_append(builder, ",\"parser_use\":") != 0 ||
      json_builder_append_json_string(builder, resource_parser_use) != 0 ||
      json_builder_appendf(builder,
        ",\"above_a5_size\":%u,\"below_a5_size\":%u,\"jump_table_length\":%u,"
        "\"jump_table_offset_from_a5\":%u,\"first_jump_table_entry_offset\":%u,"
        "\"jump_table_entry_count\":%u,\"far_model\":%s,"
        "\"far_model_header\":{\"near_entry_start_a5_offset\":%u,\"near_entry_count\":%u,"
        "\"far_entry_start_a5_offset\":%u,\"far_entry_count\":%u,"
        "\"a5_relocation_info_offset\":%u,\"current_a5_value\":%u,"
        "\"segment_relocation_info_offset\":%u,\"segment_load_address\":%u},\"layout_ranges\":[",
        (unsigned)code->above_a5_size, (unsigned)code->below_a5_size,
        (unsigned)code->jump_table_length, (unsigned)code->jump_table_offset_from_a5,
        (unsigned)code->first_jump_table_entry_offset, (unsigned)code->jump_table_entry_count,
        code->far_model ? "true" : "false", (unsigned)code->near_entry_start_a5_offset,
        (unsigned)code->near_entry_count, (unsigned)code->far_entry_start_a5_offset,
        (unsigned)code->far_entry_count, (unsigned)code->a5_relocation_info_offset,
        (unsigned)code->current_a5_value, (unsigned)code->segment_relocation_info_offset,
        (unsigned)code->segment_load_address) != 0) {
    return -1;
  }
  for (index = 0U; index < code->layout_range_count; ++index) {
    const PlatformMacosCodeRange *range = &code->layout_ranges[index];
    if (index > 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"kind\":") != 0 ||
        json_builder_append_json_string(builder, platform_macos_code_range_kind_name(range->kind)) != 0 ||
        json_builder_appendf(builder, ",\"start\":%u,\"size\":%u,\"end\":%u,\"entrypoint\":%s,\"evidence\":",
          (unsigned)range->start_offset, (unsigned)range->size,
          (unsigned)(range->start_offset + range->size), range->entrypoint ? "true" : "false") != 0 ||
        json_builder_append_json_string(builder, platform_macos_code_range_evidence_name(range->evidence)) != 0 ||
        json_builder_append(builder, ",\"fact_id\":") != 0 ||
        json_builder_append_json_string(builder, platform_macos_code_range_fact_id(range->evidence)) != 0 ||
        json_builder_append(builder, ",\"fact_status\":") != 0 ||
        json_builder_append_json_string(builder, platform_macos_code_range_fact_status(range->evidence)) != 0 ||
        json_builder_append(builder, ",\"parser_use\":") != 0 ||
        json_builder_append_json_string(builder, platform_macos_code_range_parser_use(range->evidence)) != 0 ||
        json_builder_append(builder, "}") != 0) {
      return -1;
    }
  }
  if (json_builder_append(builder, "]") != 0 ||
      macos_append_code0_jump_table(builder, code, resource->payload_size) != 0 ||
      macos_append_orphan_ranges(builder, code) != 0 ||
      macos_append_relocation_fixup_placeholder(builder) != 0 ||
      json_builder_append(builder, ",\"restored_source\":") != 0 ||
      macos_append_restored_source_packet(builder, resource) != 0 ||
      json_builder_append(builder, "}") != 0) {
    return -1;
  }
  return 0;
}

static int macos_copy_resource_name(char *buf, size_t buf_size, const PlatformMacosResourceFork *resource_fork_info,
    const unsigned char *resource_fork, size_t resource_fork_size, const PlatformMacosResourceInfo *resource) {
  size_t offset;
  size_t raw_length;
  size_t length;
  size_t index;
  if (buf == NULL || buf_size == 0U || resource == NULL) return -1;
  buf[0] = '\0';
  if (resource->name_offset < 0) return 0;
  if (resource_fork_info == NULL || resource_fork == NULL) return -1;
  offset = (size_t)resource_fork_info->name_list_offset + (size_t)(uint16_t)resource->name_offset;
  if (offset >= resource_fork_size) return -1;
  raw_length = resource_fork[offset];
  if (offset + 1U > resource_fork_size || raw_length > resource_fork_size - offset - 1U) return -1;
  length = raw_length;
  if (length >= buf_size) length = buf_size - 1U;
  for (index = 0U; index < length; ++index) {
    unsigned char ch = resource_fork[offset + 1U + index];
    buf[index] = (ch >= 0x20U && ch < 0x7FU) ? (char)ch : '?';
  }
  buf[length] = '\0';
  return 0;
}

static int macos_append_resource_name(JsonBuilder *builder, const PlatformMacosResourceFork *resource_fork_info,
    const unsigned char *resource_fork, size_t resource_fork_size, const PlatformMacosResourceInfo *resource) {
  char name[256];
  if (macos_copy_resource_name(name, sizeof(name), resource_fork_info, resource_fork, resource_fork_size, resource) != 0)
    return -1;
  if (name[0] == '\0') return json_builder_append(builder, "null");
  return json_builder_append_json_string(builder, name);
}

static int macos_append_code_resources(JsonBuilder *builder, const PlatformMacosResourceFork *resource_fork_info,
    const unsigned char *resource_fork, size_t resource_fork_size, const PlatformMacosResourceInfo *resources,
    size_t resource_count) {
  size_t index;
  int first = 1;
  if (json_builder_append(builder, "\"code_resources\":[") != 0) return -1;
  for (index = 0U; index < resource_count; ++index) {
    const PlatformMacosResourceInfo *resource = &resources[index];
    char sha256[65];
    if (strcmp(resource->type, "CODE") != 0) continue;
    if (resource->payload_offset > resource_fork_size ||
        resource->payload_size > resource_fork_size - resource->payload_offset ||
        m68k_platform_sha256_hex(resource_fork + resource->payload_offset, resource->payload_size, sha256) != 0)
      return -1;
    if (!first && json_builder_append(builder, ",") != 0) return -1;
    first = 0;
    if (json_builder_appendf(builder,
          "{\"type\":\"CODE\",\"id\":%d,\"name\":",
          (int)resource->resource_id) != 0 ||
        macos_append_resource_name(builder, resource_fork_info, resource_fork, resource_fork_size, resource) != 0 ||
        json_builder_appendf(builder, ",\"payload_offset\":%u,\"payload_size\":%u,\"sha256\":",
          (unsigned)resource->payload_offset,
          (unsigned)resource->payload_size) != 0 ||
        json_builder_append_json_string(builder, sha256) != 0 ||
        json_builder_append(builder, ",\"code\":") != 0 ||
        macos_append_code_metadata(builder, resource) != 0 ||
        json_builder_append(builder, "}") != 0) {
      return -1;
    }
  }
  return json_builder_append(builder, "]");
}

static int macos_append_resource_types(JsonBuilder *builder, const PlatformMacosResourceTypeInfo *types,
    size_t type_count) {
  size_t index;
  if (json_builder_append(builder, "\"types\":[") != 0) return -1;
  for (index = 0U; index < type_count; ++index) {
    if (index > 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"type\":") != 0 ||
        json_builder_append_json_string(builder, types[index].type) != 0 ||
        json_builder_appendf(builder, ",\"count\":%u}", (unsigned)types[index].count) != 0) {
      return -1;
    }
  }
  return json_builder_append(builder, "]");
}

static const PlatformMacosResourceInfo *macos_find_code0_resource(const PlatformMacosResourceInfo *resources,
    size_t resource_count) {
  size_t index;
  for (index = 0U; index < resource_count; ++index) {
    const PlatformMacosResourceInfo *resource = &resources[index];
    if (strcmp(resource->type, "CODE") == 0 && resource->resource_id == 0) return resource;
  }
  return NULL;
}

static int macos_code0_entry_is_unloaded_loadseg_for_segment(const unsigned char *code0_payload,
    uint32_t code0_payload_size, uint32_t code0_entry_offset, int16_t segment_id, uint32_t *routine_offset) {
  uint16_t segment_word;
  if (code0_payload == NULL || code0_entry_offset > code0_payload_size ||
      code0_payload_size - code0_entry_offset < 8U) {
    return 0;
  }
  if (macos_read_u16be_local(code0_payload, code0_entry_offset + 2U) != 0x3F3CU ||
      macos_read_u16be_local(code0_payload, code0_entry_offset + 6U) != 0xA9F0U) {
    return 0;
  }
  segment_word = macos_read_u16be_local(code0_payload, code0_entry_offset + 4U);
  if (segment_word != (uint16_t)segment_id) return 0;
  if (routine_offset != NULL) *routine_offset = macos_read_u16be_local(code0_payload, code0_entry_offset);
  return 1;
}

static int macos_code0_entry_is_far_model_loadseg_for_segment(const unsigned char *code0_payload,
    uint32_t code0_payload_size, uint32_t code0_entry_offset, int16_t segment_id, uint32_t *routine_offset) {
  uint16_t segment_word;
  if (code0_payload == NULL || code0_entry_offset > code0_payload_size ||
      code0_payload_size - code0_entry_offset < 8U) {
    return 0;
  }
  segment_word = macos_read_u16be_local(code0_payload, code0_entry_offset);
  if (segment_word != (uint16_t)segment_id ||
      macos_read_u16be_local(code0_payload, code0_entry_offset + 2U) != 0xA9F0U) {
    return 0;
  }
  if (routine_offset != NULL) {
    *routine_offset = ((uint32_t)macos_read_u16be_local(code0_payload, code0_entry_offset + 4U) << 16U) |
      (uint32_t)macos_read_u16be_local(code0_payload, code0_entry_offset + 6U);
  }
  return 1;
}

static int macos_append_segment_routine_candidate(JsonBuilder *builder, uint32_t candidate_index,
    uint32_t jump_table_entry_index, uint32_t jump_table_offset, uint32_t code0_entry_offset,
    uint32_t a5_jump_table_base_offset, uint32_t routine_offset, int16_t segment_id, const char *entry_state,
    const char *routine_offset_space, int needs_comma) {
  const MacOsCallInfo *loadseg_call = mac_os_find_call_by_opword(0xA9F0U);
  int has_payload_relative_expression =
    routine_offset_space != NULL && strcmp(routine_offset_space, "code_resource_payload") == 0;
  if (needs_comma && json_builder_append(builder, ",") != 0) return -1;
  if (json_builder_appendf(builder,
        "{\"index\":%u,\"jump_table_entry_index\":%u,\"jump_table_offset\":%u,"
        "\"code0_payload_offset\":%u,\"entry_code_offset\":%u,"
        "\"a5_entry_offset\":%u,\"a5_callable_offset\":%u,\"callable_entry_byte_offset\":2,"
        "\"callable_entry_kind\":\"segment_loader_trap_word\","
        "\"routine_offset_from_segment\":%u,\"target_resource_id\":%d,"
        "\"entry_state\":\"%s\",\"routine_offset_space\":\"%s\","
        "\"classification\":\"candidate_routine_entry\",",
        (unsigned)candidate_index, (unsigned)jump_table_entry_index, (unsigned)jump_table_offset,
        (unsigned)code0_entry_offset, (unsigned)(code0_entry_offset + 2U),
        (unsigned)(a5_jump_table_base_offset + jump_table_offset),
        (unsigned)(a5_jump_table_base_offset + jump_table_offset + 2U),
        (unsigned)routine_offset, (int)segment_id, entry_state, routine_offset_space) != 0 ||
      json_builder_append(builder, "\"platform_call\":{\"platform\":\"macos\",\"kind\":\"trap_constant\","
        "\"opword\":43504,\"symbol_name\":") != 0 ||
      json_builder_append_json_string(builder, loadseg_call != NULL ? loadseg_call->name : "_LoadSeg") != 0 ||
      json_builder_append(builder, ",\"family\":") != 0 ||
      json_builder_append_json_string(builder, loadseg_call != NULL ? loadseg_call->family : "Traps") != 0 ||
      json_builder_append(builder, ",\"source\":") != 0 ||
      json_builder_append_json_string(builder, loadseg_call != NULL ? loadseg_call->source_path : "") != 0 ||
      json_builder_appendf(builder, ",\"line\":%u},", loadseg_call != NULL ? (unsigned)loadseg_call->line : 0U) != 0) {
    return -1;
  }
  if (has_payload_relative_expression) {
    if (json_builder_appendf(builder,
          "\"stored_offset_expression\":{\"kind\":\"label_relative_offset\","
          "\"encoded_width\":4,\"byte_order\":\"big\",\"directive\":\"dc.l\","
          "\"source_resource_id\":0,\"source_payload_offset\":%u,"
          "\"target_resource_id\":%d,\"target_payload_offset\":%u,"
          "\"base_resource_id\":%d,\"base_payload_offset\":0,"
          "\"value\":%u,\"value_space\":\"code_resource_payload\","
          "\"renderer\":\"generic_label_minus_base\"},",
          (unsigned)(code0_entry_offset + 4U), (int)segment_id, (unsigned)routine_offset,
          (int)segment_id, (unsigned)routine_offset) != 0) {
      return -1;
    }
  }
  if (macos_append_fact_ref(builder, "macos.code_resource.jump_table.routine_offsets.candidate",
        "candidate", "candidate_only") != 0 ||
      json_builder_append(builder, "}") != 0) {
    return -1;
  }
  return 0;
}

static int macos_append_segment_routine_candidates(JsonBuilder *builder, const PlatformMacosResourceInfo *resource,
    const PlatformMacosResourceInfo *code0_resource, const unsigned char *code0_payload, uint32_t code0_payload_size) {
  uint32_t index;
  uint32_t first_offset;
  uint32_t count;
  uint32_t emitted = 0U;
  if (json_builder_append(builder, ",\"routine_entry_candidates\":[") != 0) return -1;
  if (resource == NULL || code0_resource == NULL || code0_payload == NULL || code0_payload_size < 16U) {
    return json_builder_append(builder, "]");
  }
  first_offset = resource->code.first_jump_table_entry_offset;
  count = resource->code.jump_table_entry_count;
  if (resource->code.far_model &&
      (resource->code.near_entry_count > 0U || resource->code.far_entry_count > 0U)) {
    uint32_t far_index;
    uint32_t far_count = resource->code.far_entry_count;
    count = resource->code.near_entry_count;
    first_offset = resource->code.near_entry_start_a5_offset;
    for (index = 0U; index < count; ++index) {
      uint32_t jump_table_offset = first_offset + index * 8U;
      uint32_t code0_entry_offset = 16U + jump_table_offset;
      uint32_t routine_offset;
      if (jump_table_offset > UINT32_MAX - 8U || code0_entry_offset > code0_payload_size - 8U) break;
      if (!macos_code0_entry_is_far_model_loadseg_for_segment(
            code0_payload, code0_payload_size, code0_entry_offset, resource->resource_id, &routine_offset)) {
        continue;
      }
      if (macos_append_segment_routine_candidate(builder, emitted, jump_table_offset / 8U, jump_table_offset,
            code0_entry_offset, code0_resource->code.jump_table_offset_from_a5, routine_offset, resource->resource_id,
            "far_model_loadseg", "code_resource_payload", emitted > 0U) != 0) {
        return -1;
      }
      emitted++;
    }
    first_offset = resource->code.far_entry_start_a5_offset;
    for (far_index = 0U; far_index < far_count; ++far_index) {
      uint32_t jump_table_offset = first_offset + far_index * 8U;
      uint32_t code0_entry_offset = 16U + jump_table_offset;
      uint32_t routine_offset;
      if (jump_table_offset > UINT32_MAX - 8U || code0_entry_offset > code0_payload_size - 8U) break;
      if (!macos_code0_entry_is_far_model_loadseg_for_segment(
            code0_payload, code0_payload_size, code0_entry_offset, resource->resource_id, &routine_offset)) {
        continue;
      }
      if (macos_append_segment_routine_candidate(builder, emitted, jump_table_offset / 8U, jump_table_offset,
            code0_entry_offset, code0_resource->code.jump_table_offset_from_a5, routine_offset, resource->resource_id,
            "far_model_loadseg", "code_resource_payload", emitted > 0U) != 0) {
        return -1;
      }
      emitted++;
    }
  } else if (first_offset != 0xFFFFU && count > 0U) {
    for (index = 0U; index < count; ++index) {
      uint32_t jump_table_offset = first_offset + index * 8U;
      uint32_t code0_entry_offset = 16U + jump_table_offset;
      uint32_t routine_offset;
      if (jump_table_offset > UINT32_MAX - 8U || code0_entry_offset > code0_payload_size - 8U) break;
      if (!macos_code0_entry_is_unloaded_loadseg_for_segment(
            code0_payload, code0_payload_size, code0_entry_offset, resource->resource_id, &routine_offset)) {
        continue;
      }
      if (macos_append_segment_routine_candidate(builder, emitted, jump_table_offset / 8U, jump_table_offset,
            code0_entry_offset, code0_resource->code.jump_table_offset_from_a5, routine_offset, resource->resource_id,
            "unloaded_loadseg", "candidate_code_range", emitted > 0U) != 0) {
        return -1;
      }
      emitted++;
    }
  } else {
    uint32_t jump_table_size = ((uint32_t)macos_read_u16be_local(code0_payload, 8U) << 16U) |
      (uint32_t)macos_read_u16be_local(code0_payload, 10U);
    if (jump_table_size > code0_payload_size - 16U) jump_table_size = code0_payload_size - 16U;
    for (index = 0U; index + 8U <= jump_table_size; index += 8U) {
      uint32_t code0_entry_offset = 16U + index;
      uint32_t routine_offset;
      if (!macos_code0_entry_is_unloaded_loadseg_for_segment(
            code0_payload, code0_payload_size, code0_entry_offset, resource->resource_id, &routine_offset)) {
        continue;
      }
      if (macos_append_segment_routine_candidate(builder, emitted, index / 8U, index, code0_entry_offset,
            code0_resource->code.jump_table_offset_from_a5, routine_offset, resource->resource_id, "unloaded_loadseg",
            "candidate_code_range", emitted > 0U) != 0) {
        return -1;
      }
      emitted++;
    }
  }
  return json_builder_append(builder, "]");
}

static int macos_append_code_segment_map(JsonBuilder *builder, const unsigned char *resource_fork,
    size_t resource_fork_size, const PlatformMacosResourceInfo *resources, size_t resource_count) {
  const PlatformMacosResourceInfo *code0 = macos_find_code0_resource(resources, resource_count);
  const unsigned char *code0_payload = NULL;
  uint32_t code0_payload_size = 0U;
  size_t index;
  int first = 1;
  if (code0 != NULL && code0->payload_offset <= resource_fork_size &&
      code0->payload_size <= resource_fork_size - code0->payload_offset) {
    code0_payload = resource_fork + code0->payload_offset;
    code0_payload_size = code0->payload_size;
  }
  if (json_builder_append(builder, "\"code_segment_map\":[") != 0) return -1;
  for (index = 0U; index < resource_count; ++index) {
    const PlatformMacosResourceInfo *resource = &resources[index];
    uint32_t first_offset;
    uint32_t entry_count;
    uint32_t span_size;
    if (strcmp(resource->type, "CODE") != 0 ||
        resource->code.kind != PLATFORM_MACOS_CODE_RESOURCE_CODE_SEGMENT) {
      continue;
    }
    first_offset = resource->code.first_jump_table_entry_offset;
    entry_count = resource->code.jump_table_entry_count;
    span_size = entry_count > UINT32_MAX / 8U ? UINT32_MAX : entry_count * 8U;
    if (!first && json_builder_append(builder, ",") != 0) return -1;
    first = 0;
    if (json_builder_appendf(builder,
          "{\"resource_id\":%d,\"kind\":\"nonzero_code_segment\",\"first_jump_table_entry_offset\":%u,"
          "\"jump_table_entry_count\":%u,\"jump_table_entry_size\":8,\"jump_table_span_size\":%u,"
          "\"kb_record_id\":\"macos.hfs_resource_fork.code_resources.mpw_application\",",
          (int)resource->resource_id, (unsigned)first_offset, (unsigned)entry_count,
          (unsigned)span_size) != 0 ||
        macos_append_fact_ref(builder, "macos.code_resource.segment_jump_table_span.accepted",
          "validated", "accepted_parser_output") != 0 ||
        macos_append_segment_routine_candidates(builder, resource, code0, code0_payload, code0_payload_size) != 0 ||
        json_builder_append(builder, "}") != 0) {
      return -1;
    }
  }
  return json_builder_append(builder, "]");
}

static const PlatformMacosResourceInfo *macos_find_resource(const PlatformMacosResourceInfo *resources,
    size_t resource_count, const char *type, int16_t resource_id) {
  size_t index;
  for (index = 0U; index < resource_count; ++index) {
    const PlatformMacosResourceInfo *resource = &resources[index];
    if (strcmp(resource->type, type) == 0 && resource->resource_id == resource_id) return resource;
  }
  return NULL;
}

static int macos_append_selected_code(JsonBuilder *builder, const PlatformMacosResourceFork *resource_fork_info,
    const unsigned char *resource_fork, size_t resource_fork_size, const PlatformMacosResourceInfo *resources,
    size_t resource_count) {
  const PlatformMacosResourceInfo *selected_resource = macos_find_resource(resources, resource_count, "CODE", 1);
  uint32_t payload_offset = 0U;
  uint32_t payload_size = 0U;
  uint32_t code_start = 0U;
  uint32_t code_offset = 0U;
  uint32_t code_size = 0U;
  char payload_sha256[65];
  char code_sha256[65];
  int status;
  payload_sha256[0] = '\0';
  code_sha256[0] = '\0';
  status = platform_macos_resource_fork_find_payload(resource_fork, resource_fork_size, "CODE", 1,
    &payload_offset, &payload_size);
  if (status != 0) {
    if (status > 0) {
      return json_builder_append(builder, "\"selected_code\":{\"type\":\"CODE\",\"id\":1,\"available\":false}");
    }
    return -1;
  }
  if (m68k_platform_sha256_hex(resource_fork + payload_offset, payload_size, payload_sha256) != 0) return -1;
  if (selected_resource != NULL &&
      platform_macos_code_metadata_executable_range(&selected_resource->code, &code_start, &code_size) == 0) {
    code_offset = payload_offset + code_start;
    if (m68k_platform_sha256_hex(resource_fork + code_offset, code_size, code_sha256) != 0) return -1;
  } else {
    code_offset = payload_offset + payload_size;
  }
  if (json_builder_appendf(builder,
        "\"selected_code\":{\"type\":\"CODE\",\"id\":1,\"available\":true,"
        "\"name\":") != 0 ||
      (selected_resource != NULL
        ? macos_append_resource_name(builder, resource_fork_info, resource_fork, resource_fork_size, selected_resource)
        : json_builder_append(builder, "null")) != 0 ||
      json_builder_appendf(builder, ",\"payload_offset\":%u,\"payload_size\":%u,\"payload_sha256\":",
        (unsigned)payload_offset, (unsigned)payload_size) != 0 ||
      json_builder_append_json_string(builder, payload_sha256) != 0 ||
      json_builder_appendf(builder, ",\"code_bytes_offset\":%u,\"code_bytes_size\":%u,\"code_bytes_sha256\":",
        (unsigned)code_offset, (unsigned)code_size) != 0 ||
      json_builder_append_json_string(builder, code_sha256) != 0 ||
      json_builder_append(builder, ",\"code\":") != 0 ||
      (selected_resource != NULL
        ? macos_append_code_metadata(builder, selected_resource)
        : json_builder_append(builder, "null")) != 0 ||
      json_builder_append(builder, "}") != 0) {
    return -1;
  }
  return 0;
}

PLATFORM_FILE_API int platform_file_macos_hfs_code_summary_json_alloc(const unsigned char *data, size_t size,
    const char *hfs_path, char **out_text) {
  PlatformMacosHFSCatalog catalog;
  PlatformMacosHFSDirectoryInfo *directories = NULL;
  PlatformMacosHFSFileInfo *files = NULL;
  PlatformMacosResourceFork resource_fork_info;
  PlatformMacosResourceTypeInfo *resource_types = NULL;
  PlatformMacosResourceInfo *resources = NULL;
  PlatformMacosHFSFileInfo *selected_file = NULL;
  unsigned char *data_fork = NULL;
  unsigned char *resource_fork = NULL;
  char *error = NULL;
  char path[PLATFORM_MACOS_HFS_PATH_SIZE];
  JsonBuilder builder;
  size_t index;
  int result = -1;
  if (out_text == NULL) return -1;
  *out_text = NULL;
  memset(&catalog, 0, sizeof(catalog));
  memset(&resource_fork_info, 0, sizeof(resource_fork_info));
  if (data == NULL || size == 0U || hfs_path == NULL || hfs_path[0] == '\0') {
    *out_text = m68k_platform_dup_string("invalid Mac HFS summary input");
    return -1;
  }
  if (platform_macos_hfs_catalog_parse(data, size, &catalog, NULL, 0U, NULL, 0U) != 0) {
    *out_text = m68k_platform_dup_string("Mac HFS catalog parse failed");
    return -1;
  }
  directories = (PlatformMacosHFSDirectoryInfo *)calloc(catalog.directory_count ? catalog.directory_count : 1U,
    sizeof(*directories));
  files = (PlatformMacosHFSFileInfo *)calloc(catalog.file_count ? catalog.file_count : 1U, sizeof(*files));
  if (directories == NULL || files == NULL) {
    *out_text = m68k_platform_dup_string("out of memory");
    goto cleanup;
  }
  if (platform_macos_hfs_catalog_parse(data, size, &catalog, directories, catalog.directory_count,
      files, catalog.file_count) != 0) {
    *out_text = m68k_platform_dup_string("Mac HFS catalog parse failed");
    goto cleanup;
  }
  for (index = 0U; index < catalog.file_count; ++index) {
    if (platform_macos_hfs_file_path(directories, catalog.directory_count, &files[index], path, sizeof(path)) != 0)
      continue;
    if (macos_hfs_path_matches(&catalog.volume, path, hfs_path)) {
      selected_file = &files[index];
      break;
    }
  }
  if (selected_file == NULL) {
    *out_text = m68k_platform_dup_string("Mac HFS file path not found");
    goto cleanup;
  }
  if (macos_copy_fork_or_error(data, size, &catalog.volume, selected_file->data_extents,
      selected_file->data_size, &data_fork, &error) != 0) {
    *out_text = error != NULL ? error : m68k_platform_dup_string("Mac HFS data fork materialization failed");
    error = NULL;
    goto cleanup;
  }
  if (macos_copy_fork_or_error(data, size, &catalog.volume, selected_file->resource_extents,
      selected_file->resource_size, &resource_fork, &error) != 0) {
    *out_text = error != NULL ? error : m68k_platform_dup_string("Mac HFS resource fork materialization failed");
    error = NULL;
    goto cleanup;
  }
  if (platform_macos_resource_fork_parse(resource_fork, selected_file->resource_size, &resource_fork_info,
      NULL, 0U, NULL, 0U) != 0) {
    *out_text = m68k_platform_dup_string("Mac resource fork parse failed");
    goto cleanup;
  }
  resource_types = (PlatformMacosResourceTypeInfo *)calloc(
    resource_fork_info.type_count ? resource_fork_info.type_count : 1U, sizeof(*resource_types));
  resources = (PlatformMacosResourceInfo *)calloc(
    resource_fork_info.resource_count ? resource_fork_info.resource_count : 1U, sizeof(*resources));
  if (resource_types == NULL || resources == NULL) {
    *out_text = m68k_platform_dup_string("out of memory");
    goto cleanup;
  }
  if (platform_macos_resource_fork_parse(resource_fork, selected_file->resource_size, &resource_fork_info,
      resource_types, resource_fork_info.type_count, resources, resource_fork_info.resource_count) != 0) {
    *out_text = m68k_platform_dup_string("Mac resource fork parse failed");
    goto cleanup;
  }
  if (platform_macos_hfs_file_path(directories, catalog.directory_count, selected_file, path, sizeof(path)) != 0) {
    *out_text = m68k_platform_dup_string("Mac HFS file path reconstruction failed");
    goto cleanup;
  }
  if (json_builder_create(&builder) != 0) {
    *out_text = m68k_platform_dup_string("out of memory");
    goto cleanup;
  }
  if (json_builder_append(&builder, "{\"platform\":\"macos\",\"container_kind\":\"hfs_resource_code_file\","
        "\"volume\":{\"name\":") != 0 ||
      json_builder_append_json_string(&builder, catalog.volume.volume_name) != 0 ||
      json_builder_appendf(&builder,
        ",\"allocation_block_size\":%u,\"allocation_block_count\":%u},\"file\":{\"path\":",
        (unsigned)catalog.volume.allocation_block_size, (unsigned)catalog.volume.allocation_block_count) != 0 ||
      json_builder_append_json_string(&builder, path) != 0 ||
      json_builder_appendf(&builder, ",\"cnid\":%u,\"type\":", (unsigned)selected_file->cnid) != 0 ||
      json_builder_append_json_string(&builder, selected_file->file_type) != 0 ||
      json_builder_append(&builder, ",\"creator\":") != 0 ||
      json_builder_append_json_string(&builder, selected_file->creator) != 0 ||
      json_builder_append(&builder, ",\"forks\":{") != 0 ||
      macos_append_fork_summary(&builder, "data", data_fork, selected_file->data_size) != 0 ||
      json_builder_append(&builder, ",") != 0 ||
      macos_append_fork_summary(&builder, "resource", resource_fork, selected_file->resource_size) != 0 ||
      json_builder_appendf(&builder,
        "}},\"resource_fork\":{\"type_count\":%u,\"resource_count\":%u,",
        (unsigned)resource_fork_info.type_count, (unsigned)resource_fork_info.resource_count) != 0 ||
      macos_append_resource_types(&builder, resource_types, resource_fork_info.type_count) != 0 ||
      json_builder_append(&builder, ",") != 0 ||
      macos_append_code_resources(&builder, &resource_fork_info, resource_fork, selected_file->resource_size,
        resources, resource_fork_info.resource_count) != 0 ||
      macos_append_segment_loader_fixup_inventory(&builder, resources, resource_fork_info.resource_count) != 0 ||
      json_builder_append(&builder, ",") != 0 ||
      macos_append_code_segment_map(&builder, resource_fork, selected_file->resource_size,
        resources, resource_fork_info.resource_count) != 0 ||
      json_builder_append(&builder, "},") != 0 ||
      macos_append_selected_code(&builder, &resource_fork_info, resource_fork, selected_file->resource_size,
        resources, resource_fork_info.resource_count) != 0 ||
      json_builder_append(&builder, ",") != 0 ||
      macos_append_shared_executable_ranges(&builder, resources, resource_fork_info.resource_count) != 0 ||
      json_builder_append(&builder, ",\"unsupported\":[\"segment_loader_relocations\",\"overflow_extents\"]}") != 0) {
    *out_text = m68k_platform_dup_string("out of memory");
    json_builder_destroy(&builder);
    goto cleanup;
  }
  *out_text = json_builder_build(&builder);
  if (*out_text == NULL) {
    *out_text = m68k_platform_dup_string("out of memory");
    json_builder_destroy(&builder);
    goto cleanup;
  }
  json_builder_destroy(&builder);
  result = 0;
cleanup:
  free(error);
  free(data_fork);
  free(resource_fork);
  free(resources);
  free(resource_types);
  free(files);
  free(directories);
  return result;
}

PLATFORM_FILE_API int platform_file_macos_hfs_code_resource_bytes_alloc(const unsigned char *data, size_t size,
    const char *hfs_path, int32_t resource_id, unsigned char **out_data, size_t *out_size, char **out_error) {
  PlatformMacosHFSCatalog catalog;
  PlatformMacosHFSDirectoryInfo *directories = NULL;
  PlatformMacosHFSFileInfo *files = NULL;
  PlatformMacosHFSFileInfo *selected_file = NULL;
  unsigned char *resource_fork = NULL;
  unsigned char *code_bytes = NULL;
  char *copy_error = NULL;
  char path[PLATFORM_MACOS_HFS_PATH_SIZE];
  uint32_t payload_offset = 0U;
  uint32_t payload_size = 0U;
  uint32_t code_start = 0U;
  uint32_t code_size = 0U;
  PlatformMacosCodeMetadata code;
  size_t index;
  int find_status;
  int result = -1;
  if (out_data == NULL || out_size == NULL || out_error == NULL) return -1;
  *out_data = NULL;
  *out_size = 0U;
  *out_error = NULL;
  memset(&catalog, 0, sizeof(catalog));
  if (data == NULL || size == 0U || hfs_path == NULL || hfs_path[0] == '\0') {
    *out_error = m68k_platform_dup_string("invalid Mac HFS CODE extraction input");
    return -1;
  }
  if (resource_id <= 0) {
    *out_error = m68k_platform_dup_string("CODE 0 is metadata, not extractable code bytes");
    return -1;
  }
  if (platform_macos_hfs_catalog_parse(data, size, &catalog, NULL, 0U, NULL, 0U) != 0) {
    *out_error = m68k_platform_dup_string("Mac HFS catalog parse failed");
    return -1;
  }
  directories = (PlatformMacosHFSDirectoryInfo *)calloc(catalog.directory_count ? catalog.directory_count : 1U,
    sizeof(*directories));
  files = (PlatformMacosHFSFileInfo *)calloc(catalog.file_count ? catalog.file_count : 1U, sizeof(*files));
  if (directories == NULL || files == NULL) {
    *out_error = m68k_platform_dup_string("out of memory");
    goto cleanup;
  }
  if (platform_macos_hfs_catalog_parse(data, size, &catalog, directories, catalog.directory_count,
      files, catalog.file_count) != 0) {
    *out_error = m68k_platform_dup_string("Mac HFS catalog parse failed");
    goto cleanup;
  }
  for (index = 0U; index < catalog.file_count; ++index) {
    if (platform_macos_hfs_file_path(directories, catalog.directory_count, &files[index], path, sizeof(path)) != 0)
      continue;
    if (macos_hfs_path_matches(&catalog.volume, path, hfs_path)) {
      selected_file = &files[index];
      break;
    }
  }
  if (selected_file == NULL) {
    *out_error = m68k_platform_dup_string("Mac HFS file path not found");
    goto cleanup;
  }
  if (macos_copy_fork_or_error(data, size, &catalog.volume, selected_file->resource_extents,
      selected_file->resource_size, &resource_fork, &copy_error) != 0) {
    *out_error = copy_error != NULL ? copy_error : m68k_platform_dup_string("Mac HFS resource fork materialization failed");
    copy_error = NULL;
    goto cleanup;
  }
  find_status = platform_macos_resource_fork_find_payload(resource_fork, selected_file->resource_size, "CODE",
    (int16_t)resource_id, &payload_offset, &payload_size);
  if (find_status != 0) {
    *out_error = m68k_platform_dup_string(find_status > 0 ? "Mac CODE resource not found"
      : "Mac CODE resource payload lookup failed");
    goto cleanup;
  }
  if (platform_macos_code_metadata_parse(resource_fork + payload_offset, payload_size,
      (int16_t)resource_id, &code) != 0) {
    *out_error = m68k_platform_dup_string("Mac CODE resource layout parse failed");
    goto cleanup;
  }
  if (platform_macos_code_metadata_executable_range(&code, &code_start, &code_size) != 0) {
    *out_error = m68k_platform_dup_string("Mac CODE resource has no confirmed executable range");
    goto cleanup;
  }
  code_bytes = (unsigned char *)malloc(code_size);
  if (code_bytes == NULL) {
    *out_error = m68k_platform_dup_string("out of memory");
    goto cleanup;
  }
  memcpy(code_bytes, resource_fork + payload_offset + code_start, code_size);
  *out_data = code_bytes;
  *out_size = code_size;
  code_bytes = NULL;
  result = 0;
cleanup:
  free(copy_error);
  free(code_bytes);
  free(resource_fork);
  free(files);
  free(directories);
  return result;
}

PLATFORM_FILE_API int platform_file_macos_hfs_code_resource_payload_bytes_alloc(const unsigned char *data, size_t size,
    const char *hfs_path, int32_t resource_id, unsigned char **out_data, size_t *out_size, char **out_error) {
  PlatformMacosHFSCatalog catalog;
  PlatformMacosHFSDirectoryInfo *directories = NULL;
  PlatformMacosHFSFileInfo *files = NULL;
  PlatformMacosHFSFileInfo *selected_file = NULL;
  unsigned char *resource_fork = NULL;
  unsigned char *payload_bytes = NULL;
  char *copy_error = NULL;
  char path[PLATFORM_MACOS_HFS_PATH_SIZE];
  uint32_t payload_offset = 0U;
  uint32_t payload_size = 0U;
  size_t index;
  int find_status;
  int result = -1;
  if (out_data == NULL || out_size == NULL || out_error == NULL) return -1;
  *out_data = NULL;
  *out_size = 0U;
  *out_error = NULL;
  memset(&catalog, 0, sizeof(catalog));
  if (data == NULL || size == 0U || hfs_path == NULL || hfs_path[0] == '\0' || resource_id < 0) {
    *out_error = m68k_platform_dup_string("invalid Mac HFS CODE payload extraction input");
    return -1;
  }
  if (platform_macos_hfs_catalog_parse(data, size, &catalog, NULL, 0U, NULL, 0U) != 0) {
    *out_error = m68k_platform_dup_string("Mac HFS catalog parse failed");
    return -1;
  }
  directories = (PlatformMacosHFSDirectoryInfo *)calloc(catalog.directory_count ? catalog.directory_count : 1U,
    sizeof(*directories));
  files = (PlatformMacosHFSFileInfo *)calloc(catalog.file_count ? catalog.file_count : 1U, sizeof(*files));
  if (directories == NULL || files == NULL) {
    *out_error = m68k_platform_dup_string("out of memory");
    goto cleanup;
  }
  if (platform_macos_hfs_catalog_parse(data, size, &catalog, directories, catalog.directory_count,
      files, catalog.file_count) != 0) {
    *out_error = m68k_platform_dup_string("Mac HFS catalog parse failed");
    goto cleanup;
  }
  for (index = 0U; index < catalog.file_count; ++index) {
    if (platform_macos_hfs_file_path(directories, catalog.directory_count, &files[index], path, sizeof(path)) != 0)
      continue;
    if (macos_hfs_path_matches(&catalog.volume, path, hfs_path)) {
      selected_file = &files[index];
      break;
    }
  }
  if (selected_file == NULL) {
    *out_error = m68k_platform_dup_string("Mac HFS file path not found");
    goto cleanup;
  }
  if (macos_copy_fork_or_error(data, size, &catalog.volume, selected_file->resource_extents,
      selected_file->resource_size, &resource_fork, &copy_error) != 0) {
    *out_error = copy_error != NULL ? copy_error : m68k_platform_dup_string("Mac HFS resource fork materialization failed");
    copy_error = NULL;
    goto cleanup;
  }
  find_status = platform_macos_resource_fork_find_payload(resource_fork, selected_file->resource_size, "CODE",
    (int16_t)resource_id, &payload_offset, &payload_size);
  if (find_status != 0) {
    *out_error = m68k_platform_dup_string(find_status > 0 ? "Mac CODE resource not found"
      : "Mac CODE resource payload lookup failed");
    goto cleanup;
  }
  payload_bytes = (unsigned char *)malloc(payload_size ? payload_size : 1U);
  if (payload_bytes == NULL) {
    *out_error = m68k_platform_dup_string("out of memory");
    goto cleanup;
  }
  if (payload_size != 0U) memcpy(payload_bytes, resource_fork + payload_offset, payload_size);
  *out_data = payload_bytes;
  *out_size = payload_size;
  payload_bytes = NULL;
  result = 0;
cleanup:
  free(copy_error);
  free(payload_bytes);
  free(resource_fork);
  free(files);
  free(directories);
  return result;
}

static int parse_u32_arg_local(const char *text, uint32_t *out_value) {
  M68kParseU32Result result;
  if (text == NULL || out_value == NULL) return 0;
  result = m68k_parse_number_u32(text);
  if (!result.ok) return 0;
  *out_value = result.value;
  return 1;
}

static int copy_policy_text(char *dest, size_t dest_size, const char *source) {
  size_t length;
  if (dest == NULL || dest_size == 0U) return 0;
  dest[0] = '\0';
  if (source == NULL || source[0] == '\0') return 1;
  length = strlen(source);
  if (length >= dest_size) return 0;
  memcpy(dest, source, length + 1U);
  return 1;
}

typedef struct TextU8Map {
  const char *name;
  uint8_t id;
} TextU8Map;

typedef struct TextU16Map {
  const char *name;
  uint16_t id;
} TextU16Map;

static uint8_t text_u8_id_from_map_local(const TextU8Map *entries, size_t entry_count, const char *name,
    uint8_t default_id) {
  size_t index;
  if (name == NULL || name[0] == '\0') return default_id;
  for (index = 0U; index < entry_count; ++index) {
    if (strcmp(name, entries[index].name) == 0) return entries[index].id;
  }
  return default_id;
}

static uint16_t text_u16_id_from_map_local(const TextU16Map *entries, size_t entry_count, const char *name,
    uint16_t default_id) {
  size_t index;
  if (name == NULL || name[0] == '\0') return default_id;
  for (index = 0U; index < entry_count; ++index) {
    if (strcmp(name, entries[index].name) == 0) return entries[index].id;
  }
  return default_id;
}

static const TextU8Map ANALYSIS_REGISTER_SEED_KIND_NAMES[] = {
  { "library_base", M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE },
  { "struct_ptr", M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR },
};

static const TextU8Map ANALYSIS_REPRESENTATION_STYLE_NAMES[] = {
  { "hex", M68K_ANALYSIS_REPRESENTATION_STYLE_HEX },
  { "decimal", M68K_ANALYSIS_REPRESENTATION_STYLE_DECIMAL },
  { "binary", M68K_ANALYSIS_REPRESENTATION_STYLE_BINARY },
  { "character", M68K_ANALYSIS_REPRESENTATION_STYLE_CHARACTER },
  { "string", M68K_ANALYSIS_REPRESENTATION_STYLE_STRING },
  { "symbol", M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL },
};

static uint8_t analysis_register_seed_kind_id_from_text_local(const char *kind) {
  return text_u8_id_from_map_local(ANALYSIS_REGISTER_SEED_KIND_NAMES,
    sizeof(ANALYSIS_REGISTER_SEED_KIND_NAMES) / sizeof(ANALYSIS_REGISTER_SEED_KIND_NAMES[0]), kind,
    M68K_ANALYSIS_REGISTER_SEED_NONE);
}

static uint8_t analysis_representation_style_id_from_text_local(const char *style) {
  return text_u8_id_from_map_local(ANALYSIS_REPRESENTATION_STYLE_NAMES,
    sizeof(ANALYSIS_REPRESENTATION_STYLE_NAMES) / sizeof(ANALYSIS_REPRESENTATION_STYLE_NAMES[0]), style,
    M68K_ANALYSIS_REPRESENTATION_STYLE_NONE);
}

static const TextU16Map STRUCTURED_DATA_PLATFORM_KIND_NAMES[] = {
  { "resident_autoinit", M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_KIND_AMIGA_RESIDENT_AUTOINIT },
};

static uint16_t structured_data_platform_kind_id_from_text_local(const char *struct_name) {
  return text_u16_id_from_map_local(STRUCTURED_DATA_PLATFORM_KIND_NAMES,
    sizeof(STRUCTURED_DATA_PLATFORM_KIND_NAMES) / sizeof(STRUCTURED_DATA_PLATFORM_KIND_NAMES[0]), struct_name,
    M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_KIND_NONE);
}

static const TextU16Map RESIDENT_AUTOINIT_PLATFORM_FIELD_NAMES[] = {
  { "resident_base_size", M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_AMIGA_RESIDENT_BASE_SIZE },
  { "resident_vectors", M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_AMIGA_RESIDENT_VECTORS },
  { "resident_init_struct", M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_AMIGA_RESIDENT_INIT_STRUCT },
  { "resident_init_function", M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_AMIGA_RESIDENT_INIT_FUNCTION },
};

static uint16_t structured_data_platform_field_id_from_text_local(uint16_t platform_kind_id,
    const char *field_name) {
  if (platform_kind_id != M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_KIND_AMIGA_RESIDENT_AUTOINIT)
    return M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_NONE;
  return text_u16_id_from_map_local(RESIDENT_AUTOINIT_PLATFORM_FIELD_NAMES,
    sizeof(RESIDENT_AUTOINIT_PLATFORM_FIELD_NAMES) / sizeof(RESIDENT_AUTOINIT_PLATFORM_FIELD_NAMES[0]), field_name,
    M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_NONE);
}

enum {
  METADATA_TARGET_TYPE_UNKNOWN = 0U,
  METADATA_TARGET_TYPE_PROGRAM = 1U,
  METADATA_TARGET_TYPE_BOOTBLOCK = 2U,
  METADATA_TARGET_TYPE_NON_PROGRAM = 3U
};

static const TextU8Map METADATA_TARGET_TYPE_NAMES[] = {
  { "program", METADATA_TARGET_TYPE_PROGRAM },
  { "bootblock", METADATA_TARGET_TYPE_BOOTBLOCK },
};

static uint8_t metadata_target_type_id_from_text_local(const char *target_type) {
  if (target_type == NULL || target_type[0] == '\0') return METADATA_TARGET_TYPE_UNKNOWN;
  return text_u8_id_from_map_local(METADATA_TARGET_TYPE_NAMES,
    sizeof(METADATA_TARGET_TYPE_NAMES) / sizeof(METADATA_TARGET_TYPE_NAMES[0]), target_type,
    METADATA_TARGET_TYPE_NON_PROGRAM);
}

static int metadata_target_type_disables_implicit_entries_local(uint8_t target_type_id) {
  return target_type_id != METADATA_TARGET_TYPE_UNKNOWN && target_type_id != METADATA_TARGET_TYPE_PROGRAM;
}

static int policy_add_named_label_domain_local(M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset,
  const char *name, uint8_t domain);
static int policy_add_named_label_local(M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset,
  const char *name);
static int policy_add_entry_comment_local(M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset,
  const char *comment);
static int policy_add_runtime_range_local(M68kAnalysisPolicy *policy, uint32_t section_index,
  uint32_t source_start, uint32_t source_end, uint32_t base_addr, const char *name);
static int policy_add_runtime_entry_point_local(M68kAnalysisPolicy *policy, uint32_t section_index,
  uint32_t runtime_address);
static int policy_add_register_seed_local(M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset,
  uint8_t has_entry_offset, const char *register_name, uint8_t seed_kind, const char *name, const char *type_name,
  const char *context_name);
static int policy_add_rsset_layout_region_local(M68kAnalysisPolicy *policy, uint32_t offset, uint8_t size,
  const char *layout_name, const char *base_symbol, const char *sizeof_symbol, const char *symbol,
  const char *struct_name, const char *pointer_struct, uint8_t flags, uint8_t storage_kind_id,
  const char *storage_kind, const char *semantic_type);
static int policy_add_rsset_use_site_binding_local(M68kAnalysisPolicy *policy, uint32_t section_index,
  uint32_t offset, uint8_t operand_index, const char *base_register, uint32_t displacement,
  const char *layout_name, const char *base_symbol, const char *base_evidence_id,
  const char *binding_id, const char *owner_action_id);
static int policy_add_custom_struct_local(M68kAnalysisPolicy *policy, const char *name, uint32_t size,
  const char *fields_start, const char *fields_end);
static int policy_add_target_equate_local(M68kAnalysisPolicy *policy, const char *name, int32_t value,
  uint8_t value_style_id, const char *value_expr);
static int policy_add_manual_representation_local(M68kAnalysisPolicy *policy, uint32_t section_index,
  uint32_t offset, uint32_t size, uint8_t style_id, uint8_t has_operand_index, uint8_t operand_index,
  const char *symbol_name);
static int policy_add_manual_runtime_address_ref_local(M68kAnalysisPolicy *policy, uint32_t section_index,
  uint32_t offset, uint32_t size, uint32_t target_section_index, uint32_t target_offset,
  uint32_t runtime_address, uint8_t confidence, const char *owner_kind, const char *owner_id,
  const char *owner_layout_id, uint32_t owner_element_offset, const char *xref_generation_mode);
static int policy_runtime_address_to_source_offset_local(const M68kAnalysisPolicy *policy,
  uint32_t runtime_address, uint32_t *out_section_index, uint32_t *out_offset);

int platform_file_analysis_policy_add_register_seed_arg(M68kAnalysisPolicy *policy, const char *text) {
  char buffer[256];
  char *parts[6] = {0};
  char *cursor;
  size_t part_count = 0U;
  M68kAnalysisRegisterSeed *seed;
  if (text == NULL || policy == NULL ||
      policy->register_seed_count >= M68K_ANALYSIS_REGISTER_SEED_LIMIT) return 0;
  if (!copy_policy_text(buffer, sizeof(buffer), text)) return 0;
  cursor = buffer;
  while (part_count < (sizeof(parts) / sizeof(parts[0]))) {
    char *next = strchr(cursor, ':');
    parts[part_count++] = cursor;
    if (next == NULL) break;
    *next = '\0';
    cursor = next + 1;
  }
  if (part_count < 4U || parts[0] == NULL || parts[1] == NULL || parts[2] == NULL || parts[3] == NULL) return 0;
  seed = &policy->register_seeds[policy->register_seed_count];
  memset(seed, 0, sizeof(*seed));
  if (strcmp(parts[0], "*") == 0) {
    seed->has_entry_offset = 0U;
  } else if (parse_u32_arg_local(parts[0], &seed->entry_offset)) {
    seed->has_entry_offset = 1U;
  } else {
    return 0;
  }
  if ((parts[1][0] == 'D' || parts[1][0] == 'd') && parts[1][1] >= '0' && parts[1][1] <= '7' &&
      parts[1][2] == '\0') {
    seed->reg_kind = M68K_ANALYSIS_REGISTER_DATA;
    seed->reg_index = (uint8_t)(parts[1][1] - '0');
  } else if ((parts[1][0] == 'A' || parts[1][0] == 'a') && parts[1][1] >= '0' && parts[1][1] <= '7' &&
      parts[1][2] == '\0') {
    seed->reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
    seed->reg_index = (uint8_t)(parts[1][1] - '0');
  } else {
    return 0;
  }
  seed->kind = analysis_register_seed_kind_id_from_text_local(parts[2]);
  if (seed->kind == M68K_ANALYSIS_REGISTER_SEED_NONE) return 0;
  if (!copy_policy_text(seed->name, sizeof(seed->name), parts[3])) return 0;
  if (part_count > 4U && !copy_policy_text(seed->type_name, sizeof(seed->type_name), parts[4])) return 0;
  if (part_count > 5U && !copy_policy_text(seed->context_name, sizeof(seed->context_name), parts[5])) return 0;
  policy->register_seed_count += 1U;
  return 1;
}

static int analysis_entry_point_provenance_is_known_local(uint8_t provenance) {
  return provenance == M68K_ANALYSIS_ENTRY_POINT_PROVENANCE_DEFAULT ||
    provenance == M68K_ANALYSIS_ENTRY_POINT_PROVENANCE_TARGET_METADATA ||
    provenance == M68K_ANALYSIS_ENTRY_POINT_PROVENANCE_MANUAL_ACTION_LOG ||
    provenance == M68K_ANALYSIS_ENTRY_POINT_PROVENANCE_DECISION_JOURNAL;
}

static const char *analysis_entry_point_provenance_name_local(uint8_t provenance) {
  switch (provenance) {
    case M68K_ANALYSIS_ENTRY_POINT_PROVENANCE_TARGET_METADATA:
      return "target_metadata";
    case M68K_ANALYSIS_ENTRY_POINT_PROVENANCE_MANUAL_ACTION_LOG:
      return "manual_action_log";
    case M68K_ANALYSIS_ENTRY_POINT_PROVENANCE_DECISION_JOURNAL:
      return "decision_journal";
    default:
      return "default";
  }
}

int platform_file_analysis_policy_add_entry_point_arg_with_provenance(M68kAnalysisPolicy *policy, const char *text,
    uint8_t provenance) {
  char buffer[64];
  char *separator;
  M68kAnalysisEntryPoint *entry;
  if (text == NULL || policy == NULL || policy->entry_point_count >= M68K_ANALYSIS_ENTRY_POINT_LIMIT) return 0;
  if (!analysis_entry_point_provenance_is_known_local(provenance)) return 0;
  if (!copy_policy_text(buffer, sizeof(buffer), text)) return 0;
  entry = &policy->entry_points[policy->entry_point_count];
  memset(entry, 0, sizeof(*entry));
  entry->provenance = provenance;
  separator = strchr(buffer, ':');
  if (separator != NULL) {
    *separator = '\0';
    if (!parse_u32_arg_local(buffer, &entry->section_index)) return 0;
    entry->has_section_index = 1U;
    if (!parse_u32_arg_local(separator + 1, &entry->offset)) return 0;
  } else {
    if (!parse_u32_arg_local(buffer, &entry->offset)) return 0;
  }
  policy->entry_point_count += 1U;
  return 1;
}

int platform_file_analysis_policy_add_entry_point_arg(M68kAnalysisPolicy *policy, const char *text) {
  return platform_file_analysis_policy_add_entry_point_arg_with_provenance(policy, text,
    M68K_ANALYSIS_ENTRY_POINT_PROVENANCE_DEFAULT);
}

M68kAnalysisPolicy *platform_file_analysis_policy_create(uint8_t max_cpu) {
  M68kAnalysisPolicy *policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*policy));
  if (policy == NULL) return NULL;
  m68k_analysis_policy_init_default(policy);
  policy->max_cpu = max_cpu;
  return policy;
}

void platform_file_analysis_policy_destroy(M68kAnalysisPolicy *policy) {
  if (policy == NULL) return;
  m68k_analysis_policy_destroy(policy);
  free(policy);
}

static char *read_text_file_local(const char *path) {
  FILE *file;
  char *text = NULL;
  size_t size = 0U;
  size_t capacity = 0U;
  if (path == NULL) return NULL;
  file = fopen(path, "rb");
  if (file == NULL) return NULL;
  for (;;) {
    size_t read_count;
    size_t required_capacity;
    if (size > ((size_t)-1) - 4097U) {
      free(text);
      fclose(file);
      return NULL;
    }
    required_capacity = size + 4096U + 1U;
    if (required_capacity > capacity) {
      size_t next_capacity;
      char *next_text;
      if (capacity == 0U) {
        next_capacity = 4097U;
      } else {
        if (capacity > ((size_t)-1) / 2U) {
          free(text);
          fclose(file);
          return NULL;
        }
        next_capacity = capacity * 2U;
      }
      while (next_capacity < required_capacity) {
        if (next_capacity > ((size_t)-1) / 2U) {
          free(text);
          fclose(file);
          return NULL;
        }
        next_capacity *= 2U;
      }
      next_text = (char *)realloc(text, next_capacity);
      if (next_text == NULL) {
        free(text);
        fclose(file);
        return NULL;
      }
      text = next_text;
      capacity = next_capacity;
    }
    read_count = fread(text + size, 1U, 4096U, file);
    size += read_count;
    if (read_count < 4096U) {
      if (ferror(file)) {
        free(text);
        fclose(file);
        return NULL;
      }
      break;
    }
  }
  text[size] = '\0';
  fclose(file);
  return text;
}

static const char *json_skip_ws_local(const char *cursor, const char *end) {
  while (cursor < end && (*cursor == ' ' || *cursor == '\t' || *cursor == '\r' || *cursor == '\n')) ++cursor;
  return cursor;
}

static const char *json_find_key_local(const char *start, const char *end, const char *key) {
  size_t key_len = strlen(key);
  const char *cursor;
  const char *string_start = NULL;
  int depth = 0;
  int in_string = 0;
  int escaped = 0;
  for (cursor = start; cursor < end; ++cursor) {
    char ch = *cursor;
    if (in_string) {
      if (escaped) {
        escaped = 0;
      } else if (ch == '\\') {
        escaped = 1;
      } else if (ch == '"') {
        const char *after;
        size_t length = (size_t)(cursor - string_start);
        in_string = 0;
        if (depth != 1 || length != key_len || memcmp(string_start, key, key_len) != 0) continue;
        after = json_skip_ws_local(cursor + 1, end);
        if (after < end && *after == ':') return after + 1;
      }
      continue;
    }
    if (ch == '"') {
      in_string = 1;
      escaped = 0;
      string_start = cursor + 1;
    } else if (ch == '{' || ch == '[') {
      ++depth;
    } else if (ch == '}' || ch == ']') {
      if (depth > 0) --depth;
    }
  }
  return NULL;
}

static int json_string_value_local(const char *value, const char *end, char *out, size_t out_size) {
  size_t used = 0U;
  const char *cursor = json_skip_ws_local(value, end);
  if (out == NULL || out_size == 0U) return 0;
  out[0] = '\0';
  if (cursor >= end || *cursor != '"') return 0;
  ++cursor;
  while (cursor < end && *cursor != '"') {
    char ch = *cursor++;
    if (ch == '\\' && cursor < end) ch = *cursor++;
    if (used + 1U >= out_size) return 0;
    out[used++] = ch;
  }
  if (cursor >= end || *cursor != '"') return 0;
  out[used] = '\0';
  return 1;
}

static int json_optional_string_field_local(const char *object_start, const char *object_end, const char *key,
    char *out, size_t out_size) {
  const char *value = json_find_key_local(object_start, object_end, key);
  if (out != NULL && out_size != 0U) out[0] = '\0';
  if (value == NULL) return 1;
  value = json_skip_ws_local(value, object_end);
  if (value + 4 <= object_end && memcmp(value, "null", 4U) == 0) return 1;
  return json_string_value_local(value, object_end, out, out_size);
}

static int json_number_field_local(const char *object_start, const char *object_end, const char *key,
    uint32_t *out_value, int *out_present) {
  char number_text[32];
  size_t used = 0U;
  const char *value = json_find_key_local(object_start, object_end, key);
  if (out_present != NULL) *out_present = 0;
  if (value == NULL) return 1;
  value = json_skip_ws_local(value, object_end);
  if (value + 4 <= object_end && memcmp(value, "null", 4U) == 0) return 1;
  while (value < object_end && ((*value >= '0' && *value <= '9') || *value == '-' || *value == '+')) {
    if (used + 1U >= sizeof(number_text)) return 0;
    number_text[used++] = *value++;
  }
  number_text[used] = '\0';
  if (used == 0U || !parse_u32_arg_local(number_text, out_value)) return 0;
  if (out_present != NULL) *out_present = 1;
  return 1;
}

static int json_bool_field_local(const char *object_start, const char *object_end, const char *key,
    uint8_t *out_value, int *out_present) {
  const char *value = json_find_key_local(object_start, object_end, key);
  if (out_present != NULL) *out_present = 0;
  if (out_value != NULL) *out_value = 0U;
  if (value == NULL) return 1;
  value = json_skip_ws_local(value, object_end);
  if (value + 4 <= object_end && memcmp(value, "true", 4U) == 0) {
    if (out_value != NULL) *out_value = 1U;
    if (out_present != NULL) *out_present = 1;
    return 1;
  }
  if (value + 5 <= object_end && memcmp(value, "false", 5U) == 0) {
    if (out_present != NULL) *out_present = 1;
    return 1;
  }
  if (value + 4 <= object_end && memcmp(value, "null", 4U) == 0) return 1;
  return 0;
}

static const char *json_find_array_local(const char *text, const char *key, const char **out_end) {
  const char *end = text + strlen(text);
  const char *cursor = json_find_key_local(text, end, key);
  int depth = 0;
  if (out_end != NULL) *out_end = NULL;
  if (cursor == NULL) return NULL;
  cursor = json_skip_ws_local(cursor, end);
  if (cursor >= end || *cursor != '[') return NULL;
  for (; cursor < end; ++cursor) {
    if (*cursor == '[') ++depth;
    else if (*cursor == ']') {
      --depth;
      if (depth == 0) {
        if (out_end != NULL) *out_end = cursor;
        return json_skip_ws_local(json_find_key_local(text, end, key), end) + 1;
      }
    }
  }
  return NULL;
}

static const char *json_next_object_local(const char *cursor, const char *end, const char **out_object_end) {
  int depth = 0;
  if (out_object_end != NULL) *out_object_end = NULL;
  while (cursor < end && *cursor != '{') ++cursor;
  if (cursor >= end) return NULL;
  {
    const char *object_start = cursor;
    for (; cursor < end; ++cursor) {
      if (*cursor == '{') ++depth;
      else if (*cursor == '}') {
        --depth;
        if (depth == 0) {
          if (out_object_end != NULL) *out_object_end = cursor + 1;
          return object_start;
        }
      }
    }
  }
  return NULL;
}

static int append_metadata_register_seed_local(const char *object_start, const char *object_end,
    M68kAnalysisPolicy *policy) {
  char register_name[8];
  char kind[32];
  char name[64];
  char struct_name[64];
  char context_name[64];
  uint32_t entry_offset = 0U;
  uint32_t hunk = 0U;
  uint8_t seed_kind;
  int has_entry_offset = 0;
  int has_hunk = 0;
  if (!json_number_field_local(object_start, object_end, "entry_offset", &entry_offset, &has_entry_offset) ||
      !json_number_field_local(object_start, object_end, "hunk", &hunk, &has_hunk) ||
      !json_optional_string_field_local(object_start, object_end, "register", register_name, sizeof(register_name)) ||
      !json_optional_string_field_local(object_start, object_end, "kind", kind, sizeof(kind)) ||
      !json_optional_string_field_local(object_start, object_end, "struct_name", struct_name, sizeof(struct_name)) ||
      !json_optional_string_field_local(object_start, object_end, "context_name", context_name, sizeof(context_name))) {
    return 0;
  }
  seed_kind = analysis_register_seed_kind_id_from_text_local(kind);
  if (seed_kind == M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE) {
    if (!json_optional_string_field_local(object_start, object_end, "library_name", name, sizeof(name))) return 0;
  } else if (seed_kind == M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR) {
    if (!json_optional_string_field_local(object_start, object_end, "note", name, sizeof(name))) return 0;
  } else {
    return kind[0] == '\0';
  }
  if (register_name[0] == '\0' || kind[0] == '\0' || name[0] == '\0') return 1;
  return policy_add_register_seed_local(policy, has_hunk ? hunk : 0U, has_entry_offset ? entry_offset : 0U,
    has_entry_offset ? 1U : 0U, register_name, seed_kind, name, struct_name, context_name);
}

static int append_metadata_entry_point_local(const char *object_start, const char *object_end,
    M68kAnalysisPolicy *policy) {
  uint32_t offset = 0U;
  uint32_t hunk = 0U;
  int has_offset = 0;
  int has_hunk = 0;
  char entry_arg[64];
  char seed_origin[64];
  char source_path[192];
  uint8_t provenance = M68K_ANALYSIS_ENTRY_POINT_PROVENANCE_TARGET_METADATA;
  seed_origin[0] = '\0';
  source_path[0] = '\0';
  if (!json_number_field_local(object_start, object_end, "addr", &offset, &has_offset) ||
      !json_number_field_local(object_start, object_end, "hunk", &hunk, &has_hunk) ||
      !json_optional_string_field_local(object_start, object_end, "seed_origin", seed_origin, sizeof(seed_origin)) ||
      !json_optional_string_field_local(object_start, object_end, "source_path", source_path, sizeof(source_path)))
    return 0;
  if (!has_offset) return 1;
  if (strcmp(seed_origin, "manual_analysis") == 0) {
    provenance = strstr(source_path, "decision_journal.jsonl") != NULL
      ? M68K_ANALYSIS_ENTRY_POINT_PROVENANCE_DECISION_JOURNAL
      : M68K_ANALYSIS_ENTRY_POINT_PROVENANCE_MANUAL_ACTION_LOG;
  }
  if (has_hunk) snprintf(entry_arg, sizeof(entry_arg), "%u:%u", (unsigned)hunk, (unsigned)offset);
  else snprintf(entry_arg, sizeof(entry_arg), "%u", (unsigned)offset);
  return platform_file_analysis_policy_add_entry_point_arg_with_provenance(policy, entry_arg, provenance);
}

static int append_metadata_seeded_code_label_local(const char *object_start, const char *object_end,
    M68kAnalysisPolicy *policy) {
  uint32_t offset = 0U;
  uint32_t hunk = 0U;
  int has_offset = 0;
  int has_hunk = 0;
  char name[64];
  char comment[192];
  name[0] = '\0';
  comment[0] = '\0';
  if (!json_number_field_local(object_start, object_end, "addr", &offset, &has_offset) ||
      !json_number_field_local(object_start, object_end, "hunk", &hunk, &has_hunk) ||
      !json_optional_string_field_local(object_start, object_end, "name", name, sizeof(name)) ||
      !json_optional_string_field_local(object_start, object_end, "comment", comment, sizeof(comment))) {
    return 0;
  }
  if (!has_offset || name[0] == '\0') return 1;
  if (!policy_add_named_label_local(policy, has_hunk ? hunk : 0U, offset, name)) return 0;
  if (comment[0] != '\0' && !policy_add_entry_comment_local(policy, has_hunk ? hunk : 0U, offset, comment)) return 0;
  return 1;
}

static int append_metadata_entry_comment_local(const char *object_start, const char *object_end,
    M68kAnalysisPolicy *policy) {
  uint32_t offset = 0U;
  uint32_t hunk = 0U;
  int has_offset = 0;
  int has_hunk = 0;
  char comment[192];
  comment[0] = '\0';
  if (!json_number_field_local(object_start, object_end, "addr", &offset, &has_offset) ||
      !json_number_field_local(object_start, object_end, "hunk", &hunk, &has_hunk) ||
      !json_optional_string_field_local(object_start, object_end, "comment", comment, sizeof(comment))) {
    return 0;
  }
  if (!has_offset || comment[0] == '\0') return 1;
  return policy_add_entry_comment_local(policy, has_hunk ? hunk : 0U, offset, comment);
}

static int append_metadata_execution_view_local(const char *object_start, const char *object_end,
    M68kAnalysisPolicy *policy) {
  uint32_t source_start = 0U;
  uint32_t source_end = 0U;
  uint32_t base_addr = 0U;
  int has_source_start = 0;
  int has_source_end = 0;
  int has_base_addr = 0;
  char name[64];
  name[0] = '\0';
  if (!json_number_field_local(object_start, object_end, "source_start", &source_start, &has_source_start) ||
      !json_number_field_local(object_start, object_end, "source_end", &source_end, &has_source_end) ||
      !json_number_field_local(object_start, object_end, "base_addr", &base_addr, &has_base_addr) ||
      !json_optional_string_field_local(object_start, object_end, "name", name, sizeof(name))) {
    return 0;
  }
  if (!has_source_start || !has_source_end || !has_base_addr) return 1;
  return policy_add_runtime_range_local(policy, 0U, source_start, source_end, base_addr, name);
}

static int append_metadata_absolute_code_label_local(const char *object_start, const char *object_end,
    M68kAnalysisPolicy *policy) {
  uint32_t runtime_address = 0U;
  uint32_t section_index = 0U;
  uint32_t offset = 0U;
  int has_addr = 0;
  char name[64];
  char comment[192];
  name[0] = '\0';
  comment[0] = '\0';
  if (!json_number_field_local(object_start, object_end, "addr", &runtime_address, &has_addr) ||
      !json_optional_string_field_local(object_start, object_end, "name", name, sizeof(name)) ||
      !json_optional_string_field_local(object_start, object_end, "comment", comment, sizeof(comment))) {
    return 0;
  }
  if (!has_addr || name[0] == '\0') return 1;
  if (!policy_add_named_label_domain_local(policy, 0U, runtime_address, name, M68K_ANALYSIS_LABEL_DOMAIN_RUNTIME))
    return 0;
  if (comment[0] != '\0' &&
      policy_runtime_address_to_source_offset_local(policy, runtime_address, &section_index, &offset) &&
      !policy_add_entry_comment_local(policy, section_index, offset, comment))
    return 0;
  return 1;
}

static uint8_t rsset_layout_region_storage_kind_id_from_text_local(const char *storage_kind) {
  static const TextU8Map storage_kind_names[] = {
    { "struct_instance", M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_STRUCT_INSTANCE },
    { "struct", M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_STRUCT_INSTANCE },
    { "struct_pointer", M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_STRUCT_POINTER },
    { "pointer", M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_POINTER },
    { "scalar", M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_SCALAR },
    { "byte_array", M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_BYTE_ARRAY },
  };
  return text_u8_id_from_map_local(storage_kind_names, sizeof(storage_kind_names) / sizeof(storage_kind_names[0]),
    storage_kind, M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_UNKNOWN);
}

static const char *rsset_layout_region_storage_kind_name_local(uint8_t storage_kind_id) {
  switch (storage_kind_id) {
    case M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_STRUCT_INSTANCE: return "struct_instance";
    case M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_STRUCT_POINTER: return "struct_pointer";
    case M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_POINTER: return "pointer";
    case M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_SCALAR: return "scalar";
    case M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_BYTE_ARRAY: return "byte_array";
    default: return NULL;
  }
}

static uint8_t rsset_layout_region_size_from_storage_kind_id_local(uint8_t storage_kind_id) {
  if (storage_kind_id == M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_BYTE_ARRAY) return 1U;
  return 4U;
}

static int append_metadata_rsset_layout_region_local(const char *object_start, const char *object_end,
    M68kAnalysisPolicy *policy) {
  uint32_t offset = 0U;
  uint32_t explicit_size = 0U;
  uint32_t flags = 0U;
  int has_offset = 0, has_size = 0;
  int has_flags = 0;
  char symbol[64];
  char layout_name[32];
  char base_symbol[64];
  char sizeof_symbol[64];
  char struct_name[64];
  char pointer_struct[64];
  char storage_kind[32];
  char semantic_type[64];
  symbol[0] = '\0';
  layout_name[0] = '\0';
  base_symbol[0] = '\0';
  sizeof_symbol[0] = '\0';
  struct_name[0] = '\0';
  pointer_struct[0] = '\0';
  storage_kind[0] = '\0';
  semantic_type[0] = '\0';
  if (!json_number_field_local(object_start, object_end, "offset", &offset, &has_offset) ||
      !json_number_field_local(object_start, object_end, "size", &explicit_size, &has_size) ||
      !json_number_field_local(object_start, object_end, "flags", &flags, &has_flags) ||
      !json_optional_string_field_local(object_start, object_end, "layout_name", layout_name,
        sizeof(layout_name)) ||
      !json_optional_string_field_local(object_start, object_end, "base_symbol", base_symbol,
        sizeof(base_symbol)) ||
      !json_optional_string_field_local(object_start, object_end, "sizeof_symbol", sizeof_symbol,
        sizeof(sizeof_symbol)) ||
      !json_optional_string_field_local(object_start, object_end, "symbol", symbol, sizeof(symbol)) ||
      !json_optional_string_field_local(object_start, object_end, "struct_name", struct_name, sizeof(struct_name)) ||
      !json_optional_string_field_local(object_start, object_end, "pointer_struct", pointer_struct,
        sizeof(pointer_struct)) ||
      !json_optional_string_field_local(object_start, object_end, "storage_kind", storage_kind,
        sizeof(storage_kind)) ||
      !json_optional_string_field_local(object_start, object_end, "semantic_type", semantic_type,
        sizeof(semantic_type))) {
    return 0;
  }
  if (!has_offset) return 1;
  if (has_size && (explicit_size == 0U || explicit_size > 255U)) return 0;
  if (has_flags && (flags & ~((uint32_t)M68K_ANALYSIS_RSSET_LAYOUT_REGION_FLAG_APP_LAYOUT |
      (uint32_t)M68K_ANALYSIS_RSSET_LAYOUT_REGION_FLAG_APP_BASE)) != 0U) {
    return 0;
  }
  {
    uint8_t storage_kind_id = rsset_layout_region_storage_kind_id_from_text_local(storage_kind);
    return policy_add_rsset_layout_region_local(policy, offset,
      has_size ? (uint8_t)explicit_size : rsset_layout_region_size_from_storage_kind_id_local(storage_kind_id),
      layout_name, base_symbol, sizeof_symbol, symbol, struct_name, pointer_struct, has_flags ? (uint8_t)flags : 0U,
      storage_kind_id, storage_kind, semantic_type);
  }
}

static int append_custom_struct_field_local(M68kAnalysisCustomStruct *custom_struct,
    const char *object_start, const char *object_end) {
  M68kAnalysisCustomStructField *field;
  uint32_t offset = 0U;
  uint32_t size = 0U;
  int has_offset = 0;
  int has_size = 0;
  char name[64];
  char type_name[64];
  char struct_name[64];
  char pointer_struct[64];
  char named_base[64];
  if (custom_struct == NULL || custom_struct->field_count >= M68K_ANALYSIS_CUSTOM_STRUCT_FIELD_LIMIT)
    return 0;
  name[0] = '\0';
  type_name[0] = '\0';
  struct_name[0] = '\0';
  pointer_struct[0] = '\0';
  named_base[0] = '\0';
  if (!json_optional_string_field_local(object_start, object_end, "name", name, sizeof(name)) ||
      !json_optional_string_field_local(object_start, object_end, "type", type_name, sizeof(type_name)) ||
      !json_number_field_local(object_start, object_end, "offset", &offset, &has_offset) ||
      !json_number_field_local(object_start, object_end, "size", &size, &has_size) ||
      !json_optional_string_field_local(object_start, object_end, "struct", struct_name, sizeof(struct_name)) ||
      !json_optional_string_field_local(object_start, object_end, "pointer_struct", pointer_struct,
        sizeof(pointer_struct)) ||
      !json_optional_string_field_local(object_start, object_end, "named_base", named_base, sizeof(named_base))) {
    return 0;
  }
  if (name[0] == '\0' || !has_offset || !has_size || size == 0U || size > UINT16_MAX) return 0;
  field = &custom_struct->fields[custom_struct->field_count++];
  memset(field, 0, sizeof(*field));
  field->offset = offset;
  field->size = size;
  if (!copy_policy_text(field->name, sizeof(field->name), name) ||
      !copy_policy_text(field->type_name, sizeof(field->type_name), type_name) ||
      !copy_policy_text(field->struct_name, sizeof(field->struct_name), struct_name) ||
      !copy_policy_text(field->pointer_struct, sizeof(field->pointer_struct), pointer_struct) ||
      !copy_policy_text(field->named_base, sizeof(field->named_base), named_base)) {
    return 0;
  }
  return 1;
}

static int policy_add_custom_struct_local(M68kAnalysisPolicy *policy, const char *name, uint32_t size,
    const char *fields_start, const char *fields_end) {
  M68kAnalysisCustomStruct *custom_struct;
  const char *cursor;
  uint16_t index;
  if (policy == NULL || name == NULL || name[0] == '\0' || size == 0U ||
      policy->custom_struct_count >= M68K_ANALYSIS_CUSTOM_STRUCT_LIMIT) {
    return 0;
  }
  if (policy->custom_structs == NULL) {
    policy->custom_structs = (M68kAnalysisCustomStruct *)calloc(M68K_ANALYSIS_CUSTOM_STRUCT_LIMIT,
      sizeof(*policy->custom_structs));
    if (policy->custom_structs == NULL) return 0;
    policy->custom_struct_capacity = M68K_ANALYSIS_CUSTOM_STRUCT_LIMIT;
    policy->custom_struct_owner = 1U;
  }
  if (policy->custom_struct_count >= policy->custom_struct_capacity) return 0;
  for (index = 0U; index < policy->custom_struct_count; ++index) {
    if (strcmp(policy->custom_structs[index].name, name) == 0) return 1;
  }
  custom_struct = &policy->custom_structs[policy->custom_struct_count++];
  memset(custom_struct, 0, sizeof(*custom_struct));
  custom_struct->size = size;
  if (!copy_policy_text(custom_struct->name, sizeof(custom_struct->name), name)) return 0;
  cursor = fields_start;
  while (cursor != NULL && cursor < fields_end) {
    const char *field_end;
    const char *field_start = json_next_object_local(cursor, fields_end, &field_end);
    if (field_start == NULL) break;
    if (!append_custom_struct_field_local(custom_struct, field_start, field_end)) return 0;
    cursor = field_end;
  }
  return 1;
}

static int append_metadata_custom_struct_local(const char *object_start, const char *object_end,
    M68kAnalysisPolicy *policy) {
  const char *fields_end = NULL;
  const char *fields_start;
  const char *fields_value;
  const char *cursor;
  int depth = 0;
  uint32_t size = 0U;
  int has_size = 0;
  char name[64];
  name[0] = '\0';
  if (!json_optional_string_field_local(object_start, object_end, "name", name, sizeof(name)) ||
      !json_number_field_local(object_start, object_end, "size", &size, &has_size)) {
    return 0;
  }
  fields_value = json_find_key_local(object_start, object_end, "fields");
  fields_value = fields_value != NULL ? json_skip_ws_local(fields_value, object_end) : NULL;
  if (fields_value == NULL || fields_value >= object_end || *fields_value != '[') return 0;
  fields_start = fields_value + 1;
  for (cursor = fields_value; cursor < object_end; ++cursor) {
    if (*cursor == '[') ++depth;
    else if (*cursor == ']') {
      --depth;
      if (depth == 0) {
        fields_end = cursor;
        break;
      }
    }
  }
  if (name[0] == '\0' || !has_size || fields_start == NULL) return 0;
  if (fields_end == NULL) return 0;
  return policy_add_custom_struct_local(policy, name, size, fields_start, fields_end);
}

static int policy_add_entry_point_local(M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset) {
  M68kAnalysisEntryPoint *entry;
  uint16_t index;
  if (policy == NULL || policy->entry_point_count >= M68K_ANALYSIS_ENTRY_POINT_LIMIT) return 0;
  for (index = 0U; index < policy->entry_point_count; ++index) {
    const M68kAnalysisEntryPoint *existing = &policy->entry_points[index];
    if (existing->has_section_index && existing->section_index == section_index && existing->offset == offset) return 1;
  }
  entry = &policy->entry_points[policy->entry_point_count++];
  memset(entry, 0, sizeof(*entry));
  entry->has_section_index = 1U;
  entry->section_index = section_index;
  entry->offset = offset;
  return 1;
}

static int policy_add_runtime_range_local(M68kAnalysisPolicy *policy, uint32_t section_index,
    uint32_t source_start, uint32_t source_end, uint32_t base_addr, const char *name) {
  M68kAnalysisRuntimeRange *range;
  uint16_t index;
  uint32_t size;
  if (policy == NULL || source_end < source_start ||
      policy->runtime_range_count >= M68K_ANALYSIS_RUNTIME_RANGE_LIMIT) return 0;
  size = source_end - source_start;
  for (index = 0U; index < policy->runtime_range_count; ++index) {
    const M68kAnalysisRuntimeRange *existing = &policy->runtime_ranges[index];
    if (existing->has_section_index && existing->section_index == section_index &&
        existing->offset == source_start && existing->size == size &&
        existing->runtime_address == base_addr) return 1;
  }
  range = &policy->runtime_ranges[policy->runtime_range_count++];
  memset(range, 0, sizeof(*range));
  range->has_section_index = 1U;
  range->section_index = section_index;
  range->offset = source_start;
  range->size = size;
  range->runtime_address = base_addr;
  if (name != NULL && name[0] != '\0' && !copy_policy_text(range->name, sizeof(range->name), name)) return 0;
  return 1;
}

static int policy_add_runtime_entry_point_local(M68kAnalysisPolicy *policy, uint32_t section_index,
    uint32_t runtime_address) {
  M68kAnalysisRuntimeEntryPoint *entry;
  uint16_t index;
  if (policy == NULL || policy->runtime_entry_point_count >= M68K_ANALYSIS_RUNTIME_ENTRY_POINT_LIMIT) return 0;
  for (index = 0U; index < policy->runtime_entry_point_count; ++index) {
    const M68kAnalysisRuntimeEntryPoint *existing = &policy->runtime_entry_points[index];
    if (existing->has_section_index && existing->section_index == section_index &&
        existing->runtime_address == runtime_address) return 1;
  }
  entry = &policy->runtime_entry_points[policy->runtime_entry_point_count++];
  memset(entry, 0, sizeof(*entry));
  entry->has_section_index = 1U;
  entry->section_index = section_index;
  entry->runtime_address = runtime_address;
  return 1;
}

static int policy_add_rsset_layout_region_local(M68kAnalysisPolicy *policy, uint32_t offset, uint8_t size,
  const char *layout_name, const char *base_symbol, const char *sizeof_symbol, const char *symbol,
  const char *struct_name, const char *pointer_struct, uint8_t flags, uint8_t storage_kind_id,
  const char *storage_kind, const char *semantic_type) {
  M68kAnalysisRssetLayoutRegion *slot;
  uint16_t index;
  const char *effective_layout = layout_name != NULL && layout_name[0] != '\0' ? layout_name : "app";
  const char *effective_base = base_symbol != NULL && base_symbol[0] != '\0' ? base_symbol : AMIGA_APP_BASE_TAG;
  if (policy == NULL || offset > 0x7FFFU || size == 0U ||
      policy->rsset_layout_region_count >= M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT) {
    return 0;
  }
  for (index = 0U; index < policy->rsset_layout_region_count; ++index) {
    const M68kAnalysisRssetLayoutRegion *existing = &policy->rsset_layout_regions[index];
    const char *existing_layout = existing->layout_name[0] != '\0' ? existing->layout_name : "app";
    const char *existing_base = existing->base_symbol[0] != '\0' ? existing->base_symbol : AMIGA_APP_BASE_TAG;
    if (existing->offset == offset && strcmp(existing_layout, effective_layout) == 0 &&
        strcmp(existing_base, effective_base) == 0) {
      return 1;
    }
  }
  slot = &policy->rsset_layout_regions[policy->rsset_layout_region_count];
  memset(slot, 0, sizeof(*slot));
  slot->offset = offset;
  slot->size = size;
  slot->flags = flags;
  if (strcmp(effective_base, AMIGA_APP_BASE_TAG) == 0) {
    slot->flags |= (uint8_t)M68K_ANALYSIS_RSSET_LAYOUT_REGION_FLAG_APP_BASE;
  }
  slot->storage_kind_id = storage_kind_id;
  if (!copy_policy_text(slot->layout_name, sizeof(slot->layout_name), effective_layout) ||
      !copy_policy_text(slot->base_symbol, sizeof(slot->base_symbol), effective_base) ||
      !copy_policy_text(slot->sizeof_symbol, sizeof(slot->sizeof_symbol), sizeof_symbol) ||
      !copy_policy_text(slot->symbol, sizeof(slot->symbol), symbol) ||
      !copy_policy_text(slot->struct_name, sizeof(slot->struct_name), struct_name) ||
      !copy_policy_text(slot->pointer_struct, sizeof(slot->pointer_struct), pointer_struct) ||
      !copy_policy_text(slot->storage_kind, sizeof(slot->storage_kind), storage_kind) ||
      !copy_policy_text(slot->semantic_type, sizeof(slot->semantic_type), semantic_type)) {
    memset(slot, 0, sizeof(*slot));
    return 0;
  }
  policy->rsset_layout_region_count += 1U;
  return 1;
}

static int address_register_index_from_text_local(const char *register_name, uint8_t *out_reg) {
  if (out_reg != NULL) *out_reg = 0U;
  if (register_name == NULL || register_name[0] == '\0') return 0;
  if ((register_name[0] != 'A' && register_name[0] != 'a') ||
      register_name[1] < '0' || register_name[1] > '7' || register_name[2] != '\0') {
    return 0;
  }
  if (out_reg != NULL) *out_reg = (uint8_t)(register_name[1] - '0');
  return 1;
}

static int policy_add_rsset_use_site_binding_local(M68kAnalysisPolicy *policy, uint32_t section_index,
    uint32_t offset, uint8_t operand_index, const char *base_register, uint32_t displacement,
    const char *layout_name, const char *base_symbol, const char *base_evidence_id,
    const char *binding_id, const char *owner_action_id) {
  M68kAnalysisRssetUseSiteBinding *slot;
  uint8_t base_reg = 0U;
  uint16_t index;
  const char *effective_layout = layout_name != NULL && layout_name[0] != '\0' ? layout_name : "app";
  const char *effective_base = base_symbol != NULL && base_symbol[0] != '\0' ? base_symbol : AMIGA_APP_BASE_TAG;
  if (policy == NULL || displacement > 0x7FFFU || operand_index >= 4U ||
      base_evidence_id == NULL || base_evidence_id[0] == '\0' ||
      !address_register_index_from_text_local(base_register, &base_reg)) {
    return 0;
  }
  for (index = 0U; index < policy->rsset_use_site_binding_count &&
       index < M68K_ANALYSIS_RSSET_USE_SITE_BINDING_LIMIT; ++index) {
    const M68kAnalysisRssetUseSiteBinding *existing = &policy->rsset_use_site_bindings[index];
    if (existing->section_index == section_index && existing->offset == offset &&
        existing->operand_index == operand_index && existing->base_reg == base_reg &&
        existing->displacement == displacement && strcmp(existing->layout_name, effective_layout) == 0 &&
        strcmp(existing->base_symbol, effective_base) == 0 &&
        strcmp(existing->base_evidence_id, base_evidence_id) == 0) {
      return 1;
    }
  }
  if (policy->rsset_use_site_binding_count >= M68K_ANALYSIS_RSSET_USE_SITE_BINDING_LIMIT) return 0;
  slot = &policy->rsset_use_site_bindings[policy->rsset_use_site_binding_count++];
  memset(slot, 0, sizeof(*slot));
  slot->section_index = section_index;
  slot->offset = offset;
  slot->operand_index = operand_index;
  slot->base_reg = base_reg;
  slot->displacement = displacement;
  if (!copy_policy_text(slot->layout_name, sizeof(slot->layout_name), effective_layout) ||
      !copy_policy_text(slot->base_symbol, sizeof(slot->base_symbol), effective_base) ||
      !copy_policy_text(slot->base_evidence_id, sizeof(slot->base_evidence_id), base_evidence_id) ||
      !copy_policy_text(slot->binding_id, sizeof(slot->binding_id), binding_id) ||
      !copy_policy_text(slot->owner_action_id, sizeof(slot->owner_action_id), owner_action_id)) {
    memset(slot, 0, sizeof(*slot));
    --policy->rsset_use_site_binding_count;
    return 0;
  }
  return 1;
}

static int policy_find_target_equate_index_local(const M68kAnalysisPolicy *policy, const char *name,
    uint16_t *out_index) {
  uint16_t index;
  if (out_index != NULL) *out_index = 0U;
  if (policy == NULL || name == NULL || name[0] == '\0') return 0;
  for (index = 0U; index < policy->target_equate_count && index < M68K_ANALYSIS_TARGET_EQUATE_LIMIT; ++index) {
    if (strcmp(policy->target_equates[index].name, name) == 0) {
      if (out_index != NULL) *out_index = (uint16_t)(index + 1U);
      return 1;
    }
  }
  return 0;
}

static int policy_add_target_equate_local(M68kAnalysisPolicy *policy, const char *name, int32_t value,
    uint8_t value_style_id, const char *value_expr) {
  uint16_t index;
  M68kAnalysisTargetEquate *slot;
  if (policy == NULL || name == NULL || name[0] == '\0' || !asm_symbol_name_is_safe_local(name)) return 0;
  if (value_style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL &&
      (value_expr == NULL || value_expr[0] == '\0')) {
    return 0;
  }
  for (index = 0U; index < policy->target_equate_count && index < M68K_ANALYSIS_TARGET_EQUATE_LIMIT; ++index) {
    slot = &policy->target_equates[index];
    if (strcmp(slot->name, name) == 0) {
      slot->value = value;
      slot->value_style_id = value_style_id;
      if (!copy_policy_text(slot->value_expr, sizeof(slot->value_expr), value_expr)) return 0;
      return 1;
    }
  }
  if (policy->target_equate_count >= M68K_ANALYSIS_TARGET_EQUATE_LIMIT) return 0;
  slot = &policy->target_equates[policy->target_equate_count++];
  memset(slot, 0, sizeof(*slot));
  if (!copy_policy_text(slot->name, sizeof(slot->name), name)) {
    memset(slot, 0, sizeof(*slot));
    --policy->target_equate_count;
    return 0;
  }
  slot->value = value;
  slot->value_style_id = value_style_id;
  if (!copy_policy_text(slot->value_expr, sizeof(slot->value_expr), value_expr)) {
    memset(slot, 0, sizeof(*slot));
    --policy->target_equate_count;
    return 0;
  }
  return 1;
}

static int policy_add_manual_runtime_address_ref_local(M68kAnalysisPolicy *policy, uint32_t section_index,
    uint32_t offset, uint32_t size, uint32_t target_section_index, uint32_t target_offset,
    uint32_t runtime_address, uint8_t confidence, const char *owner_kind, const char *owner_id,
    const char *owner_layout_id, uint32_t owner_element_offset, const char *xref_generation_mode) {
  M68kAnalysisManualRuntimeAddressRef *slot;
  uint16_t index;
  if (policy == NULL || size == 0U || owner_kind == NULL || owner_kind[0] == '\0' ||
      owner_id == NULL || owner_id[0] == '\0' || owner_layout_id == NULL || owner_layout_id[0] == '\0' ||
      xref_generation_mode == NULL || xref_generation_mode[0] == '\0')
    return 0;
  for (index = 0U; index < policy->manual_runtime_address_ref_count &&
       index < M68K_ANALYSIS_MANUAL_RUNTIME_ADDRESS_REF_LIMIT; ++index) {
    const M68kAnalysisManualRuntimeAddressRef *existing = &policy->manual_runtime_address_refs[index];
    if (existing->section_index == section_index && existing->offset == offset &&
        existing->target_section_index == target_section_index && existing->target_offset == target_offset &&
        strcmp(existing->owner_id, owner_id) == 0)
      return 1;
  }
  if (policy->manual_runtime_address_ref_count >= M68K_ANALYSIS_MANUAL_RUNTIME_ADDRESS_REF_LIMIT) return 0;
  slot = &policy->manual_runtime_address_refs[policy->manual_runtime_address_ref_count++];
  memset(slot, 0, sizeof(*slot));
  slot->has_section_index = 1U;
  slot->has_target = 1U;
  slot->has_runtime_address = 1U;
  slot->section_index = section_index;
  slot->offset = offset;
  slot->size = size;
  slot->target_section_index = target_section_index;
  slot->target_offset = target_offset;
  slot->runtime_address = runtime_address;
  slot->confidence = confidence;
  slot->owner_element_offset = owner_element_offset;
  if (!copy_policy_text(slot->owner_kind, sizeof(slot->owner_kind), owner_kind) ||
      !copy_policy_text(slot->owner_id, sizeof(slot->owner_id), owner_id) ||
      !copy_policy_text(slot->owner_layout_id, sizeof(slot->owner_layout_id), owner_layout_id) ||
      !copy_policy_text(slot->xref_generation_mode, sizeof(slot->xref_generation_mode), xref_generation_mode)) {
    memset(slot, 0, sizeof(*slot));
    --policy->manual_runtime_address_ref_count;
    return 0;
  }
  return 1;
}

static int policy_add_manual_representation_local(M68kAnalysisPolicy *policy, uint32_t section_index,
    uint32_t offset, uint32_t size, uint8_t style_id, uint8_t has_operand_index, uint8_t operand_index,
    const char *symbol_name) {
  M68kAnalysisManualRepresentation *slot;
  uint16_t index;
  uint16_t symbol_id = 0U;
  uint16_t target_equate_index = 0U;
  if (policy == NULL || size == 0U || style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_NONE ||
      policy->manual_representation_count >= M68K_ANALYSIS_MANUAL_REPRESENTATION_LIMIT) {
    return 0;
  }
  if (symbol_name != NULL && symbol_name[0] != '\0') {
    symbol_id = amiga_os_name_id(M68K_PLATFORM_NAME_SYMBOL, symbol_name);
    if (amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, symbol_id) == NULL) {
      symbol_id = 0U;
      if (!policy_find_target_equate_index_local(policy, symbol_name, &target_equate_index)) return 0;
    }
  }
  for (index = 0U; index < policy->manual_representation_count; ++index) {
    const M68kAnalysisManualRepresentation *existing = &policy->manual_representations[index];
    if (existing->has_section_index && existing->section_index == section_index &&
        existing->offset == offset && existing->size == size &&
        existing->has_operand_index == has_operand_index &&
        (!has_operand_index || existing->operand_index == operand_index)) {
      return existing->style_id == style_id && existing->symbol_id == symbol_id &&
        existing->target_equate_index == target_equate_index;
    }
  }
  slot = &policy->manual_representations[policy->manual_representation_count++];
  memset(slot, 0, sizeof(*slot));
  slot->has_section_index = 1U;
  slot->style_id = style_id;
  slot->has_operand_index = has_operand_index;
  slot->operand_index = has_operand_index ? operand_index : 0U;
  slot->section_index = section_index;
  slot->offset = offset;
  slot->size = size;
  slot->symbol_id = symbol_id;
  slot->target_equate_index = target_equate_index;
  return 1;
}

static int policy_runtime_address_to_source_offset_local(const M68kAnalysisPolicy *policy,
    uint32_t runtime_address, uint32_t *out_section_index, uint32_t *out_offset) {
  uint16_t index;
  if (policy == NULL || out_section_index == NULL || out_offset == NULL) return 0;
  for (index = policy->runtime_range_count; index > 0U; --index) {
    const M68kAnalysisRuntimeRange *range = &policy->runtime_ranges[index - 1U];
    uint32_t delta;
    if (!range->has_section_index || runtime_address < range->runtime_address) continue;
    delta = runtime_address - range->runtime_address;
    if ((range->size != 0U && delta >= range->size) || range->offset > UINT32_MAX - delta) continue;
    *out_section_index = range->section_index;
    *out_offset = range->offset + delta;
    return 1;
  }
  return 0;
}

static int analysis_range_overlaps_accepted_code(const M68kSectionAnalysisIR *section, uint32_t start,
    uint32_t size) {
  uint32_t end;
  size_t block_index;
  if (section == NULL || size == 0U || start > UINT32_MAX - size) return 1;
  end = start + size;
  for (block_index = 0U; block_index < section->block_count; ++block_index) {
    const M68kCfgBlockIR *block = &section->blocks[block_index];
    if (block->certainty != M68K_CODE_CERTAIN) continue;
    if (start < block->end_offset && end > block->start_offset) return 1;
  }
  return 0;
}

static const M68kRuntimeViewIR *find_decompression_runtime_copy_view(const M68kSourceAnalysisIR *analysis,
    const PlatformDecompressionIdentifyResult *result) {
  const M68kSectionAnalysisIR *section;
  size_t view_index;
  const M68kRuntimeViewIR *best = NULL;
  if (analysis == NULL || result == NULL || !result->has_source_section ||
      result->source_section_index >= analysis->section_count) {
    return NULL;
  }
  section = &analysis->sections[result->source_section_index];
  for (view_index = 0U; view_index < section->runtime_view_count; ++view_index) {
    const M68kRuntimeViewIR *view = &section->runtime_views[view_index];
    if (view->storage_offset != result->source_section_offset) continue;
    if (view->kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY &&
        view->kind != M68K_FACT_RUNTIME_RANGE_KIND_CONFLICTING_DISCOVERED_COPY) {
      continue;
    }
    if (best == NULL || view->size > best->size) best = view;
  }
  return best;
}

static size_t read_file_prefix_local(const char *path, uint8_t *buffer, size_t buffer_size) {
  FILE *file;
  size_t read_count;
  if (path == NULL || buffer == NULL || buffer_size == 0U) return 0U;
  file = fopen(path, "rb");
  if (file == NULL) return 0U;
  read_count = fread(buffer, 1U, buffer_size, file);
  fclose(file);
  return read_count;
}

static int read_file_to_arena_local(Arena *arena, const char *path, uint8_t **out_data, size_t *out_size) {
  FILE *file;
  long file_size_long;
  size_t file_size;
  uint8_t *data;
  if (out_data != NULL) *out_data = NULL;
  if (out_size != NULL) *out_size = 0U;
  if (arena == NULL || path == NULL || out_data == NULL || out_size == NULL) return -1;
  file = fopen(path, "rb");
  if (file == NULL) return -1;
  if (fseek(file, 0L, SEEK_END) != 0) {
    fclose(file);
    return -1;
  }
  file_size_long = ftell(file);
  if (file_size_long < 0L) {
    fclose(file);
    return -1;
  }
  if (fseek(file, 0L, SEEK_SET) != 0) {
    fclose(file);
    return -1;
  }
  file_size = (size_t)file_size_long;
  data = (uint8_t *)arena_alloc(arena, file_size != 0U ? file_size : 1U);
  if (data == NULL) {
    fclose(file);
    return -1;
  }
  if (file_size != 0U && fread(data, 1U, file_size, file) != file_size) {
    fclose(file);
    return -1;
  }
  fclose(file);
  *out_data = data;
  *out_size = file_size;
  return 0;
}

static int infer_decompressed_load_entry_from_initial_control_local(const char *path, uint8_t max_cpu,
    uint32_t load_address, uint32_t decompressed_size, uint32_t *out_entrypoint,
    uint32_t *out_initial_control_target) {
  uint8_t prefix[32];
  size_t prefix_size;
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult add_result;
  M68kDecodeIR decode;
  const M68kDecodeCandidate *candidate = NULL;
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  uint64_t runtime_start = load_address;
  uint64_t runtime_end = runtime_start + (uint64_t)decompressed_size;
  int inferred = 0;
  memset(&object, 0, sizeof(object));
  memset(&decode, 0, sizeof(decode));
  if (out_entrypoint != NULL) *out_entrypoint = 0U;
  if (out_initial_control_target != NULL) *out_initial_control_target = 0U;
  if (decompressed_size == 0U || runtime_end <= runtime_start) return 0;
  prefix_size = read_file_prefix_local(path, prefix, sizeof(prefix));
  if (prefix_size == 0U || prefix_size > UINT32_MAX) return 0;
  if (m68k_object_create(&object) != 0) return 0;
  memset(&section, 0, sizeof(section));
  section.kind = M68K_SECTION_CODE;
  section.size = (uint32_t)prefix_size;
  section.data_size = (uint32_t)prefix_size;
  add_result = m68k_object_add_section(&object, &section);
  if (!add_result.ok ||
      m68k_object_set_section_data(&object, add_result.index, prefix, (uint32_t)prefix_size) != 0 ||
      m68k_decode_ir_build_object_sections(&decode, &object, m68k_diag_sink(NULL)) != 0 ||
      m68k_decode_ir_ensure_candidate_at(&decode, 0U, 0U, max_cpu, &candidate, m68k_diag_sink(NULL)) != 0 ||
      candidate == NULL ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    goto cleanup;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || metadata->flow_kind != M68K_SIM_FLOW_JUMP) goto cleanup;
  for (operand_index = 0U; operand_index < instruction.operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction.operands[operand_index];
    uint8_t shape;
    uint32_t target;
    if (metadata->operand_result_kinds[operand_index] != M68K_SIM_RESULT_CONTROL_TARGET) continue;
    shape = m68k_instruction_operand_decoded_ea_shape(operand);
    if (m68k_instruction_decoded_ea_target_kind(operand, shape, 0) != 1U) continue;
    target = operand->value.value;
    if ((uint64_t)target < runtime_start || (uint64_t)target >= runtime_end) continue;
    if (out_entrypoint != NULL) *out_entrypoint = load_address;
    if (out_initial_control_target != NULL) *out_initial_control_target = target;
    inferred = 1;
    break;
  }

cleanup:
  m68k_decode_ir_destroy(&decode);
  m68k_object_destroy(&object);
  return inferred;
}

static int automatic_decompression_candidate_is_useful(const PlatformDecompressionCandidate *candidate) {
  if (candidate == NULL) return 0;
  if (candidate->packed_size < 16U || candidate->decompressed_size < 16U) return 0;
  if (candidate->decompressed_size <= candidate->packed_size + 15U) return 0;
  return 1;
}

static const char *decompression_event_kind_name_local(uint8_t event_kind) {
  switch (event_kind) {
    case PLATFORM_DECOMPRESSION_EVENT_KIND_DECOMPRESSION: return "decompression";
    default: return "unknown";
  }
}

static const char *derived_target_suggestion_kind_name_local(uint8_t kind) {
  switch (kind) {
    case PLATFORM_DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD: return "decompressed_payload";
    default: return "unknown";
  }
}

static const char *decompression_source_kind_name_local(uint8_t source_kind) {
  switch (source_kind) {
    case PLATFORM_DECOMPRESSION_SOURCE_SECTION_RANGE: return "section_range";
    case PLATFORM_DECOMPRESSION_SOURCE_RECOGNIZED_UNPACKER: return "recognized_unpacker";
    case PLATFORM_DECOMPRESSION_SOURCE_SELF_DECRUNCHER: return "self_decruncher";
    default: return "unknown";
  }
}

static const char *decompression_status_name_local(uint8_t status) {
  switch (status) {
    case PLATFORM_DECOMPRESSION_STATUS_IDENTIFIED: return "identified";
    case PLATFORM_DECOMPRESSION_STATUS_MATERIALIZABLE: return "materializable";
    case PLATFORM_DECOMPRESSION_STATUS_NEEDS_RUNTIME_METADATA: return "needs_runtime_metadata";
    case PLATFORM_DECOMPRESSION_STATUS_NEEDS_SIMULATED_DECRUNCH: return "needs_simulated_decrunch";
    case PLATFORM_DECOMPRESSION_STATUS_SIMULATED_OUTPUT_OBSERVED: return "simulated_output_observed";
    case PLATFORM_DECOMPRESSION_STATUS_NEEDS_REVIEW_BLOCKER: return "needs_review_blocker";
    default: return "unknown";
  }
}

static const char *decompression_reason_name_local(uint8_t reason) {
  switch (reason) {
    case PLATFORM_DECOMPRESSION_REASON_INVALID_RECORD: return "invalid_record";
    case PLATFORM_DECOMPRESSION_REASON_INITIAL_CONTROL_TARGET_VALIDATED_PROVIDER_WRAPPER:
      return "initial_control_target_validated_provider_wrapper";
    case PLATFORM_DECOMPRESSION_REASON_INITIAL_CONTROL_TARGET_VALIDATED_RUNTIME_COPY:
      return "initial_control_target_validated_runtime_copy";
    case PLATFORM_DECOMPRESSION_REASON_MISSING_RUNTIME_COPY_EVIDENCE: return "missing_runtime_copy_evidence";
    case PLATFORM_DECOMPRESSION_REASON_RUNTIME_COPY_CONFLICTING: return "runtime_copy_conflicting";
    case PLATFORM_DECOMPRESSION_REASON_RUNTIME_COPY_SHORT: return "runtime_copy_short";
    case PLATFORM_DECOMPRESSION_REASON_RUNTIME_COPY_OVERSIZE: return "runtime_copy_oversize";
    case PLATFORM_DECOMPRESSION_REASON_MISSING_DECOMPRESSED_LOAD_ENTRY: return "missing_decompressed_load_entry";
    case PLATFORM_DECOMPRESSION_REASON_NATIVE_TETRAGON_UNPACK_VALIDATED: return "native_tetragon_unpack_validated";
    case PLATFORM_DECOMPRESSION_REASON_RECOGNIZED_UNPACKER_SIGNATURE: return "recognized_unpacker_signature";
    case PLATFORM_DECOMPRESSION_REASON_UNIDENTIFIED_SELF_DECRUNCHER: return "unidentified_self_decruncher";
    case PLATFORM_DECOMPRESSION_REASON_SIMULATED_PC_RANGE_STOP: return "simulated_pc_range_stop";
    case PLATFORM_DECOMPRESSION_REASON_SIMULATED_PC_OUT_OF_RANGE: return "simulated_pc_out_of_range";
    case PLATFORM_DECOMPRESSION_REASON_SIMULATED_INSTRUCTION_LIMIT: return "simulated_instruction_limit";
    case PLATFORM_DECOMPRESSION_REASON_SIMULATED_DECODE_ERROR: return "simulated_decode_error";
    case PLATFORM_DECOMPRESSION_REASON_SIMULATED_ERROR: return "simulated_error";
    case PLATFORM_DECOMPRESSION_REASON_SIMULATED_BAD_ARGUMENT: return "simulated_bad_argument";
    case PLATFORM_DECOMPRESSION_REASON_SIMULATED_NO_OUTPUT_RANGE: return "simulated_no_output_range";
    case PLATFORM_DECOMPRESSION_REASON_SIMULATED_UNKNOWN_STOP: return "simulated_unknown_stop";
    case PLATFORM_DECOMPRESSION_REASON_INVALID_DECOMPRESSED_ENTRYPOINT: return "invalid_decompressed_entrypoint";
    case PLATFORM_DECOMPRESSION_REASON_NATIVE_TETRAGON_UNPACK_DEFERRED:
      return "native_tetragon_unpack_deferred";
    case PLATFORM_DECOMPRESSION_REASON_PROVIDER_WRAPPER_VALIDATION_DEFERRED:
      return "provider_wrapper_validation_deferred";
    default: return "unknown";
  }
}

static const char *decompression_payload_role_name_local(uint8_t payload_role) {
  switch (payload_role) {
    case PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_UNKNOWN_RUNTIME_PAYLOAD: return "unknown_runtime_payload";
    case PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_PRIMARY_PROGRAM: return "primary_program";
    case PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_ASSET_DATA: return "asset_data";
    case PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_UNKNOWN_DATA: return "unknown_data";
    default: return "unknown";
  }
}

static const char *decompression_payload_role_confidence_name_local(uint8_t confidence) {
  switch (confidence) {
    case PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_TOOL_INFERRED: return "tool_inferred";
    case PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_NATIVE_UNPACK_ENTRY_VALIDATED:
      return "native_unpack_entry_validated";
    case PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_SIGNATURE_ONLY: return "signature_only";
    case PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_OBSERVED_OUTPUT_ONLY: return "observed_output_only";
    default: return "unknown";
  }
}

static const char *decompression_parent_remains_active_name_local(uint8_t parent_remains_active) {
  switch (parent_remains_active) {
    case PLATFORM_DECOMPRESSION_PARENT_REMAINS_ACTIVE_FALSE: return "false";
    case PLATFORM_DECOMPRESSION_PARENT_REMAINS_ACTIVE_TRUE: return "true";
    default: return "unknown";
  }
}

static const char *decompression_codec_support_name_local(uint8_t codec_support) {
  switch (codec_support) {
    case PLATFORM_DECOMPRESSION_CODEC_SUPPORT_EXTERNAL_PROVIDER: return "external_provider";
    case PLATFORM_DECOMPRESSION_CODEC_SUPPORT_NATIVE_DECOMPRESSOR: return "native_decompressor";
    case PLATFORM_DECOMPRESSION_CODEC_SUPPORT_SIMULATOR_REQUIRED: return "simulator_required";
    default: return "unknown";
  }
}

static uint8_t decompression_suggestion_reason_local(const PlatformDecompressionIdentifyResult *result,
    const M68kRuntimeViewIR *runtime_copy_view) {
  if (result == NULL) return PLATFORM_DECOMPRESSION_REASON_INVALID_RECORD;
  if (result->has_decompressed_load_entry &&
      result->has_decompressed_load_entry_from_wrapper &&
      !result->decompressed)
    return PLATFORM_DECOMPRESSION_REASON_PROVIDER_WRAPPER_VALIDATION_DEFERRED;
  if (result->has_decompressed_load_entry)
    return result->has_decompressed_load_entry_from_wrapper ?
      PLATFORM_DECOMPRESSION_REASON_INITIAL_CONTROL_TARGET_VALIDATED_PROVIDER_WRAPPER :
      PLATFORM_DECOMPRESSION_REASON_INITIAL_CONTROL_TARGET_VALIDATED_RUNTIME_COPY;
  if (runtime_copy_view == NULL) return PLATFORM_DECOMPRESSION_REASON_MISSING_RUNTIME_COPY_EVIDENCE;
  if (runtime_copy_view->kind == M68K_FACT_RUNTIME_RANGE_KIND_CONFLICTING_DISCOVERED_COPY)
    return PLATFORM_DECOMPRESSION_REASON_RUNTIME_COPY_CONFLICTING;
  if (runtime_copy_view->size < result->packed_size) return PLATFORM_DECOMPRESSION_REASON_RUNTIME_COPY_SHORT;
  if (runtime_copy_view->size > result->packed_size) return PLATFORM_DECOMPRESSION_REASON_RUNTIME_COPY_OVERSIZE;
  return PLATFORM_DECOMPRESSION_REASON_MISSING_DECOMPRESSED_LOAD_ENTRY;
}

static uint8_t decompression_suggestion_payload_role_local(const PlatformDecompressionIdentifyResult *result) {
  if (result != NULL && result->has_decompressed_load_entry)
    return PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_PRIMARY_PROGRAM;
  return PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_UNKNOWN_RUNTIME_PAYLOAD;
}

static uint8_t decompression_parent_remains_active_local(const PlatformDecompressionIdentifyResult *result) {
  if (result == NULL || !result->parent_remains_active_known)
    return PLATFORM_DECOMPRESSION_PARENT_REMAINS_ACTIVE_UNKNOWN;
  return result->parent_remains_active ? PLATFORM_DECOMPRESSION_PARENT_REMAINS_ACTIVE_TRUE :
    PLATFORM_DECOMPRESSION_PARENT_REMAINS_ACTIVE_FALSE;
}

typedef struct PlatformSelfDecrunchEvent {
  uint32_t source_section_index;
  uint32_t decompressor_entry_offset;
  uint32_t transfer_offset;
  uint32_t load_address;
  uint32_t entrypoint;
  uint32_t observed_write_start;
  uint32_t observed_write_end;
  uint32_t observed_write_count;
  uint32_t simulated_output_start;
  uint32_t simulated_output_end;
  uint32_t simulated_start_pc;
  uint32_t simulated_stop_pc;
  uint32_t simulated_step_count;
  uint32_t simulated_write_count;
  uint32_t entry_validation_accepted_instructions;
  uint32_t entry_validation_unsupported_instruction_demotes;
  uint32_t entry_validation_required_instruction_failures;
  uint32_t entry_validation_code_start_control_targets;
  char simulated_output_sha256[65];
  char simulated_diagnostic[M68K_DIAG_MESSAGE_SIZE];
  uint8_t simulated_stop_reason;
  uint8_t has_simulated_output;
  uint8_t simulation_attempted;
  uint8_t entry_validation_attempted;
  uint8_t entry_validation_valid;
  uint8_t parent_remains_active;
} PlatformSelfDecrunchEvent;

typedef struct PlatformRecognizedUnpackerEvent {
  uint32_t source_section_index;
  uint32_t marker_offset;
  uint32_t compressed_source_section_offset;
  uint32_t compressed_source_section_end_offset;
  uint32_t postpass_source_start_address;
  uint32_t postpass_source_end_address;
  uint32_t target_start_address;
  uint32_t target_end_address;
  uint32_t entrypoint;
  uint32_t decompressed_size;
  uint32_t compressed_source_consumed_section_offset;
  uint32_t postpass_source_consumed_address;
  uint32_t copied_stub_storage_offset;
  uint32_t copied_stub_runtime_address;
  uint32_t copied_stub_transfer_offset;
  uint32_t copied_stub_transfer_site_offset;
  uint32_t native_execution_start_pc;
  uint32_t native_execution_step_count;
  uint32_t lz_long_reference_bit_count;
  uint32_t entry_validation_accepted_instructions;
  uint32_t entry_validation_unsupported_instruction_demotes;
  uint32_t entry_validation_required_instruction_failures;
  uint32_t entry_validation_code_start_control_targets;
  char codec_id[64];
  char codec_name[160];
  char provider_id[32];
  char decompressed_sha256[65];
  uint8_t postpass_escape_byte;
  uint8_t native_unpack_validated;
  uint8_t native_execution_attempted;
  uint8_t native_execution_deferred;
  uint8_t native_execution_stop_reason;
  uint8_t entry_validation_attempted;
  uint8_t entry_validation_valid;
  uint8_t has_copied_stub;
  uint8_t has_copied_stub_transfer;
} PlatformRecognizedUnpackerEvent;

typedef struct PlatformRuntimeWriteObservation {
  uint32_t start;
  uint32_t end;
} PlatformRuntimeWriteObservation;

typedef struct PlatformTetragonBitReader {
  const uint8_t *data;
  uint32_t start_offset;
  uint32_t cursor_offset;
  uint32_t d0;
  uint8_t failed;
} PlatformTetragonBitReader;

static void make_decompression_event_id_local(char *out, size_t out_size,
    const PlatformDecompressionIdentifyResult *result) {
  const char *codec_id = "unknown";
  if (out == NULL || out_size == 0U) return;
  if (result != NULL && result->codec_id[0] != '\0') codec_id = result->codec_id;
  snprintf(out, out_size, "decompression:section:%u:%08X:%s",
    result != NULL ? (unsigned)result->source_section_index : 0U,
    result != NULL ? (unsigned)result->source_section_offset : 0U,
    codec_id);
}

static void make_self_decrunch_event_id_local(char *out, size_t out_size,
    const PlatformSelfDecrunchEvent *event) {
  if (out == NULL || out_size == 0U) return;
  snprintf(out, out_size, "decompression:self_decrunch:section:%u:%08X:%08X",
    event != NULL ? (unsigned)event->source_section_index : 0U,
    event != NULL ? (unsigned)event->decompressor_entry_offset : 0U,
    event != NULL ? (unsigned)event->entrypoint : 0U);
}

static void make_recognized_unpacker_event_id_local(char *out, size_t out_size,
    const PlatformRecognizedUnpackerEvent *event) {
  const char *codec_id = "unknown";
  if (out == NULL || out_size == 0U) return;
  if (event != NULL && event->codec_id[0] != '\0') codec_id = event->codec_id;
  snprintf(out, out_size, "decompression:recognized_unpacker:section:%u:%08X:%s",
    event != NULL ? (unsigned)event->source_section_index : 0U,
    event != NULL ? (unsigned)event->marker_offset : 0U,
    codec_id);
}

static int runtime_transfer_target_from_candidate_min_local(const M68kDecodeSectionIR *section,
    const M68kSectionAnalysisIR *section_analysis, const M68kDecodeCandidate *candidate,
    uint32_t min_target_address, uint8_t skip_known_code_target,
    uint32_t *out_target, uint8_t *out_parent_remains_active) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (out_target != NULL) *out_target = 0U;
  if (out_parent_remains_active != NULL) *out_parent_remains_active = 1U;
  if (section == NULL || section_analysis == NULL || candidate == NULL || out_target == NULL ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || metadata->flow_conditional != 0U ||
      (metadata->flow_kind != M68K_SIM_FLOW_JUMP && metadata->flow_kind != M68K_SIM_FLOW_CALL)) {
    return 0;
  }
  for (operand_index = 0U; operand_index < instruction.operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction.operands[operand_index];
    uint8_t shape;
    uint32_t target;
    if (metadata->operand_result_kinds[operand_index] != M68K_SIM_RESULT_CONTROL_TARGET) continue;
    shape = m68k_instruction_operand_decoded_ea_shape(operand);
    if (m68k_instruction_decoded_ea_target_kind(operand, shape, 0) != 1U) continue;
    target = operand->value.value;
    if (target < min_target_address) continue;
    if (skip_known_code_target && target < section->size && section_analysis->certain_code_byte != NULL &&
        section_analysis->certain_code_byte[target] != 0U) {
      continue;
    }
    *out_target = target;
    if (out_parent_remains_active != NULL)
      *out_parent_remains_active = metadata->flow_kind == M68K_SIM_FLOW_CALL ? 1U : 0U;
    return 1;
  }
  return 0;
}

static int runtime_transfer_target_from_candidate_local(const M68kDecodeSectionIR *section,
    const M68kSectionAnalysisIR *section_analysis, const M68kDecodeCandidate *candidate,
    uint32_t *out_target, uint8_t *out_parent_remains_active) {
  return runtime_transfer_target_from_candidate_min_local(section, section_analysis, candidate, 0x1000U, 1U,
    out_target, out_parent_remains_active);
}

static int same_section_unconditional_bridge_target_local(const M68kDecodeCandidate *candidate,
    const M68kSimFormMetadata *metadata, size_t section_index, uint32_t *out_target) {
  size_t target_index;
  if (out_target != NULL) *out_target = 0U;
  if (candidate == NULL || metadata == NULL || out_target == NULL ||
      metadata->flow_conditional ||
      (metadata->flow_kind != M68K_SIM_FLOW_BRANCH && metadata->flow_kind != M68K_SIM_FLOW_JUMP)) {
    return 0;
  }
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind != M68K_DECODE_TARGET_BRANCH && target->kind != M68K_DECODE_TARGET_JUMP) continue;
    if (target->has_section && target->section_index != section_index) continue;
    if (target->offset <= candidate->offset + candidate->byte_count) continue;
    *out_target = target->offset;
    return 1;
  }
  return 0;
}

static int self_decrunch_event_duplicate_local(const PlatformSelfDecrunchEvent *events, size_t event_count,
    const PlatformSelfDecrunchEvent *candidate) {
  size_t index;
  if (events == NULL || candidate == NULL) return 0;
  for (index = 0U; index < event_count; ++index) {
    if (events[index].source_section_index == candidate->source_section_index &&
        events[index].decompressor_entry_offset == candidate->decompressor_entry_offset &&
        events[index].entrypoint == candidate->entrypoint) {
      return 1;
    }
  }
  return 0;
}

static int recognized_unpacker_event_duplicate_local(const PlatformRecognizedUnpackerEvent *events,
    size_t event_count, const PlatformRecognizedUnpackerEvent *candidate) {
  size_t index;
  if (events == NULL || candidate == NULL) return 0;
  for (index = 0U; index < event_count; ++index) {
    if (events[index].source_section_index == candidate->source_section_index &&
        events[index].marker_offset == candidate->marker_offset &&
        strcmp(events[index].codec_id, candidate->codec_id) == 0) {
      return 1;
    }
  }
  return 0;
}

static uint32_t recognized_unpacker_code_end_after_marker_local(const M68kSectionAnalysisIR *section_analysis,
    uint32_t marker_end) {
  uint32_t code_end = marker_end;
  uint32_t limit = marker_end > UINT32_MAX - 0x400U ? UINT32_MAX : marker_end + 0x400U;
  size_t block_index;
  if (section_analysis == NULL) return marker_end;
  for (block_index = 0U; block_index < section_analysis->block_count; ++block_index) {
    const M68kCfgBlockIR *block = &section_analysis->blocks[block_index];
    if (block->end_offset <= marker_end || block->start_offset >= limit) continue;
    if (block->end_offset > code_end) code_end = block->end_offset;
  }
  return code_end;
}

static int recognized_unpacker_abs_operand_value_local(const M68kDecodeCandidate *candidate,
    uint32_t *out_value) {
  M68kInstructionIR instruction;
  size_t operand_index;
  if (candidate == NULL || out_value == NULL) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  for (operand_index = 0U; operand_index < candidate->operand_count &&
      operand_index < M68K_DECODE_IR_MAX_OPERANDS; ++operand_index) {
    const M68kOperandIR *operand = &instruction.operands[operand_index];
    uint8_t shape = m68k_instruction_operand_decoded_ea_shape(operand);
    if (m68k_instruction_decoded_ea_target_kind(operand, shape, 0) == 1U) {
      *out_value = operand->value.value;
      return 1;
    }
  }
  return 0;
}

static int recognized_unpacker_immediate_operand_value_local(const M68kDecodeCandidate *candidate,
    uint32_t *out_value) {
  M68kInstructionIR instruction;
  size_t operand_index;
  if (candidate == NULL || out_value == NULL) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  for (operand_index = 0U; operand_index < candidate->operand_count &&
      operand_index < M68K_DECODE_IR_MAX_OPERANDS; ++operand_index) {
    const M68kOperandIR *operand = &instruction.operands[operand_index];
    if (operand->value.kind == M68K_ASM_OPERAND_IMM ||
        (operand->value.kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 7U &&
          operand->value.ea_reg == 4U)) {
      *out_value = operand->value.value;
      return 1;
    }
  }
  return 0;
}

static int recognized_unpacker_asm_operand_is_address_register_local(const M68kAsmOperandValue *operand,
    uint8_t reg) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_AN && operand->reg == reg) return 1;
  if (operand->kind == M68K_ASM_OPERAND_RN && operand->reg_is_address && operand->reg == reg) {
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 1U && operand->ea_reg == reg) {
    return 1;
  }
  return 0;
}

static int recognized_unpacker_abs_operand_to_a1_local(const M68kDecodeCandidate *candidate,
    uint32_t *out_value) {
  size_t operand_index;
  int has_a1 = 0;
  if (candidate == NULL || out_value == NULL) return 0;
  for (operand_index = 0U; operand_index < candidate->operand_count &&
      operand_index < M68K_DECODE_IR_MAX_OPERANDS; ++operand_index) {
    if (recognized_unpacker_asm_operand_is_address_register_local(&candidate->operands[operand_index], 1U)) {
      has_a1 = 1;
      break;
    }
  }
  if (!has_a1) return 0;
  for (operand_index = 0U; operand_index < candidate->operand_count &&
      operand_index < M68K_DECODE_IR_MAX_OPERANDS; ++operand_index) {
    const M68kAsmOperandValue *operand = &candidate->operands[operand_index];
    if (candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_ABSL ||
        operand->kind == M68K_ASM_OPERAND_ABSL ||
        (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 7U &&
          (operand->ea_reg == 0U || operand->ea_reg == 1U))) {
      *out_value = operand->value;
      return 1;
    }
  }
  return 0;
}

static int recognized_unpacker_jump_target_local(const M68kDecodeCandidate *candidate, uint32_t *out_target) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (candidate == NULL || out_target == NULL) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || metadata->flow_conditional != 0U || metadata->flow_kind != M68K_SIM_FLOW_JUMP)
    return 0;
  for (operand_index = 0U; operand_index < instruction.operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction.operands[operand_index];
    uint8_t shape;
    if (metadata->operand_result_kinds[operand_index] != M68K_SIM_RESULT_CONTROL_TARGET) continue;
    shape = m68k_instruction_operand_decoded_ea_shape(operand);
    if (m68k_instruction_decoded_ea_target_kind(operand, shape, 0) == 1U) {
      *out_target = operand->value.value;
      return 1;
    }
  }
  return 0;
}

static void recognized_unpacker_bounds_from_code_window_local(const M68kDecodeSectionIR *decode_section,
    uint32_t start_offset, uint32_t end_offset, uint32_t *out_target_start_address,
    uint32_t *out_source_end_address, uint32_t *out_entrypoint) {
  size_t candidate_index;
  uint32_t target_start_address = 0U;
  uint32_t source_end_address = 0U;
  uint32_t entrypoint = 0U;
  if (out_target_start_address != NULL) *out_target_start_address = 0U;
  if (out_source_end_address != NULL) *out_source_end_address = 0U;
  if (out_entrypoint != NULL) *out_entrypoint = 0U;
  if (decode_section == NULL || start_offset >= end_offset) return;
  for (candidate_index = 0U; candidate_index < decode_section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &decode_section->candidates[candidate_index];
    uint32_t value;
    if (candidate->offset < start_offset || candidate->offset >= end_offset) continue;
    if (target_start_address == 0U && recognized_unpacker_abs_operand_value_local(candidate, &value)) {
      target_start_address = value;
    } else if (source_end_address == 0U && recognized_unpacker_abs_operand_value_local(candidate, &value)) {
      source_end_address = value;
    }
    if (recognized_unpacker_jump_target_local(candidate, &value)) {
      entrypoint = value;
    }
  }
  if (out_target_start_address != NULL) *out_target_start_address = target_start_address;
  if (out_source_end_address != NULL) *out_source_end_address = source_end_address;
  if (out_entrypoint != NULL) *out_entrypoint = entrypoint;
}

static uint32_t recognized_unpacker_postpass_source_start_local(const M68kDecodeSectionIR *decode_section,
    const M68kSectionAnalysisIR *section_analysis, uint32_t target_start_address,
    uint32_t postpass_source_end_address, uint32_t entrypoint) {
  size_t candidate_index;
  uint32_t best = 0U;
  if (decode_section == NULL || section_analysis == NULL || section_analysis->certain_code_byte == NULL ||
      target_start_address >= postpass_source_end_address) {
    return 0U;
  }
  for (candidate_index = 0U; candidate_index < decode_section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &decode_section->candidates[candidate_index];
    uint32_t value;
    if (candidate->offset >= section_analysis->certain_code_size ||
        !section_analysis->certain_code_byte[candidate->offset])
      continue;
    if (!recognized_unpacker_abs_operand_to_a1_local(candidate, &value)) continue;
    if (value <= target_start_address || value >= postpass_source_end_address || value == entrypoint) continue;
    if (best == 0U || value < best) best = value;
  }
  return best;
}

static int recognized_unpacker_postpass_escape_byte_local(const M68kDecodeSectionIR *decode_section,
    uint32_t marker_end, uint8_t *out_escape_byte) {
  size_t candidate_index;
  if (out_escape_byte != NULL) *out_escape_byte = 0U;
  if (decode_section == NULL || out_escape_byte == NULL) return 0;
  for (candidate_index = 0U; candidate_index < decode_section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &decode_section->candidates[candidate_index];
    uint32_t value;
    if (candidate->offset != marker_end) continue;
    if (!recognized_unpacker_immediate_operand_value_local(candidate, &value)) return 0;
    *out_escape_byte = (uint8_t)(value & 0xFFU);
    return 1;
  }
  return 0;
}

static int recognized_unpacker_moveq_d1_immediate_local(const M68kDecodeCandidate *candidate,
    uint32_t *out_value) {
  if (out_value != NULL) *out_value = 0U;
  if (candidate == NULL || out_value == NULL || candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVEQ ||
      candidate->operand_count != 2U) {
    return 0;
  }
  if (candidate->operands[0].kind != M68K_ASM_OPERAND_IMM ||
      candidate->operands[1].kind != M68K_ASM_OPERAND_DN ||
      candidate->operands[1].reg != 1U) {
    return 0;
  }
  *out_value = candidate->operands[0].value;
  return 1;
}

static uint32_t recognized_tetragon_long_reference_bit_count_local(const M68kDecodeSectionIR *decode_section,
    uint32_t marker_end, uint32_t code_end) {
  size_t candidate_index;
  if (decode_section == NULL || marker_end >= code_end) return 0U;
  for (candidate_index = 0U; candidate_index < decode_section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &decode_section->candidates[candidate_index];
    const M68kDecodeCandidate *previous = NULL;
    size_t previous_index;
    size_t target_index;
    uint32_t value;
    if (candidate->offset < marker_end || candidate->offset >= code_end ||
        candidate->mnemonic_id != M68K_ASM_MNEMONIC_BRA) {
      continue;
    }
    for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
      const M68kDecodeTarget *target = &candidate->targets[target_index];
      if (target->kind == M68K_DECODE_TARGET_BRANCH && target->offset < candidate->offset) break;
    }
    if (target_index >= candidate->target_count) continue;
    for (previous_index = 0U; previous_index < decode_section->candidate_count; ++previous_index) {
      const M68kDecodeCandidate *candidate_previous = &decode_section->candidates[previous_index];
      if (candidate_previous->offset < marker_end || candidate_previous->offset >= code_end) continue;
      if (candidate_previous->offset + candidate_previous->byte_count == candidate->offset) {
        previous = candidate_previous;
        break;
      }
    }
    if (recognized_unpacker_moveq_d1_immediate_local(previous, &value) && (value == 8U || value == 11U)) {
      return value;
    }
  }
  return 0U;
}

static int tetragon_bit_reader_next_local(PlatformTetragonBitReader *reader, uint8_t *out_bit) {
  uint8_t bit;
  uint32_t loaded;
  if (out_bit != NULL) *out_bit = 0U;
  if (reader == NULL || out_bit == NULL || reader->failed) return 0;
  bit = (uint8_t)(reader->d0 & 1U);
  reader->d0 >>= 1;
  if (reader->d0 == 0U) {
    if (reader->cursor_offset < reader->start_offset + 4U) {
      reader->failed = 1U;
      return 0;
    }
    reader->cursor_offset -= 4U;
    loaded = read_be32_local(reader->data + reader->cursor_offset);
    bit = (uint8_t)(loaded & 1U);
    reader->d0 = 0x80000000U | (loaded >> 1);
  }
  *out_bit = bit;
  return 1;
}

static int tetragon_bit_reader_bits_local(PlatformTetragonBitReader *reader, uint32_t bit_count,
    uint32_t *out_value) {
  uint32_t index;
  uint32_t value = 0U;
  if (out_value != NULL) *out_value = 0U;
  if (reader == NULL || out_value == NULL || bit_count > 24U) return 0;
  for (index = 0U; index < bit_count; ++index) {
    uint8_t bit;
    if (!tetragon_bit_reader_next_local(reader, &bit)) return 0;
    value = (value << 1) | (uint32_t)bit;
  }
  *out_value = value;
  return 1;
}

static int tetragon_write_byte_local(uint8_t *memory, size_t memory_size, uint32_t address, uint8_t value) {
  if (memory == NULL || (size_t)address >= memory_size) return 0;
  memory[address] = value;
  return 1;
}

static int tetragon_read_byte_local(const uint8_t *memory, size_t memory_size, uint32_t address,
    uint8_t *out_value) {
  if (out_value != NULL) *out_value = 0U;
  if (memory == NULL || out_value == NULL || (size_t)address >= memory_size) return 0;
  *out_value = memory[address];
  return 1;
}

static int recognized_tetragon_unpack_lz_stage_local(const M68kDecodeSectionIR *decode_section,
    const PlatformRecognizedUnpackerEvent *event, uint8_t *memory, size_t memory_size,
    uint32_t long_reference_bit_count, uint32_t *out_consumed_offset) {
  PlatformTetragonBitReader reader;
  uint32_t a2;
  if (out_consumed_offset != NULL) *out_consumed_offset = 0U;
  if (decode_section == NULL || event == NULL || decode_section->data == NULL || memory == NULL ||
      event->compressed_source_section_end_offset > decode_section->size ||
      event->compressed_source_section_offset > event->compressed_source_section_end_offset ||
      event->compressed_source_section_end_offset < event->compressed_source_section_offset + 8U) {
    return 0;
  }
  memset(&reader, 0, sizeof(reader));
  reader.data = decode_section->data;
  reader.start_offset = event->compressed_source_section_offset;
  reader.cursor_offset = event->compressed_source_section_end_offset - 4U;
  a2 = read_be32_local(decode_section->data + reader.cursor_offset);
  if (a2 == 0U || a2 != event->postpass_source_end_address - event->postpass_source_start_address) {
    return 0;
  }
  a2 += event->postpass_source_start_address;
  if (a2 < event->postpass_source_start_address || (size_t)a2 > memory_size) return 0;
  if (reader.cursor_offset < event->compressed_source_section_offset + 4U) return 0;
  reader.cursor_offset -= 4U;
  reader.d0 = read_be32_local(decode_section->data + reader.cursor_offset);
  while (a2 > event->postpass_source_start_address) {
    uint8_t bit;
    uint32_t d1, d2, d3, d4, index;
    if (!tetragon_bit_reader_next_local(&reader, &bit)) return 0;
    if (bit) {
      d1 = 2U;
      if (!tetragon_bit_reader_bits_local(&reader, d1, &d2)) return 0;
      if (d2 < 2U) {
        d1 = 9U + d2;
        d3 = d2 + 2U;
      } else if (d2 == 3U) {
        d1 = 7U;
        d4 = 8U;
        if (!tetragon_bit_reader_bits_local(&reader, d1, &d2)) return 0;
        d3 = d2 + d4;
        for (index = 0U; index <= d3; ++index) {
          if (!tetragon_bit_reader_bits_local(&reader, 8U, &d2) || a2 == 0U) return 0;
          --a2;
          if (!tetragon_write_byte_local(memory, memory_size, a2, (uint8_t)(d2 & 0xFFU))) return 0;
        }
        continue;
      } else {
        d1 = long_reference_bit_count;
        if (!tetragon_bit_reader_bits_local(&reader, 8U, &d2)) return 0;
        d3 = d2 + 4U;
      }
      if (!tetragon_bit_reader_bits_local(&reader, d1, &d2)) return 0;
      for (index = 0U; index <= d3; ++index) {
        uint8_t value;
        uint32_t source = a2 + d2 - 1U;
        if (!tetragon_read_byte_local(memory, memory_size, source, &value) || a2 == 0U) return 0;
        --a2;
        if (!tetragon_write_byte_local(memory, memory_size, a2, value)) return 0;
      }
      continue;
    }
    d1 = 8U;
    d3 = 1U;
    if (!tetragon_bit_reader_next_local(&reader, &bit)) return 0;
    if (bit) {
      if (!tetragon_bit_reader_bits_local(&reader, d1, &d2)) return 0;
      for (index = 0U; index <= d3; ++index) {
        uint8_t value;
        uint32_t source = a2 + d2 - 1U;
        if (!tetragon_read_byte_local(memory, memory_size, source, &value) || a2 == 0U) return 0;
        --a2;
        if (!tetragon_write_byte_local(memory, memory_size, a2, value)) return 0;
      }
      continue;
    }
    d1 = 3U;
    d4 = 0U;
    if (!tetragon_bit_reader_bits_local(&reader, d1, &d2)) return 0;
    d3 = d2 + d4;
    for (index = 0U; index <= d3; ++index) {
      if (!tetragon_bit_reader_bits_local(&reader, 8U, &d2) || a2 == 0U) return 0;
      --a2;
      if (!tetragon_write_byte_local(memory, memory_size, a2, (uint8_t)(d2 & 0xFFU))) return 0;
    }
  }
  if (a2 > event->postpass_source_start_address || reader.failed) return 0;
  if (out_consumed_offset != NULL) *out_consumed_offset = reader.cursor_offset;
  return 1;
}

static int recognized_tetragon_unpack_postpass_local(const PlatformRecognizedUnpackerEvent *event,
    uint8_t *memory, size_t memory_size, uint32_t *out_target_end, uint32_t *out_source_consumed) {
  uint32_t source;
  uint32_t target;
  if (out_target_end != NULL) *out_target_end = 0U;
  if (out_source_consumed != NULL) *out_source_consumed = 0U;
  if (event == NULL || memory == NULL ||
      event->postpass_source_start_address > event->postpass_source_end_address) {
    return 0;
  }
  source = event->postpass_source_start_address;
  target = event->target_start_address;
  while (source < event->postpass_source_end_address) {
    uint8_t value;
    if (!tetragon_read_byte_local(memory, memory_size, source++, &value)) return 0;
    if (value == event->postpass_escape_byte) {
      uint8_t count;
      if (source >= event->postpass_source_end_address ||
          !tetragon_read_byte_local(memory, memory_size, source++, &count)) {
        return 0;
      }
      if (count != 0U) {
        uint32_t index;
        if (source >= event->postpass_source_end_address ||
            !tetragon_read_byte_local(memory, memory_size, source++, &value)) {
          return 0;
        }
        for (index = 0U; index < (uint32_t)count + 2U; ++index) {
          if (!tetragon_write_byte_local(memory, memory_size, target++, value)) return 0;
        }
      }
    }
    if (!tetragon_write_byte_local(memory, memory_size, target++, value)) return 0;
  }
  if (out_target_end != NULL) *out_target_end = target;
  if (out_source_consumed != NULL) *out_source_consumed = source;
  return 1;
}

static int validate_decompressed_entrypoint_bytes_local(const uint8_t *data, uint32_t size,
    uint32_t load_address, uint32_t entrypoint, uint32_t *out_accepted_instructions,
    uint32_t *out_unsupported_instruction_demotes, uint32_t *out_required_instruction_failures,
    uint32_t *out_code_start_control_targets, uint8_t *out_valid) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult add_result;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  uint32_t entry_offset;
  int ok = 0;
  if (out_accepted_instructions != NULL) *out_accepted_instructions = 0U;
  if (out_unsupported_instruction_demotes != NULL) *out_unsupported_instruction_demotes = 0U;
  if (out_required_instruction_failures != NULL) *out_required_instruction_failures = 0U;
  if (out_code_start_control_targets != NULL) *out_code_start_control_targets = 0U;
  if (out_valid != NULL) *out_valid = 0U;
  if (data == NULL || size == 0U || entrypoint < load_address) {
    return 0;
  }
  entry_offset = entrypoint - load_address;
  if (entry_offset >= size) return 0;
  memset(&object, 0, sizeof(object));
  memset(&section, 0, sizeof(section));
  memset(&profile, 0, sizeof(profile));
  if (m68k_object_create(&object) != 0) return 0;
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.name = "decompressed_payload";
  section.kind = M68K_SECTION_CODE;
  section.size = size;
  section.data = (uint8_t *)data;
  section.data_size = size;
  add_result = m68k_object_add_section(&object, &section);
  if (!add_result.ok) goto cleanup;
  m68k_object_mark_no_container(&object);
  m68k_analysis_policy_init_default(&policy);
  policy.disable_implicit_entry_points = 1U;
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = size;
  policy.runtime_ranges[0].runtime_address = load_address;
  policy.runtime_entry_point_count = 1U;
  policy.runtime_entry_points[0].has_section_index = 1U;
  policy.runtime_entry_points[0].section_index = 0U;
  policy.runtime_entry_points[0].runtime_address = entrypoint;
  if (m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)) != 0)
    goto cleanup;
  if (out_accepted_instructions != NULL) *out_accepted_instructions = profile.accepted_instructions;
  if (out_unsupported_instruction_demotes != NULL)
    *out_unsupported_instruction_demotes = profile.unsupported_instruction_demotes;
  if (out_required_instruction_failures != NULL)
    *out_required_instruction_failures = profile.required_instruction_failures;
  if (out_code_start_control_targets != NULL) *out_code_start_control_targets = profile.code_start_control_targets;
  if (out_valid != NULL) {
    *out_valid = (uint8_t)(profile.accepted_instructions != 0U &&
      profile.required_instruction_failures == 0U);
  }
  ok = 1;

cleanup:
  m68k_object_destroy(&object);
  return ok;
}

static int recognized_unpacker_validate_entrypoint_local(PlatformRecognizedUnpackerEvent *event,
    const uint8_t *data) {
  if (event == NULL || data == NULL || event->decompressed_size == 0U ||
      event->entrypoint < event->target_start_address) {
    return 0;
  }
  event->entry_validation_attempted = 1U;
  event->entry_validation_valid = 0U;
  return validate_decompressed_entrypoint_bytes_local(data, event->decompressed_size,
    event->target_start_address, event->entrypoint,
    &event->entry_validation_accepted_instructions,
    &event->entry_validation_unsupported_instruction_demotes,
    &event->entry_validation_required_instruction_failures,
    &event->entry_validation_code_start_control_targets,
    &event->entry_validation_valid);
}

static int platform_section_runtime_base_local(const M68kObject *object, const M68kSourceAnalysisIR *analysis,
    uint32_t section_index, uint32_t *out_runtime_base) {
  uint16_t range_index;
  size_t index;
  uint32_t runtime_base = 0U;
  if (out_runtime_base != NULL) *out_runtime_base = 0U;
  if (analysis == NULL || out_runtime_base == NULL) return 0;
  for (range_index = 0U; range_index < analysis->policy.runtime_range_count &&
      range_index < M68K_ANALYSIS_RUNTIME_RANGE_LIMIT; ++range_index) {
    const M68kAnalysisRuntimeRange *range = &analysis->policy.runtime_ranges[range_index];
    if (!range->has_section_index || range->section_index != section_index ||
        range->offset != 0U || range->size == 0U) {
      continue;
    }
    *out_runtime_base = range->runtime_address;
    return 1;
  }
  if (object == NULL || section_index >= object->section_count ||
      object->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE ||
      (object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK &&
       object->platform_backend_kind != M68K_PLATFORM_BACKEND_ATARI_ST)) {
    return 0;
  }
  for (index = 0U; index < section_index; ++index) {
    if (runtime_base > UINT32_MAX - object->sections[index].size) return 0;
    runtime_base += object->sections[index].size;
  }
  *out_runtime_base = runtime_base;
  return 1;
}

static int recognized_tetragon_try_unpack_event_local(Arena *arena, const M68kDecodeSectionIR *decode_section,
    PlatformRecognizedUnpackerEvent *event, const char *output_path, M68kDiagList *diagnostics) {
  ArenaMark mark;
  uint8_t *memory;
  uint32_t compressed_consumed;
  uint32_t postpass_consumed;
  uint32_t target_end;
  if (arena == NULL || decode_section == NULL || event == NULL) return 0;
  mark = arena_mark(arena);
  memory = (uint8_t *)arena_calloc(arena, PLATFORM_SELF_DECRUNCH_MEMORY_LIMIT, 1U);
  if (memory == NULL) {
    arena_rewind(arena, mark);
    return 0;
  }
  if (event->lz_long_reference_bit_count != 0U) {
    if (!recognized_tetragon_unpack_lz_stage_local(decode_section, event, memory,
        PLATFORM_SELF_DECRUNCH_MEMORY_LIMIT, event->lz_long_reference_bit_count, &compressed_consumed)) {
      arena_rewind(arena, mark);
      return 0;
    }
  } else if (!recognized_tetragon_unpack_lz_stage_local(decode_section, event, memory,
      PLATFORM_SELF_DECRUNCH_MEMORY_LIMIT, 11U, &compressed_consumed)) {
    memset(memory, 0, PLATFORM_SELF_DECRUNCH_MEMORY_LIMIT);
    if (!recognized_tetragon_unpack_lz_stage_local(decode_section, event, memory,
        PLATFORM_SELF_DECRUNCH_MEMORY_LIMIT, 8U, &compressed_consumed)) {
      arena_rewind(arena, mark);
      return 0;
    }
  }
  if (
      !recognized_tetragon_unpack_postpass_local(event, memory, PLATFORM_SELF_DECRUNCH_MEMORY_LIMIT,
        &target_end, &postpass_consumed) ||
      target_end <= event->target_start_address || event->entrypoint < event->target_start_address ||
      event->entrypoint >= target_end) {
    arena_rewind(arena, mark);
    return 0;
  }
  event->compressed_source_consumed_section_offset = compressed_consumed;
  event->postpass_source_consumed_address = postpass_consumed;
  event->target_end_address = target_end;
  event->decompressed_size = target_end - event->target_start_address;
  (void)m68k_platform_sha256_hex(memory + event->target_start_address, event->decompressed_size,
    event->decompressed_sha256);
  if (!recognized_unpacker_validate_entrypoint_local(event, memory + event->target_start_address) ||
      !event->entry_validation_valid) {
    arena_rewind(arena, mark);
    return 1;
  }
  if (output_path != NULL && output_path[0] != '\0' &&
      write_bytes_to_path_local(output_path, memory + event->target_start_address,
        event->decompressed_size, diagnostics) != 0) {
    arena_rewind(arena, mark);
    return 0;
  }
  event->native_unpack_validated = 1U;
  arena_rewind(arena, mark);
  return 1;
}

static int recognized_unpacker_try_native_copied_stub_local(const M68kObject *object,
    const M68kSourceAnalysisIR *analysis, const M68kDecodeSectionIR *decode_section,
    const M68kSectionAnalysisIR *section_analysis, PlatformRecognizedUnpackerEvent *event,
    const char *output_path, M68kDiagList *diagnostics, Arena *scratch_arena) {
  ArenaMark mark;
  uint8_t *memory = NULL;
  size_t memory_size, range_index, view_index;
  uint32_t copy_size;
  uint32_t output_start;
  uint32_t output_end;
  uint32_t entry_root;
  uint32_t source_runtime_base = 0U;
  uint32_t execution_start_pc;
  size_t step_limit;
  M68kSimConcreteState state;
  M68kSimConcreteMemoryPolicy memory_policy;
  M68kSimConcreteRunTraceResult result;
  int ok = 0;
  if (object == NULL || analysis == NULL || decode_section == NULL || section_analysis == NULL ||
      event == NULL || scratch_arena == NULL || decode_section->data == NULL ||
      event->source_section_index >= object->section_count || !event->has_copied_stub ||
      !event->has_copied_stub_transfer || event->copied_stub_storage_offset >= event->compressed_source_section_offset ||
      event->entrypoint > UINT32_MAX - 16U || event->target_end_address <= event->target_start_address ||
      event->entrypoint < event->target_start_address || event->entrypoint >= event->target_end_address) {
    return 0;
  }
  output_start = event->target_start_address;
  output_end = event->target_end_address;
  copy_size = event->compressed_source_section_offset - event->copied_stub_storage_offset;
  if (copy_size == 0U || event->copied_stub_runtime_address > UINT32_MAX - copy_size) return 0;
  (void)platform_section_runtime_base_local(object, analysis, event->source_section_index, &source_runtime_base);
  memory_size = source_runtime_base > UINT32_MAX - decode_section->size ?
    decode_section->size : (size_t)source_runtime_base + decode_section->size;
  if ((size_t)event->entrypoint + 16U > memory_size) memory_size = (size_t)event->entrypoint + 16U;
  if ((size_t)event->postpass_source_end_address + 16U > memory_size)
    memory_size = (size_t)event->postpass_source_end_address + 16U;
  if ((size_t)event->copied_stub_runtime_address + copy_size > memory_size) {
    memory_size = (size_t)event->copied_stub_runtime_address + copy_size;
  }
  for (range_index = 0U; range_index < analysis->policy.runtime_range_count &&
      range_index < M68K_ANALYSIS_RUNTIME_RANGE_LIMIT; ++range_index) {
    const M68kAnalysisRuntimeRange *range = &analysis->policy.runtime_ranges[range_index];
    size_t range_end;
    if (!range->has_section_index || range->size == 0U || range->runtime_address > UINT32_MAX - range->size)
      continue;
    range_end = (size_t)range->runtime_address + range->size;
    if (range_end > memory_size) memory_size = range_end;
  }
  for (view_index = 0U; view_index < section_analysis->runtime_view_count; ++view_index) {
    const M68kRuntimeViewIR *view = &section_analysis->runtime_views[view_index];
    size_t view_end;
    if (!view->materialized || view->size == 0U || view->runtime_address > UINT32_MAX - view->size)
      continue;
    if (view->runtime_address > UINT32_MAX - view->size) continue;
    view_end = (size_t)view->runtime_address + view->size;
    if (view_end > memory_size) memory_size = view_end;
  }
  if (memory_size > PLATFORM_SELF_DECRUNCH_MEMORY_LIMIT) return 0;
  mark = arena_mark(scratch_arena);
  memory = (uint8_t *)arena_calloc(scratch_arena, memory_size, 1U);
  if (memory == NULL) goto cleanup;
  if ((size_t)source_runtime_base + decode_section->size > memory_size) goto cleanup;
  memcpy(memory + source_runtime_base, decode_section->data, decode_section->size);
  for (range_index = 0U; range_index < analysis->policy.runtime_range_count &&
      range_index < M68K_ANALYSIS_RUNTIME_RANGE_LIMIT; ++range_index) {
    const M68kAnalysisRuntimeRange *range = &analysis->policy.runtime_ranges[range_index];
    const M68kSection *source_section;
    if (!range->has_section_index || range->section_index >= object->section_count || range->size == 0U ||
        range->runtime_address > UINT32_MAX - range->size) {
      continue;
    }
    source_section = &object->sections[range->section_index];
    if (source_section->data == NULL || range->offset > source_section->data_size ||
        range->size > source_section->data_size - range->offset ||
        (size_t)range->runtime_address + range->size > memory_size) {
      continue;
    }
    memcpy(memory + range->runtime_address, source_section->data + range->offset, range->size);
  }
  for (view_index = 0U; view_index < section_analysis->runtime_view_count; ++view_index) {
    const M68kRuntimeViewIR *view = &section_analysis->runtime_views[view_index];
    if (!view->materialized || view->size == 0U || view->runtime_address > UINT32_MAX - view->size ||
        view->storage_offset > decode_section->size || view->size > decode_section->size - view->storage_offset ||
        view->runtime_address > UINT32_MAX - view->size) {
      continue;
    }
    if (view->storage_offset == event->copied_stub_storage_offset &&
        view->runtime_address == event->copied_stub_runtime_address) {
      continue;
    }
    if ((size_t)view->runtime_address + view->size > memory_size) continue;
    memcpy(memory + view->runtime_address, decode_section->data + view->storage_offset, view->size);
  }
  memset(&state, 0, sizeof(state));
  memset(&memory_policy, 0, sizeof(memory_policy));
  memset(&result, 0, sizeof(result));
  memory_policy.external_write_allowed = platform_self_decrunch_external_write_allowed_local;
  memory_policy.external_read = platform_self_decrunch_external_read_local;
  memory_policy.user = (void *)object;
  entry_root = reachable_decrunch_entry_root_local(section_analysis, event->source_section_index,
    0U, event->copied_stub_transfer_site_offset, scratch_arena);
  if (source_runtime_base > UINT32_MAX - entry_root) goto cleanup;
  execution_start_pc = source_runtime_base + entry_root;
  event->native_execution_start_pc = execution_start_pc;
  state.pc = execution_start_pc;
  state.a[7] = (uint32_t)memory_size;
  step_limit = platform_self_decrunch_step_limit_for_output_local(event->decompressed_size);
  if (m68k_simulate_run_concrete(platform_self_decrunch_execution_cpu_local(object, analysis),
      memory, memory_size, &state,
      step_limit, event->entrypoint, event->entrypoint + 16U,
      &memory_policy, &result) != 0) {
    if (diagnostics != NULL && !m68k_diag_has_errors(diagnostics))
      platform_file_add_error(diagnostics, "native recognized unpacker simulation failed");
    goto cleanup;
  }
  event->native_execution_attempted = 1U;
  event->native_execution_step_count = result.step_count > UINT32_MAX ? UINT32_MAX : (uint32_t)result.step_count;
  event->native_execution_stop_reason = (uint8_t)result.stop_reason;
  if (result.stop_reason != M68K_SIM_CONCRETE_RUN_STOP_PC_RANGE || result.memory_write_range_overflow ||
      result.memory_write_range_count == 0U) {
    if (diagnostics != NULL && !m68k_diag_has_errors(diagnostics)) {
      char message[160];
      const char *detail = m68k_diag_first_message(&result.diagnostics);
      if (detail != NULL && detail[0] != '\0') {
        uint32_t pc = result.stop_pc;
        if (pc <= memory_size - 4U) {
          snprintf(message, sizeof(message), "native recognized unpacker stopped at %s pc=$%08X a7=$%08X bytes=%02X%02X%02X%02X: %s",
            self_decrunch_sim_stop_reason_name_local((uint8_t)result.stop_reason), (unsigned)pc,
            (unsigned)state.a[7],
            (unsigned)memory[pc], (unsigned)memory[pc + 1U], (unsigned)memory[pc + 2U],
            (unsigned)memory[pc + 3U], detail);
        } else {
          snprintf(message, sizeof(message), "native recognized unpacker stopped at %s pc=$%08X a7=$%08X: %s",
            self_decrunch_sim_stop_reason_name_local((uint8_t)result.stop_reason), (unsigned)result.stop_pc,
            (unsigned)state.a[7], detail);
        }
      } else {
        snprintf(message, sizeof(message), "native recognized unpacker stopped at %s pc=$%08X a7=$%08X",
          self_decrunch_sim_stop_reason_name_local((uint8_t)result.stop_reason), (unsigned)result.stop_pc,
          (unsigned)state.a[7]);
      }
      platform_file_add_error(diagnostics, message);
    }
    goto cleanup;
  }
  if ((size_t)output_end > memory_size ||
      !concrete_write_ranges_cover_span_local(&result, output_start, output_end - output_start)) {
    if (diagnostics != NULL && !m68k_diag_has_errors(diagnostics))
      platform_file_add_error(diagnostics, "native recognized unpacker writes do not cover modeled output span");
    goto cleanup;
  }
  event->postpass_source_consumed_address = state.a[1];
  (void)m68k_platform_sha256_hex(memory + output_start, event->decompressed_size,
    event->decompressed_sha256);
  event->entry_validation_attempted = 1U;
  event->entry_validation_valid = 0U;
  if (!validate_decompressed_entrypoint_bytes_local(memory + output_start, event->decompressed_size,
      output_start, event->entrypoint,
      &event->entry_validation_accepted_instructions,
      &event->entry_validation_unsupported_instruction_demotes,
      &event->entry_validation_required_instruction_failures,
      &event->entry_validation_code_start_control_targets,
      &event->entry_validation_valid) || !event->entry_validation_valid) {
    goto cleanup;
  }
  if (output_path != NULL && output_path[0] != '\0' &&
      write_bytes_to_path_local(output_path, memory + output_start, event->decompressed_size,
        diagnostics) != 0) {
    goto cleanup;
  }
  event->native_unpack_validated = 1U;
  ok = 1;

cleanup:
  arena_rewind(scratch_arena, mark);
  return ok;
}

static void recognized_unpacker_attach_copied_stub_local(const M68kSectionAnalysisIR *section_analysis,
    uint32_t marker_end, uint32_t code_end, PlatformRecognizedUnpackerEvent *event) {
  size_t view_index;
  size_t site_index;
  if (section_analysis == NULL || event == NULL) return;
  for (view_index = 0U; view_index < section_analysis->runtime_view_count; ++view_index) {
    const M68kRuntimeViewIR *view = &section_analysis->runtime_views[view_index];
    uint32_t view_end;
    if (view->storage_offset < marker_end || view->storage_offset >= code_end) continue;
    if (view->size > UINT32_MAX - view->storage_offset) continue;
    view_end = view->storage_offset + view->size;
    if (view_end < code_end) continue;
    event->has_copied_stub = 1U;
    event->copied_stub_storage_offset = view->storage_offset;
    event->copied_stub_runtime_address = view->runtime_address;
    break;
  }
  if (!event->has_copied_stub) return;
  for (site_index = 0U; site_index < section_analysis->recovered_indirect_site_count; ++site_index) {
    const M68kRecoveredIndirectSiteIR *site = &section_analysis->recovered_indirect_sites[site_index];
    uint32_t view_end;
    if (!site->has_target) continue;
    if (code_end < event->copied_stub_storage_offset) continue;
    view_end = event->copied_stub_storage_offset + (code_end - event->copied_stub_storage_offset);
    if (site->target < event->copied_stub_storage_offset || site->target >= view_end) continue;
    event->copied_stub_transfer_offset = site->target - event->copied_stub_storage_offset;
    event->copied_stub_transfer_site_offset = site->offset;
    event->has_copied_stub_transfer = 1U;
    break;
  }
}

static int collect_recognized_tetragon_events_for_section_local(const M68kObject *object,
    const M68kSourceAnalysisIR *analysis, const M68kDecodeSectionIR *decode_section,
    const M68kSectionAnalysisIR *section_analysis, Arena *arena, PlatformRecognizedUnpackerEvent *events,
    size_t event_capacity, size_t *io_event_count, const char *materialize_event_id,
    const char *materialize_output_path, PlatformRecognizedUnpackerEvent *out_materialized_event,
    M68kDiagList *materialize_diagnostics) {
  static const unsigned char marker[] = " TETRAGON ";
  uint32_t offset;
  if (object == NULL || analysis == NULL || decode_section == NULL || section_analysis == NULL ||
      events == NULL || io_event_count == NULL || decode_section->data == NULL ||
      decode_section->size < sizeof(marker) - 1U) {
    return 0;
  }
  for (offset = 0U; offset + (uint32_t)(sizeof(marker) - 1U) <= decode_section->size &&
      *io_event_count < event_capacity; ++offset) {
    PlatformRecognizedUnpackerEvent event;
    uint32_t marker_end;
    uint32_t code_end;
    uint32_t target_start_address;
    uint32_t postpass_source_start_address;
    uint32_t source_end_address;
    uint32_t entrypoint;
    uint8_t escape_byte;
    if (memcmp(decode_section->data + offset, marker, sizeof(marker) - 1U) != 0) continue;
    marker_end = offset + (uint32_t)(sizeof(marker) - 1U);
    code_end = recognized_unpacker_code_end_after_marker_local(section_analysis, marker_end);
    if (code_end <= marker_end || code_end >= decode_section->size) continue;
    recognized_unpacker_bounds_from_code_window_local(decode_section, marker_end, code_end,
      &target_start_address, &source_end_address, &entrypoint);
    if (target_start_address == 0U || source_end_address == 0U || entrypoint == 0U) continue;
    postpass_source_start_address = recognized_unpacker_postpass_source_start_local(decode_section, section_analysis,
      target_start_address, source_end_address, entrypoint);
    if (postpass_source_start_address == 0U ||
        !recognized_unpacker_postpass_escape_byte_local(decode_section, marker_end, &escape_byte)) {
      continue;
    }
    memset(&event, 0, sizeof(event));
    event.source_section_index = (uint32_t)decode_section->section_index;
    event.marker_offset = offset;
    event.compressed_source_section_offset = code_end;
    event.compressed_source_section_end_offset = decode_section->size;
    event.postpass_source_start_address = postpass_source_start_address;
    event.postpass_source_end_address = source_end_address;
    event.target_start_address = target_start_address;
    event.entrypoint = entrypoint;
    event.postpass_escape_byte = escape_byte;
    event.lz_long_reference_bit_count = recognized_tetragon_long_reference_bit_count_local(decode_section,
      marker_end, code_end);
    snprintf(event.codec_id, sizeof(event.codec_id), "tetragon");
    snprintf(event.codec_name, sizeof(event.codec_name), "Tetragon target-owned unpacker");
    snprintf(event.provider_id, sizeof(event.provider_id), "c-tetragon-signature");
    recognized_unpacker_attach_copied_stub_local(section_analysis, marker_end, code_end, &event);
    {
      char event_id[160];
      int materialize_this_event;
      make_recognized_unpacker_event_id_local(event_id, sizeof(event_id), &event);
      materialize_this_event = materialize_event_id != NULL && strcmp(event_id, materialize_event_id) == 0;
      (void)recognized_tetragon_try_unpack_event_local(arena, decode_section, &event, NULL,
        materialize_this_event ? materialize_diagnostics : NULL);
      if (event.has_copied_stub_transfer) {
        if (materialize_this_event) {
          (void)recognized_unpacker_try_native_copied_stub_local(object, analysis, decode_section,
            section_analysis, &event, materialize_output_path, materialize_diagnostics, arena);
        } else if (event.target_end_address > event.target_start_address &&
            event.entrypoint >= event.target_start_address && event.entrypoint < event.target_end_address) {
          event.native_unpack_validated = 0U;
          event.native_execution_deferred = 1U;
          event.native_execution_attempted = 0U;
          event.entry_validation_attempted = 0U;
          event.entry_validation_valid = 0U;
          event.entry_validation_accepted_instructions = 0U;
          event.entry_validation_unsupported_instruction_demotes = 0U;
          event.entry_validation_required_instruction_failures = 0U;
          event.entry_validation_code_start_control_targets = 0U;
          event.decompressed_sha256[0] = '\0';
        }
      } else if (materialize_this_event && event.native_unpack_validated) {
        (void)recognized_tetragon_try_unpack_event_local(arena, decode_section, &event,
          materialize_output_path, materialize_diagnostics);
      }
      if (materialize_this_event && out_materialized_event != NULL) *out_materialized_event = event;
    }
    if (!recognized_unpacker_event_duplicate_local(events, *io_event_count, &event)) {
      events[*io_event_count] = event;
      *io_event_count += 1U;
    }
  }
  return 0;
}

static int collect_recognized_unpacker_events_local(const M68kObject *object,
    const M68kSourceAnalysisIR *analysis, PlatformRecognizedUnpackerEvent *events, size_t event_capacity,
    size_t *out_event_count, const char *materialize_event_id, const char *materialize_output_path,
    PlatformRecognizedUnpackerEvent *out_materialized_event, M68kDiagList *materialize_diagnostics,
    Arena *scratch_arena) {
  M68kDecodeIR decode;
  size_t section_index;
  int result = 0;
  if (object == NULL || analysis == NULL || events == NULL || out_event_count == NULL || scratch_arena == NULL)
    return -1;
  *out_event_count = 0U;
  m68k_decode_ir_init(&decode);
  if (m68k_decode_ir_build_object(&decode, object, analysis->policy.max_cpu, m68k_diag_sink(NULL)) != 0) {
    return -1;
  }
  for (section_index = 0U; section_index < decode.section_count && *out_event_count < event_capacity;
      ++section_index) {
    if (section_index >= analysis->section_count) break;
    if (collect_recognized_tetragon_events_for_section_local(object, analysis, &decode.sections[section_index],
        &analysis->sections[section_index], scratch_arena, events, event_capacity, out_event_count,
        materialize_event_id, materialize_output_path, out_materialized_event,
        materialize_diagnostics) != 0) {
      result = -1;
      break;
    }
  }
  m68k_decode_ir_destroy(&decode);
  return result;
}

static int self_decrunch_event_matches_materialized_provider_local(const PlatformDecompressionIdentifyResult *results,
    size_t result_count,
    const PlatformSelfDecrunchEvent *event) {
  size_t index;
  if (results == NULL || event == NULL) return 0;
  for (index = 0U; index < result_count; ++index) {
    const PlatformDecompressionIdentifyResult *result = &results[index];
    if (!result->found || !result->has_decompressed_load_entry) continue;
    if (result->decompressed_load_address == event->load_address &&
        result->decompressed_entrypoint == event->entrypoint) {
      return 1;
    }
  }
  return 0;
}

static int self_decrunch_event_matches_native_recognized_unpacker_local(
    const PlatformRecognizedUnpackerEvent *events, size_t event_count,
    const PlatformSelfDecrunchEvent *event) {
  size_t index;
  if (events == NULL || event == NULL) return 0;
  for (index = 0U; index < event_count; ++index) {
    const PlatformRecognizedUnpackerEvent *recognized = &events[index];
    if (!recognized->native_unpack_validated && !recognized->native_execution_deferred) continue;
    if (recognized->source_section_index == event->source_section_index &&
        recognized->target_start_address == event->load_address &&
        recognized->entrypoint == event->entrypoint) {
      return 1;
    }
  }
  return 0;
}

static uint32_t candidate_write_width_local(const M68kDecodeCandidate *candidate) {
  if (candidate == NULL) return 0U;
  if (candidate->size_suffix == 'b') return 1U;
  if (candidate->size_suffix == 'w') return 2U;
  if (candidate->size_suffix == 'l') return 4U;
  return 0U;
}

static int instruction_operand_address_register_local(const M68kOperandIR *operand, uint8_t *out_reg) {
  uint8_t is_address = 0U, reg = 0U;
  if (out_reg != NULL) *out_reg = 0U;
  if (operand == NULL || !m68k_instruction_operand_direct_register(operand, &is_address, &reg) ||
      !is_address || reg >= 8U) {
    return 0;
  }
  if (out_reg != NULL) *out_reg = reg;
  return 1;
}

static int runtime_address_from_operand_local(const M68kOperandIR *operand, uint32_t a_known,
    const uint32_t a_values[8], uint32_t *out_address) {
  uint8_t shape, reg;
  int64_t address;
  if (out_address != NULL) *out_address = 0U;
  if (operand == NULL || a_values == NULL || out_address == NULL) return 0;
  shape = m68k_instruction_operand_decoded_ea_shape(operand);
  if (m68k_instruction_decoded_ea_target_kind(operand, shape, 0) == 1U) {
    *out_address = operand->value.value;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_IND || operand->kind == M68K_ASM_OPERAND_POSTINC ||
      operand->kind == M68K_ASM_OPERAND_PREDEC) {
    reg = operand->value.reg;
    if (reg >= 8U || !m68k_bitset_u32_has(a_known, reg)) return 0;
    *out_address = a_values[reg];
    return 1;
  }
  if (operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_reg >= 8U) return 0;
  reg = operand->value.ea_reg;
  if (!m68k_bitset_u32_has(a_known, reg)) return 0;
  address = (int64_t)(uint64_t)a_values[reg];
  if (shape == M68K_SIM_EA_SHAPE_DISPLACEMENT || shape == M68K_SIM_EA_SHAPE_INDEX) {
    address += (int64_t)(int16_t)(operand->value.value & 0xFFFFU);
  } else if (shape != M68K_SIM_EA_SHAPE_INDIRECT && shape != M68K_SIM_EA_SHAPE_POSTINCREMENT &&
      shape != M68K_SIM_EA_SHAPE_PREDECREMENT) {
    return 0;
  }
  if (address < 0 || address > (int64_t)(uint64_t)UINT32_MAX) return 0;
  *out_address = (uint32_t)address;
  return 1;
}

static void trace_runtime_writes_from_candidate_local(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata, uint32_t *a_known,
    uint32_t a_values[8], PlatformRuntimeWriteObservation *writes, size_t write_capacity,
    size_t *io_write_count) {
  uint32_t invalidated = 0U;
  size_t operand_index;
  if (candidate == NULL || instruction == NULL || metadata == NULL || a_known == NULL || a_values == NULL ||
      writes == NULL || io_write_count == NULL) {
    return;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t reg = 0U;
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE &&
        instruction_operand_address_register_local(&instruction->operands[operand_index], &reg)) {
      m68k_bitset_u32_set(&invalidated, reg);
    }
  }
  if (metadata->operation_class == M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS &&
      metadata->source_operand_index < instruction->operand_count &&
      metadata->dest_operand_index < instruction->operand_count) {
    uint8_t reg = 0U;
    uint32_t address = 0U;
    if (instruction_operand_address_register_local(&instruction->operands[metadata->dest_operand_index], &reg) &&
        runtime_address_from_operand_local(&instruction->operands[metadata->source_operand_index], *a_known,
          a_values, &address)) {
      m68k_bitset_u32_set(a_known, reg);
      a_values[reg] = address;
      m68k_bitset_u32_clear(&invalidated, reg);
    }
  }
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    uint32_t address = 0U;
    uint32_t width = candidate_write_width_local(candidate);
    uint8_t reg = 0U;
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_WRITE &&
        width != 0U && runtime_address_from_operand_local(&instruction->operands[operand_index], *a_known,
          a_values, &address) &&
        address <= UINT32_MAX - width && *io_write_count < write_capacity) {
      writes[*io_write_count].start = address;
      writes[*io_write_count].end = address + width;
      *io_write_count += 1U;
    }
    {
      uint8_t update = metadata->operand_ea_register_updates[operand_index];
      uint8_t shape = m68k_instruction_operand_decoded_ea_shape(&instruction->operands[operand_index]);
      if (update == M68K_SIM_EA_UPDATE_NONE &&
          (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_READ ||
           metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_WRITE)) {
        if (shape == M68K_SIM_EA_SHAPE_POSTINCREMENT) update = M68K_SIM_EA_UPDATE_POSTINCREMENT;
        else if (shape == M68K_SIM_EA_SHAPE_PREDECREMENT) update = M68K_SIM_EA_UPDATE_PREDECREMENT;
      }
      if (update != M68K_SIM_EA_UPDATE_NONE &&
        ((instruction->operands[operand_index].kind == M68K_ASM_OPERAND_EA &&
          instruction->operands[operand_index].value.ea_reg < 8U) ||
         instruction->operands[operand_index].kind == M68K_ASM_OPERAND_POSTINC ||
         instruction->operands[operand_index].kind == M68K_ASM_OPERAND_PREDEC)) {
        reg = instruction->operands[operand_index].kind == M68K_ASM_OPERAND_EA ?
          instruction->operands[operand_index].value.ea_reg : instruction->operands[operand_index].value.reg;
        if (reg >= 8U) continue;
        if (m68k_bitset_u32_has(*a_known, reg) && width != 0U) {
          if (update == M68K_SIM_EA_UPDATE_POSTINCREMENT && a_values[reg] <= UINT32_MAX - width) {
            a_values[reg] += width;
          } else if (update == M68K_SIM_EA_UPDATE_PREDECREMENT && a_values[reg] >= width) {
            a_values[reg] -= width;
          } else {
            m68k_bitset_u32_clear(a_known, reg);
          }
        }
      }
    }
  }
  for (operand_index = 0U; operand_index < 8U; ++operand_index) {
    if (m68k_bitset_u32_has(invalidated, (uint8_t)operand_index))
      m68k_bitset_u32_clear(a_known, (uint8_t)operand_index);
  }
}

static int observed_writes_cover_target_local(const PlatformRuntimeWriteObservation *writes, size_t write_count,
    uint32_t target, uint32_t *out_start, uint32_t *out_end, uint32_t *out_count) {
  size_t index;
  uint32_t start = UINT32_MAX;
  uint32_t end = 0U;
  uint32_t count = 0U;
  if (out_start != NULL) *out_start = 0U;
  if (out_end != NULL) *out_end = 0U;
  if (out_count != NULL) *out_count = 0U;
  if (writes == NULL) return 0;
  for (index = 0U; index < write_count; ++index) {
    const PlatformRuntimeWriteObservation *write = &writes[index];
    if (write->start > target || write->end <= target || write->end <= write->start) continue;
    if (write->start < start) start = write->start;
    if (write->end > end) end = write->end;
    ++count;
  }
  if (count == 0U) return 0;
  for (index = 0U; index < write_count; ++index) {
    const PlatformRuntimeWriteObservation *write = &writes[index];
    if (write->end <= write->start) continue;
    if (write->start <= end && write->end >= start) {
      if (write->start < start) start = write->start;
      if (write->end > end) end = write->end;
    }
  }
  count = 0U;
  for (index = 0U; index < write_count; ++index) {
    const PlatformRuntimeWriteObservation *write = &writes[index];
    if (write->end <= write->start) continue;
    if (write->start < end && write->end > start) ++count;
  }
  if (out_start != NULL) *out_start = start;
  if (out_end != NULL) *out_end = end;
  if (out_count != NULL) *out_count = count;
  return 1;
}

static int block_index_containing_offset_local(const M68kSectionAnalysisIR *section, uint32_t offset,
    size_t *out_block_index) {
  size_t block_index;
  if (out_block_index != NULL) *out_block_index = 0U;
  if (section == NULL || out_block_index == NULL) return 0;
  for (block_index = 0U; block_index < section->block_count; ++block_index) {
    const M68kCfgBlockIR *block = &section->blocks[block_index];
    if (block->certainty == M68K_CODE_CERTAIN && offset >= block->start_offset && offset < block->end_offset) {
      *out_block_index = block_index;
      return 1;
    }
  }
  return 0;
}

static int cfg_block_reaches_local(const M68kSectionAnalysisIR *section, size_t source_block_index,
    size_t target_block_index, Arena *arena) {
  ArenaMark mark;
  uint8_t *visited;
  size_t *queue;
  size_t read_index = 0U, write_index = 0U;
  if (section == NULL || arena == NULL || source_block_index >= section->block_count ||
      target_block_index >= section->block_count) {
    return 0;
  }
  if (source_block_index == target_block_index) return 1;
  mark = arena_mark(arena);
  visited = (uint8_t *)arena_calloc(arena, section->block_count, 1U);
  queue = (size_t *)arena_alloc(arena, section->block_count * sizeof(*queue));
  if (visited == NULL || queue == NULL) {
    arena_rewind(arena, mark);
    return 0;
  }
  visited[source_block_index] = 1U;
  queue[write_index++] = source_block_index;
  while (read_index < write_index) {
    const M68kCfgBlockIR *block;
    size_t edge_cursor, edge_end;
    size_t current = queue[read_index++];
    if (current >= section->block_count) continue;
    block = &section->blocks[current];
    edge_end = block->edge_start + block->edge_count;
    if (edge_end > section->edge_count) edge_end = section->edge_count;
    for (edge_cursor = block->edge_start; edge_cursor < edge_end; ++edge_cursor) {
      const M68kCfgEdgeIR *edge = &section->edges[edge_cursor];
      size_t next = edge->target_block_index;
      if (next >= section->block_count || visited[next]) continue;
      if (next == target_block_index) {
        arena_rewind(arena, mark);
        return 1;
      }
      visited[next] = 1U;
      queue[write_index++] = next;
    }
  }
  arena_rewind(arena, mark);
  return 0;
}

static int code_start_ref_is_external_or_entry_root_local(const M68kCodeStartRefIR *ref, size_t section_index) {
  if (ref == NULL) return 0;
  if (ref->reason == M68K_FACT_CODE_START_REASON_SECTION_ENTRY ||
      ref->reason == M68K_FACT_CODE_START_REASON_POLICY_ENTRY_OFFSET ||
      ref->reason == M68K_FACT_CODE_START_REASON_POLICY_ENTRY_POINT) {
    return 1;
  }
  return ref->reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET &&
    ref->source_section_index != section_index;
}

static uint32_t reachable_decrunch_entry_root_local(const M68kSectionAnalysisIR *section, size_t section_index,
    uint32_t fallback_entry, uint32_t transfer_offset, Arena *arena) {
  size_t target_block_index, root_block_index, ref_index;
  uint32_t best = fallback_entry;
  if (section == NULL || arena == NULL ||
      !block_index_containing_offset_local(section, transfer_offset, &target_block_index)) {
    return fallback_entry;
  }
  if (section->certain_code_start != NULL && section->certain_code_size != 0U &&
      section->certain_code_start[0] &&
      block_index_containing_offset_local(section, 0U, &root_block_index) &&
      cfg_block_reaches_local(section, root_block_index, target_block_index, arena)) {
    best = 0U;
  }
  for (ref_index = 0U; ref_index < section->code_start_ref_count; ++ref_index) {
    const M68kCodeStartRefIR *ref = &section->code_start_refs[ref_index];
    if (!code_start_ref_is_external_or_entry_root_local(ref, section_index) || ref->offset >= best ||
        !block_index_containing_offset_local(section, ref->offset, &root_block_index) ||
        !cfg_block_reaches_local(section, root_block_index, target_block_index, arena)) {
      continue;
    }
    best = ref->offset;
  }
  return best;
}

static int platform_self_decrunch_external_write_allowed_local(void *user, uint32_t address, uint8_t width) {
  const M68kObject *object = (const M68kObject *)user;
  const AmigaOsHardwareRegisterRangeInfo *range;
  uint32_t range_start, range_end;
  if (object == NULL || object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK || width == 0U ||
      address > UINT32_MAX - width) {
    return 0;
  }
  if (amiga_os_find_hardware_register_by_cpu_address(address) != NULL ||
      amiga_os_find_hardware_register_field_by_cpu_address(address) != NULL) {
    return 1;
  }
  range = amiga_os_find_hardware_register_range_by_cpu_address(address);
  if (range == NULL || range->base_address > UINT32_MAX - range->offset ||
      range->base_address + range->offset > UINT32_MAX - range->size) {
    return 0;
  }
  range_start = range->base_address + range->offset;
  range_end = range_start + range->size;
  return address >= range_start && address + width <= range_end;
}

static int platform_self_decrunch_external_read_local(void *user, uint32_t address, uint8_t width,
    uint32_t *out_value) {
  if (out_value == NULL || !platform_self_decrunch_external_write_allowed_local(user, address, width)) return 0;
  *out_value = 0U;
  return 1;
}

static uint8_t platform_self_decrunch_execution_cpu_local(const M68kObject *object,
    const M68kSourceAnalysisIR *analysis) {
  if (object != NULL && object->platform_backend_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return M68K_ASM_CPU_68000;
  }
  return analysis != NULL ? analysis->policy.max_cpu : M68K_ASM_CPU_68000;
}

static void self_decrunch_grow_memory_for_runtime_address_local(size_t *io_memory_size, uint32_t address) {
  size_t end;
  if (io_memory_size == NULL || address > UINT32_MAX - PLATFORM_SELF_DECRUNCH_RUNTIME_LITERAL_SLOP) return;
  end = (size_t)address + PLATFORM_SELF_DECRUNCH_RUNTIME_LITERAL_SLOP;
  if (end > *io_memory_size && end <= PLATFORM_SELF_DECRUNCH_MEMORY_LIMIT) *io_memory_size = end;
}

static void self_decrunch_grow_memory_for_candidate_runtime_literals_local(const M68kDecodeSectionIR *section,
    const PlatformSelfDecrunchEvent *event, size_t *io_memory_size) {
  size_t candidate_index;
  if (section == NULL || event == NULL || io_memory_size == NULL) return;
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    size_t operand_index;
    for (operand_index = 0U; operand_index < candidate->operand_count &&
        operand_index < M68K_DECODE_IR_MAX_OPERANDS; ++operand_index) {
      const M68kAsmOperandValue *operand = &candidate->operands[operand_index];
      uint32_t address;
      if (operand->kind != M68K_ASM_OPERAND_ABSL &&
          !(operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 7U && operand->ea_reg == 1U)) {
        continue;
      }
      address = operand->value;
      if (address < event->entrypoint) continue;
      self_decrunch_grow_memory_for_runtime_address_local(io_memory_size, address);
    }
  }
}

static int concrete_write_ranges_cover_span_local(const M68kSimConcreteRunTraceResult *result,
    uint32_t start, uint32_t size) {
  uint32_t cursor, end;
  size_t range_index;
  if (result == NULL || size == 0U || start > UINT32_MAX - size ||
      result->memory_write_range_overflow) {
    return 0;
  }
  cursor = start;
  end = start + size;
  while (cursor < end) {
    uint32_t next = cursor;
    for (range_index = 0U; range_index < result->memory_write_range_count; ++range_index) {
      const M68kSimConcreteWriteRange *range = &result->memory_write_ranges[range_index];
      if (range->start <= cursor && range->end > next) next = range->end;
    }
    if (next == cursor) return 0;
    cursor = next < end ? next : end;
  }
  return 1;
}

static int simulate_provider_wrapper_candidate_local(const M68kObject *object,
    const M68kSourceAnalysisIR *analysis, const M68kSection *section, uint32_t entry_offset,
    uint32_t transfer_target, const char *output_path, const PlatformDecompressionIdentifyResult *result,
    Arena *scratch_arena) {
  ArenaMark mark;
  uint8_t *expected = NULL;
  size_t expected_size = 0U;
  uint8_t *memory = NULL;
  size_t memory_size, range_index;
  M68kSimConcreteState state;
  M68kSimConcreteMemoryPolicy memory_policy;
  M68kSimConcreteRunTraceResult run_result;
  size_t step_limit;
  int ok = 0;
  if (object == NULL || analysis == NULL || scratch_arena == NULL || section == NULL || section->data == NULL ||
      output_path == NULL || result == NULL || result->decompressed_size == 0U ||
      transfer_target > UINT32_MAX - result->decompressed_size) {
    return 0;
  }
  mark = arena_mark(scratch_arena);
  if (read_file_to_arena_local(scratch_arena, output_path, &expected, &expected_size) != 0 ||
      expected_size != result->decompressed_size) {
    goto cleanup;
  }
  memory_size = section->size;
  if ((size_t)entry_offset + 16U > memory_size) memory_size = (size_t)entry_offset + 16U;
  if ((size_t)transfer_target + expected_size + 16U > memory_size)
    memory_size = (size_t)transfer_target + expected_size + 16U;
  for (range_index = 0U; range_index < analysis->policy.runtime_range_count &&
      range_index < M68K_ANALYSIS_RUNTIME_RANGE_LIMIT; ++range_index) {
    const M68kAnalysisRuntimeRange *range = &analysis->policy.runtime_ranges[range_index];
    size_t range_end;
    if (!range->has_section_index || range->size == 0U || range->runtime_address > UINT32_MAX - range->size)
      continue;
    range_end = (size_t)range->runtime_address + range->size;
    if (range_end > memory_size) memory_size = range_end;
  }
  if (memory_size > PLATFORM_SELF_DECRUNCH_MEMORY_LIMIT || entry_offset >= section->size) goto cleanup;
  memory = (uint8_t *)arena_calloc(scratch_arena, memory_size, 1U);
  if (memory == NULL) goto cleanup;
  memcpy(memory, section->data, section->size);
  for (range_index = 0U; range_index < analysis->policy.runtime_range_count &&
      range_index < M68K_ANALYSIS_RUNTIME_RANGE_LIMIT; ++range_index) {
    const M68kAnalysisRuntimeRange *range = &analysis->policy.runtime_ranges[range_index];
    const M68kSection *source_section;
    if (!range->has_section_index || range->section_index >= object->section_count || range->size == 0U ||
        range->runtime_address > UINT32_MAX - range->size) {
      continue;
    }
    source_section = &object->sections[range->section_index];
    if (source_section->data == NULL || range->offset > source_section->data_size ||
        range->size > source_section->data_size - range->offset ||
        (size_t)range->runtime_address + range->size > memory_size) {
      continue;
    }
    memcpy(memory + range->runtime_address, source_section->data + range->offset, range->size);
  }
  memset(&state, 0, sizeof(state));
  memset(&memory_policy, 0, sizeof(memory_policy));
  memset(&run_result, 0, sizeof(run_result));
  memory_policy.external_write_allowed = platform_self_decrunch_external_write_allowed_local;
  memory_policy.external_read = platform_self_decrunch_external_read_local;
  memory_policy.user = (void *)object;
  state.pc = entry_offset;
  state.a[7] = (uint32_t)memory_size;
  step_limit = platform_self_decrunch_step_limit_for_output_local(result->decompressed_size);
  if (m68k_simulate_run_concrete(platform_self_decrunch_execution_cpu_local(object, analysis),
      memory, memory_size, &state, step_limit, transfer_target, transfer_target + 16U,
      &memory_policy, &run_result) != 0) {
    goto cleanup;
  }
  if (run_result.stop_reason != M68K_SIM_CONCRETE_RUN_STOP_PC_RANGE ||
      !concrete_write_ranges_cover_span_local(&run_result, transfer_target, result->decompressed_size) ||
      memcmp(memory + transfer_target, expected, expected_size) != 0) {
    goto cleanup;
  }
  ok = 1;

cleanup:
  arena_rewind(scratch_arena, mark);
  return ok;
}

static const char *provider_candidate_codec_name_local(const PlatformDecompressionCandidate *candidate) {
  if (candidate == NULL || candidate->codec_hint[0] == '\0') return "unknown";
  if (strcmp(candidate->codec_hint, "bk") == 0) return "bk";
  if (strcmp(candidate->codec_hint, "rnc1-old") == 0) return "rnc1-old";
  return candidate->codec_hint;
}

static int init_scanned_provider_candidate_result_local(PlatformDecompressionIdentifyResult *result,
    const M68kSection *section, size_t section_index, const PlatformDecompressionCandidate *candidate) {
  if (result == NULL || section == NULL || section->data == NULL || candidate == NULL ||
      candidate->packed_size == 0U || candidate->decompressed_size == 0U ||
      candidate->offset > section->data_size || candidate->packed_size > section->data_size - candidate->offset) {
    return -1;
  }
  platform_decompression_identify_result_init(result);
  snprintf(result->provider_id, sizeof(result->provider_id), "ancient-cli");
  snprintf(result->codec_id, sizeof(result->codec_id), "%s",
    candidate->codec_hint[0] != '\0' ? candidate->codec_hint : "unknown");
  snprintf(result->codec_name, sizeof(result->codec_name), "%s",
    provider_candidate_codec_name_local(candidate));
  snprintf(result->confidence, sizeof(result->confidence), "provider-scanned");
  result->found = 1;
  result->source_offset = candidate->offset;
  result->source_section_index = (uint32_t)section_index;
  result->source_section_offset = candidate->offset;
  result->packed_size = candidate->packed_size;
  result->decompressed_size = candidate->decompressed_size;
  result->has_source_section = 1U;
  (void)m68k_platform_sha256_hex(section->data + candidate->offset, candidate->packed_size,
    result->source_sha256);
  return 0;
}

static int promote_provider_payload_from_wrapper_static_local(const M68kObject *object,
    const M68kSourceAnalysisIR *analysis, PlatformDecompressionIdentifyResult *result,
    Arena *scratch_arena) {
  M68kDecodeIR decode;
  const M68kDecodeSectionIR *decode_section;
  const M68kSectionAnalysisIR *section_analysis;
  uint32_t offset;
  uint32_t source_start, source_end;
  int promoted = 0;
  memset(&decode, 0, sizeof(decode));
  if (object == NULL || analysis == NULL || scratch_arena == NULL || result == NULL ||
      !result->has_source_section || result->source_section_index >= object->section_count ||
      result->source_section_index >= analysis->section_count ||
      result->source_section_offset > UINT32_MAX - result->packed_size) {
    return 0;
  }
  if (m68k_decode_ir_build_object_sections(&decode, object, m68k_diag_sink(NULL)) != 0) return 0;
  if (result->source_section_index >= decode.section_count) {
    m68k_decode_ir_destroy(&decode);
    return 0;
  }
  decode_section = &decode.sections[result->source_section_index];
  section_analysis = &analysis->sections[result->source_section_index];
  source_start = result->source_section_offset;
  source_end = source_start + result->packed_size;
  for (offset = 0U; offset < section_analysis->certain_code_size; ++offset) {
    const M68kDecodeCandidate *candidate = NULL;
    uint32_t transfer_target = 0U;
    uint8_t parent_remains_active;
    if (section_analysis->certain_code_start == NULL || !section_analysis->certain_code_start[offset]) continue;
    if (m68k_decode_ir_ensure_candidate_at(&decode, result->source_section_index, offset,
        analysis->policy.max_cpu, &candidate, m68k_diag_sink(NULL)) != 0 ||
        candidate == NULL || candidate->byte_count == 0U) {
      continue;
    }
    if (candidate->offset > UINT32_MAX - candidate->byte_count) continue;
    if (candidate->offset < source_end && candidate->offset + candidate->byte_count > source_start) continue;
    if (!runtime_transfer_target_from_candidate_local(decode_section, section_analysis, candidate,
        &transfer_target, &parent_remains_active)) {
      continue;
    }
    if (parent_remains_active || transfer_target > UINT32_MAX - result->decompressed_size) continue;
    result->has_decompressed_load_entry = 1U;
    result->has_decompressed_load_entry_from_wrapper = 1U;
    result->parent_remains_active_known = 1U;
    result->parent_remains_active = 0U;
    result->decompressed_load_address = transfer_target;
    result->decompressed_entrypoint = transfer_target;
    result->decompressed_initial_control_target = transfer_target;
    promoted = 1;
    break;
  }
  m68k_decode_ir_destroy(&decode);
  return promoted;
}

static int promote_provider_payload_from_wrapper_simulation_local(const M68kObject *object,
    const M68kSourceAnalysisIR *analysis, const char *output_path, PlatformDecompressionIdentifyResult *result,
    Arena *scratch_arena) {
  M68kDecodeIR decode;
  const M68kDecodeSectionIR *decode_section;
  const M68kSectionAnalysisIR *section_analysis;
  const M68kSection *section;
  uint32_t offset;
  uint32_t source_start, source_end;
  int promoted = 0;
  memset(&decode, 0, sizeof(decode));
  if (object == NULL || analysis == NULL || scratch_arena == NULL || output_path == NULL || result == NULL ||
      !result->has_source_section || result->source_section_index >= object->section_count ||
      result->source_section_index >= analysis->section_count ||
      result->source_section_offset > UINT32_MAX - result->packed_size) {
    return 0;
  }
  if (m68k_decode_ir_build_object_sections(&decode, object, m68k_diag_sink(NULL)) != 0) return 0;
  if (result->source_section_index >= decode.section_count) {
    m68k_decode_ir_destroy(&decode);
    return 0;
  }
  decode_section = &decode.sections[result->source_section_index];
  section_analysis = &analysis->sections[result->source_section_index];
  section = &object->sections[result->source_section_index];
  source_start = result->source_section_offset;
  source_end = source_start + result->packed_size;
  for (offset = 0U; offset < section_analysis->certain_code_size; ++offset) {
    const M68kDecodeCandidate *candidate = NULL;
    uint32_t transfer_target = 0U;
    uint32_t entry_offset;
    uint8_t parent_remains_active;
    if (section_analysis->certain_code_start == NULL || !section_analysis->certain_code_start[offset]) {
      continue;
    }
    if (m68k_decode_ir_ensure_candidate_at(&decode, result->source_section_index, offset,
        analysis->policy.max_cpu, &candidate, m68k_diag_sink(NULL)) != 0 ||
        candidate == NULL || candidate->byte_count == 0U) {
      continue;
    }
    if (candidate->offset > UINT32_MAX - candidate->byte_count) continue;
    if (candidate->offset < source_end && candidate->offset + candidate->byte_count > source_start) continue;
    if (!runtime_transfer_target_from_candidate_local(decode_section, section_analysis, candidate,
        &transfer_target, &parent_remains_active)) {
      continue;
    }
    if (parent_remains_active || transfer_target > UINT32_MAX - result->decompressed_size) continue;
    entry_offset = reachable_decrunch_entry_root_local(section_analysis, result->source_section_index,
      0U, candidate->offset, scratch_arena);
    if (!simulate_provider_wrapper_candidate_local(object, analysis, section, entry_offset, transfer_target,
        output_path, result, scratch_arena)) {
      continue;
    }
    result->has_decompressed_load_entry = 1U;
    result->has_decompressed_load_entry_from_wrapper = 1U;
    result->parent_remains_active_known = 1U;
    result->parent_remains_active = 0U;
    result->decompressed_load_address = transfer_target;
    result->decompressed_entrypoint = transfer_target;
    result->decompressed_initial_control_target = transfer_target;
    promoted = 1;
    break;
  }
  m68k_decode_ir_destroy(&decode);
  return promoted;
}

static int simulate_self_decrunch_output_local(const M68kObject *object, const M68kSourceAnalysisIR *analysis,
    const M68kDecodeSectionIR *section, const PlatformSelfDecrunchEvent *event,
    PlatformSelfDecrunchEvent *out_event, const char *output_path, M68kDiagList *diagnostics,
    Arena *scratch_arena) {
  ArenaMark mark;
  uint8_t *memory = NULL;
  size_t memory_size, range_index, write_range_index;
  uint32_t output_start = 0U, output_end = 0U;
  M68kSimConcreteState state;
  M68kSimConcreteMemoryPolicy memory_policy;
  M68kSimConcreteRunTraceResult result;
  int ok = 0;
  if (out_event != NULL && event != NULL) *out_event = *event;
  if (object == NULL || analysis == NULL || scratch_arena == NULL || section == NULL || event == NULL ||
      out_event == NULL || section->data == NULL ||
      event->entrypoint > UINT32_MAX - 16U || event->observed_write_end > UINT32_MAX - 16U) {
    return 0;
  }
  memory_size = section->size;
  if ((size_t)event->entrypoint + 16U > memory_size) memory_size = (size_t)event->entrypoint + 16U;
  if ((size_t)event->observed_write_end + 16U > memory_size) memory_size = (size_t)event->observed_write_end + 16U;
  if (section->size > (size_t)(UINT32_MAX - event->load_address)) return 0;
  if ((size_t)event->load_address + section->size > memory_size) {
    memory_size = (size_t)event->load_address + section->size;
  }
  self_decrunch_grow_memory_for_candidate_runtime_literals_local(section, event, &memory_size);
  for (range_index = 0U; range_index < analysis->policy.runtime_range_count &&
      range_index < M68K_ANALYSIS_RUNTIME_RANGE_LIMIT; ++range_index) {
    const M68kAnalysisRuntimeRange *range = &analysis->policy.runtime_ranges[range_index];
    size_t range_end;
    if (!range->has_section_index || range->size == 0U || range->runtime_address > UINT32_MAX - range->size)
      continue;
    range_end = (size_t)range->runtime_address + range->size;
    if (range_end > memory_size) memory_size = range_end;
  }
  if (event->source_section_index < analysis->section_count) {
    const M68kSectionAnalysisIR *section_analysis = &analysis->sections[event->source_section_index];
    size_t view_index;
    for (view_index = 0U; view_index < section_analysis->runtime_view_count; ++view_index) {
      const M68kRuntimeViewIR *view = &section_analysis->runtime_views[view_index];
      size_t view_end;
      if (!view->materialized || view->size == 0U || view->runtime_address > UINT32_MAX - view->size)
        continue;
      view_end = (size_t)view->runtime_address + view->size;
      if (view_end > memory_size) memory_size = view_end;
    }
  }
  if (memory_size > PLATFORM_SELF_DECRUNCH_MEMORY_LIMIT || event->decompressor_entry_offset >= section->size) return 0;
  mark = arena_mark(scratch_arena);
  memory = (uint8_t *)arena_calloc(scratch_arena, memory_size, 1U);
  if (memory == NULL) goto cleanup;
  memcpy(memory, section->data, section->size);
  if ((size_t)event->load_address + section->size <= memory_size) {
    memcpy(memory + event->load_address, section->data, section->size);
  }
  for (range_index = 0U; range_index < analysis->policy.runtime_range_count &&
      range_index < M68K_ANALYSIS_RUNTIME_RANGE_LIMIT; ++range_index) {
    const M68kAnalysisRuntimeRange *range = &analysis->policy.runtime_ranges[range_index];
    const M68kSection *source_section;
    if (!range->has_section_index || range->section_index >= object->section_count || range->size == 0U ||
        range->runtime_address > UINT32_MAX - range->size) {
      continue;
    }
    source_section = &object->sections[range->section_index];
    if (source_section->data == NULL || range->offset > source_section->data_size ||
        range->size > source_section->data_size - range->offset ||
        (size_t)range->runtime_address + range->size > memory_size) {
      continue;
    }
    memcpy(memory + range->runtime_address, source_section->data + range->offset, range->size);
  }
  if (event->source_section_index < analysis->section_count && event->source_section_index < object->section_count) {
    const M68kSectionAnalysisIR *section_analysis = &analysis->sections[event->source_section_index];
    const M68kSection *source_section = &object->sections[event->source_section_index];
    size_t view_index;
    for (view_index = 0U; view_index < section_analysis->runtime_view_count; ++view_index) {
      const M68kRuntimeViewIR *view = &section_analysis->runtime_views[view_index];
      if (!view->materialized || view->size == 0U || view->runtime_address > UINT32_MAX - view->size ||
          source_section->data == NULL || view->storage_offset > source_section->data_size ||
          view->size > source_section->data_size - view->storage_offset ||
          (size_t)view->runtime_address + view->size > memory_size) {
        continue;
      }
      memcpy(memory + view->runtime_address, source_section->data + view->storage_offset, view->size);
    }
  }
  memset(&state, 0, sizeof(state));
  memset(&memory_policy, 0, sizeof(memory_policy));
  memset(&result, 0, sizeof(result));
  memory_policy.external_write_allowed = platform_self_decrunch_external_write_allowed_local;
  memory_policy.external_read = platform_self_decrunch_external_read_local;
  memory_policy.user = (void *)object;
  state.pc = event->decompressor_entry_offset;
  state.a[7] = (uint32_t)memory_size;
  if (m68k_simulate_run_concrete(platform_self_decrunch_execution_cpu_local(object, analysis),
      memory, memory_size, &state,
      PLATFORM_SELF_DECRUNCH_STEP_LIMIT,
      event->entrypoint, event->entrypoint + 16U, &memory_policy, &result) != 0) {
    if (diagnostics != NULL && !m68k_diag_has_errors(diagnostics))
      platform_file_add_error(diagnostics, "self-decrunch simulation failed");
    goto cleanup;
  }
  out_event->simulation_attempted = 1U;
  out_event->simulated_stop_reason = (uint8_t)result.stop_reason;
  out_event->simulated_start_pc = result.start_pc;
  out_event->simulated_stop_pc = result.stop_pc;
  out_event->simulated_step_count = (uint32_t)result.step_count;
  out_event->simulated_write_count = (uint32_t)result.memory_write_count;
  {
    const char *message = m68k_diag_first_message(&result.diagnostics);
    if (message != NULL) {
      snprintf(out_event->simulated_diagnostic, sizeof(out_event->simulated_diagnostic), "%s", message);
    }
  }
  if (result.stop_reason != M68K_SIM_CONCRETE_RUN_STOP_PC_RANGE) {
    if (diagnostics != NULL && !m68k_diag_has_errors(diagnostics)) {
      char message[160];
      snprintf(message, sizeof(message), "self-decrunch simulation stopped at %s pc=$%08X",
        self_decrunch_sim_stop_reason_name_local((uint8_t)result.stop_reason), (unsigned)result.stop_pc);
      platform_file_add_error(diagnostics, message);
    }
    goto cleanup;
  }
  if (result.memory_write_count == 0U || result.memory_write_range_overflow ||
      result.memory_write_range_count == 0U) {
    if (diagnostics != NULL && !m68k_diag_has_errors(diagnostics))
      platform_file_add_error(diagnostics, "self-decrunch simulation produced no bounded write range");
    goto cleanup;
  }
  for (write_range_index = 0U; write_range_index < result.memory_write_range_count; ++write_range_index) {
    const M68kSimConcreteWriteRange *write_range = &result.memory_write_ranges[write_range_index];
    if (write_range->start <= event->entrypoint && write_range->end > event->entrypoint) {
      output_start = write_range->start;
      output_end = write_range->end;
      break;
    }
  }
  if (output_start > event->entrypoint || output_end <= event->entrypoint || output_end > memory_size) {
    if (diagnostics != NULL && !m68k_diag_has_errors(diagnostics))
      platform_file_add_error(diagnostics, "self-decrunch writes do not cover transfer entrypoint");
    goto cleanup;
  }
  if (output_path != NULL && output_path[0] != '\0' &&
      write_bytes_to_path_local(output_path, memory + output_start, output_end - output_start, diagnostics) != 0) {
    goto cleanup;
  }
  out_event->has_simulated_output = 1U;
  out_event->simulated_output_start = output_start;
  out_event->simulated_output_end = output_end;
  if (out_event->observed_write_count == 0U) {
    out_event->observed_write_start = output_start;
    out_event->observed_write_end = output_end;
    out_event->observed_write_count = (uint32_t)result.memory_write_range_count;
  }
  (void)m68k_platform_sha256_hex(memory + output_start, output_end - output_start,
    out_event->simulated_output_sha256);
  out_event->entry_validation_attempted = 1U;
  out_event->entry_validation_valid = 0U;
  (void)validate_decompressed_entrypoint_bytes_local(memory + output_start, output_end - output_start,
    output_start, event->entrypoint,
    &out_event->entry_validation_accepted_instructions,
    &out_event->entry_validation_unsupported_instruction_demotes,
    &out_event->entry_validation_required_instruction_failures,
    &out_event->entry_validation_code_start_control_targets,
    &out_event->entry_validation_valid);
  ok = 1;

cleanup:
  arena_rewind(scratch_arena, mark);
  return ok;
}

static int collect_self_decrunch_events_for_section(const M68kObject *object, const M68kDecodeIR *decode,
    const M68kSourceAnalysisIR *analysis, size_t section_index, PlatformSelfDecrunchEvent *events,
    size_t event_capacity, size_t *io_event_count, const char *materialize_event_id,
    const char *materialize_output_path, PlatformSelfDecrunchEvent *out_materialized_event,
    M68kDiagList *materialize_diagnostics, Arena *scratch_arena) {
  const M68kSection *object_section;
  const M68kDecodeSectionIR *decode_section;
  const M68kSectionAnalysisIR *section_analysis;
  uint32_t a_known = 0U;
  uint32_t a_values[8] = {0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U};
  PlatformRuntimeWriteObservation writes[64];
  size_t write_count = 0U;
  uint32_t offset;
  uint32_t previous_end = UINT32_MAX;
  uint32_t run_start = 0U;
  uint32_t bridge_target = UINT32_MAX;
  if (object == NULL || decode == NULL || analysis == NULL || events == NULL || io_event_count == NULL ||
      section_index >= object->section_count || section_index >= decode->section_count ||
      section_index >= analysis->section_count) {
    return 0;
  }
  object_section = &object->sections[section_index];
  decode_section = &decode->sections[section_index];
  section_analysis = &analysis->sections[section_index];
  if (object_section->data == NULL || object_section->data_size == 0U ||
      section_analysis->certain_code_start == NULL || section_analysis->certain_code_byte == NULL) {
    return 0;
  }
  memset(writes, 0, sizeof(writes));
  for (offset = 0U; offset < decode_section->size && *io_event_count < event_capacity; ++offset) {
    const M68kDecodeCandidate *candidate = NULL;
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    uint32_t target = 0U;
    uint32_t observed_write_start = 0U;
    uint32_t observed_write_end = 0U;
    uint32_t observed_write_count = 0U;
    uint8_t parent_remains_active = 1U;
    uint8_t event_emitted = 0U;
    if (section_analysis->certain_code_start[offset] == 0U) continue;
    if (previous_end != UINT32_MAX && offset != previous_end && offset != bridge_target) {
      a_known = 0U;
      memset(a_values, 0, sizeof(a_values));
      memset(writes, 0, sizeof(writes));
      write_count = 0U;
      run_start = offset;
    } else if (previous_end == UINT32_MAX) {
      run_start = offset;
    }
    if (m68k_decode_ir_ensure_candidate_at((M68kDecodeIR *)decode, section_index, offset,
        analysis->policy.max_cpu, &candidate, m68k_diag_sink(NULL)) != 0 ||
        candidate == NULL || candidate->byte_count == 0U ||
        m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
      previous_end = UINT32_MAX;
      continue;
    }
    previous_end = offset + candidate->byte_count;
    metadata = m68k_sim_metadata_for_instruction(&instruction);
    if (metadata == NULL) continue;
    if (!same_section_unconditional_bridge_target_local(candidate, metadata, section_index, &bridge_target))
      bridge_target = UINT32_MAX;
    trace_runtime_writes_from_candidate_local(candidate, &instruction, metadata, &a_known, a_values, writes,
      sizeof(writes) / sizeof(writes[0]), &write_count);
    if (runtime_transfer_target_from_candidate_local(decode_section, section_analysis, candidate, &target,
        &parent_remains_active) &&
        observed_writes_cover_target_local(writes, write_count, target, &observed_write_start,
          &observed_write_end, &observed_write_count) &&
        observed_write_count >= 2U) {
      PlatformSelfDecrunchEvent event;
      char event_id[160];
      int materialize_this_event;
      memset(&event, 0, sizeof(event));
      event.source_section_index = (uint32_t)section_index;
      event.decompressor_entry_offset = reachable_decrunch_entry_root_local(section_analysis, section_index,
        run_start, offset, scratch_arena);
      event.transfer_offset = offset;
      event.load_address = target;
      event.entrypoint = target;
      event.observed_write_start = observed_write_start;
      event.observed_write_end = observed_write_end;
      event.observed_write_count = observed_write_count;
      event.parent_remains_active = parent_remains_active;
      make_self_decrunch_event_id_local(event_id, sizeof(event_id), &event);
      materialize_this_event = materialize_event_id != NULL && strcmp(event_id, materialize_event_id) == 0;
      (void)simulate_self_decrunch_output_local(object, analysis, decode_section, &event, &event,
        materialize_this_event ? materialize_output_path : NULL,
        materialize_this_event ? materialize_diagnostics : NULL, scratch_arena);
      if (materialize_this_event && out_materialized_event != NULL) *out_materialized_event = event;
      if (!self_decrunch_event_duplicate_local(events, *io_event_count, &event)) {
        events[*io_event_count] = event;
        *io_event_count += 1U;
      }
      event_emitted = 1U;
    }
    if (!event_emitted &&
        runtime_transfer_target_from_candidate_min_local(decode_section, section_analysis, candidate, 0U, 0U,
          &target, &parent_remains_active) &&
        !parent_remains_active) {
      PlatformSelfDecrunchEvent event;
      char event_id[160];
      int materialize_this_event;
      memset(&event, 0, sizeof(event));
      event.source_section_index = (uint32_t)section_index;
      event.decompressor_entry_offset = reachable_decrunch_entry_root_local(section_analysis, section_index,
        run_start, offset, scratch_arena);
      event.transfer_offset = offset;
      event.load_address = target;
      event.entrypoint = target;
      event.parent_remains_active = parent_remains_active;
      make_self_decrunch_event_id_local(event_id, sizeof(event_id), &event);
      materialize_this_event = materialize_event_id != NULL && strcmp(event_id, materialize_event_id) == 0;
      if (simulate_self_decrunch_output_local(object, analysis, decode_section, &event, &event,
          materialize_this_event ? materialize_output_path : NULL,
          materialize_this_event ? materialize_diagnostics : NULL, scratch_arena)) {
        if (materialize_this_event && out_materialized_event != NULL) *out_materialized_event = event;
        if (!self_decrunch_event_duplicate_local(events, *io_event_count, &event)) {
          events[*io_event_count] = event;
          *io_event_count += 1U;
        }
      }
    }
  }
  for (offset = 0U; offset < section_analysis->runtime_view_count && *io_event_count < event_capacity; ++offset) {
    const M68kRuntimeViewIR *view = &section_analysis->runtime_views[offset];
    uint32_t view_storage_end;
    size_t ref_index;
    if (!view->materialized || view->size == 0U || view->storage_offset > UINT32_MAX - view->size)
      continue;
    view_storage_end = view->storage_offset + view->size;
    for (ref_index = 0U; ref_index < section_analysis->code_start_ref_count &&
        *io_event_count < event_capacity; ++ref_index) {
      const M68kCodeStartRefIR *ref = &section_analysis->code_start_refs[ref_index];
      const M68kDecodeCandidate *candidate = NULL;
      uint32_t target = 0U;
      uint8_t parent_remains_active = 1U;
      PlatformSelfDecrunchEvent event;
      char event_id[160];
      int materialize_this_event;
      if (ref->reason != M68K_FACT_CODE_START_REASON_CONTROL_TARGET ||
          !ref->has_runtime_address || ref->source_section_index != section_index ||
          ref->source_offset < view->storage_offset || ref->source_offset >= view_storage_end) {
        continue;
      }
      if (m68k_decode_ir_ensure_candidate_at((M68kDecodeIR *)decode, section_index, ref->source_offset,
          analysis->policy.max_cpu, &candidate, m68k_diag_sink(NULL)) != 0 ||
          candidate == NULL || candidate->byte_count == 0U ||
          !runtime_transfer_target_from_candidate_min_local(decode_section, section_analysis, candidate, 0U, 0U,
            &target, &parent_remains_active) ||
          parent_remains_active || target != ref->runtime_address) {
        continue;
      }
      memset(&event, 0, sizeof(event));
      event.source_section_index = (uint32_t)section_index;
      event.decompressor_entry_offset = view->runtime_address;
      event.transfer_offset = ref->source_offset;
      event.load_address = target;
      event.entrypoint = target;
      event.parent_remains_active = 0U;
      make_self_decrunch_event_id_local(event_id, sizeof(event_id), &event);
      materialize_this_event = materialize_event_id != NULL && strcmp(event_id, materialize_event_id) == 0;
      if (simulate_self_decrunch_output_local(object, analysis, decode_section, &event, &event,
          materialize_this_event ? materialize_output_path : NULL,
          materialize_this_event ? materialize_diagnostics : NULL, scratch_arena)) {
        if (materialize_this_event && out_materialized_event != NULL) *out_materialized_event = event;
        if (!self_decrunch_event_duplicate_local(events, *io_event_count, &event)) {
          events[*io_event_count] = event;
          *io_event_count += 1U;
        }
      }
    }
  }
  return 0;
}

static int collect_self_decrunch_events_local(const M68kObject *object, const M68kSourceAnalysisIR *analysis,
    PlatformSelfDecrunchEvent *events, size_t event_capacity, size_t *out_event_count,
    const char *materialize_event_id, const char *materialize_output_path,
    PlatformSelfDecrunchEvent *out_materialized_event, M68kDiagList *materialize_diagnostics,
    Arena *scratch_arena) {
  M68kDecodeIR decode;
  size_t section_index;
  int result = 0;
  if (out_event_count != NULL) *out_event_count = 0U;
  if (object == NULL || analysis == NULL || events == NULL || out_event_count == NULL || event_capacity == 0U ||
      scratch_arena == NULL)
    return 0;
  if (object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 0;
  memset(&decode, 0, sizeof(decode));
  if (m68k_decode_ir_build_object_sections(&decode, object, m68k_diag_sink(NULL)) != 0) return 0;
  for (section_index = 0U; section_index < object->section_count && *out_event_count < event_capacity;
      ++section_index) {
    if (collect_self_decrunch_events_for_section(object, &decode, analysis, section_index, events,
        event_capacity, out_event_count, materialize_event_id, materialize_output_path,
        out_materialized_event, materialize_diagnostics, scratch_arena) != 0) {
      result = -1;
      break;
    }
  }
  m68k_decode_ir_destroy(&decode);
  return result;
}

static const char *self_decrunch_sim_stop_reason_name_local(uint8_t stop_reason) {
  switch (stop_reason) {
    case M68K_SIM_CONCRETE_RUN_STOP_NONE: return "none";
    case M68K_SIM_CONCRETE_RUN_STOP_PC_RANGE: return "pc_range";
    case M68K_SIM_CONCRETE_RUN_STOP_PC_OUT_OF_RANGE: return "pc_out_of_range";
    case M68K_SIM_CONCRETE_RUN_STOP_INSTRUCTION_LIMIT: return "instruction_limit";
    case M68K_SIM_CONCRETE_RUN_STOP_DECODE_ERROR: return "decode_error";
    case M68K_SIM_CONCRETE_RUN_STOP_SIMULATION_ERROR: return "simulation_error";
    case M68K_SIM_CONCRETE_RUN_STOP_BAD_ARGUMENT: return "bad_argument";
    default: return "unknown";
  }
}

static uint8_t self_decrunch_event_reason_id_local(const PlatformSelfDecrunchEvent *event) {
  if (event == NULL) return PLATFORM_DECOMPRESSION_REASON_UNIDENTIFIED_SELF_DECRUNCHER;
  if (event->has_simulated_output) return PLATFORM_DECOMPRESSION_REASON_SIMULATED_PC_RANGE_STOP;
  if (!event->simulation_attempted) return PLATFORM_DECOMPRESSION_REASON_UNIDENTIFIED_SELF_DECRUNCHER;
  switch (event->simulated_stop_reason) {
    case M68K_SIM_CONCRETE_RUN_STOP_PC_OUT_OF_RANGE:
      return PLATFORM_DECOMPRESSION_REASON_SIMULATED_PC_OUT_OF_RANGE;
    case M68K_SIM_CONCRETE_RUN_STOP_INSTRUCTION_LIMIT:
      return PLATFORM_DECOMPRESSION_REASON_SIMULATED_INSTRUCTION_LIMIT;
    case M68K_SIM_CONCRETE_RUN_STOP_DECODE_ERROR:
      return PLATFORM_DECOMPRESSION_REASON_SIMULATED_DECODE_ERROR;
    case M68K_SIM_CONCRETE_RUN_STOP_SIMULATION_ERROR:
      return PLATFORM_DECOMPRESSION_REASON_SIMULATED_ERROR;
    case M68K_SIM_CONCRETE_RUN_STOP_BAD_ARGUMENT:
      return PLATFORM_DECOMPRESSION_REASON_SIMULATED_BAD_ARGUMENT;
    case M68K_SIM_CONCRETE_RUN_STOP_PC_RANGE:
      return PLATFORM_DECOMPRESSION_REASON_SIMULATED_NO_OUTPUT_RANGE;
    default:
      return PLATFORM_DECOMPRESSION_REASON_SIMULATED_UNKNOWN_STOP;
  }
}

static int append_recognized_unpacker_event_json(JsonBuilder *builder,
    const PlatformRecognizedUnpackerEvent *event) {
  char event_id[160];
  uint8_t status;
  uint8_t reason;
  uint8_t payload_role;
  uint8_t payload_confidence;
  uint8_t parent_remains_active;
  uint8_t native_materializable;
  if (builder == NULL || event == NULL) return -1;
  make_recognized_unpacker_event_id_local(event_id, sizeof(event_id), event);
  native_materializable = event->native_unpack_validated || event->native_execution_deferred;
  status = native_materializable ? PLATFORM_DECOMPRESSION_STATUS_MATERIALIZABLE :
    (event->entry_validation_attempted && !event->entry_validation_valid ?
      PLATFORM_DECOMPRESSION_STATUS_NEEDS_REVIEW_BLOCKER : PLATFORM_DECOMPRESSION_STATUS_IDENTIFIED);
  reason = event->native_unpack_validated ? PLATFORM_DECOMPRESSION_REASON_NATIVE_TETRAGON_UNPACK_VALIDATED :
    (event->native_execution_deferred ? PLATFORM_DECOMPRESSION_REASON_NATIVE_TETRAGON_UNPACK_DEFERRED :
    (event->entry_validation_attempted && !event->entry_validation_valid ?
      PLATFORM_DECOMPRESSION_REASON_INVALID_DECOMPRESSED_ENTRYPOINT :
      PLATFORM_DECOMPRESSION_REASON_RECOGNIZED_UNPACKER_SIGNATURE));
  payload_role = native_materializable ? PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_PRIMARY_PROGRAM :
    PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_UNKNOWN_RUNTIME_PAYLOAD;
  payload_confidence = event->native_unpack_validated ?
    PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_NATIVE_UNPACK_ENTRY_VALIDATED :
    PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_SIGNATURE_ONLY;
  parent_remains_active = native_materializable ? PLATFORM_DECOMPRESSION_PARENT_REMAINS_ACTIVE_FALSE :
    PLATFORM_DECOMPRESSION_PARENT_REMAINS_ACTIVE_UNKNOWN;
  if (json_builder_appendf(builder, "{\"event_kind_id\":%u,\"event_kind\":",
      (unsigned)PLATFORM_DECOMPRESSION_EVENT_KIND_DECOMPRESSION) != 0 ||
      json_builder_append_json_string(builder,
        decompression_event_kind_name_local(PLATFORM_DECOMPRESSION_EVENT_KIND_DECOMPRESSION)) != 0 ||
      json_builder_append(builder, ",\"event_id\":") != 0 ||
      json_builder_append_json_string(builder, event_id) != 0 ||
      json_builder_appendf(builder, ",\"status_id\":%u,\"status\":", (unsigned)status) != 0 ||
      json_builder_append_json_string(builder, decompression_status_name_local(status)) != 0 ||
      json_builder_appendf(builder, ",\"reason_id\":%u,\"reason\":", (unsigned)reason) != 0 ||
      json_builder_append_json_string(builder, decompression_reason_name_local(reason)) != 0 ||
      json_builder_appendf(builder, ",\"payload_role_id\":%u,\"payload_role\":", (unsigned)payload_role) != 0 ||
      json_builder_append_json_string(builder, decompression_payload_role_name_local(payload_role)) != 0 ||
      json_builder_appendf(builder, ",\"payload_role_confidence_id\":%u,\"payload_role_confidence\":",
        (unsigned)payload_confidence) != 0 ||
      json_builder_append_json_string(builder,
        decompression_payload_role_confidence_name_local(payload_confidence)) != 0 ||
      json_builder_appendf(builder, ",\"parent_remains_active_id\":%u,\"parent_remains_active\":",
        (unsigned)parent_remains_active) != 0 ||
      json_builder_append_json_string(builder,
        decompression_parent_remains_active_name_local(parent_remains_active)) != 0 ||
      json_builder_appendf(builder, ",\"source_kind_id\":%u,\"source_kind\":",
        (unsigned)PLATFORM_DECOMPRESSION_SOURCE_RECOGNIZED_UNPACKER) != 0 ||
      json_builder_append_json_string(builder,
        decompression_source_kind_name_local(PLATFORM_DECOMPRESSION_SOURCE_RECOGNIZED_UNPACKER)) != 0 ||
      json_builder_appendf(builder, ",\"codec_support_id\":%u,\"codec_support\":",
        (unsigned)PLATFORM_DECOMPRESSION_CODEC_SUPPORT_NATIVE_DECOMPRESSOR) != 0 ||
      json_builder_append_json_string(builder,
        decompression_codec_support_name_local(PLATFORM_DECOMPRESSION_CODEC_SUPPORT_NATIVE_DECOMPRESSOR)) != 0 ||
      json_builder_append(builder, ",\"provider_id\":") != 0 ||
      json_builder_append_json_string(builder, event->provider_id) != 0 ||
      json_builder_append(builder, ",\"codec_id\":") != 0 ||
      json_builder_append_json_string(builder, event->codec_id) != 0 ||
      json_builder_append(builder, ",\"codec_name\":") != 0 ||
      json_builder_append_json_string(builder, event->codec_name) != 0 ||
      json_builder_appendf(builder,
        ",\"source_section\":%u,\"source_section_offset\":%u,"
        "\"compressed_source_section_offset\":%u,\"unpacker_marker_offset\":%u,"
        "\"compressed_source_section_end_offset\":%u,\"postpass_source_start_address\":%u,"
        "\"postpass_source_end_address\":%u,\"postpass_escape_byte\":%u,"
        "\"target_start_address\":%u,\"entrypoint\":%u",
        (unsigned)event->source_section_index, (unsigned)event->compressed_source_section_offset,
        (unsigned)event->compressed_source_section_offset, (unsigned)event->marker_offset,
        (unsigned)event->compressed_source_section_end_offset, (unsigned)event->postpass_source_start_address,
        (unsigned)event->postpass_source_end_address, (unsigned)event->postpass_escape_byte,
        (unsigned)event->target_start_address,
        (unsigned)event->entrypoint) != 0) {
    return -1;
  }
  if (event->has_copied_stub) {
    if (json_builder_appendf(builder,
        ",\"copied_stub_storage_offset\":%u,\"copied_stub_runtime_address\":%u",
        (unsigned)event->copied_stub_storage_offset, (unsigned)event->copied_stub_runtime_address) != 0) {
      return -1;
    }
    if (event->has_copied_stub_transfer &&
        json_builder_appendf(builder, ",\"copied_stub_transfer_offset\":%u",
          (unsigned)event->copied_stub_transfer_offset) != 0)
      return -1;
    if (event->has_copied_stub_transfer &&
        json_builder_appendf(builder, ",\"copied_stub_transfer_site_offset\":%u",
          (unsigned)event->copied_stub_transfer_site_offset) != 0)
      return -1;
  }
  if (event->native_execution_attempted) {
    if (json_builder_appendf(builder, ",\"native_execution_attempted\":true,"
        "\"native_execution_start_pc\":%u,"
        "\"native_execution_step_count\":%u,"
        "\"native_execution_stop_reason\":",
        (unsigned)event->native_execution_start_pc,
        (unsigned)event->native_execution_step_count) != 0 ||
        json_builder_append_json_string(builder,
          self_decrunch_sim_stop_reason_name_local(event->native_execution_stop_reason)) != 0) {
      return -1;
    }
  }
  if (event->native_execution_deferred &&
      json_builder_append(builder, ",\"native_execution_deferred\":true") != 0) {
    return -1;
  }
  if (event->entry_validation_attempted) {
    if (json_builder_appendf(builder,
        ",\"entry_validation_attempted\":true,\"entry_validation_valid\":%s,"
        "\"entry_validation_accepted_instructions\":%u,"
        "\"entry_validation_unsupported_instruction_demotes\":%u,"
        "\"entry_validation_required_instruction_failures\":%u,"
        "\"entry_validation_code_start_control_targets\":%u",
        event->entry_validation_valid ? "true" : "false",
        (unsigned)event->entry_validation_accepted_instructions,
        (unsigned)event->entry_validation_unsupported_instruction_demotes,
        (unsigned)event->entry_validation_required_instruction_failures,
        (unsigned)event->entry_validation_code_start_control_targets) != 0) {
      return -1;
    }
  }
  if (event->native_unpack_validated || event->native_execution_deferred || event->entry_validation_attempted) {
    if (json_builder_appendf(builder,
        ",\"compressed_source_consumed_section_offset\":%u,"
        "\"postpass_source_consumed_address\":%u,\"target_end_address\":%u,"
        "\"decompressed_size\":%u,\"decompressed_sha256\":",
        (unsigned)event->compressed_source_consumed_section_offset,
        (unsigned)event->postpass_source_consumed_address,
        (unsigned)event->target_end_address,
        (unsigned)event->decompressed_size) != 0 ||
        json_builder_append_json_string(builder, event->decompressed_sha256) != 0) {
      return -1;
    }
  }
  return json_builder_append(builder, "}");
}

static int append_self_decrunch_event_json(JsonBuilder *builder, const PlatformSelfDecrunchEvent *event) {
  char event_id[160];
  uint8_t status;
  uint8_t reason;
  uint8_t parent_remains_active;
  uint8_t payload_role;
  uint8_t payload_confidence;
  if (builder == NULL || event == NULL) return -1;
  make_self_decrunch_event_id_local(event_id, sizeof(event_id), event);
  status = event->has_simulated_output ? PLATFORM_DECOMPRESSION_STATUS_SIMULATED_OUTPUT_OBSERVED :
    PLATFORM_DECOMPRESSION_STATUS_NEEDS_SIMULATED_DECRUNCH;
  reason = self_decrunch_event_reason_id_local(event);
  parent_remains_active = event->parent_remains_active ? PLATFORM_DECOMPRESSION_PARENT_REMAINS_ACTIVE_TRUE :
    PLATFORM_DECOMPRESSION_PARENT_REMAINS_ACTIVE_FALSE;
  payload_role = (event->has_simulated_output && event->entry_validation_valid && !event->parent_remains_active) ?
    PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_PRIMARY_PROGRAM :
    PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_UNKNOWN_RUNTIME_PAYLOAD;
  payload_confidence = payload_role == PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_PRIMARY_PROGRAM ?
    PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_NATIVE_UNPACK_ENTRY_VALIDATED :
    PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_OBSERVED_OUTPUT_ONLY;
  if (json_builder_appendf(builder, "{\"event_kind_id\":%u,\"event_kind\":",
      (unsigned)PLATFORM_DECOMPRESSION_EVENT_KIND_DECOMPRESSION) != 0 ||
      json_builder_append_json_string(builder,
        decompression_event_kind_name_local(PLATFORM_DECOMPRESSION_EVENT_KIND_DECOMPRESSION)) != 0 ||
      json_builder_append(builder, ",\"event_id\":") != 0 ||
      json_builder_append_json_string(builder, event_id) != 0 ||
      json_builder_appendf(builder, ",\"status_id\":%u,\"status\":", (unsigned)status) != 0 ||
      json_builder_append_json_string(builder, decompression_status_name_local(status)) != 0 ||
      json_builder_appendf(builder, ",\"reason_id\":%u,\"reason\":", (unsigned)reason) != 0 ||
      json_builder_append_json_string(builder, decompression_reason_name_local(reason)) != 0 ||
      json_builder_appendf(builder,
        ",\"payload_role_id\":%u,\"payload_role\":",
        (unsigned)payload_role) != 0 ||
      json_builder_append_json_string(builder,
        decompression_payload_role_name_local(payload_role)) != 0 ||
      json_builder_appendf(builder,
        ",\"payload_role_confidence_id\":%u,\"payload_role_confidence\":",
        (unsigned)payload_confidence) != 0 ||
      json_builder_append_json_string(builder, decompression_payload_role_confidence_name_local(payload_confidence)) != 0 ||
      json_builder_appendf(builder, ",\"parent_remains_active_id\":%u,\"parent_remains_active\":",
        (unsigned)parent_remains_active) != 0 ||
      json_builder_append_json_string(builder,
        decompression_parent_remains_active_name_local(parent_remains_active)) != 0 ||
      json_builder_appendf(builder, ",\"source_kind_id\":%u,\"source_kind\":",
        (unsigned)PLATFORM_DECOMPRESSION_SOURCE_SELF_DECRUNCHER) != 0 ||
      json_builder_append_json_string(builder,
        decompression_source_kind_name_local(PLATFORM_DECOMPRESSION_SOURCE_SELF_DECRUNCHER)) != 0 ||
      json_builder_append(builder, ",\"provider_id\":\"m68k-sim-decrunch\","
        "\"codec_id\":\"unknown-self-decrunch\",\"codec_name\":\"Unidentified target-owned self-decruncher\",") != 0 ||
      json_builder_appendf(builder, "\"codec_support_id\":%u,\"codec_support\":",
        (unsigned)PLATFORM_DECOMPRESSION_CODEC_SUPPORT_SIMULATOR_REQUIRED) != 0 ||
      json_builder_append_json_string(builder,
        decompression_codec_support_name_local(PLATFORM_DECOMPRESSION_CODEC_SUPPORT_SIMULATOR_REQUIRED)) != 0) {
    return -1;
  }
  if (json_builder_appendf(builder,
    ",\"decompressor_code_section\":%u,\"decompressor_entry_offset\":%u,"
    "\"transfer_offset\":%u,\"load_address\":%u,\"entrypoint\":%u,"
    "\"observed_write_start\":%u,\"observed_write_end\":%u,\"observed_write_count\":%u",
    (unsigned)event->source_section_index, (unsigned)event->decompressor_entry_offset,
    (unsigned)event->transfer_offset, (unsigned)event->load_address, (unsigned)event->entrypoint,
    (unsigned)event->observed_write_start, (unsigned)event->observed_write_end,
    (unsigned)event->observed_write_count) != 0)
    return -1;
  if (event->simulation_attempted) {
    if (json_builder_appendf(builder,
        ",\"simulated_stop_reason\":%u,\"simulated_start_pc\":%u,\"simulated_stop_pc\":%u,"
        "\"simulated_step_count\":%u,\"simulated_write_count\":%u,"
        "\"simulated_stop_reason_name\":",
        (unsigned)event->simulated_stop_reason, (unsigned)event->simulated_start_pc,
        (unsigned)event->simulated_stop_pc, (unsigned)event->simulated_step_count,
        (unsigned)event->simulated_write_count) != 0 ||
        json_builder_append_json_string(builder,
          self_decrunch_sim_stop_reason_name_local(event->simulated_stop_reason)) != 0) {
      return -1;
    }
    if (event->simulated_diagnostic[0] != '\0') {
      if (json_builder_append(builder, ",\"simulated_diagnostic\":") != 0 ||
          json_builder_append_json_string(builder, event->simulated_diagnostic) != 0) {
        return -1;
      }
    }
  }
  if (event->has_simulated_output) {
    if (json_builder_appendf(builder,
        ",\"simulated_output_start\":%u,\"simulated_output_end\":%u,\"simulated_output_size\":%u",
        (unsigned)event->simulated_output_start, (unsigned)event->simulated_output_end,
        (unsigned)(event->simulated_output_end - event->simulated_output_start)) != 0)
      return -1;
    if (event->simulated_output_sha256[0] != '\0') {
      if (json_builder_append(builder, ",\"simulated_output_sha256\":") != 0 ||
          json_builder_append_json_string(builder, event->simulated_output_sha256) != 0)
        return -1;
    }
  }
  if (event->entry_validation_attempted) {
    if (json_builder_appendf(builder,
        ",\"entry_validation_attempted\":true,\"entry_validation_valid\":%s,"
        "\"entry_validation_accepted_instructions\":%u,"
        "\"entry_validation_unsupported_instruction_demotes\":%u,"
        "\"entry_validation_required_instruction_failures\":%u,"
        "\"entry_validation_code_start_control_targets\":%u",
        event->entry_validation_valid ? "true" : "false",
        (unsigned)event->entry_validation_accepted_instructions,
        (unsigned)event->entry_validation_unsupported_instruction_demotes,
        (unsigned)event->entry_validation_required_instruction_failures,
        (unsigned)event->entry_validation_code_start_control_targets) != 0) {
      return -1;
    }
  }
  return json_builder_append(builder, "}");
}

static int append_derived_decompression_suggestion_json(JsonBuilder *builder,
    const PlatformDecompressionIdentifyResult *result, const M68kRuntimeViewIR *runtime_copy_view) {
  char event_id[160];
  uint8_t reason = decompression_suggestion_reason_local(result, runtime_copy_view);
  uint8_t payload_role = decompression_suggestion_payload_role_local(result);
  uint8_t parent_remains_active = decompression_parent_remains_active_local(result);
  uint8_t status = result != NULL && result->has_decompressed_load_entry ?
    PLATFORM_DECOMPRESSION_STATUS_MATERIALIZABLE : PLATFORM_DECOMPRESSION_STATUS_NEEDS_RUNTIME_METADATA;
  make_decompression_event_id_local(event_id, sizeof(event_id), result);
  if (json_builder_appendf(builder, "{\"kind_id\":%u,\"kind\":",
      (unsigned)PLATFORM_DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD) != 0 ||
      json_builder_append_json_string(builder,
        derived_target_suggestion_kind_name_local(PLATFORM_DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD)) != 0 ||
      json_builder_appendf(builder, ",\"status_id\":%u,\"status\":", (unsigned)status) != 0 ||
      json_builder_append_json_string(builder, decompression_status_name_local(status)) != 0 ||
      json_builder_appendf(builder, ",\"event_kind_id\":%u,\"event_kind\":",
        (unsigned)PLATFORM_DECOMPRESSION_EVENT_KIND_DECOMPRESSION) != 0 ||
      json_builder_append_json_string(builder,
        decompression_event_kind_name_local(PLATFORM_DECOMPRESSION_EVENT_KIND_DECOMPRESSION)) != 0 ||
      json_builder_append(builder, ",\"event_id\":") != 0 ||
      json_builder_append_json_string(builder, event_id) != 0 ||
      json_builder_appendf(builder, ",\"reason_id\":%u,\"reason\":", (unsigned)reason) != 0 ||
      json_builder_append_json_string(builder, decompression_reason_name_local(reason)) != 0 ||
      json_builder_appendf(builder, ",\"payload_role_id\":%u,\"payload_role\":", (unsigned)payload_role) != 0 ||
      json_builder_append_json_string(builder, decompression_payload_role_name_local(payload_role)) != 0 ||
      json_builder_appendf(builder, ",\"payload_role_confidence_id\":%u,\"payload_role_confidence\":",
        (unsigned)PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_TOOL_INFERRED) != 0 ||
      json_builder_append_json_string(builder,
        decompression_payload_role_confidence_name_local(
          PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_TOOL_INFERRED)) != 0 ||
      json_builder_appendf(builder, ",\"parent_remains_active_id\":%u,\"parent_remains_active\":",
        (unsigned)parent_remains_active) != 0 ||
      json_builder_append_json_string(builder,
        decompression_parent_remains_active_name_local(parent_remains_active)) != 0)
    return -1;
  if (json_builder_appendf(builder,
      ",\"source_section\":%u,\"source_section_offset\":%u,\"packed_size\":%u,\"decompressed_size\":%u",
      (unsigned)result->source_section_index, (unsigned)result->source_section_offset,
      (unsigned)result->packed_size, (unsigned)result->decompressed_size) != 0)
    return -1;
  if (runtime_copy_view != NULL) {
    if (json_builder_appendf(builder,
        ",\"runtime_copy_address\":%u,\"runtime_copy_size\":%u,\"runtime_copy_kind\":%u,"
        "\"runtime_copy_conflicting\":%s",
        (unsigned)runtime_copy_view->runtime_address, (unsigned)runtime_copy_view->size,
        (unsigned)runtime_copy_view->kind,
        runtime_copy_view->kind == M68K_FACT_RUNTIME_RANGE_KIND_CONFLICTING_DISCOVERED_COPY ? "true" : "false") != 0)
      return -1;
  }
  if (result->has_decompressed_load_entry) {
    if (json_builder_appendf(builder,
        ",\"load_address\":%u,\"entrypoint\":%u,\"initial_control_target\":%u",
        (unsigned)result->decompressed_load_address, (unsigned)result->decompressed_entrypoint,
        (unsigned)result->decompressed_initial_control_target) != 0)
      return -1;
  }
  if (json_builder_append(builder, ",\"codec_id\":") != 0 ||
      json_builder_append_json_string(builder, result->codec_id) != 0 ||
      json_builder_append(builder, ",\"codec_name\":") != 0 ||
      json_builder_append_json_string(builder, result->codec_name) != 0 ||
      json_builder_appendf(builder, ",\"codec_support_id\":%u,\"codec_support\":",
        (unsigned)PLATFORM_DECOMPRESSION_CODEC_SUPPORT_EXTERNAL_PROVIDER) != 0 ||
      json_builder_append_json_string(builder,
        decompression_codec_support_name_local(PLATFORM_DECOMPRESSION_CODEC_SUPPORT_EXTERNAL_PROVIDER)) != 0 ||
      json_builder_append(builder, ",\"source_sha256\":") != 0 ||
      json_builder_append_json_string(builder, result->source_sha256) != 0 ||
      json_builder_append(builder, ",\"decompressed_sha256\":") != 0 ||
      json_builder_append_json_string(builder, result->decompressed_sha256) != 0)
    return -1;
  return json_builder_append(builder, "}");
}

static int append_decompression_event_json(JsonBuilder *builder,
    const PlatformDecompressionIdentifyResult *result, const M68kRuntimeViewIR *runtime_copy_view) {
  char event_id[160];
  uint8_t reason = decompression_suggestion_reason_local(result, runtime_copy_view);
  uint8_t payload_role = decompression_suggestion_payload_role_local(result);
  uint8_t parent_remains_active = decompression_parent_remains_active_local(result);
  uint8_t status = result != NULL && result->has_decompressed_load_entry ?
    PLATFORM_DECOMPRESSION_STATUS_MATERIALIZABLE : PLATFORM_DECOMPRESSION_STATUS_NEEDS_RUNTIME_METADATA;
  make_decompression_event_id_local(event_id, sizeof(event_id), result);
  if (json_builder_appendf(builder, "{\"event_kind_id\":%u,\"event_kind\":",
      (unsigned)PLATFORM_DECOMPRESSION_EVENT_KIND_DECOMPRESSION) != 0 ||
      json_builder_append_json_string(builder,
        decompression_event_kind_name_local(PLATFORM_DECOMPRESSION_EVENT_KIND_DECOMPRESSION)) != 0 ||
      json_builder_append(builder, ",\"event_id\":") != 0 ||
      json_builder_append_json_string(builder, event_id) != 0 ||
      json_builder_appendf(builder, ",\"status_id\":%u,\"status\":", (unsigned)status) != 0 ||
      json_builder_append_json_string(builder, decompression_status_name_local(status)) != 0 ||
      json_builder_appendf(builder, ",\"reason_id\":%u,\"reason\":", (unsigned)reason) != 0 ||
      json_builder_append_json_string(builder, decompression_reason_name_local(reason)) != 0 ||
      json_builder_appendf(builder, ",\"payload_role_id\":%u,\"payload_role\":", (unsigned)payload_role) != 0 ||
      json_builder_append_json_string(builder, decompression_payload_role_name_local(payload_role)) != 0 ||
      json_builder_appendf(builder, ",\"payload_role_confidence_id\":%u,\"payload_role_confidence\":",
        (unsigned)PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_TOOL_INFERRED) != 0 ||
      json_builder_append_json_string(builder,
        decompression_payload_role_confidence_name_local(
          PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_TOOL_INFERRED)) != 0 ||
      json_builder_appendf(builder, ",\"parent_remains_active_id\":%u,\"parent_remains_active\":",
        (unsigned)parent_remains_active) != 0 ||
      json_builder_append_json_string(builder,
        decompression_parent_remains_active_name_local(parent_remains_active)) != 0)
    return -1;
  if (json_builder_appendf(builder,
      ",\"source_kind_id\":%u,\"source_kind\":",
      (unsigned)PLATFORM_DECOMPRESSION_SOURCE_SECTION_RANGE) != 0 ||
      json_builder_append_json_string(builder,
        decompression_source_kind_name_local(PLATFORM_DECOMPRESSION_SOURCE_SECTION_RANGE)) != 0 ||
      json_builder_appendf(builder,
      ",\"source_section\":%u,\"source_section_offset\":%u,"
      "\"packed_size\":%u,\"decompressed_size\":%u",
      (unsigned)result->source_section_index, (unsigned)result->source_section_offset,
      (unsigned)result->packed_size, (unsigned)result->decompressed_size) != 0)
    return -1;
  if (runtime_copy_view != NULL) {
    if (json_builder_appendf(builder,
        ",\"runtime_copy_address\":%u,\"runtime_copy_size\":%u,\"runtime_copy_kind\":%u,"
        "\"runtime_copy_conflicting\":%s",
        (unsigned)runtime_copy_view->runtime_address, (unsigned)runtime_copy_view->size,
        (unsigned)runtime_copy_view->kind,
        runtime_copy_view->kind == M68K_FACT_RUNTIME_RANGE_KIND_CONFLICTING_DISCOVERED_COPY ? "true" : "false") != 0)
      return -1;
  }
  if (result->has_decompressed_load_entry) {
    if (json_builder_appendf(builder,
        ",\"load_address\":%u,\"entrypoint\":%u,\"initial_control_target\":%u",
        (unsigned)result->decompressed_load_address, (unsigned)result->decompressed_entrypoint,
        (unsigned)result->decompressed_initial_control_target) != 0)
      return -1;
  }
  if (json_builder_append(builder, ",\"provider_id\":") != 0 ||
      json_builder_append_json_string(builder, result->provider_id) != 0 ||
      json_builder_append(builder, ",\"codec_id\":") != 0 ||
      json_builder_append_json_string(builder, result->codec_id) != 0 ||
      json_builder_append(builder, ",\"codec_name\":") != 0 ||
      json_builder_append_json_string(builder, result->codec_name) != 0 ||
      json_builder_appendf(builder, ",\"codec_support_id\":%u,\"codec_support\":",
        (unsigned)PLATFORM_DECOMPRESSION_CODEC_SUPPORT_EXTERNAL_PROVIDER) != 0 ||
      json_builder_append_json_string(builder,
        decompression_codec_support_name_local(PLATFORM_DECOMPRESSION_CODEC_SUPPORT_EXTERNAL_PROVIDER)) != 0 ||
      json_builder_append(builder, ",\"source_sha256\":") != 0 ||
      json_builder_append_json_string(builder, result->source_sha256) != 0 ||
      json_builder_append(builder, ",\"decompressed_sha256\":") != 0 ||
      json_builder_append_json_string(builder, result->decompressed_sha256) != 0)
    return -1;
  return json_builder_append(builder, "}");
}

typedef struct PlatformDecompressionAnalysisTiming {
  double candidate_scan_seconds;
  double provider_probe_seconds;
  double self_decrunch_seconds;
  double recognized_unpacker_seconds;
  double event_json_seconds;
} PlatformDecompressionAnalysisTiming;

static int append_decompression_timing_json(JsonBuilder *builder,
    const PlatformDecompressionAnalysisTiming *timing) {
  if (builder == NULL || timing == NULL) return -1;
  return json_builder_appendf(builder,
    "{\"decompression_candidate_scan_seconds\":%.6f,"
    "\"decompression_provider_probe_seconds\":%.6f,"
    "\"decompression_self_decrunch_seconds\":%.6f,"
    "\"decompression_recognized_unpacker_seconds\":%.6f,"
    "\"decompression_event_json_seconds\":%.6f}",
    timing->candidate_scan_seconds,
    timing->provider_probe_seconds,
    timing->self_decrunch_seconds,
    timing->recognized_unpacker_seconds,
    timing->event_json_seconds);
}

static int append_object_decompression_analysis_json(JsonBuilder *builder, const M68kObject *object,
    const M68kSourceAnalysisIR *analysis, PlatformDecompressionAnalysisTiming *timing) {
  const size_t result_capacity = 32U;
  const size_t self_decrunch_event_capacity = 16U;
  const size_t recognized_unpacker_event_capacity = 16U;
  const size_t candidate_capacity = 16U;
  Arena *scratch_arena = NULL;
  PlatformDecompressionIdentifyResult *results = NULL;
  PlatformSelfDecrunchEvent *self_decrunch_events = NULL;
  PlatformRecognizedUnpackerEvent *recognized_unpacker_events = NULL;
  PlatformDecompressionCandidate *candidates = NULL;
  size_t result_count = 0U;
  size_t self_decrunch_event_count = 0U;
  size_t recognized_unpacker_event_count = 0U;
  size_t section_index;
  size_t emitted_event_count = 0U;
  clock_t phase_start;
  int rc = -1;
  if (object == NULL || analysis == NULL) return -1;
  if (timing != NULL) memset(timing, 0, sizeof(*timing));
  /* Keep JSON-pass scratch independent of analysis->arena. Decompression probes
     use marks and rewinds for temporary memory, while analysis->arena owns
     durable source-analysis records. */
  scratch_arena = arena_create(4096U);
  if (scratch_arena == NULL) return -1;
  results = (PlatformDecompressionIdentifyResult *)arena_calloc(scratch_arena, result_capacity, sizeof(*results));
  self_decrunch_events = (PlatformSelfDecrunchEvent *)arena_calloc(scratch_arena, self_decrunch_event_capacity,
    sizeof(*self_decrunch_events));
  recognized_unpacker_events = (PlatformRecognizedUnpackerEvent *)arena_calloc(scratch_arena,
    recognized_unpacker_event_capacity,
    sizeof(*recognized_unpacker_events));
  candidates = (PlatformDecompressionCandidate *)arena_calloc(scratch_arena, candidate_capacity, sizeof(*candidates));
  if (results == NULL || self_decrunch_events == NULL || recognized_unpacker_events == NULL ||
      candidates == NULL) {
    goto cleanup;
  }
  for (section_index = 0U; section_index < object->section_count; ++section_index) {
    const M68kSection *section = &object->sections[section_index];
    const M68kSectionAnalysisIR *section_analysis;
    size_t candidate_count, candidate_index;
    if (section->data == NULL || section->data_size == 0U || section_index >= analysis->section_count) continue;
    section_analysis = &analysis->sections[section_index];
    memset(candidates, 0, candidate_capacity * sizeof(*candidates));
    phase_start = clock();
    candidate_count = platform_decompression_find_candidates_in_buffer("ancient-cli", section->data,
      section->data_size, candidates, candidate_capacity);
    if (timing != NULL) timing->candidate_scan_seconds += elapsed_seconds(phase_start, clock());
    if (candidate_count > candidate_capacity)
      candidate_count = candidate_capacity;
    for (candidate_index = 0U; candidate_index < candidate_count && result_count < result_capacity;
        ++candidate_index) {
      const PlatformDecompressionCandidate *candidate = &candidates[candidate_index];
      PlatformDecompressionIdentifyResult result;
      char output_path[512];
      char error[256];
      error[0] = '\0';
      if (!automatic_decompression_candidate_is_useful(candidate)) continue;
      if (analysis_range_overlaps_accepted_code(section_analysis, candidate->offset, candidate->packed_size))
        continue;
      if (init_scanned_provider_candidate_result_local(&result, section, section_index, candidate) == 0 &&
          promote_provider_payload_from_wrapper_static_local(object, analysis, &result, scratch_arena)) {
        results[result_count++] = result;
        continue;
      }
      if (make_temp_output_path(output_path, sizeof(output_path)) != 0) goto cleanup;
      phase_start = clock();
      if (platform_decompression_decompress_buffer_range("ancient-cli", "", section->data, section->data_size,
          candidate->offset, candidate->packed_size, output_path, &result, error, sizeof(error)) != 0) {
        if (timing != NULL) timing->provider_probe_seconds += elapsed_seconds(phase_start, clock());
        remove(output_path);
        continue;
      }
      if (timing != NULL) timing->provider_probe_seconds += elapsed_seconds(phase_start, clock());
      if (!result.found || !result.decompressed) {
        remove(output_path);
        continue;
      }
      result.has_source_section = 1U;
      result.source_section_index = (uint32_t)section_index;
      result.source_section_offset = candidate->offset;
      result.source_offset = candidate->offset;
      {
        const M68kRuntimeViewIR *runtime_copy_view =
          find_decompression_runtime_copy_view(analysis, &result);
        uint32_t entrypoint = 0U;
        uint32_t initial_control_target = 0U;
        if (runtime_copy_view != NULL &&
            infer_decompressed_load_entry_from_initial_control_local(output_path, analysis->policy.max_cpu,
              runtime_copy_view->runtime_address, result.decompressed_size, &entrypoint,
              &initial_control_target)) {
          result.has_decompressed_load_entry = 1U;
          result.decompressed_load_address = runtime_copy_view->runtime_address;
          result.decompressed_entrypoint = entrypoint;
          result.decompressed_initial_control_target = initial_control_target;
        }
        if (!result.has_decompressed_load_entry) {
          (void)promote_provider_payload_from_wrapper_simulation_local(object, analysis, output_path, &result,
            scratch_arena);
        }
      }
      result.decompressed_path[0] = '\0';
      results[result_count++] = result;
      remove(output_path);
    }
  }
  phase_start = clock();
  if (collect_self_decrunch_events_local(object, analysis, self_decrunch_events,
      self_decrunch_event_capacity, &self_decrunch_event_count,
      NULL, NULL, NULL, NULL, scratch_arena) != 0) {
    goto cleanup;
  }
  if (timing != NULL) timing->self_decrunch_seconds += elapsed_seconds(phase_start, clock());
  phase_start = clock();
  if (collect_recognized_unpacker_events_local(object, analysis, recognized_unpacker_events,
      recognized_unpacker_event_capacity,
      &recognized_unpacker_event_count, NULL, NULL, NULL, NULL, scratch_arena) != 0) {
    goto cleanup;
  }
  if (timing != NULL) timing->recognized_unpacker_seconds += elapsed_seconds(phase_start, clock());
  phase_start = clock();
  if (json_builder_append(builder, ",\"packed_payloads\":[") != 0) goto cleanup;
  for (section_index = 0U; section_index < result_count; ++section_index) {
    if (section_index != 0U && json_builder_append(builder, ",") != 0) goto cleanup;
    if (platform_decompression_append_result_json(builder, &results[section_index]) != 0) goto cleanup;
  }
  if (json_builder_append(builder, "],\"derived_target_suggestions\":[") != 0) goto cleanup;
  for (section_index = 0U; section_index < result_count; ++section_index) {
    if (section_index != 0U && json_builder_append(builder, ",") != 0) goto cleanup;
    if (append_derived_decompression_suggestion_json(builder, &results[section_index],
        find_decompression_runtime_copy_view(analysis, &results[section_index])) != 0) goto cleanup;
  }
  if (json_builder_append(builder, "],\"decompression_events\":[") != 0) goto cleanup;
  for (section_index = 0U; section_index < result_count; ++section_index) {
    if (emitted_event_count != 0U && json_builder_append(builder, ",") != 0) goto cleanup;
    if (append_decompression_event_json(builder, &results[section_index],
        find_decompression_runtime_copy_view(analysis, &results[section_index])) != 0) goto cleanup;
    ++emitted_event_count;
  }
  for (section_index = 0U; section_index < recognized_unpacker_event_count; ++section_index) {
    if (emitted_event_count != 0U && json_builder_append(builder, ",") != 0) goto cleanup;
    if (append_recognized_unpacker_event_json(builder, &recognized_unpacker_events[section_index]) != 0)
      goto cleanup;
    ++emitted_event_count;
  }
  for (section_index = 0U; section_index < self_decrunch_event_count; ++section_index) {
    if (self_decrunch_event_matches_materialized_provider_local(results, result_count,
        &self_decrunch_events[section_index]))
      continue;
    if (self_decrunch_event_matches_native_recognized_unpacker_local(recognized_unpacker_events,
        recognized_unpacker_event_count, &self_decrunch_events[section_index]))
      continue;
    if (emitted_event_count != 0U && json_builder_append(builder, ",") != 0) goto cleanup;
    if (append_self_decrunch_event_json(builder, &self_decrunch_events[section_index]) != 0) goto cleanup;
    ++emitted_event_count;
  }
  if (json_builder_append(builder, "]") != 0) goto cleanup;
  if (timing != NULL) timing->event_json_seconds += elapsed_seconds(phase_start, clock());
  rc = 0;

cleanup:
  arena_destroy(scratch_arena);
  return rc;
}

static int append_analysis_executable_ranges_json(JsonBuilder *builder, const char *backend_name,
    const M68kObject *object);

static int append_analysis_json_with_decompression_profile(JsonBuilder *builder, const char *base_json,
    const char *backend_name, const M68kObject *object, const M68kSourceAnalysisIR *analysis,
    const M68kRenderPlan *source_plan, const M68kFactsV2Profile *profile,
    PlatformDecompressionAnalysisTiming *out_decompression_timing) {
  PlatformDecompressionAnalysisTiming decompression_timing;
  size_t base_len;
  if (builder == NULL || base_json == NULL || backend_name == NULL || object == NULL || analysis == NULL) return -1;
  memset(&decompression_timing, 0, sizeof(decompression_timing));
  base_len = strlen(base_json);
  if (base_len == 0U || base_json[base_len - 1U] != '}') return -1;
  if (json_builder_appendf(builder, "%.*s", (int)(base_len - 1U), base_json) != 0)
    return -1;
  if (append_object_decompression_analysis_json(builder, object, analysis, &decompression_timing) != 0)
    return -1;
  if (out_decompression_timing != NULL) *out_decompression_timing = decompression_timing;
  if (append_analysis_executable_ranges_json(builder, backend_name, object) != 0)
    return -1;
  if (append_analysis_restored_source_model_json(builder, backend_name, object, source_plan) != 0)
    return -1;
  if (strcmp(backend_name, "macos-code") == 0) {
    const PlatformMacosA5WorldLayout *a5_layout = platform_macos_object_a5_world_layout(object);
    if (json_builder_append(builder, ",\"macos_a5_world_layout\":") != 0) return -1;
    if (a5_layout == NULL) {
      if (json_builder_append(builder, "null") != 0) return -1;
    } else if (json_builder_appendf(builder,
          "{\"present\":true,\"code0_resource_id\":%d,\"above_a5_size\":%u,\"below_a5_size\":%u,"
          "\"jump_table_offset_from_a5\":%u,\"jump_table_length\":%u,"
          "\"regions\":[{\"kind\":\"below_a5_globals\",\"base_register\":\"a5\",\"start\":%d,\"size\":%u},"
          "{\"kind\":\"jump_table\",\"base_register\":\"a5\",\"start\":%u,\"end\":%u,\"size\":%u},"
          "{\"kind\":\"above_a5_globals\",\"base_register\":\"a5\",\"start\":%u,\"size\":%u}]}",
          (int)a5_layout->code0_resource_id, (unsigned)a5_layout->above_a5_size,
          (unsigned)a5_layout->below_a5_size, (unsigned)a5_layout->jump_table_offset_from_a5,
          (unsigned)a5_layout->jump_table_length, (int)a5_layout->negative_global_start,
          (unsigned)a5_layout->negative_global_size, (unsigned)a5_layout->jump_table_start,
          (unsigned)a5_layout->jump_table_end, (unsigned)a5_layout->jump_table_length,
          (unsigned)a5_layout->positive_global_start, (unsigned)a5_layout->positive_global_size) != 0) {
      return -1;
    }
  }
  if (profile != NULL) {
    if (json_builder_append(builder,
        ",\"profile\":{\"generation\":\"facts_v2_analysis\",\"analysis_backend\":\"facts_v2\",\"facts_v2\":") != 0 ||
        json_builder_append_facts_v2_profile(builder, profile) != 0 ||
        json_builder_append(builder, ",\"decompression\":") != 0 ||
        append_decompression_timing_json(builder, &decompression_timing) != 0 ||
        json_builder_append(builder, "}") != 0)
      return -1;
  }
  return json_builder_append(builder, "}");
}

static const char *restored_source_ownership_role_name(RestoredSourceOwnershipRole role) {
  switch (role) {
  case RESTORED_SOURCE_OWNERSHIP_CODE:
    return "code";
  case RESTORED_SOURCE_OWNERSHIP_DATA:
    return "data";
  case RESTORED_SOURCE_OWNERSHIP_BSS:
    return "bss";
  case RESTORED_SOURCE_OWNERSHIP_METADATA:
    return "metadata";
  case RESTORED_SOURCE_OWNERSHIP_RELOCATION_FIXUP:
    return "relocation_fixup";
  case RESTORED_SOURCE_OWNERSHIP_PADDING:
    return "padding";
  case RESTORED_SOURCE_OWNERSHIP_PLACEHOLDER:
    return "placeholder";
  case RESTORED_SOURCE_OWNERSHIP_CANDIDATE_CODE:
    return "candidate_code";
  case RESTORED_SOURCE_OWNERSHIP_UNKNOWN:
  default:
    return "unknown";
  }
}

static int restored_source_model_add_ownership_range(RestoredSourceModel *model, RestoredSourceOwnershipRole role,
    const char *byte_space, const char *platform, const char *source_kind, uint32_t section_index,
    uint32_t start, uint32_t size, uint32_t stored_offset, uint8_t has_stored_offset, uint32_t stored_size,
    const char *fact_id, const char *fact_status, const char *parser_use, const char *provenance,
    const char *reason) {
  RestoredSourceOwnershipRange *range;
  if (model == NULL || byte_space == NULL || platform == NULL || source_kind == NULL || fact_id == NULL ||
      fact_status == NULL || parser_use == NULL || provenance == NULL ||
      model->ownership_range_count >= RESTORED_SOURCE_MODEL_MAX_OWNERSHIP_RANGES) {
    return -1;
  }
  range = &model->ownership_ranges[model->ownership_range_count++];
  range->role = role;
  range->byte_space = byte_space;
  range->platform = platform;
  range->source_kind = source_kind;
  range->section_index = section_index;
  range->start = start;
  range->size = size;
  range->stored_offset = stored_offset;
  range->has_stored_offset = has_stored_offset;
  range->stored_size = stored_size;
  range->fact.fact_id = fact_id;
  range->fact.fact_status = fact_status;
  range->fact.parser_use = parser_use;
  range->provenance = provenance;
  range->reason = reason != NULL ? reason : "";
  return 0;
}

static int restored_source_model_role_for_section(const char *backend_name, M68kSectionKind kind,
    RestoredSourceOwnershipRole *out_role, const char **out_fact_id, const char **out_fact_status,
    const char **out_parser_use) {
  if (backend_name == NULL || out_role == NULL || out_fact_id == NULL || out_fact_status == NULL ||
      out_parser_use == NULL) {
    return 0;
  }
  if (strcmp(backend_name, "amiga-hunk") == 0) {
    if (kind == M68K_SECTION_CODE) {
      *out_role = RESTORED_SOURCE_OWNERSHIP_CODE;
      *out_fact_id = PLATFORM_EXECUTABLE_FORMAT_FACT_AMIGA_HUNK_CODE_DATA_BSS_SECTIONS_ACCEPTED;
    } else if (kind == M68K_SECTION_DATA) {
      *out_role = RESTORED_SOURCE_OWNERSHIP_DATA;
      *out_fact_id = PLATFORM_EXECUTABLE_FORMAT_FACT_AMIGA_HUNK_CODE_DATA_BSS_SECTIONS_ACCEPTED;
    } else if (kind == M68K_SECTION_BSS) {
      *out_role = RESTORED_SOURCE_OWNERSHIP_BSS;
      *out_fact_id = PLATFORM_EXECUTABLE_FORMAT_FACT_AMIGA_HUNK_BSS_SIZE_ONLY_ACCEPTED;
    } else {
      return 0;
    }
    *out_fact_status = "parser_asserted";
    *out_parser_use = "accepted_parser_output";
    return 1;
  }
  if (strcmp(backend_name, "atari-st") == 0) {
    if (kind == M68K_SECTION_CODE) {
      *out_role = RESTORED_SOURCE_OWNERSHIP_CODE;
      *out_fact_id = PLATFORM_EXECUTABLE_FORMAT_FACT_ATARI_ST_PRG_TEXT_DATA_LOADED_IMAGE_ACCEPTED;
      *out_fact_status = "parser_asserted";
      *out_parser_use = "accepted_parser_output";
    } else if (kind == M68K_SECTION_DATA) {
      *out_role = RESTORED_SOURCE_OWNERSHIP_DATA;
      *out_fact_id = PLATFORM_EXECUTABLE_FORMAT_FACT_ATARI_ST_PRG_TEXT_DATA_LOADED_IMAGE_ACCEPTED;
      *out_fact_status = "parser_asserted";
      *out_parser_use = "accepted_parser_output";
    } else if (kind == M68K_SECTION_BSS) {
      *out_role = RESTORED_SOURCE_OWNERSHIP_BSS;
      *out_fact_id = PLATFORM_EXECUTABLE_FORMAT_FACT_ATARI_ST_PRG_BSS_HEADER_ONLY_CANDIDATE;
      *out_fact_status = "candidate";
      *out_parser_use = "candidate_only";
    } else {
      return 0;
    }
    return 1;
  }
  return 0;
}

static int restored_source_model_build_for_object(const char *backend_name, const M68kObject *object,
    RestoredSourceModel *model) {
  size_t index;
  uint32_t load_offset = 0U;
  uint32_t stored_offset = 0U;
  if (backend_name == NULL || object == NULL || model == NULL ||
      object->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) {
    return 0;
  }
  memset(model, 0, sizeof(*model));
  model->model = "restored_source_model_v1";
  model->platform = backend_name;
  model->source_kind = backend_name;
  model->round_trip_required = (strcmp(backend_name, "macos-code") == 0) ? 0U : 1U;
  if (strcmp(backend_name, "macos-code") == 0) {
    if (object->section_count == 0U) return 0;
    return restored_source_model_add_ownership_range(model, RESTORED_SOURCE_OWNERSHIP_CANDIDATE_CODE,
      "selected_code_bytes", "macos", "macos_code_resource", 0U, 0U, object->sections[0].size, 0U, 1U,
      object->sections[0].data_size, PLATFORM_EXECUTABLE_FORMAT_FACT_MACOS_CODE_RESOURCE_MOVEA_STACK_A0_BOUNDARY_CANDIDATE,
      "candidate", "candidate_only", "platform_file_facts_v2_listing_artifact_macos_code_buffer_create",
      "selected Mac CODE bytes remain candidate because byte-entry evidence is not accepted");
  }
  if (strcmp(backend_name, "amiga-hunk") != 0 && strcmp(backend_name, "atari-st") != 0) return 0;
  for (index = 0U; index < object->section_count; ++index) {
    const M68kSection *section = &object->sections[index];
    RestoredSourceOwnershipRole role;
    const char *fact_id = NULL;
    const char *fact_status = NULL;
    const char *parser_use = NULL;
    uint8_t has_stored_offset = section->data_size != 0U ? 1U : 0U;
    if (!restored_source_model_role_for_section(backend_name, section->kind, &role, &fact_id, &fact_status,
        &parser_use))
      return -1;
    if (restored_source_model_add_ownership_range(model, role, "loaded_image", backend_name, backend_name,
        (uint32_t)index, load_offset, section->size, stored_offset, has_stored_offset, section->data_size,
        fact_id, fact_status, parser_use, "platform_executable_summary_v1", "") != 0)
      return -1;
    load_offset += section->size;
    stored_offset += section->data_size;
  }
  return 0;
}

static int append_restored_source_model_json(JsonBuilder *builder, const RestoredSourceModel *model) {
  size_t index;
  if (builder == NULL || model == NULL || model->ownership_range_count == 0U) return 0;
  if (json_builder_append(builder, ",\"restored_source_model\":\"restored_source_model_v1\","
        "\"round_trip_required\":") != 0 ||
      json_builder_append(builder, model->round_trip_required ? "true" : "false") != 0 ||
      json_builder_append(builder, ",\"source_ownership_ranges\":[") != 0) {
    return -1;
  }
  for (index = 0U; index < model->ownership_range_count; ++index) {
    const RestoredSourceOwnershipRange *range = &model->ownership_ranges[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"role\":") != 0 ||
        json_builder_append_json_string(builder, restored_source_ownership_role_name(range->role)) != 0 ||
        json_builder_append(builder, ",\"byte_space\":") != 0 ||
        json_builder_append_json_string(builder, range->byte_space) != 0 ||
        json_builder_append(builder, ",\"platform\":") != 0 ||
        json_builder_append_json_string(builder, range->platform) != 0 ||
        json_builder_append(builder, ",\"source_kind\":") != 0 ||
        json_builder_append_json_string(builder, range->source_kind) != 0 ||
        json_builder_appendf(builder, ",\"section_index\":%u,\"start\":%u,\"size\":%u,\"stored_offset\":",
          (unsigned)range->section_index, (unsigned)range->start, (unsigned)range->size) != 0)
      return -1;
    if (range->has_stored_offset) {
      if (json_builder_appendf(builder, "%u", (unsigned)range->stored_offset) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) return -1;
    if (json_builder_appendf(builder, ",\"stored_size\":%u,\"fact_id\":", (unsigned)range->stored_size) != 0 ||
        json_builder_append_json_string(builder, range->fact.fact_id) != 0 ||
        json_builder_append(builder, ",\"fact_status\":") != 0 ||
        json_builder_append_json_string(builder, range->fact.fact_status) != 0 ||
        json_builder_append(builder, ",\"parser_use\":") != 0 ||
        json_builder_append_json_string(builder, range->fact.parser_use) != 0 ||
        json_builder_append(builder, ",\"provenance\":") != 0 ||
        json_builder_append_json_string(builder, range->provenance) != 0)
      return -1;
    if (range->reason != NULL && range->reason[0] != '\0') {
      if (json_builder_append(builder, ",\"reason\":") != 0 ||
          json_builder_append_json_string(builder, range->reason) != 0)
        return -1;
    }
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  return json_builder_append(builder, "]");
}

static const RestoredSourceOwnershipRange *restored_source_model_find_range_for_loaded_offset(
    const RestoredSourceModel *model, uint32_t offset) {
  size_t index;
  if (model == NULL) return NULL;
  for (index = 0U; index < model->ownership_range_count; ++index) {
    const RestoredSourceOwnershipRange *range = &model->ownership_ranges[index];
    if (offset >= range->start && offset - range->start < range->size) return range;
  }
  return NULL;
}

static uint32_t restored_source_loaded_offset_for_row(const M68kObject *object, const M68kRenderPlanRow *row) {
  size_t index;
  uint32_t offset = 0U;
  if (object == NULL || row == NULL) return 0U;
  for (index = 0U; index < object->section_count && index < row->source_section_index; ++index)
    offset += object->sections[index].size;
  return offset + row->source_offset;
}

static int restored_source_ownership_role_allows_instruction(RestoredSourceOwnershipRole role) {
  return role == RESTORED_SOURCE_OWNERSHIP_CODE || role == RESTORED_SOURCE_OWNERSHIP_CANDIDATE_CODE;
}

static void restored_source_coverage_verify(const RestoredSourceModel *model, const M68kObject *object,
    const M68kRenderPlan *source_plan, RestoredSourceCoverageVerifier *verifier) {
  size_t index;
  uint32_t previous_end = 0U;
  uint8_t has_previous = 0U;
  if (verifier == NULL) return;
  memset(verifier, 0, sizeof(*verifier));
  verifier->ok = 1U;
  if (model == NULL || model->ownership_range_count == 0U) return;
  for (index = 0U; index < model->ownership_range_count; ++index) {
    const RestoredSourceOwnershipRange *range = &model->ownership_ranges[index];
    uint32_t end = range->start + range->size;
    if (!has_previous && range->start != 0U) {
      ++verifier->gap_count;
    } else if (has_previous) {
      if (range->start > previous_end) ++verifier->gap_count;
      if (range->start < previous_end) ++verifier->overlap_count;
    }
    if (range->role == RESTORED_SOURCE_OWNERSHIP_UNKNOWN &&
        (range->size == 0U || range->fact.fact_status == NULL || range->fact.fact_status[0] == '\0' ||
         range->reason == NULL || range->reason[0] == '\0' ||
         range->provenance == NULL || range->provenance[0] == '\0')) {
      ++verifier->explicit_unknown_missing_detail_count;
    }
    previous_end = end;
    has_previous = 1U;
  }
  if (object != NULL && has_previous) {
    uint32_t object_size = 0U;
    for (index = 0U; index < object->section_count; ++index) object_size += object->sections[index].size;
    if (previous_end < object_size) ++verifier->gap_count;
  }
  if (source_plan != NULL && object != NULL) {
    for (index = 0U; index < source_plan->row_count; ++index) {
      const M68kRenderPlanRow *row = &source_plan->rows[index];
      const RestoredSourceOwnershipRange *range;
      if (row->kind != M68K_RENDER_PLAN_ROW_INSTRUCTION || !row->has_source_range) continue;
      range = restored_source_model_find_range_for_loaded_offset(model,
        restored_source_loaded_offset_for_row(object, row));
      if (range == NULL || !restored_source_ownership_role_allows_instruction(range->role))
        ++verifier->invalid_instruction_ownership_count;
    }
  }
  if (verifier->gap_count != 0U || verifier->overlap_count != 0U ||
      verifier->invalid_instruction_ownership_count != 0U ||
      verifier->explicit_unknown_missing_detail_count != 0U) {
    verifier->ok = 0U;
  }
}

static int append_restored_source_coverage_verifier_json(JsonBuilder *builder,
    const RestoredSourceCoverageVerifier *verifier) {
  if (builder == NULL || verifier == NULL) return -1;
  return json_builder_appendf(builder,
    ",\"source_coverage_verifier\":{\"ok\":%s,\"gap_count\":%u,\"overlap_count\":%u,"
    "\"invalid_instruction_ownership_count\":%u,\"explicit_unknown_missing_detail_count\":%u}",
    verifier->ok ? "true" : "false", (unsigned)verifier->gap_count, (unsigned)verifier->overlap_count,
    (unsigned)verifier->invalid_instruction_ownership_count,
    (unsigned)verifier->explicit_unknown_missing_detail_count);
}

static uint32_t restored_source_fixup_width_bytes(const M68kFixup *fixup) {
  if (fixup == NULL) return 0U;
  switch (fixup->width) {
  case M68K_FIXUP_WIDTH_8:
    return 1U;
  case M68K_FIXUP_WIDTH_16:
    return 2U;
  case M68K_FIXUP_WIDTH_32:
    return 4U;
  default:
    return 0U;
  }
}

static uint32_t restored_source_section_loaded_base(const M68kObject *object, size_t section_index) {
  size_t index;
  uint32_t base = 0U;
  if (object == NULL) return 0U;
  for (index = 0U; index < object->section_count && index < section_index; ++index)
    base += object->sections[index].size;
  return base;
}

static uint32_t restored_source_model_ownership_index_for_loaded_offset(const RestoredSourceModel *model,
    uint32_t offset) {
  size_t index;
  if (model == NULL) return UINT32_MAX;
  for (index = 0U; index < model->ownership_range_count; ++index) {
    const RestoredSourceOwnershipRange *range = &model->ownership_ranges[index];
    if (offset >= range->start && offset - range->start < range->size) return (uint32_t)index;
  }
  return UINT32_MAX;
}

static const char *restored_source_reference_fact_id_for_backend(const char *backend_name) {
  if (backend_name == NULL) return "";
  if (strcmp(backend_name, "amiga-hunk") == 0)
    return PLATFORM_EXECUTABLE_FORMAT_FACT_AMIGA_HUNK_RELOCATION_RECORDS_CANDIDATE;
  if (strcmp(backend_name, "atari-st") == 0)
    return PLATFORM_EXECUTABLE_FORMAT_FACT_ATARI_ST_PRG_RELOCATION_STREAM_CANDIDATE;
  if (strcmp(backend_name, "macos-code") == 0)
    return PLATFORM_EXECUTABLE_FORMAT_FACT_MACOS_SEGMENT_LOADER_RELOCATION_FIXUPS_DEFERRED;
  return "";
}

static int append_source_reference_record_json(JsonBuilder *builder, const RestoredSourceReferenceRecord *record) {
  if (builder == NULL || record == NULL) return -1;
  if (json_builder_append(builder, "{\"kind\":") != 0 ||
      json_builder_append_json_string(builder, record->kind) != 0 ||
      json_builder_appendf(builder,
        ",\"ownership_range_index\":%u,\"source_section_index\":%u,\"source_offset\":%u,\"size\":%u,"
        "\"target_section_index\":",
        (unsigned)record->ownership_range_index, (unsigned)record->source_section_index,
        (unsigned)record->source_offset, (unsigned)record->size) != 0)
    return -1;
  if (record->has_target_section) {
    if (json_builder_appendf(builder, "%u", (unsigned)record->target_section_index) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  if (json_builder_appendf(builder, ",\"target_offset\":%u,\"addend\":%d,\"row_id\":",
      (unsigned)record->target_offset, (int)record->addend) != 0)
    return -1;
  if (record->has_row_id) {
    if (json_builder_appendf(builder, "%u", (unsigned)record->row_id) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  return json_builder_append(builder, ",\"target\":") != 0 ||
      json_builder_append_json_string(builder, record->target) != 0 ||
      json_builder_append(builder, ",\"status\":") != 0 ||
      json_builder_append_json_string(builder, record->status) != 0 ||
      json_builder_append(builder, ",\"fact_id\":") != 0 ||
      json_builder_append_json_string(builder, record->fact.fact_id) != 0 ||
      json_builder_append(builder, ",\"fact_status\":") != 0 ||
      json_builder_append_json_string(builder, record->fact.fact_status) != 0 ||
      json_builder_append(builder, ",\"parser_use\":") != 0 ||
      json_builder_append_json_string(builder, record->fact.parser_use) != 0 ||
      json_builder_append(builder, ",\"provenance\":") != 0 ||
      json_builder_append_json_string(builder, record->provenance) != 0 ||
      json_builder_append(builder, "}") != 0 ? -1 : 0;
}

static int append_source_reference_records_json(JsonBuilder *builder, const char *backend_name,
    const M68kObject *object, const M68kRenderPlan *source_plan, const RestoredSourceModel *model) {
  size_t index;
  int emitted = 0;
  const char *fact_id = restored_source_reference_fact_id_for_backend(backend_name);
  if (builder == NULL || backend_name == NULL || object == NULL || model == NULL ||
      model->ownership_range_count == 0U || source_plan == NULL) {
    return 0;
  }
  if (json_builder_append(builder, ",\"source_reference_records\":[") != 0) return -1;
  if (strcmp(backend_name, "macos-code") == 0) {
    RestoredSourceReferenceRecord record;
    memset(&record, 0, sizeof(record));
    record.kind = "segment_loader_fixup_placeholder";
    record.ownership_range_index = 0U;
    record.source_section_index = 0U;
    record.source_offset = 0U;
    record.size = 0U;
    record.fact.fact_id = fact_id;
    record.fact.fact_status = "deferred";
    record.fact.parser_use = "deferred_only";
    record.status = "deferred";
    record.provenance = "platform_executable_summary_v1";
    record.target = "unresolved_segment_loader_fixup";
    if (append_source_reference_record_json(builder, &record) != 0) return -1;
    emitted = 1;
  }
  for (index = 0U; index < object->fixup_count; ++index) {
    const M68kFixup *fixup = &object->fixups[index];
    uint32_t loaded_offset = restored_source_section_loaded_base(object, fixup->section_index) + fixup->offset;
    uint32_t ownership_index = restored_source_model_ownership_index_for_loaded_offset(model, loaded_offset);
    RestoredSourceReferenceRecord record;
    const M68kRenderPlanRow *row = NULL;
    if (ownership_index == UINT32_MAX) continue;
    memset(&record, 0, sizeof(record));
    record.kind = "relocation_fixup";
    record.ownership_range_index = ownership_index;
    record.source_section_index = (uint32_t)fixup->section_index;
    record.source_offset = fixup->offset;
    record.size = restored_source_fixup_width_bytes(fixup);
    record.has_target_section = fixup->has_target_section ? 1U : 0U;
    record.target_section_index = (uint32_t)fixup->target_section_index;
    record.target_offset = (uint32_t)fixup->addend;
    record.addend = fixup->addend;
    if (source_plan != NULL &&
        (row = m68k_render_plan_find_row_for_source_offset(source_plan, (uint32_t)fixup->section_index,
           fixup->offset)) != NULL) {
      record.has_row_id = 1U;
      record.row_id = row->id;
    }
    record.fact.fact_id = fact_id;
    record.fact.fact_status = "candidate";
    record.fact.parser_use = "candidate_only";
    record.status = "candidate";
    record.provenance = "M68kObject.fixups";
    record.target = fixup->has_target_section ? "section_offset" : "external_or_unresolved";
    if (emitted++ != 0 && json_builder_append(builder, ",") != 0) return -1;
    if (append_source_reference_record_json(builder, &record) != 0) return -1;
  }
  return json_builder_append(builder, "]");
}

static int append_analysis_restored_source_model_json(JsonBuilder *builder, const char *backend_name,
    const M68kObject *object, const M68kRenderPlan *source_plan) {
  RestoredSourceModel model;
  RestoredSourceCoverageVerifier verifier;
  int status = restored_source_model_build_for_object(backend_name, object, &model);
  if (status != 0) return -1;
  if (append_restored_source_model_json(builder, &model) != 0) return -1;
  if (model.ownership_range_count == 0U) return 0;
  restored_source_coverage_verify(&model, object, source_plan, &verifier);
  if (append_restored_source_coverage_verifier_json(builder, &verifier) != 0) return -1;
  return append_source_reference_records_json(builder, backend_name, object, source_plan, &model);
}

static void make_policy_symbol_label_local(char *out, size_t out_size, const char *symbol) {
  size_t used = 0U;
  char previous = '\0';
  const char *cursor;
  int all_caps = 1;
  if (out == NULL || out_size == 0U) return;
  out[0] = '\0';
  if (symbol == NULL) return;
  for (cursor = symbol; *cursor != '\0'; ++cursor) {
    if (*cursor >= 'a' && *cursor <= 'z') {
      all_caps = 0;
      break;
    }
  }
  for (cursor = symbol; *cursor != '\0'; ++cursor) {
    char ch = *cursor;
    int is_upper = ch >= 'A' && ch <= 'Z';
    int is_lower = ch >= 'a' && ch <= 'z';
    int is_digit = ch >= '0' && ch <= '9';
    int previous_is_lower_or_digit = (previous >= 'a' && previous <= 'z') || (previous >= '0' && previous <= '9');
    if (!all_caps && is_upper && previous_is_lower_or_digit && used != 0U && out[used - 1U] != '_') {
      if (used + 1U >= out_size) break;
      out[used++] = '_';
    }
    if (!is_upper && !is_lower && !is_digit) {
      if (used != 0U && out[used - 1U] != '_' && used + 1U < out_size) out[used++] = '_';
      previous = '_';
      continue;
    }
    if (used + 1U >= out_size) break;
    out[used++] = is_upper ? (char)(ch - 'A' + 'a') : ch;
    previous = out[used - 1U];
  }
  while (used != 0U && out[used - 1U] == '_') --used;
  out[used] = '\0';
}

static void make_library_stem_label_local(char *out, size_t out_size, const char *library_name) {
  char stem[64];
  size_t stem_len;
  if (out == NULL || out_size == 0U) return;
  out[0] = '\0';
  if (library_name == NULL || library_name[0] == '\0') return;
  snprintf(stem, sizeof(stem), "%s", library_name);
  stem_len = strlen(stem);
  if (stem_len > 8U && strcmp(stem + stem_len - 8U, ".library") == 0) stem[stem_len - 8U] = '\0';
  make_policy_symbol_label_local(out, out_size, stem);
}

static int policy_add_named_label_domain_local(M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset,
    const char *name, uint8_t domain) {
  M68kAnalysisNamedLabel *label;
  char unique_name[64];
  unsigned suffix;
  size_t index;
  if (policy == NULL || name == NULL || name[0] == '\0' ||
      policy->named_label_count >= M68K_ANALYSIS_NAMED_LABEL_LIMIT) return 0;
  snprintf(unique_name, sizeof(unique_name), "%s", name);
  for (index = 0U; index < policy->named_label_count; ++index) {
    const M68kAnalysisNamedLabel *existing = &policy->named_labels[index];
    if (existing->name[0] == '\0' || strcmp(existing->name, unique_name) != 0) continue;
    if (existing->has_section_index && existing->section_index == section_index && existing->offset == offset &&
        existing->domain == domain)
      return 1;
  }
  for (suffix = 2U; suffix < 1000U; ++suffix) {
    int collision = 0;
    for (index = 0U; index < policy->named_label_count; ++index) {
      const M68kAnalysisNamedLabel *existing = &policy->named_labels[index];
      if (existing->name[0] != '\0' && strcmp(existing->name, unique_name) == 0) {
        collision = 1;
        break;
      }
    }
    if (!collision) break;
    snprintf(unique_name, sizeof(unique_name), "%s_%u", name, suffix);
  }
  label = &policy->named_labels[policy->named_label_count++];
  memset(label, 0, sizeof(*label));
  label->has_section_index = 1U;
  label->domain = domain;
  label->section_index = section_index;
  label->offset = offset;
  return copy_policy_text(label->name, sizeof(label->name), unique_name);
}

static int policy_add_named_label_local(M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset,
    const char *name) {
  return policy_add_named_label_domain_local(policy, section_index, offset, name, M68K_ANALYSIS_LABEL_DOMAIN_SOURCE);
}

static int policy_add_entry_comment_local(M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset,
    const char *comment) {
  M68kAnalysisEntryComment *entry;
  uint16_t index;
  if (policy == NULL || comment == NULL || comment[0] == '\0' ||
      policy->entry_comment_count >= M68K_ANALYSIS_ENTRY_COMMENT_LIMIT)
    return 0;
  for (index = 0U; index < policy->entry_comment_count; ++index) {
    const M68kAnalysisEntryComment *existing = &policy->entry_comments[index];
    if (existing->has_section_index && existing->section_index == section_index && existing->offset == offset &&
        strcmp(existing->comment, comment) == 0)
      return 1;
  }
  entry = &policy->entry_comments[policy->entry_comment_count++];
  memset(entry, 0, sizeof(*entry));
  entry->has_section_index = 1U;
  entry->section_index = section_index;
  entry->offset = offset;
  return copy_policy_text(entry->comment, sizeof(entry->comment), comment);
}

static void policy_remove_entry_points_at_local(M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset) {
  uint16_t index = 0U;
  if (policy == NULL) return;
  while (index < policy->entry_point_count) {
    const M68kAnalysisEntryPoint *entry = &policy->entry_points[index];
    if (entry->has_section_index && entry->section_index == section_index && entry->offset == offset) {
      if (index + 1U < policy->entry_point_count) {
        memmove(&policy->entry_points[index], &policy->entry_points[index + 1U],
          (size_t)(policy->entry_point_count - index - 1U) * sizeof(policy->entry_points[0]));
      }
      --policy->entry_point_count;
      continue;
    }
    ++index;
  }
}

static void policy_remove_named_labels_at_local(M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset) {
  uint16_t index = 0U;
  if (policy == NULL) return;
  while (index < policy->named_label_count) {
    const M68kAnalysisNamedLabel *label = &policy->named_labels[index];
    if (label->has_section_index && label->section_index == section_index && label->offset == offset) {
      if (index + 1U < policy->named_label_count) {
        memmove(&policy->named_labels[index], &policy->named_labels[index + 1U],
          (size_t)(policy->named_label_count - index - 1U) * sizeof(policy->named_labels[0]));
      }
      --policy->named_label_count;
      continue;
    }
    ++index;
  }
}

static void policy_remove_entry_comments_at_local(M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset) {
  uint16_t index = 0U;
  if (policy == NULL) return;
  while (index < policy->entry_comment_count) {
    const M68kAnalysisEntryComment *comment = &policy->entry_comments[index];
    if (comment->has_section_index && comment->section_index == section_index && comment->offset == offset) {
      if (index + 1U < policy->entry_comment_count) {
        memmove(&policy->entry_comments[index], &policy->entry_comments[index + 1U],
          (size_t)(policy->entry_comment_count - index - 1U) * sizeof(policy->entry_comments[0]));
      }
      --policy->entry_comment_count;
      continue;
    }
    ++index;
  }
}

static void policy_remove_register_seeds_at_local(M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset) {
  uint16_t index = 0U;
  if (policy == NULL) return;
  while (index < policy->register_seed_count) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    if (seed->has_section_index && seed->section_index == section_index &&
        seed->has_entry_offset && seed->entry_offset == offset) {
      if (index + 1U < policy->register_seed_count) {
        memmove(&policy->register_seeds[index], &policy->register_seeds[index + 1U],
          (size_t)(policy->register_seed_count - index - 1U) * sizeof(policy->register_seeds[0]));
      }
      --policy->register_seed_count;
      continue;
    }
    ++index;
  }
}

static int policy_add_register_seed_local(M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset,
    uint8_t has_entry_offset, const char *register_name, uint8_t seed_kind, const char *name, const char *type_name,
    const char *context_name) {
  uint16_t seed_index;
  uint8_t reg_kind;
  uint8_t reg_index;
  uint16_t index;
  if (policy == NULL || policy->register_seed_count >= M68K_ANALYSIS_REGISTER_SEED_LIMIT) return 0;
  if (register_name == NULL || register_name[0] == '\0') return 0;
  if (name == NULL || seed_kind == M68K_ANALYSIS_REGISTER_SEED_NONE) return 0;
  if ((register_name[0] == 'D' || register_name[0] == 'd') && register_name[1] >= '0' && register_name[1] <= '7' &&
      register_name[2] == '\0') {
    reg_kind = M68K_ANALYSIS_REGISTER_DATA;
    reg_index = (uint8_t)(register_name[1] - '0');
  } else if ((register_name[0] == 'A' || register_name[0] == 'a') && register_name[1] >= '0' &&
             register_name[1] <= '7' && register_name[2] == '\0') {
    reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
    reg_index = (uint8_t)(register_name[1] - '0');
  } else {
    return 0;
  }
  for (index = 0U; index < policy->register_seed_count; ++index) {
    const M68kAnalysisRegisterSeed *existing = &policy->register_seeds[index];
    if (existing->has_section_index && existing->section_index == section_index &&
        existing->has_entry_offset == has_entry_offset &&
        (!has_entry_offset || existing->entry_offset == offset) &&
        existing->reg_kind == reg_kind && existing->reg_index == reg_index && existing->kind == seed_kind &&
        strcmp(existing->name, name != NULL ? name : "") == 0 &&
        strcmp(existing->type_name, type_name != NULL ? type_name : "") == 0 &&
        strcmp(existing->context_name, context_name != NULL ? context_name : "") == 0)
      return 1;
  }
  seed_index = policy->register_seed_count;
  memset(&policy->register_seeds[seed_index], 0, sizeof(policy->register_seeds[seed_index]));
  policy->register_seeds[seed_index].has_entry_offset = has_entry_offset;
  policy->register_seeds[seed_index].entry_offset = has_entry_offset ? offset : 0U;
  policy->register_seeds[seed_index].has_section_index = 1U;
  policy->register_seeds[seed_index].section_index = section_index;
  policy->register_seeds[seed_index].reg_kind = reg_kind;
  policy->register_seeds[seed_index].reg_index = reg_index;
  policy->register_seeds[seed_index].kind = seed_kind;
  if (!copy_policy_text(policy->register_seeds[seed_index].name,
      sizeof(policy->register_seeds[seed_index].name), name) ||
      !copy_policy_text(policy->register_seeds[seed_index].type_name,
        sizeof(policy->register_seeds[seed_index].type_name), type_name) ||
      !copy_policy_text(policy->register_seeds[seed_index].context_name,
        sizeof(policy->register_seeds[seed_index].context_name), context_name)) {
    return 0;
  }
  policy->register_seed_count += 1U;
  return 1;
}

static void amiga_register_name_local(uint8_t reg_kind, uint8_t reg_index, char *out, size_t out_size) {
  if (out == NULL || out_size == 0U) return;
  out[0] = '\0';
  if (reg_index >= 8U) return;
  if (reg_kind == AMIGA_OS_REGISTER_ADDRESS) {
    snprintf(out, out_size, "A%u", (unsigned)reg_index);
  } else if (reg_kind == AMIGA_OS_REGISTER_DATA) {
    snprintf(out, out_size, "D%u", (unsigned)reg_index);
  }
}

static const char *amiga_call_value_type_name_local(uint16_t type_id, uint16_t struct_id) {
  const char *type_name = amiga_os_name(M68K_PLATFORM_NAME_TYPE, type_id);
  if (type_name != NULL && type_name[0] != '\0') return type_name;
  type_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id);
  return type_name != NULL && type_name[0] != '\0' ? type_name : NULL;
}

static int append_amiga_lvo_typed_name_local(char *buf, size_t buf_size, const char *type_name, const char *name) {
  size_t used;
  const char *separator = " ";
  if (type_name == NULL || type_name[0] == '\0') type_name = "void *";
  if (name == NULL || name[0] == '\0') name = "arg";
  if (type_name[strlen(type_name) - 1U] == '*') separator = "";
  used = strlen(buf);
  if (used + strlen(type_name) + strlen(separator) + strlen(name) + 1U >= buf_size) return 0;
  snprintf(buf + used, buf_size - used, "%s%s%s", type_name, separator, name);
  return 1;
}

static int append_amiga_lvo_decl_arg_local(char *buf, size_t buf_size, const AmigaOsCallInputInfo *input) {
  const char *type_name;
  const char *arg_name;
  char reg_name[8];
  if (buf == NULL || buf_size == 0U || input == NULL) return 0;
  type_name = amiga_call_value_type_name_local(input->type_id, input->struct_id);
  arg_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, input->input_id);
  amiga_register_name_local(input->reg_kind, input->reg_index, reg_name, sizeof(reg_name));
  if (arg_name == NULL || arg_name[0] == '\0') arg_name = reg_name[0] != '\0' ? reg_name : "arg";
  if (!append_amiga_lvo_typed_name_local(buf, buf_size, type_name, arg_name)) return 0;
  return 1;
}

static int format_amiga_lvo_declaration_local(const AmigaOsLibraryVectorInfo *vector, char *buf, size_t buf_size) {
  const AmigaOsCallInputInfo *inputs;
  const char *function_name;
  const char *return_type;
  size_t input_count;
  size_t input_index;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (vector == NULL) return 0;
  function_name = amiga_os_name(M68K_PLATFORM_NAME_FUNCTION, vector->function_id);
  if (function_name == NULL || function_name[0] == '\0') return 0;
  return_type = amiga_call_value_type_name_local(vector->output.type_id, vector->output.struct_id);
  if (return_type == NULL || return_type[0] == '\0') return_type = "void";
  if (snprintf(buf, buf_size, "DECL: ") < 0) return 0;
  if (!append_amiga_lvo_typed_name_local(buf, buf_size, return_type, function_name)) return 0;
  if (strlen(buf) + 2U >= buf_size) return 0;
  strcat(buf, "(");
  inputs = amiga_os_library_vector_inputs(vector, &input_count);
  for (input_index = 0U; input_index < input_count; ++input_index) {
    size_t used = strlen(buf);
    if (input_index != 0U) {
      if (used + 3U >= buf_size) return 0;
      snprintf(buf + used, buf_size - used, ", ");
    }
    if (!append_amiga_lvo_decl_arg_local(buf, buf_size, &inputs[input_index])) return 0;
  }
  {
    size_t used = strlen(buf);
    if (used + 2U >= buf_size) return 0;
    snprintf(buf + used, buf_size - used, ")");
  }
  return 1;
}

static int policy_add_amiga_lvo_argument_seeds_local(M68kAnalysisPolicy *policy, uint32_t section_index,
    uint32_t offset, const AmigaOsLibraryVectorInfo *vector) {
  const AmigaOsCallInputInfo *inputs;
  size_t input_count;
  size_t input_index;
  if (policy == NULL || vector == NULL) return 1;
  inputs = amiga_os_library_vector_inputs(vector, &input_count);
  for (input_index = 0U; input_index < input_count; ++input_index) {
    const AmigaOsCallInputInfo *input = &inputs[input_index];
    const char *arg_name;
    const char *type_name;
    char reg_name[8];
    if (input->reg_kind == 0U) continue;
    amiga_register_name_local(input->reg_kind, input->reg_index, reg_name, sizeof(reg_name));
    if (reg_name[0] == '\0') continue;
    arg_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, input->input_id);
    type_name = amiga_call_value_type_name_local(input->type_id, input->struct_id);
    if (arg_name == NULL || arg_name[0] == '\0') arg_name = reg_name;
    if (type_name == NULL || type_name[0] == '\0') continue;
    if (!policy_add_register_seed_local(policy, section_index, offset, 1U, reg_name,
        M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR, arg_name, type_name, ""))
      return 0;
  }
  return 1;
}

static int policy_add_structured_data_item_section_local(M68kAnalysisPolicy *policy, uint8_t has_section_index,
    uint32_t section_index, uint32_t offset, uint32_t size, uint8_t kind, const char *comment) {
  M68kAnalysisStructuredDataItem *item;
  if (policy == NULL || size == 0U ||
      policy->structured_data_item_count >= M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT) return 0;
  item = &policy->structured_data_items[policy->structured_data_item_count++];
  memset(item, 0, sizeof(*item));
  item->has_section_index = has_section_index;
  item->section_index = section_index;
  item->kind = kind;
  item->offset = offset;
  item->size = size;
  if (!copy_policy_text(item->comment, sizeof(item->comment), comment)) return 0;
  return 1;
}

static int policy_set_structured_data_item_metadata_local(M68kAnalysisPolicy *policy, uint16_t item_index,
    const char *label, const char *struct_name, const char *field_name, uint32_t semantic_role_flags,
    uint8_t is_pointer) {
  M68kAnalysisStructuredDataItem *item;
  if (policy == NULL || item_index >= policy->structured_data_item_count ||
      item_index >= M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT) return 0;
  item = &policy->structured_data_items[item_index];
  item->is_pointer = is_pointer;
  item->struct_id = amiga_os_name_id(M68K_PLATFORM_NAME_STRUCT, struct_name);
  if (amiga_os_name(M68K_PLATFORM_NAME_STRUCT, item->struct_id) == NULL) item->struct_id = AMIGA_OS_STRUCT_ID_NONE;
  item->field_id = amiga_os_name_id(M68K_PLATFORM_NAME_FIELD, field_name);
  if (amiga_os_name(M68K_PLATFORM_NAME_FIELD, item->field_id) == NULL) item->field_id = AMIGA_OS_FIELD_ID_NONE;
  item->platform_kind_id = structured_data_platform_kind_id_from_text_local(struct_name);
  item->platform_field_id =
    structured_data_platform_field_id_from_text_local(item->platform_kind_id, field_name);
  m68k_analysis_structured_data_item_set_semantic_role_flags(item, semantic_role_flags);
  return copy_policy_text(item->label, sizeof(item->label), label) &&
    copy_policy_text(item->struct_name, sizeof(item->struct_name), struct_name) &&
    copy_policy_text(item->field_name, sizeof(item->field_name), field_name);
}

static int policy_set_structured_data_item_kb_metadata_local(M68kAnalysisPolicy *policy, uint16_t item_index,
    const char *field_type, const char *c_type, const char *pointer_struct, const char *value_domain,
    const char *constant_name, uint8_t has_constant_value, int32_t constant_value) {
  M68kAnalysisStructuredDataItem *item;
  if (policy == NULL || item_index >= policy->structured_data_item_count ||
      item_index >= M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT) return 0;
  item = &policy->structured_data_items[item_index];
  item->has_constant_value = has_constant_value;
  item->constant_value = constant_value;
  item->pointer_struct_id = amiga_os_name_id(M68K_PLATFORM_NAME_STRUCT, pointer_struct);
  if (amiga_os_name(M68K_PLATFORM_NAME_STRUCT, item->pointer_struct_id) == NULL)
    item->pointer_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  return copy_policy_text(item->field_type, sizeof(item->field_type), field_type) &&
    copy_policy_text(item->c_type, sizeof(item->c_type), c_type) &&
    copy_policy_text(item->pointer_struct, sizeof(item->pointer_struct), pointer_struct) &&
    copy_policy_text(item->value_domain, sizeof(item->value_domain), value_domain) &&
    copy_policy_text(item->constant_name, sizeof(item->constant_name), constant_name);
}

static int policy_set_structured_data_item_target_local(M68kAnalysisPolicy *policy, uint16_t item_index,
    uint32_t target_section, uint32_t target_offset) {
  M68kAnalysisStructuredDataItem *item;
  if (policy == NULL || item_index >= policy->structured_data_item_count ||
      item_index >= M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT) return 0;
  item = &policy->structured_data_items[item_index];
  item->has_target = 1U;
  item->target_section = target_section;
  item->target_offset = target_offset;
  m68k_analysis_structured_data_item_refresh_table_metadata(item);
  return 1;
}

static int policy_add_structured_data_item_local(M68kAnalysisPolicy *policy, uint32_t offset, uint32_t size,
    uint8_t kind, const char *comment) {
  return policy_add_structured_data_item_section_local(policy, 0U, 0U, offset, size, kind, comment);
}

typedef enum MetadataSeededEntityTypeId {
  METADATA_SEEDED_ENTITY_TYPE_DATA = 0,
  METADATA_SEEDED_ENTITY_TYPE_IGNORED = 1
} MetadataSeededEntityTypeId;

typedef enum MetadataSeededEntitySubtypeId {
  METADATA_SEEDED_ENTITY_SUBTYPE_NONE = 0,
  METADATA_SEEDED_ENTITY_SUBTYPE_COPPER_LIST,
  METADATA_SEEDED_ENTITY_SUBTYPE_PALETTE,
  METADATA_SEEDED_ENTITY_SUBTYPE_POINTER_TABLE,
  METADATA_SEEDED_ENTITY_SUBTYPE_LOOKUP_TABLE,
  METADATA_SEEDED_ENTITY_SUBTYPE_LENGTH_PREFIXED_STRING,
  METADATA_SEEDED_ENTITY_SUBTYPE_BITMAP,
  METADATA_SEEDED_ENTITY_SUBTYPE_SOUND_SAMPLE,
  METADATA_SEEDED_ENTITY_SUBTYPE_STRING,
  METADATA_SEEDED_ENTITY_SUBTYPE_AUDIO_TABLE,
  METADATA_SEEDED_ENTITY_SUBTYPE_SPRITE,
  METADATA_SEEDED_ENTITY_SUBTYPE_STRING_CONTROL_STREAM
} MetadataSeededEntitySubtypeId;

typedef enum MetadataSeededEntityUnitId {
  METADATA_SEEDED_ENTITY_UNIT_BYTES = 0,
  METADATA_SEEDED_ENTITY_UNIT_WORDS,
  METADATA_SEEDED_ENTITY_UNIT_LONGS
} MetadataSeededEntityUnitId;

typedef struct MetadataSeededEntityClassification {
  MetadataSeededEntityTypeId type_id;
  MetadataSeededEntitySubtypeId subtype_id;
  MetadataSeededEntityUnitId unit_id;
  uint8_t structured_kind;
  uint8_t is_pointer;
  uint32_t role_flags;
} MetadataSeededEntityClassification;

typedef struct MetadataSeededEntityTypeName {
  const char *name;
  MetadataSeededEntityTypeId id;
} MetadataSeededEntityTypeName;

typedef struct MetadataSeededEntitySubtypeName {
  const char *name;
  MetadataSeededEntitySubtypeId id;
} MetadataSeededEntitySubtypeName;

typedef struct MetadataSeededEntityUnitName {
  const char *name;
  MetadataSeededEntityUnitId id;
} MetadataSeededEntityUnitName;

static const MetadataSeededEntityTypeName METADATA_SEEDED_ENTITY_TYPE_NAMES[] = {
  { "data", METADATA_SEEDED_ENTITY_TYPE_DATA },
};

static const MetadataSeededEntitySubtypeName METADATA_SEEDED_ENTITY_SUBTYPE_NAMES[] = {
  { "copper_list", METADATA_SEEDED_ENTITY_SUBTYPE_COPPER_LIST },
  { "palette", METADATA_SEEDED_ENTITY_SUBTYPE_PALETTE },
  { "pointer_table", METADATA_SEEDED_ENTITY_SUBTYPE_POINTER_TABLE },
  { "lookup_table", METADATA_SEEDED_ENTITY_SUBTYPE_LOOKUP_TABLE },
  { "scalar_table", METADATA_SEEDED_ENTITY_SUBTYPE_LOOKUP_TABLE },
  { "length_prefixed_string", METADATA_SEEDED_ENTITY_SUBTYPE_LENGTH_PREFIXED_STRING },
  { "bitmap", METADATA_SEEDED_ENTITY_SUBTYPE_BITMAP },
  { "sound_sample", METADATA_SEEDED_ENTITY_SUBTYPE_SOUND_SAMPLE },
  { "string", METADATA_SEEDED_ENTITY_SUBTYPE_STRING },
  { "audio_table", METADATA_SEEDED_ENTITY_SUBTYPE_AUDIO_TABLE },
  { "sprite", METADATA_SEEDED_ENTITY_SUBTYPE_SPRITE },
  { "string_control_stream", METADATA_SEEDED_ENTITY_SUBTYPE_STRING_CONTROL_STREAM },
};

static const MetadataSeededEntityUnitName METADATA_SEEDED_ENTITY_UNIT_NAMES[] = {
  { "word", METADATA_SEEDED_ENTITY_UNIT_WORDS },
  { "long", METADATA_SEEDED_ENTITY_UNIT_LONGS },
  { "pointer", METADATA_SEEDED_ENTITY_UNIT_LONGS },
};

static MetadataSeededEntityTypeId metadata_seeded_entity_type_id_from_text_local(const char *entity_type) {
  size_t index;
  if (entity_type == NULL || entity_type[0] == '\0') return METADATA_SEEDED_ENTITY_TYPE_DATA;
  for (index = 0U; index < sizeof(METADATA_SEEDED_ENTITY_TYPE_NAMES) / sizeof(METADATA_SEEDED_ENTITY_TYPE_NAMES[0]);
       ++index) {
    if (strcmp(entity_type, METADATA_SEEDED_ENTITY_TYPE_NAMES[index].name) == 0)
      return METADATA_SEEDED_ENTITY_TYPE_NAMES[index].id;
  }
  return METADATA_SEEDED_ENTITY_TYPE_IGNORED;
}

static MetadataSeededEntitySubtypeId metadata_seeded_entity_subtype_id_from_text_local(const char *subtype) {
  size_t index;
  if (subtype == NULL || subtype[0] == '\0') return METADATA_SEEDED_ENTITY_SUBTYPE_NONE;
  for (index = 0U; index < sizeof(METADATA_SEEDED_ENTITY_SUBTYPE_NAMES) / sizeof(METADATA_SEEDED_ENTITY_SUBTYPE_NAMES[0]);
       ++index) {
    if (strcmp(subtype, METADATA_SEEDED_ENTITY_SUBTYPE_NAMES[index].name) == 0)
      return METADATA_SEEDED_ENTITY_SUBTYPE_NAMES[index].id;
  }
  return METADATA_SEEDED_ENTITY_SUBTYPE_NONE;
}

static MetadataSeededEntityUnitId metadata_seeded_entity_unit_id_from_text_local(const char *unit) {
  size_t index;
  if (unit == NULL || unit[0] == '\0') return METADATA_SEEDED_ENTITY_UNIT_BYTES;
  for (index = 0U; index < sizeof(METADATA_SEEDED_ENTITY_UNIT_NAMES) / sizeof(METADATA_SEEDED_ENTITY_UNIT_NAMES[0]);
       ++index) {
    if (strcmp(unit, METADATA_SEEDED_ENTITY_UNIT_NAMES[index].name) == 0)
      return METADATA_SEEDED_ENTITY_UNIT_NAMES[index].id;
  }
  return METADATA_SEEDED_ENTITY_UNIT_BYTES;
}

static uint32_t metadata_seeded_entity_role_flags_from_subtype_id_local(MetadataSeededEntitySubtypeId subtype_id) {
  switch (subtype_id) {
    case METADATA_SEEDED_ENTITY_SUBTYPE_COPPER_LIST: return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_COPPER_LIST;
    case METADATA_SEEDED_ENTITY_SUBTYPE_PALETTE: return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_PALETTE;
    case METADATA_SEEDED_ENTITY_SUBTYPE_POINTER_TABLE: return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE;
    case METADATA_SEEDED_ENTITY_SUBTYPE_LOOKUP_TABLE: return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE;
    case METADATA_SEEDED_ENTITY_SUBTYPE_LENGTH_PREFIXED_STRING:
      return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LENGTH_PREFIXED_STRING;
    case METADATA_SEEDED_ENTITY_SUBTYPE_BITMAP: return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP;
    case METADATA_SEEDED_ENTITY_SUBTYPE_SOUND_SAMPLE: return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SOUND_SAMPLE;
    case METADATA_SEEDED_ENTITY_SUBTYPE_STRING: return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING;
    case METADATA_SEEDED_ENTITY_SUBTYPE_AUDIO_TABLE: return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_AUDIO_TABLE;
    case METADATA_SEEDED_ENTITY_SUBTYPE_SPRITE: return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SPRITE;
    case METADATA_SEEDED_ENTITY_SUBTYPE_STRING_CONTROL_STREAM:
      return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING_CONTROL_STREAM;
    case METADATA_SEEDED_ENTITY_SUBTYPE_NONE: break;
  }
  return 0U;
}

static uint8_t metadata_seeded_entity_kind_from_ids_local(MetadataSeededEntitySubtypeId subtype_id,
    MetadataSeededEntityUnitId unit_id) {
  if (subtype_id == METADATA_SEEDED_ENTITY_SUBTYPE_STRING) return M68K_ANALYSIS_STRUCTURED_DATA_STRING;
  if (subtype_id == METADATA_SEEDED_ENTITY_SUBTYPE_POINTER_TABLE) return M68K_ANALYSIS_STRUCTURED_DATA_LONGS;
  if (unit_id == METADATA_SEEDED_ENTITY_UNIT_WORDS) return M68K_ANALYSIS_STRUCTURED_DATA_WORDS;
  if (unit_id == METADATA_SEEDED_ENTITY_UNIT_LONGS) return M68K_ANALYSIS_STRUCTURED_DATA_LONGS;
  return M68K_ANALYSIS_STRUCTURED_DATA_BYTES;
}

static MetadataSeededEntityClassification metadata_seeded_entity_classify_local(const char *entity_type,
    const char *subtype, const char *unit) {
  MetadataSeededEntityClassification classification;
  classification.type_id = metadata_seeded_entity_type_id_from_text_local(entity_type);
  classification.subtype_id = metadata_seeded_entity_subtype_id_from_text_local(subtype);
  classification.unit_id = metadata_seeded_entity_unit_id_from_text_local(unit);
  classification.structured_kind =
    metadata_seeded_entity_kind_from_ids_local(classification.subtype_id, classification.unit_id);
  classification.is_pointer = (uint8_t)(classification.subtype_id == METADATA_SEEDED_ENTITY_SUBTYPE_POINTER_TABLE);
  classification.role_flags = metadata_seeded_entity_role_flags_from_subtype_id_local(classification.subtype_id);
  return classification;
}

static int append_metadata_seeded_entity_local(const char *object_start, const char *object_end,
    M68kAnalysisPolicy *policy) {
  uint32_t addr = 0U;
  uint32_t end = 0U;
  uint32_t hunk = 0U;
  uint16_t item_index;
  int has_addr = 0;
  int has_end = 0;
  int has_hunk = 0;
  char entity_type[16];
  char subtype[64];
  char unit[32];
  char encoding[32];
  char name[64];
  char comment[256];
  char policy_comment[96];
  char struct_name[64];
  char field_name[64];
  char field_type[64];
  char c_type[64];
  char pointer_struct[64];
  char value_domain[64];
  MetadataSeededEntityClassification classification;
  entity_type[0] = '\0';
  subtype[0] = '\0';
  unit[0] = '\0';
  encoding[0] = '\0';
  name[0] = '\0';
  comment[0] = '\0';
  policy_comment[0] = '\0';
  struct_name[0] = '\0';
  field_name[0] = '\0';
  field_type[0] = '\0';
  c_type[0] = '\0';
  pointer_struct[0] = '\0';
  value_domain[0] = '\0';
  if (!json_number_field_local(object_start, object_end, "addr", &addr, &has_addr) ||
      !json_number_field_local(object_start, object_end, "end", &end, &has_end) ||
      !json_number_field_local(object_start, object_end, "hunk", &hunk, &has_hunk) ||
      !json_optional_string_field_local(object_start, object_end, "type", entity_type, sizeof(entity_type)) ||
      !json_optional_string_field_local(object_start, object_end, "subtype", subtype, sizeof(subtype)) ||
      !json_optional_string_field_local(object_start, object_end, "unit", unit, sizeof(unit)) ||
      !json_optional_string_field_local(object_start, object_end, "encoding", encoding, sizeof(encoding)) ||
      !json_optional_string_field_local(object_start, object_end, "name", name, sizeof(name)) ||
      !json_optional_string_field_local(object_start, object_end, "comment", comment, sizeof(comment)) ||
      !json_optional_string_field_local(object_start, object_end, "struct_name", struct_name, sizeof(struct_name)) ||
      !json_optional_string_field_local(object_start, object_end, "field_name", field_name, sizeof(field_name)) ||
      !json_optional_string_field_local(object_start, object_end, "field_type", field_type, sizeof(field_type)) ||
      !json_optional_string_field_local(object_start, object_end, "c_type", c_type, sizeof(c_type)) ||
      !json_optional_string_field_local(object_start, object_end, "pointer_struct", pointer_struct,
        sizeof(pointer_struct)) ||
      !json_optional_string_field_local(object_start, object_end, "value_domain", value_domain,
        sizeof(value_domain))) {
    return 0;
  }
  if (!has_addr || !has_end || end <= addr) return 1;
  classification = metadata_seeded_entity_classify_local(entity_type, subtype, unit);
  if (classification.type_id != METADATA_SEEDED_ENTITY_TYPE_DATA) return 1;
  snprintf(policy_comment, sizeof(policy_comment), "%s", comment);
  item_index = policy->structured_data_item_count;
  if (!policy_add_structured_data_item_section_local(policy, 1U, has_hunk ? hunk : 0U, addr, end - addr,
        classification.structured_kind, policy_comment)) {
    return 0;
  }
  if (!policy_set_structured_data_item_metadata_local(policy, item_index, name, struct_name, field_name,
        classification.role_flags, classification.is_pointer)) {
    return 0;
  }
  if (name[0] != '\0' && !policy_add_named_label_local(policy, has_hunk ? hunk : 0U, addr, name)) return 0;
  return policy_set_structured_data_item_kb_metadata_local(policy, item_index, field_type[0] != '\0' ? field_type : unit,
    c_type, pointer_struct, value_domain[0] != '\0' ? value_domain : encoding, NULL, 0U, 0);
}

static int append_metadata_manual_representation_local(const char *object_start, const char *object_end,
    M68kAnalysisPolicy *policy) {
  uint32_t addr = 0U;
  uint32_t end = 0U;
  uint32_t hunk = 0U;
  uint32_t size = 1U;
  uint32_t operand_index = 0U;
  uint8_t style_id;
  int has_addr = 0;
  int has_end = 0;
  int has_hunk = 0;
  int has_operand_index = 0;
  char style[32];
  char symbol[64];
  style[0] = '\0';
  symbol[0] = '\0';
  if (!json_number_field_local(object_start, object_end, "addr", &addr, &has_addr) ||
      !json_number_field_local(object_start, object_end, "end", &end, &has_end) ||
      !json_number_field_local(object_start, object_end, "hunk", &hunk, &has_hunk) ||
      !json_number_field_local(object_start, object_end, "operand_index", &operand_index, &has_operand_index) ||
      !json_optional_string_field_local(object_start, object_end, "style", style, sizeof(style)) ||
      !json_optional_string_field_local(object_start, object_end, "symbol", symbol, sizeof(symbol))) {
    return 0;
  }
  if (!has_addr) return 1;
  style_id = analysis_representation_style_id_from_text_local(style);
  if (style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_NONE) return 1;
  if (style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL && symbol[0] == '\0') return 1;
  if (has_end && end > addr) size = end - addr;
  if (has_operand_index && operand_index > 3U) return 1;
  return policy_add_manual_representation_local(policy, has_hunk ? hunk : 0U, addr, size, style_id,
    has_operand_index ? 1U : 0U, (uint8_t)operand_index,
    style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL ? symbol : NULL);
}

static int append_metadata_target_equate_local(const char *object_start, const char *object_end,
    M68kAnalysisPolicy *policy) {
  const char *value_start;
  char number_text[32];
  char *endptr = NULL;
  long parsed;
  size_t used = 0U;
  char name[64];
  char value_representation[16];
  char value_expression[64];
  uint8_t value_style_id = M68K_ANALYSIS_REPRESENTATION_STYLE_NONE;
  name[0] = '\0';
  value_representation[0] = '\0';
  value_expression[0] = '\0';
  if (!json_optional_string_field_local(object_start, object_end, "name", name, sizeof(name)) ||
      !json_optional_string_field_local(object_start, object_end, "value_representation",
        value_representation, sizeof(value_representation)) ||
      !json_optional_string_field_local(object_start, object_end, "value_expression",
        value_expression, sizeof(value_expression))) {
    return 0;
  }
  value_start = json_find_key_local(object_start, object_end, "value");
  if (name[0] == '\0' || value_start == NULL) return 1;
  value_start = json_skip_ws_local(value_start, object_end);
  while (value_start < object_end && ((*value_start >= '0' && *value_start <= '9') ||
         *value_start == '-' || *value_start == '+')) {
    if (used + 1U >= sizeof(number_text)) return 0;
    number_text[used++] = *value_start++;
  }
  number_text[used] = '\0';
  if (used == 0U) return 0;
  parsed = strtol(number_text, &endptr, 10);
  if (endptr == NULL || *endptr != '\0' || parsed < INT32_MIN || parsed > INT32_MAX) return 0;
  if (value_representation[0] != '\0') {
    value_style_id = analysis_representation_style_id_from_text_local(value_representation);
    if (value_style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_NONE ||
        value_style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_STRING) {
      return 0;
    }
  }
  return policy_add_target_equate_local(policy, name, (int32_t)parsed, value_style_id, value_expression);
}

static int append_metadata_rsset_use_site_binding_local(const char *object_start, const char *object_end,
    M68kAnalysisPolicy *policy) {
  uint32_t hunk = 0U;
  uint32_t addr = 0U;
  uint32_t operand_index = 0U;
  uint32_t displacement = 0U;
  int has_hunk = 0;
  int has_addr = 0;
  int has_operand_index = 0;
  int has_displacement = 0;
  char base_register[8];
  char layout_name[32];
  char base_symbol[64];
  char base_evidence_id[96];
  char binding_id[256];
  char owner_action_id[96];
  base_register[0] = '\0';
  layout_name[0] = '\0';
  base_symbol[0] = '\0';
  base_evidence_id[0] = '\0';
  binding_id[0] = '\0';
  owner_action_id[0] = '\0';
  if (!json_number_field_local(object_start, object_end, "hunk", &hunk, &has_hunk) ||
      !json_number_field_local(object_start, object_end, "addr", &addr, &has_addr) ||
      !json_number_field_local(object_start, object_end, "operand_index", &operand_index, &has_operand_index) ||
      !json_number_field_local(object_start, object_end, "displacement", &displacement, &has_displacement) ||
      !json_optional_string_field_local(object_start, object_end, "base_register", base_register,
        sizeof(base_register)) ||
      !json_optional_string_field_local(object_start, object_end, "layout_name", layout_name,
        sizeof(layout_name)) ||
      !json_optional_string_field_local(object_start, object_end, "base_symbol", base_symbol,
        sizeof(base_symbol)) ||
      !json_optional_string_field_local(object_start, object_end, "base_evidence_id", base_evidence_id,
        sizeof(base_evidence_id)) ||
      !json_optional_string_field_local(object_start, object_end, "binding_id", binding_id, sizeof(binding_id)) ||
      !json_optional_string_field_local(object_start, object_end, "owner_action_id", owner_action_id,
        sizeof(owner_action_id))) {
    return 0;
  }
  if (!has_hunk || !has_addr || !has_operand_index || !has_displacement ||
      operand_index > UINT8_MAX || base_register[0] == '\0' || base_evidence_id[0] == '\0') {
    return 0;
  }
  return policy_add_rsset_use_site_binding_local(policy, hunk, addr, (uint8_t)operand_index, base_register,
    displacement, layout_name, base_symbol, base_evidence_id, binding_id, owner_action_id);
}

static int append_metadata_manual_runtime_address_ref_local(const char *object_start, const char *object_end,
    M68kAnalysisPolicy *policy) {
  uint32_t addr = 0U;
  uint32_t hunk = 0U;
  uint32_t size = 0U;
  uint32_t target_hunk = 0U;
  uint32_t target_offset = 0U;
  uint32_t runtime_address = 0U;
  uint32_t confidence = 0U;
  uint32_t owner_element_offset = 0U;
  int has_addr = 0;
  int has_hunk = 0;
  int has_size = 0;
  int has_target_hunk = 0;
  int has_target_offset = 0;
  int has_runtime_address = 0;
  int has_confidence = 0;
  int has_owner_element_offset = 0;
  char owner_kind[32];
  char owner_id[96];
  char owner_layout_id[64];
  char xref_generation_mode[32];
  owner_kind[0] = '\0';
  owner_id[0] = '\0';
  owner_layout_id[0] = '\0';
  xref_generation_mode[0] = '\0';
  if (!json_number_field_local(object_start, object_end, "addr", &addr, &has_addr) ||
      !json_number_field_local(object_start, object_end, "hunk", &hunk, &has_hunk) ||
      !json_number_field_local(object_start, object_end, "size", &size, &has_size) ||
      !json_number_field_local(object_start, object_end, "target_hunk", &target_hunk, &has_target_hunk) ||
      !json_number_field_local(object_start, object_end, "target_offset", &target_offset, &has_target_offset) ||
      !json_number_field_local(object_start, object_end, "runtime_address", &runtime_address, &has_runtime_address) ||
      !json_number_field_local(object_start, object_end, "confidence", &confidence, &has_confidence) ||
      !json_number_field_local(object_start, object_end, "owner_element_offset", &owner_element_offset,
        &has_owner_element_offset) ||
      !json_optional_string_field_local(object_start, object_end, "owner_kind", owner_kind, sizeof(owner_kind)) ||
      !json_optional_string_field_local(object_start, object_end, "owner_id", owner_id, sizeof(owner_id)) ||
      !json_optional_string_field_local(object_start, object_end, "owner_layout_id", owner_layout_id,
        sizeof(owner_layout_id)) ||
      !json_optional_string_field_local(object_start, object_end, "xref_generation_mode", xref_generation_mode,
        sizeof(xref_generation_mode))) {
    return 0;
  }
  if (!has_addr || !has_size || !has_target_hunk || !has_target_offset || !has_runtime_address ||
      !has_confidence || !has_owner_element_offset)
    return 0;
  return policy_add_manual_runtime_address_ref_local(policy, has_hunk ? hunk : 0U, addr, size, target_hunk,
    target_offset, runtime_address, (uint8_t)confidence, owner_kind, owner_id, owner_layout_id,
    owner_element_offset, xref_generation_mode);
}

static const char *json_find_object_field_local(const char *text, const char *key, const char **out_object_end) {
  const char *end = text + strlen(text);
  const char *cursor = json_find_key_local(text, end, key);
  int depth = 0;
  if (out_object_end != NULL) *out_object_end = NULL;
  if (cursor == NULL) return NULL;
  cursor = json_skip_ws_local(cursor, end);
  if (cursor + 4 <= end && memcmp(cursor, "null", 4U) == 0) return NULL;
  if (cursor >= end || *cursor != '{') return NULL;
  {
    const char *object_start = cursor;
    for (; cursor < end; ++cursor) {
      if (*cursor == '{') ++depth;
      else if (*cursor == '}') {
        --depth;
        if (depth == 0) {
          if (out_object_end != NULL) *out_object_end = cursor + 1;
          return object_start;
        }
      }
    }
  }
  return NULL;
}

static int append_metadata_bootblock_structure_local(const char *text, M68kAnalysisPolicy *policy) {
  const char *object_end = NULL;
  const char *object_start = json_find_object_field_local(text, "bootblock", &object_end);
  uint32_t bootcode_offset = 0U;
  int has_bootcode_offset = 0;
  uint8_t bootcode_has_code = 0U;
  uint8_t checksum_valid = 0U;
  int has_bootcode_has_code = 0;
  int has_checksum_valid = 0;
  int should_seed_boot_entry;
  if (object_start == NULL) return 1;
  policy->disable_implicit_entry_points = 1U;
  if (!json_number_field_local(object_start, object_end, "bootcode_offset", &bootcode_offset, &has_bootcode_offset) ||
      !json_bool_field_local(object_start, object_end, "bootcode_has_code", &bootcode_has_code,
        &has_bootcode_has_code) ||
      !json_bool_field_local(object_start, object_end, "checksum_valid", &checksum_valid, &has_checksum_valid))
    return 0;
  if (!has_bootcode_offset || bootcode_offset < 12U) return 1;
  should_seed_boot_entry = has_bootcode_has_code ? bootcode_has_code : (!has_checksum_valid || checksum_valid);
  if (!policy_add_structured_data_item_local(policy, 0U, 4U, M68K_ANALYSIS_STRUCTURED_DATA_STRING,
           "NOTE: boot magic") ||
    !policy_add_structured_data_item_local(policy, 4U, 4U, M68K_ANALYSIS_STRUCTURED_DATA_LONGS,
      "NOTE: boot checksum") ||
    !policy_add_structured_data_item_local(policy, 8U, 4U, M68K_ANALYSIS_STRUCTURED_DATA_LONGS,
      "NOTE: boot root block"))
    return 0;
  if (!should_seed_boot_entry) return 1;
  return policy_add_entry_point_local(policy, 0U, bootcode_offset) &&
    policy_add_named_label_local(policy, 0U, bootcode_offset, "boot_entry");
}

static uint8_t resident_field_kind_local(uint32_t size) {
  if (size == 4U) return M68K_ANALYSIS_STRUCTURED_DATA_LONGS;
  if (size == 2U) return M68K_ANALYSIS_STRUCTURED_DATA_WORDS;
  return M68K_ANALYSIS_STRUCTURED_DATA_BYTES;
}

static uint8_t amiga_os_type_id_is_pointer_like_local(uint16_t type_id) {
  return type_id == AMIGA_OS_TYPE_ID_APTR || type_id == AMIGA_OS_TYPE_ID_BPTR ||
    type_id == AMIGA_OS_TYPE_ID_BSTR;
}

static int make_struct_field_label_local(char *out, size_t out_size, const char *label_prefix, const char *struct_name,
    const char *field_symbol) {
  const char *cursor;
  size_t used = 0U;
  size_t prefix_len;
  if (out == NULL || out_size == 0U) return 0;
  out[0] = '\0';
  if (label_prefix == NULL || field_symbol == NULL) return 0;
  cursor = field_symbol;
  if (struct_name != NULL && struct_name[0] != '\0') {
    prefix_len = strlen(struct_name);
    if (strncmp(cursor, struct_name, prefix_len) == 0 && cursor[prefix_len] == '_') cursor += prefix_len + 1U;
  }
  prefix_len = strlen(label_prefix);
  if (used + prefix_len + 2U >= out_size) return 0;
  memcpy(out, label_prefix, prefix_len);
  used = prefix_len;
  out[used++] = '_';
  while (*cursor != '\0' && used + 1U < out_size) {
    char ch = *cursor++;
    if (ch >= 'A' && ch <= 'Z') ch = (char)(ch - 'A' + 'a');
    out[used++] = ch;
  }
  out[used] = '\0';
  return used != 0U;
}

static void make_note_comment_from_label_local(char *out, size_t out_size, const char *label) {
  size_t used = 0U;
  const char *cursor;
  if (out == NULL || out_size == 0U) return;
  out[0] = '\0';
  if (label == NULL) return;
  snprintf(out, out_size, "NOTE: ");
  used = strlen(out);
  cursor = label;
  while (*cursor != '\0' && used + 1U < out_size) {
    char ch = *cursor++;
    out[used++] = (ch == '_') ? ' ' : ch;
  }
  out[used] = '\0';
}

static uint8_t kb_struct_field_is_pointer_local(const AmigaOsStructFieldInfo *field) {
  const char *c_type;
  if (field == NULL) return 0U;
  if (field->pointer_struct_id != AMIGA_OS_STRUCT_ID_NONE) return 1U;
  c_type = amiga_os_name(M68K_PLATFORM_NAME_TYPE, field->c_type_id);
  if (amiga_os_type_id_is_pointer_like_local(field->field_type_id)) return 1U;
  return c_type != NULL && strchr(c_type, '*') != NULL;
}

static int kb_value_domain_single_exact_constant_local(uint16_t value_domain_id, const char **out_name, int32_t *out_value) {
  const AmigaOsValueDomainInfo *domain;
  const AmigaOsValueDomainMemberInfo *members;
  size_t member_count = 0U;
  if (out_name != NULL) *out_name = NULL;
  if (out_value != NULL) *out_value = 0;
  domain = amiga_os_find_value_domain_by_id(value_domain_id);
  if (domain == NULL || domain->exact_match_policy != AMIGA_OS_VALUE_DOMAIN_EXACT_MATCH_ERROR) return 0;
  members = amiga_os_value_domain_members(domain, &member_count);
  if (members == NULL || member_count != 1U || !members[0].value_known) return 0;
  if (out_name != NULL) *out_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, members[0].name_id);
  if (out_value != NULL) *out_value = members[0].value;
  return out_name == NULL || *out_name != NULL;
}

static int append_metadata_kb_struct_instance_local(M68kAnalysisPolicy *policy, uint32_t hunk, uint32_t offset,
    const char *struct_name, const char *instance_label) {
  uint16_t struct_id;
  size_t index;
  if (policy == NULL || struct_name == NULL || instance_label == NULL) return 0;
  struct_id = amiga_os_name_id(M68K_PLATFORM_NAME_STRUCT, struct_name);
  if (amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id) == NULL) return 0;
  if (!policy_add_named_label_local(policy, hunk, offset, instance_label)) return 0;
  for (index = 0U; index < AMIGA_OS_STRUCT_FIELD_COUNT; ++index) {
    const AmigaOsStructFieldInfo *field = amiga_os_struct_field_at(index);
    const char *field_symbol, *field_type, *c_type, *pointer_struct, *value_domain;
    const char *constant_name = NULL;
    int32_t constant_value = 0;
    uint8_t has_constant_value = 0U;
    char label[64], comment[64];
    uint16_t item_index;
    if (field == NULL || field->struct_id != struct_id || field->size == 0U) continue;
    field_symbol = amiga_os_name(M68K_PLATFORM_NAME_FIELD, field->field_id);
    if (field_symbol == NULL) return 0;
    if (!make_struct_field_label_local(label, sizeof(label), instance_label, struct_name, field_symbol)) return 0;
    make_note_comment_from_label_local(comment, sizeof(comment), label);
    field_type = amiga_os_name(M68K_PLATFORM_NAME_TYPE, field->field_type_id);
    c_type = amiga_os_name(M68K_PLATFORM_NAME_TYPE, field->c_type_id);
    pointer_struct = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, field->pointer_struct_id);
    value_domain = amiga_os_find_struct_field_value_domain(struct_name, field_symbol, NULL);
    if (value_domain != NULL) {
      uint16_t value_domain_id = amiga_os_name_id(M68K_PLATFORM_NAME_VALUE_DOMAIN, value_domain);
      has_constant_value = kb_value_domain_single_exact_constant_local(value_domain_id, &constant_name, &constant_value) ? 1U : 0U;
    }
    item_index = policy->structured_data_item_count;
    if (!policy_add_structured_data_item_section_local(policy, 1U, hunk, offset + (uint32_t)field->offset,
          (uint32_t)field->size, resident_field_kind_local((uint32_t)field->size), comment) ||
        !policy_set_structured_data_item_metadata_local(policy, item_index, label, struct_name, field_symbol, 0U,
          kb_struct_field_is_pointer_local(field)) ||
        !policy_set_structured_data_item_kb_metadata_local(policy, item_index, field_type, c_type, pointer_struct,
          value_domain, constant_name, has_constant_value, constant_value)) {
      return 0;
    }
  }
  return 1;
}

static int append_metadata_resident_rt_structure_local(const char *resident_start, const char *resident_end,
    M68kAnalysisPolicy *policy, uint32_t hunk, uint32_t resident_offset) {
  (void)resident_start;
  (void)resident_end;
  return append_metadata_kb_struct_instance_local(policy, hunk, resident_offset, "RT", "resident");
}

static int policy_set_structured_field_target_local(M68kAnalysisPolicy *policy, uint32_t hunk,
    const char *struct_name, const char *field_name, uint32_t target_hunk, uint32_t target_offset) {
  uint16_t index;
  uint16_t struct_id;
  uint16_t field_id;
  if (policy == NULL || struct_name == NULL || field_name == NULL) return 0;
  struct_id = amiga_os_name_id(M68K_PLATFORM_NAME_STRUCT, struct_name);
  if (amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id) == NULL) return 1;
  field_id = amiga_os_name_id(M68K_PLATFORM_NAME_FIELD, field_name);
  if (amiga_os_name(M68K_PLATFORM_NAME_FIELD, field_id) == NULL) return 1;
  for (index = 0U; index < policy->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    if (!item->has_section_index || item->section_index != hunk) continue;
    if (item->struct_id != struct_id || item->field_id != field_id) continue;
    return policy_set_structured_data_item_target_local(policy, index, target_hunk, target_offset);
  }
  return 1;
}

static int policy_add_autoinit_structured_item_local(M68kAnalysisPolicy *policy, uint32_t hunk, uint32_t offset,
    const char *label, uint8_t is_pointer, uint8_t has_target, uint32_t target_offset) {
  uint16_t item_index;
  char comment[64];
  if (policy == NULL || label == NULL) return 0;
  item_index = policy->structured_data_item_count;
  make_note_comment_from_label_local(comment, sizeof(comment), label);
  if (!policy_add_structured_data_item_section_local(policy, 1U, hunk, offset, 4U,
        M68K_ANALYSIS_STRUCTURED_DATA_LONGS, comment) ||
      !policy_set_structured_data_item_metadata_local(policy, item_index, label, "resident_autoinit",
        label, 0U, is_pointer) ||
      !policy_set_structured_data_item_kb_metadata_local(policy, item_index, is_pointer ? "APTR" : "ULONG",
        is_pointer ? "APTR" : "ULONG",
        NULL, NULL, NULL, 0U, 0)) {
      return 0;
  }
  if (has_target && !policy_set_structured_data_item_target_local(policy, item_index, hunk, target_offset)) return 0;
  return 1;
}

static const char *json_find_nested_object_field_local(const char *object_start, const char *object_end, const char *key,
    const char **out_object_end) {
  const char *cursor = json_find_key_local(object_start, object_end, key);
  int depth = 0;
  if (out_object_end != NULL) *out_object_end = NULL;
  if (cursor == NULL) return NULL;
  cursor = json_skip_ws_local(cursor, object_end);
  if (cursor + 4 <= object_end && memcmp(cursor, "null", 4U) == 0) return NULL;
  if (cursor >= object_end || *cursor != '{') return NULL;
  {
    const char *nested_start = cursor;
    for (; cursor < object_end; ++cursor) {
      if (*cursor == '{') ++depth;
      else if (*cursor == '}') {
        --depth;
        if (depth == 0) {
          if (out_object_end != NULL) *out_object_end = cursor + 1;
          return nested_start;
        }
      }
    }
  }
  return NULL;
}

static const char *json_find_array_field_in_object_local(const char *object_start, const char *object_end,
    const char *key, const char **out_end) {
  const char *cursor = json_find_key_local(object_start, object_end, key);
  int depth = 0;
  if (out_end != NULL) *out_end = NULL;
  if (cursor == NULL) return NULL;
  cursor = json_skip_ws_local(cursor, object_end);
  if (cursor >= object_end || *cursor != '[') return NULL;
  {
    const char *array_start = cursor + 1;
    for (; cursor < object_end; ++cursor) {
      if (*cursor == '[') ++depth;
      else if (*cursor == ']') {
        --depth;
        if (depth == 0) {
          if (out_end != NULL) *out_end = cursor;
          return array_start;
        }
      }
    }
  }
  return NULL;
}

typedef struct ResidentVectorMetadataEntryLocal {
  uint32_t hunk;
  uint32_t offset;
} ResidentVectorMetadataEntryLocal;

static int parse_resident_vector_offset_local(const char **inout_cursor, const char *array_end,
    uint32_t fallback_hunk, ResidentVectorMetadataEntryLocal *out_entry, int *out_present) {
  const char *cursor;
  if (out_present != NULL) *out_present = 0;
  if (inout_cursor == NULL || out_entry == NULL) return 0;
  cursor = json_skip_ws_local(*inout_cursor, array_end);
  while (cursor < array_end && *cursor == ',') cursor = json_skip_ws_local(cursor + 1, array_end);
  if (cursor >= array_end) {
    *inout_cursor = cursor;
    return 1;
  }
  {
    const char *number_start = cursor;
    while (cursor < array_end && ((*cursor >= '0' && *cursor <= '9') || *cursor == '+' || *cursor == '-')) ++cursor;
    if (cursor == number_start) {
      *inout_cursor = cursor;
      return 1;
    }
    {
      char number_text[32];
      size_t length = (size_t)(cursor - number_start);
      if (length >= sizeof(number_text)) return 0;
      memcpy(number_text, number_start, length);
      number_text[length] = '\0';
      if (!parse_u32_arg_local(number_text, &out_entry->offset)) return 0;
    }
  }
  out_entry->hunk = fallback_hunk;
  *inout_cursor = cursor;
  if (out_present != NULL) *out_present = 1;
  return 1;
}

static int parse_resident_vector_entry_local(const char **inout_cursor, const char *array_end, uint32_t fallback_hunk,
    ResidentVectorMetadataEntryLocal *out_entry, int *out_present) {
  const char *object_start;
  const char *object_end = NULL;
  uint32_t hunk = fallback_hunk;
  uint32_t section = fallback_hunk;
  uint32_t offset = 0U;
  int has_hunk = 0;
  int has_section = 0;
  int has_offset = 0;
  if (out_present != NULL) *out_present = 0;
  if (inout_cursor == NULL || out_entry == NULL) return 0;
  object_start = json_next_object_local(*inout_cursor, array_end, &object_end);
  if (object_start == NULL || object_end == NULL) {
    *inout_cursor = array_end;
    return 1;
  }
  if (!json_number_field_local(object_start, object_end, "hunk", &hunk, &has_hunk) ||
      !json_number_field_local(object_start, object_end, "section", &section, &has_section) ||
      !json_number_field_local(object_start, object_end, "offset", &offset, &has_offset)) {
    return 0;
  }
  if (!has_offset) return 0;
  out_entry->hunk = has_section ? section : (has_hunk ? hunk : fallback_hunk);
  out_entry->offset = offset;
  *inout_cursor = object_end;
  if (out_present != NULL) *out_present = 1;
  return 1;
}

static const char *resident_vector_metadata_array_local(const char *autoinit_start, const char *autoinit_end,
    const char **out_array_end, uint8_t *out_entries_are_objects) {
  const char *array_end = NULL;
  const char *cursor = json_find_array_field_in_object_local(autoinit_start, autoinit_end, "vector_entries", &array_end);
  if (cursor != NULL) {
    if (out_array_end != NULL) *out_array_end = array_end;
    if (out_entries_are_objects != NULL) *out_entries_are_objects = 1U;
    return cursor;
  }
  cursor = json_find_array_field_in_object_local(autoinit_start, autoinit_end, "vector_offsets", &array_end);
  if (out_array_end != NULL) *out_array_end = array_end;
  if (out_entries_are_objects != NULL) *out_entries_are_objects = 0U;
  return cursor;
}

static int parse_next_resident_vector_metadata_entry_local(const char **inout_cursor, const char *array_end,
    uint8_t entries_are_objects, uint32_t fallback_hunk, ResidentVectorMetadataEntryLocal *out_entry,
    int *out_present) {
  if (entries_are_objects) return parse_resident_vector_entry_local(inout_cursor, array_end, fallback_hunk, out_entry, out_present);
  return parse_resident_vector_offset_local(inout_cursor, array_end, fallback_hunk, out_entry, out_present);
}

static int policy_add_resident_vector_entrypoint_local(M68kAnalysisPolicy *policy,
    const ResidentVectorMetadataEntryLocal *entry, uint32_t vector_index, const char *target_type,
    const char *library_name, uint32_t library_version, uint32_t *inout_next_private_ordinal,
    uint32_t *inout_first_code_offset, uint32_t first_code_hunk) {
  char label_name[64];
  uint8_t target_type_id = amiga_os_resident_target_type_id(target_type);
  label_name[0] = '\0';
  if (policy == NULL || entry == NULL) return 0;
  if (inout_first_code_offset != NULL && entry->hunk == first_code_hunk &&
      (*inout_first_code_offset == UINT32_MAX || entry->offset < *inout_first_code_offset)) {
    *inout_first_code_offset = entry->offset;
  }
  if (!policy_add_entry_point_local(policy, entry->hunk, entry->offset)) return 0;
  if (library_name != NULL && library_name[0] != '\0') {
    const char *base_struct_name = amiga_os_find_library_base_struct_name(library_name);
    if (base_struct_name == NULL || base_struct_name[0] == '\0') base_struct_name = "LIB";
    if (!policy_add_register_seed_local(policy, entry->hunk, entry->offset, 1U, "A6",
          M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE, library_name, base_struct_name, ""))
      return 0;
  }
  {
    size_t prefix_index;
    for (prefix_index = 0U; prefix_index < AMIGA_OS_RESIDENT_VECTOR_PREFIX_COUNT; ++prefix_index) {
      const AmigaOsResidentVectorPrefixInfo *prefix = amiga_os_resident_vector_prefix_at(prefix_index);
      const char *symbol;
      if (prefix == NULL || prefix->slot_index != vector_index || prefix->target_type_id != target_type_id) continue;
      {
        char base_label[64];
        char library_label[32];
        symbol = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, prefix->symbol_id);
        make_policy_symbol_label_local(base_label, sizeof(base_label), symbol);
        make_library_stem_label_local(library_label, sizeof(library_label), library_name);
        if (base_label[0] != '\0' && library_label[0] != '\0') {
          snprintf(label_name, sizeof(label_name), "%s_%s", library_label, base_label);
        } else {
          snprintf(label_name, sizeof(label_name), "%s", base_label);
        }
      }
      break;
    }
  }
  if (label_name[0] == '\0' && library_name != NULL && library_name[0] != '\0') {
    const char *base_name = amiga_os_find_library_base_name(library_name);
    int16_t lvo = (int16_t)(-(int32_t)((vector_index + 1U) * (uint32_t)amiga_os_lvo_slot_size()));
    const AmigaOsLibraryVectorInfo *vector = base_name != NULL ? amiga_os_find_library_vector(base_name, lvo) : NULL;
    const char *function_name = vector != NULL ? amiga_os_name(M68K_PLATFORM_NAME_FUNCTION, vector->function_id) : NULL;
    if (function_name != NULL && function_name[0] != '\0' &&
        (vector->available_since_version == 0U || vector->available_since_version <= library_version)) {
      char declaration[192];
      make_policy_symbol_label_local(label_name, sizeof(label_name), function_name);
      if (format_amiga_lvo_declaration_local(vector, declaration, sizeof(declaration)) &&
          !policy_add_entry_comment_local(policy, entry->hunk, entry->offset, declaration)) {
        return 0;
      }
      if (!policy_add_amiga_lvo_argument_seeds_local(policy, entry->hunk, entry->offset, vector)) return 0;
    } else {
      char private_stem[48];
      uint32_t ordinal = inout_next_private_ordinal != NULL ? *inout_next_private_ordinal : 1U;
      make_library_stem_label_local(private_stem, sizeof(private_stem), library_name);
      snprintf(label_name, sizeof(label_name), "%s_private_%u", private_stem[0] != '\0' ? private_stem : "resident",
        (unsigned)ordinal);
      if (inout_next_private_ordinal != NULL) *inout_next_private_ordinal = ordinal + 1U;
    }
  }
  if (label_name[0] != '\0' && !policy_add_named_label_local(policy, entry->hunk, entry->offset, label_name))
    return 0;
  return 1;
}

static int append_metadata_resident_vector_entrypoints_local(const char *autoinit_start, const char *autoinit_end,
    M68kAnalysisPolicy *policy, uint32_t hunk, const char *target_type, const char *library_name,
    uint32_t library_version, uint32_t *inout_first_code_offset) {
  const char *array_end = NULL;
  uint8_t entries_are_objects = 0U;
  const char *cursor = resident_vector_metadata_array_local(autoinit_start, autoinit_end, &array_end, &entries_are_objects);
  uint32_t vector_index = 0U;
  uint32_t next_private_ordinal = 1U;
  if (cursor == NULL) return 1;
  while (cursor < array_end) {
    ResidentVectorMetadataEntryLocal entry;
    int has_entry = 0;
    if (!parse_next_resident_vector_metadata_entry_local(&cursor, array_end, entries_are_objects, hunk, &entry,
          &has_entry))
      return 0;
    if (!has_entry) break;
    if (!policy_add_resident_vector_entrypoint_local(policy, &entry, vector_index, target_type, library_name,
        library_version, &next_private_ordinal, inout_first_code_offset, hunk))
      return 0;
    ++vector_index;
  }
  return 1;
}

static uint32_t resident_vector_entry_size_local(const char *vector_format) {
  if (vector_format != NULL && strstr(vector_format, "16") != NULL) return 2U;
  return 4U;
}

static uint8_t resident_vector_entry_kind_local(uint32_t entry_size) {
  return entry_size == 2U ? M68K_ANALYSIS_STRUCTURED_DATA_WORDS : M68K_ANALYSIS_STRUCTURED_DATA_LONGS;
}

static int append_metadata_resident_vector_table_items_local(const char *autoinit_start, const char *autoinit_end,
    M68kAnalysisPolicy *policy, uint32_t hunk, uint32_t vectors_offset, uint32_t entry_size,
    uint32_t *out_vector_count) {
  const char *array_end = NULL;
  uint8_t entries_are_objects = 0U;
  const char *cursor = resident_vector_metadata_array_local(autoinit_start, autoinit_end, &array_end, &entries_are_objects);
  uint32_t vector_index = 0U;
  uint8_t kind = resident_vector_entry_kind_local(entry_size);
  if (out_vector_count != NULL) *out_vector_count = 0U;
  if (entry_size != 2U && entry_size != 4U) return 0;
  if (cursor == NULL) return 1;
  while (cursor < array_end) {
    ResidentVectorMetadataEntryLocal entry;
    int has_entry = 0;
    uint16_t item_index;
    if (!parse_next_resident_vector_metadata_entry_local(&cursor, array_end, entries_are_objects, hunk, &entry,
          &has_entry))
      return 0;
    if (!has_entry) break;
    item_index = policy->structured_data_item_count;
    if (!policy_add_structured_data_item_section_local(policy, 1U, hunk,
          vectors_offset + vector_index * entry_size, entry_size, kind, NULL)) {
      return 0;
    }
    if (entry_size == 4U && !policy_set_structured_data_item_target_local(policy, item_index, entry.hunk, entry.offset))
      return 0;
    ++vector_index;
  }
  if (vector_index != 0U) {
    if (!policy_add_structured_data_item_section_local(policy, 1U, hunk,
          vectors_offset + vector_index * entry_size, entry_size, kind, NULL)) {
      return 0;
    }
  }
  if (out_vector_count != NULL) *out_vector_count = vector_index;
  return 1;
}

static void policy_update_resident_vector_item_target_local(M68kAnalysisPolicy *policy, uint32_t hunk,
    uint32_t vector_item_offset, uint32_t entry_size, const ResidentVectorMetadataEntryLocal *entry) {
  uint16_t index;
  uint8_t kind = resident_vector_entry_kind_local(entry_size);
  if (policy == NULL || entry == NULL) return;
  for (index = 0U; index < policy->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    if (!item->has_section_index || item->section_index != hunk || item->offset != vector_item_offset ||
        item->size != entry_size || item->kind != kind)
      continue;
    if (entry_size == 4U && (!item->has_target ||
        (item->target_section == hunk && item->target_offset == entry->offset))) {
      item->has_target = 1U;
      item->target_section = entry->hunk;
      item->target_offset = entry->offset;
      m68k_analysis_structured_data_item_refresh_table_metadata(item);
    }
  }
}

static int repair_metadata_resident_vector_sections_local(const char *autoinit_start, const char *autoinit_end,
    M68kAnalysisPolicy *policy, uint32_t hunk, const char *target_type, const char *library_name,
    uint32_t library_version) {
  const char *array_end = NULL, *cursor;
  uint32_t vectors_offset = 0U, vector_index = 0U, vector_entry_size, first_code_offset = UINT32_MAX;
  uint8_t entries_are_objects = 0U;
  int has_vectors_offset = 0;
  char vector_format[32];
  if (policy == NULL || autoinit_start == NULL || autoinit_end == NULL) return 1;
  cursor = resident_vector_metadata_array_local(autoinit_start, autoinit_end, &array_end, &entries_are_objects);
  vector_format[0] = '\0';
  if (!json_number_field_local(autoinit_start, autoinit_end, "vectors_offset", &vectors_offset, &has_vectors_offset) ||
      !json_optional_string_field_local(autoinit_start, autoinit_end, "vector_format", vector_format,
        sizeof(vector_format))) {
    return 0;
  }
  vector_entry_size = resident_vector_entry_size_local(vector_format);
  if (cursor == NULL) return 1;
  while (cursor < array_end) {
    ResidentVectorMetadataEntryLocal entry;
    int has_entry = 0;
    uint32_t vector_item_offset;
    if (!parse_next_resident_vector_metadata_entry_local(&cursor, array_end, entries_are_objects, hunk, &entry,
          &has_entry))
      return 0;
    if (!has_entry) break;
    if (has_vectors_offset) {
      vector_item_offset = vectors_offset + vector_index * vector_entry_size;
      policy_update_resident_vector_item_target_local(policy, hunk, vector_item_offset, vector_entry_size, &entry);
    }
    if (entry.hunk != hunk) {
      policy_remove_entry_points_at_local(policy, hunk, entry.offset);
      policy_remove_named_labels_at_local(policy, hunk, entry.offset);
      policy_remove_entry_comments_at_local(policy, hunk, entry.offset);
      policy_remove_register_seeds_at_local(policy, hunk, entry.offset);
    }
    ++vector_index;
  }
  return append_metadata_resident_vector_entrypoints_local(autoinit_start, autoinit_end, policy, hunk, target_type,
    library_name, library_version, &first_code_offset);
}

static int append_metadata_resident_autoinit_structure_local(const char *autoinit_start, const char *autoinit_end,
    M68kAnalysisPolicy *policy, uint32_t hunk, const char *target_type, const char *library_name,
    uint32_t library_version) {
  uint32_t payload_offset = 0U, vectors_offset = 0U, init_struct_offset = 0U, init_func_offset = 0U;
  uint32_t first_code_offset = UINT32_MAX, vector_table_count = 0U, vector_entry_size = 4U;
  char vector_format[32];
  int has_payload_offset = 0, has_vectors_offset = 0, has_init_struct_offset = 0, has_init_func_offset = 0;
  vector_format[0] = '\0';
  if (!json_number_field_local(autoinit_start, autoinit_end, "payload_offset", &payload_offset, &has_payload_offset) ||
      !json_number_field_local(autoinit_start, autoinit_end, "vectors_offset", &vectors_offset, &has_vectors_offset) ||
      !json_number_field_local(autoinit_start, autoinit_end, "init_struct_offset", &init_struct_offset,
        &has_init_struct_offset) ||
      !json_number_field_local(autoinit_start, autoinit_end, "init_func_offset", &init_func_offset,
        &has_init_func_offset)) {
    return 0;
  }
  if (!json_optional_string_field_local(autoinit_start, autoinit_end, "vector_format", vector_format,
        sizeof(vector_format))) {
    return 0;
  }
  vector_entry_size = resident_vector_entry_size_local(vector_format);
  if (has_payload_offset) {
    if (!policy_add_autoinit_structured_item_local(policy, hunk, payload_offset, "resident_base_size", 0U, 0U, 0U) ||
        !policy_add_autoinit_structured_item_local(policy, hunk, payload_offset + 4U, "resident_vectors", 1U,
          has_vectors_offset ? 1U : 0U, vectors_offset) ||
        !policy_add_autoinit_structured_item_local(policy, hunk, payload_offset + 8U, "resident_init_struct", 1U,
          has_init_struct_offset ? 1U : 0U, init_struct_offset) ||
        !policy_add_autoinit_structured_item_local(policy, hunk, payload_offset + 12U, "resident_init_function", 1U,
          has_init_func_offset ? 1U : 0U, init_func_offset)) {
      return 0;
    }
    if (!policy_add_named_label_local(policy, hunk, payload_offset, "resident_autoinit")) return 0;
  }
  if (has_vectors_offset &&
      !append_metadata_resident_vector_table_items_local(autoinit_start, autoinit_end, policy, hunk, vectors_offset,
        vector_entry_size, &vector_table_count)) {
    return 0;
  }
  if (vector_table_count == 0U && has_vectors_offset && has_init_struct_offset && init_struct_offset > vectors_offset) {
    uint32_t cursor;
    for (cursor = vectors_offset; cursor + 4U <= init_struct_offset; cursor += 4U) {
      if (!policy_add_structured_data_item_section_local(policy, 1U, hunk, cursor, 4U,
            M68K_ANALYSIS_STRUCTURED_DATA_LONGS, NULL)) {
        return 0;
      }
    }
  }
  if (has_init_func_offset) {
    const char *app_base_struct_name = NULL;
    const char *exec_base_struct_name = amiga_os_find_library_base_struct_name("exec.library");
    if (library_name != NULL && library_name[0] != '\0') app_base_struct_name = amiga_os_find_library_base_struct_name(library_name);
    if (app_base_struct_name == NULL || app_base_struct_name[0] == '\0') app_base_struct_name = "LIB";
    if (exec_base_struct_name == NULL || exec_base_struct_name[0] == '\0') exec_base_struct_name = "LIB";
    if (first_code_offset == UINT32_MAX || init_func_offset < first_code_offset) first_code_offset = init_func_offset;
    if (!policy_add_entry_point_local(policy, hunk, init_func_offset)) return 0;
    if (!policy_add_named_label_local(policy, hunk, init_func_offset, "resident_init") ||
        !policy_add_register_seed_local(policy, hunk, init_func_offset, 1U, "D0",
          M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE, "__amiga_app_base__", "", "") ||
        !policy_add_register_seed_local(policy, hunk, init_func_offset, 1U, "D0",
          M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR, "__amiga_app_base__", app_base_struct_name, "") ||
        !policy_add_register_seed_local(policy, hunk, init_func_offset, 1U, "A0",
          M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR, "seglist", "BPTR", "") ||
        !policy_add_register_seed_local(policy, hunk, init_func_offset, 1U, "A6",
          M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE, "exec.library", exec_base_struct_name, ""))
      return 0;
  }
  if (has_vectors_offset && !policy_add_named_label_local(policy, hunk, vectors_offset, "resident_vectors")) return 0;
  if (has_init_struct_offset && !policy_add_named_label_local(policy, hunk, init_struct_offset, "resident_init_struct"))
    return 0;
  if (!append_metadata_resident_vector_entrypoints_local(autoinit_start, autoinit_end, policy, hunk, target_type,
        library_name, library_version, &first_code_offset))
    return 0;
  if (has_init_struct_offset && first_code_offset != UINT32_MAX && first_code_offset > init_struct_offset) {
    if (!policy_add_structured_data_item_section_local(policy, 1U, hunk, init_struct_offset,
          first_code_offset - init_struct_offset, M68K_ANALYSIS_STRUCTURED_DATA_BYTES,
          "NOTE: resident init struct")) {
      return 0;
    }
  }
  return 1;
}

static int append_metadata_resident_structure_local(const char *text, M68kAnalysisPolicy *policy) {
  const char *resident_end = NULL;
  const char *resident_start = json_find_object_field_local(text, "resident", &resident_end);
  const char *autoinit_end = NULL;
  const char *autoinit_start;
  const char *text_end = text + strlen(text);
  char target_type[32];
  char library_name[64];
  uint32_t resident_offset = 0U;
  uint32_t init_offset = 0U;
  uint32_t hunk = 0U;
  uint32_t library_version = 0U;
  int has_resident_offset = 0;
  int has_init_offset = 0;
  int has_hunk = 0;
  int has_library_version = 0;
  target_type[0] = '\0';
  library_name[0] = '\0';
  if (resident_start == NULL) return 1;
  policy->disable_implicit_entry_points = 1U;
  if (!json_number_field_local(resident_start, resident_end, "offset", &resident_offset, &has_resident_offset) ||
      !json_number_field_local(resident_start, resident_end, "init_offset", &init_offset, &has_init_offset) ||
      !json_number_field_local(resident_start, resident_end, "hunk", &hunk, &has_hunk) ||
      !json_optional_string_field_local(text, text_end, "target_type", target_type, sizeof(target_type)) ||
      !json_optional_string_field_local(resident_start, resident_end, "name", library_name, sizeof(library_name)) ||
      !json_number_field_local(resident_start, resident_end, "version", &library_version, &has_library_version))
    return 0;
  if (has_resident_offset &&
      !append_metadata_resident_rt_structure_local(resident_start, resident_end, policy, has_hunk ? hunk : 0U,
        resident_offset)) {
    return 0;
  }
  autoinit_start = json_find_nested_object_field_local(resident_start, resident_end, "autoinit", &autoinit_end);
  if (autoinit_start != NULL &&
      !append_metadata_resident_autoinit_structure_local(autoinit_start, autoinit_end, policy, has_hunk ? hunk : 0U,
        target_type, library_name, has_library_version ? library_version : 0U)) {
    return 0;
  }
  if (autoinit_start == NULL && has_init_offset &&
      (!policy_add_entry_point_local(policy, has_hunk ? hunk : 0U, init_offset) ||
        !policy_add_named_label_local(policy, has_hunk ? hunk : 0U, init_offset, "resident_init") ||
        !policy_set_structured_field_target_local(policy, has_hunk ? hunk : 0U, "RT", "RT_INIT",
          has_hunk ? hunk : 0U, init_offset))) {
    return 0;
  }
  return 1;
}

static void append_metadata_resident_parse_issue_local(const char *text, M68kAnalysisPolicy *policy) {
  const char *resident_end = NULL;
  const char *resident_start = json_find_object_field_local(text, "resident", &resident_end);
  uint32_t resident_offset = 0U;
  uint32_t hunk = 0U;
  int has_resident_offset = 0;
  int has_hunk = 0;
  if (resident_start == NULL || policy == NULL) return;
  if (!json_number_field_local(resident_start, resident_end, "offset", &resident_offset, &has_resident_offset))
    return;
  if (!json_number_field_local(resident_start, resident_end, "hunk", &hunk, &has_hunk)) hunk = 0U;
  if (has_resident_offset)
    (void)policy_add_entry_comment_local(policy, has_hunk ? hunk : 0U, resident_offset,
      "NOTE: resident metadata could not be fully parsed");
}

static int append_metadata_source_context_local(const char *text, M68kAnalysisPolicy *policy) {
  const char *context_end = NULL;
  const char *context_start;
  if (text == NULL || policy == NULL) return 0;
  context_start = json_find_object_field_local(text, "source_context", &context_end);
  if (context_start == NULL) return 1;
  if (!json_optional_string_field_local(context_start, context_end, "kind",
        policy->source_context_kind, sizeof(policy->source_context_kind)) ||
      !json_optional_string_field_local(context_start, context_end, "disk_id",
        policy->source_context_disk_id, sizeof(policy->source_context_disk_id)) ||
      !json_optional_string_field_local(context_start, context_end, "disk_path",
        policy->source_context_disk_path, sizeof(policy->source_context_disk_path)) ||
      !json_optional_string_field_local(context_start, context_end, "entry_path",
        policy->source_context_entry_path, sizeof(policy->source_context_entry_path)) ||
      !json_optional_string_field_local(context_start, context_end, "parent_disk_id",
        policy->source_context_parent_disk_id, sizeof(policy->source_context_parent_disk_id))) {
    return 0;
  }
  return 1;
}

static int append_metadata_generic_policy_text_local(const char *text, M68kAnalysisPolicy *policy,
    M68kDiagSink diagnostics) {
  const char *array_end;
  const char *cursor;
  const char *text_end;
  char target_type[32];
  uint8_t target_type_id;
  if (text == NULL || policy == NULL) return -1;
  text_end = text + strlen(text);
  target_type[0] = '\0';
  if (!json_optional_string_field_local(text, text_end, "target_type", target_type, sizeof(target_type))) {
    platform_file_add_error(diagnostics.list, "failed parsing target metadata target_type");
    return -1;
  }
  target_type_id = metadata_target_type_id_from_text_local(target_type);
  if (metadata_target_type_disables_implicit_entries_local(target_type_id)) {
    policy->disable_implicit_entry_points = 1U;
  }
  if (!append_metadata_source_context_local(text, policy)) {
    platform_file_add_error(diagnostics.list, "failed parsing target metadata source context");
    return -1;
  }
  cursor = json_find_array_local(text, "entry_register_seeds", &array_end);
  while (cursor != NULL && cursor < array_end) {
    const char *object_end;
    const char *object_start = json_next_object_local(cursor, array_end, &object_end);
    if (object_start == NULL) break;
    if (!append_metadata_register_seed_local(object_start, object_end, policy)) {
      platform_file_add_error(diagnostics.list, "failed parsing target metadata entry register seed");
      return -1;
    }
    cursor = object_end;
  }
  cursor = json_find_array_local(text, "seeded_code_entrypoints", &array_end);
  while (cursor != NULL && cursor < array_end) {
    const char *object_end;
    const char *object_start = json_next_object_local(cursor, array_end, &object_end);
    if (object_start == NULL) break;
    if (!append_metadata_entry_point_local(object_start, object_end, policy)) {
      platform_file_add_error(diagnostics.list, "failed parsing target metadata code entrypoint");
      return -1;
    }
    cursor = object_end;
  }
  cursor = json_find_array_local(text, "seeded_code_labels", &array_end);
  while (cursor != NULL && cursor < array_end) {
    const char *object_end;
    const char *object_start = json_next_object_local(cursor, array_end, &object_end);
    if (object_start == NULL) break;
    if (!append_metadata_seeded_code_label_local(object_start, object_end, policy)) {
      platform_file_add_error(diagnostics.list, "failed parsing target metadata code label");
      return -1;
    }
    cursor = object_end;
  }
  cursor = json_find_array_local(text, "entry_comments", &array_end);
  while (cursor != NULL && cursor < array_end) {
    const char *object_end;
    const char *object_start = json_next_object_local(cursor, array_end, &object_end);
    if (object_start == NULL) break;
    if (!append_metadata_entry_comment_local(object_start, object_end, policy)) {
      platform_file_add_error(diagnostics.list, "failed parsing target metadata entry comment");
      return -1;
    }
    cursor = object_end;
  }
  cursor = json_find_array_local(text, "seeded_entities", &array_end);
  while (cursor != NULL && cursor < array_end) {
    const char *object_end;
    const char *object_start = json_next_object_local(cursor, array_end, &object_end);
    if (object_start == NULL) break;
    if (!append_metadata_seeded_entity_local(object_start, object_end, policy)) {
      platform_file_add_error(diagnostics.list, "failed parsing target metadata seeded entity");
      return -1;
    }
    cursor = object_end;
  }
  cursor = json_find_array_local(text, "target_equates", &array_end);
  while (cursor != NULL && cursor < array_end) {
    const char *object_end;
    const char *object_start = json_next_object_local(cursor, array_end, &object_end);
    if (object_start == NULL) break;
    if (!append_metadata_target_equate_local(object_start, object_end, policy)) {
      platform_file_add_error(diagnostics.list, "failed parsing target metadata target equate");
      return -1;
    }
    cursor = object_end;
  }
  cursor = json_find_array_local(text, "custom_structs", &array_end);
  while (cursor != NULL && cursor < array_end) {
    const char *object_end;
    const char *object_start = json_next_object_local(cursor, array_end, &object_end);
    if (object_start == NULL) break;
    if (!append_metadata_custom_struct_local(object_start, object_end, policy)) {
      platform_file_add_error(diagnostics.list, "failed parsing target metadata custom struct");
      return -1;
    }
    cursor = object_end;
  }
  cursor = json_find_array_local(text, "manual_representations", &array_end);
  while (cursor != NULL && cursor < array_end) {
    const char *object_end;
    const char *object_start = json_next_object_local(cursor, array_end, &object_end);
    if (object_start == NULL) break;
    if (!append_metadata_manual_representation_local(object_start, object_end, policy)) {
      platform_file_add_error(diagnostics.list, "failed parsing target metadata manual representation");
      return -1;
    }
    cursor = object_end;
  }
  cursor = json_find_array_local(text, "manual_runtime_address_refs", &array_end);
  while (cursor != NULL && cursor < array_end) {
    const char *object_end;
    const char *object_start = json_next_object_local(cursor, array_end, &object_end);
    if (object_start == NULL) break;
    if (!append_metadata_manual_runtime_address_ref_local(object_start, object_end, policy)) {
      platform_file_add_error(diagnostics.list, "failed parsing target metadata manual runtime address ref");
      return -1;
    }
    cursor = object_end;
  }
  cursor = json_find_array_local(text, "execution_views", &array_end);
  while (cursor != NULL && cursor < array_end) {
    const char *object_end;
    const char *object_start = json_next_object_local(cursor, array_end, &object_end);
    if (object_start == NULL) break;
    if (!append_metadata_execution_view_local(object_start, object_end, policy)) {
      platform_file_add_error(diagnostics.list, "failed parsing target metadata execution view");
      return -1;
    }
    cursor = object_end;
  }
  cursor = json_find_array_local(text, "absolute_code_labels", &array_end);
  while (cursor != NULL && cursor < array_end) {
    const char *object_end;
    const char *object_start = json_next_object_local(cursor, array_end, &object_end);
    if (object_start == NULL) break;
    if (!append_metadata_absolute_code_label_local(object_start, object_end, policy)) {
      platform_file_add_error(diagnostics.list, "failed parsing target metadata absolute code label");
      return -1;
    }
    cursor = object_end;
  }
  return 0;
}

static int append_metadata_amiga_policy_text_local(const char *text, M68kAnalysisPolicy *policy,
    M68kDiagSink diagnostics) {
  const char *array_end;
  const char *cursor;
  if (!append_metadata_bootblock_structure_local(text, policy)) {
    platform_file_add_error(diagnostics.list, "failed parsing target metadata bootblock structure");
    return -1;
  }
  if (!append_metadata_resident_structure_local(text, policy)) {
    append_metadata_resident_parse_issue_local(text, policy);
    platform_file_add_warning(diagnostics.list, "failed parsing target metadata resident structure");
  }
  cursor = json_find_array_local(text, "rsset_layout_regions", &array_end);
  while (cursor != NULL && cursor < array_end) {
    const char *object_end;
    const char *object_start = json_next_object_local(cursor, array_end, &object_end);
    if (object_start == NULL) break;
    if (!append_metadata_rsset_layout_region_local(object_start, object_end, policy)) {
      platform_file_add_error(diagnostics.list, "failed parsing target metadata RSSET layout region");
      return -1;
    }
    cursor = object_end;
  }
  cursor = json_find_array_local(text, "rsset_use_site_bindings", &array_end);
  while (cursor != NULL && cursor < array_end) {
    const char *object_end;
    const char *object_start = json_next_object_local(cursor, array_end, &object_end);
    if (object_start == NULL) break;
    if (!append_metadata_rsset_use_site_binding_local(object_start, object_end, policy)) {
      platform_file_add_error(diagnostics.list, "failed parsing target metadata RSSET use-site binding");
      return -1;
    }
    cursor = object_end;
  }
  return 0;
}

static int platform_name_uses_amiga_metadata_policy_local(const char *platform_name) {
  return m68k_backend_kind_by_platform_name(platform_name) == M68K_PLATFORM_BACKEND_AMIGA_HUNK;
}

static int metadata_text_has_amiga_policy_local(const char *text) {
  const char *array_end;
  const char *array_start;
  const char *resident_end;
  const char *text_end;
  char target_type[32];
  uint8_t target_type_id;
  if (text == NULL) return 0;
  if (json_find_object_field_local(text, "resident", &resident_end) != NULL) return 1;
  array_start = json_find_array_local(text, "rsset_layout_regions", &array_end);
  if (array_start != NULL && json_next_object_local(array_start, array_end, NULL) != NULL) return 1;
  array_start = json_find_array_local(text, "rsset_use_site_bindings", &array_end);
  if (array_start != NULL && json_next_object_local(array_start, array_end, NULL) != NULL) return 1;
  text_end = text + strlen(text);
  target_type[0] = '\0';
  if (json_optional_string_field_local(text, text_end, "target_type", target_type, sizeof(target_type))) {
    target_type_id = metadata_target_type_id_from_text_local(target_type);
    if (target_type_id == METADATA_TARGET_TYPE_BOOTBLOCK) return 1;
  }
  return 0;
}

static int platform_file_analysis_policy_load_target_metadata_for_platform_local(M68kAnalysisPolicy *policy,
    const char *path, const char *platform_name, M68kDiagSink diagnostics) {
  char *text;
  if (policy == NULL || path == NULL) {
    platform_file_add_error(diagnostics.list, "bad arguments");
    return -1;
  }
  text = read_text_file_local(path);
  if (text == NULL) {
    platform_file_add_error(diagnostics.list, "failed reading target metadata");
    return -1;
  }
  if (append_metadata_generic_policy_text_local(text, policy, diagnostics) != 0) {
    free(text);
    return -1;
  }
  if (platform_name_uses_amiga_metadata_policy_local(platform_name)) {
    if (append_metadata_amiga_policy_text_local(text, policy, diagnostics) != 0) {
      free(text);
      return -1;
    }
  } else if (metadata_text_has_amiga_policy_local(text)) {
    platform_file_add_error(diagnostics.list, "target metadata contains Amiga-only policy for this platform");
    free(text);
    return -1;
  }
  free(text);
  return 0;
}

int platform_file_analysis_policy_load_target_metadata(M68kAnalysisPolicy *policy, const char *path,
    M68kDiagSink diagnostics) {
  char *text;
  int result;
  if (policy == NULL || path == NULL) {
    platform_file_add_error(diagnostics.list, "bad arguments");
    return -1;
  }
  text = read_text_file_local(path);
  if (text == NULL) {
    platform_file_add_error(diagnostics.list, "failed reading target metadata");
    return -1;
  }
  result = append_metadata_generic_policy_text_local(text, policy, diagnostics);
  free(text);
  return result;
}

int platform_file_analysis_policy_load_target_metadata_for_platform(M68kAnalysisPolicy *policy, const char *path,
    const char *platform_name, M68kDiagSink diagnostics) {
  return platform_file_analysis_policy_load_target_metadata_for_platform_local(policy, path, platform_name, diagnostics);
}

static int configure_analysis_policy_for_alloc(M68kAnalysisPolicy *policy, const char *platform_name,
    const char *metadata_path, const char *entry_offsets, M68kDiagList *diagnostics) {
  char *offsets_copy;
  char *cursor;
  char *next;
  if (policy == NULL) return -1;
  m68k_analysis_policy_init_default(policy);
  if (metadata_path != NULL && metadata_path[0] != '\0' &&
      platform_file_analysis_policy_load_target_metadata_for_platform_local(policy, metadata_path, platform_name,
        m68k_diag_sink(diagnostics)) != 0) {
    return -1;
  }
  if (entry_offsets == NULL || entry_offsets[0] == '\0') return 0;
  offsets_copy = m68k_platform_dup_string(entry_offsets);
  if (offsets_copy == NULL) {
    platform_file_add_error(diagnostics, "out of memory");
    return -1;
  }
  cursor = offsets_copy;
  while (cursor != NULL && *cursor != '\0') {
    next = strpbrk(cursor, ";,");
    if (next != NULL) {
      *next = '\0';
      ++next;
    }
    if (*cursor != '\0' && !platform_file_analysis_policy_add_entry_point_arg(policy, cursor)) {
      free(offsets_copy);
      platform_file_add_error(diagnostics, "bad entry offset");
      return -1;
    }
    cursor = next;
  }
  free(offsets_copy);
  return 0;
}

static int append_nullable_text_json_local(JsonBuilder *builder, const char *text) {
  if (builder == NULL) return -1;
  if (text == NULL || text[0] == '\0') return json_builder_append(builder, "null");
  return json_builder_append_json_string(builder, text);
}

static int append_nullable_text_json_len_local(JsonBuilder *builder, const char *text, size_t length) {
  if (builder == NULL) return -1;
  if (text == NULL || length == 0U) return json_builder_append(builder, "null");
  return json_builder_append_json_string_len(builder, text, length);
}

static int append_structured_data_text_json_local(JsonBuilder *builder,
    const M68kAnalysisStructuredDataItem *item, uint8_t field) {
  size_t length = 0U;
  const char *text = m68k_analysis_structured_data_item_text(item, field, &length);
  return append_nullable_text_json_len_local(builder, text, length);
}

static const char *analysis_register_kind_name_local(uint8_t kind) {
  if (kind == M68K_ANALYSIS_REGISTER_DATA) return "data";
  if (kind == M68K_ANALYSIS_REGISTER_ADDRESS) return "address";
  return "none";
}

static const char *analysis_register_seed_kind_name_local(uint8_t kind) {
  if (kind == M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE) return "library_base";
  if (kind == M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR) return "struct_ptr";
  return "none";
}

static const char *structured_data_kind_name_local(uint8_t kind) {
  if (kind == M68K_ANALYSIS_STRUCTURED_DATA_BYTES) return "bytes";
  if (kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS) return "words";
  if (kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS) return "longs";
  if (kind == M68K_ANALYSIS_STRUCTURED_DATA_STRING) return "string";
  return "unknown";
}

static const char *manual_representation_style_name_local(uint8_t style_id) {
  if (style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_HEX) return "hex";
  if (style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_DECIMAL) return "decimal";
  if (style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_BINARY) return "binary";
  if (style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_CHARACTER) return "character";
  if (style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_STRING) return "string";
  if (style_id == M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL) return "symbol";
  return "none";
}

static uint32_t structured_data_item_role_flags_local(const M68kAnalysisStructuredDataItem *item) {
  if (item == NULL) return 0U;
  return item->semantic_role_flags;
}

static int append_nullable_u32_json_local(JsonBuilder *builder, uint8_t has_value, uint32_t value) {
  if (!has_value) return json_builder_append(builder, "null");
  return json_builder_appendf(builder, "%u", (unsigned)value);
}

static uint32_t effective_policy_analysis_start_local(const M68kAnalysisPolicy *policy, uint32_t fallback) {
  uint16_t index;
  uint32_t result = fallback;
  int have = 0;
  if (policy == NULL) return fallback;
  if (policy->has_entry_offset) {
    result = policy->entry_offset;
    have = 1;
  }
  for (index = 0U; index < policy->entry_point_count && index < M68K_ANALYSIS_ENTRY_POINT_LIMIT; ++index) {
    uint32_t offset = policy->entry_points[index].offset;
    if (!have || offset < result) {
      result = offset;
      have = 1;
    }
  }
  for (index = 0U; index < policy->runtime_entry_point_count &&
       index < M68K_ANALYSIS_RUNTIME_ENTRY_POINT_LIMIT; ++index) {
    uint32_t section_index = 0U;
    uint32_t offset = 0U;
    if (policy_runtime_address_to_source_offset_local(policy, policy->runtime_entry_points[index].runtime_address,
        &section_index, &offset) && section_index == 0U && (!have || offset < result)) {
      result = offset;
      have = 1;
    }
  }
  return result;
}

static int validate_policy_section_index_local(M68kDiagList *diagnostics, const M68kObject *object,
    uint8_t has_section_index, uint32_t section_index) {
  if (!has_section_index || object == NULL || section_index < object->section_count) return 1;
  platform_file_add_error(diagnostics, "target metadata hunk is out of range for source file");
  return 0;
}

static int policy_section_size_local(const M68kObject *object, uint8_t has_section_index, uint32_t section_index,
    uint32_t *out_size) {
  uint32_t index = has_section_index ? section_index : 0U;
  if (out_size != NULL) *out_size = 0U;
  if (object == NULL || object->sections == NULL || index >= object->section_count) return 0;
  if (out_size != NULL) *out_size = object->sections[index].size;
  return 1;
}

static int validate_policy_offset_local(M68kDiagList *diagnostics, const M68kObject *object,
    uint8_t has_section_index, uint32_t section_index, uint32_t offset, const char *what) {
  uint32_t section_size;
  if (!policy_section_size_local(object, has_section_index, section_index, &section_size)) {
    platform_file_add_error(diagnostics, "target metadata hunk is out of range for source file");
    return 0;
  }
  if (offset < section_size) return 1;
  platform_file_add_error(diagnostics, what != NULL ? what : "target metadata offset is out of range for source file");
  return 0;
}

static int validate_policy_range_local(M68kDiagList *diagnostics, const M68kObject *object,
    uint8_t has_section_index, uint32_t section_index, uint32_t offset, uint32_t size) {
  uint32_t section_size;
  if (!policy_section_size_local(object, has_section_index, section_index, &section_size)) {
    platform_file_add_error(diagnostics, "target metadata hunk is out of range for source file");
    return 0;
  }
  if (offset <= section_size && size <= section_size - offset) return 1;
  platform_file_add_error(diagnostics, "target metadata range is out of range for source file");
  return 0;
}

static int validate_effective_policy_against_object_local(M68kDiagList *diagnostics, const M68kObject *object,
    const M68kAnalysisPolicy *policy) {
  uint16_t index;
  if (object == NULL || policy == NULL) return 0;
  if (policy->has_entry_offset &&
      !validate_policy_offset_local(diagnostics, object, 0U, 0U, policy->entry_offset,
        "target metadata analysis start offset is out of range for source file"))
    return 0;
  for (index = 0U; index < policy->entry_point_count && index < M68K_ANALYSIS_ENTRY_POINT_LIMIT; ++index) {
    const M68kAnalysisEntryPoint *entry = &policy->entry_points[index];
    if (!validate_policy_section_index_local(diagnostics, object, entry->has_section_index, entry->section_index))
      return 0;
    if (!validate_policy_offset_local(diagnostics, object, entry->has_section_index, entry->section_index,
          entry->offset, "target metadata entry offset is out of range for source file"))
      return 0;
  }
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    if (!validate_policy_section_index_local(diagnostics, object, seed->has_section_index, seed->section_index))
      return 0;
    if (seed->has_entry_offset &&
        !validate_policy_offset_local(diagnostics, object, seed->has_section_index, seed->section_index,
          seed->entry_offset, "target metadata register seed offset is out of range for source file"))
      return 0;
  }
  for (index = 0U; index < policy->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    if (!validate_policy_section_index_local(diagnostics, object, item->has_section_index, item->section_index))
      return 0;
    if (!validate_policy_range_local(diagnostics, object, item->has_section_index, item->section_index, item->offset,
          item->size))
      return 0;
    if (!validate_policy_section_index_local(diagnostics, object, item->has_target, item->target_section)) return 0;
    if (item->has_target &&
        !validate_policy_offset_local(diagnostics, object, 1U, item->target_section, item->target_offset,
          "target metadata pointer target is out of range for source file"))
      return 0;
  }
  for (index = 0U; index < policy->named_label_count && index < M68K_ANALYSIS_NAMED_LABEL_LIMIT; ++index) {
    const M68kAnalysisNamedLabel *label = &policy->named_labels[index];
    if (!validate_policy_section_index_local(diagnostics, object, label->has_section_index, label->section_index))
      return 0;
    if (label->domain != M68K_ANALYSIS_LABEL_DOMAIN_RUNTIME &&
        !validate_policy_offset_local(diagnostics, object, label->has_section_index, label->section_index,
          label->offset, "target metadata label offset is out of range for source file"))
      return 0;
  }
  for (index = 0U; index < policy->entry_comment_count && index < M68K_ANALYSIS_ENTRY_COMMENT_LIMIT; ++index) {
    const M68kAnalysisEntryComment *comment = &policy->entry_comments[index];
    if (!validate_policy_section_index_local(diagnostics, object, comment->has_section_index, comment->section_index))
      return 0;
    if (!validate_policy_offset_local(diagnostics, object, comment->has_section_index, comment->section_index,
          comment->offset, "target metadata entry comment offset is out of range for source file"))
      return 0;
  }
  for (index = 0U; index < policy->runtime_range_count && index < M68K_ANALYSIS_RUNTIME_RANGE_LIMIT; ++index) {
    const M68kAnalysisRuntimeRange *range = &policy->runtime_ranges[index];
    if (!validate_policy_section_index_local(diagnostics, object, range->has_section_index, range->section_index))
      return 0;
    if (!validate_policy_range_local(diagnostics, object, range->has_section_index, range->section_index,
          range->offset, range->size))
      return 0;
  }
  for (index = 0U; index < policy->runtime_entry_point_count &&
       index < M68K_ANALYSIS_RUNTIME_ENTRY_POINT_LIMIT; ++index) {
    const M68kAnalysisRuntimeEntryPoint *entry = &policy->runtime_entry_points[index];
    uint32_t section_index = 0U;
    uint32_t offset = 0U;
    if (!validate_policy_section_index_local(diagnostics, object, entry->has_section_index, entry->section_index))
      return 0;
    if (!policy_runtime_address_to_source_offset_local(policy, entry->runtime_address, &section_index, &offset) ||
        (entry->has_section_index && section_index != entry->section_index)) {
      platform_file_add_error(diagnostics, "target metadata runtime entrypoint is outside execution views");
      return 0;
    }
    if (!validate_policy_offset_local(diagnostics, object, 1U, section_index, offset,
          "target metadata runtime entrypoint is out of range for source file"))
      return 0;
  }
  for (index = 0U; index < policy->manual_representation_count &&
       index < M68K_ANALYSIS_MANUAL_REPRESENTATION_LIMIT; ++index) {
    const M68kAnalysisManualRepresentation *representation = &policy->manual_representations[index];
    if (!validate_policy_section_index_local(diagnostics, object, representation->has_section_index,
        representation->section_index))
      return 0;
    if (!validate_policy_range_local(diagnostics, object, representation->has_section_index,
        representation->section_index, representation->offset, representation->size))
      return 0;
  }
  for (index = 0U; index < policy->manual_runtime_address_ref_count &&
       index < M68K_ANALYSIS_MANUAL_RUNTIME_ADDRESS_REF_LIMIT; ++index) {
    const M68kAnalysisManualRuntimeAddressRef *ref = &policy->manual_runtime_address_refs[index];
    if (!validate_policy_section_index_local(diagnostics, object, ref->has_section_index, ref->section_index))
      return 0;
    if (!validate_policy_range_local(diagnostics, object, ref->has_section_index, ref->section_index,
          ref->offset, ref->size))
      return 0;
    if (!validate_policy_section_index_local(diagnostics, object, ref->has_target, ref->target_section_index))
      return 0;
    if (!validate_policy_offset_local(diagnostics, object, ref->has_target, ref->target_section_index,
          ref->target_offset, "target metadata manual runtime address ref target is out of range"))
      return 0;
  }
  return 1;
}

static int policy_set_raw_entry_address_local(M68kAnalysisPolicy *policy, const M68kObject *object,
    uint32_t entry_address, uint8_t prefer_runtime_address, M68kDiagList *diagnostics) {
  uint32_t section_size = 0U;
  uint32_t section_index = 0U;
  uint32_t offset = 0U;
  if (policy == NULL || object == NULL) return 0;
  policy_section_size_local(object, 1U, 0U, &section_size);
  if (prefer_runtime_address &&
      policy_runtime_address_to_source_offset_local(policy, entry_address, &section_index, &offset)) {
    policy->has_entry_offset = 0U;
    return policy_add_runtime_entry_point_local(policy, section_index, entry_address);
  }
  if (entry_address < section_size) {
    policy->has_entry_offset = 1U;
    policy->entry_offset = entry_address;
    return 1;
  }
  if (policy_runtime_address_to_source_offset_local(policy, entry_address, &section_index, &offset)) {
    policy->has_entry_offset = 0U;
    return policy_add_runtime_entry_point_local(policy, section_index, entry_address);
  }
  platform_file_add_error(diagnostics, "raw entrypoint is outside source bytes and execution views");
  return 0;
}

static int policy_add_raw_runtime_load_range_local(M68kAnalysisPolicy *policy, const M68kObject *object,
    uint8_t has_runtime_load_address, uint32_t runtime_load_address, M68kDiagList *diagnostics) {
  uint32_t section_size = 0U;
  if (policy == NULL || object == NULL || !has_runtime_load_address) return 1;
  if (!policy_section_size_local(object, 1U, 0U, &section_size)) {
    platform_file_add_error(diagnostics, "raw source section is missing");
    return 0;
  }
  if (section_size == 0U) return 1;
  if (policy_add_runtime_range_local(policy, 0U, 0U, section_size, runtime_load_address, "raw_load")) return 1;
  platform_file_add_error(diagnostics, "failed adding raw runtime load range");
  return 0;
}

static uint32_t read_be32_local(const uint8_t *data) {
  return ((uint32_t)data[0] << 24) | ((uint32_t)data[1] << 16) | ((uint32_t)data[2] << 8) | (uint32_t)data[3];
}

static uint16_t read_be16_local(const uint8_t *data) {
  return (uint16_t)(((uint16_t)data[0] << 8) | (uint16_t)data[1]);
}

static int operand_address_reg_index_policy_local(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (out_reg != NULL) *out_reg = 0U;
  if (operand == NULL || out_reg == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_AN) {
    *out_reg = operand->value.reg;
    return 1;
  }
  if ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->value.ea_mode == 1U) {
    *out_reg = operand->value.ea_reg;
    return 1;
  }
  return 0;
}

static int instruction_calls_exec_makelibrary_policy_local(const M68kInstructionIR *instruction) {
  const AmigaOsLibraryVectorInfo *make_library = amiga_os_find_library_vector_by_symbol_name("_LVOMakeLibrary");
  const M68kOperandIR *target_operand = NULL;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  if (make_library == NULL || instruction == NULL || !instruction_is_call_transfer(instruction)) return 0;
  if (!instruction_target_operand_local(instruction, &target_operand) || target_operand == NULL) return 0;
  return operand_is_indirect_or_disp_an(target_operand, &base_reg, &displacement) && base_reg == 6U &&
    displacement == make_library->lvo;
}

static int policy_decode_target_is_instruction_local(const M68kObject *object, const M68kAnalysisPolicy *policy,
    uint32_t hunk, uint32_t offset) {
  SectionAnalysisContext ctx;
  SectionDecodeResult decode;
  if (object == NULL || hunk >= object->section_count) return 0;
  memset(&ctx, 0, sizeof(ctx));
  ctx.object = object;
  ctx.section_index = hunk;
  ctx.section = &object->sections[hunk];
  ctx.analysis_policy = policy;
  return section_analysis_context_probe_decode(&ctx, offset, &decode);
}

static uint32_t resident_vector_prefix_count_local(const char *target_type) {
  size_t prefix_index;
  uint8_t target_type_id = amiga_os_resident_target_type_id(target_type);
  uint32_t count = 0U;
  if (target_type_id == AMIGA_OS_RESIDENT_TARGET_TYPE_NONE) return 0U;
  for (prefix_index = 0U; prefix_index < AMIGA_OS_RESIDENT_VECTOR_PREFIX_COUNT; ++prefix_index) {
    const AmigaOsResidentVectorPrefixInfo *prefix = amiga_os_resident_vector_prefix_at(prefix_index);
    if (prefix == NULL || prefix->target_type_id != target_type_id) continue;
    if (prefix->slot_index + 1U > count) count = prefix->slot_index + 1U;
  }
  return count;
}

static uint32_t fixup_width_bytes_policy_local(const M68kFixup *fixup) {
  if (fixup == NULL) return 0U;
  switch (fixup->width) {
    case M68K_FIXUP_WIDTH_8: return 1U;
    case M68K_FIXUP_WIDTH_16: return 2U;
    case M68K_FIXUP_WIDTH_32: return 4U;
    default: return 0U;
  }
}

static int fixup_target_offset_policy_local(const M68kObject *object, const M68kFixup *fixup,
    uint32_t *out_offset) {
  const M68kSection *source_section;
  const M68kSection *target_section;
  uint32_t width;
  uint32_t target_extent;
  uint32_t raw_value;
  int64_t computed_target;
  if (out_offset != NULL) *out_offset = 0U;
  if (object == NULL || fixup == NULL || out_offset == NULL || !fixup->has_target_section ||
      fixup->section_index >= object->section_count || fixup->target_section_index >= object->section_count) {
    return 0;
  }
  source_section = &object->sections[fixup->section_index];
  target_section = &object->sections[fixup->target_section_index];
  width = fixup_width_bytes_policy_local(fixup);
  target_extent = target_section->size != 0U ? target_section->size : target_section->data_size;
  if (width == 0U || fixup->offset > source_section->data_size || width > source_section->data_size - fixup->offset)
    return 0;
  if (width == 1U) raw_value = source_section->data[fixup->offset];
  else if (width == 2U) raw_value = read_be16_local(source_section->data + fixup->offset);
  else raw_value = read_be32_local(source_section->data + fixup->offset);
  if (fixup->kind == M68K_FIXUP_PC_REL) {
    int32_t signed_value = width == 1U ? (int8_t)raw_value : (width == 2U ? (int16_t)raw_value : (int32_t)raw_value);
    computed_target = (int64_t)fixup->offset + (int64_t)signed_value;
  } else if (fixup->kind == M68K_FIXUP_ABS || fixup->kind == M68K_FIXUP_SECTION_REL) {
    computed_target = raw_value;
  } else {
    return 0;
  }
  if (computed_target < 0 || computed_target > (int64_t)target_extent) return 0;
  *out_offset = (uint32_t)computed_target;
  return 1;
}

static const M68kFixup *find_relocation_fixup_policy_local(const M68kObject *object, uint32_t section_index,
    uint32_t offset, M68kFixupWidth width) {
  size_t fixup_index;
  if (object == NULL) return NULL;
  for (fixup_index = 0U; fixup_index < object->fixup_count; ++fixup_index) {
    const M68kFixup *fixup = &object->fixups[fixup_index];
    if (fixup->section_index == section_index && fixup->offset == offset && fixup->width == width)
      return fixup;
  }
  return NULL;
}

static int policy_probe_relocated_jump_template_entry_local(const M68kObject *object,
    const M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset, uint32_t *out_byte_count,
    ResidentVectorMetadataEntryLocal *out_entry) {
  SectionAnalysisContext ctx;
  SectionDecodeResult decode;
  M68kInstructionIR *instruction;
  const M68kSimFormMetadata *metadata;
  uint32_t cursor;
  uint32_t end;
  if (out_byte_count != NULL) *out_byte_count = 0U;
  if (out_entry != NULL) memset(out_entry, 0, sizeof(*out_entry));
  if (object == NULL || policy == NULL || out_byte_count == NULL || out_entry == NULL ||
      section_index >= object->section_count || object->sections[section_index].data == NULL) {
    return 0;
  }
  memset(&ctx, 0, sizeof(ctx));
  ctx.object = object;
  ctx.section_index = section_index;
  ctx.section = &object->sections[section_index];
  ctx.analysis_policy = policy;
  if (!section_analysis_context_probe_decode(&ctx, offset, &decode)) return 0;
  instruction = &decode.instruction;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL || metadata->flow_kind != M68K_SIM_FLOW_JUMP || metadata->flow_conditional != 0U ||
      instruction->byte_count == 0U || instruction->byte_count > UINT32_MAX - offset) {
    return 0;
  }
  end = offset + (uint32_t)instruction->byte_count;
  for (cursor = offset; cursor < end; ++cursor) {
    const M68kFixup *fixup = find_relocation_fixup_policy_local(object, section_index, cursor, M68K_FIXUP_WIDTH_32);
    uint32_t target_offset = 0U;
    if (fixup == NULL || !fixup->has_target_section || fixup->target_section_index >= object->section_count ||
        !fixup_target_offset_policy_local(object, fixup, &target_offset)) {
      continue;
    }
    if (object->sections[fixup->target_section_index].kind != M68K_SECTION_CODE ||
        target_offset >= object->sections[fixup->target_section_index].data_size || (target_offset & 1U) != 0U ||
        !policy_decode_target_is_instruction_local(object, policy, (uint32_t)fixup->target_section_index,
          target_offset)) {
      continue;
    }
    *out_byte_count = (uint32_t)instruction->byte_count;
    out_entry->hunk = (uint32_t)fixup->target_section_index;
    out_entry->offset = target_offset;
    return 1;
  }
  return 0;
}

static int infer_resident_jump_template_vector_table_local(M68kAnalysisPolicy *policy, const M68kObject *object,
    const char *target_type, const char *library_name, uint32_t library_version) {
  typedef struct ResidentJumpTemplateVectorGroupLocal {
    uint32_t section_index;
    uint32_t offset;
    uint32_t entry_count;
  } ResidentJumpTemplateVectorGroupLocal;
  ResidentJumpTemplateVectorGroupLocal selected;
  uint32_t min_entries = resident_vector_prefix_count_local(target_type);
  uint32_t group_count = 0U;
  size_t section_index;
  if (policy == NULL || object == NULL || min_entries == 0U) return 1;
  memset(&selected, 0, sizeof(selected));
  for (section_index = 0U; section_index < object->section_count; ++section_index) {
    const M68kSection *section = &object->sections[section_index];
    uint32_t offset;
    if (section->data == NULL || section->data_size == 0U) continue;
    for (offset = 0U; offset < section->data_size;) {
      ResidentVectorMetadataEntryLocal entry;
      uint32_t byte_count = 0U;
      uint32_t cursor;
      uint32_t entry_count = 0U;
      if (!policy_probe_relocated_jump_template_entry_local(object, policy, (uint32_t)section_index, offset,
          &byte_count, &entry) || byte_count == 0U) {
        ++offset;
        continue;
      }
      cursor = offset;
      do {
        ++entry_count;
        if (byte_count > UINT32_MAX - cursor) break;
        cursor += byte_count;
      } while (cursor < section->data_size &&
               policy_probe_relocated_jump_template_entry_local(object, policy, (uint32_t)section_index, cursor,
                 &byte_count, &entry) && byte_count != 0U);
      if (entry_count >= min_entries) {
        ++group_count;
        selected.section_index = (uint32_t)section_index;
        selected.offset = offset;
        selected.entry_count = entry_count;
      }
      offset = cursor > offset ? cursor : offset + 1U;
    }
  }
  if (group_count != 1U) return 1;
  {
    uint32_t vector_index;
    uint32_t cursor = selected.offset;
    uint32_t next_private_ordinal = 1U;
    uint32_t first_code_offset = UINT32_MAX;
    if (!policy_add_named_label_local(policy, selected.section_index, selected.offset, "resident_vectors")) return 0;
    for (vector_index = 0U; vector_index < selected.entry_count; ++vector_index) {
      ResidentVectorMetadataEntryLocal entry;
      uint32_t byte_count = 0U;
      if (!policy_probe_relocated_jump_template_entry_local(object, policy, selected.section_index, cursor,
          &byte_count, &entry) || byte_count == 0U) {
        return 0;
      }
      if (!policy_add_resident_vector_entrypoint_local(policy, &entry, vector_index, target_type, library_name,
          library_version, &next_private_ordinal, &first_code_offset, entry.hunk)) {
        return 0;
      }
      cursor += byte_count;
    }
  }
  return 1;
}

static int policy_add_non_autoinit_vector_table_local(M68kAnalysisPolicy *policy, const M68kObject *object,
    uint32_t hunk, uint32_t vectors_offset, const char *target_type, const char *library_name,
    uint32_t library_version, uint32_t *inout_first_code_offset) {
  typedef struct ResidentVectorTableEntryLocal {
    uint32_t item_offset;
    uint32_t target;
  } ResidentVectorTableEntryLocal;
  ResidentVectorTableEntryLocal entries[M68K_ANALYSIS_ENTRY_POINT_LIMIT];
  const M68kSection *section;
  uint32_t cursor;
  uint32_t entry_count = 0U;
  uint32_t vector_index = 0U;
  uint32_t next_private_ordinal = 1U;
  uint8_t entry_size;
  if (policy == NULL || object == NULL || hunk >= object->section_count) return 0;
  section = &object->sections[hunk];
  if (section->data == NULL || vectors_offset >= section->data_size) return 0;
  if (vectors_offset + 2U <= section->data_size && read_be16_local(section->data + vectors_offset) == 0xFFFFU) {
    entry_size = 2U;
    cursor = vectors_offset + 2U;
  } else {
    entry_size = 4U;
    cursor = vectors_offset;
  }
  while (cursor + entry_size <= section->data_size) {
    uint32_t target;
    if (entry_size == 2U) {
      int16_t displacement = (int16_t)read_be16_local(section->data + cursor);
      if (displacement == -1) break;
      target = (uint32_t)((int32_t)vectors_offset + (int32_t)displacement);
    } else {
      target = read_be32_local(section->data + cursor);
      if (target == 0xFFFFFFFFU) break;
    }
    if (entry_count >= M68K_ANALYSIS_ENTRY_POINT_LIMIT) return 0;
    if (target >= section->data_size || !policy_decode_target_is_instruction_local(object, policy, hunk, target))
      return 0;
    entries[entry_count].item_offset = cursor;
    entries[entry_count].target = target;
    ++entry_count;
    cursor += entry_size;
  }
  if (cursor + entry_size > section->data_size || entry_count == 0U) return 0;
  if (!policy_add_named_label_local(policy, hunk, vectors_offset, "resident_vectors")) return 0;
  for (vector_index = 0U; vector_index < entry_count; ++vector_index) {
    ResidentVectorMetadataEntryLocal entry;
    uint16_t item_index;
    item_index = policy->structured_data_item_count;
    if (!policy_add_structured_data_item_section_local(policy, 1U, hunk, entries[vector_index].item_offset,
        entry_size, entry_size == 2U ? M68K_ANALYSIS_STRUCTURED_DATA_WORDS : M68K_ANALYSIS_STRUCTURED_DATA_LONGS,
        NULL))
      return 0;
    if (entry_size == 4U &&
        !policy_set_structured_data_item_target_local(policy, item_index, hunk, entries[vector_index].target))
      return 0;
    memset(&entry, 0, sizeof(entry));
    entry.hunk = hunk;
    entry.offset = entries[vector_index].target;
    if (!policy_add_resident_vector_entrypoint_local(policy, &entry, vector_index, target_type, library_name,
        library_version, &next_private_ordinal, inout_first_code_offset, hunk))
      return 0;
  }
  if (!policy_add_structured_data_item_section_local(policy, 1U, hunk, cursor, entry_size,
      entry_size == 2U ? M68K_ANALYSIS_STRUCTURED_DATA_WORDS : M68K_ANALYSIS_STRUCTURED_DATA_LONGS, NULL))
    return 0;
  return 1;
}

static int policy_source_operand_target_local(const SectionAnalysisContext *ctx, const M68kInstructionIR *instruction,
    uint32_t instruction_offset, size_t operand_index, uint32_t *out_target) {
  const M68kSimFormMetadata *metadata;
  size_t target_section = SIZE_MAX;
  uint32_t target_offset = UINT32_MAX;
  if (out_target != NULL) *out_target = 0U;
  if (ctx == NULL || instruction == NULL || out_target == NULL || operand_index >= instruction->operand_count)
    return 0;
  if (instruction_operand_absolute_target_ref(ctx, instruction, operand_index, instruction_offset, &target_section,
      &target_offset) && target_section == ctx->section_index) {
    *out_target = target_offset;
    return 1;
  }
  metadata = instruction_sim_metadata(instruction);
  return instruction_render_operand_target(instruction, metadata, (uint8_t)operand_index, instruction_offset,
    ctx->section != NULL ? ctx->section->data_size : 0U, out_target);
}

static int enrich_policy_from_non_autoinit_resident_make_library_local(M68kAnalysisPolicy *policy,
    const M68kObject *object, uint32_t hunk, uint32_t init_offset, const char *target_type,
    const char *library_name, uint32_t library_version) {
  SectionAnalysisContext ctx;
  uint32_t addr_reg_targets[8];
  uint32_t addr_reg_known = 0U;
  uint32_t cursor;
  uint32_t scan_count;
  uint32_t first_code_offset = UINT32_MAX;
  if (policy == NULL || object == NULL || hunk >= object->section_count) return 0;
  if (object->sections[hunk].data == NULL || init_offset >= object->sections[hunk].data_size) return 0;
  memset(addr_reg_targets, 0, sizeof(addr_reg_targets));
  memset(&ctx, 0, sizeof(ctx));
  ctx.object = object;
  ctx.section_index = hunk;
  ctx.section = &object->sections[hunk];
  ctx.analysis_policy = policy;
  cursor = init_offset;
  for (scan_count = 0U; scan_count < 256U && cursor < ctx.section->data_size; ++scan_count) {
    SectionDecodeResult decode;
    M68kInstructionIR *instruction;
    uint8_t reg;
    if (!section_analysis_context_probe_decode(&ctx, cursor, &decode)) break;
    instruction = &decode.instruction;
    if (instruction_calls_exec_makelibrary_policy_local(instruction) && m68k_bitset_u32_has(addr_reg_known, 0U)) {
      return policy_add_non_autoinit_vector_table_local(policy, object, hunk, addr_reg_targets[0], target_type,
        library_name, library_version, &first_code_offset);
    }
    for (reg = 0U; reg < 8U; ++reg) {
      if (instruction_writes_address_reg_approx(instruction, reg)) m68k_bitset_u32_clear(&addr_reg_known, reg);
    }
    if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U &&
        operand_address_reg_index_policy_local(&instruction->operands[1], &reg) && reg < 8U &&
        policy_source_operand_target_local(&ctx, instruction, cursor, 0U, &addr_reg_targets[reg])) {
      m68k_bitset_u32_set(&addr_reg_known, reg);
    } else {
      const M68kOperandIR *source = NULL;
      if (instruction_is_address_move(instruction, &reg, &source) && reg < 8U && source != NULL &&
          policy_source_operand_target_local(&ctx, instruction, cursor, 0U, &addr_reg_targets[reg])) {
        m68k_bitset_u32_set(&addr_reg_known, reg);
      }
    }
    if (decode.is_call) addr_reg_known = 0U;
    if (decode.stops_fallthrough) break;
    cursor += (uint32_t)instruction->byte_count;
  }
  return 1;
}

static const char *resident_pointer_target_label_local(const M68kAnalysisStructuredDataItem *item) {
  if (item == NULL || item->struct_id != AMIGA_OS_STRUCT_ID_RT) return NULL;
  if (item->field_id == AMIGA_OS_FIELD_ID_RT_NAME) return "resident_name";
  if (item->field_id == AMIGA_OS_FIELD_ID_RT_IDSTRING) return "resident_idstring";
  return NULL;
}

static uint32_t nul_terminated_string_size_local(const M68kSection *section, uint32_t offset) {
  uint32_t cursor;
  if (section == NULL || section->data == NULL || offset >= section->data_size) return 0U;
  for (cursor = offset; cursor < section->data_size; ++cursor) {
    if (section->data[cursor] == 0U) return cursor - offset + 1U;
  }
  return 0U;
}

static void enrich_policy_pointer_targets_from_object_local(M68kAnalysisPolicy *policy, const M68kObject *object) {
  uint16_t index;
  if (policy == NULL || object == NULL || object->sections == NULL) return;
  for (index = 0U; index < policy->structured_data_item_count && index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT;
       ++index) {
    M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    const char *target_label;
    uint32_t section_index;
    const M68kSection *section;
    uint32_t target_offset;
    if (!item->is_pointer || item->has_target || item->size != 4U) continue;
    section_index = item->has_section_index ? item->section_index : 0U;
    if (section_index >= object->section_count) continue;
    section = &object->sections[section_index];
    if (section->data == NULL || item->offset > section->data_size || 4U > section->data_size - item->offset) continue;
    target_offset = read_be32_local(section->data + item->offset);
    if (target_offset != 0U && target_offset < section->size) {
      item->has_target = 1U;
      item->target_section = section_index;
      item->target_offset = target_offset;
      m68k_analysis_structured_data_item_refresh_table_metadata(item);
      target_label = resident_pointer_target_label_local(item);
      if (target_label != NULL && target_label[0] != '\0') {
        uint32_t string_size = nul_terminated_string_size_local(section, target_offset);
        (void)policy_add_named_label_local(policy, section_index, target_offset, target_label);
        if (string_size != 0U) {
          (void)policy_add_structured_data_item_section_local(policy, 1U, section_index, target_offset, string_size,
            M68K_ANALYSIS_STRUCTURED_DATA_STRING, NULL);
        }
      }
    }
  }
}

static int metadata_target_type_local(const char *metadata_path, char *out, size_t out_size) {
  char *text;
  if (out != NULL && out_size != 0U) out[0] = '\0';
  if (metadata_path == NULL || metadata_path[0] == '\0') return 1;
  text = read_text_file_local(metadata_path);
  if (text == NULL) return 0;
  if (!json_optional_string_field_local(text, text + strlen(text), "target_type", out, out_size)) {
    free(text);
    return 0;
  }
  free(text);
  return 1;
}

static int policy_has_resident_struct_policy_local(const M68kAnalysisPolicy *policy) {
  uint16_t index;
  if (policy == NULL) return 0;
  for (index = 0U; index < policy->structured_data_item_count && index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT;
       ++index) {
    const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    if (item->struct_id == AMIGA_OS_STRUCT_ID_RT ||
        item->platform_kind_id == M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_KIND_AMIGA_RESIDENT_AUTOINIT)
      return 1;
  }
  for (index = 0U; index < policy->named_label_count && index < M68K_ANALYSIS_NAMED_LABEL_LIMIT; ++index) {
    const M68kAnalysisNamedLabel *label = &policy->named_labels[index];
    if (strcmp(label->name, "resident") == 0) return 1;
  }
  return 0;
}

static int enrich_policy_from_object_target_info_local(M68kAnalysisPolicy *policy, const M68kBackend *backend,
    const M68kObject *object, char *target_type, size_t target_type_size, M68kDiagList *diagnostics) {
  char *inspect_json = NULL;
  char inspected_target_type[64];
  uint8_t inspected_target_type_id;
  const char *backend_name = backend != NULL ? backend->name : NULL;
  inspected_target_type[0] = '\0';
  if (policy == NULL || object == NULL) return 0;
  if (object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 0;
  if (backend_name == NULL) backend_name = "amiga-hunk";
  if (object_target_metadata_json(backend, object, &inspect_json) != 0 || inspect_json == NULL) {
    platform_file_add_error(diagnostics, "failed extracting target metadata");
    free(inspect_json);
    return -1;
  }
  (void)json_optional_string_field_local(inspect_json, inspect_json + strlen(inspect_json), "target_type",
    inspected_target_type, sizeof(inspected_target_type));
  if (target_type != NULL && target_type_size != 0U && target_type[0] == '\0' && inspected_target_type[0] != '\0')
    (void)copy_policy_text(target_type, target_type_size, inspected_target_type);
  inspected_target_type_id = metadata_target_type_id_from_text_local(inspected_target_type);
  if (metadata_target_type_disables_implicit_entries_local(inspected_target_type_id))
    policy->disable_implicit_entry_points = 1U;
  if (platform_name_uses_amiga_metadata_policy_local(backend_name)) {
    M68kDiagList ignored_diagnostics;
    const char *resident_end = NULL;
    const char *resident_start = json_find_object_field_local(inspect_json, "resident", &resident_end);
    if (resident_start != NULL) {
      const char *autoinit_end = NULL;
      const char *autoinit_start = json_find_nested_object_field_local(resident_start, resident_end, "autoinit",
        &autoinit_end);
      char library_name[64];
      uint32_t hunk = 0U;
      uint32_t init_offset = 0U;
      uint32_t library_version = 0U;
      int has_hunk = 0;
      int has_init_offset = 0;
      int has_library_version = 0;
      library_name[0] = '\0';
      if (!policy_has_resident_struct_policy_local(policy)) {
        m68k_diag_list_reset(&ignored_diagnostics);
        if (append_metadata_amiga_policy_text_local(inspect_json, policy, m68k_diag_sink(&ignored_diagnostics)) != 0) {
          free(inspect_json);
          return 0;
        }
      }
      if (!json_number_field_local(resident_start, resident_end, "hunk", &hunk, &has_hunk) ||
          !json_number_field_local(resident_start, resident_end, "init_offset", &init_offset, &has_init_offset) ||
          !json_optional_string_field_local(resident_start, resident_end, "name", library_name, sizeof(library_name)) ||
          !json_number_field_local(resident_start, resident_end, "version", &library_version, &has_library_version)) {
        free(inspect_json);
        return 0;
      }
      if (autoinit_start != NULL) {
        (void)repair_metadata_resident_vector_sections_local(autoinit_start, autoinit_end, policy,
          has_hunk ? hunk : 0U, inspected_target_type, library_name, has_library_version ? library_version : 0U);
      } else if (has_init_offset) {
        (void)enrich_policy_from_non_autoinit_resident_make_library_local(policy, object, has_hunk ? hunk : 0U,
          init_offset, inspected_target_type, library_name, has_library_version ? library_version : 0U);
      }
      if (!infer_resident_jump_template_vector_table_local(policy, object, inspected_target_type, library_name,
          has_library_version ? library_version : 0U)) {
        free(inspect_json);
        return 0;
      }
    } else {
      m68k_diag_list_reset(&ignored_diagnostics);
      if (append_metadata_amiga_policy_text_local(inspect_json, policy, m68k_diag_sink(&ignored_diagnostics)) != 0) {
        free(inspect_json);
        return 0;
      }
    }
  }
  free(inspect_json);
  return 0;
}

static int append_effective_analysis_policy_json_local(JsonBuilder *builder, const M68kAnalysisPolicy *policy) {
  uint16_t index;
  if (builder == NULL || policy == NULL) return -1;
  if (json_builder_appendf(builder,
        "\"analysis_policy\":{\"max_cpu\":%u,\"implicit_entry_points\":%s,"
        "\"entry_point_count\":%u,\"register_seed_count\":%u,"
        "\"structured_data_item_count\":%u,\"named_label_count\":%u,\"entry_comment_count\":%u,"
        "\"runtime_range_count\":%u,\"runtime_entry_point_count\":%u,\"rsset_layout_region_count\":%u,"
        "\"manual_representation_count\":%u,\"custom_struct_count\":%u",
        (unsigned)policy->max_cpu, policy->disable_implicit_entry_points ? "false" : "true",
        (unsigned)policy->entry_point_count, (unsigned)policy->register_seed_count,
        (unsigned)policy->structured_data_item_count, (unsigned)policy->named_label_count,
        (unsigned)policy->entry_comment_count, (unsigned)policy->runtime_range_count,
        (unsigned)policy->runtime_entry_point_count, (unsigned)policy->rsset_layout_region_count,
        (unsigned)policy->manual_representation_count, (unsigned)policy->custom_struct_count) != 0)
    return -1;
  if (json_builder_append(builder, ",\"entrypoints\":[") != 0) return -1;
  for (index = 0U; index < policy->entry_point_count && index < M68K_ANALYSIS_ENTRY_POINT_LIMIT; ++index) {
    const M68kAnalysisEntryPoint *entry = &policy->entry_points[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"section_index\":") != 0) return -1;
    if (append_nullable_u32_json_local(builder, entry->has_section_index, entry->section_index) != 0) return -1;
    if (json_builder_appendf(builder, ",\"offset\":%u,\"provenance\":", (unsigned)entry->offset) != 0) return -1;
    if (json_builder_append_json_string(builder, analysis_entry_point_provenance_name_local(entry->provenance)) != 0)
      return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  if (json_builder_append(builder, "],\"register_seeds\":[") != 0) return -1;
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    char reg_name[4];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    snprintf(reg_name, sizeof(reg_name), "%c%u",
      seed->reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS ? 'A' : 'D', (unsigned)seed->reg_index);
    if (json_builder_append(builder, "{\"section_index\":") != 0) return -1;
    if (append_nullable_u32_json_local(builder, seed->has_section_index, seed->section_index) != 0) return -1;
    if (json_builder_append(builder, ",\"entry_offset\":") != 0) return -1;
    if (append_nullable_u32_json_local(builder, seed->has_entry_offset, seed->entry_offset) != 0) return -1;
    if (json_builder_append(builder, ",\"register\":") != 0) return -1;
    if (json_builder_append_json_string(builder, reg_name) != 0) return -1;
    if (json_builder_append(builder, ",\"reg_kind\":") != 0) return -1;
    if (json_builder_append_json_string(builder, analysis_register_kind_name_local(seed->reg_kind)) != 0) return -1;
    if (json_builder_appendf(builder, ",\"reg_index\":%u,\"kind\":", (unsigned)seed->reg_index) != 0) return -1;
    if (json_builder_append_json_string(builder, analysis_register_seed_kind_name_local(seed->kind)) != 0) return -1;
    if (json_builder_append(builder, ",\"name\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, seed->name) != 0) return -1;
    if (json_builder_append(builder, ",\"type_name\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, seed->type_name) != 0) return -1;
    if (json_builder_append(builder, ",\"context_name\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, seed->context_name) != 0) return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  if (json_builder_append(builder, "],\"structured_data_items\":[") != 0) return -1;
  for (index = 0U; index < policy->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"section_index\":") != 0) return -1;
    if (append_nullable_u32_json_local(builder, item->has_section_index, item->section_index) != 0) return -1;
    if (json_builder_appendf(builder, ",\"offset\":%u,\"size\":%u,\"kind\":", (unsigned)item->offset,
          (unsigned)item->size) != 0)
      return -1;
    if (json_builder_append_json_string(builder, structured_data_kind_name_local(item->kind)) != 0) return -1;
    if (json_builder_append(builder, ",\"comment\":") != 0) return -1;
    if (append_structured_data_text_json_local(builder, item, M68K_ANALYSIS_STRUCTURED_DATA_TEXT_COMMENT) != 0)
      return -1;
    if (json_builder_append(builder, ",\"label\":") != 0) return -1;
    if (append_structured_data_text_json_local(builder, item, M68K_ANALYSIS_STRUCTURED_DATA_TEXT_LABEL) != 0)
      return -1;
    if (json_builder_append(builder, ",\"struct_name\":") != 0) return -1;
    if (append_structured_data_text_json_local(builder, item, M68K_ANALYSIS_STRUCTURED_DATA_TEXT_STRUCT_NAME) != 0)
      return -1;
    if (json_builder_append(builder, ",\"field_name\":") != 0) return -1;
    if (append_structured_data_text_json_local(builder, item, M68K_ANALYSIS_STRUCTURED_DATA_TEXT_FIELD_NAME) != 0)
      return -1;
    if (json_builder_appendf(builder,
          ",\"platform_kind_id\":%u,\"platform_field_id\":%u,\"struct_id\":%u,\"field_id\":%u",
          (unsigned)item->platform_kind_id, (unsigned)item->platform_field_id, (unsigned)item->struct_id,
          (unsigned)item->field_id) != 0)
      return -1;
    if (json_builder_append(builder, ",\"field_type\":") != 0) return -1;
    if (append_structured_data_text_json_local(builder, item, M68K_ANALYSIS_STRUCTURED_DATA_TEXT_FIELD_TYPE) != 0)
      return -1;
    if (json_builder_append(builder, ",\"c_type\":") != 0) return -1;
    if (append_structured_data_text_json_local(builder, item, M68K_ANALYSIS_STRUCTURED_DATA_TEXT_C_TYPE) != 0)
      return -1;
    if (json_builder_append(builder, ",\"pointer_struct\":") != 0) return -1;
    if (append_structured_data_text_json_local(builder, item, M68K_ANALYSIS_STRUCTURED_DATA_TEXT_POINTER_STRUCT) != 0)
      return -1;
    if (json_builder_appendf(builder, ",\"pointer_struct_id\":%u", (unsigned)item->pointer_struct_id) != 0)
      return -1;
    if (json_builder_append(builder, ",\"value_domain\":") != 0) return -1;
    if (append_structured_data_text_json_local(builder, item, M68K_ANALYSIS_STRUCTURED_DATA_TEXT_VALUE_DOMAIN) != 0)
      return -1;
    if (json_builder_append(builder, ",\"constant_name\":") != 0) return -1;
    if (append_structured_data_text_json_local(builder, item, M68K_ANALYSIS_STRUCTURED_DATA_TEXT_CONSTANT_NAME) != 0)
      return -1;
    if (json_builder_appendf(builder, ",\"has_constant_value\":%s,\"constant_value\":",
          item->has_constant_value ? "true" : "false") != 0)
      return -1;
    if (item->has_constant_value) {
      if (json_builder_appendf(builder, "%d", (int)item->constant_value) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) return -1;
    if (json_builder_append(builder, ",\"semantic_role\":") != 0) return -1;
    if (append_structured_data_text_json_local(builder, item, M68K_ANALYSIS_STRUCTURED_DATA_TEXT_SEMANTIC_ROLE) != 0)
      return -1;
    if (json_builder_appendf(builder, ",\"semantic_role_flags\":%u",
          (unsigned)structured_data_item_role_flags_local(item)) != 0)
      return -1;
    {
      const char *source_pattern = m68k_analysis_structured_data_source_pattern_name(item->source_pattern_id);
      if (json_builder_appendf(builder, ",\"source_pattern_id\":%u,\"source_pattern\":",
            (unsigned)item->source_pattern_id) != 0)
        return -1;
      if (append_nullable_text_json_local(builder, source_pattern) != 0) return -1;
    }
    if (json_builder_appendf(builder, ",\"table_kind_id\":%u,\"table_kind\":",
          (unsigned)item->table_kind_id) != 0)
      return -1;
    if (append_nullable_text_json_local(builder, m68k_analysis_table_kind_name(item->table_kind_id)) != 0)
      return -1;
    if (json_builder_appendf(builder, ",\"table_base_expression_id\":%u,\"table_base_expression\":",
          (unsigned)item->table_base_expression_id) != 0)
      return -1;
    if (append_nullable_text_json_local(builder,
          m68k_analysis_table_base_expression_name(item->table_base_expression_id)) != 0)
      return -1;
    if (json_builder_appendf(builder, ",\"is_pointer\":%s,\"target_section\":",
          item->is_pointer ? "true" : "false") != 0)
      return -1;
    if (append_nullable_u32_json_local(builder, item->has_target, item->target_section) != 0) return -1;
    if (json_builder_append(builder, ",\"target_offset\":") != 0) return -1;
    if (append_nullable_u32_json_local(builder, item->has_target, item->target_offset) != 0) return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  if (json_builder_append(builder, "],\"rsset_layout_regions\":[") != 0) return -1;
  for (index = 0U; index < policy->rsset_layout_region_count && index < M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT; ++index) {
    const M68kAnalysisRssetLayoutRegion *slot = &policy->rsset_layout_regions[index];
    const char *storage_kind = slot->storage_kind[0] != '\0'
      ? slot->storage_kind
      : rsset_layout_region_storage_kind_name_local(slot->storage_kind_id);
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_appendf(builder, "{\"offset\":%u,\"size\":%u,\"flags\":%u,\"storage_kind_id\":%u,\"layout_name\":",
          (unsigned)slot->offset, (unsigned)slot->size, (unsigned)slot->flags, (unsigned)slot->storage_kind_id) != 0)
      return -1;
    if (append_nullable_text_json_local(builder, slot->layout_name) != 0) return -1;
    if (json_builder_append(builder, ",\"base_symbol\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, slot->base_symbol) != 0) return -1;
    if (json_builder_append(builder, ",\"sizeof_symbol\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, slot->sizeof_symbol) != 0) return -1;
    if (json_builder_append(builder, ",\"symbol\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, slot->symbol) != 0) return -1;
    if (json_builder_append(builder, ",\"struct_name\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, slot->struct_name) != 0) return -1;
    if (json_builder_append(builder, ",\"pointer_struct\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, slot->pointer_struct) != 0) return -1;
    if (json_builder_append(builder, ",\"storage_kind\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, storage_kind) != 0) return -1;
    if (json_builder_append(builder, ",\"semantic_type\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, slot->semantic_type) != 0) return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  if (json_builder_append(builder, "],\"named_labels\":[") != 0) return -1;
  for (index = 0U; index < policy->named_label_count && index < M68K_ANALYSIS_NAMED_LABEL_LIMIT; ++index) {
    const M68kAnalysisNamedLabel *label = &policy->named_labels[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"section_index\":") != 0) return -1;
    if (append_nullable_u32_json_local(builder, label->has_section_index, label->section_index) != 0) return -1;
    if (json_builder_appendf(builder, ",\"offset\":%u,\"domain\":%u,\"name\":", (unsigned)label->offset,
          (unsigned)label->domain) != 0)
      return -1;
    if (json_builder_append_json_string(builder, label->name) != 0) return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  if (json_builder_append(builder, "],\"entry_comments\":[") != 0) return -1;
  for (index = 0U; index < policy->entry_comment_count && index < M68K_ANALYSIS_ENTRY_COMMENT_LIMIT; ++index) {
    const M68kAnalysisEntryComment *comment = &policy->entry_comments[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"section_index\":") != 0) return -1;
    if (append_nullable_u32_json_local(builder, comment->has_section_index, comment->section_index) != 0) return -1;
    if (json_builder_appendf(builder, ",\"offset\":%u,\"comment\":", (unsigned)comment->offset) != 0) return -1;
    if (json_builder_append_json_string(builder, comment->comment) != 0) return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  if (json_builder_append(builder, "],\"runtime_ranges\":[") != 0) return -1;
  for (index = 0U; index < policy->runtime_range_count && index < M68K_ANALYSIS_RUNTIME_RANGE_LIMIT; ++index) {
    const M68kAnalysisRuntimeRange *range = &policy->runtime_ranges[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"section_index\":") != 0) return -1;
    if (append_nullable_u32_json_local(builder, range->has_section_index, range->section_index) != 0) return -1;
    if (json_builder_appendf(builder, ",\"offset\":%u,\"size\":%u,\"runtime_address\":%u,\"name\":",
          (unsigned)range->offset, (unsigned)range->size, (unsigned)range->runtime_address) != 0)
      return -1;
    if (append_nullable_text_json_local(builder, range->name) != 0) return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  if (json_builder_append(builder, "],\"runtime_entry_points\":[") != 0) return -1;
  for (index = 0U; index < policy->runtime_entry_point_count &&
       index < M68K_ANALYSIS_RUNTIME_ENTRY_POINT_LIMIT; ++index) {
    const M68kAnalysisRuntimeEntryPoint *entry = &policy->runtime_entry_points[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"section_index\":") != 0) return -1;
    if (append_nullable_u32_json_local(builder, entry->has_section_index, entry->section_index) != 0) return -1;
    if (json_builder_appendf(builder, ",\"runtime_address\":%u}", (unsigned)entry->runtime_address) != 0)
      return -1;
  }
  if (json_builder_append(builder, "],\"custom_structs\":[") != 0) return -1;
  for (index = 0U; policy->custom_structs != NULL && index < policy->custom_struct_count &&
       index < M68K_ANALYSIS_CUSTOM_STRUCT_LIMIT; ++index) {
    const M68kAnalysisCustomStruct *custom_struct = &policy->custom_structs[index];
    uint16_t field_index;
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"name\":") != 0 ||
        json_builder_append_json_string(builder, custom_struct->name) != 0 ||
        json_builder_appendf(builder, ",\"size\":%u,\"fields\":[", (unsigned)custom_struct->size) != 0)
      return -1;
    for (field_index = 0U; field_index < custom_struct->field_count &&
         field_index < M68K_ANALYSIS_CUSTOM_STRUCT_FIELD_LIMIT; ++field_index) {
      const M68kAnalysisCustomStructField *field = &custom_struct->fields[field_index];
      if (field_index != 0U && json_builder_append(builder, ",") != 0) return -1;
      if (json_builder_append(builder, "{\"name\":") != 0 ||
          json_builder_append_json_string(builder, field->name) != 0 ||
          json_builder_append(builder, ",\"type\":") != 0 ||
          append_nullable_text_json_local(builder, field->type_name) != 0 ||
          json_builder_appendf(builder, ",\"offset\":%u,\"size\":%u,\"struct\":",
            (unsigned)field->offset, (unsigned)field->size) != 0 ||
          append_nullable_text_json_local(builder, field->struct_name) != 0 ||
          json_builder_append(builder, ",\"pointer_struct\":") != 0 ||
          append_nullable_text_json_local(builder, field->pointer_struct) != 0 ||
          json_builder_append(builder, ",\"named_base\":") != 0 ||
          append_nullable_text_json_local(builder, field->named_base) != 0 ||
          json_builder_append(builder, "}") != 0)
        return -1;
    }
    if (json_builder_append(builder, "]}") != 0) return -1;
  }
  if (json_builder_append(builder, "],\"target_equates\":[") != 0) return -1;
  for (index = 0U; index < policy->target_equate_count && index < M68K_ANALYSIS_TARGET_EQUATE_LIMIT; ++index) {
    const M68kAnalysisTargetEquate *equate = &policy->target_equates[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"name\":") != 0 ||
        json_builder_append_json_string(builder, equate->name) != 0 ||
        json_builder_appendf(builder, ",\"value\":%d", (int)equate->value) != 0)
      return -1;
    if (equate->value_style_id != M68K_ANALYSIS_REPRESENTATION_STYLE_NONE) {
      if (json_builder_append(builder, ",\"value_representation\":") != 0 ||
          json_builder_append_json_string(builder, manual_representation_style_name_local(equate->value_style_id)) != 0)
        return -1;
    }
    if (equate->value_expr[0] != '\0') {
      if (json_builder_append(builder, ",\"value_expression\":") != 0 ||
          json_builder_append_json_string(builder, equate->value_expr) != 0)
        return -1;
    }
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  if (json_builder_append(builder, "],\"manual_representations\":[") != 0) return -1;
  for (index = 0U; index < policy->manual_representation_count &&
       index < M68K_ANALYSIS_MANUAL_REPRESENTATION_LIMIT; ++index) {
    const M68kAnalysisManualRepresentation *representation = &policy->manual_representations[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"section_index\":") != 0) return -1;
    if (append_nullable_u32_json_local(builder, representation->has_section_index,
        representation->section_index) != 0)
      return -1;
    if (json_builder_appendf(builder, ",\"offset\":%u,\"size\":%u,\"style\":",
          (unsigned)representation->offset, (unsigned)representation->size) != 0)
      return -1;
    if (json_builder_append_json_string(builder,
        manual_representation_style_name_local(representation->style_id)) != 0)
      return -1;
    if (representation->has_operand_index &&
        json_builder_appendf(builder, ",\"operand_index\":%u", (unsigned)representation->operand_index) != 0)
      return -1;
    if (representation->symbol_id != 0U) {
      const char *symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, representation->symbol_id);
      if (symbol_name != NULL && symbol_name[0] != '\0' &&
          (json_builder_append(builder, ",\"symbol\":") != 0 ||
           json_builder_append_json_string(builder, symbol_name) != 0))
        return -1;
    } else if (representation->target_equate_index != 0U &&
        representation->target_equate_index <= policy->target_equate_count) {
      const M68kAnalysisTargetEquate *equate = &policy->target_equates[representation->target_equate_index - 1U];
      if (equate->name[0] != '\0' &&
          (json_builder_append(builder, ",\"symbol\":") != 0 ||
           json_builder_append_json_string(builder, equate->name) != 0))
        return -1;
    }
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  return json_builder_append(builder, "]}");
}

static int effective_policy_json_to_alloc(const char *platform_name, const char *path, const char *metadata_path,
    const char *entry_offsets, uint8_t is_raw, uint32_t raw_entry_address, uint8_t raw_has_runtime_load_address,
    uint32_t raw_runtime_load_address, char **out_text) {
  Arena *scratch_arena = NULL;
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  M68kObject object;
  JsonBuilder builder = {0};
  char target_type[64];
  uint32_t analysis_start;
  int object_loaded = 0;
  m68k_diag_list_reset(&diagnostics);
  if (out_text == NULL) return -1;
  *out_text = NULL;
  target_type[0] = '\0';
  scratch_arena = arena_create(4096U);
  analysis_policy = scratch_arena != NULL
    ? (M68kAnalysisPolicy *)arena_calloc(scratch_arena, 1U, sizeof(*analysis_policy))
    : NULL;
  if (analysis_policy == NULL) {
    PlatformFileTextResult error_result;
    memset(&error_result, 0, sizeof(error_result));
    platform_file_add_error(&error_result.diagnostics, "out of memory");
    arena_destroy(scratch_arena);
    return text_result_to_alloc(&error_result, out_text);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, platform_name, metadata_path, entry_offsets,
        &diagnostics) != 0 ||
      !metadata_target_type_local(metadata_path, target_type, sizeof(target_type))) {
    PlatformFileTextResult error_result;
    memset(&error_result, 0, sizeof(error_result));
    error_result.diagnostics = diagnostics;
    if (!m68k_diag_has_errors(&error_result.diagnostics))
      platform_file_add_error(&error_result.diagnostics, "failed reading target metadata");
    {
      int rc = text_result_to_alloc(&error_result, out_text);
      arena_destroy(scratch_arena);
      return rc;
    }
  }
  if (is_raw) {
    if (load_raw_object_from_path(platform_name, path, &object, m68k_diag_sink(&diagnostics)) != 0) {
      PlatformFileTextResult error_result;
      memset(&error_result, 0, sizeof(error_result));
      error_result.diagnostics = diagnostics;
      {
        int rc = text_result_to_alloc(&error_result, out_text);
        arena_destroy(scratch_arena);
        return rc;
      }
    }
  } else {
    const M68kBackend *backend = m68k_backend_by_name(platform_name);
    if (load_object_from_path(backend, path, &object, m68k_diag_sink(&diagnostics)) != 0) {
      PlatformFileTextResult error_result;
      memset(&error_result, 0, sizeof(error_result));
      error_result.diagnostics = diagnostics;
      {
        int rc = text_result_to_alloc(&error_result, out_text);
        arena_destroy(scratch_arena);
        return rc;
      }
    }
    if (enrich_policy_from_object_target_info_local(analysis_policy, backend, &object, target_type, sizeof(target_type),
          &diagnostics) != 0) {
      PlatformFileTextResult error_result;
      memset(&error_result, 0, sizeof(error_result));
      error_result.diagnostics = diagnostics;
      m68k_object_destroy(&object);
      {
        int rc = text_result_to_alloc(&error_result, out_text);
        arena_destroy(scratch_arena);
        return rc;
      }
    }
  }
  object_loaded = 1;
  if (is_raw) {
    if (!policy_add_raw_runtime_load_range_local(analysis_policy, &object, raw_has_runtime_load_address,
          raw_runtime_load_address, &diagnostics) ||
        !policy_set_raw_entry_address_local(analysis_policy, &object, raw_entry_address,
          raw_has_runtime_load_address, &diagnostics)) {
      PlatformFileTextResult error_result;
      memset(&error_result, 0, sizeof(error_result));
      error_result.diagnostics = diagnostics;
      m68k_object_destroy(&object);
      {
        int rc = text_result_to_alloc(&error_result, out_text);
        arena_destroy(scratch_arena);
        return rc;
      }
    }
  }
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&diagnostics, &object, analysis_policy)) {
    PlatformFileTextResult error_result;
    memset(&error_result, 0, sizeof(error_result));
    error_result.diagnostics = diagnostics;
    m68k_object_destroy(&object);
    {
      int rc = text_result_to_alloc(&error_result, out_text);
      arena_destroy(scratch_arena);
      return rc;
    }
  }
  analysis_start = effective_policy_analysis_start_local(analysis_policy, is_raw ? raw_entry_address : 0U);
  if (json_builder_create(&builder) != 0) goto oom;
  if (json_builder_append(&builder, "{\"platform\":") != 0) goto oom;
  if (json_builder_append_json_string(&builder, platform_name != NULL ? platform_name : "") != 0) goto oom;
  if (json_builder_append(&builder, ",\"path\":") != 0) goto oom;
  if (json_builder_append_json_string(&builder, path != NULL ? path : "") != 0) goto oom;
  if (json_builder_append(&builder, ",\"source_kind\":") != 0) goto oom;
  if (json_builder_append_json_string(&builder, is_raw ? "raw" : "file") != 0) goto oom;
  if (json_builder_append(&builder, ",\"target_type\":") != 0) goto oom;
  if (append_nullable_text_json_local(&builder, target_type) != 0) goto oom;
  if (json_builder_appendf(&builder, ",\"analysis_start\":%u,\"diagnostics\":[],",
        (unsigned)analysis_start) != 0)
    goto oom;
  if (append_effective_analysis_policy_json_local(&builder, analysis_policy) != 0) goto oom;
  if (json_builder_append(&builder, "}\n") != 0) goto oom;
  *out_text = json_builder_build(&builder);
  if (*out_text == NULL) goto oom;
  json_builder_destroy(&builder);
  m68k_object_destroy(&object);
  arena_destroy(scratch_arena);
  return 0;

oom:
  json_builder_destroy(&builder);
  if (object_loaded) m68k_object_destroy(&object);
  arena_destroy(scratch_arena);
  *out_text = m68k_platform_dup_string("out of memory");
  return -1;
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

static int load_raw_object_from_path(const char *platform_name, const char *path, M68kObject *object,
    M68kDiagSink diagnostics) {
  unsigned char *data = NULL;
  size_t size = 0U;
  int result;
  if (read_file_to_buffer(path, &data, &size, diagnostics) != 0) return -1;
  result = load_raw_object_from_buffer(platform_name, data, size, object, diagnostics);
  free(data);
  return result;
}

static int load_raw_object_from_buffer(const char *platform_name, const unsigned char *data, size_t size,
    M68kObject *object, M68kDiagSink diagnostics) {
  M68kSection section;
  M68kObjectAddResult add_result;
  const M68kBackend *backend = m68k_raw_backend_by_name(platform_name);
  unsigned char *section_data;
  if (backend == NULL || object == NULL || data == NULL || size > UINT32_MAX) {
    platform_file_add_error(diagnostics.list, "unknown raw platform backend");
    return -1;
  }
  section_data = (unsigned char *)malloc(size != 0U ? size : 1U);
  if (section_data == NULL) {
    platform_file_add_error(diagnostics.list, "out of memory");
    return -1;
  }
  if (size != 0U) memcpy(section_data, data, size);
  if (m68k_object_create(object) != 0) {
    free(section_data);
    platform_file_add_error(diagnostics.list, "out of memory");
    return -1;
  }
  object->platform_backend_kind = backend->platform_kind;
  object->platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  m68k_object_mark_no_container(object);
  memset(&section, 0, sizeof(section));
  section.name = "code";
  section.kind = M68K_SECTION_CODE;
  section.alignment = 2U;
  section.size = (uint32_t)size;
  section.data = section_data;
  section.data_size = (uint32_t)size;
  add_result = m68k_object_add_section(object, &section);
  free(section_data);
  if (!add_result.ok) {
    m68k_object_destroy(object);
    platform_file_add_error(diagnostics.list, "out of memory");
    return -1;
  }
  return 0;
}

static int load_flat_m68k_object_from_buffer(const unsigned char *data, size_t size, M68kObject *object,
    M68kDiagSink diagnostics) {
  M68kSection section;
  M68kObjectAddResult add_result;
  unsigned char *section_data;
  if (object == NULL || data == NULL || size > UINT32_MAX) {
    platform_file_add_error(diagnostics.list, "invalid flat M68K buffer");
    return -1;
  }
  section_data = (unsigned char *)malloc(size != 0U ? size : 1U);
  if (section_data == NULL) {
    platform_file_add_error(diagnostics.list, "out of memory");
    return -1;
  }
  if (size != 0U) memcpy(section_data, data, size);
  if (m68k_object_create(object) != 0) {
    free(section_data);
    platform_file_add_error(diagnostics.list, "out of memory");
    return -1;
  }
  object->platform_backend_kind = M68K_PLATFORM_BACKEND_UNKNOWN;
  object->platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  m68k_object_mark_no_container(object);
  memset(&section, 0, sizeof(section));
  section.name = "code";
  section.kind = M68K_SECTION_CODE;
  section.alignment = 2U;
  section.size = (uint32_t)size;
  section.data = section_data;
  section.data_size = (uint32_t)size;
  add_result = m68k_object_add_section(object, &section);
  free(section_data);
  if (!add_result.ok) {
    m68k_object_destroy(object);
    platform_file_add_error(diagnostics.list, "out of memory");
    return -1;
  }
  return 0;
}

static int configure_flat_m68k_buffer_policy(M68kAnalysisPolicy *policy, const M68kObject *object,
    const char *metadata_path, M68kDiagList *diagnostics) {
  if (policy == NULL || object == NULL) return -1;
  m68k_analysis_policy_init_default(policy);
  if (metadata_path != NULL && metadata_path[0] != '\0' &&
      platform_file_analysis_policy_load_target_metadata(policy, metadata_path, m68k_diag_sink(diagnostics)) != 0) {
    return -1;
  }
  return policy_set_raw_entry_address_local(policy, object, 0U, 0U, diagnostics) ? 0 : -1;
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

static void platform_file_add_warning(M68kDiagList *diagnostics, const char *message) {
  if (message == NULL || message[0] == '\0') message = "platform file warning";
  m68k_diag_add(m68k_diag_sink(diagnostics), M68K_DIAG_SEVERITY_WARNING, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, message);
}

static const char *facts_v2_source_export_failure_kind_name(M68kSourceExportFailureKind kind) {
  switch (kind) {
    case M68K_SOURCE_EXPORT_FAILURE_RENDER: return "render";
    case M68K_SOURCE_EXPORT_FAILURE_BYTE_MISMATCH: return "byte_mismatch";
    case M68K_SOURCE_EXPORT_FAILURE_INSTRUCTION_RELOCATION: return "instruction_relocation";
    case M68K_SOURCE_EXPORT_FAILURE_UNRESOLVED_LABEL: return "unresolved_label";
    case M68K_SOURCE_EXPORT_FAILURE_INTERIOR_CONFLICT: return "interior_conflict";
    case M68K_SOURCE_EXPORT_FAILURE_RELOCATION: return "relocation";
    case M68K_SOURCE_EXPORT_FAILURE_RELOCATION_ANCHOR: return "relocation_anchor";
    case M68K_SOURCE_EXPORT_FAILURE_UNASSEMBLABLE_HUNK_DATA_RELOCATION:
      return "unassemblable_hunk_data_relocation";
    case M68K_SOURCE_EXPORT_FAILURE_UNASSEMBLABLE_HUNK_BASE_REGISTER_RELOCATION:
      return "unassemblable_hunk_base_register_relocation";
    case M68K_SOURCE_EXPORT_FAILURE_REQUIRED_INSTRUCTION: return "required_instruction";
    case M68K_SOURCE_EXPORT_FAILURE_TABLE_TARGET_SET_LIMIT: return "table_target_set_limit";
    case M68K_SOURCE_EXPORT_FAILURE_SOURCE_QUALITY: return "source_quality";
    default: return "";
  }
}

static const char *facts_v2_relocation_failure_reason_name(uint32_t reason) {
  switch (reason) {
    case M68K_FACTS_V2_RELOCATION_FAILURE_INVALID_FIXUP: return "invalid_fixup";
    case M68K_FACTS_V2_RELOCATION_FAILURE_BAD_WIDTH: return "bad_width";
    case M68K_FACTS_V2_RELOCATION_FAILURE_PAYLOAD_OUT_OF_DATA: return "payload_out_of_data";
    case M68K_FACTS_V2_RELOCATION_FAILURE_UNSUPPORTED_KIND: return "unsupported_kind";
    case M68K_FACTS_V2_RELOCATION_FAILURE_TARGET_OUT_OF_RANGE: return "target_out_of_range";
    default: return "";
  }
}

static const char *facts_v2_relocation_anchor_kind_name(uint32_t kind) {
  switch (kind) {
    case M68K_FACTS_V2_RELOCATION_ANCHOR_POSITIVE: return "positive";
    case M68K_FACTS_V2_RELOCATION_ANCHOR_NEGATIVE: return "negative";
    default: return "";
  }
}

static const char *facts_v2_relocation_anchor_context_name(uint32_t context) {
  switch (context) {
    case M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_INSTRUCTION_BYTES: return "instruction_bytes";
    case M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_DATA_PAYLOAD: return "data_payload";
    case M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_UNKNOWN: return "unknown";
    case M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_BASE_REGISTER: return "base_register_anchor";
    default: return "";
  }
}

static const char *facts_v2_code_start_reason_name(uint32_t reason) {
  switch (reason) {
    case M68K_FACTS_V2_CODE_START_REASON_SECTION_ENTRY: return "section_entry";
    case M68K_FACTS_V2_CODE_START_REASON_POLICY_ENTRY_OFFSET: return "policy_entry_offset";
    case M68K_FACTS_V2_CODE_START_REASON_POLICY_ENTRY_POINT: return "policy_entry_point";
    case M68K_FACTS_V2_CODE_START_REASON_CONTROL_TARGET: return "control_target";
    case M68K_FACTS_V2_CODE_START_REASON_FALLTHROUGH: return "fallthrough";
    case M68K_FACTS_V2_CODE_START_REASON_INLINE_RESUME: return "inline_resume";
    case M68K_FACTS_V2_CODE_START_REASON_RUNTIME_VIEW_ENTRY: return "runtime_view_entry";
    case M68K_FACTS_V2_CODE_START_REASON_LINKAGE_API_ENTRY: return "linkage_api_entry";
    case M68K_FACTS_V2_CODE_START_REASON_PLATFORM_LOADSEG_ENTRY: return "platform_loadseg_entry";
    case M68K_FACTS_V2_CODE_START_REASON_STACK_CONTINUATION: return "stack_continuation";
    case M68K_FACTS_V2_CODE_START_REASON_BOUNDARY_API_ENTRY: return "boundary_api_entry";
    default: return "";
  }
}

static const char *facts_v2_hunk_record_kind_name(uint32_t record_kind) {
  switch ((AmigaHunkFileRecordKind)record_kind) {
    case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32: return "hunk_reloc32";
    case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC16: return "hunk_reloc16";
    case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC8: return "hunk_reloc8";
    case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_DREL32: return "hunk_drel32";
    case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_DREL16: return "hunk_drel16";
    case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_DREL8: return "hunk_drel8";
    case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELRELOC32: return "hunk_relreloc32";
    case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_ABSRELOC16: return "hunk_absreloc16";
    case AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32SHORT: return "hunk_reloc32short";
    default: return "";
  }
}

static int json_builder_append_facts_v2_profile(JsonBuilder *builder, const M68kFactsV2Profile *profile) {
  if (builder == NULL || profile == NULL) return -1;
  return json_builder_appendf(builder,
    "{"
    "\"decode_seconds\":%.6f,"
    "\"seed_seconds\":%.6f,"
    "\"fixed_point_seconds\":%.6f,"
    "\"fixed_point_reachable_seconds\":%.6f,"
    "\"fixed_point_reachable_decode_seconds\":%.6f,"
    "\"fixed_point_reachable_validate_seconds\":%.6f,"
    "\"fixed_point_reachable_accept_seconds\":%.6f,"
    "\"fixed_point_reachable_target_seconds\":%.6f,"
    "\"fixed_point_reachable_relocation_seconds\":%.6f,"
    "\"fixed_point_reachable_fallthrough_seconds\":%.6f,"
    "\"fixed_point_index_seconds\":%.6f,"
    "\"fixed_point_required_label_conflict_seconds\":%.6f,"
    "\"fixed_point_opcode_relocation_conflict_seconds\":%.6f,"
    "\"fixed_point_rebuild_accepted_seconds\":%.6f,"
    "\"fixed_point_relocation_anchor_seconds\":%.6f,"
    "\"fixed_point_materialize_labels_seconds\":%.6f,"
    "\"fixed_point_runtime_address_ref_seconds\":%.6f,"
    "\"fixed_point_required_label_materialize_seconds\":%.6f,"
    "\"fixed_point_data_span_seconds\":%.6f,"
    "\"fixed_point_invariant_seconds\":%.6f,"
    "\"render_ir_seconds\":%.6f,"
    "\"render_ir_lookup_seconds\":%.6f,"
    "\"platform_analysis_pass_seconds\":%.6f,"
    "\"platform_analysis_base_slot_seconds\":%.6f,"
    "\"platform_analysis_call_summary_seconds\":%.6f,"
    "\"platform_analysis_typed_ref_seconds\":%.6f,"
    "\"platform_analysis_call_comment_seconds\":%.6f,"
    "\"platform_analysis_app_slot_seconds\":%.6f,"
    "\"platform_analysis_runtime_data_seconds\":%.6f,"
    "\"platform_analysis_hardware_data_seconds\":%.6f,"
    "\"platform_analysis_generic_data_seconds\":%.6f,"
    "\"render_ir_header_seconds\":%.6f,"
    "\"render_ir_walk_seconds\":%.6f,"
    "\"render_ir_footer_seconds\":%.6f,"
    "\"source_render_seconds\":%.6f,"
    "\"decoded_candidates\":%u,"
    "\"accepted_instructions\":%u,"
    "\"data_spans\":%u,"
    "\"labels_created\":%u,"
    "\"labels_referenced\":%u,"
    "\"unresolved_labels\":%u,"
    "\"interior_conflicts\":%u,"
    "\"interior_conflicts_resolved_by_demote\":%u,"
    "\"interior_conflicts_unresolved\":%u,"
    "\"relocation_failures\":%u,"
    "\"first_relocation_failure_reason\":\"%s\","
    "\"first_relocation_failure_section\":%u,"
    "\"first_relocation_failure_offset\":%u,"
    "\"first_relocation_failure_target_section\":%u,"
    "\"first_relocation_failure_width\":%u,"
    "\"first_relocation_failure_raw_value\":%u,"
    "\"first_relocation_failure_computed_target\":%" PRId64 ","
    "\"relocation_anchors\":%u,"
    "\"first_relocation_anchor_kind\":\"%s\","
    "\"first_relocation_anchor_section\":%u,"
    "\"first_relocation_anchor_offset\":%u,"
    "\"first_relocation_anchor_target_section\":%u,"
    "\"first_relocation_anchor_width\":%u,"
    "\"first_relocation_anchor_platform_record_kind\":\"%s\","
    "\"first_relocation_anchor_raw_value\":%u,"
    "\"first_relocation_anchor_addend\":%" PRId64 ","
    "\"relocation_anchor_instruction_bytes\":%u,"
    "\"relocation_anchor_data_payloads\":%u,"
    "\"relocation_anchor_unknown_contexts\":%u,"
    "\"unassemblable_hunk_data_relocations\":%u,"
    "\"unassemblable_hunk_base_register_relocations\":%u,"
    "\"first_relocation_anchor_context\":\"%s\","
    "\"first_relocation_anchor_instruction_offset\":%u,"
    "\"code_start_facts\":%u,"
    "\"code_start_section_entries\":%u,"
    "\"code_start_policy_entry_offsets\":%u,"
    "\"code_start_policy_entry_points\":%u,"
    "\"code_start_control_targets\":%u,"
    "\"code_start_fallthroughs\":%u,"
    "\"code_start_inline_resumes\":%u,"
    "\"code_start_linkage_api_entries\":%u,"
    "\"code_start_platform_loadseg_entries\":%u,"
    "\"code_start_stack_continuations\":%u,"
    "\"code_start_boundary_api_entries\":%u,"
    "\"platform_loadseg_segment_link_accesses\":%u,"
    "\"platform_loadseg_segment_link_bptr_loads\":%u,"
    "\"platform_loadseg_segment_link_resolved_targets\":%u,"
    "\"first_platform_loadseg_segment_link_section\":%u,"
    "\"first_platform_loadseg_segment_link_offset\":%u,"
    "\"first_platform_loadseg_segment_link_target_section\":%u,"
    "\"runtime_address_ranges\":%u,"
    "\"runtime_address_range_conflicts\":%u,"
    "\"table_target_set_limit_hits\":%u,"
    "\"first_table_target_set_limit_section\":%u,"
    "\"first_table_target_set_limit_offset\":%u,"
    "\"first_table_target_set_limit_capacity\":%u,"
    "\"source_quality_diagnostics\":%u,"
    "\"source_quality_blockers\":%u,"
    "\"first_source_quality_diagnostic_kind\":\"%s\","
    "\"first_source_quality_diagnostic_section\":%u,"
    "\"first_source_quality_diagnostic_offset\":%u,"
    "\"runtime_address_view_starts\":%u,"
    "\"required_instruction_failures\":%u,"
    "\"unsupported_instruction_demotes\":%u,"
    "\"first_required_instruction_failure_section\":%u,"
    "\"first_required_instruction_failure_offset\":%u,"
    "\"first_required_instruction_failure_reason\":\"%s\","
    "\"first_required_instruction_failure_source_section\":%u,"
    "\"first_required_instruction_failure_source_offset\":%u,"
    "\"first_unsupported_instruction_demote_section\":%u,"
    "\"first_unsupported_instruction_demote_offset\":%u,"
    "\"first_unsupported_instruction_demote_reason\":\"%s\","
    "\"first_unsupported_instruction_demote_source_section\":%u,"
    "\"first_unsupported_instruction_demote_source_offset\":%u,"
    "\"opcode_relocation_conflicts_resolved_by_demote\":%u,"
    "\"first_opcode_relocation_conflict_section\":%u,"
    "\"first_opcode_relocation_conflict_offset\":%u,"
    "\"first_opcode_relocation_conflict_aux_offset\":%u,"
    "\"queue_iterations\":%u,"
    "\"workflow_arena_peak_used\":%u,"
    "\"workflow_arena_total_blocks\":%u,"
    "\"render_ir_statements\":%u,"
    "\"render_ir_labels\":%u,"
    "\"render_ir_instructions\":%u,"
    "\"render_ir_data_spans\":%u,"
    "\"render_ir_hash\":\"%016" PRIx64 "\","
    "\"preview_source_enabled\":%s,"
    "\"preview_source_bytes\":%u,"
    "\"preview_source_hash\":\"%016" PRIx64 "\","
    "\"asm_source_enabled\":%s,"
    "\"asm_source_refused\":%s,"
    "\"asm_source_bytes\":%u,"
    "\"asm_source_lines\":%u,"
    "\"asm_source_plan_rows\":%u,"
    "\"asm_source_plan_lines\":%u,"
    "\"asm_source_plan_bytes\":%u,"
    "\"asm_source_relocation_exprs\":%u,"
    "\"asm_source_symbolic_instructions\":%u,"
    "\"asm_source_numeric_runtime_refs\":%u,"
    "\"asm_source_first_numeric_runtime_ref_section\":%u,"
    "\"asm_source_first_numeric_runtime_ref_offset\":%u,"
    "\"asm_source_first_numeric_runtime_ref_target_section\":%u,"
    "\"asm_source_first_numeric_runtime_ref_target_offset\":%u,"
    "\"asm_source_first_numeric_runtime_ref_runtime_address\":%u,"
    "\"platform_base_slot_count\":%u,"
    "\"platform_call_count\":%u,"
    "\"platform_effect_count\":%u,"
    "\"asm_source_lossy_numeric_hunk_relocations\":%u,"
    "\"asm_source_instruction_render_failures\":%u,"
    "\"asm_source_instruction_byte_mismatches\":%u,"
    "\"asm_source_instruction_relocation_failures\":%u,"
    "\"asm_source_relocation_anchor_refusals\":%u,"
    "\"asm_source_unassemblable_hunk_data_relocation_refusals\":%u,"
    "\"asm_source_unassemblable_hunk_base_register_relocation_refusals\":%u,"
    "\"asm_source_first_failure_kind\":\"%s\","
    "\"asm_source_first_failure_section\":%u,"
    "\"asm_source_first_failure_offset\":%u,"
    "\"asm_source_first_failure_aux_offset\":%u,"
    "\"asm_source_hash\":\"%016" PRIx64 "\""
    "}",
    profile->decode_seconds,
    profile->seed_seconds,
    profile->fixed_point_seconds,
    profile->fixed_point_reachable_seconds,
    profile->fixed_point_reachable_decode_seconds,
    profile->fixed_point_reachable_validate_seconds,
    profile->fixed_point_reachable_accept_seconds,
    profile->fixed_point_reachable_target_seconds,
    profile->fixed_point_reachable_relocation_seconds,
    profile->fixed_point_reachable_fallthrough_seconds,
    profile->fixed_point_index_seconds,
    profile->fixed_point_required_label_conflict_seconds,
    profile->fixed_point_opcode_relocation_conflict_seconds,
    profile->fixed_point_rebuild_accepted_seconds,
    profile->fixed_point_relocation_anchor_seconds,
    profile->fixed_point_materialize_labels_seconds,
    profile->fixed_point_runtime_address_ref_seconds,
    profile->fixed_point_required_label_materialize_seconds,
    profile->fixed_point_data_span_seconds,
    profile->fixed_point_invariant_seconds,
    profile->render_ir_seconds,
    profile->render_ir_lookup_seconds,
    profile->platform_analysis_pass_seconds,
    profile->platform_analysis_base_slot_seconds,
    profile->platform_analysis_call_summary_seconds,
    profile->platform_analysis_typed_ref_seconds,
    profile->platform_analysis_call_comment_seconds,
    profile->platform_analysis_app_slot_seconds,
    profile->platform_analysis_runtime_data_seconds,
    profile->platform_analysis_hardware_data_seconds,
    profile->platform_analysis_generic_data_seconds,
    profile->render_ir_header_seconds,
    profile->render_ir_walk_seconds,
    profile->render_ir_footer_seconds,
    profile->source_render_seconds,
    (unsigned)profile->decoded_candidates,
    (unsigned)profile->accepted_instructions,
    (unsigned)profile->data_spans,
    (unsigned)profile->labels_created,
    (unsigned)profile->labels_referenced,
    (unsigned)profile->unresolved_labels,
    (unsigned)profile->interior_conflicts,
    (unsigned)profile->interior_conflicts_resolved_by_demote,
    (unsigned)profile->interior_conflicts_unresolved,
    (unsigned)profile->relocation_failures,
    facts_v2_relocation_failure_reason_name(profile->first_relocation_failure_reason),
    (unsigned)profile->first_relocation_failure_section,
    (unsigned)profile->first_relocation_failure_offset,
    (unsigned)profile->first_relocation_failure_target_section,
    (unsigned)profile->first_relocation_failure_width,
    (unsigned)profile->first_relocation_failure_raw_value,
    (int64_t)profile->first_relocation_failure_computed_target,
    (unsigned)profile->relocation_anchors,
    facts_v2_relocation_anchor_kind_name(profile->first_relocation_anchor_kind),
    (unsigned)profile->first_relocation_anchor_section,
    (unsigned)profile->first_relocation_anchor_offset,
    (unsigned)profile->first_relocation_anchor_target_section,
    (unsigned)profile->first_relocation_anchor_width,
    facts_v2_hunk_record_kind_name(profile->first_relocation_anchor_platform_record_kind),
    (unsigned)profile->first_relocation_anchor_raw_value,
    (int64_t)profile->first_relocation_anchor_addend,
    (unsigned)profile->relocation_anchor_instruction_bytes,
    (unsigned)profile->relocation_anchor_data_payloads,
    (unsigned)profile->relocation_anchor_unknown_contexts,
    (unsigned)profile->unassemblable_hunk_data_relocations,
    (unsigned)profile->unassemblable_hunk_base_register_relocations,
    facts_v2_relocation_anchor_context_name(profile->first_relocation_anchor_context),
    (unsigned)profile->first_relocation_anchor_instruction_offset,
    (unsigned)profile->code_start_facts,
    (unsigned)profile->code_start_section_entries,
    (unsigned)profile->code_start_policy_entry_offsets,
    (unsigned)profile->code_start_policy_entry_points,
    (unsigned)profile->code_start_control_targets,
    (unsigned)profile->code_start_fallthroughs,
    (unsigned)profile->code_start_inline_resumes,
    (unsigned)profile->code_start_linkage_api_entries,
    (unsigned)profile->code_start_platform_loadseg_entries,
    (unsigned)profile->code_start_stack_continuations,
    (unsigned)profile->code_start_boundary_api_entries,
    (unsigned)profile->platform_loadseg_segment_link_accesses,
    (unsigned)profile->platform_loadseg_segment_link_bptr_loads,
    (unsigned)profile->platform_loadseg_segment_link_resolved_targets,
    (unsigned)profile->first_platform_loadseg_segment_link_section,
    (unsigned)profile->first_platform_loadseg_segment_link_offset,
    (unsigned)profile->first_platform_loadseg_segment_link_target_section,
    (unsigned)profile->runtime_address_ranges,
    (unsigned)profile->runtime_address_range_conflicts,
    (unsigned)profile->table_target_set_limit_hits,
    (unsigned)profile->first_table_target_set_limit_section,
    (unsigned)profile->first_table_target_set_limit_offset,
    (unsigned)profile->first_table_target_set_limit_capacity,
    (unsigned)profile->source_quality_diagnostics,
    (unsigned)profile->source_quality_blockers,
    m68k_source_quality_diagnostic_kind_name((uint8_t)profile->first_source_quality_diagnostic_kind),
    (unsigned)profile->first_source_quality_diagnostic_section,
    (unsigned)profile->first_source_quality_diagnostic_offset,
    (unsigned)profile->runtime_address_view_starts,
    (unsigned)profile->required_instruction_failures,
    (unsigned)profile->unsupported_instruction_demotes,
    (unsigned)profile->first_required_instruction_failure_section,
    (unsigned)profile->first_required_instruction_failure_offset,
    facts_v2_code_start_reason_name(profile->first_required_instruction_failure_reason),
    (unsigned)profile->first_required_instruction_failure_source_section,
    (unsigned)profile->first_required_instruction_failure_source_offset,
    (unsigned)profile->first_unsupported_instruction_demote_section,
    (unsigned)profile->first_unsupported_instruction_demote_offset,
    facts_v2_code_start_reason_name(profile->first_unsupported_instruction_demote_reason),
    (unsigned)profile->first_unsupported_instruction_demote_source_section,
    (unsigned)profile->first_unsupported_instruction_demote_source_offset,
    (unsigned)profile->opcode_relocation_conflicts_resolved_by_demote,
    (unsigned)profile->first_opcode_relocation_conflict_section,
    (unsigned)profile->first_opcode_relocation_conflict_offset,
    (unsigned)profile->first_opcode_relocation_conflict_aux_offset,
    (unsigned)profile->queue_iterations,
    (unsigned)profile->workflow_arena_peak_used,
    (unsigned)profile->workflow_arena_total_blocks,
    (unsigned)profile->render_ir_statements,
    (unsigned)profile->render_ir_labels,
    (unsigned)profile->render_ir_instructions,
    (unsigned)profile->render_ir_data_spans,
    (uint64_t)profile->render_ir_hash,
    profile->preview_source_enabled != 0U ? "true" : "false",
    (unsigned)profile->preview_source_bytes,
    (uint64_t)profile->preview_source_hash,
    profile->asm_source_enabled != 0U ? "true" : "false",
    profile->asm_source_refused != 0U ? "true" : "false",
    (unsigned)profile->asm_source_bytes,
    (unsigned)profile->asm_source_lines,
    (unsigned)profile->asm_source_plan_rows,
    (unsigned)profile->asm_source_plan_lines,
    (unsigned)profile->asm_source_plan_bytes,
    (unsigned)profile->asm_source_relocation_exprs,
    (unsigned)profile->asm_source_symbolic_instructions,
    (unsigned)profile->asm_source_numeric_runtime_refs,
    (unsigned)profile->asm_source_first_numeric_runtime_ref_section,
    (unsigned)profile->asm_source_first_numeric_runtime_ref_offset,
    (unsigned)profile->asm_source_first_numeric_runtime_ref_target_section,
    (unsigned)profile->asm_source_first_numeric_runtime_ref_target_offset,
    (unsigned)profile->asm_source_first_numeric_runtime_ref_runtime_address,
    (unsigned)profile->platform_base_slot_count,
    (unsigned)profile->platform_call_count,
    (unsigned)profile->platform_effect_count,
    (unsigned)profile->asm_source_lossy_numeric_hunk_relocations,
    (unsigned)profile->asm_source_instruction_render_failures,
    (unsigned)profile->asm_source_instruction_byte_mismatches,
    (unsigned)profile->asm_source_instruction_relocation_failures,
    (unsigned)profile->asm_source_relocation_anchor_refusals,
    (unsigned)profile->asm_source_unassemblable_hunk_data_relocation_refusals,
    (unsigned)profile->asm_source_unassemblable_hunk_base_register_relocation_refusals,
    facts_v2_source_export_failure_kind_name(profile->asm_source_first_failure_kind),
    (unsigned)profile->asm_source_first_failure_section,
    (unsigned)profile->asm_source_first_failure_offset,
    (unsigned)profile->asm_source_first_failure_aux_offset,
    (uint64_t)profile->asm_source_hash);
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

static char *assembler_profile_json_alloc_local(const M68kPlatformAssembleProfile *profile) {
  JsonBuilder builder;
  char *text;
  if (profile == NULL) return m68k_platform_dup_string("{}");
  if (json_builder_create(&builder) != 0) return NULL;
  if (json_builder_appendf(&builder,
      "{\"assemble_c_api\":true"
        ",\"parse_layout_seconds\":%.6f"
        ",\"emit_object_seconds\":%.6f"
        ",\"platform_finalize_seconds\":%.6f"
        ",\"write_buffer_seconds\":%.6f"
        ",\"write_file_seconds\":%.6f"
        ",\"read_output_seconds\":%.6f"
      ",\"total_seconds\":%.6f"
      ",\"source_bytes\":%u"
      ",\"rebuilt_bytes\":%u"
      "}",
        profile->parse_layout_seconds,
        profile->emit_object_seconds,
        profile->platform_finalize_seconds,
        profile->write_buffer_seconds,
        profile->write_file_seconds,
      profile->read_output_seconds,
      profile->total_seconds,
      (unsigned)profile->source_bytes,
      (unsigned)profile->rebuilt_bytes) != 0) {
    json_builder_destroy(&builder);
    return NULL;
  }
  text = json_builder_build(&builder);
  json_builder_destroy(&builder);
  return text;
}

static int write_bytes_to_path_local(const char *path, const unsigned char *data, size_t size,
    M68kDiagList *diagnostics) {
  FILE *output;
  if (path == NULL || path[0] == '\0') return 0;
  output = fopen(path, "wb");
  if (output == NULL) {
    platform_file_add_error(diagnostics, "failed opening direct rebuild output");
    return -1;
  }
  if (size != 0U && fwrite(data, 1, size, output) != size) {
    fclose(output);
    platform_file_add_error(diagnostics, "failed writing direct rebuild output");
    return -1;
  }
  if (fclose(output) != 0) {
    platform_file_add_error(diagnostics, "failed closing direct rebuild output");
    return -1;
  }
  return 0;
}

static const char *direct_compare_status_text(const M68kReproductionCompareResult *result) {
  if (result == NULL) return "not_compared";
  switch (result->status_id) {
  case M68K_REPRO_COMPARE_STATUS_FULL_FILE_EXACT: return "full_file_exact";
  case M68K_REPRO_COMPARE_STATUS_CONTENT_EXACT: return "semantic_container_oddity";
  case M68K_REPRO_COMPARE_STATUS_MISMATCH: return "binary_mismatch";
  case M68K_REPRO_COMPARE_STATUS_INVALID_ARGUMENT: return "invalid_argument";
  default: return "not_compared";
  }
}

static int direct_compare_payload_exact(const M68kReproductionCompareResult *result) {
  return result != NULL && (result->exactness_id == M68K_REPRO_COMPARE_EXACTNESS_FULL_FILE ||
    result->exactness_id == M68K_REPRO_COMPARE_EXACTNESS_CONTENT);
}

static int direct_compare_relocation_exact(const M68kReproductionCompareResult *result) {
  return result != NULL && (result->exactness_id == M68K_REPRO_COMPARE_EXACTNESS_FULL_FILE ||
    result->exactness_id == M68K_REPRO_COMPARE_EXACTNESS_CONTENT);
}

static int json_builder_append_direct_compare_source_hints(JsonBuilder *builder,
    const M68kReproductionCompareResult *result) {
  uint32_t index;
  if (builder == NULL || result == NULL) return -1;
  if (json_builder_append(builder, "[") != 0) return -1;
  for (index = 0U; index < result->source_hint_count; ++index) {
    const M68kReproductionCompareSourceHint *hint = &result->source_hints[index];
    if ((index != 0U && json_builder_append(builder, ",") != 0) ||
        json_builder_appendf(builder,
          "{\"issue_group_flags\":%u,\"section_index\":%u,\"offset\":%u}",
          (unsigned)hint->issue_group_flags, (unsigned)hint->section_index,
          (unsigned)hint->offset) != 0)
      return -1;
  }
  return json_builder_append(builder, "]");
}

static const char *repro_compare_layout_kind_text(uint32_t kind_id) {
  switch (kind_id) {
  case 1U: return "header";
  case 2U: return "section_header";
  case 3U: return "section_payload";
  case 4U: return "section_end";
  case 5U: return "relocation";
  case 6U: return "symbol_table";
  case 7U: return "symbol";
  case 8U: return "debug";
  case 9U: return "external";
  default: return "unknown";
  }
}

static const char *repro_compare_diagnostic_kind_text(uint32_t kind_id) {
  switch (kind_id) {
  case 1U: return "atari_header_field_mismatch";
  case 2U: return "atari_relocation_size_mismatch";
  default: return "container_shape_diagnostic";
  }
}

static const char *repro_compare_atari_field_text(uint32_t field_id) {
  switch (field_id) {
  case 1U: return "text_size";
  case 2U: return "data_size";
  case 3U: return "bss_size";
  case 4U: return "symbol_size";
  case 5U: return "symbol_table_type";
  case 6U: return "flags";
  case 7U: return "relocation_flag";
  default: return "";
  }
}

static int json_builder_append_repro_compare_layout(JsonBuilder *builder,
    const M68kReproductionCompareResult *result) {
  uint32_t index;
  if (builder == NULL || result == NULL) return -1;
  if (json_builder_append(builder, "[") != 0) return -1;
  for (index = 0U; index < result->layout_count; ++index) {
    const M68kReproductionCompareLayoutRange *range = &result->layout[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"kind\":") != 0 ||
        json_builder_append_json_string(builder, repro_compare_layout_kind_text(range->kind_id)) != 0 ||
        json_builder_appendf(builder, ",\"file_start\":%u,\"file_end\":%u,\"length\":%u",
          (unsigned)range->file_start, (unsigned)range->file_end,
          (unsigned)(range->file_end > range->file_start ? range->file_end - range->file_start : 0U)) != 0)
      return -1;
    if (range->has_section_index) {
      if (json_builder_appendf(builder,
            ",\"section_index\":%u,\"hunk\":%u,\"section_offset_start\":%u",
            (unsigned)range->section_index, (unsigned)range->section_index,
            (unsigned)range->section_offset_start) != 0)
        return -1;
    }
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  return json_builder_append(builder, "]");
}

static int json_builder_append_repro_compare_diagnostics(JsonBuilder *builder,
    const M68kReproductionCompareResult *result) {
  uint32_t index;
  if (builder == NULL || result == NULL) return -1;
  if (json_builder_append(builder, "[") != 0) return -1;
  for (index = 0U; index < result->diagnostic_count; ++index) {
    const M68kReproductionCompareDiagnostic *diagnostic = &result->diagnostics[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"kind\":") != 0 ||
        json_builder_append_json_string(builder, repro_compare_diagnostic_kind_text(diagnostic->kind_id)) != 0)
      return -1;
    if (diagnostic->field_id != 0U) {
      if (json_builder_append(builder, ",\"field\":") != 0 ||
          json_builder_append_json_string(builder, repro_compare_atari_field_text(diagnostic->field_id)) != 0)
        return -1;
    }
    if (json_builder_appendf(builder, ",\"original\":%u,\"rebuilt\":%u}",
          (unsigned)diagnostic->original_value, (unsigned)diagnostic->rebuilt_value) != 0)
      return -1;
  }
  return json_builder_append(builder, "]");
}

static M68kReproductionCompareResult facts_v2_direct_compare_result(const char *backend_name,
    const M68kBackend *backend, const M68kObject *original_object, const unsigned char *rebuilt_data,
    size_t rebuilt_size, const unsigned char *compare_data, size_t compare_size,
    const M68kAssemblerPolicy *assembler_policy, Arena *workflow_arena) {
  M68kReproductionCompareResult result;
  m68k_reproduction_compare_init_result(&result);
  (void)backend_name;
  if (compare_data == NULL) return result;
  if (backend == NULL || backend->read_buffer == NULL || original_object == NULL || rebuilt_data == NULL) {
    M68kReproductionCompareContext context;
    memset(&context, 0, sizeof(context));
    context.original_bytes = compare_data;
    context.original_size = compare_size;
    context.rebuilt_bytes = rebuilt_data;
    context.rebuilt_size = rebuilt_size;
    context.backend_kind = original_object != NULL ? original_object->platform_backend_kind : M68K_PLATFORM_BACKEND_UNKNOWN;
    context.assembler_policy = assembler_policy;
    context.workflow_arena = workflow_arena;
    m68k_reproduction_compare(&context, &result);
    return result;
  }
  {
    M68kObject rebuilt_object;
    M68kDiagList diagnostics;
    M68kReproductionCompareContext context;
    m68k_diag_list_reset(&diagnostics);
    memset(&rebuilt_object, 0, sizeof(rebuilt_object));
    if (load_object_from_buffer(backend, rebuilt_data, rebuilt_size, &rebuilt_object, m68k_diag_sink(&diagnostics)) != 0) {
      memset(&context, 0, sizeof(context));
      context.original_bytes = compare_data;
      context.original_size = compare_size;
      context.rebuilt_bytes = rebuilt_data;
      context.rebuilt_size = rebuilt_size;
      context.backend_kind = original_object->platform_backend_kind;
      context.assembler_policy = assembler_policy;
      context.workflow_arena = workflow_arena;
      m68k_reproduction_compare(&context, &result);
      return result;
    }
    memset(&context, 0, sizeof(context));
    context.original_bytes = compare_data;
    context.original_size = compare_size;
    context.rebuilt_bytes = rebuilt_data;
    context.rebuilt_size = rebuilt_size;
    context.backend_kind = original_object->platform_backend_kind;
    context.assembler_policy = assembler_policy;
    context.original_object = original_object;
    context.rebuilt_object = &rebuilt_object;
    context.workflow_arena = workflow_arena;
    m68k_reproduction_compare(&context, &result);
    m68k_object_destroy(&rebuilt_object);
  }
  return result;
}

static char *facts_v2_direct_rebuild_profile_json_alloc(const char *backend_name, uint32_t source_bytes,
    uint32_t rebuilt_bytes, int refused, const char *refusal_reason, double write_buffer_seconds,
    double write_file_seconds, size_t original_bytes, M68kReproductionCompareResult compare_result,
    double compare_seconds, double total_seconds, const M68kAssemblerPolicy *assembler_policy,
    M68kDiagList *diagnostics) {
  JsonBuilder builder = {0};
  char *text;
  uint32_t policy_kind = assembler_policy != NULL ? assembler_policy->kind : M68K_ASSEMBLER_POLICY_IDEAL;
  uint32_t policy_flags = assembler_policy != NULL ? assembler_policy->flags : 0U;
  uint32_t hunk_relocation_records =
    assembler_policy != NULL ? assembler_policy->hunk_relocation_record_count : 0U;
  int compare_compared = compare_result.status_id != M68K_REPRO_COMPARE_STATUS_NOT_COMPARED;
  int compare_full_file_exact = compare_result.exactness_id == M68K_REPRO_COMPARE_EXACTNESS_FULL_FILE;
  int compare_payload_exact = direct_compare_payload_exact(&compare_result);
  int compare_relocation_exact = direct_compare_relocation_exact(&compare_result);
  int compare_semantic_exact = compare_payload_exact && compare_relocation_exact;
  int compare_container_oddity =
    (compare_result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_CONTAINER_SHAPE_DIFF) != 0U;
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"facts_v2_direct_rebuild\":true,\"backend\":") != 0 ||
      json_builder_append_json_string(&builder, backend_name != NULL ? backend_name : "") != 0 ||
      json_builder_appendf(&builder,
        ",\"direct_rebuild_refused\":%s,\"direct_rebuild_refusal_reason\":",
        refused ? "true" : "false") != 0 ||
      json_builder_append_json_string(&builder, refusal_reason != NULL ? refusal_reason : "") != 0 ||
      json_builder_appendf(&builder,
        ",\"source_bytes\":%u,\"original_bytes\":%u,\"rebuilt_bytes\":%u,"
        "\"write_buffer_seconds\":%.6f,\"write_file_seconds\":%.6f,"
        "\"direct_rebuild_compared\":%s,\"direct_rebuild_exact\":%s,"
        "\"direct_compare_status\":",
        (unsigned)source_bytes,
        (unsigned)(original_bytes > UINT32_MAX ? UINT32_MAX : original_bytes),
        (unsigned)rebuilt_bytes, write_buffer_seconds, write_file_seconds,
        compare_compared ? "true" : "false",
        compare_full_file_exact ? "true" : "false") != 0 ||
      json_builder_append_json_string(&builder, direct_compare_status_text(&compare_result)) != 0 ||
      json_builder_appendf(&builder,
        ",\"direct_compare_payload_exact\":%s,"
        "\"direct_compare_relocation_semantics_exact\":%s,"
        "\"direct_compare_semantic_exact\":%s,"
        "\"direct_compare_container_oddity\":%s,"
        "\"direct_compare_status_id\":%u,"
        "\"direct_compare_exactness_id\":%u,"
        "\"direct_compare_diagnostic_id\":%u,"
        "\"direct_compare_issue_group_flags\":%u,"
        "\"direct_compare_first_diff_offset\":%u,"
        "\"direct_compare_range_count\":%u,"
        "\"direct_compare_file_layout_count\":%u,"
        "\"direct_compare_file_layout_overflow\":%s,"
        "\"direct_compare_file_layout\":",
        compare_payload_exact ? "true" : "false",
        compare_relocation_exact ? "true" : "false",
        compare_semantic_exact ? "true" : "false",
        compare_container_oddity ? "true" : "false",
        (unsigned)compare_result.status_id, (unsigned)compare_result.exactness_id,
        (unsigned)compare_result.diagnostic_id, (unsigned)compare_result.issue_group_flags,
        (unsigned)compare_result.first_diff_offset, (unsigned)compare_result.range_count,
        (unsigned)compare_result.layout_count,
        compare_result.layout_overflow ? "true" : "false") != 0 ||
      json_builder_append_repro_compare_layout(&builder, &compare_result) != 0 ||
      json_builder_appendf(&builder,
        ",\"direct_compare_file_shape_diagnostics\":") != 0 ||
      json_builder_append_repro_compare_diagnostics(&builder, &compare_result) != 0 ||
      json_builder_appendf(&builder,
        ",\"direct_compare_source_hint_count\":%u,"
        "\"direct_compare_source_hint_overflow\":%s,"
        "\"direct_compare_source_hints\":",
        (unsigned)compare_result.source_hint_count,
        compare_result.source_hint_overflow ? "true" : "false") != 0 ||
      json_builder_append_direct_compare_source_hints(&builder, &compare_result) != 0 ||
      json_builder_appendf(&builder,
        ",\"direct_compare_seconds\":%.6f,\"assembler_policy_kind\":%u,"
        "\"assembler_policy_flags\":%u,\"assembler_policy_hunk_relocation_record_count\":%u,"
        "\"total_seconds\":%.6f}",
        compare_seconds, (unsigned)policy_kind, (unsigned)policy_flags, (unsigned)hunk_relocation_records,
        total_seconds) != 0) {
    if (diagnostics != NULL) platform_file_add_error(diagnostics, "out of memory");
    json_builder_destroy(&builder);
    return NULL;
  }
  text = json_builder_build(&builder);
  json_builder_destroy(&builder);
  if (text == NULL && diagnostics != NULL) platform_file_add_error(diagnostics, "out of memory");
  return text;
}

static char *facts_v2_reproduction_compare_profile_json_alloc(const char *backend_name, size_t original_bytes,
    uint32_t rebuilt_bytes, M68kReproductionCompareResult compare_result, double compare_seconds,
    const M68kAssemblerPolicy *assembler_policy, M68kDiagList *diagnostics) {
  JsonBuilder builder = {0};
  char *text;
  uint32_t policy_kind = assembler_policy != NULL ? assembler_policy->kind : M68K_ASSEMBLER_POLICY_IDEAL;
  uint32_t policy_flags = assembler_policy != NULL ? assembler_policy->flags : 0U;
  uint32_t hunk_relocation_records =
    assembler_policy != NULL ? assembler_policy->hunk_relocation_record_count : 0U;
  int compare_compared = compare_result.status_id != M68K_REPRO_COMPARE_STATUS_NOT_COMPARED;
  int compare_full_file_exact = compare_result.exactness_id == M68K_REPRO_COMPARE_EXACTNESS_FULL_FILE;
  int compare_payload_exact = direct_compare_payload_exact(&compare_result);
  int compare_relocation_exact = direct_compare_relocation_exact(&compare_result);
  int compare_content_exact = compare_payload_exact && compare_relocation_exact;
  int compare_container_oddity =
    (compare_result.issue_group_flags & M68K_REPRO_COMPARE_ISSUE_CONTAINER_SHAPE_DIFF) != 0U;
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"facts_v2_reproduction_compare\":true,\"backend\":") != 0 ||
      json_builder_append_json_string(&builder, backend_name != NULL ? backend_name : "") != 0 ||
      json_builder_appendf(&builder,
        ",\"original_bytes\":%u,\"rebuilt_bytes\":%u,"
        "\"reproduction_compare_compared\":%s,"
        "\"reproduction_compare_full_file_exact\":%s,"
        "\"reproduction_compare_status\":",
        (unsigned)(original_bytes > UINT32_MAX ? UINT32_MAX : original_bytes),
        (unsigned)rebuilt_bytes,
        compare_compared ? "true" : "false",
        compare_full_file_exact ? "true" : "false") != 0 ||
      json_builder_append_json_string(&builder, direct_compare_status_text(&compare_result)) != 0 ||
      json_builder_appendf(&builder,
        ",\"reproduction_compare_payload_exact\":%s,"
        "\"reproduction_compare_relocation_semantics_exact\":%s,"
        "\"reproduction_compare_content_exact\":%s,"
        "\"reproduction_compare_container_oddity\":%s,"
        "\"reproduction_compare_status_id\":%u,"
        "\"reproduction_compare_exactness_id\":%u,"
        "\"reproduction_compare_diagnostic_id\":%u,"
        "\"reproduction_compare_issue_group_flags\":%u,"
        "\"reproduction_compare_first_diff_offset\":%u,"
        "\"reproduction_compare_range_count\":%u,"
        "\"reproduction_compare_file_layout_count\":%u,"
        "\"reproduction_compare_file_layout_overflow\":%s,"
        "\"reproduction_compare_file_layout\":",
        compare_payload_exact ? "true" : "false",
        compare_relocation_exact ? "true" : "false",
        compare_content_exact ? "true" : "false",
        compare_container_oddity ? "true" : "false",
        (unsigned)compare_result.status_id, (unsigned)compare_result.exactness_id,
        (unsigned)compare_result.diagnostic_id, (unsigned)compare_result.issue_group_flags,
        (unsigned)compare_result.first_diff_offset, (unsigned)compare_result.range_count,
        (unsigned)compare_result.layout_count,
        compare_result.layout_overflow ? "true" : "false") != 0 ||
      json_builder_append_repro_compare_layout(&builder, &compare_result) != 0 ||
      json_builder_appendf(&builder,
        ",\"reproduction_compare_file_shape_diagnostics\":") != 0 ||
      json_builder_append_repro_compare_diagnostics(&builder, &compare_result) != 0 ||
      json_builder_appendf(&builder,
        ",\"reproduction_compare_source_hint_count\":%u,"
        "\"reproduction_compare_source_hint_overflow\":%s,"
        "\"reproduction_compare_source_hints\":",
        (unsigned)compare_result.source_hint_count,
        compare_result.source_hint_overflow ? "true" : "false") != 0 ||
      json_builder_append_direct_compare_source_hints(&builder, &compare_result) != 0 ||
      json_builder_appendf(&builder,
        ",\"reproduction_compare_seconds\":%.6f,\"assembler_policy_kind\":%u,"
        "\"assembler_policy_flags\":%u,\"assembler_policy_hunk_relocation_record_count\":%u}",
        compare_seconds, (unsigned)policy_kind, (unsigned)policy_flags, (unsigned)hunk_relocation_records) != 0) {
    if (diagnostics != NULL) platform_file_add_error(diagnostics, "out of memory");
    json_builder_destroy(&builder);
    return NULL;
  }
  text = json_builder_build(&builder);
  json_builder_destroy(&builder);
  if (text == NULL && diagnostics != NULL) platform_file_add_error(diagnostics, "out of memory");
  return text;
}

static int platform_file_assemble_source_common_alloc(const char *backend_name, const char *include_dir,
    const char *path, const char *source_text, const char *output_path, const char *target_cpu_name,
    unsigned char **out_data, size_t *out_size, char **out_profile_json, char **out_error) {
  M68kParseCpuResult cpu_result;
  M68kDiagList diagnostics;
  M68kPlatformAssembleProfile profile;
  const char *message;
  int result;
  if (out_data == NULL || out_size == NULL || out_profile_json == NULL || out_error == NULL) return -1;
  *out_data = NULL;
  *out_size = 0U;
  *out_profile_json = NULL;
  *out_error = NULL;
  memset(&profile, 0, sizeof(profile));
  m68k_diag_list_reset(&diagnostics);
  cpu_result = m68k_parse_cpu_name(target_cpu_name != NULL ? target_cpu_name : "");
  if (!cpu_result.ok) {
    *out_error = m68k_platform_dup_string("unknown cpu");
    *out_profile_json = assembler_profile_json_alloc_local(&profile);
    return -1;
  }
  if (m68k_raw_backend_by_name(backend_name) != NULL) {
    if (source_text == NULL) {
      *out_error = m68k_platform_dup_string("raw output backend requires source text");
      *out_profile_json = assembler_profile_json_alloc_local(&profile);
      return -1;
    }
    result = m68k_assemble_platform_source_text_to_raw_buffer_alloc(backend_name,
      include_dir != NULL ? include_dir : "", source_text, output_path != NULL ? output_path : "",
      cpu_result.cpu, out_data, out_size, &profile, m68k_diag_sink(&diagnostics));
    *out_profile_json = assembler_profile_json_alloc_local(&profile);
    if (*out_profile_json == NULL) {
      free(*out_data);
      *out_data = NULL;
      *out_size = 0U;
      *out_error = m68k_platform_dup_string("out of memory");
      return -1;
    }
    if (result != 0) {
      message = m68k_diag_first_message(&diagnostics);
      if (message == NULL || message[0] == '\0') message = "raw platform assembler failed";
      free(*out_data);
      *out_data = NULL;
      *out_size = 0U;
      *out_error = m68k_platform_dup_string(message);
      return -1;
    }
    return 0;
  }
  if (source_text != NULL) {
    if (output_path != NULL && output_path[0] != '\0')
      result = m68k_assemble_platform_source_text_to_output_buffer_alloc(backend_name,
        include_dir != NULL ? include_dir : "", source_text, output_path, cpu_result.cpu,
        out_data, out_size, &profile, m68k_diag_sink(&diagnostics));
    else
      result = m68k_assemble_platform_source_text_to_buffer_alloc(backend_name,
        include_dir != NULL ? include_dir : "", source_text, cpu_result.cpu, out_data, out_size, &profile,
        m68k_diag_sink(&diagnostics));
  } else if (output_path != NULL && output_path[0] != '\0') {
    result = m68k_assemble_platform_file_to_output_buffer_alloc(backend_name, include_dir != NULL ? include_dir : "",
      path, output_path, cpu_result.cpu, out_data, out_size, &profile, m68k_diag_sink(&diagnostics));
  } else {
    result = m68k_assemble_platform_file_to_buffer_alloc(backend_name, include_dir != NULL ? include_dir : "",
      path, cpu_result.cpu, out_data, out_size, &profile, m68k_diag_sink(&diagnostics));
  }
  *out_profile_json = assembler_profile_json_alloc_local(&profile);
  if (*out_profile_json == NULL) {
    free(*out_data);
    *out_data = NULL;
    *out_size = 0U;
    *out_error = m68k_platform_dup_string("out of memory");
    return -1;
  }
  if (result != 0) {
    message = m68k_diag_first_message(&diagnostics);
    if (message == NULL || message[0] == '\0') message = "platform assembler failed";
    free(*out_data);
    *out_data = NULL;
    *out_size = 0U;
    *out_error = m68k_platform_dup_string(message);
    return -1;
  }
  return 0;
}

int platform_file_assemble_source_path_bytes_profile_alloc(const char *backend_name, const char *include_dir,
    const char *path, const char *target_cpu_name, unsigned char **out_data, size_t *out_size,
    char **out_profile_json, char **out_error) {
  return platform_file_assemble_source_common_alloc(backend_name, include_dir, path, NULL, NULL, target_cpu_name,
    out_data, out_size, out_profile_json, out_error);
}

int platform_file_assemble_source_path_to_output_bytes_profile_alloc(const char *backend_name,
    const char *include_dir, const char *path, const char *output_path, const char *target_cpu_name,
    unsigned char **out_data, size_t *out_size, char **out_profile_json, char **out_error) {
  return platform_file_assemble_source_common_alloc(backend_name, include_dir, path, NULL, output_path,
    target_cpu_name, out_data, out_size, out_profile_json, out_error);
}

int platform_file_assemble_source_text_bytes_profile_alloc(const char *backend_name, const char *include_dir,
    const char *source_text, const char *target_cpu_name, unsigned char **out_data, size_t *out_size,
    char **out_profile_json, char **out_error) {
  return platform_file_assemble_source_common_alloc(backend_name, include_dir, NULL, source_text, NULL,
    target_cpu_name, out_data, out_size, out_profile_json, out_error);
}

int platform_file_assemble_source_text_to_output_bytes_profile_alloc(const char *backend_name,
    const char *include_dir, const char *source_text, const char *output_path, const char *target_cpu_name,
    unsigned char **out_data, size_t *out_size, char **out_profile_json, char **out_error) {
  return platform_file_assemble_source_common_alloc(backend_name, include_dir, NULL, source_text, output_path,
    target_cpu_name, out_data, out_size, out_profile_json, out_error);
}

void platform_file_free_text(char *text) { free(text); }
void platform_file_free_bytes(unsigned char *data) { free(data); }

typedef struct PlatformFileWorkflow {
  Arena *arena;
  M68kAnalysisPolicy *analysis_policy;
  M68kFactsV2Profile *profile;
  M68kSourceAnalysisIR *analysis;
  M68kObject object;
  uint8_t object_loaded;
  uint8_t reserved[7];
} PlatformFileWorkflow;

static int platform_file_workflow_create(PlatformFileWorkflow *workflow, M68kDiagList *diagnostics) {
  if (workflow == NULL) return -1;
  memset(workflow, 0, sizeof(*workflow));
  workflow->arena = arena_create(4096U);
  if (workflow->arena == NULL) goto oom;
  workflow->analysis_policy = (M68kAnalysisPolicy *)arena_calloc(workflow->arena, 1U,
    sizeof(*workflow->analysis_policy));
  workflow->profile = (M68kFactsV2Profile *)arena_calloc(workflow->arena, 1U, sizeof(*workflow->profile));
  workflow->analysis = (M68kSourceAnalysisIR *)arena_calloc(workflow->arena, 1U, sizeof(*workflow->analysis));
  if (workflow->analysis_policy == NULL || workflow->profile == NULL || workflow->analysis == NULL) goto oom;
  return 0;
oom:
  if (diagnostics != NULL) platform_file_add_error(diagnostics, "out of memory");
  arena_destroy(workflow->arena);
  memset(workflow, 0, sizeof(*workflow));
  return -1;
}

static void platform_file_workflow_destroy(PlatformFileWorkflow *workflow) {
  if (workflow == NULL) return;
  if (workflow->analysis != NULL) m68k_ir_source_analysis_destroy(workflow->analysis);
  if (workflow->analysis_policy != NULL) m68k_analysis_policy_destroy(workflow->analysis_policy);
  if (workflow->object_loaded) m68k_object_destroy(&workflow->object);
  arena_destroy(workflow->arena);
  memset(workflow, 0, sizeof(*workflow));
}

static PlatformFileTextResult facts_v2_analysis_object_json(const char *backend_name, const M68kObject *object,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  JsonBuilder builder = {0};
  PlatformFileWorkflow workflow;
  char *base_json = NULL;
  int json_result;
  memset(&result, 0, sizeof(result));
  memset(&workflow, 0, sizeof(workflow));
  if (backend_name == NULL || object == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid facts_v2 analysis request");
    return result;
  }
  if (platform_file_workflow_create(&workflow, &result.diagnostics) != 0) return result;
  if (analysis_policy != NULL) {
    if (m68k_analysis_policy_copy(workflow.analysis_policy, analysis_policy) != 0) goto cleanup;
  } else m68k_analysis_policy_init_default(workflow.analysis_policy);
  if (m68k_facts_v2_collect_source_analysis_profile(object, workflow.analysis_policy, workflow.profile,
      workflow.analysis,
      m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "failed building facts_v2 source analysis");
    goto cleanup;
  }
  json_result = source_analysis_to_json(workflow.analysis, &base_json, m68k_diag_sink(&result.diagnostics));
  if (json_result == 0) {
    if (json_builder_create(&builder) != 0 ||
        append_analysis_json_with_decompression_profile(&builder, base_json, backend_name, object, workflow.analysis,
          NULL, workflow.profile, NULL) != 0) {
      json_result = -1;
    } else {
      result.text = json_builder_build(&builder);
      if (result.text == NULL) json_result = -1;
    }
  }
  if (json_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building analysis json");
cleanup:
  json_builder_destroy(&builder);
  platform_file_free_text(base_json);
  platform_file_workflow_destroy(&workflow);
  return result;
}

static PlatformFileTextResult facts_v2_source_quality_explain_object_json(const char *backend_name, const char *path,
    const M68kObject *object, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  JsonBuilder builder = {0};
  PlatformFileWorkflow workflow;
  char *source_text = NULL;
  char *explanation_json = NULL;
  char *analysis_json = NULL;
  int json_result;
  memset(&result, 0, sizeof(result));
  memset(&workflow, 0, sizeof(workflow));
  if (backend_name == NULL || object == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid source-quality explanation request");
    return result;
  }
  if (platform_file_workflow_create(&workflow, &result.diagnostics) != 0) return result;
  if (analysis_policy != NULL) {
    if (m68k_analysis_policy_copy(workflow.analysis_policy, analysis_policy) != 0) goto cleanup;
  } else m68k_analysis_policy_init_default(workflow.analysis_policy);
  if (m68k_facts_v2_render_asm_source_analysis_profile_alloc(object, workflow.analysis_policy, &source_text,
      workflow.profile, workflow.analysis, 0U,
      m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "failed building facts_v2 source analysis");
    goto cleanup;
  }
  json_result = source_analysis_source_quality_explanations_to_json(workflow.analysis, &explanation_json,
    m68k_diag_sink(&result.diagnostics));
  if (json_result == 0)
    json_result = source_analysis_to_json(workflow.analysis, &analysis_json, m68k_diag_sink(&result.diagnostics));
  if (json_result == 0) {
    if (json_builder_create(&builder) != 0 ||
        json_builder_append(&builder, "{\"source_quality\":") != 0 ||
        json_builder_append(&builder, explanation_json) != 0 ||
        json_builder_append(&builder, ",\"source_analysis\":") != 0 ||
        json_builder_append(&builder, analysis_json) != 0 ||
        json_builder_append(&builder, ",\"profile\":{\"generation\":\"facts_v2_source_quality_explain\","
          "\"backend\":") != 0 ||
        json_builder_append_json_string(&builder, backend_name) != 0 ||
        json_builder_append(&builder, ",\"analysis_backend\":\"facts_v2\",\"path\":") != 0 ||
        json_builder_append_json_string(&builder, path != NULL ? path : "") != 0 ||
        json_builder_append(&builder, ",\"facts_v2\":") != 0 ||
        json_builder_append_facts_v2_profile(&builder, workflow.profile) != 0 ||
        json_builder_append(&builder, "}}") != 0) {
      json_result = -1;
    } else {
      result.text = json_builder_build(&builder);
      if (result.text == NULL) json_result = -1;
    }
  }
  if (json_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building source-quality explanation json");
cleanup:
  json_builder_destroy(&builder);
  m68k_facts_v2_free_text(source_text);
  platform_file_free_text(explanation_json);
  platform_file_free_text(analysis_json);
  platform_file_workflow_destroy(&workflow);
  return result;
}

PlatformFileTextResult platform_file_facts_v2_analysis_path_json(const char *backend_name, const char *path,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  PlatformFileWorkflow workflow;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  memset(&result, 0, sizeof(result));
  memset(&workflow, 0, sizeof(workflow));
  if (platform_file_workflow_create(&workflow, &result.diagnostics) != 0) return result;
  if (analysis_policy != NULL) {
    if (m68k_analysis_policy_copy(workflow.analysis_policy, analysis_policy) != 0) goto cleanup;
  } else m68k_analysis_policy_init_default(workflow.analysis_policy);
  if (load_object_from_path(backend, path, &workflow.object, m68k_diag_sink(&result.diagnostics)) != 0)
    goto cleanup;
  workflow.object_loaded = 1U;
  if (enrich_policy_from_object_target_info_local(workflow.analysis_policy, backend, &workflow.object, NULL, 0U,
      &result.diagnostics) != 0) {
    goto cleanup;
  }
  enrich_policy_pointer_targets_from_object_local(workflow.analysis_policy, &workflow.object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &workflow.object,
      workflow.analysis_policy))
    goto cleanup;
  result = facts_v2_analysis_object_json(backend_name, &workflow.object, workflow.analysis_policy);
cleanup:
  platform_file_workflow_destroy(&workflow);
  return result;
}

PlatformFileTextResult platform_file_source_quality_explain_path_json(const char *backend_name, const char *path,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  PlatformFileWorkflow workflow;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  memset(&result, 0, sizeof(result));
  memset(&workflow, 0, sizeof(workflow));
  if (platform_file_workflow_create(&workflow, &result.diagnostics) != 0) return result;
  if (analysis_policy != NULL) {
    if (m68k_analysis_policy_copy(workflow.analysis_policy, analysis_policy) != 0) goto cleanup;
  } else m68k_analysis_policy_init_default(workflow.analysis_policy);
  if (load_object_from_path(backend, path, &workflow.object, m68k_diag_sink(&result.diagnostics)) != 0)
    goto cleanup;
  workflow.object_loaded = 1U;
  if (enrich_policy_from_object_target_info_local(workflow.analysis_policy, backend, &workflow.object, NULL, 0U,
      &result.diagnostics) != 0) {
    goto cleanup;
  }
  enrich_policy_pointer_targets_from_object_local(workflow.analysis_policy, &workflow.object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &workflow.object,
      workflow.analysis_policy))
    goto cleanup;
  result = facts_v2_source_quality_explain_object_json(backend_name, path, &workflow.object, workflow.analysis_policy);
cleanup:
  platform_file_workflow_destroy(&workflow);
  return result;
}

PlatformFileTextResult platform_file_facts_v2_analysis_raw_path_json(const char *platform_name, const char *path,
    uint32_t entry_address, uint8_t has_runtime_load_address, uint32_t runtime_load_address,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  PlatformFileWorkflow workflow;
  memset(&result, 0, sizeof(result));
  memset(&workflow, 0, sizeof(workflow));
  if (platform_file_workflow_create(&workflow, &result.diagnostics) != 0) return result;
  if (analysis_policy != NULL) {
    if (m68k_analysis_policy_copy(workflow.analysis_policy, analysis_policy) != 0) goto cleanup;
  } else m68k_analysis_policy_init_default(workflow.analysis_policy);
  if (load_raw_object_from_path(platform_name, path, &workflow.object, m68k_diag_sink(&result.diagnostics)) != 0)
    goto cleanup;
  workflow.object_loaded = 1U;
  if (!policy_add_raw_runtime_load_range_local(workflow.analysis_policy, &workflow.object, has_runtime_load_address,
        runtime_load_address, &result.diagnostics) ||
      !policy_set_raw_entry_address_local(workflow.analysis_policy, &workflow.object, entry_address,
        has_runtime_load_address, &result.diagnostics))
    goto cleanup;
  enrich_policy_pointer_targets_from_object_local(workflow.analysis_policy, &workflow.object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &workflow.object,
      workflow.analysis_policy))
    goto cleanup;
  result = facts_v2_analysis_object_json(platform_name, &workflow.object, workflow.analysis_policy);
cleanup:
  platform_file_workflow_destroy(&workflow);
  return result;
}

PlatformFileTextResult platform_file_source_quality_explain_raw_path_json(const char *platform_name, const char *path,
    uint32_t entry_address, uint8_t has_runtime_load_address, uint32_t runtime_load_address,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  PlatformFileWorkflow workflow;
  memset(&result, 0, sizeof(result));
  memset(&workflow, 0, sizeof(workflow));
  if (platform_file_workflow_create(&workflow, &result.diagnostics) != 0) return result;
  if (analysis_policy != NULL) {
    if (m68k_analysis_policy_copy(workflow.analysis_policy, analysis_policy) != 0) goto cleanup;
  } else m68k_analysis_policy_init_default(workflow.analysis_policy);
  if (load_raw_object_from_path(platform_name, path, &workflow.object, m68k_diag_sink(&result.diagnostics)) != 0)
    goto cleanup;
  workflow.object_loaded = 1U;
  if (!policy_add_raw_runtime_load_range_local(workflow.analysis_policy, &workflow.object, has_runtime_load_address,
        runtime_load_address, &result.diagnostics) ||
      !policy_set_raw_entry_address_local(workflow.analysis_policy, &workflow.object, entry_address,
        has_runtime_load_address, &result.diagnostics))
    goto cleanup;
  enrich_policy_pointer_targets_from_object_local(workflow.analysis_policy, &workflow.object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &workflow.object,
      workflow.analysis_policy))
    goto cleanup;
  result = facts_v2_source_quality_explain_object_json(platform_name, path, &workflow.object,
    workflow.analysis_policy);
cleanup:
  platform_file_workflow_destroy(&workflow);
  return result;
}

PlatformFileTextResult platform_file_facts_v2_analysis_buffer_json(const char *backend_name,
    const unsigned char *data, size_t size, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  PlatformFileWorkflow workflow;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  memset(&result, 0, sizeof(result));
  memset(&workflow, 0, sizeof(workflow));
  if (platform_file_workflow_create(&workflow, &result.diagnostics) != 0) return result;
  if (analysis_policy != NULL) {
    if (m68k_analysis_policy_copy(workflow.analysis_policy, analysis_policy) != 0) goto cleanup;
  } else m68k_analysis_policy_init_default(workflow.analysis_policy);
  if (load_object_from_buffer(backend, data, size, &workflow.object, m68k_diag_sink(&result.diagnostics)) != 0)
    goto cleanup;
  workflow.object_loaded = 1U;
  if (enrich_policy_from_object_target_info_local(workflow.analysis_policy, backend, &workflow.object, NULL, 0U,
      &result.diagnostics) != 0) {
    goto cleanup;
  }
  enrich_policy_pointer_targets_from_object_local(workflow.analysis_policy, &workflow.object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &workflow.object,
      workflow.analysis_policy))
    goto cleanup;
  result = facts_v2_analysis_object_json(backend_name, &workflow.object, workflow.analysis_policy);
cleanup:
  platform_file_workflow_destroy(&workflow);
  return result;
}

PlatformFileTextResult platform_file_type_catalog_json(const char *backend_name) {
  PlatformFileTextResult result;
  int json_result;
  memset(&result, 0, sizeof(result));
  json_result = platform_type_catalog_to_json(backend_name, &result.text, m68k_diag_sink(&result.diagnostics));
  if (json_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building type catalog json");
  return result;
}

PlatformFileTextResult platform_file_naming_catalog_json(const char *backend_name) {
  PlatformFileTextResult result;
  int json_result;
  memset(&result, 0, sizeof(result));
  json_result = platform_naming_catalog_to_json(backend_name, &result.text, m68k_diag_sink(&result.diagnostics));
  if (json_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building naming catalog json");
  return result;
}

PlatformFileTextResult platform_file_os_metadata_catalog_json(const char *backend_name) {
  PlatformFileTextResult result;
  int json_result;
  memset(&result, 0, sizeof(result));
  json_result = platform_os_metadata_catalog_to_json(backend_name, &result.text, m68k_diag_sink(&result.diagnostics));
  if (json_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building OS metadata catalog json");
  return result;
}

PlatformFileTextResult platform_file_api_input_struct_json(const char *backend_name, const char *library_name,
    const char *function_name, const char *input_name, const char *struct_name) {
  PlatformFileTextResult result;
  int json_result;
  memset(&result, 0, sizeof(result));
  json_result = platform_api_input_struct_to_json(backend_name, library_name, function_name, input_name, struct_name,
    &result.text, m68k_diag_sink(&result.diagnostics));
  if (json_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building API input struct json");
  return result;
}

int platform_file_inspect_path_json_alloc(const char *backend_name, const char *path, char **out_text) {
  PlatformFileTextResult result = platform_file_inspect_path_json(backend_name, path);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_analysis_path_json_alloc(const char *backend_name, const char *path,
    const char *metadata_path, const char *entry_offsets, char **out_text) {
  PlatformFileWorkflow workflow;
  M68kDiagList diagnostics;
  PlatformFileTextResult result;
  m68k_diag_list_reset(&diagnostics);
  memset(&workflow, 0, sizeof(workflow));
  if (platform_file_workflow_create(&workflow, &diagnostics) != 0) {
    result.text = NULL;
    memset(&result.diagnostics, 0, sizeof(result.diagnostics));
    result.diagnostics = diagnostics;
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(workflow.analysis_policy, backend_name, metadata_path, entry_offsets,
        &diagnostics) != 0) {
    result.text = NULL;
    result.diagnostics = diagnostics;
    platform_file_workflow_destroy(&workflow);
    return text_result_to_alloc(&result, out_text);
  }
  result = platform_file_facts_v2_analysis_path_json(backend_name, path, workflow.analysis_policy);
  platform_file_workflow_destroy(&workflow);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_analysis_raw_path_json_alloc(const char *platform_name, const char *path,
    uint32_t entry_address, uint32_t has_runtime_load_address, uint32_t runtime_load_address,
    const char *metadata_path, const char *entry_offsets, char **out_text) {
  PlatformFileWorkflow workflow;
  M68kDiagList diagnostics;
  PlatformFileTextResult result;
  m68k_diag_list_reset(&diagnostics);
  memset(&workflow, 0, sizeof(workflow));
  if (platform_file_workflow_create(&workflow, &diagnostics) != 0) {
    result.text = NULL;
    memset(&result.diagnostics, 0, sizeof(result.diagnostics));
    result.diagnostics = diagnostics;
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(workflow.analysis_policy, platform_name, metadata_path, entry_offsets,
        &diagnostics) != 0) {
    result.text = NULL;
    result.diagnostics = diagnostics;
    platform_file_workflow_destroy(&workflow);
    return text_result_to_alloc(&result, out_text);
  }
  result = platform_file_facts_v2_analysis_raw_path_json(platform_name, path, entry_address,
    (uint8_t)(has_runtime_load_address != 0U), runtime_load_address, workflow.analysis_policy);
  platform_file_workflow_destroy(&workflow);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_source_quality_explain_path_json_alloc(const char *backend_name, const char *path,
    const char *metadata_path, const char *entry_offsets, char **out_text) {
  PlatformFileWorkflow workflow;
  M68kDiagList diagnostics;
  PlatformFileTextResult result;
  m68k_diag_list_reset(&diagnostics);
  memset(&workflow, 0, sizeof(workflow));
  if (platform_file_workflow_create(&workflow, &diagnostics) != 0) {
    result.text = NULL;
    memset(&result.diagnostics, 0, sizeof(result.diagnostics));
    result.diagnostics = diagnostics;
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(workflow.analysis_policy, backend_name, metadata_path, entry_offsets,
        &diagnostics) != 0) {
    result.text = NULL;
    result.diagnostics = diagnostics;
    platform_file_workflow_destroy(&workflow);
    return text_result_to_alloc(&result, out_text);
  }
  result = platform_file_source_quality_explain_path_json(backend_name, path, workflow.analysis_policy);
  platform_file_workflow_destroy(&workflow);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_source_quality_explain_raw_path_json_alloc(const char *platform_name, const char *path,
    uint32_t entry_address, uint32_t has_runtime_load_address, uint32_t runtime_load_address,
    const char *metadata_path, const char *entry_offsets, char **out_text) {
  PlatformFileWorkflow workflow;
  M68kDiagList diagnostics;
  PlatformFileTextResult result;
  m68k_diag_list_reset(&diagnostics);
  memset(&workflow, 0, sizeof(workflow));
  if (platform_file_workflow_create(&workflow, &diagnostics) != 0) {
    result.text = NULL;
    memset(&result.diagnostics, 0, sizeof(result.diagnostics));
    result.diagnostics = diagnostics;
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(workflow.analysis_policy, platform_name, metadata_path, entry_offsets,
        &diagnostics) != 0) {
    result.text = NULL;
    result.diagnostics = diagnostics;
    platform_file_workflow_destroy(&workflow);
    return text_result_to_alloc(&result, out_text);
  }
  result = platform_file_source_quality_explain_raw_path_json(platform_name, path, entry_address,
    (uint8_t)(has_runtime_load_address != 0U), runtime_load_address, workflow.analysis_policy);
  platform_file_workflow_destroy(&workflow);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_effective_policy_path_json_alloc(const char *backend_name, const char *path,
    const char *metadata_path, const char *entry_offsets, char **out_text) {
  return effective_policy_json_to_alloc(backend_name, path, metadata_path, entry_offsets, 0U, 0U, 0U, 0U, out_text);
}

int platform_file_effective_policy_raw_path_json_alloc(const char *platform_name, const char *path,
    uint32_t entry_address, uint32_t has_runtime_load_address, uint32_t runtime_load_address,
    const char *metadata_path, const char *entry_offsets, char **out_text) {
  return effective_policy_json_to_alloc(platform_name, path, metadata_path, entry_offsets, 1U, entry_address,
    (uint8_t)(has_runtime_load_address != 0U), runtime_load_address, out_text);
}

static char *facts_v2_asm_source_profile_json_alloc(const char *backend_name, const char *path,
    const M68kFactsV2Profile *profile, double total_seconds, M68kDiagList *diagnostics) {
  JsonBuilder builder = {0};
  char *json;
  if (backend_name == NULL || path == NULL || profile == NULL) {
    if (diagnostics != NULL) platform_file_add_error(diagnostics, "invalid facts_v2 source profile request");
    return NULL;
  }
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"generation\":\"facts_v2_asm_source\",\"backend\":") != 0 ||
      json_builder_append_json_string(&builder, backend_name) != 0 ||
      json_builder_append(&builder, ",\"analysis_backend\":\"facts_v2\",\"path\":") != 0 ||
      json_builder_append_json_string(&builder, path) != 0 ||
      json_builder_append(&builder, ",\"facts_v2\":") != 0 ||
      json_builder_append_facts_v2_profile(&builder, profile) != 0 ||
      json_builder_appendf(&builder, ",\"timing\":{\"total_seconds\":%.6f}}", total_seconds) != 0) {
    if (diagnostics != NULL) platform_file_add_error(diagnostics, "out of memory");
    json_builder_destroy(&builder);
    return NULL;
  }
  json = json_builder_build(&builder);
  json_builder_destroy(&builder);
  if (json == NULL && diagnostics != NULL) platform_file_add_error(diagnostics, "out of memory");
  return json;
}

struct PlatformFileListingArtifact {
  char *backend_name;
  char *path;
  M68kObject object;
  M68kAnalysisPolicy policy;
  M68kSourceAnalysisIR source_analysis;
  M68kRenderPlan source_plan;
  M68kRenderEvidenceIR render_evidence;
  M68kFactsV2Profile profile;
  Arena *listing_index_arena;
  PlatformListingRowIndex listing_row_index;
  size_t listing_total_rows;
  double source_seconds;
  uint8_t render_evidence_live;
};

static int listing_artifact_set_error(char **out_error, const M68kDiagList *diagnostics,
    const char *fallback) {
  const char *message;
  if (out_error == NULL) return -1;
  message = m68k_diag_first_message(diagnostics);
  if (message == NULL || message[0] == '\0') message = fallback != NULL ? fallback : "listing artifact failed";
  *out_error = m68k_platform_dup_string(message);
  return -1;
}

static int listing_artifact_append_profile_identity(JsonBuilder *builder,
    const PlatformFileListingArtifact *artifact) {
  if (builder == NULL || artifact == NULL) return -1;
  if (json_builder_append(builder, ",\"backend\":") != 0 ||
      json_builder_append_json_string(builder, artifact->backend_name) != 0)
    return -1;
  if (strcmp(artifact->backend_name, "macos-code") == 0 &&
      json_builder_append(builder, ",\"source_kind\":\"macos_code_resource\"") != 0)
    return -1;
  return 0;
}

static PlatformFileListingArtifact *listing_artifact_alloc_base(const char *backend_name, const char *path,
    M68kDiagList *diagnostics) {
  PlatformFileListingArtifact *artifact =
    (PlatformFileListingArtifact *)calloc(1U, sizeof(*artifact));
  if (artifact == NULL) {
    platform_file_add_error(diagnostics, "out of memory");
    return NULL;
  }
  artifact->backend_name = m68k_platform_dup_string(backend_name);
  artifact->path = m68k_platform_dup_string(path);
  if (artifact->backend_name == NULL || artifact->path == NULL) {
    platform_file_add_error(diagnostics, "out of memory");
    platform_file_facts_v2_listing_artifact_destroy(artifact);
    return NULL;
  }
  m68k_render_plan_init(&artifact->source_plan);
  artifact->listing_index_arena = arena_create(4096U);
  if (artifact->listing_index_arena == NULL) {
    platform_file_add_error(diagnostics, "out of memory");
    platform_file_facts_v2_listing_artifact_destroy(artifact);
    return NULL;
  }
  return artifact;
}

static int listing_artifact_build_analysis(PlatformFileListingArtifact *artifact, M68kDiagList *diagnostics) {
  clock_t source_start;
  clock_t source_end;
  char failure_message[192];
  if (artifact == NULL) {
    platform_file_add_error(diagnostics, "invalid listing artifact");
    return -1;
  }
  source_start = clock();
  if (m68k_facts_v2_render_asm_source_plan_analysis_profile_evidence_alloc(&artifact->object, &artifact->policy,
      NULL, &artifact->source_plan, &artifact->profile, &artifact->source_analysis, &artifact->render_evidence, 1U,
      m68k_diag_sink(diagnostics)) != 0) {
    if (artifact->profile.asm_source_first_failure_kind != M68K_SOURCE_EXPORT_FAILURE_NONE) {
      snprintf(failure_message, sizeof(failure_message),
        "facts_v2 asm source first failure: kind=%s section=%u offset=%u aux=%u",
        facts_v2_source_export_failure_kind_name(artifact->profile.asm_source_first_failure_kind),
        (unsigned)artifact->profile.asm_source_first_failure_section,
        (unsigned)artifact->profile.asm_source_first_failure_offset,
        (unsigned)artifact->profile.asm_source_first_failure_aux_offset);
      platform_file_add_error(diagnostics, failure_message);
    }
    if (!m68k_diag_has_errors(diagnostics))
      platform_file_add_error(diagnostics, "facts_v2 asm source render failed");
    return -1;
  }
  artifact->render_evidence_live = 1U;
  source_end = clock();
  if (source_file_listing_row_index_from_render_plan(NULL, &artifact->source_plan,
      artifact->object.platform_backend_kind, &artifact->source_analysis.policy, &artifact->source_analysis,
      "full", 0, 256U, artifact->listing_index_arena, &artifact->listing_row_index,
      m68k_diag_sink(diagnostics)) != 0) {
    if (!m68k_diag_has_errors(diagnostics))
      platform_file_add_error(diagnostics, "facts_v2 listing row index failed");
    return -1;
  }
  artifact->listing_total_rows = artifact->listing_row_index.row_count;
  artifact->source_seconds = elapsed_seconds(source_start, source_end);
  return 0;
}

static int listing_executable_range_role_for_section(const char *backend_name, M68kSectionKind kind,
    PlatformExecutableRangeRole *out_role, const char **out_fact_id, const char **out_fact_status,
    const char **out_parser_use) {
  if (backend_name == NULL || out_role == NULL || out_fact_id == NULL || out_fact_status == NULL ||
      out_parser_use == NULL) {
    return 0;
  }
  if (strcmp(backend_name, "amiga-hunk") == 0) {
    if (kind == M68K_SECTION_CODE) {
      *out_role = PLATFORM_EXECUTABLE_RANGE_ROLE_CODE;
      *out_fact_id = PLATFORM_EXECUTABLE_FORMAT_FACT_AMIGA_HUNK_CODE_DATA_BSS_SECTIONS_ACCEPTED;
    } else if (kind == M68K_SECTION_DATA) {
      *out_role = PLATFORM_EXECUTABLE_RANGE_ROLE_DATA;
      *out_fact_id = PLATFORM_EXECUTABLE_FORMAT_FACT_AMIGA_HUNK_CODE_DATA_BSS_SECTIONS_ACCEPTED;
    } else if (kind == M68K_SECTION_BSS) {
      *out_role = PLATFORM_EXECUTABLE_RANGE_ROLE_BSS;
      *out_fact_id = PLATFORM_EXECUTABLE_FORMAT_FACT_AMIGA_HUNK_BSS_SIZE_ONLY_ACCEPTED;
    } else {
      return 0;
    }
    *out_fact_status = "parser_asserted";
    *out_parser_use = "accepted_parser_output";
    return 1;
  }
  if (strcmp(backend_name, "atari-st") == 0) {
    if (kind == M68K_SECTION_CODE) {
      *out_role = PLATFORM_EXECUTABLE_RANGE_ROLE_CODE;
      *out_fact_id = PLATFORM_EXECUTABLE_FORMAT_FACT_ATARI_ST_PRG_TEXT_DATA_LOADED_IMAGE_ACCEPTED;
      *out_fact_status = "parser_asserted";
      *out_parser_use = "accepted_parser_output";
    } else if (kind == M68K_SECTION_DATA) {
      *out_role = PLATFORM_EXECUTABLE_RANGE_ROLE_DATA;
      *out_fact_id = PLATFORM_EXECUTABLE_FORMAT_FACT_ATARI_ST_PRG_TEXT_DATA_LOADED_IMAGE_ACCEPTED;
      *out_fact_status = "parser_asserted";
      *out_parser_use = "accepted_parser_output";
    } else if (kind == M68K_SECTION_BSS) {
      *out_role = PLATFORM_EXECUTABLE_RANGE_ROLE_BSS;
      *out_fact_id = PLATFORM_EXECUTABLE_FORMAT_FACT_ATARI_ST_PRG_BSS_HEADER_ONLY_CANDIDATE;
      *out_fact_status = "candidate";
      *out_parser_use = "candidate_only";
    } else {
      return 0;
    }
    return 1;
  }
  return 0;
}

static int listing_validate_shared_executable_ranges(const char *backend_name, const M68kObject *object,
    M68kDiagList *diagnostics) {
  size_t index;
  if (backend_name == NULL || object == NULL || object->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE)
    return 1;
  if (strcmp(backend_name, "amiga-hunk") != 0 && strcmp(backend_name, "atari-st") != 0)
    return 1;
  for (index = 0U; index < object->section_count; ++index) {
    const M68kSection *section = &object->sections[index];
    PlatformExecutableRangeRole role;
    const char *fact_id = NULL;
    const char *fact_status = NULL;
    const char *parser_use = NULL;
    if (!listing_executable_range_role_for_section(backend_name, section->kind, &role, &fact_id, &fact_status,
        &parser_use)) {
      platform_file_add_error(diagnostics, "shared executable listing range has unsupported section kind");
      return 0;
    }
    if (role == PLATFORM_EXECUTABLE_RANGE_ROLE_BSS && section->data_size != 0U) {
      platform_file_add_error(diagnostics, "shared executable listing range refuses stored BSS bytes");
      return 0;
    }
    if ((role == PLATFORM_EXECUTABLE_RANGE_ROLE_CODE) != (section->kind == M68K_SECTION_CODE)) {
      platform_file_add_error(diagnostics, "shared executable listing range code role does not match section kind");
      return 0;
    }
    if (fact_id == NULL || fact_status == NULL || parser_use == NULL) {
      platform_file_add_error(diagnostics, "shared executable listing range missing parser fact authority");
      return 0;
    }
  }
  return 1;
}

static const char *listing_executable_range_role_name(PlatformExecutableRangeRole role) {
  if (role == PLATFORM_EXECUTABLE_RANGE_ROLE_CODE) return "code";
  if (role == PLATFORM_EXECUTABLE_RANGE_ROLE_DATA) return "data";
  if (role == PLATFORM_EXECUTABLE_RANGE_ROLE_BSS) return "bss";
  if (role == PLATFORM_EXECUTABLE_RANGE_ROLE_METADATA) return "metadata";
  if (role == PLATFORM_EXECUTABLE_RANGE_ROLE_CANDIDATE_CODE) return "candidate_code";
  return "unknown";
}

static int append_analysis_executable_ranges_json(JsonBuilder *builder, const char *backend_name,
    const M68kObject *object) {
  size_t index;
  uint32_t load_offset = 0U;
  uint32_t stored_offset = 0U;
  int emitted = 0;
  if (builder == NULL || backend_name == NULL || object == NULL ||
      object->platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE) {
    return 0;
  }
  if (strcmp(backend_name, "amiga-hunk") != 0 && strcmp(backend_name, "atari-st") != 0)
    return 0;
  if (json_builder_append(builder,
      ",\"executable_model\":\"platform_executable_summary_v1\",\"executable_ranges\":[") != 0)
    return -1;
  for (index = 0U; index < object->section_count; ++index) {
    const M68kSection *section = &object->sections[index];
    PlatformExecutableRangeRole role;
    const char *fact_id = NULL;
    const char *fact_status = NULL;
    const char *parser_use = NULL;
    uint8_t has_stored_offset = section->data_size != 0U ? 1U : 0U;
    if (!listing_executable_range_role_for_section(backend_name, section->kind, &role, &fact_id, &fact_status,
        &parser_use)) {
      return -1;
    }
    if (emitted++ != 0 && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"section_index\":") != 0 ||
        json_builder_appendf(builder, "%u,\"role\":", (unsigned)index) != 0 ||
        json_builder_append_json_string(builder, listing_executable_range_role_name(role)) != 0 ||
        json_builder_appendf(builder, ",\"load_offset\":%u,\"stored_offset\":", (unsigned)load_offset) != 0)
      return -1;
    if (has_stored_offset) {
      if (json_builder_appendf(builder, "%u", (unsigned)stored_offset) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) return -1;
    if (json_builder_appendf(builder,
          ",\"size\":%u,\"stored_size\":%u,\"status\":",
          (unsigned)section->size, (unsigned)section->data_size) != 0 ||
        json_builder_append_json_string(builder, fact_status) != 0 ||
        json_builder_append(builder, ",\"fact_id\":") != 0 ||
        json_builder_append_json_string(builder, fact_id) != 0 ||
        json_builder_append(builder, ",\"fact_status\":") != 0 ||
        json_builder_append_json_string(builder, fact_status) != 0 ||
        json_builder_append(builder, ",\"parser_use\":") != 0 ||
        json_builder_append_json_string(builder, parser_use) != 0 ||
        json_builder_append(builder, "}") != 0)
      return -1;
    load_offset += section->size;
    stored_offset += section->data_size;
  }
  if (json_builder_append(builder, "]") != 0) return -1;
  if (strcmp(backend_name, "amiga-hunk") == 0) {
    if (json_builder_append(builder, ",\"executable_deferred\":[{\"kind\":\"runtime_entry\",\"status\":\"deferred\","
          "\"fact_id\":") != 0 ||
        json_builder_append_json_string(builder, PLATFORM_EXECUTABLE_FORMAT_FACT_AMIGA_HUNK_RUNTIME_ENTRY_DEFERRED) != 0 ||
        json_builder_append(builder, ",\"fact_status\":\"deferred\",\"parser_use\":\"deferred_only\"}]") != 0)
      return -1;
  } else {
    if (json_builder_append(builder,
          ",\"executable_deferred\":[{\"kind\":\"relocation_breadth\",\"status\":\"deferred\",\"fact_id\":") != 0 ||
        json_builder_append_json_string(builder,
          PLATFORM_EXECUTABLE_FORMAT_FACT_ATARI_ST_PRG_RELOCATION_TERMINATOR_VARIANTS_DEFERRED) != 0 ||
        json_builder_append(builder, ",\"fact_status\":\"deferred\",\"parser_use\":\"deferred_only\"}]") != 0)
      return -1;
  }
  return 0;
}

static char *listing_artifact_profile_json_alloc(const PlatformFileListingArtifact *artifact,
    const char *generation, const char *timing_key, double timing_seconds, M68kDiagList *diagnostics) {
  JsonBuilder builder = {0};
  char *json = NULL;
  if (artifact == NULL || generation == NULL || timing_key == NULL) {
    platform_file_add_error(diagnostics, "invalid listing artifact profile request");
    return NULL;
  }
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"generation\":") != 0 ||
      json_builder_append_json_string(&builder, generation) != 0 ||
      listing_artifact_append_profile_identity(&builder, artifact) != 0 ||
      json_builder_append(&builder, ",\"analysis_backend\":\"facts_v2\",\"path\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->path) != 0 ||
      json_builder_append(&builder, ",\"facts_v2\":") != 0 ||
      json_builder_append_facts_v2_profile(&builder, &artifact->profile) != 0 ||
      json_builder_appendf(&builder, ",\"listing_total_rows\":%u,\"timing\":{\"source_seconds\":%.6f,",
        (unsigned)artifact->listing_total_rows, artifact->source_seconds) != 0 ||
      json_builder_append_json_string(&builder, timing_key) != 0 ||
      json_builder_appendf(&builder, ":%.6f,\"total_seconds\":%.6f}}",
        timing_seconds, artifact->source_seconds + timing_seconds) != 0) {
    platform_file_add_error(diagnostics, "out of memory");
    json_builder_destroy(&builder);
    return NULL;
  }
  json = json_builder_build(&builder);
  json_builder_destroy(&builder);
  if (json == NULL) platform_file_add_error(diagnostics, "out of memory");
  return json;
}

static int facts_v2_direct_write_object_alloc(const char *backend_name, const M68kBackend *backend,
    const M68kObject *object, const char *output_path, uint32_t source_bytes, unsigned char **out_data,
    size_t *out_size, const unsigned char *compare_data, size_t compare_size, char **out_direct_profile_json,
    char **out_error, const M68kAssemblerPolicy *assembler_policy, Arena *workflow_arena,
    M68kDiagList *diagnostics) {
  clock_t total_start = clock();
  clock_t phase_start;
  double write_buffer_seconds = 0.0;
  double write_file_seconds = 0.0;
  double compare_seconds = 0.0;
  M68kReproductionCompareResult compare_result;
  unsigned char *data = NULL;
  size_t size = 0U;
  char temp_path[512];
  const char *read_path = NULL;
  int remove_read_path = 0;
  if (out_data == NULL || out_size == NULL || out_direct_profile_json == NULL || out_error == NULL) return -1;
  *out_data = NULL;
  *out_size = 0U;
  *out_direct_profile_json = NULL;
  *out_error = NULL;
  m68k_reproduction_compare_init_result(&compare_result);
  temp_path[0] = '\0';
  if (backend == NULL || object == NULL) {
    *out_error = m68k_platform_dup_string("unknown platform file backend");
    return -1;
  }
  if (backend->write_buffer != NULL) {
    phase_start = clock();
    if (backend->write_buffer(object, &data, &size, m68k_diag_sink(diagnostics)) != 0) {
      const char *message = m68k_diag_first_message(diagnostics);
      *out_error = m68k_platform_dup_string(message != NULL ? message : "direct rebuild write_buffer failed");
      return -1;
    }
    write_buffer_seconds += elapsed_seconds(phase_start, clock());
    if (output_path != NULL && output_path[0] != '\0') {
      phase_start = clock();
      if (write_bytes_to_path_local(output_path, data, size, diagnostics) != 0) {
        const char *message = m68k_diag_first_message(diagnostics);
        free(data);
        *out_error = m68k_platform_dup_string(message != NULL ? message : "direct rebuild write failed");
        return -1;
      }
      write_file_seconds += elapsed_seconds(phase_start, clock());
    }
  } else if (backend->write_file != NULL) {
    read_path = output_path;
    if (read_path == NULL || read_path[0] == '\0') {
      if (write_object_to_temp_file(backend, object, temp_path, sizeof(temp_path), m68k_diag_sink(diagnostics)) != 0) {
        const char *message = m68k_diag_first_message(diagnostics);
        *out_error = m68k_platform_dup_string(message != NULL ? message : "direct rebuild write failed");
        return -1;
      }
      read_path = temp_path;
      remove_read_path = 1;
    } else {
      phase_start = clock();
      remove(read_path);
      if (backend->write_file(read_path, object, m68k_diag_sink(diagnostics)) != 0) {
        const char *message = m68k_diag_first_message(diagnostics);
        remove(read_path);
        *out_error = m68k_platform_dup_string(message != NULL ? message : "direct rebuild write failed");
        return -1;
      }
      write_file_seconds += elapsed_seconds(phase_start, clock());
    }
    if (read_file_to_buffer(read_path, &data, &size, m68k_diag_sink(diagnostics)) != 0) {
      const char *message = m68k_diag_first_message(diagnostics);
      if (remove_read_path) remove(read_path);
      *out_error = m68k_platform_dup_string(message != NULL ? message : "direct rebuild read failed");
      return -1;
    }
    if (remove_read_path) remove(read_path);
  } else {
    *out_error = m68k_platform_dup_string("platform backend cannot write direct rebuild output");
    return -1;
  }
  if (compare_data != NULL) {
    phase_start = clock();
    compare_result = facts_v2_direct_compare_result(backend_name, backend, object, data, size, compare_data,
      compare_size, assembler_policy, workflow_arena);
    compare_seconds += elapsed_seconds(phase_start, clock());
  }
  *out_direct_profile_json = facts_v2_direct_rebuild_profile_json_alloc(backend_name, source_bytes,
    size > UINT32_MAX ? UINT32_MAX : (uint32_t)size, 0, NULL, write_buffer_seconds, write_file_seconds,
    compare_size, compare_result, compare_seconds, elapsed_seconds(total_start, clock()), assembler_policy,
    diagnostics);
  if (*out_direct_profile_json == NULL) {
    free(data);
    *out_error = m68k_platform_dup_string("out of memory");
    return -1;
  }
  *out_data = data;
  *out_size = size;
  return 0;
}

static int facts_v2_direct_rebuild_object_alloc(const char *backend_name, const char *path,
    const M68kBackend *backend, const M68kObject *object, const M68kAnalysisPolicy *analysis_policy,
    const char *output_path, unsigned char **out_data, size_t *out_size, char **out_source_profile_json,
    char **out_direct_profile_json, const unsigned char *compare_data, size_t compare_size, char **out_error,
    Arena *workflow_arena, M68kDiagList *diagnostics) {
  M68kFactsV2Profile source_profile;
  M68kAssemblerPolicy assembler_policy;
  M68kReproductionCompareResult not_compared;
  char *source_profile_json = NULL;
  clock_t source_start = clock();
  clock_t source_end;
  if (out_data == NULL || out_size == NULL || out_source_profile_json == NULL ||
      out_direct_profile_json == NULL || out_error == NULL) {
    return -1;
  }
  *out_data = NULL;
  *out_size = 0U;
  *out_source_profile_json = NULL;
  *out_direct_profile_json = NULL;
  *out_error = NULL;
  m68k_reproduction_compare_init_result(&not_compared);
  m68k_assembler_policy_derive_preservation(object, &assembler_policy);
  m68k_facts_v2_profile_init(&source_profile);
  if (m68k_facts_v2_collect_direct_rebuild_profile(object, analysis_policy, &source_profile,
      m68k_diag_sink(diagnostics)) != 0) {
    const char *message = m68k_diag_first_message(diagnostics);
    *out_error = m68k_platform_dup_string(message != NULL ? message : "facts_v2 source profile failed");
    return -1;
  }
  source_end = clock();
  source_profile_json = facts_v2_asm_source_profile_json_alloc(backend_name, path, &source_profile,
    elapsed_seconds(source_start, source_end), diagnostics);
  if (source_profile_json == NULL) {
    *out_error = m68k_platform_dup_string("out of memory");
    return -1;
  }
  *out_source_profile_json = source_profile_json;
  if (source_profile.asm_source_refused) {
    *out_direct_profile_json = facts_v2_direct_rebuild_profile_json_alloc(backend_name,
      source_profile.asm_source_bytes, 0U, 1, "source_refused", 0.0, 0.0, 0U, not_compared, 0.0, 0.0,
      &assembler_policy, diagnostics);
    if (*out_direct_profile_json == NULL) {
      *out_error = m68k_platform_dup_string("out of memory");
      return -1;
    }
    return 0;
  }
  if (source_profile.asm_source_lossy_numeric_hunk_relocations != 0U) {
    *out_direct_profile_json = facts_v2_direct_rebuild_profile_json_alloc(backend_name,
      source_profile.asm_source_bytes, 0U, 1, "lossy_numeric_hunk_relocations", 0.0, 0.0, 0,
      not_compared, 0.0, 0.0, &assembler_policy, diagnostics);
    if (*out_direct_profile_json == NULL) {
      *out_error = m68k_platform_dup_string("out of memory");
      return -1;
    }
    return 0;
  }
  return facts_v2_direct_write_object_alloc(backend_name, backend, object, output_path,
    source_profile.asm_source_bytes, out_data, out_size, compare_data, compare_size, out_direct_profile_json,
    out_error, &assembler_policy, workflow_arena, diagnostics);
}

static int platform_file_facts_v2_direct_rebuild_path_common_alloc(const char *backend_name, const char *path,
    const char *metadata_path, const char *output_path, unsigned char **out_data, size_t *out_size,
    char **out_source_profile_json, char **out_direct_profile_json, char **out_error, int compare_original) {
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  PlatformFileWorkflow workflow;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  unsigned char *compare_data = NULL;
  size_t compare_size = 0U;
  int result = -1;
  if (out_data == NULL || out_size == NULL || out_source_profile_json == NULL ||
      out_direct_profile_json == NULL || out_error == NULL) {
    return -1;
  }
  *out_data = NULL;
  *out_size = 0U;
  *out_source_profile_json = NULL;
  *out_direct_profile_json = NULL;
  *out_error = NULL;
  m68k_diag_list_reset(&diagnostics);
  memset(&workflow, 0, sizeof(workflow));
  if (platform_file_workflow_create(&workflow, &diagnostics) != 0) {
    *out_error = m68k_platform_dup_string("out of memory");
    return -1;
  }
  analysis_policy = workflow.analysis_policy;
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL, &diagnostics) != 0)
    goto cleanup;
  if (compare_original && read_file_to_buffer(path, &compare_data, &compare_size, m68k_diag_sink(&diagnostics)) != 0)
    goto cleanup;
  if (load_object_from_path(backend, path, &workflow.object, m68k_diag_sink(&diagnostics)) != 0) goto cleanup;
  workflow.object_loaded = 1U;
  if (enrich_policy_from_object_target_info_local(analysis_policy, backend, &workflow.object, NULL, 0U,
      &diagnostics) != 0) {
    goto cleanup;
  }
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &workflow.object);
  if (!validate_effective_policy_against_object_local(&diagnostics, &workflow.object, analysis_policy))
    goto cleanup;
  result = facts_v2_direct_rebuild_object_alloc(backend_name, path, backend, &workflow.object, analysis_policy,
    output_path, out_data, out_size, out_source_profile_json, out_direct_profile_json, compare_data, compare_size,
    out_error, workflow.arena, &diagnostics);

cleanup:
  if (result != 0 && *out_error == NULL) {
    const char *message = m68k_diag_first_message(&diagnostics);
    if (message == NULL || message[0] == '\0') message = "facts_v2 direct rebuild failed";
    *out_error = m68k_platform_dup_string(message);
  }
  free(compare_data);
  platform_file_workflow_destroy(&workflow);
  return result;
}

int platform_file_facts_v2_direct_rebuild_path_bytes_profile_alloc(const char *backend_name, const char *path,
    const char *metadata_path, const char *output_path, unsigned char **out_data, size_t *out_size,
    char **out_source_profile_json, char **out_direct_profile_json, char **out_error) {
  return platform_file_facts_v2_direct_rebuild_path_common_alloc(backend_name, path, metadata_path, output_path,
    out_data, out_size, out_source_profile_json, out_direct_profile_json, out_error, 0);
}

int platform_file_facts_v2_direct_rebuild_compare_path_bytes_profile_alloc(const char *backend_name, const char *path,
    const char *metadata_path, const char *output_path, unsigned char **out_data, size_t *out_size,
    char **out_source_profile_json, char **out_direct_profile_json, char **out_error) {
  return platform_file_facts_v2_direct_rebuild_path_common_alloc(backend_name, path, metadata_path, output_path,
    out_data, out_size, out_source_profile_json, out_direct_profile_json, out_error, 1);
}

static int platform_file_facts_v2_direct_rebuild_buffer_common_alloc(const char *backend_name,
    const unsigned char *data, size_t size, const char *metadata_path, const char *display_path,
    const char *output_path, unsigned char **out_data, size_t *out_size, char **out_source_profile_json,
    char **out_direct_profile_json, char **out_error, int compare_original) {
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  PlatformFileWorkflow workflow;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  int result = -1;
  if (out_data == NULL || out_size == NULL || out_source_profile_json == NULL ||
      out_direct_profile_json == NULL || out_error == NULL) {
    return -1;
  }
  *out_data = NULL;
  *out_size = 0U;
  *out_source_profile_json = NULL;
  *out_direct_profile_json = NULL;
  *out_error = NULL;
  m68k_diag_list_reset(&diagnostics);
  memset(&workflow, 0, sizeof(workflow));
  if (platform_file_workflow_create(&workflow, &diagnostics) != 0) {
    *out_error = m68k_platform_dup_string("out of memory");
    return -1;
  }
  analysis_policy = workflow.analysis_policy;
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL, &diagnostics) != 0)
    goto cleanup;
  if (load_object_from_buffer(backend, data, size, &workflow.object, m68k_diag_sink(&diagnostics)) != 0)
    goto cleanup;
  workflow.object_loaded = 1U;
  if (enrich_policy_from_object_target_info_local(analysis_policy, backend, &workflow.object, NULL, 0U,
      &diagnostics) != 0) {
    goto cleanup;
  }
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &workflow.object);
  if (!validate_effective_policy_against_object_local(&diagnostics, &workflow.object, analysis_policy))
    goto cleanup;
  result = facts_v2_direct_rebuild_object_alloc(backend_name, display_path != NULL ? display_path : "", backend,
    &workflow.object, analysis_policy, output_path, out_data, out_size, out_source_profile_json,
    out_direct_profile_json, compare_original ? data : NULL, compare_original ? size : 0U, out_error,
    workflow.arena, &diagnostics);

cleanup:
  if (result != 0 && *out_error == NULL) {
    const char *message = m68k_diag_first_message(&diagnostics);
    if (message == NULL || message[0] == '\0') message = "facts_v2 direct rebuild failed";
    *out_error = m68k_platform_dup_string(message);
  }
  platform_file_workflow_destroy(&workflow);
  return result;
}

int platform_file_facts_v2_direct_rebuild_buffer_bytes_profile_alloc(const char *backend_name,
    const unsigned char *data, size_t size, const char *metadata_path, const char *display_path,
    const char *output_path, unsigned char **out_data, size_t *out_size, char **out_source_profile_json,
    char **out_direct_profile_json, char **out_error) {
  return platform_file_facts_v2_direct_rebuild_buffer_common_alloc(backend_name, data, size, metadata_path,
    display_path, output_path, out_data, out_size, out_source_profile_json, out_direct_profile_json, out_error, 0);
}

int platform_file_facts_v2_direct_rebuild_compare_buffer_bytes_profile_alloc(const char *backend_name,
    const unsigned char *data, size_t size, const char *metadata_path, const char *display_path,
    const char *output_path, unsigned char **out_data, size_t *out_size, char **out_source_profile_json,
    char **out_direct_profile_json, char **out_error) {
  return platform_file_facts_v2_direct_rebuild_buffer_common_alloc(backend_name, data, size, metadata_path,
    display_path, output_path, out_data, out_size, out_source_profile_json, out_direct_profile_json, out_error, 1);
}

static int platform_file_reproduction_compare_object_common_alloc(const char *backend_name,
    const M68kBackend *backend, const M68kObject *object, const unsigned char *original_data,
    size_t original_size, const unsigned char *rebuilt_data, size_t rebuilt_size, char **out_compare_profile_json,
    char **out_error, Arena *workflow_arena, M68kDiagList *diagnostics) {
  M68kAssemblerPolicy assembler_policy;
  M68kReproductionCompareResult compare_result;
  clock_t compare_start;
  double compare_seconds;
  if (out_compare_profile_json == NULL || out_error == NULL) return -1;
  *out_compare_profile_json = NULL;
  *out_error = NULL;
  if (backend == NULL || object == NULL || original_data == NULL || rebuilt_data == NULL) {
    *out_error = m68k_platform_dup_string("invalid reproduction compare input");
    return -1;
  }
  m68k_assembler_policy_derive_preservation(object, &assembler_policy);
  compare_start = clock();
  compare_result = facts_v2_direct_compare_result(backend_name, backend, object, rebuilt_data, rebuilt_size,
    original_data, original_size, &assembler_policy, workflow_arena);
  compare_seconds = elapsed_seconds(compare_start, clock());
  *out_compare_profile_json = facts_v2_reproduction_compare_profile_json_alloc(backend_name, original_size,
    rebuilt_size > UINT32_MAX ? UINT32_MAX : (uint32_t)rebuilt_size, compare_result, compare_seconds,
    &assembler_policy, diagnostics);
  if (*out_compare_profile_json == NULL) {
    *out_error = m68k_platform_dup_string("out of memory");
    return -1;
  }
  return 0;
}

int platform_file_reproduction_compare_path_bytes_profile_alloc(const char *backend_name,
    const char *path, const char *metadata_path, const unsigned char *rebuilt_data, size_t rebuilt_size,
    char **out_compare_profile_json, char **out_error) {
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  PlatformFileWorkflow workflow;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  unsigned char *original_data = NULL;
  size_t original_size = 0U;
  int result = -1;
  if (out_compare_profile_json == NULL || out_error == NULL) return -1;
  *out_compare_profile_json = NULL;
  *out_error = NULL;
  m68k_diag_list_reset(&diagnostics);
  memset(&workflow, 0, sizeof(workflow));
  if (platform_file_workflow_create(&workflow, &diagnostics) != 0) {
    *out_error = m68k_platform_dup_string("out of memory");
    return -1;
  }
  analysis_policy = workflow.analysis_policy;
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL, &diagnostics) != 0)
    goto cleanup;
  if (read_file_to_buffer(path, &original_data, &original_size, m68k_diag_sink(&diagnostics)) != 0) goto cleanup;
  if (load_object_from_path(backend, path, &workflow.object, m68k_diag_sink(&diagnostics)) != 0) goto cleanup;
  workflow.object_loaded = 1U;
  result = platform_file_reproduction_compare_object_common_alloc(backend_name, backend, &workflow.object,
    original_data, original_size, rebuilt_data, rebuilt_size, out_compare_profile_json, out_error,
    workflow.arena, &diagnostics);

cleanup:
  if (result != 0 && *out_error == NULL) {
    const char *message = m68k_diag_first_message(&diagnostics);
    *out_error = m68k_platform_dup_string(message != NULL ? message : "reproduction compare failed");
  }
  free(original_data);
  platform_file_workflow_destroy(&workflow);
  return result;
}

int platform_file_reproduction_compare_buffer_bytes_profile_alloc(const char *backend_name,
    const unsigned char *data, size_t size, const char *metadata_path, const char *display_path,
    const unsigned char *rebuilt_data, size_t rebuilt_size, char **out_compare_profile_json, char **out_error) {
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  PlatformFileWorkflow workflow;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  int result = -1;
  (void)display_path;
  if (out_compare_profile_json == NULL || out_error == NULL) return -1;
  *out_compare_profile_json = NULL;
  *out_error = NULL;
  m68k_diag_list_reset(&diagnostics);
  memset(&workflow, 0, sizeof(workflow));
  if (platform_file_workflow_create(&workflow, &diagnostics) != 0) {
    *out_error = m68k_platform_dup_string("out of memory");
    return -1;
  }
  analysis_policy = workflow.analysis_policy;
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL, &diagnostics) != 0)
    goto cleanup;
  if (load_object_from_buffer(backend, data, size, &workflow.object, m68k_diag_sink(&diagnostics)) != 0)
    goto cleanup;
  workflow.object_loaded = 1U;
  result = platform_file_reproduction_compare_object_common_alloc(backend_name, backend, &workflow.object, data,
    size, rebuilt_data, rebuilt_size, out_compare_profile_json, out_error, workflow.arena, &diagnostics);

cleanup:
  if (result != 0 && *out_error == NULL) {
    const char *message = m68k_diag_first_message(&diagnostics);
    *out_error = m68k_platform_dup_string(message != NULL ? message : "reproduction compare failed");
  }
  platform_file_workflow_destroy(&workflow);
  return result;
}

int platform_file_facts_v2_listing_artifact_path_create(const char *backend_name, const char *path,
    const char *metadata_path, const char *include_dir, PlatformFileListingArtifact **out_artifact,
    char **out_error) {
  M68kDiagList diagnostics = {0};
  PlatformFileListingArtifact *artifact = NULL;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  (void)include_dir;
  if (out_artifact != NULL) *out_artifact = NULL;
  if (out_error != NULL) *out_error = NULL;
  if (out_artifact == NULL || out_error == NULL || backend_name == NULL || path == NULL) {
    if (out_error != NULL) *out_error = m68k_platform_dup_string("invalid listing artifact request");
    return -1;
  }
  artifact = listing_artifact_alloc_base(backend_name, path, &diagnostics);
  if (artifact == NULL) goto fail;
  if (configure_analysis_policy_for_alloc(&artifact->policy, backend_name, metadata_path, NULL, &diagnostics) != 0)
    goto fail;
  if (load_object_from_path(backend, path, &artifact->object, m68k_diag_sink(&diagnostics)) != 0) goto fail;
  if (enrich_policy_from_object_target_info_local(&artifact->policy, backend, &artifact->object, NULL, 0U,
      &diagnostics) != 0) {
    goto fail;
  }
  enrich_policy_pointer_targets_from_object_local(&artifact->policy, &artifact->object);
  if (!validate_effective_policy_against_object_local(&diagnostics, &artifact->object, &artifact->policy)) goto fail;
  if (!listing_validate_shared_executable_ranges(backend_name, &artifact->object, &diagnostics)) goto fail;
  if (listing_artifact_build_analysis(artifact, &diagnostics) != 0) goto fail;
  *out_artifact = artifact;
  return 0;

fail:
  platform_file_facts_v2_listing_artifact_destroy(artifact);
  return listing_artifact_set_error(out_error, &diagnostics, "listing artifact create failed");
}

int platform_file_facts_v2_listing_artifact_raw_path_create(const char *platform_name, const char *path,
    uint32_t entry_address, uint32_t has_runtime_load_address, uint32_t runtime_load_address,
    const char *metadata_path, const char *include_dir, PlatformFileListingArtifact **out_artifact,
    char **out_error) {
  M68kDiagList diagnostics = {0};
  PlatformFileListingArtifact *artifact = NULL;
  (void)include_dir;
  if (out_artifact != NULL) *out_artifact = NULL;
  if (out_error != NULL) *out_error = NULL;
  if (out_artifact == NULL || out_error == NULL || platform_name == NULL || path == NULL) {
    if (out_error != NULL) *out_error = m68k_platform_dup_string("invalid listing artifact request");
    return -1;
  }
  artifact = listing_artifact_alloc_base(platform_name, path, &diagnostics);
  if (artifact == NULL) goto fail;
  if (configure_analysis_policy_for_alloc(&artifact->policy, platform_name, metadata_path, NULL, &diagnostics) != 0)
    goto fail;
  if (load_raw_object_from_path(platform_name, path, &artifact->object, m68k_diag_sink(&diagnostics)) != 0)
    goto fail;
  if (!policy_add_raw_runtime_load_range_local(&artifact->policy, &artifact->object,
        (uint8_t)(has_runtime_load_address != 0U), runtime_load_address, &diagnostics) ||
      !policy_set_raw_entry_address_local(&artifact->policy, &artifact->object, entry_address,
        (uint8_t)(has_runtime_load_address != 0U), &diagnostics))
    goto fail;
  enrich_policy_pointer_targets_from_object_local(&artifact->policy, &artifact->object);
  if (!validate_effective_policy_against_object_local(&diagnostics, &artifact->object, &artifact->policy)) goto fail;
  if (listing_artifact_build_analysis(artifact, &diagnostics) != 0) goto fail;
  *out_artifact = artifact;
  return 0;

fail:
  platform_file_facts_v2_listing_artifact_destroy(artifact);
  return listing_artifact_set_error(out_error, &diagnostics, "listing artifact create failed");
}

int platform_file_facts_v2_listing_artifact_flat_m68k_buffer_create(
    const unsigned char *data, size_t size, const char *display_path, const char *metadata_path,
    const char *include_dir, PlatformFileListingArtifact **out_artifact, char **out_error) {
  M68kDiagList diagnostics = {0};
  PlatformFileListingArtifact *artifact = NULL;
  (void)include_dir;
  if (out_artifact != NULL) *out_artifact = NULL;
  if (out_error != NULL) *out_error = NULL;
  if (out_artifact == NULL || out_error == NULL || data == NULL || display_path == NULL || size > UINT32_MAX) {
    if (out_error != NULL) *out_error = m68k_platform_dup_string("invalid flat M68K listing artifact request");
    return -1;
  }
  artifact = listing_artifact_alloc_base("m68k-flat-buffer", display_path, &diagnostics);
  if (artifact == NULL) goto fail;
  if (load_flat_m68k_object_from_buffer(data, size, &artifact->object, m68k_diag_sink(&diagnostics)) != 0)
    goto fail;
  artifact->object.platform_backend_kind = M68K_PLATFORM_BACKEND_MACOS;
  if (configure_flat_m68k_buffer_policy(&artifact->policy, &artifact->object, metadata_path, &diagnostics) != 0)
    goto fail;
  enrich_policy_pointer_targets_from_object_local(&artifact->policy, &artifact->object);
  if (!validate_effective_policy_against_object_local(&diagnostics, &artifact->object, &artifact->policy)) goto fail;
  if (listing_artifact_build_analysis(artifact, &diagnostics) != 0) goto fail;
  *out_artifact = artifact;
  return 0;

fail:
  platform_file_facts_v2_listing_artifact_destroy(artifact);
  return listing_artifact_set_error(out_error, &diagnostics, "flat M68K listing artifact create failed");
}

int platform_file_facts_v2_listing_artifact_macos_code_buffer_create(
    const unsigned char *data, size_t size, const char *display_path, const char *metadata_path,
    const char *include_dir, PlatformFileListingArtifact **out_artifact, char **out_error) {
  M68kDiagList diagnostics = {0};
  PlatformFileListingArtifact *artifact = NULL;
  (void)include_dir;
  if (out_artifact != NULL) *out_artifact = NULL;
  if (out_error != NULL) *out_error = NULL;
  if (out_artifact == NULL || out_error == NULL || data == NULL || display_path == NULL || size > UINT32_MAX) {
    if (out_error != NULL) *out_error = m68k_platform_dup_string("invalid Mac CODE listing artifact request");
    return -1;
  }
  artifact = listing_artifact_alloc_base("macos-code", display_path, &diagnostics);
  if (artifact == NULL) goto fail;
  if (load_flat_m68k_object_from_buffer(data, size, &artifact->object, m68k_diag_sink(&diagnostics)) != 0)
    goto fail;
  artifact->object.platform_backend_kind = M68K_PLATFORM_BACKEND_MACOS;
  if (configure_flat_m68k_buffer_policy(&artifact->policy, &artifact->object, metadata_path, &diagnostics) != 0)
    goto fail;
  enrich_policy_pointer_targets_from_object_local(&artifact->policy, &artifact->object);
  if (!validate_effective_policy_against_object_local(&diagnostics, &artifact->object, &artifact->policy)) goto fail;
  if (listing_artifact_build_analysis(artifact, &diagnostics) != 0) goto fail;
  *out_artifact = artifact;
  return 0;

fail:
  platform_file_facts_v2_listing_artifact_destroy(artifact);
  return listing_artifact_set_error(out_error, &diagnostics, "Mac CODE listing artifact create failed");
}

static int load_macos_hfs_code_resource_object_policy_local(const unsigned char *data, size_t size,
    const char *hfs_path, int32_t resource_id, const char *metadata_path, M68kObject *object,
    M68kAnalysisPolicy *policy, uint8_t *out_object_loaded, M68kDiagList *diagnostics) {
  PlatformMacosHFSCatalog catalog;
  PlatformMacosHFSDirectoryInfo *directories = NULL;
  PlatformMacosHFSFileInfo *files = NULL;
  PlatformMacosHFSFileInfo *selected_file = NULL;
  PlatformMacosResourceFork resource_fork_info;
  PlatformMacosResourceInfo *resources = NULL;
  const PlatformMacosResourceInfo *selected_resource = NULL;
  const PlatformMacosResourceInfo *code0_resource = NULL;
  unsigned char *resource_fork = NULL;
  unsigned char *code_bytes = NULL;
  char *copy_error = NULL;
  char path[PLATFORM_MACOS_HFS_PATH_SIZE];
  uint32_t payload_offset = 0U;
  uint32_t payload_size = 0U;
  uint32_t code_start = 0U;
  uint32_t code_size = 0U;
  size_t index;
  int find_status;
  int result = -1;
  if (out_object_loaded != NULL) *out_object_loaded = 0U;
  memset(&catalog, 0, sizeof(catalog));
  memset(&resource_fork_info, 0, sizeof(resource_fork_info));
  if (data == NULL || size == 0U || hfs_path == NULL || hfs_path[0] == '\0' ||
      resource_id <= 0 || resource_id > 32767 || object == NULL || policy == NULL || diagnostics == NULL) {
    if (diagnostics != NULL) platform_file_add_error(diagnostics, "invalid Mac HFS CODE resource request");
    goto cleanup;
  }
  if (platform_macos_hfs_catalog_parse(data, size, &catalog, NULL, 0U, NULL, 0U) != 0) {
    platform_file_add_error(diagnostics, "Mac HFS catalog parse failed");
    goto cleanup;
  }
  directories = (PlatformMacosHFSDirectoryInfo *)calloc(catalog.directory_count ? catalog.directory_count : 1U,
    sizeof(*directories));
  files = (PlatformMacosHFSFileInfo *)calloc(catalog.file_count ? catalog.file_count : 1U, sizeof(*files));
  if (directories == NULL || files == NULL) {
    platform_file_add_error(diagnostics, "out of memory reading Mac HFS catalog");
    goto cleanup;
  }
  if (platform_macos_hfs_catalog_parse(data, size, &catalog, directories, catalog.directory_count,
      files, catalog.file_count) != 0) {
    platform_file_add_error(diagnostics, "Mac HFS catalog detail parse failed");
    goto cleanup;
  }
  for (index = 0U; index < catalog.file_count; ++index) {
    if (platform_macos_hfs_file_path(directories, catalog.directory_count, &files[index], path, sizeof(path)) != 0)
      continue;
    if (macos_hfs_path_matches(&catalog.volume, path, hfs_path)) {
      selected_file = &files[index];
      break;
    }
  }
  if (selected_file == NULL) {
    platform_file_add_error(diagnostics, "Mac HFS path was not found");
    goto cleanup;
  }
  if (macos_copy_fork_or_error(data, size, &catalog.volume, selected_file->resource_extents,
      selected_file->resource_size, &resource_fork, &copy_error) != 0) {
    platform_file_add_error(diagnostics, copy_error != NULL ? copy_error : "Mac HFS resource fork copy failed");
    goto cleanup;
  }
  if (platform_macos_resource_fork_parse(resource_fork, selected_file->resource_size, &resource_fork_info,
      NULL, 0U, NULL, 0U) != 0) {
    platform_file_add_error(diagnostics, "Mac resource fork parse failed");
    goto cleanup;
  }
  resources = (PlatformMacosResourceInfo *)calloc(
    resource_fork_info.resource_count ? resource_fork_info.resource_count : 1U, sizeof(*resources));
  if (resources == NULL) {
    platform_file_add_error(diagnostics, "out of memory reading Mac resources");
    goto cleanup;
  }
  if (platform_macos_resource_fork_parse(resource_fork, selected_file->resource_size, &resource_fork_info,
      NULL, 0U, resources, resource_fork_info.resource_count) != 0) {
    platform_file_add_error(diagnostics, "Mac resource fork detail parse failed");
    goto cleanup;
  }
  selected_resource = macos_find_resource(resources, resource_fork_info.resource_count, "CODE", (int16_t)resource_id);
  code0_resource = macos_find_code0_resource(resources, resource_fork_info.resource_count);
  if (selected_resource == NULL ||
      platform_macos_code_metadata_executable_range(&selected_resource->code, &code_start, &code_size) != 0) {
    platform_file_add_error(diagnostics, "Mac CODE resource has no confirmed executable range");
    goto cleanup;
  }
  find_status = platform_macos_resource_fork_find_payload(resource_fork, selected_file->resource_size, "CODE",
    (int16_t)resource_id, &payload_offset, &payload_size);
  if (find_status != 0 || code_start > payload_size || code_size > payload_size - code_start) {
    platform_file_add_error(diagnostics, "Mac CODE executable range is outside the resource payload");
    goto cleanup;
  }
  code_bytes = (unsigned char *)malloc(code_size ? code_size : 1U);
  if (code_bytes == NULL) {
    platform_file_add_error(diagnostics, "out of memory reading Mac CODE bytes");
    goto cleanup;
  }
  if (code_size != 0U) memcpy(code_bytes, resource_fork + payload_offset + code_start, code_size);
  if (load_flat_m68k_object_from_buffer(code_bytes, code_size, object, m68k_diag_sink(diagnostics)) != 0)
    goto cleanup;
  if (out_object_loaded != NULL) *out_object_loaded = 1U;
  object->platform_backend_kind = M68K_PLATFORM_BACKEND_MACOS;
  if (code0_resource != NULL &&
      platform_macos_object_set_a5_world_layout(object, code0_resource->resource_id, &code0_resource->code) != 0) {
    platform_file_add_error(diagnostics, "Mac CODE 0 A5 world layout attachment failed");
    goto cleanup;
  }
  if (configure_flat_m68k_buffer_policy(policy, object, metadata_path, diagnostics) != 0) goto cleanup;
  enrich_policy_pointer_targets_from_object_local(policy, object);
  if (!validate_effective_policy_against_object_local(diagnostics, object, policy)) goto cleanup;
  result = 0;

cleanup:
  free(copy_error);
  free(code_bytes);
  free(resource_fork);
  free(resources);
  free(files);
  free(directories);
  return result;
}

int platform_file_facts_v2_listing_artifact_macos_hfs_code_resource_create(
    const unsigned char *data, size_t size, const char *hfs_path, int32_t resource_id,
    const char *metadata_path, const char *include_dir, PlatformFileListingArtifact **out_artifact,
    char **out_error) {
  M68kDiagList diagnostics = {0};
  PlatformFileListingArtifact *artifact = NULL;
  (void)include_dir;
  if (out_artifact != NULL) *out_artifact = NULL;
  if (out_error != NULL) *out_error = NULL;
  if (out_artifact == NULL || out_error == NULL || data == NULL || size == 0U ||
      hfs_path == NULL || hfs_path[0] == '\0' || resource_id <= 0 || resource_id > 32767) {
    if (out_error != NULL) *out_error = m68k_platform_dup_string("invalid Mac HFS CODE listing artifact request");
    return -1;
  }
  artifact = listing_artifact_alloc_base("macos-code", hfs_path, &diagnostics);
  if (artifact == NULL) goto fail;
  if (load_macos_hfs_code_resource_object_policy_local(data, size, hfs_path, resource_id, metadata_path,
      &artifact->object, &artifact->policy, NULL, &diagnostics) != 0)
    goto fail;
  if (listing_artifact_build_analysis(artifact, &diagnostics) != 0) goto fail;
  *out_artifact = artifact;
  return 0;

fail:
  platform_file_facts_v2_listing_artifact_destroy(artifact);
  return listing_artifact_set_error(out_error, &diagnostics, "Mac HFS CODE listing artifact create failed");
}

int platform_file_source_quality_explain_macos_hfs_code_resource_json_alloc(
    const unsigned char *data, size_t size, const char *hfs_path, int32_t resource_id,
    const char *metadata_path, char **out_text) {
  PlatformFileTextResult result;
  PlatformFileWorkflow workflow;
  memset(&result, 0, sizeof(result));
  memset(&workflow, 0, sizeof(workflow));
  if (out_text == NULL) return -1;
  *out_text = NULL;
  if (data == NULL || size == 0U || hfs_path == NULL || hfs_path[0] == '\0' ||
      resource_id <= 0 || resource_id > 32767) {
    platform_file_add_error(&result.diagnostics, "invalid Mac HFS CODE source-quality explanation request");
    goto cleanup;
  }
  if (platform_file_workflow_create(&workflow, &result.diagnostics) != 0) goto cleanup;
  if (load_macos_hfs_code_resource_object_policy_local(data, size, hfs_path, resource_id, metadata_path,
      &workflow.object, workflow.analysis_policy, &workflow.object_loaded, &result.diagnostics) != 0)
    goto cleanup;
  result = facts_v2_source_quality_explain_object_json("macos-code", hfs_path, &workflow.object,
    workflow.analysis_policy);

cleanup:
  platform_file_workflow_destroy(&workflow);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_listing_artifact_window_json_alloc(PlatformFileListingArtifact *artifact,
    uint32_t start, uint32_t count, char **out_text) {
  PlatformFileTextResult result;
  JsonBuilder builder = {0};
  char *json = NULL;
  clock_t window_start;
  clock_t window_end;
  memset(&result, 0, sizeof(result));
  if (out_text == NULL) return -1;
  *out_text = NULL;
  if (artifact == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid listing artifact");
    return text_result_to_alloc(&result, out_text);
  }
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"listing\":") != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  window_start = clock();
  if (source_file_listing_window_from_render_plan_with_index_append_json(&builder, NULL, &artifact->source_plan,
      artifact->object.platform_backend_kind, &artifact->source_analysis.policy, &artifact->source_analysis,
      "full", 0, &artifact->listing_row_index, start, count, m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "facts_v2 listing window render-plan emission failed");
    goto cleanup;
  }
  window_end = clock();
  if (json_builder_append(&builder, ",\"profile\":{\"generation\":\"facts_v2_listing_artifact_window\""
      ) != 0 ||
      listing_artifact_append_profile_identity(&builder, artifact) != 0 ||
      json_builder_append(&builder, ",\"analysis_backend\":\"facts_v2\",\"path\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->path) != 0 ||
      json_builder_append(&builder, ",\"facts_v2\":") != 0 ||
      json_builder_append_facts_v2_profile(&builder, &artifact->profile) != 0 ||
      json_builder_appendf(&builder,
        ",\"listing_total_rows\":%u,\"timing\":{\"source_seconds\":%.6f,\"window_emit_seconds\":%.6f,"
        "\"total_seconds\":%.6f}}}",
        (unsigned)artifact->listing_total_rows,
        artifact->source_seconds, elapsed_seconds(window_start, window_end),
        elapsed_seconds(window_start, window_end)) != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  json = json_builder_build(&builder);
  if (json == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  result.text = json;
  json = NULL;

cleanup:
  json_builder_destroy(&builder);
  platform_file_free_text(json);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_listing_artifact_addr_window_json_alloc(PlatformFileListingArtifact *artifact,
    int has_addr, uint32_t addr, uint32_t before, uint32_t after, char **out_text) {
  PlatformFileTextResult result;
  JsonBuilder builder = {0};
  char *json = NULL;
  clock_t window_start;
  clock_t window_end;
  memset(&result, 0, sizeof(result));
  if (out_text == NULL) return -1;
  *out_text = NULL;
  if (artifact == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid listing artifact");
    return text_result_to_alloc(&result, out_text);
  }
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"listing\":") != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  window_start = clock();
  if (source_file_listing_addr_window_from_render_plan_with_index_append_json(&builder, NULL,
      &artifact->source_plan, artifact->object.platform_backend_kind, &artifact->source_analysis.policy,
      &artifact->source_analysis, "full", 0, &artifact->listing_row_index, has_addr, addr, before, after,
      m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "facts_v2 listing address window render-plan emission failed");
    goto cleanup;
  }
  window_end = clock();
  if (json_builder_append(&builder, ",\"profile\":{\"generation\":\"facts_v2_listing_artifact_addr_window\","
        "\"backend\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->backend_name) != 0 ||
      json_builder_append(&builder, ",\"analysis_backend\":\"facts_v2\",\"path\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->path) != 0 ||
      json_builder_append(&builder, ",\"facts_v2\":") != 0 ||
      json_builder_append_facts_v2_profile(&builder, &artifact->profile) != 0 ||
      json_builder_appendf(&builder,
        ",\"listing_total_rows\":%u,\"listing_addr_block_count\":%u,"
        "\"timing\":{\"source_seconds\":%.6f,\"window_emit_seconds\":%.6f,\"total_seconds\":%.6f}}}",
        (unsigned)artifact->listing_total_rows, (unsigned)artifact->listing_row_index.block_count,
        artifact->source_seconds, elapsed_seconds(window_start, window_end),
        elapsed_seconds(window_start, window_end)) != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  json = json_builder_build(&builder);
  if (json == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  result.text = json;
  json = NULL;

cleanup:
  json_builder_destroy(&builder);
  platform_file_free_text(json);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_listing_artifact_source_offset_row_json_alloc(PlatformFileListingArtifact *artifact,
    int has_section, uint32_t section_index, uint32_t offset, char **out_text) {
  PlatformFileTextResult result;
  JsonBuilder builder = {0};
  char *json = NULL;
  size_t row_index = 0U;
  int found = 0;
  clock_t lookup_start;
  clock_t lookup_end;
  memset(&result, 0, sizeof(result));
  if (out_text == NULL) return -1;
  *out_text = NULL;
  if (artifact == NULL || !has_section) {
    platform_file_add_error(&result.diagnostics, "invalid listing artifact source-offset lookup request");
    return text_result_to_alloc(&result, out_text);
  }
  lookup_start = clock();
  if (source_file_listing_source_offset_row_from_render_plan_with_index(&artifact->source_plan,
      &artifact->listing_row_index, section_index, offset, &row_index, &found,
      m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "facts_v2 listing source-offset lookup failed");
    goto cleanup;
  }
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"found\":") != 0 ||
      json_builder_append(&builder, found ? "true" : "false") != 0 ||
      json_builder_append(&builder, ",\"row_index\":") != 0)
    goto oom;
  if (found) {
    if (json_builder_appendf(&builder, "%u", (unsigned)row_index) != 0) goto oom;
  } else if (json_builder_append(&builder, "null") != 0) goto oom;
  if (json_builder_append(&builder, ",\"listing\":") != 0) goto oom;
  if (found) {
    if (source_file_listing_window_from_render_plan_with_index_append_json(&builder, NULL, &artifact->source_plan,
        artifact->object.platform_backend_kind, &artifact->source_analysis.policy, &artifact->source_analysis,
        "full", 0, &artifact->listing_row_index, row_index, 1U, m68k_diag_sink(&result.diagnostics)) != 0) {
      if (!m68k_diag_has_errors(&result.diagnostics))
        platform_file_add_error(&result.diagnostics, "facts_v2 listing source-offset row emission failed");
      goto cleanup;
    }
  } else if (json_builder_append(&builder, "{\"rows\":[]}") != 0) goto oom;
  lookup_end = clock();
  if (json_builder_append(&builder, ",\"profile\":{\"generation\":\"facts_v2_listing_artifact_source_offset_row\","
        "\"backend\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->backend_name) != 0 ||
      json_builder_append(&builder, ",\"analysis_backend\":\"facts_v2\",\"path\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->path) != 0 ||
      json_builder_appendf(&builder,
        ",\"listing_total_rows\":%u,\"timing\":{\"source_seconds\":%.6f,\"lookup_emit_seconds\":%.6f,"
        "\"total_seconds\":%.6f}}}",
        (unsigned)artifact->listing_total_rows, artifact->source_seconds, elapsed_seconds(lookup_start, lookup_end),
        elapsed_seconds(lookup_start, lookup_end)) != 0)
    goto oom;
  json = json_builder_build(&builder);
  if (json == NULL) goto oom;
  result.text = json;
  json = NULL;
  goto cleanup;

oom:
  platform_file_add_error(&result.diagnostics, "out of memory");

cleanup:
  json_builder_destroy(&builder);
  platform_file_free_text(json);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_listing_artifact_runtime_address_row_json_alloc(PlatformFileListingArtifact *artifact,
    uint32_t address, char **out_text) {
  PlatformFileTextResult result;
  JsonBuilder builder = {0};
  char *json = NULL;
  size_t row_index = 0U;
  int found = 0;
  clock_t lookup_start;
  clock_t lookup_end;
  memset(&result, 0, sizeof(result));
  if (out_text == NULL) return -1;
  *out_text = NULL;
  if (artifact == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid listing artifact runtime-address lookup request");
    return text_result_to_alloc(&result, out_text);
  }
  lookup_start = clock();
  if (source_file_listing_runtime_address_row_from_render_plan_with_index(&artifact->source_plan,
      &artifact->listing_row_index, address, &row_index, &found, m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "facts_v2 listing runtime-address lookup failed");
    goto cleanup;
  }
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"found\":") != 0 ||
      json_builder_append(&builder, found ? "true" : "false") != 0 ||
      json_builder_append(&builder, ",\"row_index\":") != 0)
    goto oom;
  if (found) {
    if (json_builder_appendf(&builder, "%u", (unsigned)row_index) != 0) goto oom;
  } else if (json_builder_append(&builder, "null") != 0) goto oom;
  if (json_builder_append(&builder, ",\"listing\":") != 0) goto oom;
  if (found) {
    if (source_file_listing_window_from_render_plan_with_index_append_json(&builder, NULL, &artifact->source_plan,
        artifact->object.platform_backend_kind, &artifact->source_analysis.policy, &artifact->source_analysis,
        "full", 0, &artifact->listing_row_index, row_index, 1U, m68k_diag_sink(&result.diagnostics)) != 0) {
      if (!m68k_diag_has_errors(&result.diagnostics))
        platform_file_add_error(&result.diagnostics, "facts_v2 listing runtime-address row emission failed");
      goto cleanup;
    }
  } else if (json_builder_append(&builder, "{\"rows\":[]}") != 0) goto oom;
  lookup_end = clock();
  if (json_builder_append(&builder, ",\"profile\":{\"generation\":\"facts_v2_listing_artifact_runtime_address_row\","
        "\"backend\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->backend_name) != 0 ||
      json_builder_append(&builder, ",\"analysis_backend\":\"facts_v2\",\"path\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->path) != 0 ||
      json_builder_appendf(&builder,
        ",\"listing_total_rows\":%u,\"timing\":{\"source_seconds\":%.6f,\"lookup_emit_seconds\":%.6f,"
        "\"total_seconds\":%.6f}}}",
        (unsigned)artifact->listing_total_rows, artifact->source_seconds, elapsed_seconds(lookup_start, lookup_end),
        elapsed_seconds(lookup_start, lookup_end)) != 0)
    goto oom;
  json = json_builder_build(&builder);
  if (json == NULL) goto oom;
  result.text = json;
  json = NULL;
  goto cleanup;

oom:
  platform_file_add_error(&result.diagnostics, "out of memory");

cleanup:
  json_builder_destroy(&builder);
  platform_file_free_text(json);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_listing_artifact_anchor_window_json_alloc(PlatformFileListingArtifact *artifact,
    const char *anchor_code, uint32_t count, char **out_text) {
  PlatformFileTextResult result;
  JsonBuilder builder = {0};
  char *json = NULL;
  size_t start = 0U;
  size_t safe_count;
  clock_t window_start;
  clock_t window_end;
  memset(&result, 0, sizeof(result));
  if (out_text == NULL) return -1;
  *out_text = NULL;
  if (artifact == NULL || anchor_code == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid listing artifact anchor window request");
    return text_result_to_alloc(&result, out_text);
  }
  window_start = clock();
  if (source_file_listing_anchor_code_row_from_render_plan_with_index(NULL, &artifact->source_plan,
      artifact->object.platform_backend_kind, &artifact->source_analysis.policy, &artifact->source_analysis,
      "full", 0, &artifact->listing_row_index, anchor_code, &start, m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "facts_v2 listing anchor lookup failed");
    goto cleanup;
  }
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"listing\":") != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  safe_count = count != 0U ? (size_t)count : 240U;
  if (source_file_listing_window_from_render_plan_with_index_append_json(&builder, NULL, &artifact->source_plan,
      artifact->object.platform_backend_kind, &artifact->source_analysis.policy, &artifact->source_analysis,
      "full", 0, &artifact->listing_row_index, start, safe_count, m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "facts_v2 listing anchor window emission failed");
    goto cleanup;
  }
  window_end = clock();
  if (json_builder_append(&builder, ",\"profile\":{\"generation\":\"facts_v2_listing_artifact_anchor_window\","
        "\"backend\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->backend_name) != 0 ||
      json_builder_append(&builder, ",\"analysis_backend\":\"facts_v2\",\"path\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->path) != 0 ||
      json_builder_append(&builder, ",\"facts_v2\":") != 0 ||
      json_builder_append_facts_v2_profile(&builder, &artifact->profile) != 0 ||
      json_builder_appendf(&builder,
        ",\"listing_total_rows\":%u,\"timing\":{\"source_seconds\":%.6f,\"window_emit_seconds\":%.6f,"
        "\"total_seconds\":%.6f}}}",
        (unsigned)artifact->listing_total_rows,
        artifact->source_seconds, elapsed_seconds(window_start, window_end),
        elapsed_seconds(window_start, window_end)) != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  json = json_builder_build(&builder);
  if (json == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  result.text = json;
  json = NULL;

cleanup:
  json_builder_destroy(&builder);
  platform_file_free_text(json);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_listing_artifact_source_text_profile_alloc(PlatformFileListingArtifact *artifact,
    char **out_text, char **out_profile_json) {
  PlatformFileTextResult result;
  char *profile_json = NULL;
  clock_t source_start;
  clock_t source_end;
  memset(&result, 0, sizeof(result));
  if (out_text == NULL || out_profile_json == NULL) return -1;
  *out_text = NULL;
  *out_profile_json = NULL;
  if (artifact == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid listing artifact");
    return text_result_to_alloc(&result, out_text);
  }
  source_start = clock();
  if (m68k_render_plan_emit_all_alloc(&artifact->source_plan, &result.text) != 0) {
    platform_file_add_error(&result.diagnostics, "facts_v2 listing artifact source emission failed");
    return text_result_to_alloc(&result, out_text);
  }
  source_end = clock();
  profile_json = listing_artifact_profile_json_alloc(artifact, "facts_v2_listing_artifact_source_text",
    "source_emit_seconds", elapsed_seconds(source_start, source_end), &result.diagnostics);
  if (profile_json == NULL) {
    platform_file_free_text(result.text);
    result.text = NULL;
    return text_result_to_alloc(&result, out_text);
  }
  *out_text = result.text;
  *out_profile_json = profile_json;
  result.text = NULL;
  return 0;
}

int platform_file_facts_v2_listing_artifact_summary_json_alloc(PlatformFileListingArtifact *artifact,
    char **out_text) {
  PlatformFileTextResult result;
  JsonBuilder builder = {0};
  char *json = NULL;
  clock_t summary_start;
  clock_t summary_end;
  memset(&result, 0, sizeof(result));
  if (out_text == NULL) return -1;
  *out_text = NULL;
  if (artifact == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid listing artifact");
    return text_result_to_alloc(&result, out_text);
  }
  summary_start = clock();
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"summary\":{\"total_rows\":") != 0 ||
      json_builder_appendf(&builder, "%u", (unsigned)artifact->listing_total_rows) != 0 ||
      json_builder_append(&builder, "},\"profile\":{\"generation\":\"facts_v2_listing_artifact_summary\"") != 0 ||
      listing_artifact_append_profile_identity(&builder, artifact) != 0 ||
      json_builder_append(&builder, ",\"analysis_backend\":\"facts_v2\",\"path\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->path) != 0 ||
      json_builder_append(&builder, ",\"facts_v2\":") != 0 ||
      json_builder_append_facts_v2_profile(&builder, &artifact->profile) != 0 ||
      json_builder_appendf(&builder,
        ",\"timing\":{\"source_seconds\":%.6f,\"summary_json_seconds\":",
        artifact->source_seconds) != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  summary_end = clock();
  if (json_builder_appendf(&builder, "%.6f,\"total_seconds\":%.6f}}}",
      elapsed_seconds(summary_start, summary_end), elapsed_seconds(summary_start, summary_end)) != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  json = json_builder_build(&builder);
  if (json == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  result.text = json;
  json = NULL;

cleanup:
  free(json);
  json_builder_destroy(&builder);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_listing_artifact_analysis_json_alloc(PlatformFileListingArtifact *artifact,
    char **out_text) {
  PlatformFileTextResult result;
  JsonBuilder builder = {0};
  char *analysis_json = NULL;
  char *json = NULL;
  clock_t analysis_start;
  clock_t analysis_end;
  PlatformDecompressionAnalysisTiming decompression_timing;
  memset(&result, 0, sizeof(result));
  memset(&decompression_timing, 0, sizeof(decompression_timing));
  if (out_text == NULL) return -1;
  *out_text = NULL;
  if (artifact == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid listing artifact");
    return text_result_to_alloc(&result, out_text);
  }
  analysis_start = clock();
  if (source_analysis_to_json_with_render_evidence(&artifact->source_analysis,
      artifact->render_evidence_live ? &artifact->render_evidence : NULL, &analysis_json,
      m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "facts_v2 source analysis json failed");
    goto cleanup;
  }
  analysis_end = clock();
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"analysis\":") != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  if (analysis_json == NULL ||
      append_analysis_json_with_decompression_profile(&builder, analysis_json, artifact->backend_name, &artifact->object,
        &artifact->source_analysis, &artifact->source_plan, NULL, &decompression_timing) != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  if (json_builder_append(&builder, ",\"profile\":{\"generation\":\"facts_v2_listing_artifact_analysis\","
        "\"backend\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->backend_name) != 0 ||
      json_builder_append(&builder, ",\"analysis_backend\":\"facts_v2\",\"path\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->path) != 0 ||
      json_builder_append(&builder, ",\"facts_v2\":") != 0 ||
      json_builder_append_facts_v2_profile(&builder, &artifact->profile) != 0 ||
      json_builder_append(&builder, ",\"decompression\":") != 0 ||
      append_decompression_timing_json(&builder, &decompression_timing) != 0 ||
      json_builder_appendf(&builder,
        ",\"timing\":{\"source_seconds\":%.6f,\"analysis_json_seconds\":%.6f,\"total_seconds\":%.6f}}}",
        artifact->source_seconds, elapsed_seconds(analysis_start, analysis_end),
        artifact->source_seconds + elapsed_seconds(analysis_start, analysis_end)) != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  json = json_builder_build(&builder);
  if (json == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  result.text = json;
  json = NULL;

cleanup:
  json_builder_destroy(&builder);
  platform_file_free_text(json);
  platform_file_free_text(analysis_json);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_listing_artifact_navigation_json_alloc(PlatformFileListingArtifact *artifact,
    char **out_text) {
  PlatformFileTextResult result;
  JsonBuilder builder = {0};
  char *json = NULL;
  clock_t navigation_start;
  clock_t navigation_end;
  memset(&result, 0, sizeof(result));
  if (out_text == NULL) return -1;
  *out_text = NULL;
  if (artifact == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid listing artifact");
    return text_result_to_alloc(&result, out_text);
  }
  navigation_start = clock();
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"navigation\":") != 0 ||
      source_file_listing_navigation_from_render_plan_append_json(&builder, NULL, &artifact->source_plan,
        artifact->object.platform_backend_kind, &artifact->source_analysis.policy, &artifact->source_analysis,
        "full", 0, m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "facts_v2 listing navigation render-plan emission failed");
    goto cleanup;
  }
  navigation_end = clock();
  if (json_builder_append(&builder, ",\"profile\":{\"generation\":\"facts_v2_listing_artifact_navigation\","
        "\"backend\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->backend_name) != 0 ||
      json_builder_append(&builder, ",\"analysis_backend\":\"facts_v2\",\"path\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->path) != 0 ||
      json_builder_append(&builder, ",\"facts_v2\":") != 0 ||
      json_builder_append_facts_v2_profile(&builder, &artifact->profile) != 0 ||
      json_builder_appendf(&builder,
        ",\"timing\":{\"source_seconds\":%.6f,\"navigation_emit_seconds\":%.6f,\"total_seconds\":%.6f}}}",
        artifact->source_seconds, elapsed_seconds(navigation_start, navigation_end),
        elapsed_seconds(navigation_start, navigation_end)) != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  json = json_builder_build(&builder);
  if (json == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  result.text = json;
  json = NULL;

cleanup:
  json_builder_destroy(&builder);
  platform_file_free_text(json);
  return text_result_to_alloc(&result, out_text);
}

void platform_file_facts_v2_listing_artifact_destroy(PlatformFileListingArtifact *artifact) {
  if (artifact == NULL) return;
  if (artifact->render_evidence_live) m68k_ir_render_evidence_destroy(&artifact->render_evidence);
  m68k_render_plan_destroy(&artifact->source_plan);
  m68k_ir_source_analysis_destroy(&artifact->source_analysis);
  m68k_object_destroy(&artifact->object);
  arena_destroy(artifact->listing_index_arena);
  free(artifact->backend_name);
  free(artifact->path);
  memset(artifact, 0, sizeof(*artifact));
  free(artifact);
}

int platform_file_type_catalog_json_alloc(const char *backend_name, char **out_text) {
  PlatformFileTextResult result = platform_file_type_catalog_json(backend_name);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_naming_catalog_json_alloc(const char *backend_name, char **out_text) {
  PlatformFileTextResult result = platform_file_naming_catalog_json(backend_name);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_os_metadata_catalog_json_alloc(const char *backend_name, char **out_text) {
  PlatformFileTextResult result = platform_file_os_metadata_catalog_json(backend_name);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_api_input_struct_json_alloc(const char *backend_name, const char *library_name,
    const char *function_name, const char *input_name, const char *struct_name, char **out_text) {
  PlatformFileTextResult result = platform_file_api_input_struct_json(backend_name, library_name, function_name,
    input_name, struct_name);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_decompression_identify_path_range_json_alloc(const char *provider_id, const char *provider_path,
    const char *path, uint32_t offset, uint32_t size, char **out_text) {
  return platform_decompression_identify_path_range_json_alloc(provider_id, provider_path, path, offset, size,
    out_text);
}

int platform_file_decompression_decompress_path_range_json_alloc(const char *provider_id, const char *provider_path,
    const char *path, uint32_t offset, uint32_t size, const char *output_path, char **out_text) {
  return platform_decompression_decompress_path_range_json_alloc(provider_id, provider_path, path, offset, size,
    output_path, out_text);
}

PLATFORM_FILE_API int platform_file_decompression_decompress_section_range_json_alloc(const char *backend_name,
    const char *path, uint32_t section_index, uint32_t offset, uint32_t size, const char *output_path,
    char **out_text) {
  PlatformDecompressionIdentifyResult result;
  JsonBuilder builder = {0};
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  char error[256];
  int decompress_result = -1;
  if (out_text == NULL) return -1;
  *out_text = NULL;
  memset(&object, 0, sizeof(object));
  error[0] = '\0';
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(NULL)) == 0 &&
      section_index < object.section_count &&
      object.sections[section_index].data != NULL &&
      offset <= object.sections[section_index].data_size &&
      size <= object.sections[section_index].data_size - offset) {
    decompress_result = platform_decompression_decompress_buffer_range("ancient-cli", "",
      object.sections[section_index].data, object.sections[section_index].data_size, offset, size,
      output_path, &result, error, sizeof(error));
    result.has_source_section = 1U;
    result.source_section_index = section_index;
    result.source_section_offset = offset;
  } else {
    snprintf(error, sizeof(error), "invalid decompression section range");
  }
  if (json_builder_create(&builder) != 0) {
    m68k_object_destroy(&object);
    return -1;
  }
  if (decompress_result != 0) {
    if (json_builder_append(&builder, "{\"status\":\"error\",\"error\":") != 0 ||
        json_builder_append_json_string(&builder, error[0] != '\0' ? error : "section decompression failed") != 0 ||
        json_builder_append(&builder, "}") != 0) {
      json_builder_destroy(&builder);
      m68k_object_destroy(&object);
      return -1;
    }
  } else if (json_builder_append(&builder, "{\"status\":\"ok\",\"packed_payloads\":[") != 0 ||
      platform_decompression_append_result_json(&builder, &result) != 0 ||
      json_builder_append(&builder, "]}") != 0) {
    json_builder_destroy(&builder);
    m68k_object_destroy(&object);
    return -1;
  }
  *out_text = json_builder_build(&builder);
  json_builder_destroy(&builder);
  m68k_object_destroy(&object);
  return *out_text == NULL ? -1 : decompress_result;
}

PLATFORM_FILE_API int platform_file_decompression_materialize_self_decrunch_event_json_alloc(
    const char *backend_name, const char *path, const char *event_id, const char *output_path, char **out_text) {
  Arena *scratch_arena = NULL;
  M68kAnalysisPolicy *analysis_policy = NULL;
  M68kFactsV2Profile *profile = NULL;
  M68kSourceAnalysisIR *analysis = NULL;
  M68kObject object;
  M68kDiagList diagnostics;
  JsonBuilder builder = {0};
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  PlatformSelfDecrunchEvent events[16];
  PlatformSelfDecrunchEvent materialized_event;
  size_t event_count = 0U;
  size_t index;
  int found = 0;
  int result = -1;
  if (out_text == NULL) return -1;
  *out_text = NULL;
  memset(&object, 0, sizeof(object));
  memset(events, 0, sizeof(events));
  memset(&materialized_event, 0, sizeof(materialized_event));
  m68k_diag_list_reset(&diagnostics);
  if (backend == NULL || path == NULL || event_id == NULL || event_id[0] == '\0' ||
      output_path == NULL || output_path[0] == '\0') {
    platform_file_add_error(&diagnostics, "invalid self-decrunch materialization request");
    goto cleanup;
  }
  scratch_arena = arena_create(4096U);
  if (scratch_arena == NULL) {
    platform_file_add_error(&diagnostics, "out of memory");
    goto cleanup;
  }
  analysis_policy = (M68kAnalysisPolicy *)arena_calloc(scratch_arena, 1U, sizeof(*analysis_policy));
  profile = (M68kFactsV2Profile *)arena_calloc(scratch_arena, 1U, sizeof(*profile));
  analysis = (M68kSourceAnalysisIR *)arena_calloc(scratch_arena, 1U, sizeof(*analysis));
  if (analysis_policy == NULL || profile == NULL || analysis == NULL) {
    platform_file_add_error(&diagnostics, "out of memory");
    goto cleanup;
  }
  m68k_analysis_policy_init_default(analysis_policy);
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&diagnostics)) != 0) goto cleanup;
  if (enrich_policy_from_object_target_info_local(analysis_policy, backend, &object, NULL, 0U, &diagnostics) != 0)
    goto cleanup;
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&diagnostics, &object, analysis_policy)) goto cleanup;
  if (m68k_facts_v2_collect_source_analysis_profile(&object, analysis_policy, profile, analysis,
      m68k_diag_sink(&diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&diagnostics))
      platform_file_add_error(&diagnostics, "failed building facts_v2 source analysis");
    goto cleanup;
  }
  if (collect_self_decrunch_events_local(&object, analysis, events, sizeof(events) / sizeof(events[0]),
      &event_count, event_id, output_path, &materialized_event, &diagnostics, scratch_arena) != 0) {
    platform_file_add_error(&diagnostics, "failed collecting self-decrunch events");
    goto cleanup;
  }
  for (index = 0U; index < event_count; ++index) {
    char candidate_id[160];
    make_self_decrunch_event_id_local(candidate_id, sizeof(candidate_id), &events[index]);
    if (strcmp(candidate_id, event_id) != 0) continue;
    found = 1;
    if (!events[index].has_simulated_output) {
      platform_file_add_error(&diagnostics, "self-decrunch event has no materializable simulated output");
      goto cleanup;
    }
    if (!materialized_event.has_simulated_output) {
      if (!m68k_diag_has_errors(&diagnostics))
        platform_file_add_error(&diagnostics, "failed materializing simulated self-decrunch output");
      goto cleanup;
    }
    if (events[index].simulated_output_sha256[0] != '\0' &&
        strcmp(events[index].simulated_output_sha256, materialized_event.simulated_output_sha256) != 0) {
      platform_file_add_error(&diagnostics, "self-decrunch materialization hash mismatch");
      goto cleanup;
    }
    break;
  }
  if (!found) {
    platform_file_add_error(&diagnostics, "self-decrunch event not found");
    goto cleanup;
  }
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"status\":\"ok\",\"decompression_events\":[") != 0 ||
      append_self_decrunch_event_json(&builder, &materialized_event) != 0 ||
      json_builder_appendf(&builder,
        "],\"decompressed\":{\"size\":%u,\"sha256\":",
        (unsigned)(materialized_event.simulated_output_end - materialized_event.simulated_output_start)) != 0 ||
      json_builder_append_json_string(&builder, materialized_event.simulated_output_sha256) != 0 ||
      json_builder_appendf(&builder,
        ",\"load_address\":%u,\"entrypoint\":%u},\"provider_id\":\"m68k-sim-decrunch\"}",
        (unsigned)materialized_event.simulated_output_start, (unsigned)materialized_event.entrypoint) != 0) {
    platform_file_add_error(&diagnostics, "failed building self-decrunch materialization json");
    goto cleanup;
  }
  *out_text = json_builder_build(&builder);
  if (*out_text == NULL) {
    platform_file_add_error(&diagnostics, "out of memory");
    goto cleanup;
  }
  result = 0;

cleanup:
  if (result != 0 && out_text != NULL && *out_text == NULL) {
    const char *message = m68k_diag_first_message(&diagnostics);
    JsonBuilder error_builder = {0};
    if (message == NULL || message[0] == '\0') message = "self-decrunch materialization failed";
    if (json_builder_create(&error_builder) == 0 &&
        json_builder_append(&error_builder, "{\"status\":\"error\",\"error\":") == 0 &&
        json_builder_append_json_string(&error_builder, message) == 0 &&
        json_builder_append(&error_builder, "}") == 0) {
      *out_text = json_builder_build(&error_builder);
    }
    json_builder_destroy(&error_builder);
  }
  json_builder_destroy(&builder);
  if (analysis != NULL) m68k_ir_source_analysis_destroy(analysis);
  m68k_object_destroy(&object);
  arena_destroy(scratch_arena);
  return result;
}

PLATFORM_FILE_API int platform_file_decompression_materialize_recognized_unpacker_event_json_alloc(
    const char *backend_name, const char *path, const char *event_id, const char *output_path, char **out_text) {
  Arena *scratch_arena = NULL;
  M68kAnalysisPolicy *analysis_policy = NULL;
  M68kFactsV2Profile *profile = NULL;
  M68kSourceAnalysisIR *analysis = NULL;
  M68kObject object;
  M68kDiagList diagnostics;
  JsonBuilder builder = {0};
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  PlatformRecognizedUnpackerEvent events[16];
  PlatformRecognizedUnpackerEvent materialized_event;
  size_t event_count = 0U;
  size_t index;
  int found = 0;
  int result = -1;
  if (out_text == NULL) return -1;
  *out_text = NULL;
  memset(&object, 0, sizeof(object));
  memset(events, 0, sizeof(events));
  memset(&materialized_event, 0, sizeof(materialized_event));
  m68k_diag_list_reset(&diagnostics);
  if (backend == NULL || path == NULL || event_id == NULL || event_id[0] == '\0' ||
      output_path == NULL || output_path[0] == '\0') {
    platform_file_add_error(&diagnostics, "invalid recognized unpacker materialization request");
    goto cleanup;
  }
  scratch_arena = arena_create(4096U);
  if (scratch_arena == NULL) {
    platform_file_add_error(&diagnostics, "out of memory");
    goto cleanup;
  }
  analysis_policy = (M68kAnalysisPolicy *)arena_calloc(scratch_arena, 1U, sizeof(*analysis_policy));
  profile = (M68kFactsV2Profile *)arena_calloc(scratch_arena, 1U, sizeof(*profile));
  analysis = (M68kSourceAnalysisIR *)arena_calloc(scratch_arena, 1U, sizeof(*analysis));
  if (analysis_policy == NULL || profile == NULL || analysis == NULL) {
    platform_file_add_error(&diagnostics, "out of memory");
    goto cleanup;
  }
  m68k_analysis_policy_init_default(analysis_policy);
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&diagnostics)) != 0) goto cleanup;
  if (enrich_policy_from_object_target_info_local(analysis_policy, backend, &object, NULL, 0U, &diagnostics) != 0)
    goto cleanup;
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&diagnostics, &object, analysis_policy)) goto cleanup;
  if (m68k_facts_v2_collect_source_analysis_profile(&object, analysis_policy, profile, analysis,
      m68k_diag_sink(&diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&diagnostics))
      platform_file_add_error(&diagnostics, "failed building facts_v2 source analysis");
    goto cleanup;
  }
  if (collect_recognized_unpacker_events_local(&object, analysis, events, sizeof(events) / sizeof(events[0]),
      &event_count, event_id, output_path, &materialized_event, &diagnostics, scratch_arena) != 0) {
    platform_file_add_error(&diagnostics, "failed collecting recognized unpacker events");
    goto cleanup;
  }
  for (index = 0U; index < event_count; ++index) {
    char candidate_id[160];
    make_recognized_unpacker_event_id_local(candidate_id, sizeof(candidate_id), &events[index]);
    if (strcmp(candidate_id, event_id) != 0) continue;
    found = 1;
    if (!events[index].native_unpack_validated) {
      platform_file_add_error(&diagnostics, "recognized unpacker event has no materializable native output");
      goto cleanup;
    }
    if (!materialized_event.native_unpack_validated) {
      if (!m68k_diag_has_errors(&diagnostics))
        platform_file_add_error(&diagnostics, "failed materializing recognized unpacker output");
      goto cleanup;
    }
    if (events[index].decompressed_sha256[0] != '\0' &&
        strcmp(events[index].decompressed_sha256, materialized_event.decompressed_sha256) != 0) {
      platform_file_add_error(&diagnostics, "recognized unpacker materialization hash mismatch");
      goto cleanup;
    }
    break;
  }
  if (!found) {
    platform_file_add_error(&diagnostics, "recognized unpacker event not found");
    goto cleanup;
  }
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"status\":\"ok\",\"decompression_events\":[") != 0 ||
      append_recognized_unpacker_event_json(&builder, &materialized_event) != 0 ||
      json_builder_appendf(&builder,
        "],\"decompressed\":{\"size\":%u,\"sha256\":",
        (unsigned)materialized_event.decompressed_size) != 0 ||
      json_builder_append_json_string(&builder, materialized_event.decompressed_sha256) != 0 ||
      json_builder_appendf(&builder,
        ",\"load_address\":%u,\"entrypoint\":%u},\"provider_id\":\"c-tetragon-native\"}",
        (unsigned)materialized_event.target_start_address, (unsigned)materialized_event.entrypoint) != 0) {
    platform_file_add_error(&diagnostics, "failed building recognized unpacker materialization json");
    goto cleanup;
  }
  *out_text = json_builder_build(&builder);
  if (*out_text == NULL) {
    platform_file_add_error(&diagnostics, "out of memory");
    goto cleanup;
  }
  result = 0;

cleanup:
  if (result != 0 && out_text != NULL && *out_text == NULL) {
    const char *message = m68k_diag_first_message(&diagnostics);
    JsonBuilder error_builder = {0};
    if (message == NULL || message[0] == '\0') message = "recognized unpacker materialization failed";
    if (json_builder_create(&error_builder) == 0 &&
        json_builder_append(&error_builder, "{\"status\":\"error\",\"error\":") == 0 &&
        json_builder_append_json_string(&error_builder, message) == 0 &&
        json_builder_append(&error_builder, "}") == 0) {
      *out_text = json_builder_build(&error_builder);
    }
    json_builder_destroy(&error_builder);
  }
  json_builder_destroy(&builder);
  if (analysis != NULL) m68k_ir_source_analysis_destroy(analysis);
  m68k_object_destroy(&object);
  arena_destroy(scratch_arena);
  return result;
}
