#include "m68k_source_file_parse.h"

#include "m68k_parse_util.h"
#include "m68k_instruction_spec.h"
#include "m68k_plain_parse.h"
#include "m68k_source_constant_expr.h"
#include "m68k_source_data.h"
#include "m68k_source_include.h"
#include "m68k_source_text_util.h"
#include "m68k_symbolic_parse.h"
#include "util_arena.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define M68K_SOURCE_PARSE_LINE_CAPACITY 8192U

typedef struct M68kSourceLineReader M68kSourceLineReader;

struct M68kSourceLineReader {
  int (*next)(M68kSourceLineReader *reader, char *buffer, size_t buffer_size);
  void (*close)(M68kSourceLineReader *reader);
  union {
    FILE *file;
    struct {
      const char *text;
      size_t offset;
    } memory;
  } u;
};

static void source_parse_error(M68kDiagSink diagnostics, const char *message) {
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PARSE_FAILED, message);
}

static void source_parse_errorf(M68kDiagSink diagnostics, const char *fmt, ...) {
  M68kDiag *diag;
  va_list args;
  if (diagnostics.list == NULL) return;
  if (diagnostics.list->count >= M68K_DIAG_LIST_CAPACITY) {
    diagnostics.list->dropped_count += 1U;
    return;
  }
  diag = &diagnostics.list->items[diagnostics.list->count++];
  memset(diag, 0, sizeof(*diag));
  diag->severity = M68K_DIAG_SEVERITY_ERROR;
  diag->code = M68K_DIAG_CODE_PARSE_FAILED;
  va_start(args, fmt);
  vsnprintf(diag->message, sizeof(diag->message), fmt, args);
  va_end(args);
}

static int source_file_line_reader_next(M68kSourceLineReader *reader, char *buffer, size_t buffer_size) {
  if (reader == NULL || reader->u.file == NULL || buffer == NULL || buffer_size == 0U) return 0;
  return fgets(buffer, (int)buffer_size, reader->u.file) != NULL;
}

static void source_file_line_reader_close(M68kSourceLineReader *reader) {
  if (reader == NULL || reader->u.file == NULL) return;
  fclose(reader->u.file);
  reader->u.file = NULL;
}

static int source_text_line_reader_next(M68kSourceLineReader *reader, char *buffer, size_t buffer_size) {
  const char *text;
  size_t cursor;
  size_t copied = 0U;
  if (reader == NULL || buffer == NULL || buffer_size == 0U) return 0;
  text = reader->u.memory.text;
  if (text == NULL) return 0;
  cursor = reader->u.memory.offset;
  if (text[cursor] == '\0') return 0;
  while (copied + 1U < buffer_size && text[cursor] != '\0') {
    buffer[copied++] = text[cursor++];
    if (buffer[copied - 1U] == '\n') break;
  }
  buffer[copied] = '\0';
  reader->u.memory.offset = cursor;
  return 1;
}

static void source_text_line_reader_close(M68kSourceLineReader *reader) {
  (void)reader;
}

static void source_line_reader_close(M68kSourceLineReader *reader) {
  if (reader != NULL && reader->close != NULL) reader->close(reader);
}

static int parse_include_quoted_path(const char *text, char *out_path,
                                     size_t out_path_size) {
  size_t length = strlen(text);
  if (length < 2U)
    return 0;
  if ((text[0] != '"' && text[0] != '\'') || text[length - 1U] != text[0])
    return 0;
  length -= 2U;
  if (length + 1U > out_path_size)
    return 0;
  memcpy(out_path, text + 1, length);
  out_path[length] = '\0';
  return 1;
}

static M68kSourceLookupResult lookup_defined_symbol_value(const AsmSourceFile *source, const char *name,
    int require_constant) {
  M68kSourceLookupResult result = {0};
  M68kSourceModelIndexResult index = m68k_source_model_find_symbol_index(source, name);
  if (!index.ok) return result;
  if (!source->symbols[index.index].defined) return result;
  if (require_constant &&
      source->symbols[index.index].kind != ASM_SOURCE_SYMBOL_CONSTANT)
    return result;
  result.ok = 1U;
  result.defined = 1U;
  result.is_absolute = source->symbols[index.index].is_absolute;
  result.is_constant = (uint8_t)(source->symbols[index.index].kind == ASM_SOURCE_SYMBOL_CONSTANT ||
    source->symbols[index.index].is_absolute);
  result.value = source->symbols[index.index].value;
  result.symbol_id = index.index;
  result.section_index = source->symbols[index.index].is_absolute
    ? (size_t)-1 : source->symbols[index.index].section_index;
  return result;
}

static M68kSourceConstantResult source_lookup_constant_callback(const char *name, void *user_data) {
  M68kSourceConstantResult result = {0};
  M68kSourceLookupResult lookup_result = lookup_defined_symbol_value((const AsmSourceFile *)user_data, name, 1);
  if (!lookup_result.ok || !lookup_result.defined) return result;
  result.ok = 1U;
  result.value = lookup_result.value;
  return result;
}

static M68kSourceConstantResult parse_constant_expression_value(const AsmSourceFile *source, const char *text) {
  return m68k_source_parse_constant_expression(text, source_lookup_constant_callback, (void *)source);
}

static int parse_hex_nibble(char ch, uint8_t *out_value) {
  if (out_value == NULL) return 0;
  if (ch >= '0' && ch <= '9') {
    *out_value = (uint8_t)(ch - '0');
    return 1;
  }
  if (ch >= 'A' && ch <= 'F') {
    *out_value = (uint8_t)(ch - 'A' + 10);
    return 1;
  }
  if (ch >= 'a' && ch <= 'f') {
    *out_value = (uint8_t)(ch - 'a' + 10);
    return 1;
  }
  return 0;
}

typedef enum SourceBlobApplyResult {
  SOURCE_BLOB_APPLY_OK = 1,
  SOURCE_BLOB_APPLY_BAD_HEX = 2,
  SOURCE_BLOB_APPLY_OOM = 3
} SourceBlobApplyResult;

static int parse_hex_blob(Arena *scratch_arena, const char *text, uint8_t **out_data, uint32_t *out_size) {
  const char *cursor;
  size_t digit_count = 0U;
  size_t byte_count;
  uint8_t *data;
  size_t index;
  if (out_data != NULL) *out_data = NULL;
  if (out_size != NULL) *out_size = 0U;
  if (scratch_arena == NULL || text == NULL || out_data == NULL || out_size == NULL) return 0;
  cursor = text;
  if (*cursor == '$') ++cursor;
  while (cursor[digit_count] != '\0') {
    uint8_t ignored = 0U;
    if (!parse_hex_nibble(cursor[digit_count], &ignored)) return 0;
    ++digit_count;
  }
  if ((digit_count & 1U) != 0U) return 0;
  byte_count = digit_count / 2U;
  if (byte_count > UINT32_MAX) return 0;
  data = (uint8_t *)arena_alloc(scratch_arena, byte_count == 0U ? 1U : byte_count);
  if (data == NULL) return 0;
  for (index = 0U; index < byte_count; ++index) {
    uint8_t hi = 0U;
    uint8_t lo = 0U;
    if (!parse_hex_nibble(cursor[index * 2U], &hi) || !parse_hex_nibble(cursor[index * 2U + 1U], &lo)) {
      return 0;
    }
    data[index] = (uint8_t)((hi << 4) | lo);
  }
  *out_data = data;
  *out_size = (uint32_t)byte_count;
  return 1;
}

static int append_atari_relocation_stream_chunk(AsmSourceFile *source, const uint8_t *data, uint32_t size,
    int replace_existing) {
  uint8_t *combined;
  if (source == NULL || source->arena == NULL || (data == NULL && size != 0U)) return 0;
  if (replace_existing) {
    source->atari_st_relocation_stream_data = NULL;
    source->atari_st_relocation_stream_size = 0U;
  }
  if (size == 0U) {
    source->has_atari_st_relocation_stream = 1;
    return 1;
  }
  if ((uint32_t)(UINT32_MAX - source->atari_st_relocation_stream_size) < size) return 0;
  combined = (uint8_t *)arena_alloc(source->arena, (size_t)source->atari_st_relocation_stream_size + size);
  if (combined == NULL) return 0;
  if (source->atari_st_relocation_stream_size != 0U)
    memcpy(combined, source->atari_st_relocation_stream_data, source->atari_st_relocation_stream_size);
  memcpy(combined + source->atari_st_relocation_stream_size, data, size);
  source->atari_st_relocation_stream_data = combined;
  source->atari_st_relocation_stream_size += size;
  source->has_atari_st_relocation_stream = 1;
  return 1;
}

static int append_atari_symbol_table_chunk(AsmSourceFile *source, const uint8_t *data, uint32_t size,
    int replace_existing) {
  uint8_t *combined;
  if (source == NULL || source->arena == NULL || (data == NULL && size != 0U)) return 0;
  if (replace_existing) {
    source->atari_st_symbol_table_data = NULL;
    source->atari_st_symbol_table_size = 0U;
  }
  if (size == 0U) {
    source->has_atari_st_symbol_table = 1;
    return 1;
  }
  if ((uint32_t)(UINT32_MAX - source->atari_st_symbol_table_size) < size) return 0;
  combined = (uint8_t *)arena_alloc(source->arena, (size_t)source->atari_st_symbol_table_size + size);
  if (combined == NULL) return 0;
  if (source->atari_st_symbol_table_size != 0U)
    memcpy(combined, source->atari_st_symbol_table_data, source->atari_st_symbol_table_size);
  memcpy(combined + source->atari_st_symbol_table_size, data, size);
  source->atari_st_symbol_table_data = combined;
  source->atari_st_symbol_table_size += size;
  source->has_atari_st_symbol_table = 1;
  return 1;
}

static SourceBlobApplyResult parse_and_append_atari_symbol_table_chunk(AsmSourceFile *source,
    const char *text, int replace_existing) {
  Arena *scratch_arena = arena_create(4096U);
  uint8_t *data = NULL;
  uint32_t size = 0U;
  SourceBlobApplyResult result = SOURCE_BLOB_APPLY_OOM;
  if (scratch_arena == NULL) return SOURCE_BLOB_APPLY_OOM;
  if (!parse_hex_blob(scratch_arena, text, &data, &size)) {
    result = SOURCE_BLOB_APPLY_BAD_HEX;
  } else if (append_atari_symbol_table_chunk(source, data, size, replace_existing)) {
    result = SOURCE_BLOB_APPLY_OK;
  }
  arena_destroy(scratch_arena);
  return result;
}

static SourceBlobApplyResult parse_and_append_atari_relocation_stream_chunk(AsmSourceFile *source,
    const char *text, int replace_existing) {
  Arena *scratch_arena = arena_create(4096U);
  uint8_t *data = NULL;
  uint32_t size = 0U;
  SourceBlobApplyResult result = SOURCE_BLOB_APPLY_OOM;
  if (scratch_arena == NULL) return SOURCE_BLOB_APPLY_OOM;
  if (!parse_hex_blob(scratch_arena, text, &data, &size)) {
    result = SOURCE_BLOB_APPLY_BAD_HEX;
  } else if (append_atari_relocation_stream_chunk(source, data, size, replace_existing)) {
    result = SOURCE_BLOB_APPLY_OK;
  }
  arena_destroy(scratch_arena);
  return result;
}

static int parse_rs_delta_directive(M68kSourceDirectiveToken directive, uint32_t *out_width) {
  if (out_width != NULL) *out_width = 0U;
  switch (directive) {
  case M68K_SOURCE_DIRECTIVE_RS_B:
    if (out_width != NULL) *out_width = 1U;
    return 1;
  case M68K_SOURCE_DIRECTIVE_RS_W:
    if (out_width != NULL) *out_width = 2U;
    return 1;
  case M68K_SOURCE_DIRECTIVE_RS_L:
    if (out_width != NULL) *out_width = 4U;
    return 1;
  default:
    return 0;
  }
}

static int parse_ds_directive_width(M68kSourceDirectiveToken directive, uint32_t *out_width) {
  if (out_width != NULL) *out_width = 0U;
  switch (directive) {
  case M68K_SOURCE_DIRECTIVE_DS_B:
    if (out_width != NULL) *out_width = 1U;
    return 1;
  case M68K_SOURCE_DIRECTIVE_DS_W:
    if (out_width != NULL) *out_width = 2U;
    return 1;
  case M68K_SOURCE_DIRECTIVE_DS_L:
    if (out_width != NULL) *out_width = 4U;
    return 1;
  default:
    return 0;
  }
}

static int parse_rs_count_delta(const AsmSourceFile *source, const char *text, uint32_t width, uint32_t *out_delta) {
  M68kSourceConstantResult count;
  char buffer[128];
  if (out_delta != NULL) *out_delta = 0U;
  if (out_delta == NULL || width == 0U) return 0;
  snprintf(buffer, sizeof(buffer), "%s", text != NULL ? text : "");
  count = parse_constant_expression_value(source, m68k_trim_in_place(buffer));
  if (!count.ok) return 0;
  *out_delta = count.value * width;
  return 1;
}

static uint32_t apply_rs_directive_alignment(uint32_t offset, uint32_t width) {
  if (width >= 2U && (offset & 1U) != 0U) return offset + 1U;
  return offset;
}

static int source_is_symbol_name(const char *text, void *user_data) {
  (void)user_data;
  return m68k_is_symbol_name(text);
}

static M68kSourceLookupResult source_include_lookup_callback(const char *name, int require_constant, void *user_data) {
  return lookup_defined_symbol_value((const AsmSourceFile *)user_data, name, require_constant);
}

static int source_include_set_constant_callback(const char *name,
                                                uint32_t value,
                                                int allow_redefine,
                                                void *user_data) {
  return m68k_source_model_set_constant((AsmSourceFile *)user_data, name, value,
                                        allow_redefine);
}

static M68kSourceConstantResult source_parse_constant_callback(const char *text, void *user_data) {
  return parse_constant_expression_value((const AsmSourceFile *)user_data, text);
}

static int source_data_append_item_callback(AsmSourceDataStmt *data_stmt,
                                            const AsmDataItem *item,
                                            void *user_data) {
  (void)user_data;
  return m68k_source_model_append_data_item((AsmSourceFile *)user_data, data_stmt, item);
}

static AsmSourceStmt *previous_appendable_data_statement(AsmSourceFile *source,
    size_t current_section_index, uint8_t width_bytes) {
  AsmSourceStmt *stmt;
  if (source == NULL || source->statement_count == 0U) return NULL;
  stmt = &source->statements[source->statement_count - 1U];
  if (stmt->kind != ASM_SOURCE_STMT_DATA) return NULL;
  if (stmt->section_index != current_section_index) return NULL;
  if (stmt->u.data.width_bytes != width_bytes) return NULL;
  return stmt;
}

static int statement_is_fpu_id_alias_instruction(const char *text) {
  char line[128];
  char *cursor;
  char *token;
  M68kParseMnemonicResult mnemonic;
  if (text == NULL) return 0;
  snprintf(line, sizeof(line), "%s", text);
  cursor = line;
  token = m68k_next_token_in_place(&cursor);
  mnemonic = m68k_parse_mnemonic_token(token);
  return mnemonic.mnemonic_id == M68K_ASM_MNEMONIC_FRESTORE ||
    mnemonic.mnemonic_id == M68K_ASM_MNEMONIC_FSAVE;
}

static int parse_plain_instruction_for_cpu_ceiling(const char *text, uint8_t target_cpu,
    M68kInstructionIR *out_instruction, M68kDiagList *diagnostics) {
  uint8_t cpu;
  if (out_instruction == NULL || diagnostics == NULL) return 0;
  m68k_diag_list_reset(diagnostics);
  *out_instruction = m68k_plain_parse_instruction_to_ir(text, target_cpu, m68k_diag_sink(diagnostics));
  if (!m68k_diag_has_errors(diagnostics)) return 1;
  if (target_cpu == M68K_ASM_CPU_ANY || target_cpu > M68K_ASM_CPU_68060) return 0;
  for (cpu = M68K_ASM_CPU_68000; cpu < target_cpu; ++cpu) {
    m68k_diag_list_reset(diagnostics);
    *out_instruction = m68k_plain_parse_instruction_to_ir(text, cpu, m68k_diag_sink(diagnostics));
    if (!m68k_diag_has_errors(diagnostics)) return 1;
  }
  return 0;
}

static int parse_symbolic_instruction_for_cpu_ceiling(const M68kSymbolicParseContext *context,
    const char *text, M68kInstructionIR *out_instruction, char *out_fallback_line,
    size_t out_fallback_line_size) {
  M68kSymbolicParseContext cpu_context;
  uint8_t cpu;
  if (context == NULL || out_instruction == NULL) return 0;
  if (m68k_parse_instruction_with_symbol_fallback_ir(context, text, out_instruction, out_fallback_line,
      out_fallback_line_size)) {
    return 1;
  }
  if (context->target_cpu == M68K_ASM_CPU_ANY || context->target_cpu > M68K_ASM_CPU_68060) return 0;
  for (cpu = M68K_ASM_CPU_68000; cpu < context->target_cpu; ++cpu) {
    cpu_context = *context;
    cpu_context.target_cpu = cpu;
    if (m68k_parse_instruction_with_symbol_fallback_ir(&cpu_context, text, out_instruction, out_fallback_line,
        out_fallback_line_size)) {
      return 1;
    }
  }
  return 0;
}


static int m68k_source_file_parse_reader(AsmSourceFile *source, M68kSourceLineReader *reader,
    M68kDiagSink diagnostics) {
  char line[M68K_SOURCE_PARSE_LINE_CAPACITY];
  char last_symbol_fallback_line[M68K_SOURCE_PARSE_LINE_CAPACITY];
  size_t line_number = 0;
  size_t current_section_index = (size_t)-1;
  uint8_t current_fpu_id = 1U;
  uint8_t current_fpu_directive_active = 0U;
  M68kSourceIncludeState include_state;
  M68kSourceIncludeContext include_context;
  M68kSourceDataParseContext data_parse_context;
  M68kSymbolicParseContext symbolic_parse_context;
  memset(&include_state, 0, sizeof(include_state));
  memset(&include_context, 0, sizeof(include_context));
  memset(&data_parse_context, 0, sizeof(data_parse_context));
  memset(&symbolic_parse_context, 0, sizeof(symbolic_parse_context));
  m68k_source_include_state_init(&include_state, source->include_dir);
  include_context.user_data = source;
  include_context.lookup_defined = source_include_lookup_callback;
  include_context.set_constant = source_include_set_constant_callback;
  include_context.parse_constant = source_parse_constant_callback;
  data_parse_context.user_data = source;
  data_parse_context.parse_constant = source_parse_constant_callback;
  data_parse_context.append_item = source_data_append_item_callback;
  symbolic_parse_context.target_cpu = source->target_cpu;
  symbolic_parse_context.user_data = source;
  symbolic_parse_context.lookup_symbol = source_include_lookup_callback;
  symbolic_parse_context.is_symbol_name = source_is_symbol_name;
  last_symbol_fallback_line[0] = '\0';
  if (reader == NULL || reader->next == NULL) {
    source_parse_error(diagnostics, "bad source reader");
    return 0;
  }
  while (reader->next(reader, line, sizeof(line))) {
    char *rest = NULL;
    char *cursor = NULL;
    char *token0 = NULL;
    M68kSourceDirectiveToken directive0 = M68K_SOURCE_DIRECTIVE_NONE;
    char statement_text[M68K_SOURCE_PARSE_LINE_CAPACITY];
    ++line_number;
    m68k_strip_comment_in_place(line);
    rest = m68k_trim_in_place(line);
    if (*rest == '\0')
      continue;
    {
      char *colon = m68k_find_label_delimiter(rest);
      if (colon != NULL) {
        M68kSourceModelIndexResult label_symbol_result;
        M68kSourceModelIndexResult label_stmt_result;
        AsmSourceStmt *label_stmt = NULL;
        *colon = '\0';
        if (!m68k_is_symbol_name(m68k_trim_in_place(rest))) {
          source_line_reader_close(reader);
          source_parse_errorf(diagnostics, "bad label at line %u", (unsigned)line_number);
          return 0;
        }
        label_symbol_result = m68k_source_model_ensure_symbol(source, m68k_trim_in_place(rest),
          ASM_SOURCE_SYMBOL_LABEL);
        if (!label_symbol_result.ok) {
          source_line_reader_close(reader);
          source_parse_error(diagnostics, "out of memory");
          return 0;
        }
        label_stmt_result = m68k_source_model_append_statement(source, ASM_SOURCE_STMT_LABEL, line_number);
        if (!label_stmt_result.ok) {
          source_line_reader_close(reader);
          source_parse_error(diagnostics, "out of memory");
          return 0;
        }
        label_stmt = &source->statements[label_stmt_result.index];
        snprintf(label_stmt->u.label.name, sizeof(label_stmt->u.label.name),
                 "%s", m68k_trim_in_place(rest));
        label_stmt->section_index = current_section_index;
        rest = m68k_trim_in_place(colon + 1);
        if (*rest == '\0')
          continue;
      }
    }
    snprintf(statement_text, sizeof(statement_text), "%s", rest);
    cursor = rest;
    token0 = m68k_next_token_in_place(&cursor);
    rest = m68k_trim_in_place(cursor);
    directive0 = m68k_parse_source_directive_token(token0);
    if (directive0 == M68K_SOURCE_DIRECTIVE_INCLUDE) {
      char include_path[512];
      char full_path[1024];
      if (!parse_include_quoted_path(rest, include_path, sizeof(include_path))) {
        source_line_reader_close(reader);
        source_parse_errorf(diagnostics, "bad include path at line %u", (unsigned)line_number);
        return 0;
      }
      snprintf(full_path, sizeof(full_path), "%s\\%s", source->include_dir,
               include_path);
      if (!m68k_source_include_process_file(&include_context, &include_state, full_path, diagnostics)) {
        source_line_reader_close(reader);
        return 0;
      }
      continue;
    }
    if (*rest != '\0') {
      char rest_copy[256];
      char *cursor1 = NULL;
      char *token1 = NULL;
      M68kSourceDirectiveToken directive1 = M68K_SOURCE_DIRECTIVE_NONE;
      M68kSourceConstantResult value;
      snprintf(rest_copy, sizeof(rest_copy), "%s", rest);
      cursor1 = rest_copy;
      token1 = m68k_next_token_in_place(&cursor1);
      directive1 = m68k_parse_source_directive_token(token1);
      value = parse_constant_expression_value(source, m68k_trim_in_place(cursor1));
      if ((directive1 == M68K_SOURCE_DIRECTIVE_EQU || directive1 == M68K_SOURCE_DIRECTIVE_SET) &&
          value.ok &&
          m68k_source_model_set_constant(source, token0, value.value,
                                         directive1 == M68K_SOURCE_DIRECTIVE_SET)) {
        continue;
      } else if (directive1 == M68K_SOURCE_DIRECTIVE_EQU || directive1 == M68K_SOURCE_DIRECTIVE_SET) {
        source_line_reader_close(reader);
        source_parse_errorf(diagnostics, "bad source constant at line %u", (unsigned)line_number);
        return 0;
      }
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_RSSET) {
      M68kSourceConstantResult value = parse_constant_expression_value(source, rest);
      if (!value.ok || !m68k_source_model_set_constant(source, "__RS", value.value, 1)) {
        source_line_reader_close(reader);
        source_parse_errorf(diagnostics, "bad RSSET directive at line %u", (unsigned)line_number);
        return 0;
      }
      continue;
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_RSRESET) {
      if (*rest != '\0' || !m68k_source_model_set_constant(source, "__RS", 0U, 1)) {
        source_line_reader_close(reader);
        source_parse_errorf(diagnostics, "bad RSRESET directive at line %u", (unsigned)line_number);
        return 0;
      }
      continue;
    }
    {
      uint32_t width = 0U;
      if (parse_rs_delta_directive(directive0, &width)) {
        M68kSourceLookupResult current_offset = lookup_defined_symbol_value(source, "__RS", 1);
        uint32_t delta = 0U;
        uint32_t aligned_offset = 0U;
        if (current_offset.ok) aligned_offset = apply_rs_directive_alignment(current_offset.value, width);
        if (!current_offset.ok || !parse_rs_count_delta(source, rest, width, &delta) ||
            !m68k_source_model_set_constant(source, "__RS", aligned_offset + delta, 1)) {
          source_line_reader_close(reader);
          source_parse_errorf(diagnostics, "bad RS directive at line %u", (unsigned)line_number);
          return 0;
        }
        continue;
      }
    }
    if (*rest != '\0' && directive0 == M68K_SOURCE_DIRECTIVE_NONE) {
      char rest_copy[256];
      char *cursor1 = NULL;
      char *token1 = NULL;
      M68kSourceDirectiveToken directive1 = M68K_SOURCE_DIRECTIVE_NONE;
      uint32_t width = 0U;
      uint32_t delta = 0U;
      M68kSourceLookupResult current_offset;
      snprintf(rest_copy, sizeof(rest_copy), "%s", rest);
      cursor1 = rest_copy;
      token1 = m68k_next_token_in_place(&cursor1);
      directive1 = m68k_parse_source_directive_token(token1);
      if (parse_rs_delta_directive(directive1, &width)) {
        current_offset = lookup_defined_symbol_value(source, "__RS", 1);
        if (current_offset.ok) current_offset.value = apply_rs_directive_alignment(current_offset.value, width);
        if (!current_offset.ok || !m68k_source_model_set_constant(source, token0, current_offset.value, 0) ||
            !parse_rs_count_delta(source, m68k_trim_in_place(cursor1), width, &delta) ||
            !m68k_source_model_set_constant(source, "__RS", current_offset.value + delta, 1)) {
          source_line_reader_close(reader);
          source_parse_errorf(diagnostics, "bad RS label directive at line %u", (unsigned)line_number);
          return 0;
        }
        continue;
      }
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_SECTION) {
      M68kSourceModelIndexResult stmt_result;
      M68kSourceModelIndexResult section_result;
      AsmSourceStmt *stmt = NULL;
      char buffer[128];
      char *parts[3];
      size_t count = 0;
      M68kSectionKind kind;
      uint8_t platform_mem_type = 0U;
      uint32_t platform_mem_attrs = 0U;
      uint8_t has_alloc_size = 0U;
      uint32_t alloc_size = 0U;
      snprintf(buffer, sizeof(buffer), "%s", rest);
      count = m68k_split_delimited_in_place(buffer, ',', parts,
                                            sizeof(parts) / sizeof(parts[0]));
      if ((count != 2U && count != 3U) ||
          !m68k_parse_section_spec(m68k_trim_in_place(parts[1]), &kind, &platform_mem_type,
            &platform_mem_attrs)) {
        source_line_reader_close(reader);
        source_parse_errorf(diagnostics, "bad section directive at line %u", (unsigned)line_number);
        return 0;
      }
      if (count == 3U) {
        M68kParseU32Result parsed_alloc_size = m68k_parse_number_u32(m68k_trim_in_place(parts[2]));
        if (!parsed_alloc_size.ok) {
          source_line_reader_close(reader);
          source_parse_errorf(diagnostics, "bad section allocation size at line %u", (unsigned)line_number);
          return 0;
        }
        has_alloc_size = 1U;
        alloc_size = parsed_alloc_size.value;
      }
      stmt_result = m68k_source_model_append_statement(source, ASM_SOURCE_STMT_SECTION, line_number);
      section_result = m68k_source_model_append_section(source, m68k_trim_in_place(parts[0]), kind,
        platform_mem_type, platform_mem_attrs, has_alloc_size, alloc_size);
      if (!stmt_result.ok || !section_result.ok) {
        source_line_reader_close(reader);
        source_parse_errorf(diagnostics, "bad section directive at line %u", (unsigned)line_number);
        return 0;
      }
      stmt = &source->statements[stmt_result.index];
      current_section_index = section_result.index;
      stmt->section_index = current_section_index;
      snprintf(stmt->u.section.name, sizeof(stmt->u.section.name), "%s",
                 m68k_trim_in_place(parts[0]));
      stmt->u.section.kind = kind;
      stmt->u.section.platform_mem_type = platform_mem_type;
      stmt->u.section.platform_mem_attrs = platform_mem_attrs;
      stmt->u.section.has_alloc_size = has_alloc_size;
      stmt->u.section.alloc_size = alloc_size;
      continue;
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_EVEN) {
      M68kSourceModelIndexResult stmt_result;
      AsmSourceStmt *stmt = NULL;
      stmt_result = m68k_source_model_append_statement(source, ASM_SOURCE_STMT_EVEN, line_number);
      if (!stmt_result.ok) {
        source_line_reader_close(reader);
        source_parse_error(diagnostics, "out of memory");
        return 0;
      }
      stmt = &source->statements[stmt_result.index];
      stmt->section_index = current_section_index;
      continue;
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_END) {
      M68kSourceModelIndexResult stmt_result;
      AsmSourceStmt *stmt = NULL;
      stmt_result = m68k_source_model_append_statement(source, ASM_SOURCE_STMT_END, line_number);
      if (!stmt_result.ok) {
        source_line_reader_close(reader);
        source_parse_error(diagnostics, "out of memory");
        return 0;
      }
      stmt = &source->statements[stmt_result.index];
      stmt->section_index = current_section_index;
      break;
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_COMMENT) {
      static const char head_prefix[] = "HEAD=", reloc_flag_prefix[] = "ATARI_RELOC_FLAG=";
      static const char symbol_type_prefix[] = "ATARI_SYMBOL_TYPE=", symbol_append_prefix[] = "ATARI_SYMBOLS+=";
      static const char symbol_prefix[] = "ATARI_SYMBOLS=", reloc_append_prefix[] = "ATARI_RELOC+=";
      static const char reloc_prefix[] = "ATARI_RELOC=";
      size_t head_prefix_len = strlen(head_prefix), reloc_flag_prefix_len = strlen(reloc_flag_prefix);
      size_t symbol_type_prefix_len = strlen(symbol_type_prefix), symbol_append_prefix_len = strlen(symbol_append_prefix);
      size_t symbol_prefix_len = strlen(symbol_prefix), reloc_append_prefix_len = strlen(reloc_append_prefix);
      size_t reloc_prefix_len = strlen(reloc_prefix);
      char *head_text = m68k_trim_in_place(rest);
      M68kSourceConstantResult value;
      if (m68k_ascii_prefix_equal_ci(head_text, head_prefix)) {
        head_text = m68k_trim_in_place(head_text + head_prefix_len);
        value = parse_constant_expression_value(source, head_text);
        if (!value.ok) {
          source_line_reader_close(reader);
          source_parse_errorf(diagnostics, "bad COMMENT HEAD directive at line %u", (unsigned)line_number);
          return 0;
        }
        source->has_atari_st_program_flags = 1;
        source->atari_st_program_flags = value.value;
        continue;
      }
      if (m68k_ascii_prefix_equal_ci(head_text, reloc_flag_prefix)) {
        head_text = m68k_trim_in_place(head_text + reloc_flag_prefix_len);
        value = parse_constant_expression_value(source, head_text);
        if (!value.ok || value.value > 0xFFFFU) {
          source_line_reader_close(reader);
          source_parse_errorf(diagnostics, "bad COMMENT ATARI_RELOC_FLAG directive at line %u",
            (unsigned)line_number);
          return 0;
        }
        source->has_atari_st_relocation_flag = 1;
        source->atari_st_relocation_flag = value.value;
        continue;
      }
      if (m68k_ascii_prefix_equal_ci(head_text, symbol_type_prefix)) {
        head_text = m68k_trim_in_place(head_text + symbol_type_prefix_len);
        value = parse_constant_expression_value(source, head_text);
        if (!value.ok) {
          source_line_reader_close(reader);
          source_parse_errorf(diagnostics, "bad COMMENT ATARI_SYMBOL_TYPE directive at line %u",
            (unsigned)line_number);
          return 0;
        }
        source->has_atari_st_symbol_table = 1;
        source->atari_st_symbol_table_type = value.value;
        continue;
      }
      if (m68k_ascii_prefix_equal_ci(head_text, symbol_append_prefix)) {
        SourceBlobApplyResult blob_result;
        head_text = m68k_trim_in_place(head_text + symbol_append_prefix_len);
        blob_result = parse_and_append_atari_symbol_table_chunk(source, head_text, 0);
        if (blob_result == SOURCE_BLOB_APPLY_BAD_HEX) {
          source_line_reader_close(reader);
          source_parse_errorf(diagnostics, "bad COMMENT ATARI_SYMBOLS append directive at line %u",
            (unsigned)line_number);
          return 0;
        }
        if (blob_result != SOURCE_BLOB_APPLY_OK) {
          source_line_reader_close(reader);
          source_parse_error(diagnostics, "out of memory");
          return 0;
        }
        continue;
      }
      if (m68k_ascii_prefix_equal_ci(head_text, symbol_prefix)) {
        SourceBlobApplyResult blob_result;
        head_text = m68k_trim_in_place(head_text + symbol_prefix_len);
        blob_result = parse_and_append_atari_symbol_table_chunk(source, head_text, 1);
        if (blob_result == SOURCE_BLOB_APPLY_BAD_HEX) {
          source_line_reader_close(reader);
          source_parse_errorf(diagnostics, "bad COMMENT ATARI_SYMBOLS directive at line %u",
            (unsigned)line_number);
          return 0;
        }
        if (blob_result != SOURCE_BLOB_APPLY_OK) {
          source_line_reader_close(reader);
          source_parse_error(diagnostics, "out of memory");
          return 0;
        }
        continue;
      }
      if (m68k_ascii_prefix_equal_ci(head_text, reloc_append_prefix)) {
        SourceBlobApplyResult blob_result;
        head_text = m68k_trim_in_place(head_text + reloc_append_prefix_len);
        blob_result = parse_and_append_atari_relocation_stream_chunk(source, head_text, 0);
        if (blob_result == SOURCE_BLOB_APPLY_BAD_HEX) {
          source_line_reader_close(reader);
          source_parse_errorf(diagnostics, "bad COMMENT ATARI_RELOC append directive at line %u",
            (unsigned)line_number);
          return 0;
        }
        if (blob_result != SOURCE_BLOB_APPLY_OK) {
          source_line_reader_close(reader);
          source_parse_error(diagnostics, "out of memory");
          return 0;
        }
        continue;
      }
      if (m68k_ascii_prefix_equal_ci(head_text, reloc_prefix)) {
        SourceBlobApplyResult blob_result;
        head_text = m68k_trim_in_place(head_text + reloc_prefix_len);
        blob_result = parse_and_append_atari_relocation_stream_chunk(source, head_text, 1);
        if (blob_result == SOURCE_BLOB_APPLY_BAD_HEX) {
          source_line_reader_close(reader);
          source_parse_errorf(diagnostics, "bad COMMENT ATARI_RELOC directive at line %u",
            (unsigned)line_number);
          return 0;
        }
        if (blob_result != SOURCE_BLOB_APPLY_OK) {
          source_line_reader_close(reader);
          source_parse_error(diagnostics, "out of memory");
          return 0;
        }
        continue;
      }
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_FPU) {
      M68kSourceConstantResult fpu_id = parse_constant_expression_value(source, rest);
      if (!fpu_id.ok || fpu_id.value > 7U) {
        source_line_reader_close(reader);
        source_parse_errorf(diagnostics, "bad FPU directive at line %u", (unsigned)line_number);
        return 0;
      }
      current_fpu_id = (uint8_t)fpu_id.value;
      current_fpu_directive_active = 1U;
      continue;
    }
    if (current_section_index == (size_t)-1) {
      source_line_reader_close(reader);
      source_parse_error(diagnostics, "source statement before section");
      return 0;
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_ORG) {
      M68kSourceModelIndexResult stmt_result;
      M68kSourceConstantResult org_value;
      AsmSourceStmt *stmt = NULL;
      org_value = parse_constant_expression_value(source, rest);
      stmt_result = m68k_source_model_append_statement(source, ASM_SOURCE_STMT_ORG, line_number);
      if (!org_value.ok || !stmt_result.ok) {
        source_line_reader_close(reader);
        source_parse_errorf(diagnostics, "bad ORG directive at line %u", (unsigned)line_number);
        return 0;
      }
      stmt = &source->statements[stmt_result.index];
      stmt->section_index = current_section_index;
      stmt->u.org_value = org_value.value;
      continue;
    }
    {
      uint32_t ds_width = 0U;
      if (parse_ds_directive_width(directive0, &ds_width)) {
        M68kSourceModelIndexResult stmt_result;
        M68kSourceConstantResult reserve_count;
        AsmSourceStmt *stmt = NULL;
        reserve_count = parse_constant_expression_value(source, rest);
        stmt_result = m68k_source_model_append_statement(source, ASM_SOURCE_STMT_RESERVE, line_number);
        if (!reserve_count.ok || !stmt_result.ok || (ds_width != 0U && reserve_count.value > UINT32_MAX / ds_width)) {
          source_line_reader_close(reader);
          source_parse_errorf(diagnostics, "bad DS directive at line %u", (unsigned)line_number);
          return 0;
        }
        stmt = &source->statements[stmt_result.index];
        stmt->section_index = current_section_index;
        stmt->u.reserve_size = reserve_count.value * ds_width;
        continue;
      }
    }
    {
      M68kParseDataDirectiveResult data_directive = m68k_parse_data_directive_token(directive0);
      if (data_directive.ok && data_directive.is_repeat == 0U) {
        M68kSourceModelIndexResult stmt_result;
        AsmSourceStmt *stmt = previous_appendable_data_statement(source, current_section_index,
          data_directive.width_bytes);
        if (stmt == NULL) {
          stmt_result = m68k_source_model_append_statement(source, ASM_SOURCE_STMT_DATA, line_number);
          if (!stmt_result.ok) {
            source_line_reader_close(reader);
            source_parse_errorf(diagnostics,
                       "bad data directive at line %u: %s %s",
                       (unsigned)line_number, token0, rest);
            return 0;
          }
          stmt = &source->statements[stmt_result.index];
          stmt->section_index = current_section_index;
        }
        if (!m68k_source_parse_data_statement(token0, rest, &stmt->u.data, &data_parse_context)) {
          source_line_reader_close(reader);
          source_parse_errorf(diagnostics,
                     "bad data directive at line %u: %s %s",
                     (unsigned)line_number, token0, rest);
          return 0;
        }
        continue;
      }
      if (data_directive.ok && data_directive.is_repeat != 0U) {
        M68kSourceModelIndexResult stmt_result;
        AsmSourceStmt *stmt = previous_appendable_data_statement(source, current_section_index,
          data_directive.width_bytes);
        if (stmt == NULL) {
          stmt_result = m68k_source_model_append_statement(source, ASM_SOURCE_STMT_DATA, line_number);
          if (!stmt_result.ok) {
            source_line_reader_close(reader);
            source_parse_errorf(diagnostics,
                       "bad data directive at line %u: %s %s",
                       (unsigned)line_number, token0, rest);
            return 0;
          }
          stmt = &source->statements[stmt_result.index];
          stmt->section_index = current_section_index;
        }
        if (!m68k_source_parse_dcb_statement(token0, rest, &stmt->u.data, &data_parse_context)) {
          source_line_reader_close(reader);
          source_parse_errorf(diagnostics,
                     "bad data directive at line %u: %s %s",
                     (unsigned)line_number, token0, rest);
          return 0;
        }
        continue;
      }
    }
    if (source->platform_backend_kind == M68K_PLATFORM_BACKEND_MACOS && directive0 == M68K_SOURCE_DIRECTIVE_NONE &&
        *rest == '\0') {
      M68kSourceLookupResult trap_word = lookup_defined_symbol_value(source, token0, 1);
      if (trap_word.ok && trap_word.defined && trap_word.value <= 0xFFFFU) {
        M68kSourceModelIndexResult stmt_result =
          m68k_source_model_append_statement(source, ASM_SOURCE_STMT_DATA, line_number);
        AsmSourceStmt *stmt = NULL;
        char expr[128];
        if (!stmt_result.ok) {
          source_line_reader_close(reader);
          source_parse_error(diagnostics, "out of memory");
          return 0;
        }
        stmt = &source->statements[stmt_result.index];
        stmt->section_index = current_section_index;
        snprintf(expr, sizeof(expr), "%s", token0);
        if (!m68k_source_parse_data_statement("DC.W", expr, &stmt->u.data, &data_parse_context)) {
          source_line_reader_close(reader);
          source_parse_errorf(diagnostics, "bad OPWORD reference at line %u", (unsigned)line_number);
          return 0;
        }
        continue;
      }
    }
    {
      M68kSourceModelIndexResult stmt_result;
      AsmSourceStmt *stmt = NULL;
      int parse_ok;
      M68kDiagList parse_diagnostics;
      stmt_result = m68k_source_model_append_statement(source, ASM_SOURCE_STMT_INSTRUCTION, line_number);
      if (!stmt_result.ok) {
        source_line_reader_close(reader);
        source_parse_error(diagnostics, "out of memory");
        return 0;
      }
      stmt = &source->statements[stmt_result.index];
      parse_ok = parse_plain_instruction_for_cpu_ceiling(statement_text, source->target_cpu,
        &stmt->u.instruction.parsed_ir, &parse_diagnostics);
      if (!parse_ok && current_fpu_directive_active != 0U && current_fpu_id > 0U &&
          statement_is_fpu_id_alias_instruction(statement_text)) {
        m68k_diag_list_reset(&parse_diagnostics);
        stmt->u.instruction.parsed_ir = m68k_plain_parse_instruction_to_ir(statement_text,
          M68K_ASM_CPU_68040, m68k_diag_sink(&parse_diagnostics));
        parse_ok = !m68k_diag_has_errors(&parse_diagnostics);
      }
      if (!parse_ok) {
        parse_ok = parse_symbolic_instruction_for_cpu_ceiling(&symbolic_parse_context, statement_text,
            &stmt->u.instruction.parsed_ir, last_symbol_fallback_line,
            sizeof(last_symbol_fallback_line));
      }
      if (!parse_ok && current_fpu_directive_active != 0U && current_fpu_id > 0U &&
          statement_is_fpu_id_alias_instruction(statement_text)) {
        M68kSymbolicParseContext fpu_symbolic_parse_context = symbolic_parse_context;
        fpu_symbolic_parse_context.target_cpu = M68K_ASM_CPU_68040;
        parse_ok = m68k_parse_instruction_with_symbol_fallback_ir(&fpu_symbolic_parse_context,
            statement_text, &stmt->u.instruction.parsed_ir, last_symbol_fallback_line,
            sizeof(last_symbol_fallback_line));
      }
      if (!parse_ok) {
        source_line_reader_close(reader);
        if (strstr(statement_text, "MEMF_PUBLIC") != NULL ||
            strstr(statement_text, "MEMF_LARGEST") != NULL) {
          M68kSourceLookupResult public_value = lookup_defined_symbol_value(source, "MEMF_PUBLIC", 1);
          M68kSourceLookupResult largest_value = lookup_defined_symbol_value(source, "MEMF_LARGEST", 1);
          M68kSourceConstantResult expr_value = parse_constant_expression_value(source, "MEMF_PUBLIC|MEMF_LARGEST");
          source_parse_errorf(diagnostics,
                   "unable to parse source line %u: %s | fallback=%s | "
                   "MEMF_PUBLIC=%d:%u MEMF_LARGEST=%d:%u EXPR=%d:%u",
                   (unsigned)line_number, statement_text,
                   last_symbol_fallback_line, public_value.ok,
                   public_value.ok ? public_value.value : 0U, largest_value.ok,
                   largest_value.ok ? largest_value.value : 0U, expr_value.ok,
                   expr_value.ok ? expr_value.value : 0U);
        } else {
          source_parse_errorf(diagnostics,
                   "unable to parse source line %u: %s | fallback=%s",
                   (unsigned)line_number, statement_text,
                   last_symbol_fallback_line);
        }
        return 0;
      }
      if (!m68k_instruction_apply_fpu_directive_alias(&stmt->u.instruction.parsed_ir, current_fpu_id,
          current_fpu_directive_active, source->target_cpu)) {
        source_line_reader_close(reader);
        source_parse_errorf(diagnostics, "bad FPU instruction at line %u", (unsigned)line_number);
        return 0;
      }
      stmt->section_index = current_section_index;
      stmt->u.instruction.requested_size_suffix =
          m68k_requested_size_suffix_from_text(statement_text);
    }
  }
  source_line_reader_close(reader);
  return 1;
}

int m68k_source_file_parse(AsmSourceFile *source, const char *path, M68kDiagSink diagnostics) {
  FILE *input;
  M68kSourceLineReader reader;
  memset(&reader, 0, sizeof(reader));
  if (path == NULL) {
    source_parse_error(diagnostics, "failed opening source file");
    return 0;
  }
  input = fopen(path, "r");
  if (input == NULL) {
    source_parse_error(diagnostics, "failed opening source file");
    return 0;
  }
  reader.next = source_file_line_reader_next;
  reader.close = source_file_line_reader_close;
  reader.u.file = input;
  return m68k_source_file_parse_reader(source, &reader, diagnostics);
}

int m68k_source_file_parse_text(AsmSourceFile *source, const char *source_text, M68kDiagSink diagnostics) {
  M68kSourceLineReader reader;
  memset(&reader, 0, sizeof(reader));
  if (source_text == NULL) {
    source_parse_error(diagnostics, "missing source text");
    return 0;
  }
  reader.next = source_text_line_reader_next;
  reader.close = source_text_line_reader_close;
  reader.u.memory.text = source_text;
  reader.u.memory.offset = 0U;
  return m68k_source_file_parse_reader(source, &reader, diagnostics);
}



