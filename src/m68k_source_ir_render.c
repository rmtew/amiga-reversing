#include "m68k_source_ir_render.h"
#include "generated/amiga_os_runtime.h"
#include "generated/atari_st_os_runtime.h"
#include "json_builder.h"
#include "m68k_instruction_spec.h"
#include "m68k_ir_codec.h"
#include "m68k_parse_util.h"
#include "m68k_source_text_util.h"

#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define M68K_RENDER_COMMENT_COLUMN 40U
#define M68K_RENDER_STRING_CHUNK_BYTES 128U

static int byte_is_quoted_string_char(unsigned char ch) {
  return ch >= 32U && ch <= 126U && ch != '"' && ch != '\\';
}

static int append_rendered_string_bytes(JsonBuilder *builder, const uint8_t *data, size_t size) {
  size_t index = 0U;
  int has_operand = 0;
  while (index < size) {
    unsigned char ch = data[index];
    if (has_operand && json_builder_append(builder, ",") != 0) return -1;
    if (byte_is_quoted_string_char(ch)) {
      if (json_builder_append(builder, "\"") != 0) return -1;
      while (index < size && byte_is_quoted_string_char(data[index])) {
        if (json_builder_appendf(builder, "%c", data[index]) != 0) return -1;
        ++index;
      }
      if (json_builder_append(builder, "\"") != 0) return -1;
    } else {
      if (json_builder_appendf(builder, "$%02x", (unsigned)ch) != 0) return -1;
      ++index;
    }
    has_operand = 1;
  }
  return has_operand ? 0 : json_builder_append(builder, "\"\"");
}

static int append_rendered_string_data_stmt(JsonBuilder *builder, const M68kDataItemIR *data) {
  size_t string_size;
  size_t offset = 0U;
  int has_trailing_nul = 0;
  if (builder == NULL || data == NULL) return -1;
  string_size = data->size;
  if (string_size != 0U && data->data[string_size - 1U] == 0U) {
    has_trailing_nul = 1;
    --string_size;
  }
  if (string_size == 0U) {
    if (json_builder_append(builder, "    DC.B    ") != 0) return -1;
    if (append_rendered_string_bytes(builder, data->data, 0U) != 0) return -1;
    return has_trailing_nul ? json_builder_append(builder, ",0") : 0;
  }
  while (offset < string_size) {
    size_t chunk = string_size - offset;
    if (chunk > M68K_RENDER_STRING_CHUNK_BYTES) chunk = M68K_RENDER_STRING_CHUNK_BYTES;
    if (offset != 0U && json_builder_append(builder, "\n") != 0) return -1;
    if (json_builder_append(builder, "    DC.B    ") != 0) return -1;
    if (append_rendered_string_bytes(builder, data->data + offset, chunk) != 0) return -1;
    offset += chunk;
  }
  return has_trailing_nul ? json_builder_append(builder, ",0") : 0;
}

static const char *section_base_name(const M68kSectionIR *section) {
  return (section != NULL && section->name != NULL && section->name[0] != '\0') ? section->name : "section";
}

static int section_name_needs_suffix(const M68kSourceFileIR *source_file, size_t section_index) {
  const char *base_name;
  size_t index;
  if (source_file == NULL || section_index >= source_file->section_count) return 0;
  base_name = section_base_name(&source_file->sections[section_index]);
  if ((source_file->sections[section_index].name == NULL || source_file->sections[section_index].name[0] == '\0') &&
      source_file->section_count > 1U) {
    return 1;
  }
  for (index = 0U; index < source_file->section_count; ++index) {
    if (index == section_index) continue;
    if (m68k_ascii_equal_ci(section_base_name(&source_file->sections[index]), base_name)) return 1;
  }
  return 0;
}

static const char *rendered_section_name(const M68kSourceFileIR *source_file, size_t section_index, char *buffer,
    size_t buffer_size) {
  const char *base_name;
  if (buffer != NULL && buffer_size != 0U) buffer[0] = '\0';
  if (source_file == NULL || section_index >= source_file->section_count) return "section";
  base_name = section_base_name(&source_file->sections[section_index]);
  if (!section_name_needs_suffix(source_file, section_index)) return base_name;
  if (buffer == NULL || buffer_size == 0U) return base_name;
  snprintf(buffer, buffer_size, "%s_%u", base_name, (unsigned)section_index);
  return buffer;
}

static int append_rendered_data_stmt(JsonBuilder *builder, const M68kDataItemIR *data, const M68kRenderPolicy *policy) {
  size_t index;
  const char *directive = (data->kind == M68K_DATA_ITEM_WORDS) ? "DC.W" : (data->kind == M68K_DATA_ITEM_LONGS) ? "DC.L"
    : "DC.B";
  size_t step = (data->kind == M68K_DATA_ITEM_WORDS)   ? 2U : (data->kind == M68K_DATA_ITEM_LONGS) ? 4U : 1U;
  size_t items_per_line = (data->kind == M68K_DATA_ITEM_LONGS) ? 8U : (data->kind == M68K_DATA_ITEM_WORDS) ? 12U : 16U;
  if (data->kind == M68K_DATA_ITEM_STRING && (policy == NULL || policy->presentation.prefer_strings != 0U)) {
    return append_rendered_string_data_stmt(builder, data);
  }
  if (data->expr_text != NULL && data->expr_text[0] != '\0')
    return json_builder_appendf(builder, "    %-7s %s", directive, data->expr_text);
  if (data->kind == M68K_DATA_ITEM_STRING) {
    directive = "DC.B";
    step = 1U;
  }
  if (data->kind == M68K_DATA_ITEM_LONGS && policy != NULL && policy->presentation.prefer_long_data == 0U) {
    directive = "DC.B";
    step = 1U;
    items_per_line = 16U;
  }
  for (index = 0; index < data->size; index += step) {
    if ((index / step) % items_per_line == 0U) {
      if (index != 0U && json_builder_append(builder, "\n") != 0) return -1;
      if (json_builder_appendf(builder, "    %-7s ", directive) != 0) return -1;
    } else if (json_builder_append(builder, ",") != 0) {
      return -1;
    }
    if (step == 1U) {
      if (json_builder_appendf(builder, "$%02x", (unsigned)data->data[index]) != 0) return -1;
    } else if (step == 2U) {
      uint16_t value = (uint16_t)(((uint16_t)data->data[index] << 8) | data->data[index + 1U]);
      if (json_builder_appendf(builder, "$%04x", (unsigned)value) != 0) return -1;
    } else {
      uint32_t value = ((uint32_t)data->data[index] << 24) | ((uint32_t)data->data[index + 1U] << 16) |
                       ((uint32_t)data->data[index + 2U] << 8) | (uint32_t)data->data[index + 3U];
      if (json_builder_appendf(builder, "$%08x", (unsigned)value) != 0) return -1;
    }
  }
  return 0;
}

static int append_comment_at_column(JsonBuilder *builder, size_t line_start, const char *comment) {
  size_t line_len;
  if (builder == NULL || comment == NULL) return -1;
  line_len = builder->size >= line_start ? builder->size - line_start : 0U;
  if (line_len + 1U < M68K_RENDER_COMMENT_COLUMN) {
    size_t index;
    for (index = line_len; index < M68K_RENDER_COMMENT_COLUMN; ++index) {
      if (json_builder_append_char(builder, ' ') != 0) return -1;
    }
    return json_builder_appendf(builder, "; %s\n", comment);
  }
  return json_builder_appendf(builder, " ; %s\n", comment);
}

static int append_statement_comment(JsonBuilder *builder, const M68kStatementIR *stmt, size_t line_start) {
  if (stmt == NULL || stmt->comment == NULL || stmt->comment[0] == '\0') return json_builder_append(builder, "\n");
  if (strncmp(stmt->comment, "FIELD:", 6) == 0) {
    const char *field_comment = stmt->comment + 6;
    while (*field_comment == ' ' || *field_comment == '\t') ++field_comment;
    return append_comment_at_column(builder, line_start, field_comment);
  }
  if (strstr(stmt->comment, "CANDIDATE:") != NULL || strncmp(stmt->comment, "NOTE:", 5) == 0 ||
      strncmp(stmt->comment, "KNOWN:", 6) == 0 || strncmp(stmt->comment, "DECL:", 5) == 0 ||
      strncmp(stmt->comment, "STRUCT ", 7) == 0) {
    return append_comment_at_column(builder, line_start, stmt->comment);
  }
  return json_builder_appendf(builder,
    line_start == builder->size ? "; VIOLATION: %s\n" : " ; VIOLATION: %s\n", stmt->comment);
}

static int instruction_needs_fpu_id_directive(const M68kInstructionIR *instruction) {
  if (instruction == NULL || instruction->has_coprocessor_id == 0U || instruction->coprocessor_id == 1U)
    return 0;
  return instruction->mnemonic_id == M68K_ASM_MNEMONIC_CPRESTORE ||
    instruction->mnemonic_id == M68K_ASM_MNEMONIC_CPSAVE;
}

static int instruction_renders_with_fpu_mnemonic(const M68kInstructionIR *instruction) {
  if (instruction == NULL || instruction->has_coprocessor_id == 0U) return 0;
  return instruction->mnemonic_id == M68K_ASM_MNEMONIC_CPRESTORE ||
    instruction->mnemonic_id == M68K_ASM_MNEMONIC_CPSAVE;
}

static int make_fpu_id_render_instruction(const M68kInstructionIR *instruction,
    M68kInstructionIR *out_instruction) {
  M68kAsmOperandValue operands[4];
  uint8_t mnemonic_id;
  size_t operand_index;
  if (instruction == NULL || out_instruction == NULL) return 0;
  if (!instruction_renders_with_fpu_mnemonic(instruction)) return 0;
  *out_instruction = *instruction;
  mnemonic_id = instruction->mnemonic_id == M68K_ASM_MNEMONIC_CPRESTORE
    ? M68K_ASM_MNEMONIC_FRESTORE : M68K_ASM_MNEMONIC_FSAVE;
  out_instruction->mnemonic_id = mnemonic_id;
  out_instruction->has_coprocessor_id = 0U;
  out_instruction->coprocessor_id = 0U;
  out_instruction->target_cpu = M68K_ASM_CPU_68040;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    m68k_instruction_operand_to_asm_value(&instruction->operands[operand_index], &operands[operand_index]);
  }
  out_instruction->asm_form_index = m68k_asm_form_index_for_operands_id(mnemonic_id, operands,
    instruction->operand_count, instruction->size_suffix, instruction->target_cpu);
  return g_m68k_asm_forms[out_instruction->asm_form_index].mnemonic_id != M68K_ASM_MNEMONIC_NONE;
}

typedef struct RenderLabelIndex {
  const char **names;
  size_t count;
  size_t capacity;
} RenderLabelIndex;

typedef struct RenderLabelIndexes {
  RenderLabelIndex all;
  RenderLabelIndex *sections;
  size_t section_count;
} RenderLabelIndexes;

static size_t render_label_hash(const char *name) {
  size_t hash = 1469598103934665603ULL;
  while (name != NULL && *name != '\0') {
    hash ^= (unsigned char)*name++;
    hash *= 1099511628211ULL;
  }
  return hash;
}

static int render_label_index_init(RenderLabelIndex *index, size_t count) {
  size_t capacity = 1U;
  if (index == NULL) return 0;
  memset(index, 0, sizeof(*index));
  if (count == 0U) return 1;
  while (capacity < count * 2U) capacity <<= 1U;
  index->names = (const char **)calloc(capacity, sizeof(*index->names));
  if (index->names == NULL) return 0;
  index->capacity = capacity;
  return 1;
}

static int render_label_index_insert(RenderLabelIndex *index, const char *name) {
  size_t mask;
  size_t slot;
  if (index == NULL || name == NULL || name[0] == '\0') return 1;
  if (index->names == NULL || index->capacity == 0U) return 0;
  mask = index->capacity - 1U;
  slot = render_label_hash(name) & mask;
  for (;;) {
    if (index->names[slot] == NULL) {
      index->names[slot] = name;
      index->count += 1U;
      return 1;
    }
    if (strcmp(index->names[slot], name) == 0) return 1;
    slot = (slot + 1U) & mask;
  }
}

static int render_label_index_has(const RenderLabelIndex *index, const char *name) {
  size_t mask;
  size_t slot;
  if (name == NULL || name[0] == '\0') return 0;
  if (name[0] == '*') return 1;
  if (index == NULL || index->names == NULL || index->capacity == 0U) return 0;
  mask = index->capacity - 1U;
  slot = render_label_hash(name) & mask;
  for (;;) {
    const char *stored = index->names[slot];
    if (stored == NULL) return 0;
    if (strcmp(stored, name) == 0) return 1;
    slot = (slot + 1U) & mask;
  }
}

static void render_label_index_destroy(RenderLabelIndex *index) {
  if (index == NULL) return;
  free(index->names);
  memset(index, 0, sizeof(*index));
}

static void render_label_indexes_destroy(RenderLabelIndexes *indexes) {
  size_t section_index;
  if (indexes == NULL) return;
  render_label_index_destroy(&indexes->all);
  for (section_index = 0U; section_index < indexes->section_count; ++section_index) {
    render_label_index_destroy(&indexes->sections[section_index]);
  }
  free(indexes->sections);
  memset(indexes, 0, sizeof(*indexes));
}

static int render_label_indexes_build(RenderLabelIndexes *indexes, const M68kSourceFileIR *source_file) {
  size_t *section_label_counts = NULL;
  size_t total_label_count = 0U;
  size_t section_index;
  if (indexes == NULL || source_file == NULL) return 0;
  memset(indexes, 0, sizeof(*indexes));
  if (source_file->section_count != 0U) {
    indexes->sections = (RenderLabelIndex *)calloc(source_file->section_count, sizeof(*indexes->sections));
    section_label_counts = (size_t *)calloc(source_file->section_count, sizeof(*section_label_counts));
    if (indexes->sections == NULL || section_label_counts == NULL) goto fail;
    indexes->section_count = source_file->section_count;
  }
  for (section_index = 0U; section_index < source_file->section_count; ++section_index) {
    const M68kSectionIR *section = &source_file->sections[section_index];
    size_t stmt_index;
    for (stmt_index = 0U; stmt_index < section->statement_count; ++stmt_index) {
      const M68kStatementIR *stmt = &section->statements[stmt_index];
      if (stmt->kind != M68K_STATEMENT_LABEL || stmt->label_name == NULL || stmt->label_name[0] == '\0') continue;
      section_label_counts[section_index] += 1U;
      total_label_count += 1U;
    }
  }
  if (!render_label_index_init(&indexes->all, total_label_count)) goto fail;
  for (section_index = 0U; section_index < source_file->section_count; ++section_index) {
    if (!render_label_index_init(&indexes->sections[section_index], section_label_counts[section_index])) goto fail;
  }
  for (section_index = 0U; section_index < source_file->section_count; ++section_index) {
    const M68kSectionIR *section = &source_file->sections[section_index];
    size_t stmt_index;
    for (stmt_index = 0U; stmt_index < section->statement_count; ++stmt_index) {
      const M68kStatementIR *stmt = &section->statements[stmt_index];
      if (stmt->kind != M68K_STATEMENT_LABEL || stmt->label_name == NULL || stmt->label_name[0] == '\0') continue;
      if (!render_label_index_insert(&indexes->all, stmt->label_name) ||
          !render_label_index_insert(&indexes->sections[section_index], stmt->label_name)) {
        goto fail;
      }
    }
  }
  free(section_label_counts);
  return 1;

fail:
  free(section_label_counts);
  render_label_indexes_destroy(indexes);
  return 0;
}

static int section_has_label_name(const M68kSectionIR *section, const char *name) {
  size_t stmt_index;
  if (section == NULL || name == NULL || name[0] == '\0') return 0;
  if (name[0] == '*') return 1;
  for (stmt_index = 0; stmt_index < section->statement_count; ++stmt_index) {
    const M68kStatementIR *stmt = &section->statements[stmt_index];
    if (stmt->kind != M68K_STATEMENT_LABEL || stmt->label_name == NULL) continue;
    if (strcmp(stmt->label_name, name) == 0) return 1;
  }
  return 0;
}

static int render_section_has_label_name(const RenderLabelIndexes *label_indexes, size_t section_index,
    const M68kSectionIR *section, const char *name) {
  if (name == NULL || name[0] == '\0') return 0;
  if (name[0] == '*') return 1;
  if (label_indexes != NULL && section_index < label_indexes->section_count) {
    return render_label_index_has(&label_indexes->sections[section_index], name);
  }
  return section_has_label_name(section, name);
}

static int source_file_has_label_name(const M68kSourceFileIR *source_file, const RenderLabelIndexes *label_indexes,
    const char *name) {
  size_t section_index;
  if (source_file == NULL || name == NULL || name[0] == '\0') return 0;
  if (name[0] == '*') return 1;
  if (label_indexes != NULL) return render_label_index_has(&label_indexes->all, name);
  for (section_index = 0; section_index < source_file->section_count; ++section_index) {
    if (section_has_label_name(&source_file->sections[section_index], name)) return 1;
  }
  return 0;
}

static int source_file_has_amiga_resident_library_context(const M68kSourceFileIR *source_file,
    const RenderLabelIndexes *label_indexes) {
  return source_file != NULL &&
    source_file->platform_backend_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK &&
    (source_file_has_label_name(source_file, label_indexes, "resident") ||
      source_file_has_label_name(source_file, label_indexes, "resident_autoinit") ||
      source_file_has_label_name(source_file, label_indexes, "resident_vectors"));
}

typedef struct RenderEquate {
  char name[64];
  int32_t value;
  int32_t min_extent;
  uint8_t consumed;
} RenderEquate;

static void render_error(M68kDiagSink diagnostics, const char *message) {
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_RENDER_FAILED, message);
}

typedef struct RenderInclude {
  char path[128];
} RenderInclude;

typedef int (*RenderSymbolVisitor)(const char *name, uint8_t provenance, void *context);

typedef struct RenderSymbolIncludeCacheEntry {
  char name[128];
  uint8_t provenance;
  uint8_t platform_backend_kind;
  uint8_t used;
  const char *include_path;
} RenderSymbolIncludeCacheEntry;

typedef struct RenderSymbolIncludeCache {
  RenderSymbolIncludeCacheEntry *entries;
  size_t count;
  size_t capacity;
} RenderSymbolIncludeCache;

static const char *lookup_symbol_include_path(const M68kSourceFileIR *source_file, const char *name, uint8_t provenance) {
  if (name == NULL || name[0] == '\0') return NULL;
  switch (provenance) {
  case M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA:
    return amiga_os_find_symbol_include(name);
  case M68K_IR_SYMBOL_PROVENANCE_PLATFORM_ATARI_ST:
    return atari_st_os_find_symbol_include(name);
  case M68K_IR_SYMBOL_PROVENANCE_NONE:
    if (source_file == NULL) return NULL;
    if (source_file->platform_backend_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK)
      return amiga_os_find_symbol_include(name);
    if (source_file->platform_backend_kind == M68K_PLATFORM_BACKEND_ATARI_ST)
      return atari_st_os_find_symbol_include(name);
    return NULL;
  default:
    return NULL;
  }
}

static size_t render_symbol_include_cache_hash(const char *name, uint8_t provenance, uint8_t platform_backend_kind) {
  size_t hash = 1469598103934665603ULL;
  hash ^= provenance;
  hash *= 1099511628211ULL;
  hash ^= platform_backend_kind;
  hash *= 1099511628211ULL;
  while (name != NULL && *name != '\0') {
    hash ^= (unsigned char)*name++;
    hash *= 1099511628211ULL;
  }
  return hash;
}

static void render_symbol_include_cache_destroy(RenderSymbolIncludeCache *cache) {
  if (cache == NULL) return;
  free(cache->entries);
  memset(cache, 0, sizeof(*cache));
}

static int render_symbol_include_cache_reserve(RenderSymbolIncludeCache *cache, size_t count_needed) {
  RenderSymbolIncludeCacheEntry *old_entries;
  size_t old_capacity;
  size_t capacity = 64U;
  size_t index;
  if (cache == NULL) return 0;
  while (capacity < count_needed * 2U) capacity <<= 1U;
  if (cache->capacity >= capacity) return 1;
  old_entries = cache->entries;
  old_capacity = cache->capacity;
  cache->entries = (RenderSymbolIncludeCacheEntry *)calloc(capacity, sizeof(*cache->entries));
  if (cache->entries == NULL) {
    cache->entries = old_entries;
    return 0;
  }
  cache->capacity = capacity;
  cache->count = 0U;
  for (index = 0U; index < old_capacity; ++index) {
    RenderSymbolIncludeCacheEntry *old_entry = &old_entries[index];
    size_t mask;
    size_t slot;
    if (!old_entry->used) continue;
    mask = cache->capacity - 1U;
    slot = render_symbol_include_cache_hash(old_entry->name, old_entry->provenance,
      old_entry->platform_backend_kind) & mask;
    while (cache->entries[slot].used) slot = (slot + 1U) & mask;
    cache->entries[slot] = *old_entry;
    cache->count += 1U;
  }
  free(old_entries);
  return 1;
}

static const char *lookup_symbol_include_path_cached(RenderSymbolIncludeCache *cache,
    const M68kSourceFileIR *source_file, const char *name, uint8_t provenance) {
  uint8_t platform_backend_kind = source_file != NULL ? source_file->platform_backend_kind : 0U;
  const char *include_path;
  size_t mask;
  size_t slot;
  if (cache == NULL || name == NULL || name[0] == '\0' ||
      strlen(name) >= sizeof(((RenderSymbolIncludeCacheEntry *)0)->name)) {
    return lookup_symbol_include_path(source_file, name, provenance);
  }
  if (cache->capacity == 0U || cache->count * 4U >= cache->capacity * 3U) {
    if (!render_symbol_include_cache_reserve(cache, cache->count + 1U)) return lookup_symbol_include_path(source_file, name, provenance);
  }
  mask = cache->capacity - 1U;
  slot = render_symbol_include_cache_hash(name, provenance, platform_backend_kind) & mask;
  for (;;) {
    RenderSymbolIncludeCacheEntry *entry = &cache->entries[slot];
    if (!entry->used) break;
    if (entry->provenance == provenance && entry->platform_backend_kind == platform_backend_kind &&
        strcmp(entry->name, name) == 0) {
      return entry->include_path;
    }
    slot = (slot + 1U) & mask;
  }
  include_path = lookup_symbol_include_path(source_file, name, provenance);
  cache->entries[slot].used = 1U;
  cache->entries[slot].provenance = provenance;
  cache->entries[slot].platform_backend_kind = platform_backend_kind;
  snprintf(cache->entries[slot].name, sizeof(cache->entries[slot].name), "%s", name);
  cache->entries[slot].include_path = include_path;
  cache->count += 1U;
  return include_path;
}

static int lookup_symbol_equate_value(const char *name, int32_t *out_value) {
  const AmigaOsLibraryVectorInfo *amiga_vector;
  const AtariStOsCallInfo *atari_call;
  const AmigaOsStructFieldInfo *amiga_field;
  uint32_t amiga_hardware_base_address = 0U;
  if (name == NULL || name[0] == '\0' || out_value == NULL) return 0;
  atari_call = atari_st_os_find_call_by_symbol_name(name);
  if (atari_call != NULL) {
    *out_value = atari_call->opcode;
    return 1;
  }
  amiga_vector = amiga_os_find_library_vector_by_symbol_name(name);
  if (amiga_vector != NULL) {
    *out_value = amiga_vector->lvo;
    return 1;
  }
  amiga_field = amiga_os_find_struct_field_by_symbol_name(name);
  if (amiga_field != NULL) {
    *out_value = amiga_field->offset;
    return 1;
  }
  if (amiga_os_find_hardware_base_address(name, &amiga_hardware_base_address) &&
      amiga_hardware_base_address <= (uint32_t)INT32_MAX) {
    *out_value = (int32_t)amiga_hardware_base_address;
    return 1;
  }
  if (amiga_os_find_constant_value(name, out_value)) return 1;
  return 0;
}

static int visit_symbol_text_identifiers(const char *text, uint8_t provenance, RenderSymbolVisitor visitor, void *context) {
  const char *cursor = text;
  if (text == NULL || text[0] == '\0' || visitor == NULL) return 0;
  while (*cursor != '\0') {
    const char *start;
    char symbol_name[64];
    size_t length = 0U;
    if (!((*cursor >= 'A' && *cursor <= 'Z') || (*cursor >= 'a' && *cursor <= 'z') || *cursor == '_')) {
      ++cursor;
      continue;
    }
    start = cursor;
    while ((*cursor >= 'A' && *cursor <= 'Z') || (*cursor >= 'a' && *cursor <= 'z') ||
           (*cursor >= '0' && *cursor <= '9') || *cursor == '_') {
      if (length + 1U < sizeof(symbol_name)) symbol_name[length++] = *cursor;
      ++cursor;
    }
    if (length == 0U) continue;
    symbol_name[length] = '\0';
    if (start != text) {
      char previous = start[-1];
      if ((previous >= 'A' && previous <= 'Z') || (previous >= 'a' && previous <= 'z') ||
          (previous >= '0' && previous <= '9') || previous == '_')
        continue;
    }
    if (visitor(symbol_name, provenance, context) != 0) return -1;
  }
  return 0;
}

static int visit_operand_symbol_refs(const M68kOperandIR *operand, RenderSymbolVisitor visitor, void *context) {
  if (operand == NULL || visitor == NULL) return 0;
  if (operand->symbol_ref.has_name != 0U && operand->symbol_ref.name_is_generated == 0U &&
      visit_symbol_text_identifiers(operand->symbol_ref.name, operand->symbol_ref.name_provenance, visitor, context) != 0)
    return -1;
  if (operand->symbol_ref.has_symbolic_addend != 0U && operand->symbol_ref.symbolic_addend_name[0] != '\0' &&
      visit_symbol_text_identifiers(operand->symbol_ref.symbolic_addend_name,
        operand->symbol_ref.symbolic_addend_provenance, visitor, context) != 0)
    return -1;
  return 0;
}

static int visit_expr_text_symbols(const char *expr_text, RenderSymbolVisitor visitor, void *context) {
  const char *cursor = expr_text;
  if (expr_text == NULL || visitor == NULL) return 0;
  while (*cursor != '\0') {
    const char *start;
    char symbol_name[64];
    size_t length = 0U;
    if (!((*cursor >= 'A' && *cursor <= 'Z') || (*cursor >= 'a' && *cursor <= 'z') || *cursor == '_')) {
      ++cursor;
      continue;
    }
    start = cursor;
    while ((*cursor >= 'A' && *cursor <= 'Z') || (*cursor >= 'a' && *cursor <= 'z') ||
           (*cursor >= '0' && *cursor <= '9') || *cursor == '_') {
      if (length + 1U < sizeof(symbol_name)) symbol_name[length++] = *cursor;
      ++cursor;
    }
    if (length == 0U) continue;
    symbol_name[length] = '\0';
    if (start != expr_text) {
      char previous = start[-1];
      if ((previous >= 'A' && previous <= 'Z') || (previous >= 'a' && previous <= 'z') ||
          (previous >= '0' && previous <= '9') || previous == '_')
        continue;
    }
    if (visitor(symbol_name, M68K_IR_SYMBOL_PROVENANCE_NONE, context) != 0) return -1;
  }
  return 0;
}

static int append_or_update_render_include(RenderInclude *includes, size_t *inout_include_count,
    size_t include_capacity, const char *path) {
  size_t include_index;
  if (includes == NULL || inout_include_count == NULL || path == NULL || path[0] == '\0') return -1;
  for (include_index = 0; include_index < *inout_include_count; ++include_index) {
    if (strcmp(includes[include_index].path, path) == 0) return 0;
  }
  if (*inout_include_count >= include_capacity) return -1;
  snprintf(includes[*inout_include_count].path, sizeof(includes[*inout_include_count].path), "%s", path);
  ++(*inout_include_count);
  return 0;
}

typedef struct RenderIncludeCollectorContext {
  RenderInclude *includes;
  size_t *include_count;
  size_t include_capacity;
  const M68kSourceFileIR *source_file;
  RenderSymbolIncludeCache *include_cache;
} RenderIncludeCollectorContext;

static int collect_needed_include_symbol(const char *name, uint8_t provenance, void *opaque) {
  RenderIncludeCollectorContext *context = (RenderIncludeCollectorContext *)opaque;
  const char *include_path;
  include_path = lookup_symbol_include_path_cached(context->include_cache, context->source_file, name, provenance);
  if (include_path == NULL) return 0;
  return append_or_update_render_include(context->includes, context->include_count, context->include_capacity, include_path);
}

static int collect_needed_includes(RenderInclude *includes, size_t *out_include_count, size_t include_capacity,
    const M68kSourceFileIR *source_file, RenderSymbolIncludeCache *include_cache) {
  size_t section_index;
  RenderIncludeCollectorContext context;
  *out_include_count = 0U;
  context.includes = includes;
  context.include_count = out_include_count;
  context.include_capacity = include_capacity;
  context.source_file = source_file;
  context.include_cache = include_cache;
  for (section_index = 0; section_index < source_file->section_count; ++section_index) {
    const M68kSectionIR *section = &source_file->sections[section_index];
    size_t stmt_index;
    for (stmt_index = 0; stmt_index < section->statement_count; ++stmt_index) {
      const M68kStatementIR *stmt = &section->statements[stmt_index];
      size_t operand_index;
      if (stmt->kind == M68K_STATEMENT_INSTRUCTION) {
        for (operand_index = 0; operand_index < stmt->u.instruction.operand_count; ++operand_index) {
          if (visit_operand_symbol_refs(&stmt->u.instruction.operands[operand_index], collect_needed_include_symbol, &context) != 0)
            return -1;
        }
      } else if (stmt->kind == M68K_STATEMENT_DATA) {
        if (visit_expr_text_symbols(stmt->u.data.expr_text, collect_needed_include_symbol, &context) != 0) return -1;
      }
    }
  }
  return 0;
}

static int validate_amiga_compatibility_requirement(const char *kind, const char *name,
    uint16_t required_since_version, uint16_t compatibility_level, M68kDiagSink diagnostics) {
  const char *required_since_name;
  const char *min_os_version_name;
  char message[160];
  if (required_since_version == 0U) return 0;
  if (compatibility_level == 0U) return 0;
  required_since_name = amiga_os_compatibility_version_name((AmigaOsCompatVersion)required_since_version);
  min_os_version_name = amiga_os_compatibility_version_name((AmigaOsCompatVersion)compatibility_level);
  if (required_since_name == NULL || min_os_version_name == NULL) {
    render_error(diagnostics, "missing KB compatibility version");
    return -1;
  }
  if (required_since_version <= compatibility_level) return 0;
  snprintf(message, sizeof(message), "%s %s requires OS %s above minimum OS version %s",
    kind, name, required_since_name, min_os_version_name);
  render_error(diagnostics, message);
  return -1;
}

static int validate_amiga_include_compatibility(const char *include_path, uint16_t compatibility_level,
    M68kDiagSink diagnostics) {
  uint16_t required_since_version;
  if (include_path == NULL || include_path[0] == '\0') return 0;
  required_since_version = (uint16_t)amiga_os_find_include_min_compat_version(include_path);
  return validate_amiga_compatibility_requirement("Amiga include", include_path, required_since_version,
    compatibility_level, diagnostics);
}

static int validate_amiga_symbol_compatibility(const char *symbol_name, uint16_t compatibility_level,
    M68kDiagSink diagnostics) {
  const AmigaOsLibraryVectorInfo *entry;
  if (symbol_name == NULL || symbol_name[0] == '\0') return 0;
  entry = amiga_os_find_library_vector_by_symbol_name(symbol_name);
  if (entry == NULL) return 0;
  return validate_amiga_compatibility_requirement("Amiga symbol", symbol_name, entry->available_since_version,
    compatibility_level, diagnostics);
}

typedef struct AmigaCompatibilitySymbolContext {
  uint16_t compatibility_level;
  M68kDiagSink diagnostics;
} AmigaCompatibilitySymbolContext;

static int validate_amiga_symbol_compatibility_visitor(const char *name, uint8_t provenance, void *opaque) {
  AmigaCompatibilitySymbolContext *context = (AmigaCompatibilitySymbolContext *)opaque;
  if (context == NULL) return -1;
  if (provenance == M68K_IR_SYMBOL_PROVENANCE_PLATFORM_ATARI_ST) return 0;
  return validate_amiga_symbol_compatibility(name, context->compatibility_level, context->diagnostics);
}

static int validate_amiga_compatibility_floor(const M68kSourceFileIR *source_file, const RenderInclude *includes,
    size_t include_count, uint16_t compatibility_level, M68kDiagSink diagnostics) {
  size_t include_index;
  size_t section_index;
  AmigaCompatibilitySymbolContext context;
  if (source_file == NULL || compatibility_level == 0U) return 0;
  if (source_file->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 0;
  for (include_index = 0U; include_index < include_count; ++include_index) {
    if (validate_amiga_include_compatibility(includes[include_index].path, compatibility_level, diagnostics) != 0) return -1;
  }
  context.compatibility_level = compatibility_level;
  context.diagnostics = diagnostics;
  for (section_index = 0U; section_index < source_file->section_count; ++section_index) {
    const M68kSectionIR *section = &source_file->sections[section_index];
    size_t stmt_index;
    for (stmt_index = 0U; stmt_index < section->statement_count; ++stmt_index) {
      const M68kStatementIR *stmt = &section->statements[stmt_index];
      size_t operand_index;
      if (stmt->kind == M68K_STATEMENT_INSTRUCTION) {
        for (operand_index = 0U; operand_index < stmt->u.instruction.operand_count; ++operand_index) {
          if (visit_operand_symbol_refs(&stmt->u.instruction.operands[operand_index],
                validate_amiga_symbol_compatibility_visitor, &context) != 0) {
            return -1;
          }
        }
      } else if (stmt->kind == M68K_STATEMENT_DATA) {
        if (visit_expr_text_symbols(stmt->u.data.expr_text, validate_amiga_symbol_compatibility_visitor, &context) != 0)
          return -1;
      }
    }
  }
  return 0;
}

static int32_t render_equate_value(const M68kStatementIR *stmt, const M68kOperandIR *operand) {
  const AmigaOsLibraryVectorInfo *amiga_vector;
  const AtariStOsCallInfo *atari_call;
  if (operand != NULL && operand->symbol_ref.has_name != 0U && operand->symbol_ref.name_is_generated == 0U) {
    atari_call = atari_st_os_find_call_by_symbol_name(operand->symbol_ref.name);
    if (atari_call != NULL) return atari_call->opcode;
    amiga_vector = amiga_os_find_library_vector_by_symbol_name(operand->symbol_ref.name);
    if (amiga_vector != NULL) return amiga_vector->lvo;
  }
  if (stmt != NULL && operand != NULL && operand->kind == M68K_ASM_OPERAND_IMM &&
      stmt->u.instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ) {
    return (int32_t)m68k_sign_extend32(operand->value.value, 8U);
  }
  return (int16_t)(operand != NULL ? (operand->value.value & 0xFFFFU) : 0U);
}

static int append_or_update_render_equate_with_extent(RenderEquate *equates, size_t *inout_equate_count,
    size_t equate_capacity, const char *name, int32_t value, int32_t min_extent) {
  size_t equate_index;
  if (equates == NULL || inout_equate_count == NULL || name == NULL || name[0] == '\0') return -1;
  for (equate_index = 0; equate_index < *inout_equate_count; ++equate_index) {
    if (strcmp(equates[equate_index].name, name) == 0) {
      equates[equate_index].value = value;
      if (min_extent > equates[equate_index].min_extent) equates[equate_index].min_extent = min_extent;
      return 0;
    }
  }
  if (*inout_equate_count >= equate_capacity) return -1;
  snprintf(equates[*inout_equate_count].name, sizeof(equates[*inout_equate_count].name), "%s", name);
  equates[*inout_equate_count].value = value;
  equates[*inout_equate_count].min_extent = min_extent;
  equates[*inout_equate_count].consumed = 0U;
  ++(*inout_equate_count);
  return 0;
}

static int append_or_update_render_equate(RenderEquate *equates, size_t *inout_equate_count,
    size_t equate_capacity, const char *name, int32_t value) {
  return append_or_update_render_equate_with_extent(equates, inout_equate_count, equate_capacity, name, value, 0);
}

static int render_equate_compare_by_value_then_name(const void *left, const void *right) {
  const RenderEquate *left_equate = (const RenderEquate *)left;
  const RenderEquate *right_equate = (const RenderEquate *)right;
  if (left_equate->value < right_equate->value) return -1;
  if (left_equate->value > right_equate->value) return 1;
  return strcmp(left_equate->name, right_equate->name);
}

static int render_equate_is_app_extension_symbol(const RenderEquate *equate, int32_t base_offset) {
  if (equate == NULL || base_offset < 0) return 0;
  if (strncmp(equate->name, "app_", 4U) != 0) return 0;
  if (strcmp(equate->name, "app_SIZEOF") == 0) return 0;
  if (equate->value < base_offset) return 0;
  return 1;
}

static void format_render_equate_value(int32_t value, char *out_text, size_t out_text_size) {
  if (out_text == NULL || out_text_size == 0U) return;
  if (value >= 0) snprintf(out_text, out_text_size, "$%X", (unsigned)value);
  else snprintf(out_text, out_text_size, "%d", (int)value);
}

static int append_exact_rs_byte_gap(JsonBuilder *builder, int32_t gap, const char *directive_prefix) {
  if (gap <= 0) return 0;
  return json_builder_appendf(builder, "%sRS.B %d\n", directive_prefix, (int)gap);
}

static int append_needed_amiga_app_extension_rs(JsonBuilder *builder, RenderEquate *equates, size_t equate_count,
    const M68kSourceFileIR *source_file, const RenderLabelIndexes *label_indexes, uint8_t has_app_sizeof_value,
    int32_t app_sizeof_value, uint8_t syntax_mode) {
  RenderEquate slots[64];
  size_t slot_count = 0U;
  size_t index;
  int32_t lib_size = 0;
  int32_t base_offset = 0;
  int has_resident_library_context;
  int32_t cursor;
  int32_t inferred_sizeof = 0;
  const char *directive_prefix = syntax_mode == M68K_IR_SYNTAX_VASM ? "    " : "";
  if (builder == NULL) return 0;
  has_resident_library_context = source_file_has_amiga_resident_library_context(source_file, label_indexes);
  if (has_resident_library_context) {
    if (!amiga_os_find_constant_value("LIB_SIZE", &lib_size) || lib_size <= 0) return 0;
    base_offset = lib_size;
  }
  for (index = 0U; index < equate_count; ++index) {
    int32_t extent_end;
    if (!render_equate_is_app_extension_symbol(&equates[index], base_offset)) continue;
    if (slot_count >= sizeof(slots) / sizeof(slots[0])) return -1;
    slots[slot_count++] = equates[index];
    equates[index].consumed = 1U;
    extent_end = equates[index].value + equates[index].min_extent;
    if (extent_end > inferred_sizeof) inferred_sizeof = extent_end;
  }
  if (slot_count == 0U && has_app_sizeof_value == 0U) return 0;
  qsort(slots, slot_count, sizeof(slots[0]), render_equate_compare_by_value_then_name);
  if (has_resident_library_context) {
    if (json_builder_appendf(builder, "%sRSSET LIB_SIZE\n", directive_prefix) != 0) return -1;
  } else {
    if (json_builder_appendf(builder, "%sRSSET 0\n", directive_prefix) != 0) return -1;
  }
  cursor = base_offset;
  for (index = 0U; index < slot_count; ++index) {
    if (slots[index].value > cursor) {
      int32_t gap = slots[index].value - cursor;
      if (append_exact_rs_byte_gap(builder, gap, directive_prefix) != 0) return -1;
      cursor = slots[index].value;
    }
    if (slots[index].value < cursor) {
      char value_text[32];
      format_render_equate_value(slots[index].value, value_text, sizeof(value_text));
      if (json_builder_appendf(builder, "%s EQU %s\n", slots[index].name, value_text) != 0) return -1;
    } else if ((cursor & 1) == 0) {
      if (json_builder_appendf(builder, "%s RS.L 1\n", slots[index].name) != 0) return -1;
      cursor += 4;
    } else {
      if (json_builder_appendf(builder, "%s RS.B 1\n", slots[index].name) != 0) return -1;
      cursor += 1;
    }
  }
  {
    int32_t target_sizeof = has_app_sizeof_value != 0U ? app_sizeof_value : inferred_sizeof;
    if (inferred_sizeof > target_sizeof) target_sizeof = inferred_sizeof;
    if (target_sizeof > cursor) {
      int32_t gap = target_sizeof - cursor;
      if (append_exact_rs_byte_gap(builder, gap, directive_prefix) != 0) return -1;
    }
  }
  if (json_builder_append(builder, "app_SIZEOF EQU __RS\n\n") != 0) return -1;
  return 0;
}

typedef struct RenderEquateCollectorContext {
  RenderEquate *equates;
  size_t *equate_count;
  size_t equate_capacity;
  const M68kSourceFileIR *source_file;
  const RenderLabelIndexes *label_indexes;
  RenderSymbolIncludeCache *include_cache;
} RenderEquateCollectorContext;

static int collect_data_expr_equate_symbol(const char *name, uint8_t provenance, void *opaque) {
  RenderEquateCollectorContext *context = (RenderEquateCollectorContext *)opaque;
  int32_t value;
  if (lookup_symbol_include_path_cached(context->include_cache, context->source_file, name, provenance) != NULL) return 0;
  if (source_file_has_label_name(context->source_file, context->label_indexes, name)) return 0;
  if (!lookup_symbol_equate_value(name, &value)) return 0;
  return append_or_update_render_equate(context->equates, context->equate_count, context->equate_capacity, name, value);
}

static int append_needed_equates(JsonBuilder *builder, const M68kSourceFileIR *source_file,
    const RenderLabelIndexes *label_indexes, RenderSymbolIncludeCache *include_cache, uint8_t syntax_mode) {
  RenderEquate equates[128];
  size_t equate_count = 0U;
  size_t section_index;
  uint8_t has_app_sizeof_value = 0U;
  int32_t app_sizeof_value = 0;
  RenderEquateCollectorContext context;
  context.equates = equates;
  context.equate_count = &equate_count;
  context.equate_capacity = sizeof(equates) / sizeof(equates[0]);
  context.source_file = source_file;
  context.label_indexes = label_indexes;
  context.include_cache = include_cache;
  for (section_index = 0; section_index < source_file->section_count; ++section_index) {
    const M68kSectionIR *section = &source_file->sections[section_index];
    size_t stmt_index;
    for (stmt_index = 0; stmt_index < section->statement_count; ++stmt_index) {
      const M68kStatementIR *stmt = &section->statements[stmt_index];
      size_t operand_index;
        if (stmt->kind == M68K_STATEMENT_DATA) {
          if (stmt->u.data.expr_text != NULL && strcmp(stmt->u.data.expr_text, "app_SIZEOF") == 0 &&
              stmt->u.data.data != NULL && stmt->u.data.size == 4U) {
            uint32_t raw_value = ((uint32_t)stmt->u.data.data[0] << 24) | ((uint32_t)stmt->u.data.data[1] << 16) |
              ((uint32_t)stmt->u.data.data[2] << 8) | (uint32_t)stmt->u.data.data[3];
            has_app_sizeof_value = 1U;
            app_sizeof_value = (int32_t)raw_value;
          }
          if (visit_expr_text_symbols(stmt->u.data.expr_text, collect_data_expr_equate_symbol, &context) != 0) return -1;
          continue;
        }
        if (stmt->kind != M68K_STATEMENT_INSTRUCTION) continue;
          for (operand_index = 0; operand_index < stmt->u.instruction.operand_count; ++operand_index) {
            const M68kOperandIR *operand = &stmt->u.instruction.operands[operand_index];
            int32_t total_value;
            if (operand->symbol_ref.has_name == 0U || operand->symbol_ref.name_is_generated != 0U) continue;
            if (strpbrk(operand->symbol_ref.name, "|+-*/&^~()") != NULL) {
              if (visit_symbol_text_identifiers(operand->symbol_ref.name, operand->symbol_ref.name_provenance,
                    collect_data_expr_equate_symbol, &context) != 0) {
                return -1;
              }
              if (operand->symbol_ref.has_symbolic_addend != 0U &&
                  operand->symbol_ref.symbolic_addend_name[0] != '\0' &&
                  visit_symbol_text_identifiers(operand->symbol_ref.symbolic_addend_name,
                    operand->symbol_ref.symbolic_addend_provenance, collect_data_expr_equate_symbol, &context) != 0) {
                return -1;
              }
              continue;
            }
            if (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) {
              if (operand->value.ea_mode != 5U &&
                  !(operand->value.ea_mode == 7U && operand->value.ea_reg == 4U)) {
                continue;
              }
            } else if (operand->kind != M68K_ASM_OPERAND_IMM) {
              continue;
            }
            total_value = render_equate_value(stmt, operand);
            if (operand->symbol_ref.has_symbolic_addend != 0U &&
                operand->symbol_ref.symbolic_addend_name[0] != '\0') {
              if (lookup_symbol_include_path_cached(include_cache, source_file, operand->symbol_ref.name,
                    operand->symbol_ref.name_provenance) == NULL &&
                  !source_file_has_label_name(source_file, label_indexes, operand->symbol_ref.name)) {
                if (append_or_update_render_equate_with_extent(equates, &equate_count,
                      sizeof(equates) / sizeof(equates[0]), operand->symbol_ref.name,
                      total_value - operand->symbol_ref.symbolic_addend_value,
                      (int32_t)operand->symbol_ref.symbolic_addend_value) != 0) {
                  return -1;
                }
              }
              if (lookup_symbol_include_path_cached(include_cache, source_file, operand->symbol_ref.symbolic_addend_name,
                    operand->symbol_ref.symbolic_addend_provenance) == NULL &&
                  !source_file_has_label_name(source_file, label_indexes, operand->symbol_ref.symbolic_addend_name)) {
                if (append_or_update_render_equate(equates, &equate_count, sizeof(equates) / sizeof(equates[0]),
                      operand->symbol_ref.symbolic_addend_name, operand->symbol_ref.symbolic_addend_value) != 0) {
                  return -1;
                }
              }
              continue;
            }
            if (lookup_symbol_include_path_cached(include_cache, source_file, operand->symbol_ref.name,
                  operand->symbol_ref.name_provenance) == NULL &&
                !source_file_has_label_name(source_file, label_indexes, operand->symbol_ref.name)) {
              if (append_or_update_render_equate(equates, &equate_count, sizeof(equates) / sizeof(equates[0]),
                    operand->symbol_ref.name, total_value) != 0) {
                return -1;
              }
            }
      }
    }
  }
  if (append_needed_amiga_app_extension_rs(builder, equates, equate_count, source_file, label_indexes, has_app_sizeof_value,
        app_sizeof_value, syntax_mode) != 0) return -1;
  for (section_index = 0; section_index < equate_count; ++section_index) {
    char value_text[32];
    if (equates[section_index].consumed != 0U) continue;
    format_render_equate_value(equates[section_index].value, value_text, sizeof(value_text));
    if (json_builder_appendf(builder, "%s EQU %s\n", equates[section_index].name, value_text) != 0)
      return -1;
  }
  if (equate_count != 0U && json_builder_append(builder, "\n") != 0) return -1;
  return 0;
}

int m68k_source_ir_render_text_with_policy(const M68kSourceFileIR *source_file, const M68kRenderPolicy *policy,
    char **out_text, M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  RenderLabelIndexes label_indexes;
  RenderSymbolIncludeCache include_cache;
  RenderInclude includes[32];
  size_t include_count = 0U;
  size_t section_index;
  M68kRenderPolicy default_policy;
  const M68kRenderPolicy *active_policy = policy;
  const char *min_os_version_name = NULL;
  if (source_file == NULL || out_text == NULL) {
    render_error(diagnostics, "bad arguments");
    return -1;
  }
  if (active_policy == NULL) {
    m68k_render_policy_init_default(&default_policy);
    active_policy = &default_policy;
  }
  memset(&label_indexes, 0, sizeof(label_indexes));
  memset(&include_cache, 0, sizeof(include_cache));
  if (!render_label_indexes_build(&label_indexes, source_file)) goto oom;
  if (json_builder_create(&builder) != 0) goto oom;
  if (collect_needed_includes(includes, &include_count, sizeof(includes) / sizeof(includes[0]), source_file,
      &include_cache) != 0) goto oom;
  if (active_policy->os.compatibility_kind == M68K_OS_COMPATIBILITY_AMIGA &&
      active_policy->os.compatibility_level != 0U) {
    min_os_version_name = amiga_os_compatibility_version_name((AmigaOsCompatVersion)active_policy->os.compatibility_level);
    if (min_os_version_name == NULL) {
      json_builder_destroy(&builder);
      render_label_indexes_destroy(&label_indexes);
      render_symbol_include_cache_destroy(&include_cache);
      render_error(diagnostics, "invalid minimum os version");
      return -1;
    }
    if (validate_amiga_compatibility_floor(source_file, includes, include_count, active_policy->os.compatibility_level,
        diagnostics) != 0) {
      json_builder_destroy(&builder);
      render_label_indexes_destroy(&label_indexes);
      render_symbol_include_cache_destroy(&include_cache);
      return -1;
    }
    if (source_file->platform_backend_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK &&
        json_builder_appendf(&builder, "; Minimum OS version: %s\n", min_os_version_name) != 0) {
      goto oom;
    }
  }
  for (section_index = 0; section_index < include_count; ++section_index) {
    const char *include_prefix = active_policy->syntax.syntax_mode == M68K_IR_SYNTAX_VASM ? "    " : "";
    if (json_builder_appendf(&builder, "%sINCLUDE \"%s\"\n", include_prefix, includes[section_index].path) != 0)
      goto oom;
  }
  if (include_count != 0U && json_builder_append(&builder, "\n") != 0) goto oom;
  if (append_needed_equates(&builder, source_file, &label_indexes, &include_cache,
      active_policy->syntax.syntax_mode) != 0) goto oom;
  if (source_file->has_atari_st_program_flags != 0U &&
      json_builder_appendf(&builder, "    COMMENT HEAD=$%x\n", (unsigned)source_file->atari_st_program_flags) != 0)
    goto oom;
  for (section_index = 0; section_index < source_file->section_count; ++section_index) {
    const M68kSectionIR *section = &source_file->sections[section_index];
    size_t stmt_index;
    char section_name_buffer[96];
    char section_kind_buffer[32];
    const char *section_name = rendered_section_name(source_file, section_index, section_name_buffer,
      sizeof(section_name_buffer));
    if (!m68k_format_section_spec(section->kind, section->platform_mem_type, section->platform_mem_attrs,
          section_kind_buffer, sizeof(section_kind_buffer)))
      goto oom;
    if (section->size != section->data_size) {
      if (json_builder_appendf(&builder, "    SECTION %s,%s,$%X\n", section_name, section_kind_buffer,
            (unsigned)section->size) != 0)
        goto oom;
    } else if (json_builder_appendf(&builder, "    SECTION %s,%s\n", section_name,
        section_kind_buffer) != 0) {
      goto oom;
    }
    for (stmt_index = 0; stmt_index < section->statement_count; ++stmt_index) {
      const M68kStatementIR *stmt = &section->statements[stmt_index];
      if (stmt->kind == M68K_STATEMENT_LABEL) {
        size_t line_start;
        if (stmt->comment != NULL && stmt->comment[0] != '\0' && strncmp(stmt->comment, "STRUCT ", 7) != 0 &&
            json_builder_appendf(&builder, "    ; %s\n", stmt->comment) != 0)
          goto oom;
        line_start = builder.size;
        if (json_builder_appendf(&builder, "%s:", stmt->label_name != NULL ? stmt->label_name : "label") != 0) goto oom;
        if (stmt->comment != NULL && strncmp(stmt->comment, "STRUCT ", 7) == 0) {
          if (append_statement_comment(&builder, stmt, line_start) != 0) goto oom;
        } else if (json_builder_append(&builder, "\n") != 0) goto oom;
      } else if (stmt->kind == M68K_STATEMENT_ALIGN) {
        if (json_builder_append(&builder, "    EVEN\n") != 0) goto oom;
      } else if (stmt->kind == M68K_STATEMENT_RESERVE) {
        size_t line_start = builder.size;
        if (json_builder_appendf(&builder, "    DS.B    $%X", (unsigned)stmt->u.reserve_size) != 0) goto oom;
        if (append_statement_comment(&builder, stmt, line_start) != 0) goto oom;
      } else if (stmt->kind == M68K_STATEMENT_INSTRUCTION) {
        M68kInstructionIR rendered_instruction = stmt->u.instruction;
        M68kDiagList render_diagnostics;
        M68kIrRenderResult rendered;
        size_t line_start;
        size_t operand_index;
        m68k_diag_list_reset(&render_diagnostics);
        for (operand_index = 0; operand_index < rendered_instruction.operand_count; ++operand_index) {
          M68kOperandIR *operand = &rendered_instruction.operands[operand_index];
          if (operand->symbol_ref.has_name == 0U) continue;
          if (operand->symbol_ref.name_is_generated != 0U &&
              !render_section_has_label_name(&label_indexes, section_index, section, operand->symbol_ref.name)) {
            operand->symbol_ref.has_name = 0U;
          }
        }
        if (instruction_renders_with_fpu_mnemonic(&rendered_instruction)) {
          if (!make_fpu_id_render_instruction(&rendered_instruction, &rendered_instruction)) {
            render_error(diagnostics, "unable to render coprocessor instruction");
            json_builder_destroy(&builder);
            render_label_indexes_destroy(&label_indexes);
            render_symbol_include_cache_destroy(&include_cache);
            return -1;
          }
          if (instruction_needs_fpu_id_directive(&stmt->u.instruction) &&
              json_builder_appendf(&builder, "    FPU     %u\n",
                (unsigned)stmt->u.instruction.coprocessor_id) != 0)
            goto oom;
          m68k_diag_list_reset(&render_diagnostics);
        }
        rendered = m68k_ir_render_one_at_with_policy(&rendered_instruction, stmt->offset, active_policy,
          m68k_diag_sink(&render_diagnostics));
        if (m68k_diag_has_errors(&render_diagnostics)) {
          render_error(diagnostics, m68k_diag_first_message(&render_diagnostics));
          json_builder_destroy(&builder);
          render_label_indexes_destroy(&label_indexes);
          render_symbol_include_cache_destroy(&include_cache);
          return -1;
        }
        line_start = builder.size;
        if (json_builder_appendf(&builder, "    %s", rendered.text) != 0) goto oom;
        if (append_statement_comment(&builder, stmt, line_start) != 0) goto oom;
        if (instruction_needs_fpu_id_directive(&stmt->u.instruction) &&
            json_builder_append(&builder, "    FPU     1\n") != 0)
          goto oom;
      } else if (stmt->kind == M68K_STATEMENT_DATA) {
        size_t line_start = builder.size;
        if (append_rendered_data_stmt(&builder, &stmt->u.data, active_policy) != 0) goto oom;
        if (append_statement_comment(&builder, stmt, line_start) != 0) goto oom;
      }
    }
  }
  *out_text = json_builder_build(&builder);
  if (*out_text == NULL) goto oom;
  json_builder_destroy(&builder);
  render_label_indexes_destroy(&label_indexes);
  render_symbol_include_cache_destroy(&include_cache);
  return 0;

oom:
  json_builder_destroy(&builder);
  render_label_indexes_destroy(&label_indexes);
  render_symbol_include_cache_destroy(&include_cache);
  render_error(diagnostics, "out of memory");
  return -1;
}
