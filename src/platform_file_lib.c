#include "platform_file_lib.h"
#include "platform_file_internal.h"
#include "json_builder.h"
#include "m68k_analysis_facts_v2.h"
#include "m68k_assembler_app.h"
#include "m68k_assembler.h"
#include "m68k_backend.h"
#include "m68k_instruction_spec.h"
#include "m68k_ir_codec.h"
#include "m68k_object.h"
#include "m68k_parse_util.h"
#include "m68k_simulator.h"
#include "m68k_source_pipeline.h"
#include "m68k_source_ir_render.h"
#include "platform_atari_st.h"
#include "platform_common.h"
#include "util_arena.h"
#include "generated/amiga_hunk_file_runtime.h"

#include <inttypes.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static void platform_file_add_error(M68kDiagList *diagnostics, const char *message);
static void platform_file_add_warning(M68kDiagList *diagnostics, const char *message);
static int read_file_to_buffer(const char *path, unsigned char **out_data, size_t *out_size,
    M68kDiagSink diagnostics);
static int load_object_from_path(const M68kBackend *backend, const char *path, M68kObject *object,
    M68kDiagSink diagnostics);
static int load_raw_object_from_path(const char *platform_name, const char *path, M68kObject *object,
    M68kDiagSink diagnostics);

static char *duplicate_text_local(const char *text) {
  size_t length;
  char *copy;
  if (text == NULL) text = "";
  length = strlen(text);
  copy = (char *)malloc(length + 1U);
  if (copy == NULL) return NULL;
  memcpy(copy, text, length + 1U);
  return copy;
}

static int text_result_to_alloc(PlatformFileTextResult *result, char **out_text) {
  const char *message;
  if (out_text == NULL) return -1;
  *out_text = NULL;
  if (result == NULL) {
    *out_text = duplicate_text_local("platform file operation failed");
    return -1;
  }
  if (m68k_diag_has_errors(&result->diagnostics) || result->text == NULL) {
    message = m68k_diag_first_message(&result->diagnostics);
    if (message == NULL || message[0] == '\0') message = "platform file operation failed";
    *out_text = duplicate_text_local(message);
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

static int policy_add_named_label_local(M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset,
  const char *name);
static int policy_add_entry_comment_local(M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset,
  const char *comment);
static int policy_add_runtime_range_local(M68kAnalysisPolicy *policy, uint32_t section_index,
  uint32_t source_start, uint32_t source_end, uint32_t base_addr, const char *name);
static int policy_add_runtime_entry_point_local(M68kAnalysisPolicy *policy, uint32_t section_index,
  uint32_t runtime_address);
static int policy_add_app_slot_region_local(M68kAnalysisPolicy *policy, uint32_t offset, uint8_t size,
  const char *symbol, const char *struct_name, const char *pointer_struct, const char *storage_kind,
  const char *semantic_type);
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
  if (strcmp(parts[2], "library_base") == 0) {
    seed->kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  } else if (strcmp(parts[2], "struct_ptr") == 0) {
    seed->kind = M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR;
  } else {
    return 0;
  }
  if (!copy_policy_text(seed->name, sizeof(seed->name), parts[3])) return 0;
  if (part_count > 4U && !copy_policy_text(seed->type_name, sizeof(seed->type_name), parts[4])) return 0;
  if (part_count > 5U && !copy_policy_text(seed->context_name, sizeof(seed->context_name), parts[5])) return 0;
  policy->register_seed_count += 1U;
  return 1;
}

int platform_file_analysis_policy_add_entry_point_arg(M68kAnalysisPolicy *policy, const char *text) {
  char buffer[64];
  char *separator;
  M68kAnalysisEntryPoint *entry;
  if (text == NULL || policy == NULL || policy->entry_point_count >= M68K_ANALYSIS_ENTRY_POINT_LIMIT) return 0;
  if (!copy_policy_text(buffer, sizeof(buffer), text)) return 0;
  entry = &policy->entry_points[policy->entry_point_count];
  memset(entry, 0, sizeof(*entry));
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
    if (size + 4096U + 1U > capacity) {
      size_t next_capacity = capacity == 0U ? 4097U : capacity * 2U;
      char *next_text;
      while (next_capacity < size + 4096U + 1U) next_capacity *= 2U;
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
  char entry_text[32];
  char register_name[8];
  char kind[32];
  char name[64];
  char struct_name[64];
  char context_name[64];
  char seed_arg[256];
  uint32_t entry_offset = 0U;
  uint32_t hunk = 0U;
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
  if (strcmp(kind, "library_base") == 0) {
    if (!json_optional_string_field_local(object_start, object_end, "library_name", name, sizeof(name))) return 0;
  } else {
    if (!json_optional_string_field_local(object_start, object_end, "note", name, sizeof(name))) return 0;
  }
  if (register_name[0] == '\0' || kind[0] == '\0' || name[0] == '\0') return 1;
  if (has_entry_offset) snprintf(entry_text, sizeof(entry_text), "%u", (unsigned)entry_offset);
  else copy_policy_text(entry_text, sizeof(entry_text), "*");
  snprintf(seed_arg, sizeof(seed_arg), "%s:%s:%s:%s:%s:%s", entry_text, register_name, kind, name, struct_name,
    context_name);
  {
    uint16_t seed_index = policy->register_seed_count;
    if (!platform_file_analysis_policy_add_register_seed_arg(policy, seed_arg)) return 0;
    policy->register_seeds[seed_index].has_section_index = 1U;
    policy->register_seeds[seed_index].section_index = has_hunk ? hunk : 0U;
  }
  return 1;
}

static int append_metadata_entry_point_local(const char *object_start, const char *object_end,
    M68kAnalysisPolicy *policy) {
  uint32_t offset = 0U;
  uint32_t hunk = 0U;
  int has_offset = 0;
  int has_hunk = 0;
  char entry_arg[64];
  if (!json_number_field_local(object_start, object_end, "addr", &offset, &has_offset) ||
      !json_number_field_local(object_start, object_end, "hunk", &hunk, &has_hunk)) return 0;
  if (!has_offset) return 1;
  if (has_hunk) snprintf(entry_arg, sizeof(entry_arg), "%u:%u", (unsigned)hunk, (unsigned)offset);
  else snprintf(entry_arg, sizeof(entry_arg), "%u", (unsigned)offset);
  return platform_file_analysis_policy_add_entry_point_arg(policy, entry_arg);
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
  if (!policy_runtime_address_to_source_offset_local(policy, runtime_address, &section_index, &offset)) return 0;
  if (!policy_add_named_label_local(policy, section_index, offset, name)) return 0;
  if (comment[0] != '\0' && !policy_add_entry_comment_local(policy, section_index, offset, comment)) return 0;
  return 1;
}

static uint8_t app_slot_region_size_from_storage_kind_local(const char *storage_kind) {
  if (storage_kind == NULL || storage_kind[0] == '\0') return 4U;
  if (strcmp(storage_kind, "struct_instance") == 0 ||
      strcmp(storage_kind, "struct_pointer") == 0 ||
      strcmp(storage_kind, "pointer") == 0 ||
      strcmp(storage_kind, "scalar") == 0) {
    return 4U;
  }
  return 4U;
}

static int append_metadata_app_slot_region_local(const char *object_start, const char *object_end,
    M68kAnalysisPolicy *policy) {
  uint32_t offset = 0U;
  int has_offset = 0;
  char symbol[64];
  char struct_name[64];
  char pointer_struct[64];
  char storage_kind[32];
  char semantic_type[64];
  symbol[0] = '\0';
  struct_name[0] = '\0';
  pointer_struct[0] = '\0';
  storage_kind[0] = '\0';
  semantic_type[0] = '\0';
  if (!json_number_field_local(object_start, object_end, "offset", &offset, &has_offset) ||
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
  return policy_add_app_slot_region_local(policy, offset,
    app_slot_region_size_from_storage_kind_local(storage_kind), symbol, struct_name, pointer_struct, storage_kind,
    semantic_type);
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

static int policy_add_app_slot_region_local(M68kAnalysisPolicy *policy, uint32_t offset, uint8_t size,
    const char *symbol, const char *struct_name, const char *pointer_struct, const char *storage_kind,
    const char *semantic_type) {
  M68kAnalysisAppSlotRegion *slot;
  uint16_t index;
  if (policy == NULL || offset > 0x7FFFU || size == 0U ||
      policy->app_slot_region_count >= M68K_ANALYSIS_APP_SLOT_REGION_LIMIT) {
    return 0;
  }
  for (index = 0U; index < policy->app_slot_region_count; ++index) {
    const M68kAnalysisAppSlotRegion *existing = &policy->app_slot_regions[index];
    if (existing->offset == offset) return 1;
  }
  slot = &policy->app_slot_regions[policy->app_slot_region_count];
  memset(slot, 0, sizeof(*slot));
  slot->offset = offset;
  slot->size = size;
  if (!copy_policy_text(slot->symbol, sizeof(slot->symbol), symbol) ||
      !copy_policy_text(slot->struct_name, sizeof(slot->struct_name), struct_name) ||
      !copy_policy_text(slot->pointer_struct, sizeof(slot->pointer_struct), pointer_struct) ||
      !copy_policy_text(slot->storage_kind, sizeof(slot->storage_kind), storage_kind) ||
      !copy_policy_text(slot->semantic_type, sizeof(slot->semantic_type), semantic_type)) {
    memset(slot, 0, sizeof(*slot));
    return 0;
  }
  policy->app_slot_region_count += 1U;
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

static int policy_add_named_label_local(M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset,
    const char *name) {
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
    if (existing->has_section_index && existing->section_index == section_index && existing->offset == offset) return 1;
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
  label->section_index = section_index;
  label->offset = offset;
  return copy_policy_text(label->name, sizeof(label->name), unique_name);
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
    const char *register_name, const char *kind, const char *name, const char *type_name, const char *context_name) {
  char seed_arg[256];
  uint16_t seed_index;
  uint8_t reg_kind;
  uint8_t reg_index;
  uint8_t seed_kind;
  uint16_t index;
  if (policy == NULL || policy->register_seed_count >= M68K_ANALYSIS_REGISTER_SEED_LIMIT) return 0;
  if (register_name == NULL || register_name[0] == '\0') return 0;
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
  if (kind != NULL && strcmp(kind, "library_base") == 0) seed_kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  else if (kind != NULL && strcmp(kind, "struct_ptr") == 0) seed_kind = M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR;
  else return 0;
  for (index = 0U; index < policy->register_seed_count; ++index) {
    const M68kAnalysisRegisterSeed *existing = &policy->register_seeds[index];
    if (existing->has_section_index && existing->section_index == section_index &&
        existing->has_entry_offset && existing->entry_offset == offset &&
        existing->reg_kind == reg_kind && existing->reg_index == reg_index && existing->kind == seed_kind &&
        strcmp(existing->name, name != NULL ? name : "") == 0 &&
        strcmp(existing->type_name, type_name != NULL ? type_name : "") == 0 &&
        strcmp(existing->context_name, context_name != NULL ? context_name : "") == 0)
      return 1;
  }
  seed_index = policy->register_seed_count;
  snprintf(seed_arg, sizeof(seed_arg), "%u:%s:%s:%s:%s:%s", (unsigned)offset, register_name, kind, name,
    type_name != NULL ? type_name : "", context_name != NULL ? context_name : "");
  if (!platform_file_analysis_policy_add_register_seed_arg(policy, seed_arg)) return 0;
  policy->register_seeds[seed_index].has_section_index = 1U;
  policy->register_seeds[seed_index].section_index = section_index;
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
    if (!policy_add_register_seed_local(policy, section_index, offset, reg_name, "struct_ptr", arg_name, type_name, ""))
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
    const char *label, const char *struct_name, const char *field_name, const char *semantic_role,
    uint8_t is_pointer) {
  M68kAnalysisStructuredDataItem *item;
  if (policy == NULL || item_index >= policy->structured_data_item_count ||
      item_index >= M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT) return 0;
  item = &policy->structured_data_items[item_index];
  item->is_pointer = is_pointer;
  return copy_policy_text(item->label, sizeof(item->label), label) &&
    copy_policy_text(item->struct_name, sizeof(item->struct_name), struct_name) &&
    copy_policy_text(item->field_name, sizeof(item->field_name), field_name) &&
    copy_policy_text(item->semantic_role, sizeof(item->semantic_role), semantic_role);
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
  return 1;
}

static int policy_add_structured_data_item_local(M68kAnalysisPolicy *policy, uint32_t offset, uint32_t size,
    uint8_t kind, const char *comment) {
  return policy_add_structured_data_item_section_local(policy, 0U, 0U, offset, size, kind, comment);
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
  uint32_t bootcode_offset = 0U, bootcode_size = 0U, load_address = 0U, entrypoint = 0U;
  int has_bootcode_offset = 0, has_bootcode_size = 0, has_load_address = 0, has_entrypoint = 0;
  if (object_start == NULL) return 1;
  policy->disable_implicit_entry_points = 1U;
  if (!json_number_field_local(object_start, object_end, "bootcode_offset", &bootcode_offset, &has_bootcode_offset) ||
      !json_number_field_local(object_start, object_end, "bootcode_size", &bootcode_size, &has_bootcode_size) ||
      !json_number_field_local(object_start, object_end, "load_address", &load_address, &has_load_address) ||
      !json_number_field_local(object_start, object_end, "entrypoint", &entrypoint, &has_entrypoint))
    return 0;
  if (has_load_address && has_bootcode_offset) {
    uint32_t source_end = 0U;
    if (has_bootcode_size) {
      if (bootcode_offset > UINT32_MAX - bootcode_size) return 0;
      source_end = bootcode_offset + bootcode_size;
    }
    if (!policy_add_runtime_range_local(policy, 0U, 0U, source_end, load_address, "bootblock")) return 0;
  }
  if (has_entrypoint && !policy_add_runtime_entry_point_local(policy, 0U, entrypoint)) return 0;
  if (!has_bootcode_offset || bootcode_offset < 12U) return 1;
  return policy_add_entry_point_local(policy, 0U, bootcode_offset) &&
    policy_add_named_label_local(policy, 0U, bootcode_offset, "boot_entry") &&
    policy_add_structured_data_item_local(policy, 0U, 4U, M68K_ANALYSIS_STRUCTURED_DATA_STRING,
           "NOTE: boot magic") &&
    policy_add_structured_data_item_local(policy, 4U, 4U, M68K_ANALYSIS_STRUCTURED_DATA_LONGS,
      "NOTE: boot checksum") &&
    policy_add_structured_data_item_local(policy, 8U, 4U, M68K_ANALYSIS_STRUCTURED_DATA_LONGS,
      "NOTE: boot root block");
}

static uint8_t resident_field_kind_local(uint32_t size) {
  if (size == 4U) return M68K_ANALYSIS_STRUCTURED_DATA_LONGS;
  if (size == 2U) return M68K_ANALYSIS_STRUCTURED_DATA_WORDS;
  return M68K_ANALYSIS_STRUCTURED_DATA_BYTES;
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
  const char *field_type;
  const char *c_type;
  if (field == NULL) return 0U;
  if (field->pointer_struct_id != AMIGA_OS_STRUCT_ID_NONE) return 1U;
  field_type = amiga_os_name(M68K_PLATFORM_NAME_TYPE, field->field_type_id);
  c_type = amiga_os_name(M68K_PLATFORM_NAME_TYPE, field->c_type_id);
  if (field_type != NULL && (strcmp(field_type, "APTR") == 0 || strcmp(field_type, "BPTR") == 0 ||
        strcmp(field_type, "BSTR") == 0))
    return 1U;
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
        !policy_set_structured_data_item_metadata_local(policy, item_index, label, struct_name, field_symbol, label,
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
        label, label, is_pointer) ||
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
    char label_name[64];
    label_name[0] = '\0';
    if (!parse_next_resident_vector_metadata_entry_local(&cursor, array_end, entries_are_objects, hunk, &entry,
          &has_entry))
      return 0;
    if (!has_entry) break;
    if (inout_first_code_offset != NULL && entry.hunk == hunk &&
        (*inout_first_code_offset == UINT32_MAX || entry.offset < *inout_first_code_offset)) {
      *inout_first_code_offset = entry.offset;
    }
    if (!policy_add_entry_point_local(policy, entry.hunk, entry.offset)) return 0;
    if (library_name != NULL && library_name[0] != '\0') {
      const char *base_struct_name = amiga_os_find_library_base_struct_name(library_name);
      if (base_struct_name == NULL || base_struct_name[0] == '\0') base_struct_name = "LIB";
      if (!policy_add_register_seed_local(policy, entry.hunk, entry.offset, "A6", "library_base", library_name,
            base_struct_name, ""))
        return 0;
    }
    {
      size_t prefix_index;
      for (prefix_index = 0U; prefix_index < AMIGA_OS_RESIDENT_VECTOR_PREFIX_COUNT; ++prefix_index) {
        const AmigaOsResidentVectorPrefixInfo *prefix = amiga_os_resident_vector_prefix_at(prefix_index);
        const char *symbol;
        if (prefix == NULL || prefix->slot_index != vector_index || target_type == NULL ||
            strcmp(prefix->target_type, target_type) != 0)
          continue;
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
              !policy_add_entry_comment_local(policy, entry.hunk, entry.offset, declaration)) {
            return 0;
          }
          if (!policy_add_amiga_lvo_argument_seeds_local(policy, entry.hunk, entry.offset, vector)) return 0;
        } else {
          char private_stem[48];
          make_library_stem_label_local(private_stem, sizeof(private_stem), library_name);
          snprintf(label_name, sizeof(label_name), "%s_private_%u", private_stem[0] != '\0' ? private_stem : "resident",
            (unsigned)next_private_ordinal++);
        }
      }
      if (label_name[0] != '\0' && !policy_add_named_label_local(policy, entry.hunk, entry.offset, label_name))
        return 0;
    }
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
        !policy_add_register_seed_local(policy, hunk, init_func_offset, "D0", "library_base", "__amiga_app_base__", "",
          "") ||
        !policy_add_register_seed_local(policy, hunk, init_func_offset, "D0", "struct_ptr", "__amiga_app_base__",
          app_base_struct_name, "") ||
        !policy_add_register_seed_local(policy, hunk, init_func_offset, "A0", "struct_ptr", "seglist", "BPTR", "") ||
        !policy_add_register_seed_local(policy, hunk, init_func_offset, "A6", "library_base", "exec.library",
          exec_base_struct_name, ""))
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
  uint32_t hunk = 0U;
  uint32_t library_version = 0U;
  int has_resident_offset = 0;
  int has_hunk = 0;
  int has_library_version = 0;
  target_type[0] = '\0';
  library_name[0] = '\0';
  if (resident_start == NULL) return 1;
  policy->disable_implicit_entry_points = 1U;
  if (!json_number_field_local(resident_start, resident_end, "offset", &resident_offset, &has_resident_offset) ||
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

static int append_metadata_generic_policy_text_local(const char *text, M68kAnalysisPolicy *policy,
    M68kDiagSink diagnostics) {
  const char *array_end;
  const char *cursor;
  if (text == NULL || policy == NULL) return -1;
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
  cursor = json_find_array_local(text, "app_slot_regions", &array_end);
  while (cursor != NULL && cursor < array_end) {
    const char *object_end;
    const char *object_start = json_next_object_local(cursor, array_end, &object_end);
    if (object_start == NULL) break;
    if (!append_metadata_app_slot_region_local(object_start, object_end, policy)) {
      platform_file_add_error(diagnostics.list, "failed parsing target metadata app slot region");
      return -1;
    }
    cursor = object_end;
  }
  return 0;
}

static int platform_name_uses_amiga_metadata_policy_local(const char *platform_name) {
  return platform_name != NULL &&
         (strcmp(platform_name, "amiga-hunk") == 0 || strcmp(platform_name, "amiga-raw") == 0);
}

static int metadata_text_has_amiga_policy_local(const char *text) {
  const char *array_end;
  const char *array_start;
  const char *resident_end;
  const char *text_end;
  char target_type[32];
  if (text == NULL) return 0;
  if (json_find_object_field_local(text, "resident", &resident_end) != NULL) return 1;
  array_start = json_find_array_local(text, "app_slot_regions", &array_end);
  if (array_start != NULL && json_next_object_local(array_start, array_end, NULL) != NULL) return 1;
  text_end = text + strlen(text);
  target_type[0] = '\0';
  if (json_optional_string_field_local(text, text_end, "target_type", target_type, sizeof(target_type)) &&
      strcmp(target_type, "bootblock") == 0)
    return 1;
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
  offsets_copy = duplicate_text_local(entry_offsets);
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
    if (!validate_policy_offset_local(diagnostics, object, label->has_section_index, label->section_index,
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
  return 1;
}

static int policy_set_raw_entry_address_local(M68kAnalysisPolicy *policy, const M68kObject *object,
    uint32_t entry_address, M68kDiagList *diagnostics) {
  uint32_t section_size = 0U;
  uint32_t section_index = 0U;
  uint32_t offset = 0U;
  if (policy == NULL || object == NULL) return 0;
  policy_section_size_local(object, 1U, 0U, &section_size);
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

static uint32_t read_be32_local(const uint8_t *data) {
  return ((uint32_t)data[0] << 24) | ((uint32_t)data[1] << 16) | ((uint32_t)data[2] << 8) | (uint32_t)data[3];
}

static const char *resident_pointer_target_label_local(const M68kAnalysisStructuredDataItem *item) {
  if (item == NULL || strcmp(item->struct_name, "RT") != 0) return NULL;
  if (strcmp(item->field_name, "RT_NAME") == 0) return "resident_name";
  if (strcmp(item->field_name, "RT_IDSTRING") == 0) return "resident_idstring";
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
    if (strcmp(item->struct_name, "RT") == 0) return 1;
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
  if (inspected_target_type[0] != '\0' && strcmp(inspected_target_type, "program") != 0)
    policy->disable_implicit_entry_points = 1U;
  if (platform_name_uses_amiga_metadata_policy_local(backend_name)) {
    M68kDiagList ignored_diagnostics;
    const char *resident_end = NULL;
    const char *resident_start = json_find_object_field_local(inspect_json, "resident", &resident_end);
    if (resident_start != NULL && policy_has_resident_struct_policy_local(policy)) {
      const char *autoinit_end = NULL;
      const char *autoinit_start = json_find_nested_object_field_local(resident_start, resident_end, "autoinit",
        &autoinit_end);
      char library_name[64];
      uint32_t hunk = 0U;
      uint32_t library_version = 0U;
      int has_hunk = 0;
      int has_library_version = 0;
      library_name[0] = '\0';
      if (autoinit_start != NULL &&
          json_number_field_local(resident_start, resident_end, "hunk", &hunk, &has_hunk) &&
          json_optional_string_field_local(resident_start, resident_end, "name", library_name, sizeof(library_name)) &&
          json_number_field_local(resident_start, resident_end, "version", &library_version, &has_library_version)) {
        (void)repair_metadata_resident_vector_sections_local(autoinit_start, autoinit_end, policy,
          has_hunk ? hunk : 0U, inspected_target_type, library_name, has_library_version ? library_version : 0U);
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
        "\"runtime_range_count\":%u,\"runtime_entry_point_count\":%u,\"app_slot_region_count\":%u",
        (unsigned)policy->max_cpu, policy->disable_implicit_entry_points ? "false" : "true",
        (unsigned)policy->entry_point_count, (unsigned)policy->register_seed_count,
        (unsigned)policy->structured_data_item_count, (unsigned)policy->named_label_count,
        (unsigned)policy->entry_comment_count, (unsigned)policy->runtime_range_count,
        (unsigned)policy->runtime_entry_point_count, (unsigned)policy->app_slot_region_count) != 0)
    return -1;
  if (json_builder_append(builder, ",\"entrypoints\":[") != 0) return -1;
  for (index = 0U; index < policy->entry_point_count && index < M68K_ANALYSIS_ENTRY_POINT_LIMIT; ++index) {
    const M68kAnalysisEntryPoint *entry = &policy->entry_points[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"section_index\":") != 0) return -1;
    if (append_nullable_u32_json_local(builder, entry->has_section_index, entry->section_index) != 0) return -1;
    if (json_builder_appendf(builder, ",\"offset\":%u}", (unsigned)entry->offset) != 0) return -1;
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
    if (append_nullable_text_json_local(builder, item->comment) != 0) return -1;
    if (json_builder_append(builder, ",\"label\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, item->label) != 0) return -1;
    if (json_builder_append(builder, ",\"struct_name\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, item->struct_name) != 0) return -1;
    if (json_builder_append(builder, ",\"field_name\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, item->field_name) != 0) return -1;
    if (json_builder_append(builder, ",\"field_type\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, item->field_type) != 0) return -1;
    if (json_builder_append(builder, ",\"c_type\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, item->c_type) != 0) return -1;
    if (json_builder_append(builder, ",\"pointer_struct\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, item->pointer_struct) != 0) return -1;
    if (json_builder_append(builder, ",\"value_domain\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, item->value_domain) != 0) return -1;
    if (json_builder_append(builder, ",\"constant_name\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, item->constant_name) != 0) return -1;
    if (json_builder_appendf(builder, ",\"has_constant_value\":%s,\"constant_value\":",
          item->has_constant_value ? "true" : "false") != 0)
      return -1;
    if (item->has_constant_value) {
      if (json_builder_appendf(builder, "%d", (int)item->constant_value) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) return -1;
    if (json_builder_append(builder, ",\"semantic_role\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, item->semantic_role) != 0) return -1;
    if (json_builder_appendf(builder, ",\"is_pointer\":%s,\"target_section\":",
          item->is_pointer ? "true" : "false") != 0)
      return -1;
    if (append_nullable_u32_json_local(builder, item->has_target, item->target_section) != 0) return -1;
    if (json_builder_append(builder, ",\"target_offset\":") != 0) return -1;
    if (append_nullable_u32_json_local(builder, item->has_target, item->target_offset) != 0) return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  if (json_builder_append(builder, "],\"app_slot_regions\":[") != 0) return -1;
  for (index = 0U; index < policy->app_slot_region_count && index < M68K_ANALYSIS_APP_SLOT_REGION_LIMIT; ++index) {
    const M68kAnalysisAppSlotRegion *slot = &policy->app_slot_regions[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_appendf(builder, "{\"offset\":%u,\"size\":%u,\"symbol\":",
          (unsigned)slot->offset, (unsigned)slot->size) != 0)
      return -1;
    if (append_nullable_text_json_local(builder, slot->symbol) != 0) return -1;
    if (json_builder_append(builder, ",\"struct_name\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, slot->struct_name) != 0) return -1;
    if (json_builder_append(builder, ",\"pointer_struct\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, slot->pointer_struct) != 0) return -1;
    if (json_builder_append(builder, ",\"storage_kind\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, slot->storage_kind) != 0) return -1;
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
    if (json_builder_appendf(builder, ",\"offset\":%u,\"name\":", (unsigned)label->offset) != 0) return -1;
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
  return json_builder_append(builder, "]}");
}

static int effective_policy_json_to_alloc(const char *platform_name, const char *path, const char *metadata_path,
    const char *entry_offsets, uint8_t is_raw, uint32_t raw_entry_offset, char **out_text) {
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
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    PlatformFileTextResult error_result;
    memset(&error_result, 0, sizeof(error_result));
    platform_file_add_error(&error_result.diagnostics, "out of memory");
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
      free(analysis_policy);
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
        free(analysis_policy);
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
        free(analysis_policy);
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
        free(analysis_policy);
        return rc;
      }
    }
  }
  object_loaded = 1;
  if (is_raw) {
    if (!policy_set_raw_entry_address_local(analysis_policy, &object, raw_entry_offset, &diagnostics)) {
      PlatformFileTextResult error_result;
      memset(&error_result, 0, sizeof(error_result));
      error_result.diagnostics = diagnostics;
      m68k_object_destroy(&object);
      {
        int rc = text_result_to_alloc(&error_result, out_text);
        free(analysis_policy);
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
      free(analysis_policy);
      return rc;
    }
  }
  analysis_start = effective_policy_analysis_start_local(analysis_policy, is_raw ? raw_entry_offset : 0U);
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
  free(analysis_policy);
  return 0;

oom:
  json_builder_destroy(&builder);
  if (object_loaded) m68k_object_destroy(&object);
  free(analysis_policy);
  *out_text = duplicate_text_local("out of memory");
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

static const M68kBackend *raw_platform_backend(const char *platform_name) {
  if (platform_name == NULL) return NULL;
  if (strcmp(platform_name, "amiga-raw") == 0) return &M68K_BACKEND_AMIGA_HUNK;
  if (strcmp(platform_name, "atari-st-raw") == 0) return &M68K_BACKEND_ATARI_ST;
  return NULL;
}

static int load_raw_object_from_path(const char *platform_name, const char *path, M68kObject *object,
    M68kDiagSink diagnostics) {
  unsigned char *data = NULL;
  size_t size = 0U;
  M68kSection section;
  M68kObjectAddResult add_result;
  const M68kBackend *backend = raw_platform_backend(platform_name);
  if (backend == NULL || object == NULL) {
    platform_file_add_error(diagnostics.list, "unknown raw platform backend");
    return -1;
  }
  if (read_file_to_buffer(path, &data, &size, diagnostics) != 0) return -1;
  if (m68k_object_create(object) != 0) {
    free(data);
    platform_file_add_error(diagnostics.list, "out of memory");
    return -1;
  }
  object->platform_backend_kind = (backend == &M68K_BACKEND_ATARI_ST) ? M68K_PLATFORM_BACKEND_ATARI_ST
    : M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object->platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  memset(&section, 0, sizeof(section));
  section.name = "code";
  section.kind = M68K_SECTION_CODE;
  section.alignment = 2U;
  section.size = (uint32_t)size;
  section.data = data;
  section.data_size = (uint32_t)size;
  add_result = m68k_object_add_section(object, &section);
  free(data);
  if (!add_result.ok) {
    m68k_object_destroy(object);
    platform_file_add_error(diagnostics.list, "out of memory");
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

static void platform_file_add_warning(M68kDiagList *diagnostics, const char *message) {
  if (message == NULL || message[0] == '\0') message = "platform file warning";
  m68k_diag_add(m68k_diag_sink(diagnostics), M68K_DIAG_SEVERITY_WARNING, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, message);
}

static const char *facts_v2_asm_source_failure_kind_name(uint32_t kind) {
  switch (kind) {
    case 1U: return "render";
    case 2U: return "byte_mismatch";
    case 3U: return "instruction_relocation";
    case 4U: return "unresolved_label";
    case 5U: return "interior_conflict";
    case 6U: return "relocation";
    case 7U: return "relocation_anchor";
    case 8U: return "unassemblable_hunk_data_relocation";
    case 9U: return "unassemblable_hunk_base_register_relocation";
    case 10U: return "required_instruction";
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
    "\"render_ir_platform_pass_seconds\":%.6f,"
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
    "\"runtime_address_ranges\":%u,"
    "\"runtime_address_range_conflicts\":%u,"
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
    profile->render_ir_platform_pass_seconds,
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
    (unsigned)profile->runtime_address_ranges,
    (unsigned)profile->runtime_address_range_conflicts,
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
    facts_v2_asm_source_failure_kind_name(profile->asm_source_first_failure_kind),
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
  if (profile == NULL) return duplicate_text_local("{}");
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

typedef struct FactsV2DirectCompareResult {
  int compared;
  int full_file_exact;
  int payload_exact;
  int relocation_semantics_exact;
  int semantic_exact;
  int container_oddity;
  const char *status;
} FactsV2DirectCompareResult;

static int objects_have_same_payload_semantics(const M68kObject *left, const M68kObject *right) {
  size_t index;
  if (left == NULL || right == NULL || left->section_count != right->section_count) return 0;
  for (index = 0U; index < left->section_count; ++index) {
    const M68kSection *a = &left->sections[index];
    const M68kSection *b = &right->sections[index];
    if (a->kind != b->kind || a->size != b->size || a->data_size != b->data_size ||
        a->platform_mem_type != b->platform_mem_type || a->platform_mem_attrs != b->platform_mem_attrs)
      return 0;
    if (a->data_size != 0U && (a->data == NULL || b->data == NULL ||
        memcmp(a->data, b->data, a->data_size) != 0))
      return 0;
  }
  return 1;
}

static const M68kSymbol *fixup_symbol_local(const M68kObject *object, const M68kFixup *fixup) {
  if (object == NULL || fixup == NULL || !fixup->has_symbol || fixup->symbol_index >= object->symbol_count)
    return NULL;
  return &object->symbols[fixup->symbol_index];
}

static int fixups_have_same_semantics(const M68kObject *left_object, const M68kFixup *left,
    const M68kObject *right_object, const M68kFixup *right) {
  const M68kSymbol *left_symbol;
  const M68kSymbol *right_symbol;
  const char *left_name;
  const char *right_name;
  if (left == NULL || right == NULL) return 0;
  if (left->section_index != right->section_index || left->offset != right->offset ||
      left->kind != right->kind || left->width != right->width || left->addend != right->addend ||
      left->has_target_section != right->has_target_section || left->has_symbol != right->has_symbol)
    return 0;
  if (left->has_target_section && left->target_section_index != right->target_section_index) return 0;
  if (!left->has_symbol) return 1;
  left_symbol = fixup_symbol_local(left_object, left);
  right_symbol = fixup_symbol_local(right_object, right);
  if (left_symbol == NULL || right_symbol == NULL) return 0;
  left_name = left_symbol->name != NULL ? left_symbol->name : "";
  right_name = right_symbol->name != NULL ? right_symbol->name : "";
  return left_symbol->binding == right_symbol->binding && left_symbol->defined == right_symbol->defined &&
    strcmp(left_name, right_name) == 0;
}

static int objects_have_same_relocation_semantics(const M68kObject *left, const M68kObject *right) {
  uint8_t *used;
  size_t left_index;
  if (left == NULL || right == NULL || left->fixup_count != right->fixup_count) return 0;
  if (left->fixup_count == 0U) return 1;
  used = (uint8_t *)calloc(right->fixup_count, sizeof(*used));
  if (used == NULL) return 0;
  for (left_index = 0U; left_index < left->fixup_count; ++left_index) {
    size_t right_index;
    int matched = 0;
    for (right_index = 0U; right_index < right->fixup_count; ++right_index) {
      if (used[right_index]) continue;
      if (!fixups_have_same_semantics(left, &left->fixups[left_index], right, &right->fixups[right_index]))
        continue;
      used[right_index] = 1U;
      matched = 1;
      break;
    }
    if (!matched) {
      free(used);
      return 0;
    }
  }
  free(used);
  return 1;
}

static FactsV2DirectCompareResult facts_v2_direct_compare_result(const char *backend_name,
    const M68kBackend *backend, const M68kObject *original_object, const unsigned char *rebuilt_data,
    size_t rebuilt_size, const unsigned char *compare_data, size_t compare_size) {
  FactsV2DirectCompareResult result;
  memset(&result, 0, sizeof(result));
  result.status = "not_compared";
  if (compare_data == NULL) return result;
  result.compared = 1;
  result.full_file_exact = (rebuilt_size == compare_size &&
    (rebuilt_size == 0U || memcmp(rebuilt_data, compare_data, rebuilt_size) == 0)) ? 1 : 0;
  if (result.full_file_exact) {
    result.payload_exact = 1;
    result.relocation_semantics_exact = 1;
    result.semantic_exact = 1;
    result.status = "full_file_exact";
    return result;
  }
  result.status = "binary_mismatch";
  if (backend_name == NULL || strcmp(backend_name, "amiga-hunk") != 0 || backend == NULL ||
      backend->read_buffer == NULL || original_object == NULL || rebuilt_data == NULL) {
    return result;
  }
  {
    M68kObject rebuilt_object;
    M68kDiagList diagnostics;
    m68k_diag_list_reset(&diagnostics);
    memset(&rebuilt_object, 0, sizeof(rebuilt_object));
    if (load_object_from_buffer(backend, rebuilt_data, rebuilt_size, &rebuilt_object, m68k_diag_sink(&diagnostics)) != 0)
      return result;
    result.payload_exact = objects_have_same_payload_semantics(original_object, &rebuilt_object);
    result.relocation_semantics_exact = objects_have_same_relocation_semantics(original_object, &rebuilt_object);
    result.semantic_exact = result.payload_exact && result.relocation_semantics_exact;
    if (result.semantic_exact) {
      result.container_oddity = 1;
      result.status = "semantic_container_oddity";
    }
    m68k_object_destroy(&rebuilt_object);
  }
  return result;
}

static char *facts_v2_direct_rebuild_profile_json_alloc(const char *backend_name, uint32_t source_bytes,
    uint32_t rebuilt_bytes, int refused, const char *refusal_reason, double write_buffer_seconds,
    double write_file_seconds, size_t original_bytes, FactsV2DirectCompareResult compare_result,
    double compare_seconds, double total_seconds, M68kDiagList *diagnostics) {
  JsonBuilder builder = {0};
  char *text;
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
        compare_result.compared ? "true" : "false",
        compare_result.full_file_exact ? "true" : "false") != 0 ||
      json_builder_append_json_string(&builder, compare_result.status != NULL ? compare_result.status : "") != 0 ||
      json_builder_appendf(&builder,
        ",\"direct_compare_payload_exact\":%s,"
        "\"direct_compare_relocation_semantics_exact\":%s,"
        "\"direct_compare_semantic_exact\":%s,"
        "\"direct_compare_container_oddity\":%s,"
        "\"direct_compare_seconds\":%.6f,\"total_seconds\":%.6f}",
        compare_result.payload_exact ? "true" : "false",
        compare_result.relocation_semantics_exact ? "true" : "false",
        compare_result.semantic_exact ? "true" : "false",
        compare_result.container_oddity ? "true" : "false",
        compare_seconds, total_seconds) != 0) {
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
    int enable_vasm_compat_rewrites, unsigned char **out_data, size_t *out_size, char **out_profile_json,
    char **out_error) {
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
    *out_error = duplicate_text_local("unknown cpu");
    *out_profile_json = assembler_profile_json_alloc_local(&profile);
    return -1;
  }
  if (source_text != NULL) {
    if (output_path != NULL && output_path[0] != '\0')
      result = m68k_assemble_platform_source_text_to_output_buffer_alloc(backend_name,
        include_dir != NULL ? include_dir : "", source_text, output_path, cpu_result.cpu,
        enable_vasm_compat_rewrites, out_data, out_size, &profile, m68k_diag_sink(&diagnostics));
    else
      result = m68k_assemble_platform_source_text_to_buffer_alloc(backend_name,
        include_dir != NULL ? include_dir : "", source_text, cpu_result.cpu, enable_vasm_compat_rewrites,
        out_data, out_size, &profile, m68k_diag_sink(&diagnostics));
  } else if (output_path != NULL && output_path[0] != '\0') {
    result = m68k_assemble_platform_file_to_output_buffer_alloc(backend_name, include_dir != NULL ? include_dir : "",
      path, output_path, cpu_result.cpu, enable_vasm_compat_rewrites, out_data, out_size, &profile,
      m68k_diag_sink(&diagnostics));
  } else {
    result = m68k_assemble_platform_file_to_buffer_alloc(backend_name, include_dir != NULL ? include_dir : "",
      path, cpu_result.cpu, enable_vasm_compat_rewrites, out_data, out_size, &profile, m68k_diag_sink(&diagnostics));
  }
  *out_profile_json = assembler_profile_json_alloc_local(&profile);
  if (*out_profile_json == NULL) {
    free(*out_data);
    *out_data = NULL;
    *out_size = 0U;
    *out_error = duplicate_text_local("out of memory");
    return -1;
  }
  if (result != 0) {
    message = m68k_diag_first_message(&diagnostics);
    if (message == NULL || message[0] == '\0') message = "platform assembler failed";
    free(*out_data);
    *out_data = NULL;
    *out_size = 0U;
    *out_error = duplicate_text_local(message);
    return -1;
  }
  return 0;
}

int platform_file_assemble_source_path_bytes_profile_alloc(const char *backend_name, const char *include_dir,
    const char *path, const char *target_cpu_name, int enable_vasm_compat_rewrites, unsigned char **out_data,
    size_t *out_size, char **out_profile_json, char **out_error) {
  return platform_file_assemble_source_common_alloc(backend_name, include_dir, path, NULL, NULL, target_cpu_name,
    enable_vasm_compat_rewrites, out_data, out_size, out_profile_json, out_error);
}

int platform_file_assemble_source_path_to_output_bytes_profile_alloc(const char *backend_name,
    const char *include_dir, const char *path, const char *output_path, const char *target_cpu_name,
    int enable_vasm_compat_rewrites, unsigned char **out_data, size_t *out_size, char **out_profile_json,
    char **out_error) {
  return platform_file_assemble_source_common_alloc(backend_name, include_dir, path, NULL, output_path,
    target_cpu_name, enable_vasm_compat_rewrites, out_data, out_size, out_profile_json, out_error);
}

int platform_file_assemble_source_text_bytes_profile_alloc(const char *backend_name, const char *include_dir,
    const char *source_text, const char *target_cpu_name, int enable_vasm_compat_rewrites,
    unsigned char **out_data, size_t *out_size, char **out_profile_json, char **out_error) {
  return platform_file_assemble_source_common_alloc(backend_name, include_dir, NULL, source_text, NULL,
    target_cpu_name, enable_vasm_compat_rewrites, out_data, out_size, out_profile_json, out_error);
}

int platform_file_assemble_source_text_to_output_bytes_profile_alloc(const char *backend_name,
    const char *include_dir, const char *source_text, const char *output_path, const char *target_cpu_name,
    int enable_vasm_compat_rewrites, unsigned char **out_data, size_t *out_size, char **out_profile_json,
    char **out_error) {
  return platform_file_assemble_source_common_alloc(backend_name, include_dir, NULL, source_text, output_path,
    target_cpu_name, enable_vasm_compat_rewrites, out_data, out_size, out_profile_json, out_error);
}

void platform_file_free_text(char *text) { free(text); }
void platform_file_free_bytes(unsigned char *data) { free(data); }

static PlatformFileTextResult facts_v2_analysis_object_json(const M68kObject *object,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  M68kAnalysisPolicy local_policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  int json_result;
  memset(&result, 0, sizeof(result));
  memset(&profile, 0, sizeof(profile));
  memset(&analysis, 0, sizeof(analysis));
  if (object == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid facts_v2 analysis request");
    return result;
  }
  if (analysis_policy != NULL) local_policy = *analysis_policy;
  else m68k_analysis_policy_init_default(&local_policy);
  if (m68k_facts_v2_collect_source_analysis_profile(object, &local_policy, &profile, &analysis,
      m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "failed building facts_v2 source analysis");
    return result;
  }
  json_result = source_analysis_to_json(&analysis, &result.text, m68k_diag_sink(&result.diagnostics));
  m68k_ir_source_analysis_destroy(&analysis);
  if (json_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building analysis json");
  return result;
}

PlatformFileTextResult platform_file_facts_v2_analysis_path_json(const char *backend_name, const char *path,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  M68kAnalysisPolicy active_analysis_policy;
  memset(&result, 0, sizeof(result));
  memset(&object, 0, sizeof(object));
  if (analysis_policy != NULL) active_analysis_policy = *analysis_policy;
  else m68k_analysis_policy_init_default(&active_analysis_policy);
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) return result;
  if (enrich_policy_from_object_target_info_local(&active_analysis_policy, backend, &object, NULL, 0U,
      &result.diagnostics) != 0) {
    m68k_object_destroy(&object);
    return result;
  }
  enrich_policy_pointer_targets_from_object_local(&active_analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, &active_analysis_policy)) {
    m68k_object_destroy(&object);
    return result;
  }
  result = facts_v2_analysis_object_json(&object, &active_analysis_policy);
  m68k_object_destroy(&object);
  return result;
}

PlatformFileTextResult platform_file_facts_v2_analysis_raw_path_json(const char *platform_name, const char *path,
    uint32_t entry_offset, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  M68kObject object;
  M68kAnalysisPolicy raw_analysis_policy;
  memset(&result, 0, sizeof(result));
  memset(&object, 0, sizeof(object));
  if (analysis_policy != NULL) raw_analysis_policy = *analysis_policy;
  else m68k_analysis_policy_init_default(&raw_analysis_policy);
  if (load_raw_object_from_path(platform_name, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) return result;
  if (!policy_set_raw_entry_address_local(&raw_analysis_policy, &object, entry_offset, &result.diagnostics)) {
    m68k_object_destroy(&object);
    return result;
  }
  enrich_policy_pointer_targets_from_object_local(&raw_analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, &raw_analysis_policy)) {
    m68k_object_destroy(&object);
    return result;
  }
  result = facts_v2_analysis_object_json(&object, &raw_analysis_policy);
  m68k_object_destroy(&object);
  return result;
}

PlatformFileTextResult platform_file_facts_v2_analysis_buffer_json(const char *backend_name,
    const unsigned char *data, size_t size, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  M68kAnalysisPolicy active_analysis_policy;
  memset(&result, 0, sizeof(result));
  memset(&object, 0, sizeof(object));
  if (analysis_policy != NULL) active_analysis_policy = *analysis_policy;
  else m68k_analysis_policy_init_default(&active_analysis_policy);
  if (load_object_from_buffer(backend, data, size, &object, m68k_diag_sink(&result.diagnostics)) != 0) return result;
  if (enrich_policy_from_object_target_info_local(&active_analysis_policy, backend, &object, NULL, 0U,
      &result.diagnostics) != 0) {
    m68k_object_destroy(&object);
    return result;
  }
  enrich_policy_pointer_targets_from_object_local(&active_analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, &active_analysis_policy)) {
    m68k_object_destroy(&object);
    return result;
  }
  result = facts_v2_analysis_object_json(&object, &active_analysis_policy);
  m68k_object_destroy(&object);
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
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  PlatformFileTextResult result;
  m68k_diag_list_reset(&diagnostics);
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    result.text = NULL;
    memset(&result.diagnostics, 0, sizeof(result.diagnostics));
    platform_file_add_error(&result.diagnostics, "out of memory");
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, entry_offsets,
        &diagnostics) != 0) {
    result.text = NULL;
    result.diagnostics = diagnostics;
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  result = platform_file_facts_v2_analysis_path_json(backend_name, path, analysis_policy);
  free(analysis_policy);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_analysis_raw_path_json_alloc(const char *platform_name, const char *path,
    uint32_t entry_offset, const char *metadata_path, const char *entry_offsets, char **out_text) {
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  PlatformFileTextResult result;
  m68k_diag_list_reset(&diagnostics);
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    result.text = NULL;
    memset(&result.diagnostics, 0, sizeof(result.diagnostics));
    platform_file_add_error(&result.diagnostics, "out of memory");
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, platform_name, metadata_path, entry_offsets,
        &diagnostics) != 0) {
    result.text = NULL;
    result.diagnostics = diagnostics;
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  result = platform_file_facts_v2_analysis_raw_path_json(platform_name, path, entry_offset, analysis_policy);
  free(analysis_policy);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_effective_policy_path_json_alloc(const char *backend_name, const char *path,
    const char *metadata_path, const char *entry_offsets, char **out_text) {
  return effective_policy_json_to_alloc(backend_name, path, metadata_path, entry_offsets, 0U, 0U, out_text);
}

int platform_file_effective_policy_raw_path_json_alloc(const char *platform_name, const char *path,
    uint32_t entry_offset, const char *metadata_path, const char *entry_offsets, char **out_text) {
  return effective_policy_json_to_alloc(platform_name, path, metadata_path, entry_offsets, 1U, entry_offset, out_text);
}

int platform_file_facts_v2_asm_source_path_text_alloc(const char *backend_name, const char *path,
    const char *metadata_path, char **out_text) {
  M68kAnalysisPolicy *analysis_policy;
  PlatformFileTextResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  memset(&result, 0, sizeof(result));
  memset(&object, 0, sizeof(object));
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL,
        &result.diagnostics) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (enrich_policy_from_object_target_info_local(analysis_policy, backend, &object, NULL, 0U,
      &result.diagnostics) != 0) {
    m68k_object_destroy(&object);
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, analysis_policy) ||
      m68k_facts_v2_render_asm_source_alloc(&object, analysis_policy, &result.text, NULL,
        m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "facts_v2 asm source render failed");
  }
  m68k_object_destroy(&object);
  free(analysis_policy);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_asm_source_raw_path_text_alloc(const char *platform_name, const char *path,
    uint32_t entry_offset, const char *metadata_path, char **out_text) {
  M68kAnalysisPolicy *analysis_policy;
  PlatformFileTextResult result;
  M68kObject object;
  memset(&result, 0, sizeof(result));
  memset(&object, 0, sizeof(object));
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, platform_name, metadata_path, NULL,
        &result.diagnostics) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (load_raw_object_from_path(platform_name, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (!policy_set_raw_entry_address_local(analysis_policy, &object, entry_offset, &result.diagnostics)) {
    m68k_object_destroy(&object);
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, analysis_policy) ||
      m68k_facts_v2_render_asm_source_alloc(&object, analysis_policy, &result.text, NULL,
        m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "facts_v2 asm source render failed");
  }
  m68k_object_destroy(&object);
  free(analysis_policy);
  return text_result_to_alloc(&result, out_text);
}

static PlatformFileTextResult facts_v2_asm_source_object_json(const char *backend_name, const char *path,
    const M68kObject *object, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  M68kFactsV2Profile profile;
  JsonBuilder builder = {0};
  char *source = NULL;
  char *json = NULL;
  clock_t total_start = clock();
  clock_t total_end;
  memset(&result, 0, sizeof(result));
  if (backend_name == NULL || path == NULL || object == NULL || analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid facts_v2 source request");
    return result;
  }
  if (m68k_facts_v2_render_asm_source_profile_alloc(object, analysis_policy, &source, &profile, 0U,
      m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "facts_v2 asm source render failed");
    m68k_facts_v2_free_text(source);
    return result;
  }
  total_end = clock();
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"source_text\":") != 0 ||
      json_builder_append_json_string(&builder, source != NULL ? source : "") != 0 ||
      json_builder_append(&builder, ",\"profile\":{\"generation\":\"facts_v2_asm_source\",\"backend\":") != 0 ||
      json_builder_append_json_string(&builder, backend_name) != 0 ||
      json_builder_append(&builder, ",\"analysis_backend\":\"facts_v2\",\"path\":") != 0 ||
      json_builder_append_json_string(&builder, path) != 0 ||
      json_builder_append(&builder, ",\"facts_v2\":") != 0 ||
      json_builder_append_facts_v2_profile(&builder, &profile) != 0 ||
      json_builder_appendf(&builder, ",\"timing\":{\"total_seconds\":%.6f}}}",
        elapsed_seconds(total_start, total_end)) != 0) {
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
  m68k_facts_v2_free_text(source);
  return result;
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

static int facts_v2_asm_source_object_text_profile_alloc(const char *backend_name, const char *path,
    const M68kObject *object, const M68kAnalysisPolicy *analysis_policy, char **out_source_text,
    char **out_profile_json, M68kDiagList *diagnostics) {
  M68kFactsV2Profile profile;
  char *source = NULL;
  char *profile_json = NULL;
  clock_t total_start = clock();
  clock_t total_end;
  if (out_source_text == NULL || out_profile_json == NULL) return -1;
  *out_source_text = NULL;
  *out_profile_json = NULL;
  if (backend_name == NULL || path == NULL || object == NULL || analysis_policy == NULL) {
    if (diagnostics != NULL) platform_file_add_error(diagnostics, "invalid facts_v2 source request");
    return -1;
  }
  if (m68k_facts_v2_render_asm_source_profile_alloc(object, analysis_policy, &source, &profile, 0U,
      diagnostics != NULL ? m68k_diag_sink(diagnostics) : m68k_diag_sink(NULL)) != 0) {
    if (diagnostics != NULL && !m68k_diag_has_errors(diagnostics))
      platform_file_add_error(diagnostics, "facts_v2 asm source render failed");
    m68k_facts_v2_free_text(source);
    return -1;
  }
  total_end = clock();
  profile_json = facts_v2_asm_source_profile_json_alloc(backend_name, path, &profile,
    elapsed_seconds(total_start, total_end), diagnostics);
  if (profile_json == NULL) {
    m68k_facts_v2_free_text(source);
    return -1;
  }
  if (source == NULL) {
    source = duplicate_text_local("");
    if (source == NULL) {
      if (diagnostics != NULL) platform_file_add_error(diagnostics, "out of memory");
      platform_file_free_text(profile_json);
      return -1;
    }
  }
  *out_source_text = source;
  *out_profile_json = profile_json;
  return 0;
}

static int facts_v2_asm_source_text_profile_error_to_alloc(const M68kDiagList *diagnostics,
    char **out_source_text, char **out_profile_json) {
  const char *message;
  if (out_source_text == NULL || out_profile_json == NULL) return -1;
  message = diagnostics != NULL ? m68k_diag_first_message(diagnostics) : NULL;
  if (message == NULL || message[0] == '\0') message = "facts_v2 asm source render failed";
  platform_file_free_text(*out_source_text);
  platform_file_free_text(*out_profile_json);
  *out_source_text = duplicate_text_local("");
  *out_profile_json = duplicate_text_local(message);
  return -1;
}

static void facts_v2_listing_fill_source_bytes_from_object(M68kSourceFileIR *source_file,
    const M68kObject *object) {
  size_t section_index;
  if (source_file == NULL || object == NULL) return;
  for (section_index = 0U; section_index < source_file->section_count && section_index < object->section_count;
       ++section_index) {
    M68kSectionIR *source_section = &source_file->sections[section_index];
    const M68kSection *object_section = &object->sections[section_index];
    size_t statement_index;
    if (object_section->data == NULL || object_section->data_size == 0U) continue;
    for (statement_index = 0U; statement_index < source_section->statement_count; ++statement_index) {
      M68kStatementIR *stmt = &source_section->statements[statement_index];
      size_t byte_count = 0U;
      if (stmt->kind == M68K_STATEMENT_INSTRUCTION) byte_count = stmt->u.instruction.byte_count;
      else if (stmt->kind == M68K_STATEMENT_DATA) byte_count = stmt->u.data.size;
      if (byte_count == 0U || stmt->offset >= object_section->data_size) continue;
      if (byte_count > object_section->data_size - stmt->offset) byte_count = object_section->data_size - stmt->offset;
      if (byte_count > M68K_STATEMENT_SOURCE_BYTES_MAX) byte_count = M68K_STATEMENT_SOURCE_BYTES_MAX;
      memcpy(stmt->source_bytes, object_section->data + stmt->offset, byte_count);
      stmt->source_byte_count = (uint8_t)byte_count;
    }
  }
}

#define FACTS_V2_BASIC_LISTING_DATA_CHUNK 4096U

static int basic_listing_policy_entry_matches(const M68kAnalysisPolicy *policy, size_t section_index,
    uint32_t offset) {
  uint16_t index;
  if (policy == NULL) return 0;
  if (policy->has_entry_offset && section_index == 0U && policy->entry_offset == offset) return 1;
  for (index = 0U; index < policy->entry_point_count && index < M68K_ANALYSIS_ENTRY_POINT_LIMIT; ++index) {
    const M68kAnalysisEntryPoint *entry = &policy->entry_points[index];
    if ((!entry->has_section_index || entry->section_index == (uint32_t)section_index) && entry->offset == offset)
      return 1;
  }
  return 0;
}

static const char *basic_listing_policy_label_name(const M68kAnalysisPolicy *policy, size_t section_index,
    uint32_t offset) {
  uint16_t index;
  if (policy == NULL) return NULL;
  for (index = 0U; index < policy->named_label_count && index < M68K_ANALYSIS_NAMED_LABEL_LIMIT; ++index) {
    const M68kAnalysisNamedLabel *label = &policy->named_labels[index];
    if (label->section_index == (uint32_t)section_index && label->offset == offset && label->name[0] != '\0')
      return label->name;
  }
  return NULL;
}

static int basic_listing_offset_is_code_region(const M68kAnalysisPolicy *policy, size_t section_index,
    const M68kSection *section, uint32_t offset) {
  if (section == NULL || section->kind != M68K_SECTION_CODE) return 0;
  if (policy != NULL && policy->has_entry_offset && section_index == 0U) return offset >= policy->entry_offset;
  return 1;
}

static int basic_listing_append_label(M68kSectionIR *section_ir, const M68kAnalysisPolicy *policy,
    size_t section_index, uint32_t offset, uint32_t *last_label_offset, int *last_label_valid) {
  M68kStatementIR stmt;
  char label_name[96];
  const char *policy_name;
  if (section_ir == NULL || last_label_offset == NULL || last_label_valid == NULL) return -1;
  if (*last_label_valid && *last_label_offset == offset) return 0;
  policy_name = basic_listing_policy_label_name(policy, section_index, offset);
  if (policy_name != NULL) snprintf(label_name, sizeof(label_name), "%s", policy_name);
  else snprintf(label_name, sizeof(label_name), "loc_%u_%08X", (unsigned)section_index, (unsigned)offset);
  m68k_ir_statement_init(&stmt);
  stmt.kind = M68K_STATEMENT_LABEL;
  stmt.offset = offset;
  stmt.label_name = label_name;
  stmt.label_is_generated = policy_name == NULL ? 1U : 0U;
  if (m68k_ir_section_append_statement(section_ir, &stmt) != 0) return -1;
  *last_label_offset = offset;
  *last_label_valid = 1;
  return 0;
}

static int basic_listing_append_data(M68kSectionIR *section_ir, const uint8_t *data, uint32_t offset,
    uint32_t size) {
  M68kStatementIR stmt;
  uint32_t byte_count;
  if (section_ir == NULL || size == 0U) return 0;
  m68k_ir_statement_init(&stmt);
  stmt.kind = M68K_STATEMENT_DATA;
  stmt.offset = offset;
  stmt.u.data.kind = M68K_DATA_ITEM_BYTES;
  stmt.u.data.data = (uint8_t *)data;
  stmt.u.data.size = size;
  stmt.comment = "facts_v2 basic data bytes";
  byte_count = size;
  if (byte_count > M68K_STATEMENT_SOURCE_BYTES_MAX) byte_count = M68K_STATEMENT_SOURCE_BYTES_MAX;
  if (data != NULL && byte_count != 0U) {
    memcpy(stmt.source_bytes, data, byte_count);
    stmt.source_byte_count = (uint8_t)byte_count;
  }
  return m68k_ir_section_append_statement(section_ir, &stmt);
}

static int basic_listing_append_instruction(M68kSectionIR *section_ir, const M68kInstructionIR *instruction,
    const uint8_t *data, uint32_t offset) {
  M68kStatementIR stmt;
  size_t byte_count;
  if (section_ir == NULL || instruction == NULL || instruction->byte_count == 0U) return -1;
  m68k_ir_statement_init(&stmt);
  stmt.kind = M68K_STATEMENT_INSTRUCTION;
  stmt.offset = offset;
  stmt.u.instruction = *instruction;
  byte_count = instruction->byte_count;
  if (byte_count > M68K_STATEMENT_SOURCE_BYTES_MAX) byte_count = M68K_STATEMENT_SOURCE_BYTES_MAX;
  if (data != NULL && byte_count != 0U) {
    memcpy(stmt.source_bytes, data + offset, byte_count);
    stmt.source_byte_count = (uint8_t)byte_count;
  }
  return m68k_ir_section_append_statement(section_ir, &stmt);
}

static int facts_v2_basic_listing_build_source_file(const M68kObject *object, const M68kAnalysisPolicy *policy,
    M68kSourceFileIR *source_file, M68kDiagSink diagnostics) {
  size_t section_index;
  uint8_t max_cpu;
  if (object == NULL || source_file == NULL) return -1;
  if (m68k_ir_source_file_create(source_file) != 0) goto oom;
  source_file->platform_backend_kind = object->platform_backend_kind;
  source_file->file_kind = object->platform_file_kind;
  if (object->platform_backend_kind == M68K_PLATFORM_BACKEND_ATARI_ST &&
      m68k_atari_st_get_program_flags(object, &source_file->atari_st_program_flags) == 0) {
    source_file->has_atari_st_program_flags = 1U;
  }
  max_cpu = policy != NULL && policy->max_cpu != 0U ? policy->max_cpu : M68K_ASM_CPU_68060;
  for (section_index = 0U; section_index < object->section_count; ++section_index) {
    const M68kSection *object_section = &object->sections[section_index];
    M68kSectionIR section_ir;
    uint32_t offset = 0U;
    uint32_t data_size = object_section->data_size;
    uint32_t last_label_offset = 0U;
    int last_label_valid = 0;
    int section_live = 0;
    if (m68k_ir_section_create(&section_ir) != 0) goto oom;
    section_live = 1;
    section_ir.kind = object_section->kind;
    section_ir.platform_mem_type = object_section->platform_mem_type;
    section_ir.platform_mem_attrs = object_section->platform_mem_attrs;
    section_ir.size = object_section->size;
    section_ir.data_size = object_section->data_size;
    if (m68k_ir_section_set_name(&section_ir, object_section->name) != 0) goto oom_section;
    while (offset < data_size) {
      int code_region = basic_listing_offset_is_code_region(policy, section_index, object_section, offset);
      if (code_region && (offset & 1U) == 0U && object_section->data != NULL) {
        M68kInstructionIR instruction = m68k_ir_decode_one(object_section->data + offset, data_size - offset,
          max_cpu, m68k_diag_sink(NULL));
        if (instruction.byte_count != 0U && instruction.byte_count <= data_size - offset) {
          if ((offset == 0U || basic_listing_policy_entry_matches(policy, section_index, offset)) &&
              basic_listing_append_label(&section_ir, policy, section_index, offset, &last_label_offset,
                &last_label_valid) != 0)
            goto oom_section;
          if (basic_listing_append_instruction(&section_ir, &instruction, object_section->data, offset) != 0)
            goto oom_section;
          offset += (uint32_t)instruction.byte_count;
          continue;
        }
      }
      {
        uint32_t start = offset;
        uint32_t limit = data_size;
        uint32_t chunk;
        if (policy != NULL && policy->has_entry_offset && section_index == 0U && start < policy->entry_offset &&
            policy->entry_offset < limit) {
          limit = policy->entry_offset;
        }
        if (limit <= start) limit = start + 1U;
        chunk = limit - start;
        if (chunk > FACTS_V2_BASIC_LISTING_DATA_CHUNK) chunk = FACTS_V2_BASIC_LISTING_DATA_CHUNK;
        if (object_section->data != NULL &&
            basic_listing_append_data(&section_ir, object_section->data + start, start, chunk) != 0)
          goto oom_section;
        offset = start + chunk;
      }
    }
    if (m68k_ir_source_file_append_section(source_file, &section_ir) != 0) goto oom_section;
    m68k_ir_section_destroy(&section_ir);
    section_live = 0;
    continue;
oom_section:
    if (section_live) m68k_ir_section_destroy(&section_ir);
    goto oom;
  }
  return 0;
oom:
  m68k_ir_source_file_destroy(source_file);
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
  return -1;
}

static PlatformFileTextResult facts_v2_basic_listing_rows_object_json(const char *backend_name, const char *path,
    const M68kObject *object, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  M68kSourceFileIR source_ir;
  M68kRenderPolicy render_policy;
  JsonBuilder builder = {0};
  char *source_text = NULL;
  char *rows_json = NULL;
  char *json = NULL;
  clock_t total_start = clock();
  clock_t render_end;
  clock_t rows_end;
  memset(&result, 0, sizeof(result));
  memset(&source_ir, 0, sizeof(source_ir));
  if (backend_name == NULL || path == NULL || object == NULL || analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid facts_v2 basic listing rows request");
    return result;
  }
  if (facts_v2_basic_listing_build_source_file(object, analysis_policy, &source_ir,
      m68k_diag_sink(&result.diagnostics)) != 0)
    goto cleanup;
  m68k_render_policy_init_default(&render_policy);
  if (m68k_source_ir_render_text_with_policy(&source_ir, &render_policy, &source_text,
      m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "facts_v2 basic listing render failed");
    goto cleanup;
  }
  render_end = clock();
  if (source_file_listing_rows_to_json(&source_ir, source_text, analysis_policy, NULL, "basic", 0, &rows_json,
      m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "facts_v2 basic listing row json failed");
    goto cleanup;
  }
  rows_end = clock();
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"listing\":") != 0 ||
      json_builder_append(&builder, rows_json != NULL ? rows_json : "{\"rows\":[]}") != 0 ||
      json_builder_append(&builder, ",\"analysis\":{\"sections\":[]}") != 0 ||
      json_builder_append(&builder, ",\"profile\":{\"generation\":\"facts_v2_basic_listing\",\"backend\":") != 0 ||
      json_builder_append_json_string(&builder, backend_name) != 0 ||
      json_builder_append(&builder, ",\"analysis_backend\":\"facts_v2\",\"path\":") != 0 ||
      json_builder_append_json_string(&builder, path) != 0 ||
      json_builder_appendf(&builder,
        ",\"timing\":{\"render_seconds\":%.6f,\"rows_json_seconds\":%.6f,\"total_seconds\":%.6f}}}",
        elapsed_seconds(total_start, render_end), elapsed_seconds(render_end, rows_end),
        elapsed_seconds(total_start, rows_end)) != 0) {
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
  platform_file_free_text(rows_json);
  platform_file_free_text(source_text);
  m68k_ir_source_file_destroy(&source_ir);
  return result;
}

static int facts_v2_listing_rows_from_source_text(const M68kObject *object, const M68kAnalysisPolicy *analysis_policy,
    const M68kSourceAnalysisIR *source_analysis, const char *source_text, const char *include_dir,
    int include_source_only_rows, char **out_rows_json, M68kDiagSink diagnostics) {
  AsmSourceFile source_model;
  M68kSourceFileIR source_ir;
  int result = -1;
  if (object == NULL || analysis_policy == NULL || source_text == NULL || out_rows_json == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_BAD_ARGUMENT,
      "invalid facts_v2 listing rows request");
    return -1;
  }
  memset(&source_model, 0, sizeof(source_model));
  memset(&source_ir, 0, sizeof(source_ir));
  snprintf(source_model.include_dir, sizeof(source_model.include_dir), "%s", include_dir != NULL ? include_dir : "");
  source_model.target_cpu = analysis_policy->max_cpu != 0U ? analysis_policy->max_cpu : M68K_ASM_CPU_68060;
  source_model.platform_backend_kind = object->platform_backend_kind;
  source_model.file_kind = object->platform_file_kind;
  if (!m68k_source_pipeline_parse_text_and_layout(&source_model, source_text, diagnostics) ||
      !m68k_source_pipeline_build_ir(&source_model, &source_ir, diagnostics)) {
    goto cleanup;
  }
  source_ir.platform_backend_kind = object->platform_backend_kind;
  source_ir.file_kind = object->platform_file_kind;
  facts_v2_listing_fill_source_bytes_from_object(&source_ir, object);
  if (source_file_listing_rows_to_json(&source_ir, source_text, analysis_policy, source_analysis, "full",
      include_source_only_rows, out_rows_json, diagnostics) != 0)
    goto cleanup;
  result = 0;

cleanup:
  m68k_ir_source_file_destroy(&source_ir);
  m68k_source_model_free(&source_model);
  return result;
}

static PlatformFileTextResult facts_v2_listing_rows_object_json(const char *backend_name, const char *path,
    const M68kObject *object, const M68kAnalysisPolicy *analysis_policy, const char *include_dir,
    int include_source_text) {
  PlatformFileTextResult result;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  JsonBuilder builder = {0};
  char *source = NULL;
  char *rows_json = NULL;
  char *analysis_json = NULL;
  char *json = NULL;
  clock_t total_start = clock();
  clock_t source_end;
  clock_t rows_end;
  clock_t total_end;
  memset(&result, 0, sizeof(result));
  memset(&source_analysis, 0, sizeof(source_analysis));
  if (backend_name == NULL || path == NULL || object == NULL || analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid facts_v2 listing rows request");
    return result;
  }
  if (m68k_facts_v2_render_asm_source_analysis_profile_alloc(object, analysis_policy, &source, &profile,
      &source_analysis, 1U, m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "facts_v2 asm source render failed");
    goto cleanup;
  }
  source_end = clock();
  if (facts_v2_listing_rows_from_source_text(object, &source_analysis.policy, &source_analysis, source, include_dir,
      include_source_text, &rows_json,
      m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "facts_v2 listing row source parse failed");
    goto cleanup;
  }
  rows_end = clock();
  if (source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "facts_v2 source analysis json failed");
    goto cleanup;
  }
  total_end = clock();
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"listing\":") != 0 ||
      json_builder_append(&builder, rows_json != NULL ? rows_json : "{\"rows\":[]}") != 0 ||
      json_builder_append(&builder, ",\"analysis\":") != 0 ||
      json_builder_append(&builder, analysis_json != NULL ? analysis_json : "{\"sections\":[]}") != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  if (include_source_text) {
    if (json_builder_append(&builder, ",\"source_text\":") != 0 ||
        json_builder_append_json_string(&builder, source != NULL ? source : "") != 0) {
      platform_file_add_error(&result.diagnostics, "out of memory");
      goto cleanup;
    }
  }
  if (json_builder_append(&builder, ",\"profile\":{\"generation\":\"facts_v2_listing\",\"backend\":") != 0 ||
      json_builder_append_json_string(&builder, backend_name) != 0 ||
      json_builder_append(&builder, ",\"analysis_backend\":\"facts_v2\",\"path\":") != 0 ||
      json_builder_append_json_string(&builder, path) != 0 ||
      json_builder_append(&builder, ",\"facts_v2\":") != 0 ||
      json_builder_append_facts_v2_profile(&builder, &profile) != 0 ||
      json_builder_appendf(&builder,
        ",\"timing\":{\"source_seconds\":%.6f,\"rows_json_seconds\":%.6f,\"total_seconds\":%.6f}}}",
        elapsed_seconds(total_start, source_end), elapsed_seconds(source_end, rows_end),
        elapsed_seconds(total_start, total_end)) != 0) {
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
  platform_file_free_text(rows_json);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_facts_v2_free_text(source);
  return result;
}

int platform_file_facts_v2_asm_source_path_json_alloc(const char *backend_name, const char *path,
    const char *metadata_path, char **out_text) {
  M68kAnalysisPolicy *analysis_policy;
  PlatformFileTextResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  memset(&result, 0, sizeof(result));
  memset(&object, 0, sizeof(object));
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL,
        &result.diagnostics) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (enrich_policy_from_object_target_info_local(analysis_policy, backend, &object, NULL, 0U,
      &result.diagnostics) != 0) {
    m68k_object_destroy(&object);
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, analysis_policy)) {
    m68k_object_destroy(&object);
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  result = facts_v2_asm_source_object_json(backend_name, path, &object, analysis_policy);
  m68k_object_destroy(&object);
  free(analysis_policy);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_asm_source_raw_path_json_alloc(const char *platform_name, const char *path,
    uint32_t entry_offset, const char *metadata_path, char **out_text) {
  M68kAnalysisPolicy *analysis_policy;
  PlatformFileTextResult result;
  M68kObject object;
  memset(&result, 0, sizeof(result));
  memset(&object, 0, sizeof(object));
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, platform_name, metadata_path, NULL,
        &result.diagnostics) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (load_raw_object_from_path(platform_name, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (!policy_set_raw_entry_address_local(analysis_policy, &object, entry_offset, &result.diagnostics)) {
    m68k_object_destroy(&object);
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, analysis_policy)) {
    m68k_object_destroy(&object);
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  result = facts_v2_asm_source_object_json(platform_name, path, &object, analysis_policy);
  m68k_object_destroy(&object);
  free(analysis_policy);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_asm_source_path_text_profile_alloc(const char *backend_name, const char *path,
    const char *metadata_path, char **out_source_text, char **out_profile_json) {
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  int result = -1;
  if (out_source_text == NULL || out_profile_json == NULL) return -1;
  *out_source_text = NULL;
  *out_profile_json = NULL;
  m68k_diag_list_reset(&diagnostics);
  memset(&object, 0, sizeof(object));
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    platform_file_add_error(&diagnostics, "out of memory");
    return facts_v2_asm_source_text_profile_error_to_alloc(&diagnostics, out_source_text, out_profile_json);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL, &diagnostics) != 0)
    goto cleanup;
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&diagnostics)) != 0) goto cleanup;
  if (enrich_policy_from_object_target_info_local(analysis_policy, backend, &object, NULL, 0U,
      &diagnostics) != 0) {
    goto cleanup;
  }
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&diagnostics, &object, analysis_policy)) goto cleanup;
  result = facts_v2_asm_source_object_text_profile_alloc(backend_name, path, &object, analysis_policy,
    out_source_text, out_profile_json, &diagnostics);

cleanup:
  m68k_object_destroy(&object);
  free(analysis_policy);
  if (result != 0)
    return facts_v2_asm_source_text_profile_error_to_alloc(&diagnostics, out_source_text, out_profile_json);
  return 0;
}

int platform_file_facts_v2_asm_source_raw_path_text_profile_alloc(const char *platform_name, const char *path,
    uint32_t entry_offset, const char *metadata_path, char **out_source_text, char **out_profile_json) {
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  M68kObject object;
  int result = -1;
  if (out_source_text == NULL || out_profile_json == NULL) return -1;
  *out_source_text = NULL;
  *out_profile_json = NULL;
  m68k_diag_list_reset(&diagnostics);
  memset(&object, 0, sizeof(object));
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    platform_file_add_error(&diagnostics, "out of memory");
    return facts_v2_asm_source_text_profile_error_to_alloc(&diagnostics, out_source_text, out_profile_json);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, platform_name, metadata_path, NULL, &diagnostics) != 0)
    goto cleanup;
  if (load_raw_object_from_path(platform_name, path, &object, m68k_diag_sink(&diagnostics)) != 0) goto cleanup;
  if (!policy_set_raw_entry_address_local(analysis_policy, &object, entry_offset, &diagnostics)) goto cleanup;
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&diagnostics, &object, analysis_policy)) goto cleanup;
  result = facts_v2_asm_source_object_text_profile_alloc(platform_name, path, &object, analysis_policy,
    out_source_text, out_profile_json, &diagnostics);

cleanup:
  m68k_object_destroy(&object);
  free(analysis_policy);
  if (result != 0)
    return facts_v2_asm_source_text_profile_error_to_alloc(&diagnostics, out_source_text, out_profile_json);
  return 0;
}

static int facts_v2_render_assemble_object_alloc(const char *backend_name, const char *path,
    const M68kObject *object, const M68kAnalysisPolicy *analysis_policy, const char *include_dir,
    const char *output_path, const char *target_cpu_name, int enable_vasm_compat_rewrites,
    unsigned char **out_data, size_t *out_size, char **out_source_profile_json,
    char **out_assembler_profile_json, char **out_error, M68kDiagList *diagnostics) {
  M68kFactsV2Profile source_profile;
  M68kPlatformAssembleProfile empty_assembler_profile;
  char *source = NULL;
  char *source_profile_json = NULL;
  unsigned char *assembled_data = NULL;
  size_t assembled_size = 0U;
  char *assembler_profile_json = NULL;
  char *assembler_error = NULL;
  clock_t source_start = clock();
  clock_t source_end;
  int result;
  if (out_data == NULL || out_size == NULL || out_source_profile_json == NULL ||
      out_assembler_profile_json == NULL || out_error == NULL) {
    return -1;
  }
  *out_data = NULL;
  *out_size = 0U;
  *out_source_profile_json = NULL;
  *out_assembler_profile_json = NULL;
  *out_error = NULL;
  memset(&empty_assembler_profile, 0, sizeof(empty_assembler_profile));
  m68k_facts_v2_profile_init(&source_profile);
  if (backend_name == NULL || path == NULL || object == NULL || analysis_policy == NULL) {
    if (diagnostics != NULL) platform_file_add_error(diagnostics, "invalid facts_v2 render assemble request");
    *out_error = duplicate_text_local("invalid facts_v2 render assemble request");
    *out_source_profile_json = facts_v2_asm_source_profile_json_alloc("", "", &source_profile, 0.0, diagnostics);
    *out_assembler_profile_json = assembler_profile_json_alloc_local(&empty_assembler_profile);
    return -1;
  }
  if (m68k_facts_v2_render_asm_source_profile_alloc(object, analysis_policy, &source, &source_profile, 0U,
      diagnostics != NULL ? m68k_diag_sink(diagnostics) : m68k_diag_sink(NULL)) != 0) {
    const char *message = diagnostics != NULL ? m68k_diag_first_message(diagnostics) : NULL;
    if (message == NULL || message[0] == '\0') message = "facts_v2 asm source render failed";
    *out_error = duplicate_text_local(message);
    *out_source_profile_json = facts_v2_asm_source_profile_json_alloc(backend_name, path, &source_profile, 0.0,
      diagnostics);
    *out_assembler_profile_json = assembler_profile_json_alloc_local(&empty_assembler_profile);
    m68k_facts_v2_free_text(source);
    return -1;
  }
  source_end = clock();
  source_profile_json = facts_v2_asm_source_profile_json_alloc(backend_name, path, &source_profile,
    elapsed_seconds(source_start, source_end), diagnostics);
  if (source_profile_json == NULL) {
    *out_error = duplicate_text_local("out of memory");
    *out_assembler_profile_json = assembler_profile_json_alloc_local(&empty_assembler_profile);
    m68k_facts_v2_free_text(source);
    return -1;
  }
  if (source_profile.asm_source_refused) {
    *out_source_profile_json = source_profile_json;
    *out_assembler_profile_json = assembler_profile_json_alloc_local(&empty_assembler_profile);
    if (*out_assembler_profile_json == NULL) {
      platform_file_free_text(*out_source_profile_json);
      *out_source_profile_json = NULL;
      *out_error = duplicate_text_local("out of memory");
      m68k_facts_v2_free_text(source);
      return -1;
    }
    m68k_facts_v2_free_text(source);
    return 0;
  }
  result = platform_file_assemble_source_common_alloc(backend_name, include_dir != NULL ? include_dir : "",
    NULL, source != NULL ? source : "", output_path != NULL ? output_path : "", target_cpu_name,
    enable_vasm_compat_rewrites, &assembled_data, &assembled_size, &assembler_profile_json, &assembler_error);
  m68k_facts_v2_free_text(source);
  *out_source_profile_json = source_profile_json;
  *out_assembler_profile_json = assembler_profile_json;
  if (result != 0) {
    *out_error = assembler_error != NULL ? assembler_error : duplicate_text_local("platform assembler failed");
    return -1;
  }
  *out_data = assembled_data;
  *out_size = assembled_size;
  return 0;
}

int platform_file_facts_v2_render_assemble_path_bytes_profile_alloc(const char *backend_name, const char *path,
    const char *metadata_path, const char *include_dir, const char *output_path, const char *target_cpu_name,
    int enable_vasm_compat_rewrites, unsigned char **out_data, size_t *out_size, char **out_source_profile_json,
    char **out_assembler_profile_json, char **out_error) {
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  int result = -1;
  if (out_data == NULL || out_size == NULL || out_source_profile_json == NULL ||
      out_assembler_profile_json == NULL || out_error == NULL) {
    return -1;
  }
  *out_data = NULL;
  *out_size = 0U;
  *out_source_profile_json = NULL;
  *out_assembler_profile_json = NULL;
  *out_error = NULL;
  m68k_diag_list_reset(&diagnostics);
  memset(&object, 0, sizeof(object));
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    *out_error = duplicate_text_local("out of memory");
    return -1;
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL, &diagnostics) != 0)
    goto cleanup;
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&diagnostics)) != 0) goto cleanup;
  if (enrich_policy_from_object_target_info_local(analysis_policy, backend, &object, NULL, 0U,
      &diagnostics) != 0) {
    goto cleanup;
  }
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&diagnostics, &object, analysis_policy)) goto cleanup;
  result = facts_v2_render_assemble_object_alloc(backend_name, path, &object, analysis_policy, include_dir,
    output_path, target_cpu_name, enable_vasm_compat_rewrites, out_data, out_size, out_source_profile_json,
    out_assembler_profile_json, out_error, &diagnostics);

cleanup:
  if (result != 0 && *out_error == NULL) {
    const char *message = m68k_diag_first_message(&diagnostics);
    if (message == NULL || message[0] == '\0') message = "facts_v2 render assemble failed";
    *out_error = duplicate_text_local(message);
  }
  m68k_object_destroy(&object);
  free(analysis_policy);
  return result;
}

int platform_file_facts_v2_render_assemble_raw_path_bytes_profile_alloc(const char *platform_name, const char *path,
    uint32_t entry_offset, const char *metadata_path, const char *include_dir, const char *output_path,
    const char *target_cpu_name, int enable_vasm_compat_rewrites, unsigned char **out_data, size_t *out_size,
    char **out_source_profile_json, char **out_assembler_profile_json, char **out_error) {
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  M68kObject object;
  int result = -1;
  if (out_data == NULL || out_size == NULL || out_source_profile_json == NULL ||
      out_assembler_profile_json == NULL || out_error == NULL) {
    return -1;
  }
  *out_data = NULL;
  *out_size = 0U;
  *out_source_profile_json = NULL;
  *out_assembler_profile_json = NULL;
  *out_error = NULL;
  m68k_diag_list_reset(&diagnostics);
  memset(&object, 0, sizeof(object));
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    *out_error = duplicate_text_local("out of memory");
    return -1;
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, platform_name, metadata_path, NULL, &diagnostics) != 0)
    goto cleanup;
  if (load_raw_object_from_path(platform_name, path, &object, m68k_diag_sink(&diagnostics)) != 0) goto cleanup;
  if (!policy_set_raw_entry_address_local(analysis_policy, &object, entry_offset, &diagnostics)) goto cleanup;
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&diagnostics, &object, analysis_policy)) goto cleanup;
  result = facts_v2_render_assemble_object_alloc(platform_name, path, &object, analysis_policy, include_dir,
    output_path, target_cpu_name, enable_vasm_compat_rewrites, out_data, out_size, out_source_profile_json,
    out_assembler_profile_json, out_error, &diagnostics);

cleanup:
  if (result != 0 && *out_error == NULL) {
    const char *message = m68k_diag_first_message(&diagnostics);
    if (message == NULL || message[0] == '\0') message = "facts_v2 render assemble failed";
    *out_error = duplicate_text_local(message);
  }
  m68k_object_destroy(&object);
  free(analysis_policy);
  return result;
}

static int facts_v2_direct_write_object_alloc(const char *backend_name, const M68kBackend *backend,
    const M68kObject *object, const char *output_path, uint32_t source_bytes, unsigned char **out_data,
    size_t *out_size, const unsigned char *compare_data, size_t compare_size, char **out_direct_profile_json,
    char **out_error, M68kDiagList *diagnostics) {
  clock_t total_start = clock();
  clock_t phase_start;
  double write_buffer_seconds = 0.0;
  double write_file_seconds = 0.0;
  double compare_seconds = 0.0;
  FactsV2DirectCompareResult compare_result;
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
  memset(&compare_result, 0, sizeof(compare_result));
  compare_result.status = "not_compared";
  temp_path[0] = '\0';
  if (backend == NULL || object == NULL) {
    *out_error = duplicate_text_local("unknown platform file backend");
    return -1;
  }
  if (backend->write_buffer != NULL) {
    phase_start = clock();
    if (backend->write_buffer(object, &data, &size, m68k_diag_sink(diagnostics)) != 0) {
      const char *message = m68k_diag_first_message(diagnostics);
      *out_error = duplicate_text_local(message != NULL ? message : "direct rebuild write_buffer failed");
      return -1;
    }
    write_buffer_seconds += elapsed_seconds(phase_start, clock());
    if (output_path != NULL && output_path[0] != '\0') {
      phase_start = clock();
      if (write_bytes_to_path_local(output_path, data, size, diagnostics) != 0) {
        const char *message = m68k_diag_first_message(diagnostics);
        free(data);
        *out_error = duplicate_text_local(message != NULL ? message : "direct rebuild write failed");
        return -1;
      }
      write_file_seconds += elapsed_seconds(phase_start, clock());
    }
  } else if (backend->write_file != NULL) {
    read_path = output_path;
    if (read_path == NULL || read_path[0] == '\0') {
      if (write_object_to_temp_file(backend, object, temp_path, sizeof(temp_path), m68k_diag_sink(diagnostics)) != 0) {
        const char *message = m68k_diag_first_message(diagnostics);
        *out_error = duplicate_text_local(message != NULL ? message : "direct rebuild write failed");
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
        *out_error = duplicate_text_local(message != NULL ? message : "direct rebuild write failed");
        return -1;
      }
      write_file_seconds += elapsed_seconds(phase_start, clock());
    }
    if (read_file_to_buffer(read_path, &data, &size, m68k_diag_sink(diagnostics)) != 0) {
      const char *message = m68k_diag_first_message(diagnostics);
      if (remove_read_path) remove(read_path);
      *out_error = duplicate_text_local(message != NULL ? message : "direct rebuild read failed");
      return -1;
    }
    if (remove_read_path) remove(read_path);
  } else {
    *out_error = duplicate_text_local("platform backend cannot write direct rebuild output");
    return -1;
  }
  if (compare_data != NULL) {
    phase_start = clock();
    compare_result = facts_v2_direct_compare_result(backend_name, backend, object, data, size, compare_data,
      compare_size);
    compare_seconds += elapsed_seconds(phase_start, clock());
  }
  *out_direct_profile_json = facts_v2_direct_rebuild_profile_json_alloc(backend_name, source_bytes,
    size > UINT32_MAX ? UINT32_MAX : (uint32_t)size, 0, NULL, write_buffer_seconds, write_file_seconds,
    compare_size, compare_result, compare_seconds, elapsed_seconds(total_start, clock()), diagnostics);
  if (*out_direct_profile_json == NULL) {
    free(data);
    *out_error = duplicate_text_local("out of memory");
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
    M68kDiagList *diagnostics) {
  M68kFactsV2Profile source_profile;
  FactsV2DirectCompareResult not_compared;
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
  memset(&not_compared, 0, sizeof(not_compared));
  not_compared.status = "not_compared";
  m68k_facts_v2_profile_init(&source_profile);
  if (m68k_facts_v2_collect_direct_rebuild_profile(object, analysis_policy, &source_profile,
      m68k_diag_sink(diagnostics)) != 0) {
    const char *message = m68k_diag_first_message(diagnostics);
    *out_error = duplicate_text_local(message != NULL ? message : "facts_v2 source profile failed");
    return -1;
  }
  source_end = clock();
  source_profile_json = facts_v2_asm_source_profile_json_alloc(backend_name, path, &source_profile,
    elapsed_seconds(source_start, source_end), diagnostics);
  if (source_profile_json == NULL) {
    *out_error = duplicate_text_local("out of memory");
    return -1;
  }
  *out_source_profile_json = source_profile_json;
  if (source_profile.asm_source_refused) {
    *out_direct_profile_json = facts_v2_direct_rebuild_profile_json_alloc(backend_name,
      source_profile.asm_source_bytes, 0U, 1, "source_refused", 0.0, 0.0, 0U, not_compared, 0.0, 0.0,
      diagnostics);
    if (*out_direct_profile_json == NULL) {
      *out_error = duplicate_text_local("out of memory");
      return -1;
    }
    return 0;
  }
  if (source_profile.asm_source_lossy_numeric_hunk_relocations != 0U ||
      source_profile.unassemblable_hunk_data_relocations != 0U ||
      source_profile.unassemblable_hunk_base_register_relocations != 0U) {
    *out_direct_profile_json = facts_v2_direct_rebuild_profile_json_alloc(backend_name,
      source_profile.asm_source_bytes, 0U, 1, "lossy_numeric_hunk_relocations", 0.0, 0.0, 0,
      not_compared, 0.0, 0.0, diagnostics);
    if (*out_direct_profile_json == NULL) {
      *out_error = duplicate_text_local("out of memory");
      return -1;
    }
    return 0;
  }
  return facts_v2_direct_write_object_alloc(backend_name, backend, object, output_path,
    source_profile.asm_source_bytes, out_data, out_size, compare_data, compare_size, out_direct_profile_json,
    out_error, diagnostics);
}

static int platform_file_facts_v2_direct_rebuild_path_common_alloc(const char *backend_name, const char *path,
    const char *metadata_path, const char *output_path, unsigned char **out_data, size_t *out_size,
    char **out_source_profile_json, char **out_direct_profile_json, char **out_error, int compare_original) {
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  M68kObject object;
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
  memset(&object, 0, sizeof(object));
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    *out_error = duplicate_text_local("out of memory");
    return -1;
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL, &diagnostics) != 0)
    goto cleanup;
  if (compare_original && read_file_to_buffer(path, &compare_data, &compare_size, m68k_diag_sink(&diagnostics)) != 0)
    goto cleanup;
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&diagnostics)) != 0) goto cleanup;
  if (enrich_policy_from_object_target_info_local(analysis_policy, backend, &object, NULL, 0U,
      &diagnostics) != 0) {
    goto cleanup;
  }
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&diagnostics, &object, analysis_policy)) goto cleanup;
  result = facts_v2_direct_rebuild_object_alloc(backend_name, path, backend, &object, analysis_policy,
    output_path, out_data, out_size, out_source_profile_json, out_direct_profile_json, compare_data, compare_size,
    out_error, &diagnostics);

cleanup:
  if (result != 0 && *out_error == NULL) {
    const char *message = m68k_diag_first_message(&diagnostics);
    if (message == NULL || message[0] == '\0') message = "facts_v2 direct rebuild failed";
    *out_error = duplicate_text_local(message);
  }
  free(compare_data);
  m68k_object_destroy(&object);
  free(analysis_policy);
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
  M68kObject object;
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
  memset(&object, 0, sizeof(object));
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    *out_error = duplicate_text_local("out of memory");
    return -1;
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL, &diagnostics) != 0)
    goto cleanup;
  if (load_object_from_buffer(backend, data, size, &object, m68k_diag_sink(&diagnostics)) != 0) goto cleanup;
  if (enrich_policy_from_object_target_info_local(analysis_policy, backend, &object, NULL, 0U,
      &diagnostics) != 0) {
    goto cleanup;
  }
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&diagnostics, &object, analysis_policy)) goto cleanup;
  result = facts_v2_direct_rebuild_object_alloc(backend_name, display_path != NULL ? display_path : "", backend,
    &object, analysis_policy, output_path, out_data, out_size, out_source_profile_json, out_direct_profile_json,
    compare_original ? data : NULL, compare_original ? size : 0U, out_error, &diagnostics);

cleanup:
  if (result != 0 && *out_error == NULL) {
    const char *message = m68k_diag_first_message(&diagnostics);
    if (message == NULL || message[0] == '\0') message = "facts_v2 direct rebuild failed";
    *out_error = duplicate_text_local(message);
  }
  m68k_object_destroy(&object);
  free(analysis_policy);
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

static int platform_file_facts_v2_listing_rows_path_json_alloc_local(const char *backend_name, const char *path,
    const char *metadata_path, const char *include_dir, int include_source_text, char **out_text) {
  M68kAnalysisPolicy *analysis_policy;
  PlatformFileTextResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  memset(&result, 0, sizeof(result));
  memset(&object, 0, sizeof(object));
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL,
        &result.diagnostics) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (enrich_policy_from_object_target_info_local(analysis_policy, backend, &object, NULL, 0U,
      &result.diagnostics) != 0) {
    m68k_object_destroy(&object);
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, analysis_policy)) {
    m68k_object_destroy(&object);
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  result = facts_v2_listing_rows_object_json(backend_name, path, &object, analysis_policy, include_dir,
    include_source_text);
  m68k_object_destroy(&object);
  free(analysis_policy);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_listing_rows_with_analysis_path_json_alloc(const char *backend_name, const char *path,
    const char *metadata_path, const char *include_dir, char **out_text) {
  return platform_file_facts_v2_listing_rows_path_json_alloc_local(backend_name, path, metadata_path, include_dir,
    0, out_text);
}

int platform_file_facts_v2_listing_rows_with_analysis_and_text_path_json_alloc(const char *backend_name,
    const char *path, const char *metadata_path, const char *include_dir, char **out_text) {
  return platform_file_facts_v2_listing_rows_path_json_alloc_local(backend_name, path, metadata_path, include_dir,
    1, out_text);
}

int platform_file_facts_v2_basic_listing_rows_path_json_alloc(const char *backend_name, const char *path,
    const char *metadata_path, const char *include_dir, char **out_text) {
  M68kAnalysisPolicy *analysis_policy;
  PlatformFileTextResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  (void)include_dir;
  memset(&result, 0, sizeof(result));
  memset(&object, 0, sizeof(object));
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL,
        &result.diagnostics) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (enrich_policy_from_object_target_info_local(analysis_policy, backend, &object, NULL, 0U,
      &result.diagnostics) != 0) {
    m68k_object_destroy(&object);
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, analysis_policy)) {
    m68k_object_destroy(&object);
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  result = facts_v2_basic_listing_rows_object_json(backend_name, path, &object, analysis_policy);
  m68k_object_destroy(&object);
  free(analysis_policy);
  return text_result_to_alloc(&result, out_text);
}

static int platform_file_facts_v2_listing_rows_raw_path_json_alloc_local(const char *platform_name, const char *path,
    uint32_t entry_offset, const char *metadata_path, const char *include_dir, int include_source_text,
    char **out_text) {
  M68kAnalysisPolicy *analysis_policy;
  PlatformFileTextResult result;
  M68kObject object;
  memset(&result, 0, sizeof(result));
  memset(&object, 0, sizeof(object));
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, platform_name, metadata_path, NULL,
        &result.diagnostics) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (load_raw_object_from_path(platform_name, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (!policy_set_raw_entry_address_local(analysis_policy, &object, entry_offset, &result.diagnostics)) {
    m68k_object_destroy(&object);
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, analysis_policy)) {
    m68k_object_destroy(&object);
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  result = facts_v2_listing_rows_object_json(platform_name, path, &object, analysis_policy, include_dir,
    include_source_text);
  m68k_object_destroy(&object);
  free(analysis_policy);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_listing_rows_with_analysis_raw_path_json_alloc(const char *platform_name,
    const char *path, uint32_t entry_offset, const char *metadata_path, const char *include_dir, char **out_text) {
  return platform_file_facts_v2_listing_rows_raw_path_json_alloc_local(platform_name, path, entry_offset,
    metadata_path, include_dir, 0, out_text);
}

int platform_file_facts_v2_listing_rows_with_analysis_and_text_raw_path_json_alloc(const char *platform_name,
    const char *path, uint32_t entry_offset, const char *metadata_path, const char *include_dir, char **out_text) {
  return platform_file_facts_v2_listing_rows_raw_path_json_alloc_local(platform_name, path, entry_offset,
    metadata_path, include_dir, 1, out_text);
}

int platform_file_facts_v2_basic_listing_rows_raw_path_json_alloc(const char *platform_name,
    const char *path, uint32_t entry_offset, const char *metadata_path, const char *include_dir, char **out_text) {
  M68kAnalysisPolicy *analysis_policy;
  PlatformFileTextResult result;
  M68kObject object;
  (void)include_dir;
  memset(&result, 0, sizeof(result));
  memset(&object, 0, sizeof(object));
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, platform_name, metadata_path, NULL,
        &result.diagnostics) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (load_raw_object_from_path(platform_name, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (!policy_set_raw_entry_address_local(analysis_policy, &object, entry_offset, &result.diagnostics)) {
    m68k_object_destroy(&object);
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  enrich_policy_pointer_targets_from_object_local(analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, analysis_policy)) {
    m68k_object_destroy(&object);
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  result = facts_v2_basic_listing_rows_object_json(platform_name, path, &object, analysis_policy);
  m68k_object_destroy(&object);
  free(analysis_policy);
  return text_result_to_alloc(&result, out_text);
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
