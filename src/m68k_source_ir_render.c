#include "m68k_source_ir_render.h"
#include "generated/amiga_os_runtime.h"
#include "generated/atari_st_os_runtime.h"
#include "json_builder.h"
#include "m68k_ir_codec.h"
#include "m68k_parse_util.h"
#include "platform_common.h"

#include <stdio.h>
#include <string.h>

static int append_rendered_string_bytes(JsonBuilder *builder, const uint8_t *data, size_t size) {
  size_t index;
  if (json_builder_append(builder, "\"") != 0) return -1;
  for (index = 0; index < size; ++index) {
    unsigned char ch = data[index];
    if (ch == '"' || ch == '\\') {
      if (json_builder_appendf(builder, "\\%c", ch) != 0) return -1;
    } else if (ch >= 32U && ch <= 126U) {
      if (json_builder_appendf(builder, "%c", ch) != 0) return -1;
    } else if (json_builder_appendf(builder, "\\x%02x", (unsigned)ch) != 0) return -1;
  }
  return json_builder_append(builder, "\"");
}

static int data_string_is_plain_renderable(const uint8_t *data, size_t size) {
  size_t index;
  for (index = 0; index < size; ++index) {
    unsigned char ch = data[index];
    if (ch == '"' || ch == '\\') return 0;
  }
  return 1;
}

static int append_rendered_data_stmt(JsonBuilder *builder, const M68kDataItemIR *data, const M68kRenderPolicy *policy) {
  size_t index;
  const char *directive = (data->kind == M68K_DATA_ITEM_WORDS) ? "DC.W" : (data->kind == M68K_DATA_ITEM_LONGS) ? "DC.L"
    : "DC.B";
  size_t step = (data->kind == M68K_DATA_ITEM_WORDS)   ? 2U : (data->kind == M68K_DATA_ITEM_LONGS) ? 4U : 1U;
  size_t items_per_line = (data->kind == M68K_DATA_ITEM_LONGS) ? 8U : (data->kind == M68K_DATA_ITEM_WORDS) ? 12U : 16U;
  if (data->kind == M68K_DATA_ITEM_STRING && (policy == NULL || policy->presentation.prefer_strings != 0U) &&
      data_string_is_plain_renderable(data->data, data->size)) {
    size_t string_size = data->size;
    int has_trailing_nul = 0;
    if (json_builder_append(builder, "    DC.B    ") != 0) return -1;
    if (string_size != 0U && data->data[string_size - 1U] == 0U) {
      has_trailing_nul = 1;
      --string_size;
    }
    if (append_rendered_string_bytes(builder, data->data, string_size) != 0) return -1;
    if (has_trailing_nul && json_builder_append(builder, ",0") != 0) return -1;
    return 0;
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

static int append_statement_comment(JsonBuilder *builder, const M68kStatementIR *stmt) {
  if (stmt == NULL || stmt->comment == NULL || stmt->comment[0] == '\0') return json_builder_append(builder, "\n");
  if (strstr(stmt->comment, "CANDIDATE:") != NULL || strncmp(stmt->comment, "NOTE:", 5) == 0 ||
      strncmp(stmt->comment, "KNOWN:", 6) == 0)
    return json_builder_appendf(builder, " ; %s\n", stmt->comment);
  return json_builder_appendf(builder, " ; VIOLATION: %s\n", stmt->comment);
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

typedef struct RenderEquate {
  char name[64];
  int32_t value;
} RenderEquate;

typedef struct RenderInclude {
  char path[128];
} RenderInclude;

typedef int (*RenderSymbolVisitor)(const char *name, uint8_t provenance, void *context);

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

static int lookup_symbol_equate_value(const char *name, int32_t *out_value) {
  const AmigaOsLibraryVectorInfo *amiga_vector;
  const AtariStOsCallInfo *atari_call;
  const AmigaOsStructFieldInfo *amiga_field;
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
  return 0;
}

static int visit_operand_symbol_refs(const M68kOperandIR *operand, RenderSymbolVisitor visitor, void *context) {
  if (operand == NULL || visitor == NULL) return 0;
  if (operand->symbol_ref.has_name != 0U && operand->symbol_ref.name_is_generated == 0U &&
      visitor(operand->symbol_ref.name, operand->symbol_ref.name_provenance, context) != 0)
    return -1;
  if (operand->symbol_ref.has_symbolic_addend != 0U && operand->symbol_ref.symbolic_addend_name[0] != '\0' &&
      visitor(operand->symbol_ref.symbolic_addend_name, operand->symbol_ref.symbolic_addend_provenance, context) != 0)
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
} RenderIncludeCollectorContext;

static int collect_needed_include_symbol(const char *name, uint8_t provenance, void *opaque) {
  RenderIncludeCollectorContext *context = (RenderIncludeCollectorContext *)opaque;
  const char *include_path;
  include_path = lookup_symbol_include_path(context->source_file, name, provenance);
  if (include_path == NULL) return 0;
  return append_or_update_render_include(context->includes, context->include_count, context->include_capacity, include_path);
}

static int collect_needed_includes(RenderInclude *includes, size_t *out_include_count, size_t include_capacity,
    const M68kSourceFileIR *source_file) {
  size_t section_index;
  RenderIncludeCollectorContext context;
  *out_include_count = 0U;
  context.includes = includes;
  context.include_count = out_include_count;
  context.include_capacity = include_capacity;
  context.source_file = source_file;
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
      _stricmp(stmt->u.instruction.mnemonic, "moveq") == 0) {
    return (int32_t)m68k_sign_extend32(operand->value.value, 8U);
  }
  return (int16_t)(operand != NULL ? (operand->value.value & 0xFFFFU) : 0U);
}

static int append_or_update_render_equate(RenderEquate *equates, size_t *inout_equate_count,
    size_t equate_capacity, const char *name, int32_t value) {
  size_t equate_index;
  if (equates == NULL || inout_equate_count == NULL || name == NULL || name[0] == '\0') return -1;
  for (equate_index = 0; equate_index < *inout_equate_count; ++equate_index) {
    if (strcmp(equates[equate_index].name, name) == 0) {
      equates[equate_index].value = value;
      return 0;
    }
  }
  if (*inout_equate_count >= equate_capacity) return -1;
  snprintf(equates[*inout_equate_count].name, sizeof(equates[*inout_equate_count].name), "%s", name);
  equates[*inout_equate_count].value = value;
  ++(*inout_equate_count);
  return 0;
}

typedef struct RenderEquateCollectorContext {
  RenderEquate *equates;
  size_t *equate_count;
  size_t equate_capacity;
  const M68kSourceFileIR *source_file;
} RenderEquateCollectorContext;

static int collect_data_expr_equate_symbol(const char *name, uint8_t provenance, void *opaque) {
  RenderEquateCollectorContext *context = (RenderEquateCollectorContext *)opaque;
  int32_t value;
  if (lookup_symbol_include_path(context->source_file, name, provenance) != NULL) return 0;
  if (!lookup_symbol_equate_value(name, &value)) return 0;
  return append_or_update_render_equate(context->equates, context->equate_count, context->equate_capacity, name, value);
}

static int append_needed_equates(JsonBuilder *builder, const M68kSourceFileIR *source_file) {
  RenderEquate equates[128];
  size_t equate_count = 0U;
  size_t section_index;
  RenderEquateCollectorContext context;
  context.equates = equates;
  context.equate_count = &equate_count;
  context.equate_capacity = sizeof(equates) / sizeof(equates[0]);
  context.source_file = source_file;
  for (section_index = 0; section_index < source_file->section_count; ++section_index) {
    const M68kSectionIR *section = &source_file->sections[section_index];
    size_t stmt_index;
    for (stmt_index = 0; stmt_index < section->statement_count; ++stmt_index) {
      const M68kStatementIR *stmt = &section->statements[stmt_index];
      size_t operand_index;
        if (stmt->kind == M68K_STATEMENT_DATA) {
          if (visit_expr_text_symbols(stmt->u.data.expr_text, collect_data_expr_equate_symbol, &context) != 0) return -1;
          continue;
        }
        if (stmt->kind != M68K_STATEMENT_INSTRUCTION) continue;
          for (operand_index = 0; operand_index < stmt->u.instruction.operand_count; ++operand_index) {
            const M68kOperandIR *operand = &stmt->u.instruction.operands[operand_index];
            int32_t total_value;
            if (operand->symbol_ref.has_name == 0U || operand->symbol_ref.name_is_generated != 0U) continue;
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
              if (lookup_symbol_include_path(source_file, operand->symbol_ref.name,
                    operand->symbol_ref.name_provenance) == NULL) {
                if (append_or_update_render_equate(equates, &equate_count, sizeof(equates) / sizeof(equates[0]),
                      operand->symbol_ref.name, total_value - operand->symbol_ref.symbolic_addend_value) != 0) {
                  return -1;
                }
              }
              if (lookup_symbol_include_path(source_file, operand->symbol_ref.symbolic_addend_name,
                    operand->symbol_ref.symbolic_addend_provenance) == NULL) {
                if (append_or_update_render_equate(equates, &equate_count, sizeof(equates) / sizeof(equates[0]),
                      operand->symbol_ref.symbolic_addend_name, operand->symbol_ref.symbolic_addend_value) != 0) {
                  return -1;
                }
              }
              continue;
            }
            if (lookup_symbol_include_path(source_file, operand->symbol_ref.name,
                  operand->symbol_ref.name_provenance) == NULL) {
              if (append_or_update_render_equate(equates, &equate_count, sizeof(equates) / sizeof(equates[0]),
                    operand->symbol_ref.name, total_value) != 0) {
                return -1;
              }
            }
      }
    }
  }
  for (section_index = 0; section_index < equate_count; ++section_index) {
    if (json_builder_appendf(builder, "%s EQU %d\n", equates[section_index].name, (int)equates[section_index].value) != 0)
      return -1;
  }
  if (equate_count != 0U && json_builder_append(builder, "\n") != 0) return -1;
  return 0;
}

int m68k_source_ir_render_text_with_policy(const M68kSourceFileIR *source_file, const M68kRenderPolicy *policy,
    char **out_text, char *out_error, size_t out_error_size) {
  JsonBuilder builder = {0};
  RenderInclude includes[32];
  size_t include_count = 0U;
  size_t section_index;
  M68kRenderPolicy default_policy;
  const M68kRenderPolicy *active_policy = policy;
  if (source_file == NULL || out_text == NULL) {
    m68k_platform_set_error(out_error, out_error_size, "bad arguments");
    return -1;
  }
  if (active_policy == NULL) {
    m68k_render_policy_init_default(&default_policy);
    active_policy = &default_policy;
  }
  if (json_builder_create(&builder) != 0) goto oom;
  if (collect_needed_includes(includes, &include_count, sizeof(includes) / sizeof(includes[0]), source_file) != 0) goto oom;
  for (section_index = 0; section_index < include_count; ++section_index) {
    if (json_builder_appendf(&builder, "    INCLUDE \"%s\"\n", includes[section_index].path) != 0) goto oom;
  }
  if (include_count != 0U && json_builder_append(&builder, "\n") != 0) goto oom;
  if (append_needed_equates(&builder, source_file) != 0) goto oom;
  if (source_file->has_atari_st_program_flags != 0U &&
      json_builder_appendf(&builder, "    COMMENT HEAD=$%x\n", (unsigned)source_file->atari_st_program_flags) != 0)
    goto oom;
  for (section_index = 0; section_index < source_file->section_count; ++section_index) {
    const M68kSectionIR *section = &source_file->sections[section_index];
    size_t stmt_index;
    const char *section_name = (section->name != NULL && section->name[0] != '\0') ? section->name : "section";
    const char *section_kind = (section->kind == M68K_SECTION_CODE)   ? "code"
      : (section->kind == M68K_SECTION_DATA) ? "data" : "bss";
    if (json_builder_appendf(&builder, "    SECTION %s,%s\n", section_name, section_kind) != 0) goto oom;
    for (stmt_index = 0; stmt_index < section->statement_count; ++stmt_index) {
      const M68kStatementIR *stmt = &section->statements[stmt_index];
      if (stmt->kind == M68K_STATEMENT_LABEL) {
        if (json_builder_appendf(&builder, "%s:\n", stmt->label_name != NULL ? stmt->label_name : "label") != 0)
          goto oom;
      } else if (stmt->kind == M68K_STATEMENT_ALIGN) {
        if (json_builder_append(&builder, "    EVEN\n") != 0) goto oom;
      } else if (stmt->kind == M68K_STATEMENT_INSTRUCTION) {
        M68kInstructionIR rendered_instruction = stmt->u.instruction;
        char text[256];
        size_t operand_index;
        for (operand_index = 0; operand_index < rendered_instruction.operand_count; ++operand_index) {
          M68kOperandIR *operand = &rendered_instruction.operands[operand_index];
          if (operand->symbol_ref.has_name == 0U) continue;
          if (operand->symbol_ref.name_is_generated != 0U &&
              !section_has_label_name(section, operand->symbol_ref.name)) {
            operand->symbol_ref.has_name = 0U;
          }
        }
        if (m68k_ir_render_one_at_with_policy(&rendered_instruction, stmt->offset, active_policy, text, sizeof(text), out_error,
            out_error_size) != 0) {
          json_builder_destroy(&builder);
          return -1;
        }
        if (json_builder_appendf(&builder, "    %s", text) != 0) goto oom;
        if (append_statement_comment(&builder, stmt) != 0) goto oom;
      } else if (stmt->kind == M68K_STATEMENT_DATA) {
        if (append_rendered_data_stmt(&builder, &stmt->u.data, active_policy) != 0) goto oom;
        if (append_statement_comment(&builder, stmt) != 0) goto oom;
      }
    }
  }
  *out_text = json_builder_build(&builder);
  if (*out_text == NULL) goto oom;
  json_builder_destroy(&builder);
  m68k_platform_set_error(out_error, out_error_size, "");
  return 0;

oom:
  json_builder_destroy(&builder);
  m68k_platform_set_error(out_error, out_error_size, "out of memory");
  return -1;
}
