#include "m68k_source_include.h"
#include "m68k_source_text_util.h"
#include "platform_common.h"

#include <ctype.h>
#include <stdio.h>
#include <string.h>


static int parse_include_quoted_path_local(const char *text, char *out_path,
                                           size_t out_path_size) {
  const char *first_quote = strchr(text, '"');
  const char *last_quote = strrchr(text, '"');
  size_t length;
  if (first_quote == NULL || last_quote == NULL || last_quote <= first_quote)
    return 0;
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
  uint32_t value = 0;
  if (comma == NULL)
    return 0;
  *comma = '\0';
  if (!context->set_constant(m68k_trim_in_place(rest), 0U, 0,
                             context->user_data))
    return 0;
  if (!context->parse_constant(m68k_trim_in_place(comma + 1), &value,
                               context->user_data))
    return 0;
  return context->set_constant("SOFFSET", value, 1, context->user_data);
}

static int parse_struct_builtin(const M68kSourceIncludeContext *context,
                                char *rest) {
  char *comma = strchr(rest, ',');
  uint32_t current_offset = 0;
  uint32_t value = 0;
  if (comma == NULL)
    return 0;
  *comma = '\0';
  if (!context->lookup_defined("SOFFSET", &current_offset, 1,
                               context->user_data))
    return 0;
  if (!context->set_constant(m68k_trim_in_place(rest), current_offset, 0,
                             context->user_data))
    return 0;
  if (!context->parse_constant(m68k_trim_in_place(comma + 1), &value,
                               context->user_data))
    return 0;
  return context->set_constant("SOFFSET", current_offset + value, 1,
                               context->user_data);
}

static int parse_label_builtin(const M68kSourceIncludeContext *context,
                               char *rest) {
  uint32_t current_offset = 0;
  if (!context->lookup_defined("SOFFSET", &current_offset, 1,
                               context->user_data))
    return 0;
  return context->set_constant(m68k_trim_in_place(rest), current_offset, 0,
                               context->user_data);
}

static int parse_offset_builtin(const M68kSourceIncludeContext *context,
                                char *rest, uint32_t delta) {
  uint32_t current_offset = 0;
  if (!context->lookup_defined("SOFFSET", &current_offset, 1,
                               context->user_data))
    return 0;
  if (!context->set_constant(m68k_trim_in_place(rest), current_offset, 0,
                             context->user_data))
    return 0;
  return context->set_constant("SOFFSET", current_offset + delta, 1,
                               context->user_data);
}

static int parse_bitdef_builtin(const M68kSourceIncludeContext *context,
                                char *rest) {
  char buffer[128];
  char *parts[3];
  size_t count;
  uint32_t bit_value = 0;
  snprintf(buffer, sizeof(buffer), "%s", rest);
  count = m68k_split_delimited_in_place(buffer, ',', parts,
                                        sizeof(parts) / sizeof(parts[0]));
  if (count != 3U)
    return 0;
  if (!context->parse_constant(m68k_trim_in_place(parts[2]), &bit_value,
                               context->user_data))
    return 0;
  {
    char name_buffer[128];
    snprintf(name_buffer, sizeof(name_buffer), "%sB_%s",
             m68k_trim_in_place(parts[0]), m68k_trim_in_place(parts[1]));
    if (!context->set_constant(name_buffer, bit_value, 0, context->user_data))
      return 0;
    snprintf(name_buffer, sizeof(name_buffer), "%sF_%s",
             m68k_trim_in_place(parts[0]), m68k_trim_in_place(parts[1]));
    return context->set_constant(name_buffer,
                                 (bit_value >= 31U) ? 0U : (1U << bit_value), 0,
                                 context->user_data);
  }
}

static int parse_libinit_builtin(const M68kSourceIncludeContext *context,
                                 char *rest) {
  uint32_t base_value = 0;
  if (*m68k_trim_in_place(rest) == '\0') {
    if (!context->lookup_defined("LIB_USERDEF", &base_value, 1,
                                 context->user_data))
      return 0;
  } else {
    if (!context->parse_constant(m68k_trim_in_place(rest), &base_value,
                                 context->user_data))
      return 0;
  }
  return context->set_constant("COUNT_LIB", base_value, 1, context->user_data);
}

static int parse_libdef_builtin(const M68kSourceIncludeContext *context,
                                char *rest) {
  uint32_t count_lib = 0;
  uint32_t vect_size = 0;
  if (!context->lookup_defined("COUNT_LIB", &count_lib, 1, context->user_data))
    return 0;
  if (!context->lookup_defined("LIB_VECTSIZE", &vect_size, 1,
                               context->user_data))
    return 0;
  if (!context->set_constant(m68k_trim_in_place(rest), count_lib, 0,
                             context->user_data))
    return 0;
  return context->set_constant("COUNT_LIB", count_lib - vect_size, 1,
                               context->user_data);
}

static int parse_devinit_builtin(const M68kSourceIncludeContext *context,
                                 char *rest) {
  uint32_t base_value = 0;
  if (*m68k_trim_in_place(rest) == '\0') {
    if (!context->lookup_defined("CMD_NONSTD", &base_value, 1,
                                 context->user_data))
      return 0;
  } else {
    if (!context->parse_constant(m68k_trim_in_place(rest), &base_value,
                                 context->user_data))
      return 0;
  }
  return context->set_constant("CMD_COUNT", base_value, 1, context->user_data);
}

static int parse_devcmd_builtin(const M68kSourceIncludeContext *context,
                                char *rest) {
  uint32_t count_value = 0;
  if (!context->lookup_defined("CMD_COUNT", &count_value, 1,
                               context->user_data))
    return 0;
  if (!context->set_constant(m68k_trim_in_place(rest), count_value, 0,
                             context->user_data))
    return 0;
  return context->set_constant("CMD_COUNT", count_value + 1U, 1,
                               context->user_data);
}

static int parse_libent_builtin(const M68kSourceIncludeContext *context,
                                char *rest) {
  uint32_t count_value = 0;
  char name_buffer[128];
  if (!context->lookup_defined("count", &count_value, 1, context->user_data))
    return 0;
  snprintf(name_buffer, sizeof(name_buffer), "_LVO%s",
           m68k_trim_in_place(rest));
  if (!context->set_constant(name_buffer, count_value, 0, context->user_data))
    return 0;
  if (!context->lookup_defined("vsize", &count_value, 1, context->user_data))
    return 0;
  {
    uint32_t current_count = 0;
    if (!context->lookup_defined("count", &current_count, 1,
                                 context->user_data))
      return 0;
    return context->set_constant("count", current_count - count_value, 1,
                                 context->user_data);
  }
}

static int process_include_line(const M68kSourceIncludeContext *context,
                                M68kSourceIncludeState *state, char *line,
                                char *out_error, size_t out_error_size);

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
                                     const char *path, char *out_error,
                                     size_t out_error_size) {
  FILE *input = fopen(path, "r");
  char line[256];
  if (input == NULL) {
    m68k_platform_set_error(out_error, out_error_size, "failed opening include file");
    return 0;
  }
  while (fgets(line, sizeof(line), input) != NULL) {
    if (!process_include_line(context, state, line, out_error,
                              out_error_size)) {
      fclose(input);
      return 0;
    }
  }
  fclose(input);
  return 1;
}

static int process_include_line(const M68kSourceIncludeContext *context,
                                M68kSourceIncludeState *state, char *line,
                                char *out_error, size_t out_error_size) {
  char *rest = NULL;
  char *token0 = NULL;
  char *token1 = NULL;
  m68k_strip_comment_in_place(line);
  trim_trailing_line_continuation_in_place(line);
  rest = m68k_trim_in_place(line);
  if (*rest == '\0' || *rest == '*')
    return 1;
  {
    char *cursor = rest;
    token0 = m68k_next_token_in_place(&cursor);
    rest = m68k_trim_in_place(cursor);
    if (_stricmp(token0, "ENDM") == 0) {
      state->inside_macro_definition = 0;
      return 1;
    }
    if (state->inside_macro_definition)
      return 1;
    if (_stricmp(token0, "IFND") == 0) {
      uint32_t ignored = 0;
      return push_conditional(state,
                              !context->lookup_defined(
                                  m68k_trim_in_place(rest), &ignored, 0,
                                  context->user_data));
    }
    if (_stricmp(token0, "IFC") == 0 || _stricmp(token0, "IFNC") == 0) {
      char left[64];
      char right[64];
      int equal = 0;
      if (!parse_ifc_args(rest, left, sizeof(left), right, sizeof(right)))
        return 0;
      equal = (strcmp(left, right) == 0);
      return push_conditional(state,
                              (_stricmp(token0, "IFC") == 0) ? equal : !equal);
    }
    if (_stricmp(token0, "ENDC") == 0)
      return pop_conditional(state);
    if (!current_conditional_is_active(state)) {
      if (_stricmp(rest, "MACRO") == 0)
        state->inside_macro_definition = 1;
      return 1;
    }
    if (_stricmp(rest, "MACRO") == 0 || _stricmp(token0, "MACRO") == 0) {
      state->inside_macro_definition = 1;
      return 1;
    }
    if (_stricmp(token0, "INCLUDE") == 0) {
      char include_path[512];
      char full_path[1024];
      if (!parse_include_quoted_path_local(rest, include_path,
                                          sizeof(include_path))) {
        m68k_platform_set_error(out_error, out_error_size, "bad include path");
        return 0;
      }
      snprintf(full_path, sizeof(full_path), "%s\\%s", state->include_dir,
               include_path);
      return m68k_source_include_process_file(context, state, full_path,
                                              out_error, out_error_size);
    }
    if (*rest != '\0') {
      char *cursor1 = rest;
      token1 = m68k_next_token_in_place(&cursor1);
      if (_stricmp(token1, "EQU") == 0 || _stricmp(token1, "SET") == 0) {
        uint32_t value = 0;
        if (!context->parse_constant(m68k_trim_in_place(cursor1), &value,
                                     context->user_data)) {
          m68k_platform_set_error(out_error, out_error_size, "bad constant expression");
          return 0;
        }
        return context->set_constant( token0, value, _stricmp(token1, "SET") == 0, context->user_data);
      }
    }
    if (_stricmp(token0, "STRUCTURE") == 0)
      return parse_structure_builtin(context, rest);
    if (_stricmp(token0, "STRUCT") == 0)
      return parse_struct_builtin(context, rest);
    if (_stricmp(token0, "LABEL") == 0)
      return parse_label_builtin(context, rest);
    if (_stricmp(token0, "BYTE") == 0 || _stricmp(token0, "UBYTE") == 0)
      return parse_offset_builtin(context, rest, 1U);
    if (_stricmp(token0, "WORD") == 0 || _stricmp(token0, "UWORD") == 0 ||
        _stricmp(token0, "BOOL") == 0 || _stricmp(token0, "SHORT") == 0 ||
        _stricmp(token0, "USHORT") == 0 || _stricmp(token0, "RPTR") == 0) {
      return parse_offset_builtin(context, rest, 2U);
    }
    if (_stricmp(token0, "LONG") == 0 || _stricmp(token0, "ULONG") == 0 ||
        _stricmp(token0, "FLOAT") == 0 || _stricmp(token0, "APTR") == 0 ||
        _stricmp(token0, "CPTR") == 0 || _stricmp(token0, "FPTR") == 0) {
      return parse_offset_builtin(context, rest, 4U);
    }
    if (_stricmp(token0, "DOUBLE") == 0)
      return parse_offset_builtin(context, rest, 8U);
    if (_stricmp(token0, "ALIGNWORD") == 0) {
      uint32_t current_offset = 0;
      if (!context->lookup_defined("SOFFSET", &current_offset, 1,
                                   context->user_data))
        return 0;
      return context->set_constant("SOFFSET", (current_offset + 1U) & ~1U, 1,
                                   context->user_data);
    }
    if (_stricmp(token0, "ALIGNLONG") == 0) {
      uint32_t current_offset = 0;
      if (!context->lookup_defined("SOFFSET", &current_offset, 1,
                                   context->user_data))
        return 0;
      return context->set_constant("SOFFSET", (current_offset + 3U) & ~3U, 1,
                                   context->user_data);
    }
    if (_stricmp(token0, "BITDEF") == 0)
      return parse_bitdef_builtin(context, rest);
    if (_stricmp(token0, "LIBINIT") == 0)
      return parse_libinit_builtin(context, rest);
    if (_stricmp(token0, "LIBDEF") == 0)
      return parse_libdef_builtin(context, rest);
    if (_stricmp(token0, "LIBENT") == 0)
      return parse_libent_builtin(context, rest);
    if (_stricmp(token0, "DEVINIT") == 0)
      return parse_devinit_builtin(context, rest);
    if (_stricmp(token0, "DEVCMD") == 0)
      return parse_devcmd_builtin(context, rest);
    return 1;
  }
}

void m68k_source_include_state_init(M68kSourceIncludeState *state,
                                    const char *include_dir) {
  memset(state, 0, sizeof(*state));
  if (include_dir != NULL)
    snprintf(state->include_dir, sizeof(state->include_dir), "%s", include_dir);
}


