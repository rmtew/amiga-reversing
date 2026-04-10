#include "m68k_source_ir_render.h"
#include "json_builder.h"
#include "m68k_ir_codec.h"
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
  if (strstr(stmt->comment, "CANDIDATE:") != NULL || strncmp(stmt->comment, "NOTE:", 5) == 0)
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

int m68k_source_ir_render_text_with_policy(const M68kSourceFileIR *source_file, const M68kRenderPolicy *policy,
    char **out_text, char *out_error, size_t out_error_size) {
  JsonBuilder builder = {0};
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
          if (!section_has_label_name(section, operand->symbol_ref.name)) operand->symbol_ref.has_name = 0U;
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
