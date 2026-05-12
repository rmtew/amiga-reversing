#include "platform_file_lib.h"
#include "platform_file_internal.h"
#include "json_builder.h"
#include "m68k_analysis_facts_v2.h"
#include "m68k_assembler_app.h"
#include "m68k_assembler.h"
#include "m68k_assembler_policy.h"
#include "m68k_backend.h"
#include "m68k_decode_ir.h"
#include "m68k_fact_ir.h"
#include "m68k_instruction_spec.h"
#include "m68k_ir_codec.h"
#include "m68k_object.h"
#include "m68k_parse_util.h"
#include "m68k_reproduction_compare.h"
#include "m68k_simulator.h"
#include "m68k_source_pipeline.h"
#include "m68k_source_ir_render.h"
#include "platform_atari_st.h"
#include "platform_common.h"
#include "platform_file_decompression.h"
#include "util_arena.h"
#include "generated/amiga_hunk_file_runtime.h"
#include "generated/amiga_os_runtime.h"

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
static void platform_file_add_warning(M68kDiagList *diagnostics, const char *message);
static int read_file_to_buffer(const char *path, unsigned char **out_data, size_t *out_size,
    M68kDiagSink diagnostics);
static int load_object_from_path(const M68kBackend *backend, const char *path, M68kObject *object,
    M68kDiagSink diagnostics);
static int load_raw_object_from_path(const char *platform_name, const char *path, M68kObject *object,
    M68kDiagSink diagnostics);
static int json_builder_append_facts_v2_profile(JsonBuilder *builder, const M68kFactsV2Profile *profile);
static uint32_t read_be32_local(const uint8_t *data);
static int write_bytes_to_path_local(const char *path, const unsigned char *data, size_t size,
    M68kDiagList *diagnostics);
static const char *self_decrunch_sim_stop_reason_name_local(uint8_t stop_reason);

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
static int policy_add_rsset_layout_region_local(M68kAnalysisPolicy *policy, uint32_t offset, uint8_t size,
  const char *layout_name, const char *base_symbol, const char *sizeof_symbol, const char *symbol,
  const char *struct_name, const char *pointer_struct, uint8_t flags, uint8_t storage_kind_id,
  const char *storage_kind, const char *semantic_type);
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

static uint8_t rsset_layout_region_storage_kind_id_from_text_local(const char *storage_kind) {
  if (storage_kind == NULL || storage_kind[0] == '\0') return M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_UNKNOWN;
  if (strcmp(storage_kind, "struct_instance") == 0 ||
      strcmp(storage_kind, "struct") == 0) return M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_STRUCT_INSTANCE;
  if (strcmp(storage_kind, "struct_pointer") == 0) return M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_STRUCT_POINTER;
  if (strcmp(storage_kind, "pointer") == 0) return M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_POINTER;
  if (strcmp(storage_kind, "scalar") == 0) return M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_SCALAR;
  return M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_UNKNOWN;
}

static const char *rsset_layout_region_storage_kind_name_local(uint8_t storage_kind_id) {
  switch (storage_kind_id) {
    case M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_STRUCT_INSTANCE: return "struct_instance";
    case M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_STRUCT_POINTER: return "struct_pointer";
    case M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_POINTER: return "pointer";
    case M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_SCALAR: return "scalar";
    default: return NULL;
  }
}

static uint8_t rsset_layout_region_size_from_storage_kind_id_local(uint8_t storage_kind_id) {
  (void)storage_kind_id;
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
    default: return "unknown";
  }
}

static const char *decompression_payload_role_name_local(uint8_t payload_role) {
  switch (payload_role) {
    case PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_UNKNOWN_RUNTIME_PAYLOAD: return "unknown_runtime_payload";
    case PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_PRIMARY_PROGRAM: return "primary_program";
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
  char simulated_output_sha256[65];
  char simulated_diagnostic[M68K_DIAG_MESSAGE_SIZE];
  uint8_t simulated_stop_reason;
  uint8_t has_simulated_output;
  uint8_t simulation_attempted;
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
  char codec_id[64];
  char codec_name[160];
  char provider_id[32];
  char decompressed_sha256[65];
  uint8_t postpass_escape_byte;
  uint8_t native_unpack_validated;
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

static int runtime_transfer_target_from_candidate_local(const M68kDecodeSectionIR *section,
    const M68kSectionAnalysisIR *section_analysis, const M68kDecodeCandidate *candidate,
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
    if (target < 0x1000U) continue;
    if (target < section->size && section_analysis->certain_code_byte != NULL &&
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
  if (!recognized_tetragon_unpack_lz_stage_local(decode_section, event, memory,
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
    event->has_copied_stub_transfer = 1U;
    break;
  }
}

static int collect_recognized_tetragon_events_for_section_local(const M68kDecodeSectionIR *decode_section,
    const M68kSectionAnalysisIR *section_analysis, Arena *arena, PlatformRecognizedUnpackerEvent *events,
    size_t event_capacity, size_t *io_event_count, const char *materialize_event_id,
    const char *materialize_output_path, PlatformRecognizedUnpackerEvent *out_materialized_event,
    M68kDiagList *materialize_diagnostics) {
  static const unsigned char marker[] = " TETRAGON ";
  uint32_t offset;
  if (decode_section == NULL || section_analysis == NULL || events == NULL || io_event_count == NULL ||
      decode_section->data == NULL || decode_section->size < sizeof(marker) - 1U) {
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
    snprintf(event.codec_id, sizeof(event.codec_id), "tetragon");
    snprintf(event.codec_name, sizeof(event.codec_name), "Tetragon target-owned unpacker");
    snprintf(event.provider_id, sizeof(event.provider_id), "c-tetragon-signature");
    if (materialize_event_id != NULL) {
      char event_id[160];
      int materialize_this_event;
      make_recognized_unpacker_event_id_local(event_id, sizeof(event_id), &event);
      materialize_this_event = strcmp(event_id, materialize_event_id) == 0;
      (void)recognized_tetragon_try_unpack_event_local(arena, decode_section, &event,
        materialize_this_event ? materialize_output_path : NULL,
        materialize_this_event ? materialize_diagnostics : NULL);
      recognized_unpacker_attach_copied_stub_local(section_analysis, marker_end, code_end, &event);
      if (materialize_this_event && out_materialized_event != NULL) *out_materialized_event = event;
    } else {
      (void)recognized_tetragon_try_unpack_event_local(arena, decode_section, &event, NULL, NULL);
      recognized_unpacker_attach_copied_stub_local(section_analysis, marker_end, code_end, &event);
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
    PlatformRecognizedUnpackerEvent *out_materialized_event, M68kDiagList *materialize_diagnostics) {
  M68kDecodeIR decode;
  size_t section_index;
  int result = 0;
  if (object == NULL || analysis == NULL || events == NULL || out_event_count == NULL) return -1;
  *out_event_count = 0U;
  m68k_decode_ir_init(&decode);
  if (m68k_decode_ir_build_object(&decode, object, analysis->policy.max_cpu, m68k_diag_sink(NULL)) != 0) {
    return -1;
  }
  for (section_index = 0U; section_index < decode.section_count && *out_event_count < event_capacity;
      ++section_index) {
    if (section_index >= analysis->section_count) break;
    if (collect_recognized_tetragon_events_for_section_local(&decode.sections[section_index],
        &analysis->sections[section_index], analysis->arena, events, event_capacity, out_event_count,
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
    if (!recognized->native_unpack_validated) continue;
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

static int runtime_address_from_operand_local(const M68kOperandIR *operand, const uint8_t a_known[8],
    const uint32_t a_values[8], uint32_t *out_address) {
  uint8_t shape, reg;
  int64_t address;
  if (out_address != NULL) *out_address = 0U;
  if (operand == NULL || a_known == NULL || a_values == NULL || out_address == NULL) return 0;
  shape = m68k_instruction_operand_decoded_ea_shape(operand);
  if (m68k_instruction_decoded_ea_target_kind(operand, shape, 0) == 1U) {
    *out_address = operand->value.value;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_IND || operand->kind == M68K_ASM_OPERAND_POSTINC ||
      operand->kind == M68K_ASM_OPERAND_PREDEC) {
    reg = operand->value.reg;
    if (reg >= 8U || !a_known[reg]) return 0;
    *out_address = a_values[reg];
    return 1;
  }
  if (operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_reg >= 8U) return 0;
  reg = operand->value.ea_reg;
  if (!a_known[reg]) return 0;
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
    const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata, uint8_t a_known[8],
    uint32_t a_values[8], PlatformRuntimeWriteObservation *writes, size_t write_capacity,
    size_t *io_write_count) {
  uint8_t invalidated[8] = {0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U};
  size_t operand_index;
  if (candidate == NULL || instruction == NULL || metadata == NULL || a_known == NULL || a_values == NULL ||
      writes == NULL || io_write_count == NULL) {
    return;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t reg = 0U;
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE &&
        instruction_operand_address_register_local(&instruction->operands[operand_index], &reg)) {
      invalidated[reg] = 1U;
    }
  }
  if (metadata->operation_class == M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS &&
      metadata->source_operand_index < instruction->operand_count &&
      metadata->dest_operand_index < instruction->operand_count) {
    uint8_t reg = 0U;
    uint32_t address = 0U;
    if (instruction_operand_address_register_local(&instruction->operands[metadata->dest_operand_index], &reg) &&
        runtime_address_from_operand_local(&instruction->operands[metadata->source_operand_index], a_known,
          a_values, &address)) {
      a_known[reg] = 1U;
      a_values[reg] = address;
      invalidated[reg] = 0U;
    }
  }
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    uint32_t address = 0U;
    uint32_t width = candidate_write_width_local(candidate);
    uint8_t reg = 0U;
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_WRITE &&
        width != 0U && runtime_address_from_operand_local(&instruction->operands[operand_index], a_known,
          a_values, &address) &&
        address >= 0x1000U && address <= UINT32_MAX - width && *io_write_count < write_capacity) {
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
        if (a_known[reg] && width != 0U) {
          if (update == M68K_SIM_EA_UPDATE_POSTINCREMENT && a_values[reg] <= UINT32_MAX - width) {
            a_values[reg] += width;
          } else if (update == M68K_SIM_EA_UPDATE_PREDECREMENT && a_values[reg] >= width) {
            a_values[reg] -= width;
          } else {
            a_known[reg] = 0U;
          }
        }
      }
    }
  }
  for (operand_index = 0U; operand_index < 8U; ++operand_index) {
    if (invalidated[operand_index]) a_known[operand_index] = 0U;
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
    uint32_t transfer_target, const char *output_path, const PlatformDecompressionIdentifyResult *result) {
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
  if (object == NULL || analysis == NULL || analysis->arena == NULL || section == NULL || section->data == NULL ||
      output_path == NULL || result == NULL || result->decompressed_size == 0U ||
      transfer_target > UINT32_MAX - result->decompressed_size) {
    return 0;
  }
  mark = arena_mark(analysis->arena);
  if (read_file_to_arena_local(analysis->arena, output_path, &expected, &expected_size) != 0 ||
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
  memory = (uint8_t *)arena_calloc(analysis->arena, memory_size, 1U);
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
  memory_policy.user = (void *)object;
  state.pc = entry_offset;
  state.a[7] = (uint32_t)memory_size;
  step_limit = result->decompressed_size > PLATFORM_PROVIDER_WRAPPER_STEP_LIMIT / 64U ?
    PLATFORM_PROVIDER_WRAPPER_STEP_LIMIT : result->decompressed_size * 64U;
  if (step_limit < PLATFORM_SELF_DECRUNCH_STEP_LIMIT) step_limit = PLATFORM_SELF_DECRUNCH_STEP_LIMIT;
  if (m68k_simulate_run_concrete(analysis->policy.max_cpu, memory, memory_size, &state,
      step_limit, transfer_target, transfer_target + 16U,
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
  arena_rewind(analysis->arena, mark);
  return ok;
}

static int promote_provider_payload_from_wrapper_simulation_local(const M68kObject *object,
    const M68kSourceAnalysisIR *analysis, const char *output_path, PlatformDecompressionIdentifyResult *result) {
  M68kDecodeIR decode;
  const M68kDecodeSectionIR *decode_section;
  const M68kSectionAnalysisIR *section_analysis;
  const M68kSection *section;
  uint32_t offset;
  uint32_t source_start, source_end;
  int promoted = 0;
  memset(&decode, 0, sizeof(decode));
  if (object == NULL || analysis == NULL || output_path == NULL || result == NULL ||
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
      0U, candidate->offset, analysis->arena);
    if (!simulate_provider_wrapper_candidate_local(object, analysis, section, entry_offset, transfer_target,
        output_path, result)) {
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
    PlatformSelfDecrunchEvent *out_event, const char *output_path, M68kDiagList *diagnostics) {
  ArenaMark mark;
  uint8_t *memory = NULL;
  size_t memory_size, range_index, write_range_index;
  uint32_t output_start = 0U, output_end = 0U;
  M68kSimConcreteState state;
  M68kSimConcreteMemoryPolicy memory_policy;
  M68kSimConcreteRunTraceResult result;
  int ok = 0;
  if (out_event != NULL && event != NULL) *out_event = *event;
  if (object == NULL || analysis == NULL || analysis->arena == NULL || section == NULL || event == NULL ||
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
  if (memory_size > PLATFORM_SELF_DECRUNCH_MEMORY_LIMIT || event->decompressor_entry_offset >= section->size) return 0;
  mark = arena_mark(analysis->arena);
  memory = (uint8_t *)arena_calloc(analysis->arena, memory_size, 1U);
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
  memset(&state, 0, sizeof(state));
  memset(&memory_policy, 0, sizeof(memory_policy));
  memset(&result, 0, sizeof(result));
  memory_policy.external_write_allowed = platform_self_decrunch_external_write_allowed_local;
  memory_policy.user = (void *)object;
  state.pc = event->decompressor_entry_offset;
  state.a[7] = (uint32_t)memory_size;
  if (m68k_simulate_run_concrete(analysis->policy.max_cpu, memory, memory_size, &state,
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
  (void)m68k_platform_sha256_hex(memory + output_start, output_end - output_start,
    out_event->simulated_output_sha256);
  ok = 1;

cleanup:
  arena_rewind(analysis->arena, mark);
  return ok;
}

static int collect_self_decrunch_events_for_section(const M68kObject *object, const M68kDecodeIR *decode,
    const M68kSourceAnalysisIR *analysis, size_t section_index, PlatformSelfDecrunchEvent *events,
    size_t event_capacity, size_t *io_event_count, const char *materialize_event_id,
    const char *materialize_output_path, PlatformSelfDecrunchEvent *out_materialized_event,
    M68kDiagList *materialize_diagnostics) {
  const M68kSection *object_section;
  const M68kDecodeSectionIR *decode_section;
  const M68kSectionAnalysisIR *section_analysis;
  uint8_t a_known[8] = {0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U};
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
    if (section_analysis->certain_code_start[offset] == 0U) continue;
    if (previous_end != UINT32_MAX && offset != previous_end && offset != bridge_target) {
      memset(a_known, 0, sizeof(a_known));
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
    trace_runtime_writes_from_candidate_local(candidate, &instruction, metadata, a_known, a_values, writes,
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
        run_start, offset, analysis->arena);
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
        materialize_this_event ? materialize_diagnostics : NULL);
      if (materialize_this_event && out_materialized_event != NULL) *out_materialized_event = event;
      if (!self_decrunch_event_duplicate_local(events, *io_event_count, &event)) {
        events[*io_event_count] = event;
        *io_event_count += 1U;
      }
    }
  }
  return 0;
}

static int collect_self_decrunch_events_local(const M68kObject *object, const M68kSourceAnalysisIR *analysis,
    PlatformSelfDecrunchEvent *events, size_t event_capacity, size_t *out_event_count,
    const char *materialize_event_id, const char *materialize_output_path,
    PlatformSelfDecrunchEvent *out_materialized_event, M68kDiagList *materialize_diagnostics) {
  M68kDecodeIR decode;
  size_t section_index;
  int result = 0;
  if (out_event_count != NULL) *out_event_count = 0U;
  if (object == NULL || analysis == NULL || events == NULL || out_event_count == NULL || event_capacity == 0U)
    return 0;
  if (object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 0;
  memset(&decode, 0, sizeof(decode));
  if (m68k_decode_ir_build_object_sections(&decode, object, m68k_diag_sink(NULL)) != 0) return 0;
  for (section_index = 0U; section_index < object->section_count && *out_event_count < event_capacity;
      ++section_index) {
    if (collect_self_decrunch_events_for_section(object, &decode, analysis, section_index, events,
        event_capacity, out_event_count, materialize_event_id, materialize_output_path,
        out_materialized_event, materialize_diagnostics) != 0) {
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
  if (builder == NULL || event == NULL) return -1;
  make_recognized_unpacker_event_id_local(event_id, sizeof(event_id), event);
  status = event->native_unpack_validated ? PLATFORM_DECOMPRESSION_STATUS_MATERIALIZABLE :
    PLATFORM_DECOMPRESSION_STATUS_IDENTIFIED;
  reason = event->native_unpack_validated ? PLATFORM_DECOMPRESSION_REASON_NATIVE_TETRAGON_UNPACK_VALIDATED :
    PLATFORM_DECOMPRESSION_REASON_RECOGNIZED_UNPACKER_SIGNATURE;
  payload_role = event->native_unpack_validated ? PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_PRIMARY_PROGRAM :
    PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_UNKNOWN_RUNTIME_PAYLOAD;
  payload_confidence = event->native_unpack_validated ?
    PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_NATIVE_UNPACK_ENTRY_VALIDATED :
    PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_SIGNATURE_ONLY;
  parent_remains_active = event->native_unpack_validated ? PLATFORM_DECOMPRESSION_PARENT_REMAINS_ACTIVE_FALSE :
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
  }
  if (event->native_unpack_validated) {
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
  if (builder == NULL || event == NULL) return -1;
  make_self_decrunch_event_id_local(event_id, sizeof(event_id), event);
  status = event->has_simulated_output ? PLATFORM_DECOMPRESSION_STATUS_SIMULATED_OUTPUT_OBSERVED :
    PLATFORM_DECOMPRESSION_STATUS_NEEDS_SIMULATED_DECRUNCH;
  reason = self_decrunch_event_reason_id_local(event);
  parent_remains_active = event->parent_remains_active ? PLATFORM_DECOMPRESSION_PARENT_REMAINS_ACTIVE_TRUE :
    PLATFORM_DECOMPRESSION_PARENT_REMAINS_ACTIVE_FALSE;
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
        (unsigned)PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_UNKNOWN_RUNTIME_PAYLOAD) != 0 ||
      json_builder_append_json_string(builder,
        decompression_payload_role_name_local(PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_UNKNOWN_RUNTIME_PAYLOAD)) != 0 ||
      json_builder_appendf(builder,
        ",\"payload_role_confidence_id\":%u,\"payload_role_confidence\":",
        (unsigned)PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_OBSERVED_OUTPUT_ONLY) != 0 ||
      json_builder_append_json_string(builder,
        decompression_payload_role_confidence_name_local(
          PLATFORM_DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_OBSERVED_OUTPUT_ONLY)) != 0 ||
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

static int append_object_decompression_analysis_json(JsonBuilder *builder, const M68kObject *object,
    const M68kSourceAnalysisIR *analysis) {
  PlatformDecompressionIdentifyResult results[32];
  PlatformSelfDecrunchEvent self_decrunch_events[16];
  PlatformRecognizedUnpackerEvent recognized_unpacker_events[16];
  size_t result_count = 0U;
  size_t self_decrunch_event_count = 0U;
  size_t recognized_unpacker_event_count = 0U;
  size_t section_index;
  size_t emitted_event_count = 0U;
  if (object == NULL || analysis == NULL) return -1;
  memset(results, 0, sizeof(results));
  memset(self_decrunch_events, 0, sizeof(self_decrunch_events));
  memset(recognized_unpacker_events, 0, sizeof(recognized_unpacker_events));
  for (section_index = 0U; section_index < object->section_count; ++section_index) {
    const M68kSection *section = &object->sections[section_index];
    const M68kSectionAnalysisIR *section_analysis;
    PlatformDecompressionCandidate candidates[16];
    size_t candidate_count, candidate_index;
    if (section->data == NULL || section->data_size == 0U || section_index >= analysis->section_count) continue;
    section_analysis = &analysis->sections[section_index];
    candidate_count = platform_decompression_find_candidates_in_buffer("ancient-cli", section->data,
      section->data_size, candidates, sizeof(candidates) / sizeof(candidates[0]));
    if (candidate_count > sizeof(candidates) / sizeof(candidates[0]))
      candidate_count = sizeof(candidates) / sizeof(candidates[0]);
    for (candidate_index = 0U; candidate_index < candidate_count && result_count < sizeof(results) / sizeof(results[0]);
        ++candidate_index) {
      const PlatformDecompressionCandidate *candidate = &candidates[candidate_index];
      PlatformDecompressionIdentifyResult result;
      char output_path[512];
      char error[256];
      error[0] = '\0';
      if (!automatic_decompression_candidate_is_useful(candidate)) continue;
      if (analysis_range_overlaps_accepted_code(section_analysis, candidate->offset, candidate->packed_size))
        continue;
      if (make_temp_output_path(output_path, sizeof(output_path)) != 0) return -1;
      if (platform_decompression_decompress_buffer_range("ancient-cli", "", section->data, section->data_size,
          candidate->offset, candidate->packed_size, output_path, &result, error, sizeof(error)) != 0) {
        remove(output_path);
        continue;
      }
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
          (void)promote_provider_payload_from_wrapper_simulation_local(object, analysis, output_path, &result);
        }
      }
      result.decompressed_path[0] = '\0';
      results[result_count++] = result;
      remove(output_path);
    }
  }
  if (collect_self_decrunch_events_local(object, analysis, self_decrunch_events,
      sizeof(self_decrunch_events) / sizeof(self_decrunch_events[0]), &self_decrunch_event_count,
      NULL, NULL, NULL, NULL) != 0) {
    return -1;
  }
  if (collect_recognized_unpacker_events_local(object, analysis, recognized_unpacker_events,
      sizeof(recognized_unpacker_events) / sizeof(recognized_unpacker_events[0]),
      &recognized_unpacker_event_count, NULL, NULL, NULL, NULL) != 0) {
    return -1;
  }
  if (json_builder_append(builder, ",\"packed_payloads\":[") != 0) return -1;
  for (section_index = 0U; section_index < result_count; ++section_index) {
    if (section_index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (platform_decompression_append_result_json(builder, &results[section_index]) != 0) return -1;
  }
  if (json_builder_append(builder, "],\"derived_target_suggestions\":[") != 0) return -1;
  for (section_index = 0U; section_index < result_count; ++section_index) {
    if (section_index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (append_derived_decompression_suggestion_json(builder, &results[section_index],
        find_decompression_runtime_copy_view(analysis, &results[section_index])) != 0) return -1;
  }
  if (json_builder_append(builder, "],\"decompression_events\":[") != 0) return -1;
  for (section_index = 0U; section_index < result_count; ++section_index) {
    if (emitted_event_count != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (append_decompression_event_json(builder, &results[section_index],
        find_decompression_runtime_copy_view(analysis, &results[section_index])) != 0) return -1;
    ++emitted_event_count;
  }
  for (section_index = 0U; section_index < recognized_unpacker_event_count; ++section_index) {
    if (emitted_event_count != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (append_recognized_unpacker_event_json(builder, &recognized_unpacker_events[section_index]) != 0) return -1;
    ++emitted_event_count;
  }
  for (section_index = 0U; section_index < self_decrunch_event_count; ++section_index) {
    if (self_decrunch_event_matches_materialized_provider_local(results, result_count,
        &self_decrunch_events[section_index]))
      continue;
    if (self_decrunch_event_matches_native_recognized_unpacker_local(recognized_unpacker_events,
        recognized_unpacker_event_count, &self_decrunch_events[section_index]))
      continue;
    if (emitted_event_count != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (append_self_decrunch_event_json(builder, &self_decrunch_events[section_index]) != 0) return -1;
    ++emitted_event_count;
  }
  return json_builder_append(builder, "]");
}

static int append_analysis_json_with_decompression_profile(JsonBuilder *builder, const char *base_json,
    const M68kObject *object, const M68kSourceAnalysisIR *analysis, const M68kFactsV2Profile *profile) {
  size_t base_len;
  if (builder == NULL || base_json == NULL || object == NULL || analysis == NULL) return -1;
  base_len = strlen(base_json);
  if (base_len == 0U || base_json[base_len - 1U] != '}') return -1;
  if (json_builder_appendf(builder, "%.*s", (int)(base_len - 1U), base_json) != 0)
    return -1;
  if (append_object_decompression_analysis_json(builder, object, analysis) != 0)
    return -1;
  if (profile != NULL) {
    if (json_builder_append(builder,
        ",\"profile\":{\"generation\":\"facts_v2_analysis\",\"analysis_backend\":\"facts_v2\",\"facts_v2\":") != 0 ||
        json_builder_append_facts_v2_profile(builder, profile) != 0 ||
        json_builder_append(builder, "}") != 0)
      return -1;
  }
  return json_builder_append(builder, "}");
}

static int append_analysis_json_with_decompression(JsonBuilder *builder, const char *base_json,
    const M68kObject *object, const M68kSourceAnalysisIR *analysis) {
  return append_analysis_json_with_decompression_profile(builder, base_json, object, analysis, NULL);
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
  if (struct_name != NULL && strcmp(struct_name, "resident_autoinit") == 0) {
    item->platform_kind_id = M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_KIND_AMIGA_RESIDENT_AUTOINIT;
    if (field_name != NULL && strcmp(field_name, "resident_base_size") == 0)
      item->platform_field_id = M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_AMIGA_RESIDENT_BASE_SIZE;
    else if (field_name != NULL && strcmp(field_name, "resident_vectors") == 0)
      item->platform_field_id = M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_AMIGA_RESIDENT_VECTORS;
    else if (field_name != NULL && strcmp(field_name, "resident_init_struct") == 0)
      item->platform_field_id = M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_AMIGA_RESIDENT_INIT_STRUCT;
    else if (field_name != NULL && strcmp(field_name, "resident_init_function") == 0)
      item->platform_field_id = M68K_ANALYSIS_STRUCTURED_DATA_PLATFORM_FIELD_AMIGA_RESIDENT_INIT_FUNCTION;
  }
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
    if (!policy_add_register_seed_local(policy, entry->hunk, entry->offset, "A6", "library_base", library_name,
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
  array_start = json_find_array_local(text, "rsset_layout_regions", &array_end);
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
  uint32_t count = 0U;
  if (target_type == NULL || target_type[0] == '\0') return 0U;
  for (prefix_index = 0U; prefix_index < AMIGA_OS_RESIDENT_VECTOR_PREFIX_COUNT; ++prefix_index) {
    const AmigaOsResidentVectorPrefixInfo *prefix = amiga_os_resident_vector_prefix_at(prefix_index);
    if (prefix == NULL || strcmp(prefix->target_type, target_type) != 0) continue;
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
  uint8_t addr_reg_known[8];
  uint32_t cursor;
  uint32_t scan_count;
  uint32_t first_code_offset = UINT32_MAX;
  if (policy == NULL || object == NULL || hunk >= object->section_count) return 0;
  if (object->sections[hunk].data == NULL || init_offset >= object->sections[hunk].data_size) return 0;
  memset(addr_reg_targets, 0, sizeof(addr_reg_targets));
  memset(addr_reg_known, 0, sizeof(addr_reg_known));
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
    if (instruction_calls_exec_makelibrary_policy_local(instruction) && addr_reg_known[0]) {
      return policy_add_non_autoinit_vector_table_local(policy, object, hunk, addr_reg_targets[0], target_type,
        library_name, library_version, &first_code_offset);
    }
    for (reg = 0U; reg < 8U; ++reg) {
      if (instruction_writes_address_reg_approx(instruction, reg)) addr_reg_known[reg] = 0U;
    }
    if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U &&
        operand_address_reg_index_policy_local(&instruction->operands[1], &reg) && reg < 8U &&
        policy_source_operand_target_local(&ctx, instruction, cursor, 0U, &addr_reg_targets[reg])) {
      addr_reg_known[reg] = 1U;
    } else {
      const M68kOperandIR *source = NULL;
      if (instruction_is_address_move(instruction, &reg, &source) && reg < 8U && source != NULL &&
          policy_source_operand_target_local(&ctx, instruction, cursor, 0U, &addr_reg_targets[reg])) {
        addr_reg_known[reg] = 1U;
      }
    }
    if (decode.is_call) memset(addr_reg_known, 0, sizeof(addr_reg_known));
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
        "\"runtime_range_count\":%u,\"runtime_entry_point_count\":%u,\"rsset_layout_region_count\":%u",
        (unsigned)policy->max_cpu, policy->disable_implicit_entry_points ? "false" : "true",
        (unsigned)policy->entry_point_count, (unsigned)policy->register_seed_count,
        (unsigned)policy->structured_data_item_count, (unsigned)policy->named_label_count,
        (unsigned)policy->entry_comment_count, (unsigned)policy->runtime_range_count,
        (unsigned)policy->runtime_entry_point_count, (unsigned)policy->rsset_layout_region_count) != 0)
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
    if (json_builder_appendf(builder,
          ",\"platform_kind_id\":%u,\"platform_field_id\":%u,\"struct_id\":%u,\"field_id\":%u",
          (unsigned)item->platform_kind_id, (unsigned)item->platform_field_id, (unsigned)item->struct_id,
          (unsigned)item->field_id) != 0)
      return -1;
    if (json_builder_append(builder, ",\"field_type\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, item->field_type) != 0) return -1;
    if (json_builder_append(builder, ",\"c_type\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, item->c_type) != 0) return -1;
    if (json_builder_append(builder, ",\"pointer_struct\":") != 0) return -1;
    if (append_nullable_text_json_local(builder, item->pointer_struct) != 0) return -1;
    if (json_builder_appendf(builder, ",\"pointer_struct_id\":%u", (unsigned)item->pointer_struct_id) != 0)
      return -1;
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
  m68k_object_mark_no_container(object);
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
    "\"render_ir_platform_pass_seconds\":%.6f,"
    "\"render_ir_platform_base_slot_seconds\":%.6f,"
    "\"render_ir_platform_call_summary_seconds\":%.6f,"
    "\"render_ir_platform_typed_ref_seconds\":%.6f,"
    "\"render_ir_platform_call_comment_seconds\":%.6f,"
    "\"render_ir_platform_app_slot_seconds\":%.6f,"
    "\"render_ir_platform_runtime_data_seconds\":%.6f,"
    "\"render_ir_platform_hardware_data_seconds\":%.6f,"
    "\"render_ir_platform_generic_data_seconds\":%.6f,"
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
    profile->render_ir_platform_pass_seconds,
    profile->render_ir_platform_base_slot_seconds,
    profile->render_ir_platform_call_summary_seconds,
    profile->render_ir_platform_typed_ref_seconds,
    profile->render_ir_platform_call_comment_seconds,
    profile->render_ir_platform_app_slot_seconds,
    profile->render_ir_platform_runtime_data_seconds,
    profile->render_ir_platform_hardware_data_seconds,
    profile->render_ir_platform_generic_data_seconds,
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

static M68kReproductionCompareResult facts_v2_direct_compare_result(const char *backend_name,
    const M68kBackend *backend, const M68kObject *original_object, const unsigned char *rebuilt_data,
    size_t rebuilt_size, const unsigned char *compare_data, size_t compare_size,
    const M68kAssemblerPolicy *assembler_policy) {
  M68kReproductionCompareResult result;
  m68k_reproduction_compare_init_result(&result);
  if (compare_data == NULL) return result;
  if (backend_name == NULL || strcmp(backend_name, "amiga-hunk") != 0 || backend == NULL ||
      backend->read_buffer == NULL || original_object == NULL || rebuilt_data == NULL) {
    M68kReproductionCompareContext context;
    memset(&context, 0, sizeof(context));
    context.original_bytes = compare_data;
    context.original_size = compare_size;
    context.rebuilt_bytes = rebuilt_data;
    context.rebuilt_size = rebuilt_size;
    context.backend_kind = original_object != NULL ? original_object->platform_backend_kind : M68K_PLATFORM_BACKEND_UNKNOWN;
    context.assembler_policy = assembler_policy;
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
        "\"direct_compare_source_hint_count\":%u,"
        "\"direct_compare_source_hint_overflow\":%s,"
        "\"direct_compare_source_hints\":",
        compare_payload_exact ? "true" : "false",
        compare_relocation_exact ? "true" : "false",
        compare_semantic_exact ? "true" : "false",
        compare_container_oddity ? "true" : "false",
        (unsigned)compare_result.status_id, (unsigned)compare_result.exactness_id,
        (unsigned)compare_result.diagnostic_id, (unsigned)compare_result.issue_group_flags,
        (unsigned)compare_result.first_diff_offset, (unsigned)compare_result.range_count,
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
    *out_error = duplicate_text_local("unknown cpu");
    *out_profile_json = assembler_profile_json_alloc_local(&profile);
    return -1;
  }
  if (backend_name != NULL &&
      (strcmp(backend_name, "amiga-raw") == 0 || strcmp(backend_name, "atari-st-raw") == 0)) {
    if (source_text == NULL) {
      *out_error = duplicate_text_local("raw output backend requires source text");
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
      *out_error = duplicate_text_local("out of memory");
      return -1;
    }
    if (result != 0) {
      message = m68k_diag_first_message(&diagnostics);
      if (message == NULL || message[0] == '\0') message = "raw platform assembler failed";
      free(*out_data);
      *out_data = NULL;
      *out_size = 0U;
      *out_error = duplicate_text_local(message);
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

static PlatformFileTextResult facts_v2_analysis_object_json(const M68kObject *object,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  JsonBuilder builder = {0};
  Arena *scratch_arena = NULL;
  M68kAnalysisPolicy *local_policy = NULL;
  M68kFactsV2Profile *profile = NULL;
  M68kSourceAnalysisIR *analysis = NULL;
  char *base_json = NULL;
  int json_result;
  memset(&result, 0, sizeof(result));
  if (object == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid facts_v2 analysis request");
    return result;
  }
  scratch_arena = arena_create(4096U);
  if (scratch_arena == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return result;
  }
  local_policy = (M68kAnalysisPolicy *)arena_calloc(scratch_arena, 1U, sizeof(*local_policy));
  profile = (M68kFactsV2Profile *)arena_calloc(scratch_arena, 1U, sizeof(*profile));
  analysis = (M68kSourceAnalysisIR *)arena_calloc(scratch_arena, 1U, sizeof(*analysis));
  if (local_policy == NULL || profile == NULL || analysis == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  if (analysis_policy != NULL) *local_policy = *analysis_policy;
  else m68k_analysis_policy_init_default(local_policy);
  if (m68k_facts_v2_collect_source_analysis_profile(object, local_policy, profile, analysis,
      m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "failed building facts_v2 source analysis");
    goto cleanup;
  }
  json_result = source_analysis_to_json(analysis, &base_json, m68k_diag_sink(&result.diagnostics));
  if (json_result == 0) {
    if (json_builder_create(&builder) != 0 ||
        append_analysis_json_with_decompression_profile(&builder, base_json, object, analysis, profile) != 0) {
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
  if (analysis != NULL) m68k_ir_source_analysis_destroy(analysis);
  arena_destroy(scratch_arena);
  return result;
}

PlatformFileTextResult platform_file_facts_v2_analysis_path_json(const char *backend_name, const char *path,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  Arena *scratch_arena = NULL;
  M68kAnalysisPolicy *active_analysis_policy = NULL;
  memset(&result, 0, sizeof(result));
  memset(&object, 0, sizeof(object));
  scratch_arena = arena_create(4096U);
  if (scratch_arena == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return result;
  }
  active_analysis_policy = (M68kAnalysisPolicy *)arena_calloc(scratch_arena, 1U, sizeof(*active_analysis_policy));
  if (active_analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  if (analysis_policy != NULL) *active_analysis_policy = *analysis_policy;
  else m68k_analysis_policy_init_default(active_analysis_policy);
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) goto cleanup;
  if (enrich_policy_from_object_target_info_local(active_analysis_policy, backend, &object, NULL, 0U,
      &result.diagnostics) != 0) {
    goto cleanup;
  }
  enrich_policy_pointer_targets_from_object_local(active_analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, active_analysis_policy))
    goto cleanup;
  result = facts_v2_analysis_object_json(&object, active_analysis_policy);
cleanup:
  m68k_object_destroy(&object);
  arena_destroy(scratch_arena);
  return result;
}

PlatformFileTextResult platform_file_facts_v2_analysis_raw_path_json(const char *platform_name, const char *path,
    uint32_t entry_address, uint8_t has_runtime_load_address, uint32_t runtime_load_address,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  M68kObject object;
  Arena *scratch_arena = NULL;
  M68kAnalysisPolicy *raw_analysis_policy = NULL;
  memset(&result, 0, sizeof(result));
  memset(&object, 0, sizeof(object));
  scratch_arena = arena_create(4096U);
  if (scratch_arena == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return result;
  }
  raw_analysis_policy = (M68kAnalysisPolicy *)arena_calloc(scratch_arena, 1U, sizeof(*raw_analysis_policy));
  if (raw_analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  if (analysis_policy != NULL) *raw_analysis_policy = *analysis_policy;
  else m68k_analysis_policy_init_default(raw_analysis_policy);
  if (load_raw_object_from_path(platform_name, path, &object, m68k_diag_sink(&result.diagnostics)) != 0)
    goto cleanup;
  if (!policy_add_raw_runtime_load_range_local(raw_analysis_policy, &object, has_runtime_load_address,
        runtime_load_address, &result.diagnostics) ||
      !policy_set_raw_entry_address_local(raw_analysis_policy, &object, entry_address,
        has_runtime_load_address, &result.diagnostics))
    goto cleanup;
  enrich_policy_pointer_targets_from_object_local(raw_analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, raw_analysis_policy))
    goto cleanup;
  result = facts_v2_analysis_object_json(&object, raw_analysis_policy);
cleanup:
  m68k_object_destroy(&object);
  arena_destroy(scratch_arena);
  return result;
}

PlatformFileTextResult platform_file_facts_v2_analysis_buffer_json(const char *backend_name,
    const unsigned char *data, size_t size, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  Arena *scratch_arena = NULL;
  M68kAnalysisPolicy *active_analysis_policy = NULL;
  memset(&result, 0, sizeof(result));
  memset(&object, 0, sizeof(object));
  scratch_arena = arena_create(4096U);
  if (scratch_arena == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return result;
  }
  active_analysis_policy = (M68kAnalysisPolicy *)arena_calloc(scratch_arena, 1U, sizeof(*active_analysis_policy));
  if (active_analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  if (analysis_policy != NULL) *active_analysis_policy = *analysis_policy;
  else m68k_analysis_policy_init_default(active_analysis_policy);
  if (load_object_from_buffer(backend, data, size, &object, m68k_diag_sink(&result.diagnostics)) != 0)
    goto cleanup;
  if (enrich_policy_from_object_target_info_local(active_analysis_policy, backend, &object, NULL, 0U,
      &result.diagnostics) != 0) {
    goto cleanup;
  }
  enrich_policy_pointer_targets_from_object_local(active_analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, active_analysis_policy))
    goto cleanup;
  result = facts_v2_analysis_object_json(&object, active_analysis_policy);
cleanup:
  m68k_object_destroy(&object);
  arena_destroy(scratch_arena);
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
  Arena *scratch_arena = NULL;
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  PlatformFileTextResult result;
  m68k_diag_list_reset(&diagnostics);
  scratch_arena = arena_create(4096U);
  analysis_policy = scratch_arena != NULL
    ? (M68kAnalysisPolicy *)arena_calloc(scratch_arena, 1U, sizeof(*analysis_policy))
    : NULL;
  if (analysis_policy == NULL) {
    result.text = NULL;
    memset(&result.diagnostics, 0, sizeof(result.diagnostics));
    platform_file_add_error(&result.diagnostics, "out of memory");
    arena_destroy(scratch_arena);
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, entry_offsets,
        &diagnostics) != 0) {
    result.text = NULL;
    result.diagnostics = diagnostics;
    arena_destroy(scratch_arena);
    return text_result_to_alloc(&result, out_text);
  }
  result = platform_file_facts_v2_analysis_path_json(backend_name, path, analysis_policy);
  arena_destroy(scratch_arena);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_facts_v2_analysis_raw_path_json_alloc(const char *platform_name, const char *path,
    uint32_t entry_address, uint32_t has_runtime_load_address, uint32_t runtime_load_address,
    const char *metadata_path, const char *entry_offsets, char **out_text) {
  Arena *scratch_arena = NULL;
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  PlatformFileTextResult result;
  m68k_diag_list_reset(&diagnostics);
  scratch_arena = arena_create(4096U);
  analysis_policy = scratch_arena != NULL
    ? (M68kAnalysisPolicy *)arena_calloc(scratch_arena, 1U, sizeof(*analysis_policy))
    : NULL;
  if (analysis_policy == NULL) {
    result.text = NULL;
    memset(&result.diagnostics, 0, sizeof(result.diagnostics));
    platform_file_add_error(&result.diagnostics, "out of memory");
    arena_destroy(scratch_arena);
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, platform_name, metadata_path, entry_offsets,
        &diagnostics) != 0) {
    result.text = NULL;
    result.diagnostics = diagnostics;
    arena_destroy(scratch_arena);
    return text_result_to_alloc(&result, out_text);
  }
  result = platform_file_facts_v2_analysis_raw_path_json(platform_name, path, entry_address,
    (uint8_t)(has_runtime_load_address != 0U), runtime_load_address, analysis_policy);
  arena_destroy(scratch_arena);
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
  M68kFactsV2Profile profile;
  Arena *listing_index_arena;
  PlatformListingRowIndex listing_row_index;
  size_t listing_total_rows;
  double source_seconds;
};

static int listing_artifact_set_error(char **out_error, const M68kDiagList *diagnostics,
    const char *fallback) {
  const char *message;
  if (out_error == NULL) return -1;
  message = m68k_diag_first_message(diagnostics);
  if (message == NULL || message[0] == '\0') message = fallback != NULL ? fallback : "listing artifact failed";
  *out_error = duplicate_text_local(message);
  return -1;
}

static PlatformFileListingArtifact *listing_artifact_alloc_base(const char *backend_name, const char *path,
    M68kDiagList *diagnostics) {
  PlatformFileListingArtifact *artifact = (PlatformFileListingArtifact *)calloc(1U, sizeof(*artifact));
  if (artifact == NULL) {
    platform_file_add_error(diagnostics, "out of memory");
    return NULL;
  }
  artifact->backend_name = duplicate_text_local(backend_name);
  artifact->path = duplicate_text_local(path);
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
  if (artifact == NULL) {
    platform_file_add_error(diagnostics, "invalid listing artifact");
    return -1;
  }
  source_start = clock();
  if (m68k_facts_v2_render_asm_source_plan_analysis_profile_alloc(&artifact->object, &artifact->policy, NULL,
      &artifact->source_plan, &artifact->profile, &artifact->source_analysis, 1U, m68k_diag_sink(diagnostics)) != 0) {
    if (!m68k_diag_has_errors(diagnostics))
      platform_file_add_error(diagnostics, "facts_v2 asm source render failed");
    return -1;
  }
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
      json_builder_append(&builder, ",\"backend\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->backend_name) != 0 ||
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
    char **out_error, const M68kAssemblerPolicy *assembler_policy, M68kDiagList *diagnostics) {
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
      compare_size, assembler_policy);
    compare_seconds += elapsed_seconds(phase_start, clock());
  }
  *out_direct_profile_json = facts_v2_direct_rebuild_profile_json_alloc(backend_name, source_bytes,
    size > UINT32_MAX ? UINT32_MAX : (uint32_t)size, 0, NULL, write_buffer_seconds, write_file_seconds,
    compare_size, compare_result, compare_seconds, elapsed_seconds(total_start, clock()), assembler_policy,
    diagnostics);
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
      &assembler_policy, diagnostics);
    if (*out_direct_profile_json == NULL) {
      *out_error = duplicate_text_local("out of memory");
      return -1;
    }
    return 0;
  }
  if (source_profile.asm_source_lossy_numeric_hunk_relocations != 0U) {
    *out_direct_profile_json = facts_v2_direct_rebuild_profile_json_alloc(backend_name,
      source_profile.asm_source_bytes, 0U, 1, "lossy_numeric_hunk_relocations", 0.0, 0.0, 0,
      not_compared, 0.0, 0.0, &assembler_policy, diagnostics);
    if (*out_direct_profile_json == NULL) {
      *out_error = duplicate_text_local("out of memory");
      return -1;
    }
    return 0;
  }
  return facts_v2_direct_write_object_alloc(backend_name, backend, object, output_path,
    source_profile.asm_source_bytes, out_data, out_size, compare_data, compare_size, out_direct_profile_json,
    out_error, &assembler_policy, diagnostics);
}

static int platform_file_facts_v2_direct_rebuild_path_common_alloc(const char *backend_name, const char *path,
    const char *metadata_path, const char *output_path, unsigned char **out_data, size_t *out_size,
    char **out_source_profile_json, char **out_direct_profile_json, char **out_error, int compare_original) {
  Arena *scratch_arena = NULL;
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
  scratch_arena = arena_create(4096U);
  analysis_policy = scratch_arena != NULL
    ? (M68kAnalysisPolicy *)arena_calloc(scratch_arena, 1U, sizeof(*analysis_policy))
    : NULL;
  if (analysis_policy == NULL) {
    *out_error = duplicate_text_local("out of memory");
    arena_destroy(scratch_arena);
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
  arena_destroy(scratch_arena);
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
  Arena *scratch_arena = NULL;
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
  scratch_arena = arena_create(4096U);
  analysis_policy = scratch_arena != NULL
    ? (M68kAnalysisPolicy *)arena_calloc(scratch_arena, 1U, sizeof(*analysis_policy))
    : NULL;
  if (analysis_policy == NULL) {
    *out_error = duplicate_text_local("out of memory");
    arena_destroy(scratch_arena);
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
  arena_destroy(scratch_arena);
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
    size_t original_size, const unsigned char *rebuilt_data, size_t rebuilt_size, char **out_direct_profile_json,
    char **out_error, M68kDiagList *diagnostics) {
  M68kAssemblerPolicy assembler_policy;
  M68kReproductionCompareResult compare_result;
  clock_t compare_start;
  double compare_seconds;
  if (out_direct_profile_json == NULL || out_error == NULL) return -1;
  *out_direct_profile_json = NULL;
  *out_error = NULL;
  if (backend == NULL || object == NULL || original_data == NULL || rebuilt_data == NULL) {
    *out_error = duplicate_text_local("invalid reproduction compare input");
    return -1;
  }
  m68k_assembler_policy_derive_preservation(object, &assembler_policy);
  compare_start = clock();
  compare_result = facts_v2_direct_compare_result(backend_name, backend, object, rebuilt_data, rebuilt_size,
    original_data, original_size, &assembler_policy);
  compare_seconds = elapsed_seconds(compare_start, clock());
  *out_direct_profile_json = facts_v2_direct_rebuild_profile_json_alloc(backend_name, 0U,
    rebuilt_size > UINT32_MAX ? UINT32_MAX : (uint32_t)rebuilt_size, 0, NULL, 0.0, 0.0, original_size,
    compare_result, compare_seconds, compare_seconds, &assembler_policy, diagnostics);
  if (*out_direct_profile_json == NULL) {
    *out_error = duplicate_text_local("out of memory");
    return -1;
  }
  return 0;
}

int platform_file_reproduction_compare_path_bytes_profile_alloc(const char *backend_name,
    const char *path, const char *metadata_path, const unsigned char *rebuilt_data, size_t rebuilt_size,
    char **out_direct_profile_json, char **out_error) {
  Arena *scratch_arena = NULL;
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  unsigned char *original_data = NULL;
  size_t original_size = 0U;
  int result = -1;
  if (out_direct_profile_json == NULL || out_error == NULL) return -1;
  *out_direct_profile_json = NULL;
  *out_error = NULL;
  m68k_diag_list_reset(&diagnostics);
  memset(&object, 0, sizeof(object));
  scratch_arena = arena_create(4096U);
  analysis_policy = scratch_arena != NULL
    ? (M68kAnalysisPolicy *)arena_calloc(scratch_arena, 1U, sizeof(*analysis_policy))
    : NULL;
  if (analysis_policy == NULL) {
    *out_error = duplicate_text_local("out of memory");
    arena_destroy(scratch_arena);
    return -1;
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL, &diagnostics) != 0)
    goto cleanup;
  if (read_file_to_buffer(path, &original_data, &original_size, m68k_diag_sink(&diagnostics)) != 0) goto cleanup;
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&diagnostics)) != 0) goto cleanup;
  result = platform_file_reproduction_compare_object_common_alloc(backend_name, backend, &object, original_data,
    original_size, rebuilt_data, rebuilt_size, out_direct_profile_json, out_error, &diagnostics);

cleanup:
  if (result != 0 && *out_error == NULL) {
    const char *message = m68k_diag_first_message(&diagnostics);
    *out_error = duplicate_text_local(message != NULL ? message : "reproduction compare failed");
  }
  free(original_data);
  m68k_object_destroy(&object);
  arena_destroy(scratch_arena);
  return result;
}

int platform_file_reproduction_compare_buffer_bytes_profile_alloc(const char *backend_name,
    const unsigned char *data, size_t size, const char *metadata_path, const char *display_path,
    const unsigned char *rebuilt_data, size_t rebuilt_size, char **out_direct_profile_json, char **out_error) {
  Arena *scratch_arena = NULL;
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  int result = -1;
  (void)display_path;
  if (out_direct_profile_json == NULL || out_error == NULL) return -1;
  *out_direct_profile_json = NULL;
  *out_error = NULL;
  m68k_diag_list_reset(&diagnostics);
  memset(&object, 0, sizeof(object));
  scratch_arena = arena_create(4096U);
  analysis_policy = scratch_arena != NULL
    ? (M68kAnalysisPolicy *)arena_calloc(scratch_arena, 1U, sizeof(*analysis_policy))
    : NULL;
  if (analysis_policy == NULL) {
    *out_error = duplicate_text_local("out of memory");
    arena_destroy(scratch_arena);
    return -1;
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL, &diagnostics) != 0)
    goto cleanup;
  if (load_object_from_buffer(backend, data, size, &object, m68k_diag_sink(&diagnostics)) != 0) goto cleanup;
  result = platform_file_reproduction_compare_object_common_alloc(backend_name, backend, &object, data, size,
    rebuilt_data, rebuilt_size, out_direct_profile_json, out_error, &diagnostics);

cleanup:
  if (result != 0 && *out_error == NULL) {
    const char *message = m68k_diag_first_message(&diagnostics);
    *out_error = duplicate_text_local(message != NULL ? message : "reproduction compare failed");
  }
  m68k_object_destroy(&object);
  arena_destroy(scratch_arena);
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
    if (out_error != NULL) *out_error = duplicate_text_local("invalid listing artifact request");
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
    if (out_error != NULL) *out_error = duplicate_text_local("invalid listing artifact request");
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
  if (json_builder_append(&builder, ",\"profile\":{\"generation\":\"facts_v2_listing_artifact_window\","
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
      json_builder_append(&builder, "},\"profile\":{\"generation\":\"facts_v2_listing_artifact_summary\","
        "\"backend\":") != 0 ||
      json_builder_append_json_string(&builder, artifact->backend_name) != 0 ||
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
  memset(&result, 0, sizeof(result));
  if (out_text == NULL) return -1;
  *out_text = NULL;
  if (artifact == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid listing artifact");
    return text_result_to_alloc(&result, out_text);
  }
  analysis_start = clock();
  if (source_analysis_to_json(&artifact->source_analysis, &analysis_json, m68k_diag_sink(&result.diagnostics)) != 0) {
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
      append_analysis_json_with_decompression(&builder, analysis_json, &artifact->object,
        &artifact->source_analysis) != 0) {
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
      &event_count, event_id, output_path, &materialized_event, &diagnostics) != 0) {
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
      &event_count, event_id, output_path, &materialized_event, &diagnostics) != 0) {
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
