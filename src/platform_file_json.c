/* Internal JSON/inspection implementation for platform_file_lib. */
#include "platform_file_internal.h"
#include "m68k_fact_ir.h"
#include "m68k_render_plan.h"
#include "m68k_source_text_util.h"

static int json_builder_append_nullable_string(JsonBuilder *builder, const char *text);
static void amiga_struct_catalog_info(uint16_t struct_id, const char **out_source, int16_t *out_size);
static const char *app_slot_access_kind_name(uint8_t access_kind);
static const char *unresolved_typed_access_classification_name(uint8_t classification);
static const char *type_provenance_kind_name(uint8_t kind);
static int append_listing_operand_parts_json(JsonBuilder *builder, const M68kStatementIR *stmt);

static const char *file_kind_name(M68kPlatformFileKind kind) {
  if (kind == M68K_PLATFORM_FILE_EXECUTABLE) return "executable";
  if (kind == M68K_PLATFORM_FILE_OBJECT) return "object";
  return "unknown";
}

static const char *unresolved_typed_access_classification_name(uint8_t classification) {
  switch (classification) {
  case M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION:
    return "prefix_extension";
  case M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_CUSTOM_TAIL_OR_MISTYPED_BASE:
    return "custom_tail_or_mistyped_base";
  case M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_FIELD_GAP:
  default:
    return "field_gap";
  }
}

static const char *type_provenance_kind_name(uint8_t kind) {
  switch (kind) {
  case M68K_PLATFORM_TYPE_PROVENANCE_API_OUTPUT:
    return "api_output";
  case M68K_PLATFORM_TYPE_PROVENANCE_REGISTER_COPY:
    return "register_copy";
  case M68K_PLATFORM_TYPE_PROVENANCE_STACK_SLOT:
    return "stack_slot";
  case M68K_PLATFORM_TYPE_PROVENANCE_BASE_SLOT:
    return "base_slot";
  case M68K_PLATFORM_TYPE_PROVENANCE_LOOKUP_STORAGE:
    return "lookup_storage";
  case M68K_PLATFORM_TYPE_PROVENANCE_APP_SLOT:
    return "app_slot";
  case M68K_PLATFORM_TYPE_PROVENANCE_FIELD_POINTER:
    return "field_pointer";
  case M68K_PLATFORM_TYPE_PROVENANCE_PREFIX_REFINEMENT:
    return "prefix_refinement";
  case M68K_PLATFORM_TYPE_PROVENANCE_FIELD_ADDRESS:
    return "field_address";
  case M68K_PLATFORM_TYPE_PROVENANCE_NONE:
  default:
    return "unknown";
  }
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
  uint32_t vector_sections[256];
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

static int first_code_section_index(const M68kObject *object, size_t *out_index) {
  size_t index;
  if (out_index != NULL) *out_index = 0U;
  if (object == NULL) return 0;
  for (index = 0U; index < object->section_count; ++index) {
    if (object->sections[index].kind == M68K_SECTION_CODE) {
      if (out_index != NULL) *out_index = index;
      return 1;
    }
  }
  return 0;
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

static const M68kFixup *find_abs32_fixup_at_offset(const M68kObject *object, size_t section_index, uint32_t offset) {
  size_t index;
  if (object == NULL) return NULL;
  for (index = 0U; index < object->fixup_count; ++index) {
    const M68kFixup *fixup = &object->fixups[index];
    if (fixup->section_index == section_index && fixup->offset == offset && fixup->kind == M68K_FIXUP_ABS &&
        fixup->width == M68K_FIXUP_WIDTH_32 && fixup->has_target_section) {
      return fixup;
    }
  }
  return NULL;
}

static int vector_target_in_section_bounds(const M68kObject *object, uint32_t section_index, uint32_t offset) {
  const M68kSection *section;
  if (object == NULL || section_index >= object->section_count) return 0;
  section = &object->sections[section_index];
  return section->data != NULL && offset < section->data_size;
}

static int parse_resident_autoinit(const M68kObject *object, size_t code_section_index, const M68kSection *code_section,
    AmigaResidentInfo *resident) {
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
      resident->autoinit.vector_sections[resident->autoinit.vector_offset_count] = (uint32_t)code_section_index;
      resident->autoinit.vector_offsets[resident->autoinit.vector_offset_count++] = target;
    }
  } else {
    resident->autoinit.vector_format = "offset32";
    table_offset = resident->autoinit.vectors_offset;
    while (resident->autoinit.vector_offset_count
        < sizeof(resident->autoinit.vector_offsets) / sizeof(resident->autoinit.vector_offsets[0])) {
      uint32_t target;
      uint32_t target_section = (uint32_t)code_section_index;
      const M68kFixup *fixup;
      if (table_offset > size || size - table_offset < 4U) return 0;
      target = read_u32be_local(data, size, table_offset, &ok);
      fixup = find_abs32_fixup_at_offset(object, code_section_index, table_offset);
      if (fixup != NULL) target_section = (uint32_t)fixup->target_section_index;
      table_offset += 4U;
      if (target == 0xFFFFFFFFU) break;
      if (!vector_target_in_section_bounds(object, target_section, target)) return 0;
      resident->autoinit.vector_sections[resident->autoinit.vector_offset_count] = target_section;
      resident->autoinit.vector_offsets[resident->autoinit.vector_offset_count++] = target;
    }
  }
  resident->autoinit.present = 1U;
  return 1;
}

static int find_amiga_resident_info(const M68kObject *object, AmigaResidentInfo *out_resident) {
  size_t code_section_index = 0U;
  const M68kSection *code_section = NULL;
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
  if (first_code_section_index(object, &code_section_index)) code_section = &object->sections[code_section_index];
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
    parse_resident_autoinit(object, code_section_index, code_section, out_resident);
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
  if (json_builder_append(builder, "],\"vector_entries\":[") != 0) return -1;
  for (index = 0U; index < autoinit->vector_offset_count; ++index) {
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_appendf(builder, "{\"hunk\":%u,\"offset\":%u}",
          (unsigned)autoinit->vector_sections[index], (unsigned)autoinit->vector_offsets[index]) != 0)
      return -1;
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

static int append_amiga_call_outputs_json(JsonBuilder *builder, const AmigaOsLibraryVectorInfo *entry) {
  const AmigaOsCallOutputInfo *output;
  const char *reg_name;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (entry == NULL) return json_builder_append(builder, "]");
  output = &entry->output;
  if (output->reg_kind == AMIGA_OS_REGISTER_NONE && output->output_id == AMIGA_OS_SYMBOL_ID_NONE &&
      output->type_id == AMIGA_OS_TYPE_ID_NONE && output->struct_id == AMIGA_OS_STRUCT_ID_NONE &&
      output->semantic_kind_id == AMIGA_OS_SEMANTIC_KIND_ID_NONE &&
      output->value_domain_id == AMIGA_OS_VALUE_DOMAIN_ID_NONE) {
    return json_builder_append(builder, "]");
  }
  reg_name = amiga_os_register_name(output->reg_kind, output->reg_index);
  if (json_builder_append(builder, "{\"name\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, amiga_os_name(4U, output->output_id)) != 0) return -1;
  if (json_builder_append(builder, ",\"regs\":[") != 0) return -1;
  if (reg_name != NULL) {
    if (json_builder_append_json_string(builder, reg_name) != 0) return -1;
  }
  if (json_builder_append(builder, "],\"type\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, amiga_os_name(6U, output->type_id)) != 0) return -1;
  if (json_builder_append(builder, ",\"o_struct\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, amiga_os_name(7U, output->struct_id)) != 0) return -1;
  if (json_builder_append(builder, ",\"semantic_kind\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, amiga_os_name(9U, output->semantic_kind_id)) != 0) return -1;
  if (json_builder_append(builder, ",\"value_domain\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, amiga_os_name(10U, output->value_domain_id)) != 0) return -1;
  return json_builder_append(builder, "}]");
}

static const char *atari_return_value_domain(uint8_t return_kind) {
  switch (return_kind) {
  case ATARI_ST_OS_RETURN_WORD:
    return "atari.st.os.return.word";
  case ATARI_ST_OS_RETURN_LONG:
    return "atari.st.os.return.long";
  default:
    return NULL;
  }
}

static int append_atari_call_outputs_json(JsonBuilder *builder, const M68kRecoveredPlatformCallIR *call) {
  const char *value_domain;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (call == NULL || call->note_symbol_ref.platform_kind != M68K_PLATFORM_BACKEND_ATARI_ST)
    return json_builder_append(builder, "]");
  value_domain = atari_return_value_domain(call->note_return_kind);
  if (value_domain == NULL) return json_builder_append(builder, "]");
  if (json_builder_append(builder, "{\"name\":\"return\",\"regs\":[\"D0\"],\"type\":null,\"o_struct\":null,") != 0)
    return -1;
  if (json_builder_append(builder, "\"semantic_kind\":\"return_value\",\"value_domain\":") != 0)
    return -1;
  if (json_builder_append_json_string(builder, value_domain) != 0) return -1;
  return json_builder_append(builder, "}]");
}

static const char *app_slot_symbol_for_effect(const M68kRecoveredPlatformEffectIR *effect, const char *base_name,
    const char *symbol_name, const char *type_name, char *fallback, size_t fallback_size) {
  if (symbol_name != NULL && strncmp(symbol_name, "app_", 4U) == 0) return symbol_name;
  if (base_name != NULL && strncmp(base_name, "app_", 4U) == 0) return base_name;
  if (type_name != NULL && strncmp(type_name, "app_", 4U) == 0) return type_name;
  snprintf(fallback, fallback_size, "app_%04X", (unsigned)(uint16_t)effect->displacement);
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
  size_t index;
  for (index = 0U; index < AMIGA_OS_STRUCT_FIELD_COUNT; ++index) {
    const AmigaOsStructFieldInfo *field = amiga_os_struct_field_at(index);
    const char *field_name;
    const char *field_source;
    int32_t field_end;
    if (field == NULL || field->struct_id != struct_id) continue;
    field_name = amiga_os_name(8U, field->field_id);
    field_source = amiga_os_find_symbol_include(field_name);
    if (source == NULL && field_source != NULL) source = field_source;
    field_end = (int32_t)field->offset + (int32_t)field->size;
    if (field_end > max_field_offset) max_field_offset = (int16_t)field_end;
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
  for (struct_id = 0U; struct_id < AMIGA_OS_STRUCT_ID_COUNT; ++struct_id) {
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

static int append_amiga_struct_fields_json(JsonBuilder *builder, uint16_t struct_id) {
  size_t index;
  int first = 1;
  if (json_builder_append(builder, "[") != 0) return -1;
  for (index = 0U; index < AMIGA_OS_STRUCT_FIELD_COUNT; ++index) {
    const AmigaOsStructFieldInfo *field = amiga_os_struct_field_at(index);
    const char *field_name;
    if (field == NULL || field->struct_id != struct_id) continue;
    field_name = amiga_os_name(8U, field->field_id);
    if (field_name == NULL) continue;
    if (!first && json_builder_append(builder, ",") != 0) return -1;
    first = 0;
    if (json_builder_appendf(builder, "{\"name\":") != 0) return -1;
    if (json_builder_append_json_string(builder, field_name) != 0) return -1;
    if (json_builder_appendf(builder, ",\"offset\":%d,\"size\":%u,\"field_type\":",
          (int)field->offset, (unsigned)field->size) != 0)
      return -1;
    if (json_builder_append_nullable_string(builder, amiga_os_name(6U, field->field_type_id)) != 0) return -1;
    if (json_builder_append(builder, ",\"c_type\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, amiga_os_name(6U, field->c_type_id)) != 0) return -1;
    if (json_builder_append(builder, ",\"nested_type\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, amiga_os_name(6U, field->nested_type_id)) != 0) return -1;
    if (json_builder_append(builder, ",\"pointer_struct\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, amiga_os_name(7U, field->pointer_struct_id)) != 0) return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  return json_builder_append(builder, "]");
}

static int append_amiga_struct_base_json(JsonBuilder *builder, uint16_t struct_id) {
  const AmigaOsStructBaseInfo *base = amiga_os_find_struct_base_by_struct_id(struct_id);
  if (base == NULL) return json_builder_append(builder, "null");
  if (json_builder_append(builder, "{\"struct\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, amiga_os_name(7U, base->base_struct_id)) != 0) return -1;
  if (json_builder_append(builder, ",\"size_symbol\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, amiga_os_name(4U, base->size_symbol_id)) != 0) return -1;
  if (json_builder_appendf(builder, ",\"size\":%u}", (unsigned)base->size) != 0) return -1;
  return 0;
}

static int resolved_struct_field_shape_matches(const AmigaOsResolvedStructFieldInfo *left,
    const AmigaOsResolvedStructFieldInfo *right) {
  size_t index;
  if (left == NULL || right == NULL) return 0;
  if (left->root_struct_id != right->root_struct_id || left->offset != right->offset ||
      left->field_id != right->field_id || left->owner_struct_id != right->owner_struct_id ||
      left->size != right->size || left->inherited != right->inherited || left->nested != right->nested ||
      left->path_count != right->path_count) {
    return 0;
  }
  for (index = 0U; index < left->path_count; ++index) {
    if (left->path_field_ids[index] != right->path_field_ids[index]) return 0;
  }
  return 1;
}

static int append_amiga_resolved_struct_field_json(JsonBuilder *builder,
    const AmigaOsResolvedStructFieldInfo *field, int16_t query_start, int16_t query_end) {
  size_t path_index;
  const char *field_name;
  if (field == NULL) return -1;
  field_name = amiga_os_name(8U, field->field_id);
  if (field_name == NULL) return -1;
  if (json_builder_appendf(builder, "{\"query_start\":%d,\"query_end\":%d,\"name\":",
        (int)query_start, (int)query_end) != 0)
    return -1;
  if (json_builder_append_json_string(builder, field_name) != 0) return -1;
  if (json_builder_appendf(builder, ",\"offset\":%d,\"size\":%u,\"owner_struct\":",
        (int)field->offset, (unsigned)field->size) != 0)
    return -1;
  if (json_builder_append_nullable_string(builder, amiga_os_name(7U, field->owner_struct_id)) != 0) return -1;
  if (json_builder_appendf(builder, ",\"inherited\":%s,\"nested\":%s,\"path\":[",
        field->inherited ? "true" : "false", field->nested ? "true" : "false") != 0)
    return -1;
  for (path_index = 0U; path_index < field->path_count; ++path_index) {
    const char *path_name = amiga_os_name(8U, field->path_field_ids[path_index]);
    if (path_name == NULL) return -1;
    if (path_index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append_json_string(builder, path_name) != 0) return -1;
  }
  return json_builder_append(builder, "]}");
}

static int append_amiga_resolved_struct_fields_json(JsonBuilder *builder, uint16_t struct_id, int16_t struct_size,
    int prefer_nested_exact) {
  int16_t cursor;
  int first = 1;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (struct_size <= 0) return json_builder_append(builder, "]");
  cursor = 0;
  while (cursor < struct_size) {
    AmigaOsResolvedStructFieldInfo resolved;
    int16_t query_start;
    int16_t query_end;
    if (!amiga_os_resolve_struct_field_by_struct_id(struct_id, cursor, prefer_nested_exact, &resolved)) {
      ++cursor;
      continue;
    }
    query_start = cursor;
    query_end = (int16_t)(cursor + 1);
    while (query_end < struct_size) {
      AmigaOsResolvedStructFieldInfo next;
      if (!amiga_os_resolve_struct_field_by_struct_id(struct_id, query_end, prefer_nested_exact, &next) ||
          !resolved_struct_field_shape_matches(&resolved, &next)) {
        break;
      }
      ++query_end;
    }
    if (!first && json_builder_append(builder, ",") != 0) return -1;
    first = 0;
    if (append_amiga_resolved_struct_field_json(builder, &resolved, query_start, query_end) != 0) return -1;
    cursor = query_end;
  }
  return json_builder_append(builder, "]");
}

static int append_amiga_os_structs_json(JsonBuilder *builder) {
  uint16_t struct_id;
  int first = 1;
  if (json_builder_append(builder, "[") != 0) return -1;
  for (struct_id = 0U; struct_id < AMIGA_OS_STRUCT_ID_COUNT; ++struct_id) {
    const char *struct_name = amiga_os_name(7U, struct_id);
    const char *source = NULL;
    int16_t struct_size = 0;
    if (struct_name == NULL) continue;
    amiga_struct_catalog_info(struct_id, &source, &struct_size);
    if (!first && json_builder_append(builder, ",") != 0) return -1;
    first = 0;
    if (json_builder_append(builder, "{\"name\":") != 0) return -1;
    if (json_builder_append_json_string(builder, struct_name) != 0) return -1;
    if (json_builder_append(builder, ",\"source\":") != 0) return -1;
    if (json_builder_append_json_string(builder, source) != 0) return -1;
    if (json_builder_appendf(builder, ",\"size\":%d,\"fields\":", (int)struct_size) != 0) return -1;
    if (append_amiga_struct_fields_json(builder, struct_id) != 0) return -1;
    if (json_builder_append(builder, ",\"base\":") != 0) return -1;
    if (append_amiga_struct_base_json(builder, struct_id) != 0) return -1;
    if (json_builder_append(builder, ",\"resolved_fields\":") != 0) return -1;
    if (append_amiga_resolved_struct_fields_json(builder, struct_id, struct_size, 0) != 0) return -1;
    if (json_builder_append(builder, ",\"resolved_gap_fields\":") != 0) return -1;
    if (append_amiga_resolved_struct_fields_json(builder, struct_id, struct_size, 1) != 0) return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  return json_builder_append(builder, "]");
}

static int append_amiga_os_metadata_catalog_json(JsonBuilder *builder) {
  size_t index;
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
  if (json_builder_append(builder, "],\"structs\":") != 0) return -1;
  if (append_amiga_os_structs_json(builder) != 0) return -1;
  if (json_builder_append(builder, ",\"libraries\":[") != 0) return -1;
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
      if (json_builder_append(builder, ",\"outputs\":") != 0) return -1;
      if (append_amiga_call_outputs_json(builder, vector) != 0) return -1;
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

static const char *m68k_code_start_reason_name(uint32_t reason) {
  switch (reason) {
    case M68K_FACT_CODE_START_REASON_SECTION_ENTRY: return "section_entry";
    case M68K_FACT_CODE_START_REASON_POLICY_ENTRY_OFFSET: return "policy_entry_offset";
    case M68K_FACT_CODE_START_REASON_POLICY_ENTRY_POINT: return "policy_entry_point";
    case M68K_FACT_CODE_START_REASON_CONTROL_TARGET: return "control_target";
    case M68K_FACT_CODE_START_REASON_FALLTHROUGH: return "fallthrough";
    case M68K_FACT_CODE_START_REASON_INLINE_RESUME: return "inline_resume";
    default: return "unknown";
  }
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

static int append_source_analysis_policy_structured_items_json(JsonBuilder *builder,
    const M68kAnalysisPolicy *policy) {
  uint16_t index;
  if (builder == NULL || policy == NULL) return -1;
  for (index = 0U; index < policy->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_appendf(builder, "{\"section_index\":") != 0) return -1;
    if (item->has_section_index) {
      if (json_builder_appendf(builder, "%u", (unsigned)item->section_index) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) {
      return -1;
    }
    if (json_builder_appendf(builder, ",\"offset\":%u,\"size\":%u,\"kind\":%u,\"semantic_role\":",
        (unsigned)item->offset, (unsigned)item->size, (unsigned)item->kind) != 0) {
      return -1;
    }
    if (json_builder_append_nullable_string(builder, item->semantic_role[0] != '\0' ?
        item->semantic_role : NULL) != 0) {
      return -1;
    }
    if (json_builder_append(builder, ",\"label\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, item->label[0] != '\0' ? item->label : NULL) != 0)
      return -1;
    if (json_builder_append(builder, ",\"struct_name\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, item->struct_name[0] != '\0' ?
        item->struct_name : NULL) != 0) {
      return -1;
    }
    if (json_builder_append(builder, ",\"comment\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, item->comment[0] != '\0' ? item->comment : NULL) != 0)
      return -1;
    if (json_builder_appendf(builder, ",\"has_target\":%s,\"target_section\":",
        item->has_target ? "true" : "false") != 0) {
      return -1;
    }
    if (item->has_target) {
      if (json_builder_appendf(builder, "%u", (unsigned)item->target_section) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) {
      return -1;
    }
    if (json_builder_append(builder, ",\"target_offset\":") != 0) return -1;
    if (item->has_target) {
      if (json_builder_appendf(builder, "%u", (unsigned)item->target_offset) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) {
      return -1;
    }
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  return 0;
}

int source_analysis_to_json(const M68kSourceAnalysisIR *source_analysis, char **out_json, M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  size_t section_index;
  if (json_builder_create(&builder) != 0)
    goto oom;
  if (json_builder_appendf(&builder,
      "{\"file_kind\":%u,\"analysis_policy\":{\"max_cpu\":%u,\"entry_point_count\":%u,"
      "\"structured_data_item_count\":%u,\"structured_data_items\":[",
      (unsigned)source_analysis->file_kind, (unsigned)source_analysis->policy.max_cpu,
      (unsigned)source_analysis->policy.entry_point_count,
      (unsigned)source_analysis->policy.structured_data_item_count) != 0) {
    goto oom;
  }
  if (append_source_analysis_policy_structured_items_json(&builder, &source_analysis->policy) != 0)
    goto oom;
  if (json_builder_appendf(&builder,
      "]},\"findings\":{\"required_cpu\":%u,\"cpu_violation_count\":%u},\"section_count\":%u,\"sections\":[",
      (unsigned)source_analysis->findings.required_cpu,
      (unsigned)source_analysis->findings.cpu_violation_count, (unsigned)source_analysis->section_count) != 0)
    goto oom;
  for (section_index = 0; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t block_index, edge_index, violation_index, app_slot_ref_index, typed_access_index;
    size_t unresolved_typed_access_index, runtime_view_index, runtime_address_ref_index, code_start_ref_index;
    size_t string_ref_index;
    size_t effect_index, call_index, indirect_site_index;
    if (section_index != 0U && json_builder_append(&builder, ",") != 0)
      goto oom;
    if (json_builder_appendf(&builder,
        "{\"section_index\":%u,\"section_kind\":%u,\"section_size\":%u,\"label_count\":%u,\"block_count\":%u,"
        "\"edge_count\":%u,\"violation_count\":%u,\"runtime_view_count\":%u,\"runtime_views\":[",
        (unsigned)section->section_index, (unsigned)section->section_kind, (unsigned)section->section_size,
        (unsigned)section->label_count, (unsigned)section->block_count, (unsigned)section->edge_count,
        (unsigned)section->violation_count, (unsigned)section->runtime_view_count) != 0) {
      goto oom;
    }
    for (runtime_view_index = 0; runtime_view_index < section->runtime_view_count; ++runtime_view_index) {
      const M68kRuntimeViewIR *view = &section->runtime_views[runtime_view_index];
      if (runtime_view_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf(&builder,
          "{\"runtime_view_id\":%u,\"storage_address\":%u,\"storage_offset\":%u,\"size\":%u,"
          "\"runtime_address\":%u,\"kind\":%u,\"confidence\":%u}",
          (unsigned)view->runtime_view_id, (unsigned)view->storage_offset,
          (unsigned)view->storage_offset, (unsigned)view->size, (unsigned)view->runtime_address,
          (unsigned)view->kind, (unsigned)view->confidence) != 0) {
        goto oom;
      }
    }
    if (json_builder_appendf(&builder, "],\"runtime_address_ref_count\":%u,\"runtime_address_refs\":[",
          (unsigned)section->runtime_address_ref_count) != 0)
      goto oom;
    for (runtime_address_ref_index = 0; runtime_address_ref_index < section->runtime_address_ref_count;
        ++runtime_address_ref_index) {
      const M68kRuntimeAddressRefIR *ref = &section->runtime_address_refs[runtime_address_ref_index];
      if (runtime_address_ref_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf(&builder,
          "{\"offset\":%u,\"operand_index\":",
          (unsigned)ref->offset) != 0)
        goto oom;
      if (ref->operand_index == UINT32_MAX) {
        if (json_builder_append(&builder, "null") != 0) goto oom;
      } else if (json_builder_appendf(&builder, "%u", (unsigned)ref->operand_index) != 0) {
        goto oom;
      }
      if (json_builder_append(&builder, ",\"target_section_index\":") != 0)
        goto oom;
      if (ref->has_target) {
        if (json_builder_appendf(&builder, "%u", (unsigned)ref->target_section_index) != 0) goto oom;
      } else if (json_builder_append(&builder, "null") != 0) goto oom;
      if (json_builder_append(&builder, ",\"target_offset\":") != 0)
        goto oom;
      if (ref->has_target) {
        if (json_builder_appendf(&builder, "%u", (unsigned)ref->target_offset) != 0) goto oom;
      } else if (json_builder_append(&builder, "null") != 0) goto oom;
      if (json_builder_append(&builder, ",\"runtime_address\":") != 0)
        goto oom;
      if (ref->has_runtime_address) {
        if (json_builder_appendf(&builder, "%u", (unsigned)ref->runtime_address) != 0) goto oom;
      } else if (json_builder_append(&builder, "null") != 0) goto oom;
      if (ref->size != 0U) {
        if (json_builder_appendf(&builder, ",\"size\":%u", (unsigned)ref->size) != 0) goto oom;
      }
      if (json_builder_appendf(&builder, ",\"confidence\":%u,\"data_class\":",
          (unsigned)ref->confidence) != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, ref->data_class) != 0)
        goto oom;
      if (json_builder_append(&builder, "}") != 0)
        goto oom;
    }
    if (json_builder_appendf(&builder, "],\"code_start_ref_count\":%u,\"code_start_refs\":[",
          (unsigned)section->code_start_ref_count) != 0)
      goto oom;
    for (code_start_ref_index = 0; code_start_ref_index < section->code_start_ref_count;
        ++code_start_ref_index) {
      const M68kCodeStartRefIR *ref = &section->code_start_refs[code_start_ref_index];
      if (code_start_ref_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf(&builder,
          "{\"offset\":%u,\"reason\":%u,\"reason_name\":",
          (unsigned)ref->offset, (unsigned)ref->reason) != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, m68k_code_start_reason_name(ref->reason)) != 0)
        goto oom;
      if (json_builder_appendf(&builder,
          ",\"confidence\":%u,\"source_section_index\":%u,\"source_offset\":%u,\"runtime_address\":",
          (unsigned)ref->confidence, (unsigned)ref->source_section_index, (unsigned)ref->source_offset) != 0)
        goto oom;
      if (ref->has_runtime_address) {
        if (json_builder_appendf(&builder, "%u", (unsigned)ref->runtime_address) != 0) goto oom;
      } else if (json_builder_append(&builder, "null") != 0) goto oom;
      if (json_builder_appendf(&builder, ",\"size\":%u}", (unsigned)ref->size) != 0)
        goto oom;
    }
    if (json_builder_append(&builder, "],\"blocks\":[") != 0)
      goto oom;
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
    if (json_builder_appendf(&builder, "],\"app_slot_ref_count\":%u,\"app_slot_refs\":[",
          (unsigned)section->app_slot_ref_count) != 0)
      goto oom;
    for (app_slot_ref_index = 0; app_slot_ref_index < section->app_slot_ref_count; ++app_slot_ref_index) {
      const M68kAppSlotRefIR *ref = &section->app_slot_refs[app_slot_ref_index];
      const char *access = app_slot_access_kind_name(ref->access_kind);
      if (app_slot_ref_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf(&builder,
            "{\"offset\":%u,\"displacement\":%d,\"base_register\":\"A%u\",\"operand_index\":%u,\"access\":",
            (unsigned)ref->offset, (int)ref->displacement, (unsigned)ref->base_reg,
            (unsigned)ref->operand_index) != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, access != NULL ? access : "") != 0)
        goto oom;
      if (json_builder_append(&builder, "}") != 0)
        goto oom;
    }
    if (json_builder_appendf(&builder,
          "],\"recovered_platform_typed_access_count\":%u,\"recovered_platform_typed_accesses\":[",
          (unsigned)section->recovered_platform_typed_access_count) != 0)
      goto oom;
    for (typed_access_index = 0; typed_access_index < section->recovered_platform_typed_access_count;
        ++typed_access_index) {
      const M68kRecoveredPlatformTypedAccessIR *access =
        &section->recovered_platform_typed_accesses[typed_access_index];
      const char *root_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref,
        access->root_struct_name);
      const char *owner_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->owner_struct_ref,
        access->owner_struct_name);
      const char *field_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->field_ref,
        access->field_name);
      if (typed_access_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf(&builder,
            "{\"offset\":%u,\"operand_index\":%u,\"base_register\":\"A%u\",\"displacement\":%d,"
            "\"field_offset\":%d,\"root_struct_name\":",
            (unsigned)access->offset, (unsigned)access->operand_index, (unsigned)access->base_reg,
            (int)access->displacement, (int)access->field_offset) != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, root_struct_name) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"owner_struct_name\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, owner_struct_name) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"field_name\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, field_name) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"field_expr\":") != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, access->field_expr != NULL ? access->field_expr : "") != 0)
        goto oom;
      if (json_builder_appendf(&builder, ",\"inherited\":%u,\"nested\":%u,\"type_provenance_kind\":",
          (unsigned)access->inherited, (unsigned)access->nested) != 0)
        goto oom;
      if (json_builder_append_json_string(&builder,
          type_provenance_kind_name(access->type_provenance_kind)) != 0)
        goto oom;
      if (access->type_provenance_kind != M68K_PLATFORM_TYPE_PROVENANCE_NONE) {
        if (json_builder_appendf(&builder, ",\"type_provenance_section\":%u,\"type_provenance_offset\":%u",
            (unsigned)access->type_provenance_section_index, (unsigned)access->type_provenance_offset) != 0)
          goto oom;
      }
      if (json_builder_append(&builder, "}") != 0)
        goto oom;
    }
    if (json_builder_appendf(&builder,
          "],\"recovered_platform_unresolved_typed_access_count\":%u,"
          "\"recovered_platform_unresolved_typed_accesses\":[",
          (unsigned)section->recovered_platform_unresolved_typed_access_count) != 0)
      goto oom;
    for (unresolved_typed_access_index = 0;
        unresolved_typed_access_index < section->recovered_platform_unresolved_typed_access_count;
        ++unresolved_typed_access_index) {
      const M68kRecoveredPlatformUnresolvedTypedAccessIR *access =
        &section->recovered_platform_unresolved_typed_accesses[unresolved_typed_access_index];
      const char *root_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref,
        access->root_struct_name);
      const char *container_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(
        &access->container_struct_ref, access->container_struct_name);
      const char *refined_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(
        &access->refined_struct_ref, access->refined_struct_name);
      if (unresolved_typed_access_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf(&builder,
            "{\"offset\":%u,\"operand_index\":%u,\"base_register\":\"A%u\",\"displacement\":%d,"
            "\"struct_size\":%u,\"root_struct_name\":",
            (unsigned)access->offset, (unsigned)access->operand_index, (unsigned)access->base_reg,
            (int)access->displacement, (unsigned)access->struct_size) != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, root_struct_name) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"classification\":") != 0)
        goto oom;
      if (json_builder_append_json_string(&builder,
          unresolved_typed_access_classification_name(access->classification)) != 0)
        goto oom;
      if (json_builder_appendf(&builder, ",\"container_candidate_count\":%u,\"container_struct_name\":",
          (unsigned)access->container_candidate_count) != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, container_struct_name) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"container_field_expr\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, access->container_field_expr) != 0)
        goto oom;
      if (json_builder_appendf(&builder, ",\"refinement_applied\":%u,\"refined_struct_name\":",
          (unsigned)access->refinement_applied) != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, refined_struct_name) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"type_provenance_kind\":") != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, type_provenance_kind_name(access->type_provenance_kind)) != 0)
        goto oom;
      if (access->type_provenance_kind != M68K_PLATFORM_TYPE_PROVENANCE_NONE) {
        if (json_builder_appendf(&builder, ",\"type_provenance_section\":%u,\"type_provenance_offset\":%u",
            (unsigned)access->type_provenance_section_index, (unsigned)access->type_provenance_offset) != 0)
          goto oom;
      }
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
      } else if (effect->kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG ||
          effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT ||
          effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT) {
        symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.symbol_ref,
          effect->payload.typed.symbol_name);
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
    if (json_builder_appendf(&builder,
          "],\"recovered_local_call_summary_count\":%u,\"recovered_local_call_summaries\":[",
          (unsigned)section->recovered_local_call_summary_count) != 0)
      goto oom;
    for (effect_index = 0; effect_index < section->recovered_local_call_summary_count; ++effect_index) {
      const M68kRecoveredLocalCallSummaryIR *summary = &section->recovered_local_call_summaries[effect_index];
      const char *base_name = NULL, *symbol_name = NULL, *type_name = NULL;
      const char *semantic_kind = NULL, *value_domain_name = NULL;
      uint8_t has_constant_value = 0U;
      int32_t constant_value = 0;
      if (effect_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (summary->effect_kind == M68K_PLATFORM_EFFECT_SET_BASE_REG) {
        base_name = m68k_platform_name_ref_resolve_text_or_fallback(&summary->payload.named_base.base_ref,
          summary->payload.named_base.base_name);
      } else if (summary->effect_kind == M68K_PLATFORM_EFFECT_SET_TYPED_REG) {
        base_name = m68k_platform_name_ref_resolve_text_or_fallback(&summary->payload.typed.context_ref,
          summary->payload.typed.context_name);
        symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&summary->payload.typed.symbol_ref,
          summary->payload.typed.symbol_name);
        type_name = m68k_platform_name_ref_resolve_text_or_fallback(&summary->payload.typed.type_ref,
          summary->payload.typed.type_name);
        semantic_kind = m68k_platform_name_ref_resolve_text_or_fallback(&summary->payload.typed.semantic_kind_ref,
          summary->payload.typed.semantic_kind);
        value_domain_name = m68k_platform_name_ref_resolve_text_or_fallback(&summary->payload.typed.value_domain_ref,
          summary->payload.typed.value_domain_name);
        has_constant_value = summary->payload.typed.has_constant_value;
        constant_value = summary->payload.typed.constant_value;
      }
      if (json_builder_appendf(&builder,
            "{\"target_offset\":%u,\"effect_kind\":%u,\"reg_kind\":%u,\"reg_index\":%u,"
            "\"success_reg_kind\":%u,\"success_reg_index\":%u,\"success_value_known\":%u,"
            "\"success_reg_value\":%d,\"base_name\":",
            (unsigned)summary->target_offset, (unsigned)summary->effect_kind,
            (unsigned)summary->reg_kind, (unsigned)summary->reg_index,
            (unsigned)summary->success_reg_kind, (unsigned)summary->success_reg_index,
            (unsigned)summary->success_value_known, (int)summary->success_reg_value) != 0)
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
      if (json_builder_appendf(&builder, ",\"has_constant_value\":%u,\"constant_value\":%d}",
            (unsigned)has_constant_value, (int)constant_value) != 0)
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
      if (json_builder_append(&builder, ",\"device_name\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, call->device_name) != 0)
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
      if (json_builder_append(&builder, ",\"outputs\":") != 0)
        goto oom;
      if (amiga_vector != NULL) {
        if (append_amiga_call_outputs_json(&builder, amiga_vector) != 0)
          goto oom;
      } else if (call->note_symbol_ref.platform_kind == M68K_PLATFORM_BACKEND_ATARI_ST) {
        if (append_atari_call_outputs_json(&builder, call) != 0)
          goto oom;
      } else if (json_builder_append(&builder, "[]") != 0) {
        goto oom;
      }
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

static int json_data_string_is_plain_renderable(const uint8_t *data, size_t size) {
  size_t index;
  for (index = 0; index < size; ++index) {
    unsigned char ch = data[index];
    if (ch == '"' || ch == '\\') return 0;
  }
  return 1;
}

static const M68kAnalysisStructuredDataItem *listing_structured_data_item_at_offset(
    const M68kAnalysisPolicy *policy, int section_index, uint32_t offset);

static size_t source_statement_rendered_line_count(const M68kStatementIR *stmt, const M68kRenderPolicy *policy,
    const M68kAnalysisStructuredDataItem *structured_item) {
  size_t step;
  size_t items_per_line;
  if (stmt == NULL) return 0U;
  if (stmt->kind != M68K_STATEMENT_DATA) return 1U;
  if (stmt->u.data.size == 0U) return 1U;
  if (stmt->u.data.expr_text != NULL && stmt->u.data.expr_text[0] != '\0') return 1U;
  if (structured_item != NULL && structured_item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS &&
      structured_item->has_target && strcmp(structured_item->semantic_role, "lookup_table") == 0) {
    return (((stmt->u.data.size + 1U) / 2U) + 3U) / 4U;
  }
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

static int structured_data_item_needs_listing_line_count_override(const M68kAnalysisStructuredDataItem *structured_item) {
  return structured_item != NULL && structured_item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS &&
    structured_item->has_target && strcmp(structured_item->semantic_role, "lookup_table") == 0;
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

static int text_first_token_equals_ci(const char *text, const char *expected) {
  const char *cursor = text;
  const char *token_start;
  size_t token_length;
  if (cursor == NULL) return 0;
  while (*cursor == ' ' || *cursor == '\t') ++cursor;
  token_start = cursor;
  while (*cursor != '\0' && *cursor != ' ' && *cursor != '\t') ++cursor;
  token_length = (size_t)(cursor - token_start);
  return token_length != 0U && text_token_equals_ci(token_start, token_length, expected);
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
  if (text_starts_with_ci(stripped, "DC.") || text_starts_with_ci(stripped, "DCB.") ||
      text_starts_with_ci(stripped, "DS.")) return "data";
  if (text_starts_with_ci(stripped, "INCLUDE ") || text_starts_with_ci(stripped, "SECTION ") ||
      text_starts_with_ci(stripped, "COMMENT ") || text_starts_with_ci(stripped, "EVEN") ||
      text_starts_with_ci(stripped, "FPU ") || text_first_token_equals_ci(stripped, "ORG") ||
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

static const M68kStatementIR *listing_statement_for_line(const M68kSourceFileIR *source_file,
    const M68kAnalysisPolicy *analysis_policy, size_t section_index, size_t *inout_statement_index,
    size_t *inout_data_lines_left, const char *row_kind, int use_rendered_line_count,
    int allow_structured_line_count_override) {
  const M68kSectionIR *section;
  const M68kStatementIR *stmt;
  if (source_file == NULL || inout_statement_index == NULL || inout_data_lines_left == NULL) return NULL;
  if (section_index >= source_file->section_count) return NULL;
  section = &source_file->sections[section_index];
  if (*inout_statement_index >= section->statement_count) return NULL;
  stmt = &section->statements[*inout_statement_index];
  if (use_rendered_line_count && *inout_data_lines_left != 0U) {
    --*inout_data_lines_left;
    if (*inout_data_lines_left == 0U) ++*inout_statement_index;
    return stmt;
  }
  if ((stmt->kind == M68K_STATEMENT_LABEL && strcmp(row_kind, "label") == 0) ||
      (stmt->kind == M68K_STATEMENT_INSTRUCTION && strcmp(row_kind, "instruction") == 0) ||
      (stmt->kind == M68K_STATEMENT_ALIGN && strcmp(row_kind, "directive") == 0) ||
      (stmt->kind == M68K_STATEMENT_DATA && strcmp(row_kind, "data") == 0)) {
    const M68kAnalysisStructuredDataItem *structured_item =
      stmt->kind == M68K_STATEMENT_DATA
        ? listing_structured_data_item_at_offset(analysis_policy, (int)section_index, stmt->offset)
        : NULL;
    if (use_rendered_line_count ||
        (allow_structured_line_count_override &&
          structured_data_item_needs_listing_line_count_override(structured_item))) {
      size_t line_count = source_statement_rendered_line_count(stmt, NULL, structured_item);
      if (stmt->kind == M68K_STATEMENT_DATA && line_count > 1U) *inout_data_lines_left = line_count - 1U;
      else ++*inout_statement_index;
    } else {
      ++*inout_statement_index;
    }
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
    uint32_t end_offset;
    if (item->has_section_index) {
      if (item->section_index != (uint32_t)section_index) continue;
    } else if (section_index != 0) {
      continue;
    }
    if (item->size == 0U || offset < item->offset || item->size > UINT32_MAX - item->offset) continue;
    end_offset = item->offset + item->size;
    if (offset < end_offset) return item;
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
  if (json_builder_appendf(builder, "{\"section_index\":%u,\"offset\":%u,\"size\":%u,\"kind\":%u,\"label\":",
      item->has_section_index ? (unsigned)item->section_index : 0U, (unsigned)item->offset,
      (unsigned)item->size, (unsigned)item->kind) != 0) return -1;
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

static int listing_data_class_is_known(const char *value) {
  static const char *known[] = {
    "audio_table",
    "bitmap",
    "blitter_destination",
    "blitter_source",
    "copper_list",
    "disk_buffer",
    "pointer_table",
    "sound_sample",
    "sprite",
    "string_control_stream"
  };
  size_t index;
  if (value == NULL || value[0] == '\0') return 0;
  for (index = 0U; index < sizeof(known) / sizeof(known[0]); ++index) {
    if (strcmp(value, known[index]) == 0) return 1;
  }
  return 0;
}

static const char *listing_data_class_for_structured_item(const M68kAnalysisStructuredDataItem *item) {
  if (item == NULL) return NULL;
  if (listing_data_class_is_known(item->semantic_role)) return item->semantic_role;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_STRING) return "string";
  return NULL;
}

static const char *app_slot_access_kind_name(uint8_t access_kind) {
  switch (access_kind) {
  case M68K_APP_SLOT_ACCESS_READ: return "read";
  case M68K_APP_SLOT_ACCESS_WRITE: return "write";
  case M68K_APP_SLOT_ACCESS_READ_WRITE: return "read-write";
  case M68K_APP_SLOT_ACCESS_ADDRESS: return "address";
  default: return NULL;
  }
}

static int listing_symbol_name_is_app_slot_ref(const char *symbol_name) {
  return symbol_name != NULL && strncmp(symbol_name, "app_", 4U) == 0 && strcmp(symbol_name, "app_SIZEOF") != 0;
}

static int listing_app_slot_fallback_symbol_name(int16_t displacement, char *symbol_name, size_t symbol_name_size) {
  int written;
  if (symbol_name == NULL || symbol_name_size == 0U) return 0;
  written = snprintf(symbol_name, symbol_name_size, "app_%04X", (unsigned)(uint16_t)displacement);
  return written > 0 && (size_t)written < symbol_name_size;
}

static int listing_app_slot_memory_write_is_readwrite(const M68kSimFormMetadata *metadata) {
  if (metadata == NULL) return 0;
  switch (metadata->operation_type) {
  case M68K_SIM_OP_MOVE:
  case M68K_SIM_OP_CLEAR:
  case M68K_SIM_OP_SET_COND:
  case M68K_SIM_OP_MOVE_MULTIPLE:
  case M68K_SIM_OP_MOVE_PERIPHERAL:
    return 0;
  default:
    return 1;
  }
}

static const char *listing_app_slot_access_kind(const M68kSimFormMetadata *metadata, size_t operand_index,
    const M68kOperandIR *operand) {
  uint8_t access_kind;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  if (metadata == NULL || operand == NULL || operand_index >= 4U) return NULL;
  if (!operand_is_indirect_or_disp_an(operand, &base_reg, &displacement)) return NULL;
  access_kind = metadata->operand_access_kinds[operand_index];
  if (access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS || access_kind == M68K_SIM_ACCESS_BRANCH_TARGET)
    return "address";
  if (access_kind == M68K_SIM_ACCESS_MEMORY_READ || access_kind == M68K_SIM_ACCESS_REGISTER_READ)
    return "read";
  if (access_kind == M68K_SIM_ACCESS_MEMORY_WRITE || access_kind == M68K_SIM_ACCESS_REGISTER_WRITE) {
    return listing_app_slot_memory_write_is_readwrite(metadata) ? "read-write" : "write";
  }
  return NULL;
}

static const char *listing_app_slot_ref_symbol_name(const M68kStatementIR *stmt, const M68kAppSlotRefIR *ref,
    char *fallback, size_t fallback_size) {
  const M68kOperandIR *operand;
  if (stmt != NULL && stmt->kind == M68K_STATEMENT_INSTRUCTION && ref != NULL &&
      ref->operand_index < stmt->u.instruction.operand_count) {
    operand = &stmt->u.instruction.operands[ref->operand_index];
    if (operand->symbol_ref.has_name != 0U && listing_symbol_name_is_app_slot_ref(operand->symbol_ref.name))
      return operand->symbol_ref.name;
  }
  if (ref == NULL || !listing_app_slot_fallback_symbol_name(ref->displacement, fallback, fallback_size)) return NULL;
  return fallback;
}

static int append_listing_app_slot_ref_json(JsonBuilder *builder, const char *symbol_name, int16_t displacement,
    uint8_t base_reg, uint8_t operand_index, const char *access_kind) {
  char base_register[4];
  if (symbol_name == NULL || access_kind == NULL) return 0;
  snprintf(base_register, sizeof(base_register), "A%u", (unsigned)base_reg);
  if (json_builder_append(builder, "{\"symbol\":") != 0) return -1;
  if (json_builder_append_json_string(builder, symbol_name) != 0) return -1;
  if (json_builder_appendf(builder, ",\"displacement\":%d,\"base_register\":", (int)displacement) != 0)
    return -1;
  if (json_builder_append_json_string(builder, base_register) != 0) return -1;
  if (json_builder_appendf(builder, ",\"operand_index\":%u,\"access\":", (unsigned)operand_index) != 0)
    return -1;
  if (json_builder_append_json_string(builder, access_kind) != 0) return -1;
  return json_builder_append(builder, "}");
}

static int append_listing_app_slot_refs_json(JsonBuilder *builder, const M68kStatementIR *stmt,
    const M68kSectionAnalysisIR *section_analysis) {
  size_t operand_index;
  int emitted = 0;
  const M68kInstructionIR *instruction;
  const M68kSimFormMetadata *metadata;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION) return json_builder_append(builder, "]");
  if (section_analysis != NULL) {
    size_t ref_index;
    for (ref_index = 0U; ref_index < section_analysis->app_slot_ref_count; ++ref_index) {
      const M68kAppSlotRefIR *ref = &section_analysis->app_slot_refs[ref_index];
      char fallback_symbol[64];
      const char *symbol_name;
      const char *access_kind;
      if (ref->offset != stmt->offset) continue;
      symbol_name = listing_app_slot_ref_symbol_name(stmt, ref, fallback_symbol, sizeof(fallback_symbol));
      access_kind = app_slot_access_kind_name(ref->access_kind);
      if (symbol_name == NULL || access_kind == NULL) continue;
      if (emitted && json_builder_append(builder, ",") != 0) return -1;
      if (append_listing_app_slot_ref_json(builder, symbol_name, ref->displacement, ref->base_reg,
          ref->operand_index, access_kind) != 0)
        return -1;
      emitted = 1;
    }
    return json_builder_append(builder, "]");
  }
  instruction = &stmt->u.instruction;
  metadata = instruction_sim_metadata(instruction);
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand_ir = &instruction->operands[operand_index];
    uint8_t base_reg = 0U;
    int16_t displacement = 0;
    const char *access_kind;
    if (operand_ir->symbol_ref.has_name == 0U ||
        !listing_symbol_name_is_app_slot_ref(operand_ir->symbol_ref.name)) {
      continue;
    }
    if (!operand_is_indirect_or_disp_an(operand_ir, &base_reg, &displacement)) continue;
    access_kind = listing_app_slot_access_kind(metadata, operand_index, operand_ir);
    if (access_kind == NULL) continue;
    if (emitted && json_builder_append(builder, ",") != 0) return -1;
    if (append_listing_app_slot_ref_json(builder, operand_ir->symbol_ref.name, displacement, base_reg,
        (uint8_t)operand_index, access_kind) != 0)
      return -1;
    emitted = 1;
  }
  return json_builder_append(builder, "]");
}

static int listing_comment_runtime_pointer_address(const char *comment, uint32_t *out_address) {
  const char *marker;
  uint32_t value = 0U;
  int parsed = 0;
  if (out_address != NULL) *out_address = 0U;
  if (comment == NULL) return 0;
  marker = strstr(comment, " pointer $");
  if (marker == NULL) return 0;
  marker += strlen(" pointer $");
  while (*marker != '\0') {
    uint32_t digit;
    if (*marker >= '0' && *marker <= '9') digit = (uint32_t)(*marker - '0');
    else if (*marker >= 'A' && *marker <= 'F') digit = (uint32_t)(*marker - 'A' + 10);
    else if (*marker >= 'a' && *marker <= 'f') digit = (uint32_t)(*marker - 'a' + 10);
    else break;
    if (value > (UINT32_MAX - digit) / 16U) return 0;
    value = value * 16U + digit;
    parsed = 1;
    ++marker;
  }
  if (!parsed) return 0;
  if (out_address != NULL) *out_address = value;
  return 1;
}

static int append_listing_runtime_address_ref_json(JsonBuilder *builder, const M68kRuntimeAddressRefIR *ref) {
  if (json_builder_appendf(builder, "{\"offset\":%u,\"operand_index\":",
      (unsigned)ref->offset) != 0)
    return -1;
  if (ref->operand_index == UINT32_MAX) {
    if (json_builder_append(builder, "null") != 0) return -1;
  } else if (json_builder_appendf(builder, "%u", (unsigned)ref->operand_index) != 0) return -1;
  if (json_builder_append(builder, ",\"target_section_index\":") != 0) return -1;
  if (ref->has_target) {
    if (json_builder_appendf(builder, "%u", (unsigned)ref->target_section_index) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  if (json_builder_append(builder, ",\"target_offset\":") != 0) return -1;
  if (ref->has_target) {
    if (json_builder_appendf(builder, "%u", (unsigned)ref->target_offset) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  if (json_builder_append(builder, ",\"runtime_address\":") != 0) return -1;
  if (ref->has_runtime_address) {
    if (json_builder_appendf(builder, "%u", (unsigned)ref->runtime_address) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  if (ref->size != 0U) {
    if (json_builder_appendf(builder, ",\"size\":%u", (unsigned)ref->size) != 0) return -1;
  }
  if (json_builder_appendf(builder, ",\"confidence\":%u,\"data_class\":",
      (unsigned)ref->confidence) != 0)
    return -1;
  if (json_builder_append_nullable_string(builder, ref->data_class) != 0) return -1;
  return json_builder_append(builder, "}");
}

static int append_listing_runtime_address_refs_json(JsonBuilder *builder, const M68kStatementIR *stmt,
    const M68kSectionAnalysisIR *section_analysis, const char *comment) {
  size_t index;
  int emitted = 0;
  uint32_t comment_runtime_address = 0U;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (stmt == NULL ||
      (stmt->kind != M68K_STATEMENT_INSTRUCTION && stmt->kind != M68K_STATEMENT_DATA) ||
      section_analysis == NULL)
    return json_builder_append(builder, "]");
  if (listing_comment_runtime_pointer_address(comment, &comment_runtime_address)) {
    for (index = 0U; index < section_analysis->runtime_address_ref_count; ++index) {
      const M68kRuntimeAddressRefIR *ref = &section_analysis->runtime_address_refs[index];
      if (!ref->has_runtime_address || ref->runtime_address != comment_runtime_address ||
          ref->data_class == NULL || strstr(comment, ref->data_class) == NULL)
        continue;
      if (emitted && json_builder_append(builder, ",") != 0) return -1;
      if (append_listing_runtime_address_ref_json(builder, ref) != 0) return -1;
      emitted = 1;
    }
    if (emitted) return json_builder_append(builder, "]");
  }
  for (index = 0U; index < section_analysis->runtime_address_ref_count; ++index) {
    const M68kRuntimeAddressRefIR *ref = &section_analysis->runtime_address_refs[index];
    if (ref->offset != stmt->offset) continue;
    if (emitted && json_builder_append(builder, ",") != 0) return -1;
    if (append_listing_runtime_address_ref_json(builder, ref) != 0) return -1;
    emitted = 1;
  }
  return json_builder_append(builder, "]");
}

static int append_listing_code_start_refs_json(JsonBuilder *builder, const M68kStatementIR *stmt,
    const M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  int emitted = 0;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION || section_analysis == NULL)
    return json_builder_append(builder, "]");
  for (index = 0U; index < section_analysis->code_start_ref_count; ++index) {
    const M68kCodeStartRefIR *ref = &section_analysis->code_start_refs[index];
    if (ref->offset != stmt->offset) continue;
    if (emitted && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_appendf(builder, "{\"offset\":%u,\"reason\":%u,\"reason_name\":",
        (unsigned)ref->offset, (unsigned)ref->reason) != 0)
      return -1;
    if (json_builder_append_json_string(builder, m68k_code_start_reason_name(ref->reason)) != 0) return -1;
    if (json_builder_appendf(builder,
        ",\"confidence\":%u,\"source_section_index\":%u,\"source_offset\":%u,\"runtime_address\":",
        (unsigned)ref->confidence, (unsigned)ref->source_section_index, (unsigned)ref->source_offset) != 0)
      return -1;
    if (ref->has_runtime_address) {
      if (json_builder_appendf(builder, "%u", (unsigned)ref->runtime_address) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) return -1;
    if (json_builder_appendf(builder, ",\"size\":%u}", (unsigned)ref->size) != 0) return -1;
    emitted = 1;
  }
  return json_builder_append(builder, "]");
}

static int append_listing_typed_accesses_json(JsonBuilder *builder, const M68kStatementIR *stmt,
    const M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  int emitted = 0;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION || section_analysis == NULL)
    return json_builder_append(builder, "]");
  for (index = 0U; index < section_analysis->recovered_platform_typed_access_count; ++index) {
    const M68kRecoveredPlatformTypedAccessIR *access = &section_analysis->recovered_platform_typed_accesses[index];
    const char *root_struct_name;
    const char *owner_struct_name;
    const char *field_name;
    if (access->offset != stmt->offset) continue;
    root_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref,
      access->root_struct_name);
    owner_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->owner_struct_ref,
      access->owner_struct_name);
    field_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->field_ref, access->field_name);
    if (emitted && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_appendf(builder,
        "{\"operand_index\":%u,\"base_register\":\"A%u\",\"displacement\":%d,\"field_offset\":%d,"
        "\"root_struct_name\":",
        (unsigned)access->operand_index, (unsigned)access->base_reg, (int)access->displacement,
        (int)access->field_offset) != 0)
      return -1;
    if (json_builder_append_nullable_string(builder, root_struct_name) != 0) return -1;
    if (json_builder_append(builder, ",\"owner_struct_name\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, owner_struct_name) != 0) return -1;
    if (json_builder_append(builder, ",\"field_name\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, field_name) != 0) return -1;
    if (json_builder_append(builder, ",\"field_expr\":") != 0) return -1;
    if (json_builder_append_json_string(builder, access->field_expr != NULL ? access->field_expr : "") != 0)
      return -1;
    if (json_builder_appendf(builder, ",\"inherited\":%u,\"nested\":%u,\"type_provenance_kind\":",
        (unsigned)access->inherited, (unsigned)access->nested) != 0)
      return -1;
    if (json_builder_append_json_string(builder, type_provenance_kind_name(access->type_provenance_kind)) != 0)
      return -1;
    if (access->type_provenance_kind != M68K_PLATFORM_TYPE_PROVENANCE_NONE &&
        json_builder_appendf(builder, ",\"type_provenance_section\":%u,\"type_provenance_offset\":%u",
          (unsigned)access->type_provenance_section_index, (unsigned)access->type_provenance_offset) != 0)
      return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
    emitted = 1;
  }
  return json_builder_append(builder, "]");
}

static int append_listing_unresolved_typed_accesses_json(JsonBuilder *builder, const M68kStatementIR *stmt,
    const M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  int emitted = 0;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION || section_analysis == NULL)
    return json_builder_append(builder, "]");
  for (index = 0U; index < section_analysis->recovered_platform_unresolved_typed_access_count; ++index) {
    const M68kRecoveredPlatformUnresolvedTypedAccessIR *access =
      &section_analysis->recovered_platform_unresolved_typed_accesses[index];
    const char *root_struct_name;
    const char *container_struct_name;
    const char *refined_struct_name;
    if (access->offset != stmt->offset) continue;
    root_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref,
      access->root_struct_name);
    container_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->container_struct_ref,
      access->container_struct_name);
    refined_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->refined_struct_ref,
      access->refined_struct_name);
    if (emitted && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_appendf(builder,
        "{\"operand_index\":%u,\"base_register\":\"A%u\",\"displacement\":%d,\"struct_size\":%u,"
        "\"root_struct_name\":",
        (unsigned)access->operand_index, (unsigned)access->base_reg, (int)access->displacement,
        (unsigned)access->struct_size) != 0)
      return -1;
    if (json_builder_append_nullable_string(builder, root_struct_name) != 0) return -1;
    if (json_builder_append(builder, ",\"classification\":") != 0) return -1;
    if (json_builder_append_json_string(builder,
        unresolved_typed_access_classification_name(access->classification)) != 0) return -1;
    if (json_builder_appendf(builder, ",\"container_candidate_count\":%u,\"container_struct_name\":",
        (unsigned)access->container_candidate_count) != 0) return -1;
    if (json_builder_append_nullable_string(builder, container_struct_name) != 0) return -1;
    if (json_builder_append(builder, ",\"container_field_expr\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, access->container_field_expr) != 0) return -1;
    if (json_builder_appendf(builder, ",\"refinement_applied\":%u,\"refined_struct_name\":",
        (unsigned)access->refinement_applied) != 0) return -1;
    if (json_builder_append_nullable_string(builder, refined_struct_name) != 0) return -1;
    if (json_builder_append(builder, ",\"type_provenance_kind\":") != 0) return -1;
    if (json_builder_append_json_string(builder, type_provenance_kind_name(access->type_provenance_kind)) != 0)
      return -1;
    if (access->type_provenance_kind != M68K_PLATFORM_TYPE_PROVENANCE_NONE &&
        json_builder_appendf(builder, ",\"type_provenance_section\":%u,\"type_provenance_offset\":%u",
          (unsigned)access->type_provenance_section_index, (unsigned)access->type_provenance_offset) != 0)
      return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
    emitted = 1;
  }
  return json_builder_append(builder, "]");
}

static int append_listing_operand_parts_json(JsonBuilder *builder, const M68kStatementIR *stmt) {
  size_t operand_index;
  int emitted = 0;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION) return json_builder_append(builder, "]");
  for (operand_index = 0U; operand_index < stmt->u.instruction.operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &stmt->u.instruction.operands[operand_index];
    const char *symbol_name = operand->symbol_ref.has_name != 0U ? operand->symbol_ref.name : NULL;
    if (symbol_name == NULL || symbol_name[0] == '\0') continue;
    if (emitted && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"kind\":\"symbol\",\"text\":") != 0) return -1;
    if (json_builder_append_json_string(builder, symbol_name) != 0) return -1;
    if (json_builder_append(builder,
          ",\"value\":null,\"register\":null,\"base_register\":null,\"displacement\":null,"
          "\"segment_addr\":null,\"metadata\":{\"symbol\":") != 0)
      return -1;
    if (json_builder_append_json_string(builder, symbol_name) != 0) return -1;
    if (json_builder_append(builder, "}}") != 0) return -1;
    emitted = 1;
  }
  return json_builder_append(builder, "]");
}

static const char *listing_operand_access_name(uint8_t access_kind) {
  switch (access_kind) {
  case M68K_SIM_ACCESS_NONE: return "none";
  case M68K_SIM_ACCESS_REGISTER_READ: return "register_read";
  case M68K_SIM_ACCESS_REGISTER_WRITE: return "register_write";
  case M68K_SIM_ACCESS_MEMORY_READ: return "memory_read";
  case M68K_SIM_ACCESS_MEMORY_WRITE: return "memory_write";
  case M68K_SIM_ACCESS_COMPUTE_ADDRESS: return "address";
  case M68K_SIM_ACCESS_IMMEDIATE: return "immediate";
  case M68K_SIM_ACCESS_BRANCH_TARGET: return "branch_target";
  case M68K_SIM_ACCESS_REGISTER_LIST_READ: return "register_list_read";
  case M68K_SIM_ACCESS_REGISTER_LIST_WRITE: return "register_list_write";
  default: return "unknown";
  }
}

static const char *listing_operation_type_name(uint8_t operation_type) {
  switch (operation_type) {
  case M68K_SIM_OP_NONE: return NULL;
  case M68K_SIM_OP_ADD: return "add";
  case M68K_SIM_OP_CLEAR: return "clear";
  case M68K_SIM_OP_COMPARE: return "compare";
  case M68K_SIM_OP_DBCC: return "dbcc";
  case M68K_SIM_OP_MOVE: return "move";
  case M68K_SIM_OP_SET_COND: return "set_cond";
  case M68K_SIM_OP_SUB: return "sub";
  case M68K_SIM_OP_SWAP: return "swap";
  case M68K_SIM_OP_TEST: return "test";
  case M68K_SIM_OP_PUSH_EA: return "push_ea";
  case M68K_SIM_OP_LINK: return "link";
  case M68K_SIM_OP_UNLK: return "unlk";
  case M68K_SIM_OP_TEST_AND_SET: return "test_and_set";
  case M68K_SIM_OP_BIT_TEST: return "bit_test";
  case M68K_SIM_OP_BIT_SET: return "bit_set";
  case M68K_SIM_OP_BIT_CLEAR: return "bit_clear";
  case M68K_SIM_OP_BIT_CHANGE: return "bit_change";
  case M68K_SIM_OP_MOVE_MULTIPLE: return "move_multiple";
  case M68K_SIM_OP_MOVE_PERIPHERAL: return "move_peripheral";
  case M68K_SIM_OP_LOGIC_AND: return "logic_and";
  case M68K_SIM_OP_LOGIC_OR: return "logic_or";
  case M68K_SIM_OP_LOGIC_XOR: return "logic_xor";
  case M68K_SIM_OP_NEGATE: return "negate";
  case M68K_SIM_OP_NOT: return "not";
  case M68K_SIM_OP_SIGN_EXTEND: return "sign_extend";
  case M68K_SIM_OP_SWAP_WORDS: return "swap_words";
  case M68K_SIM_OP_SHIFT: return "shift";
  case M68K_SIM_OP_ROTATE: return "rotate";
  case M68K_SIM_OP_ROTATE_EXTEND: return "rotate_extend";
  case M68K_SIM_OP_TRAPV: return "trapv";
  case M68K_SIM_OP_PACK: return "pack";
  case M68K_SIM_OP_UNPACK: return "unpack";
  case M68K_SIM_OP_MULTIPLY: return "multiply";
  case M68K_SIM_OP_DIVIDE: return "divide";
  case M68K_SIM_OP_BOUNDS_CHECK: return "bounds_check";
  case M68K_SIM_OP_COMPARE_SWAP: return "compare_swap";
  case M68K_SIM_OP_BITFIELD_CHANGE: return "bitfield_change";
  case M68K_SIM_OP_BITFIELD_CLEAR: return "bitfield_clear";
  case M68K_SIM_OP_BITFIELD_EXTRACT_SIGNED: return "bitfield_extract_signed";
  case M68K_SIM_OP_BITFIELD_EXTRACT_UNSIGNED: return "bitfield_extract_unsigned";
  case M68K_SIM_OP_BITFIELD_FIND_FIRST_ONE: return "bitfield_find_first_one";
  case M68K_SIM_OP_BITFIELD_INSERT: return "bitfield_insert";
  case M68K_SIM_OP_BITFIELD_SET: return "bitfield_set";
  case M68K_SIM_OP_BITFIELD_TEST: return "bitfield_test";
  default: return "unknown";
  }
}

static const char *listing_statement_operation_type(const M68kStatementIR *stmt) {
  const M68kSimFormMetadata *metadata;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION) return NULL;
  metadata = instruction_sim_metadata(&stmt->u.instruction);
  return metadata != NULL ? listing_operation_type_name(metadata->operation_type) : NULL;
}

static int append_listing_operand_accesses_json(JsonBuilder *builder, const M68kStatementIR *stmt) {
  const M68kInstructionIR *instruction;
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION) return json_builder_append(builder, "]");
  instruction = &stmt->u.instruction;
  metadata = instruction_sim_metadata(instruction);
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    const char *access_name = "unknown";
    if (metadata != NULL) access_name = listing_operand_access_name(metadata->operand_access_kinds[operand_index]);
    if (operand_index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append_json_string(builder, access_name) != 0) return -1;
  }
  return json_builder_append(builder, "]");
}

static int append_listing_operand_registers_json(JsonBuilder *builder, const M68kStatementIR *stmt) {
  const M68kInstructionIR *instruction;
  size_t operand_index;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION) return json_builder_append(builder, "]");
  instruction = &stmt->u.instruction;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    uint8_t is_address = 0U;
    uint8_t reg = 0U;
    if (operand_index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (m68k_instruction_operand_direct_register(operand, &is_address, &reg)) {
      if (json_builder_appendf(builder, "\"%c%u\"", is_address ? 'A' : 'D', (unsigned)reg) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) return -1;
  }
  return json_builder_append(builder, "]");
}

typedef struct ListingAppSlotRefRecord {
  char symbol[64];
  int16_t displacement;
  uint8_t base_reg;
  uint8_t operand_index;
  uint8_t width_size;
  char width_name[16];
  char access[16];
  size_t row_index;
  uint32_t addr;
  int section_index;
  char stable_key[128];
} ListingAppSlotRefRecord;

typedef struct ListingAppSlotSource {
  uint8_t valid;
  char symbol[64];
  int16_t displacement;
  int16_t symbol_displacement;
  uint8_t base_reg;
  size_t row_index;
  size_t origin_row_index;
  size_t last_row_index;
  uint32_t addr;
  char stable_key[128];
  uint8_t has_via_reg;
  uint8_t via_reg;
} ListingAppSlotSource;

typedef struct ListingAppSlotEvidence {
  size_t row_index;
  uint32_t addr;
  int section_index;
  char stable_key[128];
  char library[64];
  char function[64];
  char input_name[64];
  char reg[4];
  size_t source_row_index;
  size_t source_flow_row_index;
  uint32_t source_addr;
  char source_stable_key[128];
  char source_via_register[4];
} ListingAppSlotEvidence;

typedef struct ListingAppSlotApiArgCandidate {
  char id[96];
  char symbol[64];
  char base_symbol[64];
  int16_t displacement;
  int16_t base_displacement;
  uint8_t base_reg;
  ListingAppSlotEvidence evidence;
  char type_name[64];
  char reason[64];
} ListingAppSlotApiArgCandidate;

typedef struct ListingAppSlotTypedRegion {
  char id[96];
  char symbol[64];
  char base_symbol[64];
  int16_t offset;
  int16_t base_displacement;
  int16_t end;
  int16_t size;
  uint16_t struct_id;
  char struct_name[64];
  char struct_source[128];
  ListingAppSlotEvidence *evidence;
  size_t evidence_count;
  size_t evidence_capacity;
} ListingAppSlotTypedRegion;

typedef struct ListingAppSlotAnalysisBuilder {
  uint8_t enabled;
  ListingAppSlotRefRecord *refs;
  size_t ref_count;
  size_t ref_capacity;
  ListingAppSlotTypedRegion *regions;
  size_t region_count;
  size_t region_capacity;
  ListingAppSlotApiArgCandidate *untyped_api_args;
  size_t untyped_api_arg_count;
  size_t untyped_api_arg_capacity;
  ListingAppSlotSource *sources;
  size_t source_section_count;
} ListingAppSlotAnalysisBuilder;

typedef struct ListingAppSlotSummary {
  char symbol[64];
  int16_t displacement;
  uint8_t base_regs[8];
  uint32_t access_read;
  uint32_t access_write;
  uint32_t access_read_write;
  uint32_t access_address;
  uint32_t width_byte;
  uint32_t width_word;
  uint32_t width_long;
  uint32_t width_unknown;
  uint32_t ref_count;
  uint8_t observed_size;
  int16_t observed_end;
  size_t first_row_index;
  size_t last_row_index;
  uint32_t first_addr;
  uint32_t last_addr;
} ListingAppSlotSummary;

typedef struct ListingAppSlotFieldRefSummary {
  char symbol[64];
  int16_t displacement;
  int16_t field_offset;
  uint32_t ref_count;
  uint32_t access_read;
  uint32_t access_write;
  uint32_t access_read_write;
  uint32_t access_address;
  uint32_t width_byte;
  uint32_t width_word;
  uint32_t width_long;
  uint32_t width_unknown;
  uint8_t region_address;
  uint8_t has_field;
  AmigaOsResolvedStructFieldInfo field;
} ListingAppSlotFieldRefSummary;

typedef struct ListingAppSlotInterval {
  int16_t offset;
  int16_t end;
  char id[96];
} ListingAppSlotInterval;

static void listing_copy_text(char *dst, size_t dst_size, const char *src) {
  if (dst == NULL || dst_size == 0U) return;
  snprintf(dst, dst_size, "%s", src != NULL ? src : "");
}

static void listing_row_stable_key(char *buf, size_t buf_size, int section_index, uint32_t addr,
    const char *row_kind, size_t row_index) {
  if (buf == NULL || buf_size == 0U) return;
  snprintf(buf, buf_size, "s%d:%08X:%s:%u", section_index, (unsigned)addr, row_kind != NULL ? row_kind : "",
    (unsigned)row_index);
}

static void listing_register_name(char *buf, size_t buf_size, uint8_t reg) {
  if (buf == NULL || buf_size == 0U) return;
  snprintf(buf, buf_size, "A%u", (unsigned)reg);
}

static void listing_app_slot_ref_width(const M68kStatementIR *stmt, char *width_name, size_t width_name_size,
    uint8_t *out_width_size) {
  uint8_t width_size = 1U;
  const char *name = "unknown";
  if (stmt != NULL && stmt->kind == M68K_STATEMENT_INSTRUCTION) {
    if (stmt->u.instruction.size_suffix == 'b') {
      name = "byte";
      width_size = 1U;
    } else if (stmt->u.instruction.size_suffix == 'w') {
      name = "word";
      width_size = 2U;
    } else if (stmt->u.instruction.size_suffix == 'l') {
      name = "long";
      width_size = 4U;
    }
  }
  listing_copy_text(width_name, width_name_size, name);
  if (out_width_size != NULL) *out_width_size = width_size;
}

static int listing_app_slot_analysis_init(ListingAppSlotAnalysisBuilder *analysis,
    const M68kSourceFileIR *source_file, const M68kSourceAnalysisIR *source_analysis) {
  if (analysis == NULL) return -1;
  memset(analysis, 0, sizeof(*analysis));
  if (source_file == NULL || source_analysis == NULL ||
      source_file->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK ||
      source_analysis->section_count == 0U) {
    return 0;
  }
  analysis->sources = (ListingAppSlotSource *)calloc(source_analysis->section_count * 8U, sizeof(*analysis->sources));
  if (analysis->sources == NULL) return -1;
  analysis->source_section_count = source_analysis->section_count;
  analysis->enabled = 1U;
  return 0;
}

static void listing_app_slot_analysis_destroy(ListingAppSlotAnalysisBuilder *analysis) {
  size_t index;
  if (analysis == NULL) return;
  for (index = 0U; index < analysis->region_count; ++index) {
    free(analysis->regions[index].evidence);
  }
  free(analysis->regions);
  free(analysis->untyped_api_args);
  free(analysis->refs);
  free(analysis->sources);
  memset(analysis, 0, sizeof(*analysis));
}

static ListingAppSlotSource *listing_app_slot_source_for(ListingAppSlotAnalysisBuilder *analysis, int section_index,
    uint8_t reg) {
  if (analysis == NULL || analysis->sources == NULL || reg >= 8U || section_index < 0 ||
      (size_t)section_index >= analysis->source_section_count) {
    return NULL;
  }
  return &analysis->sources[((size_t)section_index * 8U) + reg];
}

static int listing_app_slot_analysis_append_ref(ListingAppSlotAnalysisBuilder *analysis,
    const ListingAppSlotRefRecord *ref) {
  ListingAppSlotRefRecord *grown;
  size_t next_capacity;
  if (analysis == NULL || ref == NULL || !analysis->enabled) return 0;
  if (analysis->ref_count == analysis->ref_capacity) {
    next_capacity = analysis->ref_capacity == 0U ? 64U : analysis->ref_capacity * 2U;
    grown = (ListingAppSlotRefRecord *)realloc(analysis->refs, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    analysis->refs = grown;
    analysis->ref_capacity = next_capacity;
  }
  analysis->refs[analysis->ref_count++] = *ref;
  return 0;
}

static ListingAppSlotTypedRegion *listing_app_slot_analysis_region_for(ListingAppSlotAnalysisBuilder *analysis,
    int16_t offset, int16_t end, uint16_t struct_id, const char *symbol, int16_t base_displacement) {
  ListingAppSlotTypedRegion *grown;
  ListingAppSlotTypedRegion *region;
  const char *struct_source = NULL;
  size_t index, next_capacity;
  if (analysis == NULL || !analysis->enabled) return NULL;
  for (index = 0U; index < analysis->region_count; ++index) {
    region = &analysis->regions[index];
    if (region->offset == offset && region->end == end && region->struct_id == struct_id) return region;
  }
  if (analysis->region_count == analysis->region_capacity) {
    next_capacity = analysis->region_capacity == 0U ? 8U : analysis->region_capacity * 2U;
    grown = (ListingAppSlotTypedRegion *)realloc(analysis->regions, next_capacity * sizeof(*grown));
    if (grown == NULL) return NULL;
    analysis->regions = grown;
    analysis->region_capacity = next_capacity;
  }
  region = &analysis->regions[analysis->region_count++];
  memset(region, 0, sizeof(*region));
  region->offset = offset;
  region->base_displacement = base_displacement;
  region->end = end;
  region->size = (int16_t)(end - offset);
  region->struct_id = struct_id;
  listing_copy_text(region->symbol, sizeof(region->symbol), symbol);
  listing_copy_text(region->base_symbol, sizeof(region->base_symbol), symbol);
  listing_copy_text(region->struct_name, sizeof(region->struct_name), amiga_os_name(7U, struct_id));
  amiga_struct_catalog_info(struct_id, &struct_source, NULL);
  listing_copy_text(region->struct_source, sizeof(region->struct_source), struct_source);
  snprintf(region->id, sizeof(region->id), "app_slot_region_%04X_%s", (unsigned)(uint16_t)offset,
    region->struct_name);
  return region;
}

static int listing_app_slot_analysis_append_evidence(ListingAppSlotTypedRegion *region,
    const ListingAppSlotEvidence *evidence) {
  ListingAppSlotEvidence *grown;
  size_t next_capacity;
  if (region == NULL || evidence == NULL) return -1;
  if (region->evidence_count == region->evidence_capacity) {
    next_capacity = region->evidence_capacity == 0U ? 2U : region->evidence_capacity * 2U;
    grown = (ListingAppSlotEvidence *)realloc(region->evidence, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    region->evidence = grown;
    region->evidence_capacity = next_capacity;
  }
  region->evidence[region->evidence_count++] = *evidence;
  return 0;
}

static int listing_app_slot_analysis_append_untyped_api_arg(ListingAppSlotAnalysisBuilder *analysis,
    const ListingAppSlotSource *source, const ListingAppSlotEvidence *evidence, const AmigaOsCallInputInfo *input,
    const char *reason) {
  ListingAppSlotApiArgCandidate *candidate;
  ListingAppSlotApiArgCandidate *grown;
  const char *type_name = NULL;
  size_t index, next_capacity;
  if (analysis == NULL || source == NULL || evidence == NULL || input == NULL || !analysis->enabled) return 0;
  for (index = 0U; index < analysis->untyped_api_arg_count; ++index) {
    candidate = &analysis->untyped_api_args[index];
    if (candidate->displacement == source->displacement && candidate->evidence.row_index == evidence->row_index &&
        strcmp(candidate->symbol, source->symbol) == 0 &&
        strcmp(candidate->evidence.reg, evidence->reg) == 0) {
      return 0;
    }
  }
  if (analysis->untyped_api_arg_count == analysis->untyped_api_arg_capacity) {
    next_capacity = analysis->untyped_api_arg_capacity == 0U ? 8U : analysis->untyped_api_arg_capacity * 2U;
    grown = (ListingAppSlotApiArgCandidate *)realloc(analysis->untyped_api_args, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    analysis->untyped_api_args = grown;
    analysis->untyped_api_arg_capacity = next_capacity;
  }
  candidate = &analysis->untyped_api_args[analysis->untyped_api_arg_count++];
  memset(candidate, 0, sizeof(*candidate));
  listing_copy_text(candidate->symbol, sizeof(candidate->symbol), source->symbol);
  listing_copy_text(candidate->base_symbol, sizeof(candidate->base_symbol), source->symbol);
  candidate->displacement = source->displacement;
  candidate->base_displacement = source->symbol_displacement;
  candidate->base_reg = source->base_reg;
  candidate->evidence = *evidence;
  type_name = amiga_os_name(6U, input->type_id);
  listing_copy_text(candidate->type_name, sizeof(candidate->type_name), type_name);
  listing_copy_text(candidate->reason, sizeof(candidate->reason), reason);
  snprintf(candidate->id, sizeof(candidate->id), "app_slot_api_arg_%04X_%s_%s",
    (unsigned)(uint16_t)candidate->displacement, evidence->function, evidence->reg);
  return 0;
}

static int listing_app_slot_address_target_register(const M68kStatementIR *stmt, uint8_t ref_operand_index,
    uint8_t *out_reg) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  uint8_t found = 0U;
  uint8_t found_reg = 0U;
  if (out_reg != NULL) *out_reg = 0U;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION) return 0;
  metadata = instruction_sim_metadata(&stmt->u.instruction);
  if (metadata == NULL) return 0;
  for (operand_index = 0U; operand_index < stmt->u.instruction.operand_count && operand_index < 4U; ++operand_index) {
    uint8_t is_address = 0U;
    uint8_t reg = 0U;
    if (operand_index == ref_operand_index ||
        metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_REGISTER_WRITE ||
        !m68k_instruction_operand_direct_register(&stmt->u.instruction.operands[operand_index], &is_address, &reg) ||
        !is_address) {
      continue;
    }
    if (found) return 0;
    found = 1U;
    found_reg = reg;
  }
  if (!found) return 0;
  if (out_reg != NULL) *out_reg = found_reg;
  return 1;
}

static int listing_app_slot_address_register_copy(const M68kStatementIR *stmt, uint8_t *out_source_reg,
    uint8_t *out_target_reg) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  uint8_t read_count = 0U, write_count = 0U;
  uint8_t read_reg = 0U, write_reg = 0U;
  if (out_source_reg != NULL) *out_source_reg = 0U;
  if (out_target_reg != NULL) *out_target_reg = 0U;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION) return 0;
  metadata = instruction_sim_metadata(&stmt->u.instruction);
  if (metadata == NULL || metadata->operation_type != M68K_SIM_OP_MOVE) return 0;
  for (operand_index = 0U; operand_index < stmt->u.instruction.operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &stmt->u.instruction.operands[operand_index];
    uint8_t access = metadata->operand_access_kinds[operand_index];
    uint8_t is_address = 0U;
    uint8_t reg = 0U;
    if (!m68k_instruction_operand_direct_register(operand, &is_address, &reg) || !is_address) continue;
    if (access == M68K_SIM_ACCESS_REGISTER_READ || access == M68K_SIM_ACCESS_MEMORY_READ) {
      ++read_count;
      read_reg = reg;
    } else if (access == M68K_SIM_ACCESS_REGISTER_WRITE || access == M68K_SIM_ACCESS_MEMORY_WRITE) {
      ++write_count;
      write_reg = reg;
    }
  }
  if (read_count != 1U || write_count != 1U || read_reg == write_reg) return 0;
  if (out_source_reg != NULL) *out_source_reg = read_reg;
  if (out_target_reg != NULL) *out_target_reg = write_reg;
  return 1;
}

static int listing_operand_is_immediate_value(const M68kOperandIR *operand, uint32_t *out_value) {
  if (out_value != NULL) *out_value = 0U;
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_IMM ||
      ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_ABSL) &&
        operand->value.ea_mode == 7U && operand->value.ea_reg == 4U)) {
    if (out_value != NULL) *out_value = operand->value.value;
    return 1;
  }
  return 0;
}

static int listing_app_slot_address_register_immediate_adjust(const M68kStatementIR *stmt, uint8_t *out_reg,
    int16_t *out_delta) {
  const M68kSimFormMetadata *metadata;
  const M68kOperandIR *source, *dest;
  uint8_t is_address = 0U, reg = 0U;
  uint32_t value = 0U;
  int32_t delta;
  if (out_reg != NULL) *out_reg = 0U;
  if (out_delta != NULL) *out_delta = 0;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION) return 0;
  metadata = instruction_sim_metadata(&stmt->u.instruction);
  if (metadata == NULL || (metadata->operation_type != M68K_SIM_OP_ADD &&
      metadata->operation_type != M68K_SIM_OP_SUB) ||
      metadata->source_operand_index >= stmt->u.instruction.operand_count ||
      metadata->dest_operand_index >= stmt->u.instruction.operand_count) {
    return 0;
  }
  source = &stmt->u.instruction.operands[metadata->source_operand_index];
  dest = &stmt->u.instruction.operands[metadata->dest_operand_index];
  if (!listing_operand_is_immediate_value(source, &value) || value > INT16_MAX ||
      !m68k_instruction_operand_direct_register(dest, &is_address, &reg) || !is_address) {
    return 0;
  }
  delta = metadata->operation_type == M68K_SIM_OP_SUB ? -(int32_t)value : (int32_t)value;
  if (delta < INT16_MIN || delta > INT16_MAX) return 0;
  if (out_reg != NULL) *out_reg = reg;
  if (out_delta != NULL) *out_delta = (int16_t)delta;
  return 1;
}

static int listing_app_slot_computed_address_register_copy(const M68kStatementIR *stmt, uint8_t *out_source_reg,
    uint8_t *out_target_reg, int16_t *out_delta) {
  const M68kSimFormMetadata *metadata;
  const M68kOperandIR *source, *dest;
  size_t operand_index;
  uint8_t is_address = 0U, target_reg = 0U;
  uint8_t source_reg = 0U;
  int16_t displacement = 0;
  uint8_t source_operand_index = 255U, dest_operand_index = 255U;
  if (out_source_reg != NULL) *out_source_reg = 0U;
  if (out_target_reg != NULL) *out_target_reg = 0U;
  if (out_delta != NULL) *out_delta = 0;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION) return 0;
  metadata = instruction_sim_metadata(&stmt->u.instruction);
  if (metadata == NULL) return 0;
  for (operand_index = 0U; operand_index < stmt->u.instruction.operand_count && operand_index < 4U; ++operand_index) {
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_COMPUTE_ADDRESS) {
      if (source_operand_index != 255U) return 0;
      source_operand_index = (uint8_t)operand_index;
    } else if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE) {
      const M68kOperandIR *operand = &stmt->u.instruction.operands[operand_index];
      uint8_t operand_is_address = 0U, operand_reg = 0U;
      if (!m68k_instruction_operand_direct_register(operand, &operand_is_address, &operand_reg) ||
          !operand_is_address) {
        continue;
      }
      if (dest_operand_index != 255U) return 0;
      dest_operand_index = (uint8_t)operand_index;
    }
  }
  if (source_operand_index == 255U || dest_operand_index == 255U) return 0;
  source = &stmt->u.instruction.operands[source_operand_index];
  dest = &stmt->u.instruction.operands[dest_operand_index];
  if (!m68k_instruction_operand_direct_register(dest, &is_address, &target_reg) || !is_address) return 0;
  if (!operand_is_indirect_or_disp_an(source, &source_reg, &displacement)) return 0;
  if (source_reg >= 8U) return 0;
  if (out_source_reg != NULL) *out_source_reg = source_reg;
  if (out_target_reg != NULL) *out_target_reg = target_reg;
  if (out_delta != NULL) *out_delta = displacement;
  return 1;
}

static void listing_app_slot_mark_written_address_registers(const M68kStatementIR *stmt, uint8_t written_regs[8]) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION || written_regs == NULL) return;
  metadata = instruction_sim_metadata(&stmt->u.instruction);
  if (metadata == NULL) return;
  for (operand_index = 0U; operand_index < stmt->u.instruction.operand_count && operand_index < 4U; ++operand_index) {
    uint8_t is_address = 0U;
    uint8_t reg = 0U;
    uint8_t access = metadata->operand_access_kinds[operand_index];
    if (access != M68K_SIM_ACCESS_REGISTER_WRITE && access != M68K_SIM_ACCESS_MEMORY_WRITE &&
        access != M68K_SIM_ACCESS_REGISTER_LIST_WRITE) {
      continue;
    }
    if (!m68k_instruction_operand_direct_register(&stmt->u.instruction.operands[operand_index], &is_address, &reg) ||
        !is_address || reg >= 8U) {
      continue;
    }
    written_regs[reg] = 1U;
  }
}

static int listing_app_slot_analysis_add_api_regions(ListingAppSlotAnalysisBuilder *analysis, int section_index,
    size_t row_index, const char *row_kind, const M68kStatementIR *stmt, const M68kSectionAnalysisIR *section) {
  size_t call_index;
  if (analysis == NULL || !analysis->enabled || stmt == NULL || section == NULL ||
      stmt->kind != M68K_STATEMENT_INSTRUCTION) {
    return 0;
  }
  for (call_index = 0U; call_index < section->recovered_platform_call_count; ++call_index) {
    const M68kRecoveredPlatformCallIR *call = &section->recovered_platform_calls[call_index];
    const AmigaOsLibraryVectorInfo *vector;
    const AmigaOsCallInputInfo *inputs;
    const char *resolved_symbol = NULL;
    const char *library_name;
    const char *function_name;
    size_t input_count = 0U;
    size_t input_index;
    if (call->offset != stmt->offset) continue;
    vector = resolve_amiga_call_vector_for_json(call, &resolved_symbol);
    if (vector == NULL) continue;
    library_name = resolve_amiga_call_library_name_for_json(call, vector);
    function_name = amiga_os_name(3U, vector->function_id);
    inputs = amiga_os_library_vector_inputs(vector, &input_count);
    for (input_index = 0U; input_index < input_count; ++input_index) {
      const AmigaOsCallInputInfo *input = &inputs[input_index];
      ListingAppSlotSource *source;
      ListingAppSlotTypedRegion *region;
      ListingAppSlotEvidence evidence;
      int16_t struct_size = 0;
      int16_t end;
      uint8_t source_is_stale;
      if (input->reg_kind != AMIGA_OS_REGISTER_ADDRESS || input->reg_index >= 8U) continue;
      source = listing_app_slot_source_for(analysis, section_index, input->reg_index);
      source_is_stale = source != NULL && row_index - source->last_row_index > 32U;
      if (source == NULL || !source->valid || source->last_row_index >= row_index || source_is_stale) continue;
      memset(&evidence, 0, sizeof(evidence));
      evidence.row_index = row_index;
      evidence.addr = stmt->offset;
      evidence.section_index = section_index;
      listing_row_stable_key(evidence.stable_key, sizeof(evidence.stable_key), section_index, stmt->offset, row_kind,
        row_index);
      listing_copy_text(evidence.library, sizeof(evidence.library), library_name);
      listing_copy_text(evidence.function, sizeof(evidence.function), function_name);
      listing_copy_text(evidence.input_name, sizeof(evidence.input_name), amiga_os_name(4U, input->input_id));
      listing_register_name(evidence.reg, sizeof(evidence.reg), input->reg_index);
      evidence.source_row_index = source->origin_row_index;
      evidence.source_flow_row_index = source->last_row_index;
      evidence.source_addr = source->addr;
      listing_copy_text(evidence.source_stable_key, sizeof(evidence.source_stable_key), source->stable_key);
      if (source->has_via_reg) listing_register_name(evidence.source_via_register,
        sizeof(evidence.source_via_register), source->via_reg);
      if (input->struct_id == AMIGA_OS_STRUCT_ID_NONE) {
        if (listing_app_slot_analysis_append_untyped_api_arg(analysis, source, &evidence, input,
            "missing_struct_metadata") != 0)
          return -1;
        continue;
      }
      amiga_struct_catalog_info(input->struct_id, NULL, &struct_size);
      if (struct_size <= 0 || source->displacement > INT16_MAX - struct_size) {
        if (listing_app_slot_analysis_append_untyped_api_arg(analysis, source, &evidence, input,
            "unknown_struct_size") != 0)
          return -1;
        continue;
      }
      end = (int16_t)(source->displacement + struct_size);
      region = listing_app_slot_analysis_region_for(analysis, source->displacement, end, input->struct_id,
        source->symbol, source->symbol_displacement);
      if (region == NULL) return -1;
      if (listing_app_slot_analysis_append_evidence(region, &evidence) != 0) return -1;
    }
  }
  return 0;
}

static int listing_app_slot_analysis_observe_row(ListingAppSlotAnalysisBuilder *analysis, size_t row_index,
    const char *row_kind, int section_index, const M68kStatementIR *stmt,
    const M68kSourceAnalysisIR *source_analysis) {
  const M68kSectionAnalysisIR *section = NULL;
  uint8_t set_regs[8] = {0};
  uint8_t written_regs[8] = {0};
  size_t ref_index;
  if (analysis == NULL || !analysis->enabled || stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION ||
      source_analysis == NULL || section_index < 0 || (size_t)section_index >= source_analysis->section_count) {
    return 0;
  }
  section = &source_analysis->sections[section_index];
  if (listing_app_slot_analysis_add_api_regions(analysis, section_index, row_index, row_kind, stmt, section) != 0)
    return -1;
  for (ref_index = 0U; ref_index < section->app_slot_ref_count; ++ref_index) {
    const M68kAppSlotRefIR *ref = &section->app_slot_refs[ref_index];
    char fallback_symbol[64];
    const char *symbol_name;
    const char *access_kind;
    ListingAppSlotRefRecord record;
    if (ref->offset != stmt->offset) continue;
    symbol_name = listing_app_slot_ref_symbol_name(stmt, ref, fallback_symbol, sizeof(fallback_symbol));
    access_kind = app_slot_access_kind_name(ref->access_kind);
    if (symbol_name == NULL || access_kind == NULL) continue;
    memset(&record, 0, sizeof(record));
    listing_copy_text(record.symbol, sizeof(record.symbol), symbol_name);
    record.displacement = ref->displacement;
    record.base_reg = ref->base_reg;
    record.operand_index = ref->operand_index;
    listing_copy_text(record.access, sizeof(record.access), access_kind);
    listing_app_slot_ref_width(strcmp(access_kind, "address") == 0 ? NULL : stmt, record.width_name,
      sizeof(record.width_name), &record.width_size);
    if (strcmp(access_kind, "address") == 0) record.width_size = 0U;
    record.row_index = row_index;
    record.addr = stmt->offset;
    record.section_index = section_index;
    listing_row_stable_key(record.stable_key, sizeof(record.stable_key), section_index, stmt->offset, row_kind,
      row_index);
    if (listing_app_slot_analysis_append_ref(analysis, &record) != 0) return -1;
    if (strcmp(access_kind, "address") == 0) {
      uint8_t target_reg = 0U;
      if (listing_app_slot_address_target_register(stmt, ref->operand_index, &target_reg)) {
        ListingAppSlotSource *source = listing_app_slot_source_for(analysis, section_index, target_reg);
        if (source != NULL) {
          memset(source, 0, sizeof(*source));
          source->valid = 1U;
          listing_copy_text(source->symbol, sizeof(source->symbol), symbol_name);
          source->displacement = ref->displacement;
          source->symbol_displacement = ref->displacement;
          source->base_reg = ref->base_reg;
          source->row_index = row_index;
          source->origin_row_index = row_index;
          source->last_row_index = row_index;
          source->addr = stmt->offset;
          listing_copy_text(source->stable_key, sizeof(source->stable_key), record.stable_key);
          set_regs[target_reg] = 1U;
        }
      }
    }
  }
  {
    uint8_t source_reg = 0U, target_reg = 0U;
    int16_t delta = 0;
    if (listing_app_slot_address_register_copy(stmt, &source_reg, &target_reg) ||
        listing_app_slot_computed_address_register_copy(stmt, &source_reg, &target_reg, &delta)) {
      ListingAppSlotSource *source = listing_app_slot_source_for(analysis, section_index, source_reg);
      ListingAppSlotSource *target = listing_app_slot_source_for(analysis, section_index, target_reg);
      int32_t adjusted = source != NULL ? (int32_t)source->displacement + (int32_t)delta : 0;
      if (source != NULL && target != NULL && source->valid && adjusted >= INT16_MIN && adjusted <= INT16_MAX) {
        *target = *source;
        target->displacement = (int16_t)adjusted;
        target->last_row_index = row_index;
        target->has_via_reg = 1U;
        target->via_reg = source_reg;
        set_regs[target_reg] = 1U;
      }
    }
  }
  {
    uint8_t target_reg = 0U;
    int16_t delta = 0;
    if (listing_app_slot_address_register_immediate_adjust(stmt, &target_reg, &delta)) {
      ListingAppSlotSource *source = listing_app_slot_source_for(analysis, section_index, target_reg);
      int32_t adjusted = source != NULL ? (int32_t)source->displacement + (int32_t)delta : 0;
      if (source != NULL && source->valid && adjusted >= INT16_MIN && adjusted <= INT16_MAX) {
        source->displacement = (int16_t)adjusted;
        source->last_row_index = row_index;
        set_regs[target_reg] = 1U;
      }
    }
  }
  listing_app_slot_mark_written_address_registers(stmt, written_regs);
  for (ref_index = 0U; ref_index < 8U; ++ref_index) {
    if (written_regs[ref_index] && !set_regs[ref_index]) {
      ListingAppSlotSource *source = listing_app_slot_source_for(analysis, section_index, (uint8_t)ref_index);
      if (source != NULL) memset(source, 0, sizeof(*source));
    }
  }
  return 0;
}

static int listing_app_slot_summary_compare(const void *left_ptr, const void *right_ptr) {
  const ListingAppSlotSummary *left = (const ListingAppSlotSummary *)left_ptr;
  const ListingAppSlotSummary *right = (const ListingAppSlotSummary *)right_ptr;
  if (left->displacement != right->displacement) return (int)left->displacement - (int)right->displacement;
  return strcmp(left->symbol, right->symbol);
}

static int listing_app_slot_region_compare(const void *left_ptr, const void *right_ptr) {
  const ListingAppSlotTypedRegion *left = (const ListingAppSlotTypedRegion *)left_ptr;
  const ListingAppSlotTypedRegion *right = (const ListingAppSlotTypedRegion *)right_ptr;
  if (left->offset != right->offset) return (int)left->offset - (int)right->offset;
  if (left->end != right->end) return (int)left->end - (int)right->end;
  return strcmp(left->struct_name, right->struct_name);
}

static int listing_app_slot_interval_compare(const void *left_ptr, const void *right_ptr) {
  const ListingAppSlotInterval *left = (const ListingAppSlotInterval *)left_ptr;
  const ListingAppSlotInterval *right = (const ListingAppSlotInterval *)right_ptr;
  if (left->offset != right->offset) return (int)left->offset - (int)right->offset;
  if (left->end != right->end) return (int)left->end - (int)right->end;
  return strcmp(left->id, right->id);
}

static int listing_app_slot_field_ref_compare(const void *left_ptr, const void *right_ptr) {
  const ListingAppSlotFieldRefSummary *left = (const ListingAppSlotFieldRefSummary *)left_ptr;
  const ListingAppSlotFieldRefSummary *right = (const ListingAppSlotFieldRefSummary *)right_ptr;
  if (left->field_offset != right->field_offset) return (int)left->field_offset - (int)right->field_offset;
  return strcmp(left->symbol, right->symbol);
}

static void listing_app_slot_summary_add_counts(ListingAppSlotSummary *summary, const ListingAppSlotRefRecord *ref) {
  if (summary == NULL || ref == NULL) return;
  ++summary->ref_count;
  if (ref->base_reg < 8U) summary->base_regs[ref->base_reg] = 1U;
  if (strcmp(ref->access, "read") == 0) ++summary->access_read;
  else if (strcmp(ref->access, "write") == 0) ++summary->access_write;
  else if (strcmp(ref->access, "read-write") == 0) ++summary->access_read_write;
  else if (strcmp(ref->access, "address") == 0) ++summary->access_address;
  if (ref->width_size != 0U) {
    if (strcmp(ref->width_name, "byte") == 0) ++summary->width_byte;
    else if (strcmp(ref->width_name, "word") == 0) ++summary->width_word;
    else if (strcmp(ref->width_name, "long") == 0) ++summary->width_long;
    else ++summary->width_unknown;
    if (ref->width_size > summary->observed_size) summary->observed_size = ref->width_size;
  }
  if (ref->row_index < summary->first_row_index) summary->first_row_index = ref->row_index;
  if (ref->row_index > summary->last_row_index) summary->last_row_index = ref->row_index;
  if (ref->addr < summary->first_addr) summary->first_addr = ref->addr;
  if (ref->addr > summary->last_addr) summary->last_addr = ref->addr;
}

static ListingAppSlotSummary *listing_app_slot_build_summaries(const ListingAppSlotAnalysisBuilder *analysis,
    size_t *out_count) {
  ListingAppSlotSummary *summaries = NULL;
  size_t summary_count = 0U, summary_capacity = 0U;
  size_t ref_index;
  if (out_count != NULL) *out_count = 0U;
  if (analysis == NULL || analysis->ref_count == 0U) return NULL;
  for (ref_index = 0U; ref_index < analysis->ref_count; ++ref_index) {
    const ListingAppSlotRefRecord *ref = &analysis->refs[ref_index];
    ListingAppSlotSummary *summary = NULL;
    size_t summary_index;
    for (summary_index = 0U; summary_index < summary_count; ++summary_index) {
      if (strcmp(summaries[summary_index].symbol, ref->symbol) == 0) {
        summary = &summaries[summary_index];
        break;
      }
    }
    if (summary == NULL) {
      ListingAppSlotSummary *grown;
      size_t next_capacity;
      if (summary_count == summary_capacity) {
        next_capacity = summary_capacity == 0U ? 32U : summary_capacity * 2U;
        grown = (ListingAppSlotSummary *)realloc(summaries, next_capacity * sizeof(*grown));
        if (grown == NULL) {
          free(summaries);
          return NULL;
        }
        summaries = grown;
        summary_capacity = next_capacity;
      }
      summary = &summaries[summary_count++];
      memset(summary, 0, sizeof(*summary));
      listing_copy_text(summary->symbol, sizeof(summary->symbol), ref->symbol);
      summary->displacement = ref->displacement;
      summary->first_row_index = ref->row_index;
      summary->last_row_index = ref->row_index;
      summary->first_addr = ref->addr;
      summary->last_addr = ref->addr;
    }
    listing_app_slot_summary_add_counts(summary, ref);
  }
  for (ref_index = 0U; ref_index < summary_count; ++ref_index) {
    ListingAppSlotSummary *summary = &summaries[ref_index];
    if (summary->observed_size == 0U) summary->observed_size = 1U;
    summary->observed_end = (int16_t)(summary->displacement + summary->observed_size);
  }
  qsort(summaries, summary_count, sizeof(*summaries), listing_app_slot_summary_compare);
  if (out_count != NULL) *out_count = summary_count;
  return summaries;
}

static int append_listing_count_object(JsonBuilder *builder, const char *first_name, uint32_t first_count,
    const char *second_name, uint32_t second_count, const char *third_name, uint32_t third_count,
    const char *fourth_name, uint32_t fourth_count) {
  int emitted = 0;
  const char *names[4];
  uint32_t counts[4];
  size_t index;
  names[0] = first_name;
  names[1] = second_name;
  names[2] = third_name;
  names[3] = fourth_name;
  counts[0] = first_count;
  counts[1] = second_count;
  counts[2] = third_count;
  counts[3] = fourth_count;
  if (json_builder_append(builder, "{") != 0) return -1;
  for (index = 0U; index < 4U; ++index) {
    if (counts[index] == 0U || names[index] == NULL) continue;
    if (emitted && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append_json_string(builder, names[index]) != 0) return -1;
    if (json_builder_appendf(builder, ":%u", (unsigned)counts[index]) != 0) return -1;
    emitted = 1;
  }
  return json_builder_append(builder, "}");
}

static int append_listing_app_slot_base_registers(JsonBuilder *builder, const uint8_t base_regs[8]) {
  uint8_t reg;
  int emitted = 0;
  if (json_builder_append(builder, "[") != 0) return -1;
  for (reg = 0U; reg < 8U; ++reg) {
    char reg_name[4];
    if (!base_regs[reg]) continue;
    if (emitted && json_builder_append(builder, ",") != 0) return -1;
    listing_register_name(reg_name, sizeof(reg_name), reg);
    if (json_builder_append_json_string(builder, reg_name) != 0) return -1;
    emitted = 1;
  }
  return json_builder_append(builder, "]");
}

static int append_listing_app_slot_slots_json(JsonBuilder *builder, const ListingAppSlotSummary *summaries,
    size_t summary_count) {
  size_t index;
  if (json_builder_append(builder, "[") != 0) return -1;
  for (index = 0U; index < summary_count; ++index) {
    const ListingAppSlotSummary *summary = &summaries[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"symbol\":") != 0) return -1;
    if (json_builder_append_json_string(builder, summary->symbol) != 0) return -1;
    if (json_builder_appendf(builder, ",\"displacement\":%d,\"base_registers\":", (int)summary->displacement) != 0)
      return -1;
    if (append_listing_app_slot_base_registers(builder, summary->base_regs) != 0) return -1;
    if (json_builder_appendf(builder, ",\"ref_count\":%u,\"access_counts\":", (unsigned)summary->ref_count) != 0)
      return -1;
    if (append_listing_count_object(builder, "read", summary->access_read, "write", summary->access_write,
        "read-write", summary->access_read_write, "address", summary->access_address) != 0)
      return -1;
    if (json_builder_append(builder, ",\"width_counts\":") != 0) return -1;
    if (append_listing_count_object(builder, "byte", summary->width_byte, "word", summary->width_word,
        "long", summary->width_long, "unknown", summary->width_unknown) != 0)
      return -1;
    if (json_builder_appendf(builder,
          ",\"observed_size\":%u,\"observed_end\":%d,\"first_row_index\":%u,\"last_row_index\":%u,"
          "\"first_addr\":%u,\"last_addr\":%u}",
          (unsigned)summary->observed_size, (int)summary->observed_end, (unsigned)summary->first_row_index,
          (unsigned)summary->last_row_index, (unsigned)summary->first_addr, (unsigned)summary->last_addr) != 0)
      return -1;
  }
  return json_builder_append(builder, "]");
}

static void listing_app_slot_field_ref_add_counts(ListingAppSlotFieldRefSummary *summary,
    const ListingAppSlotRefRecord *ref) {
  if (summary == NULL || ref == NULL) return;
  ++summary->ref_count;
  if (strcmp(ref->access, "read") == 0) ++summary->access_read;
  else if (strcmp(ref->access, "write") == 0) ++summary->access_write;
  else if (strcmp(ref->access, "read-write") == 0) ++summary->access_read_write;
  else if (strcmp(ref->access, "address") == 0) ++summary->access_address;
  if (ref->width_size != 0U) {
    if (strcmp(ref->width_name, "byte") == 0) ++summary->width_byte;
    else if (strcmp(ref->width_name, "word") == 0) ++summary->width_word;
    else if (strcmp(ref->width_name, "long") == 0) ++summary->width_long;
    else ++summary->width_unknown;
  }
}

static ListingAppSlotFieldRefSummary *listing_app_slot_build_field_refs(
    const ListingAppSlotAnalysisBuilder *analysis, const ListingAppSlotTypedRegion *region, size_t *out_count) {
  ListingAppSlotFieldRefSummary *fields = NULL;
  size_t field_count = 0U, field_capacity = 0U;
  size_t ref_index;
  if (out_count != NULL) *out_count = 0U;
  if (analysis == NULL || region == NULL) return NULL;
  for (ref_index = 0U; ref_index < analysis->ref_count; ++ref_index) {
    const ListingAppSlotRefRecord *ref = &analysis->refs[ref_index];
    ListingAppSlotFieldRefSummary *field = NULL;
    int16_t field_offset;
    size_t field_index;
    if (ref->displacement < region->offset || ref->displacement >= region->end) continue;
    field_offset = (int16_t)(ref->displacement - region->offset);
    for (field_index = 0U; field_index < field_count; ++field_index) {
      if (fields[field_index].field_offset == field_offset &&
          strcmp(fields[field_index].symbol, ref->symbol) == 0) {
        field = &fields[field_index];
        break;
      }
    }
    if (field == NULL) {
      ListingAppSlotFieldRefSummary *grown;
      size_t next_capacity;
      if (field_count == field_capacity) {
        next_capacity = field_capacity == 0U ? 8U : field_capacity * 2U;
        grown = (ListingAppSlotFieldRefSummary *)realloc(fields, next_capacity * sizeof(*grown));
        if (grown == NULL) {
          free(fields);
          return NULL;
        }
        fields = grown;
        field_capacity = next_capacity;
      }
      field = &fields[field_count++];
      memset(field, 0, sizeof(*field));
      listing_copy_text(field->symbol, sizeof(field->symbol), ref->symbol);
      field->displacement = ref->displacement;
      field->field_offset = field_offset;
      field->region_address = strcmp(ref->access, "address") == 0 && field_offset == 0 &&
        strcmp(ref->symbol, region->symbol) == 0;
      if (!field->region_address &&
          amiga_os_resolve_struct_field_by_struct_id(region->struct_id, field_offset, 0, &field->field)) {
        field->has_field = 1U;
      }
    } else if (!(strcmp(ref->access, "address") == 0 && field_offset == 0 &&
        strcmp(ref->symbol, region->symbol) == 0)) {
      field->region_address = 0U;
      if (!field->has_field &&
          amiga_os_resolve_struct_field_by_struct_id(region->struct_id, field_offset, 0, &field->field)) {
        field->has_field = 1U;
      }
    }
    listing_app_slot_field_ref_add_counts(field, ref);
  }
  qsort(fields, field_count, sizeof(*fields), listing_app_slot_field_ref_compare);
  if (out_count != NULL) *out_count = field_count;
  return fields;
}

static uint8_t listing_app_slot_field_observed_size(const ListingAppSlotFieldRefSummary *field) {
  if (field == NULL) return 1U;
  if (field->width_long != 0U) return 4U;
  if (field->width_word != 0U) return 2U;
  if (field->width_byte != 0U || field->width_unknown != 0U) return 1U;
  return 1U;
}

static int append_listing_resolved_field_path_json(JsonBuilder *builder,
    const AmigaOsResolvedStructFieldInfo *resolved) {
  size_t index;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (resolved != NULL) {
    for (index = 0U; index < resolved->path_count; ++index) {
      const char *name = amiga_os_name(8U, resolved->path_field_ids[index]);
      if (name == NULL) continue;
      if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
      if (json_builder_append_json_string(builder, name) != 0) return -1;
    }
  }
  return json_builder_append(builder, "]");
}

static int append_listing_field_refs_json(JsonBuilder *builder, const ListingAppSlotAnalysisBuilder *analysis,
    const ListingAppSlotTypedRegion *region, const ListingAppSlotFieldRefSummary *fields, size_t field_count) {
  size_t field_index;
  if (json_builder_append(builder, "[") != 0) return -1;
  for (field_index = 0U; field_index < field_count; ++field_index) {
    const ListingAppSlotFieldRefSummary *field = &fields[field_index];
    size_t ref_index;
    int emitted_ref = 0;
    if (field_index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"symbol\":") != 0) return -1;
    if (json_builder_append_json_string(builder, field->symbol) != 0) return -1;
    if (json_builder_appendf(builder,
          ",\"base_symbol\":") != 0)
      return -1;
    if (json_builder_append_json_string(builder, region->symbol) != 0) return -1;
    if (json_builder_appendf(builder,
          ",\"displacement\":%d,\"field_offset\":%d,\"ref_count\":%u,\"access_counts\":",
          (int)field->displacement, (int)field->field_offset, (unsigned)field->ref_count) != 0)
      return -1;
    if (append_listing_count_object(builder, "read", field->access_read, "write", field->access_write,
        "read-write", field->access_read_write, "address", field->access_address) != 0)
      return -1;
    if (json_builder_append(builder, ",\"width_counts\":") != 0) return -1;
    if (append_listing_count_object(builder, "byte", field->width_byte, "word", field->width_word,
        "long", field->width_long, "unknown", field->width_unknown) != 0)
      return -1;
    if (field->region_address && json_builder_append(builder, ",\"region_address\":true") != 0) return -1;
    if (field->has_field) {
      const char *field_name = amiga_os_name(8U, field->field.field_id);
      const char *owner_name = amiga_os_name(7U, field->field.owner_struct_id);
      if (json_builder_append(builder, ",\"field_name\":") != 0) return -1;
      if (json_builder_append_nullable_string(builder, field_name) != 0) return -1;
      if (json_builder_appendf(builder, ",\"field_base_offset\":%d,\"field_owner_struct\":",
            (int)field->field.offset) != 0)
        return -1;
      if (json_builder_append_nullable_string(builder, owner_name) != 0) return -1;
      if (json_builder_appendf(builder, ",\"field_inherited\":%s,\"field_nested\":%s,\"field_path\":",
            field->field.inherited ? "true" : "false", field->field.nested ? "true" : "false") != 0)
        return -1;
      if (append_listing_resolved_field_path_json(builder, &field->field) != 0) return -1;
      if (field->field.offset != field->field_offset &&
          json_builder_appendf(builder, ",\"field_delta\":%d", (int)(field->field_offset - field->field.offset)) != 0)
        return -1;
      {
        char field_expr[128];
        if (amiga_os_resolve_struct_field_symbol_expr_by_struct_id(region->struct_id, field->field_offset, 0,
            field_expr, sizeof(field_expr))) {
          if (json_builder_append(builder, ",\"field_expr\":") != 0) return -1;
          if (json_builder_append_json_string(builder, field_expr) != 0) return -1;
        }
      }
    }
    if (json_builder_append(builder, ",\"refs\":[") != 0) return -1;
    for (ref_index = 0U; ref_index < analysis->ref_count; ++ref_index) {
      const ListingAppSlotRefRecord *ref = &analysis->refs[ref_index];
      if (ref->displacement < region->offset || ref->displacement >= region->end ||
          (int16_t)(ref->displacement - region->offset) != field->field_offset ||
          strcmp(ref->symbol, field->symbol) != 0) {
        continue;
      }
      if (emitted_ref && json_builder_append(builder, ",") != 0) return -1;
      if (json_builder_appendf(builder, "{\"row_index\":%u,\"addr\":%u,\"access\":",
            (unsigned)ref->row_index, (unsigned)ref->addr) != 0)
        return -1;
      if (json_builder_append_json_string(builder, ref->access) != 0) return -1;
      if (json_builder_append(builder, ",\"stable_key\":") != 0) return -1;
      if (json_builder_append_json_string(builder, ref->stable_key) != 0) return -1;
      if (json_builder_append(builder, "}") != 0) return -1;
      emitted_ref = 1;
    }
    if (json_builder_append(builder, "]}") != 0) return -1;
  }
  return json_builder_append(builder, "]");
}

static int append_listing_app_slot_region_evidence_json(JsonBuilder *builder,
    const ListingAppSlotTypedRegion *region) {
  size_t index;
  if (json_builder_append(builder, "[") != 0) return -1;
  for (index = 0U; index < region->evidence_count; ++index) {
    const ListingAppSlotEvidence *evidence = &region->evidence[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_appendf(builder, "{\"row_index\":%u,\"addr\":%u,\"hunk_index\":%d,\"library\":",
          (unsigned)evidence->row_index, (unsigned)evidence->addr, evidence->section_index) != 0)
      return -1;
    if (json_builder_append_json_string(builder, evidence->library) != 0) return -1;
    if (json_builder_append(builder, ",\"function\":") != 0) return -1;
    if (json_builder_append_json_string(builder, evidence->function) != 0) return -1;
    if (json_builder_append(builder, ",\"input_name\":") != 0) return -1;
    if (json_builder_append_json_string(builder, evidence->input_name) != 0) return -1;
    if (json_builder_append(builder, ",\"register\":") != 0) return -1;
    if (json_builder_append_json_string(builder, evidence->reg) != 0) return -1;
    if (json_builder_append(builder, ",\"stable_key\":") != 0) return -1;
    if (json_builder_append_json_string(builder, evidence->stable_key) != 0) return -1;
    if (json_builder_appendf(builder,
          ",\"source_row_index\":%u,\"source_flow_row_index\":%u,\"source_addr\":%u,\"source_stable_key\":",
          (unsigned)evidence->source_row_index, (unsigned)evidence->source_flow_row_index,
          (unsigned)evidence->source_addr) != 0)
      return -1;
    if (json_builder_append_json_string(builder, evidence->source_stable_key) != 0) return -1;
    if (evidence->source_via_register[0] != '\0') {
      if (json_builder_append(builder, ",\"source_via_register\":") != 0) return -1;
      if (json_builder_append_json_string(builder, evidence->source_via_register) != 0) return -1;
    }
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  return json_builder_append(builder, "]");
}

static int append_listing_app_slot_regions_json(JsonBuilder *builder, const ListingAppSlotAnalysisBuilder *analysis,
    const ListingAppSlotSummary *summaries, size_t summary_count) {
  size_t index;
  int emitted = 0;
  if (json_builder_append(builder, "[") != 0) return -1;
  for (index = 0U; index < analysis->region_count; ++index) {
    const ListingAppSlotTypedRegion *region = &analysis->regions[index];
    ListingAppSlotFieldRefSummary *fields;
    size_t field_count = 0U;
    fields = listing_app_slot_build_field_refs(analysis, region, &field_count);
    if (emitted && json_builder_append(builder, ",") != 0) {
      free(fields);
      return -1;
    }
    if (json_builder_append(builder, "{\"id\":") != 0) {
      free(fields);
      return -1;
    }
    if (json_builder_append_json_string(builder, region->id) != 0 ||
        json_builder_append(builder, ",\"symbol\":") != 0 ||
        json_builder_append_json_string(builder, region->symbol) != 0 ||
        json_builder_append(builder, ",\"base_symbol\":") != 0 ||
        json_builder_append_json_string(builder, region->base_symbol) != 0 ||
        json_builder_appendf(builder,
          ",\"offset\":%d,\"base_displacement\":%d,\"effective_offset\":%d,\"end\":%d,\"size\":%d,"
          "\"source\":\"platform_api_arg\","
          "\"confidence\":\"tool-inferred\",\"struct_name\":",
          (int)region->offset, (int)region->base_displacement, (int)region->offset, (int)region->end,
          (int)region->size) != 0 ||
        json_builder_append_json_string(builder, region->struct_name) != 0 ||
        json_builder_append(builder, ",\"struct_source\":") != 0 ||
        json_builder_append_json_string(builder, region->struct_source) != 0 ||
        json_builder_append(builder, ",\"evidence\":") != 0 ||
        append_listing_app_slot_region_evidence_json(builder, region) != 0 ||
        json_builder_append(builder, ",\"field_refs\":") != 0 ||
        append_listing_field_refs_json(builder, analysis, region, fields, field_count) != 0 ||
        json_builder_append(builder, "}") != 0) {
      free(fields);
      return -1;
    }
    free(fields);
    emitted = 1;
  }
  for (index = 0U; index < summary_count; ++index) {
    const ListingAppSlotSummary *summary = &summaries[index];
    char id[96];
    snprintf(id, sizeof(id), "app_slot_observed_%s", summary->symbol);
    if (emitted && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"id\":") != 0) return -1;
    if (json_builder_append_json_string(builder, id) != 0) return -1;
    if (json_builder_append(builder, ",\"symbol\":") != 0) return -1;
    if (json_builder_append_json_string(builder, summary->symbol) != 0) return -1;
    if (json_builder_appendf(builder,
          ",\"offset\":%d,\"end\":%d,\"size\":%d,\"source\":\"observed_app_slot_refs\","
          "\"confidence\":\"tool-inferred\",\"ref_count\":%u,\"covered_by_regions\":[",
          (int)summary->displacement, (int)summary->observed_end,
          (int)(summary->observed_end - summary->displacement), (unsigned)summary->ref_count) != 0)
      return -1;
    {
      size_t region_index;
      int emitted_region = 0;
      for (region_index = 0U; region_index < analysis->region_count; ++region_index) {
        const ListingAppSlotTypedRegion *region = &analysis->regions[region_index];
        if (region->offset <= summary->displacement && summary->observed_end <= region->end) {
          if (emitted_region && json_builder_append(builder, ",") != 0) return -1;
          if (json_builder_append_json_string(builder, region->id) != 0) return -1;
          emitted_region = 1;
        }
      }
    }
    if (json_builder_append(builder, "]}") != 0) return -1;
    emitted = 1;
  }
  return json_builder_append(builder, "]");
}

static ListingAppSlotInterval *listing_app_slot_build_intervals(const ListingAppSlotAnalysisBuilder *analysis,
    const ListingAppSlotSummary *summaries, size_t summary_count, size_t *out_count) {
  ListingAppSlotInterval *intervals;
  size_t index, count = 0U;
  if (out_count != NULL) *out_count = 0U;
  if (analysis == NULL || (analysis->region_count + summary_count) == 0U) return NULL;
  intervals = (ListingAppSlotInterval *)calloc(analysis->region_count + summary_count, sizeof(*intervals));
  if (intervals == NULL) return NULL;
  for (index = 0U; index < analysis->region_count; ++index) {
    intervals[count].offset = analysis->regions[index].offset;
    intervals[count].end = analysis->regions[index].end;
    listing_copy_text(intervals[count].id, sizeof(intervals[count].id), analysis->regions[index].id);
    ++count;
  }
  for (index = 0U; index < summary_count; ++index) {
    intervals[count].offset = summaries[index].displacement;
    intervals[count].end = summaries[index].observed_end;
    snprintf(intervals[count].id, sizeof(intervals[count].id), "app_slot_observed_%s", summaries[index].symbol);
    ++count;
  }
  qsort(intervals, count, sizeof(*intervals), listing_app_slot_interval_compare);
  if (out_count != NULL) *out_count = count;
  return intervals;
}

static int append_listing_app_slot_gaps_json(JsonBuilder *builder, const ListingAppSlotInterval *intervals,
    size_t interval_count, size_t *out_gap_count) {
  size_t index;
  int emitted = 0;
  int16_t current_end;
  const char *current_id;
  size_t gap_count = 0U;
  if (out_gap_count != NULL) *out_gap_count = 0U;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (interval_count == 0U) return json_builder_append(builder, "]");
  current_end = intervals[0].end;
  current_id = intervals[0].id;
  for (index = 1U; index < interval_count; ++index) {
    if (intervals[index].offset > current_end) {
      if (emitted && json_builder_append(builder, ",") != 0) return -1;
      if (json_builder_appendf(builder, "{\"start\":%d,\"end\":%d,\"size\":%d,\"after\":",
            (int)current_end, (int)intervals[index].offset, (int)(intervals[index].offset - current_end)) != 0)
        return -1;
      if (json_builder_append_json_string(builder, current_id) != 0) return -1;
      if (json_builder_append(builder, ",\"before\":") != 0) return -1;
      if (json_builder_append_json_string(builder, intervals[index].id) != 0) return -1;
      if (json_builder_append(builder, ",\"coverage\":\"unknown_app_slot_space\"}") != 0) return -1;
      emitted = 1;
      ++gap_count;
    }
    if (intervals[index].end > current_end) {
      current_end = intervals[index].end;
      current_id = intervals[index].id;
    }
  }
  if (out_gap_count != NULL) *out_gap_count = gap_count;
  return json_builder_append(builder, "]");
}

static size_t listing_app_slot_gap_count(const ListingAppSlotInterval *intervals, size_t interval_count) {
  size_t index, gap_count = 0U;
  int16_t current_end;
  if (intervals == NULL || interval_count == 0U) return 0U;
  current_end = intervals[0].end;
  for (index = 1U; index < interval_count; ++index) {
    if (intervals[index].offset > current_end) ++gap_count;
    if (intervals[index].end > current_end) current_end = intervals[index].end;
  }
  return gap_count;
}

static int append_listing_app_slot_field_gap_json(JsonBuilder *builder, const ListingAppSlotTypedRegion *region,
    int16_t start, int16_t end, size_t *io_count) {
  AmigaOsResolvedStructFieldInfo resolved;
  int has_field;
  if (builder == NULL || region == NULL || start >= end) return -1;
  has_field = amiga_os_resolve_struct_field_by_struct_id(region->struct_id, start, 1, &resolved);
  if (json_builder_appendf(builder,
        "{\"id\":\"%s_field_gap_%04X_%04X\",\"region_id\":",
        region->id, (unsigned)(uint16_t)start, (unsigned)(uint16_t)end) != 0)
    return -1;
  if (json_builder_append_json_string(builder, region->id) != 0) return -1;
  if (json_builder_append(builder, ",\"symbol\":") != 0) return -1;
  if (json_builder_append_json_string(builder, region->symbol) != 0) return -1;
  if (json_builder_append(builder, ",\"struct_name\":") != 0) return -1;
  if (json_builder_append_json_string(builder, region->struct_name) != 0) return -1;
  if (json_builder_appendf(builder,
        ",\"start\":%d,\"end\":%d,\"size\":%d,\"field_offset\":%d,\"field_end_offset\":%d,\"coverage\":",
        (int)(region->offset + start), (int)(region->offset + end), (int)(end - start), (int)start,
        (int)end) != 0)
    return -1;
  if (json_builder_append_json_string(builder, has_field ? "known_struct_field" : "unknown_struct_area") != 0)
    return -1;
  if (has_field) {
    const char *field_name = amiga_os_name(8U, resolved.field_id);
    const char *owner_name = amiga_os_name(7U, resolved.owner_struct_id);
    if (json_builder_append(builder, ",\"field_name\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, field_name) != 0) return -1;
    if (json_builder_appendf(builder, ",\"field_base_offset\":%d,\"field_owner_struct\":",
          (int)resolved.offset) != 0)
      return -1;
    if (json_builder_append_nullable_string(builder, owner_name) != 0) return -1;
    if (json_builder_appendf(builder, ",\"field_inherited\":%s,\"field_nested\":%s,\"field_path\":",
          resolved.inherited ? "true" : "false", resolved.nested ? "true" : "false") != 0)
      return -1;
    if (append_listing_resolved_field_path_json(builder, &resolved) != 0) return -1;
  }
  if (json_builder_append(builder, "}") != 0) return -1;
  if (io_count != NULL) ++*io_count;
  return 0;
}

static int listing_app_slot_next_known_field_offset(const ListingAppSlotTypedRegion *region, int16_t start,
    int16_t end, int16_t *out_offset) {
  int16_t cursor;
  if (out_offset != NULL) *out_offset = end;
  if (region == NULL) return 0;
  for (cursor = (int16_t)(start + 1); cursor < end; ++cursor) {
    AmigaOsResolvedStructFieldInfo resolved;
    if (amiga_os_resolve_struct_field_by_struct_id(region->struct_id, cursor, 1, &resolved)) {
      if (out_offset != NULL) *out_offset = cursor;
      return 1;
    }
  }
  return 0;
}

static int append_listing_app_slot_field_gap_segments_json(JsonBuilder *builder,
    const ListingAppSlotTypedRegion *region, int16_t start, int16_t end, int *io_emitted, size_t *io_count) {
  int16_t cursor = start;
  if (builder == NULL || region == NULL || io_emitted == NULL || start > end) return -1;
  while (cursor < end) {
    AmigaOsResolvedStructFieldInfo resolved;
    int16_t segment_end;
    if (amiga_os_resolve_struct_field_by_struct_id(region->struct_id, cursor, 1, &resolved)) {
      if (resolved.offset >= cursor && resolved.size != 0U) {
        segment_end = (int16_t)(resolved.offset + (int16_t)resolved.size);
        if (segment_end <= cursor) segment_end = (int16_t)(cursor + 1);
        if (segment_end > end) segment_end = end;
      } else {
        segment_end = (int16_t)(cursor + 1);
      }
    } else if (!listing_app_slot_next_known_field_offset(region, cursor, end, &segment_end)) {
      segment_end = end;
    }
    if (*io_emitted && json_builder_append(builder, ",") != 0) return -1;
    if (append_listing_app_slot_field_gap_json(builder, region, cursor, segment_end, io_count) != 0) return -1;
    *io_emitted = 1;
    cursor = segment_end;
  }
  return 0;
}

static size_t listing_app_slot_count_field_gap_segments(const ListingAppSlotTypedRegion *region, int16_t start,
    int16_t end) {
  int16_t cursor = start;
  size_t count = 0U;
  if (region == NULL || start > end) return 0U;
  while (cursor < end) {
    AmigaOsResolvedStructFieldInfo resolved;
    int16_t segment_end;
    if (amiga_os_resolve_struct_field_by_struct_id(region->struct_id, cursor, 1, &resolved)) {
      if (resolved.offset >= cursor && resolved.size != 0U) {
        segment_end = (int16_t)(resolved.offset + (int16_t)resolved.size);
        if (segment_end <= cursor) segment_end = (int16_t)(cursor + 1);
        if (segment_end > end) segment_end = end;
      } else {
        segment_end = (int16_t)(cursor + 1);
      }
    } else if (!listing_app_slot_next_known_field_offset(region, cursor, end, &segment_end)) {
      segment_end = end;
    }
    ++count;
    cursor = segment_end;
  }
  return count;
}

static int append_listing_app_slot_field_gaps_json(JsonBuilder *builder,
    const ListingAppSlotAnalysisBuilder *analysis, size_t *out_field_gap_count) {
  size_t region_index;
  int emitted = 0;
  size_t gap_count = 0U;
  if (out_field_gap_count != NULL) *out_field_gap_count = 0U;
  if (json_builder_append(builder, "[") != 0) return -1;
  for (region_index = 0U; region_index < analysis->region_count; ++region_index) {
    const ListingAppSlotTypedRegion *region = &analysis->regions[region_index];
    ListingAppSlotFieldRefSummary *fields;
    size_t field_count = 0U;
    int16_t intervals[128][2];
    size_t interval_count = 0U;
    int16_t cursor = 0;
    size_t field_index, interval_index;
    fields = listing_app_slot_build_field_refs(analysis, region, &field_count);
    for (field_index = 0U; field_index < field_count && interval_count < 128U; ++field_index) {
      ListingAppSlotFieldRefSummary *field = &fields[field_index];
      int16_t start = field->field_offset;
      int16_t end;
      if (field->region_address || start < 0 || start >= region->size) continue;
      end = (int16_t)(start + listing_app_slot_field_observed_size(field));
      if (end > region->size) end = region->size;
      if (end <= start) continue;
      intervals[interval_count][0] = start;
      intervals[interval_count][1] = end;
      ++interval_count;
    }
    for (interval_index = 0U; interval_index < interval_count; ++interval_index) {
      size_t other;
      for (other = interval_index + 1U; other < interval_count; ++other) {
        if (intervals[other][0] < intervals[interval_index][0]) {
          int16_t tmp_start = intervals[interval_index][0], tmp_end = intervals[interval_index][1];
          intervals[interval_index][0] = intervals[other][0];
          intervals[interval_index][1] = intervals[other][1];
          intervals[other][0] = tmp_start;
          intervals[other][1] = tmp_end;
        }
      }
    }
    for (interval_index = 0U; interval_index < interval_count; ++interval_index) {
      int16_t start = intervals[interval_index][0];
      int16_t end = intervals[interval_index][1];
      if (start > cursor) {
        if (append_listing_app_slot_field_gap_segments_json(builder, region, cursor, start, &emitted,
            &gap_count) != 0) {
          free(fields);
          return -1;
        }
      }
      if (end > cursor) cursor = end;
    }
    if (cursor < region->size && interval_count != 0U) {
      if (append_listing_app_slot_field_gap_segments_json(builder, region, cursor, region->size, &emitted,
          &gap_count) != 0) {
        free(fields);
        return -1;
      }
    }
    free(fields);
  }
  if (out_field_gap_count != NULL) *out_field_gap_count = gap_count;
  return json_builder_append(builder, "]");
}

static size_t listing_app_slot_field_gap_count(const ListingAppSlotAnalysisBuilder *analysis) {
  size_t region_index, gap_count = 0U;
  if (analysis == NULL) return 0U;
  for (region_index = 0U; region_index < analysis->region_count; ++region_index) {
    const ListingAppSlotTypedRegion *region = &analysis->regions[region_index];
    ListingAppSlotFieldRefSummary *fields;
    size_t field_count = 0U;
    int16_t intervals[128][2];
    size_t interval_count = 0U;
    int16_t cursor = 0;
    size_t field_index, interval_index;
    fields = listing_app_slot_build_field_refs(analysis, region, &field_count);
    for (field_index = 0U; field_index < field_count && interval_count < 128U; ++field_index) {
      ListingAppSlotFieldRefSummary *field = &fields[field_index];
      int16_t start = field->field_offset;
      int16_t end;
      if (field->region_address || start < 0 || start >= region->size) continue;
      end = (int16_t)(start + listing_app_slot_field_observed_size(field));
      if (end > region->size) end = region->size;
      if (end <= start) continue;
      intervals[interval_count][0] = start;
      intervals[interval_count][1] = end;
      ++interval_count;
    }
    for (interval_index = 0U; interval_index < interval_count; ++interval_index) {
      size_t other;
      for (other = interval_index + 1U; other < interval_count; ++other) {
        if (intervals[other][0] < intervals[interval_index][0]) {
          int16_t tmp_start = intervals[interval_index][0], tmp_end = intervals[interval_index][1];
          intervals[interval_index][0] = intervals[other][0];
          intervals[interval_index][1] = intervals[other][1];
          intervals[other][0] = tmp_start;
          intervals[other][1] = tmp_end;
        }
      }
    }
    for (interval_index = 0U; interval_index < interval_count; ++interval_index) {
      int16_t start = intervals[interval_index][0];
      int16_t end = intervals[interval_index][1];
      if (start > cursor) gap_count += listing_app_slot_count_field_gap_segments(region, cursor, start);
      if (end > cursor) cursor = end;
    }
    if (cursor < region->size && interval_count != 0U)
      gap_count += listing_app_slot_count_field_gap_segments(region, cursor, region->size);
    free(fields);
  }
  return gap_count;
}

static int append_listing_app_slot_suggestions_json(JsonBuilder *builder,
    const ListingAppSlotAnalysisBuilder *analysis) {
  size_t index;
  if (json_builder_append(builder, "[") != 0) return -1;
  for (index = 0U; index < analysis->region_count; ++index) {
    const ListingAppSlotTypedRegion *region = &analysis->regions[index];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"kind\":\"app_slot_region\",\"action\":\"add_target_metadata\","
          "\"confidence\":\"tool-inferred\",\"summary\":") != 0)
      return -1;
    {
      char summary[192];
      snprintf(summary, sizeof(summary), "%s at app+0x%x matches %s from platform API usage",
        region->symbol, (unsigned)(uint16_t)region->offset, region->struct_name);
      if (json_builder_append_json_string(builder, summary) != 0) return -1;
    }
    if (json_builder_appendf(builder, ",\"metadata\":{\"offset\":%d,\"size\":%d,\"symbol\":",
          (int)region->offset, (int)region->size) != 0)
      return -1;
    if (json_builder_append_json_string(builder, region->symbol) != 0) return -1;
    if (json_builder_append(builder, ",\"storage_kind\":\"struct_instance\","
          "\"semantic_type\":\"platform_api_buffer\",\"struct_name\":") != 0)
      return -1;
    if (json_builder_append_json_string(builder, region->struct_name) != 0) return -1;
    if (json_builder_append(builder, ",\"pointer_struct\":null,\"seed_origin\":\"auto_analysis\","
          "\"review_status\":\"suggested\"},\"evidence\":") != 0)
      return -1;
    if (append_listing_app_slot_region_evidence_json(builder, region) != 0) return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  return json_builder_append(builder, "]");
}

static int append_listing_app_slot_untyped_api_args_json(JsonBuilder *builder,
    const ListingAppSlotAnalysisBuilder *analysis) {
  size_t index;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (analysis == NULL) return json_builder_append(builder, "]");
  for (index = 0U; index < analysis->untyped_api_arg_count; ++index) {
    const ListingAppSlotApiArgCandidate *candidate = &analysis->untyped_api_args[index];
    const ListingAppSlotEvidence *evidence = &candidate->evidence;
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"id\":") != 0) return -1;
    if (json_builder_append_json_string(builder, candidate->id) != 0) return -1;
    if (json_builder_append(builder, ",\"symbol\":") != 0) return -1;
    if (json_builder_append_json_string(builder, candidate->symbol) != 0) return -1;
    if (json_builder_append(builder, ",\"base_symbol\":") != 0) return -1;
    if (json_builder_append_json_string(builder, candidate->base_symbol) != 0) return -1;
    if (json_builder_appendf(builder,
          ",\"displacement\":%d,\"base_displacement\":%d,\"effective_displacement\":%d,\"base_register\":",
          (int)candidate->displacement, (int)candidate->base_displacement, (int)candidate->displacement) != 0)
      return -1;
    {
      char reg_name[4];
      listing_register_name(reg_name, sizeof(reg_name), candidate->base_reg);
      if (json_builder_append_json_string(builder, reg_name) != 0) return -1;
    }
    if (json_builder_append(builder, ",\"type_name\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, candidate->type_name[0] != '\0' ? candidate->type_name : NULL) != 0)
      return -1;
    if (json_builder_append(builder, ",\"reason\":") != 0) return -1;
    if (json_builder_append_json_string(builder, candidate->reason) != 0) return -1;
    if (json_builder_appendf(builder, ",\"row_index\":%u,\"addr\":%u,\"hunk_index\":%d,\"library\":",
          (unsigned)evidence->row_index, (unsigned)evidence->addr, evidence->section_index) != 0)
      return -1;
    if (json_builder_append_json_string(builder, evidence->library) != 0) return -1;
    if (json_builder_append(builder, ",\"function\":") != 0) return -1;
    if (json_builder_append_json_string(builder, evidence->function) != 0) return -1;
    if (json_builder_append(builder, ",\"input_name\":") != 0) return -1;
    if (json_builder_append_json_string(builder, evidence->input_name) != 0) return -1;
    if (json_builder_append(builder, ",\"register\":") != 0) return -1;
    if (json_builder_append_json_string(builder, evidence->reg) != 0) return -1;
    if (json_builder_append(builder, ",\"stable_key\":") != 0) return -1;
    if (json_builder_append_json_string(builder, evidence->stable_key) != 0) return -1;
    if (json_builder_appendf(builder,
          ",\"source_row_index\":%u,\"source_flow_row_index\":%u,\"source_addr\":%u,\"source_stable_key\":",
          (unsigned)evidence->source_row_index, (unsigned)evidence->source_flow_row_index,
          (unsigned)evidence->source_addr) != 0)
      return -1;
    if (json_builder_append_json_string(builder, evidence->source_stable_key) != 0) return -1;
    if (evidence->source_via_register[0] != '\0') {
      if (json_builder_append(builder, ",\"source_via_register\":") != 0) return -1;
      if (json_builder_append_json_string(builder, evidence->source_via_register) != 0) return -1;
    }
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  return json_builder_append(builder, "]");
}

static int append_listing_app_slot_analysis_json(JsonBuilder *builder,
    const ListingAppSlotAnalysisBuilder *analysis) {
  ListingAppSlotSummary *summaries = NULL;
  ListingAppSlotInterval *intervals = NULL;
  size_t summary_count = 0U, interval_count = 0U;
  size_t gap_count = 0U, field_gap_count = 0U;
  int result = -1;
  if (analysis == NULL || !analysis->enabled) {
    return json_builder_append(builder,
      "{\"slot_count\":0,\"ref_count\":0,\"typed_region_count\":0,\"gap_count\":0,\"field_gap_count\":0,"
      "\"suggestion_count\":0,\"untyped_api_arg_count\":0,\"slots\":[],\"regions\":[],\"gaps\":[],"
      "\"field_gaps\":[],\"suggestions\":[],\"untyped_api_args\":[]}");
  }
  qsort(analysis->regions, analysis->region_count, sizeof(*analysis->regions), listing_app_slot_region_compare);
  summaries = listing_app_slot_build_summaries(analysis, &summary_count);
  intervals = listing_app_slot_build_intervals(analysis, summaries, summary_count, &interval_count);
  gap_count = listing_app_slot_gap_count(intervals, interval_count);
  field_gap_count = listing_app_slot_field_gap_count(analysis);
  if (json_builder_appendf(builder,
        "{\"slot_count\":%u,\"ref_count\":%u,\"typed_region_count\":%u,\"gap_count\":%u,"
        "\"field_gap_count\":%u,\"suggestion_count\":%u,\"untyped_api_arg_count\":%u,\"slots\":",
        (unsigned)summary_count, (unsigned)analysis->ref_count, (unsigned)analysis->region_count,
        (unsigned)gap_count, (unsigned)field_gap_count, (unsigned)analysis->region_count,
        (unsigned)analysis->untyped_api_arg_count) != 0)
    goto cleanup;
  if (append_listing_app_slot_slots_json(builder, summaries, summary_count) != 0) goto cleanup;
  if (json_builder_append(builder, ",\"regions\":") != 0) goto cleanup;
  if (append_listing_app_slot_regions_json(builder, analysis, summaries, summary_count) != 0) goto cleanup;
  if (json_builder_append(builder, ",\"gaps\":") != 0) goto cleanup;
  if (append_listing_app_slot_gaps_json(builder, intervals, interval_count, NULL) != 0) goto cleanup;
  if (json_builder_append(builder, ",\"field_gaps\":") != 0) goto cleanup;
  if (append_listing_app_slot_field_gaps_json(builder, analysis, NULL) != 0) goto cleanup;
  if (json_builder_append(builder, ",\"suggestions\":") != 0) goto cleanup;
  if (append_listing_app_slot_suggestions_json(builder, analysis) != 0) goto cleanup;
  if (json_builder_append(builder, ",\"untyped_api_args\":") != 0) goto cleanup;
  if (append_listing_app_slot_untyped_api_args_json(builder, analysis) != 0) goto cleanup;
  if (json_builder_append(builder, "}") != 0) goto cleanup;
  result = 0;

cleanup:
  free(summaries);
  free(intervals);
  return result;
}

static const M68kRuntimeViewIR *listing_runtime_view_for_storage_offset(
    const M68kSourceAnalysisIR *source_analysis, int section_index, uint32_t storage_offset,
    uint32_t *out_runtime_address) {
  const M68kSectionAnalysisIR *section;
  size_t index;
  if (out_runtime_address != NULL) *out_runtime_address = 0U;
  if (source_analysis == NULL || section_index < 0 || (size_t)section_index >= source_analysis->section_count)
    return NULL;
  section = &source_analysis->sections[section_index];
  for (index = 0U; index < section->runtime_view_count; ++index) {
    const M68kRuntimeViewIR *view = &section->runtime_views[index];
    uint32_t delta;
    if (storage_offset < view->storage_offset) continue;
    delta = storage_offset - view->storage_offset;
    if (delta >= view->size || view->runtime_address > UINT32_MAX - delta) continue;
    if (out_runtime_address != NULL) *out_runtime_address = view->runtime_address + delta;
    return view;
  }
  return NULL;
}

static int listing_stmt_has_symbol_operand_parts(const M68kStatementIR *stmt) {
  size_t operand_index;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION) return 0;
  for (operand_index = 0U; operand_index < stmt->u.instruction.operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &stmt->u.instruction.operands[operand_index];
    if (operand->symbol_ref.has_name != 0U && operand->symbol_ref.name[0] != '\0') return 1;
  }
  return 0;
}

static int listing_stmt_has_operand_metadata(const M68kStatementIR *stmt) {
  return stmt != NULL && stmt->kind == M68K_STATEMENT_INSTRUCTION && stmt->u.instruction.operand_count != 0U;
}

static int listing_stmt_has_app_slot_refs(const M68kStatementIR *stmt,
    const M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION) return 0;
  if (section_analysis != NULL) {
    for (index = 0U; index < section_analysis->app_slot_ref_count; ++index)
      if (section_analysis->app_slot_refs[index].offset == stmt->offset) return 1;
    return 0;
  }
  return listing_stmt_has_symbol_operand_parts(stmt);
}

static int listing_stmt_has_runtime_address_refs(const M68kStatementIR *stmt,
    const M68kSectionAnalysisIR *section_analysis, const char *comment) {
  size_t index;
  uint32_t comment_runtime_address = 0U;
  if (stmt == NULL ||
      (stmt->kind != M68K_STATEMENT_INSTRUCTION && stmt->kind != M68K_STATEMENT_DATA) ||
      section_analysis == NULL)
    return 0;
  if (listing_comment_runtime_pointer_address(comment, &comment_runtime_address)) {
    for (index = 0U; index < section_analysis->runtime_address_ref_count; ++index) {
      const M68kRuntimeAddressRefIR *ref = &section_analysis->runtime_address_refs[index];
      if (ref->has_runtime_address && ref->runtime_address == comment_runtime_address &&
          ref->data_class != NULL && comment != NULL && strstr(comment, ref->data_class) != NULL)
        return 1;
    }
  }
  for (index = 0U; index < section_analysis->runtime_address_ref_count; ++index)
    if (section_analysis->runtime_address_refs[index].offset == stmt->offset) return 1;
  return 0;
}

static int listing_stmt_has_code_start_refs(const M68kStatementIR *stmt,
    const M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION || section_analysis == NULL) return 0;
  for (index = 0U; index < section_analysis->code_start_ref_count; ++index)
    if (section_analysis->code_start_refs[index].offset == stmt->offset) return 1;
  return 0;
}

static int listing_stmt_has_typed_accesses(const M68kStatementIR *stmt,
    const M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION || section_analysis == NULL) return 0;
  for (index = 0U; index < section_analysis->recovered_platform_typed_access_count; ++index)
    if (section_analysis->recovered_platform_typed_accesses[index].offset == stmt->offset) return 1;
  return 0;
}

static int listing_stmt_has_unresolved_typed_accesses(const M68kStatementIR *stmt,
    const M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION || section_analysis == NULL) return 0;
  for (index = 0U; index < section_analysis->recovered_platform_unresolved_typed_access_count; ++index)
    if (section_analysis->recovered_platform_unresolved_typed_accesses[index].offset == stmt->offset) return 1;
  return 0;
}

static int listing_structured_data_item_has_json(const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && !(item->label[0] == '\0' && item->struct_name[0] == '\0' &&
    item->field_name[0] == '\0' && item->field_type[0] == '\0' && item->c_type[0] == '\0' &&
    item->pointer_struct[0] == '\0' && item->value_domain[0] == '\0' && item->constant_name[0] == '\0' &&
    item->semantic_role[0] == '\0' && !item->has_constant_value && !item->is_pointer && !item->has_target);
}

static int append_listing_row_json_parsed(JsonBuilder *builder, size_t row_index, const char *line_start,
    size_t line_length, const char *row_kind, const char *stripped, const char *opcode, const char *operand,
    const char *comment, int section_index, const M68kStatementIR *stmt,
    const M68kAnalysisPolicy *analysis_policy, const M68kSourceAnalysisIR *source_analysis,
    const char *analysis_generation) {
  char text[1200];
  char label_text[1024];
  const char *label = NULL;
  const M68kAnalysisStructuredDataItem *structured_item = NULL;
  int has_addr = 0;
  uint32_t addr = 0U;
  uint32_t end_offset = 0U;
  uint32_t byte_count = 0U;
  const M68kRuntimeViewIR *runtime_view = NULL;
  uint32_t runtime_address = 0U;
  if (line_length + 1U < sizeof(text)) {
    memcpy(text, line_start, line_length);
    text[line_length] = '\0';
  } else {
    copy_trimmed(text, sizeof(text), line_start, line_length);
  }
  if (stmt != NULL) {
    has_addr = 1;
    addr = stmt->offset;
    if (stmt->kind == M68K_STATEMENT_INSTRUCTION) byte_count = (uint32_t)stmt->u.instruction.byte_count;
    else if (stmt->kind == M68K_STATEMENT_DATA) byte_count = (uint32_t)stmt->u.data.size;
    end_offset = addr + byte_count;
    label = stmt->label_name;
    structured_item = listing_structured_data_item_at_offset(analysis_policy, section_index, addr);
    runtime_view = listing_runtime_view_for_storage_offset(source_analysis, section_index, addr, &runtime_address);
  } else if (strcmp(row_kind, "label") == 0) {
    size_t stripped_length;
    snprintf(label_text, sizeof(label_text), "%s", stripped != NULL ? stripped : "");
    stripped_length = strlen(label_text);
    if (stripped_length != 0U && label_text[stripped_length - 1U] == ':') label_text[stripped_length - 1U] = '\0';
    label = label_text;
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
  if (json_builder_append_json_string(builder, analysis_generation != NULL ? analysis_generation : "full") != 0)
    return -1;
  if (json_builder_append(builder, ",\"analysis_phase\":") != 0) return -1;
  if (json_builder_append_json_string(builder, analysis_generation != NULL ? analysis_generation : "full") != 0)
    return -1;
  if (json_builder_append(builder, ",\"section_index\":") != 0) return -1;
  if (section_index >= 0) {
    if (json_builder_appendf(builder, "%d", section_index) != 0) return -1;
  } else if (json_builder_append(builder, "null") != 0) return -1;
  if (has_addr) {
    if (json_builder_append(builder, ",\"start_offset\":") != 0) return -1;
    if (json_builder_appendf(builder, "%u", (unsigned)addr) != 0) return -1;
    if (json_builder_append(builder, ",\"end_offset\":") != 0) return -1;
    if (json_builder_appendf(builder, "%u", (unsigned)end_offset) != 0) return -1;
    if (json_builder_append(builder, ",\"storage_address\":") != 0) return -1;
    if (json_builder_appendf(builder, "%u", (unsigned)addr) != 0) return -1;
  }
  if (runtime_view != NULL) {
    if (json_builder_append(builder, ",\"runtime_address\":") != 0) return -1;
    if (json_builder_appendf(builder, "%u", (unsigned)runtime_address) != 0) return -1;
    if (json_builder_append(builder, ",\"runtime_view_id\":") != 0) return -1;
    if (json_builder_appendf(builder, "%u", (unsigned)runtime_view->runtime_view_id) != 0) return -1;
  }
  if (json_builder_append(builder, ",\"text\":") != 0) return -1;
  if (json_builder_append_json_string(builder, text) != 0) return -1;
  if (stmt != NULL && stmt->source_byte_count != 0U) {
    if (json_builder_append(builder, ",\"bytes\":") != 0) return -1;
    if (json_builder_append_char(builder, '"') != 0) return -1;
    if (json_builder_append_hex_bytes(builder, stmt->source_bytes, stmt->source_byte_count) != 0) return -1;
    if (json_builder_append_char(builder, '"') != 0) return -1;
  }
  if (has_addr) {
    if (json_builder_append(builder, ",\"addr\":") != 0) return -1;
    if (json_builder_appendf(builder, "%u", (unsigned)addr) != 0) return -1;
    if (json_builder_append(builder, ",\"entity_addr\":") != 0) return -1;
    if (json_builder_appendf(builder, "%u", (unsigned)addr) != 0) return -1;
  }
  if (label != NULL) {
    if (json_builder_append(builder, ",\"label\":") != 0) return -1;
    if (json_builder_append_json_string(builder, label) != 0) return -1;
  }
  if (opcode != NULL && opcode[0] != '\0' && strcmp(row_kind, "label") != 0 && strcmp(row_kind, "blank") != 0 &&
      strcmp(row_kind, "comment") != 0) {
    if (json_builder_append(builder, ",\"opcode_or_directive\":") != 0) return -1;
    if (json_builder_append_json_string(builder, opcode) != 0) return -1;
  }
  if (listing_statement_operation_type(stmt) != NULL) {
    if (json_builder_append(builder, ",\"operation_type\":") != 0) return -1;
    if (json_builder_append_json_string(builder, listing_statement_operation_type(stmt)) != 0) return -1;
  }
  if (operand != NULL && operand[0] != '\0') {
    if (json_builder_append(builder, ",\"operand_text\":") != 0) return -1;
    if (json_builder_append_json_string(builder, operand) != 0) return -1;
  }
  if (listing_stmt_has_symbol_operand_parts(stmt)) {
    if (json_builder_append(builder, ",\"operand_parts\":") != 0) return -1;
    if (append_listing_operand_parts_json(builder, stmt) != 0) return -1;
  }
  if (listing_stmt_has_operand_metadata(stmt)) {
    if (json_builder_append(builder, ",\"operand_accesses\":") != 0) return -1;
    if (append_listing_operand_accesses_json(builder, stmt) != 0) return -1;
    if (json_builder_append(builder, ",\"operand_registers\":") != 0) return -1;
    if (append_listing_operand_registers_json(builder, stmt) != 0) return -1;
  }
  if (comment != NULL && comment[0] != '\0') {
    if (json_builder_append(builder, ",\"comment_text\":") != 0) return -1;
    if (json_builder_append_json_string(builder, comment) != 0) return -1;
  }
  if (json_builder_append(builder, ",\"source_context\":") != 0) return -1;
  if (stmt != NULL) {
    if (append_listing_source_context(builder, row_kind, section_index) != 0) return -1;
  } else if (append_listing_source_context(builder, NULL, -1) != 0) return -1;
  {
    const M68kSectionAnalysisIR *section_analysis =
      source_analysis != NULL && section_index >= 0 && (size_t)section_index < source_analysis->section_count
        ? &source_analysis->sections[section_index]
        : NULL;
    if (listing_stmt_has_app_slot_refs(stmt, section_analysis)) {
      if (json_builder_append(builder, ",\"app_slot_refs\":") != 0) return -1;
      if (append_listing_app_slot_refs_json(builder, stmt, section_analysis) != 0) return -1;
    }
    if (listing_stmt_has_runtime_address_refs(stmt, section_analysis, comment)) {
      if (json_builder_append(builder, ",\"runtime_address_refs\":") != 0) return -1;
      if (append_listing_runtime_address_refs_json(builder, stmt, section_analysis, comment) != 0) return -1;
    }
    if (listing_stmt_has_code_start_refs(stmt, section_analysis)) {
      if (json_builder_append(builder, ",\"code_start_refs\":") != 0) return -1;
      if (append_listing_code_start_refs_json(builder, stmt, section_analysis) != 0) return -1;
    }
    if (listing_stmt_has_typed_accesses(stmt, section_analysis)) {
      if (json_builder_append(builder, ",\"typed_accesses\":") != 0) return -1;
      if (append_listing_typed_accesses_json(builder, stmt, section_analysis) != 0) return -1;
    }
    if (listing_stmt_has_unresolved_typed_accesses(stmt, section_analysis)) {
      if (json_builder_append(builder, ",\"unresolved_typed_accesses\":") != 0) return -1;
      if (append_listing_unresolved_typed_accesses_json(builder, stmt, section_analysis) != 0) return -1;
    }
  }
  if (listing_structured_data_item_has_json(structured_item)) {
    if (json_builder_append(builder, ",\"structured_data\":") != 0) return -1;
    if (append_listing_structured_data_json(builder, structured_item) != 0) return -1;
  }
  if (listing_data_class_for_structured_item(structured_item) != NULL) {
    if (json_builder_append(builder, ",\"data_class\":") != 0) return -1;
    if (json_builder_append_json_string(builder, listing_data_class_for_structured_item(structured_item)) != 0)
      return -1;
  }
  return json_builder_append(builder, "}");
}

static int append_listing_row_json(JsonBuilder *builder, size_t row_index, const char *line_start, size_t line_length,
    const char *row_kind, int section_index, const M68kStatementIR *stmt, const M68kAnalysisPolicy *analysis_policy,
    const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation) {
  char stripped[1024];
  char opcode[128];
  char operand[1024];
  char comment[512];
  split_listing_line(line_start, line_length, stripped, sizeof(stripped), opcode, sizeof(opcode), operand,
    sizeof(operand), comment, sizeof(comment));
  return append_listing_row_json_parsed(builder, row_index, line_start, line_length, row_kind, stripped, opcode,
    operand, comment, section_index, stmt, analysis_policy, source_analysis, analysis_generation);
}

typedef struct ListingSourceHeaderRow {
  const char *line_start;
  size_t line_length;
  const char *row_kind;
  int section_index;
  int group;
} ListingSourceHeaderRow;

typedef struct ListingSourceHeaderRows {
  ListingSourceHeaderRow *items;
  size_t count;
  size_t capacity;
} ListingSourceHeaderRows;

static void listing_source_header_rows_destroy(ListingSourceHeaderRows *rows) {
  if (rows == NULL) return;
  free(rows->items);
  rows->items = NULL;
  rows->count = 0U;
  rows->capacity = 0U;
}

static int listing_source_header_rows_append(ListingSourceHeaderRows *rows, const char *line_start, size_t line_length,
    const char *row_kind, int section_index, int group) {
  ListingSourceHeaderRow *new_items;
  size_t new_capacity;
  if (rows == NULL || line_start == NULL || row_kind == NULL) return -1;
  if (rows->count == rows->capacity) {
    new_capacity = rows->capacity == 0U ? 16U : rows->capacity * 2U;
    new_items = (ListingSourceHeaderRow *)realloc(rows->items, new_capacity * sizeof(*new_items));
    if (new_items == NULL) return -1;
    rows->items = new_items;
    rows->capacity = new_capacity;
  }
  rows->items[rows->count].line_start = line_start;
  rows->items[rows->count].line_length = line_length;
  rows->items[rows->count].row_kind = row_kind;
  rows->items[rows->count].section_index = section_index;
  rows->items[rows->count].group = group;
  ++rows->count;
  return 0;
}

static int listing_source_header_group(const char *row_kind, const char *stripped) {
  if (row_kind == NULL) return -1;
  if (strcmp(row_kind, "comment") == 0) return 0;
  if (stripped == NULL || stripped[0] == '\0') return -1;
  if (strcmp(row_kind, "directive") != 0) return -1;
  if (text_starts_with_ci(stripped, "COMMENT ")) return 0;
  if (text_starts_with_ci(stripped, "INCLUDE ")) return 1;
  if (text_contains_equ(stripped) || text_contains_rs_directive_token(stripped)) return 2;
  return -1;
}

static int listing_should_hoist_source_header_row(const char *row_kind, const char *stripped) {
  return listing_source_header_group(row_kind, stripped) >= 0;
}

static int listing_should_keep_source_only_body_row(const char *row_kind, const char *stripped,
    int active_section_index) {
  if (active_section_index < 0 || row_kind == NULL) return 0;
  if (strcmp(row_kind, "comment") == 0) return 1;
  return strcmp(row_kind, "directive") == 0 &&
    (text_starts_with_ci(stripped, "FPU ") || text_first_token_equals_ci(stripped, "ORG"));
}

static int append_listing_blank_row(JsonBuilder *builder, size_t *row_index, const char *analysis_generation) {
  static const char blank_line[] = "\n";
  if (builder == NULL || row_index == NULL) return -1;
  if (*row_index != 0U && json_builder_append(builder, ",") != 0) return -1;
  if (append_listing_row_json(builder, *row_index, blank_line, 1U, "blank", -1, NULL, NULL, NULL,
      analysis_generation) != 0)
    return -1;
  ++*row_index;
  return 0;
}

typedef struct BasicListingRenderPlanContext {
  JsonBuilder *builder;
  ListingAppSlotAnalysisBuilder *app_slot_analysis;
  const M68kSourceFileIR *source_file;
  const M68kAnalysisPolicy *analysis_policy;
  size_t row_index;
} BasicListingRenderPlanContext;

static const char *listing_row_kind_for_plan_row(const M68kRenderPlanRow *row) {
  if (row == NULL) return "unknown";
  if (row->kind == M68K_RENDER_PLAN_ROW_INCLUDE) return "directive";
  if (row->kind == M68K_RENDER_PLAN_ROW_RSSET) return "directive";
  if (row->kind == M68K_RENDER_PLAN_ROW_RS_FIELD) return "directive";
  if (row->kind == M68K_RENDER_PLAN_ROW_EQUATE) return "directive";
  if (row->kind == M68K_RENDER_PLAN_ROW_SECTION) return "directive";
  if (row->kind == M68K_RENDER_PLAN_ROW_ORG) return "directive";
  if (row->kind == M68K_RENDER_PLAN_ROW_LABEL) return "label";
  if (row->kind == M68K_RENDER_PLAN_ROW_INSTRUCTION) return "instruction";
  if (row->kind == M68K_RENDER_PLAN_ROW_DATA) return "data";
  if (row->kind == M68K_RENDER_PLAN_ROW_RESERVE) return "data";
  if (row->kind == M68K_RENDER_PLAN_ROW_BLANK) return "blank";
  if (row->kind == M68K_RENDER_PLAN_ROW_PLATFORM_DIRECTIVE) return "directive";
  return NULL;
}

static int listing_section_index_for_plan_row(const M68kRenderPlanRow *row) {
  if (row == NULL || row->source_section_index == M68K_RENDER_PLAN_NO_SECTION) return -1;
  if (row->source_section_index > (uint32_t)INT32_MAX) return -1;
  return (int)row->source_section_index;
}

static const M68kStatementIR *listing_statement_for_plan_row(const M68kSourceFileIR *source_file,
    const M68kRenderPlanRow *row) {
  const M68kSectionIR *section;
  size_t statement_index;
  if (source_file == NULL || row == NULL || !row->has_statement ||
      row->source_section_index >= source_file->section_count)
    goto source_range_lookup;
  section = &source_file->sections[row->source_section_index];
  if (row->statement_index >= section->statement_count) return NULL;
  return &section->statements[row->statement_index];

source_range_lookup:
  if (source_file == NULL || row == NULL || !row->has_source_range ||
      row->source_section_index >= source_file->section_count)
    return NULL;
  section = &source_file->sections[row->source_section_index];
  for (statement_index = 0U; statement_index < section->statement_count; ++statement_index) {
    const M68kStatementIR *stmt = &section->statements[statement_index];
    if (stmt->offset != row->source_offset) continue;
    if ((row->kind == M68K_RENDER_PLAN_ROW_LABEL && stmt->kind == M68K_STATEMENT_LABEL) ||
        (row->kind == M68K_RENDER_PLAN_ROW_INSTRUCTION && stmt->kind == M68K_STATEMENT_INSTRUCTION) ||
        ((row->kind == M68K_RENDER_PLAN_ROW_DATA || row->kind == M68K_RENDER_PLAN_ROW_RESERVE) &&
          (stmt->kind == M68K_STATEMENT_DATA || stmt->kind == M68K_STATEMENT_RESERVE))) {
      return stmt;
    }
  }
  return NULL;
}

static int append_basic_listing_render_plan_line(const M68kRenderPlanRow *row, uint32_t subline, uint32_t line,
    const char *line_start, size_t line_length, void *user) {
  BasicListingRenderPlanContext *context = (BasicListingRenderPlanContext *)user;
  const char *row_kind = listing_row_kind_for_plan_row(row);
  const M68kStatementIR *stmt;
  int section_index = listing_section_index_for_plan_row(row);
  (void)subline;
  (void)line;
  if (context == NULL || context->builder == NULL) return -1;
  if (row_kind == NULL) row_kind = "directive";
  stmt = listing_statement_for_plan_row(context->source_file, row);
  if (context->row_index != 0U && json_builder_append(context->builder, ",") != 0) return -1;
  if (append_listing_row_json(context->builder, context->row_index, line_start, line_length, row_kind,
      section_index, stmt, context->analysis_policy, NULL, "basic") != 0)
    return -1;
  if (listing_app_slot_analysis_observe_row(context->app_slot_analysis, context->row_index, row_kind,
      section_index, stmt, NULL) != 0)
    return -1;
  ++context->row_index;
  return 0;
}

int source_file_basic_listing_rows_to_json(const M68kSourceFileIR *source_file,
    const M68kAnalysisPolicy *analysis_policy, char **out_json, M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  ListingAppSlotAnalysisBuilder app_slot_analysis = {0};
  M68kRenderPlan render_plan;
  BasicListingRenderPlanContext context;
  memset(&render_plan, 0, sizeof(render_plan));
  memset(&context, 0, sizeof(context));
  if (source_file == NULL || out_json == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, "bad arguments");
    return -1;
  }
  if (m68k_render_plan_build_source_file_body(source_file, NULL, &render_plan, diagnostics) != 0) goto oom;
  if (listing_app_slot_analysis_init(&app_slot_analysis, source_file, NULL) != 0) goto oom;
  if (json_builder_create(&builder) != 0) goto oom;
  if (json_builder_append(&builder, "{\"rows\":[") != 0) goto oom;
  context.builder = &builder;
  context.app_slot_analysis = &app_slot_analysis;
  context.source_file = source_file;
  context.analysis_policy = analysis_policy;
  if (m68k_render_plan_visit_row_lines(&render_plan, 0U, render_plan.row_count,
      append_basic_listing_render_plan_line, &context) != 0)
    goto oom;
  if (json_builder_append(&builder, "],\"app_slot_analysis\":") != 0) goto oom;
  if (append_listing_app_slot_analysis_json(&builder, &app_slot_analysis) != 0) goto oom;
  if (json_builder_append(&builder, "}") != 0) goto oom;
  *out_json = json_builder_build(&builder);
  if (*out_json == NULL) goto oom;
  json_builder_destroy(&builder);
  listing_app_slot_analysis_destroy(&app_slot_analysis);
  m68k_render_plan_destroy(&render_plan);
  return 0;

oom:
  json_builder_destroy(&builder);
  listing_app_slot_analysis_destroy(&app_slot_analysis);
  m68k_render_plan_destroy(&render_plan);
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
  return -1;
}

static int append_listing_source_header_rows(JsonBuilder *builder, const ListingSourceHeaderRows *header_rows,
    size_t *row_index, const M68kAnalysisPolicy *analysis_policy, const M68kSourceAnalysisIR *source_analysis,
    const char *analysis_generation) {
  size_t index;
  int group;
  int emitted_any = 0;
  if (builder == NULL || header_rows == NULL || row_index == NULL) return -1;
  for (group = 0; group <= 2; ++group) {
    int emitted_group = 0;
    for (index = 0U; index < header_rows->count; ++index) {
      const ListingSourceHeaderRow *row = &header_rows->items[index];
      if (row->group != group) continue;
      if (emitted_any && !emitted_group) {
        if (append_listing_blank_row(builder, row_index, analysis_generation) != 0) return -1;
      }
      if (*row_index != 0U && json_builder_append(builder, ",") != 0) return -1;
      if (append_listing_row_json(builder, *row_index, row->line_start, row->line_length, row->row_kind,
            row->section_index, NULL, analysis_policy, source_analysis, analysis_generation) != 0)
        return -1;
      ++*row_index;
      emitted_group = 1;
      emitted_any = 1;
    }
  }
  if (emitted_any && append_listing_blank_row(builder, row_index, analysis_generation) != 0) return -1;
  return 0;
}

typedef struct ListingRenderPlanHeaderContext {
  ListingSourceHeaderRows *header_rows;
  int stopped;
} ListingRenderPlanHeaderContext;

static int collect_listing_source_header_plan_line(const M68kRenderPlanRow *row, uint32_t subline, uint32_t line,
    const char *line_start, size_t line_length, void *user) {
  ListingRenderPlanHeaderContext *context = (ListingRenderPlanHeaderContext *)user;
  char stripped[1024];
  char opcode[128];
  char operand[1024];
  char comment[512];
  const char *row_kind;
  (void)row;
  (void)subline;
  (void)line;
  if (context == NULL || context->header_rows == NULL || context->stopped) return 0;
  split_listing_line(line_start, line_length, stripped, sizeof(stripped), opcode, sizeof(opcode), operand,
    sizeof(operand), comment, sizeof(comment));
  row_kind = listing_row_kind_for_line(stripped);
  if (strcmp(row_kind, "blank") == 0 && comment[0] != '\0') row_kind = "comment";
  if (strcmp(row_kind, "directive") == 0 && text_starts_with_ci(stripped, "SECTION ")) {
    context->stopped = 1;
    return 0;
  }
  if (listing_should_hoist_source_header_row(row_kind, stripped)) {
    int group = listing_source_header_group(row_kind, stripped);
    if (listing_source_header_rows_append(context->header_rows, line_start, line_length, row_kind, -1, group) != 0)
      return -1;
  }
  return 0;
}

static int collect_listing_source_header_rows_from_plan(const M68kRenderPlan *render_plan,
    ListingSourceHeaderRows *header_rows) {
  ListingRenderPlanHeaderContext context;
  size_t row_index;
  memset(&context, 0, sizeof(context));
  if (render_plan == NULL || header_rows == NULL) return -1;
  context.header_rows = header_rows;
  for (row_index = 0U; row_index < render_plan->row_count && !context.stopped; ++row_index) {
    const M68kRenderPlanRow *row = &render_plan->rows[row_index];
    const char *cursor = row->text;
    uint32_t subline = 0U;
    if (cursor == NULL) continue;
    while (*cursor != '\0' && !context.stopped) {
      const char *line_start = cursor;
      size_t line_length;
      while (*cursor != '\0' && *cursor != '\n') ++cursor;
      if (*cursor == '\n') ++cursor;
      line_length = (size_t)(cursor - line_start);
      if (collect_listing_source_header_plan_line(row, subline, row->start_line + subline, line_start,
          line_length, &context) != 0)
        return -1;
      ++subline;
    }
  }
  return 0;
}

typedef struct ListingRenderPlanJsonContext {
  JsonBuilder *builder;
  ListingSourceHeaderRows *header_rows;
  ListingAppSlotAnalysisBuilder *app_slot_analysis;
  const M68kSourceFileIR *source_file;
  const M68kAnalysisPolicy *analysis_policy;
  const M68kSourceAnalysisIR *source_analysis;
  const char *analysis_generation;
  size_t row_index;
  int active_section_index;
  int preamble_emitted;
  int include_source_only_rows;
  int use_rendered_line_count;
  size_t statement_index;
  size_t data_lines_left;
} ListingRenderPlanJsonContext;

static int append_full_listing_render_plan_line(const M68kRenderPlanRow *row, uint32_t subline, uint32_t line,
    const char *line_start, size_t line_length, void *user) {
  ListingRenderPlanJsonContext *context = (ListingRenderPlanJsonContext *)user;
  int is_section_directive = 0;
  int section_index = -1;
  char stripped[1024];
  char opcode[128];
  char operand[1024];
  char comment[512];
  const char *row_kind;
  const M68kStatementIR *stmt = NULL;
  (void)subline;
  (void)line;
  if (context == NULL || context->builder == NULL) return -1;
  split_listing_line(line_start, line_length, stripped, sizeof(stripped), opcode, sizeof(opcode), operand,
    sizeof(operand), comment, sizeof(comment));
  row_kind = listing_row_kind_for_plan_row(row);
  if (row_kind == NULL) {
    row_kind = listing_row_kind_for_line(stripped);
    if (strcmp(row_kind, "blank") == 0 && comment[0] != '\0') row_kind = "comment";
  }
  is_section_directive = strcmp(row_kind, "directive") == 0 && text_starts_with_ci(stripped, "SECTION ");
  section_index = listing_section_index_for_plan_row(row);
  if (is_section_directive) {
    if (section_index >= 0) context->active_section_index = section_index;
    else ++context->active_section_index;
    section_index = context->active_section_index;
    context->statement_index = 0U;
    context->data_lines_left = 0U;
  } else if (row != NULL && (row->has_statement || row->has_source_range)) {
    stmt = listing_statement_for_plan_row(context->source_file, row);
    if (section_index >= 0) context->active_section_index = section_index;
  } else if (context->active_section_index >= 0) {
    stmt = listing_statement_for_line(context->source_file, context->analysis_policy,
      (size_t)context->active_section_index, &context->statement_index, &context->data_lines_left, row_kind,
      context->use_rendered_line_count, strcmp(row_kind, "data") == 0 && strchr(stripped, '-') != NULL);
    section_index = context->active_section_index;
  }
  if (!context->include_source_only_rows && !context->preamble_emitted && is_section_directive) {
    if (append_listing_source_header_rows(context->builder, context->header_rows, &context->row_index,
          context->analysis_policy, context->source_analysis, context->analysis_generation) != 0)
      return -1;
    context->preamble_emitted = 1;
  }
  if (!context->include_source_only_rows && stmt == NULL && !is_section_directive &&
      !listing_should_keep_source_only_body_row(row_kind, stripped, context->active_section_index)) {
    return 0;
  }
  if (context->row_index != 0U && json_builder_append(context->builder, ",") != 0) return -1;
  if (append_listing_row_json_parsed(context->builder, context->row_index, line_start, line_length, row_kind,
        stripped, opcode, operand, comment, section_index, stmt, context->analysis_policy,
        context->source_analysis, context->analysis_generation) != 0)
    return -1;
  if (listing_app_slot_analysis_observe_row(context->app_slot_analysis, context->row_index, row_kind,
      section_index, stmt, context->source_analysis) != 0)
    return -1;
  ++context->row_index;
  return 0;
}

int source_file_listing_rows_from_render_plan_to_json(const M68kSourceFileIR *source_file,
    const M68kRenderPlan *render_plan, const M68kAnalysisPolicy *analysis_policy,
    const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation, int include_source_only_rows,
    char **out_json, M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  ListingSourceHeaderRows header_rows = {0};
  ListingAppSlotAnalysisBuilder app_slot_analysis = {0};
  ListingRenderPlanJsonContext context;
  memset(&context, 0, sizeof(context));
  if (source_file == NULL || render_plan == NULL || out_json == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, "bad arguments");
    return -1;
  }
  if (!include_source_only_rows) {
    if (collect_listing_source_header_rows_from_plan(render_plan, &header_rows) != 0) goto oom;
  }
  if (listing_app_slot_analysis_init(&app_slot_analysis, source_file, source_analysis) != 0) goto oom;
  if (json_builder_create(&builder) != 0) goto oom;
  if (json_builder_append(&builder, "{\"rows\":[") != 0) goto oom;
  context.builder = &builder;
  context.header_rows = &header_rows;
  context.app_slot_analysis = &app_slot_analysis;
  context.source_file = source_file;
  context.analysis_policy = analysis_policy;
  context.source_analysis = source_analysis;
  context.analysis_generation = analysis_generation;
  context.active_section_index = -1;
  context.include_source_only_rows = include_source_only_rows;
  context.use_rendered_line_count = analysis_generation != NULL && strcmp(analysis_generation, "basic") == 0;
  if (m68k_render_plan_visit_row_lines(render_plan, 0U, render_plan->row_count,
      append_full_listing_render_plan_line, &context) != 0)
    goto oom;
  if (json_builder_append(&builder, "],\"app_slot_analysis\":") != 0) goto oom;
  if (append_listing_app_slot_analysis_json(&builder, &app_slot_analysis) != 0) goto oom;
  if (json_builder_append(&builder, "}") != 0) goto oom;
  *out_json = json_builder_build(&builder);
  if (*out_json == NULL) goto oom;
  json_builder_destroy(&builder);
  listing_app_slot_analysis_destroy(&app_slot_analysis);
  listing_source_header_rows_destroy(&header_rows);
  return 0;

oom:
  json_builder_destroy(&builder);
  listing_app_slot_analysis_destroy(&app_slot_analysis);
  listing_source_header_rows_destroy(&header_rows);
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
  return -1;
}
