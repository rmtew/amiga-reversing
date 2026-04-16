/* Internal JSON/inspection implementation for platform_file_lib. */
#include "platform_file_internal.h"

static const char *file_kind_name(M68kPlatformFileKind kind) {
  if (kind == M68K_PLATFORM_FILE_EXECUTABLE) return "executable";
  if (kind == M68K_PLATFORM_FILE_OBJECT) return "object";
  return "unknown";
}

static const char *section_kind_name(M68kSectionKind kind) {
  if (kind == M68K_SECTION_CODE) return "code";
  if (kind == M68K_SECTION_DATA) return "data";
  return "bss";
}
static int json_builder_append_hex_bytes(JsonBuilder *builder, const unsigned char *data, size_t size) {
  static const char hex[] = "0123456789abcdef";
  size_t i;
  for (i = 0; i < size; ++i) {
    if (json_builder_append_char(builder, hex[data[i] >> 4]) != 0) return -1;
    if (json_builder_append_char(builder, hex[data[i] & 0x0F]) != 0) return -1;
  }
  return 0;
}

static int json_builder_append_nullable_string(JsonBuilder *builder, const char *text) {
  if (builder == NULL) return -1;
  if (text == NULL) return json_builder_append(&builder[0], "null");
  return json_builder_append_json_string(builder, text);
}

int inspect_object_json(const M68kBackend *backend, const M68kObject *object, char **out_json) {
  JsonBuilder builder = {0};
  size_t i;
  size_t local_count = 0, global_count = 0, external_count = 0;
  if (json_builder_create(&builder) != 0)
    goto fail;

  for (i = 0; i < object->symbol_count; ++i) {
    if (object->symbols[i].binding == M68K_SYMBOL_LOCAL) ++local_count;
    else if (object->symbols[i].binding == M68K_SYMBOL_GLOBAL) ++global_count;
    else if (object->symbols[i].binding == M68K_SYMBOL_EXTERNAL) ++external_count;
  }
  if (json_builder_append(&builder, "{\"platform\":") != 0)
    goto fail;
  if (json_builder_append_json_string(&builder, backend->name) != 0)
    goto fail;
  if (json_builder_append(&builder, ",\"file_kind\":") != 0)
    goto fail;
  if (json_builder_append_json_string(&builder, file_kind_name(object->platform_file_kind)) != 0)
    goto fail;
  if (json_builder_appendf(&builder, ",\"section_count\":%zu,\"symbol_count\":%zu,\"fixup_count\":%zu",
      object->section_count, object->symbol_count, object->fixup_count) != 0)
    goto fail;
  if (json_builder_appendf(&builder, ",\"local_symbol_count\":%zu,\"global_symbol_count\":%zu,"
      "\"external_symbol_count\":%zu", local_count, global_count, external_count) != 0)
    goto fail;
  if (json_builder_append(&builder, ",\"sections\":[") != 0)
    goto fail;
  for (i = 0; i < object->section_count; ++i) {
    const M68kSection *section = &object->sections[i];
    size_t section_symbol_count = 0, section_fixup_count = 0, j;
    if (i != 0U && json_builder_append(&builder, ",") != 0)
      goto fail;
    for (j = 0; j < object->symbol_count; ++j) {
      const M68kSymbol *symbol = &object->symbols[j];
      if (symbol->defined && symbol->section_index == i) ++section_symbol_count;
    }
    for (j = 0; j < object->fixup_count; ++j) {
      if (object->fixups[j].section_index == i) ++section_fixup_count;
    }
    if (json_builder_append(&builder, "{\"name\":") != 0)
      goto fail;
    if (json_builder_append_json_string(&builder, section->name != NULL ? section->name : "") != 0)
      goto fail;
    if (json_builder_append(&builder, ",\"kind\":") != 0)
      goto fail;
    if (json_builder_append_json_string(&builder, section_kind_name(section->kind)) != 0)
      goto fail;
    if (json_builder_appendf(&builder, ",\"size\":%u,\"data_size\":%u,\"alloc_size\":%u,\"stored_size\":%u,"
        "\"debug_size\":%u,\"mem_type\":%u,\"mem_attrs\":%u,"
        "\"symbol_count\":%zu,\"fixup_count\":%zu", section->size, section->data_size, section->size,
        section->data_size, section->debug_size, (unsigned)section->platform_mem_type, section->platform_mem_attrs,
        section_symbol_count, section_fixup_count) != 0)
      goto fail;
    if (json_builder_append(&builder, ",\"data_hex\":\"") != 0)
      goto fail;
    if (section->data_size != 0U && json_builder_append_hex_bytes(&builder, section->data, section->data_size) != 0)
      goto fail;
    if (json_builder_append(&builder, "\"}") != 0)
      goto fail;
  }
  if (json_builder_append(&builder, "]}") != 0)
    goto fail;
  *out_json = json_builder_build(&builder);
  if (*out_json == NULL) goto fail;
  json_builder_destroy(&builder);
  return 0;

fail:
  json_builder_destroy(&builder);
  return -1;
}

int source_analysis_to_json(const M68kSourceAnalysisIR *source_analysis, char **out_json, M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  size_t section_index;
  if (json_builder_create(&builder) != 0)
    goto oom;
  if (json_builder_appendf(&builder,
      "{\"file_kind\":%u,\"analysis_policy\":{\"max_cpu\":%u},\"findings\":{\"required_cpu\":%u,"
      "\"cpu_violation_count\":%u},\"section_count\":%u,\"sections\":[",
      (unsigned)source_analysis->file_kind, (unsigned)source_analysis->policy.max_cpu,
      (unsigned)source_analysis->findings.required_cpu, (unsigned)source_analysis->findings.cpu_violation_count,
      (unsigned)source_analysis->section_count) != 0) {
    goto oom;
  }
  for (section_index = 0; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t block_index;
    size_t edge_index;
    size_t violation_index;
    size_t effect_index;
    size_t call_index;
    if (section_index != 0U && json_builder_append(&builder, ",") != 0)
      goto oom;
    if (json_builder_appendf(&builder,
        "{\"section_index\":%u,\"section_kind\":%u,\"section_size\":%u,\"label_count\":%u,\"block_count\":%u,"
        "\"edge_count\":%u,\"violation_count\":%u,\"blocks\":[",
        (unsigned)section->section_index, (unsigned)section->section_kind, (unsigned)section->section_size,
        (unsigned)section->label_count, (unsigned)section->block_count, (unsigned)section->edge_count,
        (unsigned)section->violation_count) != 0) {
      goto oom;
    }
    for (block_index = 0; block_index < section->block_count; ++block_index) {
      const M68kCfgBlockIR *block = &section->blocks[block_index];
      if (block_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf(&builder,
          "{\"start_offset\":%u,\"end_offset\":%u,\"certainty\":%u,\"edge_start\":%u,\"edge_count\":%u}",
          (unsigned)block->start_offset, (unsigned)block->end_offset, (unsigned)block->certainty,
          (unsigned)block->edge_start, (unsigned)block->edge_count) != 0) {
        goto oom;
      }
    }
    if (json_builder_append(&builder, "],\"edges\":[") != 0)
      goto oom;
    for (edge_index = 0; edge_index < section->edge_count; ++edge_index) {
      const M68kCfgEdgeIR *edge = &section->edges[edge_index];
      if (edge_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf(&builder,
          "{\"source_block_index\":%u,\"target_block_index\":%u,\"source_offset\":%u,\"target_offset\":%u,\"kind\":%u}",
          (unsigned)edge->source_block_index, (unsigned)edge->target_block_index, (unsigned)edge->source_offset,
          (unsigned)edge->target_offset, (unsigned)edge->kind) != 0) {
        goto oom;
      }
    }
    if (json_builder_append(&builder, "],\"violations\":[") != 0)
      goto oom;
    for (violation_index = 0; violation_index < section->violation_count; ++violation_index) {
      const M68kViolationIR *violation = &section->violations[violation_index];
      if (violation_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf(&builder, "{\"offset\":%u,\"kind\":%u,\"message\":",
          (unsigned)violation->offset, (unsigned)violation->kind) != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, violation->message != NULL ? violation->message : "") != 0)
        goto oom;
      if (json_builder_append(&builder, "}") != 0)
        goto oom;
    }
    if (json_builder_appendf(&builder, "],\"recovered_platform_effect_count\":%u,\"recovered_platform_effects\":[",
          (unsigned)section->recovered_platform_effect_count) != 0)
      goto oom;
    for (effect_index = 0; effect_index < section->recovered_platform_effect_count; ++effect_index) {
      const M68kRecoveredPlatformEffectIR *effect = &section->recovered_platform_effects[effect_index];
      const char *base_name = NULL, *symbol_name = NULL, *type_name = NULL;
      const char *semantic_kind = NULL, *value_domain_name = NULL;
      uint8_t has_constant_value = 0U;
      int32_t constant_value = 0;
      if (effect_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (effect->kind == M68K_PLATFORM_EFFECT_SET_BASE_REG || effect->kind == M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT) {
        base_name = m68k_platform_name_ref_name_or_text(&effect->payload.named_base.base_ref,
          effect->payload.named_base.base_name);
      } else if (effect->kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG) {
        symbol_name = m68k_platform_name_ref_name_or_text(&effect->payload.code_ptr.field_symbol_ref,
          effect->payload.code_ptr.field_symbol_name);
        type_name = m68k_platform_name_ref_name_or_text(&effect->payload.code_ptr.owner_type_ref,
          effect->payload.code_ptr.owner_type_name);
        semantic_kind = m68k_platform_name_ref_name_or_text(&effect->payload.code_ptr.semantic_kind_ref,
          effect->payload.code_ptr.semantic_kind);
      } else if (effect->kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG || effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT) {
        type_name = m68k_platform_name_ref_name_or_text(&effect->payload.typed.type_ref,
          effect->payload.typed.type_name);
        semantic_kind = m68k_platform_name_ref_name_or_text(&effect->payload.typed.semantic_kind_ref,
          effect->payload.typed.semantic_kind);
        value_domain_name = m68k_platform_name_ref_name_or_text(&effect->payload.typed.value_domain_ref,
          effect->payload.typed.value_domain_name);
        has_constant_value = effect->payload.typed.has_constant_value;
        constant_value = effect->payload.typed.constant_value;
      }
      if (json_builder_appendf(&builder,
            "{\"offset\":%u,\"kind\":%u,\"reg_kind\":%u,\"reg_index\":%u,\"displacement\":%d,\"field_disp\":%d,"
            "\"base_name\":",
            (unsigned)effect->offset, (unsigned)effect->kind, (unsigned)effect->reg_kind,
            (unsigned)effect->reg_index, (int)effect->displacement, (int)effect->field_disp) != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, base_name) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"symbol_name\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, symbol_name) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"type_name\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, type_name) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"semantic_kind\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, semantic_kind) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"value_domain_name\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, value_domain_name) != 0)
        goto oom;
      if (json_builder_appendf(&builder, ",\"has_constant_value\":%u,\"constant_value\":%d",
            (unsigned)has_constant_value, (int)constant_value) != 0)
        goto oom;
      if (json_builder_append(&builder, "}") != 0)
        goto oom;
    }
    if (json_builder_appendf(&builder, "],\"recovered_platform_call_count\":%u,\"recovered_platform_calls\":[",
          (unsigned)section->recovered_platform_call_count) != 0)
      goto oom;
    for (call_index = 0; call_index < section->recovered_platform_call_count; ++call_index) {
      const M68kRecoveredPlatformCallIR *call = &section->recovered_platform_calls[call_index];
      if (call_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf(&builder,
            "{\"offset\":%u,\"kind\":%u,\"symbol_name\":",
            (unsigned)call->offset, (unsigned)call->kind) != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder,
            m68k_platform_name_ref_name_or_text(&call->symbol_ref, call->symbol_name)) != 0)
        goto oom;
      if (json_builder_appendf(&builder,
            ",\"note_kind\":%u,\"note_base_name\":",
            (unsigned)call->note_kind) != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder,
            m68k_platform_name_ref_name_or_text(&call->note_base_ref, call->note_base_name)) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"note_symbol_name\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder,
            m68k_platform_name_ref_name_or_text(&call->note_symbol_ref, call->note_symbol_name)) != 0)
        goto oom;
      if (json_builder_appendf(&builder,
            ",\"note_reg\":%u,\"note_disp\":%d,\"note_field_disp\":%d,\"note_stack_cleanup_known\":%u,"
            "\"note_stack_cleanup_bytes\":%u,\"note_return_kind\":%u,\"available_since\":",
            (unsigned)call->note_reg, (int)call->note_disp, (int)call->note_field_disp,
            (unsigned)call->note_stack_cleanup_known, (unsigned)call->note_stack_cleanup_bytes,
            (unsigned)call->note_return_kind) != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, call->available_since) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"fd_version\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, call->fd_version) != 0)
        goto oom;
      if (json_builder_append(&builder, "}") != 0)
        goto oom;
    }
    if (json_builder_append(&builder, "]}") != 0)
      goto oom;
  }
  if (json_builder_append(&builder, "]}") != 0)
    goto oom;
  *out_json = json_builder_build(&builder);
  if (*out_json == NULL) goto oom;
  json_builder_destroy(&builder);
  return 0;

oom:
  json_builder_destroy(&builder);
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
  return -1;
}
