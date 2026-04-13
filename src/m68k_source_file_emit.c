#include "m68k_source_file_emit.h"
#include "m68k_ir_codec.h"
#include "platform_binary_io.h"
#include "platform_common.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define M68K_SOURCE_FILE_EMIT_MAX_FIXUP_OPERANDS 4
#define M68K_SOURCE_FILE_EMIT_MAX_CASE_BYTES 64

typedef struct M68kSourceEmitExprContext {
  M68kSourceExprLookupFn base_lookup;
  void *base_user_data;
  uint32_t current_offset;
} M68kSourceEmitExprContext;

static size_t data_statement_size(const AsmSourceDataStmt *data_stmt) {
  size_t total = 0;
  size_t index;
  for (index = 0; index < data_stmt->item_count; ++index) {
    total += (data_stmt->items[index].kind == ASM_DATA_ITEM_STRING)
      ? data_stmt->items[index].byte_count : data_stmt->width_bytes;
  }
  return total;
}

static int detect_fixup_span_ir(const M68kInstructionIR *instruction, int operand_index, size_t *out_start,
    size_t *out_width, char *out_error, size_t out_error_size) {
  static const uint32_t marker_values[] = {0x01010101U, 0x00000101U, 0x00000001U};
  size_t marker_index;
  for (marker_index = 0; marker_index < sizeof(marker_values) / sizeof(marker_values[0]);
       ++marker_index) {
    M68kInstructionIR baseline = *instruction;
    M68kInstructionIR marker = *instruction;
    unsigned char baseline_bytes[M68K_SOURCE_FILE_EMIT_MAX_CASE_BYTES];
    unsigned char marker_bytes[M68K_SOURCE_FILE_EMIT_MAX_CASE_BYTES];
    size_t baseline_size = 0;
    size_t marker_size = 0;
    size_t diff_start = (size_t)-1;
    size_t diff_end = 0;
    size_t index;
    baseline.operands[operand_index].value.value = 0U;
    marker.operands[operand_index].value.value = marker_values[marker_index];
    if (m68k_ir_encode_one(&baseline, baseline_bytes, sizeof(baseline_bytes), &baseline_size, out_error,
        out_error_size) != 0)
      continue;
    if (m68k_ir_encode_one(&marker, marker_bytes, sizeof(marker_bytes), &marker_size, out_error, out_error_size) != 0)
      continue;
    if (baseline_size != marker_size) continue;
    for (index = 0; index < baseline_size; ++index) {
      if (baseline_bytes[index] != marker_bytes[index]) {
        if (diff_start == (size_t)-1) diff_start = index;
        diff_end = index + 1U;
      }
    }
    if (diff_start == (size_t)-1) continue;
    for (index = diff_start; index < diff_end; ++index) {
      if (baseline_bytes[index] == marker_bytes[index]) {
        m68k_platform_set_error(out_error, out_error_size, "non-contiguous fixup field");
        return 0;
      }
    }
    *out_start = diff_start;
    *out_width = diff_end - diff_start;
    return 1;
  }
  m68k_platform_set_error(out_error, out_error_size, "failed detecting fixup span");
  return 0;
}

static int expr_lookup_symbol_with_current(const char *name, int *out_defined, int *out_is_constant, uint32_t *out_value,
    size_t *out_symbol_id, size_t *out_section_index, void *user_data) {
  const M68kSourceEmitExprContext *context = (const M68kSourceEmitExprContext *)user_data;
  if (strcmp(name, "*") == 0) {
    if (out_defined != NULL) *out_defined = 1;
    if (out_is_constant != NULL) *out_is_constant = 1;
    if (out_value != NULL) *out_value = context->current_offset;
    if (out_symbol_id != NULL) *out_symbol_id = (size_t)-1;
    if (out_section_index != NULL) *out_section_index = (size_t)-1;
    return 1;
  }
  return context->base_lookup(name, out_defined, out_is_constant, out_value, out_symbol_id, out_section_index,
    context->base_user_data);
}

static void init_emit_expr_context(M68kSourceEmitExprContext *context, M68kSourceExprLookupFn base_lookup,
    void *base_user_data, uint32_t current_offset) {
  context->base_lookup = base_lookup;
  context->base_user_data = base_user_data;
  context->current_offset = current_offset;
}

static int should_emit_internal_abs_fixup(const AsmSourceFile *source, M68kFixupWidth width) {
  if (source == NULL) return 1;
  if (source->file_kind == M68K_PLATFORM_FILE_EXECUTABLE &&
      source->platform_backend_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK &&
      width == M68K_FIXUP_WIDTH_16) {
    return 0;
  }
  return 1;
}

int m68k_source_file_layout(AsmSourceFile *source, const M68kSourceFileEmitContext *context,
    char *out_error, size_t out_error_size) {
  size_t pass_index;
  for (pass_index = 0; pass_index < 8U; ++pass_index) {
    uint32_t offsets[16] = {0};
    int changed = 0;
    size_t stmt_index;
    for (stmt_index = 0; stmt_index < source->statement_count; ++stmt_index) {
      AsmSourceStmt *stmt = &source->statements[stmt_index];
      if (stmt->kind == ASM_SOURCE_STMT_SECTION) continue;
      if (stmt->kind == ASM_SOURCE_STMT_END) break;
      if (stmt->kind == ASM_SOURCE_STMT_LABEL) {
        uint32_t value = (stmt->section_index == (size_t)-1) ? 0U : offsets[stmt->section_index];
        if (!context->set_label_value(source, stmt->u.label.name, stmt->section_index, value)) {
          m68k_platform_set_error(out_error, out_error_size, "failed updating label");
          return 0;
        }
        stmt->offset = value; continue;
      }
      if (stmt->section_index >= sizeof(offsets) / sizeof(offsets[0])) {
        m68k_platform_set_error(out_error, out_error_size, "too many sections");
        return 0;
      }
      stmt->offset = offsets[stmt->section_index];
      if (stmt->kind == ASM_SOURCE_STMT_EVEN) {
        stmt->size = (stmt->offset & 1U) ? 1U : 0U;
      } else if (stmt->kind == ASM_SOURCE_STMT_DATA) {
        stmt->size = (uint32_t)data_statement_size(&stmt->u.data);
      } else if (stmt->kind == ASM_SOURCE_STMT_INSTRUCTION) {
        const M68kAsmFormDef *form = NULL;
        M68kInstructionIR resolved_ir;
        int fixup_operands[M68K_SOURCE_FILE_EMIT_MAX_FIXUP_OPERANDS];
        size_t fixup_count = 0;
        unsigned char bytes[M68K_SOURCE_FILE_EMIT_MAX_CASE_BYTES];
        size_t byte_count = 0;
        if (!context->resolve_instruction(source, stmt, &form, &resolved_ir, stmt->offset, fixup_operands,
            &fixup_count, 1, out_error, out_error_size)) {
          return 0;
        }
        if (form != NULL) resolved_ir.form_index = (uint16_t)(form - g_m68k_asm_forms);
        if (resolved_ir.size_suffix == '\0') resolved_ir.size_suffix = stmt->u.instruction.requested_size_suffix;
        if (m68k_ir_encode_one(&resolved_ir, bytes, sizeof(bytes), &byte_count, out_error, out_error_size) != 0)
          return 0;
        if (stmt->size != (uint32_t)byte_count) changed = 1;
        stmt->size = (uint32_t)byte_count;
      }
      offsets[stmt->section_index] += stmt->size;
    }
    if (!changed) return 1;
  }
  m68k_platform_set_error(out_error, out_error_size, "layout did not stabilize");
  return 0;
}

static int emit_data_statement(const AsmSourceFile *source, const AsmSourceStmt *stmt,
    M68kSourceExprLookupFn expr_lookup_symbol, void *expr_lookup_user_data, M68kBinaryWriter *writer,
    M68kObject *object, char *out_error, size_t out_error_size) {
  size_t item_index;
  (void)source;
  for (item_index = 0; item_index < stmt->u.data.item_count; ++item_index) {
    const AsmDataItem *item = &stmt->u.data.items[item_index];
    if (item->kind == ASM_DATA_ITEM_STRING) {
      if (stmt->u.data.width_bytes != 1U) {
        m68k_platform_set_error(out_error, out_error_size, "string data only supported for DC.B");
        return 0;
      }
      if (m68k_writer_bytes(writer, item->bytes, item->byte_count) != 0) return 0;
      continue;
    } else {
      M68kSourceLinearExpr expr;
      M68kSourceEmitExprContext expr_context;
      uint32_t value = 0;
      int is_reloc = 0;
      size_t target_section = (size_t)-1;
      M68kFixup fixup;
      init_emit_expr_context(&expr_context, expr_lookup_symbol, expr_lookup_user_data, (uint32_t)writer->size);
      if (!m68k_source_parse_linear_expression(item->expr, 0, expr_lookup_symbol_with_current, &expr_context, &expr) ||
          !m68k_source_evaluate_linear_expression(&expr, &value, &is_reloc, &target_section)) {
        m68k_platform_set_error(out_error, out_error_size, "bad data expression");
        return 0;
      }
      if (stmt->u.data.width_bytes == 1U) {
        uint8_t byte_value = (uint8_t)value;
        if (m68k_writer_u8(writer, byte_value) != 0) return 0;
      } else if (stmt->u.data.width_bytes == 2U) {
        if (m68k_writer_u16be(writer, (uint16_t)value) != 0) return 0;
      } else {
        if (m68k_writer_u32be(writer, value) != 0) return 0;
      }
      if (is_reloc) {
        M68kFixupWidth width = (stmt->u.data.width_bytes == 4U)
          ? M68K_FIXUP_WIDTH_32 : (stmt->u.data.width_bytes == 2U) ? M68K_FIXUP_WIDTH_16 : M68K_FIXUP_WIDTH_8;
        if (!should_emit_internal_abs_fixup(source, width)) continue;
        memset(&fixup, 0, sizeof(fixup));
        fixup.section_index = stmt->section_index;
        fixup.offset = (uint32_t)(writer->size - stmt->u.data.width_bytes);
        fixup.kind = M68K_FIXUP_ABS;
        fixup.width = width;
        fixup.target_section_index = target_section;
        fixup.has_target_section = 1;
        if (m68k_object_add_fixup(object, &fixup, NULL) != 0) return 0;
      }
    }
  }
  return 1;
}

static int emit_instruction_statement(const AsmSourceFile *source, const M68kSourceFileEmitContext *context,
    const AsmSourceStmt *stmt, M68kBinaryWriter *writer, M68kObject *object, char *out_error, size_t out_error_size) {
  const M68kAsmFormDef *form = NULL;
  M68kInstructionIR resolved_ir;
  int fixup_operands[M68K_SOURCE_FILE_EMIT_MAX_FIXUP_OPERANDS];
  size_t fixup_count = 0;
  unsigned char bytes[M68K_SOURCE_FILE_EMIT_MAX_CASE_BYTES];
  size_t byte_count = 0;
  size_t fixup_index;
  if (!context->resolve_instruction(source, stmt, &form, &resolved_ir, stmt->offset, fixup_operands, &fixup_count,
      0, out_error, out_error_size)) {
    return 0;
  }
  if (form != NULL) resolved_ir.form_index = (uint16_t)(form - g_m68k_asm_forms);
  if (resolved_ir.size_suffix == '\0') resolved_ir.size_suffix = stmt->u.instruction.requested_size_suffix;
  if (m68k_ir_encode_one(&resolved_ir, bytes, sizeof(bytes), &byte_count, out_error, out_error_size) != 0 ||
      m68k_writer_bytes(writer, bytes, byte_count) != 0) {
    return 0;
  }
  for (fixup_index = 0; fixup_index < fixup_count; ++fixup_index) {
    size_t span_start = 0;
    size_t span_width = 0;
    size_t symbol_index = 0;
    M68kFixup fixup;
    if (!resolved_ir.operands[fixup_operands[fixup_index]].symbol_ref.has_name ||
        !context->find_symbol_index(source, resolved_ir.operands[fixup_operands[fixup_index]].symbol_ref.name,
          &symbol_index) ||
        !detect_fixup_span_ir(&resolved_ir, fixup_operands[fixup_index], &span_start, &span_width, out_error,
          out_error_size)) {
      return 0;
    }
    memset(&fixup, 0, sizeof(fixup));
    fixup.width = (span_width == 4U)
      ? M68K_FIXUP_WIDTH_32 : (span_width == 2U) ? M68K_FIXUP_WIDTH_16 : M68K_FIXUP_WIDTH_8;
    if (!should_emit_internal_abs_fixup(source, fixup.width)) continue;
    fixup.section_index = stmt->section_index;
    fixup.offset = (uint32_t)(stmt->offset + span_start);
    fixup.kind = M68K_FIXUP_ABS;
    fixup.target_section_index = source->symbols[symbol_index].section_index;
    fixup.has_target_section = 1;
    if (m68k_object_add_fixup(object, &fixup, NULL) != 0) return 0;
  }
  return 1;
}

int m68k_source_file_emit_object(const AsmSourceFile *source, const M68kSourceFileEmitContext *context,
    M68kObject *out_object, char *out_error, size_t out_error_size) {
  M68kBinaryWriter section_writers[16];
  size_t index;
  memset(section_writers, 0, sizeof(section_writers));
  if (m68k_object_create(out_object) != 0) {
    m68k_platform_set_error(out_error, out_error_size, "out of memory");
    return 0;
  }
  out_object->platform_backend_kind = source->platform_backend_kind;
  out_object->platform_file_kind = source->file_kind;
  for (index = 0; index < source->section_count; ++index) {
    if (m68k_writer_create(&section_writers[index]) != 0) {
      m68k_platform_set_error(out_error, out_error_size, "out of memory");
      goto fail;
    }
  }
  for (index = 0; index < source->section_count; ++index) {
    M68kSection section;
    memset(&section, 0, sizeof(section));
    section.name = source->sections[index].name;
    section.kind = source->sections[index].kind;
    section.alignment = 2U;
    if (m68k_object_add_section(out_object, &section, NULL) != 0) return 0;
  }
  for (index = 0; index < source->statement_count; ++index) {
    const AsmSourceStmt *stmt = &source->statements[index];
    if (stmt->kind == ASM_SOURCE_STMT_END || stmt->kind == ASM_SOURCE_STMT_SECTION ||
        stmt->kind == ASM_SOURCE_STMT_LABEL)
      continue;
    if (stmt->kind == ASM_SOURCE_STMT_EVEN) {
      if ((section_writers[stmt->section_index].size & 1U) != 0U &&
          m68k_writer_u8(&section_writers[stmt->section_index], 0U) != 0)
        return 0;
    } else if (stmt->kind == ASM_SOURCE_STMT_DATA) {
      if (!emit_data_statement(source, stmt, context->expr_lookup_symbol, (void *)source,
          &section_writers[stmt->section_index], out_object, out_error, out_error_size))
        goto fail;
    } else if (stmt->kind == ASM_SOURCE_STMT_INSTRUCTION) {
      if (!emit_instruction_statement(source, context, stmt, &section_writers[stmt->section_index], out_object,
          out_error, out_error_size))
        goto fail;
    }
  }
  for (index = 0; index < out_object->section_count; ++index) {
    M68kSection *section = &out_object->sections[index];
    uint8_t *data = (uint8_t *)m68k_writer_build(&section_writers[index]);
    if (section_writers[index].size != 0U && data == NULL) {
      m68k_platform_set_error(out_error, out_error_size, "out of memory");
      goto fail;
    }
    if (m68k_object_set_section_data(out_object, index, data, (uint32_t)section_writers[index].size) != 0) {
      free(data);
      m68k_platform_set_error(out_error, out_error_size, "out of memory");
      goto fail;
    }
    section->size = (uint32_t)section_writers[index].size;
    free(data);
    m68k_writer_destroy(&section_writers[index]);
  }
  m68k_platform_set_error(out_error, out_error_size, "");
  return 1;

fail:
  for (index = 0; index < source->section_count; ++index)
    m68k_writer_destroy(&section_writers[index]);
  m68k_object_destroy(out_object);
  return 0;
}

static int append_instruction_ir_statement_direct(M68kSectionIR *section, uint32_t offset,
    const M68kInstructionIR *instruction) {
  M68kStatementIR statement;
  m68k_ir_statement_init(&statement);
  statement.kind = M68K_STATEMENT_INSTRUCTION;
  statement.offset = offset;
  statement.u.instruction = *instruction;
  return m68k_ir_section_append_statement(section, &statement) == 0;
}

static int append_data_ir_statement(const AsmSourceFile *source, const AsmSourceStmt *stmt,
    M68kSourceExprLookupFn expr_lookup_symbol, void *expr_lookup_user_data, M68kSectionIR *section) {
  M68kStatementIR statement;
  M68kBinaryWriter writer;
  size_t item_index;
  (void)source;
  if (m68k_writer_create(&writer) != 0) return 0;
  m68k_ir_statement_init(&statement);
  statement.kind = M68K_STATEMENT_DATA;
  statement.offset = stmt->offset;
  statement.u.data.kind = (stmt->u.data.width_bytes == 1U)
    ? M68K_DATA_ITEM_BYTES : (stmt->u.data.width_bytes == 2U) ? M68K_DATA_ITEM_WORDS : M68K_DATA_ITEM_LONGS;
  for (item_index = 0; item_index < stmt->u.data.item_count; ++item_index) {
    const AsmDataItem *item = &stmt->u.data.items[item_index];
    if (item->kind == ASM_DATA_ITEM_STRING) {
      if (m68k_writer_bytes(&writer, item->bytes, item->byte_count) != 0) goto fail;
    } else {
      M68kSourceLinearExpr expr;
      M68kSourceEmitExprContext expr_context;
      uint32_t value = 0;
      int is_reloc = 0;
      size_t target_section = (size_t)-1;
      init_emit_expr_context(&expr_context, expr_lookup_symbol, expr_lookup_user_data,
        stmt->offset + (uint32_t)writer.size);
      if (!m68k_source_parse_linear_expression(item->expr, 0, expr_lookup_symbol_with_current, &expr_context, &expr) ||
          !m68k_source_evaluate_linear_expression(&expr, &value, &is_reloc, &target_section)) {
        goto fail;
      }
      if (stmt->u.data.width_bytes == 1U) {
        uint8_t byte_value = (uint8_t)value;
        if (m68k_writer_u8(&writer, byte_value) != 0) goto fail;
      } else if (stmt->u.data.width_bytes == 2U) {
        if (m68k_writer_u16be(&writer, (uint16_t)value) != 0) goto fail;
      } else if (m68k_writer_u32be(&writer, value) != 0) {
        goto fail;
      }
    }
  }
  statement.u.data.data = (uint8_t *)m68k_writer_build(&writer);
  statement.u.data.size = writer.size;
  if (statement.u.data.size != 0U && statement.u.data.data == NULL) goto fail;
  if (m68k_ir_section_append_statement(section, &statement) != 0) goto fail;
  free(statement.u.data.data);
  m68k_writer_destroy(&writer);
  return 1;

fail:
  free(statement.u.data.data);
  m68k_writer_destroy(&writer);
  return 0;
}

int m68k_source_file_build_ir(const AsmSourceFile *source, M68kSourceExprLookupFn expr_lookup_symbol,
    void *expr_lookup_user_data, M68kSourceFileIR *out_source_file, char *out_error, size_t out_error_size) {
  size_t section_index;
  size_t stmt_index;
  size_t required_section_count = 0U;
  if (source == NULL || out_source_file == NULL) {
    m68k_platform_set_error(out_error, out_error_size, "bad source ir arguments");
    return 0;
  }
  if (m68k_ir_source_file_create(out_source_file) != 0) {
    m68k_platform_set_error(out_error, out_error_size, "out of memory");
    return 0;
  }
  out_source_file->file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  out_source_file->has_atari_st_program_flags = (uint8_t)(source->has_atari_st_program_flags != 0);
  out_source_file->atari_st_program_flags = source->atari_st_program_flags;
  for (stmt_index = 0; stmt_index < source->statement_count; ++stmt_index) {
    const AsmSourceStmt *stmt = &source->statements[stmt_index];
    if (stmt->section_index != (size_t)-1 && stmt->section_index + 1U > required_section_count)
      required_section_count = stmt->section_index + 1U;
  }
  if (required_section_count > source->section_count) {
    m68k_platform_set_error(out_error, out_error_size, "source ir section map is inconsistent");
    return 0;
  }
  for (section_index = 0; section_index < source->section_count; ++section_index) {
    M68kSectionIR section;
    if (m68k_ir_section_create(&section) != 0) {
      m68k_platform_set_error(out_error, out_error_size, "out of memory");
      goto fail;
    }
    if (m68k_ir_section_set_name(&section, source->sections[section_index].name != NULL
        ? source->sections[section_index].name : "section") != 0) {
      m68k_platform_set_error(out_error, out_error_size, "failed duplicating source ir section name");
      m68k_ir_section_destroy(&section);
      goto fail;
    }
    section.kind = source->sections[section_index].kind;
    for (stmt_index = 0; stmt_index < source->statement_count; ++stmt_index) {
      const AsmSourceStmt *stmt = &source->statements[stmt_index];
      M68kStatementIR statement;
      if (stmt->section_index != section_index) continue;
      if (stmt->kind == ASM_SOURCE_STMT_END || stmt->kind == ASM_SOURCE_STMT_SECTION) continue;
      if (stmt->kind == ASM_SOURCE_STMT_LABEL) {
        m68k_ir_statement_init(&statement);
        statement.kind = M68K_STATEMENT_LABEL;
        statement.offset = stmt->offset;
        statement.label_name = (char *)stmt->u.label.name;
        statement.label_is_generated = 0U;
        if (m68k_ir_section_append_statement(&section, &statement) != 0) {
          m68k_platform_set_error(out_error, out_error_size, "failed appending source ir label");
          m68k_ir_section_destroy(&section);
          goto fail;
        }
      } else if (stmt->kind == ASM_SOURCE_STMT_EVEN) {
        m68k_ir_statement_init(&statement);
        statement.kind = M68K_STATEMENT_ALIGN;
        statement.offset = stmt->offset;
        statement.u.alignment = 2U;
        if (m68k_ir_section_append_statement(&section, &statement) != 0) {
          m68k_platform_set_error(out_error, out_error_size, "failed appending source ir alignment");
          m68k_ir_section_destroy(&section);
          goto fail;
        }
      } else if (stmt->kind == ASM_SOURCE_STMT_INSTRUCTION) {
        if (!append_instruction_ir_statement_direct(&section, stmt->offset, &stmt->u.instruction.parsed_ir)) {
          m68k_platform_set_error(out_error, out_error_size, "failed appending source ir instruction");
          m68k_ir_section_destroy(&section);
          goto fail;
        }
      } else if (stmt->kind == ASM_SOURCE_STMT_DATA) {
        if (!append_data_ir_statement(source, stmt, expr_lookup_symbol, expr_lookup_user_data, &section)) {
          m68k_platform_set_error(out_error, out_error_size, "failed appending source ir data");
          m68k_ir_section_destroy(&section);
          goto fail;
        }
      }
    }
    if (m68k_ir_source_file_append_section(out_source_file, &section) != 0) {
      m68k_platform_set_error(out_error, out_error_size, "failed appending source ir section");
      m68k_ir_section_destroy(&section);
      goto fail;
    }
    m68k_ir_section_destroy(&section);
  }
  m68k_platform_set_error(out_error, out_error_size, "");
  return 1;

fail:
  m68k_ir_source_file_destroy(out_source_file);
  if (out_error == NULL || out_error[0] == '\0') m68k_platform_set_error(out_error, out_error_size, "failed building source ir");
  return 0;
}

