#include "m68k_render_lookup_internal.h"

#include "m68k_assembler.h"
#include "m68k_instruction_spec.h"
#include "m68k_ir_codec.h"
#include "m68k_parse_util.h"
#include "m68k_plain_parse.h"
#include "m68k_simulator.h"
#include "m68k_source_pipeline.h"
#include "m68k_source_text_util.h"
#include "platform_atari_st.h"
#include "platform_common.h"
#include "util_arena.h"
#include "generated/amiga_hunk_file_runtime.h"
#include "generated/m68k_cpu_runtime.h"
#include "generated/amiga_os_runtime.h"

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double elapsed_seconds_local(clock_t start, clock_t end) {
  return (double)(end - start) / (double)CLOCKS_PER_SEC;
}

char ascii_lower_local(char c) {
  return (c >= 'A' && c <= 'Z') ? (char)(c - 'A' + 'a') : c;
}

int ascii_char_is_symbol_local(char c, int first) {
  if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || c == '_' || c == '.') return 1;
  if (!first && c >= '0' && c <= '9') return 1;
  return 0;
}

int asm_symbol_name_is_safe_local(const char *name) {
  size_t index;
  if (name == NULL || name[0] == '\0') return 0;
  for (index = 0U; name[index] != '\0'; ++index) {
    if (!ascii_char_is_symbol_local(name[index], index == 0U)) return 0;
  }
  return 1;
}

int ascii_contains_case_local(const char *text, const char *needle) {
  size_t text_index;
  size_t needle_len;
  if (text == NULL || needle == NULL || needle[0] == '\0') return 0;
  needle_len = strlen(needle);
  for (text_index = 0U; text[text_index] != '\0'; ++text_index) {
    size_t needle_index;
    for (needle_index = 0U; needle_index < needle_len; ++needle_index) {
      if (text[text_index + needle_index] == '\0') return 0;
      if (ascii_lower_local(text[text_index + needle_index]) != ascii_lower_local(needle[needle_index])) break;
    }
    if (needle_index == needle_len) return 1;
  }
  return 0;
}

const char *amiga_library_name_from_base_symbol_name(const char *symbol_name) {
  const char *matched_library = NULL;
  size_t index;
  if (symbol_name == NULL || symbol_name[0] == '\0') return NULL;
  if (ascii_contains_case_local(symbol_name, "ExecBase")) return amiga_os_exec_base_library_name();
  for (index = 0U; index < AMIGA_OS_LIBRARY_VECTOR_COUNT; ++index) {
    const AmigaOsLibraryVectorInfo *vector = amiga_os_library_vector_at(index);
    const char *base_name;
    const char *library_name;
    if (vector == NULL) continue;
    base_name = amiga_os_name(M68K_PLATFORM_NAME_BASE, vector->base_id);
    if (base_name == NULL || base_name[0] == '\0') continue;
    if (!ascii_contains_case_local(symbol_name, base_name)) continue;
    library_name = amiga_os_find_library_name_by_base_name(base_name);
    if (library_name == NULL || library_name[0] == '\0') continue;
    if (matched_library == NULL) {
      matched_library = library_name;
    } else if (strcmp(matched_library, library_name) != 0) {
      return NULL;
    }
  }
  return matched_library;
}

static uint64_t hash_step(uint64_t hash, uint64_t value) {
  hash ^= value;
  hash *= 1099511628211ULL;
  return hash;
}

static void hash_statement(M68kRenderIRPreview *preview, uint8_t kind, size_t section_index, uint32_t offset,
    uint32_t size, uint32_t aux) {
  preview->structural_hash = hash_step(preview->structural_hash, kind);
  preview->structural_hash = hash_step(preview->structural_hash, (uint64_t)section_index);
  preview->structural_hash = hash_step(preview->structural_hash, offset);
  preview->structural_hash = hash_step(preview->structural_hash, size);
  preview->structural_hash = hash_step(preview->structural_hash, aux);
}

static void render_text_line(M68kRenderIRPreview *preview, char kind, size_t section_index, uint32_t offset,
    uint32_t size, uint32_t aux) {
  char line[96];
  int length;
  size_t index;
  if (preview == NULL) return;
  length = snprintf(line, sizeof(line), "%c %u %08X %u %u\n", kind, (unsigned)section_index,
    (unsigned)offset, (unsigned)size, (unsigned)aux);
  if (length <= 0) return;
  preview->text_bytes += (uint32_t)length;
  for (index = 0U; index < (size_t)length && index < sizeof(line); ++index)
    preview->text_hash = hash_step(preview->text_hash, (unsigned char)line[index]);
}

static void hash_asm_text(M68kRenderIRPreview *preview, const char *text) {
  size_t index;
  size_t length;
  if (preview == NULL || text == NULL) return;
  length = strlen(text);
  if (preview->collect_asm_source_text) {
    if (length > (size_t)UINT32_MAX - (size_t)preview->asm_source_bytes) {
      preview->asm_source_allocation_failed = 1U;
    } else if (!preview->asm_source_row_builder.active) {
      preview->asm_source_allocation_failed = 1U;
    }
  }
  if (preview->collect_asm_source_hash) {
    for (index = 0U; index < length; ++index)
      preview->asm_source_hash = hash_step(preview->asm_source_hash, (unsigned char)text[index]);
  }
  if (preview->asm_source_row_builder.active &&
      m68k_render_plan_row_builder_append_span(&preview->asm_source_row_builder, text, length) != 0) {
    preview->asm_source_allocation_failed = 1U;
  }
  preview->asm_source_bytes += (uint32_t)length;
}

static void begin_asm_source_plan_row(M68kRenderIRPreview *preview, uint32_t kind, uint32_t region_id) {
  if (preview == NULL || !preview->collect_asm_source_text || preview->asm_source_row_builder.active) return;
  if (m68k_render_plan_row_builder_begin(&preview->asm_source_row_builder, &preview->asm_source_plan,
      kind, region_id) != 0) {
    preview->asm_source_allocation_failed = 1U;
  }
}

static M68kRenderPlanRow *finish_asm_source_plan_row(M68kRenderIRPreview *preview, size_t section_index,
    uint32_t source_offset, uint32_t source_size, int has_source_range) {
  M68kRenderPlanRow *row = NULL;
  if (preview == NULL || !preview->asm_source_row_builder.active) return NULL;
  if (preview->asm_source_row_builder.size == 0U) {
    m68k_render_plan_row_builder_cancel(&preview->asm_source_row_builder);
    return NULL;
  }
  if (m68k_render_plan_row_builder_commit(&preview->asm_source_row_builder, &row) != 0) {
    preview->asm_source_allocation_failed = 1U;
    return NULL;
  }
  if (has_source_range && row != NULL) {
    m68k_render_plan_row_set_source_range(row, (uint32_t)section_index, source_offset, source_size);
  }
  return row;
}

static void cancel_asm_source_plan_row(M68kRenderIRPreview *preview) {
  if (preview == NULL || !preview->asm_source_row_builder.active) return;
  m68k_render_plan_row_builder_cancel(&preview->asm_source_row_builder);
}

static void set_asm_source_plan_row_statement_from_section(M68kRenderPlanRow *row, uint8_t statement_kind,
    const M68kInstructionIR *instruction, const M68kDecodeSectionIR *section, uint32_t offset, uint32_t size) {
  const uint8_t *source_bytes = NULL;
  size_t source_byte_count = 0U;
  if (row == NULL) return;
  if (section != NULL && section->data != NULL && size != 0U && offset < section->size) {
    source_byte_count = size;
    if (source_byte_count > section->size - offset) source_byte_count = section->size - offset;
    source_bytes = section->data + offset;
  }
  m68k_render_plan_row_set_statement_metadata(row, statement_kind, instruction, source_bytes, source_byte_count);
}

static int store_asm_source_declaration_line(M68kRenderIRPreview *preview, const char *line) {
  char *copy;
  if (preview == NULL || line == NULL ||
      preview->asm_source_declaration_count >= M68K_RENDER_ASM_DECLARATION_LIMIT)
    return 0;
  if (preview->asm_source_header_arena == NULL) {
    preview->asm_source_header_arena = arena_create(4096U);
    if (preview->asm_source_header_arena == NULL) return 0;
  }
  copy = arena_strdup(preview->asm_source_header_arena, line);
  if (copy == NULL) return 0;
  preview->asm_source_declaration_lines[preview->asm_source_declaration_count] = copy;
  return 1;
}

static Arena *render_preview_scratch_arena(M68kRenderIRPreview *preview) {
  if (preview == NULL) return NULL;
  if (preview->scratch_arena == NULL) {
    preview->scratch_arena = arena_create(4096U);
    if (preview->scratch_arena == NULL) return NULL;
  }
  return preview->scratch_arena;
}

static int compare_asm_source_include_paths(const void *left, const void *right) {
  const char *const *left_path = (const char *const *)left;
  const char *const *right_path = (const char *const *)right;
  return strcmp(*left_path, *right_path);
}

static void recompute_asm_source_plan_metrics(M68kRenderIRPreview *preview, const M68kRenderPlan *plan);

static int append_asm_source_plan_row_copy(M68kRenderPlan *dest, const M68kRenderPlanRow *source) {
  M68kRenderPlanRow *row = NULL;
  if (dest == NULL || source == NULL) return 0;
  if (m68k_render_plan_append_text_row(dest, source->kind, source->region_id, source->text, &row) != 0)
    return 0;
  row->directive_line_mask = source->directive_line_mask;
  if (source->has_source_range)
    m68k_render_plan_row_set_source_range(row, source->source_section_index, source->source_offset,
      source->source_size);
  if (source->has_runtime_range)
    m68k_render_plan_row_set_runtime_range(row, source->runtime_address, source->runtime_size);
  if (source->has_statement) {
    row->has_statement = 1U;
    row->statement_index = source->statement_index;
  }
  if (source->has_statement_metadata) {
    m68k_render_plan_row_set_statement_metadata(row, source->statement_kind,
      source->statement_kind == M68K_STATEMENT_INSTRUCTION ? &source->statement_instruction : NULL,
      source->source_bytes, source->source_byte_count);
  }
  return 1;
}

static int assemble_asm_source_plan_regions(M68kRenderIRPreview *preview, int emit_source_text) {
  M68kRenderPlan final_plan;
  char *include_paths[M68K_RENDER_ASM_INCLUDE_LIMIT];
  char *source_text = NULL;
  size_t row_index;
  uint16_t index;
  if (preview == NULL) return 0;
  if (preview->asm_source_row_builder.active) cancel_asm_source_plan_row(preview);
  if (preview->asm_source_plan.total_bytes != (size_t)preview->asm_source_bytes) return 0;
  m68k_render_plan_init(&final_plan);
  for (index = 0U; index < preview->asm_source_include_count; ++index)
    include_paths[index] = preview->asm_source_includes[index];
  qsort(include_paths, preview->asm_source_include_count, sizeof(include_paths[0]), compare_asm_source_include_paths);
  for (index = 0U; index < preview->asm_source_include_count; ++index) {
    char line[128];
    int length = snprintf(line, sizeof(line), "    INCLUDE \"%s\"\n", include_paths[index]);
    if (length <= 0 || (size_t)length >= sizeof(line) ||
        m68k_render_plan_append_text_row(&final_plan, M68K_RENDER_PLAN_ROW_INCLUDE, 0U, line, NULL) != 0) {
      m68k_render_plan_destroy(&final_plan);
      return 0;
    }
  }
  if (preview->asm_source_include_count != 0U &&
      m68k_render_plan_append_text_row(&final_plan, M68K_RENDER_PLAN_ROW_BLANK, 0U, "\n", NULL) != 0) {
    m68k_render_plan_destroy(&final_plan);
    return 0;
  }
  for (row_index = 0U; row_index < preview->asm_source_plan.row_count; ++row_index) {
    const M68kRenderPlanRow *row = &preview->asm_source_plan.rows[row_index];
    if (row->start_byte >= (size_t)preview->asm_source_body_start_byte) continue;
    if (!append_asm_source_plan_row_copy(&final_plan, row)) {
      m68k_render_plan_destroy(&final_plan);
      return 0;
    }
  }
  for (index = 0U; index < preview->asm_source_declaration_count; ++index) {
    if (m68k_render_plan_append_text_row(&final_plan, M68K_RENDER_PLAN_ROW_EQUATE, 0U,
        preview->asm_source_declaration_lines[index], NULL) != 0) {
      m68k_render_plan_destroy(&final_plan);
      return 0;
    }
  }
  if ((preview->asm_source_include_count != 0U || preview->asm_source_declaration_count != 0U) &&
      m68k_render_plan_append_text_row(&final_plan, M68K_RENDER_PLAN_ROW_BLANK, 0U, "\n", NULL) != 0) {
    m68k_render_plan_destroy(&final_plan);
    return 0;
  }
  for (row_index = 0U; row_index < preview->asm_source_plan.row_count; ++row_index) {
    const M68kRenderPlanRow *row = &preview->asm_source_plan.rows[row_index];
    if (row->start_byte < (size_t)preview->asm_source_body_start_byte) continue;
    if (!append_asm_source_plan_row_copy(&final_plan, row)) {
      m68k_render_plan_destroy(&final_plan);
      return 0;
    }
  }
  free(preview->asm_source_text);
  preview->asm_source_text = NULL;
  preview->asm_source_text_capacity = 0U;
  if (emit_source_text) {
    if (m68k_render_plan_emit_all_alloc(&final_plan, &source_text) != 0) {
      m68k_render_plan_destroy(&final_plan);
      return 0;
    }
    preview->asm_source_text = source_text;
    preview->asm_source_text_capacity = final_plan.total_bytes + 1U;
  }
  recompute_asm_source_plan_metrics(preview, &final_plan);
  m68k_render_plan_move(&preview->asm_source_plan, &final_plan);
  return 1;
}

static void recompute_asm_source_plan_metrics(M68kRenderIRPreview *preview, const M68kRenderPlan *plan) {
  size_t row_index;
  if (preview == NULL || plan == NULL) return;
  preview->asm_source_bytes = 0U;
  preview->asm_source_lines = 0U;
  preview->asm_source_hash = 1469598103934665603ULL;
  for (row_index = 0U; row_index < plan->row_count; ++row_index) {
    const char *cursor = plan->rows[row_index].text;
    if (cursor == NULL) continue;
    while (*cursor != '\0') {
      if (preview->collect_asm_source_hash)
        preview->asm_source_hash = hash_step(preview->asm_source_hash, (unsigned char)*cursor);
      if (*cursor == '\n') ++preview->asm_source_lines;
      ++preview->asm_source_bytes;
      ++cursor;
    }
  }
}

static void format_asm_label(char *buf, size_t buf_size, size_t section_index, uint32_t offset) {
  if (buf == NULL || buf_size == 0U) return;
  snprintf(buf, buf_size, "loc_%u_%08X", (unsigned)section_index, (unsigned)offset);
}

static void format_runtime_asm_label(const M68kRenderLookup *lookup, char *buf, size_t buf_size,
    size_t section_index, uint32_t source_offset, uint32_t runtime_address) {
  (void)lookup;
  if (buf == NULL || buf_size == 0U) return;
  if (source_offset == runtime_address) {
    format_asm_label(buf, buf_size, section_index, runtime_address);
    return;
  }
  snprintf(buf, buf_size, "abs_%u_%08X", (unsigned)section_index, (unsigned)runtime_address);
}

static uint8_t format_rendered_asm_label_with_generation(const M68kRenderLookup *lookup, char *buf, size_t buf_size,
    size_t section_index, uint32_t offset) {
  uint32_t runtime_address = 0U;
  uint8_t generated = format_lookup_asm_label_with_generation(lookup, buf, buf_size, section_index, offset);
  if (generated && lookup_source_should_render_runtime_label(lookup, section_index, offset, &runtime_address)) {
    format_runtime_asm_label(lookup, buf, buf_size, section_index, offset, runtime_address);
  }
  return generated;
}

static uint8_t format_storage_asm_label_with_generation(const M68kRenderLookup *lookup, char *buf, size_t buf_size,
    size_t section_index, uint32_t offset) {
  return format_lookup_asm_label_with_generation(lookup, buf, buf_size, section_index, offset);
}

static int runtime_range_is_materialized(const M68kRenderLookup *lookup, const M68kFact *range);

static int render_asm_include_once(M68kRenderIRPreview *preview, const char *include_path) {
  uint16_t index;
  char line[128];
  if (preview == NULL || include_path == NULL || include_path[0] == '\0') return 1;
  if (preview->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 1;
  for (index = 0U; index < preview->asm_source_include_count; ++index) {
    if (strcmp(preview->asm_source_includes[index], include_path) == 0) return 1;
  }
  if (preview->asm_source_include_count >= M68K_RENDER_ASM_INCLUDE_LIMIT) {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, 0U, 0U);
    return 0;
  }
  snprintf(preview->asm_source_includes[preview->asm_source_include_count],
    sizeof(preview->asm_source_includes[preview->asm_source_include_count]), "%s", include_path);
  ++preview->asm_source_include_count;
  snprintf(line, sizeof(line), "    INCLUDE \"%s\"\n", include_path);
  if (preview->collect_asm_source_text) return 1;
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  return 1;
}

static int render_asm_declare_symbol_once(M68kRenderIRPreview *preview, const char *symbol_name, int32_t value) {
  uint16_t index;
  char line[160];
  if (preview == NULL || symbol_name == NULL || symbol_name[0] == '\0') return 1;
  if (preview->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 1;
  if (!asm_symbol_name_is_safe_local(symbol_name)) {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, 0U, 0U);
    return 0;
  }
  for (index = 0U; index < preview->asm_source_declaration_count; ++index) {
    if (strcmp(preview->asm_source_declarations[index], symbol_name) == 0) return 1;
  }
  if (preview->asm_source_declaration_count >= M68K_RENDER_ASM_DECLARATION_LIMIT) {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, 0U, 0U);
    return 0;
  }
  snprintf(preview->asm_source_declarations[preview->asm_source_declaration_count],
    sizeof(preview->asm_source_declarations[preview->asm_source_declaration_count]), "%s", symbol_name);
  snprintf(line, sizeof(line), "%s\tEQU\t%d\n", symbol_name, (int)value);
  if (preview->collect_asm_source_text) {
    if (!store_asm_source_declaration_line(preview, line)) return 0;
    ++preview->asm_source_declaration_count;
    return 1;
  }
  ++preview->asm_source_declaration_count;
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  return 1;
}

static int render_asm_declare_symbol_hex_once(M68kRenderIRPreview *preview, const char *symbol_name, uint32_t value) {
  uint16_t index;
  char line[160];
  if (preview == NULL || symbol_name == NULL || symbol_name[0] == '\0') return 1;
  if (!asm_symbol_name_is_safe_local(symbol_name)) {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, 0U, 0U);
    return 0;
  }
  for (index = 0U; index < preview->asm_source_declaration_count; ++index) {
    if (strcmp(preview->asm_source_declarations[index], symbol_name) == 0) return 1;
  }
  if (preview->asm_source_declaration_count >= M68K_RENDER_ASM_DECLARATION_LIMIT) {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, 0U, 0U);
    return 0;
  }
  snprintf(preview->asm_source_declarations[preview->asm_source_declaration_count],
    sizeof(preview->asm_source_declarations[preview->asm_source_declaration_count]), "%s", symbol_name);
  snprintf(line, sizeof(line), "%s\tEQU\t$%X\n", symbol_name, (unsigned)value);
  if (preview->collect_asm_source_text) {
    if (!store_asm_source_declaration_line(preview, line)) return 0;
    ++preview->asm_source_declaration_count;
    return 1;
  }
  ++preview->asm_source_declaration_count;
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  return 1;
}

static int render_asm_declare_symbol_expr_once(M68kRenderIRPreview *preview, const char *symbol_name,
    const char *expr) {
  uint16_t index;
  char line[192];
  if (preview == NULL || symbol_name == NULL || symbol_name[0] == '\0' || expr == NULL || expr[0] == '\0')
    return 1;
  if (!asm_symbol_name_is_safe_local(symbol_name)) {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, 0U, 0U);
    return 0;
  }
  for (index = 0U; index < preview->asm_source_declaration_count; ++index) {
    if (strcmp(preview->asm_source_declarations[index], symbol_name) == 0) return 1;
  }
  if (preview->asm_source_declaration_count >= M68K_RENDER_ASM_DECLARATION_LIMIT) {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, 0U, 0U);
    return 0;
  }
  snprintf(preview->asm_source_declarations[preview->asm_source_declaration_count],
    sizeof(preview->asm_source_declarations[preview->asm_source_declaration_count]), "%s", symbol_name);
  snprintf(line, sizeof(line), "%s\tEQU\t%s\n", symbol_name, expr);
  if (preview->collect_asm_source_text) {
    if (!store_asm_source_declaration_line(preview, line)) return 0;
    ++preview->asm_source_declaration_count;
    return 1;
  }
  ++preview->asm_source_declaration_count;
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  return 1;
}

static int render_asm_define_amiga_lvo_symbol_once(M68kRenderIRPreview *preview, uint16_t symbol_id) {
  const char *symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, symbol_id);
  const AmigaOsLibraryVectorInfo *vector = amiga_os_find_library_vector_by_symbol_id(symbol_id);
  if (symbol_name == NULL || symbol_name[0] == '\0' || vector == NULL) {
    if (preview != NULL) {
      ++preview->asm_source_instruction_render_failures;
      record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, 0U, 0U);
    }
    return 0;
  }
  return render_asm_declare_symbol_once(preview, symbol_name, (int32_t)vector->lvo);
}

static int render_asm_define_amiga_hardware_base_once(M68kRenderIRPreview *preview, const char *symbol_name) {
  uint32_t address;
  if (symbol_name == NULL || symbol_name[0] == '\0') return 1;
  if (!amiga_os_find_hardware_base_address(symbol_name, &address)) return 1;
  if (address > (uint32_t)INT32_MAX) return 0;
  return render_asm_declare_symbol_hex_once(preview, symbol_name, address);
}

static int render_asm_define_amiga_constant_once(M68kRenderIRPreview *preview, const char *symbol_name) {
  int32_t value;
  if (symbol_name == NULL || symbol_name[0] == '\0') return 1;
  if (amiga_os_find_symbol_include(symbol_name) != NULL) return 1;
  if (!amiga_os_find_constant_value(symbol_name, &value)) return 1;
  if (value >= 0) return render_asm_declare_symbol_hex_once(preview, symbol_name, (uint32_t)value);
  return render_asm_declare_symbol_once(preview, symbol_name, value);
}

static int render_asm_define_m68k_vector_symbol_once(M68kRenderIRPreview *preview, const char *symbol_name) {
  const M68kCpuExceptionVectorInfo *vector;
  if (symbol_name == NULL || symbol_name[0] == '\0') return 1;
  vector = m68k_cpu_find_exception_vector_by_symbol_name(symbol_name);
  if (vector == NULL) return 1;
  return render_asm_declare_symbol_hex_once(preview, symbol_name, vector->address);
}

static int render_asm_define_platform_symbol_once(M68kRenderIRPreview *preview, const char *symbol_name) {
  int32_t value;
  if (preview == NULL || symbol_name == NULL || symbol_name[0] == '\0') return 1;
  if (!platform_facts_v2_synthetic_symbol_value(preview->platform_backend_kind, symbol_name, &value)) return 1;
  return render_asm_declare_symbol_once(preview, symbol_name, value);
}

static int render_asm_include_for_symbol_expr(M68kRenderIRPreview *preview, const char *expr);

static int render_asm_define_amiga_hardware_instance_alias_once(M68kRenderIRPreview *preview,
    const char *symbol_name) {
  const char *expr;
  if (preview == NULL || symbol_name == NULL || symbol_name[0] == '\0') return 1;
  if (preview->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 1;
  expr = amiga_os_find_hardware_register_instance_alias_expr(symbol_name);
  if (expr == NULL || expr[0] == '\0') return 1;
  if (!render_asm_include_for_symbol_expr(preview, expr)) return 0;
  return render_asm_declare_symbol_expr_once(preview, symbol_name, expr);
}

static int render_asm_include_for_amiga_symbol(M68kRenderIRPreview *preview, const char *symbol_name) {
  const char *include_path;
  uint16_t symbol_id;
  if (symbol_name == NULL || symbol_name[0] == '\0') return 1;
  include_path = amiga_os_find_symbol_include(symbol_name);
  if (include_path != NULL && include_path[0] != '\0') return render_asm_include_once(preview, include_path);
  symbol_id = amiga_os_name_id(M68K_PLATFORM_NAME_SYMBOL, symbol_name);
  if (amiga_os_find_library_vector_by_symbol_id(symbol_id) != NULL)
    return render_asm_define_amiga_lvo_symbol_once(preview, symbol_id);
  return 1;
}

static int render_asm_include_for_symbol_expr(M68kRenderIRPreview *preview, const char *expr) {
  const char *cursor;
  if (expr == NULL || expr[0] == '\0') return 1;
  cursor = expr;
  while (*cursor != '\0') {
    char token[64];
    size_t token_len = 0U;
    if (!((*cursor >= 'A' && *cursor <= 'Z') || (*cursor >= 'a' && *cursor <= 'z') || *cursor == '_')) {
      ++cursor;
      continue;
    }
    while ((*cursor >= 'A' && *cursor <= 'Z') || (*cursor >= 'a' && *cursor <= 'z') ||
           (*cursor >= '0' && *cursor <= '9') || *cursor == '_') {
      if (token_len + 1U >= sizeof(token)) return 0;
      token[token_len++] = *cursor;
      ++cursor;
    }
    token[token_len] = '\0';
    if (!asm_symbol_name_is_safe_local(token)) return 0;
    if (!render_asm_include_for_amiga_symbol(preview, token)) return 0;
    if (!render_asm_define_amiga_hardware_base_once(preview, token)) return 0;
    if (!render_asm_define_amiga_constant_once(preview, token)) return 0;
    if (!render_asm_define_m68k_vector_symbol_once(preview, token)) return 0;
    if (!render_asm_define_platform_symbol_once(preview, token)) return 0;
    if (!render_asm_define_amiga_hardware_instance_alias_once(preview, token)) return 0;
  }
  return 1;
}

static int render_asm_includes_for_structured_data_item(M68kRenderIRPreview *preview,
    const M68kAnalysisStructuredDataItem *item) {
  if (item == NULL) return 1;
  return render_asm_include_for_amiga_symbol(preview, item->field_name) &&
    render_asm_include_for_amiga_symbol(preview, item->constant_name);
}

static void render_asm_label(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset, uint32_t *io_logical_pc) {
  const M68kAnalysisStructuredDataItem *item =
    lookup_structured_data_item_at_offset(lookup, section_index, offset);
  char line[160];
  char name[64];
  char storage_name[64];
  uint32_t runtime_address = 0U;
  int has_runtime_address;
  if (!render_asm_includes_for_structured_data_item(preview, item)) return;
  has_runtime_address = lookup_source_should_render_runtime_label(lookup, section_index, offset, &runtime_address);
  if (has_runtime_address && io_logical_pc != NULL && runtime_address != offset &&
      lookup_source_offset_is_materialized_runtime_range_start(lookup, section_index, offset)) {
    (void)format_storage_asm_label_with_generation(lookup, storage_name, sizeof(storage_name), section_index,
      offset);
    if (*io_logical_pc != offset) {
      render_asm_org(preview, offset);
      *io_logical_pc = offset;
    }
    snprintf(line, sizeof(line), "%s:\n", storage_name);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
    render_asm_org(preview, runtime_address);
    *io_logical_pc = runtime_address;
  } else if (io_logical_pc != NULL) {
    render_asm_sync_logical_pc(preview, lookup, section_index, offset, io_logical_pc);
  }
  if (render_asm_runtime_alias_labels(preview, lookup, section_index, offset,
      has_runtime_address ? 1U : 0U, runtime_address) && has_runtime_address) {
    render_asm_org(preview, runtime_address);
    if (io_logical_pc != NULL) *io_logical_pc = runtime_address;
  }
  (void)format_rendered_asm_label_with_generation(lookup, name, sizeof(name), section_index, offset);
  if (item != NULL && item->struct_name[0] != '\0') {
    snprintf(line, sizeof(line), "%s:\t; STRUCT %s\n", name, item->struct_name);
  } else {
    snprintf(line, sizeof(line), "%s:\n", name);
  }
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static void platform_state_clear_register(M68kRenderPlatformState *state, uint8_t reg_index) {
  size_t index;
  if (state == NULL || reg_index >= 8U) return;
  state->address_base_known[reg_index] = 0U;
  state->address_base_library[reg_index][0] = '\0';
  state->address_hardware_base_known[reg_index] = 0U;
  state->address_hardware_base_symbol[reg_index][0] = '\0';
  state->address_app_base_known[reg_index] = 0U;
  state->address_layout_base_known[reg_index] = 0U;
  state->address_layout_base_symbol[reg_index][0] = '\0';
  for (index = 0U; index < sizeof(state->local_base_slots) / sizeof(state->local_base_slots[0]); ++index) {
    if (state->local_base_slots[index].valid && state->local_base_slots[index].base_reg == reg_index)
      state->local_base_slots[index].valid = 0U;
  }
}

static void platform_state_clear_data_library(M68kRenderPlatformState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  state->data_base_known[reg_index] = 0U;
  state->data_base_library[reg_index][0] = '\0';
  state->data_layout_base_known[reg_index] = 0U;
  state->data_layout_base_symbol[reg_index][0] = '\0';
}

static void platform_state_clear_all_data_libraries(M68kRenderPlatformState *state) {
  if (state == NULL) return;
  memset(state->data_base_known, 0, sizeof(state->data_base_known));
  memset(state->data_base_library, 0, sizeof(state->data_base_library));
  memset(state->data_layout_base_known, 0, sizeof(state->data_layout_base_known));
  memset(state->data_layout_base_symbol, 0, sizeof(state->data_layout_base_symbol));
}

static void platform_state_clear_all_local_base_slots(M68kRenderPlatformState *state) {
  if (state == NULL) return;
  memset(state->local_base_slots, 0, sizeof(state->local_base_slots));
}

static void platform_state_clear_address_app_base(M68kRenderPlatformState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  state->address_app_base_known[reg_index] = 0U;
}

static void platform_state_clear_address_layout_base(M68kRenderPlatformState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  state->address_layout_base_known[reg_index] = 0U;
  state->address_layout_base_symbol[reg_index][0] = '\0';
}

static void platform_state_clear_address_hardware_base(M68kRenderPlatformState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  state->address_hardware_base_known[reg_index] = 0U;
  state->address_hardware_base_symbol[reg_index][0] = '\0';
}

static void platform_state_clear_all_hardware_bases(M68kRenderPlatformState *state) {
  if (state == NULL) return;
  memset(state->address_hardware_base_known, 0, sizeof(state->address_hardware_base_known));
  memset(state->address_hardware_base_symbol, 0, sizeof(state->address_hardware_base_symbol));
}

static void platform_state_clear_data_app_base(M68kRenderPlatformState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  state->data_app_base_known[reg_index] = 0U;
}

static void platform_state_clear_data_layout_base(M68kRenderPlatformState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  state->data_layout_base_known[reg_index] = 0U;
  state->data_layout_base_symbol[reg_index][0] = '\0';
}

static void platform_state_clear_all_app_bases(M68kRenderPlatformState *state) {
  if (state == NULL) return;
  memset(state->data_app_base_known, 0, sizeof(state->data_app_base_known));
  memset(state->address_app_base_known, 0, sizeof(state->address_app_base_known));
}

static void platform_state_clear_all_layout_bases(M68kRenderPlatformState *state) {
  if (state == NULL) return;
  memset(state->data_layout_base_known, 0, sizeof(state->data_layout_base_known));
  memset(state->data_layout_base_symbol, 0, sizeof(state->data_layout_base_symbol));
  memset(state->address_layout_base_known, 0, sizeof(state->address_layout_base_known));
  memset(state->address_layout_base_symbol, 0, sizeof(state->address_layout_base_symbol));
}

void platform_state_clear_d0_lvo(M68kRenderPlatformState *state) {
  if (state == NULL) return;
  state->d0_lvo_known = 0U;
  state->d0_lvo = 0;
}

static void platform_state_set_register_library(M68kRenderPlatformState *state, uint8_t reg_index,
    const char *library_name) {
  size_t index;
  if (state == NULL || reg_index >= 8U || library_name == NULL || library_name[0] == '\0') return;
  if (amiga_os_find_library_base_name(library_name) == NULL) return;
  for (index = 0U; index < sizeof(state->local_base_slots) / sizeof(state->local_base_slots[0]); ++index) {
    if (state->local_base_slots[index].valid && state->local_base_slots[index].base_reg == reg_index)
      state->local_base_slots[index].valid = 0U;
  }
  state->address_base_known[reg_index] = 1U;
  state->address_app_base_known[reg_index] = 0U;
  platform_state_clear_address_layout_base(state, reg_index);
  platform_state_clear_address_hardware_base(state, reg_index);
  snprintf(state->address_base_library[reg_index], sizeof(state->address_base_library[reg_index]), "%s",
    library_name);
}

static void platform_state_set_data_library(M68kRenderPlatformState *state, uint8_t reg_index,
    const char *library_name) {
  if (state == NULL || reg_index >= 8U || library_name == NULL || library_name[0] == '\0') return;
  if (amiga_os_find_library_base_name(library_name) == NULL) return;
  state->data_base_known[reg_index] = 1U;
  snprintf(state->data_base_library[reg_index], sizeof(state->data_base_library[reg_index]), "%s",
    library_name);
}

int amiga_unknown_base_register_owner_name(uint8_t base_reg, char *buf, size_t buf_size) {
  int written;
  if (buf != NULL && buf_size != 0U) buf[0] = '\0';
  if (buf == NULL || buf_size == 0U || base_reg >= 8U || base_reg == 6U || base_reg == 7U) return 0;
  written = snprintf(buf, buf_size, "__amiga_local_base_a%u__", (unsigned)base_reg);
  return written > 0 && (size_t)written < buf_size;
}

static int amiga_unknown_base_owner_name_is_internal(const char *owner_name) {
  static const char prefix[] = "__amiga_local_base_a";
  size_t prefix_len = sizeof(prefix) - 1U;
  if (owner_name == NULL) return 0;
  if (strncmp(owner_name, prefix, prefix_len) != 0) return 0;
  if (owner_name[prefix_len] < '0' || owner_name[prefix_len] > '7') return 0;
  return owner_name[prefix_len + 1U] == '_' &&
    owner_name[prefix_len + 2U] == '_' &&
    owner_name[prefix_len + 3U] == '\0';
}

static int amiga_vector_is_open_library_result(const AmigaOsLibraryVectorInfo *vector);

static const char *platform_state_local_base_slot_library(const M68kRenderPlatformState *state, uint8_t base_reg,
    int16_t displacement) {
  size_t index;
  if (state == NULL || base_reg >= 8U) return NULL;
  for (index = 0U; index < sizeof(state->local_base_slots) / sizeof(state->local_base_slots[0]); ++index) {
    const M68kRenderPlatformLocalBaseSlot *slot = &state->local_base_slots[index];
    if (slot->valid && slot->base_reg == base_reg && slot->displacement == displacement)
      return slot->library_name;
  }
  return NULL;
}

static void platform_state_set_local_base_slot(M68kRenderPlatformState *state, uint8_t base_reg,
    int16_t displacement, const char *library_name) {
  size_t index;
  if (state == NULL || base_reg >= 8U || library_name == NULL || library_name[0] == '\0') return;
  if (amiga_os_find_library_base_name(library_name) == NULL) return;
  for (index = 0U; index < sizeof(state->local_base_slots) / sizeof(state->local_base_slots[0]); ++index) {
    M68kRenderPlatformLocalBaseSlot *slot = &state->local_base_slots[index];
    if (slot->valid && slot->base_reg == base_reg && slot->displacement == displacement) {
      snprintf(slot->library_name, sizeof(slot->library_name), "%s", library_name);
      return;
    }
  }
  for (index = 0U; index < sizeof(state->local_base_slots) / sizeof(state->local_base_slots[0]); ++index) {
    M68kRenderPlatformLocalBaseSlot *slot = &state->local_base_slots[index];
    if (slot->valid) continue;
    slot->valid = 1U;
    slot->base_reg = base_reg;
    slot->displacement = displacement;
    snprintf(slot->library_name, sizeof(slot->library_name), "%s", library_name);
    return;
  }
}

static void platform_state_clear_local_base_slot(M68kRenderPlatformState *state, uint8_t base_reg,
    int16_t displacement) {
  size_t index;
  if (state == NULL || base_reg >= 8U) return;
  for (index = 0U; index < sizeof(state->local_base_slots) / sizeof(state->local_base_slots[0]); ++index) {
    M68kRenderPlatformLocalBaseSlot *slot = &state->local_base_slots[index];
    if (slot->valid && slot->base_reg == base_reg && slot->displacement == displacement)
      slot->valid = 0U;
  }
}

static const char *platform_state_operand_library(const M68kRenderPlatformState *state,
    const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  if (state == NULL || operand == NULL) return NULL;
  if (operand_is_data_register_local(operand, &reg) && state->data_base_known[reg])
    return state->data_base_library[reg];
  if (operand_address_register_index_local(operand, &reg) && state->address_base_known[reg])
    return state->address_base_library[reg];
  return NULL;
}

int platform_state_name_is_app_base(const char *name) {
  return name != NULL && strcmp(name, "__amiga_app_base__") == 0;
}

static int policy_has_layout_base_symbol(const M68kAnalysisPolicy *policy, const char *name) {
  uint16_t index;
  if (policy == NULL || name == NULL || name[0] == '\0') return 0;
  for (index = 0U; index < policy->rsset_layout_region_count && index < M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT; ++index) {
    const M68kAnalysisRssetLayoutRegion *region = &policy->rsset_layout_regions[index];
    const char *base_symbol = region->base_symbol[0] != '\0' ? region->base_symbol : "__amiga_app_base__";
    if (strcmp(base_symbol, name) == 0) return 1;
  }
  return 0;
}

static void platform_state_set_register_app_base(M68kRenderPlatformState *state, uint8_t reg_kind,
    uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == M68K_ANALYSIS_REGISTER_DATA) {
    platform_state_clear_data_library(state, reg_index);
    state->data_app_base_known[reg_index] = 1U;
    if (reg_index == 0U) platform_state_clear_d0_lvo(state);
  } else if (reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS) {
    platform_state_clear_register(state, reg_index);
    state->address_app_base_known[reg_index] = 1U;
  }
}

static void platform_state_set_register_layout_base(M68kRenderPlatformState *state, uint8_t reg_kind,
    uint8_t reg_index, const char *base_symbol) {
  if (state == NULL || reg_index >= 8U || base_symbol == NULL || base_symbol[0] == '\0') return;
  if (reg_kind == M68K_ANALYSIS_REGISTER_DATA) {
    platform_state_clear_data_library(state, reg_index);
    platform_state_clear_data_app_base(state, reg_index);
    state->data_layout_base_known[reg_index] = 1U;
    snprintf(state->data_layout_base_symbol[reg_index], sizeof(state->data_layout_base_symbol[reg_index]), "%s",
      base_symbol);
    if (reg_index == 0U) platform_state_clear_d0_lvo(state);
  } else if (reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS) {
    platform_state_clear_register(state, reg_index);
    state->address_layout_base_known[reg_index] = 1U;
    snprintf(state->address_layout_base_symbol[reg_index], sizeof(state->address_layout_base_symbol[reg_index]),
      "%s", base_symbol);
  }
}

static void platform_state_set_register_hardware_base(M68kRenderPlatformState *state, uint8_t reg_index,
    const char *base_symbol) {
  uint32_t base_address;
  if (state == NULL || reg_index >= 8U || base_symbol == NULL || base_symbol[0] == '\0') return;
  if (!amiga_os_find_hardware_base_address(base_symbol, &base_address)) return;
  (void)base_address;
  platform_state_clear_register(state, reg_index);
  state->address_hardware_base_known[reg_index] = 1U;
  snprintf(state->address_hardware_base_symbol[reg_index], sizeof(state->address_hardware_base_symbol[reg_index]),
    "%s", base_symbol);
}

static void preview_record_platform_vector(M68kRenderIRPreview *preview, const AmigaOsLibraryVectorInfo *vector) {
  if (preview == NULL || vector == NULL) return;
  ++preview->platform_call_count;
  preview->platform_effect_count += vector->input_count;
  if (vector->output.reg_kind != AMIGA_OS_REGISTER_NONE ||
      vector->output.output_id != AMIGA_OS_SYMBOL_ID_NONE ||
      vector->output.type_id != AMIGA_OS_TYPE_ID_NONE ||
      vector->output.struct_id != AMIGA_OS_STRUCT_ID_NONE) {
    ++preview->platform_effect_count;
  }
}

static void preview_record_platform_vector_effects(M68kRenderIRPreview *preview,
    M68kSectionAnalysisIR *section_analysis, uint32_t offset, const AmigaOsLibraryVectorInfo *vector) {
  const AmigaOsCallOutputInfo *output;
  const char *output_symbol_name;
  const char *output_type_name;
  const char *output_semantic_kind;
  const char *output_value_domain_name;
  if (preview == NULL || section_analysis == NULL || vector == NULL) return;
  output = &vector->output;
  if (output->reg_kind == AMIGA_OS_REGISTER_NONE || output->reg_index >= 8U) return;
  output_symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, output->output_id);
  output_type_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, output->struct_id);
  if (output_type_name == NULL || output_type_name[0] == '\0')
    output_type_name = amiga_os_name(M68K_PLATFORM_NAME_TYPE, output->type_id);
  output_semantic_kind = amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, output->semantic_kind_id);
  output_value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, output->value_domain_id);
  if ((output_symbol_name == NULL || output_symbol_name[0] == '\0') &&
      (output_type_name == NULL || output_type_name[0] == '\0') &&
      (output_semantic_kind == NULL || output_semantic_kind[0] == '\0') &&
      (output_value_domain_name == NULL || output_value_domain_name[0] == '\0')) {
    return;
  }
  if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis,
      M68K_PLATFORM_BACKEND_AMIGA_HUNK, offset, M68K_PLATFORM_EFFECT_SET_TYPED_REG,
      output->reg_kind, output->reg_index, INT16_MIN, INT16_MIN, NULL,
      output_symbol_name, output_type_name, output_semantic_kind, output_value_domain_name, 0U, 0) != 0) {
    preview->asm_source_allocation_failed = 1U;
  }
}

static void preview_record_platform_vector_call(M68kRenderIRPreview *preview,
    const M68kRenderLookup *lookup, M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t kind,
    uint8_t note_kind, const AmigaOsLibraryVectorInfo *vector) {
  const char *symbol_name, *library_name, *device_name;
  const char *note_symbol_name = NULL, *available_since = NULL, *note_base_name = NULL;
  if (preview == NULL || vector == NULL) return;
  preview_record_platform_vector(preview, vector);
  if (section_analysis == NULL) return;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, vector->lvo_symbol_id);
  if (symbol_name == NULL || symbol_name[0] == '\0') return;
  if (note_kind != M68K_PLATFORM_CALL_NOTE_NONE) {
    note_symbol_name = symbol_name;
    symbol_name = NULL;
    library_name = amiga_os_name(M68K_PLATFORM_NAME_LIBRARY, vector->library_id);
    note_base_name = amiga_os_find_library_base_name(library_name);
  }
  available_since = amiga_os_compatibility_version_name((AmigaOsCompatVersion)vector->available_since_version);
  if (m68k_ir_section_analysis_append_recovered_platform_call(section_analysis,
      M68K_PLATFORM_BACKEND_AMIGA_HUNK, offset, kind, symbol_name, note_kind,
      note_base_name, note_symbol_name, 0U, INT16_MIN, INT16_MIN, 0U, 0U, 0U,
      available_since != NULL && available_since[0] != '\0' ? available_since : NULL,
      vector->fd_version != NULL && vector->fd_version[0] != '\0' ? vector->fd_version : NULL) != 0) {
    preview->asm_source_allocation_failed = 1U;
  }
  device_name = render_lookup_device_name_for_call(lookup, section_analysis->section_index, offset);
  if (device_name != NULL &&
      m68k_ir_section_analysis_set_recovered_platform_call_device_name(section_analysis, offset, kind,
        device_name) != 0) {
    preview->asm_source_allocation_failed = 1U;
  }
  preview_record_platform_vector_effects(preview, section_analysis, offset, vector);
}

void platform_state_apply_policy_register_seeds(M68kRenderPlatformState *state,
    const M68kAnalysisPolicy *policy, size_t section_index, uint32_t offset) {
  uint16_t index;
  if (state == NULL || policy == NULL) return;
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    if (seed->has_section_index && seed->section_index != (uint32_t)section_index) continue;
    if (seed->has_entry_offset) {
      if (seed->entry_offset != offset) continue;
    } else if (!policy->has_entry_offset || section_index != 0U || policy->entry_offset != offset) continue;
    if (seed->kind != M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE &&
        seed->kind != M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR) {
      continue;
    }
    if (platform_state_name_is_app_base(seed->name)) {
      platform_state_set_register_app_base(state, seed->reg_kind, seed->reg_index);
      continue;
    }
    if (policy_has_layout_base_symbol(policy, seed->name)) {
      platform_state_set_register_layout_base(state, seed->reg_kind, seed->reg_index, seed->name);
      continue;
    }
    if (seed->reg_kind != M68K_ANALYSIS_REGISTER_ADDRESS || seed->reg_index >= 8U) continue;
    platform_state_set_register_library(state, seed->reg_index, seed->name);
  }
}

static void render_asm_policy_entry_comments(M68kRenderIRPreview *preview, const M68kAnalysisPolicy *policy,
    size_t section_index, uint32_t offset) {
  uint16_t index;
  if (preview == NULL || policy == NULL) return;
  for (index = 0U; index < policy->entry_comment_count && index < M68K_ANALYSIS_ENTRY_COMMENT_LIMIT; ++index) {
    const M68kAnalysisEntryComment *comment = &policy->entry_comments[index];
    char line[256];
    if (comment->has_section_index && comment->section_index != (uint32_t)section_index) continue;
    if (comment->offset != offset || comment->comment[0] == '\0') continue;
    snprintf(line, sizeof(line), "    ; %s\n", comment->comment);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
  }
}

static void render_asm_comment_line(M68kRenderIRPreview *preview, const char *comment) {
  char line[512];
  if (preview == NULL || comment == NULL || comment[0] == '\0') return;
  snprintf(line, sizeof(line), "    ; %s\n", comment);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static int format_policy_register_seed_comment_local(const M68kAnalysisPolicy *policy, size_t section_index,
    uint32_t offset, char *message, size_t message_size) {
  size_t used = 0U;
  uint8_t emitted[2][8] = {{0}};
  uint16_t index;
  if (message == NULL || message_size == 0U) return 0;
  message[0] = '\0';
  if (policy == NULL) return 0;
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    char reg_name[4];
    const char *kind_text;
    if (seed->has_section_index && seed->section_index != (uint32_t)section_index) continue;
    if (seed->has_entry_offset) {
      if (seed->entry_offset != offset) continue;
    } else if (!policy->has_entry_offset || section_index != 0U || policy->entry_offset != offset) continue;
    if (seed->reg_kind != M68K_ANALYSIS_REGISTER_DATA && seed->reg_kind != M68K_ANALYSIS_REGISTER_ADDRESS) continue;
    if (seed->reg_index >= 8U || seed->name[0] == '\0') continue;
    if (emitted[seed->reg_kind - 1U][seed->reg_index]) continue;
    emitted[seed->reg_kind - 1U][seed->reg_index] = 1U;
    snprintf(reg_name, sizeof(reg_name), "%c%u",
      seed->reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS ? 'A' : 'D', (unsigned)seed->reg_index);
    kind_text = seed->kind == M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE ? "base" : "type";
    if (used == 0U) {
      int wrote = snprintf(message, message_size, "KNOWN: %s %s=%s", kind_text, reg_name, seed->name);
      if (wrote < 0) return 0;
      used = (size_t)wrote < message_size ? (size_t)wrote : message_size - 1U;
    } else if (used + 4U < message_size) {
      int wrote = snprintf(message + used, message_size - used, "; %s %s=%s", kind_text, reg_name, seed->name);
      if (wrote < 0) return 0;
      used += (size_t)wrote < message_size - used ? (size_t)wrote : message_size - used - 1U;
    }
    if (seed->type_name[0] != '\0' && used + strlen(seed->type_name) + 2U < message_size) {
      message[used++] = ':';
      snprintf(message + used, message_size - used, "%s", seed->type_name);
      used = strlen(message);
    }
  }
  return used != 0U;
}

static void render_asm_policy_register_seed_comment(M68kRenderIRPreview *preview, const M68kAnalysisPolicy *policy,
    size_t section_index, uint32_t offset) {
  char comment[256];
  char line[320];
  if (preview == NULL) return;
  if (!format_policy_register_seed_comment_local(policy, section_index, offset, comment, sizeof(comment))) return;
  snprintf(line, sizeof(line), "    ; %s\n", comment);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

void record_asm_source_failure(M68kRenderIRPreview *preview, uint32_t kind, size_t section_index,
    uint32_t offset, uint32_t aux_offset) {
  if (preview == NULL || preview->asm_source_first_failure_kind != M68K_RENDER_IR_ASM_SOURCE_FAILURE_NONE) return;
  preview->asm_source_first_failure_kind = kind;
  preview->asm_source_first_failure_section = (uint32_t)section_index;
  preview->asm_source_first_failure_offset = offset;
  preview->asm_source_first_failure_aux_offset = aux_offset;
}

void record_numeric_runtime_ref(M68kRenderIRPreview *preview, const M68kFact *fact) {
  if (preview == NULL || fact == NULL) return;
  if (preview->asm_source_numeric_runtime_refs == 0U) {
    preview->asm_source_first_numeric_runtime_ref_section = (uint32_t)fact->section_index;
    preview->asm_source_first_numeric_runtime_ref_offset = fact->offset;
    preview->asm_source_first_numeric_runtime_ref_target_section = (uint32_t)fact->target_section_index;
    preview->asm_source_first_numeric_runtime_ref_target_offset = fact->target_offset;
    preview->asm_source_first_numeric_runtime_ref_runtime_address = fact->runtime_address;
  }
  ++preview->asm_source_numeric_runtime_refs;
}

static const char *section_base_name(const M68kDecodeSectionIR *section) {
  return section != NULL && section->name != NULL && section->name[0] != '\0' ? section->name : "section";
}

static int section_name_needs_suffix(const M68kDecodeIR *decode, size_t section_index) {
  const char *base_name;
  size_t index;
  if (decode == NULL || section_index >= decode->section_count) return 0;
  base_name = section_base_name(&decode->sections[section_index]);
  if ((decode->sections[section_index].name == NULL || decode->sections[section_index].name[0] == '\0') &&
      decode->section_count > 1U) {
    return 1;
  }
  for (index = 0U; index < decode->section_count; ++index) {
    if (index == section_index) continue;
    if (m68k_ascii_equal_ci(section_base_name(&decode->sections[index]), base_name)) return 1;
  }
  return 0;
}

static const char *rendered_section_name(const M68kDecodeIR *decode, size_t section_index, char *buffer,
    size_t buffer_size) {
  const char *base_name;
  if (buffer != NULL && buffer_size != 0U) buffer[0] = '\0';
  if (decode == NULL || section_index >= decode->section_count) return "section";
  base_name = section_base_name(&decode->sections[section_index]);
  if (!section_name_needs_suffix(decode, section_index)) return base_name;
  if (buffer == NULL || buffer_size == 0U) return base_name;
  snprintf(buffer, buffer_size, "%s_%u", base_name, (unsigned)section_index);
  return buffer;
}

static void render_asm_section_header(M68kRenderIRPreview *preview, const M68kDecodeIR *decode,
    size_t section_index) {
  char line[160];
  char name_buffer[96];
  char kind_buffer[32];
  const M68kDecodeSectionIR *section;
  const char *name;
  uint32_t allocation_size;
  if (preview == NULL || decode == NULL || section_index >= decode->section_count) return;
  section = &decode->sections[section_index];
  name = rendered_section_name(decode, section_index, name_buffer, sizeof(name_buffer));
  if (!m68k_format_section_spec(section->kind, section->platform_mem_type, section->platform_mem_attrs,
      kind_buffer, sizeof(kind_buffer))) {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, section_index, 0U, 0U);
    return;
  }
  allocation_size = section->allocation_size != 0U ? section->allocation_size : section->size;
  if (allocation_size != section->size) {
    snprintf(line, sizeof(line), "    SECTION %s,%s,$%X\n", name, kind_buffer, (unsigned)allocation_size);
  } else {
    snprintf(line, sizeof(line), "    SECTION %s,%s\n", name, kind_buffer);
  }
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

void render_asm_org(M68kRenderIRPreview *preview, uint32_t logical_address) {
  char line[64];
  if (preview == NULL) return;
  snprintf(line, sizeof(line), "    ORG $%X\n", (unsigned)logical_address);
  if (preview->asm_source_row_builder.active)
    m68k_render_plan_row_builder_mark_current_line_directive(&preview->asm_source_row_builder);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

void render_asm_sync_logical_pc(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    size_t section_index, uint32_t source_offset, uint32_t *io_logical_pc) {
  uint32_t desired = source_offset;
  if (preview == NULL || io_logical_pc == NULL) return;
  (void)lookup_source_logical_address(lookup, section_index, source_offset, &desired);
  if (*io_logical_pc != desired) render_asm_org(preview, desired);
  *io_logical_pc = desired;
}

static void render_asm_hex_blob_comments(M68kRenderIRPreview *preview, const char *first_prefix,
    const char *append_prefix, const uint8_t *data, uint32_t size) {
  enum { BYTES_PER_COMMENT = 64U };
  uint32_t chunk_start = 0U;
  if (preview == NULL || first_prefix == NULL || append_prefix == NULL || data == NULL || size == 0U) return;
  while (chunk_start < size) {
    uint32_t index;
    uint32_t chunk_end = chunk_start + BYTES_PER_COMMENT;
    if (chunk_end > size) chunk_end = size;
    hash_asm_text(preview, chunk_start == 0U ? first_prefix : append_prefix);
    for (index = chunk_start; index < chunk_end; ++index) {
      char token[3];
      snprintf(token, sizeof(token), "%02X", (unsigned)data[index]);
      hash_asm_text(preview, token);
    }
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
    chunk_start = chunk_end;
  }
}

static void render_asm_platform_header(M68kRenderIRPreview *preview, const M68kObject *object) {
  uint32_t program_flags = 0U;
  uint16_t relocation_flag = 0U;
  uint32_t symbol_table_type = 0U;
  const uint8_t *symbol_table = NULL, *relocation_stream = NULL;
  uint32_t symbol_table_size = 0U, relocation_stream_size = 0U;
  char line[64];
  if (preview == NULL || object == NULL) return;
  if (object->platform_backend_kind != M68K_PLATFORM_BACKEND_ATARI_ST) return;
  if (m68k_atari_st_get_program_flags(object, &program_flags) == 0) {
    snprintf(line, sizeof(line), "    COMMENT HEAD=$%x\n", (unsigned)program_flags);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
  }
  if (m68k_atari_st_get_relocation_flag(object, &relocation_flag) == 0 && relocation_flag != 0U) {
    snprintf(line, sizeof(line), "    COMMENT ATARI_RELOC_FLAG=$%04X\n", (unsigned)relocation_flag);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
  }
  if (m68k_atari_st_get_raw_symbol_table(object, &symbol_table_type, &symbol_table, &symbol_table_size) == 0) {
    if (symbol_table_type != 0U || symbol_table_size != 0U) {
      snprintf(line, sizeof(line), "    COMMENT ATARI_SYMBOL_TYPE=$%x\n", (unsigned)symbol_table_type);
      hash_asm_text(preview, line);
      ++preview->asm_source_lines;
    }
    if (symbol_table != NULL && symbol_table_size != 0U) {
      render_asm_hex_blob_comments(preview, "    COMMENT ATARI_SYMBOLS=$", "    COMMENT ATARI_SYMBOLS+=$",
        symbol_table, symbol_table_size);
    }
  }
  if (m68k_atari_st_get_raw_relocation_stream(object, &relocation_stream, &relocation_stream_size) == 0 &&
      relocation_stream != NULL && relocation_stream_size != 0U) {
    render_asm_hex_blob_comments(preview, "    COMMENT ATARI_RELOC=$", "    COMMENT ATARI_RELOC+=$",
      relocation_stream, relocation_stream_size);
  }
}

static void render_asm_relocation_expr(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kFact *fact) {
  char line[256];
  char name[64];
  char value[32];
  char structured_comment[128];
  const char *directive;
  uint32_t numeric_value;
  if (preview == NULL || lookup == NULL || fact == NULL) return;
  if (fact->size == 4U) directive = "dc.l";
  else if (fact->size == 2U) directive = "dc.w";
  else directive = "dc.b";
  (void)format_rendered_asm_label_with_generation(lookup, name, sizeof(name), fact->target_section_index,
    fact->target_offset);
  if (!lookup_has_renderable_label(lookup, fact->target_section_index, fact->target_offset)) {
    numeric_value = fact->target_addend >= 0 && fact->target_addend <= UINT32_MAX
      ? (uint32_t)fact->target_addend : fact->target_offset;
    format_numeric_value(value, sizeof(value), fact->size, numeric_value);
    if (fact->platform_record_kind == AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32) {
      const char *reason = lookup_offset_is_inside_relocation_payload(lookup, fact->target_section_index,
        fact->target_offset) ? "is inside another relocation payload" : "has no renderable statement boundary";
      snprintf(line, sizeof(line),
        "\t%s %s\t; facts_v2 HUNK_RELOC32 numeric: target label %s %s; left numeric\n",
        directive, value, name, reason);
      ++preview->asm_source_lossy_numeric_hunk_relocations;
    } else {
      snprintf(line, sizeof(line),
        "\t%s %s\t; facts_v2 relocation numeric: target label %s is not renderable\n",
        directive, value, name);
      ++preview->asm_source_instruction_relocation_failures;
      record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RELOCATION,
        fact->section_index, fact->offset, fact->target_offset);
    }
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
    return;
  }
  if (structured_data_item_comment(lookup_structured_data_item_at_offset(lookup, fact->section_index, fact->offset),
      structured_comment, sizeof(structured_comment))) {
    snprintf(line, sizeof(line), "\t%s %s\t; %s\n", directive, name, structured_comment);
  } else {
    snprintf(line, sizeof(line), "\t%s %s\n", directive, name);
  }
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  ++preview->asm_source_relocation_exprs;
}

static uint32_t repeated_byte_run_length(const uint8_t *data, uint32_t offset, uint32_t size) {
  uint32_t count = 1U;
  uint8_t value;
  if (data == NULL || size == 0U) return 0U;
  value = data[offset];
  while (count < size && data[offset + count] == value) ++count;
  return count;
}

static void render_asm_dcb_b(M68kRenderIRPreview *preview, uint32_t count, uint8_t value,
    const char *comment) {
  char line[128];
  if (preview == NULL || count == 0U) return;
  if (comment != NULL && comment[0] != '\0')
    snprintf(line, sizeof(line), "\tdcb.b $%X,$%02X\t; %s\n", (unsigned)count, (unsigned)value, comment);
  else
    snprintf(line, sizeof(line), "\tdcb.b $%X,$%02X\n", (unsigned)count, (unsigned)value);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static void render_asm_dc_b(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t size, const char *comment) {
  enum { DCB_MIN_REPEAT = 8U };
  uint32_t cursor = 0U;
  if (preview == NULL || data == NULL) return;
  while (cursor < size) {
    uint32_t line_count = size - cursor;
    uint32_t index;
    uint32_t repeat_count = repeated_byte_run_length(data, offset + cursor, size - cursor);
    if (repeat_count >= DCB_MIN_REPEAT) {
      render_asm_dcb_b(preview, repeat_count, data[offset + cursor], comment);
      cursor += repeat_count;
      continue;
    }
    if (line_count > 16U) line_count = 16U;
    for (index = 1U; index < line_count; ++index) {
      if (repeated_byte_run_length(data, offset + cursor + index, size - cursor - index) >= DCB_MIN_REPEAT) {
        line_count = index;
        break;
      }
    }
    hash_asm_text(preview, "\tdc.b ");
    for (index = 0U; index < line_count; ++index) {
      char token[8];
      if (index != 0U) hash_asm_text(preview, ",");
      snprintf(token, sizeof(token), "$%02X", (unsigned)data[offset + cursor + index]);
      hash_asm_text(preview, token);
    }
    if (comment != NULL && comment[0] != '\0') {
      hash_asm_text(preview, "\t; ");
      hash_asm_text(preview, comment);
    }
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
    cursor += line_count;
  }
}

int byte_is_quoted_string_safe(uint8_t value) {
  return value >= 0x20U && value <= 0x7eU && value != '"' && value != '\\';
}

static void render_asm_dc_b_string(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t size, const char *comment) {
  uint32_t cursor;
  int wrote = 0;
  if (preview == NULL || data == NULL || size == 0U) return;
  hash_asm_text(preview, "\tdc.b ");
  cursor = 0U;
  while (cursor < size) {
    if (byte_is_quoted_string_safe(data[offset + cursor])) {
      char byte_text[2];
      if (wrote) hash_asm_text(preview, ",");
      hash_asm_text(preview, "\"");
      while (cursor < size && byte_is_quoted_string_safe(data[offset + cursor])) {
        byte_text[0] = (char)data[offset + cursor];
        byte_text[1] = '\0';
        hash_asm_text(preview, byte_text);
        ++cursor;
      }
      hash_asm_text(preview, "\"");
      wrote = 1;
    } else {
      char token[8];
      if (wrote) hash_asm_text(preview, ",");
      snprintf(token, sizeof(token), "$%02X", (unsigned)data[offset + cursor]);
      hash_asm_text(preview, token);
      ++cursor;
      wrote = 1;
    }
  }
  if (comment != NULL && comment[0] != '\0') {
    hash_asm_text(preview, "\t; ");
    hash_asm_text(preview, comment);
  }
  hash_asm_text(preview, "\n");
  ++preview->asm_source_lines;
}

static void render_asm_dc_b_length_prefixed_string(M68kRenderIRPreview *preview, const uint8_t *data,
    uint32_t offset, uint32_t size, const char *comment) {
  char token[16];
  uint32_t cursor;
  if (preview == NULL || data == NULL || size == 0U) return;
  snprintf(token, sizeof(token), "\tdc.b $%02X", (unsigned)data[offset]);
  hash_asm_text(preview, token);
  if (size > 1U) {
    hash_asm_text(preview, ",\"");
    for (cursor = 1U; cursor < size && byte_is_quoted_string_safe(data[offset + cursor]); ++cursor) {
      char byte_text[2];
      byte_text[0] = (char)data[offset + cursor];
      byte_text[1] = '\0';
      hash_asm_text(preview, byte_text);
    }
    hash_asm_text(preview, "\"");
    if (cursor < size) {
      for (; cursor < size; ++cursor) {
        snprintf(token, sizeof(token), ",$%02X", (unsigned)data[offset + cursor]);
        hash_asm_text(preview, token);
      }
    }
  }
  if (comment != NULL && comment[0] != '\0') {
    hash_asm_text(preview, "\t; ");
    hash_asm_text(preview, comment);
  }
  hash_asm_text(preview, "\n");
  ++preview->asm_source_lines;
}

static void render_asm_ds_b(M68kRenderIRPreview *preview, uint32_t size, const char *comment) {
  char line[96];
  if (preview == NULL || size == 0U) return;
  if (comment != NULL && comment[0] != '\0')
    snprintf(line, sizeof(line), "\tDS.B $%X\t; %s\n", (unsigned)size, comment);
  else
    snprintf(line, sizeof(line), "\tDS.B $%X\n", (unsigned)size);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static void render_asm_dc_w_values(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t size, const char *comment) {
  uint32_t cursor = 0U;
  if (preview == NULL || data == NULL || size == 0U) return;
  while (cursor + 2U <= size) {
    uint32_t line_count = (size - cursor) / 2U;
    uint32_t index;
    if (line_count > 8U) line_count = 8U;
    hash_asm_text(preview, "\tdc.w ");
    for (index = 0U; index < line_count; ++index) {
      char token[16];
      if (index != 0U) hash_asm_text(preview, ",");
      snprintf(token, sizeof(token), "$%04X", (unsigned)m68k_read_u16be(data + offset + cursor + (index * 2U)));
      hash_asm_text(preview, token);
    }
    if (comment != NULL && comment[0] != '\0') {
      hash_asm_text(preview, "\t; ");
      hash_asm_text(preview, comment);
    }
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
    cursor += line_count * 2U;
  }
  if (cursor < size) render_asm_dc_b(preview, data, offset + cursor, size - cursor, comment);
}

static void render_asm_dc_l_values(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t size, const char *comment) {
  uint32_t cursor = 0U;
  if (preview == NULL || data == NULL || size == 0U) return;
  while (cursor + 4U <= size) {
    uint32_t line_count = (size - cursor) / 4U;
    uint32_t index;
    if (line_count > 4U) line_count = 4U;
    hash_asm_text(preview, "\tdc.l ");
    for (index = 0U; index < line_count; ++index) {
      char token[16];
      if (index != 0U) hash_asm_text(preview, ",");
      snprintf(token, sizeof(token), "$%08X", (unsigned)m68k_read_u32be(data + offset + cursor + (index * 4U)));
      hash_asm_text(preview, token);
    }
    if (comment != NULL && comment[0] != '\0') {
      hash_asm_text(preview, "\t; ");
      hash_asm_text(preview, comment);
    }
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
    cursor += line_count * 4U;
  }
  if (cursor < size) render_asm_dc_b(preview, data, offset + cursor, size - cursor, comment);
}

static int lookup_exact_pointer_value_label_offset(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t section_size, uint32_t value, uint32_t *out_source_offset) {
  size_t index;
  uint32_t logical_address = 0U;
  if (out_source_offset != NULL) *out_source_offset = 0U;
  if (lookup == NULL) return 0;
  if (value < section_size && lookup_has_renderable_label(lookup, section_index, value) &&
      lookup_source_logical_address(lookup, section_index, value, &logical_address) &&
      logical_address == value) {
    if (out_source_offset != NULL) *out_source_offset = value;
    return 1;
  }
  if (lookup->runtime_address_ranges == NULL) return 0;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_ranges[index].fact;
    uint32_t delta;
    uint32_t source_offset;
    logical_address = 0U;
    if (!runtime_range_is_materialized(lookup, fact) || fact->section_index != section_index ||
        !fact->has_runtime_address || value < fact->runtime_address) {
      continue;
    }
    delta = value - fact->runtime_address;
    if (delta >= fact->size || fact->offset > UINT32_MAX - delta) continue;
    source_offset = fact->offset + delta;
    if (source_offset >= section_size) continue;
    if (!lookup_has_renderable_label(lookup, section_index, source_offset)) continue;
    if (!lookup_source_logical_address(lookup, section_index, source_offset, &logical_address) ||
        logical_address != value) {
      continue;
    }
    if (out_source_offset != NULL) *out_source_offset = source_offset;
    return 1;
  }
  return 0;
}

static int render_asm_pointer_table_raw_long(M68kRenderIRPreview *preview, const M68kDecodeSectionIR *section,
    const M68kRenderLookup *lookup, uint32_t offset, const char *comment) {
  char line[256];
  char name[64];
  uint32_t target;
  uint32_t target_offset;
  if (preview == NULL || section == NULL || lookup == NULL || section->data == NULL ||
      offset > section->size || section->size - offset < 4U) {
    return 0;
  }
  target = m68k_read_u32be(section->data + offset);
  if (target == 0U) return 0;
  if (!lookup_exact_pointer_value_label_offset(lookup, section->section_index, section->size, target,
      &target_offset)) {
    return 0;
  }
  (void)format_rendered_asm_label_with_generation(lookup, name, sizeof(name), section->section_index, target_offset);
  if (comment != NULL && comment[0] != '\0')
    snprintf(line, sizeof(line), "\tdc.l %s\t; %s\n", name, comment);
  else
    snprintf(line, sizeof(line), "\tdc.l %s\n", name);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  return 1;
}

static void render_asm_dc_symbol_expr(M68kRenderIRPreview *preview, uint32_t size, const char *expr,
    const char *comment) {
  const char *directive = size == 4U ? "dc.l" : size == 2U ? "dc.w" : "dc.b";
  char line[256];
  if (preview == NULL || expr == NULL || expr[0] == '\0') return;
  if (comment != NULL && comment[0] != '\0')
    snprintf(line, sizeof(line), "\t%s %s\t; %s\n", directive, expr, comment);
  else
    snprintf(line, sizeof(line), "\t%s %s\n", directive, expr);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static void render_asm_ds_best_fit(M68kRenderIRPreview *preview, uint32_t offset, uint32_t size) {
  char line[96];
  const char *directive = "DS.B";
  uint32_t count = size;
  if (preview == NULL || size == 0U) return;
  if ((offset & 3U) == 0U && (size & 3U) == 0U) {
    directive = "DS.L";
    count = size / 4U;
  } else if ((offset & 1U) == 0U && (size & 1U) == 0U) {
    directive = "DS.W";
    count = size / 2U;
  }
  snprintf(line, sizeof(line), "\t%s $%X\n", directive, (unsigned)count);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static int structured_data_item_is_copper_list(const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS &&
    strcmp(item->semantic_role, "copper_list") == 0;
}

static int structured_data_item_is_palette(const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS &&
    strcmp(item->semantic_role, "palette") == 0;
}

static int structured_data_item_is_pointer_table(const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS &&
    strcmp(item->semantic_role, "pointer_table") == 0;
}

static int structured_data_item_is_word_relative_lookup_table(const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS && item->has_target &&
    strcmp(item->semantic_role, "lookup_table") == 0;
}

static int structured_data_item_is_absolute_long_lookup_table(const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS &&
    strcmp(item->semantic_role, "lookup_table") == 0;
}

static int format_absolute_long_lookup_table_expr(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, uint32_t raw_long, char *expr, size_t expr_size) {
  uint32_t target_offset = 0U;
  if (lookup == NULL || section == NULL || expr == NULL || expr_size == 0U) return 0;
  expr[0] = '\0';
  if (raw_long == 0U) {
    snprintf(expr, expr_size, "$00000000");
    return strlen(expr) + 1U < expr_size;
  }
  if (!lookup_exact_pointer_value_label_offset(lookup, section->section_index, section->size, raw_long,
      &target_offset)) {
    return 0;
  }
  (void)format_rendered_asm_label_with_generation(lookup, expr, expr_size, section->section_index, target_offset);
  return expr[0] != '\0' && strlen(expr) + 1U < expr_size;
}

static int render_asm_absolute_long_lookup_table(M68kRenderIRPreview *preview,
    const M68kDecodeSectionIR *section, const M68kRenderLookup *lookup,
    const M68kAnalysisStructuredDataItem *item, uint32_t available, const char *comment) {
  uint32_t cursor = 0U;
  if (preview == NULL || section == NULL || lookup == NULL || item == NULL || section->data == NULL ||
      item->offset >= section->size || (available & 3U) != 0U) {
    return 0;
  }
  while (cursor + 4U <= available) {
    uint32_t line_count = (available - cursor) / 4U;
    uint32_t index;
    if (line_count > 4U) line_count = 4U;
    hash_asm_text(preview, "\tdc.l ");
    for (index = 0U; index < line_count; ++index) {
      char expr[96];
      uint32_t raw_long = m68k_read_u32be(section->data + item->offset + cursor + (index * 4U));
      if (!format_absolute_long_lookup_table_expr(lookup, section, raw_long, expr, sizeof(expr)))
        snprintf(expr, sizeof(expr), "$%08X", (unsigned)raw_long);
      if (index != 0U) hash_asm_text(preview, ",");
      hash_asm_text(preview, expr);
    }
    if (comment != NULL && comment[0] != '\0') {
      hash_asm_text(preview, "\t; ");
      hash_asm_text(preview, comment);
    }
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
    cursor += line_count * 4U;
  }
  return cursor == available;
}

static int format_word_relative_lookup_table_expr(const M68kRenderLookup *lookup,
    const M68kAnalysisStructuredDataItem *item, uint16_t raw_word, char *expr, size_t expr_size) {
  int32_t displacement = (int32_t)(int16_t)raw_word;
  int64_t target_offset = (int64_t)item->target_offset + displacement;
  char target_name[96];
  char base_name[96];
  if (lookup == NULL || item == NULL || expr == NULL || expr_size == 0U ||
      item->target_section >= lookup->section_count || target_offset < 0 ||
      target_offset > UINT32_MAX) {
    return 0;
  }
  expr[0] = '\0';
  if (!lookup_has_renderable_label(lookup, item->target_section, item->target_offset) ||
      !lookup_has_renderable_label(lookup, item->target_section, (uint32_t)target_offset)) {
    return 0;
  }
  (void)format_rendered_asm_label_with_generation(lookup, base_name, sizeof(base_name),
    item->target_section, item->target_offset);
  (void)format_rendered_asm_label_with_generation(lookup, target_name, sizeof(target_name),
    item->target_section, (uint32_t)target_offset);
  snprintf(expr, expr_size, "%s-%s", target_name, base_name);
  return strlen(expr) + 1U < expr_size;
}

static int render_asm_word_relative_lookup_table(M68kRenderIRPreview *preview,
    const M68kDecodeSectionIR *section, const M68kRenderLookup *lookup,
    const M68kAnalysisStructuredDataItem *item, uint32_t available, const char *comment) {
  uint32_t cursor = 0U;
  if (preview == NULL || section == NULL || lookup == NULL || item == NULL || section->data == NULL ||
      item->offset >= section->size || (available & 1U) != 0U) {
    return 0;
  }
  while (cursor + 2U <= available) {
    uint32_t line_count = (available - cursor) / 2U;
    uint32_t index;
    if (line_count > 4U) line_count = 4U;
    hash_asm_text(preview, "\tdc.w ");
    for (index = 0U; index < line_count; ++index) {
      char expr[192];
      uint16_t raw_word = m68k_read_u16be(section->data + item->offset + cursor + (index * 2U));
      if (!format_word_relative_lookup_table_expr(lookup, item, raw_word, expr, sizeof(expr)))
        snprintf(expr, sizeof(expr), "$%04X", (unsigned)raw_word);
      if (index != 0U) hash_asm_text(preview, ",");
      hash_asm_text(preview, expr);
    }
    if (comment != NULL && comment[0] != '\0') {
      hash_asm_text(preview, "\t; ");
      hash_asm_text(preview, comment);
    }
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
    cursor += line_count * 2U;
  }
  return cursor == available;
}

static int format_copper_register_symbol(uint16_t copper_register_word, char *buf, size_t buf_size) {
  const AmigaOsHardwareRegisterInfo *hardware_register;
  const AmigaOsHardwareRegisterFieldInfo *hardware_field;
  const AmigaOsHardwareRegisterRangeInfo *hardware_range;
  uint32_t offset = (uint32_t)(copper_register_word & 0x01FEU);
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if ((copper_register_word & 1U) != 0U) return 0;
  hardware_register = amiga_os_find_hardware_register_by_base_offset("_custom", offset);
  if (hardware_register != NULL && hardware_register->symbol_name != NULL &&
      hardware_register->symbol_name[0] != '\0') {
    snprintf(buf, buf_size, "%s", hardware_register->symbol_name);
    return strlen(buf) + 1U < buf_size;
  }
  hardware_field = amiga_os_find_hardware_register_field_by_base_offset("_custom", offset);
  if (hardware_field != NULL && format_amiga_hardware_register_field_symbol(hardware_field, 0, buf, buf_size))
    return 1;
  hardware_range = amiga_os_find_hardware_register_range_by_base_offset("_custom", offset);
  if (hardware_range != NULL && format_amiga_hardware_register_range_symbol(hardware_range, offset, 0, buf, buf_size))
    return 1;
  return 0;
}

static int format_copper_register_value_expr(uint16_t copper_register_word, uint16_t value, char *buf,
    size_t buf_size) {
  const AmigaOsHardwareRegisterInfo *hardware_register;
  const char *domain_name;
  uint32_t offset = (uint32_t)(copper_register_word & 0x01FEU);
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if ((copper_register_word & 1U) != 0U) return 0;
  hardware_register = amiga_os_find_hardware_register_by_base_offset("_custom", offset);
  if (hardware_register == NULL) return 0;
  if (amiga_hardware_register_custom_immediate_expr(hardware_register, value, 0, buf, buf_size)) return 1;
  if (hardware_register->value_domain_id == AMIGA_OS_VALUE_DOMAIN_ID_NONE) return 0;
  domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, hardware_register->value_domain_id);
  return amiga_value_domain_symbolic_expr(domain_name, value, buf, buf_size);
}

static const AmigaOsHardwareRegisterInfo *copper_runtime_pointer_register(uint16_t copper_register_word) {
  const AmigaOsHardwareRegisterInfo *hardware_register;
  const AmigaOsHardwareRegisterRangeInfo *hardware_range;
  uint32_t offset = (uint32_t)(copper_register_word & 0x01FEU);
  if ((copper_register_word & 1U) != 0U) return NULL;
  hardware_register = amiga_os_find_hardware_register_by_base_offset("_custom", offset);
  if (hardware_register == NULL) {
    hardware_range = amiga_os_find_hardware_register_range_by_base_offset("_custom", offset);
    if (hardware_range != NULL)
      hardware_register = amiga_os_find_hardware_register_by_base_offset("_custom", hardware_range->offset);
  }
  if (hardware_register == NULL ||
      (hardware_register->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) == 0U ||
      hardware_register->runtime_target_role == NULL || hardware_register->runtime_target_role[0] == '\0') {
    return NULL;
  }
  return hardware_register;
}

static void format_runtime_address_symbol_name(const char *role, uint32_t address, const char *suffix,
    char *buf, size_t buf_size) {
  char prefix[40];
  size_t used = 0U;
  size_t index;
  if (buf == NULL || buf_size == 0U) return;
  if (role == NULL || role[0] == '\0') role = "memory";
  for (index = 0U; role[index] != '\0' && used + 1U < sizeof(prefix); ++index) {
    char ch = role[index];
    if ((ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') ||
        (ch >= '0' && ch <= '9') || ch == '_') {
      prefix[used++] = ch;
    } else if (used != 0U && prefix[used - 1U] != '_') {
      prefix[used++] = '_';
    }
  }
  if (used == 0U) snprintf(prefix, sizeof(prefix), "memory");
  else prefix[used] = '\0';
  snprintf(buf, buf_size, "%s_%08X%s", prefix, (unsigned)address, suffix != NULL ? suffix : "");
}

static int render_asm_define_runtime_address_word_symbols_once(M68kRenderIRPreview *preview,
    const char *role, uint32_t address, char *high_symbol, size_t high_symbol_size,
    char *low_symbol, size_t low_symbol_size) {
  char base_symbol[80];
  char high_expr[112];
  char low_expr[160];
  if (high_symbol != NULL && high_symbol_size != 0U) high_symbol[0] = '\0';
  if (low_symbol != NULL && low_symbol_size != 0U) low_symbol[0] = '\0';
  if (preview == NULL || address == 0U) return 0;
  format_runtime_address_symbol_name(role, address, "", base_symbol, sizeof(base_symbol));
  format_runtime_address_symbol_name(role, address, "_hi", high_symbol, high_symbol_size);
  format_runtime_address_symbol_name(role, address, "_lo", low_symbol, low_symbol_size);
  if (high_symbol == NULL || high_symbol[0] == '\0' || low_symbol == NULL || low_symbol[0] == '\0') return 0;
  snprintf(high_expr, sizeof(high_expr), "%s/$10000", base_symbol);
  snprintf(low_expr, sizeof(low_expr), "%s-(%s*$10000)", base_symbol, high_symbol);
  return render_asm_declare_symbol_hex_once(preview, base_symbol, address) &&
    render_asm_declare_symbol_expr_once(preview, high_symbol, high_expr) &&
    render_asm_declare_symbol_expr_once(preview, low_symbol, low_expr);
}

static int render_asm_define_runtime_address_symbol_once(M68kRenderIRPreview *preview,
    const char *role, uint32_t address, char *symbol, size_t symbol_size) {
  if (symbol != NULL && symbol_size != 0U) symbol[0] = '\0';
  if (preview == NULL || symbol == NULL || symbol_size == 0U || address == 0U) return 0;
  format_runtime_address_symbol_name(role, address, "", symbol, symbol_size);
  if (symbol[0] == '\0') return 0;
  return render_asm_declare_symbol_hex_once(preview, symbol, address);
}

static int format_copper_runtime_pointer_value_expr(M68kRenderIRPreview *preview, const uint8_t *data,
    uint32_t offset, uint32_t cursor, uint32_t size, uint16_t first, uint16_t second, char *buf,
    size_t buf_size) {
  const AmigaOsHardwareRegisterInfo *hardware_register;
  uint32_t register_offset = (uint32_t)(first & 0x01FEU);
  uint16_t pair_first;
  uint16_t pair_second;
  uint32_t pointer_address;
  char high_symbol[80];
  char low_symbol[80];
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (data == NULL || preview == NULL || (first & 1U) != 0U) return 0;
  hardware_register = copper_runtime_pointer_register(first);
  if (hardware_register != NULL && cursor + 8U <= size) {
    pair_first = m68k_read_u16be(data + offset + cursor + 4U);
    pair_second = m68k_read_u16be(data + offset + cursor + 6U);
    if ((pair_first & 1U) == 0U && (uint32_t)(pair_first & 0x01FEU) == register_offset + 2U &&
        register_offset >= hardware_register->offset &&
        ((register_offset - hardware_register->offset) & 3U) == 0U) {
      pointer_address = ((uint32_t)second << 16) | pair_second;
      if (render_asm_define_runtime_address_word_symbols_once(preview, hardware_register->runtime_target_role,
          pointer_address, high_symbol, sizeof(high_symbol), low_symbol, sizeof(low_symbol))) {
        snprintf(buf, buf_size, "%s", high_symbol);
        return 1;
      }
    }
  }
  if (cursor >= 4U) {
    uint16_t prev_first = m68k_read_u16be(data + offset + cursor - 4U);
    uint16_t prev_second = m68k_read_u16be(data + offset + cursor - 2U);
    uint32_t prev_register_offset = (uint32_t)(prev_first & 0x01FEU);
    hardware_register = copper_runtime_pointer_register(prev_first);
    if (hardware_register != NULL && (prev_first & 1U) == 0U &&
        register_offset == prev_register_offset + 2U &&
        prev_register_offset >= hardware_register->offset &&
        ((prev_register_offset - hardware_register->offset) & 3U) == 0U) {
      pointer_address = ((uint32_t)prev_second << 16) | second;
      if (render_asm_define_runtime_address_word_symbols_once(preview, hardware_register->runtime_target_role,
          pointer_address, high_symbol, sizeof(high_symbol), low_symbol, sizeof(low_symbol))) {
        snprintf(buf, buf_size, "%s", low_symbol);
        return 1;
      }
    }
  }
  return 0;
}

static int format_copper_runtime_pointer_comment(const uint8_t *data, uint32_t offset, uint32_t cursor,
    uint32_t size, uint16_t first, uint16_t second, char *buf, size_t buf_size) {
  const AmigaOsHardwareRegisterInfo *hardware_register;
  uint32_t register_offset = (uint32_t)(first & 0x01FEU);
  uint32_t pointer_index;
  uint16_t next_first;
  uint16_t next_second;
  uint32_t pointer_address;
  if (data == NULL || buf == NULL || buf_size == 0U || cursor + 8U > size) return 0;
  buf[0] = '\0';
  hardware_register = copper_runtime_pointer_register(first);
  if (hardware_register == NULL) return 0;
  if (register_offset < hardware_register->offset ||
      ((register_offset - hardware_register->offset) & 3U) != 0U) {
    return 0;
  }
  next_first = m68k_read_u16be(data + offset + cursor + 4U);
  next_second = m68k_read_u16be(data + offset + cursor + 6U);
  if ((next_first & 1U) != 0U || (uint32_t)(next_first & 0x01FEU) != register_offset + 2U) return 0;
  pointer_index = (register_offset - hardware_register->offset) / 4U;
  pointer_address = ((uint32_t)second << 16) | next_second;
  if (pointer_address == 0U) {
    snprintf(buf, buf_size, "%s pointer %u disabled", hardware_register->runtime_target_role,
      (unsigned)pointer_index);
  } else {
    snprintf(buf, buf_size, "%s pointer $%08X", hardware_register->runtime_target_role,
      (unsigned)pointer_address);
  }
  return strlen(buf) + 1U < buf_size;
}

static int format_amiga_display_register_comment(const AmigaOsHardwareRegisterInfo *hardware_register,
    uint32_t value, char *buf, size_t buf_size) {
  uint32_t word = value & 0xFFFFU;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (hardware_register == NULL || hardware_register->symbol_name == NULL) return 0;
  if (strcmp(hardware_register->symbol_name, "bplcon0") == 0) {
    uint32_t plane_count = (word >> 12) & 7U;
    const char *resolution = (word & 0x8000U) != 0U ? "hires" : "lores";
    const char *color = (word & 0x0200U) != 0U ? " color" : "";
    if (plane_count == 0U) return 0;
    snprintf(buf, buf_size, "display %u bitplanes %s%s", (unsigned)plane_count, resolution, color);
    return strlen(buf) + 1U < buf_size;
  }
  if (strcmp(hardware_register->symbol_name, "bplcon1") == 0) {
    snprintf(buf, buf_size, "display scroll pf1=%u pf2=%u",
      (unsigned)(word & 0xFU), (unsigned)((word >> 4) & 0xFU));
    return strlen(buf) + 1U < buf_size;
  }
  if (strcmp(hardware_register->symbol_name, "diwstrt") == 0) {
    snprintf(buf, buf_size, "display window start v=$%02X h=$%02X",
      (unsigned)((word >> 8) & 0xFFU), (unsigned)(word & 0xFFU));
    return strlen(buf) + 1U < buf_size;
  }
  if (strcmp(hardware_register->symbol_name, "diwstop") == 0) {
    snprintf(buf, buf_size, "display window stop v=$%02X h=$%02X",
      (unsigned)((word >> 8) & 0xFFU), (unsigned)(word & 0xFFU));
    return strlen(buf) + 1U < buf_size;
  }
  if (strcmp(hardware_register->symbol_name, "ddfstrt") == 0) {
    snprintf(buf, buf_size, "display fetch start $%02X", (unsigned)(word & 0xFFU));
    return strlen(buf) + 1U < buf_size;
  }
  if (strcmp(hardware_register->symbol_name, "ddfstop") == 0) {
    snprintf(buf, buf_size, "display fetch stop $%02X", (unsigned)(word & 0xFFU));
    return strlen(buf) + 1U < buf_size;
  }
  if (strcmp(hardware_register->symbol_name, "bpl1mod") == 0 ||
      strcmp(hardware_register->symbol_name, "bpl2mod") == 0) {
    int16_t modulo = (int16_t)word;
    snprintf(buf, buf_size, "bitplane modulo %d bytes", (int)modulo);
    return strlen(buf) + 1U < buf_size;
  }
  if (strcmp(hardware_register->symbol_name, "bltsize") == 0) {
    uint32_t height = (word >> 6) & 0x3FFU;
    uint32_t width_words = word & 0x3FU;
    if (height == 0U) height = 1024U;
    if (width_words == 0U) width_words = 64U;
    snprintf(buf, buf_size, "blitter size %u rows x %u words (%u bytes/row)",
      (unsigned)height, (unsigned)width_words, (unsigned)(width_words * 2U));
    return strlen(buf) + 1U < buf_size;
  }
  return 0;
}

static int format_amiga_disk_dma_register_comment(const AmigaOsHardwareRegisterInfo *hardware_register,
    uint32_t value, char *buf, size_t buf_size) {
  uint32_t word = value & 0xFFFFU;
  uint32_t byte_length;
  const char *direction;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (hardware_register == NULL || hardware_register->symbol_name == NULL ||
      (strcmp(hardware_register->symbol_name, "dsklen") != 0 &&
       strcmp(hardware_register->symbol_name, "dsksync") != 0)) {
    return 0;
  }
  if (strcmp(hardware_register->symbol_name, "dsksync") == 0) {
    snprintf(buf, buf_size, "disk sync word $%04X", (unsigned)word);
    return strlen(buf) + 1U < buf_size;
  }
  if ((word & AMIGA_OS_DSKLEN_DMA_ENABLE_MASK) == 0U) return 0;
  byte_length = (word & AMIGA_OS_DSKLEN_LENGTH_MASK) * AMIGA_OS_DSKLEN_LENGTH_UNIT_BYTES;
  if (byte_length == 0U) return 0;
  direction = (word & AMIGA_OS_DSKLEN_WRITE_MASK) != 0U ? "write" : "read";
  snprintf(buf, buf_size, "disk DMA %s %u bytes", direction, (unsigned)byte_length);
  return strlen(buf) + 1U < buf_size;
}

static int format_amiga_audio_register_comment(const AmigaOsHardwareRegisterFieldInfo *hardware_field,
    uint32_t value, char *buf, size_t buf_size) {
  uint32_t word = value & 0xFFFFU;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (hardware_field == NULL || hardware_field->register_symbol == NULL || hardware_field->field_symbol == NULL ||
      strncmp(hardware_field->register_symbol, "aud", 3U) != 0) {
    return 0;
  }
  if (strcmp(hardware_field->field_symbol, "ac_len") == 0) {
    snprintf(buf, buf_size, "sound sample length %u bytes", (unsigned)(word * 2U));
    return strlen(buf) + 1U < buf_size;
  }
  if (strcmp(hardware_field->field_symbol, "ac_per") == 0) {
    snprintf(buf, buf_size, "audio period %u", (unsigned)word);
    return strlen(buf) + 1U < buf_size;
  }
  if (strcmp(hardware_field->field_symbol, "ac_vol") == 0) {
    snprintf(buf, buf_size, "audio volume %u", (unsigned)word);
    return strlen(buf) + 1U < buf_size;
  }
  return 0;
}

static int format_amiga_audio_register_access_comment(const AmigaOsHardwareRegisterFieldInfo *hardware_field,
    char *buf, size_t buf_size) {
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (hardware_field == NULL || hardware_field->register_symbol == NULL || hardware_field->field_symbol == NULL ||
      strncmp(hardware_field->register_symbol, "aud", 3U) != 0) {
    return 0;
  }
  if (strcmp(hardware_field->field_symbol, "ac_per") == 0) {
    snprintf(buf, buf_size, "audio period");
    return strlen(buf) + 1U < buf_size;
  }
  if (strcmp(hardware_field->field_symbol, "ac_dat") == 0) {
    snprintf(buf, buf_size, "audio data word");
    return strlen(buf) + 1U < buf_size;
  }
  return 0;
}

static int format_amiga_hardware_register_access_comment(const AmigaOsHardwareRegisterInfo *hardware_register,
    uint8_t access_kind, char *buf, size_t buf_size) {
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (hardware_register == NULL || hardware_register->symbol_name == NULL) return 0;
  if (access_kind == M68K_SIM_ACCESS_MEMORY_READ) {
    if (strcmp(hardware_register->symbol_name, "joy0dat") == 0) {
      snprintf(buf, buf_size, "joystick/mouse port 0 data");
      return strlen(buf) + 1U < buf_size;
    }
    if (strcmp(hardware_register->symbol_name, "joy1dat") == 0) {
      snprintf(buf, buf_size, "joystick/mouse port 1 data");
      return strlen(buf) + 1U < buf_size;
    }
    if (strcmp(hardware_register->symbol_name, "intreqr") == 0) {
      snprintf(buf, buf_size, "interrupt request state");
      return strlen(buf) + 1U < buf_size;
    }
  }
  return 0;
}

static int format_amiga_hardware_range_access_comment(const AmigaOsHardwareRegisterRangeInfo *hardware_range,
    uint32_t offset, uint8_t access_kind, uint32_t byte_width, char *buf, size_t buf_size) {
  uint32_t index;
  uint32_t color_count;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (hardware_range == NULL || hardware_range->symbol_name == NULL ||
      strcmp(hardware_range->symbol_name, "color") != 0 ||
      access_kind != M68K_SIM_ACCESS_MEMORY_WRITE || offset < hardware_range->offset) {
    return 0;
  }
  index = (offset - hardware_range->offset) / 2U;
  color_count = byte_width > 2U ? byte_width / 2U : 1U;
  if (color_count > 1U) {
    snprintf(buf, buf_size, "palette colors %u-%u", (unsigned)index, (unsigned)(index + color_count - 1U));
  } else {
    snprintf(buf, buf_size, "palette color %u", (unsigned)index);
  }
  return strlen(buf) + 1U < buf_size;
}

static int format_copper_display_register_comment(uint16_t first, uint16_t second, char *buf, size_t buf_size) {
  const AmigaOsHardwareRegisterInfo *hardware_register;
  uint32_t register_offset = (uint32_t)(first & 0x01FEU);
  if (buf == NULL || buf_size == 0U || (first & 1U) != 0U) return 0;
  buf[0] = '\0';
  hardware_register = amiga_os_find_hardware_register_by_base_offset("_custom", register_offset);
  return format_amiga_display_register_comment(hardware_register, (uint32_t)second, buf, buf_size);
}

static int format_copper_wait_comment(uint16_t first, uint16_t second, char *buf, size_t buf_size) {
  uint32_t wait_word = (uint32_t)(first & 0xFFFEU);
  if (buf == NULL || buf_size == 0U || (first & 1U) == 0U || (second & 1U) != 0U) return 0;
  buf[0] = '\0';
  snprintf(buf, buf_size, "copper wait v=$%02X h=$%02X mask $%04X",
    (unsigned)((wait_word >> 8) & 0xFFU), (unsigned)(wait_word & 0xFEU), (unsigned)second);
  return strlen(buf) + 1U < buf_size;
}

static void render_asm_copper_list_words(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *data, uint32_t offset, uint32_t size,
    const char *comment, uint32_t *io_logical_pc) {
  uint32_t cursor = 0U;
  if (preview == NULL || data == NULL || size == 0U) return;
  while (cursor + 4U <= size) {
    char left[64];
    char right[96];
    char row_comment[96];
    char line[256];
    uint16_t first = m68k_read_u16be(data + offset + cursor);
    uint16_t second = m68k_read_u16be(data + offset + cursor + 2U);
    int copper_move = 0;
    int copper_wait = 0;
    if (cursor != 0U && lookup_has_renderable_label(lookup, section->section_index, offset + cursor)) {
      render_asm_label(preview, lookup, section->section_index, offset + cursor, io_logical_pc);
    }
    if (first == 0xFFFFU && second == 0xFFFEU) {
      snprintf(left, sizeof(left), "$FFFF");
    } else if ((first & 1U) != 0U && (second & 1U) == 0U) {
      snprintf(left, sizeof(left), "COPPER_WAIT|$%04X", (unsigned)(first & 0xFFFEU));
      if (!render_asm_include_for_symbol_expr(preview, left)) {
        ++preview->asm_source_instruction_render_failures;
        record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, offset + cursor, 0U);
        return;
      }
      copper_wait = 1;
    } else if (!format_copper_register_symbol(first, left, sizeof(left))) {
      snprintf(left, sizeof(left), "$%04X", (unsigned)first);
    } else if (!render_asm_include_for_symbol_expr(preview, left)) {
      ++preview->asm_source_instruction_render_failures;
      record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, offset + cursor, 0U);
      return;
    } else {
      copper_move = 1;
    }
    if (copper_move &&
        format_copper_runtime_pointer_value_expr(preview, data, offset, cursor, size, first, second,
          right, sizeof(right))) {
      ;
    } else if (!copper_move || !format_copper_register_value_expr(first, second, right, sizeof(right))) {
      snprintf(right, sizeof(right), "$%04X", (unsigned)second);
    } else if (!render_asm_include_for_symbol_expr(preview, right)) {
      ++preview->asm_source_instruction_render_failures;
      record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, offset + cursor, 0U);
      return;
    }
    row_comment[0] = '\0';
    if (copper_wait) {
      (void)format_copper_wait_comment(first, second, row_comment, sizeof(row_comment));
    } else if (copper_move &&
        !format_copper_display_register_comment(first, second, row_comment, sizeof(row_comment)))
      (void)format_copper_runtime_pointer_comment(data, offset, cursor, size, first, second,
        row_comment, sizeof(row_comment));
    if (comment != NULL && comment[0] != '\0' && row_comment[0] != '\0')
      snprintf(line, sizeof(line), "\tdc.w %s,%s\t; %s; %s\n", left, right, comment, row_comment);
    else if (comment != NULL && comment[0] != '\0')
      snprintf(line, sizeof(line), "\tdc.w %s,%s\t; %s\n", left, right, comment);
    else if (row_comment[0] != '\0')
      snprintf(line, sizeof(line), "\tdc.w %s,%s\t; %s\n", left, right, row_comment);
    else
      snprintf(line, sizeof(line), "\tdc.w %s,%s\n", left, right);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
    if (io_logical_pc != NULL) *io_logical_pc += 4U;
    cursor += 4U;
  }
  if (cursor + 2U <= size) {
    render_asm_dc_w_values(preview, data, offset + cursor, 2U, comment);
    if (io_logical_pc != NULL) *io_logical_pc += 2U;
    cursor += 2U;
  }
  if (cursor < size) {
    render_asm_dc_b(preview, data, offset + cursor, size - cursor, comment);
    if (io_logical_pc != NULL) *io_logical_pc += size - cursor;
  }
}

static void render_asm_palette_words(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *data, uint32_t offset, uint32_t size,
    const char *comment, uint32_t *io_logical_pc) {
  uint32_t cursor = 0U;
  if (preview == NULL || lookup == NULL || section == NULL || data == NULL || size == 0U) return;
  while (cursor + 2U <= size) {
    uint32_t start = cursor;
    uint32_t span;
    if (cursor != 0U && lookup_has_renderable_label(lookup, section->section_index, offset + cursor)) {
      render_asm_label(preview, lookup, section->section_index, offset + cursor, io_logical_pc);
    }
    cursor += 2U;
    while (cursor + 2U <= size && !lookup_has_renderable_label(lookup, section->section_index, offset + cursor))
      cursor += 2U;
    span = cursor - start;
    render_asm_dc_w_values(preview, data, offset + start, span, start == 0U ? comment : NULL);
    if (io_logical_pc != NULL) *io_logical_pc += span;
  }
  if (cursor < size) {
    render_asm_dc_b(preview, data, offset + cursor, size - cursor, NULL);
    if (io_logical_pc != NULL) *io_logical_pc += size - cursor;
  }
}

static void render_asm_structured_data_item(M68kRenderIRPreview *preview, const M68kDecodeSectionIR *section,
    const M68kRenderLookup *lookup, const M68kAnalysisStructuredDataItem *item, uint32_t *io_logical_pc,
    int *out_updated_logical_pc) {
  char comment[128];
  char expr[96];
  const char *comment_text;
  uint32_t available;
  if (out_updated_logical_pc != NULL) *out_updated_logical_pc = 0;
  if (preview == NULL || section == NULL || item == NULL || item->size == 0U) return;
  if (!render_asm_includes_for_structured_data_item(preview, item)) return;
  comment[0] = '\0';
  comment_text = structured_data_item_render_comment(section, item, comment, sizeof(comment)) ? comment : NULL;
  if (item->offset >= section->size || section->data == NULL) {
    render_asm_ds_b(preview, item->size, comment_text);
    return;
  }
  available = section->size - item->offset;
  if (available > item->size) available = item->size;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_STRING && available == item->size &&
      strcmp(item->semantic_role, "length_prefixed_string") == 0) {
    render_asm_dc_b_length_prefixed_string(preview, section->data, item->offset, available, comment_text);
    return;
  }
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_STRING && available == item->size) {
    render_asm_dc_b_string(preview, section->data, item->offset, available, comment_text);
    return;
  }
  if (available == item->size && structured_data_item_is_copper_list(item)) {
    const char *copper_comment = item->comment[0] != '\0' ? comment_text : NULL;
    render_asm_copper_list_words(preview, lookup, section, section->data, item->offset, available, copper_comment,
      io_logical_pc);
    if (out_updated_logical_pc != NULL && io_logical_pc != NULL) *out_updated_logical_pc = 1;
    return;
  }
  if (available == item->size && structured_data_item_is_palette(item)) {
    render_asm_palette_words(preview, lookup, section, section->data, item->offset, available, comment_text,
      io_logical_pc);
    if (out_updated_logical_pc != NULL && io_logical_pc != NULL) *out_updated_logical_pc = 1;
    return;
  }
  if (available == item->size && structured_data_item_is_pointer_table(item)) {
    uint32_t cursor;
    for (cursor = 0U; cursor + 4U <= available; cursor += 4U) {
      const M68kFact *relocation = lookup_relocation_at(lookup, section->section_index, item->offset + cursor);
      if (relocation != NULL && relocation->size == 4U) {
        render_asm_relocation_expr(preview, lookup, relocation);
      } else if (render_asm_pointer_table_raw_long(preview, section, lookup, item->offset + cursor,
          cursor == 0U ? comment_text : NULL)) {
        ;
      } else {
        render_asm_dc_l_values(preview, section->data, item->offset + cursor, 4U,
          cursor == 0U ? comment_text : NULL);
      }
    }
    if (cursor < available) render_asm_dc_b(preview, section->data, item->offset + cursor, available - cursor, NULL);
    return;
  }
  if (available == item->size && structured_data_item_is_word_relative_lookup_table(item) &&
      render_asm_word_relative_lookup_table(preview, section, lookup, item, available, comment_text)) {
    return;
  }
  if (available == item->size && structured_data_item_is_absolute_long_lookup_table(item) &&
      render_asm_absolute_long_lookup_table(preview, section, lookup, item, available, comment_text)) {
    return;
  }
  if (available == item->size &&
      structured_data_item_symbolic_operand_expr(section, item, expr, sizeof(expr))) {
    if (!render_asm_include_for_symbol_expr(preview, expr)) {
      ++preview->asm_source_instruction_render_failures;
      record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER,
        item->has_section_index ? item->section_index : 0U, item->offset, 0U);
      return;
    }
    render_asm_dc_symbol_expr(preview, item->size, expr, comment_text);
    return;
  }
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS && available >= 4U) {
    render_asm_dc_l_values(preview, section->data, item->offset, available, comment_text);
  } else if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS && available >= 2U) {
    render_asm_dc_w_values(preview, section->data, item->offset, available, comment_text);
  } else {
    render_asm_dc_b(preview, section->data, item->offset, available, comment_text);
  }
  if (available < item->size) render_asm_ds_b(preview, item->size - available, comment_text);
}

const M68kDecodeCandidate *find_candidate_at_offset_local(const M68kDecodeSectionIR *section,
    uint32_t offset) {
  size_t lo = 0U;
  size_t hi;
  if (section == NULL) return NULL;
  hi = section->candidate_count;
  while (lo < hi) {
    size_t mid = lo + ((hi - lo) / 2U);
    uint32_t candidate_offset = section->candidates[mid].offset;
    if (candidate_offset == offset) return &section->candidates[mid];
    if (candidate_offset < offset) lo = mid + 1U;
    else hi = mid;
  }
  return NULL;
}

static int operand_uses_single_word_extension_local(const M68kAsmOperandValue *operand) {
  if (operand == NULL) return 0;
  return (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
    (operand->ea_mode == 5U || (operand->ea_mode == 7U && operand->ea_reg == 0U) ||
      (operand->ea_mode == 7U && operand->ea_reg == 2U));
}

static int operand_uses_long_address_extension_local(const M68kAsmOperandValue *operand) {
  if (operand == NULL) return 0;
  return (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
    operand->ea_mode == 7U && operand->ea_reg == 1U;
}

static int operand_uses_immediate_extension_local(const M68kAsmOperandValue *operand) {
  if (operand == NULL) return 0;
  return ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->ea_mode == 7U && operand->ea_reg == 4U) || operand->kind == M68K_ASM_OPERAND_IMM;
}

static M68kAsmOperandValue normalized_layout_operand(const M68kDecodeCandidate *candidate, size_t operand_index) {
  M68kAsmOperandValue operand;
  memset(&operand, 0, sizeof(operand));
  if (candidate == NULL || operand_index >= candidate->operand_count) return operand;
  operand = candidate->operands[operand_index];
  operand.kind = candidate->operand_kinds[operand_index];
  switch (candidate->operand_kinds[operand_index]) {
  case M68K_ASM_OPERAND_ABSL:
    operand.kind = M68K_ASM_OPERAND_EA;
    operand.ea_mode = 7U;
    operand.ea_reg = 1U;
    break;
  case M68K_ASM_OPERAND_IND:
    operand.kind = M68K_ASM_OPERAND_EA;
    operand.ea_mode = 2U;
    break;
  case M68K_ASM_OPERAND_POSTINC:
    operand.kind = M68K_ASM_OPERAND_EA;
    operand.ea_mode = 3U;
    break;
  case M68K_ASM_OPERAND_PREDEC:
    operand.kind = M68K_ASM_OPERAND_EA;
    operand.ea_mode = 4U;
    break;
  default:
    break;
  }
  return operand;
}

static size_t relocation_extension_word_count(uint16_t asm_form_index, uint8_t extension_kind,
    const M68kAsmOperandValue *operand, char size_suffix) {
  if (operand == NULL) return 0U;
  switch (extension_kind) {
  case M68K_ASM_EXTENSION_EA_SINGLE_WORD:
    return operand_uses_single_word_extension_local(operand) ? 1U : 0U;
  case M68K_ASM_EXTENSION_EA_LONG_ADDRESS:
    return operand_uses_long_address_extension_local(operand) ? 2U : 0U;
  case M68K_ASM_EXTENSION_EA_IMMEDIATE:
    return operand_uses_immediate_extension_local(operand) ? (size_suffix == 'l' ? 2U : 1U) : 0U;
  case M68K_ASM_EXTENSION_EA_INDEX:
    if (!((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
        (operand->ea_mode == 6U || (operand->ea_mode == 7U && operand->ea_reg == 3U)))) {
      return 0U;
    }
    return m68k_asm_operand_extension_word_count(asm_form_index, operand, size_suffix);
  case M68K_ASM_EXTENSION_LABEL_DISP16_IF_ZERO:
    return size_suffix == 'b' ? 0U : 1U;
  case M68K_ASM_EXTENSION_LABEL_DISP16_ALWAYS:
  case M68K_ASM_EXTENSION_DISP16_ALWAYS:
    return 1U;
  default:
    return 0U;
  }
}

static char candidate_effective_size_suffix(const M68kDecodeCandidate *candidate) {
  M68kAsmOperandValue layout_operands[M68K_DECODE_IR_MAX_OPERANDS];
  const M68kAsmFormDef *form;
  char size_suffix;
  size_t index;
  if (candidate == NULL || candidate->asm_form_index >= M68K_ASM_FORM_SLOT_COUNT)
    return candidate != NULL ? candidate->size_suffix : '\0';
  form = &g_m68k_asm_forms[candidate->asm_form_index];
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) return candidate->size_suffix;
  for (index = 0U; index < candidate->operand_count; ++index)
    layout_operands[index] = normalized_layout_operand(candidate, index);
  size_suffix = m68k_asm_choose_size_suffix(form, layout_operands, candidate->operand_count,
    candidate->size_suffix);
  return size_suffix != '\0' ? size_suffix : candidate->size_suffix;
}

typedef struct ByteImmediateExtensionSite {
  size_t byte_offset;
  uint8_t operand_index;
} ByteImmediateExtensionSite;

static uint16_t instruction_asm_form_index_local(const M68kInstructionIR *instruction,
    M68kAsmOperandValue *out_operands, size_t max_operands) {
  size_t operand_index;
  uint16_t asm_form_index;
  if (instruction == NULL || out_operands == NULL || max_operands < instruction->operand_count)
    return M68K_ASM_FORM_NONE;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index)
    out_operands[operand_index] = instruction->operands[operand_index].value;
  asm_form_index = instruction->asm_form_index;
  if (asm_form_index < M68K_ASM_FORM_SLOT_COUNT &&
      g_m68k_asm_forms[asm_form_index].mnemonic_id != M68K_ASM_MNEMONIC_NONE) {
    return asm_form_index;
  }
  return m68k_asm_form_index_for_operands_id(instruction->mnemonic_id, out_operands,
    instruction->operand_count, instruction->size_suffix, instruction->target_cpu);
}

static size_t collect_byte_immediate_extension_sites(const M68kInstructionIR *instruction,
    ByteImmediateExtensionSite *out_sites, size_t max_sites) {
  M68kAsmOperandValue operands[4];
  uint16_t asm_form_index;
  const M68kAsmFormDef *form;
  char size_suffix;
  size_t site_count = 0U;
  size_t word_index;
  size_t extension_index;
  if (instruction == NULL || instruction->operand_count > 4U) return 0U;
  asm_form_index = instruction_asm_form_index_local(instruction, operands, sizeof(operands) / sizeof(operands[0]));
  if (asm_form_index >= M68K_ASM_FORM_SLOT_COUNT) return 0U;
  form = &g_m68k_asm_forms[asm_form_index];
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) return 0U;
  size_suffix = m68k_asm_choose_size_suffix(form, operands, instruction->operand_count, instruction->size_suffix);
  if (size_suffix == '\0') size_suffix = instruction->size_suffix;
  word_index = 1U + form->bound_word_count;
  for (extension_index = 0U; extension_index < form->extension_count; ++extension_index) {
    const M68kAsmExtensionDef *extension = &g_m68k_asm_extensions[form->extension_start + extension_index];
    const M68kAsmOperandValue *operand;
    if (extension->operand_index >= instruction->operand_count) continue;
    operand = &operands[extension->operand_index];
    switch (extension->kind) {
    case M68K_ASM_EXTENSION_EA_SINGLE_WORD:
      if (operand_uses_single_word_extension_local(operand)) ++word_index;
      break;
    case M68K_ASM_EXTENSION_EA_LONG_ADDRESS:
      if (operand_uses_long_address_extension_local(operand)) word_index += 2U;
      break;
    case M68K_ASM_EXTENSION_EA_IMMEDIATE:
      if (operand_uses_immediate_extension_local(operand)) {
        if (size_suffix == 'b') {
          if (site_count < max_sites) {
            out_sites[site_count].byte_offset = word_index * 2U;
            out_sites[site_count].operand_index = extension->operand_index;
          }
          ++site_count;
        }
        word_index += size_suffix == 'l' ? 2U : 1U;
      }
      break;
    case M68K_ASM_EXTENSION_EA_INDEX:
      word_index += m68k_asm_operand_extension_word_count(asm_form_index, operand, size_suffix);
      break;
    case M68K_ASM_EXTENSION_LABEL_DISP16_IF_ZERO:
    case M68K_ASM_EXTENSION_LABEL_DISP16_ALWAYS:
    case M68K_ASM_EXTENSION_DISP16_ALWAYS:
      ++word_index;
      break;
    default:
      break;
    }
  }
  return site_count;
}

static void apply_exact_byte_immediate_render_values(M68kInstructionIR *instruction, const uint8_t *raw_bytes,
    size_t raw_size) {
  ByteImmediateExtensionSite sites[4];
  size_t site_count;
  size_t site_index;
  if (instruction == NULL || raw_bytes == NULL || raw_size == 0U) return;
  site_count = collect_byte_immediate_extension_sites(instruction, sites, sizeof(sites) / sizeof(sites[0]));
  for (site_index = 0U; site_index < site_count; ++site_index) {
    uint8_t operand_index = sites[site_index].operand_index;
    uint16_t raw_word;
    if (sites[site_index].byte_offset + 1U >= raw_size) continue;
    if (operand_index >= instruction->operand_count) continue;
    raw_word = m68k_read_u16be(raw_bytes + sites[site_index].byte_offset);
    if ((raw_word & 0xFF00U) == 0U) continue;
    if ((raw_word & 0x00FFU) != (instruction->operands[operand_index].value.value & 0xFFU)) continue;
    instruction->operands[operand_index].has_exact_render_value = 1U;
    instruction->operands[operand_index].exact_render_value = raw_word;
  }
}

static int encoded_bytes_match_with_exact_byte_immediates(const M68kInstructionIR *instruction,
    const uint8_t *encoded_bytes, const uint8_t *raw_bytes, size_t raw_size) {
  ByteImmediateExtensionSite sites[4];
  size_t site_count;
  size_t byte_index;
  if (instruction == NULL || encoded_bytes == NULL || raw_bytes == NULL) return 0;
  if (memcmp(encoded_bytes, raw_bytes, raw_size) == 0) return 1;
  site_count = collect_byte_immediate_extension_sites(instruction, sites, sizeof(sites) / sizeof(sites[0]));
  for (byte_index = 0U; byte_index < raw_size; ++byte_index) {
    size_t site_index;
    int allowed_exact_high_byte = 0;
    if (encoded_bytes[byte_index] == raw_bytes[byte_index]) continue;
    for (site_index = 0U; site_index < site_count; ++site_index) {
      uint8_t operand_index = sites[site_index].operand_index;
      uint16_t raw_word;
      uint16_t encoded_word;
      if (sites[site_index].byte_offset != byte_index) continue;
      if (sites[site_index].byte_offset + 1U >= raw_size) continue;
      if (operand_index >= instruction->operand_count) continue;
      if (instruction->operands[operand_index].has_exact_render_value == 0U) continue;
      raw_word = m68k_read_u16be(raw_bytes + sites[site_index].byte_offset);
      encoded_word = m68k_read_u16be(encoded_bytes + sites[site_index].byte_offset);
      if ((uint16_t)instruction->operands[operand_index].exact_render_value == raw_word &&
          (encoded_word & 0x00FFU) == (raw_word & 0x00FFU)) {
        allowed_exact_high_byte = 1;
        break;
      }
    }
    if (!allowed_exact_high_byte) return 0;
  }
  return 1;
}

static int instruction_has_symbolic_or_relative_text(const M68kInstructionIR *instruction) {
  size_t operand_index;
  if (instruction == NULL) return 1;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (operand->kind == M68K_ASM_OPERAND_LABEL) return 1;
    if (operand->symbol_ref.has_name != 0U || operand->symbol_ref.has_symbol != 0 ||
        operand->symbol_ref.has_symbolic_addend != 0U) {
      return 1;
    }
  }
  return 0;
}

int operand_is_address_register_local(const M68kOperandIR *operand, uint8_t reg_index) {
  if (operand == NULL) return 0;
  return operand->kind == M68K_ASM_OPERAND_AN && operand->value.reg == reg_index;
}

int operand_is_absolute_address_local(const M68kOperandIR *operand, uint32_t address) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_ABSL) return operand->value.value == address;
  if (operand->kind != M68K_ASM_OPERAND_EA) return 0;
  return operand->value.value == address &&
    operand->value.ea_mode == 7U && (operand->value.ea_reg == 0U || operand->value.ea_reg == 1U);
}

int operand_absolute_offset_local(const M68kOperandIR *operand, uint32_t *out_offset) {
  if (operand == NULL || out_offset == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_ABSL) {
    *out_offset = operand->value.value;
    return 1;
  }
  if (operand->kind != M68K_ASM_OPERAND_EA) return 0;
  if (operand->value.ea_mode == 7U && (operand->value.ea_reg == 0U || operand->value.ea_reg == 1U)) {
    *out_offset = operand->value.value;
    return 1;
  }
  return 0;
}

static int candidate_operand_is_absolute_word_local(const M68kDecodeCandidate *candidate, size_t operand_index) {
  return candidate != NULL && operand_index < candidate->operand_count &&
    candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_EA &&
    candidate->operands[operand_index].ea_mode == 7U && candidate->operands[operand_index].ea_reg == 0U;
}

int reglist_contains_address_register_local(const M68kOperandIR *operand, uint8_t reg_index) {
  uint32_t mask;
  if (operand == NULL || operand->kind != M68K_ASM_OPERAND_REGLIST || reg_index >= 8U) return 0;
  mask = operand->value.value;
  return (mask & (1UL << (8U + reg_index))) != 0U;
}

static int platform_state_operand_is_app_base(const M68kRenderPlatformState *state,
    const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  if (state == NULL || operand == NULL) return 0;
  if (operand_is_data_register_local(operand, &reg) && reg < 8U && state->data_app_base_known[reg]) return 1;
  if (operand_address_register_index_local(operand, &reg) && reg < 8U && state->address_app_base_known[reg])
    return 1;
  return 0;
}

static const char *platform_state_operand_layout_base_symbol(const M68kRenderPlatformState *state,
    const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  if (state == NULL || operand == NULL) return NULL;
  if (operand_is_data_register_local(operand, &reg) && reg < 8U && state->data_layout_base_known[reg])
    return state->data_layout_base_symbol[reg];
  if (operand_address_register_index_local(operand, &reg) && reg < 8U && state->address_layout_base_known[reg])
    return state->address_layout_base_symbol[reg];
  return NULL;
}

static const char *platform_state_operand_hardware_base_symbol(const M68kRenderPlatformState *state,
    const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  uint32_t value = 0U;
  const char *base_symbol;
  if (operand == NULL) return NULL;
  if (operand_address_register_index_local(operand, &reg) && reg < 8U &&
      state != NULL && state->address_hardware_base_known[reg]) {
    return state->address_hardware_base_symbol[reg];
  }
  if (operand->symbol_ref.has_name != 0U) {
    uint32_t base_address;
    if (amiga_os_find_hardware_base_address(operand->symbol_ref.name, &base_address))
      return operand->symbol_ref.name;
  }
  if (operand_is_immediate_value_local(operand, &value) || operand_absolute_offset_local(operand, &value)) {
    base_symbol = amiga_os_find_hardware_base_symbol_by_address(value);
    if (base_symbol != NULL && base_symbol[0] != '\0') return base_symbol;
  }
  return NULL;
}

static void platform_state_update_hardware_base_after_instruction(M68kRenderPlatformState *state,
    const M68kInstructionIR *instruction) {
  uint8_t dest_reg = 0U;
  const char *source_base_symbol;
  if (state == NULL || instruction == NULL) return;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_RTS ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_RTE ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_JMP) {
    platform_state_clear_all_hardware_bases(state);
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    if (instruction->operand_count >= 2U && instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
      for (dest_reg = 0U; dest_reg < 8U; ++dest_reg) {
        if (reglist_contains_address_register_local(&instruction->operands[1], dest_reg))
          platform_state_clear_address_hardware_base(state, dest_reg);
      }
    }
    return;
  }
  if (instruction->operand_count < 2U) return;
  source_base_symbol = platform_state_operand_hardware_base_symbol(state, &instruction->operands[0]);
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA) {
    const M68kOperandIR *dest = &instruction->operands[instruction->operand_count - 1U];
    if (operand_address_register_index_local(dest, &dest_reg)) {
      if (source_base_symbol != NULL) platform_state_set_register_hardware_base(state, dest_reg, source_base_symbol);
      else platform_state_clear_address_hardware_base(state, dest_reg);
    }
  }
}

static void platform_state_update_app_base_after_instruction(M68kRenderPlatformState *state,
    const M68kInstructionIR *instruction) {
  uint8_t dest_reg = 0U;
  int source_is_app_base;
  if (state == NULL || instruction == NULL) return;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_RTS ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_RTE ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_JMP) {
    platform_state_clear_all_app_bases(state);
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    if (instruction->operand_count >= 2U && instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
      for (dest_reg = 0U; dest_reg < 8U; ++dest_reg) {
        if (reglist_contains_data_register_local(&instruction->operands[1], dest_reg))
          platform_state_clear_data_app_base(state, dest_reg);
        if (reglist_contains_address_register_local(&instruction->operands[1], dest_reg))
          platform_state_clear_address_app_base(state, dest_reg);
      }
    }
    return;
  }
  if (instruction->operand_count < 2U) return;
  source_is_app_base = platform_state_operand_is_app_base(state, &instruction->operands[0]);
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) {
    const M68kOperandIR *dest = &instruction->operands[instruction->operand_count - 1U];
    if (operand_is_data_register_local(dest, &dest_reg)) {
      if (source_is_app_base) platform_state_set_register_app_base(state, M68K_ANALYSIS_REGISTER_DATA, dest_reg);
      else platform_state_clear_data_app_base(state, dest_reg);
    } else if (operand_address_register_index_local(dest, &dest_reg)) {
      if (source_is_app_base) platform_state_set_register_app_base(state, M68K_ANALYSIS_REGISTER_ADDRESS, dest_reg);
      else platform_state_clear_address_app_base(state, dest_reg);
    }
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
      operand_address_register_index_local(&instruction->operands[instruction->operand_count - 1U], &dest_reg)) {
    platform_state_clear_address_app_base(state, dest_reg);
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ &&
      operand_is_data_register_local(&instruction->operands[instruction->operand_count - 1U], &dest_reg)) {
    platform_state_clear_data_app_base(state, dest_reg);
  }
}

static void platform_state_update_layout_base_after_instruction(M68kRenderPlatformState *state,
    const M68kInstructionIR *instruction) {
  uint8_t dest_reg = 0U;
  const char *source_layout_base;
  if (state == NULL || instruction == NULL) return;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_RTS ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_RTE ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_JMP) {
    platform_state_clear_all_layout_bases(state);
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    if (instruction->operand_count >= 2U && instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
      for (dest_reg = 0U; dest_reg < 8U; ++dest_reg) {
        if (reglist_contains_data_register_local(&instruction->operands[1], dest_reg))
          platform_state_clear_data_layout_base(state, dest_reg);
        if (reglist_contains_address_register_local(&instruction->operands[1], dest_reg))
          platform_state_clear_address_layout_base(state, dest_reg);
      }
    }
    return;
  }
  if (instruction->operand_count < 2U) return;
  source_layout_base = platform_state_operand_layout_base_symbol(state, &instruction->operands[0]);
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) {
    const M68kOperandIR *dest = &instruction->operands[instruction->operand_count - 1U];
    if (operand_is_data_register_local(dest, &dest_reg)) {
      if (source_layout_base != NULL)
        platform_state_set_register_layout_base(state, M68K_ANALYSIS_REGISTER_DATA, dest_reg, source_layout_base);
      else
        platform_state_clear_data_layout_base(state, dest_reg);
    } else if (operand_address_register_index_local(dest, &dest_reg)) {
      if (source_layout_base != NULL)
        platform_state_set_register_layout_base(state, M68K_ANALYSIS_REGISTER_ADDRESS, dest_reg, source_layout_base);
      else
        platform_state_clear_address_layout_base(state, dest_reg);
    }
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
      operand_address_register_index_local(&instruction->operands[instruction->operand_count - 1U], &dest_reg)) {
    platform_state_clear_address_layout_base(state, dest_reg);
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ &&
      operand_is_data_register_local(&instruction->operands[instruction->operand_count - 1U], &dest_reg)) {
    platform_state_clear_data_layout_base(state, dest_reg);
  }
}

static void platform_state_update_library_slots_after_instruction(M68kRenderPlatformState *state,
    const M68kInstructionIR *instruction) {
  const M68kOperandIR *source;
  const M68kOperandIR *dest;
  const char *source_library;
  uint8_t dest_reg = 0U;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  if (state == NULL || instruction == NULL || instruction->operand_count < 2U) return;
  source = &instruction->operands[0];
  dest = &instruction->operands[instruction->operand_count - 1U];
  source_library = platform_state_operand_library(state, source);
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) {
    if (operand_is_data_register_local(dest, &dest_reg)) {
      if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction->size_suffix == 'l' &&
          source_library != NULL) {
        platform_state_set_data_library(state, dest_reg, source_library);
      } else {
        platform_state_clear_data_library(state, dest_reg);
      }
    } else if (operand_address_register_index_local(dest, &dest_reg)) {
      const char *slot_library = NULL;
      if (operand_is_address_displacement_local(source, &base_reg, &displacement))
        slot_library = platform_state_local_base_slot_library(state, base_reg, displacement);
      if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && slot_library != NULL) {
        platform_state_set_register_library(state, dest_reg, slot_library);
      } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && source_library != NULL) {
        platform_state_set_register_library(state, dest_reg, source_library);
      } else if (dest_reg != 6U) {
        platform_state_clear_register(state, dest_reg);
      }
    } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction->size_suffix == 'l' &&
        operand_is_address_displacement_local(dest, &base_reg, &displacement)) {
      if (source_library != NULL) platform_state_set_local_base_slot(state, base_reg, displacement, source_library);
      else platform_state_clear_local_base_slot(state, base_reg, displacement);
    }
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ &&
      operand_is_data_register_local(dest, &dest_reg)) {
    platform_state_clear_data_library(state, dest_reg);
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
      operand_address_register_index_local(dest, &dest_reg) && dest_reg != 6U) {
    platform_state_clear_register(state, dest_reg);
  }
}

void platform_state_update_after_instruction(M68kRenderPlatformState *state, const M68kRenderLookup *lookup,
    const M68kInstructionIR *instruction) {
  if (state == NULL || instruction == NULL) return;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_RTS ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_RTE ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_JMP) {
    platform_state_clear_register(state, 6U);
    platform_state_clear_all_data_libraries(state);
    platform_state_clear_all_local_base_slots(state);
    platform_state_update_hardware_base_after_instruction(state, instruction);
    platform_state_update_app_base_after_instruction(state, instruction);
    platform_state_update_layout_base_after_instruction(state, instruction);
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    if (instruction->operand_count >= 2U) {
      uint8_t reg_index;
      if (reglist_contains_address_register_local(&instruction->operands[1], 6U))
        platform_state_clear_register(state, 6U);
      for (reg_index = 0U; reg_index < 8U; ++reg_index) {
        if (reglist_contains_data_register_local(&instruction->operands[1], reg_index))
          platform_state_clear_data_library(state, reg_index);
        if (reg_index != 6U && reglist_contains_address_register_local(&instruction->operands[1], reg_index))
          platform_state_clear_register(state, reg_index);
      }
    }
    platform_state_update_hardware_base_after_instruction(state, instruction);
    platform_state_update_app_base_after_instruction(state, instruction);
    platform_state_update_layout_base_after_instruction(state, instruction);
    return;
  }
  platform_state_update_library_slots_after_instruction(state, instruction);
  if (instruction->operand_count >= 2U && operand_is_address_register_local(&instruction->operands[1], 6U)) {
    uint32_t absolute_offset = 0U;
    const char *library_name = platform_state_operand_library(state, &instruction->operands[0]);
    if (library_name == NULL && instruction->operands[0].symbol_ref.has_name)
      library_name = amiga_library_name_from_base_symbol_name(instruction->operands[0].symbol_ref.name);
    if (library_name == NULL && instruction->operands[0].symbol_ref.has_section &&
        operand_absolute_offset_local(&instruction->operands[0], &absolute_offset)) {
      library_name = lookup_global_base_slot_library(lookup, instruction->operands[0].symbol_ref.section_index,
        absolute_offset);
    }
    if (library_name == NULL) {
      uint8_t base_reg = 0U;
      int16_t displacement = 0;
      if (operand_is_address_displacement_local(&instruction->operands[0], &base_reg, &displacement) &&
          state->address_base_known[base_reg]) {
        library_name = lookup_base_field_slot_library(lookup, state->address_base_library[base_reg], displacement);
      }
      if (library_name == NULL && operand_is_address_displacement_local(&instruction->operands[0], &base_reg,
          &displacement)) {
        library_name = platform_state_local_base_slot_library(state, base_reg, displacement);
      }
      if (library_name == NULL && operand_is_address_displacement_local(&instruction->operands[0], &base_reg,
          &displacement)) {
        char owner_name[32];
        if (amiga_unknown_base_register_owner_name(base_reg, owner_name, sizeof(owner_name)))
          library_name = lookup_base_field_slot_library(lookup, owner_name, displacement);
      }
    }
    if (library_name == NULL && instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) {
      uint8_t base_reg = 0U;
      int16_t displacement = 0;
      if (!state->address_base_known[6U] &&
          operand_is_address_displacement_local(&instruction->operands[0], &base_reg, &displacement) &&
          base_reg == 6U) {
        library_name = lookup_app_base_field_slot_library(lookup, displacement);
      }
    }
    if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA &&
        library_name != NULL) {
      platform_state_set_register_library(state, 6U, library_name);
    } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA &&
        operand_is_absolute_address_local(&instruction->operands[0], 4U)) {
      platform_state_set_register_library(state, 6U, amiga_os_exec_base_library_name());
    } else {
      platform_state_clear_register(state, 6U);
    }
  }
  platform_state_update_hardware_base_after_instruction(state, instruction);
  platform_state_update_app_base_after_instruction(state, instruction);
  platform_state_update_layout_base_after_instruction(state, instruction);
}

void platform_state_note_call_result_after_instruction(M68kRenderPlatformState *state,
    const M68kInstructionIR *instruction, const AmigaOsLibraryVectorInfo *vector) {
  if (state == NULL || instruction == NULL) return;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_JSR &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_BSR &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_JMP) {
    return;
  }
  platform_state_clear_data_library(state, 0U);
  if (amiga_vector_is_open_library_result(vector) && state->address_base_known[1U])
    platform_state_set_data_library(state, 0U, state->address_base_library[1U]);
}

const AmigaOsLibraryVectorInfo *attach_amiga_lvo_symbol_if_known(const M68kRenderPlatformState *state,
    M68kInstructionIR *instruction) {
  M68kOperandIR *operand;
  const char *base_name;
  const AmigaOsLibraryVectorInfo *vector;
  const char *symbol_name;
  int16_t displacement;
  if (state == NULL || instruction == NULL) return NULL;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_JSR &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_JMP)
    return NULL;
  if (instruction->operand_count != 1U) return NULL;
  if (!state->address_base_known[6]) return NULL;
  operand = &instruction->operands[0];
  if (operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_mode != 5U || operand->value.ea_reg != 6U)
    return NULL;
  displacement = (int16_t)(operand->value.value & 0xFFFFU);
  if (displacement >= 0) return NULL;
  base_name = amiga_os_find_library_base_name(state->address_base_library[6]);
  if (base_name == NULL) return NULL;
  vector = amiga_os_find_library_vector(base_name, displacement);
  if (vector == NULL) return NULL;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, vector->lvo_symbol_id);
  if (symbol_name == NULL || symbol_name[0] == '\0') return NULL;
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
  operand->symbol_ref.has_name = 1U;
  operand->symbol_ref.name_is_generated = 0U;
  operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
  operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
  snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol_name);
  return vector;
}

static void attach_amiga_platform_symbol(M68kOperandIR *operand, const char *symbol_name) {
  if (operand == NULL || symbol_name == NULL || symbol_name[0] == '\0') return;
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
  operand->symbol_ref.has_name = 1U;
  operand->symbol_ref.name_is_generated = 0U;
  operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
  operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
  snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol_name);
}

static void attach_generic_symbol(M68kOperandIR *operand, const char *symbol_name) {
  if (operand == NULL || symbol_name == NULL || symbol_name[0] == '\0') return;
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
  operand->symbol_ref.has_name = 1U;
  operand->symbol_ref.name_is_generated = 0U;
  operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_NONE;
  operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
  snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol_name);
}

static int attach_m68k_cpu_vector_symbols(const M68kRenderLookup *lookup, M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  int attached = 0;
  uint8_t platform_kind = M68K_PLATFORM_BACKEND_UNKNOWN;
  if (lookup != NULL && lookup->object != NULL) platform_kind = lookup->object->platform_backend_kind;
  if (instruction == NULL) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    const M68kCpuExceptionVectorInfo *vector;
    uint32_t address = 0U;
    uint8_t access_kind = M68K_SIM_ACCESS_NONE;
    int uses_vector_slot = 0;
    if (operand->symbol_ref.has_name != 0U) continue;
    if (metadata != NULL && operand_index < 4U)
      access_kind = metadata->operand_access_kinds[operand_index];
    if (!operand_absolute_offset_local(operand, &address)) continue;
    if (!platform_facts_v2_is_callback_vector_slot(platform_kind, address)) continue;
    if (access_kind == M68K_SIM_ACCESS_MEMORY_READ || access_kind == M68K_SIM_ACCESS_MEMORY_WRITE) {
      uses_vector_slot = 1;
    } else if (metadata != NULL && metadata->operation_class == M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS &&
        metadata->source_operand_index == operand_index && operand->kind == M68K_ASM_OPERAND_EA &&
        operand->value.ea_mode == 7U && operand->value.ea_reg == 0U) {
      uses_vector_slot = 1;
    }
    if (!uses_vector_slot) continue;
    vector = m68k_cpu_find_exception_vector_by_address(address);
    if (vector == NULL || vector->symbol_name == NULL || vector->symbol_name[0] == '\0') continue;
    m68k_ir_symbol_ref_init(&operand->symbol_ref);
    operand->symbol_ref.has_name = 1U;
    operand->symbol_ref.name_is_generated = 0U;
    operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_NONE;
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
    snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", vector->symbol_name);
    attached = 1;
  }
  return attached;
}

static int amiga_hardware_register_field_instance_delta(const AmigaOsHardwareRegisterFieldInfo *hardware_field,
    uint32_t *out_delta) {
  size_t index;
  uint32_t canonical_offset = UINT32_MAX;
  if (out_delta != NULL) *out_delta = 0U;
  if (hardware_field == NULL || hardware_field->base_symbol == NULL ||
      hardware_field->register_symbol == NULL || out_delta == NULL) {
    return 0;
  }
  for (index = 0U;; ++index) {
    const AmigaOsHardwareRegisterInfo *register_info = amiga_os_hardware_register_at(index);
    if (register_info == NULL) break;
    if (register_info->base_symbol == NULL || register_info->symbol_name == NULL) continue;
    if (strcmp(register_info->base_symbol, hardware_field->base_symbol) != 0 ||
        strcmp(register_info->symbol_name, hardware_field->register_symbol) != 0) {
      continue;
    }
    if (canonical_offset == UINT32_MAX || register_info->offset < canonical_offset)
      canonical_offset = register_info->offset;
  }
  if (canonical_offset == UINT32_MAX || hardware_field->register_offset < canonical_offset) return 0;
  *out_delta = hardware_field->register_offset - canonical_offset;
  return 1;
}

static int format_amiga_hardware_register_field_instance_delta(
    const AmigaOsHardwareRegisterFieldInfo *hardware_field, uint32_t instance_delta, char *buf, size_t buf_size) {
  uint32_t multiplier;
  int written;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (instance_delta == 0U) return 1;
  if (hardware_field != NULL && hardware_field->repeat_stride_symbol != NULL &&
      hardware_field->repeat_stride_symbol[0] != '\0' && hardware_field->repeat_stride != 0U &&
      (instance_delta % hardware_field->repeat_stride) == 0U) {
    multiplier = instance_delta / hardware_field->repeat_stride;
    if (multiplier == 1U) {
      written = snprintf(buf, buf_size, "%s", hardware_field->repeat_stride_symbol);
    } else {
      written = snprintf(buf, buf_size, "%s*%u", hardware_field->repeat_stride_symbol, (unsigned)multiplier);
    }
    return written > 0 && (size_t)written < buf_size;
  }
  written = snprintf(buf, buf_size, instance_delta < 0x100U ? "$%02X" : "$%X", (unsigned)instance_delta);
  return written > 0 && (size_t)written < buf_size;
}

int format_amiga_hardware_register_field_symbol(const AmigaOsHardwareRegisterFieldInfo *hardware_field,
    int include_hardware_base, char *buf, size_t buf_size) {
  uint32_t instance_delta = 0U;
  char delta_text[16];
  const char *instance_symbol;
  int written;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (hardware_field == NULL || hardware_field->register_symbol == NULL || hardware_field->field_symbol == NULL ||
      hardware_field->register_symbol[0] == '\0' || hardware_field->field_symbol[0] == '\0') {
    return 0;
  }
  instance_symbol = (hardware_field->instance_symbol != NULL && hardware_field->instance_symbol[0] != '\0')
    ? hardware_field->instance_symbol
    : NULL;
  if (instance_symbol != NULL) {
    if (include_hardware_base) {
      if (hardware_field->base_symbol == NULL || hardware_field->base_symbol[0] == '\0') return 0;
      written = snprintf(buf, buf_size, "%s+%s+%s", hardware_field->base_symbol, instance_symbol,
        hardware_field->field_symbol);
      return written > 0 && (size_t)written < buf_size;
    }
    written = snprintf(buf, buf_size, "%s+%s", instance_symbol, hardware_field->field_symbol);
    return written > 0 && (size_t)written < buf_size;
  }
  if (!amiga_hardware_register_field_instance_delta(hardware_field, &instance_delta)) instance_delta = 0U;
  if (!format_amiga_hardware_register_field_instance_delta(hardware_field, instance_delta, delta_text,
      sizeof(delta_text))) {
    return 0;
  }
  if (include_hardware_base) {
    if (hardware_field->base_symbol == NULL || hardware_field->base_symbol[0] == '\0') return 0;
    if (instance_delta != 0U) {
      written = snprintf(buf, buf_size, "%s+%s+%s+%s", hardware_field->base_symbol,
        hardware_field->register_symbol, delta_text, hardware_field->field_symbol);
      return written > 0 && (size_t)written < buf_size;
    }
    written = snprintf(buf, buf_size, "%s+%s+%s", hardware_field->base_symbol, hardware_field->register_symbol,
      hardware_field->field_symbol);
    return written > 0 && (size_t)written < buf_size;
  }
  if (instance_delta != 0U) {
    written = snprintf(buf, buf_size, "%s+%s+%s", hardware_field->register_symbol, delta_text,
      hardware_field->field_symbol);
    return written > 0 && (size_t)written < buf_size;
  }
  written = snprintf(buf, buf_size, "%s+%s", hardware_field->register_symbol, hardware_field->field_symbol);
  return written > 0 && (size_t)written < buf_size;
}

int format_amiga_hardware_register_range_symbol(const AmigaOsHardwareRegisterRangeInfo *hardware_range,
    uint32_t offset, int include_hardware_base, char *buf, size_t buf_size) {
  uint32_t delta;
  char delta_text[16];
  int written;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (hardware_range == NULL || hardware_range->symbol_name == NULL || hardware_range->symbol_name[0] == '\0' ||
      offset < hardware_range->offset || offset >= hardware_range->offset + hardware_range->size) {
    return 0;
  }
  delta = offset - hardware_range->offset;
  snprintf(delta_text, sizeof(delta_text), delta < 0x100U ? "$%02X" : "$%X", (unsigned)delta);
  if (include_hardware_base) {
    if (hardware_range->base_symbol == NULL || hardware_range->base_symbol[0] == '\0') return 0;
    if (delta == 0U)
      written = snprintf(buf, buf_size, "%s+%s", hardware_range->base_symbol, hardware_range->symbol_name);
    else
      written = snprintf(buf, buf_size, "%s+%s+%s", hardware_range->base_symbol,
        hardware_range->symbol_name, delta_text);
  } else {
    if (delta == 0U)
      written = snprintf(buf, buf_size, "%s", hardware_range->symbol_name);
    else
      written = snprintf(buf, buf_size, "%s+%s", hardware_range->symbol_name, delta_text);
  }
  return written > 0 && (size_t)written < buf_size;
}

static int attach_amiga_hardware_register_symbols(const M68kRenderPlatformState *state,
    const M68kInstructionIR *source_instruction, M68kInstructionIR *instruction) {
  size_t operand_index;
  int attached = 0;
  if (instruction == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    uint32_t value = 0U;
    uint8_t base_reg = 0U;
    int16_t displacement = 0;
    const char *base_symbol = NULL;
    const AmigaOsHardwareRegisterInfo *hardware_register = NULL;
    const AmigaOsHardwareRegisterFieldInfo *hardware_field = NULL;
    const AmigaOsHardwareRegisterRangeInfo *hardware_range = NULL;
    char symbol_name[64];
    if (operand->symbol_ref.has_name != 0U) continue;
    if (operand_is_address_displacement_local(operand, &base_reg, &displacement) &&
        state != NULL && base_reg < 8U && state->address_hardware_base_known[base_reg] &&
        displacement >= 0) {
      hardware_register = amiga_os_find_hardware_register_by_base_offset(
        state->address_hardware_base_symbol[base_reg], (uint32_t)(uint16_t)displacement);
      hardware_field = amiga_os_find_hardware_register_field_by_base_offset(
        state->address_hardware_base_symbol[base_reg], (uint32_t)(uint16_t)displacement);
      if (hardware_field != NULL &&
          format_amiga_hardware_register_field_symbol(hardware_field, 0, symbol_name, sizeof(symbol_name))) {
        attach_amiga_platform_symbol(operand, symbol_name);
        attached = 1;
        continue;
      }
      if (hardware_register != NULL) {
        attach_amiga_platform_symbol(operand, hardware_register->symbol_name);
        attached = 1;
        continue;
      }
      {
        hardware_range = amiga_os_find_hardware_register_range_by_base_offset(
          state->address_hardware_base_symbol[base_reg], (uint32_t)(uint16_t)displacement);
        if (hardware_range == NULL ||
            !format_amiga_hardware_register_range_symbol(hardware_range, (uint32_t)(uint16_t)displacement,
              0, symbol_name, sizeof(symbol_name))) {
          continue;
        }
      }
      attach_amiga_platform_symbol(operand, symbol_name);
      attached = 1;
      continue;
    }
    if (operand_absolute_offset_local(operand, &value)) {
      base_symbol = amiga_os_find_hardware_base_symbol_by_address(value);
      if (source_instruction != NULL && source_instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
          base_symbol != NULL && base_symbol[0] != '\0') {
        attach_amiga_platform_symbol(operand, base_symbol);
        attached = 1;
        continue;
      }
      hardware_field = amiga_os_find_hardware_register_field_by_cpu_address(value);
      if (hardware_field != NULL &&
          format_amiga_hardware_register_field_symbol(hardware_field, 1, symbol_name, sizeof(symbol_name))) {
        attach_amiga_platform_symbol(operand, symbol_name);
        attached = 1;
        continue;
      }
      hardware_register = amiga_os_find_hardware_register_by_cpu_address(value);
      if (hardware_register != NULL) {
        snprintf(symbol_name, sizeof(symbol_name), "%s+%s", hardware_register->base_symbol,
          hardware_register->symbol_name);
        attach_amiga_platform_symbol(operand, symbol_name);
        attached = 1;
        continue;
      }
      hardware_range = amiga_os_find_hardware_register_range_by_cpu_address(value);
      if (hardware_range != NULL &&
          format_amiga_hardware_register_range_symbol(hardware_range, value - hardware_range->base_address,
            1, symbol_name, sizeof(symbol_name))) {
        attach_amiga_platform_symbol(operand, symbol_name);
        attached = 1;
        continue;
      }
      if (base_symbol != NULL && base_symbol[0] != '\0') {
        attach_amiga_platform_symbol(operand, base_symbol);
        attached = 1;
      }
      continue;
    }
    if (operand_is_immediate_value_local(operand, &value)) {
      base_symbol = amiga_os_find_hardware_base_symbol_by_address(value);
      if (base_symbol == NULL || base_symbol[0] == '\0') continue;
      attach_amiga_platform_symbol(operand, base_symbol);
      attached = 1;
    }
  }
  return attached;
}

static const AmigaOsHardwareRegisterInfo *resolve_amiga_hardware_register_operand(const M68kRenderPlatformState *state,
    const M68kOperandIR *operand) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  uint32_t value = 0U;
  if (operand == NULL) return NULL;
  if (operand_is_address_displacement_local(operand, &base_reg, &displacement) &&
      state != NULL && base_reg < 8U && state->address_hardware_base_known[base_reg] &&
      displacement >= 0) {
    const char *base_symbol = state->address_hardware_base_symbol[base_reg];
    return amiga_os_find_hardware_register_by_base_offset(base_symbol, (uint32_t)(uint16_t)displacement);
  }
  if (operand_absolute_offset_local(operand, &value)) return amiga_os_find_hardware_register_by_cpu_address(value);
  return NULL;
}

static const AmigaOsHardwareRegisterFieldInfo *resolve_amiga_hardware_register_field_operand(
    const M68kRenderPlatformState *state, const M68kOperandIR *operand) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  uint32_t value = 0U;
  if (operand == NULL) return NULL;
  if (operand_is_address_displacement_local(operand, &base_reg, &displacement) &&
      state != NULL && base_reg < 8U && state->address_hardware_base_known[base_reg] &&
      displacement >= 0) {
    const char *base_symbol = state->address_hardware_base_symbol[base_reg];
    return amiga_os_find_hardware_register_field_by_base_offset(base_symbol, (uint32_t)(uint16_t)displacement);
  }
  if (operand_absolute_offset_local(operand, &value)) return amiga_os_find_hardware_register_field_by_cpu_address(value);
  return NULL;
}

static const AmigaOsHardwareRegisterRangeInfo *resolve_amiga_hardware_register_range_operand(
    const M68kRenderPlatformState *state, const M68kOperandIR *operand, uint32_t *out_offset) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  uint32_t value = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (operand == NULL) return NULL;
  if (operand_is_address_displacement_local(operand, &base_reg, &displacement) &&
      state != NULL && base_reg < 8U && state->address_hardware_base_known[base_reg] &&
      displacement >= 0) {
    const char *base_symbol = state->address_hardware_base_symbol[base_reg];
    if (out_offset != NULL) *out_offset = (uint32_t)(uint16_t)displacement;
    return amiga_os_find_hardware_register_range_by_base_offset(base_symbol, (uint32_t)(uint16_t)displacement);
  }
  if (operand_absolute_offset_local(operand, &value)) {
    const AmigaOsHardwareRegisterRangeInfo *range = amiga_os_find_hardware_register_range_by_cpu_address(value);
    if (range != NULL && out_offset != NULL) *out_offset = value - range->base_address;
    return range;
  }
  return NULL;
}

static uint32_t immediate_domain_value_for_instruction_size(const M68kInstructionIR *instruction, uint32_t value) {
  if (instruction == NULL) return value;
  if (instruction->size_suffix == 'b') return value & 0xFFU;
  if (instruction->size_suffix == 'w') return value & 0xFFFFU;
  return value;
}

static uint32_t byte_width_for_instruction_size(const M68kInstructionIR *instruction) {
  if (instruction == NULL) return 0U;
  if (instruction->size_suffix == 'b') return 1U;
  if (instruction->size_suffix == 'w') return 2U;
  if (instruction->size_suffix == 'l') return 4U;
  return 0U;
}

static int append_symbolic_expr_component(char *expr, size_t expr_size, const char *component) {
  size_t used;
  size_t component_len;
  if (expr == NULL || expr_size == 0U || component == NULL || component[0] == '\0') return 0;
  used = strlen(expr);
  component_len = strlen(component);
  if (used + (used != 0U ? 1U : 0U) + component_len + 1U > expr_size) return 0;
  if (used != 0U) strcat(expr, "|");
  strcat(expr, component);
  return 1;
}

static int amiga_bplcon0_symbolic_expr(uint32_t value, char *expr, size_t expr_size) {
  uint32_t word = value & 0xFFFFU;
  uint32_t remaining = word;
  uint32_t plane_count = (word >> 12) & 7U;
  char component[32];
  if (expr == NULL || expr_size == 0U) return 0;
  expr[0] = '\0';
  if ((word & 0x8000U) != 0U) {
    if (!append_symbolic_expr_component(expr, expr_size, "MODE_640")) return 0;
    remaining &= ~0x8000U;
  }
  if (plane_count != 0U) {
    snprintf(component, sizeof(component), "(%u<<PLNCNTSHFT)", (unsigned)plane_count);
    if (!append_symbolic_expr_component(expr, expr_size, component)) return 0;
    remaining &= ~0x7000U;
  }
  if ((word & 0x0800U) != 0U) {
    if (!append_symbolic_expr_component(expr, expr_size, "HOLDNMODIFY")) return 0;
    remaining &= ~0x0800U;
  }
  if ((word & 0x0400U) != 0U) {
    if (!append_symbolic_expr_component(expr, expr_size, "DBLPF")) return 0;
    remaining &= ~0x0400U;
  }
  if ((word & 0x0200U) != 0U) {
    if (!append_symbolic_expr_component(expr, expr_size, "COLORON")) return 0;
    remaining &= ~0x0200U;
  }
  if ((word & 0x0004U) != 0U) {
    if (!append_symbolic_expr_component(expr, expr_size, "INTERLACE")) return 0;
    remaining &= ~0x0004U;
  }
  if (remaining != 0U) return 0;
  return expr[0] != '\0';
}

static int amiga_bltsize_symbolic_expr(uint32_t value, char *expr, size_t expr_size) {
  uint32_t word = value & 0xFFFFU;
  uint32_t encoded_height = (word >> 6) & 0x3FFU;
  uint32_t encoded_width_words = word & 0x3FU;
  if (expr == NULL || expr_size == 0U || word == 0U) return 0;
  expr[0] = '\0';
  snprintf(expr, expr_size, "(%u<<6)|%u", (unsigned)encoded_height, (unsigned)encoded_width_words);
  return strlen(expr) + 1U < expr_size;
}

static int amiga_hardware_register_uses_custom_immediate_expr(const AmigaOsHardwareRegisterInfo *hardware_register,
    int use_bit_domain) {
  if (hardware_register == NULL || use_bit_domain) return 0;
  if (strcmp(hardware_register->base_symbol, "_custom") != 0) return 0;
  return strcmp(hardware_register->symbol_name, "bplcon0") == 0 ||
    strcmp(hardware_register->symbol_name, "bltsize") == 0;
}

int amiga_hardware_register_custom_immediate_expr(const AmigaOsHardwareRegisterInfo *hardware_register,
    uint32_t value, int use_bit_domain, char *expr, size_t expr_size) {
  if (amiga_hardware_register_uses_custom_immediate_expr(hardware_register, use_bit_domain)) {
    if (strcmp(hardware_register->symbol_name, "bplcon0") == 0) return amiga_bplcon0_symbolic_expr(value, expr, expr_size);
    if (strcmp(hardware_register->symbol_name, "bltsize") == 0) return amiga_bltsize_symbolic_expr(value, expr, expr_size);
  }
  return 0;
}

static int attach_amiga_hardware_register_immediate_symbols(const M68kRenderPlatformState *state,
    M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  const AmigaOsHardwareRegisterInfo *hardware_register = NULL;
  uint16_t domain_id = AMIGA_OS_VALUE_DOMAIN_ID_NONE;
  const char *domain_name = NULL;
  size_t operand_index;
  int use_bit_domain = 0;
  if (instruction == NULL || instruction->operand_count < 2U) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return 0;
  use_bit_domain =
    metadata->operation_type == M68K_SIM_OP_BIT_TEST ||
    metadata->operation_type == M68K_SIM_OP_BIT_SET ||
    metadata->operation_type == M68K_SIM_OP_BIT_CLEAR ||
    metadata->operation_type == M68K_SIM_OP_BIT_CHANGE;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    uint8_t access_kind = metadata->operand_access_kinds[operand_index];
    if (access_kind != M68K_SIM_ACCESS_MEMORY_WRITE &&
        access_kind != M68K_SIM_ACCESS_MEMORY_READ &&
        access_kind != M68K_SIM_ACCESS_COMPUTE_ADDRESS) {
      continue;
    }
    hardware_register = resolve_amiga_hardware_register_operand(state, &instruction->operands[operand_index]);
    if (hardware_register == NULL) continue;
    domain_id = use_bit_domain ? hardware_register->bit_domain_id : hardware_register->value_domain_id;
    if (domain_id != AMIGA_OS_VALUE_DOMAIN_ID_NONE ||
        amiga_hardware_register_uses_custom_immediate_expr(hardware_register, use_bit_domain)) {
      break;
    }
  }
  if (hardware_register == NULL) return 0;
  if (domain_id != AMIGA_OS_VALUE_DOMAIN_ID_NONE) {
    domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, domain_id);
    if (domain_name == NULL || domain_name[0] == '\0') return 0;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    uint32_t value = 0U;
    char symbol_expr[M68K_IR_SYMBOL_NAME_SIZE];
    if (operand->symbol_ref.has_name != 0U) continue;
    if (!operand_is_immediate_value_local(operand, &value)) continue;
    if (!use_bit_domain) value = immediate_domain_value_for_instruction_size(instruction, value);
    if (!amiga_hardware_register_custom_immediate_expr(hardware_register, value, use_bit_domain, symbol_expr,
          sizeof(symbol_expr)) &&
        (domain_name == NULL ||
         !amiga_value_domain_symbolic_expr(domain_name, value, symbol_expr, sizeof(symbol_expr)))) {
      continue;
    }
    attach_amiga_platform_symbol(operand, symbol_expr);
    return 1;
  }
  return 0;
}

static uint16_t render_amiga_struct_size_for_struct_id(uint16_t struct_id);

static int lookup_typed_app_slot_field_symbol_name(const M68kRenderLookup *lookup, int16_t displacement,
    char *base_symbol, size_t base_symbol_size, char *field_expr, size_t field_expr_size,
    int32_t *out_field_offset) {
  size_t index;
  int found = 0;
  char found_base_symbol[64];
  char found_field_expr[96];
  int32_t found_field_offset = 0;
  if (base_symbol != NULL && base_symbol_size > 0U) base_symbol[0] = '\0';
  if (field_expr != NULL && field_expr_size > 0U) field_expr[0] = '\0';
  if (out_field_offset != NULL) *out_field_offset = 0;
  if (lookup == NULL) return 0;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    if (slot->conflicted == 0U && strcmp(slot->owner_name, "__amiga_app_base__") == 0 &&
        slot->displacement == displacement && slot->value_kind != M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS) {
      return 0;
    }
  }
  for (index = 0U; index < lookup->typed_app_slot_count; ++index) {
    const M68kRenderTypedAppSlot *slot = &lookup->typed_app_slots[index];
    uint16_t struct_size;
    int32_t field_offset;
    char candidate_base_symbol[64];
    char candidate_field_expr[96];
    if (slot->conflicted != 0U || slot->inline_region == 0U ||
        slot->struct_id == AMIGA_OS_STRUCT_ID_NONE) {
      continue;
    }
    struct_size = render_amiga_struct_size_for_struct_id(slot->struct_id);
    field_offset = (int32_t)displacement - (int32_t)slot->displacement;
    if (struct_size == 0U || field_offset <= 0 || field_offset >= (int32_t)struct_size ||
        field_offset < INT16_MIN || field_offset > INT16_MAX) {
      continue;
    }
    if (!lookup_app_base_field_slot_symbol_name(lookup, slot->displacement, candidate_base_symbol,
        sizeof(candidate_base_symbol)) ||
        !amiga_os_resolve_struct_field_symbol_expr_by_struct_id(slot->struct_id, (int16_t)field_offset, 0,
          candidate_field_expr, sizeof(candidate_field_expr))) {
      continue;
    }
    if (found != 0) {
      if (strcmp(found_base_symbol, candidate_base_symbol) != 0 ||
          strcmp(found_field_expr, candidate_field_expr) != 0 ||
          found_field_offset != field_offset) {
        return 0;
      }
      continue;
    }
    snprintf(found_base_symbol, sizeof(found_base_symbol), "%s", candidate_base_symbol);
    snprintf(found_field_expr, sizeof(found_field_expr), "%s", candidate_field_expr);
    found_field_offset = field_offset;
    found = 1;
  }
  if (found == 0) return 0;
  if (base_symbol != NULL && base_symbol_size > 0U)
    snprintf(base_symbol, base_symbol_size, "%s", found_base_symbol);
  if (field_expr != NULL && field_expr_size > 0U)
    snprintf(field_expr, field_expr_size, "%s", found_field_expr);
  if (out_field_offset != NULL) *out_field_offset = found_field_offset;
  return 1;
}

static uint16_t render_amiga_struct_size_for_struct_id(uint16_t struct_id) {
  int32_t max_end = 0;
  size_t index;
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE || amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id) == NULL)
    return 0U;
  for (index = 0U; index < AMIGA_OS_STRUCT_FIELD_COUNT; ++index) {
    const AmigaOsStructFieldInfo *field = amiga_os_struct_field_at(index);
    int32_t end;
    if (field == NULL || field->struct_id != struct_id) continue;
    end = (int32_t)field->offset + (int32_t)field->size;
    if (field->size == 0U) end = field->offset;
    if (end > max_end) max_end = end;
  }
  if (max_end <= 0) return 0U;
  return max_end > UINT16_MAX ? UINT16_MAX : (uint16_t)max_end;
}

static int32_t lookup_typed_app_slot_region_size(const M68kRenderLookup *lookup, int16_t displacement) {
  size_t index;
  int32_t found_size = 0;
  if (lookup == NULL) return 0;
  for (index = 0U; index < lookup->typed_app_slot_count; ++index) {
    const M68kRenderTypedAppSlot *slot = &lookup->typed_app_slots[index];
    uint16_t struct_size;
    if (slot->conflicted != 0U || slot->inline_region == 0U || slot->displacement != displacement ||
        slot->struct_id == AMIGA_OS_STRUCT_ID_NONE) {
      continue;
    }
    struct_size = render_amiga_struct_size_for_struct_id(slot->struct_id);
    if (struct_size == 0U) continue;
    if (found_size != 0 && found_size != (int32_t)struct_size) return 0;
    found_size = (int32_t)struct_size;
  }
  return found_size;
}

static int attach_amiga_app_base_slot_symbols(const M68kRenderLookup *lookup,
    const M68kRenderPlatformState *state, M68kInstructionIR *instruction) {
  size_t operand_index;
  int attached = 0;
  if (lookup == NULL || state == NULL || instruction == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    uint8_t base_reg = 0U;
    int16_t displacement = 0;
    char symbol_name[64], field_expr[96];
    int32_t field_offset = 0;
    if (operand->symbol_ref.has_name != 0U) continue;
    if (!operand_is_address_displacement_local(operand, &base_reg, &displacement)) continue;
    if (state->address_hardware_base_known[base_reg]) continue;
    if (state->address_app_base_known[base_reg]) {
      if (!lookup_typed_app_slot_field_symbol_name(lookup, displacement, symbol_name, sizeof(symbol_name),
          field_expr, sizeof(field_expr), &field_offset) &&
          !lookup_app_base_field_slot_symbol_name(lookup, displacement, symbol_name, sizeof(symbol_name))) {
        continue;
      }
    } else if (state->address_base_known[base_reg]) {
      if (!library_base_can_use_app_extension_slot(state->address_base_library[base_reg], displacement) ||
          (!lookup_typed_app_slot_field_symbol_name(lookup, displacement, symbol_name, sizeof(symbol_name),
            field_expr, sizeof(field_expr), &field_offset) &&
          !lookup_app_base_field_slot_symbol_name(lookup, displacement, symbol_name, sizeof(symbol_name)))) {
        if (!lookup_base_field_slot_symbol_name(lookup, state->address_base_library[base_reg], displacement,
            symbol_name, sizeof(symbol_name))) {
          continue;
        }
      }
    } else if (state->address_layout_base_known[base_reg]) {
      if (!lookup_base_field_slot_symbol_name(lookup, state->address_layout_base_symbol[base_reg], displacement,
          symbol_name, sizeof(symbol_name))) {
        continue;
      }
    } else if (base_reg == 6U) {
      if (!lookup_typed_app_slot_field_symbol_name(lookup, displacement, symbol_name, sizeof(symbol_name),
          field_expr, sizeof(field_expr), &field_offset) &&
          !lookup_app_base_field_slot_symbol_name(lookup, displacement, symbol_name, sizeof(symbol_name))) {
        continue;
      }
    } else {
      continue;
    }
    m68k_ir_symbol_ref_init(&operand->symbol_ref);
    operand->symbol_ref.has_name = 1U;
    operand->symbol_ref.name_is_generated = 0U;
    operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
    snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol_name);
    if (field_offset != 0 && field_expr[0] != '\0') {
      operand->symbol_ref.has_symbolic_addend = 1U;
      operand->symbol_ref.symbolic_addend_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
      operand->symbol_ref.symbolic_addend_value = field_offset;
      snprintf(operand->symbol_ref.symbolic_addend_name, sizeof(operand->symbol_ref.symbolic_addend_name),
        "%s", field_expr);
    }
    attached = 1;
  }
  return attached;
}

static const M68kRenderTypedAccess *lookup_typed_access_for_operand(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset, uint8_t operand_index) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->typed_access_count; ++index) {
    const M68kRenderTypedAccess *access = &lookup->typed_accesses[index];
    if (access->section_index == section_index && access->offset == offset &&
        access->operand_index == operand_index) {
      return access;
    }
  }
  return NULL;
}

static int attach_amiga_typed_struct_field_symbols(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, M68kInstructionIR *instruction) {
  size_t operand_index;
  int attached = 0;
  if (lookup == NULL || instruction == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    const M68kRenderTypedAccess *access;
    if (operand->symbol_ref.has_name != 0U) continue;
    access = lookup_typed_access_for_operand(lookup, section_index, offset, (uint8_t)operand_index);
    if (access == NULL || access->field_expr[0] == '\0') continue;
    m68k_ir_symbol_ref_init(&operand->symbol_ref);
    operand->symbol_ref.has_name = 1U;
    operand->symbol_ref.name_is_generated = 0U;
    operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
    snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", access->field_expr);
    attached = 1;
  }
  return attached;
}

static int render_asm_include_for_instruction_platform_symbols(M68kRenderIRPreview *preview,
    const M68kInstructionIR *instruction) {
  size_t operand_index;
  if (instruction == NULL) return 1;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (operand->symbol_ref.has_name == 0U) continue;
    if (!render_asm_include_for_symbol_expr(preview, operand->symbol_ref.name)) return 0;
    if (operand->symbol_ref.has_symbolic_addend != 0U &&
        operand->symbol_ref.symbolic_addend_name[0] != '\0' &&
        !render_asm_include_for_symbol_expr(preview, operand->symbol_ref.symbolic_addend_name)) {
      return 0;
    }
  }
  return 1;
}

int operand_is_immediate_value_local(const M68kOperandIR *operand, uint32_t *out_value) {
  if (out_value != NULL) *out_value = 0U;
  if (operand == NULL || out_value == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_IMM) {
    *out_value = operand->value.value;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 7U && operand->value.ea_reg == 4U) {
    *out_value = operand->value.value;
    return 1;
  }
  return 0;
}

static int instruction_loads_d0_immediate(const M68kInstructionIR *instruction, int16_t *out_value) {
  int32_t value;
  uint32_t immediate = 0U;
  uint8_t dest_reg = 0U;
  if (out_value != NULL) *out_value = 0;
  if (instruction == NULL || out_value == NULL || instruction->operand_count != 2U) return 0;
  if (!operand_is_immediate_value_local(&instruction->operands[0], &immediate)) return 0;
  if (!operand_is_data_register_local(&instruction->operands[1], &dest_reg) || dest_reg != 0U) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ) {
    value = (int8_t)(immediate & 0xFFU);
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE) {
    value = (int32_t)immediate;
  } else {
    return 0;
  }
  if ((value < INT16_MIN || value > INT16_MAX) && instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE &&
      ((immediate & 0x8000U) != 0U)) {
    value = (int16_t)(immediate & 0xFFFFU);
  }
  if (value < INT16_MIN || value > INT16_MAX) return 0;
  *out_value = (int16_t)value;
  return 1;
}

static int instruction_writes_d0_unknown_for_state(const M68kInstructionIR *instruction) {
  const M68kOperandIR *dest;
  uint8_t reg = 0U;
  if (instruction == NULL) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_JSR ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_BSR) {
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    return instruction->operand_count >= 2U && reglist_contains_data_register_local(&instruction->operands[1], 0U);
  }
  if (instruction->operand_count == 0U) return 0;
  dest = &instruction->operands[instruction->operand_count - 1U];
  return operand_is_data_register_local(dest, &reg) && reg == 0U;
}

void platform_state_update_d0_lvo_after_instruction(M68kRenderPlatformState *state,
    const M68kInstructionIR *instruction) {
  int16_t lvo = 0;
  if (state == NULL || instruction == NULL) return;
  if (instruction_loads_d0_immediate(instruction, &lvo) && lvo < 0) {
    state->d0_lvo_known = 1U;
    state->d0_lvo = lvo;
    return;
  }
  if (instruction_writes_d0_unknown_for_state(instruction)) platform_state_clear_d0_lvo(state);
}

const AmigaOsLibraryVectorInfo *attach_amiga_lvo_immediate_if_known(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  uint32_t next_offset;
  uint32_t wrapper_offset = 0U;
  int16_t lvo = 0;
  const M68kDecodeCandidate *next_candidate;
  const char *library_name;
  const char *base_name;
  const AmigaOsLibraryVectorInfo *vector;
  const char *symbol_name;
  M68kOperandIR *operand;
  if (lookup == NULL || section == NULL || accepted_start == NULL || candidate == NULL || instruction == NULL)
    return NULL;
  if (!instruction_loads_d0_immediate(instruction, &lvo)) return NULL;
  if (lvo >= 0) return NULL;
  next_offset = candidate->offset + candidate->byte_count;
  if (!accepted_start_at(section, accepted_start, next_offset)) return NULL;
  next_candidate = find_candidate_at_offset_local(section, next_offset);
  if (!candidate_direct_same_section_target(next_candidate, section->section_index, &wrapper_offset)) return NULL;
  library_name = lookup_indexed_vector_wrapper_library(lookup, section->section_index, wrapper_offset);
  if (library_name == NULL) return NULL;
  base_name = amiga_os_find_library_base_name(library_name);
  if (base_name == NULL) return NULL;
  vector = amiga_os_find_library_vector(base_name, lvo);
  if (vector == NULL) return NULL;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, vector->lvo_symbol_id);
  if (symbol_name == NULL || symbol_name[0] == '\0') return NULL;
  operand = &instruction->operands[0];
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
  operand->symbol_ref.has_name = 1U;
  operand->symbol_ref.name_is_generated = 0U;
  operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
  operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
  snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol_name);
  return vector;
}

const AmigaOsLibraryVectorInfo *resolve_amiga_indexed_wrapper_call_vector(
    const M68kRenderLookup *lookup, const M68kRenderPlatformState *state, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate) {
  uint32_t wrapper_offset = 0U;
  const char *library_name;
  const char *base_name;
  if (lookup == NULL || state == NULL || section == NULL || candidate == NULL) return NULL;
  if (!state->d0_lvo_known) return NULL;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_BSR &&
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR) {
    return NULL;
  }
  size_t wrapper_section_index = 0U;
  if (!candidate_direct_control_target(lookup, section->section_index, candidate, &wrapper_section_index,
      &wrapper_offset)) {
    return NULL;
  }
  library_name = lookup_indexed_vector_wrapper_library(lookup, wrapper_section_index, wrapper_offset);
  if (library_name == NULL || library_name[0] == '\0') return NULL;
  base_name = amiga_os_find_library_base_name(library_name);
  if (base_name == NULL || base_name[0] == '\0') return NULL;
  return amiga_os_find_library_vector(base_name, state->d0_lvo);
}

static int rendered_text_reencodes_original_bytes(const char *text, const M68kInstructionIR *source_instruction,
    const M68kInstructionIR *render_instruction, const uint8_t *raw_bytes, size_t raw_size) {
  M68kInstructionIR parsed;
  M68kDiagList parse_diagnostics;
  M68kDiagList encode_diagnostics;
  M68kIrEncodeResult encoded;
  uint8_t encoded_bytes[32];
  uint8_t parse_cpu;
  if (text == NULL || source_instruction == NULL || raw_bytes == NULL || raw_size > sizeof(encoded_bytes)) return 0;
  if (instruction_has_symbolic_or_relative_text(source_instruction)) return 1;
  if (m68k_instruction_needs_fpu_id_directive(source_instruction)) {
    AsmSourceFile source;
    M68kObject object;
    char source_text[512];
    int ok = 0;
    memset(&source, 0, sizeof(source));
    memset(&object, 0, sizeof(object));
    snprintf(source_text, sizeof(source_text), "SECTION section_0,code\n\tFPU %u\n\t%s\n\tFPU 1\n",
      (unsigned)source_instruction->coprocessor_id, text);
    source.target_cpu = source_instruction->target_cpu;
    m68k_diag_list_reset(&parse_diagnostics);
    if (m68k_source_pipeline_parse_text_and_layout(&source, source_text, m68k_diag_sink(&parse_diagnostics)) &&
        !m68k_diag_has_errors(&parse_diagnostics)) {
      m68k_diag_list_reset(&encode_diagnostics);
      if (m68k_source_pipeline_emit_object(&source, &object, m68k_diag_sink(&encode_diagnostics)) &&
          !m68k_diag_has_errors(&encode_diagnostics) && object.section_count == 1U &&
          object.sections[0].data_size == raw_size && object.sections[0].data != NULL) {
        ok = memcmp(object.sections[0].data, raw_bytes, raw_size) == 0;
      }
    }
    m68k_object_destroy(&object);
    m68k_source_model_free(&source);
    return ok;
  }
  parse_cpu = render_instruction != NULL ? render_instruction->target_cpu : source_instruction->target_cpu;
  m68k_diag_list_reset(&parse_diagnostics);
  parsed = m68k_plain_parse_instruction_to_ir(text, parse_cpu, m68k_diag_sink(&parse_diagnostics));
  if (m68k_diag_has_errors(&parse_diagnostics)) return 0;
  m68k_diag_list_reset(&encode_diagnostics);
  encoded = m68k_ir_encode_one(&parsed, encoded_bytes, sizeof(encoded_bytes), m68k_diag_sink(&encode_diagnostics));
  if (m68k_diag_has_errors(&encode_diagnostics) || encoded.byte_count != raw_size) return 0;
  return memcmp(encoded_bytes, raw_bytes, raw_size) == 0;
}

uint32_t render_section_extent(const M68kDecodeSectionIR *section) {
  if (section == NULL) return 0U;
  return section->allocation_size > section->size ? section->allocation_size : section->size;
}

Arena *render_lookup_arena(M68kRenderLookup *lookup) {
  if (lookup == NULL) return NULL;
  if (lookup->arena == NULL) {
    lookup->arena = arena_create(16384U);
    if (lookup->arena == NULL) return NULL;
  }
  return lookup->arena;
}

void *render_lookup_calloc(M68kRenderLookup *lookup, size_t count, size_t size) {
  Arena *arena = render_lookup_arena(lookup);
  if (arena == NULL) return NULL;
  return arena_calloc(arena, count, size);
}

void *render_lookup_grow_array(M68kRenderLookup *lookup, const void *old_items, size_t old_count,
    size_t item_size, size_t new_capacity) {
  Arena *arena;
  size_t old_size;
  size_t new_size;
  if (item_size == 0U || new_capacity == 0U) return NULL;
  if (old_count > ((size_t)-1) / item_size || new_capacity > ((size_t)-1) / item_size) return NULL;
  arena = render_lookup_arena(lookup);
  if (arena == NULL) return NULL;
  old_size = old_count * item_size;
  new_size = new_capacity * item_size;
  return arena_realloc_copy(arena, old_items, old_size, new_size);
}

static void render_lookup_destroy(M68kRenderLookup *lookup) {
  if (lookup == NULL) return;
  arena_destroy(lookup->arena);
  memset(lookup, 0, sizeof(*lookup));
}

static const char *lookup_policy_label_name(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  uint16_t index;
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  if (policy == NULL) return NULL;
  for (index = 0U; index < policy->named_label_count && index < M68K_ANALYSIS_NAMED_LABEL_LIMIT; ++index) {
    const M68kAnalysisNamedLabel *label = &policy->named_labels[index];
    if (label->name[0] == '\0' || label->offset != offset) continue;
    if (label->has_section_index) {
      if (label->section_index != (uint32_t)section_index) continue;
    } else if (section_index != 0U) {
      continue;
    }
    return label->name;
  }
  return NULL;
}

static const char *lookup_object_symbol_label_name(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  size_t index;
  const M68kObject *object = lookup != NULL ? lookup->object : NULL;
  if (lookup != NULL && section_index < lookup->section_count && lookup->object_symbol_labels != NULL &&
      lookup->object_symbol_label_extents != NULL && offset <= lookup->object_symbol_label_extents[section_index] &&
      lookup->object_symbol_labels[section_index] != NULL) {
    return lookup->object_symbol_labels[section_index][offset];
  }
  if (object == NULL) return NULL;
  for (index = 0U; index < object->symbol_count; ++index) {
    const M68kSymbol *symbol = &object->symbols[index];
    if (!symbol->defined || symbol->section_index != section_index || symbol->value != offset) continue;
    if (!asm_symbol_name_is_safe_local(symbol->name)) continue;
    return symbol->name;
  }
  return NULL;
}

uint8_t format_lookup_asm_label_with_generation(const M68kRenderLookup *lookup, char *buf, size_t buf_size,
    size_t section_index, uint32_t offset) {
  const char *policy_name = lookup_policy_label_name(lookup, section_index, offset);
  const char *object_name = NULL;
  if (buf == NULL || buf_size == 0U) return 1U;
  if (policy_name != NULL && policy_name[0] != '\0') {
    snprintf(buf, buf_size, "%s", policy_name);
    return 0U;
  }
  object_name = lookup_object_symbol_label_name(lookup, section_index, offset);
  if (object_name != NULL && object_name[0] != '\0') {
    snprintf(buf, buf_size, "%s", object_name);
    return 0U;
  }
  if (lookup != NULL && lookup->object != NULL &&
      lookup->object->platform_backend_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    const char *library_name = lookup_global_base_slot_library(lookup, section_index, offset);
    const char *base_name = amiga_os_find_library_base_name(library_name);
    if (base_name == NULL) base_name = library_name;
    if (base_name != NULL &&
        platform_amiga_format_global_base_slot_label(section_index, 'l', base_name, buf, buf_size)) {
      return 0U;
    }
  }
  format_asm_label(buf, buf_size, section_index, offset);
  return 1U;
}

static int structured_item_matches_section(const M68kAnalysisStructuredDataItem *item, size_t section_index) {
  if (item == NULL) return 0;
  if (item->has_section_index) return item->section_index == (uint32_t)section_index;
  return section_index == 0U;
}

const M68kAnalysisStructuredDataItem *lookup_structured_data_item_at_offset(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  uint16_t index;
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  if (policy != NULL) {
    for (index = 0U; index < policy->structured_data_item_count &&
         index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
      const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
      if (item->offset == offset && item->size != 0U && structured_item_matches_section(item, section_index))
        return item;
    }
  }
  if (lookup != NULL) {
    size_t auto_index;
    for (auto_index = 0U; auto_index < lookup->auto_structured_data_item_count; ++auto_index) {
      const M68kAnalysisStructuredDataItem *item = &lookup->auto_structured_data_items[auto_index];
      if (item->offset == offset && item->size != 0U && structured_item_matches_section(item, section_index))
        return item;
    }
  }
  return NULL;
}

const M68kAnalysisStructuredDataItem *lookup_structured_data_item_covering_offset(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  uint16_t index;
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  if (policy != NULL) {
    for (index = 0U; index < policy->structured_data_item_count &&
         index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
      const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
      uint32_t end;
      if (item->size == 0U || !structured_item_matches_section(item, section_index)) continue;
      if (UINT32_MAX - item->offset < item->size) continue;
      end = item->offset + item->size;
      if (offset >= item->offset && offset < end) return item;
    }
  }
  if (lookup != NULL) {
    size_t auto_index;
    for (auto_index = 0U; auto_index < lookup->auto_structured_data_item_count; ++auto_index) {
      const M68kAnalysisStructuredDataItem *item = &lookup->auto_structured_data_items[auto_index];
      uint32_t end;
      if (item->size == 0U || !structured_item_matches_section(item, section_index)) continue;
      if (UINT32_MAX - item->offset < item->size) continue;
      end = item->offset + item->size;
      if (offset >= item->offset && offset < end) return item;
    }
  }
  return NULL;
}

static int lookup_has_structured_data_item_at_offset(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  return lookup_structured_data_item_at_offset(lookup, section_index, offset) != NULL;
}

int structured_data_item_comment(const M68kAnalysisStructuredDataItem *item, char *comment,
    size_t comment_size) {
  const char *field_name;
  const char *type_name;
  if (comment == NULL || comment_size == 0U) return 0;
  comment[0] = '\0';
  if (item == NULL) return 0;
  field_name = item->field_name[0] != '\0' ? item->field_name : item->label;
  if (item->struct_name[0] != '\0' && field_name != NULL && field_name[0] != '\0') {
    type_name = item->field_type[0] != '\0' ? item->field_type : item->c_type;
    if (type_name != NULL && type_name[0] != '\0') {
      snprintf(comment, comment_size, "%s %s", type_name, field_name);
    } else {
      snprintf(comment, comment_size, "FIELD: %s.%s", item->struct_name, field_name);
    }
    return 1;
  }
  if (item->comment[0] != '\0') {
    snprintf(comment, comment_size, "%s", item->comment);
    return 1;
  }
  if (item->semantic_role[0] != '\0') {
    snprintf(comment, comment_size, "%s", item->semantic_role);
    return 1;
  }
  return 0;
}

static int structured_data_item_constant_matches_bytes(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item) {
  uint32_t value = 0U;
  uint32_t mask = 0xFFFFFFFFU;
  if (section == NULL || section->data == NULL || item == NULL || item->has_constant_value == 0U ||
      item->constant_name[0] == '\0' || item->offset >= section->size) {
    return 0;
  }
  if (item->size == 1U && item->offset + 1U <= section->size) {
    value = section->data[item->offset];
    mask = 0xFFU;
  } else if (item->size == 2U && item->offset + 2U <= section->size) {
    value = m68k_read_u16be(section->data + item->offset);
    mask = 0xFFFFU;
  } else if (item->size == 4U && item->offset + 4U <= section->size) {
    value = m68k_read_u32be(section->data + item->offset);
  } else {
    return 0;
  }
  return value == ((uint32_t)item->constant_value & mask);
}

static int structured_data_item_raw_value(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, uint32_t *out_value) {
  if (out_value != NULL) *out_value = 0U;
  if (section == NULL || section->data == NULL || item == NULL || item->offset >= section->size) return 0;
  if (item->size == 1U && item->offset + 1U <= section->size) {
    if (out_value != NULL) *out_value = section->data[item->offset];
    return 1;
  }
  if (item->size == 2U && item->offset + 2U <= section->size) {
    if (out_value != NULL) *out_value = m68k_read_u16be(section->data + item->offset);
    return 1;
  }
  if (item->size == 4U && item->offset + 4U <= section->size) {
    if (out_value != NULL) *out_value = m68k_read_u32be(section->data + item->offset);
    return 1;
  }
  return 0;
}

static int structured_data_item_value_domain_expr(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, char *expr, size_t expr_size) {
  uint32_t value;
  if (expr == NULL || expr_size == 0U || item == NULL) return 0;
  expr[0] = '\0';
  if (item->value_domain[0] == '\0' || !structured_data_item_raw_value(section, item, &value)) return 0;
  return amiga_value_domain_symbolic_expr(item->value_domain, value, expr, expr_size);
}

int amiga_value_domain_symbolic_expr(const char *domain_name, uint32_t value, char *expr,
    size_t expr_size) {
  const AmigaOsValueDomainInfo *domain;
  const AmigaOsValueDomainMemberInfo *members;
  size_t member_count = 0U;
  uint32_t remaining;
  size_t index;
  int wrote = 0;
  if (expr == NULL || expr_size == 0U || domain_name == NULL || domain_name[0] == '\0') return 0;
  expr[0] = '\0';
  domain = amiga_os_find_value_domain(domain_name);
  if (domain == NULL) return 0;
  members = amiga_os_value_domain_members(domain, &member_count);
  if (members == NULL) return 0;
  for (index = 0U; index < member_count; ++index) {
    const char *name;
    if (!members[index].value_known || (uint32_t)members[index].value != value) continue;
    name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, members[index].name_id);
    if (name == NULL || name[0] == '\0') continue;
    snprintf(expr, expr_size, "%s", name);
    return 1;
  }
  if (value == 0U && domain->zero_name_id != AMIGA_OS_SYMBOL_ID_NONE) {
    const char *name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, domain->zero_name_id);
    if (name == NULL || name[0] == '\0') return 0;
    snprintf(expr, expr_size, "%s", name);
    return 1;
  }
  if (domain->kind != AMIGA_OS_VALUE_DOMAIN_KIND_FLAGS ||
      (domain->composition != AMIGA_OS_VALUE_DOMAIN_COMPOSITION_OR &&
       domain->composition != AMIGA_OS_VALUE_DOMAIN_COMPOSITION_BIT_OR)) {
    return 0;
  }
  remaining = value;
  while (remaining != 0U) {
    uint32_t best_value = 0U;
    const char *best_name = NULL;
    for (index = 0U; index < member_count; ++index) {
      uint32_t member_value;
      const char *name;
      if (!members[index].value_known || members[index].value <= 0) continue;
      member_value = (uint32_t)members[index].value;
      if ((remaining & member_value) != member_value) continue;
      name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, members[index].name_id);
      if (name == NULL || name[0] == '\0') continue;
      if (best_name == NULL || member_value > best_value) {
        best_value = member_value;
        best_name = name;
      }
    }
    if (best_name == NULL) return 0;
    if (wrote) {
      size_t used = strlen(expr);
      if (used + 2U > expr_size) return 0;
      expr[used] = '|';
      expr[used + 1U] = '\0';
    }
    if (strlen(expr) + strlen(best_name) + 1U > expr_size) return 0;
    strcat(expr, best_name);
    remaining &= ~best_value;
    wrote = 1;
  }
  return wrote;
}

int structured_data_item_symbolic_operand_expr(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, char *expr, size_t expr_size) {
  if (expr == NULL || expr_size == 0U || item == NULL) return 0;
  expr[0] = '\0';
  if (!((item->size == 1U && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_BYTES) ||
        (item->size == 2U && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS) ||
        (item->size == 4U && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS))) {
    return 0;
  }
  if (item->size == 4U && strcmp(item->struct_name, "resident_autoinit") == 0 &&
      strcmp(item->field_name, "resident_base_size") == 0) {
    snprintf(expr, expr_size, "app_SIZEOF");
    return 1;
  }
  if (structured_data_item_constant_matches_bytes(section, item)) {
    if (!asm_symbol_name_is_safe_local(item->constant_name)) return 0;
    snprintf(expr, expr_size, "%s", item->constant_name);
    return 1;
  }
  if (!structured_data_item_value_domain_expr(section, item, expr, expr_size)) return 0;
  return render_asm_include_for_symbol_expr(NULL, expr);
}

int structured_data_item_render_comment(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, char *comment, size_t comment_size) {
  char expr[96];
  size_t used;
  if (!structured_data_item_comment(item, comment, comment_size)) return 0;
  if (structured_data_item_constant_matches_bytes(section, item)) {
    snprintf(expr, sizeof(expr), "%s", item->constant_name);
  } else if (!structured_data_item_value_domain_expr(section, item, expr, sizeof(expr))) {
    return 1;
  }
  used = strlen(comment);
  if (used + strlen(expr) + 4U >= comment_size) return 1;
  snprintf(comment + used, comment_size - used, " = %s", expr);
  return 1;
}

static int render_lookup_build(M68kRenderLookup *lookup, const M68kObject *object, const M68kDecodeIR *decode,
    const M68kFactIR *facts, const M68kAnalysisPolicy *policy) {
  size_t section_index;
  size_t fact_index;
  if (lookup == NULL || decode == NULL || facts == NULL) return -1;
  memset(lookup, 0, sizeof(*lookup));
  lookup->section_count = decode->section_count;
  lookup->object = object;
  lookup->policy = policy;
  lookup->labels = (uint8_t **)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->labels));
  lookup->object_symbol_labels =
    (const char ***)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->object_symbol_labels));
  lookup->relocations = (const M68kFact ***)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->relocations));
  lookup->anchors = (const M68kFact ***)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->anchors));
  lookup->block_starts = (uint8_t **)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->block_starts));
  lookup->label_extents = (uint32_t *)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->label_extents));
  lookup->object_symbol_label_extents =
    (uint32_t *)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->object_symbol_label_extents));
  lookup->relocation_extents = (uint32_t *)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->relocation_extents));
  lookup->anchor_extents = (uint32_t *)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->anchor_extents));
  lookup->block_start_extents = (uint32_t *)render_lookup_calloc(lookup, decode->section_count,
    sizeof(*lookup->block_start_extents));
  lookup->instruction_comment_indices =
    (size_t **)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->instruction_comment_indices));
  lookup->instruction_comment_extents =
    (uint32_t *)render_lookup_calloc(lookup, decode->section_count, sizeof(*lookup->instruction_comment_extents));
  lookup->runtime_address_ref_indices =
    (M68kRenderRuntimeAddressRefIndex **)render_lookup_calloc(lookup, decode->section_count,
      sizeof(*lookup->runtime_address_ref_indices));
  lookup->runtime_address_ref_index_extents =
    (uint32_t *)render_lookup_calloc(lookup, decode->section_count,
      sizeof(*lookup->runtime_address_ref_index_extents));
  if (lookup->labels == NULL || lookup->object_symbol_labels == NULL || lookup->relocations == NULL ||
      lookup->anchors == NULL || lookup->block_starts == NULL || lookup->label_extents == NULL ||
      lookup->object_symbol_label_extents == NULL || lookup->relocation_extents == NULL ||
      lookup->anchor_extents == NULL || lookup->block_start_extents == NULL ||
      lookup->instruction_comment_indices == NULL || lookup->instruction_comment_extents == NULL ||
      lookup->runtime_address_ref_indices == NULL || lookup->runtime_address_ref_index_extents == NULL)
    goto oom;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    uint32_t label_extent = render_section_extent(&decode->sections[section_index]);
    uint32_t block_start_extent = label_extent;
    uint32_t relocation_extent = decode->sections[section_index].size;
    uint32_t anchor_extent = relocation_extent, comment_extent = relocation_extent;
    uint32_t runtime_ref_extent = relocation_extent;
    lookup->label_extents[section_index] = label_extent;
    lookup->object_symbol_label_extents[section_index] = label_extent;
    lookup->relocation_extents[section_index] = relocation_extent;
    lookup->anchor_extents[section_index] = anchor_extent;
    lookup->block_start_extents[section_index] = block_start_extent;
    lookup->instruction_comment_extents[section_index] = comment_extent;
    lookup->runtime_address_ref_index_extents[section_index] = runtime_ref_extent;
    lookup->labels[section_index] =
      (uint8_t *)render_lookup_calloc(lookup, (size_t)label_extent + 1U, sizeof(*lookup->labels[section_index]));
    lookup->object_symbol_labels[section_index] =
      (const char **)render_lookup_calloc(lookup, (size_t)label_extent + 1U,
        sizeof(*lookup->object_symbol_labels[section_index]));
    if (relocation_extent != 0U) {
      lookup->relocations[section_index] =
        (const M68kFact **)render_lookup_calloc(lookup, relocation_extent,
          sizeof(*lookup->relocations[section_index]));
    }
    if (anchor_extent != 0U) {
      lookup->anchors[section_index] =
        (const M68kFact **)render_lookup_calloc(lookup, anchor_extent, sizeof(*lookup->anchors[section_index]));
    }
    if (block_start_extent != 0U) {
      lookup->block_starts[section_index] =
        (uint8_t *)render_lookup_calloc(lookup, block_start_extent, sizeof(*lookup->block_starts[section_index]));
    }
    if (comment_extent != 0U) {
      lookup->instruction_comment_indices[section_index] =
        (size_t *)render_lookup_calloc(lookup, comment_extent,
          sizeof(*lookup->instruction_comment_indices[section_index]));
    }
    if (runtime_ref_extent != 0U) {
      lookup->runtime_address_ref_indices[section_index] =
        (M68kRenderRuntimeAddressRefIndex *)render_lookup_calloc(lookup, runtime_ref_extent,
          sizeof(*lookup->runtime_address_ref_indices[section_index]));
    }
    if (lookup->labels[section_index] == NULL || lookup->object_symbol_labels[section_index] == NULL ||
        (relocation_extent != 0U && lookup->relocations[section_index] == NULL) ||
        (anchor_extent != 0U && lookup->anchors[section_index] == NULL) ||
        (block_start_extent != 0U && lookup->block_starts[section_index] == NULL) ||
        (comment_extent != 0U && lookup->instruction_comment_indices[section_index] == NULL) ||
        (runtime_ref_extent != 0U && lookup->runtime_address_ref_indices[section_index] == NULL))
      goto oom;
  }
  if (object != NULL) {
    size_t symbol_index;
    for (symbol_index = 0U; symbol_index < object->symbol_count; ++symbol_index) {
      const M68kSymbol *symbol = &object->symbols[symbol_index];
      if (!symbol->defined || symbol->section_index >= decode->section_count ||
          symbol->value > lookup->object_symbol_label_extents[symbol->section_index] ||
          !asm_symbol_name_is_safe_local(symbol->name)) {
        continue;
      }
      if (lookup->object_symbol_labels[symbol->section_index][symbol->value] == NULL) {
        lookup->object_symbol_labels[symbol->section_index][symbol->value] = symbol->name;
      }
    }
  }
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *fact = &facts->facts[fact_index];
    if (fact->section_index >= decode->section_count) continue;
    if (fact->kind == M68K_FACT_LABEL_CREATED && fact->offset <= lookup->label_extents[fact->section_index]) {
      lookup->labels[fact->section_index][fact->offset] = 1U;
    } else if (fact->kind == M68K_FACT_CODE_START &&
        fact->reason != M68K_FACT_CODE_START_REASON_FALLTHROUGH &&
        fact->offset < lookup->block_start_extents[fact->section_index]) {
      lookup->block_starts[fact->section_index][fact->offset] = 1U;
      if (render_lookup_add_code_start_ref(lookup, fact) != 0) goto oom;
    } else if (fact->kind == M68K_FACT_RELOCATION_REF &&
        fact->offset < lookup->relocation_extents[fact->section_index] && fact->size != 0U) {
      lookup->relocations[fact->section_index][fact->offset] = fact;
    } else if (fact->kind == M68K_FACT_RELOCATION_ANCHOR &&
        fact->offset < lookup->anchor_extents[fact->section_index] && fact->size != 0U) {
      lookup->anchors[fact->section_index][fact->offset] = fact;
    } else if (fact->kind == M68K_FACT_RUNTIME_ADDRESS_REF) {
      if (render_lookup_add_runtime_address_ref(lookup, fact) != 0) goto oom;
    } else if (fact->kind == M68K_FACT_RUNTIME_ADDRESS_RANGE) {
      if (render_lookup_add_runtime_address_range(lookup, fact) != 0) goto oom;
    } else if (fact->kind == M68K_FACT_CODE_ACCEPTED) {
      if (render_lookup_add_code_start_ref(lookup, fact) != 0) goto oom;
    } else if (fact->kind == M68K_FACT_VIOLATION) {
      if (render_lookup_add_violation_ref(lookup, fact) != 0) goto oom;
      const M68kAnalysisStructuredDataItem *item =
        lookup_structured_data_item_covering_offset(lookup, fact->section_index, fact->offset);
      uint32_t comment_offset = fact->offset;
      char comment[192];
      comment[0] = '\0';
      if (item != NULL) {
        if (fact->offset == item->offset) {
          comment_offset = item->offset;
          snprintf(comment, sizeof(comment),
            "invalid overlap: decoded code at $%04X starts at structured data; emitted as data",
            (unsigned)fact->offset);
        }
      } else if (fact->target_section_index < decode->section_count) {
        item = lookup_structured_data_item_covering_offset(lookup, fact->target_section_index,
          fact->target_offset);
        if (item != NULL && fact->target_section_index == fact->section_index) {
          comment_offset = item->offset;
          snprintf(comment, sizeof(comment),
            "invalid overlap: decoded code at $%04X crosses structured data at $%04X; emitted as data",
            (unsigned)fact->offset, (unsigned)fact->target_offset);
        }
      }
      if (comment[0] != '\0' &&
          render_lookup_add_instruction_comment(lookup, fact->section_index, comment_offset, comment) != 0) {
        goto oom;
      }
    }
  }
  if (render_lookup_add_pc_relative_xrefs(lookup, decode) != 0) goto oom;
  return 0;
oom:
  render_lookup_destroy(lookup);
  return -1;
}

int lookup_has_label(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->labels == NULL ||
      lookup->label_extents == NULL || offset > lookup->label_extents[section_index] ||
      lookup->labels[section_index] == NULL) {
    return 0;
  }
  return lookup->labels[section_index][offset] != 0U;
}

const M68kFact *lookup_relocation_at(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->relocations == NULL ||
      lookup->relocation_extents == NULL || offset >= lookup->relocation_extents[section_index] ||
      lookup->relocations[section_index] == NULL) {
    return NULL;
  }
  return lookup->relocations[section_index][offset];
}

static const M68kFact *lookup_anchor_at(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->anchors == NULL ||
      lookup->anchor_extents == NULL || offset >= lookup->anchor_extents[section_index] ||
      lookup->anchors[section_index] == NULL) {
    return NULL;
  }
  return lookup->anchors[section_index][offset];
}

static int runtime_range_contains_source(const M68kFact *range, size_t section_index, uint32_t source_offset,
    uint32_t *out_runtime_address) {
  uint32_t delta;
  if (out_runtime_address != NULL) *out_runtime_address = 0U;
  if (range == NULL || range->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE || !range->has_runtime_address ||
      range->section_index != section_index || source_offset < range->offset) {
    return 0;
  }
  delta = source_offset - range->offset;
  if (delta >= range->size || range->runtime_address > UINT32_MAX - delta) return 0;
  if (out_runtime_address != NULL) *out_runtime_address = range->runtime_address + delta;
  return 1;
}

static int runtime_range_contains_runtime_ref_target(const M68kFact *range, const M68kFact *ref) {
  uint32_t expected_runtime = 0U;
  if (range == NULL || ref == NULL || ref->kind != M68K_FACT_RUNTIME_ADDRESS_REF ||
      !ref->has_runtime_address || ref->target_section_index != range->section_index) {
    return 0;
  }
  if (!runtime_range_contains_source(range, ref->target_section_index, ref->target_offset, &expected_runtime))
    return 0;
  return expected_runtime == ref->runtime_address;
}

static int runtime_range_contains_policy_entry_point(const M68kRenderLookup *lookup, const M68kFact *range) {
  uint16_t index;
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  if (policy == NULL || range == NULL || range->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_POLICY) return 0;
  for (index = 0U; index < policy->runtime_entry_point_count &&
       index < M68K_ANALYSIS_RUNTIME_ENTRY_POINT_LIMIT; ++index) {
    const M68kAnalysisRuntimeEntryPoint *entry = &policy->runtime_entry_points[index];
    uint32_t delta;
    if ((entry->has_section_index ? entry->section_index : 0U) != (uint32_t)range->section_index) continue;
    if (entry->runtime_address < range->runtime_address) continue;
    delta = entry->runtime_address - range->runtime_address;
    if (delta < range->size) return 1;
  }
  return 0;
}

static int runtime_range_is_crossed_by_storage_xref(const M68kRenderLookup *lookup, const M68kFact *range) {
  size_t index;
  uint32_t range_end;
  if (lookup == NULL || range == NULL || range->size == 0U || range->offset > UINT32_MAX - range->size)
    return 1;
  range_end = range->offset + range->size;
  for (index = 0U; index < lookup->xref_count; ++index) {
    const M68kRenderXref *xref = &lookup->xrefs[index];
    uint32_t lo, hi;
    if (xref->section_index != range->section_index || xref->target_section_index != range->section_index ||
        xref->offset == xref->target_offset) {
      continue;
    }
    if (xref->offset < xref->target_offset) {
      lo = xref->offset;
      hi = xref->target_offset;
    } else {
      lo = xref->target_offset;
      hi = xref->offset;
    }
    if (lo >= range->offset && hi < range_end) continue;
    if (lo < range_end && range->offset < hi) return 1;
  }
  return 0;
}

static int runtime_range_is_exited_to_larger_runtime_range(const M68kRenderLookup *lookup,
    const M68kFact *range) {
  size_t ref_index;
  uint32_t range_end;
  if (lookup == NULL || range == NULL || range->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
      range->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY ||
      range->confidence >= M68K_FACT_CONFIDENCE_REQUIRED || range->size == 0U ||
      range->offset > UINT32_MAX - range->size) {
    return 0;
  }
  range_end = range->offset + range->size;
  for (ref_index = 0U; ref_index < lookup->runtime_address_ref_count; ++ref_index) {
    const M68kFact *ref = lookup->runtime_address_refs[ref_index].fact;
    size_t other_index;
    if (ref == NULL || ref->section_index != range->section_index ||
        ref->target_section_index != range->section_index || ref->offset < range->offset ||
        ref->offset >= range_end) {
      continue;
    }
    if (ref->target_offset >= range->offset && ref->target_offset < range_end) continue;
    for (other_index = 0U; other_index < lookup->runtime_address_range_count; ++other_index) {
      const M68kFact *other = lookup->runtime_address_ranges[other_index].fact;
      uint32_t other_runtime = 0U;
      if (other == NULL || other == range || other->section_index != range->section_index ||
          other->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE || other->size <= range->size) {
        continue;
      }
      if (runtime_range_contains_source(other, ref->target_section_index, ref->target_offset,
          &other_runtime) && other_runtime == ref->runtime_address) {
        return 1;
      }
    }
  }
  return 0;
}

static int runtime_range_is_materialized(const M68kRenderLookup *lookup, const M68kFact *range) {
  size_t index;
  if (lookup == NULL || range == NULL) return 0;
  if (range->runtime_kind == M68K_FACT_RUNTIME_RANGE_KIND_CONFLICTING_DISCOVERED_COPY) return 0;
  if (runtime_range_is_crossed_by_storage_xref(lookup, range)) return 0;
  if (runtime_range_is_exited_to_larger_runtime_range(lookup, range)) return 0;
  if (runtime_range_contains_policy_entry_point(lookup, range)) return 1;
  for (index = 0U; index < lookup->runtime_address_ref_count; ++index) {
    if (runtime_range_contains_runtime_ref_target(range, lookup->runtime_address_refs[index].fact)) return 1;
  }
  return 0;
}

int lookup_source_runtime_address(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset, uint32_t *out_runtime_address) {
  size_t index;
  if (out_runtime_address != NULL) *out_runtime_address = 0U;
  if (lookup == NULL || lookup->runtime_address_ranges == NULL) return 0;
  for (index = lookup->runtime_address_ref_count; index > 0U; --index) {
    const M68kFact *ref = lookup->runtime_address_refs[index - 1U].fact;
    size_t range_index;
    if (ref == NULL || ref->target_section_index != section_index || ref->target_offset != source_offset ||
        !ref->has_runtime_address) {
      continue;
    }
    for (range_index = lookup->runtime_address_range_count; range_index > 0U; --range_index) {
      const M68kFact *range = lookup->runtime_address_ranges[range_index - 1U].fact;
      uint32_t mapped_runtime_address = 0U;
      if (!runtime_range_is_materialized(lookup, range)) continue;
      if (!runtime_range_contains_source(range, section_index, source_offset, &mapped_runtime_address)) continue;
      if (mapped_runtime_address == ref->runtime_address) {
        if (out_runtime_address != NULL) *out_runtime_address = ref->runtime_address;
        return 1;
      }
    }
  }
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_ranges[index].fact;
    if (!runtime_range_is_materialized(lookup, fact)) continue;
    if (runtime_range_contains_source(fact, section_index, source_offset, out_runtime_address)) return 1;
  }
  return 0;
}

int lookup_source_has_materialized_runtime_address(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset, uint32_t runtime_address) {
  size_t index;
  if (lookup == NULL || lookup->runtime_address_ranges == NULL) return 0;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_ranges[index].fact;
    uint32_t mapped_runtime_address = 0U;
    if (!runtime_range_is_materialized(lookup, fact)) continue;
    if (!runtime_range_contains_source(fact, section_index, source_offset, &mapped_runtime_address)) continue;
    if (mapped_runtime_address == runtime_address) return 1;
  }
  return 0;
}

int lookup_source_should_render_runtime_label(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset, uint32_t *out_runtime_address) {
  return lookup_source_runtime_address(lookup, section_index, source_offset, out_runtime_address);
}

static int lookup_source_offsets_share_runtime_view(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset, uint32_t target_offset) {
  size_t index;
  int source_has_runtime_view = 0;
  int target_has_runtime_view = 0;
  if (lookup == NULL || lookup->runtime_address_ranges == NULL || lookup->runtime_address_range_count == 0U) return 1;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_ranges[index].fact;
    uint32_t source_delta, target_delta;
    if (!runtime_range_is_materialized(lookup, fact) ||
        fact->section_index != section_index || source_offset < fact->offset || target_offset < fact->offset) {
      continue;
    }
    source_delta = source_offset - fact->offset;
    target_delta = target_offset - fact->offset;
    if (source_delta < fact->size) source_has_runtime_view = 1;
    if (target_delta < fact->size) target_has_runtime_view = 1;
    if (source_delta < fact->size && target_delta < fact->size) return 1;
  }
  return source_has_runtime_view == 0 && target_has_runtime_view == 0;
}

int lookup_source_offset_is_materialized_runtime_range_start(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset) {
  size_t index;
  if (lookup == NULL || lookup->runtime_address_ranges == NULL) return 0;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_ranges[index].fact;
    if (runtime_range_is_materialized(lookup, fact) && fact->section_index == section_index &&
        fact->offset == source_offset) {
      return 1;
    }
  }
  return 0;
}

static int lookup_source_offset_is_block_start(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->block_starts == NULL ||
      lookup->block_start_extents == NULL || lookup->block_starts[section_index] == NULL ||
      source_offset >= lookup->block_start_extents[section_index]) {
    return 0;
  }
  return lookup->block_starts[section_index][source_offset] != 0U;
}

static int runtime_address_ref_targets_unmaterialized_discovered_code(const M68kRenderLookup *lookup,
    const M68kFact *ref) {
  size_t index;
  if (lookup == NULL || ref == NULL || ref->kind != M68K_FACT_RUNTIME_ADDRESS_REF ||
      !ref->has_runtime_address || ref->target_section_index >= lookup->section_count) {
    return 0;
  }
  if (!lookup_source_offset_is_block_start(lookup, ref->target_section_index, ref->target_offset)) return 0;
  if (lookup_source_has_materialized_runtime_address(lookup, ref->target_section_index, ref->target_offset,
      ref->runtime_address)) {
    return 0;
  }
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *range = lookup->runtime_address_ranges[index].fact;
    uint32_t mapped_runtime_address = 0U;
    if (range == NULL || range->runtime_kind != M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY) continue;
    if (!runtime_range_contains_source(range, ref->target_section_index, ref->target_offset,
        &mapped_runtime_address)) {
      continue;
    }
    if (mapped_runtime_address == ref->runtime_address) return 1;
  }
  return 0;
}

int lookup_source_logical_address(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_offset, uint32_t *out_logical_address) {
  uint32_t runtime_address = 0U;
  if (out_logical_address == NULL) return 0;
  if (lookup_source_should_render_runtime_label(lookup, section_index, source_offset, &runtime_address)) {
    *out_logical_address = runtime_address;
    return 1;
  }
  *out_logical_address = source_offset;
  return 1;
}

static const M68kFact *lookup_runtime_address_ref_for_operand(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset, size_t operand_index) {
  size_t index;
  if (lookup == NULL || operand_index > UINT32_MAX) return NULL;
  if (operand_index < M68K_DECODE_IR_MAX_OPERANDS && section_index < lookup->section_count &&
      lookup->runtime_address_ref_indices != NULL && lookup->runtime_address_ref_index_extents != NULL &&
      offset < lookup->runtime_address_ref_index_extents[section_index] &&
      lookup->runtime_address_ref_indices[section_index] != NULL) {
    return lookup->runtime_address_ref_indices[section_index][offset].operand_refs[operand_index];
  }
  for (index = lookup->runtime_address_ref_count; index > 0U; --index) {
    const M68kFact *fact = lookup->runtime_address_refs[index - 1U].fact;
    if (fact == NULL) continue;
    if (fact->section_index == section_index && fact->offset == offset &&
        fact->reason == (uint32_t)operand_index && fact->has_runtime_address) {
      return fact;
    }
  }
  return NULL;
}

static const M68kFact *lookup_external_runtime_address_ref_for_instruction(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset) {
  size_t index;
  if (lookup == NULL) return NULL;
  if (section_index < lookup->section_count && lookup->runtime_address_ref_indices != NULL &&
      lookup->runtime_address_ref_index_extents != NULL &&
      offset < lookup->runtime_address_ref_index_extents[section_index] &&
      lookup->runtime_address_ref_indices[section_index] != NULL) {
    return lookup->runtime_address_ref_indices[section_index][offset].external_ref;
  }
  for (index = lookup->runtime_address_ref_count; index > 0U; --index) {
    const M68kFact *fact = lookup->runtime_address_refs[index - 1U].fact;
    if (fact == NULL) continue;
    if (fact->section_index == section_index && fact->offset == offset && fact->has_runtime_address &&
        fact->target_section_index >= lookup->section_count) {
      return fact;
    }
  }
  return NULL;
}

static const AmigaOsHardwareRegisterInfo *external_runtime_address_ref_sink_register(const M68kFact *fact) {
  const AmigaOsHardwareRegisterInfo *hardware_register;
  const AmigaOsHardwareRegisterRangeInfo *hardware_range;
  if (fact == NULL || fact->target_section_index != (size_t)-1 || fact->target_offset == 0U) return NULL;
  hardware_register = amiga_os_find_hardware_register_by_cpu_address(fact->target_offset);
  if (hardware_register == NULL) {
    hardware_range = amiga_os_find_hardware_register_range_by_cpu_address(fact->target_offset);
    if (hardware_range != NULL)
      hardware_register = amiga_os_find_hardware_register_by_base_offset("_custom", hardware_range->offset);
  }
  if (hardware_register == NULL)
    hardware_register = amiga_os_find_hardware_register_by_base_offset("_custom", fact->target_offset);
  if (hardware_register == NULL) {
    hardware_range = amiga_os_find_hardware_register_range_by_base_offset("_custom", fact->target_offset);
    if (hardware_range != NULL)
      hardware_register = amiga_os_find_hardware_register_by_base_offset("_custom", hardware_range->offset);
  }
  if (hardware_register == NULL ||
      (hardware_register->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) == 0U ||
      hardware_register->runtime_target_role == NULL || hardware_register->runtime_target_role[0] == '\0') {
    return NULL;
  }
  return hardware_register;
}

static const char *external_runtime_address_ref_role(const M68kRenderLookup *lookup, const M68kFact *fact) {
  const AmigaOsHardwareRegisterInfo *hardware_register = external_runtime_address_ref_sink_register(fact);
  const M68kSection *section;
  const char *role;
  if (hardware_register != NULL) return hardware_register->runtime_target_role;
  if (lookup == NULL || fact == NULL || lookup->object == NULL ||
      fact->source_section_index >= lookup->object->section_count) {
    return NULL;
  }
  section = &lookup->object->sections[fact->source_section_index];
  role = platform_facts_v2_runtime_address_storage_sink_data_class(lookup->object->platform_backend_kind,
    section->data, section->data_size, fact->source_offset);
  return role != NULL && role[0] != '\0' ? role : NULL;
}

static int runtime_alias_label_seen_before(const M68kRenderLookup *lookup, size_t current_index,
    size_t section_index, uint32_t offset, uint32_t runtime_address) {
  size_t index;
  if (lookup == NULL) return 0;
  for (index = 0U; index < current_index; ++index) {
    const M68kFact *fact = lookup->runtime_address_refs[index].fact;
    if (fact != NULL && fact->target_section_index == section_index && fact->target_offset == offset &&
        fact->has_runtime_address && fact->runtime_address == runtime_address) {
      return 1;
    }
  }
  return 0;
}

int render_asm_runtime_alias_labels(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset, uint8_t has_primary_runtime, uint32_t primary_runtime_address) {
  size_t index;
  int emitted = 0;
  if (preview == NULL || lookup == NULL) return 0;
  for (index = 0U; index < lookup->runtime_address_ref_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_refs[index].fact;
    char name[64];
    char line[160];
    if (fact == NULL || fact->target_section_index != section_index || fact->target_offset != offset ||
        !fact->has_runtime_address) {
      continue;
    }
    if (has_primary_runtime && fact->runtime_address == primary_runtime_address) continue;
    if (!lookup_source_has_materialized_runtime_address(lookup, section_index, offset, fact->runtime_address))
      continue;
    if (runtime_alias_label_seen_before(lookup, index, section_index, offset, fact->runtime_address)) continue;
    render_asm_org(preview, fact->runtime_address);
    format_runtime_asm_label(lookup, name, sizeof(name), section_index, offset, fact->runtime_address);
    snprintf(line, sizeof(line), "%s:\n", name);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
    emitted = 1;
  }
  return emitted;
}

static uint32_t lookup_code_block_start_before_or_at(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  const uint8_t *block_starts;
  uint32_t cursor;
  if (lookup == NULL || section_index >= lookup->section_count || lookup->block_starts == NULL ||
      lookup->block_start_extents == NULL || lookup->block_starts[section_index] == NULL ||
      lookup->block_start_extents[section_index] == 0U) {
    return 0U;
  }
  block_starts = lookup->block_starts[section_index];
  cursor = offset;
  if (cursor >= lookup->block_start_extents[section_index]) {
    cursor = lookup->block_start_extents[section_index] - 1U;
  }
  for (;;) {
    if (block_starts[cursor] != 0U) return cursor;
    if (cursor == 0U) break;
    --cursor;
  }
  return 0U;
}

int lookup_offset_is_inside_relocation_payload(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  uint32_t back;
  if (lookup == NULL || offset == 0U) return 0;
  for (back = 1U; back <= 4U && back <= offset; ++back) {
    uint32_t start = offset - back;
    const M68kFact *relocation = lookup_relocation_at(lookup, section_index, start);
    const M68kFact *anchor = lookup_anchor_at(lookup, section_index, start);
    if (relocation != NULL && relocation->size > back) return 1;
    if (anchor != NULL && anchor->size > back) return 1;
  }
  return 0;
}

int lookup_has_renderable_label(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  const M68kAnalysisStructuredDataItem *covering_item;
  if (!lookup_has_label(lookup, section_index, offset)) return 0;
  covering_item = lookup_structured_data_item_covering_offset(lookup, section_index, offset);
  if (covering_item != NULL && covering_item->offset != offset &&
      lookup_structured_data_item_at_offset(lookup, section_index, offset) == NULL &&
      lookup_relocation_at(lookup, section_index, offset) == NULL &&
      lookup_anchor_at(lookup, section_index, offset) == NULL &&
      lookup_string_span_at_offset(lookup, section_index, offset) == NULL) {
    if ((structured_data_item_is_copper_list(covering_item) || structured_data_item_is_palette(covering_item)) &&
        offset > covering_item->offset && offset - covering_item->offset < covering_item->size &&
        ((offset - covering_item->offset) % 2U) == 0U) {
      return !lookup_offset_is_inside_relocation_payload(lookup, section_index, offset);
    }
    return 0;
  }
  return !lookup_offset_is_inside_relocation_payload(lookup, section_index, offset);
}

const char *lookup_global_base_slot_library(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->global_base_slot_count; ++index) {
    const M68kRenderGlobalBaseSlot *slot = &lookup->global_base_slots[index];
    if (slot->section_index == section_index && slot->offset == offset && slot->library_name[0] != '\0')
      return slot->library_name;
  }
  return NULL;
}

static int base_field_owner_matches(const char *slot_owner, const char *owner_name) {
  if (slot_owner == NULL || owner_name == NULL || slot_owner[0] == '\0' || owner_name[0] == '\0') return 0;
  if (strcmp(slot_owner, owner_name) == 0) return 1;
  return strcmp(slot_owner, "__amiga_app_base__") == 0 && amiga_os_find_library_base_name(owner_name) != NULL;
}

static int app_base_slot_symbol_name_from_library(const char *library_name, char *symbol_name,
    size_t symbol_name_size) {
  const char *base_name;
  if (symbol_name != NULL && symbol_name_size != 0U) symbol_name[0] = '\0';
  if (library_name == NULL || library_name[0] == '\0') return 0;
  base_name = amiga_os_find_library_base_name(library_name);
  if (base_name == NULL && amiga_os_find_library_name_by_base_name(library_name) != NULL) base_name = library_name;
  if (base_name == NULL) return 0;
  return platform_amiga_format_app_base_slot_name(base_name, symbol_name, symbol_name_size);
}

static int format_app_base_fallback_slot_symbol_name(int16_t displacement, char *symbol_name,
    size_t symbol_name_size) {
  int written;
  if (symbol_name == NULL || symbol_name_size == 0U) return 0;
  written = snprintf(symbol_name, symbol_name_size, "app_%04X", (unsigned)(uint16_t)displacement);
  return written > 0 && (size_t)written < symbol_name_size;
}

static int app_base_slot_symbol_name_from_slot(const M68kRenderBaseFieldSlot *slot, char *symbol_name,
    size_t symbol_name_size) {
  if (symbol_name != NULL && symbol_name_size != 0U) symbol_name[0] = '\0';
  if (slot == NULL || slot->conflicted != 0U) return 0;
  if (amiga_unknown_base_owner_name_is_internal(slot->owner_name)) return 0;
  if (slot->symbol_name[0] != '\0') {
    if (symbol_name == NULL || symbol_name_size == 0U) return 0;
    snprintf(symbol_name, symbol_name_size, "%s", slot->symbol_name);
    return strlen(slot->symbol_name) < symbol_name_size;
  }
  if (slot->library_name[0] == '\0') {
    if (strcmp(slot->owner_name, "__amiga_app_base__") == 0) {
      return format_app_base_fallback_slot_symbol_name(slot->displacement, symbol_name, symbol_name_size);
    }
    return 0;
  }
  if (slot->value_kind != M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE &&
      slot->value_kind != M68K_RENDER_BASE_FIELD_SLOT_DEVICE_BASE)
    return 0;
  return app_base_slot_symbol_name_from_library(slot->library_name, symbol_name, symbol_name_size);
}

int base_field_slot_is_base_pointer(const M68kRenderBaseFieldSlot *slot) {
  return slot != NULL && (slot->value_kind == M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE ||
    slot->value_kind == M68K_RENDER_BASE_FIELD_SLOT_DEVICE_BASE);
}

static uint16_t library_base_struct_id_for_library(const char *library_name) {
  uint16_t library_id;
  uint16_t struct_id;
  if (library_name == NULL || library_name[0] == '\0') return AMIGA_OS_STRUCT_ID_NONE;
  library_id = amiga_os_name_id(M68K_PLATFORM_NAME_LIBRARY, library_name);
  if (library_id == 0U) return AMIGA_OS_STRUCT_ID_NONE;
  struct_id = amiga_os_find_library_base_struct_id(library_id);
  return struct_id != AMIGA_OS_STRUCT_ID_NONE ? struct_id : AMIGA_OS_STRUCT_ID_LIB;
}

static uint16_t base_field_slot_struct_id(const M68kRenderBaseFieldSlot *slot) {
  if (slot == NULL || slot->conflicted != 0U || slot->library_name[0] == '\0') return AMIGA_OS_STRUCT_ID_NONE;
  if (slot->value_kind == M68K_RENDER_BASE_FIELD_SLOT_DEVICE_BASE) return AMIGA_OS_STRUCT_ID_DD;
  if (slot->value_kind == M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE)
    return library_base_struct_id_for_library(slot->library_name);
  return AMIGA_OS_STRUCT_ID_NONE;
}

static const char *library_base_struct_name_for_field_lookup(const char *owner_name) {
  const char *library_name;
  const char *struct_name;
  if (owner_name == NULL || owner_name[0] == '\0') return NULL;
  library_name = amiga_os_find_library_base_name(owner_name) != NULL
    ? owner_name
    : amiga_os_find_library_name_by_base_name(owner_name);
  if (library_name == NULL || library_name[0] == '\0') return NULL;
  struct_name = amiga_os_find_library_base_struct_name(library_name);
  if (struct_name != NULL && struct_name[0] != '\0') return struct_name;
  return amiga_os_name(M68K_PLATFORM_NAME_STRUCT, AMIGA_OS_STRUCT_ID_LIB);
}

static int kb_library_base_field_symbol_name(const char *owner_name, int16_t displacement, char *symbol_name,
    size_t symbol_name_size) {
  const char *common_struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, AMIGA_OS_STRUCT_ID_LIB);
  const char *struct_name;
  const AmigaOsStructFieldInfo *field = NULL;
  const char *field_name;
  if (symbol_name != NULL && symbol_name_size != 0U) symbol_name[0] = '\0';
  if (symbol_name == NULL || symbol_name_size == 0U) return 0;
  struct_name = library_base_struct_name_for_field_lookup(owner_name);
  if (struct_name == NULL || struct_name[0] == '\0') return 0;
  field = amiga_os_find_struct_field(struct_name, displacement);
  if (field == NULL && common_struct_name != NULL && strcmp(struct_name, common_struct_name) != 0) {
    field = amiga_os_find_struct_field_by_struct_id(AMIGA_OS_STRUCT_ID_LIB, displacement);
  }
  if (field == NULL) return 0;
  field_name = amiga_os_name(M68K_PLATFORM_NAME_FIELD, field->field_id);
  if (field_name == NULL || field_name[0] == '\0') return 0;
  snprintf(symbol_name, symbol_name_size, "%s", field_name);
  return strlen(field_name) < symbol_name_size;
}

static int library_base_has_specific_struct_name(const char *owner_name) {
  const char *library_name;
  const char *struct_name;
  const char *common_struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, AMIGA_OS_STRUCT_ID_LIB);
  if (owner_name == NULL || owner_name[0] == '\0') return 0;
  library_name = amiga_os_find_library_base_name(owner_name) != NULL
    ? owner_name
    : amiga_os_find_library_name_by_base_name(owner_name);
  if (library_name == NULL || library_name[0] == '\0') return 0;
  struct_name = amiga_os_find_library_base_struct_name(library_name);
  return struct_name != NULL && struct_name[0] != '\0' &&
    (common_struct_name == NULL || strcmp(struct_name, common_struct_name) != 0);
}

int library_base_can_use_app_extension_slot(const char *owner_name, int16_t displacement) {
  int32_t lib_size = 0;
  char kb_symbol[64];
  if (owner_name == NULL || owner_name[0] == '\0') return 0;
  if (!amiga_os_find_constant_value("LIB_SIZE", &lib_size) || displacement < lib_size) return 0;
  if (library_base_has_specific_struct_name(owner_name) &&
      kb_library_base_field_symbol_name(owner_name, displacement, kb_symbol, sizeof(kb_symbol))) {
    return 0;
  }
  return 1;
}

static int lookup_app_base_field_slot_symbol_has_other_displacement(const M68kRenderLookup *lookup,
    const char *symbol_name, int16_t displacement) {
  size_t index;
  if (lookup == NULL || symbol_name == NULL || symbol_name[0] == '\0') return 0;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    char other_symbol_name[64];
    if (slot->conflicted != 0U || strcmp(slot->owner_name, "__amiga_app_base__") != 0) continue;
    if (!app_base_slot_symbol_name_from_slot(slot, other_symbol_name, sizeof(other_symbol_name))) continue;
    if (strcmp(symbol_name, other_symbol_name) == 0 && slot->displacement != displacement) return 1;
  }
  return 0;
}

const char *lookup_base_field_slot_library(const M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement) {
  const char *matched_library = NULL;
  size_t index;
  if (lookup == NULL || owner_name == NULL || owner_name[0] == '\0') return NULL;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    char symbol_name[64];
    if (slot->displacement != displacement || slot->conflicted || slot->library_name[0] == '\0' ||
        !base_field_slot_is_base_pointer(slot)) {
      continue;
    }
    if (!base_field_owner_matches(slot->owner_name, owner_name)) continue;
    if (strcmp(slot->owner_name, "__amiga_app_base__") == 0 &&
        (!app_base_slot_symbol_name_from_slot(slot, symbol_name, sizeof(symbol_name)) ||
          lookup_app_base_field_slot_symbol_has_other_displacement(lookup, symbol_name, displacement))) {
      continue;
    }
    if (matched_library != NULL && strcmp(matched_library, slot->library_name) != 0) return NULL;
    matched_library = slot->library_name;
  }
  return matched_library;
}

const char *lookup_app_base_field_slot_library(const M68kRenderLookup *lookup, int16_t displacement) {
  const char *matched_library = NULL;
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    char symbol_name[64];
    if (slot->displacement != displacement || slot->conflicted || slot->library_name[0] == '\0' ||
        !base_field_slot_is_base_pointer(slot)) {
      continue;
    }
    if (strcmp(slot->owner_name, "__amiga_app_base__") != 0) continue;
    if (!app_base_slot_symbol_name_from_slot(slot, symbol_name, sizeof(symbol_name)) ||
        lookup_app_base_field_slot_symbol_has_other_displacement(lookup, symbol_name, displacement)) {
      continue;
    }
    if (matched_library != NULL && strcmp(matched_library, slot->library_name) != 0) return NULL;
    matched_library = slot->library_name;
  }
  return matched_library;
}

uint16_t lookup_base_field_slot_struct_id(const M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement) {
  uint16_t matched_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  size_t index;
  if (lookup == NULL || owner_name == NULL || owner_name[0] == '\0') return AMIGA_OS_STRUCT_ID_NONE;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    uint16_t struct_id;
    char symbol_name[64];
    if (slot->displacement != displacement || slot->conflicted || !base_field_slot_is_base_pointer(slot))
      continue;
    if (!base_field_owner_matches(slot->owner_name, owner_name)) continue;
    if (strcmp(slot->owner_name, "__amiga_app_base__") == 0 &&
        (!app_base_slot_symbol_name_from_slot(slot, symbol_name, sizeof(symbol_name)) ||
          lookup_app_base_field_slot_symbol_has_other_displacement(lookup, symbol_name, displacement))) {
      continue;
    }
    struct_id = base_field_slot_struct_id(slot);
    if (struct_id == AMIGA_OS_STRUCT_ID_NONE) continue;
    if (matched_struct_id != AMIGA_OS_STRUCT_ID_NONE && matched_struct_id != struct_id) return AMIGA_OS_STRUCT_ID_NONE;
    matched_struct_id = struct_id;
  }
  return matched_struct_id;
}

uint16_t lookup_app_base_field_slot_struct_id(const M68kRenderLookup *lookup, int16_t displacement) {
  uint16_t matched_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  size_t index;
  if (lookup == NULL) return AMIGA_OS_STRUCT_ID_NONE;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    uint16_t struct_id;
    char symbol_name[64];
    if (slot->displacement != displacement || slot->conflicted || !base_field_slot_is_base_pointer(slot))
      continue;
    if (strcmp(slot->owner_name, "__amiga_app_base__") != 0) continue;
    if (!app_base_slot_symbol_name_from_slot(slot, symbol_name, sizeof(symbol_name)) ||
        lookup_app_base_field_slot_symbol_has_other_displacement(lookup, symbol_name, displacement)) {
      continue;
    }
    struct_id = base_field_slot_struct_id(slot);
    if (struct_id == AMIGA_OS_STRUCT_ID_NONE) continue;
    if (matched_struct_id != AMIGA_OS_STRUCT_ID_NONE && matched_struct_id != struct_id) return AMIGA_OS_STRUCT_ID_NONE;
    matched_struct_id = struct_id;
  }
  return matched_struct_id;
}

int lookup_base_field_slot_symbol_name(const M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement, char *symbol_name, size_t symbol_name_size) {
  int matched = 0;
  int blocked = 0;
  char matched_symbol[64];
  size_t index;
  if (symbol_name != NULL && symbol_name_size != 0U) symbol_name[0] = '\0';
  if (lookup == NULL || owner_name == NULL || owner_name[0] == '\0' ||
      symbol_name == NULL || symbol_name_size == 0U) {
    return 0;
  }
  if (amiga_unknown_base_owner_name_is_internal(owner_name)) return 0;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    char slot_symbol[64];
    if (slot->displacement != displacement) continue;
    if (strcmp(slot->owner_name, owner_name) != 0) continue;
    if (slot->conflicted != 0U) {
      blocked = 1;
      continue;
    }
    if (slot->library_name[0] == '\0' && slot->symbol_name[0] == '\0' &&
        strcmp(slot->owner_name, "__amiga_app_base__") != 0) {
      continue;
    }
    if (strcmp(slot->owner_name, "__amiga_app_base__") == 0 &&
        (!app_base_slot_symbol_name_from_slot(slot, slot_symbol, sizeof(slot_symbol)) ||
          lookup_app_base_field_slot_symbol_has_other_displacement(lookup, slot_symbol, displacement))) {
      continue;
    }
    if (!app_base_slot_symbol_name_from_slot(slot, slot_symbol, sizeof(slot_symbol))) continue;
    if (matched && strcmp(matched_symbol, slot_symbol) != 0) return 0;
    snprintf(matched_symbol, sizeof(matched_symbol), "%s", slot_symbol);
    matched = 1;
  }
  if (blocked) return 0;
  if (!matched) return kb_library_base_field_symbol_name(owner_name, displacement, symbol_name, symbol_name_size);
  snprintf(symbol_name, symbol_name_size, "%s", matched_symbol);
  return strlen(matched_symbol) < symbol_name_size;
}

int lookup_app_base_field_slot_symbol_name(const M68kRenderLookup *lookup, int16_t displacement,
    char *symbol_name, size_t symbol_name_size) {
  return lookup_base_field_slot_symbol_name(lookup, "__amiga_app_base__", displacement, symbol_name,
    symbol_name_size);
}

typedef struct M68kRenderAppRsSlot {
  int32_t displacement;
  int32_t size;
  uint8_t alias;
  char layout_name[32];
  char sizeof_symbol[64];
  char name[64];
} M68kRenderAppRsSlot;

static int render_app_rs_slot_compare(const void *left, const void *right) {
  const M68kRenderAppRsSlot *left_slot = (const M68kRenderAppRsSlot *)left;
  const M68kRenderAppRsSlot *right_slot = (const M68kRenderAppRsSlot *)right;
  int layout_cmp = strcmp(left_slot->layout_name, right_slot->layout_name);
  if (layout_cmp != 0) return layout_cmp;
  if (left_slot->displacement < right_slot->displacement) return -1;
  if (left_slot->displacement > right_slot->displacement) return 1;
  return strcmp(left_slot->name, right_slot->name);
}

int lookup_has_amiga_resident_library_context(const M68kRenderLookup *lookup) {
  const M68kAnalysisPolicy *policy;
  uint16_t index;
  if (lookup == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  policy = lookup->policy;
  if (policy == NULL) return 0;
  for (index = 0U; index < policy->named_label_count && index < M68K_ANALYSIS_NAMED_LABEL_LIMIT; ++index) {
    const char *name = policy->named_labels[index].name;
    if (strcmp(name, "resident") == 0 || strcmp(name, "resident_autoinit") == 0 ||
        strcmp(name, "resident_vectors") == 0) {
      return 1;
    }
  }
  for (index = 0U; index < policy->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    if (strcmp(item->struct_name, "resident") == 0 || strcmp(item->struct_name, "resident_autoinit") == 0 ||
        strcmp(item->struct_name, "resident_vectors") == 0) {
      return 1;
    }
    if (strcmp(item->label, "resident") == 0 || strcmp(item->label, "resident_autoinit") == 0 ||
        strcmp(item->label, "resident_vectors") == 0) {
      return 1;
    }
  }
  return 0;
}

static int render_app_rs_slot_exists(const M68kRenderAppRsSlot *slots, size_t slot_count, const char *name,
    const char *layout_name, int32_t displacement, int *out_conflict) {
  size_t index;
  if (out_conflict != NULL) *out_conflict = 0;
  for (index = 0U; index < slot_count; ++index) {
    if (strcmp(slots[index].layout_name, layout_name) != 0) continue;
    if (strcmp(slots[index].name, name) != 0) continue;
    if (slots[index].displacement != displacement && out_conflict != NULL) *out_conflict = 1;
    return 1;
  }
  return 0;
}

static void render_app_rs_default_sizeof_symbol(const char *layout_name, char *symbol_name, size_t symbol_name_size) {
  if (symbol_name == NULL || symbol_name_size == 0U) return;
  if (layout_name == NULL || layout_name[0] == '\0' || strcmp(layout_name, "app") == 0) {
    snprintf(symbol_name, symbol_name_size, "app_SIZEOF");
  } else {
    snprintf(symbol_name, symbol_name_size, "%s_SIZEOF", layout_name);
  }
}

static void render_app_rs_effective_sizeof_symbol(const char *layout_name, const char *metadata_symbol,
    char *symbol_name, size_t symbol_name_size) {
  if (symbol_name == NULL || symbol_name_size == 0U) return;
  if (metadata_symbol != NULL && metadata_symbol[0] != '\0') {
    snprintf(symbol_name, symbol_name_size, "%s", metadata_symbol);
  } else {
    render_app_rs_default_sizeof_symbol(layout_name, symbol_name, symbol_name_size);
  }
}

static int render_app_rs_resident_sizeof_value(const M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    int32_t *out_value) {
  const M68kAnalysisPolicy *policy;
  uint16_t index;
  if (out_value != NULL) *out_value = 0;
  if (lookup == NULL || decode == NULL || lookup->policy == NULL) return 0;
  policy = lookup->policy;
  for (index = 0U; index < policy->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    const M68kDecodeSectionIR *section;
    size_t section_index;
    if (item->size != 4U || strcmp(item->struct_name, "resident_autoinit") != 0 ||
        strcmp(item->field_name, "resident_base_size") != 0) {
      continue;
    }
    section_index = item->has_section_index ? (size_t)item->section_index : 0U;
    if (section_index >= decode->section_count) continue;
    section = &decode->sections[section_index];
    if (section->data == NULL || item->offset > section->size || section->size - item->offset < 4U) continue;
    if (out_value != NULL) *out_value = (int32_t)m68k_read_u32be(section->data + item->offset);
    return 1;
  }
  return 0;
}

void render_asm_app_extension_rs(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode) {
  Arena *scratch_arena;
  ArenaMark scratch_mark;
  M68kRenderAppRsSlot *slots = NULL;
  size_t slot_count = 0U;
  size_t slot_capacity = 0U;
  size_t index;
  int32_t lib_size = 0, base_offset = 0, cursor;
  int32_t inferred_sizeof = 0, app_sizeof_value = 0;
  int has_app_sizeof_value;
  int has_resident_context;
  char line[160];
  if (preview == NULL || lookup == NULL) return;
  slot_capacity = lookup->base_field_slot_count +
    (lookup->policy != NULL ? lookup->policy->rsset_layout_region_count : 0U);
  if (slot_capacity == 0U) slot_capacity = 1U;
  scratch_arena = render_preview_scratch_arena(preview);
  if (scratch_arena == NULL) {
    preview->asm_source_allocation_failed = 1U;
    return;
  }
  scratch_mark = arena_mark(scratch_arena);
  slots = (M68kRenderAppRsSlot *)arena_calloc(scratch_arena, slot_capacity, sizeof(*slots));
  if (slots == NULL) {
    preview->asm_source_allocation_failed = 1U;
    goto cleanup;
  }
  has_resident_context = lookup_has_amiga_resident_library_context(lookup);
  has_app_sizeof_value = render_app_rs_resident_sizeof_value(lookup, decode, &app_sizeof_value);
  if (has_resident_context) {
    if (!amiga_os_find_constant_value("LIB_SIZE", &lib_size) || lib_size <= 0) {
      goto cleanup;
    }
    base_offset = lib_size;
  }
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    char symbol_name[64];
    char region_symbol_name[64], field_expr[96];
    int conflict = 0;
    int32_t extent_end;
    int32_t region_size;
    if (slot->conflicted != 0U || strcmp(slot->owner_name, "__amiga_app_base__") != 0) continue;
    if ((int32_t)slot->displacement < base_offset) continue;
    if (lookup_typed_app_slot_field_symbol_name(lookup, slot->displacement, region_symbol_name,
        sizeof(region_symbol_name), field_expr, sizeof(field_expr), NULL)) {
      continue;
    }
    if (!app_base_slot_symbol_name_from_slot(slot, symbol_name, sizeof(symbol_name)) ||
        lookup_app_base_field_slot_symbol_has_other_displacement(lookup, symbol_name, slot->displacement)) {
      continue;
    }
    if (render_app_rs_slot_exists(slots, slot_count, symbol_name, "app", slot->displacement, &conflict)) {
      if (conflict) {
        ++preview->asm_source_instruction_render_failures;
        record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER,
          slot->source_section_index, slot->source_offset, (uint32_t)(uint16_t)slot->displacement);
      }
      continue;
    }
    if (slot_count >= slot_capacity) {
      ++preview->asm_source_instruction_render_failures;
      record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER,
        slot->source_section_index, slot->source_offset, (uint32_t)(uint16_t)slot->displacement);
      continue;
    }
    slots[slot_count].displacement = slot->displacement;
    region_size = lookup_typed_app_slot_region_size(lookup, slot->displacement);
    slots[slot_count].size = region_size > 0
      ? region_size
      : (slot->observed_access_size != 0U ? slot->observed_access_size : ((slot->displacement & 1) == 0 ? 4 : 1));
    snprintf(slots[slot_count].layout_name, sizeof(slots[slot_count].layout_name), "app");
    render_app_rs_default_sizeof_symbol("app", slots[slot_count].sizeof_symbol,
      sizeof(slots[slot_count].sizeof_symbol));
    snprintf(slots[slot_count].name, sizeof(slots[slot_count].name), "%s", symbol_name);
    ++slot_count;
    extent_end = (int32_t)slot->displacement + slots[slot_count - 1U].size;
    if (extent_end > inferred_sizeof) inferred_sizeof = extent_end;
  }
  if (lookup->policy != NULL) {
    const M68kAnalysisPolicy *policy = lookup->policy;
    for (index = 0U; index < policy->rsset_layout_region_count && index < M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT; ++index) {
      const M68kAnalysisRssetLayoutRegion *region = &policy->rsset_layout_regions[index];
      const char *layout_name = region->layout_name[0] != '\0' ? region->layout_name : "app";
      const char *base_symbol = region->base_symbol[0] != '\0' ? region->base_symbol : "__amiga_app_base__";
      int conflict = 0;
      if (strcmp(layout_name, "app") == 0 && strcmp(base_symbol, "__amiga_app_base__") == 0) continue;
      if (region->symbol[0] == '\0' || region->offset > 0x7FFFU || region->size == 0U) continue;
      if (render_app_rs_slot_exists(slots, slot_count, region->symbol, layout_name, (int32_t)region->offset,
          &conflict)) {
        if (conflict) ++preview->asm_source_instruction_render_failures;
        continue;
      }
      if (slot_count >= slot_capacity) {
        ++preview->asm_source_instruction_render_failures;
        continue;
      }
      snprintf(slots[slot_count].layout_name, sizeof(slots[slot_count].layout_name), "%s", layout_name);
      render_app_rs_effective_sizeof_symbol(layout_name, region->sizeof_symbol, slots[slot_count].sizeof_symbol,
        sizeof(slots[slot_count].sizeof_symbol));
      snprintf(slots[slot_count].name, sizeof(slots[slot_count].name), "%s", region->symbol);
      slots[slot_count].displacement = (int32_t)region->offset;
      slots[slot_count].size = region->size;
      ++slot_count;
    }
  }
  if (slot_count == 0U && has_app_sizeof_value == 0) {
    goto cleanup;
  }
  if (slot_count == 0U) {
    if (has_resident_context) {
      if (!render_asm_include_for_amiga_symbol(preview, "LIB_SIZE")) {
        ++preview->asm_source_instruction_render_failures;
        record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, 0U, 0U);
        goto cleanup;
      }
      hash_asm_text(preview, "    RSSET LIB_SIZE\n");
      cursor = base_offset;
    } else {
      hash_asm_text(preview, "    RSSET 0\n");
      cursor = 0;
    }
    ++preview->asm_source_lines;
    if (app_sizeof_value > cursor) {
      snprintf(line, sizeof(line), "    RS.B %d\n", (int)(app_sizeof_value - cursor));
      hash_asm_text(preview, line);
      ++preview->asm_source_lines;
    }
    hash_asm_text(preview, "app_SIZEOF EQU __RS\n\n");
    preview->asm_source_lines += 2U;
    goto cleanup;
  }
  qsort(slots, slot_count, sizeof(slots[0]), render_app_rs_slot_compare);
  for (index = 0U; index < slot_count; ++index) {
    size_t layout_end = index + 1U;
    const char *layout_name = slots[index].layout_name;
    const char *sizeof_symbol = slots[index].sizeof_symbol;
    int32_t layout_base_offset = strcmp(layout_name, "app") == 0 ? base_offset : 0;
    int32_t layout_sizeof = 0;
    while (layout_end < slot_count && strcmp(slots[layout_end].layout_name, layout_name) == 0) ++layout_end;
    if (strcmp(layout_name, "app") == 0 && has_resident_context) {
      if (!render_asm_include_for_amiga_symbol(preview, "LIB_SIZE")) {
        ++preview->asm_source_instruction_render_failures;
        record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, 0U, 0U);
        goto cleanup;
      }
      hash_asm_text(preview, "    RSSET LIB_SIZE\n");
    } else {
      hash_asm_text(preview, "    RSSET 0\n");
    }
    ++preview->asm_source_lines;
    cursor = layout_base_offset;
    for (; index < layout_end; ++index) {
      if (slots[index].displacement > cursor) {
        snprintf(line, sizeof(line), "    RS.B %d\n", (int)(slots[index].displacement - cursor));
        hash_asm_text(preview, line);
        ++preview->asm_source_lines;
        cursor = slots[index].displacement;
      }
      if (slots[index].displacement < cursor) {
        slots[index].alias = 1U;
        continue;
      } else if (slots[index].size == 4) {
        snprintf(line, sizeof(line), "%s RS.L 1\n", slots[index].name);
        cursor += 4;
      } else if (slots[index].size == 1) {
        snprintf(line, sizeof(line), "%s RS.B 1\n", slots[index].name);
        cursor += 1;
      } else if (slots[index].size == 2 && (cursor & 1) == 0) {
        snprintf(line, sizeof(line), "%s RS.W 1\n", slots[index].name);
        cursor += 2;
      } else {
        snprintf(line, sizeof(line), "%s RS.B %d\n", slots[index].name, (int)slots[index].size);
        cursor += slots[index].size;
      }
      hash_asm_text(preview, line);
      ++preview->asm_source_lines;
      if (cursor > layout_sizeof) layout_sizeof = cursor;
    }
    --index;
    if (strcmp(layout_name, "app") == 0) {
      if (has_app_sizeof_value != 0 && app_sizeof_value > layout_sizeof) layout_sizeof = app_sizeof_value;
    }
    if (layout_sizeof > cursor) {
      snprintf(line, sizeof(line), "    RS.B %d\n", (int)(layout_sizeof - cursor));
      hash_asm_text(preview, line);
      ++preview->asm_source_lines;
    }
    snprintf(line, sizeof(line), "%s EQU __RS\n", sizeof_symbol);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
    {
      size_t alias_index;
      for (alias_index = index + 1U; alias_index > 0U; --alias_index) {
        size_t slot_index = alias_index - 1U;
        if (strcmp(slots[slot_index].layout_name, layout_name) != 0) continue;
        if (slots[slot_index].alias == 0U) continue;
        snprintf(line, sizeof(line), "%s EQU $%04X\n", slots[slot_index].name,
          (unsigned)((uint32_t)slots[slot_index].displacement & 0xFFFFU));
        hash_asm_text(preview, line);
        ++preview->asm_source_lines;
      }
    }
    hash_asm_text(preview, "\n");
  }

cleanup:
  arena_rewind(scratch_arena, scratch_mark);
}

const char *lookup_indexed_vector_wrapper_library(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->indexed_vector_wrapper_count; ++index) {
    const M68kRenderIndexedVectorWrapper *wrapper = &lookup->indexed_vector_wrappers[index];
    if (wrapper->section_index == section_index && wrapper->offset == offset && wrapper->library_name[0] != '\0')
      return wrapper->library_name;
  }
  return NULL;
}

static const char *directive_for_data_size(uint32_t size) {
  if (size == 4U) return "dc.l";
  if (size == 2U) return "dc.w";
  return "dc.b";
}

void format_numeric_value(char *buffer, size_t buffer_size, uint32_t size, uint32_t value) {
  if (buffer == NULL || buffer_size == 0U) return;
  if (size == 4U) snprintf(buffer, buffer_size, "$%08X", (unsigned)value);
  else if (size == 2U) snprintf(buffer, buffer_size, "$%04X", (unsigned)(value & 0xFFFFU));
  else snprintf(buffer, buffer_size, "$%02X", (unsigned)(value & 0xFFU));
}

static void format_hunk_anchor_expression(char *buffer, size_t buffer_size, const M68kFact *anchor) {
  if (buffer == NULL || buffer_size == 0U) return;
  if (anchor == NULL) {
    buffer[0] = '\0';
    return;
  }
  if (anchor->target_addend < 0) {
    uint64_t magnitude = (uint64_t)(-anchor->target_addend);
    snprintf(buffer, buffer_size, "base(hunk %u)-$%08X",
      (unsigned)anchor->target_section_index, (unsigned)magnitude);
  } else {
    snprintf(buffer, buffer_size, "base(hunk %u)+$%08X",
      (unsigned)anchor->target_section_index, (unsigned)((uint64_t)anchor->target_addend & 0xFFFFFFFFULL));
  }
}

static void format_hunk_anchor_reason(char *buffer, size_t buffer_size, const M68kRenderLookup *lookup,
    const M68kFact *anchor) {
  uint32_t target_extent = 0U;
  if (buffer == NULL || buffer_size == 0U) return;
  if (lookup == NULL || anchor == NULL || anchor->target_section_index >= lookup->section_count ||
      lookup->label_extents == NULL) {
    snprintf(buffer, buffer_size, "target hunk unavailable; left numeric");
    return;
  }
  target_extent = lookup->label_extents[anchor->target_section_index];
  if (anchor->target_addend < 0) {
    snprintf(buffer, buffer_size, "negative addend points before target hunk; left numeric");
  } else if ((uint64_t)anchor->target_addend >= (uint64_t)target_extent) {
    snprintf(buffer, buffer_size, "addend outside target hunk real size $%08X; left numeric",
      (unsigned)target_extent);
  } else {
    snprintf(buffer, buffer_size, "unproven hunk relocation; left numeric");
  }
}

static void format_lossy_hunk_anchor_comment(char *buffer, size_t buffer_size, const M68kRenderLookup *lookup,
    const M68kFact *anchor) {
  char expr[96];
  char reason[160];
  if (buffer == NULL || buffer_size == 0U) return;
  if (anchor == NULL) {
    buffer[0] = '\0';
    return;
  }
  format_hunk_anchor_expression(expr, sizeof(expr), anchor);
  format_hunk_anchor_reason(reason, sizeof(reason), lookup, anchor);
  snprintf(buffer, buffer_size,
    "facts_v2 HUNK_RELOC32 numeric: source hunk %u offset $%08X, target hunk %u, loader result %s; %s",
    (unsigned)anchor->section_index, (unsigned)anchor->offset,
    (unsigned)anchor->target_section_index, expr, reason);
}

static void render_asm_lossy_hunk_relocation(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kFact *anchor) {
  char line[512];
  char value[32];
  char comment[384];
  const char *directive;
  if (preview == NULL || lookup == NULL || anchor == NULL) return;
  directive = directive_for_data_size(anchor->size);
  format_numeric_value(value, sizeof(value), anchor->size, anchor->target_offset);
  format_lossy_hunk_anchor_comment(comment, sizeof(comment), lookup, anchor);
  snprintf(line, sizeof(line), "\t%s %s\t; %s\n", directive, value, comment);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  ++preview->asm_source_lossy_numeric_hunk_relocations;
}

int accepted_start_at(const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t offset) {
  return section != NULL && accepted_start != NULL && offset < section->size && accepted_start[offset] != 0U;
}

int candidate_is_accepted_start(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kDecodeCandidate *candidate) {
  return candidate != NULL && candidate->byte_count != 0U &&
    accepted_start_at(section, accepted_start, candidate->offset);
}

static int accepted_byte_at(const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes, uint32_t offset) {
  return section != NULL && accepted_bytes != NULL && offset < section->size && accepted_bytes[offset] != 0U;
}

static const M68kSimFormMetadata *render_cfg_candidate_metadata(const M68kDecodeCandidate *candidate,
    M68kInstructionIR *instruction) {
  if (candidate == NULL || instruction == NULL) return NULL;
  if (m68k_decode_candidate_to_instruction(candidate, instruction) != 0) return NULL;
  return m68k_sim_metadata_for_instruction(instruction);
}

static int render_cfg_candidate_has_control_target(const M68kDecodeCandidate *candidate) {
  size_t target_index;
  if (candidate == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_CALL ||
        target->kind == M68K_DECODE_TARGET_JUMP) {
      return 1;
    }
  }
  return 0;
}

int render_cfg_candidate_has_fallthrough(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata = render_cfg_candidate_metadata(candidate, &instruction);
  if (metadata == NULL) return 1;
  if (metadata->flow_kind == M68K_SIM_FLOW_RETURN) return 0;
  if ((metadata->flow_kind == M68K_SIM_FLOW_JUMP || metadata->flow_kind == M68K_SIM_FLOW_BRANCH) &&
      !metadata->flow_conditional) {
    return 0;
  }
  return 1;
}

static uint8_t render_cfg_edge_kind_for_target(const M68kDecodeCandidate *candidate,
    const M68kDecodeTarget *target) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  if (target != NULL && target->kind == M68K_DECODE_TARGET_CALL) return M68K_CFG_EDGE_CALL;
  if (target != NULL && target->kind == M68K_DECODE_TARGET_JUMP) return M68K_CFG_EDGE_JUMP;
  metadata = render_cfg_candidate_metadata(candidate, &instruction);
  if (metadata != NULL && (metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
      (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && !metadata->flow_conditional))) {
    return M68K_CFG_EDGE_JUMP;
  }
  return M68K_CFG_EDGE_BRANCH;
}

static int render_cfg_append_edge(M68kSectionAnalysisIR *section_analysis, size_t source_block_index,
    uint32_t source_offset, uint32_t target_offset, uint8_t kind) {
  M68kCfgEdgeIR edge;
  memset(&edge, 0, sizeof(edge));
  edge.source_block_index = source_block_index;
  edge.target_block_index = SIZE_MAX;
  edge.source_offset = source_offset;
  edge.target_offset = target_offset;
  edge.kind = kind;
  return m68k_ir_section_analysis_append_edge(section_analysis, &edge);
}

static int render_cfg_resolve_edge_targets(M68kSectionAnalysisIR *section_analysis) {
  size_t edge_index;
  if (section_analysis == NULL) return -1;
  for (edge_index = 0U; edge_index < section_analysis->edge_count; ++edge_index) {
    M68kCfgEdgeIR *edge = &section_analysis->edges[edge_index];
    size_t block_index;
    edge->target_block_index = SIZE_MAX;
    if (edge->target_offset == UINT32_MAX) continue;
    for (block_index = 0U; block_index < section_analysis->block_count; ++block_index) {
      if (section_analysis->blocks[block_index].start_offset == edge->target_offset) {
        edge->target_block_index = block_index;
        break;
      }
    }
  }
  return 0;
}

static int render_cfg_lookup_block_start_at(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  return lookup != NULL && section_index < lookup->section_count && lookup->block_starts != NULL &&
    lookup->block_start_extents != NULL && lookup->block_starts[section_index] != NULL &&
    offset < lookup->block_start_extents[section_index] && lookup->block_starts[section_index][offset] != 0U;
}

static int render_cfg_build_block_start_map(const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const uint8_t *accepted_bytes, uint8_t *block_starts, uint32_t render_extent) {
  uint32_t offset = 0U;
  if (section == NULL || accepted_start == NULL || accepted_bytes == NULL || block_starts == NULL) return -1;
  while (offset < render_extent) {
    const M68kDecodeCandidate *candidate;
    uint32_t next_offset;
    size_t target_index;
    if (!accepted_start_at(section, accepted_start, offset)) {
      ++offset;
      continue;
    }
    candidate = find_candidate_at_offset_local(section, offset);
    if (candidate == NULL || candidate->byte_count == 0U || candidate->byte_count > render_extent - offset)
      return -1;
    if (offset == 0U || !accepted_byte_at(section, accepted_bytes, offset - 1U) ||
        render_cfg_lookup_block_start_at(lookup, section->section_index, offset)) {
      block_starts[offset] = 1U;
    }
    next_offset = offset + candidate->byte_count;
    for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
      const M68kDecodeTarget *target = &candidate->targets[target_index];
      if ((target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_CALL ||
          target->kind == M68K_DECODE_TARGET_JUMP) && target->has_section &&
          target->section_index == section->section_index && target->offset < render_extent &&
          accepted_start_at(section, accepted_start, target->offset)) {
        block_starts[target->offset] = 1U;
      }
    }
    if (render_cfg_candidate_has_control_target(candidate) && render_cfg_candidate_has_fallthrough(candidate) &&
        next_offset < render_extent && accepted_start_at(section, accepted_start, next_offset)) {
      block_starts[next_offset] = 1U;
    }
    offset = next_offset;
  }
  return 0;
}

static int render_analysis_append_cfg_for_section(const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const uint8_t *accepted_bytes, Arena *scratch_arena,
    M68kSectionAnalysisIR *section_analysis) {
  ArenaMark scratch_mark;
  uint32_t render_extent;
  uint8_t *block_starts = NULL;
  uint32_t offset = 0U;
  int result = -1;
  if (section == NULL || scratch_arena == NULL || section_analysis == NULL) return -1;
  render_extent = render_section_extent(section);
  if (render_extent == 0U) return 0;
  scratch_mark = arena_mark(scratch_arena);
  block_starts = (uint8_t *)arena_calloc(scratch_arena, render_extent, sizeof(*block_starts));
  if (block_starts == NULL) return -1;
  if (render_cfg_build_block_start_map(lookup, section, accepted_start, accepted_bytes, block_starts,
      render_extent) != 0) {
    goto cleanup;
  }
  while (offset < render_extent) {
    M68kCfgBlockIR block;
    uint32_t cursor;
    if (!accepted_start_at(section, accepted_start, offset) || block_starts[offset] == 0U) {
      ++offset;
      continue;
    }
    memset(&block, 0, sizeof(block));
    block.start_offset = offset;
    block.certainty = M68K_CODE_CERTAIN;
    block.edge_start = section_analysis->edge_count;
    cursor = offset;
    while (cursor < render_extent && accepted_start_at(section, accepted_start, cursor)) {
      const M68kDecodeCandidate *candidate = find_candidate_at_offset_local(section, cursor);
      uint32_t next_offset;
      size_t target_index;
      int has_control_target;
      int has_fallthrough;
      if (candidate == NULL || candidate->byte_count == 0U || candidate->byte_count > render_extent - cursor)
        goto cleanup;
      next_offset = cursor + candidate->byte_count;
      has_control_target = render_cfg_candidate_has_control_target(candidate);
      has_fallthrough = render_cfg_candidate_has_fallthrough(candidate);
      for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
        const M68kDecodeTarget *target = &candidate->targets[target_index];
        if ((target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_CALL ||
            target->kind == M68K_DECODE_TARGET_JUMP) && target->has_section &&
            target->section_index == section->section_index) {
          if (render_cfg_append_edge(section_analysis, section_analysis->block_count, cursor, target->offset,
              render_cfg_edge_kind_for_target(candidate, target)) != 0) {
            goto cleanup;
          }
        }
      }
      if (has_control_target) {
        if (has_fallthrough && next_offset < render_extent && accepted_start_at(section, accepted_start, next_offset) &&
            render_cfg_append_edge(section_analysis, section_analysis->block_count, cursor, next_offset,
              M68K_CFG_EDGE_FALLTHROUGH) != 0) {
          goto cleanup;
        }
        cursor = next_offset;
        break;
      }
      if (!has_fallthrough) {
        if (render_cfg_append_edge(section_analysis, section_analysis->block_count, cursor, UINT32_MAX,
            M68K_CFG_EDGE_RETURN) != 0) {
          goto cleanup;
        }
        cursor = next_offset;
        break;
      }
      if (next_offset >= render_extent || !accepted_start_at(section, accepted_start, next_offset) ||
          block_starts[next_offset] != 0U) {
        if (next_offset < render_extent && accepted_start_at(section, accepted_start, next_offset) &&
            render_cfg_append_edge(section_analysis, section_analysis->block_count, cursor, next_offset,
              M68K_CFG_EDGE_FALLTHROUGH) != 0) {
          goto cleanup;
        }
        cursor = next_offset;
        break;
      }
      cursor = next_offset;
    }
    block.end_offset = cursor;
    block.edge_count = section_analysis->edge_count - block.edge_start;
    if (m68k_ir_section_analysis_append_block(section_analysis, &block) != 0) goto cleanup;
    offset = cursor > offset ? cursor : offset + 1U;
  }
  if (render_cfg_resolve_edge_targets(section_analysis) != 0) goto cleanup;
  result = 0;

cleanup:
  arena_rewind(scratch_arena, scratch_mark);
  return result;
}

uint8_t symbol_ref_kind_for_operand(const M68kOperandIR *operand) {
  if (operand == NULL) return M68K_IR_SYMBOL_REF_ABS;
  if (operand->kind == M68K_ASM_OPERAND_LABEL) return M68K_IR_SYMBOL_REF_PC_REL;
  if ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->value.ea_mode == 7U && (operand->value.ea_reg == 2U || operand->value.ea_reg == 3U)) {
    return M68K_IR_SYMBOL_REF_PC_REL;
  }
  return M68K_IR_SYMBOL_REF_ABS;
}

void attach_operand_label_symbol(const M68kRenderLookup *lookup, M68kInstructionIR *instruction,
    size_t operand_index, size_t source_section_index, uint32_t source_offset, size_t target_section_index,
    uint32_t target_offset) {
  M68kOperandIR *operand;
  uint8_t symbol_kind;
  if (instruction == NULL || operand_index >= instruction->operand_count) return;
  operand = &instruction->operands[operand_index];
  symbol_kind = symbol_ref_kind_for_operand(operand);
  if (symbol_kind == M68K_IR_SYMBOL_REF_PC_REL && source_section_index == target_section_index &&
      !lookup_source_offsets_share_runtime_view(lookup, source_section_index, source_offset, target_offset) &&
      !lookup_source_offset_is_materialized_runtime_range_start(lookup, target_section_index, target_offset)) {
    return;
  }
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
  operand->symbol_ref.kind = symbol_kind;
  operand->symbol_ref.has_name = 1U;
  if (symbol_kind == M68K_IR_SYMBOL_REF_PC_REL && source_section_index == target_section_index &&
      (!lookup_source_offsets_share_runtime_view(lookup, source_section_index, source_offset, target_offset) ||
       (source_offset < target_offset &&
        lookup_source_offset_is_materialized_runtime_range_start(lookup, target_section_index, target_offset)))) {
    operand->symbol_ref.name_is_generated = format_storage_asm_label_with_generation(lookup,
      operand->symbol_ref.name, sizeof(operand->symbol_ref.name), target_section_index, target_offset);
  } else {
    operand->symbol_ref.name_is_generated = format_rendered_asm_label_with_generation(lookup,
      operand->symbol_ref.name, sizeof(operand->symbol_ref.name), target_section_index, target_offset);
  }
  operand->symbol_ref.has_section = 1;
  operand->symbol_ref.section_index = target_section_index;
}

static void attach_operand_storage_label_symbol(const M68kRenderLookup *lookup, M68kInstructionIR *instruction,
    size_t operand_index, size_t target_section_index, uint32_t target_offset) {
  M68kOperandIR *operand;
  if (instruction == NULL || operand_index >= instruction->operand_count) return;
  operand = &instruction->operands[operand_index];
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
  operand->symbol_ref.kind = symbol_ref_kind_for_operand(operand);
  operand->symbol_ref.has_name = 1U;
  operand->symbol_ref.name_is_generated = format_storage_asm_label_with_generation(lookup,
    operand->symbol_ref.name, sizeof(operand->symbol_ref.name), target_section_index, target_offset);
  operand->symbol_ref.has_section = 1;
  operand->symbol_ref.section_index = target_section_index;
}

static int target_matches_relocation(const M68kDecodeTarget *target, const M68kFact *relocation) {
  return target != NULL && relocation != NULL && target->has_section != 0U &&
    target->section_index == relocation->target_section_index && target->offset == relocation->target_offset;
}

static int32_t signed_8(uint32_t value) {
  return (int8_t)(value & 0xFFU);
}

static int32_t signed_16(uint32_t value) {
  return (int16_t)(value & 0xFFFFU);
}

static int exact_operand_relocation_span(const M68kDecodeCandidate *candidate, size_t operand_index,
    uint32_t *out_start, uint32_t *out_size) {
  const M68kAsmFormDef *form;
  M68kAsmOperandValue layout_operands[M68K_DECODE_IR_MAX_OPERANDS];
  char size_suffix;
  size_t word_index;
  size_t extension_index;
  size_t index;
  if (candidate == NULL || out_start == NULL || out_size == NULL || operand_index >= candidate->operand_count)
    return 0;
  if (candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_LABEL && candidate->size_suffix == 'b') {
    *out_start = candidate->offset + 1U;
    *out_size = 1U;
    return 1;
  }
  if (candidate->asm_form_index >= M68K_ASM_FORM_SLOT_COUNT) return 0;
  form = &g_m68k_asm_forms[candidate->asm_form_index];
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) return 0;
  for (index = 0U; index < candidate->operand_count; ++index)
    layout_operands[index] = normalized_layout_operand(candidate, index);
  size_suffix = candidate_effective_size_suffix(candidate);
  word_index = 1U + form->bound_word_count;
  for (extension_index = 0U; extension_index < form->extension_count; ++extension_index) {
    const M68kAsmExtensionDef *extension = &g_m68k_asm_extensions[form->extension_start + extension_index];
    size_t word_count;
    if (extension->operand_index >= candidate->operand_count) continue;
    word_count = relocation_extension_word_count(candidate->asm_form_index, extension->kind,
      &layout_operands[extension->operand_index], size_suffix);
    if (extension->operand_index == operand_index && word_count != 0U) {
      if (word_index > UINT32_MAX / 2U || word_count > UINT32_MAX / 2U) return 0;
      if (candidate->offset > UINT32_MAX - (uint32_t)(word_index * 2U)) return 0;
      *out_start = candidate->offset + (uint32_t)(word_index * 2U);
      *out_size = (uint32_t)(word_count * 2U);
      return 1;
    }
    word_index += word_count;
  }
  return 0;
}

static int relocation_fits_operand_span(const M68kFact *relocation, uint32_t span_start, uint32_t span_size) {
  uint32_t span_end;
  uint32_t relocation_end;
  if (relocation == NULL || relocation->size == 0U || span_size == 0U) return 0;
  if (span_start > UINT32_MAX - span_size || relocation->offset > UINT32_MAX - relocation->size) return 0;
  span_end = span_start + span_size;
  relocation_end = relocation->offset + relocation->size;
  return relocation->offset == span_start && relocation_end == span_end;
}

static int absolute_operand_value_matches_relocation(const M68kAsmOperandValue *operand, const M68kFact *relocation,
    char size_suffix) {
  uint32_t encoded_value = 0U;
  int has_encoded_value = 0;
  if (operand == NULL || relocation == NULL) return 0;
  if (relocation->target_addend > 0 && relocation->target_addend <= UINT32_MAX) {
    encoded_value = (uint32_t)relocation->target_addend;
    has_encoded_value = 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_IMM) {
    if (size_suffix == 'l' && relocation->size != 4U) return 0;
    if (size_suffix != 'l' && relocation->size != 2U) return 0;
    return operand->value == relocation->target_offset ||
      (has_encoded_value && operand->value == encoded_value);
  }
  if (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) {
    if (operand->ea_mode == 7U && operand->ea_reg == 1U && relocation->size == 4U)
      return operand->value == relocation->target_offset ||
        (has_encoded_value && operand->value == encoded_value);
    if (operand->ea_mode == 7U && operand->ea_reg == 4U) {
      if (size_suffix == 'l' && relocation->size != 4U) return 0;
      if (size_suffix != 'l' && relocation->size != 2U) return 0;
      return operand->value == relocation->target_offset ||
        (has_encoded_value && operand->value == encoded_value);
    }
  }
  if (operand->kind == M68K_ASM_OPERAND_ABSL && relocation->size == 4U)
    return operand->value == relocation->target_offset ||
      (has_encoded_value && operand->value == encoded_value);
  return 0;
}

static int pc_relative_operand_value_matches_relocation(const M68kDecodeCandidate *candidate, size_t operand_index,
    const M68kAsmOperandValue *operand, const M68kFact *relocation) {
  M68kAsmOperandValue asm_operands[M68K_DECODE_IR_MAX_OPERANDS];
  size_t index;
  size_t relative_base;
  int64_t target;
  if (candidate == NULL || operand == NULL || relocation == NULL || operand_index >= candidate->operand_count)
    return 0;
  if (operand->kind == M68K_ASM_OPERAND_LABEL) {
    int32_t disp = relocation->size == 1U ? signed_8(operand->value) : signed_16(operand->value);
    target = (int64_t)candidate->offset + 2 + disp;
    return target >= 0 && target <= UINT32_MAX && (uint32_t)target == relocation->target_offset;
  }
  if (!((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->ea_mode == 7U && (operand->ea_reg == 2U || operand->ea_reg == 3U))) {
    return 0;
  }
  if (operand->ea_reg == 3U &&
      (operand->full_ext_base_suppress != 0U || operand->full_ext_index_suppress != 0U ||
       operand->full_ext_base_disp_size != 0U || operand->full_ext_outer_disp_size != 0U ||
       operand->full_ext_iis != 0U)) {
    return 0;
  }
  for (index = 0U; index < candidate->operand_count; ++index) {
    asm_operands[index] = candidate->operands[index];
    asm_operands[index].kind = candidate->operand_kinds[index];
  }
  relative_base = m68k_asm_operand_relative_base_offset(candidate->asm_form_index, asm_operands,
    candidate->operand_count, candidate_effective_size_suffix(candidate), operand_index, 0);
  target = (int64_t)candidate->offset + (int64_t)relative_base + signed_16(operand->value);
  return target >= 0 && target <= UINT32_MAX && (uint32_t)target == relocation->target_offset;
}

static int operand_value_matches_relocation(const M68kDecodeCandidate *candidate, size_t operand_index,
    const M68kFact *relocation) {
  M68kAsmOperandValue operand;
  if (candidate == NULL || relocation == NULL || operand_index >= candidate->operand_count) return 0;
  operand = candidate->operands[operand_index];
  operand.kind = candidate->operand_kinds[operand_index];
  if (absolute_operand_value_matches_relocation(&operand, relocation, candidate_effective_size_suffix(candidate)))
    return 1;
  return pc_relative_operand_value_matches_relocation(candidate, operand_index, &operand, relocation);
}

int find_unique_relocation_operand(const M68kDecodeCandidate *candidate, const M68kFact *relocation,
    size_t *out_operand_index) {
  size_t operand_index;
  size_t match_index = 0U;
  size_t match_count = 0U;
  if (candidate == NULL || relocation == NULL || out_operand_index == NULL) return 0;
  for (operand_index = 0U; operand_index < candidate->operand_count; ++operand_index) {
    uint32_t span_start = 0U;
    uint32_t span_size = 0U;
    if (!exact_operand_relocation_span(candidate, operand_index, &span_start, &span_size)) continue;
    if (!relocation_fits_operand_span(relocation, span_start, span_size)) continue;
    if (!operand_value_matches_relocation(candidate, operand_index, relocation)) continue;
    match_index = operand_index;
    ++match_count;
  }
  if (match_count != 1U) return 0;
  *out_operand_index = match_index;
  return 1;
}

int candidate_loads_relocated_global_slot_to_a6(const M68kRenderLookup *lookup, size_t section_index,
    const M68kDecodeCandidate *candidate, size_t *out_target_section, uint32_t *out_target_offset) {
  M68kInstructionIR instruction;
  uint32_t offset;
  uint32_t end;
  if (lookup == NULL || candidate == NULL || out_target_section == NULL || out_target_offset == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!operand_is_address_register_local(&instruction.operands[1], 6U)) return 0;
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset + 2U; offset < end; ++offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section_index, offset);
    size_t operand_index = 0U;
    if (relocation == NULL) continue;
    if (!lookup_has_renderable_label(lookup, relocation->target_section_index, relocation->target_offset)) continue;
    if (!find_unique_relocation_operand(candidate, relocation, &operand_index) || operand_index != 0U) continue;
    *out_target_section = relocation->target_section_index;
    *out_target_offset = relocation->target_offset;
    return 1;
  }
  return 0;
}

int candidate_direct_control_target(const M68kRenderLookup *lookup, size_t source_section_index,
    const M68kDecodeCandidate *candidate, size_t *out_section_index, uint32_t *out_target) {
  uint32_t offset;
  uint32_t end;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_target != NULL) *out_target = 0U;
  if (candidate == NULL || out_section_index == NULL || out_target == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_BSR &&
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR &&
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_JMP) {
    return 0;
  }
  if (lookup != NULL && candidate->operand_count == 1U) {
    end = candidate->offset + candidate->byte_count;
    for (offset = candidate->offset + 2U; offset < end; ++offset) {
      const M68kFact *relocation = lookup_relocation_at(lookup, source_section_index, offset);
      size_t operand_index = 0U;
      if (relocation == NULL) continue;
      if (!find_unique_relocation_operand(candidate, relocation, &operand_index) || operand_index != 0U) continue;
      *out_section_index = relocation->target_section_index;
      *out_target = relocation->target_offset;
      return 1;
    }
  }
  return candidate_direct_target(candidate, out_section_index, out_target);
}

int candidate_calls_a6_lvo(const M68kDecodeCandidate *candidate, int16_t *out_lvo) {
  M68kAsmOperandValue operand;
  int16_t displacement;
  if (candidate == NULL || out_lvo == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR && candidate->mnemonic_id != M68K_ASM_MNEMONIC_JMP)
    return 0;
  if (candidate->operand_count != 1U) return 0;
  operand = candidate->operands[0];
  operand.kind = candidate->operand_kinds[0];
  if (operand.kind != M68K_ASM_OPERAND_EA || operand.ea_mode != 5U || operand.ea_reg != 6U) return 0;
  displacement = (int16_t)(operand.value & 0xFFFFU);
  if (displacement >= 0) return 0;
  *out_lvo = displacement;
  return 1;
}

int operand_is_postinc_a7_local(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_POSTINC) return operand->value.reg == 7U;
  return operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 3U && operand->value.ea_reg == 7U;
}

int instruction_is_local_wrapper_cleanup(const M68kInstructionIR *instruction) {
  if (instruction == NULL) return 0;
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDQ || instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADD) &&
      instruction->operand_count == 2U && operand_is_address_register_local(&instruction->operands[1], 7U)) {
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U &&
      operand_is_address_register_local(&instruction->operands[1], 7U)) {
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && instruction->operand_count == 2U &&
      operand_is_postinc_a7_local(&instruction->operands[0])) {
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count == 2U &&
      operand_is_postinc_a7_local(&instruction->operands[0])) {
    return 1;
  }
  return 0;
}

int candidate_has_non_call_control_target(const M68kDecodeCandidate *candidate) {
  size_t target_index;
  if (candidate == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_JUMP) return 1;
  }
  return 0;
}

int candidate_calls_a6_d0_indexed_vector(const M68kDecodeCandidate *candidate) {
  M68kAsmOperandValue operand;
  if (candidate == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR && candidate->mnemonic_id != M68K_ASM_MNEMONIC_JMP)
    return 0;
  if (candidate->operand_count != 1U) return 0;
  operand = candidate->operands[0];
  operand.kind = candidate->operand_kinds[0];
  return operand.kind == M68K_ASM_OPERAND_EA && operand.ea_mode == 6U && operand.ea_reg == 6U &&
    operand.index_is_address == 0U && operand.index_reg == 0U && operand.value == 0U;
}

int candidate_direct_same_section_target(const M68kDecodeCandidate *candidate, size_t section_index,
    uint32_t *out_target) {
  size_t target_section_index = 0U;
  if (out_target != NULL) *out_target = 0U;
  if (!candidate_direct_target(candidate, &target_section_index, out_target)) return 0;
  return target_section_index == section_index;
}

int candidate_direct_target(const M68kDecodeCandidate *candidate, size_t *out_section_index,
    uint32_t *out_target) {
  size_t target_index;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_target != NULL) *out_target = 0U;
  if (candidate == NULL || out_section_index == NULL || out_target == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_BSR &&
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR &&
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_JMP) {
    return 0;
  }
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->has_section == 0U) continue;
    if ((candidate->mnemonic_id == M68K_ASM_MNEMONIC_BSR ||
         candidate->mnemonic_id == M68K_ASM_MNEMONIC_JSR) &&
        target->kind != M68K_DECODE_TARGET_CALL) {
      continue;
    }
    if (candidate->mnemonic_id == M68K_ASM_MNEMONIC_JMP && target->kind != M68K_DECODE_TARGET_JUMP)
      continue;
    *out_section_index = target->section_index;
    *out_target = target->offset;
    return 1;
  }
  return 0;
}

static int candidate_any_same_section_target(const M68kDecodeCandidate *candidate, size_t section_index,
    uint32_t *out_target) {
  size_t target_index;
  if (out_target != NULL) *out_target = 0U;
  if (candidate == NULL || out_target == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->has_section == 0U || target->section_index != section_index) continue;
    if (target->kind != M68K_DECODE_TARGET_BRANCH && target->kind != M68K_DECODE_TARGET_CALL &&
        target->kind != M68K_DECODE_TARGET_JUMP) {
      continue;
    }
    *out_target = target->offset;
    return 1;
  }
  return 0;
}

int candidate_loads_d0_lvo_immediate(const M68kDecodeCandidate *candidate, int16_t *out_lvo) {
  M68kInstructionIR instruction;
  if (out_lvo != NULL) *out_lvo = 0;
  if (candidate == NULL || out_lvo == NULL) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!instruction_loads_d0_immediate(&instruction, out_lvo)) return 0;
  return *out_lvo < 0;
}

int render_lookup_add_indexed_vector_wrapper_branch_aliases(M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t indexed_entry,
    const char *library_name) {
  uint32_t offset = 0U;
  uint32_t segment_entry = 0U;
  int segment_valid = 0;
  if (lookup == NULL || section == NULL || accepted_start == NULL || library_name == NULL) return 0;
  while (offset < section->size) {
    const M68kDecodeCandidate *candidate;
    uint32_t target = 0U;
    if (!accepted_start_at(section, accepted_start, offset)) {
      segment_valid = 0;
      ++offset;
      continue;
    }
    candidate = find_candidate_at_offset_local(section, offset);
    if (candidate == NULL || candidate->byte_count == 0U) {
      segment_valid = 0;
      ++offset;
      continue;
    }
    if (!segment_valid) {
      segment_valid = 1;
      segment_entry = offset;
    }
    if (candidate_any_same_section_target(candidate, section->section_index, &target) && target == indexed_entry &&
        segment_entry != indexed_entry) {
      if (render_lookup_add_indexed_vector_wrapper(lookup, section->section_index, segment_entry, library_name) != 0)
        return -1;
    }
    if (candidate_terminates_a6_state(candidate)) segment_valid = 0;
    offset += candidate->byte_count;
  }
  return 0;
}

int candidate_writes_a6_unknown(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  if (candidate == NULL) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    return instruction.operand_count >= 2U && reglist_contains_address_register_local(&instruction.operands[1], 6U);
  }
  return instruction.operand_count >= 2U && operand_is_address_register_local(&instruction.operands[1], 6U);
}

int candidate_terminates_a6_state(const M68kDecodeCandidate *candidate) {
  return candidate != NULL && (candidate->mnemonic_id == M68K_ASM_MNEMONIC_RTS ||
    candidate->mnemonic_id == M68K_ASM_MNEMONIC_RTE || candidate->mnemonic_id == M68K_ASM_MNEMONIC_JMP);
}

int candidate_has_local_helper_summary_fallthrough(const M68kDecodeCandidate *candidate) {
  if (candidate == NULL) return 0;
  return candidate->mnemonic_id != M68K_ASM_MNEMONIC_RTS &&
    candidate->mnemonic_id != M68K_ASM_MNEMONIC_RTR &&
    candidate->mnemonic_id != M68K_ASM_MNEMONIC_RTE &&
    candidate->mnemonic_id != M68K_ASM_MNEMONIC_STOP &&
    candidate->mnemonic_id != M68K_ASM_MNEMONIC_ILLEGAL &&
    candidate->mnemonic_id != M68K_ASM_MNEMONIC_JMP &&
    candidate->mnemonic_id != M68K_ASM_MNEMONIC_BRA;
}

const AmigaOsCallInputInfo *amiga_vector_input_by_register(const AmigaOsLibraryVectorInfo *vector,
    uint8_t reg_kind, uint8_t reg_index) {
  const AmigaOsCallInputInfo *inputs;
  size_t input_count = 0U;
  size_t index;
  if (vector == NULL) return NULL;
  inputs = amiga_os_library_vector_inputs(vector, &input_count);
  if (inputs == NULL) return NULL;
  for (index = 0U; index < input_count; ++index) {
    if (inputs[index].reg_kind == reg_kind && inputs[index].reg_index == reg_index) return &inputs[index];
  }
  return NULL;
}

const AmigaOsCallInputInfo *amiga_vector_input_by_stack_index(const AmigaOsLibraryVectorInfo *vector,
    size_t stack_index) {
  const AmigaOsCallInputInfo *inputs;
  size_t input_count = 0U;
  if (vector == NULL) return NULL;
  inputs = amiga_os_library_vector_inputs(vector, &input_count);
  if (inputs == NULL || stack_index >= input_count) return NULL;
  return &inputs[stack_index];
}

static int attach_symbolic_targets(const M68kRenderLookup *lookup, size_t source_section_index,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  size_t target_index;
  if (lookup == NULL || candidate == NULL || instruction == NULL) return -1;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    M68kOperandIR *operand;
    uint8_t symbol_kind;
    if (target->has_section == 0U || target->has_operand == 0U ||
        target->operand_index >= instruction->operand_count) {
      continue;
    }
    if (!lookup_has_renderable_label(lookup, target->section_index, target->offset)) continue;
    operand = &instruction->operands[target->operand_index];
    symbol_kind = symbol_ref_kind_for_operand(operand);
    if (symbol_kind == M68K_IR_SYMBOL_REF_ABS &&
        ((target->kind != M68K_DECODE_TARGET_CALL && target->kind != M68K_DECODE_TARGET_JUMP) ||
         !candidate_operand_is_absolute_word_local(candidate, target->operand_index))) {
      continue;
    }
    attach_operand_label_symbol(lookup, instruction, target->operand_index, source_section_index,
      candidate->offset, target->section_index, target->offset);
  }
  return 0;
}

static int attach_absolute_word_control_symbols(const M68kRenderLookup *lookup, size_t source_section_index,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  uint32_t section_size;
  size_t operand_index;
  if (lookup == NULL || lookup->object == NULL || candidate == NULL || instruction == NULL ||
      source_section_index >= lookup->object->section_count) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL ||
      (metadata->flow_kind != M68K_SIM_FLOW_CALL && metadata->flow_kind != M68K_SIM_FLOW_JUMP)) {
    return 0;
  }
  section_size = lookup->object->sections[source_section_index].size;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    uint32_t absolute = 0U;
    uint32_t target_offset = 0U;
    if (operand->symbol_ref.has_name != 0U || !candidate_operand_is_absolute_word_local(candidate, operand_index) ||
        !operand_absolute_offset_local(operand, &absolute)) {
      continue;
    }
    if (!lookup_exact_pointer_value_label_offset(lookup, source_section_index, section_size, absolute,
        &target_offset)) {
      continue;
    }
    attach_operand_label_symbol(lookup, instruction, operand_index, source_section_index, candidate->offset,
      source_section_index, target_offset);
  }
  return 0;
}

static int attach_platform_pc_relative_synthetic_symbols(const M68kRenderLookup *lookup, size_t section_index,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  size_t operand_index;
  if (lookup == NULL || lookup->object == NULL || candidate == NULL || instruction == NULL) return 0;
  (void)section_index;
  for (operand_index = 0U; operand_index < instruction->operand_count &&
       operand_index < candidate->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    M68kAsmOperandValue asm_operands[M68K_DECODE_IR_MAX_OPERANDS];
    char symbol_name[M68K_IR_SYMBOL_NAME_SIZE];
    size_t index;
    size_t relative_base;
    int64_t target;
    if (operand->symbol_ref.has_name != 0U) continue;
    if (operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_mode != 7U || operand->value.ea_reg != 2U)
      continue;
    if (candidate->operand_kinds[operand_index] != M68K_ASM_OPERAND_EA ||
        candidate->operands[operand_index].ea_mode != 7U ||
        candidate->operands[operand_index].ea_reg != 2U) {
      continue;
    }
    for (index = 0U; index < candidate->operand_count; ++index) {
      asm_operands[index] = candidate->operands[index];
      asm_operands[index].kind = candidate->operand_kinds[index];
    }
    relative_base = m68k_asm_operand_relative_base_offset(candidate->asm_form_index, asm_operands,
      candidate->operand_count, candidate_effective_size_suffix(candidate), operand_index, 0);
    target = (int64_t)candidate->offset + (int64_t)relative_base + signed_16(candidate->operands[operand_index].value);
    if (!platform_facts_v2_pc_relative_symbol_for_target(lookup->object->platform_backend_kind, target,
        symbol_name, sizeof(symbol_name))) {
      continue;
    }
    m68k_ir_symbol_ref_init(&operand->symbol_ref);
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_PC_REL;
    operand->symbol_ref.has_name = 1U;
    operand->symbol_ref.name_provenance = lookup->object->platform_backend_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK
      ? M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA
      : M68K_IR_SYMBOL_PROVENANCE_NONE;
    snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol_name);
  }
  return 0;
}

static int amiga_abs_exec_base_load_should_stay_absolute(const M68kRenderLookup *lookup,
    const M68kInstructionIR *instruction, size_t operand_index, const M68kOperandIR *operand,
    const M68kFact *fact) {
  uint32_t absolute = 0U;
  if (lookup == NULL || lookup->object == NULL || instruction == NULL || operand == NULL || fact == NULL) return 0;
  if (lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 0;
  if (fact->runtime_address != 4U || operand_index != 0U || instruction->operand_count < 2U) return 0;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA) {
    return 0;
  }
  return operand_absolute_offset_local(operand, &absolute) && absolute == 4U;
}

static int attach_runtime_address_ref_symbols(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    size_t section_index,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  size_t operand_index;
  if (lookup == NULL || candidate == NULL || instruction == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kFact *fact;
    M68kOperandIR *operand;
    if (operand_index >= candidate->operand_count) break;
    operand = &instruction->operands[operand_index];
    if (operand->symbol_ref.has_name != 0U) continue;
    fact = lookup_runtime_address_ref_for_operand(lookup, section_index, candidate->offset, operand_index);
    if (fact == NULL) continue;
    if (fact->target_section_index >= lookup->section_count) {
      const char *role;
      uint32_t value = 0U;
      char symbol[80];
      if (!operand_is_immediate_value_local(operand, &value) || value != fact->runtime_address) continue;
      role = external_runtime_address_ref_role(lookup, fact);
      if (role == NULL) continue;
      if (!render_asm_define_runtime_address_symbol_once(preview, role, fact->runtime_address, symbol,
          sizeof(symbol))) {
        return 0;
      }
      attach_amiga_platform_symbol(operand, symbol);
      continue;
    }
    {
      uint32_t target_runtime_address = fact->runtime_address;
      int has_materialized_target = lookup_source_has_materialized_runtime_address(lookup,
        fact->target_section_index, fact->target_offset, fact->runtime_address);
      if (!has_materialized_target &&
          lookup_source_runtime_address(lookup, fact->target_section_index, fact->target_offset,
            &target_runtime_address) && target_runtime_address != fact->runtime_address &&
          lookup_has_renderable_label(lookup, fact->target_section_index, fact->target_offset)) {
        int64_t addend = (int64_t)(uint64_t)fact->runtime_address - (int64_t)(uint64_t)target_runtime_address;
        if (addend < INT32_MIN || addend > INT32_MAX) {
          record_numeric_runtime_ref(preview, fact);
          continue;
        }
      } else if (!has_materialized_target) {
        char symbol[80];
        if (!amiga_abs_exec_base_load_should_stay_absolute(lookup, instruction, operand_index, operand, fact) &&
            runtime_address_ref_targets_unmaterialized_discovered_code(lookup, fact) &&
            render_asm_define_runtime_address_symbol_once(preview, "runtime_code", fact->runtime_address, symbol,
              sizeof(symbol))) {
          attach_generic_symbol(operand, symbol);
          continue;
        }
        record_numeric_runtime_ref(preview, fact);
        continue;
      }
      if (amiga_abs_exec_base_load_should_stay_absolute(lookup, instruction, operand_index, operand, fact)) {
        record_numeric_runtime_ref(preview, fact);
        continue;
      }
      {
        uint32_t absolute = 0U;
        if (operand_absolute_offset_local(operand, &absolute) && absolute == fact->target_offset &&
            lookup_has_renderable_label(lookup, fact->target_section_index, fact->target_offset) &&
            lookup_source_offset_is_materialized_runtime_range_start(lookup, fact->target_section_index,
              fact->target_offset)) {
          attach_operand_storage_label_symbol(lookup, instruction, operand_index, fact->target_section_index,
            fact->target_offset);
          continue;
        }
      }
      if (!lookup_has_renderable_label(lookup, fact->target_section_index, fact->target_offset)) {
        if (preview != NULL) {
          ++preview->asm_source_instruction_render_failures;
          record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, section_index,
            candidate->offset, fact->target_offset);
        }
        return 0;
      }
      m68k_ir_symbol_ref_init(&operand->symbol_ref);
      operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_ABS;
      operand->symbol_ref.has_name = 1U;
      operand->symbol_ref.name_is_generated = 1U;
      operand->symbol_ref.has_section = 1;
      operand->symbol_ref.section_index = fact->target_section_index;
      if (target_runtime_address != fact->runtime_address) {
        int64_t addend = (int64_t)(uint64_t)fact->runtime_address - (int64_t)(uint64_t)target_runtime_address;
        if (addend >= INT32_MIN && addend <= INT32_MAX) operand->symbol_ref.addend = (int32_t)addend;
      }
      format_runtime_asm_label(lookup, operand->symbol_ref.name, sizeof(operand->symbol_ref.name),
        fact->target_section_index, fact->target_offset, target_runtime_address);
    }
  }
  return 1;
}

static int attach_absolute_stack_top_symbol(M68kRenderIRPreview *preview, M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  uint8_t source_index;
  uint8_t dest_index;
  uint8_t dest_reg = 0U;
  uint32_t value = 0U;
  char symbol[80];
  if (preview == NULL || instruction == NULL) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL || instruction->operand_count == 0U) return 0;
  if (metadata->operation_type != M68K_SIM_OP_MOVE &&
      metadata->operation_class != M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS) {
    return 0;
  }
  source_index = metadata->source_operand_index;
  dest_index = metadata->dest_operand_index;
  if (source_index >= instruction->operand_count || dest_index >= instruction->operand_count) return 0;
  if (metadata->operand_access_kinds[dest_index] != M68K_SIM_ACCESS_REGISTER_WRITE ||
      !operand_address_register_index_local(&instruction->operands[dest_index], &dest_reg) || dest_reg != 7U ||
      instruction->operands[source_index].symbol_ref.has_name != 0U) {
    return 0;
  }
  if (!operand_is_immediate_value_local(&instruction->operands[source_index], &value) &&
      !operand_absolute_offset_local(&instruction->operands[source_index], &value)) {
    return 0;
  }
  if (value == 0U || m68k_cpu_find_exception_vector_by_address(value) != NULL ||
      amiga_os_find_hardware_base_symbol_by_address(value) != NULL ||
      amiga_os_find_hardware_register_by_cpu_address(value) != NULL ||
      amiga_os_find_hardware_register_field_by_cpu_address(value) != NULL ||
      amiga_os_find_hardware_register_range_by_cpu_address(value) != NULL) {
    return 0;
  }
  if (!render_asm_define_runtime_address_symbol_once(preview, "stack_top", value, symbol, sizeof(symbol)))
    return 0;
  attach_generic_symbol(&instruction->operands[source_index], symbol);
  return 1;
}

static int instruction_relocation_is_proven_operand(const M68kRenderLookup *lookup, size_t source_section_index,
    const M68kDecodeCandidate *candidate, const M68kFact *relocation, M68kInstructionIR *instruction) {
  size_t target_index;
  if (lookup == NULL || candidate == NULL || relocation == NULL || instruction == NULL) return 0;
  if (!lookup_has_renderable_label(lookup, relocation->target_section_index, relocation->target_offset)) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    M68kOperandIR *operand;
    uint32_t absolute = 0U;
    uint32_t runtime_address = 0U;
    if (target->has_operand == 0U || target->operand_index >= instruction->operand_count) continue;
    if (!target_matches_relocation(target, relocation)) continue;
    operand = &instruction->operands[target->operand_index];
    if (operand_absolute_offset_local(operand, &absolute) && absolute == relocation->target_offset &&
        lookup_source_should_render_runtime_label(lookup, relocation->target_section_index,
          relocation->target_offset, &runtime_address)) {
      attach_operand_storage_label_symbol(lookup, instruction, target->operand_index,
        relocation->target_section_index, relocation->target_offset);
    } else {
      attach_operand_label_symbol(lookup, instruction, target->operand_index, source_section_index,
        candidate->offset, relocation->target_section_index, relocation->target_offset);
    }
    return 1;
  }
  {
    size_t operand_index = 0U;
    M68kOperandIR *operand;
    uint32_t absolute = 0U;
    uint32_t runtime_address = 0U;
    if (find_unique_relocation_operand(candidate, relocation, &operand_index) &&
        operand_index < instruction->operand_count) {
      operand = &instruction->operands[operand_index];
      if (operand_absolute_offset_local(operand, &absolute) && absolute == relocation->target_offset &&
          lookup_source_should_render_runtime_label(lookup, relocation->target_section_index,
            relocation->target_offset, &runtime_address)) {
        attach_operand_storage_label_symbol(lookup, instruction, operand_index, relocation->target_section_index,
          relocation->target_offset);
      } else {
        attach_operand_label_symbol(lookup, instruction, operand_index, source_section_index, candidate->offset,
          relocation->target_section_index, relocation->target_offset);
      }
      return 1;
    }
  }
  return 0;
}

static int attach_proven_instruction_relocations(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    size_t section_index, const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  uint32_t offset;
  uint32_t end;
  int ok = 1;
  if (preview == NULL || lookup == NULL || candidate == NULL || instruction == NULL) return 0;
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset; offset < end; ++offset) {
    const M68kFact *fact = lookup_relocation_at(lookup, section_index, offset);
    if (fact == NULL) continue;
    if (!instruction_relocation_is_proven_operand(lookup, section_index, candidate, fact, instruction)) {
      ++preview->asm_source_instruction_relocation_failures;
      record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_INSTRUCTION_RELOCATION,
        section_index, candidate->offset, fact->offset);
      ok = 0;
    }
  }
  return ok;
}

static const M68kFact *first_anchor_in_candidate(const M68kRenderLookup *lookup, size_t section_index,
    const M68kDecodeCandidate *candidate, uint32_t *out_count) {
  uint32_t offset;
  uint32_t end;
  const M68kFact *first = NULL;
  uint32_t count = 0U;
  if (out_count != NULL) *out_count = 0U;
  if (lookup == NULL || candidate == NULL) return NULL;
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset; offset < end; ++offset) {
    const M68kFact *anchor = lookup_anchor_at(lookup, section_index, offset);
    if (anchor == NULL) continue;
    if (first == NULL) first = anchor;
    ++count;
  }
  if (out_count != NULL) *out_count = count;
  return first;
}

static int instruction_loads_immediate_to_register(const M68kInstructionIR *instruction, uint8_t *out_reg_kind,
    uint8_t *out_reg_index, uint32_t *out_value) {
  uint32_t value = 0U;
  uint8_t reg = 0U;
  if (out_reg_kind != NULL) *out_reg_kind = 0U;
  if (out_reg_index != NULL) *out_reg_index = 0U;
  if (out_value != NULL) *out_value = 0U;
  if (instruction == NULL || instruction->operand_count != 2U ||
      !operand_is_immediate_value_local(&instruction->operands[0], &value)) {
    return 0;
  }
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEQ) {
    return 0;
  }
  if (operand_is_data_register_local(&instruction->operands[1], &reg)) {
    if (out_reg_kind != NULL) *out_reg_kind = 1U;
  } else if (operand_address_register_index_local(&instruction->operands[1], &reg)) {
    if (out_reg_kind != NULL) *out_reg_kind = 2U;
  } else {
    return 0;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ) value = (uint32_t)(int32_t)(int8_t)(value & 0xFFU);
  else if (instruction->size_suffix == 'b') value = (uint32_t)(int32_t)(int8_t)(value & 0xFFU);
  else if (instruction->size_suffix == 'w') value = (uint32_t)(int32_t)(int16_t)(value & 0xFFFFU);
  if (out_reg_index != NULL) *out_reg_index = reg;
  if (out_value != NULL) *out_value = value;
  return 1;
}

static int instruction_writes_register(const M68kInstructionIR *instruction, uint8_t reg_kind,
    uint8_t reg_index) {
  size_t operand_index;
  uint8_t reg = 0U;
  if (instruction == NULL || reg_kind == 0U || reg_index >= 8U) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count >= 2U &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
    if (reg_kind == 1U) return reglist_contains_data_register_local(&instruction->operands[1], reg_index);
    return reglist_contains_address_register_local(&instruction->operands[1], reg_index);
  }
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (!instruction_operand_writes_register_from_metadata(instruction, operand_index)) continue;
    if (reg_kind == 1U && operand_is_data_register_local(operand, &reg) && reg == reg_index) return 1;
    if (reg_kind == 2U && operand_address_register_index_local(operand, &reg) && reg == reg_index) return 1;
  }
  return 0;
}

static int attach_amiga_next_call_input_immediate_symbol(M68kRenderIRPreview *preview,
    const M68kRenderLookup *lookup, const M68kRenderPlatformState *platform_state, const M68kDecodeIR *decode,
    uint8_t **accepted_start_all, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    M68kInstructionIR *instruction) {
  M68kRenderPlatformState state;
  uint8_t reg_kind = 0U;
  uint8_t reg_index = 0U;
  uint32_t value = 0U;
  uint32_t cursor;
  size_t scan_count = 0U;
  if (preview == NULL || lookup == NULL || platform_state == NULL || decode == NULL || accepted_start_all == NULL ||
      section == NULL || candidate == NULL || instruction == NULL) {
    return 0;
  }
  if (lookup->object == NULL || lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK)
    return 0;
  if (!instruction_loads_immediate_to_register(instruction, &reg_kind, &reg_index, &value)) return 0;
  state = *platform_state;
  cursor = candidate->offset + candidate->byte_count;
  while (cursor < section->size && scan_count < 12U) {
    const M68kDecodeCandidate *next_candidate;
    M68kInstructionIR next_instruction;
    const AmigaOsLibraryVectorInfo *platform_vector;
    const AmigaOsLibraryVectorInfo *immediate_vector;
    const AmigaOsLibraryVectorInfo *wrapper_call_vector;
    const AmigaOsLibraryVectorInfo *direct_wrapper_vector;
    const AmigaOsLibraryVectorInfo *helper_call_vector;
    const AmigaOsLibraryVectorInfo *vector;
    const AmigaOsCallInputInfo *input;
    const char *value_domain_name;
    char symbol_expr[M68K_IR_SYMBOL_NAME_SIZE];
    if (!accepted_start_at(section, accepted_start_all[section->section_index], cursor)) break;
    next_candidate = find_candidate_at_offset_local(section, cursor);
    if (next_candidate == NULL || next_candidate->byte_count == 0U) break;
    platform_state_apply_policy_register_seeds(&state, lookup->policy, section->section_index, cursor);
    if (m68k_decode_candidate_to_instruction(next_candidate, &next_instruction) != 0) break;
    attach_known_instruction_relocations(lookup, section->section_index, next_candidate, &next_instruction);
    platform_vector = attach_amiga_lvo_symbol_if_known(&state, &next_instruction);
    immediate_vector = attach_amiga_lvo_immediate_if_known(lookup, section,
      accepted_start_all[section->section_index], next_candidate, &next_instruction);
    wrapper_call_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &state, section, next_candidate);
    direct_wrapper_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start_all,
      section->section_index, next_candidate);
    helper_call_vector = (platform_vector == NULL && immediate_vector == NULL && wrapper_call_vector == NULL &&
      direct_wrapper_vector == NULL)
      ? resolve_amiga_local_helper_call_vector(lookup, decode, accepted_start_all, section->section_index,
          next_candidate)
      : NULL;
    vector = platform_vector != NULL ? platform_vector :
      (direct_wrapper_vector != NULL ? direct_wrapper_vector :
      (wrapper_call_vector != NULL ? wrapper_call_vector :
      (immediate_vector != NULL ? immediate_vector : helper_call_vector)));
    if (vector != NULL) {
      input = amiga_vector_input_by_register(vector, reg_kind, reg_index);
      if (input == NULL) return 0;
      value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, input->value_domain_id);
      if (value_domain_name == NULL ||
          !amiga_value_domain_symbolic_expr(value_domain_name, value, symbol_expr, sizeof(symbol_expr))) {
        return 0;
      }
      if (!render_asm_include_for_symbol_expr(preview, symbol_expr)) {
        ++preview->asm_source_instruction_render_failures;
        record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, section->section_index,
          candidate->offset, 0U);
        return -1;
      }
      m68k_ir_symbol_ref_init(&instruction->operands[0].symbol_ref);
      instruction->operands[0].symbol_ref.has_name = 1U;
      instruction->operands[0].symbol_ref.name_is_generated = 0U;
      instruction->operands[0].symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
      instruction->operands[0].symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
      snprintf(instruction->operands[0].symbol_ref.name, sizeof(instruction->operands[0].symbol_ref.name), "%s",
        symbol_expr);
      return 1;
    }
    if (instruction_writes_register(&next_instruction, reg_kind, reg_index)) break;
    if (next_candidate->mnemonic_id == M68K_ASM_MNEMONIC_BSR ||
        next_candidate->mnemonic_id == M68K_ASM_MNEMONIC_JSR) {
      break;
    }
    platform_state_update_d0_lvo_after_instruction(&state, &next_instruction);
    platform_state_update_after_instruction(&state, lookup, &next_instruction);
    if (!candidate_has_local_helper_summary_fallthrough(next_candidate)) break;
    cursor += next_candidate->byte_count;
    ++scan_count;
  }
  return 0;
}

static void record_facts_v2_platform_call(M68kRenderIRPreview *preview,
    M68kSectionAnalysisIR *section_analysis, uint32_t offset,
    const PlatformFactsV2ResolvedCall *call_info) {
  if (preview == NULL || call_info == NULL || call_info->platform_kind == 0U) return;
  ++preview->platform_call_count;
  if (section_analysis == NULL) return;
  if (m68k_ir_section_analysis_append_recovered_platform_call(section_analysis, call_info->platform_kind,
      offset, call_info->kind, NULL, call_info->note_kind,
      call_info->note_base_name[0] != '\0' ? call_info->note_base_name : NULL,
      call_info->note_symbol_name[0] != '\0' ? call_info->note_symbol_name : NULL,
      0U, INT16_MIN, INT16_MIN, call_info->note_stack_cleanup_known,
      call_info->note_stack_cleanup_bytes, call_info->note_return_kind, NULL, NULL) != 0) {
    preview->asm_source_allocation_failed = 1U;
  }
}

static int record_platform_trap_call_for_render(M68kRenderIRPreview *preview,
    const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kDecodeCandidate *candidate, M68kSectionAnalysisIR *section_analysis) {
  PlatformFactsV2ResolvedCall call_info;
  uint32_t block_start;
  if (preview == NULL || lookup == NULL || lookup->object == NULL || section == NULL || candidate == NULL)
    return 0;
  block_start = lookup_code_block_start_before_or_at(lookup, section->section_index, candidate->offset);
  if (!platform_facts_v2_resolve_trap_call(lookup->object->platform_backend_kind, section, accepted_start,
      block_start, candidate->offset, &call_info)) {
    return 0;
  }
  record_facts_v2_platform_call(preview, section_analysis, candidate->offset, &call_info);
  return 1;
}

static void attach_platform_stack_cleanup_comment_for_render(M68kRenderIRPreview *preview,
    const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction,
    M68kSectionAnalysisIR *section_analysis, char *comment, size_t comment_size) {
  PlatformFactsV2ResolvedCall call_info;
  uint32_t block_start;
  char note[160];
  if (preview == NULL || lookup == NULL || lookup->object == NULL || section == NULL || accepted_start == NULL ||
      candidate == NULL || instruction == NULL || comment == NULL || comment_size == 0U) {
    return;
  }
  block_start = lookup_code_block_start_before_or_at(lookup, section->section_index, candidate->offset);
  if (!platform_facts_v2_resolve_stack_cleanup_call(lookup->object->platform_backend_kind, section,
      accepted_start, block_start, candidate->offset, instruction, &call_info)) {
    return;
  }
  if (call_info.note_symbol_name[0] == '\0') return;
  snprintf(note, sizeof(note), "KNOWN: stack cleanup for %s pop %u", call_info.note_symbol_name,
    (unsigned)call_info.note_stack_cleanup_bytes);
  (void)append_comment_part_local(comment, comment_size, note);
  record_facts_v2_platform_call(preview, section_analysis, candidate->offset, &call_info);
}

static void attach_amiga_hardware_display_comment_for_render(const M68kRenderPlatformState *state,
    const M68kInstructionIR *instruction, char *comment, size_t comment_size) {
  const M68kSimFormMetadata *metadata;
  const AmigaOsHardwareRegisterInfo *hardware_register;
  const AmigaOsHardwareRegisterFieldInfo *hardware_field;
  uint32_t value = 0U;
  uint8_t source_index = 0xFFU;
  uint8_t dest_index = 0xFFU;
  uint8_t operand_index;
  char note[160];
  if (instruction == NULL || comment == NULL || comment_size == 0U) return;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_WRITE) {
      dest_index = operand_index;
      break;
    }
  }
  if (dest_index >= instruction->operand_count) return;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    if (operand_index == dest_index) continue;
    if (operand_is_immediate_value_local(&instruction->operands[operand_index], &value)) {
      source_index = operand_index;
      break;
    }
  }
  if (source_index >= instruction->operand_count) return;
  hardware_register = resolve_amiga_hardware_register_operand(state, &instruction->operands[dest_index]);
  if (!format_amiga_display_register_comment(hardware_register,
      immediate_domain_value_for_instruction_size(instruction, value), note, sizeof(note))) {
    if (!format_amiga_disk_dma_register_comment(hardware_register,
        immediate_domain_value_for_instruction_size(instruction, value), note, sizeof(note))) {
      hardware_field = resolve_amiga_hardware_register_field_operand(state, &instruction->operands[dest_index]);
      if (!format_amiga_audio_register_comment(hardware_field,
          immediate_domain_value_for_instruction_size(instruction, value), note, sizeof(note))) {
        return;
      }
    }
  }
  (void)append_comment_part_local(comment, comment_size, note);
}

static void attach_amiga_hardware_access_comment_for_render(const M68kRenderPlatformState *state,
    const M68kInstructionIR *instruction, char *comment, size_t comment_size) {
  const M68kSimFormMetadata *metadata;
  const AmigaOsHardwareRegisterInfo *hardware_register;
  const AmigaOsHardwareRegisterFieldInfo *hardware_field;
  const AmigaOsHardwareRegisterRangeInfo *hardware_range;
  uint32_t range_offset = 0U;
  uint8_t access_pass;
  uint8_t operand_index;
  char note[160];
  if (instruction == NULL || comment == NULL || comment_size == 0U) return;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return;
  for (access_pass = 0U; access_pass < 2U; ++access_pass) {
    uint8_t wanted_access = access_pass == 0U ? M68K_SIM_ACCESS_MEMORY_WRITE : M68K_SIM_ACCESS_MEMORY_READ;
    for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
      uint8_t access_kind = metadata->operand_access_kinds[operand_index];
      uint8_t source_index;
      if (access_kind != wanted_access) continue;
      if (access_kind == M68K_SIM_ACCESS_MEMORY_WRITE) {
        int has_immediate_source = 0;
        for (source_index = 0U; source_index < instruction->operand_count; ++source_index) {
          uint32_t value = 0U;
          if (source_index != operand_index &&
              operand_is_immediate_value_local(&instruction->operands[source_index], &value)) {
            has_immediate_source = 1;
            break;
          }
        }
        if (has_immediate_source) continue;
      }
      hardware_register = resolve_amiga_hardware_register_operand(state, &instruction->operands[operand_index]);
      if (!format_amiga_hardware_register_access_comment(hardware_register, access_kind, note, sizeof(note))) {
        hardware_field = resolve_amiga_hardware_register_field_operand(state, &instruction->operands[operand_index]);
        if (!format_amiga_audio_register_access_comment(hardware_field, note, sizeof(note))) {
          hardware_range = resolve_amiga_hardware_register_range_operand(state, &instruction->operands[operand_index],
            &range_offset);
          if (!format_amiga_hardware_range_access_comment(hardware_range, range_offset, access_kind,
              byte_width_for_instruction_size(instruction), note, sizeof(note))) {
            continue;
          }
        }
      }
      (void)append_comment_part_local(comment, comment_size, note);
      return;
    }
  }
}

static void attach_amiga_runtime_sink_comment_for_render(const M68kRenderPlatformState *state,
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset, const M68kInstructionIR *instruction,
    char *comment, size_t comment_size) {
  const M68kSimFormMetadata *metadata;
  const AmigaOsHardwareRegisterInfo *hardware_register;
  const M68kFact *external_ref;
  uint8_t dest_index = 0xFFU;
  uint8_t operand_index;
  char note[160];
  if (instruction == NULL || comment == NULL || comment_size == 0U) return;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_WRITE) {
      dest_index = operand_index;
      break;
    }
  }
  if (dest_index >= instruction->operand_count) return;
  hardware_register = resolve_amiga_hardware_register_operand(state, &instruction->operands[dest_index]);
  if (hardware_register == NULL ||
      (hardware_register->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) == 0U ||
      hardware_register->runtime_target_role == NULL || hardware_register->runtime_target_role[0] == '\0') {
    return;
  }
  external_ref = lookup_external_runtime_address_ref_for_instruction(lookup, section_index, offset);
  if (external_ref != NULL) {
    snprintf(note, sizeof(note), "%s pointer $%08X", hardware_register->runtime_target_role,
      (unsigned)external_ref->runtime_address);
  } else {
    snprintf(note, sizeof(note), "%s pointer", hardware_register->runtime_target_role);
  }
  (void)append_comment_part_local(comment, comment_size, note);
}

static int amiga_vector_is_open_library_result(const AmigaOsLibraryVectorInfo *vector) {
  const char *symbol_name;
  if (vector == NULL) return 0;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, vector->lvo_symbol_id);
  return symbol_name != NULL &&
    (strcmp(symbol_name, "_LVOOpenLibrary") == 0 || strcmp(symbol_name, "_LVOOldOpenLibrary") == 0);
}

static int render_asm_instruction(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    M68kRenderPlatformState *platform_state, const M68kDecodeIR *decode, uint8_t **accepted_start_all,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const M68kDecodeCandidate *candidate,
    M68kSectionAnalysisIR *section_analysis, M68kInstructionIR *out_listing_instruction) {
  M68kInstructionIR instruction;
  M68kInstructionIR render_instruction;
  M68kRenderPolicy policy;
  M68kDiagList render_diagnostics;
  M68kDiagList encode_diagnostics;
  M68kIrRenderResult rendered;
  M68kIrEncodeResult encoded;
  const AmigaOsLibraryVectorInfo *platform_vector = NULL;
  const AmigaOsLibraryVectorInfo *immediate_vector = NULL;
  const AmigaOsLibraryVectorInfo *wrapper_call_vector = NULL;
  const AmigaOsLibraryVectorInfo *direct_wrapper_vector = NULL;
  const AmigaOsLibraryVectorInfo *helper_call_vector = NULL;
  const AmigaOsLibraryVectorInfo *chosen_vector = NULL;
  uint8_t chosen_kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL;
  uint8_t chosen_note_kind = M68K_PLATFORM_CALL_NOTE_NONE;
  uint8_t encoded_bytes[32];
  char platform_comment[160];
  char instruction_comment[640];
  char line[1024];
  if (preview == NULL || lookup == NULL || section == NULL || candidate == NULL) return 0;
  platform_comment[0] = '\0';
  instruction_comment[0] = '\0';
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, section->section_index,
      candidate->offset, 0U);
    return 0;
  }
  if (attach_symbolic_targets(lookup, section->section_index, candidate, &instruction) != 0 ||
      !attach_proven_instruction_relocations(preview, lookup, section->section_index, candidate, &instruction)) {
    return 0;
  }
  (void)attach_absolute_word_control_symbols(lookup, section->section_index, candidate, &instruction);
  (void)attach_platform_pc_relative_synthetic_symbols(lookup, section->section_index, candidate, &instruction);
  if (!attach_runtime_address_ref_symbols(preview, lookup, section->section_index, candidate, &instruction)) return 0;
  platform_vector = attach_amiga_lvo_symbol_if_known(platform_state, &instruction);
  immediate_vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start, candidate, &instruction);
  wrapper_call_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, platform_state, section, candidate);
  direct_wrapper_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start_all,
    section->section_index, candidate);
  (void)record_platform_trap_call_for_render(preview, lookup, section, accepted_start, candidate, section_analysis);
  if (platform_vector == NULL && immediate_vector == NULL && wrapper_call_vector == NULL &&
      direct_wrapper_vector == NULL) {
    helper_call_vector = resolve_amiga_local_helper_call_vector(lookup, decode, accepted_start_all,
      section->section_index, candidate);
  }
  if (attach_amiga_next_call_input_immediate_symbol(preview, lookup, platform_state, decode, accepted_start_all,
      section, candidate, &instruction) < 0) {
    return 0;
  }
  attach_amiga_hardware_display_comment_for_render(platform_state, &instruction, platform_comment,
    sizeof(platform_comment));
  attach_amiga_hardware_access_comment_for_render(platform_state, &instruction, platform_comment,
    sizeof(platform_comment));
  (void)attach_amiga_hardware_register_symbols(platform_state, &instruction, &instruction);
  (void)attach_amiga_hardware_register_immediate_symbols(platform_state, &instruction);
  (void)attach_absolute_stack_top_symbol(preview, &instruction);
  (void)attach_amiga_app_base_slot_symbols(lookup, platform_state, &instruction);
  (void)attach_amiga_typed_struct_field_symbols(lookup, section->section_index, candidate->offset, &instruction);
  (void)attach_m68k_cpu_vector_symbols(lookup, &instruction);
  if (!render_asm_include_for_instruction_platform_symbols(preview, &instruction)) return 0;
  attach_amiga_runtime_sink_comment_for_render(platform_state, lookup, section->section_index, candidate->offset,
    &instruction, platform_comment, sizeof(platform_comment));
  attach_platform_stack_cleanup_comment_for_render(preview, lookup, section, accepted_start, candidate, &instruction,
    section_analysis, platform_comment, sizeof(platform_comment));
  (void)append_comment_part_local(instruction_comment, sizeof(instruction_comment),
    lookup_instruction_comment(lookup, section->section_index, candidate->offset));
  (void)append_comment_part_local(instruction_comment, sizeof(instruction_comment), platform_comment);
  apply_exact_byte_immediate_render_values(&instruction, section->data + candidate->offset, candidate->byte_count);
  render_instruction = instruction;
  if (m68k_instruction_is_fpu_id_alias_instruction(&instruction) &&
      !m68k_instruction_make_fpu_id_render_instruction(&instruction, &render_instruction)) {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, section->section_index,
      candidate->offset, 0U);
    return 0;
  }
  m68k_render_policy_init_default(&policy);
  m68k_diag_list_reset(&render_diagnostics);
  rendered = m68k_ir_render_one_at_with_policy(&render_instruction, candidate->offset, &policy,
    m68k_diag_sink(&render_diagnostics));
  if (m68k_diag_has_errors(&render_diagnostics) || rendered.text[0] == '\0') {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, section->section_index,
      candidate->offset, 0U);
    return 0;
  }
  m68k_diag_list_reset(&encode_diagnostics);
  encoded = m68k_ir_encode_one(&instruction, encoded_bytes, sizeof(encoded_bytes), m68k_diag_sink(&encode_diagnostics));
  if (m68k_diag_has_errors(&encode_diagnostics) || encoded.byte_count != candidate->byte_count ||
      !encoded_bytes_match_with_exact_byte_immediates(&instruction, encoded_bytes, section->data + candidate->offset,
        candidate->byte_count)) {
    ++preview->asm_source_instruction_byte_mismatches;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_BYTE_MISMATCH, section->section_index,
      candidate->offset, 0U);
    return 0;
  }
  if (!rendered_text_reencodes_original_bytes(rendered.text, &instruction, &render_instruction, section->data + candidate->offset,
      candidate->byte_count)) {
    ++preview->asm_source_instruction_byte_mismatches;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_BYTE_MISMATCH, section->section_index,
      candidate->offset, 0U);
    return 0;
  }
  {
    uint32_t anchor_count = 0U;
    const M68kFact *anchor = first_anchor_in_candidate(lookup, section->section_index, candidate, &anchor_count);
    if (anchor != NULL) {
      char comment[384];
      format_lossy_hunk_anchor_comment(comment, sizeof(comment), lookup, anchor);
      if (anchor_count > 1U) {
        char count_suffix[64];
        snprintf(count_suffix, sizeof(count_suffix), "; %u lossy hunk relocations in instruction",
          (unsigned)anchor_count);
        strncat(comment, count_suffix, sizeof(comment) - strlen(comment) - 1U);
      }
      if (instruction_comment[0] != '\0') {
        snprintf(line, sizeof(line), "\t%s\t; %s; %s\n", rendered.text, instruction_comment, comment);
      } else {
        snprintf(line, sizeof(line), "\t%s\t; %s\n", rendered.text, comment);
      }
      preview->asm_source_lossy_numeric_hunk_relocations += anchor_count;
    } else if (instruction_comment[0] != '\0') {
      snprintf(line, sizeof(line), "\t%s\t; %s\n", rendered.text, instruction_comment);
    } else {
      snprintf(line, sizeof(line), "\t%s\n", rendered.text);
    }
    if (m68k_instruction_needs_fpu_id_directive(&instruction)) {
      char scoped_line[1200];
      snprintf(scoped_line, sizeof(scoped_line), "\tFPU     %u\n%s\tFPU     1\n",
        (unsigned)instruction.coprocessor_id, line);
      snprintf(line, sizeof(line), "%s", scoped_line);
      preview->asm_source_lines += 2U;
    }
  }
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  ++preview->asm_source_symbolic_instructions;
  if (out_listing_instruction != NULL) *out_listing_instruction = render_instruction;
  chosen_vector = platform_vector != NULL ? platform_vector :
    (direct_wrapper_vector != NULL ? direct_wrapper_vector :
    (wrapper_call_vector != NULL ? wrapper_call_vector :
    (immediate_vector != NULL ? immediate_vector : helper_call_vector)));
  if (wrapper_call_vector != NULL) {
    chosen_kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH;
    chosen_note_kind = M68K_PLATFORM_CALL_NOTE_INDEXED_VECTOR;
  } else if (direct_wrapper_vector != NULL || helper_call_vector != NULL) {
    chosen_note_kind = M68K_PLATFORM_CALL_NOTE_LOCAL_WRAPPER_SYMBOL;
  }
  preview_record_platform_vector_call(preview, lookup, section_analysis, candidate->offset, chosen_kind,
    chosen_note_kind, chosen_vector);
  platform_state_update_d0_lvo_after_instruction(platform_state, &instruction);
  platform_state_update_after_instruction(platform_state, lookup, &instruction);
  {
    uint8_t loaded_address_reg = 0U;
    char loaded_library_name[64];
    if (candidate_lea_known_amiga_name_to_address_reg(lookup, section, candidate, &loaded_address_reg,
        loaded_library_name, sizeof(loaded_library_name))) {
      platform_state_set_register_library(platform_state, loaded_address_reg, loaded_library_name);
    }
  }
  if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_JSR ||
      instruction.mnemonic_id == M68K_ASM_MNEMONIC_BSR) {
    platform_state_note_call_result_after_instruction(platform_state, &instruction, chosen_vector);
  }
  return 1;
}

void m68k_render_ir_preview_init(M68kRenderIRPreview *preview) {
  if (preview == NULL) return;
  memset(preview, 0, sizeof(*preview));
  preview->structural_hash = 1469598103934665603ULL;
  preview->text_hash = 1469598103934665603ULL;
  preview->asm_source_hash = 1469598103934665603ULL;
  m68k_render_plan_init(&preview->asm_source_plan);
  m68k_render_plan_row_builder_init(&preview->asm_source_row_builder);
}

void m68k_render_ir_preview_destroy(M68kRenderIRPreview *preview) {
  if (preview == NULL) return;
  arena_destroy(preview->asm_source_header_arena);
  arena_destroy(preview->scratch_arena);
  free(preview->asm_source_text);
  m68k_render_plan_row_builder_destroy(&preview->asm_source_row_builder);
  m68k_render_plan_destroy(&preview->asm_source_plan);
  memset(preview, 0, sizeof(*preview));
}

int m68k_render_ir_preview_build(const M68kObject *object, const M68kDecodeIR *decode, const M68kFactIR *facts,
    const M68kAnalysisPolicy *policy, uint8_t **accepted_start, uint8_t **accepted_bytes, int render_text_preview,
    int render_asm_source, int collect_asm_source_text, int emit_asm_source_text,
    M68kRenderIRPreview *out_preview, M68kSourceAnalysisIR *out_source_analysis) {
  size_t section_index;
  clock_t phase_start;
  clock_t phase_end;
  M68kRenderLookup lookup;
  M68kRenderPlatformState platform_state;
  M68kSectionAnalysisIR section_analysis;
  Arena *scratch_arena = NULL;
  int section_analysis_live = 0;
  int build_source_analysis = out_source_analysis != NULL;
  int build_platform_analysis = render_asm_source || build_source_analysis;
  int result = -1;
  if (decode == NULL || facts == NULL || accepted_start == NULL || accepted_bytes == NULL || out_preview == NULL)
    return -1;
  memset(&lookup, 0, sizeof(lookup));
  memset(&platform_state, 0, sizeof(platform_state));
  memset(&section_analysis, 0, sizeof(section_analysis));
  m68k_render_ir_preview_init(out_preview);
  out_preview->platform_backend_kind = object->platform_backend_kind;
  if (out_source_analysis != NULL) {
    if (m68k_ir_source_analysis_create(out_source_analysis) != 0) goto cleanup;
    out_source_analysis->file_kind = object->platform_file_kind;
    if (policy != NULL) out_source_analysis->policy = *policy;
  }
  phase_start = clock();
  if (render_lookup_build(&lookup, object, decode, facts, policy) != 0) goto cleanup;
  phase_end = clock();
  out_preview->lookup_seconds = elapsed_seconds_local(phase_start, phase_end);
  phase_start = clock();
  if (build_platform_analysis &&
      m68k_analysis_render_lookup_run_platform_passes(&lookup, decode, accepted_start, accepted_bytes,
        out_preview) != 0) {
    goto cleanup;
  }
  phase_end = clock();
  out_preview->platform_pass_seconds = elapsed_seconds_local(phase_start, phase_end);
  if (out_source_analysis != NULL &&
      m68k_analysis_render_lookup_append_auto_policy(out_source_analysis, &lookup) != 0) {
    goto cleanup;
  }
  if (render_asm_source) {
    out_preview->platform_base_slot_count = (uint32_t)(lookup.global_base_slot_count + lookup.base_field_slot_count);
  }
  out_preview->collect_asm_source_text = render_asm_source && collect_asm_source_text ? 1U : 0U;
  out_preview->collect_asm_source_hash = out_preview->collect_asm_source_text;
  phase_start = clock();
  if (render_asm_source) {
    begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_PLATFORM_DIRECTIVE, 0U);
    render_asm_platform_header(out_preview, object);
    finish_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_NO_SECTION, 0U, 0U, 0);
    begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_RSSET, 0U);
    render_asm_app_extension_rs(out_preview, &lookup, decode);
    finish_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_NO_SECTION, 0U, 0U, 0);
    out_preview->asm_source_body_start_byte = out_preview->asm_source_bytes;
  }
  phase_end = clock();
  out_preview->header_seconds = elapsed_seconds_local(phase_start, phase_end);
  phase_start = clock();
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kSectionAnalysisIR *current_section_analysis = NULL;
    uint32_t offset = 0U;
    uint32_t asm_logical_pc = 0U;
    uint32_t render_extent = render_section_extent(section);
    size_t render_candidate_index = 0U;
    out_preview->structural_hash = hash_step(out_preview->structural_hash, section_index);
    out_preview->structural_hash = hash_step(out_preview->structural_hash, render_extent);
    if (out_source_analysis != NULL) {
      if (m68k_ir_section_analysis_create(&section_analysis) != 0) goto cleanup;
      section_analysis_live = 1;
      section_analysis.section_index = section->section_index;
      section_analysis.section_kind = section->kind;
      section_analysis.section_size = section->allocation_size != 0U ? section->allocation_size : section->size;
      if (m68k_ir_section_analysis_set_name(&section_analysis, section->name) != 0 ||
          m68k_ir_section_analysis_set_code_map(&section_analysis, accepted_start[section_index],
            accepted_bytes[section_index], section->size) != 0) {
        goto cleanup;
      }
      if (m68k_analysis_render_lookup_append_section(&lookup, decode, &section_analysis) != 0) goto cleanup;
      current_section_analysis = &section_analysis;
    }
    if (render_asm_source) {
      begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_SECTION, (uint32_t)section_index);
      render_asm_section_header(out_preview, decode, section_index);
      finish_asm_source_plan_row(out_preview, section->section_index, 0U, 0U, 1);
    }
    while (offset < render_extent) {
      if (render_asm_source) {
        platform_state_apply_policy_register_seeds(&platform_state, policy, section->section_index, offset);
        begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_DIAGNOSTIC, (uint32_t)section_index);
        render_asm_policy_entry_comments(out_preview, policy, section->section_index, offset);
        render_asm_policy_register_seed_comment(out_preview, policy, section->section_index, offset);
        finish_asm_source_plan_row(out_preview, section->section_index, offset, 0U, 1);
      }
      if (lookup_has_renderable_label(&lookup, section->section_index, offset)) {
        ++out_preview->statement_count;
        ++out_preview->label_statement_count;
        hash_statement(out_preview, 'L', section->section_index, offset, 0U, 0U);
        if (current_section_analysis != NULL &&
            m68k_ir_section_analysis_add_label(current_section_analysis, offset) != 0) {
          goto cleanup;
        }
        if (render_text_preview) render_text_line(out_preview, 'L', section->section_index, offset, 0U, 0U);
        if (render_asm_source) {
          M68kRenderPlanRow *row;
          begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_LABEL, (uint32_t)section_index);
          render_asm_label(out_preview, &lookup, section->section_index, offset, &asm_logical_pc);
          row = finish_asm_source_plan_row(out_preview, section->section_index, offset, 0U, 1);
          set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_LABEL, NULL, section, offset, 0U);
        }
      }
      if (accepted_start_at(section, accepted_start[section_index], offset)) {
        const M68kDecodeCandidate *candidate = NULL;
        while (render_candidate_index < section->candidate_count &&
            section->candidates[render_candidate_index].offset < offset) {
          ++render_candidate_index;
        }
        if (render_candidate_index < section->candidate_count &&
            section->candidates[render_candidate_index].offset == offset) {
          candidate = &section->candidates[render_candidate_index];
        }
        if (candidate == NULL || candidate->byte_count == 0U) goto cleanup;
        ++out_preview->statement_count;
        ++out_preview->instruction_statement_count;
        hash_statement(out_preview, 'I', section->section_index, offset, candidate->byte_count,
          candidate->mnemonic_id);
        if (render_text_preview) render_text_line(out_preview, 'I', section->section_index, offset,
          candidate->byte_count, candidate->mnemonic_id);
        if (render_asm_source) {
          M68kRenderPlanRow *row;
          M68kInstructionIR listing_instruction;
          int rendered_instruction;
          m68k_ir_instruction_init(&listing_instruction);
          begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_INSTRUCTION, (uint32_t)section_index);
          render_asm_sync_logical_pc(out_preview, &lookup, section->section_index, offset, &asm_logical_pc);
          rendered_instruction = render_asm_instruction(out_preview, &lookup, &platform_state, decode,
            accepted_start, section, accepted_start[section_index], candidate, current_section_analysis,
            &listing_instruction);
          row = finish_asm_source_plan_row(out_preview, section->section_index, offset, candidate->byte_count, 1);
          if (rendered_instruction) {
            set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_INSTRUCTION, &listing_instruction,
              section, offset, candidate->byte_count);
          }
          asm_logical_pc += candidate->byte_count;
        }
        offset += candidate->byte_count;
      } else {
        const M68kFact *anchor = lookup_anchor_at(&lookup, section->section_index, offset);
        const M68kFact *relocation = lookup_relocation_at(&lookup, section->section_index, offset);
        if (anchor != NULL && offset + anchor->size <= section->size &&
            !accepted_byte_at(section, accepted_bytes[section_index], offset)) {
          ++out_preview->statement_count;
          ++out_preview->data_statement_count;
          hash_statement(out_preview, 'A', section->section_index, offset, anchor->size,
            (uint32_t)anchor->target_section_index ^ anchor->target_offset);
          if (render_text_preview) render_text_line(out_preview, 'A', section->section_index, offset,
            anchor->size, anchor->target_offset);
          if (render_asm_source) {
            M68kRenderPlanRow *row;
            begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_DATA, (uint32_t)section_index);
            render_asm_sync_logical_pc(out_preview, &lookup, section->section_index, offset, &asm_logical_pc);
            render_asm_comment_line(out_preview,
              lookup_instruction_comment(&lookup, section->section_index, offset));
            render_asm_lossy_hunk_relocation(out_preview, &lookup, anchor);
            row = finish_asm_source_plan_row(out_preview, section->section_index, offset, anchor->size, 1);
            set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_DATA, NULL, section, offset,
              anchor->size);
            asm_logical_pc += anchor->size;
          }
          offset += anchor->size;
        } else if (relocation != NULL && offset + relocation->size <= section->size &&
            !accepted_byte_at(section, accepted_bytes[section_index], offset)) {
          ++out_preview->statement_count;
          ++out_preview->data_statement_count;
          hash_statement(out_preview, 'R', section->section_index, offset, relocation->size,
            (uint32_t)relocation->target_section_index ^ relocation->target_offset);
          if (render_text_preview) render_text_line(out_preview, 'R', section->section_index, offset,
            relocation->size, relocation->target_offset);
          if (render_asm_source) {
            M68kRenderPlanRow *row;
            begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_DATA, (uint32_t)section_index);
            render_asm_sync_logical_pc(out_preview, &lookup, section->section_index, offset, &asm_logical_pc);
            render_asm_comment_line(out_preview,
              lookup_instruction_comment(&lookup, section->section_index, offset));
            render_asm_relocation_expr(out_preview, &lookup, relocation);
            row = finish_asm_source_plan_row(out_preview, section->section_index, offset, relocation->size, 1);
            set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_DATA, NULL, section, offset,
              relocation->size);
            asm_logical_pc += relocation->size;
          }
          offset += relocation->size;
        } else {
          const M68kAnalysisStructuredDataItem *structured_item =
            lookup_structured_data_item_at_offset(&lookup, section->section_index, offset);
          int structured_item_clear = structured_item != NULL && structured_item->size != 0U &&
            structured_item->size <= render_extent - offset &&
            !accepted_byte_at(section, accepted_bytes[section_index], offset);
          if (structured_item_clear) {
            uint32_t probe;
            for (probe = offset + 1U; probe < offset + structured_item->size; ++probe) {
              int internal_copper_label =
                structured_data_item_is_copper_list(structured_item) &&
                lookup_has_renderable_label(&lookup, section->section_index, probe) &&
                ((probe - structured_item->offset) % 2U) == 0U;
              int internal_palette_label =
                structured_data_item_is_palette(structured_item) &&
                lookup_has_renderable_label(&lookup, section->section_index, probe) &&
                ((probe - structured_item->offset) % 2U) == 0U;
              if (accepted_byte_at(section, accepted_bytes[section_index], probe) ||
                  (!internal_copper_label && !internal_palette_label &&
                   lookup_has_renderable_label(&lookup, section->section_index, probe)) ||
                  lookup_relocation_at(&lookup, section->section_index, probe) != NULL ||
                  lookup_anchor_at(&lookup, section->section_index, probe) != NULL ||
                  lookup_string_span_at_offset(&lookup, section->section_index, probe) != NULL ||
                  lookup_has_structured_data_item_at_offset(&lookup, section->section_index, probe)) {
                structured_item_clear = 0;
                break;
              }
            }
          }
          if (structured_item != NULL && structured_item_clear) {
            ++out_preview->statement_count;
            ++out_preview->data_statement_count;
            hash_statement(out_preview, 'S', section->section_index, offset, structured_item->size,
              structured_item->kind);
            if (render_text_preview) render_text_line(out_preview, 'S', section->section_index, offset,
              structured_item->size, structured_item->kind);
            if (render_asm_source) {
              M68kRenderPlanRow *row;
              int structured_item_updated_pc = 0;
              begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_DATA, (uint32_t)section_index);
              render_asm_sync_logical_pc(out_preview, &lookup, section->section_index, offset, &asm_logical_pc);
              render_asm_comment_line(out_preview,
                lookup_instruction_comment(&lookup, section->section_index, offset));
              render_asm_structured_data_item(out_preview, section, &lookup, structured_item, &asm_logical_pc,
                &structured_item_updated_pc);
              row = finish_asm_source_plan_row(out_preview, section->section_index, offset, structured_item->size,
                1);
              set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_DATA, NULL, section, offset,
                structured_item->size);
              if (!structured_item_updated_pc) asm_logical_pc += structured_item->size;
            }
            offset += structured_item->size;
          } else {
            const M68kRenderStringSpan *string_span =
              lookup_string_span_at_offset(&lookup, section->section_index, offset);
            int string_span_clear = string_span != NULL && string_span->size != 0U &&
              string_span->size <= render_extent - offset && offset + string_span->size <= section->size &&
              section->data != NULL && !accepted_byte_at(section, accepted_bytes[section_index], offset);
            if (string_span_clear) {
              uint32_t probe;
              for (probe = offset + 1U; probe < offset + string_span->size; ++probe) {
                if (accepted_byte_at(section, accepted_bytes[section_index], probe) ||
                    lookup_has_renderable_label(&lookup, section->section_index, probe) ||
                    lookup_relocation_at(&lookup, section->section_index, probe) != NULL ||
                    lookup_anchor_at(&lookup, section->section_index, probe) != NULL ||
                    lookup_has_structured_data_item_at_offset(&lookup, section->section_index, probe) ||
                    lookup_instruction_comment(&lookup, section->section_index, probe) != NULL) {
                  string_span_clear = 0;
                  break;
                }
              }
            }
            if (string_span != NULL && string_span_clear) {
              ++out_preview->statement_count;
              ++out_preview->data_statement_count;
              hash_statement(out_preview, 'D', section->section_index, offset, string_span->size, 0U);
              if (render_text_preview) render_text_line(out_preview, 'D', section->section_index, offset,
                string_span->size, 0U);
              if (render_asm_source) {
                M68kRenderPlanRow *row;
                begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_DATA, (uint32_t)section_index);
                render_asm_sync_logical_pc(out_preview, &lookup, section->section_index, offset, &asm_logical_pc);
                render_asm_comment_line(out_preview,
                  lookup_instruction_comment(&lookup, section->section_index, offset));
                render_asm_dc_b_string(out_preview, section->data, offset, string_span->size, NULL);
                row = finish_asm_source_plan_row(out_preview, section->section_index, offset, string_span->size, 1);
                set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_DATA, NULL, section, offset,
                  string_span->size);
                asm_logical_pc += string_span->size;
              }
              offset += string_span->size;
            } else {
              uint32_t start = offset;
              int initialized_span = section->data != NULL && start < section->size;
              while (offset < render_extent &&
                  !accepted_byte_at(section, accepted_bytes[section_index], offset) &&
                  (offset == start || !lookup_has_renderable_label(&lookup, section->section_index, offset)) &&
                  lookup_relocation_at(&lookup, section->section_index, offset) == NULL &&
                  lookup_anchor_at(&lookup, section->section_index, offset) == NULL &&
                  (offset == start ||
                   !lookup_has_structured_data_item_at_offset(&lookup, section->section_index, offset)) &&
                  (offset == start ||
                   lookup_string_span_at_offset(&lookup, section->section_index, offset) == NULL) &&
                  (offset == start ||
                   lookup_instruction_comment(&lookup, section->section_index, offset) == NULL) &&
                  ((section->data != NULL && offset < section->size) == initialized_span)) {
                ++offset;
              }
              if (offset == start) ++offset;
              else {
              ++out_preview->statement_count;
              ++out_preview->data_statement_count;
              hash_statement(out_preview, 'D', section->section_index, start, offset - start, 0U);
              if (render_text_preview) render_text_line(out_preview, 'D', section->section_index, start,
                offset - start, 0U);
              if (render_asm_source) {
                M68kRenderPlanRow *row;
                begin_asm_source_plan_row(out_preview,
                  initialized_span ? M68K_RENDER_PLAN_ROW_DATA : M68K_RENDER_PLAN_ROW_RESERVE,
                  (uint32_t)section_index);
                render_asm_sync_logical_pc(out_preview, &lookup, section->section_index, start, &asm_logical_pc);
                render_asm_comment_line(out_preview,
                  lookup_instruction_comment(&lookup, section->section_index, start));
                if (initialized_span) render_asm_dc_b(out_preview, section->data, start, offset - start, NULL);
                else render_asm_ds_best_fit(out_preview, start, offset - start);
                row = finish_asm_source_plan_row(out_preview, section->section_index, start, offset - start, 1);
                set_asm_source_plan_row_statement_from_section(row,
                  initialized_span ? M68K_STATEMENT_DATA : M68K_STATEMENT_RESERVE, NULL, section, start,
                  offset - start);
                asm_logical_pc += offset - start;
              }
              }
            }
          }
        }
      }
    }
    if (lookup_has_renderable_label(&lookup, section->section_index, render_extent)) {
      if (render_asm_source) {
        begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_DIAGNOSTIC, (uint32_t)section_index);
        render_asm_policy_entry_comments(out_preview, policy, section->section_index, render_extent);
        render_asm_policy_register_seed_comment(out_preview, policy, section->section_index, render_extent);
        finish_asm_source_plan_row(out_preview, section->section_index, render_extent, 0U, 1);
      }
      ++out_preview->statement_count;
      ++out_preview->label_statement_count;
      hash_statement(out_preview, 'L', section->section_index, render_extent, 0U, 0U);
      if (current_section_analysis != NULL &&
          m68k_ir_section_analysis_add_label(current_section_analysis, render_extent) != 0) {
        goto cleanup;
      }
      if (render_text_preview) render_text_line(out_preview, 'L', section->section_index, render_extent, 0U, 0U);
      if (render_asm_source) {
        M68kRenderPlanRow *row;
        begin_asm_source_plan_row(out_preview, M68K_RENDER_PLAN_ROW_LABEL, (uint32_t)section_index);
        render_asm_label(out_preview, &lookup, section->section_index, render_extent, &asm_logical_pc);
        row = finish_asm_source_plan_row(out_preview, section->section_index, render_extent, 0U, 1);
        set_asm_source_plan_row_statement_from_section(row, M68K_STATEMENT_LABEL, NULL, section, render_extent,
          0U);
      }
    }
    if (out_source_analysis != NULL) {
      scratch_arena = render_preview_scratch_arena(out_preview);
      if (scratch_arena == NULL) goto cleanup;
      if (render_analysis_append_cfg_for_section(&lookup, section, accepted_start[section_index],
          accepted_bytes[section_index], scratch_arena, current_section_analysis) != 0) {
        goto cleanup;
      }
      if (m68k_ir_source_analysis_append_section(out_source_analysis, current_section_analysis) != 0) goto cleanup;
      m68k_ir_section_analysis_destroy(&section_analysis);
      section_analysis_live = 0;
    } else if (section_analysis_live) {
      m68k_ir_section_analysis_destroy(&section_analysis);
      section_analysis_live = 0;
    }
  }
  phase_end = clock();
  out_preview->walk_seconds = elapsed_seconds_local(phase_start, phase_end);
  if (out_preview->asm_source_allocation_failed) goto cleanup;
  phase_start = clock();
  if (render_asm_source && collect_asm_source_text &&
      !assemble_asm_source_plan_regions(out_preview, emit_asm_source_text)) {
    out_preview->asm_source_allocation_failed = 1U;
    goto cleanup;
  }
  out_preview->asm_source_plan_rows = (uint32_t)out_preview->asm_source_plan.row_count;
  out_preview->asm_source_plan_lines = out_preview->asm_source_plan.total_lines;
  out_preview->asm_source_plan_bytes = (uint32_t)out_preview->asm_source_plan.total_bytes;
  phase_end = clock();
  out_preview->footer_seconds = elapsed_seconds_local(phase_start, phase_end);
  result = 0;
cleanup:
  if (section_analysis_live) {
    m68k_ir_section_analysis_destroy(&section_analysis);
  }
  if (result != 0 && out_source_analysis != NULL) {
    m68k_ir_source_analysis_destroy(out_source_analysis);
  }
  render_lookup_destroy(&lookup);
  return result;
}
