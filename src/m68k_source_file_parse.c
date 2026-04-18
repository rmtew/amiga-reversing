#include "m68k_source_file_parse.h"

#include "m68k_parse_util.h"
#include "m68k_plain_parse.h"
#include "m68k_source_constant_expr.h"
#include "m68k_source_data.h"
#include "m68k_source_include.h"
#include "m68k_source_rewrite.h"
#include "m68k_source_text_util.h"
#include "m68k_symbolic_parse.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>

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
  result.is_constant = (uint8_t)(source->symbols[index.index].kind == ASM_SOURCE_SYMBOL_CONSTANT);
  result.value = source->symbols[index.index].value;
  result.symbol_id = index.index;
  result.section_index = source->symbols[index.index].section_index;
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

static int source_rewrite_is_constant_symbol(const char *name,
                                             void *user_data) {
  const AsmSourceFile *source = (const AsmSourceFile *)user_data;
  M68kSourceModelIndexResult symbol_index = m68k_source_model_find_symbol_index(source, name);
  return symbol_index.ok && source->symbols[symbol_index.index].kind == ASM_SOURCE_SYMBOL_CONSTANT;
}

static M68kSourceConstantResult source_rewrite_parse_constant(const char *text, void *user_data) {
  return parse_constant_expression_value((const AsmSourceFile *)user_data, text);
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
  return m68k_source_model_append_data_item(data_stmt, item);
}


int m68k_source_file_parse(AsmSourceFile *source, const char *path, M68kDiagSink diagnostics) {
  FILE *input = fopen(path, "r");
  char line[256];
  char last_symbol_fallback_line[256];
  size_t line_number = 0;
  size_t current_section_index = (size_t)-1;
  M68kSourceIncludeState include_state;
  M68kSourceIncludeContext include_context;
  M68kSourceDataParseContext data_parse_context;
  M68kSymbolicParseContext symbolic_parse_context;
  M68kSourceRewriteContext rewrite_context;
  memset(&include_state, 0, sizeof(include_state));
  memset(&include_context, 0, sizeof(include_context));
  memset(&data_parse_context, 0, sizeof(data_parse_context));
  memset(&symbolic_parse_context, 0, sizeof(symbolic_parse_context));
  memset(&rewrite_context, 0, sizeof(rewrite_context));
  m68k_source_include_state_init(&include_state, source->include_dir);
  include_context.user_data = source;
  include_context.lookup_defined = source_include_lookup_callback;
  include_context.set_constant = source_include_set_constant_callback;
  include_context.parse_constant = source_parse_constant_callback;
  data_parse_context.user_data = source;
  data_parse_context.parse_constant = source_parse_constant_callback;
  data_parse_context.append_item = source_data_append_item_callback;
  symbolic_parse_context.target_cpu = source->target_cpu;
  symbolic_parse_context.enable_vasm_compat_rewrites =
      source->enable_vasm_compat_rewrites;
  symbolic_parse_context.user_data = source;
  symbolic_parse_context.lookup_symbol = source_include_lookup_callback;
  symbolic_parse_context.is_symbol_name = source_is_symbol_name;
  rewrite_context.user_data = source;
  rewrite_context.is_symbol_name = source_is_symbol_name;
  rewrite_context.is_constant_symbol = source_rewrite_is_constant_symbol;
  rewrite_context.parse_constant = source_rewrite_parse_constant;
  last_symbol_fallback_line[0] = '\0';
  if (input == NULL) {
    source_parse_error(diagnostics, "failed opening source file");
    return 0;
  }
  while (fgets(line, sizeof(line), input) != NULL) {
    char *rest = NULL;
    char *cursor = NULL;
    char *token0 = NULL;
    M68kSourceDirectiveToken directive0 = M68K_SOURCE_DIRECTIVE_NONE;
    char statement_text[256];
    char rewritten_statement_text[256];
    char optimized_statement_text[256];
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
          fclose(input);
          source_parse_errorf(diagnostics, "bad label at line %u", (unsigned)line_number);
          return 0;
        }
        label_symbol_result = m68k_source_model_ensure_symbol(source, m68k_trim_in_place(rest),
          ASM_SOURCE_SYMBOL_LABEL);
        if (!label_symbol_result.ok) {
          fclose(input);
          source_parse_error(diagnostics, "out of memory");
          return 0;
        }
        label_stmt_result = m68k_source_model_append_statement(source, ASM_SOURCE_STMT_LABEL, line_number);
        if (!label_stmt_result.ok) {
          fclose(input);
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
    if (source->enable_vasm_compat_rewrites) {
      m68k_rewrite_movea_symbolic_immediate_to_lea( &rewrite_context, statement_text, rewritten_statement_text,
          sizeof(rewritten_statement_text));
      snprintf(optimized_statement_text, sizeof(optimized_statement_text), "%s",
               rewritten_statement_text);
      m68k_rewrite_move_immediate_to_moveq( &rewrite_context, optimized_statement_text, optimized_statement_text,
          sizeof(optimized_statement_text));
      m68k_rewrite_cmp_zero_to_tst(optimized_statement_text,
                                   optimized_statement_text,
                                   sizeof(optimized_statement_text));
    } else {
      snprintf(optimized_statement_text, sizeof(optimized_statement_text), "%s",
               statement_text);
    }
    cursor = rest;
    token0 = m68k_next_token_in_place(&cursor);
    rest = m68k_trim_in_place(cursor);
    directive0 = m68k_parse_source_directive_token(token0);
    if (directive0 == M68K_SOURCE_DIRECTIVE_INCLUDE) {
      char include_path[512];
      char full_path[1024];
      if (!parse_include_quoted_path(rest, include_path, sizeof(include_path))) {
        fclose(input);
        source_parse_errorf(diagnostics, "bad include path at line %u", (unsigned)line_number);
        return 0;
      }
      snprintf(full_path, sizeof(full_path), "%s\\%s", source->include_dir,
               include_path);
      if (!m68k_source_include_process_file(&include_context, &include_state, full_path, diagnostics)) {
        fclose(input);
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
        fclose(input);
        source_parse_errorf(diagnostics, "bad source constant at line %u", (unsigned)line_number);
        return 0;
      }
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_RSSET) {
      M68kSourceConstantResult value = parse_constant_expression_value(source, rest);
      if (!value.ok || !m68k_source_model_set_constant(source, "__RS", value.value, 1)) {
        fclose(input);
        source_parse_errorf(diagnostics, "bad RSSET directive at line %u", (unsigned)line_number);
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
          fclose(input);
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
          fclose(input);
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
      char *parts[2];
      size_t count = 0;
      M68kSectionKind kind;
      snprintf(buffer, sizeof(buffer), "%s", rest);
      count = m68k_split_delimited_in_place(buffer, ',', parts,
                                            sizeof(parts) / sizeof(parts[0]));
      if (count != 2U || !m68k_parse_section_kind(m68k_trim_in_place(parts[1]), &kind)) {
        fclose(input);
        source_parse_errorf(diagnostics, "bad section directive at line %u", (unsigned)line_number);
        return 0;
      }
      stmt_result = m68k_source_model_append_statement(source, ASM_SOURCE_STMT_SECTION, line_number);
      section_result = m68k_source_model_append_section(source, m68k_trim_in_place(parts[0]), kind);
      if (!stmt_result.ok || !section_result.ok) {
        fclose(input);
        source_parse_errorf(diagnostics, "bad section directive at line %u", (unsigned)line_number);
        return 0;
      }
      stmt = &source->statements[stmt_result.index];
      current_section_index = section_result.index;
      stmt->section_index = current_section_index;
      snprintf(stmt->u.section.name, sizeof(stmt->u.section.name), "%s",
               m68k_trim_in_place(parts[0]));
      stmt->u.section.kind = kind;
      continue;
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_EVEN) {
      M68kSourceModelIndexResult stmt_result;
      AsmSourceStmt *stmt = NULL;
      stmt_result = m68k_source_model_append_statement(source, ASM_SOURCE_STMT_EVEN, line_number);
      if (!stmt_result.ok) {
        fclose(input);
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
        fclose(input);
        source_parse_error(diagnostics, "out of memory");
        return 0;
      }
      stmt = &source->statements[stmt_result.index];
      stmt->section_index = current_section_index;
      break;
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_COMMENT) {
      const char *head_prefix = "HEAD=";
      size_t head_prefix_len = strlen(head_prefix);
      char *head_text = m68k_trim_in_place(rest);
      M68kSourceConstantResult value;
      if (m68k_ascii_prefix_equal_ci(head_text, head_prefix)) {
        head_text = m68k_trim_in_place(head_text + head_prefix_len);
        value = parse_constant_expression_value(source, head_text);
        if (!value.ok) {
          fclose(input);
          source_parse_errorf(diagnostics, "bad COMMENT HEAD directive at line %u", (unsigned)line_number);
          return 0;
        }
        source->has_atari_st_program_flags = 1;
        source->atari_st_program_flags = value.value;
        continue;
      }
    }
    if (current_section_index == (size_t)-1) {
      fclose(input);
      source_parse_error(diagnostics, "source statement before section");
      return 0;
    }
    if (source->enable_vasm_compat_rewrites &&
        m68k_is_elided_lea_noop(optimized_statement_text))
      continue;
    {
      M68kParseDataDirectiveResult data_directive = m68k_parse_data_directive_token(directive0);
      if (data_directive.ok && data_directive.is_repeat == 0U) {
        M68kSourceModelIndexResult stmt_result;
        AsmSourceStmt *stmt = NULL;
        stmt_result = m68k_source_model_append_statement(source, ASM_SOURCE_STMT_DATA, line_number);
        if (!stmt_result.ok) {
          fclose(input);
          source_parse_errorf(diagnostics,
                     "bad data directive at line %u: %s %s",
                     (unsigned)line_number, token0, rest);
          return 0;
        }
        stmt = &source->statements[stmt_result.index];
        if (!m68k_source_parse_data_statement(token0, rest, &stmt->u.data, &data_parse_context)) {
          fclose(input);
          source_parse_errorf(diagnostics,
                     "bad data directive at line %u: %s %s",
                     (unsigned)line_number, token0, rest);
          return 0;
        }
        stmt->section_index = current_section_index;
        continue;
      }
      if (data_directive.ok && data_directive.is_repeat != 0U) {
        M68kSourceModelIndexResult stmt_result;
        AsmSourceStmt *stmt = NULL;
        stmt_result = m68k_source_model_append_statement(source, ASM_SOURCE_STMT_DATA, line_number);
        if (!stmt_result.ok) {
          fclose(input);
          source_parse_errorf(diagnostics,
                     "bad data directive at line %u: %s %s",
                     (unsigned)line_number, token0, rest);
          return 0;
        }
        stmt = &source->statements[stmt_result.index];
        if (!m68k_source_parse_dcb_statement(token0, rest, &stmt->u.data, &data_parse_context)) {
          fclose(input);
          source_parse_errorf(diagnostics,
                     "bad data directive at line %u: %s %s",
                     (unsigned)line_number, token0, rest);
          return 0;
        }
        stmt->section_index = current_section_index;
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
        fclose(input);
        source_parse_error(diagnostics, "out of memory");
        return 0;
      }
      stmt = &source->statements[stmt_result.index];
      m68k_diag_list_reset(&parse_diagnostics);
      stmt->u.instruction.parsed_ir = m68k_plain_parse_instruction_to_ir(optimized_statement_text,
        source->target_cpu, m68k_diag_sink(&parse_diagnostics));
      parse_ok = !m68k_diag_has_errors(&parse_diagnostics);
      if (!parse_ok) {
        parse_ok = m68k_parse_instruction_with_symbol_fallback_ir( &symbolic_parse_context, optimized_statement_text,
            &stmt->u.instruction.parsed_ir, last_symbol_fallback_line,
            sizeof(last_symbol_fallback_line));
      }
      if (!parse_ok) {
        fclose(input);
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
      stmt->section_index = current_section_index;
      stmt->u.instruction.requested_size_suffix =
          m68k_requested_size_suffix_from_text(statement_text);
    }
  }
  fclose(input);
  return 1;
}


