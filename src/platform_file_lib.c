#include "platform_file_lib.h"
#include "platform_file_internal.h"
#include "json_builder.h"
#include "m68k_assembler.h"
#include "m68k_backend.h"
#include "m68k_disassembler.h"
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
static int read_file_to_buffer(const char *path, unsigned char **out_data, size_t *out_size,
    M68kDiagSink diagnostics);
static int load_object_from_path(const M68kBackend *backend, const char *path, M68kObject *object,
    M68kDiagSink diagnostics);
static int load_raw_object_from_path(const char *platform_name, const char *path, M68kObject *object,
    M68kDiagSink diagnostics);

static uint8_t basic_listing_max_cpu(const M68kAnalysisPolicy *policy) {
  if (policy == NULL || policy->max_cpu > M68K_ASM_CPU_68060) return M68K_ASM_CPU_68060;
  return policy->max_cpu;
}

static void split_basic_disasm_text(const char *text, char *opcode, size_t opcode_size,
    char *operand, size_t operand_size) {
  const char *cursor = text;
  size_t opcode_len;
  if (opcode_size != 0U) opcode[0] = '\0';
  if (operand_size != 0U) operand[0] = '\0';
  if (text == NULL) return;
  while (*cursor == ' ' || *cursor == '\t') ++cursor;
  opcode_len = strcspn(cursor, " \t\r\n");
  if (opcode_size != 0U) {
    size_t copy_len = opcode_len < opcode_size - 1U ? opcode_len : opcode_size - 1U;
    memcpy(opcode, cursor, copy_len);
    opcode[copy_len] = '\0';
  }
  cursor += opcode_len;
  while (*cursor == ' ' || *cursor == '\t') ++cursor;
  if (operand_size != 0U) {
    size_t operand_len = strcspn(cursor, "\r\n");
    size_t copy_len = operand_len < operand_size - 1U ? operand_len : operand_size - 1U;
    memcpy(operand, cursor, copy_len);
    operand[copy_len] = '\0';
  }
}

static int append_basic_listing_row(JsonBuilder *builder, size_t *row_index, int *need_comma,
    const char *kind, int section_index, int has_addr, uint32_t addr, const char *text,
    const uint8_t *source_bytes, size_t source_byte_count, const char *label, const char *opcode,
    const char *operand) {
  static const char hex[] = "0123456789abcdef";
  char stable_key[96];
  size_t byte_index;
  if (*need_comma && json_builder_append(builder, ",") != 0) return -1;
  *need_comma = 1;
  if (has_addr)
    snprintf(stable_key, sizeof(stable_key), "s%d:%08X:%s:%u", section_index, addr, kind, (unsigned)*row_index);
  else
    snprintf(stable_key, sizeof(stable_key), "global:%s:%u", kind, (unsigned)*row_index);
  if (json_builder_append(builder, "{\"row_id\":\"b:") != 0 ||
      json_builder_appendf(builder, "%u", (unsigned)*row_index) != 0 ||
      json_builder_append(builder, "\",\"kind\":") != 0 ||
      json_builder_append_json_string(builder, kind) != 0 ||
      json_builder_append(builder, ",\"text\":") != 0 ||
      json_builder_append_json_string(builder, text != NULL ? text : "") != 0 ||
      json_builder_append(builder, ",\"bytes\":") != 0)
    return -1;
  if (source_bytes != NULL && source_byte_count != 0U) {
    size_t count = source_byte_count < M68K_STATEMENT_SOURCE_BYTES_MAX ? source_byte_count : M68K_STATEMENT_SOURCE_BYTES_MAX;
    if (json_builder_append_char(builder, '"') != 0) return -1;
    for (byte_index = 0U; byte_index < count; ++byte_index) {
      if (json_builder_append_char(builder, hex[source_bytes[byte_index] >> 4]) != 0 ||
          json_builder_append_char(builder, hex[source_bytes[byte_index] & 0x0F]) != 0)
        return -1;
    }
    if (json_builder_append_char(builder, '"') != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  if (json_builder_append(builder, ",\"stable_key\":") != 0 ||
      json_builder_append_json_string(builder, stable_key) != 0 ||
      json_builder_append(builder, ",\"analysis_generation\":\"basic\",\"addr\":") != 0)
    return -1;
  if (has_addr) {
    if (json_builder_appendf(builder, "%u", (unsigned)addr) != 0 ||
        json_builder_append(builder, ",\"entity_addr\":") != 0 ||
        json_builder_appendf(builder, "%u", (unsigned)addr) != 0)
      return -1;
  } else if (json_builder_append(builder, "null,\"entity_addr\":null") != 0) {
    return -1;
  }
  if (json_builder_append(builder, ",\"label\":") != 0) return -1;
  if (label != NULL && label[0] != '\0') {
    if (json_builder_append_json_string(builder, label) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) {
    return -1;
  }
  if (json_builder_append(builder, ",\"opcode_or_directive\":") != 0) return -1;
  if (opcode != NULL && opcode[0] != '\0') {
    if (json_builder_append_json_string(builder, opcode) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) {
    return -1;
  }
  if (json_builder_append(builder, ",\"operand_text\":") != 0 ||
      json_builder_append_json_string(builder, operand != NULL ? operand : "") != 0 ||
      json_builder_append(builder, ",\"comment_text\":\"\",\"source_context\":") != 0)
    return -1;
  if (section_index >= 0) {
    if (json_builder_appendf(builder, "{\"kind\":\"basic-section\",\"hunk_index\":%d}", section_index) != 0)
      return -1;
  } else if (json_builder_append(builder, "{\"section\":\"c-backend\"}") != 0) {
    return -1;
  }
  if (json_builder_append(builder, ",\"structured_data\":null}") != 0) return -1;
  ++(*row_index);
  return 0;
}

static const char *basic_policy_label_at(const M68kAnalysisPolicy *policy, size_t section_index, uint32_t offset) {
  size_t index;
  if (policy == NULL) return NULL;
  for (index = 0U; index < policy->named_label_count; ++index) {
    const M68kAnalysisNamedLabel *label = &policy->named_labels[index];
    if (label->offset == offset && label->name[0] != '\0' &&
        (!label->has_section_index || label->section_index == section_index))
      return label->name;
  }
  return NULL;
}

static int basic_policy_has_entry_at(const M68kAnalysisPolicy *policy, size_t section_index, uint32_t offset) {
  size_t index;
  if (policy == NULL) return 0;
  if (policy->has_entry_offset && offset == policy->entry_offset) return 1;
  for (index = 0U; index < policy->entry_point_count; ++index) {
    const M68kAnalysisEntryPoint *entry = &policy->entry_points[index];
    if (entry->offset == offset && (!entry->has_section_index || entry->section_index == section_index))
      return 1;
  }
  return 0;
}

static int basic_listing_rows_object_json(const M68kObject *object, const M68kAnalysisPolicy *analysis_policy,
    char **out_json, M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  size_t row_index = 0U;
  int need_comma = 0;
  size_t section_index;
  if (object == NULL || out_json == NULL) return -1;
  if (json_builder_create(&builder) != 0 || json_builder_append(&builder, "{\"rows\":[") != 0) goto oom;
  for (section_index = 0U; section_index < object->section_count; ++section_index) {
    const M68kSection *section = &object->sections[section_index];
    char line[256];
    uint32_t offset = 0U;
    const char *section_kind = section->kind == M68K_SECTION_BSS ? "bss" :
      (section->kind == M68K_SECTION_DATA ? "data" : "code");
    snprintf(line, sizeof(line), "    SECTION %s,%s\n",
      (section->name != NULL && section->name[0] != '\0') ? section->name : "section", section_kind);
    if (append_basic_listing_row(&builder, &row_index, &need_comma, "directive", (int)section_index, 0U, 0U,
        line, NULL, 0U, NULL, "SECTION", "") != 0)
      goto oom;
    {
      const char *policy_label = basic_policy_label_at(analysis_policy, section_index, 0U);
      if (policy_label != NULL)
        snprintf(line, sizeof(line), "%s:\n", policy_label);
      else
        snprintf(line, sizeof(line), "h%u_0000:\n", (unsigned)section_index);
    }
    if (append_basic_listing_row(&builder, &row_index, &need_comma, "label", (int)section_index, 1U, 0U,
        line, NULL, 0U, line, NULL, "") != 0)
      goto oom;
    if (section->kind == M68K_SECTION_BSS) {
      snprintf(line, sizeof(line), "    DS.B    $%x\n", (unsigned)section->size);
      if (append_basic_listing_row(&builder, &row_index, &need_comma, "directive", (int)section_index, 1U, 0U,
          line, NULL, 0U, NULL, "DS.B", "") != 0)
        goto oom;
      continue;
    }
    while (offset < section->data_size) {
      const char *policy_label = basic_policy_label_at(analysis_policy, section_index, offset);
      if (offset != 0U && (policy_label != NULL || basic_policy_has_entry_at(analysis_policy, section_index, offset))) {
        if (policy_label != NULL)
          snprintf(line, sizeof(line), "%s:\n", policy_label);
        else
          snprintf(line, sizeof(line), "h%u_%04x:\n", (unsigned)section_index, (unsigned)offset);
        if (append_basic_listing_row(&builder, &row_index, &need_comma, "label", (int)section_index, 1U, offset,
            line, NULL, 0U, line, NULL, "") != 0)
          goto oom;
      }
      if (section->kind == M68K_SECTION_CODE && offset + 2U <= section->data_size) {
        M68kDiagList instruction_diagnostics;
        M68kDisasmResult disasm;
        char opcode[64];
        char operand[160];
        m68k_diag_list_reset(&instruction_diagnostics);
        disasm = m68k_disassemble_one_for_cpu(section->data + offset, section->data_size - offset,
          basic_listing_max_cpu(analysis_policy), m68k_diag_sink(&instruction_diagnostics));
        if (!m68k_diag_has_errors(&instruction_diagnostics) && disasm.byte_count != 0U) {
          split_basic_disasm_text(disasm.text, opcode, sizeof(opcode), operand, sizeof(operand));
          snprintf(line, sizeof(line), "    %s\n", disasm.text);
          if (append_basic_listing_row(&builder, &row_index, &need_comma, "instruction", (int)section_index, 1U,
              offset, line, section->data + offset, disasm.byte_count, NULL, opcode, operand) != 0)
            goto oom;
          offset += (uint32_t)disasm.byte_count;
          continue;
        }
      }
      snprintf(line, sizeof(line), "    DC.B    $%02x\n", (unsigned)section->data[offset]);
      if (append_basic_listing_row(&builder, &row_index, &need_comma, "data", (int)section_index, 1U, offset,
          line, NULL, 0U, NULL, "DC.B", "") != 0)
        goto oom;
      ++offset;
    }
  }
  if (json_builder_append(&builder, "]}") != 0) goto oom;
  *out_json = json_builder_build(&builder);
  if (*out_json == NULL) goto oom;
  json_builder_destroy(&builder);
  return 0;
oom:
  json_builder_destroy(&builder);
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
  return -1;
}

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

typedef struct PlatformFilePolicyInclude {
  char path[128];
} PlatformFilePolicyInclude;

static int policy_include_add_local(PlatformFilePolicyInclude *includes, size_t *inout_count, size_t capacity,
    const char *path) {
  size_t index;
  if (includes == NULL || inout_count == NULL || path == NULL || path[0] == '\0') return 1;
  for (index = 0U; index < *inout_count; ++index) {
    if (strcmp(includes[index].path, path) == 0) return 1;
  }
  if (*inout_count >= capacity) return 0;
  snprintf(includes[*inout_count].path, sizeof(includes[*inout_count].path), "%s", path);
  ++(*inout_count);
  return 1;
}

static int policy_include_compare_local(const void *left, const void *right) {
  const PlatformFilePolicyInclude *left_include = (const PlatformFilePolicyInclude *)left;
  const PlatformFilePolicyInclude *right_include = (const PlatformFilePolicyInclude *)right;
  return strcmp(left_include->path, right_include->path);
}

static int policy_include_add_symbol_local(PlatformFilePolicyInclude *includes, size_t *inout_count, size_t capacity,
    const char *symbol_name) {
  return policy_include_add_local(includes, inout_count, capacity, amiga_os_find_symbol_include(symbol_name));
}

static int policy_include_add_struct_local(PlatformFilePolicyInclude *includes, size_t *inout_count, size_t capacity,
    const char *struct_name) {
  uint16_t struct_id;
  int16_t offset;
  if (struct_name == NULL || struct_name[0] == '\0') return 1;
  struct_id = amiga_os_name_id(M68K_PLATFORM_NAME_STRUCT, struct_name);
  if (amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id) == NULL) return 1;
  for (offset = 0; offset <= 8191; ++offset) {
    const AmigaOsStructFieldInfo *field = amiga_os_find_struct_field_by_struct_id(struct_id, offset);
    const char *field_name;
    if (field == NULL) continue;
    field_name = amiga_os_name(M68K_PLATFORM_NAME_FIELD, field->field_id);
    if (field_name != NULL && !policy_include_add_symbol_local(includes, inout_count, capacity, field_name)) return 0;
    return 1;
  }
  return 1;
}

static int policy_collect_needed_includes_local(const M68kAnalysisPolicy *policy, PlatformFilePolicyInclude *includes,
    size_t *out_count, size_t capacity) {
  uint16_t index;
  if (out_count == NULL) return 0;
  *out_count = 0U;
  if (policy == NULL) return 1;
  for (index = 0U; index < policy->structured_data_item_count && index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT;
       ++index) {
    const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    if (!policy_include_add_symbol_local(includes, out_count, capacity, item->field_name) ||
        !policy_include_add_symbol_local(includes, out_count, capacity, item->constant_name) ||
        !policy_include_add_struct_local(includes, out_count, capacity, item->struct_name) ||
        !policy_include_add_struct_local(includes, out_count, capacity, item->pointer_struct)) {
      return 0;
    }
  }
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    if (!policy_include_add_struct_local(includes, out_count, capacity, seed->type_name)) return 0;
  }
  return 1;
}

static const char *line_after_local(const char *line_start) {
  const char *newline;
  if (line_start == NULL) return NULL;
  newline = strchr(line_start, '\n');
  return newline == NULL ? line_start + strlen(line_start) : newline + 1;
}

static int rendered_include_line_path_local(const char *line_start, char *out_path, size_t out_path_size) {
  const char *cursor = line_start;
  const char *path_start;
  const char *path_end;
  size_t path_size;
  if (line_start == NULL || out_path == NULL || out_path_size == 0U) return 0;
  out_path[0] = '\0';
  while (*cursor == ' ' || *cursor == '\t') ++cursor;
  if (strncmp(cursor, "INCLUDE", 7U) != 0) return 0;
  cursor += 7U;
  while (*cursor == ' ' || *cursor == '\t') ++cursor;
  if (*cursor != '"') return 0;
  path_start = cursor + 1U;
  path_end = strchr(path_start, '"');
  if (path_end == NULL) return 0;
  path_size = (size_t)(path_end - path_start);
  if (path_size == 0U || path_size >= out_path_size) return 0;
  memcpy(out_path, path_start, path_size);
  out_path[path_size] = '\0';
  return 1;
}

static int rendered_blank_line_local(const char *line_start) {
  const char *cursor = line_start;
  if (cursor == NULL) return 0;
  while (*cursor == ' ' || *cursor == '\t' || *cursor == '\r') ++cursor;
  return *cursor == '\n' || *cursor == '\0';
}

static int merge_policy_includes_into_rendered_text_local(PlatformFileTextResult *rendered,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFilePolicyInclude includes[32];
  size_t include_count = 0U;
  JsonBuilder builder = {0};
  char *text;
  const char *body_start;
  const char *cursor;
  const char *prefix_start;
  size_t index;
  int had_include_block = 0;
  if (rendered == NULL || rendered->text == NULL) return 0;
  if (!policy_collect_needed_includes_local(analysis_policy, includes, &include_count,
        sizeof(includes) / sizeof(includes[0]))) {
    platform_file_add_error(&rendered->diagnostics, "too many policy include dependencies");
    return -1;
  }
  prefix_start = rendered->text;
  cursor = rendered->text;
  if (strncmp(cursor, "; Minimum OS version:", 21U) == 0) cursor = line_after_local(cursor);
  body_start = cursor;
  while (*cursor != '\0') {
    char path[128];
    const char *next = line_after_local(cursor);
    if (rendered_include_line_path_local(cursor, path, sizeof(path))) {
      if (!policy_include_add_local(includes, &include_count, sizeof(includes) / sizeof(includes[0]), path)) {
        platform_file_add_error(&rendered->diagnostics, "too many policy include dependencies");
        return -1;
      }
      cursor = next;
      body_start = cursor;
      had_include_block = 1;
      continue;
    }
    if (had_include_block && rendered_blank_line_local(cursor)) {
      cursor = next;
      body_start = cursor;
      continue;
    }
    break;
  }
  if (include_count == 0U && !had_include_block) return 0;
  qsort(includes, include_count, sizeof(includes[0]), policy_include_compare_local);
  if (json_builder_create(&builder) != 0) {
    platform_file_add_error(&rendered->diagnostics, "out of memory");
    return -1;
  }
  if (body_start != rendered->text && prefix_start != cursor && strncmp(prefix_start, "; Minimum OS version:", 21U) == 0) {
    const char *prefix_end = line_after_local(prefix_start);
    if (json_builder_appendf(&builder, "%.*s", (int)(prefix_end - prefix_start), prefix_start) != 0) goto oom;
  }
  for (index = 0U; index < include_count; ++index) {
    if (json_builder_appendf(&builder, "INCLUDE \"%s\"\n", includes[index].path) != 0) goto oom;
  }
  if (include_count != 0U && json_builder_append(&builder, "\n") != 0) goto oom;
  if (json_builder_append(&builder, body_start) != 0) goto oom;
  text = json_builder_build(&builder);
  if (text == NULL) goto oom;
  json_builder_destroy(&builder);
  platform_file_free_text(rendered->text);
  rendered->text = text;
  return 0;

oom:
  json_builder_destroy(&builder);
  platform_file_add_error(&rendered->diagnostics, "out of memory");
  return -1;
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

static int run_result_to_alloc(PlatformFileRunResult *result, char **out_text) {
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
    platform_file_run_metrics_free(&result->metrics);
    m68k_ir_source_file_destroy(&result->source_file);
    return -1;
  }
  *out_text = result->text;
  result->text = NULL;
  platform_file_run_metrics_free(&result->metrics);
  m68k_ir_source_file_destroy(&result->source_file);
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

static M68kAnalysisPolicy *analysis_policy_heap_copy_local(const M68kAnalysisPolicy *policy) {
  M68kAnalysisPolicy *copy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*copy));
  if (copy == NULL) return NULL;
  if (policy != NULL) *copy = *policy;
  else m68k_analysis_policy_init_default(copy);
  return copy;
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
  for (cursor = start; cursor < end; ++cursor) {
    if (*cursor != '"') continue;
    if ((size_t)(end - cursor) < key_len + 2U) return NULL;
    if (memcmp(cursor + 1, key, key_len) != 0 || cursor[key_len + 1U] != '"') continue;
    cursor += key_len + 2U;
    cursor = json_skip_ws_local(cursor, end);
    if (cursor < end && *cursor == ':') return cursor + 1;
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
  uint32_t bootcode_offset = 0U;
  int has_bootcode_offset = 0;
  if (object_start == NULL) return 1;
  if (!json_number_field_local(object_start, object_end, "bootcode_offset", &bootcode_offset, &has_bootcode_offset))
    return 0;
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

static int append_metadata_resident_vector_entrypoints_local(const char *autoinit_start, const char *autoinit_end,
    M68kAnalysisPolicy *policy, uint32_t hunk, const char *target_type, const char *library_name,
    uint32_t library_version, uint32_t *inout_first_code_offset) {
  const char *array_end = NULL;
  const char *cursor = json_find_array_field_in_object_local(autoinit_start, autoinit_end, "vector_offsets", &array_end);
  uint32_t vector_index = 0U;
  uint32_t next_private_ordinal = 1U;
  if (cursor == NULL) return 1;
  while (cursor < array_end) {
    uint32_t offset = 0U;
    char label_name[64];
    label_name[0] = '\0';
    cursor = json_skip_ws_local(cursor, array_end);
    if (cursor < array_end && *cursor == ',') {
      ++cursor;
      continue;
    }
    if (cursor >= array_end) break;
    {
      const char *number_start = cursor;
      while (cursor < array_end && ((*cursor >= '0' && *cursor <= '9') || *cursor == '+' || *cursor == '-')) ++cursor;
      if (cursor == number_start) break;
      {
        char number_text[32];
        size_t length = (size_t)(cursor - number_start);
        if (length >= sizeof(number_text)) return 0;
        memcpy(number_text, number_start, length);
        number_text[length] = '\0';
        if (!parse_u32_arg_local(number_text, &offset)) return 0;
      }
    }
    if (inout_first_code_offset != NULL &&
        (*inout_first_code_offset == UINT32_MAX || offset < *inout_first_code_offset)) {
      *inout_first_code_offset = offset;
    }
    if (!policy_add_entry_point_local(policy, hunk, offset)) return 0;
    if (library_name != NULL && library_name[0] != '\0') {
      const char *base_struct_name = amiga_os_find_library_base_struct_name(library_name);
      if (base_struct_name == NULL || base_struct_name[0] == '\0') base_struct_name = "LIB";
      if (!policy_add_register_seed_local(policy, hunk, offset, "A6", "library_base", library_name, base_struct_name, ""))
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
        symbol = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, prefix->symbol_id);
        make_policy_symbol_label_local(label_name, sizeof(label_name), symbol);
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
              !policy_add_entry_comment_local(policy, hunk, offset, declaration)) {
            return 0;
          }
          if (!policy_add_amiga_lvo_argument_seeds_local(policy, hunk, offset, vector)) return 0;
        } else {
          char private_stem[48];
          char library_stem[48];
          size_t stem_len;
          snprintf(library_stem, sizeof(library_stem), "%s", library_name);
          stem_len = strlen(library_stem);
          if (stem_len > 8U && strcmp(library_stem + stem_len - 8U, ".library") == 0) library_stem[stem_len - 8U] = '\0';
          make_policy_symbol_label_local(private_stem, sizeof(private_stem), library_stem);
          snprintf(label_name, sizeof(label_name), "%s_private_%u", private_stem[0] != '\0' ? private_stem : "resident",
            (unsigned)next_private_ordinal++);
        }
      }
      if (label_name[0] != '\0' && !policy_add_named_label_local(policy, hunk, offset, label_name)) return 0;
    }
    ++vector_index;
  }
  return 1;
}

static int append_metadata_resident_autoinit_structure_local(const char *autoinit_start, const char *autoinit_end,
    M68kAnalysisPolicy *policy, uint32_t hunk, const char *target_type, const char *library_name,
    uint32_t library_version) {
  uint32_t payload_offset = 0U;
  uint32_t vectors_offset = 0U;
  uint32_t init_struct_offset = 0U;
  uint32_t init_func_offset = 0U;
  uint32_t first_code_offset = UINT32_MAX;
  int has_payload_offset = 0;
  int has_vectors_offset = 0;
  int has_init_struct_offset = 0;
  int has_init_func_offset = 0;
  if (!json_number_field_local(autoinit_start, autoinit_end, "payload_offset", &payload_offset, &has_payload_offset) ||
      !json_number_field_local(autoinit_start, autoinit_end, "vectors_offset", &vectors_offset, &has_vectors_offset) ||
      !json_number_field_local(autoinit_start, autoinit_end, "init_struct_offset", &init_struct_offset,
        &has_init_struct_offset) ||
      !json_number_field_local(autoinit_start, autoinit_end, "init_func_offset", &init_func_offset,
        &has_init_func_offset)) {
    return 0;
  }
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
  if (has_vectors_offset && has_init_struct_offset && init_struct_offset > vectors_offset) {
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
  return 0;
}

static int append_metadata_amiga_policy_text_local(const char *text, M68kAnalysisPolicy *policy,
    M68kDiagSink diagnostics) {
  if (!append_metadata_bootblock_structure_local(text, policy)) {
    platform_file_add_error(diagnostics.list, "failed parsing target metadata bootblock structure");
    return -1;
  }
  if (!append_metadata_resident_structure_local(text, policy)) {
    platform_file_add_error(diagnostics.list, "failed parsing target metadata resident structure");
    return -1;
  }
  return 0;
}

static int platform_name_uses_amiga_metadata_policy_local(const char *platform_name) {
  return platform_name != NULL &&
         (strcmp(platform_name, "amiga-hunk") == 0 || strcmp(platform_name, "amiga-raw") == 0);
}

static int metadata_text_has_amiga_policy_local(const char *text) {
  const char *resident_end;
  const char *text_end;
  char target_type[32];
  if (text == NULL) return 0;
  if (json_find_object_field_local(text, "resident", &resident_end) != NULL) return 1;
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

static int configure_render_policy_for_alloc(M68kRenderPolicy *policy, const char *syntax,
    M68kDiagList *diagnostics) {
  uint8_t syntax_mode = M68K_IR_SYNTAX_CANONICAL;
  if (syntax != NULL && syntax[0] != '\0' && !m68k_ir_parse_syntax_mode_name(syntax, &syntax_mode)) {
    platform_file_add_error(diagnostics, "unknown syntax");
    return -1;
  }
  m68k_render_policy_init_for_syntax(policy, syntax_mode);
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
  return 1;
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
  if (platform_name_uses_amiga_metadata_policy_local(backend_name)) {
    M68kDiagList ignored_diagnostics;
    const char *resident_end = NULL;
    if (!(json_find_object_field_local(inspect_json, "resident", &resident_end) != NULL &&
          policy_has_resident_struct_policy_local(policy))) {
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
        "\"analysis_policy\":{\"max_cpu\":%u,\"entry_point_count\":%u,\"register_seed_count\":%u,"
        "\"structured_data_item_count\":%u,\"named_label_count\":%u,\"entry_comment_count\":%u",
        (unsigned)policy->max_cpu, (unsigned)policy->entry_point_count, (unsigned)policy->register_seed_count,
        (unsigned)policy->structured_data_item_count, (unsigned)policy->named_label_count,
        (unsigned)policy->entry_comment_count) != 0)
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
    analysis_policy->has_entry_offset = 1U;
    analysis_policy->entry_offset = raw_entry_offset;
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
void platform_file_free_bytes(unsigned char *data) { free(data); }

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
  M68kAnalysisPolicy *active_analysis_policy;
  const M68kRenderPolicy *active_policy = resolve_render_policy(policy, &default_policy);
  int populate_result;
  memset(&result, 0, sizeof(result));
  active_analysis_policy = analysis_policy_heap_copy_local(analysis_policy);
  if (active_analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return result;
  }
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(active_analysis_policy);
    return result;
  }
  if (enrich_policy_from_object_target_info_local(active_analysis_policy, backend, &object, NULL, 0U,
      &result.diagnostics) != 0) {
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    return result;
  }
  enrich_policy_pointer_targets_from_object_local(active_analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, active_analysis_policy)) {
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    return result;
  }
  populate_result = populate_source_ir_from_object(backend, &object, active_policy, active_analysis_policy,
    &result.source_file, m68k_diag_sink(&result.diagnostics));
  m68k_object_destroy(&object);
  free(active_analysis_policy);
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
  M68kAnalysisPolicy *active_analysis_policy;
  const M68kRenderPolicy *active_policy = resolve_render_policy(policy, &default_policy);
  clock_t total_start, total_end, render_start, render_end;
  int populate_result;
  PlatformFileTextResult rendered;
  memset(&result, 0, sizeof(result));
  platform_file_run_metrics_init(&result.metrics);
  active_analysis_policy = analysis_policy_heap_copy_local(analysis_policy);
  if (active_analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    platform_file_run_metrics_free(&result.metrics);
    return result;
  }
  total_start = clock();
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(active_analysis_policy);
    platform_file_run_metrics_free(&result.metrics);
    return result;
  }
  if (enrich_policy_from_object_target_info_local(active_analysis_policy, backend, &object, NULL, 0U,
      &result.diagnostics) != 0) {
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    platform_file_run_metrics_free(&result.metrics);
    return result;
  }
  enrich_policy_pointer_targets_from_object_local(active_analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, active_analysis_policy)) {
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    platform_file_run_metrics_free(&result.metrics);
    return result;
  }
  populate_result = populate_source_ir_from_object_with_metrics(backend, &object, active_policy, active_analysis_policy,
    &result.source_file, &result.metrics, NULL, m68k_diag_sink(&result.diagnostics));
  if (populate_result != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics)) platform_file_add_error(&result.diagnostics, "failed building source ir");
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    platform_file_run_metrics_free(&result.metrics);
    return result;
  }
  render_start = clock();
  rendered = platform_file_render_ir_with_policy(&result.source_file, active_policy);
  if (!m68k_diag_has_errors(&rendered.diagnostics))
    (void)merge_policy_includes_into_rendered_text_local(&rendered, active_analysis_policy);
  render_end = clock();
  m68k_object_destroy(&object);
  if (m68k_diag_has_errors(&rendered.diagnostics)) {
    result.diagnostics = rendered.diagnostics;
    platform_file_source_ir_free(&result.source_file);
    free(active_analysis_policy);
    platform_file_run_metrics_free(&result.metrics);
    return result;
  }
  result.metrics.render_seconds = elapsed_seconds(render_start, render_end);
  result.metrics.text_bytes = strlen(rendered.text);
  total_end = clock();
  result.metrics.total_seconds = elapsed_seconds(total_start, total_end);
  result.text = rendered.text;
  free(active_analysis_policy);
  return result;
}

PlatformFileRunResult platform_file_run_raw_path_with_policy(const char *platform_name, const char *path,
    uint32_t entry_offset, const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileRunResult result;
  M68kObject object;
  const M68kBackend *backend = raw_platform_backend(platform_name);
  M68kRenderPolicy default_policy;
  M68kAnalysisPolicy *raw_analysis_policy;
  const M68kRenderPolicy *active_policy = resolve_render_policy(policy, &default_policy);
  clock_t total_start, total_end, render_start, render_end;
  int populate_result;
  PlatformFileTextResult rendered;
  memset(&result, 0, sizeof(result));
  platform_file_run_metrics_init(&result.metrics);
  raw_analysis_policy = analysis_policy_heap_copy_local(analysis_policy);
  if (raw_analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    platform_file_run_metrics_free(&result.metrics);
    return result;
  }
  raw_analysis_policy->has_entry_offset = 1U;
  raw_analysis_policy->entry_offset = entry_offset;
  total_start = clock();
  if (load_raw_object_from_path(platform_name, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(raw_analysis_policy);
    platform_file_run_metrics_free(&result.metrics);
    return result;
  }
  enrich_policy_pointer_targets_from_object_local(raw_analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, raw_analysis_policy)) {
    m68k_object_destroy(&object);
    free(raw_analysis_policy);
    platform_file_run_metrics_free(&result.metrics);
    return result;
  }
  populate_result = populate_source_ir_from_object_with_metrics(backend, &object, active_policy, raw_analysis_policy,
    &result.source_file, &result.metrics, NULL, m68k_diag_sink(&result.diagnostics));
  if (populate_result != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "failed building source ir");
    m68k_object_destroy(&object);
    free(raw_analysis_policy);
    platform_file_run_metrics_free(&result.metrics);
    return result;
  }
  render_start = clock();
  rendered = platform_file_render_ir_with_policy(&result.source_file, active_policy);
  if (!m68k_diag_has_errors(&rendered.diagnostics))
    (void)merge_policy_includes_into_rendered_text_local(&rendered, raw_analysis_policy);
  render_end = clock();
  m68k_object_destroy(&object);
  if (m68k_diag_has_errors(&rendered.diagnostics)) {
    result.diagnostics = rendered.diagnostics;
    platform_file_source_ir_free(&result.source_file);
    free(raw_analysis_policy);
    platform_file_run_metrics_free(&result.metrics);
    return result;
  }
  result.metrics.render_seconds = elapsed_seconds(render_start, render_end);
  result.metrics.text_bytes = strlen(rendered.text);
  total_end = clock();
  result.metrics.total_seconds = elapsed_seconds(total_start, total_end);
  result.text = rendered.text;
  free(raw_analysis_policy);
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
      "    \"violation_counts\": {\n"
      "      \"cpu_policy\": %u,\n"
      "      \"decode_failed_reachable\": %u,\n"
      "      \"invalid_interior_reference\": %u,\n"
      "      \"unresolved_indirect\": %u,\n"
      "      \"pc_relative_data_span_anchor\": %u,\n"
      "      \"pc_relative_data_code_overlap\": %u,\n"
      "      \"absolute_in_section_without_relocation\": %u,\n"
      "      \"unproven_label_addend\": %u,\n"
      "      \"unresolved_relocation_symbol\": %u,\n"
      "      \"branch_target_unstable\": %u,\n"
      "      \"orphaned_code\": %u\n"
      "    },\n"
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
      (unsigned)metrics->cpu_policy_violation_count,
      (unsigned)metrics->decode_failed_reachable_violation_count,
      (unsigned)metrics->invalid_interior_reference_violation_count,
      (unsigned)metrics->unresolved_indirect_violation_count,
      (unsigned)metrics->pc_relative_data_span_anchor_violation_count,
      (unsigned)metrics->pc_relative_data_code_overlap_violation_count,
      (unsigned)metrics->absolute_in_section_without_relocation_violation_count,
      (unsigned)metrics->unproven_label_addend_violation_count,
      (unsigned)metrics->unresolved_relocation_symbol_violation_count,
      (unsigned)metrics->branch_target_unstable_violation_count,
      (unsigned)metrics->orphaned_code_violation_count,
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
        "      \"violation_counts\": {\n"
        "        \"cpu_policy\": %u,\n"
        "        \"decode_failed_reachable\": %u,\n"
        "        \"invalid_interior_reference\": %u,\n"
        "        \"unresolved_indirect\": %u,\n"
        "        \"pc_relative_data_span_anchor\": %u,\n"
        "        \"pc_relative_data_code_overlap\": %u,\n"
        "        \"absolute_in_section_without_relocation\": %u,\n"
        "        \"unproven_label_addend\": %u,\n"
        "        \"unresolved_relocation_symbol\": %u,\n"
        "        \"branch_target_unstable\": %u,\n"
        "        \"orphaned_code\": %u\n"
        "      },\n"
        "      \"timing\": {\n"
        "        \"analysis_cache_seconds\": %.6f,\n"
        "        \"analysis_finalize_seconds\": %.6f,\n"
        "        \"analysis_rebuild_seconds\": %.6f,\n"
        "        \"ir_build_seconds\": %.6f,\n"
        "        \"ir_append_seconds\": %.6f,\n"
        "        \"ir_preseed_seconds\": %.6f,\n"
        "        \"ir_label_plan_seconds\": %.6f,\n"
        "        \"ir_label_comment_seconds\": %.6f,\n"
        "        \"ir_label_emit_seconds\": %.6f,\n"
        "        \"ir_code_decode_seconds\": %.6f,\n"
        "        \"ir_code_annotate_seconds\": %.6f,\n"
        "        \"ir_label_annotation_seconds\": %.6f,\n"
        "        \"ir_control_stabilize_seconds\": %.6f,\n"
        "        \"ir_platform_symbol_seconds\": %.6f,\n"
        "        \"ir_code_comment_seconds\": %.6f,\n"
        "        \"ir_instruction_append_seconds\": %.6f,\n"
        "        \"ir_data_span_seconds\": %.6f\n"
        "      },\n"
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
        (unsigned)section->cpu_policy_violation_count,
        (unsigned)section->decode_failed_reachable_violation_count,
        (unsigned)section->invalid_interior_reference_violation_count,
        (unsigned)section->unresolved_indirect_violation_count,
        (unsigned)section->pc_relative_data_span_anchor_violation_count,
        (unsigned)section->pc_relative_data_code_overlap_violation_count,
        (unsigned)section->absolute_in_section_without_relocation_violation_count,
        (unsigned)section->unproven_label_addend_violation_count,
        (unsigned)section->unresolved_relocation_symbol_violation_count,
        (unsigned)section->branch_target_unstable_violation_count,
        (unsigned)section->orphaned_code_violation_count,
        section->analysis_cache_seconds,
        section->analysis_finalize_seconds,
        section->analysis_rebuild_seconds,
        section->ir_build_seconds,
        section->ir_append_seconds,
        section->ir_preseed_seconds,
        section->ir_label_plan_seconds,
        section->ir_label_comment_seconds,
        section->ir_label_emit_seconds,
        section->ir_code_decode_seconds,
        section->ir_code_annotate_seconds,
        section->ir_label_annotation_seconds,
        section->ir_control_stabilize_seconds,
        section->ir_platform_symbol_seconds,
        section->ir_code_comment_seconds,
        section->ir_instruction_append_seconds,
        section->ir_data_span_seconds,
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
  M68kAnalysisPolicy *active_analysis_policy;
  const M68kRenderPolicy *active_policy = resolve_render_policy(policy, &default_policy);
  int populate_result;
  memset(&result, 0, sizeof(result));
  active_analysis_policy = analysis_policy_heap_copy_local(analysis_policy);
  if (active_analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return result;
  }
  if (load_object_from_buffer(backend, data, size, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(active_analysis_policy);
    return result;
  }
  if (enrich_policy_from_object_target_info_local(active_analysis_policy, backend, &object, NULL, 0U,
      &result.diagnostics) != 0) {
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    return result;
  }
  enrich_policy_pointer_targets_from_object_local(active_analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, active_analysis_policy)) {
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    return result;
  }
  populate_result = populate_source_ir_from_object(backend, &object, active_policy, active_analysis_policy,
    &result.source_file, m68k_diag_sink(&result.diagnostics));
  m68k_object_destroy(&object);
  free(active_analysis_policy);
  if (populate_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building source ir");
  return result;
}

PlatformFileSourceAnalysisResult platform_file_analyze_path(const char *backend_name, const char *path,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileSourceAnalysisResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  M68kAnalysisPolicy *active_analysis_policy;
  int populate_result;
  memset(&result, 0, sizeof(result));
  active_analysis_policy = analysis_policy_heap_copy_local(analysis_policy);
  result.source_analysis = (M68kSourceAnalysisIR *)calloc(1U, sizeof(*result.source_analysis));
  if (active_analysis_policy == NULL || result.source_analysis == NULL) {
    free(active_analysis_policy);
    free(result.source_analysis);
    result.source_analysis = NULL;
    platform_file_add_error(&result.diagnostics, "out of memory");
    return result;
  }
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(active_analysis_policy);
    free(result.source_analysis);
    result.source_analysis = NULL;
    return result;
  }
  if (enrich_policy_from_object_target_info_local(active_analysis_policy, backend, &object, NULL, 0U,
      &result.diagnostics) != 0) {
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    free(result.source_analysis);
    result.source_analysis = NULL;
    return result;
  }
  enrich_policy_pointer_targets_from_object_local(active_analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, active_analysis_policy)) {
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    free(result.source_analysis);
    result.source_analysis = NULL;
    return result;
  }
  populate_result = populate_source_analysis_from_object(&object, active_analysis_policy, result.source_analysis,
    m68k_diag_sink(&result.diagnostics));
  m68k_object_destroy(&object);
  free(active_analysis_policy);
  if (populate_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building source analysis");
  return result;
}

PlatformFileSourceAnalysisResult platform_file_analyze_buffer(const char *backend_name, const unsigned char *data,
    size_t size, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileSourceAnalysisResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  M68kAnalysisPolicy *active_analysis_policy;
  int populate_result;
  memset(&result, 0, sizeof(result));
  active_analysis_policy = analysis_policy_heap_copy_local(analysis_policy);
  result.source_analysis = (M68kSourceAnalysisIR *)calloc(1U, sizeof(*result.source_analysis));
  if (active_analysis_policy == NULL || result.source_analysis == NULL) {
    free(active_analysis_policy);
    free(result.source_analysis);
    result.source_analysis = NULL;
    platform_file_add_error(&result.diagnostics, "out of memory");
    return result;
  }
  if (load_object_from_buffer(backend, data, size, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(active_analysis_policy);
    free(result.source_analysis);
    result.source_analysis = NULL;
    return result;
  }
  if (enrich_policy_from_object_target_info_local(active_analysis_policy, backend, &object, NULL, 0U,
      &result.diagnostics) != 0) {
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    free(result.source_analysis);
    result.source_analysis = NULL;
    return result;
  }
  enrich_policy_pointer_targets_from_object_local(active_analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, active_analysis_policy)) {
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    free(result.source_analysis);
    result.source_analysis = NULL;
    return result;
  }
  populate_result = populate_source_analysis_from_object(&object, active_analysis_policy, result.source_analysis,
    m68k_diag_sink(&result.diagnostics));
  m68k_object_destroy(&object);
  free(active_analysis_policy);
  if (populate_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building source analysis");
  return result;
}

void platform_file_source_analysis_result_destroy(PlatformFileSourceAnalysisResult *result) {
  if (result == NULL) return;
  if (result->source_analysis != NULL) {
    m68k_ir_source_analysis_destroy(result->source_analysis);
    free(result->source_analysis);
    result->source_analysis = NULL;
  }
  m68k_diag_list_reset(&result->diagnostics);
}

PlatformFileTextResult platform_file_analyze_path_json(const char *backend_name, const char *path,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  M68kAnalysisPolicy *active_analysis_policy;
  M68kSourceAnalysisIR *analysis;
  int json_result;
  memset(&result, 0, sizeof(result));
  active_analysis_policy = analysis_policy_heap_copy_local(analysis_policy);
  analysis = (M68kSourceAnalysisIR *)calloc(1U, sizeof(*analysis));
  if (active_analysis_policy == NULL || analysis == NULL) {
    free(active_analysis_policy);
    free(analysis);
    platform_file_add_error(&result.diagnostics, "out of memory");
    return result;
  }
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(active_analysis_policy);
    free(analysis);
    return result;
  }
  if (enrich_policy_from_object_target_info_local(active_analysis_policy, backend, &object, NULL, 0U,
      &result.diagnostics) != 0) {
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    free(analysis);
    return result;
  }
  enrich_policy_pointer_targets_from_object_local(active_analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, active_analysis_policy)) {
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    free(analysis);
    return result;
  }
  if (populate_source_analysis_from_object(&object, active_analysis_policy, analysis,
      m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "failed building source analysis");
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    free(analysis);
    return result;
  }
  m68k_object_destroy(&object);
  json_result = source_analysis_to_json(analysis, &result.text, m68k_diag_sink(&result.diagnostics));
  m68k_ir_source_analysis_destroy(analysis);
  free(analysis);
  free(active_analysis_policy);
  if (json_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building analysis json");
  return result;
}

PlatformFileTextResult platform_file_analyze_raw_path_json(const char *platform_name, const char *path,
    uint32_t entry_offset, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  M68kObject object;
  M68kAnalysisPolicy *raw_analysis_policy;
  M68kSourceAnalysisIR *analysis;
  int json_result;
  memset(&result, 0, sizeof(result));
  raw_analysis_policy = analysis_policy_heap_copy_local(analysis_policy);
  analysis = (M68kSourceAnalysisIR *)calloc(1U, sizeof(*analysis));
  if (raw_analysis_policy == NULL || analysis == NULL) {
    free(raw_analysis_policy);
    free(analysis);
    platform_file_add_error(&result.diagnostics, "out of memory");
    return result;
  }
  if (load_raw_object_from_path(platform_name, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(raw_analysis_policy);
    free(analysis);
    return result;
  }
  raw_analysis_policy->has_entry_offset = 1U;
  raw_analysis_policy->entry_offset = entry_offset;
  enrich_policy_pointer_targets_from_object_local(raw_analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, raw_analysis_policy)) {
    m68k_object_destroy(&object);
    free(raw_analysis_policy);
    free(analysis);
    return result;
  }
  if (populate_source_analysis_from_object(&object, raw_analysis_policy, analysis,
      m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "failed building source analysis");
    m68k_object_destroy(&object);
    free(raw_analysis_policy);
    free(analysis);
    return result;
  }
  m68k_object_destroy(&object);
  json_result = source_analysis_to_json(analysis, &result.text, m68k_diag_sink(&result.diagnostics));
  m68k_ir_source_analysis_destroy(analysis);
  free(analysis);
  free(raw_analysis_policy);
  if (json_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building analysis json");
  return result;
}

PlatformFileTextResult platform_file_analyze_buffer_json(const char *backend_name, const unsigned char *data,
    size_t size, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  M68kAnalysisPolicy *active_analysis_policy;
  M68kSourceAnalysisIR *analysis;
  int json_result;
  memset(&result, 0, sizeof(result));
  active_analysis_policy = analysis_policy_heap_copy_local(analysis_policy);
  analysis = (M68kSourceAnalysisIR *)calloc(1U, sizeof(*analysis));
  if (active_analysis_policy == NULL || analysis == NULL) {
    free(active_analysis_policy);
    free(analysis);
    platform_file_add_error(&result.diagnostics, "out of memory");
    return result;
  }
  if (load_object_from_buffer(backend, data, size, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(active_analysis_policy);
    free(analysis);
    return result;
  }
  if (enrich_policy_from_object_target_info_local(active_analysis_policy, backend, &object, NULL, 0U,
      &result.diagnostics) != 0) {
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    free(analysis);
    return result;
  }
  enrich_policy_pointer_targets_from_object_local(active_analysis_policy, &object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, &object, active_analysis_policy)) {
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    free(analysis);
    return result;
  }
  if (populate_source_analysis_from_object(&object, active_analysis_policy, analysis,
      m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "failed building source analysis");
    m68k_object_destroy(&object);
    free(active_analysis_policy);
    free(analysis);
    return result;
  }
  m68k_object_destroy(&object);
  json_result = source_analysis_to_json(analysis, &result.text, m68k_diag_sink(&result.diagnostics));
  m68k_ir_source_analysis_destroy(analysis);
  free(analysis);
  free(active_analysis_policy);
  if (json_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building analysis json");
  return result;
}

PlatformFileTextResult platform_file_source_map_path_json(const char *backend_name, const char *path,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  PlatformFileSourceIrResult source_ir;
  int json_result;
  memset(&result, 0, sizeof(result));
  source_ir = platform_file_to_ir_with_policy(backend_name, path, policy, analysis_policy);
  if (m68k_diag_has_errors(&source_ir.diagnostics)) {
    result.diagnostics = source_ir.diagnostics;
    return result;
  }
  json_result = source_file_to_json(&source_ir.source_file, &result.text, m68k_diag_sink(&result.diagnostics));
  m68k_ir_source_file_destroy(&source_ir.source_file);
  if (json_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building source map json");
  return result;
}

PlatformFileTextResult platform_file_listing_rows_path_json(const char *backend_name, const char *path,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  PlatformFileSourceIrResult source_ir;
  PlatformFileTextResult rendered;
  M68kAnalysisPolicy *rows_analysis_policy;
  M68kObject object;
  int json_result;
  memset(&result, 0, sizeof(result));
  rows_analysis_policy = analysis_policy_heap_copy_local(analysis_policy);
  if (rows_analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return result;
  }
  if (load_object_from_path(m68k_backend_by_name(backend_name), path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(rows_analysis_policy);
    return result;
  }
  if (enrich_policy_from_object_target_info_local(rows_analysis_policy, m68k_backend_by_name(backend_name), &object, NULL, 0U,
      &result.diagnostics) != 0) {
    m68k_object_destroy(&object);
    free(rows_analysis_policy);
    return result;
  }
  enrich_policy_pointer_targets_from_object_local(rows_analysis_policy, &object);
  m68k_object_destroy(&object);
  source_ir = platform_file_to_ir_with_policy(backend_name, path, policy, rows_analysis_policy);
  if (m68k_diag_has_errors(&source_ir.diagnostics)) {
    result.diagnostics = source_ir.diagnostics;
    free(rows_analysis_policy);
    return result;
  }
  rendered = platform_file_render_ir_with_policy(&source_ir.source_file, policy);
  if (!m68k_diag_has_errors(&rendered.diagnostics))
    (void)merge_policy_includes_into_rendered_text_local(&rendered, rows_analysis_policy);
  if (m68k_diag_has_errors(&rendered.diagnostics)) {
    result.diagnostics = rendered.diagnostics;
    m68k_ir_source_file_destroy(&source_ir.source_file);
    free(rows_analysis_policy);
    return result;
  }
  json_result = source_file_listing_rows_to_json(&source_ir.source_file, rendered.text, rows_analysis_policy, &result.text,
    m68k_diag_sink(&result.diagnostics));
  platform_file_free_text(rendered.text);
  m68k_ir_source_file_destroy(&source_ir.source_file);
  free(rows_analysis_policy);
  if (json_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building listing rows json");
  return result;
}

typedef struct PlatformFileListingProfile {
  double policy_seconds;
  double pointer_validate_seconds;
  double render_seconds;
  double rows_json_seconds;
  double analysis_json_seconds;
  double total_seconds;
} PlatformFileListingProfile;

PlatformFileTextResult platform_file_listing_rows_raw_path_json(const char *platform_name, const char *path,
    uint32_t entry_offset, const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  PlatformFileRunResult run_result;
  M68kAnalysisPolicy *rows_analysis_policy;
  M68kObject object;
  int json_result;
  memset(&result, 0, sizeof(result));
  rows_analysis_policy = analysis_policy_heap_copy_local(analysis_policy);
  if (rows_analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return result;
  }
  rows_analysis_policy->has_entry_offset = 1U;
  rows_analysis_policy->entry_offset = entry_offset;
  if (load_raw_object_from_path(platform_name, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(rows_analysis_policy);
    return result;
  }
  enrich_policy_pointer_targets_from_object_local(rows_analysis_policy, &object);
  m68k_object_destroy(&object);
  run_result = platform_file_run_raw_path_with_policy(platform_name, path, entry_offset, policy, rows_analysis_policy);
  if (m68k_diag_has_errors(&run_result.diagnostics)) {
    result.diagnostics = run_result.diagnostics;
    free(rows_analysis_policy);
    return result;
  }
  json_result = source_file_listing_rows_to_json(&run_result.source_file, run_result.text, rows_analysis_policy, &result.text,
    m68k_diag_sink(&result.diagnostics));
  platform_file_free_text(run_result.text);
  platform_file_run_metrics_free(&run_result.metrics);
  m68k_ir_source_file_destroy(&run_result.source_file);
  free(rows_analysis_policy);
  if (json_result != 0 && !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building listing rows json");
  return result;
}

static PlatformFileTextResult platform_file_listing_rows_with_analysis_object_json(const M68kBackend *backend,
    const char *backend_name, const char *path, M68kObject *object, const M68kRenderPolicy *policy,
    M68kAnalysisPolicy *analysis_policy, int enrich_target_info) {
  PlatformFileTextResult result;
  M68kSourceFileIR source_file;
  M68kSourceAnalysisIR source_analysis;
  PlatformFileTextResult rendered;
  PlatformFileRunMetrics metrics;
  PlatformFileListingProfile profile;
  char *rows_json = NULL, *analysis_json = NULL;
  JsonBuilder builder;
  clock_t total_start, total_end, phase_start, phase_end;
  size_t section_index;
  int have_source_file = 0, have_source_analysis = 0;
  memset(&result, 0, sizeof(result));
  memset(&source_file, 0, sizeof(source_file));
  memset(&source_analysis, 0, sizeof(source_analysis));
  memset(&builder, 0, sizeof(builder));
  memset(&profile, 0, sizeof(profile));
  platform_file_run_metrics_init(&metrics);
  (void)backend_name;
  if (backend == NULL || backend_name == NULL || path == NULL || object == NULL || analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "invalid listing rows request");
    return result;
  }
  total_start = clock();
  phase_start = clock();
  if (enrich_target_info && enrich_policy_from_object_target_info_local(analysis_policy, backend, object, NULL, 0U,
      &result.diagnostics) != 0) {
    platform_file_run_metrics_free(&metrics);
    return result;
  }
  phase_end = clock();
  profile.policy_seconds = elapsed_seconds(phase_start, phase_end);
  phase_start = clock();
  enrich_policy_pointer_targets_from_object_local(analysis_policy, object);
  if (!validate_effective_policy_against_object_local(&result.diagnostics, object, analysis_policy)) {
    platform_file_run_metrics_free(&metrics);
    return result;
  }
  phase_end = clock();
  profile.pointer_validate_seconds = elapsed_seconds(phase_start, phase_end);
  if (populate_source_ir_from_object_with_metrics(backend, object, policy, analysis_policy, &source_file, &metrics,
      &source_analysis, m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "failed building source ir");
    platform_file_run_metrics_free(&metrics);
    return result;
  }
  have_source_file = 1;
  have_source_analysis = 1;
  phase_start = clock();
  rendered = platform_file_render_ir_with_policy(&source_file, policy);
  if (!m68k_diag_has_errors(&rendered.diagnostics))
    (void)merge_policy_includes_into_rendered_text_local(&rendered, analysis_policy);
  phase_end = clock();
  profile.render_seconds = elapsed_seconds(phase_start, phase_end);
  if (m68k_diag_has_errors(&rendered.diagnostics)) {
    result.diagnostics = rendered.diagnostics;
    goto cleanup;
  }
  phase_start = clock();
  if (source_file_listing_rows_to_json(&source_file, rendered.text, analysis_policy, &rows_json,
      m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "failed building listing rows with analysis json");
    platform_file_free_text(rendered.text);
    goto cleanup;
  }
  phase_end = clock();
  profile.rows_json_seconds = elapsed_seconds(phase_start, phase_end);
  phase_start = clock();
  if (source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(&result.diagnostics)) != 0) {
    if (!m68k_diag_has_errors(&result.diagnostics))
      platform_file_add_error(&result.diagnostics, "failed building listing rows with analysis json");
    platform_file_free_text(rendered.text);
    goto cleanup;
  }
  phase_end = clock();
  profile.analysis_json_seconds = elapsed_seconds(phase_start, phase_end);
  platform_file_free_text(rendered.text);
  total_end = clock();
  profile.total_seconds = elapsed_seconds(total_start, total_end);
  phase_start = clock();
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"listing\":") != 0 ||
      json_builder_append(&builder, rows_json) != 0 ||
      json_builder_append(&builder, ",\"analysis\":") != 0 ||
      json_builder_append(&builder, analysis_json) != 0 ||
      json_builder_append(&builder, ",\"profile\":{\"generation\":\"full\",\"backend\":") != 0 ||
      json_builder_append_json_string(&builder, backend_name) != 0 ||
      json_builder_append(&builder, ",\"path\":") != 0 ||
      json_builder_append_json_string(&builder, path) != 0 ||
      json_builder_appendf(&builder,
        ",\"timing\":{"
        "\"policy_seconds\":%.6f,"
        "\"pointer_validate_seconds\":%.6f,"
        "\"analysis_seconds\":%.6f,"
        "\"ir_build_seconds\":%.6f,"
        "\"render_seconds\":%.6f,"
        "\"rows_json_seconds\":%.6f,"
        "\"analysis_json_seconds\":%.6f,"
        "\"total_before_combine_seconds\":%.6f"
        "},\"counts\":{\"section_count\":%zu,\"row_json_bytes\":%u,\"analysis_json_bytes\":%u},\"sections\":[",
        profile.policy_seconds, profile.pointer_validate_seconds, metrics.analysis_seconds, metrics.ir_build_seconds,
        profile.render_seconds, profile.rows_json_seconds, profile.analysis_json_seconds, profile.total_seconds,
        object->section_count,
        (unsigned)(rows_json != NULL ? strlen(rows_json) : 0U),
        (unsigned)(analysis_json != NULL ? strlen(analysis_json) : 0U)) != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  for (section_index = 0U; section_index < metrics.section_count; ++section_index) {
    const PlatformFileRunSectionMetrics *section = &metrics.sections[section_index];
    if (section_index != 0U && json_builder_append(&builder, ",") != 0) {
      platform_file_add_error(&result.diagnostics, "out of memory");
      goto cleanup;
    }
    if (json_builder_appendf(&builder,
        "{\"section_index\":%u,\"name\":",
        (unsigned)section_index) != 0 ||
        json_builder_append_json_string(&builder, section->name) != 0 ||
        json_builder_appendf(&builder,
        ",\"size\":%u,"
        "\"analysis_cache_seconds\":%.6f,"
        "\"analysis_finalize_seconds\":%.6f,"
        "\"analysis_rebuild_seconds\":%.6f,"
        "\"ir_build_seconds\":%.6f,"
        "\"ir_append_seconds\":%.6f,"
        "\"ir_preseed_seconds\":%.6f,"
        "\"ir_label_plan_seconds\":%.6f,"
        "\"ir_label_comment_seconds\":%.6f,"
        "\"ir_label_emit_seconds\":%.6f,"
        "\"ir_code_decode_seconds\":%.6f,"
        "\"ir_code_annotate_seconds\":%.6f,"
        "\"ir_label_annotation_seconds\":%.6f,"
        "\"ir_control_stabilize_seconds\":%.6f,"
        "\"ir_platform_symbol_seconds\":%.6f,"
        "\"ir_code_comment_seconds\":%.6f,"
        "\"ir_instruction_append_seconds\":%.6f,"
        "\"ir_data_span_seconds\":%.6f}",
        (unsigned)section->size,
        section->analysis_cache_seconds,
        section->analysis_finalize_seconds,
        section->analysis_rebuild_seconds,
        section->ir_build_seconds,
        section->ir_append_seconds,
        section->ir_preseed_seconds,
        section->ir_label_plan_seconds,
        section->ir_label_comment_seconds,
        section->ir_label_emit_seconds,
        section->ir_code_decode_seconds,
        section->ir_code_annotate_seconds,
        section->ir_label_annotation_seconds,
        section->ir_control_stabilize_seconds,
        section->ir_platform_symbol_seconds,
        section->ir_code_comment_seconds,
        section->ir_instruction_append_seconds,
        section->ir_data_span_seconds) != 0) {
      platform_file_add_error(&result.diagnostics, "out of memory");
      goto cleanup;
    }
  }
  if (json_builder_append(&builder, "]}}") != 0) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    goto cleanup;
  }
  result.text = json_builder_build(&builder);
  if (result.text == NULL)
    platform_file_add_error(&result.diagnostics, "out of memory");

cleanup:
  json_builder_destroy(&builder);
  platform_file_free_text(rows_json);
  platform_file_free_text(analysis_json);
  if (have_source_analysis) m68k_ir_source_analysis_destroy(&source_analysis);
  if (have_source_file) m68k_ir_source_file_destroy(&source_file);
  platform_file_run_metrics_free(&metrics);
  return result;
}

PlatformFileTextResult platform_file_listing_rows_with_analysis_path_json(const char *backend_name, const char *path,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  M68kAnalysisPolicy *rows_analysis_policy;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  memset(&result, 0, sizeof(result));
  rows_analysis_policy = analysis_policy_heap_copy_local(analysis_policy);
  if (rows_analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return result;
  }
  if (load_object_from_path(backend, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(rows_analysis_policy);
    return result;
  }
  result = platform_file_listing_rows_with_analysis_object_json(backend, backend_name, path, &object, policy,
    rows_analysis_policy, 1);
  m68k_object_destroy(&object);
  free(rows_analysis_policy);
  return result;
}

PlatformFileTextResult platform_file_listing_rows_with_analysis_raw_path_json(const char *platform_name,
    const char *path, uint32_t entry_offset, const M68kRenderPolicy *policy,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result;
  M68kAnalysisPolicy *rows_analysis_policy;
  M68kObject object;
  const M68kBackend *backend = raw_platform_backend(platform_name);
  memset(&result, 0, sizeof(result));
  rows_analysis_policy = analysis_policy_heap_copy_local(analysis_policy);
  if (rows_analysis_policy == NULL) {
    platform_file_add_error(&result.diagnostics, "out of memory");
    return result;
  }
  rows_analysis_policy->has_entry_offset = 1U;
  rows_analysis_policy->entry_offset = entry_offset;
  if (load_raw_object_from_path(platform_name, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(rows_analysis_policy);
    return result;
  }
  result = platform_file_listing_rows_with_analysis_object_json(backend, platform_name, path, &object, policy,
    rows_analysis_policy, 0);
  m68k_object_destroy(&object);
  free(rows_analysis_policy);
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

int platform_file_disassemble_path_text_alloc(const char *backend_name, const char *path, const char *syntax,
    const char *metadata_path, char **out_text) {
  M68kRenderPolicy render_policy;
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  PlatformFileRunResult result;
  m68k_diag_list_reset(&diagnostics);
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    PlatformFileTextResult error_result;
    memset(&error_result, 0, sizeof(error_result));
    platform_file_add_error(&error_result.diagnostics, "out of memory");
    return text_result_to_alloc(&error_result, out_text);
  }
  if (configure_render_policy_for_alloc(&render_policy, syntax, &diagnostics) != 0 ||
      configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL, &diagnostics) != 0) {
    PlatformFileTextResult error_result;
    memset(&error_result, 0, sizeof(error_result));
    error_result.diagnostics = diagnostics;
    free(analysis_policy);
    return text_result_to_alloc(&error_result, out_text);
  }
  result = platform_file_run_path_with_policy(backend_name, path, &render_policy, analysis_policy);
  free(analysis_policy);
  return run_result_to_alloc(&result, out_text);
}

int platform_file_disassemble_raw_path_text_alloc(const char *platform_name, const char *path, uint32_t entry_offset,
    const char *syntax, const char *metadata_path, char **out_text) {
  M68kRenderPolicy render_policy;
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  PlatformFileRunResult result;
  m68k_diag_list_reset(&diagnostics);
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    PlatformFileTextResult error_result;
    memset(&error_result, 0, sizeof(error_result));
    platform_file_add_error(&error_result.diagnostics, "out of memory");
    return text_result_to_alloc(&error_result, out_text);
  }
  if (configure_render_policy_for_alloc(&render_policy, syntax, &diagnostics) != 0 ||
      configure_analysis_policy_for_alloc(analysis_policy, platform_name, metadata_path, NULL, &diagnostics) != 0) {
    PlatformFileTextResult error_result;
    memset(&error_result, 0, sizeof(error_result));
    error_result.diagnostics = diagnostics;
    free(analysis_policy);
    return text_result_to_alloc(&error_result, out_text);
  }
  result = platform_file_run_raw_path_with_policy(platform_name, path, entry_offset, &render_policy, analysis_policy);
  free(analysis_policy);
  return run_result_to_alloc(&result, out_text);
}

int platform_file_analyze_path_json_alloc(const char *backend_name, const char *path, const char *metadata_path,
    const char *entry_offsets, char **out_text) {
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
  result = platform_file_analyze_path_json(backend_name, path, analysis_policy);
  free(analysis_policy);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_analyze_raw_path_json_alloc(const char *platform_name, const char *path, uint32_t entry_offset,
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
  if (configure_analysis_policy_for_alloc(analysis_policy, platform_name, metadata_path, entry_offsets,
        &diagnostics) != 0) {
    result.text = NULL;
    result.diagnostics = diagnostics;
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  result = platform_file_analyze_raw_path_json(platform_name, path, entry_offset, analysis_policy);
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

static int benchmark_run_result_with_text_to_alloc(const char *platform_name, const char *path,
    PlatformFileRunResult *run_result, char **out_text) {
  PlatformFileTextResult metrics_result;
  JsonBuilder builder = {0};
  char *combined = NULL;
  int result;
  if (m68k_diag_has_errors(&run_result->diagnostics)) return run_result_to_alloc(run_result, out_text);
  metrics_result = platform_file_run_metrics_json(platform_name, path, &run_result->metrics);
  if (m68k_diag_has_errors(&metrics_result.diagnostics) || metrics_result.text == NULL) {
    result = text_result_to_alloc(&metrics_result, out_text);
    platform_file_free_text(run_result->text);
    platform_file_run_metrics_free(&run_result->metrics);
    platform_file_source_ir_free(&run_result->source_file);
    return result;
  }
  if (json_builder_create(&builder) != 0) goto oom;
  if (json_builder_append(&builder, "{\n  \"benchmark\": ") != 0) goto oom;
  if (json_builder_append(&builder, metrics_result.text) != 0) goto oom;
  if (json_builder_append(&builder, ",\n  \"text\": ") != 0) goto oom;
  if (json_builder_append_json_string(&builder, run_result->text) != 0) goto oom;
  if (json_builder_append(&builder, "\n}\n") != 0) goto oom;
  combined = json_builder_build(&builder);
  if (combined == NULL) goto oom;
  json_builder_destroy(&builder);
  platform_file_free_text(metrics_result.text);
  platform_file_free_text(run_result->text);
  platform_file_run_metrics_free(&run_result->metrics);
  platform_file_source_ir_free(&run_result->source_file);
  *out_text = combined;
  return 0;

oom:
  json_builder_destroy(&builder);
  platform_file_free_text(metrics_result.text);
  platform_file_free_text(run_result->text);
  platform_file_run_metrics_free(&run_result->metrics);
  platform_file_source_ir_free(&run_result->source_file);
  *out_text = duplicate_text_local("out of memory");
  return -1;
}

int platform_file_benchmark_with_text_path_json_alloc(const char *backend_name, const char *path, const char *syntax,
    const char *metadata_path, char **out_text) {
  M68kRenderPolicy render_policy;
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  PlatformFileRunResult run_result;
  m68k_diag_list_reset(&diagnostics);
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    PlatformFileTextResult metrics_result;
    metrics_result.text = NULL;
    memset(&metrics_result.diagnostics, 0, sizeof(metrics_result.diagnostics));
    platform_file_add_error(&metrics_result.diagnostics, "out of memory");
    return text_result_to_alloc(&metrics_result, out_text);
  }
  if (configure_render_policy_for_alloc(&render_policy, syntax, &diagnostics) != 0 ||
      configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL, &diagnostics) != 0) {
    PlatformFileTextResult metrics_result;
    metrics_result.text = NULL;
    metrics_result.diagnostics = diagnostics;
    free(analysis_policy);
    return text_result_to_alloc(&metrics_result, out_text);
  }
  run_result = platform_file_run_path_with_policy(backend_name, path, &render_policy, analysis_policy);
  free(analysis_policy);
  return benchmark_run_result_with_text_to_alloc(backend_name, path, &run_result, out_text);
}

int platform_file_benchmark_with_text_raw_path_json_alloc(const char *platform_name, const char *path,
    uint32_t entry_offset, const char *syntax, const char *metadata_path, char **out_text) {
  M68kRenderPolicy render_policy;
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  PlatformFileRunResult run_result;
  m68k_diag_list_reset(&diagnostics);
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    PlatformFileTextResult metrics_result;
    metrics_result.text = NULL;
    memset(&metrics_result.diagnostics, 0, sizeof(metrics_result.diagnostics));
    platform_file_add_error(&metrics_result.diagnostics, "out of memory");
    return text_result_to_alloc(&metrics_result, out_text);
  }
  if (configure_render_policy_for_alloc(&render_policy, syntax, &diagnostics) != 0 ||
      configure_analysis_policy_for_alloc(analysis_policy, platform_name, metadata_path, NULL, &diagnostics) != 0) {
    PlatformFileTextResult metrics_result;
    metrics_result.text = NULL;
    metrics_result.diagnostics = diagnostics;
    free(analysis_policy);
    return text_result_to_alloc(&metrics_result, out_text);
  }
  run_result = platform_file_run_raw_path_with_policy(platform_name, path, entry_offset, &render_policy, analysis_policy);
  free(analysis_policy);
  return benchmark_run_result_with_text_to_alloc(platform_name, path, &run_result, out_text);
}

int platform_file_listing_rows_path_json_alloc(const char *backend_name, const char *path, const char *metadata_path,
    char **out_text) {
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
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL, &diagnostics) != 0) {
    result.text = NULL;
    result.diagnostics = diagnostics;
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  result = platform_file_listing_rows_path_json(backend_name, path, NULL, analysis_policy);
  free(analysis_policy);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_basic_listing_rows_path_json_alloc(const char *backend_name, const char *path,
    const char *metadata_path, char **out_text) {
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  PlatformFileTextResult result;
  M68kObject object;
  m68k_diag_list_reset(&diagnostics);
  memset(&object, 0, sizeof(object));
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    result.text = NULL;
    memset(&result.diagnostics, 0, sizeof(result.diagnostics));
    platform_file_add_error(&result.diagnostics, "out of memory");
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL, &diagnostics) != 0) {
    result.text = NULL;
    result.diagnostics = diagnostics;
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  analysis_policy->skip_platform_facts = 1U;
  memset(&result, 0, sizeof(result));
  if (load_object_from_path(m68k_backend_by_name(backend_name), path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (basic_listing_rows_object_json(&object, analysis_policy, &result.text, m68k_diag_sink(&result.diagnostics)) != 0 &&
      !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building basic listing rows json");
  m68k_object_destroy(&object);
  free(analysis_policy);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_listing_rows_with_analysis_path_json_alloc(const char *backend_name, const char *path,
    const char *metadata_path, char **out_text) {
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
  if (configure_analysis_policy_for_alloc(analysis_policy, backend_name, metadata_path, NULL, &diagnostics) != 0) {
    result.text = NULL;
    result.diagnostics = diagnostics;
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  result = platform_file_listing_rows_with_analysis_path_json(backend_name, path, NULL, analysis_policy);
  free(analysis_policy);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_listing_rows_raw_path_json_alloc(const char *platform_name, const char *path, uint32_t entry_offset,
    const char *metadata_path, char **out_text) {
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
  if (configure_analysis_policy_for_alloc(analysis_policy, platform_name, metadata_path, NULL, &diagnostics) != 0) {
    result.text = NULL;
    result.diagnostics = diagnostics;
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  result = platform_file_listing_rows_raw_path_json(platform_name, path, entry_offset, NULL, analysis_policy);
  free(analysis_policy);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_listing_rows_with_analysis_raw_path_json_alloc(const char *platform_name, const char *path,
    uint32_t entry_offset, const char *metadata_path, char **out_text) {
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
  if (configure_analysis_policy_for_alloc(analysis_policy, platform_name, metadata_path, NULL, &diagnostics) != 0) {
    result.text = NULL;
    result.diagnostics = diagnostics;
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  result = platform_file_listing_rows_with_analysis_raw_path_json(platform_name, path, entry_offset, NULL,
    analysis_policy);
  free(analysis_policy);
  return text_result_to_alloc(&result, out_text);
}

int platform_file_basic_listing_rows_raw_path_json_alloc(const char *platform_name, const char *path,
    uint32_t entry_offset, const char *metadata_path, char **out_text) {
  M68kAnalysisPolicy *analysis_policy;
  M68kDiagList diagnostics;
  PlatformFileTextResult result;
  M68kObject object;
  m68k_diag_list_reset(&diagnostics);
  memset(&object, 0, sizeof(object));
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    result.text = NULL;
    memset(&result.diagnostics, 0, sizeof(result.diagnostics));
    platform_file_add_error(&result.diagnostics, "out of memory");
    return text_result_to_alloc(&result, out_text);
  }
  if (configure_analysis_policy_for_alloc(analysis_policy, platform_name, metadata_path, NULL, &diagnostics) != 0) {
    result.text = NULL;
    result.diagnostics = diagnostics;
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  analysis_policy->skip_platform_facts = 1U;
  analysis_policy->has_entry_offset = 1U;
  analysis_policy->entry_offset = entry_offset;
  memset(&result, 0, sizeof(result));
  if (load_raw_object_from_path(platform_name, path, &object, m68k_diag_sink(&result.diagnostics)) != 0) {
    free(analysis_policy);
    return text_result_to_alloc(&result, out_text);
  }
  if (basic_listing_rows_object_json(&object, analysis_policy, &result.text, m68k_diag_sink(&result.diagnostics)) != 0 &&
      !m68k_diag_has_errors(&result.diagnostics))
    platform_file_add_error(&result.diagnostics, "failed building basic listing rows json");
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
