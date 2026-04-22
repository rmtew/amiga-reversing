/* Internal JSON/inspection implementation for platform_file_lib. */
#include "platform_file_internal.h"

static int json_builder_append_nullable_string(JsonBuilder *builder, const char *text);
static void amiga_struct_catalog_info(uint16_t struct_id, const char **out_source, int16_t *out_size);

static const char *file_kind_name(M68kPlatformFileKind kind) {
  if (kind == M68K_PLATFORM_FILE_EXECUTABLE) return "executable";
  if (kind == M68K_PLATFORM_FILE_OBJECT) return "object";
  return "unknown";
}

static uint16_t read_u16be_local(const uint8_t *data, size_t size, uint32_t offset, int *ok) {
  if (offset > size || size - offset < 2U) {
    if (ok != NULL) *ok = 0;
    return 0U;
  }
  return (uint16_t)(((uint16_t)data[offset] << 8) | data[offset + 1U]);
}

static uint32_t read_u32be_local(const uint8_t *data, size_t size, uint32_t offset, int *ok) {
  if (offset > size || size - offset < 4U) {
    if (ok != NULL) *ok = 0;
    return 0U;
  }
  return ((uint32_t)data[offset] << 24) | ((uint32_t)data[offset + 1U] << 16)
      | ((uint32_t)data[offset + 2U] << 8) | (uint32_t)data[offset + 3U];
}

static int8_t read_i8_local(const uint8_t *data, size_t size, uint32_t offset, int *ok) {
  if (offset >= size) {
    if (ok != NULL) *ok = 0;
    return 0;
  }
  return (int8_t)data[offset];
}

static const char *read_c_string_local(const uint8_t *data, size_t size, uint32_t offset) {
  size_t index;
  if (offset >= size) return NULL;
  for (index = offset; index < size; ++index) {
    if (data[index] == 0U) return (const char *)&data[offset];
  }
  return NULL;
}

typedef struct AmigaResidentAutoinitInfo {
  uint8_t present;
  uint32_t payload_offset;
  uint32_t base_size;
  uint32_t vectors_offset;
  const char *vector_format;
  uint32_t vector_offsets[256];
  size_t vector_offset_count;
  uint32_t init_struct_offset;
  uint32_t init_func_offset;
  uint8_t has_init_struct_offset;
  uint8_t has_init_func_offset;
} AmigaResidentAutoinitInfo;

typedef struct AmigaResidentInfo {
  uint8_t present;
  uint32_t offset;
  uint8_t flags;
  uint8_t version;
  uint8_t node_type;
  int8_t priority;
  uint32_t init_offset;
  uint8_t auto_init;
  const char *node_type_name;
  const char *name;
  const char *id_string;
  AmigaResidentAutoinitInfo autoinit;
} AmigaResidentInfo;

static int amiga_constant_value(const char *name, int32_t *out_value) {
  if (out_value == NULL) return 0;
  return amiga_os_find_constant_value(name, out_value);
}

static const M68kSection *first_code_section(const M68kObject *object) {
  size_t index;
  if (object == NULL) return NULL;
  for (index = 0U; index < object->section_count; ++index) {
    if (object->sections[index].kind == M68K_SECTION_CODE) return &object->sections[index];
  }
  return NULL;
}

static const char *resident_node_type_name(uint8_t node_type) {
  int32_t value = 0;
  if (amiga_constant_value("NT_LIBRARY", &value) && node_type == (uint8_t)value) return "library";
  if (amiga_constant_value("NT_DEVICE", &value) && node_type == (uint8_t)value) return "device";
  if (amiga_constant_value("NT_RESOURCE", &value) && node_type == (uint8_t)value) return "resource";
  return NULL;
}

static int append_resident_node_type_name(JsonBuilder *builder, uint8_t node_type) {
  const char *name = resident_node_type_name(node_type);
  char fallback[32];
  if (name != NULL) return json_builder_append_json_string(builder, name);
  snprintf(fallback, sizeof(fallback), "type_%u", (unsigned)node_type);
  return json_builder_append_json_string(builder, fallback);
}

static int parse_resident_autoinit(const M68kSection *code_section, AmigaResidentInfo *resident) {
  const uint8_t *data;
  size_t size;
  uint32_t table_offset;
  int ok = 1;
  if (code_section == NULL || resident == NULL || !resident->auto_init) return 0;
  data = code_section->data;
  size = code_section->data_size;
  resident->autoinit.payload_offset = resident->init_offset;
  if (resident->autoinit.payload_offset > size || size - resident->autoinit.payload_offset < 16U) return 0;
  resident->autoinit.base_size = read_u32be_local(data, size, resident->autoinit.payload_offset, &ok);
  resident->autoinit.vectors_offset = read_u32be_local(data, size, resident->autoinit.payload_offset + 4U, &ok);
  resident->autoinit.init_struct_offset = read_u32be_local(data, size, resident->autoinit.payload_offset + 8U, &ok);
  resident->autoinit.init_func_offset = read_u32be_local(data, size, resident->autoinit.payload_offset + 12U, &ok);
  if (!ok || resident->autoinit.base_size == 0U || resident->autoinit.vectors_offset >= size) return 0;
  if (resident->autoinit.init_struct_offset != 0U) {
    if (resident->autoinit.init_struct_offset >= size) return 0;
    resident->autoinit.has_init_struct_offset = 1U;
  }
  if (resident->autoinit.init_func_offset != 0U) {
    if (resident->autoinit.init_func_offset >= size) return 0;
    resident->autoinit.has_init_func_offset = 1U;
  }
  if (read_u16be_local(data, size, resident->autoinit.vectors_offset, &ok) == 0xFFFFU) {
    resident->autoinit.vector_format = "disp16";
    table_offset = resident->autoinit.vectors_offset + 2U;
    while (resident->autoinit.vector_offset_count
        < sizeof(resident->autoinit.vector_offsets) / sizeof(resident->autoinit.vector_offsets[0])) {
      int16_t disp;
      uint32_t target;
      if (table_offset > size || size - table_offset < 2U) return 0;
      disp = (int16_t)read_u16be_local(data, size, table_offset, &ok);
      table_offset += 2U;
      if (disp == -1) break;
      target = (uint32_t)((int32_t)resident->autoinit.vectors_offset + (int32_t)disp);
      if (target >= size) return 0;
      resident->autoinit.vector_offsets[resident->autoinit.vector_offset_count++] = target;
    }
  } else {
    resident->autoinit.vector_format = "offset32";
    table_offset = resident->autoinit.vectors_offset;
    while (resident->autoinit.vector_offset_count
        < sizeof(resident->autoinit.vector_offsets) / sizeof(resident->autoinit.vector_offsets[0])) {
      uint32_t target;
      if (table_offset > size || size - table_offset < 4U) return 0;
      target = read_u32be_local(data, size, table_offset, &ok);
      table_offset += 4U;
      if (target == 0xFFFFFFFFU) break;
      if (target >= size) return 0;
      resident->autoinit.vector_offsets[resident->autoinit.vector_offset_count++] = target;
    }
  }
  resident->autoinit.present = 1U;
  return 1;
}

static int find_amiga_resident_info(const M68kObject *object, AmigaResidentInfo *out_resident) {
  const M68kSection *code_section = first_code_section(object);
  const uint8_t *data;
  size_t size;
  int32_t matchword = 0;
  int32_t autoinit_flag = 0;
  uint32_t offset;
  const AmigaOsStructFieldInfo *field_matchword = amiga_os_find_struct_field_by_field_id(AMIGA_OS_FIELD_ID_RT_MATCHWORD);
  const AmigaOsStructFieldInfo *field_matchtag = amiga_os_find_struct_field_by_field_id(AMIGA_OS_FIELD_ID_RT_MATCHTAG);
  const AmigaOsStructFieldInfo *field_flags = amiga_os_find_struct_field_by_field_id(AMIGA_OS_FIELD_ID_RT_FLAGS);
  const AmigaOsStructFieldInfo *field_version = amiga_os_find_struct_field_by_field_id(AMIGA_OS_FIELD_ID_RT_VERSION);
  const AmigaOsStructFieldInfo *field_type = amiga_os_find_struct_field_by_field_id(AMIGA_OS_FIELD_ID_RT_TYPE);
  const AmigaOsStructFieldInfo *field_pri = amiga_os_find_struct_field_by_field_id(AMIGA_OS_FIELD_ID_RT_PRI);
  const AmigaOsStructFieldInfo *field_name = amiga_os_find_struct_field_by_field_id(AMIGA_OS_FIELD_ID_RT_NAME);
  const AmigaOsStructFieldInfo *field_idstring = amiga_os_find_struct_field_by_field_id(AMIGA_OS_FIELD_ID_RT_IDSTRING);
  const AmigaOsStructFieldInfo *field_init = amiga_os_find_struct_field_by_field_id(AMIGA_OS_FIELD_ID_RT_INIT);
  const AmigaOsStructFieldInfo *field_size = amiga_os_find_struct_field_by_field_id(AMIGA_OS_FIELD_ID_RT_SIZE);
  if (out_resident == NULL) return 0;
  memset(out_resident, 0, sizeof(*out_resident));
  if (code_section == NULL || code_section->data == NULL) return 0;
  if (!amiga_constant_value("RTC_MATCHWORD", &matchword) || !amiga_constant_value("RTF_AUTOINIT", &autoinit_flag))
    return 0;
  if (field_matchword == NULL || field_matchtag == NULL || field_flags == NULL || field_version == NULL
      || field_type == NULL || field_pri == NULL || field_name == NULL || field_idstring == NULL
      || field_init == NULL || field_size == NULL)
    return 0;
  data = code_section->data;
  size = code_section->data_size;
  for (offset = 0U; offset + (uint32_t)field_size->offset <= size; offset += 2U) {
    uint32_t matchtag, name_offset, id_offset;
    int ok = 1;
    if (read_u16be_local(data, size, offset + (uint32_t)field_matchword->offset, &ok) != (uint16_t)matchword) continue;
    matchtag = read_u32be_local(data, size, offset + (uint32_t)field_matchtag->offset, &ok);
    if (!ok || matchtag != offset) continue;
    name_offset = read_u32be_local(data, size, offset + (uint32_t)field_name->offset, &ok);
    id_offset = read_u32be_local(data, size, offset + (uint32_t)field_idstring->offset, &ok);
    out_resident->init_offset = read_u32be_local(data, size, offset + (uint32_t)field_init->offset, &ok);
    if (!ok) continue;
    out_resident->offset = offset;
    out_resident->flags = (uint8_t)read_i8_local(data, size, offset + (uint32_t)field_flags->offset, &ok);
    out_resident->version = (uint8_t)read_i8_local(data, size, offset + (uint32_t)field_version->offset, &ok);
    out_resident->node_type = (uint8_t)read_i8_local(data, size, offset + (uint32_t)field_type->offset, &ok);
    out_resident->priority = read_i8_local(data, size, offset + (uint32_t)field_pri->offset, &ok);
    if (!ok) continue;
    out_resident->node_type_name = resident_node_type_name(out_resident->node_type);
    out_resident->name = read_c_string_local(data, size, name_offset);
    out_resident->id_string = read_c_string_local(data, size, id_offset);
    out_resident->auto_init = (uint8_t)((out_resident->flags & (uint8_t)autoinit_flag) == (uint8_t)autoinit_flag);
    parse_resident_autoinit(code_section, out_resident);
    out_resident->present = 1U;
    return 1;
  }
  return 0;
}

static int append_autoinit_json(JsonBuilder *builder, const AmigaResidentAutoinitInfo *autoinit) {
  size_t index;
  if (autoinit == NULL || !autoinit->present) return json_builder_append(builder, "null");
  if (json_builder_appendf(builder,
        "{\"payload_offset\":%u,\"base_size\":%u,\"vectors_offset\":%u,\"vector_format\":",
        (unsigned)autoinit->payload_offset, (unsigned)autoinit->base_size, (unsigned)autoinit->vectors_offset) != 0)
    return -1;
  if (json_builder_append_json_string(builder, autoinit->vector_format) != 0) return -1;
  if (json_builder_append(builder, ",\"vector_offsets\":[") != 0) return -1;
  for (index = 0U; index < autoinit->vector_offset_count; ++index) {
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_appendf(builder, "%u", (unsigned)autoinit->vector_offsets[index]) != 0) return -1;
  }
  if (json_builder_append(builder, "],\"init_struct_offset\":") != 0) return -1;
  if (autoinit->has_init_struct_offset) {
    if (json_builder_appendf(builder, "%u", (unsigned)autoinit->init_struct_offset) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) {
    return -1;
  }
  if (json_builder_append(builder, ",\"init_func_offset\":") != 0) return -1;
  if (autoinit->has_init_func_offset) {
    if (json_builder_appendf(builder, "%u", (unsigned)autoinit->init_func_offset) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) {
    return -1;
  }
  return json_builder_append(builder, "}");
}

static int append_library_info_json(JsonBuilder *builder, const AmigaResidentInfo *resident) {
  uint16_t library_id;
  size_t index;
  uint32_t public_count = 0U;
  uint32_t total_count = 0U;
  if (resident == NULL || !resident->present || resident->name == NULL
      || strcmp(resident->node_type_name != NULL ? resident->node_type_name : "", "library") != 0)
    return json_builder_append(builder, "null");
  library_id = amiga_os_name_id(1U, resident->name);
  if (amiga_os_name(1U, library_id) != NULL) {
    for (index = 0U; index < AMIGA_OS_LIBRARY_VECTOR_COUNT; ++index) {
      const AmigaOsLibraryVectorInfo *entry = amiga_os_library_vector_at(index);
      const char *function_name;
      if (entry == NULL || entry->library_id != library_id) continue;
      ++total_count;
      function_name = amiga_os_name(3U, entry->function_id);
      if (function_name == NULL || strstr(function_name, "Private") == NULL) ++public_count;
    }
  }
  if (json_builder_append(builder, "{\"library_name\":") != 0) return -1;
  if (json_builder_append_json_string(builder, resident->name) != 0) return -1;
  if (json_builder_append(builder, ",\"id_string\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, resident->id_string) != 0) return -1;
  if (json_builder_appendf(builder, ",\"version\":%u,\"public_function_count\":", (unsigned)resident->version) != 0)
    return -1;
  if (total_count != 0U) {
    if (json_builder_appendf(builder, "%u", (unsigned)public_count) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) {
    return -1;
  }
  if (json_builder_append(builder, ",\"total_lvo_count\":") != 0) return -1;
  if (total_count != 0U) {
    if (json_builder_appendf(builder, "%u", (unsigned)total_count) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) {
    return -1;
  }
  return json_builder_append(builder, "}");
}

static int append_amiga_target_metadata_json(JsonBuilder *builder, const M68kBackend *backend,
    const M68kObject *object) {
  AmigaResidentInfo resident;
  const char *target_type = "program";
  if (backend == NULL || strcmp(backend->name, "amiga-hunk") != 0) return 0;
  find_amiga_resident_info(object, &resident);
  if (resident.present && resident.node_type_name != NULL) target_type = resident.node_type_name;
  if (json_builder_append(builder, ",\"target_type\":") != 0) return -1;
  if (json_builder_append_json_string(builder, target_type) != 0) return -1;
  if (json_builder_append(builder, ",\"resident\":") != 0) return -1;
  if (!resident.present) {
    if (json_builder_append(builder, "null,\"library\":null") != 0) return -1;
    return 0;
  }
  if (json_builder_appendf(builder,
        "{\"offset\":%u,\"flags\":%u,\"version\":%u,\"node_type\":%u,\"node_type_name\":",
        (unsigned)resident.offset, (unsigned)resident.flags, (unsigned)resident.version,
        (unsigned)resident.node_type) != 0)
    return -1;
  if (append_resident_node_type_name(builder, resident.node_type) != 0) return -1;
  if (json_builder_appendf(builder, ",\"priority\":%d,\"name\":", (int)resident.priority) != 0) return -1;
  if (json_builder_append_nullable_string(builder, resident.name) != 0) return -1;
  if (json_builder_append(builder, ",\"id_string\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, resident.id_string) != 0) return -1;
  if (json_builder_appendf(builder, ",\"init_offset\":%u,\"auto_init\":%s,\"autoinit\":",
        (unsigned)resident.init_offset, resident.auto_init ? "true" : "false") != 0)
    return -1;
  if (append_autoinit_json(builder, &resident.autoinit) != 0) return -1;
  if (json_builder_append(builder, "},\"library\":") != 0) return -1;
  return append_library_info_json(builder, &resident);
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

static int json_builder_append_disp_string(JsonBuilder *builder, int16_t displacement) {
  char text[16];
  if (displacement < 0) {
    snprintf(text, sizeof(text), "-0x%04X", (unsigned)(uint16_t)(-displacement));
  } else {
    snprintf(text, sizeof(text), "0x%04X", (unsigned)(uint16_t)displacement);
  }
  return json_builder_append_json_string(builder, text);
}

static const AmigaOsLibraryVectorInfo *resolve_amiga_call_vector_for_json(
    const M68kRecoveredPlatformCallIR *call, const char **out_symbol_name) {
  const char *symbol_name;
  const AmigaOsLibraryVectorInfo *entry;
  if (out_symbol_name != NULL) *out_symbol_name = NULL;
  if (call == NULL) return NULL;
  symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&call->note_symbol_ref, call->note_symbol_name);
  if (symbol_name == NULL || symbol_name[0] == '\0')
    symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&call->symbol_ref, call->symbol_name);
  if (symbol_name == NULL || symbol_name[0] == '\0') return NULL;
  entry = amiga_os_find_library_vector_by_symbol_name(symbol_name);
  if (entry == NULL) return NULL;
  if (out_symbol_name != NULL) *out_symbol_name = symbol_name;
  return entry;
}

static const char *resolve_amiga_call_library_name_for_json(const M68kRecoveredPlatformCallIR *call,
    const AmigaOsLibraryVectorInfo *amiga_vector) {
  const char *base_name;
  if (amiga_vector != NULL) return amiga_os_name(1U, amiga_vector->library_id);
  if (call == NULL) return NULL;
  base_name = m68k_platform_name_ref_resolve_text_or_fallback(&call->note_base_ref, call->note_base_name);
  if (base_name == NULL || base_name[0] == '\0') return NULL;
  return amiga_os_find_library_name_by_base_name(base_name);
}

static int append_amiga_call_inputs_json(JsonBuilder *builder, const AmigaOsLibraryVectorInfo *entry) {
  const AmigaOsCallInputInfo *inputs;
  size_t input_count = 0U;
  size_t input_index;
  if (json_builder_append(builder, "[") != 0) return -1;
  inputs = amiga_os_library_vector_inputs(entry, &input_count);
  for (input_index = 0U; input_index < input_count; ++input_index) {
    const AmigaOsCallInputInfo *input = &inputs[input_index];
    const char *reg_name = amiga_os_register_name(input->reg_kind, input->reg_index);
    if (input_index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"name\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, amiga_os_name(4U, input->input_id)) != 0) return -1;
    if (json_builder_append(builder, ",\"regs\":[") != 0) return -1;
    if (reg_name != NULL) {
      if (json_builder_append_json_string(builder, reg_name) != 0) return -1;
    }
    if (json_builder_append(builder, "],\"type\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, amiga_os_name(6U, input->type_id)) != 0) return -1;
    if (json_builder_append(builder, ",\"i_struct\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, amiga_os_name(7U, input->struct_id)) != 0) return -1;
    if (json_builder_append(builder, ",\"semantic_kind\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, amiga_os_name(9U, input->semantic_kind_id)) != 0) return -1;
    if (json_builder_append(builder, ",\"value_domain\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, amiga_os_name(10U, input->value_domain_id)) != 0) return -1;
    if (json_builder_append(builder, ",\"source\":") != 0) return -1;
    if (json_builder_append_json_string(builder, input->source_kind != 0U ? "global correction" : "parsed NDK") != 0)
      return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  return json_builder_append(builder, "]");
}

static const char *app_slot_symbol_for_effect(const M68kRecoveredPlatformEffectIR *effect, const char *base_name,
    const char *symbol_name, const char *type_name, char *fallback, size_t fallback_size) {
  if (symbol_name != NULL && strncmp(symbol_name, "app_slot_", 9U) == 0) return symbol_name;
  if (base_name != NULL && strncmp(base_name, "app_slot_", 9U) == 0) return base_name;
  if (type_name != NULL && strncmp(type_name, "app_slot_", 9U) == 0) return type_name;
  snprintf(fallback, fallback_size, "app_slot_%04X", (unsigned)(uint16_t)effect->displacement);
  return fallback;
}

static int append_entity_app_slot_hint_json(JsonBuilder *builder, const M68kRecoveredPlatformEffectIR *effect) {
  const char *base_name = NULL, *symbol_name = NULL, *type_name = NULL;
  const char *semantic_kind = NULL, *value_domain_name = NULL;
  char fallback_symbol[32];
  const char *slot_symbol;
  if (effect == NULL || effect->displacement == INT16_MIN) return 0;
  if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT && effect->kind != M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG &&
      effect->kind != M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT)
    return 0;
  if (effect->kind == M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT) {
    base_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.named_base.base_ref,
      effect->payload.named_base.base_name);
  } else if (effect->kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG) {
    symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.code_ptr.field_symbol_ref,
      effect->payload.code_ptr.field_symbol_name);
    type_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.code_ptr.owner_type_ref,
      effect->payload.code_ptr.owner_type_name);
    semantic_kind = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.code_ptr.semantic_kind_ref,
      effect->payload.code_ptr.semantic_kind);
  } else {
    type_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.type_ref,
      effect->payload.typed.type_name);
    semantic_kind = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.semantic_kind_ref,
      effect->payload.typed.semantic_kind);
    value_domain_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.value_domain_ref,
      effect->payload.typed.value_domain_name);
  }
  slot_symbol = app_slot_symbol_for_effect(effect, base_name, symbol_name, type_name, fallback_symbol,
    sizeof(fallback_symbol));
  if (json_builder_appendf(builder, "{\"offset\":%u,\"hint_kind\":\"app_slot\",\"app_slot\":{\"offset\":",
        (unsigned)effect->offset) != 0)
    return -1;
  if (json_builder_append_disp_string(builder, effect->displacement) != 0) return -1;
  if (json_builder_append(builder, ",\"symbol\":") != 0) return -1;
  if (json_builder_append_json_string(builder, slot_symbol) != 0) return -1;
  if (base_name != NULL) {
    if (json_builder_append(builder, ",\"named_base\":") != 0) return -1;
    if (json_builder_append_json_string(builder, base_name) != 0) return -1;
  }
  if (semantic_kind != NULL) {
    if (json_builder_append(builder, ",\"semantic_type\":") != 0) return -1;
    if (json_builder_append_json_string(builder, semantic_kind) != 0) return -1;
  }
  if (value_domain_name != NULL) {
    if (json_builder_append(builder, ",\"value_domain\":") != 0) return -1;
    if (json_builder_append_json_string(builder, value_domain_name) != 0) return -1;
  }
  if (effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT && type_name != NULL) {
    uint16_t struct_id = amiga_os_name_id(7U, type_name);
    if (amiga_os_name(7U, struct_id) != NULL) {
      int16_t struct_size = -1;
      amiga_struct_catalog_info(struct_id, NULL, &struct_size);
      if (json_builder_append(builder, ",\"kind\":\"struct_instance\",\"struct\":") != 0) return -1;
      if (json_builder_append_json_string(builder, type_name) != 0) return -1;
      if (json_builder_appendf(builder, ",\"size\":%d", (int)struct_size) != 0) return -1;
    } else {
      if (json_builder_append(builder, ",\"storage_kind\":\"scalar\",\"value_type\":") != 0) return -1;
      if (json_builder_append_json_string(builder, type_name) != 0) return -1;
    }
  } else if (effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT) {
    if (json_builder_append(builder, ",\"storage_kind\":\"scalar\"") != 0) return -1;
  } else if (effect->kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG) {
    if (json_builder_append(builder, ",\"kind\":\"code_pointer\"") != 0) return -1;
    if (type_name != NULL) {
      if (json_builder_append(builder, ",\"owner_type\":") != 0) return -1;
      if (json_builder_append_json_string(builder, type_name) != 0) return -1;
    }
    if (effect->field_disp != INT16_MIN) {
      if (json_builder_append(builder, ",\"field_offset\":") != 0) return -1;
      if (json_builder_append_disp_string(builder, effect->field_disp) != 0) return -1;
    }
  }
  if (effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT && effect->payload.typed.has_constant_value) {
    if (json_builder_appendf(builder, ",\"constant_value\":%d", (int)effect->payload.typed.constant_value) != 0)
      return -1;
  }
  return json_builder_append(builder, "}}");
}

static int append_entity_platform_call_hint_json(JsonBuilder *builder, const M68kRecoveredPlatformCallIR *call) {
  const char *shape = NULL;
  const char *status = NULL;
  const char *base_name;
  const char *symbol_name;
  const char *resolved_lvo_symbol_name = NULL;
  const AmigaOsLibraryVectorInfo *amiga_vector;
  const char *library_name;
  if (call == NULL) return 0;
  if (call->kind == PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL ||
      call->note_kind == M68K_PLATFORM_CALL_NOTE_CALLBACK_FIELD) {
    shape = "callback_field";
    status = "per_caller";
  } else if (call->kind == PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH &&
             call->note_kind == M68K_PLATFORM_CALL_NOTE_LOCAL_WRAPPER_SYMBOL) {
    shape = "local_wrapper_dispatch";
    status = "external";
  } else if (call->kind == PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH &&
             call->note_kind == M68K_PLATFORM_CALL_NOTE_INDEXED_VECTOR) {
    shape = "indexed_library_dispatch";
    status = "per_caller";
  } else {
    return 0;
  }
  base_name = m68k_platform_name_ref_resolve_text_or_fallback(&call->note_base_ref, call->note_base_name);
  amiga_vector = resolve_amiga_call_vector_for_json(call, &resolved_lvo_symbol_name);
  library_name = resolve_amiga_call_library_name_for_json(call, amiga_vector);
  symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&call->note_symbol_ref, call->note_symbol_name);
  if (symbol_name == NULL) symbol_name = resolved_lvo_symbol_name;
  if (symbol_name == NULL && amiga_vector != NULL) symbol_name = amiga_os_name(3U, amiga_vector->function_id);
  symbol_name = symbol_name != NULL ? symbol_name :
    m68k_platform_name_ref_resolve_text_or_fallback(&call->symbol_ref, call->symbol_name);
  if (json_builder_appendf(builder,
        "{\"offset\":%u,\"hint_kind\":\"indirect_site\",\"indirect_site\":{\"addr\":\"0x%04X\",\"shape\":",
        (unsigned)call->offset, (unsigned)call->offset) != 0)
    return -1;
  if (json_builder_append_json_string(builder, shape) != 0) return -1;
  if (json_builder_append(builder, ",\"status\":") != 0) return -1;
  if (json_builder_append_json_string(builder, status) != 0) return -1;
  if (json_builder_append(builder, ",\"flow\":\"call\"") != 0) return -1;
  if (base_name != NULL || symbol_name != NULL) {
    if (json_builder_append(builder, ",\"detail\":") != 0) return -1;
    if (base_name != NULL && symbol_name != NULL) {
      char detail[256];
      snprintf(detail, sizeof(detail), strcmp(shape, "callback_field") == 0 ? "%s.%s" : "%s/%s", base_name,
        symbol_name);
      if (json_builder_append_json_string(builder, detail) != 0) return -1;
    } else if (json_builder_append_json_string(builder, base_name != NULL ? base_name : symbol_name) != 0) {
      return -1;
    }
  }
  if (library_name != NULL) {
    if (json_builder_append(builder, ",\"library\":") != 0) return -1;
    if (json_builder_append_json_string(builder, library_name) != 0) return -1;
  }
  if (call->note_disp != INT16_MIN) {
    if (json_builder_append(builder, ",\"base_offset\":") != 0) return -1;
    if (json_builder_append_disp_string(builder, call->note_disp) != 0) return -1;
  }
  if (call->note_field_disp != INT16_MIN) {
    if (json_builder_append(builder, ",\"field_offset\":") != 0) return -1;
    if (json_builder_append_disp_string(builder, call->note_field_disp) != 0) return -1;
  }
  return json_builder_append(builder, "}}");
}

static const char *recovered_indirect_flow_name(uint8_t flow) {
  if (flow == M68K_RECOVERED_INDIRECT_FLOW_CALL) return "call";
  if (flow == M68K_RECOVERED_INDIRECT_FLOW_JUMP) return "jump";
  return "unknown";
}

static const char *recovered_indirect_shape_name(uint8_t shape) {
  if (shape == M68K_RECOVERED_INDIRECT_SHAPE_IND) return "ind";
  if (shape == M68K_RECOVERED_INDIRECT_SHAPE_DISP) return "disp";
  if (shape == M68K_RECOVERED_INDIRECT_SHAPE_INDEX_BRIEF) return "index.brief";
  if (shape == M68K_RECOVERED_INDIRECT_SHAPE_PCINDEX_BRIEF) return "pcindex.brief";
  if (shape == M68K_RECOVERED_INDIRECT_SHAPE_INDEX_FULL) return "index.full";
  if (shape == M68K_RECOVERED_INDIRECT_SHAPE_PCINDEX_FULL) return "pcindex.full";
  if (shape == M68K_RECOVERED_INDIRECT_SHAPE_INDEX_MEMIND) return "index.memind";
  if (shape == M68K_RECOVERED_INDIRECT_SHAPE_PCINDEX_MEMIND) return "pcindex.memind";
  return "unknown";
}

static const char *recovered_indirect_status_name(uint8_t status) {
  if (status == M68K_RECOVERED_INDIRECT_STATUS_UNRESOLVED) return "unresolved";
  if (status == M68K_RECOVERED_INDIRECT_STATUS_RESOLVED_RUNTIME) return "resolved_runtime";
  if (status == M68K_RECOVERED_INDIRECT_STATUS_RUNTIME) return "runtime";
  if (status == M68K_RECOVERED_INDIRECT_STATUS_PER_CALLER) return "per_caller";
  if (status == M68K_RECOVERED_INDIRECT_STATUS_BACKWARD_SLICE) return "backward_slice";
  if (status == M68K_RECOVERED_INDIRECT_STATUS_JUMP_TABLE) return "jump_table";
  if (status == M68K_RECOVERED_INDIRECT_STATUS_EXTERNAL) return "external";
  return "unknown";
}

static int text_ends_with(const char *text, const char *suffix) {
  size_t text_len;
  size_t suffix_len;
  if (text == NULL || suffix == NULL) return 0;
  text_len = strlen(text);
  suffix_len = strlen(suffix);
  if (suffix_len > text_len) return 0;
  return strcmp(text + text_len - suffix_len, suffix) == 0;
}

static int pointer_depth(const char *type_name) {
  int depth = 0;
  if (type_name == NULL) return 0;
  while (*type_name != '\0') {
    if (*type_name == '*') ++depth;
    ++type_name;
  }
  return depth;
}

static void amiga_struct_catalog_info(uint16_t struct_id, const char **out_source, int16_t *out_size) {
  const char *source = NULL;
  int16_t size = -1;
  int16_t max_field_offset = 0;
  int offset;
  for (offset = 0; offset <= 8191; ++offset) {
    const AmigaOsStructFieldInfo *field = amiga_os_find_struct_field_by_struct_id(struct_id, (int16_t)offset);
    const char *field_name;
    const char *field_source;
    if (field == NULL) continue;
    field_name = amiga_os_name(8U, field->field_id);
    field_source = amiga_os_find_symbol_include(field_name);
    if (source == NULL && field_source != NULL) source = field_source;
    if (field->offset > max_field_offset) max_field_offset = field->offset;
    if (text_ends_with(field_name, "_SIZEOF")) {
      size = field->offset;
      if (field_source != NULL) source = field_source;
    }
  }
  if (out_source != NULL) *out_source = source != NULL ? source : "generated Amiga OS runtime";
  if (out_size != NULL) *out_size = size >= 0 ? size : max_field_offset;
}

static int append_amiga_type_catalog_json(JsonBuilder *builder) {
  uint16_t struct_id;
  int first = 1;
  if (json_builder_append(builder, "[") != 0) return -1;
  for (struct_id = 0U; struct_id < AMIGA_OS_STRUCT_ID_NONE; ++struct_id) {
    const char *struct_name = amiga_os_name(7U, struct_id);
    const char *source = NULL;
    const char *named_base = NULL;
    int16_t size = 0;
    size_t named_base_index;
    if (struct_name == NULL) continue;
    amiga_struct_catalog_info(struct_id, &source, &size);
    for (named_base_index = 0U; named_base_index < AMIGA_OS_NAMED_BASE_STRUCT_COUNT; ++named_base_index) {
      const AmigaOsNamedBaseStructInfo *entry = amiga_os_named_base_struct_at(named_base_index);
      if (entry == NULL || entry->struct_id != struct_id) continue;
      named_base = amiga_os_name(1U, entry->library_id);
      break;
    }
    if (!first && json_builder_append(builder, ",") != 0) return -1;
    first = 0;
    if (json_builder_append(builder, "{\"name\":") != 0) return -1;
    if (json_builder_append_json_string(builder, struct_name) != 0) return -1;
    if (json_builder_append(builder, ",\"source\":") != 0) return -1;
    if (json_builder_append_json_string(builder, source) != 0) return -1;
    if (json_builder_appendf(builder, ",\"size\":%d,\"named_base\":", (int)size) != 0) return -1;
    if (json_builder_append_nullable_string(builder, named_base) != 0) return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  return json_builder_append(builder, "]");
}

static int append_amiga_naming_catalog_json(JsonBuilder *builder) {
  size_t index;
  if (json_builder_append(builder, "{\"patterns\":[") != 0) return -1;
  for (index = 0U; index < AMIGA_OS_NAMING_PATTERN_COUNT; ++index) {
    const AmigaOsNamingPatternInfo *pattern = amiga_os_naming_pattern_at(index);
    size_t function_index;
    if (pattern == NULL) continue;
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"name\":") != 0) return -1;
    if (json_builder_append_json_string(builder, pattern->name) != 0) return -1;
    if (json_builder_append(builder, ",\"functions\":[") != 0) return -1;
    for (function_index = 0U; function_index < pattern->function_count; ++function_index) {
      const char *function_name = amiga_os_name(3U, pattern->function_ids[function_index]);
      if (function_name == NULL) continue;
      if (function_index != 0U && json_builder_append(builder, ",") != 0) return -1;
      if (json_builder_append_json_string(builder, function_name) != 0) return -1;
    }
    if (json_builder_appendf(builder, "],\"partial\":%s}", pattern->partial ? "true" : "false") != 0)
      return -1;
  }
  if (json_builder_append(builder, "],\"trivial_functions\":[") != 0) return -1;
  for (index = 0U; index < AMIGA_OS_FUNCTION_ID_NONE; ++index) {
    const char *function_name;
    if (!amiga_os_is_trivial_naming_function_id((uint16_t)index)) continue;
    function_name = amiga_os_name(3U, (uint16_t)index);
    if (function_name == NULL) continue;
    if (json_builder_append_json_string(builder, function_name) != 0) return -1;
    if (index + 1U < AMIGA_OS_FUNCTION_ID_NONE) {
      size_t probe;
      int has_more = 0;
      for (probe = index + 1U; probe < AMIGA_OS_FUNCTION_ID_NONE; ++probe) {
        if (amiga_os_is_trivial_naming_function_id((uint16_t)probe)) {
          has_more = 1;
          break;
        }
      }
      if (has_more && json_builder_append(builder, ",") != 0) return -1;
    }
  }
  if (json_builder_append(builder, "],\"generic_prefix\":") != 0) return -1;
  if (json_builder_append_json_string(builder, amiga_os_generic_naming_prefix()) != 0) return -1;
  if (json_builder_append(builder, ",\"libraries\":[") != 0) return -1;
  for (index = 0U; index < AMIGA_OS_LIBRARY_ID_NONE; ++index) {
    const char *library_name = amiga_os_name(1U, (uint16_t)index);
    if (library_name == NULL) continue;
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append_json_string(builder, library_name) != 0) return -1;
  }
  return json_builder_append(builder, "]}");
}

static int append_amiga_struct_fields_json(JsonBuilder *builder, uint16_t struct_id, int16_t struct_size) {
  int16_t offset;
  int first = 1;
  if (json_builder_append(builder, "[") != 0) return -1;
  for (offset = 0; offset <= struct_size; ++offset) {
    const AmigaOsStructFieldInfo *field = amiga_os_find_struct_field_by_struct_id(struct_id, offset);
    const char *field_name;
    int16_t next_offset;
    int16_t size = 0;
    if (field == NULL) continue;
    field_name = amiga_os_name(8U, field->field_id);
    if (field_name == NULL) continue;
    for (next_offset = (int16_t)(offset + 1); next_offset <= struct_size; ++next_offset) {
      if (amiga_os_find_struct_field_by_struct_id(struct_id, next_offset) != NULL) {
        size = (int16_t)(next_offset - offset);
        break;
      }
    }
    if (size == 0 && struct_size > offset) size = (int16_t)(struct_size - offset);
    if (!first && json_builder_append(builder, ",") != 0) return -1;
    first = 0;
    if (json_builder_appendf(builder, "{\"name\":") != 0) return -1;
    if (json_builder_append_json_string(builder, field_name) != 0) return -1;
    if (json_builder_appendf(builder, ",\"offset\":%d,\"size\":%d}", (int)offset, (int)size) != 0) return -1;
  }
  return json_builder_append(builder, "]");
}

static int append_amiga_os_metadata_catalog_json(JsonBuilder *builder) {
  size_t index;
  const char *source = NULL;
  int16_t rt_size = 0;
  int first = 1;
  if (json_builder_append(builder, "{\"exec_base_library\":") != 0) return -1;
  if (json_builder_append_json_string(builder, amiga_os_exec_base_library_name()) != 0) return -1;
  if (json_builder_appendf(builder, ",\"lvo_slot_size\":%u,\"resident_vector_prefixes\":[",
        (unsigned)amiga_os_lvo_slot_size()) != 0)
    return -1;
  for (index = 0U; index < AMIGA_OS_RESIDENT_VECTOR_PREFIX_COUNT; ++index) {
    const AmigaOsResidentVectorPrefixInfo *entry = amiga_os_resident_vector_prefix_at(index);
    const char *symbol_name;
    if (entry == NULL) continue;
    symbol_name = amiga_os_name(4U, entry->symbol_id);
    if (symbol_name == NULL) continue;
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"target_type\":") != 0) return -1;
    if (json_builder_append_json_string(builder, entry->target_type) != 0) return -1;
    if (json_builder_appendf(builder, ",\"slot_index\":%u,\"symbol\":", (unsigned)entry->slot_index) != 0)
      return -1;
    if (json_builder_append_json_string(builder, symbol_name) != 0) return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  if (json_builder_append(builder, "],\"resident_entry_register_seeds\":[") != 0) return -1;
  for (index = 0U; index < AMIGA_OS_RESIDENT_ENTRY_SEED_COUNT; ++index) {
    const AmigaOsResidentEntrySeedInfo *seed = amiga_os_resident_entry_seed_at(index);
    if (seed == NULL) continue;
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"target_type\":") != 0) return -1;
    if (json_builder_append_json_string(builder, seed->target_type) != 0) return -1;
    if (json_builder_append(builder, ",\"role\":") != 0) return -1;
    if (json_builder_append_json_string(builder, seed->role) != 0) return -1;
    if (json_builder_append(builder, ",\"register\":") != 0) return -1;
    if (json_builder_append_json_string(builder, seed->register_name) != 0) return -1;
    if (json_builder_append(builder, ",\"kind\":") != 0) return -1;
    if (json_builder_append_json_string(builder, seed->kind) != 0) return -1;
    if (json_builder_append(builder, ",\"named_base_source\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, seed->named_base_source) != 0) return -1;
    if (json_builder_append(builder, ",\"named_base_name\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, amiga_os_name(1U, seed->named_base_library_id)) != 0) return -1;
    if (json_builder_append(builder, ",\"struct_name\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, amiga_os_name(7U, seed->struct_id)) != 0) return -1;
    if (json_builder_append(builder, ",\"context_name\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, amiga_os_name(4U, seed->context_id)) != 0) return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  if (json_builder_append(builder, "],\"named_base_structs\":[") != 0) return -1;
  for (index = 0U; index < AMIGA_OS_NAMED_BASE_STRUCT_COUNT; ++index) {
    const AmigaOsNamedBaseStructInfo *entry = amiga_os_named_base_struct_at(index);
    if (entry == NULL) continue;
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"library\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, amiga_os_name(1U, entry->library_id)) != 0) return -1;
    if (json_builder_append(builder, ",\"struct\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, amiga_os_name(7U, entry->struct_id)) != 0) return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  amiga_struct_catalog_info(AMIGA_OS_STRUCT_ID_RT, &source, &rt_size);
  if (json_builder_append(builder, "],\"structs\":[{\"name\":\"RT\",\"size\":") != 0) return -1;
  if (json_builder_appendf(builder, "%d,\"fields\":", (int)rt_size) != 0) return -1;
  if (append_amiga_struct_fields_json(builder, AMIGA_OS_STRUCT_ID_RT, rt_size) != 0) return -1;
  if (json_builder_append(builder, "}],\"libraries\":[") != 0) return -1;
  for (index = 0U; index < AMIGA_OS_LIBRARY_ID_NONE; ++index) {
    const char *library_name = amiga_os_name(1U, (uint16_t)index);
    size_t vector_index;
    int first_vector = 1;
    if (library_name == NULL) continue;
    if (!first && json_builder_append(builder, ",") != 0) return -1;
    first = 0;
    if (json_builder_append(builder, "{\"name\":") != 0) return -1;
    if (json_builder_append_json_string(builder, library_name) != 0) return -1;
    if (json_builder_append(builder, ",\"vectors\":[") != 0) return -1;
    for (vector_index = 0U; vector_index < AMIGA_OS_LIBRARY_VECTOR_COUNT; ++vector_index) {
      const AmigaOsLibraryVectorInfo *vector = amiga_os_library_vector_at(vector_index);
      const char *function_name;
      if (vector == NULL || vector->library_id != (uint16_t)index) continue;
      function_name = amiga_os_name(3U, vector->function_id);
      if (function_name == NULL) continue;
      if (!first_vector && json_builder_append(builder, ",") != 0) return -1;
      first_vector = 0;
      if (json_builder_appendf(builder, "{\"lvo\":%d,\"function\":", (int)vector->lvo) != 0) return -1;
      if (json_builder_append_json_string(builder, function_name) != 0) return -1;
      if (json_builder_append(builder, ",\"fd_version\":") != 0) return -1;
      if (json_builder_append_nullable_string(builder, vector->fd_version) != 0) return -1;
      if (json_builder_append(builder, ",\"inputs\":") != 0) return -1;
      if (append_amiga_call_inputs_json(builder, vector) != 0) return -1;
      if (json_builder_append(builder, "}") != 0) return -1;
    }
    if (json_builder_append(builder, "]}") != 0) return -1;
  }
  return json_builder_append(builder, "]}");
}

static const AmigaOsLibraryVectorInfo *find_amiga_library_function(const char *library_name,
    const char *function_name) {
  uint16_t library_id = amiga_os_name_id(1U, library_name);
  uint16_t function_id = amiga_os_name_id(3U, function_name);
  size_t index;
  if (amiga_os_name(1U, library_id) == NULL || amiga_os_name(3U, function_id) == NULL) return NULL;
  for (index = 0U; index < AMIGA_OS_LIBRARY_VECTOR_COUNT; ++index) {
    const AmigaOsLibraryVectorInfo *entry = amiga_os_library_vector_at(index);
    if (entry != NULL && entry->library_id == library_id && entry->function_id == function_id) return entry;
  }
  return NULL;
}

static const AmigaOsCallInputInfo *find_amiga_call_input(const AmigaOsLibraryVectorInfo *entry,
    const char *input_name, const char **out_type_name) {
  const AmigaOsCallInputInfo *inputs;
  size_t input_count = 0U;
  size_t input_index;
  uint16_t input_id = amiga_os_name_id(4U, input_name);
  if (out_type_name != NULL) *out_type_name = NULL;
  if (entry == NULL || amiga_os_name(4U, input_id) == NULL) return NULL;
  inputs = amiga_os_library_vector_inputs(entry, &input_count);
  for (input_index = 0U; input_index < input_count; ++input_index) {
    if (inputs[input_index].input_id == input_id) {
      if (out_type_name != NULL) *out_type_name = amiga_os_name(6U, inputs[input_index].type_id);
      return &inputs[input_index];
    }
  }
  return NULL;
}

int platform_api_input_struct_to_json(const char *backend_name, const char *library_name, const char *function_name,
    const char *input_name, const char *struct_name, char **out_json, M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  uint16_t struct_id;
  const char *struct_source = NULL;
  int16_t struct_size = 0;
  const AmigaOsLibraryVectorInfo *entry;
  const AmigaOsCallInputInfo *input;
  const char *input_type = NULL;
  if (out_json == NULL) return -1;
  *out_json = NULL;
  if (backend_name == NULL || strcmp(backend_name, "amiga-hunk") != 0) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
      "API metadata is only available for amiga-hunk");
    return -1;
  }
  struct_id = amiga_os_name_id(7U, struct_name);
  if (amiga_os_name(7U, struct_id) == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, "unknown struct");
    return -1;
  }
  entry = find_amiga_library_function(library_name, function_name);
  if (entry == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, "unknown API function");
    return -1;
  }
  input = find_amiga_call_input(entry, input_name, &input_type);
  if (input == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, "unknown API input");
    return -1;
  }
  if (pointer_depth(input_type) != 1) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
      "API input is not a supported single-pointer argument");
    return -1;
  }
  amiga_struct_catalog_info(struct_id, &struct_source, &struct_size);
  if (json_builder_create(&builder) != 0) goto oom;
  if (json_builder_append(&builder, "{\"library\":") != 0) goto oom;
  if (json_builder_append_json_string(&builder, library_name) != 0) goto oom;
  if (json_builder_append(&builder, ",\"function\":") != 0) goto oom;
  if (json_builder_append_json_string(&builder, function_name) != 0) goto oom;
  if (json_builder_append(&builder, ",\"input\":") != 0) goto oom;
  if (json_builder_append_json_string(&builder, input_name) != 0) goto oom;
  if (json_builder_append(&builder, ",\"type\":") != 0) goto oom;
  if (json_builder_appendf(&builder, "\"struct %s *\"", struct_name) != 0) goto oom;
  if (json_builder_append(&builder, ",\"i_struct\":") != 0) goto oom;
  if (json_builder_append_json_string(&builder, struct_name) != 0) goto oom;
  if (json_builder_append(&builder, ",\"source\":\"global correction\",\"struct_source\":") != 0) goto oom;
  if (json_builder_append_json_string(&builder, struct_source) != 0) goto oom;
  if (json_builder_appendf(&builder, ",\"struct_size\":%d}", (int)struct_size) != 0) goto oom;
  *out_json = json_builder_build(&builder);
  json_builder_destroy(&builder);
  return *out_json != NULL ? 0 : -1;

oom:
  json_builder_destroy(&builder);
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
  return -1;
}

int platform_type_catalog_to_json(const char *backend_name, char **out_json, M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  (void)diagnostics;
  if (out_json == NULL) return -1;
  *out_json = NULL;
  if (json_builder_create(&builder) != 0) return -1;
  if (backend_name != NULL && strcmp(backend_name, "amiga-hunk") == 0) {
    if (append_amiga_type_catalog_json(&builder) != 0) goto fail;
  } else {
    if (json_builder_append(&builder, "[]") != 0) goto fail;
  }
  *out_json = json_builder_build(&builder);
  json_builder_destroy(&builder);
  return *out_json != NULL ? 0 : -1;

fail:
  json_builder_destroy(&builder);
  return -1;
}

int platform_naming_catalog_to_json(const char *backend_name, char **out_json, M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  (void)diagnostics;
  if (out_json == NULL) return -1;
  *out_json = NULL;
  if (json_builder_create(&builder) != 0) return -1;
  if (backend_name != NULL && strcmp(backend_name, "amiga-hunk") == 0) {
    if (append_amiga_naming_catalog_json(&builder) != 0) goto fail;
  } else {
    if (json_builder_append(&builder, "{\"patterns\":[],\"trivial_functions\":[],\"generic_prefix\":\"\",\"libraries\":[]}") != 0)
      goto fail;
  }
  *out_json = json_builder_build(&builder);
  json_builder_destroy(&builder);
  return *out_json != NULL ? 0 : -1;

fail:
  json_builder_destroy(&builder);
  return -1;
}

int platform_os_metadata_catalog_to_json(const char *backend_name, char **out_json, M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  (void)diagnostics;
  if (out_json == NULL) return -1;
  *out_json = NULL;
  if (json_builder_create(&builder) != 0) return -1;
  if (backend_name != NULL && strcmp(backend_name, "amiga-hunk") == 0) {
    if (append_amiga_os_metadata_catalog_json(&builder) != 0) goto fail;
  } else {
    if (json_builder_append(&builder,
          "{\"exec_base_library\":null,\"lvo_slot_size\":0,\"resident_vector_prefixes\":[],"
          "\"resident_entry_register_seeds\":[],\"named_base_structs\":[],\"structs\":[],\"libraries\":[]}") != 0)
      goto fail;
  }
  *out_json = json_builder_build(&builder);
  json_builder_destroy(&builder);
  return *out_json != NULL ? 0 : -1;

fail:
  json_builder_destroy(&builder);
  return -1;
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
  if (append_amiga_target_metadata_json(&builder, backend, object) != 0)
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

int object_target_metadata_json(const M68kBackend *backend, const M68kObject *object, char **out_json) {
  JsonBuilder builder = {0};
  if (out_json == NULL) return -1;
  *out_json = NULL;
  if (json_builder_create(&builder) != 0) goto fail;
  if (json_builder_append(&builder, "{\"platform\":") != 0) goto fail;
  if (json_builder_append_json_string(&builder, backend != NULL ? backend->name : "") != 0) goto fail;
  if (append_amiga_target_metadata_json(&builder, backend, object) != 0) goto fail;
  if (json_builder_append(&builder, "}") != 0) goto fail;
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
      "{\"file_kind\":%u,\"analysis_policy\":{\"max_cpu\":%u,\"entry_point_count\":%u},\"findings\":{\"required_cpu\":%u,"
      "\"cpu_violation_count\":%u},\"section_count\":%u,\"sections\":[",
      (unsigned)source_analysis->file_kind, (unsigned)source_analysis->policy.max_cpu,
      (unsigned)source_analysis->policy.entry_point_count, (unsigned)source_analysis->findings.required_cpu,
      (unsigned)source_analysis->findings.cpu_violation_count, (unsigned)source_analysis->section_count) != 0) {
    goto oom;
  }
  for (section_index = 0; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t block_index, edge_index, violation_index;
    size_t string_ref_index;
    size_t effect_index, call_index, indirect_site_index;
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
      if (effect->kind == M68K_PLATFORM_EFFECT_SET_BASE_REG || effect->kind == M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT ||
          effect->kind == M68K_PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT) {
        base_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.named_base.base_ref,
          effect->payload.named_base.base_name);
      } else if (effect->kind == M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG) {
        symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.code_ptr.field_symbol_ref,
          effect->payload.code_ptr.field_symbol_name);
        type_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.code_ptr.owner_type_ref,
          effect->payload.code_ptr.owner_type_name);
        semantic_kind = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.code_ptr.semantic_kind_ref,
          effect->payload.code_ptr.semantic_kind);
      } else if (effect->kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG || effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT) {
        type_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.type_ref,
          effect->payload.typed.type_name);
        semantic_kind = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.semantic_kind_ref,
          effect->payload.typed.semantic_kind);
        value_domain_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.value_domain_ref,
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
      if (json_builder_appendf(&builder,
            ",\"has_constant_value\":%u,\"constant_value\":%d,\"target_section_index\":%u,"
            "\"target_offset\":%u",
            (unsigned)has_constant_value, (int)constant_value,
            effect->target_section_index != SIZE_MAX ? (unsigned)effect->target_section_index : UINT_MAX,
            effect->target_offset != UINT32_MAX ? (unsigned)effect->target_offset : UINT_MAX) != 0)
        goto oom;
      if (json_builder_append(&builder, "}") != 0)
        goto oom;
    }
    if (json_builder_appendf(&builder, "],\"recovered_function_arg_count\":%u,\"recovered_function_args\":[",
          (unsigned)section->recovered_function_arg_count) != 0)
      goto oom;
    for (effect_index = 0; effect_index < section->recovered_function_arg_count; ++effect_index) {
      const M68kRecoveredFunctionArgIR *arg = &section->recovered_function_args[effect_index];
      const char *context_name = m68k_platform_name_ref_resolve_text_or_fallback(&arg->typed.context_ref,
        arg->typed.context_name);
      const char *symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&arg->typed.symbol_ref,
        arg->typed.symbol_name);
      const char *type_name = m68k_platform_name_ref_resolve_text_or_fallback(&arg->typed.type_ref,
        arg->typed.type_name);
      const char *semantic_kind = m68k_platform_name_ref_resolve_text_or_fallback(&arg->typed.semantic_kind_ref,
        arg->typed.semantic_kind);
      const char *value_domain_name = m68k_platform_name_ref_resolve_text_or_fallback(&arg->typed.value_domain_ref,
        arg->typed.value_domain_name);
      if (effect_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf(&builder,
            "{\"function_offset\":%u,\"stack_offset\":%u,\"reg_kind\":%u,\"reg_index\":%u,\"context_name\":",
            (unsigned)arg->function_offset, (unsigned)arg->stack_offset, (unsigned)arg->reg_kind,
            (unsigned)arg->reg_index) != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, context_name) != 0)
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
      if (json_builder_appendf(&builder, ",\"has_constant_value\":%u,\"constant_value\":%d}",
            (unsigned)arg->typed.has_constant_value, (int)arg->typed.constant_value) != 0)
        goto oom;
    }
    if (json_builder_append(&builder, "],\"entity_hints\":[") != 0)
      goto oom;
    {
      int first_hint = 1;
      for (effect_index = 0; effect_index < section->recovered_platform_effect_count; ++effect_index) {
        const M68kRecoveredPlatformEffectIR *effect = &section->recovered_platform_effects[effect_index];
        if (effect->displacement == INT16_MIN ||
            (effect->kind != M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT &&
              effect->kind != M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG &&
              effect->kind != M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT))
          continue;
        if (!first_hint && json_builder_append(&builder, ",") != 0) goto oom;
        if (append_entity_app_slot_hint_json(&builder, effect) != 0) goto oom;
        first_hint = 0;
      }
      for (call_index = 0; call_index < section->recovered_platform_call_count; ++call_index) {
        const M68kRecoveredPlatformCallIR *call = &section->recovered_platform_calls[call_index];
        if (call->kind != PLATFORM_RESOLVED_INDIRECT_AMIGA_CALLBACK_FIELD_CALL &&
            !(call->kind == PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH &&
              (call->note_kind == M68K_PLATFORM_CALL_NOTE_LOCAL_WRAPPER_SYMBOL ||
                call->note_kind == M68K_PLATFORM_CALL_NOTE_INDEXED_VECTOR)))
          continue;
        if (!first_hint && json_builder_append(&builder, ",") != 0) goto oom;
        if (append_entity_platform_call_hint_json(&builder, call) != 0) goto oom;
        first_hint = 0;
      }
    }
    if (json_builder_appendf(&builder, "],\"recovered_platform_call_count\":%u,\"recovered_platform_calls\":[",
          (unsigned)section->recovered_platform_call_count) != 0)
      goto oom;
    for (call_index = 0; call_index < section->recovered_platform_call_count; ++call_index) {
      const M68kRecoveredPlatformCallIR *call = &section->recovered_platform_calls[call_index];
      const char *resolved_lvo_symbol_name = NULL;
      const AmigaOsLibraryVectorInfo *amiga_vector = resolve_amiga_call_vector_for_json(call, &resolved_lvo_symbol_name);
      const char *library_name = resolve_amiga_call_library_name_for_json(call, amiga_vector);
      if (call_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf(&builder,
            "{\"offset\":%u,\"kind\":%u,\"symbol_name\":",
            (unsigned)call->offset, (unsigned)call->kind) != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder,
            m68k_platform_name_ref_resolve_text_or_fallback(&call->symbol_ref, call->symbol_name)) != 0)
        goto oom;
      if (json_builder_appendf(&builder,
            ",\"note_kind\":%u,\"note_base_name\":",
            (unsigned)call->note_kind) != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder,
            m68k_platform_name_ref_resolve_text_or_fallback(&call->note_base_ref, call->note_base_name)) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"note_symbol_name\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder,
            m68k_platform_name_ref_resolve_text_or_fallback(&call->note_symbol_ref, call->note_symbol_name)) != 0)
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
      if (json_builder_append(&builder, ",\"library_name\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, library_name) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"function_name\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder,
            amiga_vector != NULL ? amiga_os_name(3U, amiga_vector->function_id) : NULL) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"lvo_symbol_name\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, resolved_lvo_symbol_name) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"inputs\":") != 0)
        goto oom;
      if (append_amiga_call_inputs_json(&builder, amiga_vector) != 0)
        goto oom;
      if (json_builder_append(&builder, "}") != 0)
        goto oom;
    }
    if (json_builder_appendf(&builder, "],\"recovered_string_ref_count\":%u,\"recovered_string_refs\":[",
          (unsigned)section->recovered_string_ref_count) != 0)
      goto oom;
    for (string_ref_index = 0; string_ref_index < section->recovered_string_ref_count; ++string_ref_index) {
      const M68kRecoveredStringRefIR *ref = &section->recovered_string_refs[string_ref_index];
      if (string_ref_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf(&builder, "{\"offset\":%u,\"target\":%u,\"text\":",
            (unsigned)ref->offset, (unsigned)ref->target) != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, ref->text != NULL ? ref->text : "") != 0)
        goto oom;
      if (json_builder_append(&builder, "}") != 0)
        goto oom;
    }
    if (json_builder_appendf(&builder, "],\"recovered_indirect_site_count\":%u,\"recovered_indirect_sites\":[",
          (unsigned)section->recovered_indirect_site_count) != 0)
      goto oom;
    for (indirect_site_index = 0; indirect_site_index < section->recovered_indirect_site_count; ++indirect_site_index) {
      const M68kRecoveredIndirectSiteIR *site = &section->recovered_indirect_sites[indirect_site_index];
      if (indirect_site_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf(&builder, "{\"offset\":%u,\"flow\":", (unsigned)site->offset) != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, recovered_indirect_flow_name(site->flow_kind)) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"shape\":") != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, recovered_indirect_shape_name(site->shape)) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"status\":") != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, recovered_indirect_status_name(site->status)) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"detail\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, site->detail) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"target\":") != 0)
        goto oom;
      if (site->has_target != 0U) {
        if (json_builder_appendf(&builder, "%u", (unsigned)site->target) != 0)
          goto oom;
      } else if (json_builder_append(&builder, "null") != 0) {
        goto oom;
      }
      if (json_builder_append(&builder, ",\"target_count\":") != 0)
        goto oom;
      if (site->has_target_count != 0U) {
        if (json_builder_appendf(&builder, "%u", (unsigned)site->target_count) != 0)
          goto oom;
      } else if (json_builder_append(&builder, "null") != 0) {
        goto oom;
      }
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

static const char *statement_kind_name(uint8_t kind) {
  if (kind == M68K_STATEMENT_LABEL) return "label";
  if (kind == M68K_STATEMENT_INSTRUCTION) return "instruction";
  if (kind == M68K_STATEMENT_DATA) return "data";
  if (kind == M68K_STATEMENT_ALIGN) return "align";
  return "unknown";
}

static int json_data_string_is_plain_renderable(const uint8_t *data, size_t size) {
  size_t index;
  for (index = 0; index < size; ++index) {
    unsigned char ch = data[index];
    if (ch == '"' || ch == '\\') return 0;
  }
  return 1;
}

static size_t source_statement_rendered_line_count(const M68kStatementIR *stmt, const M68kRenderPolicy *policy) {
  size_t step;
  size_t items_per_line;
  if (stmt == NULL) return 0U;
  if (stmt->kind != M68K_STATEMENT_DATA) return 1U;
  if (stmt->u.data.size == 0U) return 1U;
  if (stmt->u.data.expr_text != NULL && stmt->u.data.expr_text[0] != '\0') return 1U;
  if (stmt->u.data.kind == M68K_DATA_ITEM_STRING && (policy == NULL || policy->presentation.prefer_strings != 0U) &&
      json_data_string_is_plain_renderable(stmt->u.data.data, stmt->u.data.size)) {
    return 1U;
  }
  step = (stmt->u.data.kind == M68K_DATA_ITEM_WORDS) ? 2U : (stmt->u.data.kind == M68K_DATA_ITEM_LONGS) ? 4U : 1U;
  items_per_line = (stmt->u.data.kind == M68K_DATA_ITEM_LONGS) ? 8U : (stmt->u.data.kind == M68K_DATA_ITEM_WORDS) ? 12U : 16U;
  if (stmt->u.data.kind == M68K_DATA_ITEM_STRING) {
    step = 1U;
    items_per_line = 16U;
  }
  if (stmt->u.data.kind == M68K_DATA_ITEM_LONGS && policy != NULL && policy->presentation.prefer_long_data == 0U) {
    step = 1U;
    items_per_line = 16U;
  }
  return ((stmt->u.data.size + step - 1U) / step + items_per_line - 1U) / items_per_line;
}

int source_file_to_json(const M68kSourceFileIR *source_file, char **out_json, M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  size_t section_index;
  if (source_file == NULL || out_json == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, "bad arguments");
    return -1;
  }
  if (json_builder_create(&builder) != 0) goto oom;
  if (json_builder_appendf(&builder, "{\"file_kind\":%u,\"platform_backend_kind\":%u,\"section_count\":%u,"
        "\"sections\":[",
        (unsigned)source_file->file_kind, (unsigned)source_file->platform_backend_kind,
        (unsigned)source_file->section_count) != 0)
    goto oom;
  for (section_index = 0; section_index < source_file->section_count; ++section_index) {
    const M68kSectionIR *section = &source_file->sections[section_index];
    size_t statement_index;
    if (section_index != 0U && json_builder_append(&builder, ",") != 0) goto oom;
    if (json_builder_appendf(&builder, "{\"section_index\":%u,\"name\":",
          (unsigned)section_index) != 0)
      goto oom;
    if (json_builder_append_json_string(&builder, section->name != NULL ? section->name : "") != 0) goto oom;
    if (json_builder_appendf(&builder, ",\"kind\":%u,\"size\":%u,\"statement_count\":%u,\"statements\":[",
          (unsigned)section->kind, (unsigned)section->size, (unsigned)section->statement_count) != 0)
      goto oom;
    for (statement_index = 0; statement_index < section->statement_count; ++statement_index) {
      const M68kStatementIR *stmt = &section->statements[statement_index];
      if (statement_index != 0U && json_builder_append(&builder, ",") != 0) goto oom;
      if (json_builder_appendf(&builder, "{\"statement_index\":%u,\"kind\":",
            (unsigned)statement_index) != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, statement_kind_name(stmt->kind)) != 0) goto oom;
      if (json_builder_appendf(&builder, ",\"offset\":%u,\"label\":",
            (unsigned)stmt->offset) != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, stmt->label_name) != 0) goto oom;
      if (json_builder_appendf(&builder, ",\"label_is_generated\":%u,\"comment\":",
            (unsigned)stmt->label_is_generated) != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, stmt->comment) != 0) goto oom;
      if (json_builder_appendf(&builder, ",\"rendered_line_count\":%u",
            (unsigned)source_statement_rendered_line_count(stmt, NULL)) != 0)
        goto oom;
      if (stmt->kind == M68K_STATEMENT_INSTRUCTION) {
        const M68kInstructionIR *instruction = &stmt->u.instruction;
        if (json_builder_append(&builder, ",\"mnemonic\":") != 0) goto oom;
        if (json_builder_append_nullable_string(&builder, m68k_ir_instruction_mnemonic_name(instruction)) != 0)
          goto oom;
        if (json_builder_appendf(&builder, ",\"byte_count\":%u,\"mnemonic_id\":%u",
              (unsigned)instruction->byte_count, (unsigned)instruction->mnemonic_id) != 0)
          goto oom;
      } else if (stmt->kind == M68K_STATEMENT_DATA) {
        if (json_builder_appendf(&builder, ",\"byte_count\":%u", (unsigned)stmt->u.data.size) != 0) goto oom;
      } else {
        if (json_builder_append(&builder, ",\"byte_count\":0") != 0) goto oom;
      }
      if (json_builder_append(&builder, "}") != 0) goto oom;
    }
    if (json_builder_append(&builder, "]}") != 0) goto oom;
  }
  if (json_builder_append(&builder, "]}") != 0) goto oom;
  *out_json = json_builder_build(&builder);
  if (*out_json == NULL) goto oom;
  json_builder_destroy(&builder);
  return 0;

oom:
  json_builder_destroy(&builder);
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
  return -1;
}

static void copy_trimmed(char *dst, size_t dst_size, const char *start, size_t length) {
  size_t out_length;
  while (length != 0U && (*start == ' ' || *start == '\t' || *start == '\r' || *start == '\n')) {
    ++start;
    --length;
  }
  while (length != 0U &&
      (start[length - 1U] == ' ' || start[length - 1U] == '\t' || start[length - 1U] == '\r' ||
       start[length - 1U] == '\n')) {
    --length;
  }
  if (dst_size == 0U) return;
  out_length = length < dst_size - 1U ? length : dst_size - 1U;
  if (out_length != 0U) memcpy(dst, start, out_length);
  dst[out_length] = '\0';
}

static int text_starts_with_ci(const char *text, const char *prefix) {
  while (*prefix != '\0') {
    char a = *text++;
    char b = *prefix++;
    if (a >= 'a' && a <= 'z') a = (char)(a - 'a' + 'A');
    if (b >= 'a' && b <= 'z') b = (char)(b - 'a' + 'A');
    if (a != b) return 0;
  }
  return 1;
}

static int text_contains_equ(const char *text) {
  const char *cursor = text;
  while (*cursor != '\0') {
    if ((cursor[0] == ' ' || cursor[0] == '\t') &&
        (cursor[1] == 'E' || cursor[1] == 'e') &&
        (cursor[2] == 'Q' || cursor[2] == 'q') &&
        (cursor[3] == 'U' || cursor[3] == 'u') &&
        (cursor[4] == ' ' || cursor[4] == '\t')) {
      return 1;
    }
    ++cursor;
  }
  return 0;
}

static int text_token_equals_ci(const char *text, size_t length, const char *expected) {
  size_t index;
  if (text == NULL || expected == NULL) return 0;
  if (strlen(expected) != length) return 0;
  for (index = 0U; index < length; ++index) {
    char a = text[index];
    char b = expected[index];
    if (a >= 'a' && a <= 'z') a = (char)(a - 'a' + 'A');
    if (b >= 'a' && b <= 'z') b = (char)(b - 'a' + 'A');
    if (a != b) return 0;
  }
  return 1;
}

static int text_token_is_rs_directive(const char *text, size_t length) {
  return text_token_equals_ci(text, length, "RSSET") ||
    text_token_equals_ci(text, length, "RSRESET") ||
    text_token_equals_ci(text, length, "RS.B") ||
    text_token_equals_ci(text, length, "RS.W") ||
    text_token_equals_ci(text, length, "RS.L");
}

static int text_contains_rs_directive_token(const char *text) {
  const char *cursor = text;
  if (cursor == NULL) return 0;
  while (*cursor != '\0') {
    const char *token_start;
    size_t token_length;
    while (*cursor == ' ' || *cursor == '\t') ++cursor;
    token_start = cursor;
    while (*cursor != '\0' && *cursor != ' ' && *cursor != '\t') ++cursor;
    token_length = (size_t)(cursor - token_start);
    if (token_length != 0U && text_token_is_rs_directive(token_start, token_length)) return 1;
  }
  return 0;
}

static const char *listing_row_kind_for_line(const char *stripped) {
  size_t length;
  if (stripped == NULL || stripped[0] == '\0') return "blank";
  if (stripped[0] == ';') return "comment";
  length = strlen(stripped);
  if (length != 0U && stripped[length - 1U] == ':') return "label";
  if (text_starts_with_ci(stripped, "DC.") || text_starts_with_ci(stripped, "DS.")) return "data";
  if (text_starts_with_ci(stripped, "INCLUDE ") || text_starts_with_ci(stripped, "SECTION ") ||
      text_starts_with_ci(stripped, "COMMENT ") || text_starts_with_ci(stripped, "EVEN") ||
      text_contains_equ(stripped) || text_contains_rs_directive_token(stripped)) {
    return "directive";
  }
  return "instruction";
}

static void split_listing_line(const char *line_start, size_t line_length, char *stripped, size_t stripped_size,
    char *opcode, size_t opcode_size, char *operand, size_t operand_size, char *comment, size_t comment_size) {
  const char *comment_start = NULL;
  size_t body_length = line_length;
  char body[1024];
  size_t index;
  if (opcode_size != 0U) opcode[0] = '\0';
  if (operand_size != 0U) operand[0] = '\0';
  if (comment_size != 0U) comment[0] = '\0';
  for (index = 0U; index < line_length; ++index) {
    if (line_start[index] == ';') {
      comment_start = line_start + index + 1U;
      body_length = index;
      break;
    }
  }
  copy_trimmed(stripped, stripped_size, line_start, body_length);
  if (comment_start != NULL) copy_trimmed(comment, comment_size, comment_start,
      line_length - (size_t)(comment_start - line_start));
  copy_trimmed(body, sizeof(body), line_start, body_length);
  if (body[0] != '\0') {
    size_t token_length = 0U;
    while (body[token_length] != '\0' && body[token_length] != ' ' && body[token_length] != '\t') ++token_length;
    copy_trimmed(opcode, opcode_size, body, token_length);
    copy_trimmed(operand, operand_size, body + token_length, strlen(body + token_length));
  }
}

static const M68kStatementIR *listing_statement_for_line(const M68kSourceFileIR *source_file, size_t section_index,
    size_t *inout_statement_index, size_t *inout_data_lines_left, const char *row_kind) {
  const M68kSectionIR *section;
  const M68kStatementIR *stmt;
  if (source_file == NULL || inout_statement_index == NULL || inout_data_lines_left == NULL) return NULL;
  if (section_index >= source_file->section_count) return NULL;
  section = &source_file->sections[section_index];
  if (*inout_statement_index >= section->statement_count) return NULL;
  stmt = &section->statements[*inout_statement_index];
  if (*inout_data_lines_left != 0U) {
    --*inout_data_lines_left;
    if (*inout_data_lines_left == 0U) ++*inout_statement_index;
    return stmt;
  }
  if ((stmt->kind == M68K_STATEMENT_LABEL && strcmp(row_kind, "label") == 0) ||
      (stmt->kind == M68K_STATEMENT_INSTRUCTION && strcmp(row_kind, "instruction") == 0) ||
      (stmt->kind == M68K_STATEMENT_ALIGN && strcmp(row_kind, "directive") == 0) ||
      (stmt->kind == M68K_STATEMENT_DATA && strcmp(row_kind, "data") == 0)) {
    size_t line_count = source_statement_rendered_line_count(stmt, NULL);
    if (stmt->kind == M68K_STATEMENT_DATA && line_count > 1U) *inout_data_lines_left = line_count - 1U;
    else ++*inout_statement_index;
    return stmt;
  }
  return NULL;
}

static int append_listing_source_context(JsonBuilder *builder, const char *kind, int section_index) {
  if (section_index >= 0 && kind != NULL) {
    if (json_builder_appendf(builder, "{\"kind\":\"c-%s\",\"hunk_index\":%d}", kind, section_index) != 0) return -1;
    return 0;
  }
  return json_builder_append(builder, "{\"section\":\"c-backend\"}");
}

static const M68kAnalysisStructuredDataItem *listing_structured_data_item_at_offset(
    const M68kAnalysisPolicy *policy, int section_index, uint32_t offset) {
  uint16_t index;
  if (policy == NULL || section_index < 0) return NULL;
  for (index = 0U; index < policy->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    if (item->has_section_index && item->section_index != (uint32_t)section_index) continue;
    if (item->offset == offset) return item;
  }
  return NULL;
}

static int append_listing_structured_data_json(JsonBuilder *builder, const M68kAnalysisStructuredDataItem *item) {
  if (item == NULL || (item->label[0] == '\0' && item->struct_name[0] == '\0' && item->field_name[0] == '\0' &&
        item->field_type[0] == '\0' && item->c_type[0] == '\0' && item->pointer_struct[0] == '\0' &&
        item->value_domain[0] == '\0' && item->constant_name[0] == '\0' && item->semantic_role[0] == '\0' &&
        !item->has_constant_value && !item->is_pointer && !item->has_target)) {
    return json_builder_append(builder, "null");
  }
  if (json_builder_append(builder, "{\"label\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, item->label[0] != '\0' ? item->label : NULL) != 0) return -1;
  if (json_builder_append(builder, ",\"struct_name\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, item->struct_name[0] != '\0' ? item->struct_name : NULL) != 0)
    return -1;
  if (json_builder_append(builder, ",\"field_name\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, item->field_name[0] != '\0' ? item->field_name : NULL) != 0)
    return -1;
  if (json_builder_append(builder, ",\"field_type\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, item->field_type[0] != '\0' ? item->field_type : NULL) != 0)
    return -1;
  if (json_builder_append(builder, ",\"c_type\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, item->c_type[0] != '\0' ? item->c_type : NULL) != 0)
    return -1;
  if (json_builder_append(builder, ",\"pointer_struct\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, item->pointer_struct[0] != '\0' ? item->pointer_struct : NULL) != 0)
    return -1;
  if (json_builder_append(builder, ",\"value_domain\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, item->value_domain[0] != '\0' ? item->value_domain : NULL) != 0)
    return -1;
  if (json_builder_append(builder, ",\"constant_name\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, item->constant_name[0] != '\0' ? item->constant_name : NULL) != 0)
    return -1;
  if (json_builder_appendf(builder, ",\"has_constant_value\":%s,\"constant_value\":",
        item->has_constant_value ? "true" : "false") != 0)
    return -1;
  if (item->has_constant_value) {
    if (json_builder_appendf(builder, "%d", (int)item->constant_value) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  if (json_builder_append(builder, ",\"semantic_role\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, item->semantic_role[0] != '\0' ? item->semantic_role : NULL) != 0)
    return -1;
  if (json_builder_appendf(builder, ",\"is_pointer\":%s,\"target_section\":",
        item->is_pointer ? "true" : "false") != 0)
    return -1;
  if (item->has_target) {
    if (json_builder_appendf(builder, "%u", (unsigned)item->target_section) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  if (json_builder_append(builder, ",\"target_offset\":") != 0) return -1;
  if (item->has_target) {
    if (json_builder_appendf(builder, "%u", (unsigned)item->target_offset) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  return json_builder_append(builder, "}");
}

static int append_listing_row_json(JsonBuilder *builder, size_t row_index, const char *line_start, size_t line_length,
    const char *row_kind, int section_index, const M68kStatementIR *stmt, const M68kAnalysisPolicy *analysis_policy) {
  char text[1200];
  char stripped[1024];
  char opcode[128];
  char operand[1024];
  char comment[512];
  const char *label = NULL;
  const M68kAnalysisStructuredDataItem *structured_item = NULL;
  int has_addr = 0;
  uint32_t addr = 0U;
  uint32_t end_offset = 0U;
  uint32_t byte_count = 0U;
  copy_trimmed(text, sizeof(text), line_start, line_length);
  if (line_length + 1U < sizeof(text)) {
    memcpy(text, line_start, line_length);
    text[line_length] = '\0';
  }
  split_listing_line(line_start, line_length, stripped, sizeof(stripped), opcode, sizeof(opcode), operand,
    sizeof(operand), comment, sizeof(comment));
  if (stmt != NULL) {
    has_addr = 1;
    addr = stmt->offset;
    if (stmt->kind == M68K_STATEMENT_INSTRUCTION) byte_count = (uint32_t)stmt->u.instruction.byte_count;
    else if (stmt->kind == M68K_STATEMENT_DATA) byte_count = (uint32_t)stmt->u.data.size;
    end_offset = addr + byte_count;
    label = stmt->label_name;
    structured_item = listing_structured_data_item_at_offset(analysis_policy, section_index, addr);
  } else if (strcmp(row_kind, "label") == 0) {
    size_t stripped_length = strlen(stripped);
    if (stripped_length != 0U && stripped[stripped_length - 1U] == ':') stripped[stripped_length - 1U] = '\0';
    label = stripped;
  }
  if (json_builder_appendf(builder, "{\"row_id\":\"c:%u\",\"kind\":", (unsigned)row_index) != 0) return -1;
  if (json_builder_append_json_string(builder, row_kind) != 0) return -1;
  if (json_builder_append(builder, ",\"stable_key\":") != 0) return -1;
  if (has_addr) {
    char stable_key[128];
    snprintf(stable_key, sizeof(stable_key), "s%d:%08X:%s:%u", section_index, (unsigned)addr, row_kind,
      (unsigned)row_index);
    if (json_builder_append_json_string(builder, stable_key) != 0) return -1;
  } else if (json_builder_appendf(builder, "\"global:%s:%u\"", row_kind, (unsigned)row_index) != 0) return -1;
  if (json_builder_append(builder, ",\"analysis_generation\":") != 0) return -1;
  if (json_builder_append_json_string(builder,
      analysis_policy != NULL && analysis_policy->skip_platform_facts != 0U ? "basic" : "full") != 0)
    return -1;
  if (json_builder_append(builder, ",\"analysis_phase\":") != 0) return -1;
  if (json_builder_append_json_string(builder,
      analysis_policy != NULL && analysis_policy->skip_platform_facts != 0U ? "raw-data" : "full") != 0)
    return -1;
  if (json_builder_append(builder, ",\"section_index\":") != 0) return -1;
  if (section_index >= 0) {
    if (json_builder_appendf(builder, "%d", section_index) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  if (json_builder_append(builder, ",\"start_offset\":") != 0) return -1;
  if (has_addr) {
    if (json_builder_appendf(builder, "%u", (unsigned)addr) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  if (json_builder_append(builder, ",\"end_offset\":") != 0) return -1;
  if (has_addr) {
    if (json_builder_appendf(builder, "%u", (unsigned)end_offset) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  if (json_builder_append(builder, ",\"text\":") != 0) return -1;
  if (json_builder_append_json_string(builder, text) != 0) return -1;
  if (json_builder_append(builder, ",\"bytes\":") != 0) return -1;
  if (stmt != NULL && stmt->source_byte_count != 0U) {
    if (json_builder_append_char(builder, '"') != 0) return -1;
    if (json_builder_append_hex_bytes(builder, stmt->source_bytes, stmt->source_byte_count) != 0) return -1;
    if (json_builder_append_char(builder, '"') != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  if (json_builder_append(builder, ",\"addr\":") != 0) return -1;
  if (has_addr) {
    if (json_builder_appendf(builder, "%u", (unsigned)addr) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  if (json_builder_append(builder, ",\"entity_addr\":") != 0) return -1;
  if (has_addr) {
    if (json_builder_appendf(builder, "%u", (unsigned)addr) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  if (json_builder_append(builder, ",\"label\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, label) != 0) return -1;
  if (json_builder_append(builder, ",\"opcode_or_directive\":") != 0) return -1;
  if (opcode[0] != '\0' && strcmp(row_kind, "label") != 0 && strcmp(row_kind, "blank") != 0 &&
      strcmp(row_kind, "comment") != 0) {
    if (json_builder_append_json_string(builder, opcode) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  if (json_builder_append(builder, ",\"operand_text\":") != 0) return -1;
  if (json_builder_append_json_string(builder, operand) != 0) return -1;
  if (json_builder_append(builder, ",\"comment_text\":") != 0) return -1;
  if (json_builder_append_json_string(builder, comment) != 0) return -1;
  if (json_builder_append(builder, ",\"source_context\":") != 0) return -1;
  if (stmt != NULL) {
    if (append_listing_source_context(builder, row_kind, section_index) != 0) return -1;
  } else if (append_listing_source_context(builder, NULL, -1) != 0) return -1;
  if (json_builder_append(builder, ",\"structured_data\":") != 0) return -1;
  if (append_listing_structured_data_json(builder, structured_item) != 0) return -1;
  return json_builder_append(builder, "}");
}

int source_file_listing_rows_to_json(const M68kSourceFileIR *source_file, const char *rendered_text,
    const M68kAnalysisPolicy *analysis_policy, char **out_json, M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  const char *cursor = rendered_text;
  size_t row_index = 0U;
  int active_section_index = -1;
  size_t statement_index = 0U;
  size_t data_lines_left = 0U;
  if (source_file == NULL || rendered_text == NULL || out_json == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, "bad arguments");
    return -1;
  }
  if (json_builder_create(&builder) != 0) goto oom;
  if (json_builder_append(&builder, "{\"rows\":[") != 0) goto oom;
  while (*cursor != '\0') {
    const char *line_start = cursor;
    size_t line_length;
    char stripped[1024];
    char opcode[128];
    char operand[1024];
    char comment[512];
    const char *row_kind;
    const M68kStatementIR *stmt = NULL;
    while (*cursor != '\0' && *cursor != '\n') ++cursor;
    if (*cursor == '\n') ++cursor;
    line_length = (size_t)(cursor - line_start);
    split_listing_line(line_start, line_length, stripped, sizeof(stripped), opcode, sizeof(opcode), operand,
      sizeof(operand), comment, sizeof(comment));
    row_kind = listing_row_kind_for_line(stripped);
    if (strcmp(row_kind, "directive") == 0 && text_starts_with_ci(stripped, "SECTION ")) {
      ++active_section_index;
      statement_index = 0U;
      data_lines_left = 0U;
    } else if (active_section_index >= 0) {
      stmt = listing_statement_for_line(source_file, (size_t)active_section_index, &statement_index, &data_lines_left,
        row_kind);
    }
    if (row_index != 0U && json_builder_append(&builder, ",") != 0) goto oom;
    if (append_listing_row_json(&builder, row_index, line_start, line_length, row_kind, active_section_index, stmt,
          analysis_policy) != 0)
      goto oom;
    ++row_index;
  }
  if (json_builder_append(&builder, "]}") != 0) goto oom;
  *out_json = json_builder_build(&builder);
  if (*out_json == NULL) goto oom;
  json_builder_destroy(&builder);
  return 0;

oom:
  json_builder_destroy(&builder);
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
  return -1;
}
