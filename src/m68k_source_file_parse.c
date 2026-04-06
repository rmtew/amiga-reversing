#include "m68k_source_file_parse.h"

#include "m68k_parse_util.h"
#include "m68k_plain_parse.h"
#include "m68k_source_constant_expr.h"
#include "m68k_source_data.h"
#include "m68k_source_include.h"
#include "m68k_source_rewrite.h"
#include "m68k_source_text_util.h"
#include "m68k_symbolic_parse.h"
#include "platform_common.h"

#include <stdio.h>
#include <string.h>


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

static int lookup_defined_symbol_value(const AsmSourceFile *source,
                                       const char *name, uint32_t *out_value,
                                       int require_constant) {
  size_t index = 0;
  if (!m68k_source_model_find_symbol_index(source, name, &index))
    return 0;
  if (!source->symbols[index].defined)
    return 0;
  if (require_constant &&
      source->symbols[index].kind != ASM_SOURCE_SYMBOL_CONSTANT)
    return 0;
  if (out_value != NULL)
    *out_value = source->symbols[index].value;
  return 1;
}

static int source_lookup_constant_callback(const char *name,
                                           uint32_t *out_value,
                                           void *user_data) {
  return lookup_defined_symbol_value((const AsmSourceFile *)user_data, name,
                                     out_value, 1);
}

static int parse_constant_expression_value(const AsmSourceFile *source,
                                           const char *text,
                                           uint32_t *out_value) {
  return m68k_source_parse_constant_expression( text, source_lookup_constant_callback, (void *)source, out_value);
}

static int source_is_symbol_name(const char *text, void *user_data) {
  (void)user_data;
  return m68k_is_symbol_name(text);
}

static int source_rewrite_is_constant_symbol(const char *name,
                                             void *user_data) {
  const AsmSourceFile *source = (const AsmSourceFile *)user_data;
  size_t symbol_index = 0;
  return m68k_source_model_find_symbol_index(source, name, &symbol_index) &&
         source->symbols[symbol_index].kind == ASM_SOURCE_SYMBOL_CONSTANT;
}

static int source_rewrite_parse_constant(const char *text, uint32_t *out_value,
                                         void *user_data) {
  return parse_constant_expression_value((const AsmSourceFile *)user_data, text,
                                         out_value);
}

static int source_include_lookup_callback(const char *name, uint32_t *out_value,
                                          int require_constant,
                                          void *user_data) {
  return lookup_defined_symbol_value((const AsmSourceFile *)user_data, name,
                                     out_value, require_constant);
}

static int source_include_set_constant_callback(const char *name,
                                                uint32_t value,
                                                int allow_redefine,
                                                void *user_data) {
  return m68k_source_model_set_constant((AsmSourceFile *)user_data, name, value,
                                        allow_redefine);
}

static int source_parse_constant_callback(const char *text,
                                          uint32_t *out_value,
                                          void *user_data) {
  return parse_constant_expression_value((const AsmSourceFile *)user_data, text,
                                         out_value);
}

static int source_data_append_item_callback(AsmSourceDataStmt *data_stmt,
                                            const AsmDataItem *item,
                                            void *user_data) {
  (void)user_data;
  return m68k_source_model_append_data_item(data_stmt, item);
}


int m68k_source_file_parse(AsmSourceFile *source, const char *path,
                           char *out_error, size_t out_error_size) {
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
    m68k_platform_set_error(out_error, out_error_size, "failed opening source file");
    return 0;
  }
  while (fgets(line, sizeof(line), input) != NULL) {
    char *rest = NULL;
    char *cursor = NULL;
    char *token0 = NULL;
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
        AsmSourceStmt *label_stmt = NULL;
        *colon = '\0';
        if (!m68k_is_symbol_name(m68k_trim_in_place(rest))) {
          fclose(input);
          m68k_platform_set_errorf(out_error, out_error_size, "bad label at line %u",
                     (unsigned)line_number);
          return 0;
        }
        if (!m68k_source_model_ensure_symbol(source, m68k_trim_in_place(rest),
                                             ASM_SOURCE_SYMBOL_LABEL, NULL) ||
            !m68k_source_model_append_statement(source, ASM_SOURCE_STMT_LABEL,
                                                line_number, &label_stmt)) {
          fclose(input);
          m68k_platform_set_error(out_error, out_error_size, "out of memory");
          return 0;
        }
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
    if (_stricmp(token0, "INCLUDE") == 0) {
      char include_path[512];
      char full_path[1024];
      if (!parse_include_quoted_path(rest, include_path, sizeof(include_path))) {
        fclose(input);
        m68k_platform_set_errorf(out_error, out_error_size, "bad include path at line %u",
                   (unsigned)line_number);
        return 0;
      }
      snprintf(full_path, sizeof(full_path), "%s\\%s", source->include_dir,
               include_path);
      if (!m68k_source_include_process_file(&include_context, &include_state, full_path,
                                            out_error, out_error_size)) {
        fclose(input);
        return 0;
      }
      continue;
    }
    if (*rest != '\0') {
      char rest_copy[256];
      char *cursor1 = NULL;
      char *token1 = NULL;
      uint32_t value = 0;
      snprintf(rest_copy, sizeof(rest_copy), "%s", rest);
      cursor1 = rest_copy;
      token1 = m68k_next_token_in_place(&cursor1);
      if ((_stricmp(token1, "EQU") == 0 || _stricmp(token1, "SET") == 0) &&
          parse_constant_expression_value(source, m68k_trim_in_place(cursor1),
                                         &value) &&
          m68k_source_model_set_constant(source, token0, value,
                                         _stricmp(token1, "SET") == 0)) {
        continue;
      } else if (_stricmp(token1, "EQU") == 0 || _stricmp(token1, "SET") == 0) {
        fclose(input);
        m68k_platform_set_errorf(out_error, out_error_size, "bad source constant at line %u",
                   (unsigned)line_number);
        return 0;
      }
    }
    if (_stricmp(token0, "SECTION") == 0) {
      AsmSourceStmt *stmt = NULL;
      char buffer[128];
      char *parts[2];
      size_t count = 0;
      M68kSectionKind kind;
      snprintf(buffer, sizeof(buffer), "%s", rest);
      count = m68k_split_delimited_in_place(buffer, ',', parts,
                                            sizeof(parts) / sizeof(parts[0]));
      if (count != 2U || !m68k_parse_section_kind(m68k_trim_in_place(parts[1]), &kind) ||
          !m68k_source_model_append_statement(source, ASM_SOURCE_STMT_SECTION,
                                              line_number, &stmt) ||
          !m68k_source_model_append_section(source, m68k_trim_in_place(parts[0]), kind,
                                            &current_section_index)) {
        fclose(input);
        m68k_platform_set_errorf(out_error, out_error_size,
                   "bad section directive at line %u", (unsigned)line_number);
        return 0;
      }
      stmt->section_index = current_section_index;
      snprintf(stmt->u.section.name, sizeof(stmt->u.section.name), "%s",
               m68k_trim_in_place(parts[0]));
      stmt->u.section.kind = kind;
      continue;
    }
    if (_stricmp(token0, "EVEN") == 0) {
      AsmSourceStmt *stmt = NULL;
      if (!m68k_source_model_append_statement(source, ASM_SOURCE_STMT_EVEN,
                                              line_number, &stmt)) {
        fclose(input);
        m68k_platform_set_error(out_error, out_error_size, "out of memory");
        return 0;
      }
      stmt->section_index = current_section_index;
      continue;
    }
    if (_stricmp(token0, "END") == 0) {
      AsmSourceStmt *stmt = NULL;
      if (!m68k_source_model_append_statement(source, ASM_SOURCE_STMT_END,
                                              line_number, &stmt)) {
        fclose(input);
        m68k_platform_set_error(out_error, out_error_size, "out of memory");
        return 0;
      }
      stmt->section_index = current_section_index;
      break;
    }
    if (_stricmp(token0, "COMMENT") == 0) {
      const char *head_prefix = "HEAD=";
      size_t head_prefix_len = strlen(head_prefix);
      char *head_text = m68k_trim_in_place(rest);
      uint32_t value = 0;
      if (_strnicmp(head_text, head_prefix, head_prefix_len) == 0) {
        head_text = m68k_trim_in_place(head_text + head_prefix_len);
        if (!parse_constant_expression_value(source, head_text, &value)) {
          fclose(input);
          m68k_platform_set_errorf(out_error, out_error_size, "bad COMMENT HEAD directive at line %u",
                   (unsigned)line_number);
          return 0;
        }
        source->has_atari_st_program_flags = 1;
        source->atari_st_program_flags = value;
        continue;
      }
    }
    if (current_section_index == (size_t)-1) {
      fclose(input);
      m68k_platform_set_error(out_error, out_error_size, "source statement before section");
      return 0;
    }
    if (source->enable_vasm_compat_rewrites &&
        m68k_is_elided_lea_noop(optimized_statement_text))
      continue;
    if (_stricmp(token0, "DC.B") == 0 || _stricmp(token0, "DC.W") == 0 ||
        _stricmp(token0, "DC.L") == 0) {
      AsmSourceStmt *stmt = NULL;
      if (!m68k_source_model_append_statement(source, ASM_SOURCE_STMT_DATA,
                                              line_number, &stmt) ||
          !m68k_source_parse_data_statement(token0, rest, &stmt->u.data,
                                            &data_parse_context)) {
        fclose(input);
        m68k_platform_set_errorf(out_error, out_error_size,
                   "bad data directive at line %u: %s %s",
                   (unsigned)line_number, token0, rest);
        return 0;
      }
      stmt->section_index = current_section_index;
      continue;
    }
    if (_stricmp(token0, "DCB.B") == 0 || _stricmp(token0, "DCB.W") == 0 ||
        _stricmp(token0, "DCB.L") == 0) {
      AsmSourceStmt *stmt = NULL;
      if (!m68k_source_model_append_statement(source, ASM_SOURCE_STMT_DATA,
                                              line_number, &stmt) ||
          !m68k_source_parse_dcb_statement(token0, rest, &stmt->u.data,
                                           &data_parse_context)) {
        fclose(input);
        m68k_platform_set_errorf(out_error, out_error_size,
                   "bad data directive at line %u: %s %s",
                   (unsigned)line_number, token0, rest);
        return 0;
      }
      stmt->section_index = current_section_index;
      continue;
    }
    {
      AsmSourceStmt *stmt = NULL;
      int parse_ok;
      if (!m68k_source_model_append_statement(source, ASM_SOURCE_STMT_INSTRUCTION,
                                              line_number, &stmt)) {
        fclose(input);
        m68k_platform_set_error(out_error, out_error_size, "out of memory");
        return 0;
      }
      parse_ok = (m68k_plain_parse_instruction_to_ir( optimized_statement_text, source->target_cpu,
                       &stmt->u.instruction.parsed_ir, out_error,
                       out_error_size) == 0);
      if (!parse_ok) {
        parse_ok = m68k_parse_instruction_with_symbol_fallback_ir( &symbolic_parse_context, optimized_statement_text,
            &stmt->u.instruction.parsed_ir, last_symbol_fallback_line,
            sizeof(last_symbol_fallback_line));
      }
      if (!parse_ok) {
        fclose(input);
        if (strstr(statement_text, "MEMF_PUBLIC") != NULL ||
            strstr(statement_text, "MEMF_LARGEST") != NULL) {
          uint32_t public_value = 0;
          uint32_t largest_value = 0;
          uint32_t expr_value = 0;
          int have_public = lookup_defined_symbol_value(source, "MEMF_PUBLIC",
                                                        &public_value, 1);
          int have_largest = lookup_defined_symbol_value(source, "MEMF_LARGEST",
                                                         &largest_value, 1);
          int have_expr = parse_constant_expression_value( source, "MEMF_PUBLIC|MEMF_LARGEST", &expr_value);
          snprintf(out_error, out_error_size,
                   "unable to parse source line %u: %s | fallback=%s | "
                   "MEMF_PUBLIC=%d:%u MEMF_LARGEST=%d:%u EXPR=%d:%u",
                   (unsigned)line_number, statement_text,
                   last_symbol_fallback_line, have_public,
                   have_public ? public_value : 0U, have_largest,
                   have_largest ? largest_value : 0U, have_expr,
                   have_expr ? expr_value : 0U);
        } else {
          snprintf(out_error, out_error_size,
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


