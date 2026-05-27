#include "m68k_source_include.h"
#include "m68k_parse_util.h"
#include "m68k_source_text_util.h"

#include <ctype.h>
#include <stdio.h>
#include <string.h>

static void source_include_error(M68kDiagSink diagnostics, const char *message) {
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_SOURCE_FAILED, message);
}


static int parse_include_quoted_path_local(const char *text, char *out_path,
                                           size_t out_path_size) {
  const char *first_quote;
  const char *last_quote;
  char quote;
  size_t length;
  while (*text != '\0' && isspace((unsigned char)*text)) ++text;
  if (*text != '"' && *text != '\'') return 0;
  quote = *text;
  first_quote = text;
  last_quote = strrchr(text + 1, quote);
  if (last_quote == NULL || last_quote <= first_quote) return 0;
  length = (size_t)(last_quote - first_quote - 1);
  if (length >= out_path_size)
    return 0;
  memcpy(out_path, first_quote + 1, length);
  out_path[length] = '\0';
  return 1;
}

static int current_conditional_is_active(const M68kSourceIncludeState *state) {
  if (state->conditional_count == 0U)
    return 1;
  return state->conditionals[state->conditional_count - 1U].this_active;
}

static int push_conditional(M68kSourceIncludeState *state, int this_active) {
  if (state->conditional_count >=
      sizeof(state->conditionals) / sizeof(state->conditionals[0]))
    return 0;
  state->conditionals[state->conditional_count].parent_active =
      (state->conditional_count == 0U)
          ? 1
          : state->conditionals[state->conditional_count - 1U].this_active;
  state->conditionals[state->conditional_count].this_active =
      state->conditionals[state->conditional_count].parent_active &&
      this_active;
  state->conditional_count += 1U;
  return 1;
}

static int pop_conditional(M68kSourceIncludeState *state) {
  if (state->conditional_count == 0U)
    return 0;
  state->conditional_count -= 1U;
  return 1;
}

static int parse_ifc_args(const char *text, char *left, size_t left_size,
                          char *right, size_t right_size) {
  const char *comma = strchr(text, ',');
  size_t left_length;
  size_t right_length;
  const char *right_text;
  if (comma == NULL)
    return 0;
  while (*text != '\0' && isspace((unsigned char)*text))
    ++text;
  while (*comma != '\0' && isspace((unsigned char)comma[-1]))
    --comma;
  left_length = (size_t)(comma - text);
  right_text = strchr(text, ',');
  if (right_text == NULL)
    return 0;
  ++right_text;
  while (*right_text != '\0' && isspace((unsigned char)*right_text))
    ++right_text;
  right_length = strlen(right_text);
  while (right_length > 0U &&
         isspace((unsigned char)right_text[right_length - 1U]))
    --right_length;
  if (left_length >= left_size || right_length >= right_size)
    return 0;
  memcpy(left, text, left_length);
  left[left_length] = '\0';
  memcpy(right, right_text, right_length);
  right[right_length] = '\0';
  return 1;
}

static int parse_structure_builtin(const M68kSourceIncludeContext *context,
                                   char *rest) {
  char *comma = strchr(rest, ',');
  M68kSourceConstantResult value;
  if (comma == NULL)
    return 0;
  *comma = '\0';
  if (!context->set_constant(m68k_trim_in_place(rest), 0U, 0,
                             context->user_data))
    return 0;
  value = context->parse_constant(m68k_trim_in_place(comma + 1), context->user_data);
  if (!value.ok)
    return 0;
  return context->set_constant("SOFFSET", value.value, 1, context->user_data);
}

static char *normalize_struct_size_expression(char *text) {
  char *expr = m68k_trim_in_place(text);
  size_t length = strlen(expr);
  if (length >= 2U && expr[0] == '<' && expr[length - 1U] == '>') {
    expr[length - 1U] = '\0';
    expr = m68k_trim_in_place(expr + 1);
  }
  return expr;
}

static int parse_struct_builtin(const M68kSourceIncludeContext *context,
                                char *rest) {
  char *comma = strchr(rest, ',');
  uint32_t current_offset = 0;
  M68kSourceConstantResult value;
  if (comma == NULL)
    return 0;
  *comma = '\0';
  {
    M68kSourceLookupResult offset = context->lookup_defined("SOFFSET", 1, context->user_data);
    if (!offset.ok || !offset.defined) return 0;
    current_offset = offset.value;
  }
  if (!context->set_constant(m68k_trim_in_place(rest), current_offset, 0, context->user_data))
    return 0;
  value = context->parse_constant(normalize_struct_size_expression(comma + 1), context->user_data);
  if (!value.ok)
    return 0;
  return context->set_constant("SOFFSET", current_offset + value.value, 1,
                               context->user_data);
}

static int parse_label_builtin(const M68kSourceIncludeContext *context,
                               char *rest) {
  M68kSourceLookupResult current_offset = context->lookup_defined("SOFFSET", 1, context->user_data);
  if (!current_offset.ok || !current_offset.defined)
    return 0;
  return context->set_constant(m68k_trim_in_place(rest), current_offset.value, 0,
                               context->user_data);
}

static int parse_offset_builtin(const M68kSourceIncludeContext *context,
                                char *rest, uint32_t delta, M68kDiagSink diagnostics) {
  M68kSourceLookupResult current_offset = context->lookup_defined("SOFFSET", 1, context->user_data);
  char *name = m68k_trim_in_place(rest);
  if (!current_offset.ok || !current_offset.defined) {
    source_include_error(diagnostics, "offset directive before active structure");
    return 0;
  }
  if (!context->set_constant(name, current_offset.value, 0, context->user_data)) {
    m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_SOURCE_FAILED,
      "failed defining include offset label %.96s", name);
    return 0;
  }
  if (!context->set_constant("SOFFSET", current_offset.value + delta, 1, context->user_data)) {
    source_include_error(diagnostics, "failed updating include structure offset");
    return 0;
  }
  return 1;
}

static int parse_bitdef_builtin(const M68kSourceIncludeContext *context,
                                char *rest) {
  char buffer[128];
  char *parts[3];
  size_t count;
  M68kSourceConstantResult bit_value;
  snprintf(buffer, sizeof(buffer), "%s", rest);
  count = m68k_split_delimited_in_place(buffer, ',', parts,
                                        sizeof(parts) / sizeof(parts[0]));
  if (count != 3U)
    return 0;
  bit_value = context->parse_constant(m68k_trim_in_place(parts[2]), context->user_data);
  if (!bit_value.ok)
    return 0;
  {
    char name_buffer[128];
    snprintf(name_buffer, sizeof(name_buffer), "%sB_%s",
             m68k_trim_in_place(parts[0]), m68k_trim_in_place(parts[1]));
    if (!context->set_constant(name_buffer, bit_value.value, 0, context->user_data))
      return 0;
    snprintf(name_buffer, sizeof(name_buffer), "%sF_%s",
             m68k_trim_in_place(parts[0]), m68k_trim_in_place(parts[1]));
    return context->set_constant(name_buffer,
                                 (bit_value.value >= 31U) ? 0U : (1U << bit_value.value), 0,
                                 context->user_data);
  }
}

static int parse_libinit_builtin(const M68kSourceIncludeContext *context,
                                 char *rest) {
  uint32_t base_value = 0;
  if (*m68k_trim_in_place(rest) == '\0') {
    M68kSourceLookupResult base = context->lookup_defined("LIB_USERDEF", 1, context->user_data);
    if (!base.ok || !base.defined) return 0;
    base_value = base.value;
  } else {
    M68kSourceConstantResult base = context->parse_constant(m68k_trim_in_place(rest), context->user_data);
    if (!base.ok) return 0;
    base_value = base.value;
  }
  return context->set_constant("COUNT_LIB", base_value, 1, context->user_data);
}

static int parse_libdef_builtin(const M68kSourceIncludeContext *context,
                                char *rest) {
  M68kSourceLookupResult count_lib = context->lookup_defined("COUNT_LIB", 1, context->user_data);
  M68kSourceLookupResult vect_size = context->lookup_defined("LIB_VECTSIZE", 1, context->user_data);
  if (!count_lib.ok || !count_lib.defined || !vect_size.ok || !vect_size.defined)
    return 0;
  if (!context->set_constant(m68k_trim_in_place(rest), count_lib.value, 0,
                             context->user_data))
    return 0;
  return context->set_constant("COUNT_LIB", count_lib.value - vect_size.value, 1,
                               context->user_data);
}

static int parse_devinit_builtin(const M68kSourceIncludeContext *context,
                                 char *rest) {
  uint32_t base_value = 0;
  if (*m68k_trim_in_place(rest) == '\0') {
    M68kSourceLookupResult base = context->lookup_defined("CMD_NONSTD", 1, context->user_data);
    if (!base.ok || !base.defined) return 0;
    base_value = base.value;
  } else {
    M68kSourceConstantResult base = context->parse_constant(m68k_trim_in_place(rest), context->user_data);
    if (!base.ok) return 0;
    base_value = base.value;
  }
  return context->set_constant("CMD_COUNT", base_value, 1, context->user_data);
}

static int parse_devcmd_builtin(const M68kSourceIncludeContext *context,
                                char *rest) {
  M68kSourceLookupResult count_value = context->lookup_defined("CMD_COUNT", 1, context->user_data);
  if (!count_value.ok || !count_value.defined)
    return 0;
  if (!context->set_constant(m68k_trim_in_place(rest), count_value.value, 0,
                             context->user_data))
    return 0;
  return context->set_constant("CMD_COUNT", count_value.value + 1U, 1,
                               context->user_data);
}

static int parse_enum_builtin(const M68kSourceIncludeContext *context,
                              char *rest) {
  char *expr = m68k_trim_in_place(rest);
  uint32_t base_value = 0U;
  if (*expr != '\0') {
    M68kSourceConstantResult base = context->parse_constant(expr, context->user_data);
    if (!base.ok) return 0;
    base_value = base.value;
  }
  return context->set_constant("EOFFSET", base_value, 1, context->user_data);
}

static int parse_eitem_builtin(const M68kSourceIncludeContext *context,
                               char *rest) {
  char *name = m68k_trim_in_place(rest);
  char *comma = strchr(name, ',');
  M68kSourceLookupResult current_offset;
  if (comma != NULL) *comma = '\0';
  name = m68k_trim_in_place(name);
  if (*name == '\0') return 0;
  current_offset = context->lookup_defined("EOFFSET", 1, context->user_data);
  if (!current_offset.ok || !current_offset.defined) return 0;
  if (!context->set_constant(name, current_offset.value, 0, context->user_data)) return 0;
  return context->set_constant("EOFFSET", current_offset.value + 1U, 1, context->user_data);
}

static int parse_libent_builtin(const M68kSourceIncludeContext *context,
                                char *rest) {
  M68kSourceLookupResult count_value = context->lookup_defined("count", 1, context->user_data);
  M68kSourceLookupResult vsize;
  char name_buffer[128];
  if (!count_value.ok || !count_value.defined) return 0;
  snprintf(name_buffer, sizeof(name_buffer), "_LVO%s",
           m68k_trim_in_place(rest));
  if (!context->set_constant(name_buffer, count_value.value, 0, context->user_data))
    return 0;
  vsize = context->lookup_defined("vsize", 1, context->user_data);
  if (!vsize.ok || !vsize.defined) return 0;
  count_value = context->lookup_defined("count", 1, context->user_data);
  if (!count_value.ok || !count_value.defined) return 0;
  return context->set_constant("count", count_value.value - vsize.value, 1,
                               context->user_data);
}

static int parse_opword_definition(const M68kSourceIncludeContext *context,
                                   char *name, char *expr_text) {
  size_t name_length;
  M68kSourceConstantResult value;
  name = m68k_trim_in_place(name);
  name_length = strlen(name);
  if (name_length != 0U && name[name_length - 1U] == ':') name[name_length - 1U] = '\0';
  if (name[0] == '\0') return 0;
  value = context->parse_constant(m68k_trim_in_place(expr_text), context->user_data);
  if (!value.ok) return 0;
  return context->set_constant(name, value.value, 0, context->user_data);
}

static int process_include_line(const M68kSourceIncludeContext *context,
                                M68kSourceIncludeState *state, char *line,
                                M68kDiagSink diagnostics);

static void trim_trailing_line_continuation_in_place(char *line) {
  size_t length;
  if (line == NULL) return;
  length = strlen(line);
  while (length > 0U && isspace((unsigned char)line[length - 1U])) {
    line[length - 1U] = '\0';
    --length;
  }
  if (length > 0U && line[length - 1U] == '\\') {
    line[length - 1U] = '\0';
    --length;
    while (length > 0U && isspace((unsigned char)line[length - 1U])) {
      line[length - 1U] = '\0';
      --length;
    }
  }
}

int m68k_source_include_process_file(const M68kSourceIncludeContext *context,
                                     M68kSourceIncludeState *state,
                                     const char *path, M68kDiagSink diagnostics) {
  FILE *input = fopen(path, "r");
  char line[256];
  unsigned line_number = 0U;
  if (input == NULL) {
    source_include_error(diagnostics, "failed opening include file");
    return 0;
  }
  while (fgets(line, sizeof(line), input) != NULL) {
    ++line_number;
    if (!process_include_line(context, state, line, diagnostics)) {
      if (!m68k_diag_has_errors(diagnostics.list)) {
        m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_SOURCE_FAILED,
          "failed processing include file %s at line %u", path, line_number);
      }
      fclose(input);
      return 0;
    }
  }
  fclose(input);
  return 1;
}

static int process_include_line(const M68kSourceIncludeContext *context,
                                M68kSourceIncludeState *state, char *line,
                                M68kDiagSink diagnostics) {
  char *rest = NULL;
  char *token0 = NULL;
  char *token1 = NULL;
  M68kSourceDirectiveToken directive0 = M68K_SOURCE_DIRECTIVE_NONE;
  m68k_strip_comment_in_place(line);
  trim_trailing_line_continuation_in_place(line);
  rest = m68k_trim_in_place(line);
  if (*rest == '\0' || *rest == '*')
    return 1;
  {
    char *cursor = rest;
    token0 = m68k_next_token_in_place(&cursor);
    rest = m68k_trim_in_place(cursor);
    directive0 = m68k_parse_source_directive_token(token0);
    if (directive0 == M68K_SOURCE_DIRECTIVE_ENDM) {
      state->inside_macro_definition = 0;
      return 1;
    }
    if (state->inside_macro_definition)
      return 1;
    if (directive0 == M68K_SOURCE_DIRECTIVE_IFD || directive0 == M68K_SOURCE_DIRECTIVE_IFND) {
      M68kSourceLookupResult lookup_result = context->lookup_defined(m68k_trim_in_place(rest), 0, context->user_data);
      int defined = lookup_result.ok && lookup_result.defined;
      return push_conditional(state, (directive0 == M68K_SOURCE_DIRECTIVE_IFD) ? defined : !defined);
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_IFC || directive0 == M68K_SOURCE_DIRECTIVE_IFNC) {
      char left[64];
      char right[64];
      int equal = 0;
      if (!parse_ifc_args(rest, left, sizeof(left), right, sizeof(right)))
        return 0;
      equal = (strcmp(left, right) == 0);
      return push_conditional(state,
                              (directive0 == M68K_SOURCE_DIRECTIVE_IFC) ? equal : !equal);
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_ENDC)
      return pop_conditional(state);
    if (!current_conditional_is_active(state)) {
      if (m68k_parse_source_directive_token(rest) == M68K_SOURCE_DIRECTIVE_MACRO)
        state->inside_macro_definition = 1;
      return 1;
    }
    if (m68k_parse_source_directive_token(rest) == M68K_SOURCE_DIRECTIVE_MACRO ||
        directive0 == M68K_SOURCE_DIRECTIVE_MACRO) {
      state->inside_macro_definition = 1;
      return 1;
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_INCLUDE) {
      char include_path[512];
      char full_path[1024];
      if (!parse_include_quoted_path_local(rest, include_path,
                                          sizeof(include_path))) {
        m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_SOURCE_FAILED,
          "bad include path: %.96s", rest);
        return 0;
      }
      snprintf(full_path, sizeof(full_path), "%s\\%s", state->include_dir,
               include_path);
      return m68k_source_include_process_file(context, state, full_path, diagnostics);
    }
    if (*rest != '\0') {
      char *cursor1 = rest;
      M68kSourceDirectiveToken directive1 = M68K_SOURCE_DIRECTIVE_NONE;
      token1 = m68k_next_token_in_place(&cursor1);
      directive1 = m68k_parse_source_directive_token(token1);
      if (directive1 == M68K_SOURCE_DIRECTIVE_EQU || directive1 == M68K_SOURCE_DIRECTIVE_SET) {
        const char *expr_text = m68k_trim_in_place(cursor1);
        M68kSourceConstantResult value = context->parse_constant(expr_text, context->user_data);
        if (!value.ok) {
          m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_SOURCE_FAILED,
            "bad include constant expression %.96s", expr_text);
          return 0;
        }
        return context->set_constant(token0, value.value, directive1 == M68K_SOURCE_DIRECTIVE_SET,
          context->user_data);
      }
      if (directive1 == M68K_SOURCE_DIRECTIVE_OPWORD)
        return parse_opword_definition(context, token0, cursor1);
    }
    /* Supported include builtins are an explicit subset pinned by regression
     * coverage against Amiga NDK includes and Atari Devpac includes. */
    if (directive0 == M68K_SOURCE_DIRECTIVE_STRUCTURE)
      return parse_structure_builtin(context, rest);
    if (directive0 == M68K_SOURCE_DIRECTIVE_STRUCT)
      return parse_struct_builtin(context, rest);
    if (directive0 == M68K_SOURCE_DIRECTIVE_LABEL)
      return parse_label_builtin(context, rest);
    {
      M68kParseOffsetDirectiveResult offset_directive = m68k_parse_offset_directive_token(directive0);
      if (offset_directive.ok) return parse_offset_builtin(context, rest, offset_directive.delta, diagnostics);
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_ALIGNWORD) {
      M68kSourceLookupResult current_offset = context->lookup_defined("SOFFSET", 1, context->user_data);
      if (!current_offset.ok || !current_offset.defined)
        return 0;
      return context->set_constant("SOFFSET", (current_offset.value + 1U) & ~1U, 1,
                                   context->user_data);
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_ALIGNLONG) {
      M68kSourceLookupResult current_offset = context->lookup_defined("SOFFSET", 1, context->user_data);
      if (!current_offset.ok || !current_offset.defined)
        return 0;
      return context->set_constant("SOFFSET", (current_offset.value + 3U) & ~3U, 1,
                                   context->user_data);
    }
    if (directive0 == M68K_SOURCE_DIRECTIVE_BITDEF)
      return parse_bitdef_builtin(context, rest);
    if (directive0 == M68K_SOURCE_DIRECTIVE_LIBINIT)
      return parse_libinit_builtin(context, rest);
    if (directive0 == M68K_SOURCE_DIRECTIVE_LIBDEF)
      return parse_libdef_builtin(context, rest);
    if (directive0 == M68K_SOURCE_DIRECTIVE_LIBENT)
      return parse_libent_builtin(context, rest);
    if (directive0 == M68K_SOURCE_DIRECTIVE_DEVINIT)
      return parse_devinit_builtin(context, rest);
    if (directive0 == M68K_SOURCE_DIRECTIVE_DEVCMD)
      return parse_devcmd_builtin(context, rest);
    if (directive0 == M68K_SOURCE_DIRECTIVE_ENUM)
      return parse_enum_builtin(context, rest);
    if (directive0 == M68K_SOURCE_DIRECTIVE_EITEM)
      return parse_eitem_builtin(context, rest);
    return 1;
  }
}

void m68k_source_include_state_init(M68kSourceIncludeState *state,
                                    const char *include_dir) {
  memset(state, 0, sizeof(*state));
  if (include_dir != NULL)
    snprintf(state->include_dir, sizeof(state->include_dir), "%s", include_dir);
}


