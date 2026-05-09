/* Internal JSON/inspection implementation for platform_file_lib. */
#include "platform_file_internal.h"
#include "m68k_fact_ir.h"
#include "m68k_render_plan.h"
#include "m68k_source_text_util.h"
#include "generated/amiga_os_runtime.h"
#include "generated/m68k_cpu_runtime.h"
#include "util_arena.h"

static int json_builder_append_nullable_string(JsonBuilder *builder, const char *text);
static void amiga_struct_catalog_info(uint16_t struct_id, const char **out_source, int16_t *out_size);
static const char *app_slot_access_kind_name(uint8_t access_kind);
static const char *unresolved_typed_access_classification_name(uint8_t classification);
static const char *type_provenance_kind_name(uint8_t kind);
static const char *runtime_view_materialization_reason_name(uint8_t reason);
static const char *runtime_view_relationship_kind_name(uint8_t kind);
static int append_runtime_view_relationship_json(JsonBuilder *builder,
  const M68kRuntimeViewRelationshipIR *relationship);
static const char *absolute_memory_owner_kind_name(uint8_t owner_kind);
static const char *analysis_conflict_state_name(uint8_t conflict_state);
static void absolute_memory_ref_owner_symbols(const M68kAbsoluteMemoryRefIR *ref,
  const char **out_symbol, const char **out_base_symbol);
static const char *listing_operand_access_name(uint8_t access_kind);
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

static const char *runtime_view_materialization_reason_name(uint8_t reason) {
  switch (reason) {
  case M68K_RUNTIME_VIEW_MATERIALIZED_FULL_SOURCE_POLICY_LOAD_VIEW:
    return "full_source_policy_load_view";
  case M68K_RUNTIME_VIEW_MATERIALIZED_POLICY_ENTRY_POINT:
    return "policy_entry_point";
  case M68K_RUNTIME_VIEW_MATERIALIZED_RUNTIME_REF_TARGET:
    return "runtime_ref_target";
  case M68K_RUNTIME_VIEW_MATERIALIZED_DISCOVERED_COPY_ENTRY:
    return "discovered_copy_entry";
  case M68K_RUNTIME_VIEW_SUPPRESSED_CONFLICTING_DISCOVERED_COPY:
    return "conflicting_discovered_copy";
  case M68K_RUNTIME_VIEW_SUPPRESSED_CROSSED_BY_STORAGE_XREF:
    return "crossed_by_storage_xref";
  case M68K_RUNTIME_VIEW_SUPPRESSED_EXIT_TO_LARGER_RUNTIME_RANGE:
    return "exit_to_larger_runtime_range";
  case M68K_RUNTIME_VIEW_SUPPRESSED_REDUNDANT_CONTAINED_VIEW:
    return "redundant_contained_view";
  case M68K_RUNTIME_VIEW_SUPPRESSED_STORAGE_CONTINUATION:
    return "storage_continuation";
  case M68K_RUNTIME_VIEW_SUPPRESSED_NO_MATERIALIZING_EVIDENCE:
    return "no_materializing_evidence";
  case M68K_RUNTIME_VIEW_SUPPRESSED_OVERLAID_BY_RUNTIME_COPY:
    return "overlaid_by_runtime_copy";
  case M68K_RUNTIME_VIEW_MATERIALIZATION_REASON_NONE:
  default:
    return "none";
  }
}

static const char *runtime_view_relationship_kind_name(uint8_t kind) {
  switch (kind) {
  case M68K_RUNTIME_VIEW_RELATIONSHIP_EXITS_TO_LARGER_RUNTIME_RANGE:
    return "exits_to_larger_runtime_range";
  case M68K_RUNTIME_VIEW_RELATIONSHIP_CONTAINED_BY_RUNTIME_RANGE:
    return "contained_by_runtime_range";
  case M68K_RUNTIME_VIEW_RELATIONSHIP_OVERLAID_BY_RUNTIME_COPY:
    return "overlaid_by_runtime_copy";
  case M68K_RUNTIME_VIEW_RELATIONSHIP_NONE:
  default:
    return "none";
  }
}

static int append_runtime_view_relationship_json(JsonBuilder *builder,
    const M68kRuntimeViewRelationshipIR *relationship) {
  if (builder == NULL || relationship == NULL ||
      relationship->kind == M68K_RUNTIME_VIEW_RELATIONSHIP_NONE) {
    return 0;
  }
  return json_builder_appendf(builder,
    ",\"relationship_kind\":%u,\"relationship_kind_name\":\"%s\","
    "\"related_runtime_view_id\":%u,\"related_storage_offset\":%u,"
    "\"related_runtime_address\":%u,\"related_runtime_size\":%u",
    (unsigned)relationship->kind, runtime_view_relationship_kind_name(relationship->kind),
    (unsigned)relationship->runtime_view_id, (unsigned)relationship->storage_offset,
    (unsigned)relationship->runtime_address, (unsigned)relationship->size);
}

static const char *absolute_memory_owner_kind_name(uint8_t owner_kind) {
  switch (owner_kind) {
  case M68K_ABSOLUTE_MEMORY_OWNER_EXECBASE_LITERAL:
    return "execbase_literal";
  case M68K_ABSOLUTE_MEMORY_OWNER_CPU_VECTOR:
    return "cpu_vector";
  case M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER:
    return "hardware_register";
  case M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER_RANGE:
    return "hardware_register_range";
  case M68K_ABSOLUTE_MEMORY_OWNER_RUNTIME_RANGE:
    return "runtime_range";
  case M68K_ABSOLUTE_MEMORY_OWNER_SECTION_STORAGE:
    return "section_storage";
  case M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY:
    return "absolute_memory";
  case M68K_ABSOLUTE_MEMORY_OWNER_UNKNOWN:
  default:
    return "unknown";
  }
}

static const char *analysis_conflict_state_name(uint8_t conflict_state) {
  switch (conflict_state) {
  case M68K_ANALYSIS_CONFLICT_STATE_CLEAN:
    return "clean";
  case M68K_ANALYSIS_CONFLICT_STATE_CODE_OVERLAP:
    return "code_overlap";
  case M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED:
    return "unresolved";
  case M68K_ANALYSIS_CONFLICT_STATE_CONFLICTED:
    return "conflicted";
  default:
    return "unknown";
  }
}

static void absolute_memory_ref_owner_symbols(const M68kAbsoluteMemoryRefIR *ref,
    const char **out_symbol, const char **out_base_symbol) {
  const char *symbol = NULL;
  const char *base_symbol = NULL;
  if (ref != NULL) {
    if (ref->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_EXECBASE_LITERAL) {
      symbol = "ExecBase";
    } else if (ref->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_CPU_VECTOR) {
      const M68kCpuExceptionVectorInfo *vector = m68k_cpu_find_exception_vector_by_address(ref->address);
      symbol = vector != NULL ? vector->symbol_name : NULL;
    } else if (ref->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER) {
      const AmigaOsHardwareRegisterInfo *hardware_register =
        amiga_os_find_hardware_register_by_cpu_address(ref->address);
      symbol = hardware_register != NULL ? hardware_register->symbol_name : NULL;
      base_symbol = hardware_register != NULL ? hardware_register->base_symbol : NULL;
    } else if (ref->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER_RANGE) {
      const AmigaOsHardwareRegisterRangeInfo *hardware_range =
        amiga_os_find_hardware_register_range_by_cpu_address(ref->address);
      symbol = hardware_range != NULL ? hardware_range->symbol_name : NULL;
      base_symbol = hardware_range != NULL ? hardware_range->base_symbol : NULL;
    }
  }
  if (out_symbol != NULL) *out_symbol = symbol;
  if (out_base_symbol != NULL) *out_base_symbol = base_symbol;
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
  if (json_builder_append(builder, ",\"source\":") != 0) return -1;
  if (json_builder_append_json_string(builder, "parsed NDK") != 0) return -1;
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
  if (json_builder_append(builder,
        "{\"name\":\"return\",\"regs\":[\"D0\"],\"type\":null,\"o_struct\":null,\"source\":\"parsed NDK\",") != 0)
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

static int append_recovered_platform_call_json(JsonBuilder *builder, const M68kRecoveredPlatformCallIR *call) {
  const char *resolved_lvo_symbol_name = NULL;
  const AmigaOsLibraryVectorInfo *amiga_vector;
  const char *library_name;
  if (builder == NULL || call == NULL) return -1;
  amiga_vector = resolve_amiga_call_vector_for_json(call, &resolved_lvo_symbol_name);
  library_name = resolve_amiga_call_library_name_for_json(call, amiga_vector);
  if (json_builder_appendf(builder, "{\"offset\":%u,\"kind\":%u,\"symbol_name\":",
        (unsigned)call->offset, (unsigned)call->kind) != 0)
    return -1;
  if (json_builder_append_nullable_string(builder,
        m68k_platform_name_ref_resolve_text_or_fallback(&call->symbol_ref, call->symbol_name)) != 0)
    return -1;
  if (json_builder_appendf(builder, ",\"note_kind\":%u,\"note_base_name\":",
        (unsigned)call->note_kind) != 0)
    return -1;
  if (json_builder_append_nullable_string(builder,
        m68k_platform_name_ref_resolve_text_or_fallback(&call->note_base_ref, call->note_base_name)) != 0)
    return -1;
  if (json_builder_append(builder, ",\"note_symbol_name\":") != 0)
    return -1;
  if (json_builder_append_nullable_string(builder,
        m68k_platform_name_ref_resolve_text_or_fallback(&call->note_symbol_ref, call->note_symbol_name)) != 0)
    return -1;
  if (json_builder_appendf(builder,
        ",\"note_reg\":%u,\"note_disp\":%d,\"note_field_disp\":%d,\"note_stack_cleanup_known\":%u,"
        "\"note_stack_cleanup_bytes\":%u,\"note_return_kind\":%u,\"available_since\":",
        (unsigned)call->note_reg, (int)call->note_disp, (int)call->note_field_disp,
        (unsigned)call->note_stack_cleanup_known, (unsigned)call->note_stack_cleanup_bytes,
        (unsigned)call->note_return_kind) != 0)
    return -1;
  if (json_builder_append_nullable_string(builder, call->available_since) != 0)
    return -1;
  if (json_builder_append(builder, ",\"fd_version\":") != 0)
    return -1;
  if (json_builder_append_nullable_string(builder, call->fd_version) != 0)
    return -1;
  if (json_builder_append(builder, ",\"device_name\":") != 0)
    return -1;
  if (json_builder_append_nullable_string(builder, call->device_name) != 0)
    return -1;
  if (json_builder_append(builder, ",\"library_name\":") != 0)
    return -1;
  if (json_builder_append_nullable_string(builder, library_name) != 0)
    return -1;
  if (json_builder_append(builder, ",\"function_name\":") != 0)
    return -1;
  if (json_builder_append_nullable_string(builder,
        amiga_vector != NULL ? amiga_os_name(3U, amiga_vector->function_id) : NULL) != 0)
    return -1;
  if (json_builder_append(builder, ",\"lvo_symbol_name\":") != 0)
    return -1;
  if (json_builder_append_nullable_string(builder, resolved_lvo_symbol_name) != 0)
    return -1;
  if (json_builder_append(builder, ",\"inputs\":") != 0)
    return -1;
  if (append_amiga_call_inputs_json(builder, amiga_vector) != 0)
    return -1;
  if (json_builder_append(builder, ",\"outputs\":") != 0)
    return -1;
  if (amiga_vector != NULL) {
    if (append_amiga_call_outputs_json(builder, amiga_vector) != 0)
      return -1;
  } else if (call->note_symbol_ref.platform_kind == M68K_PLATFORM_BACKEND_ATARI_ST) {
    if (append_atari_call_outputs_json(builder, call) != 0)
      return -1;
  } else if (json_builder_append(builder, "[]") != 0) {
    return -1;
  }
  return json_builder_append(builder, "}");
}

static const char *listing_api_call_function_name(const M68kRecoveredPlatformCallIR *call,
    const AmigaOsLibraryVectorInfo *amiga_vector) {
  const char *symbol;
  if (amiga_vector != NULL) return amiga_os_name(3U, amiga_vector->function_id);
  symbol = m68k_platform_name_ref_resolve_text_or_fallback(&call->symbol_ref, call->symbol_name);
  if (symbol == NULL || symbol[0] == '\0')
    symbol = m68k_platform_name_ref_resolve_text_or_fallback(&call->note_symbol_ref, call->note_symbol_name);
  if (symbol != NULL && strncmp(symbol, "_LVO", 4U) == 0) symbol += 4U;
  return symbol;
}

static int append_listing_api_call_json(JsonBuilder *builder, const M68kRecoveredPlatformCallIR *call) {
  const char *resolved_lvo_symbol_name = NULL;
  const AmigaOsLibraryVectorInfo *amiga_vector;
  const char *library_name;
  const char *function_name;
  if (builder == NULL || call == NULL) return -1;
  amiga_vector = resolve_amiga_call_vector_for_json(call, &resolved_lvo_symbol_name);
  (void)resolved_lvo_symbol_name;
  library_name = resolve_amiga_call_library_name_for_json(call, amiga_vector);
  if (library_name == NULL || library_name[0] == '\0')
    library_name = m68k_platform_name_ref_resolve_text_or_fallback(&call->note_base_ref, call->note_base_name);
  if (library_name == NULL || library_name[0] == '\0') library_name = "unknown";
  function_name = listing_api_call_function_name(call, amiga_vector);
  if (function_name == NULL || function_name[0] == '\0') return -1;
  if (json_builder_append(builder, "{\"library\":") != 0) return -1;
  if (json_builder_append_json_string(builder, library_name) != 0) return -1;
  if (json_builder_append(builder, ",\"function\":") != 0) return -1;
  if (json_builder_append_json_string(builder, function_name) != 0) return -1;
  if (json_builder_appendf(builder, ",\"note_kind\":%u,\"call_kind\":%u,\"symbol_name\":",
        (unsigned)call->note_kind, (unsigned)call->kind) != 0)
    return -1;
  if (json_builder_append_nullable_string(builder,
        m68k_platform_name_ref_resolve_text_or_fallback(&call->symbol_ref, call->symbol_name)) != 0)
    return -1;
  if (json_builder_append(builder, ",\"note_symbol_name\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder,
        m68k_platform_name_ref_resolve_text_or_fallback(&call->note_symbol_ref, call->note_symbol_name)) != 0)
    return -1;
  if (json_builder_append(builder, ",\"inputs\":") != 0) return -1;
  if (append_amiga_call_inputs_json(builder, amiga_vector) != 0) return -1;
  if (json_builder_append(builder, ",\"outputs\":") != 0) return -1;
  if (amiga_vector != NULL) {
    if (append_amiga_call_outputs_json(builder, amiga_vector) != 0) return -1;
  } else if (call->note_symbol_ref.platform_kind == M68K_PLATFORM_BACKEND_ATARI_ST) {
    if (append_atari_call_outputs_json(builder, call) != 0) return -1;
  } else if (json_builder_append(builder, "[]") != 0) {
    return -1;
  }
  return json_builder_append(builder, "}");
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

static const char *recovered_indirect_table_bounds_status_name(uint8_t status) {
  if (status == M68K_RECOVERED_INDIRECT_TABLE_BOUNDS_REJECTED_INSUFFICIENT_ENTRIES)
    return "rejected_insufficient_entries";
  return "none";
}

static const char *orphan_code_signal_reason_name(uint8_t reason) {
  if (reason == M68K_ORPHAN_CODE_SIGNAL_TERMINAL_DECODE) return "terminal_decode";
  return "unknown";
}

static const char *orphan_code_signal_status_name(uint8_t status) {
  if (status == M68K_ORPHAN_CODE_SIGNAL_UNRESOLVED) return "unresolved";
  if (status == M68K_ORPHAN_CODE_SIGNAL_REJECTED) return "rejected";
  if (status == M68K_ORPHAN_CODE_SIGNAL_SUPPRESSED) return "suppressed";
  if (status == M68K_ORPHAN_CODE_SIGNAL_LINKED) return "linked";
  if (status == M68K_ORPHAN_CODE_SIGNAL_PROMOTED) return "promoted";
  return "unknown";
}

static const char *orphan_code_signal_context_name(uint8_t context) {
  if (context == M68K_ORPHAN_CODE_SIGNAL_CONTEXT_ACCEPTED_CODE_BOUNDARY) return "accepted_code_boundary";
  if (context == M68K_ORPHAN_CODE_SIGNAL_CONTEXT_RENDERABLE_LABEL) return "renderable_label";
  if (context == M68K_ORPHAN_CODE_SIGNAL_CONTEXT_RUNTIME_VIEW) return "runtime_view";
  return "unknown";
}

static const char *orphan_code_signal_inbound_name(uint8_t inbound) {
  if (inbound == M68K_ORPHAN_CODE_SIGNAL_INBOUND_UNKNOWN) return "unknown";
  if (inbound == M68K_ORPHAN_CODE_SIGNAL_INBOUND_JUMP_TABLE) return "jump_table";
  if (inbound == M68K_ORPHAN_CODE_SIGNAL_INBOUND_CALLBACK) return "callback";
  if (inbound == M68K_ORPHAN_CODE_SIGNAL_INBOUND_VECTOR) return "vector";
  if (inbound == M68K_ORPHAN_CODE_SIGNAL_INBOUND_RUNTIME_COPY) return "runtime_copy";
  if (inbound == M68K_ORPHAN_CODE_SIGNAL_INBOUND_API) return "api";
  if (inbound == M68K_ORPHAN_CODE_SIGNAL_INBOUND_METADATA) return "metadata";
  if (inbound == M68K_ORPHAN_CODE_SIGNAL_INBOUND_POLICY_SEED) return "policy_seed";
  return "unknown";
}

static const char *base_layout_field_source_kind_name(uint8_t source_kind) {
  if (source_kind == M68K_BASE_LAYOUT_FIELD_SOURCE_APP_SLOT_ACCESS) return "app_slot_access";
  if (source_kind == M68K_BASE_LAYOUT_FIELD_SOURCE_POLICY_RSSET_REGION) return "policy_rsset_region";
  return "none";
}

static const char *sim_flow_kind_name(uint8_t flow_kind) {
  if (flow_kind == M68K_SIM_FLOW_NONE) return "none";
  if (flow_kind == M68K_SIM_FLOW_SEQUENTIAL) return "sequential";
  if (flow_kind == M68K_SIM_FLOW_BRANCH) return "branch";
  if (flow_kind == M68K_SIM_FLOW_JUMP) return "jump";
  if (flow_kind == M68K_SIM_FLOW_CALL) return "call";
  if (flow_kind == M68K_SIM_FLOW_RETURN) return "return";
  if (flow_kind == M68K_SIM_FLOW_TRAP) return "trap";
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
    case M68K_FACT_CODE_START_REASON_RUNTIME_VIEW_ENTRY: return "runtime_view_entry";
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

static uint32_t structured_data_item_role_flags_json(const M68kAnalysisStructuredDataItem *item) {
  if (item == NULL) return 0U;
  return item->semantic_role_flags;
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
    if (json_builder_append_nullable_string(builder,
        m68k_analysis_structured_data_role_name_for_flags(structured_data_item_role_flags_json(item))) != 0) {
      return -1;
    }
    if (json_builder_appendf(builder, ",\"semantic_role_flags\":%u",
        (unsigned)structured_data_item_role_flags_json(item)) != 0) {
      return -1;
    }
    {
      const char *source_pattern = m68k_analysis_structured_data_source_pattern_name(item->source_pattern_id);
      if (json_builder_appendf(builder, ",\"source_pattern_id\":%u,\"source_pattern\":",
            (unsigned)item->source_pattern_id) != 0)
        return -1;
      if (json_builder_append_nullable_string(builder, source_pattern) != 0) {
        return -1;
      }
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

static uint32_t structured_data_item_entry_size(const M68kAnalysisStructuredDataItem *item) {
  if (item == NULL) return 0U;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_BYTES) return 1U;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS) return 2U;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS) return 4U;
  return 0U;
}

static uint8_t structured_data_item_table_kind_id(const M68kAnalysisStructuredDataItem *item) {
  uint32_t role_flags;
  if (item == NULL) return M68K_ANALYSIS_TABLE_KIND_UNKNOWN;
  role_flags = structured_data_item_role_flags_json(item);
  if ((role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE) != 0U)
    return M68K_ANALYSIS_TABLE_KIND_POINTER;
  if ((role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE) != 0U) {
    if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS && item->has_target)
      return M68K_ANALYSIS_TABLE_KIND_RELATIVE_CODE_DISPATCH;
    if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS)
      return M68K_ANALYSIS_TABLE_KIND_ABSOLUTE_CODE_DISPATCH;
    return M68K_ANALYSIS_TABLE_KIND_SCALAR;
  }
  return M68K_ANALYSIS_TABLE_KIND_UNKNOWN;
}

static const char *recovered_indirect_table_candidate_source_pattern(uint8_t shape) {
  if (shape == M68K_RECOVERED_INDIRECT_SHAPE_PCINDEX_BRIEF ||
      shape == M68K_RECOVERED_INDIRECT_SHAPE_PCINDEX_FULL ||
      shape == M68K_RECOVERED_INDIRECT_SHAPE_PCINDEX_MEMIND) {
    return "pc_indexed_indirect";
  }
  if (shape == M68K_RECOVERED_INDIRECT_SHAPE_INDEX_BRIEF ||
      shape == M68K_RECOVERED_INDIRECT_SHAPE_INDEX_FULL ||
      shape == M68K_RECOVERED_INDIRECT_SHAPE_INDEX_MEMIND) {
    return "indexed_indirect";
  }
  return "indirect";
}

static int recovered_indirect_site_is_unresolved_table_candidate(const M68kRecoveredIndirectSiteIR *site) {
  if (site == NULL) return 0;
  return site->status != M68K_RECOVERED_INDIRECT_STATUS_JUMP_TABLE &&
    site->status != M68K_RECOVERED_INDIRECT_STATUS_RESOLVED_RUNTIME &&
    site->status != M68K_RECOVERED_INDIRECT_STATUS_RUNTIME &&
    site->status != M68K_RECOVERED_INDIRECT_STATUS_EXTERNAL;
}

static size_t source_analysis_table_record_count(const M68kAnalysisPolicy *policy) {
  uint16_t index;
  size_t count = 0U;
  if (policy == NULL) return 0U;
  for (index = 0U; index < policy->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    if (structured_data_item_table_kind_id(&policy->structured_data_items[index]) !=
        M68K_ANALYSIS_TABLE_KIND_UNKNOWN) {
      ++count;
    }
  }
  return count;
}

static size_t source_analysis_table_candidate_record_count(const M68kSourceAnalysisIR *source_analysis) {
  size_t section_index;
  size_t count = 0U;
  if (source_analysis == NULL) return 0U;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t site_index;
    for (site_index = 0U; site_index < section->recovered_indirect_site_count; ++site_index) {
      if (recovered_indirect_site_is_unresolved_table_candidate(&section->recovered_indirect_sites[site_index]))
        ++count;
    }
  }
  return count;
}

static int source_analysis_range_overlaps_accepted_code(const M68kSourceAnalysisIR *source_analysis,
    const M68kAnalysisStructuredDataItem *item) {
  uint32_t cursor;
  const M68kSectionAnalysisIR *section;
  if (source_analysis == NULL || item == NULL || !item->has_section_index ||
      item->section_index >= source_analysis->section_count || item->size == 0U) {
    return 0;
  }
  section = &source_analysis->sections[item->section_index];
  if (section->certain_code_byte == NULL || item->offset >= section->certain_code_size) return 0;
  for (cursor = 0U; cursor < item->size && cursor < section->certain_code_size - item->offset; ++cursor) {
    if (section->certain_code_byte[item->offset + cursor] != 0U) return 1;
  }
  return 0;
}

static int append_source_analysis_table_candidate_records_json(JsonBuilder *builder,
    const M68kSourceAnalysisIR *source_analysis) {
  size_t section_index;
  size_t emitted = 0U;
  if (builder == NULL || source_analysis == NULL) return -1;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t site_index;
    for (site_index = 0U; site_index < section->recovered_indirect_site_count; ++site_index) {
      const M68kRecoveredIndirectSiteIR *site = &section->recovered_indirect_sites[site_index];
      const char *source_pattern;
      if (!recovered_indirect_site_is_unresolved_table_candidate(site)) continue;
      source_pattern = recovered_indirect_table_candidate_source_pattern(site->shape);
      if (emitted++ != 0U && json_builder_append(builder, ",") != 0) return -1;
      if (json_builder_appendf(builder,
          "{\"section_index\":%u,\"offset\":%u,\"source_offset\":%u,\"source_size\":%u,"
          "\"operand_index\":%u,\"flow_kind\":%u,\"flow\":",
          (unsigned)section->section_index, (unsigned)site->offset, (unsigned)site->offset,
          (unsigned)site->source_size, (unsigned)site->operand_index, (unsigned)site->flow_kind) != 0)
        return -1;
      if (json_builder_append_json_string(builder, recovered_indirect_flow_name(site->flow_kind)) != 0)
        return -1;
      if (json_builder_appendf(builder, ",\"shape_id\":%u,\"shape\":", (unsigned)site->shape) != 0)
        return -1;
      if (json_builder_append_json_string(builder, recovered_indirect_shape_name(site->shape)) != 0)
        return -1;
      if (json_builder_appendf(builder, ",\"status_id\":%u,\"status\":", (unsigned)site->status) != 0)
        return -1;
      if (json_builder_append_json_string(builder, recovered_indirect_status_name(site->status)) != 0)
        return -1;
      if (json_builder_append(builder, ",\"source_pattern\":") != 0) return -1;
      if (json_builder_append_json_string(builder, source_pattern) != 0) return -1;
      if (json_builder_append(builder, ",\"target\":") != 0) return -1;
      if (site->has_target != 0U) {
        if (json_builder_appendf(builder, "%u", (unsigned)site->target) != 0) return -1;
      } else if (json_builder_append(builder, "null") != 0) return -1;
      if (json_builder_append(builder, ",\"target_count\":") != 0) return -1;
      if (site->has_target_count != 0U) {
        if (json_builder_appendf(builder, "%u", (unsigned)site->target_count) != 0) return -1;
      } else if (json_builder_append(builder, "null") != 0) return -1;
      if (json_builder_append(builder, ",\"table_offset\":") != 0) return -1;
      if (site->has_table_bounds != 0U) {
        if (json_builder_appendf(builder, "%u", (unsigned)site->table_offset) != 0) return -1;
      } else if (json_builder_append(builder, "null") != 0) return -1;
      if (json_builder_append(builder, ",\"table_size\":") != 0) return -1;
      if (site->has_table_bounds != 0U) {
        if (json_builder_appendf(builder, "%u", (unsigned)site->table_size) != 0) return -1;
      } else if (json_builder_append(builder, "null") != 0) return -1;
      if (json_builder_append(builder, ",\"table_entry_size\":") != 0) return -1;
      if (site->has_table_bounds != 0U) {
        if (json_builder_appendf(builder, "%u", (unsigned)site->table_entry_size) != 0) return -1;
      } else if (json_builder_append(builder, "null") != 0) return -1;
      if (json_builder_append(builder, ",\"table_entry_count\":") != 0) return -1;
      if (site->has_table_bounds != 0U) {
        if (json_builder_appendf(builder, "%u", (unsigned)site->table_entry_count) != 0) return -1;
      } else if (json_builder_append(builder, "null") != 0) return -1;
      if (json_builder_appendf(builder, ",\"table_bounds_status_id\":%u,\"table_bounds_status\":",
          (unsigned)site->table_bounds_status) != 0)
        return -1;
      if (json_builder_append_json_string(builder,
          recovered_indirect_table_bounds_status_name(site->table_bounds_status)) != 0) {
        return -1;
      }
      if (json_builder_append(builder, ",\"detail\":") != 0) return -1;
      if (json_builder_append_nullable_string(builder, site->detail) != 0) return -1;
      if (json_builder_appendf(builder,
          ",\"confidence\":\"diagnostic\",\"conflict_state_id\":%u,\"conflict_state\":\"%s\"}",
          (unsigned)M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED,
          analysis_conflict_state_name(M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED)) != 0)
        return -1;
    }
  }
  return 0;
}

static int append_source_analysis_table_records_json(JsonBuilder *builder,
    const M68kSourceAnalysisIR *source_analysis) {
  uint16_t index;
  size_t emitted = 0U;
  const M68kAnalysisPolicy *policy;
  if (builder == NULL || source_analysis == NULL) return -1;
  policy = &source_analysis->policy;
  for (index = 0U; index < policy->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    uint32_t role_flags = structured_data_item_role_flags_json(item);
    uint8_t table_kind_id = structured_data_item_table_kind_id(item);
    uint8_t base_expression_id = item->has_target ? M68K_ANALYSIS_TABLE_BASE_EXPRESSION_TARGET_LABEL :
      M68K_ANALYSIS_TABLE_BASE_EXPRESSION_TABLE_LABEL;
    const char *table_kind = m68k_analysis_table_kind_name(table_kind_id);
    const char *base_expression = m68k_analysis_table_base_expression_name(base_expression_id);
    const char *role_name = m68k_analysis_structured_data_role_name_for_flags(role_flags);
    int code_overlap = source_analysis_range_overlaps_accepted_code(source_analysis, item);
    uint32_t entry_size = structured_data_item_entry_size(item);
    uint32_t entry_count = entry_size != 0U ? item->size / entry_size : 0U;
    if (table_kind == NULL || base_expression == NULL || role_name == NULL) continue;
    if (emitted++ != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"section_index\":") != 0) return -1;
    if (item->has_section_index) {
      if (json_builder_appendf(builder, "%u", (unsigned)item->section_index) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) return -1;
    if (json_builder_appendf(builder,
        ",\"offset\":%u,\"size\":%u,\"entry_size\":%u,\"entry_count\":%u",
        (unsigned)item->offset, (unsigned)item->size, (unsigned)entry_size, (unsigned)entry_count) != 0)
      return -1;
    if (json_builder_appendf(builder, ",\"role_flags\":%u,\"role\":", (unsigned)role_flags) != 0) return -1;
    if (json_builder_append_json_string(builder, role_name) != 0) return -1;
    if (json_builder_appendf(builder, ",\"table_kind_id\":%u,\"table_kind\":", (unsigned)table_kind_id) != 0)
      return -1;
    if (json_builder_append_json_string(builder, table_kind) != 0) return -1;
    {
      const char *source_pattern = m68k_analysis_structured_data_source_pattern_name(item->source_pattern_id);
      if (json_builder_appendf(builder, ",\"source_pattern_id\":%u,\"source_pattern\":",
            (unsigned)item->source_pattern_id) != 0)
        return -1;
      if (json_builder_append_nullable_string(builder, source_pattern) != 0) {
        return -1;
      }
    }
    if (json_builder_appendf(builder, ",\"base_expression_id\":%u,\"base_expression\":",
          (unsigned)base_expression_id) != 0)
      return -1;
    if (json_builder_append_json_string(builder, base_expression) != 0)
      return -1;
    if (json_builder_append(builder, ",\"target_section\":") != 0) return -1;
    if (item->has_target) {
      if (json_builder_appendf(builder, "%u", (unsigned)item->target_section) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) return -1;
    if (json_builder_append(builder, ",\"target_offset\":") != 0) return -1;
    if (item->has_target) {
      if (json_builder_appendf(builder, "%u", (unsigned)item->target_offset) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) return -1;
    if (json_builder_append(builder, ",\"consumer_section\":") != 0) return -1;
    if (item->has_consumer) {
      if (json_builder_appendf(builder, "%u", (unsigned)item->consumer_section) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) return -1;
    if (json_builder_append(builder, ",\"consumer_offset\":") != 0) return -1;
    if (item->has_consumer) {
      if (json_builder_appendf(builder, "%u", (unsigned)item->consumer_offset) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) return -1;
    {
      uint8_t conflict_state = code_overlap ? M68K_ANALYSIS_CONFLICT_STATE_CODE_OVERLAP :
        M68K_ANALYSIS_CONFLICT_STATE_CLEAN;
      if (json_builder_appendf(builder,
          ",\"confidence\":\"tool_inferred\",\"conflicted\":%s,\"conflict_state_id\":%u,\"conflict_state\":\"%s\"}",
          code_overlap ? "true" : "false", (unsigned)conflict_state,
          analysis_conflict_state_name(conflict_state)) != 0)
        return -1;
    }
  }
  return 0;
}

static int platform_effect_is_storage_kind(uint8_t kind);

static int source_analysis_base_layout_field_same_layout(const M68kBaseLayoutFieldIR *left,
    const M68kBaseLayoutFieldIR *right) {
  const char *left_layout;
  const char *right_layout;
  const char *left_base;
  const char *right_base;
  const char *left_sizeof;
  const char *right_sizeof;
  if (left == NULL || right == NULL) return 0;
  if (left->layout_kind != right->layout_kind) return 0;
  left_layout = left->layout_name != NULL ? left->layout_name : "";
  right_layout = right->layout_name != NULL ? right->layout_name : "";
  left_base = left->base_symbol != NULL ? left->base_symbol : "";
  right_base = right->base_symbol != NULL ? right->base_symbol : "";
  left_sizeof = left->sizeof_symbol != NULL ? left->sizeof_symbol : "";
  right_sizeof = right->sizeof_symbol != NULL ? right->sizeof_symbol : "";
  return strcmp(left_layout, right_layout) == 0 && strcmp(left_base, right_base) == 0 &&
    strcmp(left_sizeof, right_sizeof) == 0;
}

static size_t source_analysis_base_layout_record_count(const M68kSourceAnalysisIR *source_analysis) {
  size_t index;
  size_t count = 0U;
  if (source_analysis == NULL) return 0U;
  for (index = 0U; index < source_analysis->base_layout_field_count; ++index) {
    size_t probe;
    int seen = 0;
    for (probe = 0U; probe < index; ++probe) {
      if (source_analysis_base_layout_field_same_layout(&source_analysis->base_layout_fields[probe],
          &source_analysis->base_layout_fields[index])) {
        seen = 1;
        break;
      }
    }
    if (!seen) ++count;
  }
  return count;
}

static size_t source_analysis_memory_layout_record_count(const M68kSourceAnalysisIR *source_analysis) {
  size_t section_index;
  size_t count = 0U;
  if (source_analysis == NULL) return 0U;
  count += source_analysis_base_layout_record_count(source_analysis);
  count += source_analysis->base_layout_field_count;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t ref_index;
    count += section->recovered_platform_typed_access_count;
    count += section->recovered_platform_unresolved_typed_access_count;
    count += section->runtime_view_count;
    count += section->absolute_memory_ref_count;
    for (ref_index = 0U; ref_index < section->recovered_platform_effect_count; ++ref_index) {
      if (platform_effect_is_storage_kind(section->recovered_platform_effects[ref_index].kind))
        ++count;
    }
    for (ref_index = 0U; ref_index < section->runtime_address_ref_count; ++ref_index) {
      const M68kRuntimeAddressRefIR *ref = &section->runtime_address_refs[ref_index];
      if (ref->has_runtime_address || ref->has_target || ref->data_class_flags != 0U) {
        ++count;
      }
    }
  }
  return count;
}

enum {
  MEMORY_LAYOUT_RANGE_SPACE_BASE_RELATIVE = 1,
  MEMORY_LAYOUT_RANGE_SPACE_RUNTIME_ABSOLUTE = 2,
  MEMORY_LAYOUT_RANGE_SPACE_ABSOLUTE = 3,
  MEMORY_LAYOUT_RANGE_SPACE_SECTION_RELATIVE = 4
};

static const char *memory_layout_range_space_name(uint8_t range_space_kind) {
  switch (range_space_kind) {
  case MEMORY_LAYOUT_RANGE_SPACE_BASE_RELATIVE: return "base_relative";
  case MEMORY_LAYOUT_RANGE_SPACE_RUNTIME_ABSOLUTE: return "runtime_absolute";
  case MEMORY_LAYOUT_RANGE_SPACE_ABSOLUTE: return "absolute";
  case MEMORY_LAYOUT_RANGE_SPACE_SECTION_RELATIVE: return "section_relative";
  default: return "unknown";
  }
}

static int append_memory_layout_range_json(JsonBuilder *builder, uint8_t range_space_kind, int64_t start,
    uint32_t size) {
  int64_t end = start + (int64_t)size;
  if (builder == NULL || range_space_kind == 0U) return -1;
  return json_builder_appendf(builder,
    ",\"range_space_kind\":%u,\"range_space\":\"%s\",\"range_start\":%lld,\"range_size\":%u,\"range_end\":%lld",
    (unsigned)range_space_kind, memory_layout_range_space_name(range_space_kind), (long long)start,
    (unsigned)size, (long long)end);
}

static const char *platform_effect_kind_name(uint8_t kind) {
  switch (kind) {
  case M68K_PLATFORM_EFFECT_SET_BASE_REG: return "set_base_reg";
  case M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT: return "write_base_slot";
  case M68K_PLATFORM_EFFECT_SET_CODE_PTR_REG: return "set_code_ptr_reg";
  case M68K_PLATFORM_EFFECT_SET_TYPED_REG: return "set_typed_reg";
  case M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT: return "write_typed_slot";
  case M68K_PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT: return "write_global_base_slot";
  case M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT: return "write_typed_global_slot";
  default: return "unknown";
  }
}

static int platform_effect_is_storage_kind(uint8_t kind) {
  switch (kind) {
  case M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT:
  case M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT:
  case M68K_PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT:
  case M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT:
    return 1;
  default:
    return 0;
  }
}

static const char *platform_storage_effect_memory_kind(uint8_t kind) {
  switch (kind) {
  case M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT: return "base_slot";
  case M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT: return "typed_slot";
  case M68K_PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT: return "global_base_slot";
  case M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT: return "typed_global_slot";
  default: return "unknown";
  }
}

static int platform_effect_has_storage_range(const M68kRecoveredPlatformEffectIR *effect,
    uint8_t *out_range_space_kind, int64_t *out_range_start, uint32_t *out_range_size) {
  if (out_range_space_kind != NULL) *out_range_space_kind = 0U;
  if (out_range_start != NULL) *out_range_start = 0;
  if (out_range_size != NULL) *out_range_size = 0U;
  if (effect == NULL || !platform_effect_is_storage_kind(effect->kind)) return 0;
  if (effect->kind == M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT ||
      effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT) {
    if (effect->displacement == INT16_MIN) return 0;
    if (out_range_space_kind != NULL) *out_range_space_kind = MEMORY_LAYOUT_RANGE_SPACE_BASE_RELATIVE;
    if (out_range_start != NULL) *out_range_start = (int64_t)effect->displacement;
    if (out_range_size != NULL) *out_range_size = 4U;
    return 1;
  }
  if (effect->target_section_index == SIZE_MAX || effect->target_offset == UINT32_MAX) return 0;
  if (out_range_space_kind != NULL) *out_range_space_kind = MEMORY_LAYOUT_RANGE_SPACE_SECTION_RELATIVE;
  if (out_range_start != NULL) *out_range_start = (int64_t)effect->target_offset;
  if (out_range_size != NULL) *out_range_size = 4U;
  return 1;
}

static int append_source_analysis_memory_layout_records_json(JsonBuilder *builder,
    const M68kSourceAnalysisIR *source_analysis) {
  size_t field_index;
  size_t section_index;
  size_t emitted = 0U;
  if (builder == NULL || source_analysis == NULL) return -1;
  for (field_index = 0U; field_index < source_analysis->base_layout_field_count; ++field_index) {
    const M68kBaseLayoutFieldIR *first = &source_analysis->base_layout_fields[field_index];
    uint32_t range_start = first->offset;
    uint32_t range_end = first->offset + first->size;
    uint32_t field_count = 0U;
    uint8_t conflicted = 0U;
    uint8_t conflict_state = M68K_ANALYSIS_CONFLICT_STATE_CLEAN;
    size_t probe;
    int seen = 0;
    if (UINT32_MAX - first->offset < first->size) continue;
    for (probe = 0U; probe < field_index; ++probe) {
      if (source_analysis_base_layout_field_same_layout(&source_analysis->base_layout_fields[probe], first)) {
        seen = 1;
        break;
      }
    }
    if (seen) continue;
    for (probe = field_index; probe < source_analysis->base_layout_field_count; ++probe) {
      const M68kBaseLayoutFieldIR *field = &source_analysis->base_layout_fields[probe];
      uint32_t field_end;
      if (!source_analysis_base_layout_field_same_layout(first, field)) continue;
      if (UINT32_MAX - field->offset < field->size) continue;
      field_end = field->offset + field->size;
      if (field->offset < range_start) range_start = field->offset;
      if (field_end > range_end) range_end = field_end;
      if (field->conflicted) {
        conflicted = 1U;
        conflict_state = M68K_ANALYSIS_CONFLICT_STATE_CONFLICTED;
      }
      ++field_count;
    }
    if (range_end <= range_start || field_count == 0U) continue;
    if (emitted++ != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_appendf(builder,
        "{\"record_kind_id\":%u,\"record_kind\":\"base_layout\",\"memory_kind\":\"base_layout\","
        "\"layout_kind\":%u,\"layout_name\":",
        (unsigned)M68K_MEMORY_LAYOUT_RECORD_BASE_LAYOUT, (unsigned)first->layout_kind) != 0) {
      return -1;
    }
    if (json_builder_append_nullable_string(builder, first->layout_name) != 0) return -1;
    if (json_builder_append(builder, ",\"base_symbol\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, first->base_symbol) != 0) return -1;
    if (json_builder_append(builder, ",\"sizeof_symbol\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, first->sizeof_symbol) != 0) return -1;
    if (json_builder_appendf(builder, ",\"field_count\":%u", (unsigned)field_count) != 0) return -1;
    if (append_memory_layout_range_json(builder, MEMORY_LAYOUT_RANGE_SPACE_BASE_RELATIVE,
        (int64_t)range_start, range_end - range_start) != 0) return -1;
    if (json_builder_appendf(builder,
        ",\"confidence\":%u,\"conflicted\":%s,\"conflict_state_id\":%u,\"conflict_state\":\"%s\"}",
        (unsigned)M68K_FACT_CONFIDENCE_TOOL_INFERRED, conflicted ? "true" : "false",
        (unsigned)conflict_state, analysis_conflict_state_name(conflict_state)) != 0)
      return -1;
  }
  for (field_index = 0U; field_index < source_analysis->base_layout_field_count; ++field_index) {
    const M68kBaseLayoutFieldIR *field = &source_analysis->base_layout_fields[field_index];
    const char *memory_kind = field->alias ? "base_layout_alias" : "base_layout_field";
    const char *owner_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&field->owner_struct_ref,
      field->owner_struct_name);
    if (emitted++ != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_appendf(builder,
        "{\"record_kind_id\":%u,\"record_kind\":\"base_layout_field\",\"memory_kind\":\"%s\","
        "\"layout_kind\":%u,\"layout_name\":",
        (unsigned)M68K_MEMORY_LAYOUT_RECORD_BASE_LAYOUT_FIELD, memory_kind, (unsigned)field->layout_kind) != 0)
      return -1;
    if (json_builder_append_nullable_string(builder, field->layout_name) != 0) return -1;
    if (json_builder_append(builder, ",\"base_symbol\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, field->base_symbol) != 0) return -1;
    if (json_builder_append(builder, ",\"symbol\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, field->symbol) != 0) return -1;
    if (json_builder_append(builder, ",\"owner_struct_name\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, owner_struct_name) != 0) return -1;
    if (json_builder_append(builder, ",\"root_struct_name\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, owner_struct_name) != 0) return -1;
    if (json_builder_append(builder, ",\"section_index\":") != 0) return -1;
    if (field->has_source) {
      if (json_builder_appendf(builder, "%u", (unsigned)field->source_section_index) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) return -1;
    if (json_builder_append(builder, ",\"source_offset\":") != 0) return -1;
    if (field->has_source) {
      if (json_builder_appendf(builder, "%u", (unsigned)field->source_offset) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) return -1;
    if (json_builder_appendf(builder,
        ",\"field_offset\":%u,\"field_size\":%u",
        (unsigned)field->offset, (unsigned)field->size) != 0) return -1;
    if (json_builder_appendf(builder, ",\"alias\":%s", field->alias ? "true" : "false") != 0)
      return -1;
    if (append_memory_layout_range_json(builder, MEMORY_LAYOUT_RANGE_SPACE_BASE_RELATIVE,
        (int64_t)field->offset, field->size) != 0) return -1;
    {
      uint8_t conflict_state = field->conflicted ? M68K_ANALYSIS_CONFLICT_STATE_CONFLICTED :
        M68K_ANALYSIS_CONFLICT_STATE_CLEAN;
      if (json_builder_appendf(builder,
          ",\"confidence\":%u,\"conflicted\":%s,\"conflict_state_id\":%u,\"conflict_state\":\"%s\"}",
          (unsigned)field->confidence, field->conflicted ? "true" : "false",
          (unsigned)conflict_state, analysis_conflict_state_name(conflict_state)) != 0)
        return -1;
    }
  }
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t typed_access_index;
    size_t unresolved_typed_access_index;
    size_t effect_index;
    size_t view_index;
    size_t ref_index;
    size_t absolute_ref_index;
    for (effect_index = 0U; effect_index < section->recovered_platform_effect_count; ++effect_index) {
      const M68kRecoveredPlatformEffectIR *effect = &section->recovered_platform_effects[effect_index];
      const char *memory_kind;
      const char *base_name = NULL;
      const char *symbol_name = NULL;
      const char *type_name = NULL;
      uint8_t range_space_kind = 0U;
      int64_t range_start = 0;
      uint32_t range_size = 0U;
      if (!platform_effect_is_storage_kind(effect->kind)) continue;
      memory_kind = platform_storage_effect_memory_kind(effect->kind);
      if (effect->kind == M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT ||
          effect->kind == M68K_PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT) {
        base_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.named_base.base_ref,
          effect->payload.named_base.base_name);
      } else {
        symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.symbol_ref,
          effect->payload.typed.symbol_name);
        type_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.type_ref,
          effect->payload.typed.type_name);
        base_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.context_ref,
          effect->payload.typed.context_name);
      }
      if (emitted++ != 0U && json_builder_append(builder, ",") != 0) return -1;
      if (json_builder_appendf(builder,
          "{\"record_kind_id\":%u,\"record_kind\":\"platform_storage_effect\",\"memory_kind\":",
          (unsigned)M68K_MEMORY_LAYOUT_RECORD_PLATFORM_STORAGE_EFFECT) != 0) return -1;
      if (json_builder_append_json_string(builder, memory_kind) != 0) return -1;
      if (json_builder_appendf(builder,
          ",\"section_index\":%u,\"source_offset\":%u,\"effect_kind\":%u,\"effect_kind_name\":",
          (unsigned)section->section_index, (unsigned)effect->offset, (unsigned)effect->kind) != 0)
        return -1;
      if (json_builder_append_json_string(builder, platform_effect_kind_name(effect->kind)) != 0) return -1;
      if (json_builder_appendf(builder, ",\"displacement\":%d,\"field_disp\":%d,\"base_name\":",
          (int)effect->displacement, (int)effect->field_disp) != 0) return -1;
      if (json_builder_append_nullable_string(builder, base_name) != 0) return -1;
      if (json_builder_append(builder, ",\"symbol_name\":") != 0) return -1;
      if (json_builder_append_nullable_string(builder, symbol_name) != 0) return -1;
      if (json_builder_append(builder, ",\"type_name\":") != 0) return -1;
      if (json_builder_append_nullable_string(builder, type_name) != 0) return -1;
      if (json_builder_append(builder, ",\"target_section_index\":") != 0) return -1;
      if (effect->target_section_index != SIZE_MAX) {
        if (json_builder_appendf(builder, "%u", (unsigned)effect->target_section_index) != 0) return -1;
      } else if (json_builder_append(builder, "null") != 0) return -1;
      if (json_builder_append(builder, ",\"target_offset\":") != 0) return -1;
      if (effect->target_offset != UINT32_MAX) {
        if (json_builder_appendf(builder, "%u", (unsigned)effect->target_offset) != 0) return -1;
      } else if (json_builder_append(builder, "null") != 0) return -1;
      if (platform_effect_has_storage_range(effect, &range_space_kind, &range_start, &range_size) &&
          append_memory_layout_range_json(builder, range_space_kind, range_start, range_size) != 0)
        return -1;
      if (json_builder_append(builder, "}") != 0) return -1;
    }
    for (typed_access_index = 0U; typed_access_index < section->recovered_platform_typed_access_count;
        ++typed_access_index) {
      const M68kRecoveredPlatformTypedAccessIR *access =
        &section->recovered_platform_typed_accesses[typed_access_index];
      const char *root_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref,
        access->root_struct_name);
      const char *owner_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->owner_struct_ref,
        access->owner_struct_name);
      const char *field_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->field_ref,
        access->field_name);
      if (emitted++ != 0U && json_builder_append(builder, ",") != 0) return -1;
      if (json_builder_appendf(builder,
          "{\"record_kind_id\":%u,\"record_kind\":\"platform_typed_access\",\"memory_kind\":\"platform_struct_field\","
          "\"section_index\":%u,\"source_offset\":%u,\"operand_index\":%u,\"base_register\":\"A%u\","
          "\"displacement\":%d,\"field_offset\":%d,\"struct_size\":%u,\"field_size\":%u,"
          "\"root_struct_name\":",
          (unsigned)M68K_MEMORY_LAYOUT_RECORD_PLATFORM_TYPED_ACCESS,
          (unsigned)section->section_index, (unsigned)access->offset, (unsigned)access->operand_index,
          (unsigned)access->base_reg, (int)access->displacement, (int)access->field_offset,
          (unsigned)access->struct_size, (unsigned)access->field_size) != 0) {
        return -1;
      }
      if (json_builder_append_nullable_string(builder, root_struct_name) != 0) return -1;
      if (json_builder_append(builder, ",\"owner_struct_name\":") != 0) return -1;
      if (json_builder_append_nullable_string(builder, owner_struct_name) != 0) return -1;
      if (json_builder_append(builder, ",\"field_name\":") != 0) return -1;
      if (json_builder_append_nullable_string(builder, field_name) != 0) return -1;
      if (json_builder_append(builder, ",\"field_expr\":") != 0) return -1;
      if (json_builder_append_json_string(builder, access->field_expr != NULL ? access->field_expr : "") != 0)
        return -1;
      if (json_builder_append(builder, ",\"type_provenance_kind\":") != 0) return -1;
      if (json_builder_append_json_string(builder, type_provenance_kind_name(access->type_provenance_kind)) != 0)
        return -1;
      if (append_memory_layout_range_json(builder, MEMORY_LAYOUT_RANGE_SPACE_BASE_RELATIVE,
          (int64_t)access->displacement, access->field_size) != 0) return -1;
      if (json_builder_append(builder, "}") != 0) return -1;
    }
    for (unresolved_typed_access_index = 0U;
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
      if (emitted++ != 0U && json_builder_append(builder, ",") != 0) return -1;
      if (json_builder_appendf(builder,
          "{\"record_kind_id\":%u,\"record_kind\":\"platform_unresolved_typed_access\","
          "\"memory_kind\":\"platform_struct_unresolved\",\"section_index\":%u,\"source_offset\":%u,"
          "\"operand_index\":%u,\"base_register\":\"A%u\",\"displacement\":%d,\"struct_size\":%u,"
          "\"classification_id\":%u,\"classification\":",
          (unsigned)M68K_MEMORY_LAYOUT_RECORD_PLATFORM_UNRESOLVED_TYPED_ACCESS,
          (unsigned)section->section_index, (unsigned)access->offset, (unsigned)access->operand_index,
          (unsigned)access->base_reg, (int)access->displacement, (unsigned)access->struct_size,
          (unsigned)access->classification) != 0) {
        return -1;
      }
      if (json_builder_append_json_string(builder,
          unresolved_typed_access_classification_name(access->classification)) != 0) return -1;
      if (json_builder_append(builder, ",\"root_struct_name\":") != 0) return -1;
      if (json_builder_append_nullable_string(builder, root_struct_name) != 0) return -1;
      if (json_builder_append(builder, ",\"container_struct_name\":") != 0) return -1;
      if (json_builder_append_nullable_string(builder, container_struct_name) != 0) return -1;
      if (json_builder_append(builder, ",\"container_field_expr\":") != 0) return -1;
      if (json_builder_append_nullable_string(builder, access->container_field_expr) != 0) return -1;
      if (json_builder_append(builder, ",\"refined_struct_name\":") != 0) return -1;
      if (json_builder_append_nullable_string(builder, refined_struct_name) != 0) return -1;
      if (json_builder_append(builder, ",\"type_provenance_kind\":") != 0) return -1;
      if (json_builder_append_json_string(builder, type_provenance_kind_name(access->type_provenance_kind)) != 0)
        return -1;
      if (append_memory_layout_range_json(builder, MEMORY_LAYOUT_RANGE_SPACE_BASE_RELATIVE,
          (int64_t)access->displacement, access->struct_size) != 0) return -1;
      if (json_builder_append(builder, "}") != 0) return -1;
    }
    for (view_index = 0U; view_index < section->runtime_view_count; ++view_index) {
      const M68kRuntimeViewIR *view = &section->runtime_views[view_index];
      const char *memory_kind = view->materialized ? "runtime_code" : "runtime_view_candidate";
      if (emitted++ != 0U && json_builder_append(builder, ",") != 0) return -1;
      if (json_builder_appendf(builder,
          "{\"record_kind_id\":%u,\"record_kind\":\"runtime_view\",\"memory_kind\":\"%s\",\"section_index\":%u,"
          "\"source_offset\":%u,\"source_size\":%u,\"runtime_address\":%u,\"runtime_size\":%u,"
          "\"runtime_view_id\":%u,\"view_kind\":%u,\"confidence\":%u,\"materialized\":%s,"
          "\"materialization_reason\":%u,\"materialization_reason_name\":\"%s\"",
          (unsigned)M68K_MEMORY_LAYOUT_RECORD_RUNTIME_VIEW,
          memory_kind, (unsigned)section->section_index, (unsigned)view->storage_offset,
          (unsigned)view->size, (unsigned)view->runtime_address, (unsigned)view->size,
          (unsigned)view->runtime_view_id, (unsigned)view->kind, (unsigned)view->confidence,
          view->materialized ? "true" : "false", (unsigned)view->materialization_reason,
          runtime_view_materialization_reason_name(view->materialization_reason)) != 0) {
        return -1;
      }
      if (append_memory_layout_range_json(builder, MEMORY_LAYOUT_RANGE_SPACE_RUNTIME_ABSOLUTE,
          (int64_t)view->runtime_address, view->size) != 0) return -1;
      if (append_runtime_view_relationship_json(builder, &view->relationship) != 0) return -1;
      if (json_builder_append(builder, "}") != 0) return -1;
    }
    for (ref_index = 0U; ref_index < section->runtime_address_ref_count; ++ref_index) {
      const M68kRuntimeAddressRefIR *ref = &section->runtime_address_refs[ref_index];
      const char *data_class = m68k_analysis_structured_data_role_name_for_flags(ref->data_class_flags);
      const char *memory_kind = data_class != NULL ? data_class : "runtime_address";
      if (!ref->has_runtime_address && !ref->has_target && ref->data_class_flags == 0U) {
        continue;
      }
      if (emitted++ != 0U && json_builder_append(builder, ",") != 0) return -1;
      if (json_builder_appendf(builder,
          "{\"record_kind_id\":%u,\"record_kind\":\"runtime_address_ref\",\"memory_kind\":",
          (unsigned)M68K_MEMORY_LAYOUT_RECORD_RUNTIME_ADDRESS_REF) != 0)
        return -1;
      if (json_builder_append_json_string(builder, memory_kind) != 0) return -1;
      if (json_builder_appendf(builder, ",\"section_index\":%u,\"source_offset\":%u,\"source_size\":%u,"
          "\"runtime_address\":", (unsigned)section->section_index, (unsigned)ref->offset,
          (unsigned)ref->size) != 0) return -1;
      if (ref->has_runtime_address) {
        if (json_builder_appendf(builder, "%u", (unsigned)ref->runtime_address) != 0) return -1;
      } else if (json_builder_append(builder, "null") != 0) return -1;
      if (json_builder_append(builder, ",\"runtime_size\":") != 0) return -1;
      if (ref->size != 0U) {
        if (json_builder_appendf(builder, "%u", (unsigned)ref->size) != 0) return -1;
      } else if (json_builder_append(builder, "null") != 0) return -1;
      if (ref->has_runtime_address &&
          append_memory_layout_range_json(builder, MEMORY_LAYOUT_RANGE_SPACE_RUNTIME_ABSOLUTE,
            (int64_t)ref->runtime_address, ref->size) != 0)
        return -1;
      if (json_builder_append(builder, ",\"target_section_index\":") != 0) return -1;
      if (ref->has_target) {
        if (json_builder_appendf(builder, "%u", (unsigned)ref->target_section_index) != 0) return -1;
      } else if (json_builder_append(builder, "null") != 0) return -1;
      if (json_builder_append(builder, ",\"target_offset\":") != 0) return -1;
      if (ref->has_target) {
        if (json_builder_appendf(builder, "%u", (unsigned)ref->target_offset) != 0) return -1;
      } else if (json_builder_append(builder, "null") != 0) return -1;
      if (json_builder_append(builder, ",\"sink_address\":") != 0) return -1;
      if (ref->has_sink_address) {
        if (json_builder_appendf(builder, "%u", (unsigned)ref->sink_address) != 0) return -1;
      } else if (json_builder_append(builder, "null") != 0) return -1;
      if (json_builder_appendf(builder, ",\"confidence\":%u,\"data_class\":",
          (unsigned)ref->confidence) != 0) return -1;
      if (json_builder_append_nullable_string(builder, data_class) != 0) return -1;
      if (ref->data_class_flags != 0U &&
          json_builder_appendf(builder, ",\"data_class_flags\":%u", (unsigned)ref->data_class_flags) != 0)
        return -1;
      if (json_builder_append(builder, "}") != 0) return -1;
    }
    for (absolute_ref_index = 0U; absolute_ref_index < section->absolute_memory_ref_count;
        ++absolute_ref_index) {
      const M68kAbsoluteMemoryRefIR *ref = &section->absolute_memory_refs[absolute_ref_index];
      const char *memory_kind = absolute_memory_owner_kind_name(ref->owner_kind);
      const char *owner_symbol = NULL;
      const char *owner_base_symbol = NULL;
      absolute_memory_ref_owner_symbols(ref, &owner_symbol, &owner_base_symbol);
      if (emitted++ != 0U && json_builder_append(builder, ",") != 0) return -1;
      if (json_builder_appendf(builder,
          "{\"record_kind_id\":%u,\"record_kind\":\"absolute_memory_ref\",\"memory_kind\":",
          (unsigned)M68K_MEMORY_LAYOUT_RECORD_ABSOLUTE_MEMORY_REF) != 0)
        return -1;
      if (json_builder_append_json_string(builder, memory_kind) != 0) return -1;
      if (json_builder_appendf(builder,
          ",\"section_index\":%u,\"source_offset\":%u,\"source_size\":%u,"
          "\"operand_index\":%u,\"access\":",
          (unsigned)section->section_index, (unsigned)ref->offset, (unsigned)ref->source_size,
          (unsigned)ref->operand_index) != 0) {
        return -1;
      }
      if (json_builder_append_json_string(builder, listing_operand_access_name(ref->access_kind)) != 0)
        return -1;
      if (json_builder_appendf(builder,
          ",\"access_width\":%u,\"address\":%u,\"owner_kind_id\":%u,\"owner_kind\":",
          (unsigned)ref->access_width, (unsigned)ref->address, (unsigned)ref->owner_kind) != 0) {
        return -1;
      }
      if (json_builder_append_json_string(builder, absolute_memory_owner_kind_name(ref->owner_kind)) != 0)
        return -1;
      if (append_memory_layout_range_json(builder, MEMORY_LAYOUT_RANGE_SPACE_ABSOLUTE,
          (int64_t)ref->address, ref->access_width) != 0) return -1;
      if (json_builder_append(builder, ",\"owner_symbol\":") != 0) return -1;
      if (json_builder_append_nullable_string(builder, owner_symbol) != 0) return -1;
      if (json_builder_append(builder, ",\"owner_base_symbol\":") != 0) return -1;
      if (json_builder_append_nullable_string(builder, owner_base_symbol) != 0) return -1;
      {
        uint8_t conflict_state = ref->conflicted ? M68K_ANALYSIS_CONFLICT_STATE_CODE_OVERLAP :
          M68K_ANALYSIS_CONFLICT_STATE_CLEAN;
        if (json_builder_appendf(builder,
            ",\"owner_offset\":%u,\"confidence\":%u,\"conflicted\":%s,"
            "\"conflict_state_id\":%u,\"conflict_state\":\"%s\"}",
            (unsigned)ref->owner_offset, (unsigned)ref->confidence, ref->conflicted ? "true" : "false",
            (unsigned)conflict_state, analysis_conflict_state_name(conflict_state)) != 0) {
          return -1;
        }
      }
    }
  }
  return 0;
}

int source_analysis_to_json(const M68kSourceAnalysisIR *source_analysis, char **out_json, M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  size_t field_index, section_index;
  size_t orphan_code_signal_count = 0U;
  uint32_t orphan_status_counts[8] = {0U};
  uint32_t orphan_missing_inbound_counts[9] = {0U};
  size_t table_record_count = source_analysis_table_record_count(source_analysis != NULL ? &source_analysis->policy : NULL);
  size_t table_candidate_record_count = source_analysis_table_candidate_record_count(source_analysis);
  size_t memory_layout_record_count = source_analysis_memory_layout_record_count(source_analysis);
  for (section_index = 0U; source_analysis != NULL && section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t signal_index;
    orphan_code_signal_count += section->orphan_code_signal_count;
    for (signal_index = 0U; signal_index < section->orphan_code_signal_count; ++signal_index) {
      const M68kOrphanCodeSignalIR *signal = &section->orphan_code_signals[signal_index];
      if (signal->status < (sizeof(orphan_status_counts) / sizeof(orphan_status_counts[0])))
        ++orphan_status_counts[signal->status];
      if (signal->missing_inbound < (sizeof(orphan_missing_inbound_counts) /
          sizeof(orphan_missing_inbound_counts[0]))) {
        ++orphan_missing_inbound_counts[signal->missing_inbound];
      }
    }
  }
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
      "]},\"findings\":{\"required_cpu\":%u,\"cpu_violation_count\":%u},"
      "\"orphan_code_signal_count\":%u,\"orphan_code_signal_summary\":{"
      "\"status\":{\"unresolved\":%u,\"rejected\":%u,\"suppressed\":%u,\"linked\":%u,\"promoted\":%u},"
      "\"missing_inbound\":{\"unknown\":%u,\"jump_table\":%u,\"callback\":%u,\"vector\":%u,"
      "\"runtime_copy\":%u,\"api\":%u,\"metadata\":%u,\"policy_seed\":%u}},"
      "\"table_record_count\":%u,\"table_records\":[",
      (unsigned)source_analysis->findings.required_cpu,
      (unsigned)source_analysis->findings.cpu_violation_count,
      (unsigned)orphan_code_signal_count,
      (unsigned)orphan_status_counts[M68K_ORPHAN_CODE_SIGNAL_UNRESOLVED],
      (unsigned)orphan_status_counts[M68K_ORPHAN_CODE_SIGNAL_REJECTED],
      (unsigned)orphan_status_counts[M68K_ORPHAN_CODE_SIGNAL_SUPPRESSED],
      (unsigned)orphan_status_counts[M68K_ORPHAN_CODE_SIGNAL_LINKED],
      (unsigned)orphan_status_counts[M68K_ORPHAN_CODE_SIGNAL_PROMOTED],
      (unsigned)orphan_missing_inbound_counts[M68K_ORPHAN_CODE_SIGNAL_INBOUND_UNKNOWN],
      (unsigned)orphan_missing_inbound_counts[M68K_ORPHAN_CODE_SIGNAL_INBOUND_JUMP_TABLE],
      (unsigned)orphan_missing_inbound_counts[M68K_ORPHAN_CODE_SIGNAL_INBOUND_CALLBACK],
      (unsigned)orphan_missing_inbound_counts[M68K_ORPHAN_CODE_SIGNAL_INBOUND_VECTOR],
      (unsigned)orphan_missing_inbound_counts[M68K_ORPHAN_CODE_SIGNAL_INBOUND_RUNTIME_COPY],
      (unsigned)orphan_missing_inbound_counts[M68K_ORPHAN_CODE_SIGNAL_INBOUND_API],
      (unsigned)orphan_missing_inbound_counts[M68K_ORPHAN_CODE_SIGNAL_INBOUND_METADATA],
      (unsigned)orphan_missing_inbound_counts[M68K_ORPHAN_CODE_SIGNAL_INBOUND_POLICY_SEED],
      (unsigned)table_record_count) != 0)
    goto oom;
  if (append_source_analysis_table_records_json(&builder, source_analysis) != 0)
    goto oom;
  if (json_builder_appendf(&builder,
      "],\"table_candidate_record_count\":%u,\"table_candidate_records\":[",
      (unsigned)table_candidate_record_count) != 0)
    goto oom;
  if (append_source_analysis_table_candidate_records_json(&builder, source_analysis) != 0)
    goto oom;
  if (json_builder_appendf(&builder, "],\"memory_layout_record_count\":%u,\"memory_layout_records\":[",
      (unsigned)memory_layout_record_count) != 0)
    goto oom;
  if (append_source_analysis_memory_layout_records_json(&builder, source_analysis) != 0)
    goto oom;
  if (json_builder_appendf(&builder, "],\"base_layout_field_count\":%u,\"base_layout_fields\":[",
      (unsigned)source_analysis->base_layout_field_count) != 0)
    goto oom;
  for (field_index = 0U; field_index < source_analysis->base_layout_field_count; ++field_index) {
    const M68kBaseLayoutFieldIR *field = &source_analysis->base_layout_fields[field_index];
    const char *owner_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&field->owner_struct_ref,
      field->owner_struct_name);
    if (field_index != 0U && json_builder_append(&builder, ",") != 0) goto oom;
    if (json_builder_append(&builder, "{\"layout_name\":") != 0) goto oom;
    if (json_builder_append_nullable_string(&builder, field->layout_name) != 0) goto oom;
    if (json_builder_append(&builder, ",\"base_symbol\":") != 0) goto oom;
    if (json_builder_append_nullable_string(&builder, field->base_symbol) != 0) goto oom;
    if (json_builder_append(&builder, ",\"sizeof_symbol\":") != 0) goto oom;
    if (json_builder_append_nullable_string(&builder, field->sizeof_symbol) != 0) goto oom;
    if (json_builder_append(&builder, ",\"symbol\":") != 0) goto oom;
    if (json_builder_append_nullable_string(&builder, field->symbol) != 0) goto oom;
    if (json_builder_append(&builder, ",\"owner_struct_name\":") != 0) goto oom;
    if (json_builder_append_nullable_string(&builder, owner_struct_name) != 0) goto oom;
    if (json_builder_appendf(&builder,
        ",\"offset\":%u,\"size\":%u,\"alias\":%s,\"layout_kind\":%u,\"source_kind\":%u,\"source_kind_name\":",
        (unsigned)field->offset, (unsigned)field->size, field->alias ? "true" : "false",
        (unsigned)field->layout_kind, (unsigned)field->source_kind) != 0) goto oom;
    if (json_builder_append_json_string(&builder, base_layout_field_source_kind_name(field->source_kind)) != 0)
      goto oom;
    if (json_builder_appendf(&builder,
        ",\"value_kind\":%u,\"confidence\":%u,\"conflicted\":%s,\"conflict_reason\":",
        (unsigned)field->value_kind, (unsigned)field->confidence, field->conflicted ? "true" : "false") != 0)
      goto oom;
    if (json_builder_append_nullable_string(&builder, field->conflict_reason) != 0) goto oom;
    if (json_builder_append(&builder, ",\"alias_of_symbol\":") != 0) goto oom;
    if (field->has_alias_of) {
      if (json_builder_append_nullable_string(&builder, field->alias_of_symbol) != 0) goto oom;
    } else if (json_builder_append(&builder, "null") != 0) goto oom;
    if (json_builder_append(&builder, ",\"alias_of_offset\":") != 0) goto oom;
    if (field->has_alias_of) {
      if (json_builder_appendf(&builder, "%u", (unsigned)field->alias_of_offset) != 0) goto oom;
    } else if (json_builder_append(&builder, "null") != 0) goto oom;
    if (json_builder_append(&builder, ",\"source_section_index\":") != 0) goto oom;
    if (field->has_source) {
      if (json_builder_appendf(&builder, "%u", (unsigned)field->source_section_index) != 0) goto oom;
    } else if (json_builder_append(&builder, "null") != 0) goto oom;
    if (json_builder_append(&builder, ",\"source_offset\":") != 0) goto oom;
    if (field->has_source) {
      if (json_builder_appendf(&builder, "%u", (unsigned)field->source_offset) != 0) goto oom;
    } else if (json_builder_append(&builder, "null") != 0) goto oom;
    if (json_builder_append(&builder, "}") != 0) goto oom;
  }
  if (json_builder_appendf(&builder, "],\"section_count\":%u,\"sections\":[",
      (unsigned)source_analysis->section_count) != 0) goto oom;
  for (section_index = 0; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    size_t block_index, edge_index, violation_index, app_slot_ref_index, typed_access_index;
    size_t unresolved_typed_access_index, runtime_view_index, runtime_address_ref_index, code_start_ref_index;
    size_t string_ref_index;
    size_t effect_index, call_index, indirect_site_index, orphan_signal_index;
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
          "\"runtime_address\":%u,\"kind\":%u,\"confidence\":%u,"
          "\"materialized\":%s,\"materialization_reason\":%u,\"materialization_reason_name\":\"%s\"",
          (unsigned)view->runtime_view_id, (unsigned)view->storage_offset,
          (unsigned)view->storage_offset, (unsigned)view->size, (unsigned)view->runtime_address,
          (unsigned)view->kind, (unsigned)view->confidence, view->materialized ? "true" : "false",
          (unsigned)view->materialization_reason,
          runtime_view_materialization_reason_name(view->materialization_reason)) != 0) {
        goto oom;
      }
      if (append_runtime_view_relationship_json(&builder, &view->relationship) != 0) goto oom;
      if (json_builder_append(&builder, "}") != 0) goto oom;
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
      if (json_builder_append(&builder, ",\"sink_address\":") != 0)
        goto oom;
      if (ref->has_sink_address) {
        if (json_builder_appendf(&builder, "%u", (unsigned)ref->sink_address) != 0) goto oom;
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
      if (json_builder_append_nullable_string(&builder,
          m68k_analysis_structured_data_role_name_for_flags(ref->data_class_flags)) != 0)
        goto oom;
      if (ref->data_class_flags != 0U &&
          json_builder_appendf(&builder, ",\"data_class_flags\":%u", (unsigned)ref->data_class_flags) != 0)
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
            "\"field_offset\":%d,\"struct_size\":%u,\"field_size\":%u,\"root_struct_name\":",
            (unsigned)access->offset, (unsigned)access->operand_index, (unsigned)access->base_reg,
            (int)access->displacement, (int)access->field_offset, (unsigned)access->struct_size,
            (unsigned)access->field_size) != 0)
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
      if (json_builder_appendf(&builder, ",\"classification_id\":%u,\"classification\":",
          (unsigned)access->classification) != 0)
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
      if (call_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (append_recovered_platform_call_json(&builder, call) != 0)
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
      if (json_builder_appendf(&builder,
          "{\"offset\":%u,\"source_offset\":%u,\"source_size\":%u,\"operand_index\":%u,\"flow_kind\":%u,\"flow\":",
          (unsigned)site->offset, (unsigned)site->offset, (unsigned)site->source_size,
          (unsigned)site->operand_index, (unsigned)site->flow_kind) != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, recovered_indirect_flow_name(site->flow_kind)) != 0)
        goto oom;
      if (json_builder_appendf(&builder, ",\"shape_id\":%u,\"shape\":", (unsigned)site->shape) != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, recovered_indirect_shape_name(site->shape)) != 0)
        goto oom;
      if (json_builder_appendf(&builder, ",\"status_id\":%u,\"status\":", (unsigned)site->status) != 0)
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
      if (json_builder_append(&builder, ",\"table_offset\":") != 0)
        goto oom;
      if (site->has_table_bounds != 0U) {
        if (json_builder_appendf(&builder, "%u", (unsigned)site->table_offset) != 0)
          goto oom;
      } else if (json_builder_append(&builder, "null") != 0) {
        goto oom;
      }
      if (json_builder_append(&builder, ",\"table_size\":") != 0)
        goto oom;
      if (site->has_table_bounds != 0U) {
        if (json_builder_appendf(&builder, "%u", (unsigned)site->table_size) != 0)
          goto oom;
      } else if (json_builder_append(&builder, "null") != 0) {
        goto oom;
      }
      if (json_builder_append(&builder, ",\"table_entry_size\":") != 0)
        goto oom;
      if (site->has_table_bounds != 0U) {
        if (json_builder_appendf(&builder, "%u", (unsigned)site->table_entry_size) != 0)
          goto oom;
      } else if (json_builder_append(&builder, "null") != 0) {
        goto oom;
      }
      if (json_builder_append(&builder, ",\"table_entry_count\":") != 0)
        goto oom;
      if (site->has_table_bounds != 0U) {
        if (json_builder_appendf(&builder, "%u", (unsigned)site->table_entry_count) != 0)
          goto oom;
      } else if (json_builder_append(&builder, "null") != 0) {
        goto oom;
      }
      if (json_builder_appendf(&builder, ",\"table_bounds_status_id\":%u,\"table_bounds_status\":",
          (unsigned)site->table_bounds_status) != 0)
        goto oom;
      if (json_builder_append_json_string(&builder,
          recovered_indirect_table_bounds_status_name(site->table_bounds_status)) != 0) {
        goto oom;
      }
      if (json_builder_append(&builder, "}") != 0)
        goto oom;
    }
    if (json_builder_appendf(&builder, "],\"orphan_code_signal_count\":%u,\"orphan_code_signals\":[",
          (unsigned)section->orphan_code_signal_count) != 0)
      goto oom;
    for (orphan_signal_index = 0; orphan_signal_index < section->orphan_code_signal_count; ++orphan_signal_index) {
      const M68kOrphanCodeSignalIR *signal = &section->orphan_code_signals[orphan_signal_index];
      if (orphan_signal_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf(&builder,
          "{\"offset\":%u,\"size\":%u,\"terminal_offset\":%u,\"terminal_flow_kind\":%u,\"terminal_flow\":",
          (unsigned)signal->offset, (unsigned)signal->size, (unsigned)signal->terminal_offset,
          (unsigned)signal->terminal_flow_kind) != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, sim_flow_kind_name(signal->terminal_flow_kind)) != 0)
        goto oom;
      if (json_builder_appendf(&builder,
          ",\"required_cpu\":%u,\"instruction_count\":%u,\"decode_conflict_count\":%u",
          (unsigned)signal->required_cpu, (unsigned)signal->instruction_count,
          (unsigned)signal->decode_conflict_count) != 0)
        goto oom;
      if (json_builder_appendf(&builder, ",\"reason_id\":%u,\"reason\":",
          (unsigned)signal->reason) != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, orphan_code_signal_reason_name(signal->reason)) != 0)
        goto oom;
      if (json_builder_appendf(&builder, ",\"status_id\":%u,\"status\":",
          (unsigned)signal->status) != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, orphan_code_signal_status_name(signal->status)) != 0)
        goto oom;
      if (json_builder_appendf(&builder, ",\"context_id\":%u,\"context\":",
          (unsigned)signal->context) != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, orphan_code_signal_context_name(signal->context)) != 0)
        goto oom;
      if (json_builder_appendf(&builder, ",\"missing_inbound_id\":%u,\"missing_inbound\":",
          (unsigned)signal->missing_inbound) != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, orphan_code_signal_inbound_name(signal->missing_inbound)) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"nearby_data_class\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, signal->nearby_data_class) != 0)
        goto oom;
      if (json_builder_appendf(&builder, ",\"nearby_data_flags\":%u",
          (unsigned)signal->nearby_data_flags) != 0)
        goto oom;
      if (json_builder_appendf(&builder, ",\"nearby_data_offset\":%u,\"nearby_data_distance\":%u",
          (unsigned)signal->nearby_data_offset, (unsigned)signal->nearby_data_distance) != 0)
        goto oom;
      if (json_builder_append(&builder, ",\"nearby_data_relation\":") != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, signal->nearby_data_relation) != 0)
        goto oom;
      if (json_builder_appendf(&builder, ",\"confidence\":%u,\"detail\":",
          (unsigned)signal->confidence) != 0)
        goto oom;
      if (json_builder_append_nullable_string(&builder, signal->detail) != 0)
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

int source_analysis_platform_calls_to_json(const M68kSourceAnalysisIR *source_analysis, char **out_json,
    M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  size_t section_index;
  size_t call_index;
  int first_call = 1;
  if (out_json == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, "bad arguments");
    return -1;
  }
  *out_json = NULL;
  if (source_analysis == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, "bad arguments");
    return -1;
  }
  if (json_builder_create(&builder) != 0 ||
      json_builder_append(&builder, "{\"platform_calls\":[") != 0)
    goto oom;
  for (section_index = 0; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    for (call_index = 0; call_index < section->recovered_platform_call_count; ++call_index) {
      const M68kRecoveredPlatformCallIR *call = &section->recovered_platform_calls[call_index];
      if (!first_call && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf(&builder, "{\"section_index\":%u,\"call\":",
          (unsigned)section->section_index) != 0)
        goto oom;
      if (append_recovered_platform_call_json(&builder, call) != 0)
        goto oom;
      if (json_builder_append(&builder, "}") != 0)
        goto oom;
      first_call = 0;
    }
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
  uint32_t semantic_role_flags = structured_data_item_role_flags_json(item);
  if (item == NULL || (item->label[0] == '\0' && item->struct_name[0] == '\0' && item->field_name[0] == '\0' &&
        item->field_type[0] == '\0' && item->c_type[0] == '\0' && item->pointer_struct[0] == '\0' &&
        item->value_domain[0] == '\0' && item->constant_name[0] == '\0' && semantic_role_flags == 0U &&
        item->source_pattern[0] == '\0' && !item->has_constant_value && !item->is_pointer && !item->has_target)) {
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
  if (json_builder_append_nullable_string(builder,
      m68k_analysis_structured_data_role_name_for_flags(semantic_role_flags)) != 0)
    return -1;
  if (json_builder_appendf(builder, ",\"semantic_role_flags\":%u", (unsigned)semantic_role_flags) != 0)
    return -1;
  {
    const char *source_pattern = m68k_analysis_structured_data_source_pattern_name(item->source_pattern_id);
    if (json_builder_appendf(builder, ",\"source_pattern_id\":%u,\"source_pattern\":",
          (unsigned)item->source_pattern_id) != 0)
      return -1;
    if (json_builder_append_nullable_string(builder, source_pattern) != 0) return -1;
  }
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

static uint32_t listing_row_data_class_flags(const M68kAnalysisStructuredDataItem *item, const char *plan_data_class,
    uint32_t plan_data_class_flags) {
  uint32_t item_flags;
  if (item != NULL) {
    item_flags = structured_data_item_role_flags_json(item);
    if (item_flags != 0U) return item_flags;
    if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_STRING) return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING;
  }
  if (plan_data_class_flags != 0U) return plan_data_class_flags;
  (void)plan_data_class;
  return 0U;
}

static const char *listing_row_data_class(const M68kAnalysisStructuredDataItem *item, const char *plan_data_class,
    uint32_t plan_data_class_flags) {
  return m68k_analysis_structured_data_role_name_for_flags(
    listing_row_data_class_flags(item, plan_data_class, plan_data_class_flags));
}

static int listing_statement_allows_data_class(const M68kStatementIR *stmt) {
  return stmt != NULL && (stmt->kind == M68K_STATEMENT_DATA || stmt->kind == M68K_STATEMENT_RESERVE);
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
  if (json_builder_append(builder, ",\"sink_address\":") != 0) return -1;
  if (ref->has_sink_address) {
    if (json_builder_appendf(builder, "%u", (unsigned)ref->sink_address) != 0) return -1;
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
  if (json_builder_append_nullable_string(builder,
      m68k_analysis_structured_data_role_name_for_flags(ref->data_class_flags)) != 0) return -1;
  if (ref->data_class_flags != 0U &&
      json_builder_appendf(builder, ",\"data_class_flags\":%u", (unsigned)ref->data_class_flags) != 0)
    return -1;
  return json_builder_append(builder, "}");
}

static int append_listing_runtime_address_refs_json(JsonBuilder *builder, const M68kStatementIR *stmt,
    const M68kSectionAnalysisIR *section_analysis, const char *comment, int suppress_offset_fallback) {
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
          ref->data_class_flags == 0U)
        continue;
      if (emitted && json_builder_append(builder, ",") != 0) return -1;
      if (append_listing_runtime_address_ref_json(builder, ref) != 0) return -1;
      emitted = 1;
    }
    if (emitted) return json_builder_append(builder, "]");
  }
  if (suppress_offset_fallback) return json_builder_append(builder, "]");
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
        "\"struct_size\":%u,\"field_size\":%u,\"root_struct_name\":",
        (unsigned)access->operand_index, (unsigned)access->base_reg, (int)access->displacement,
        (int)access->field_offset, (unsigned)access->struct_size, (unsigned)access->field_size) != 0)
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
    if (json_builder_appendf(builder, ",\"classification_id\":%u,\"classification\":",
        (unsigned)access->classification) != 0) return -1;
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
  uint8_t access_kind;
  uint8_t width_kind;
  uint8_t width_size;
  size_t row_index;
  uint32_t addr;
  int section_index;
  char stable_key[128];
} ListingAppSlotRefRecord;

enum {
  LISTING_APP_SLOT_WIDTH_UNKNOWN = 0,
  LISTING_APP_SLOT_WIDTH_BYTE = 1,
  LISTING_APP_SLOT_WIDTH_WORD = 2,
  LISTING_APP_SLOT_WIDTH_LONG = 3
};

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
  Arena *arena;
  const M68kSourceAnalysisIR *source_analysis;
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

static void *listing_arena_grow_array(Arena *arena, const void *old_items, size_t old_count,
    size_t new_capacity, size_t item_size) {
  size_t old_size;
  size_t new_size;
  if (arena == NULL || item_size == 0U || new_capacity == 0U) return NULL;
  if (old_count > ((size_t)-1) / item_size || new_capacity > ((size_t)-1) / item_size) return NULL;
  old_size = old_count * item_size;
  new_size = new_capacity * item_size;
  return arena_realloc_copy(arena, old_items, old_size, new_size);
}

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

enum {
  LISTING_ROW_KIND_UNKNOWN = 0,
  LISTING_ROW_KIND_DIRECTIVE = 1,
  LISTING_ROW_KIND_LABEL = 2,
  LISTING_ROW_KIND_INSTRUCTION = 3,
  LISTING_ROW_KIND_DATA = 4,
  LISTING_ROW_KIND_BLANK = 5,
  LISTING_ROW_KIND_COMMENT = 6
};

static const char *listing_row_kind_name(uint8_t row_kind_id) {
  switch (row_kind_id) {
    case LISTING_ROW_KIND_DIRECTIVE: return "directive";
    case LISTING_ROW_KIND_LABEL: return "label";
    case LISTING_ROW_KIND_INSTRUCTION: return "instruction";
    case LISTING_ROW_KIND_DATA: return "data";
    case LISTING_ROW_KIND_BLANK: return "blank";
    case LISTING_ROW_KIND_COMMENT: return "comment";
    default: return "unknown";
  }
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

static uint8_t listing_app_slot_ref_width_kind(const M68kStatementIR *stmt, uint8_t *out_width_size) {
  uint8_t width_size = 1U;
  uint8_t width_kind = LISTING_APP_SLOT_WIDTH_UNKNOWN;
  if (stmt != NULL && stmt->kind == M68K_STATEMENT_INSTRUCTION) {
    if (stmt->u.instruction.size_suffix == 'b') {
      width_kind = LISTING_APP_SLOT_WIDTH_BYTE;
      width_size = 1U;
    } else if (stmt->u.instruction.size_suffix == 'w') {
      width_kind = LISTING_APP_SLOT_WIDTH_WORD;
      width_size = 2U;
    } else if (stmt->u.instruction.size_suffix == 'l') {
      width_kind = LISTING_APP_SLOT_WIDTH_LONG;
      width_size = 4U;
    }
  }
  if (out_width_size != NULL) *out_width_size = width_size;
  return width_kind;
}

static int listing_app_slot_analysis_init(ListingAppSlotAnalysisBuilder *analysis,
    uint8_t platform_backend_kind, const M68kSourceAnalysisIR *source_analysis) {
  if (analysis == NULL) return -1;
  memset(analysis, 0, sizeof(*analysis));
  analysis->arena = arena_create(4096U);
  if (analysis->arena == NULL) return -1;
  analysis->source_analysis = source_analysis;
  if (source_analysis == NULL || platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK ||
      source_analysis->section_count == 0U) {
    return 0;
  }
  if (source_analysis->section_count > ((size_t)-1) / 8U) return -1;
  analysis->sources = (ListingAppSlotSource *)arena_calloc(analysis->arena, source_analysis->section_count * 8U,
    sizeof(*analysis->sources));
  if (analysis->sources == NULL) return -1;
  analysis->source_section_count = source_analysis->section_count;
  analysis->enabled = 1U;
  return 0;
}

static void listing_app_slot_analysis_destroy(ListingAppSlotAnalysisBuilder *analysis) {
  if (analysis == NULL) return;
  arena_destroy(analysis->arena);
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
    grown = (ListingAppSlotRefRecord *)listing_arena_grow_array(analysis->arena, analysis->refs,
      analysis->ref_count, next_capacity, sizeof(*grown));
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
    grown = (ListingAppSlotTypedRegion *)listing_arena_grow_array(analysis->arena, analysis->regions,
      analysis->region_count, next_capacity, sizeof(*grown));
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

static int listing_app_slot_analysis_append_evidence(ListingAppSlotAnalysisBuilder *analysis,
    ListingAppSlotTypedRegion *region,
    const ListingAppSlotEvidence *evidence) {
  ListingAppSlotEvidence *grown;
  size_t next_capacity;
  if (analysis == NULL || region == NULL || evidence == NULL) return -1;
  if (region->evidence_count == region->evidence_capacity) {
    next_capacity = region->evidence_capacity == 0U ? 2U : region->evidence_capacity * 2U;
    grown = (ListingAppSlotEvidence *)listing_arena_grow_array(analysis->arena, region->evidence,
      region->evidence_count, next_capacity, sizeof(*grown));
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
    grown = (ListingAppSlotApiArgCandidate *)listing_arena_grow_array(analysis->arena, analysis->untyped_api_args,
      analysis->untyped_api_arg_count, next_capacity, sizeof(*grown));
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
      if (listing_app_slot_analysis_append_evidence(analysis, region, &evidence) != 0) return -1;
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
    ListingAppSlotRefRecord record;
    if (ref->offset != stmt->offset) continue;
    symbol_name = listing_app_slot_ref_symbol_name(stmt, ref, fallback_symbol, sizeof(fallback_symbol));
    if (symbol_name == NULL || app_slot_access_kind_name(ref->access_kind) == NULL) continue;
    memset(&record, 0, sizeof(record));
    listing_copy_text(record.symbol, sizeof(record.symbol), symbol_name);
    record.displacement = ref->displacement;
    record.base_reg = ref->base_reg;
    record.operand_index = ref->operand_index;
    record.access_kind = ref->access_kind;
    if (record.access_kind == M68K_APP_SLOT_ACCESS_ADDRESS) {
      record.width_kind = LISTING_APP_SLOT_WIDTH_UNKNOWN;
      record.width_size = 0U;
    } else {
      record.width_kind = listing_app_slot_ref_width_kind(stmt, &record.width_size);
    }
    record.row_index = row_index;
    record.addr = stmt->offset;
    record.section_index = section_index;
    listing_row_stable_key(record.stable_key, sizeof(record.stable_key), section_index, stmt->offset, row_kind,
      row_index);
    if (listing_app_slot_analysis_append_ref(analysis, &record) != 0) return -1;
    if (record.access_kind == M68K_APP_SLOT_ACCESS_ADDRESS) {
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
  switch (ref->access_kind) {
  case M68K_APP_SLOT_ACCESS_READ: ++summary->access_read; break;
  case M68K_APP_SLOT_ACCESS_WRITE: ++summary->access_write; break;
  case M68K_APP_SLOT_ACCESS_READ_WRITE: ++summary->access_read_write; break;
  case M68K_APP_SLOT_ACCESS_ADDRESS: ++summary->access_address; break;
  default: break;
  }
  if (ref->width_size != 0U) {
    switch (ref->width_kind) {
    case LISTING_APP_SLOT_WIDTH_BYTE: ++summary->width_byte; break;
    case LISTING_APP_SLOT_WIDTH_WORD: ++summary->width_word; break;
    case LISTING_APP_SLOT_WIDTH_LONG: ++summary->width_long; break;
    default: ++summary->width_unknown; break;
    }
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
        grown = (ListingAppSlotSummary *)listing_arena_grow_array(analysis->arena, summaries, summary_count,
          next_capacity, sizeof(*grown));
        if (grown == NULL) return NULL;
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

static int append_listing_base_layout_fields_json(JsonBuilder *builder,
    const ListingAppSlotAnalysisBuilder *analysis) {
  const M68kSourceAnalysisIR *source_analysis;
  size_t index;
  if (json_builder_append(builder, "[") != 0) return -1;
  source_analysis = analysis != NULL ? analysis->source_analysis : NULL;
  if (source_analysis == NULL) return json_builder_append(builder, "]");
  for (index = 0U; index < source_analysis->base_layout_field_count; ++index) {
    const M68kBaseLayoutFieldIR *field = &source_analysis->base_layout_fields[index];
    const char *owner_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&field->owner_struct_ref,
      field->owner_struct_name);
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"layout_name\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, field->layout_name) != 0) return -1;
    if (json_builder_append(builder, ",\"base_symbol\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, field->base_symbol) != 0) return -1;
    if (json_builder_append(builder, ",\"sizeof_symbol\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, field->sizeof_symbol) != 0) return -1;
    if (json_builder_append(builder, ",\"symbol\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, field->symbol) != 0) return -1;
    if (json_builder_append(builder, ",\"owner_struct_name\":") != 0) return -1;
    if (json_builder_append_nullable_string(builder, owner_struct_name) != 0) return -1;
    if (json_builder_appendf(builder,
          ",\"offset\":%u,\"size\":%u,\"alias\":%s,\"layout_kind\":%u,\"source_kind\":%u,\"source_kind_name\":",
          (unsigned)field->offset, (unsigned)field->size, field->alias ? "true" : "false",
          (unsigned)field->layout_kind, (unsigned)field->source_kind) != 0)
      return -1;
    if (json_builder_append_json_string(builder, base_layout_field_source_kind_name(field->source_kind)) != 0)
      return -1;
    if (json_builder_appendf(builder, ",\"confidence\":%u,\"conflicted\":%s,\"conflict_reason\":",
          (unsigned)field->confidence, field->conflicted ? "true" : "false") != 0)
      return -1;
    if (json_builder_append_nullable_string(builder, field->conflict_reason) != 0) return -1;
    if (json_builder_append(builder, ",\"alias_of_symbol\":") != 0) return -1;
    if (field->has_alias_of) {
      if (json_builder_append_nullable_string(builder, field->alias_of_symbol) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) return -1;
    if (json_builder_append(builder, ",\"alias_of_offset\":") != 0) return -1;
    if (field->has_alias_of) {
      if (json_builder_appendf(builder, "%u", (unsigned)field->alias_of_offset) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) return -1;
    if (json_builder_append(builder, "}") != 0) return -1;
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
  switch (ref->access_kind) {
  case M68K_APP_SLOT_ACCESS_READ: ++summary->access_read; break;
  case M68K_APP_SLOT_ACCESS_WRITE: ++summary->access_write; break;
  case M68K_APP_SLOT_ACCESS_READ_WRITE: ++summary->access_read_write; break;
  case M68K_APP_SLOT_ACCESS_ADDRESS: ++summary->access_address; break;
  default: break;
  }
  if (ref->width_size != 0U) {
    switch (ref->width_kind) {
    case LISTING_APP_SLOT_WIDTH_BYTE: ++summary->width_byte; break;
    case LISTING_APP_SLOT_WIDTH_WORD: ++summary->width_word; break;
    case LISTING_APP_SLOT_WIDTH_LONG: ++summary->width_long; break;
    default: ++summary->width_unknown; break;
    }
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
        grown = (ListingAppSlotFieldRefSummary *)listing_arena_grow_array(analysis->arena, fields, field_count,
          next_capacity, sizeof(*grown));
        if (grown == NULL) return NULL;
        fields = grown;
        field_capacity = next_capacity;
      }
      field = &fields[field_count++];
      memset(field, 0, sizeof(*field));
      listing_copy_text(field->symbol, sizeof(field->symbol), ref->symbol);
      field->displacement = ref->displacement;
      field->field_offset = field_offset;
      field->region_address = ref->access_kind == M68K_APP_SLOT_ACCESS_ADDRESS && field_offset == 0 &&
        strcmp(ref->symbol, region->symbol) == 0;
      if (!field->region_address &&
          amiga_os_resolve_struct_field_by_struct_id(region->struct_id, field_offset, 0, &field->field)) {
        field->has_field = 1U;
      }
    } else if (!(ref->access_kind == M68K_APP_SLOT_ACCESS_ADDRESS && field_offset == 0 &&
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
      if (json_builder_append_json_string(builder, app_slot_access_kind_name(ref->access_kind)) != 0) return -1;
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

static int append_listing_rsset_layout_regions_json(JsonBuilder *builder, const ListingAppSlotAnalysisBuilder *analysis,
    const ListingAppSlotSummary *summaries, size_t summary_count) {
  size_t index;
  int emitted = 0;
  if (json_builder_append(builder, "[") != 0) return -1;
  for (index = 0U; index < analysis->region_count; ++index) {
    const ListingAppSlotTypedRegion *region = &analysis->regions[index];
    ListingAppSlotFieldRefSummary *fields;
    ArenaMark mark = arena_mark(analysis->arena);
    size_t field_count = 0U;
    fields = listing_app_slot_build_field_refs(analysis, region, &field_count);
    if (emitted && json_builder_append(builder, ",") != 0) {
      arena_rewind(analysis->arena, mark);
      return -1;
    }
    if (json_builder_append(builder, "{\"id\":") != 0) {
      arena_rewind(analysis->arena, mark);
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
      arena_rewind(analysis->arena, mark);
      return -1;
    }
    arena_rewind(analysis->arena, mark);
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
  intervals = (ListingAppSlotInterval *)arena_calloc(analysis->arena, analysis->region_count + summary_count,
    sizeof(*intervals));
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
    ArenaMark mark = arena_mark(analysis->arena);
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
          arena_rewind(analysis->arena, mark);
          return -1;
        }
      }
      if (end > cursor) cursor = end;
    }
    if (cursor < region->size && interval_count != 0U) {
      if (append_listing_app_slot_field_gap_segments_json(builder, region, cursor, region->size, &emitted,
          &gap_count) != 0) {
        arena_rewind(analysis->arena, mark);
        return -1;
      }
    }
    arena_rewind(analysis->arena, mark);
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
    ArenaMark mark = arena_mark(analysis->arena);
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
    arena_rewind(analysis->arena, mark);
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
      "{\"slot_count\":0,\"ref_count\":0,\"typed_region_count\":0,\"layout_field_count\":0,\"gap_count\":0,"
      "\"field_gap_count\":0,\"suggestion_count\":0,\"untyped_api_arg_count\":0,\"slots\":[],"
      "\"layout_fields\":[],\"regions\":[],\"gaps\":[],"
      "\"field_gaps\":[],\"suggestions\":[],\"untyped_api_args\":[]}");
  }
  qsort(analysis->regions, analysis->region_count, sizeof(*analysis->regions), listing_app_slot_region_compare);
  summaries = listing_app_slot_build_summaries(analysis, &summary_count);
  intervals = listing_app_slot_build_intervals(analysis, summaries, summary_count, &interval_count);
  gap_count = listing_app_slot_gap_count(intervals, interval_count);
  field_gap_count = listing_app_slot_field_gap_count(analysis);
  if (json_builder_appendf(builder,
        "{\"slot_count\":%u,\"ref_count\":%u,\"typed_region_count\":%u,\"layout_field_count\":%u,\"gap_count\":%u,"
        "\"field_gap_count\":%u,\"suggestion_count\":%u,\"untyped_api_arg_count\":%u,\"slots\":",
        (unsigned)summary_count, (unsigned)analysis->ref_count, (unsigned)analysis->region_count,
        (unsigned)(analysis->source_analysis != NULL ? analysis->source_analysis->base_layout_field_count : 0U),
        (unsigned)gap_count, (unsigned)field_gap_count, (unsigned)analysis->region_count,
        (unsigned)analysis->untyped_api_arg_count) != 0)
    goto cleanup;
  if (append_listing_app_slot_slots_json(builder, summaries, summary_count) != 0) goto cleanup;
  if (json_builder_append(builder, ",\"layout_fields\":") != 0) goto cleanup;
  if (append_listing_base_layout_fields_json(builder, analysis) != 0) goto cleanup;
  if (json_builder_append(builder, ",\"regions\":") != 0) goto cleanup;
  if (append_listing_rsset_layout_regions_json(builder, analysis, summaries, summary_count) != 0) goto cleanup;
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

static const M68kRuntimeViewIR *listing_runtime_view_at_storage_offset(
    const M68kSourceAnalysisIR *source_analysis, int section_index, uint32_t storage_offset) {
  const M68kSectionAnalysisIR *section;
  size_t index;
  if (source_analysis == NULL || section_index < 0 || (size_t)section_index >= source_analysis->section_count)
    return NULL;
  section = &source_analysis->sections[section_index];
  for (index = 0U; index < section->runtime_view_count; ++index) {
    const M68kRuntimeViewIR *view = &section->runtime_views[index];
    if (view->storage_offset == storage_offset) return view;
  }
  return NULL;
}

static const M68kRuntimeViewIR *listing_runtime_view_for_storage_runtime_offset(
    const M68kSourceAnalysisIR *source_analysis, int section_index, uint32_t storage_offset,
    uint32_t runtime_address) {
  const M68kSectionAnalysisIR *section;
  size_t index;
  if (source_analysis == NULL || section_index < 0 || (size_t)section_index >= source_analysis->section_count)
    return NULL;
  section = &source_analysis->sections[section_index];
  for (index = 0U; index < section->runtime_view_count; ++index) {
    const M68kRuntimeViewIR *view = &section->runtime_views[index];
    uint32_t delta;
    if (storage_offset < view->storage_offset) continue;
    delta = storage_offset - view->storage_offset;
    if (delta >= view->size || view->runtime_address > UINT32_MAX - delta) continue;
    if (view->runtime_address + delta == runtime_address) return view;
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
    const M68kSectionAnalysisIR *section_analysis, const char *comment, int suppress_offset_fallback) {
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
          ref->data_class_flags != 0U)
        return 1;
    }
  }
  if (suppress_offset_fallback) return 0;
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

static const M68kRecoveredPlatformCallIR *listing_platform_call_at_offset(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset) {
  size_t index;
  if (section_analysis == NULL) return NULL;
  for (index = 0U; index < section_analysis->recovered_platform_call_count; ++index)
    if (section_analysis->recovered_platform_calls[index].offset == offset)
      return &section_analysis->recovered_platform_calls[index];
  return NULL;
}

static int listing_structured_data_item_has_json(const M68kAnalysisStructuredDataItem *item) {
  uint32_t semantic_role_flags = structured_data_item_role_flags_json(item);
  return item != NULL && !(item->label[0] == '\0' && item->struct_name[0] == '\0' &&
    item->field_name[0] == '\0' && item->field_type[0] == '\0' && item->c_type[0] == '\0' &&
    item->pointer_struct[0] == '\0' && item->value_domain[0] == '\0' && item->constant_name[0] == '\0' &&
    semantic_role_flags == 0U && !item->has_constant_value && !item->is_pointer && !item->has_target);
}

static int append_listing_row_json_parsed(JsonBuilder *builder, size_t row_index, const char *line_start,
    size_t line_length, uint8_t row_kind_id, const char *stripped, const char *opcode, const char *operand,
    const char *comment, int section_index, const M68kStatementIR *stmt,
    const M68kAnalysisPolicy *analysis_policy, const M68kSourceAnalysisIR *source_analysis,
    const char *analysis_generation, const char *plan_data_class, uint32_t plan_data_class_flags,
    int has_plan_runtime_address, uint32_t plan_runtime_address) {
  char text[1200];
  char label_text[1024];
  const char *row_kind = listing_row_kind_name(row_kind_id);
  const char *label = NULL;
  const M68kAnalysisStructuredDataItem *structured_item = NULL;
  int has_addr = 0;
  uint32_t addr = 0U;
  uint32_t end_offset = 0U;
  uint32_t byte_count = 0U;
  const M68kRuntimeViewIR *runtime_view = NULL;
  uint32_t runtime_address = 0U;
  int suppress_offset_runtime_refs = 0;
  const char *row_data_class = NULL;
  uint32_t row_data_class_flags = 0U;
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
    suppress_offset_runtime_refs =
      structured_item != NULL && stmt->kind == M68K_STATEMENT_DATA && byte_count > 4U;
    if (has_plan_runtime_address) {
      runtime_address = plan_runtime_address;
      runtime_view = listing_runtime_view_for_storage_runtime_offset(source_analysis, section_index, addr,
        runtime_address);
    } else {
      runtime_view = listing_runtime_view_for_storage_offset(source_analysis, section_index, addr,
        &runtime_address);
    }
  }
  if (label == NULL && row_kind_id == LISTING_ROW_KIND_LABEL) {
    size_t stripped_length;
    snprintf(label_text, sizeof(label_text), "%s", stripped != NULL ? stripped : "");
    stripped_length = strlen(label_text);
    if (stripped_length != 0U && label_text[stripped_length - 1U] == ':') label_text[stripped_length - 1U] = '\0';
    label = label_text;
  }
  if (listing_statement_allows_data_class(stmt)) {
    row_data_class_flags = listing_row_data_class_flags(structured_item, plan_data_class, plan_data_class_flags);
    row_data_class = m68k_analysis_structured_data_role_name_for_flags(row_data_class_flags);
  }
  if (json_builder_appendf(builder, "{\"row_id\":\"c:%u\",\"kind_id\":%u,\"kind\":",
      (unsigned)row_index, (unsigned)row_kind_id) != 0) return -1;
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
  } else {
    if (json_builder_append(builder, ",\"start_offset\":null,\"end_offset\":null,\"storage_address\":null") != 0)
      return -1;
  }
  if (runtime_view != NULL || has_plan_runtime_address) {
    if (json_builder_append(builder, ",\"runtime_address\":") != 0) return -1;
    if (json_builder_appendf(builder, "%u", (unsigned)runtime_address) != 0) return -1;
    if (json_builder_append(builder, ",\"runtime_view_id\":") != 0) return -1;
    if (runtime_view != NULL) {
      if (json_builder_appendf(builder, "%u", (unsigned)runtime_view->runtime_view_id) != 0) return -1;
    } else if (json_builder_append(builder, "null") != 0) return -1;
  } else {
    if (json_builder_append(builder, ",\"runtime_address\":null,\"runtime_view_id\":null") != 0) return -1;
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
  } else {
    if (json_builder_append(builder, ",\"addr\":null,\"entity_addr\":null") != 0) return -1;
  }
  if (label != NULL) {
    if (json_builder_append(builder, ",\"label\":") != 0) return -1;
    if (json_builder_append_json_string(builder, label) != 0) return -1;
  }
  if (opcode != NULL && opcode[0] != '\0' && row_kind_id != LISTING_ROW_KIND_LABEL &&
      row_kind_id != LISTING_ROW_KIND_BLANK && row_kind_id != LISTING_ROW_KIND_COMMENT) {
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
    if (listing_stmt_has_runtime_address_refs(stmt, section_analysis, comment, suppress_offset_runtime_refs)) {
      if (json_builder_append(builder, ",\"runtime_address_refs\":") != 0) return -1;
      if (append_listing_runtime_address_refs_json(builder, stmt, section_analysis, comment,
          suppress_offset_runtime_refs) != 0)
        return -1;
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
    if (stmt != NULL && stmt->kind == M68K_STATEMENT_INSTRUCTION) {
      const M68kRecoveredPlatformCallIR *call = listing_platform_call_at_offset(section_analysis, stmt->offset);
      if (call != NULL) {
        if (json_builder_append(builder, ",\"api_call\":") != 0) return -1;
        if (append_listing_api_call_json(builder, call) != 0) return -1;
      }
    }
  }
  if (listing_structured_data_item_has_json(structured_item)) {
    if (json_builder_append(builder, ",\"structured_data\":") != 0) return -1;
    if (append_listing_structured_data_json(builder, structured_item) != 0) return -1;
  }
  if (row_data_class != NULL) {
    if (json_builder_append(builder, ",\"data_class\":") != 0) return -1;
    if (json_builder_append_json_string(builder, row_data_class) != 0)
      return -1;
    if (json_builder_appendf(builder, ",\"data_class_flags\":%u", (unsigned)row_data_class_flags) != 0)
      return -1;
  }
  return json_builder_append(builder, "}");
}

static int append_listing_row_json(JsonBuilder *builder, size_t row_index, const char *line_start, size_t line_length,
    uint8_t row_kind_id, int section_index, const M68kStatementIR *stmt, const M68kAnalysisPolicy *analysis_policy,
    const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation) {
  char stripped[1024];
  char opcode[128];
  char operand[1024];
  char comment[512];
  split_listing_line(line_start, line_length, stripped, sizeof(stripped), opcode, sizeof(opcode), operand,
    sizeof(operand), comment, sizeof(comment));
  return append_listing_row_json_parsed(builder, row_index, line_start, line_length, row_kind_id, stripped, opcode,
    operand, comment, section_index, stmt, analysis_policy, source_analysis, analysis_generation, NULL, 0U, 0, 0U);
}

typedef struct ListingSourceHeaderRow {
  const char *line_start;
  size_t line_length;
  uint8_t row_kind_id;
  int section_index;
  int group;
} ListingSourceHeaderRow;

typedef struct ListingSourceHeaderRows {
  Arena *arena;
  ListingSourceHeaderRow *items;
  size_t count;
  size_t capacity;
} ListingSourceHeaderRows;

typedef struct ListingNavigationJsonContext ListingNavigationJsonContext;

static int listing_navigation_observe_row(ListingNavigationJsonContext *navigation, size_t row_index,
    const char *line_start, size_t line_length, uint8_t row_kind_id, const char *stripped, const char *opcode,
    const char *operand, const char *comment, int section_index, const M68kStatementIR *stmt,
    const char *plan_data_class, uint32_t plan_data_class_flags);

static int listing_source_header_rows_init(ListingSourceHeaderRows *rows) {
  if (rows == NULL) return -1;
  memset(rows, 0, sizeof(*rows));
  rows->arena = arena_create(4096U);
  return rows->arena != NULL ? 0 : -1;
}

static void listing_source_header_rows_destroy(ListingSourceHeaderRows *rows) {
  if (rows == NULL) return;
  arena_destroy(rows->arena);
  memset(rows, 0, sizeof(*rows));
}

static int listing_source_header_rows_append(ListingSourceHeaderRows *rows, const char *line_start, size_t line_length,
    uint8_t row_kind_id, int section_index, int group) {
  ListingSourceHeaderRow *new_items;
  size_t new_capacity;
  if (rows == NULL || line_start == NULL) return -1;
  if (rows->count == rows->capacity) {
    new_capacity = rows->capacity == 0U ? 16U : rows->capacity * 2U;
    new_items = (ListingSourceHeaderRow *)listing_arena_grow_array(rows->arena, rows->items, rows->count,
      new_capacity, sizeof(*new_items));
    if (new_items == NULL) return -1;
    rows->items = new_items;
    rows->capacity = new_capacity;
  }
  rows->items[rows->count].line_start = line_start;
  rows->items[rows->count].line_length = line_length;
  rows->items[rows->count].row_kind_id = row_kind_id;
  rows->items[rows->count].section_index = section_index;
  rows->items[rows->count].group = group;
  ++rows->count;
  return 0;
}

static int listing_should_keep_source_only_body_row(const M68kRenderPlanRow *row, uint8_t row_kind_id,
    int active_section_index, int is_plan_directive_subline) {
  if (active_section_index < 0 || row == NULL) return 0;
  if (row_kind_id == LISTING_ROW_KIND_COMMENT) return 1;
  if (is_plan_directive_subline) return 1;
  return row->kind == M68K_RENDER_PLAN_ROW_ORG || row->kind == M68K_RENDER_PLAN_ROW_PLATFORM_DIRECTIVE;
}

typedef struct ListingRenderPlanJsonContext {
  JsonBuilder *builder;
  ListingSourceHeaderRows *header_rows;
  ListingAppSlotAnalysisBuilder *app_slot_analysis;
  ListingNavigationJsonContext *navigation;
  const M68kSourceFileIR *source_file;
  const M68kAnalysisPolicy *analysis_policy;
  const M68kSourceAnalysisIR *source_analysis;
  const char *analysis_generation;
  const M68kRenderPlan *render_plan;
  const M68kRenderPlanRow *current_plan_row;
  PlatformListingRowIndexEntry *row_index_entries;
  size_t row_index_entry_count;
  size_t row_index;
  size_t emitted_count;
  size_t window_start;
  size_t window_end;
  uint32_t anchor_addr;
  const char *anchor_code;
  size_t anchor_code_row_index;
  uint32_t current_subline;
  int active_section_index;
  int preamble_emitted;
  int emit_preamble_headers;
  int include_source_only_rows;
  int count_only;
  int window_enabled;
  int has_anchor_addr;
  int has_anchor_code_row;
} ListingRenderPlanJsonContext;

static uint8_t listing_row_kind_id_for_plan_row(const M68kRenderPlanRow *row) {
  if (row == NULL) return LISTING_ROW_KIND_UNKNOWN;
  if (row->kind == M68K_RENDER_PLAN_ROW_INCLUDE) return LISTING_ROW_KIND_DIRECTIVE;
  if (row->kind == M68K_RENDER_PLAN_ROW_RSSET) return LISTING_ROW_KIND_DIRECTIVE;
  if (row->kind == M68K_RENDER_PLAN_ROW_RS_FIELD) return LISTING_ROW_KIND_DIRECTIVE;
  if (row->kind == M68K_RENDER_PLAN_ROW_EQUATE) return LISTING_ROW_KIND_DIRECTIVE;
  if (row->kind == M68K_RENDER_PLAN_ROW_SECTION) return LISTING_ROW_KIND_DIRECTIVE;
  if (row->kind == M68K_RENDER_PLAN_ROW_ORG) return LISTING_ROW_KIND_DIRECTIVE;
  if (row->kind == M68K_RENDER_PLAN_ROW_LABEL) return LISTING_ROW_KIND_LABEL;
  if (row->kind == M68K_RENDER_PLAN_ROW_INSTRUCTION) return LISTING_ROW_KIND_INSTRUCTION;
  if (row->kind == M68K_RENDER_PLAN_ROW_DATA) return LISTING_ROW_KIND_DATA;
  if (row->kind == M68K_RENDER_PLAN_ROW_RESERVE) return LISTING_ROW_KIND_DATA;
  if (row->kind == M68K_RENDER_PLAN_ROW_BLANK) return LISTING_ROW_KIND_BLANK;
  if (row->kind == M68K_RENDER_PLAN_ROW_PLATFORM_DIRECTIVE) return LISTING_ROW_KIND_DIRECTIVE;
  if (row->kind == M68K_RENDER_PLAN_ROW_DIAGNOSTIC) return LISTING_ROW_KIND_COMMENT;
  return LISTING_ROW_KIND_UNKNOWN;
}

static int listing_plan_subline_is_directive(const M68kRenderPlanRow *row, uint32_t subline) {
  if (row == NULL || subline >= 32U) return 0;
  return (row->directive_line_mask & (1U << subline)) != 0U;
}

static int listing_plan_subline_is_label(const M68kRenderPlanRow *row, uint32_t subline,
    uint32_t *out_source_offset, uint8_t *out_has_runtime_address, uint32_t *out_runtime_address) {
  if (out_source_offset != NULL) *out_source_offset = 0U;
  if (out_has_runtime_address != NULL) *out_has_runtime_address = 0U;
  if (out_runtime_address != NULL) *out_runtime_address = 0U;
  if (row == NULL || subline >= 32U || (row->label_line_mask & (1U << subline)) == 0U) return 0;
  if (out_source_offset != NULL) *out_source_offset = row->label_line_source_offsets[subline];
  if ((row->label_line_runtime_mask & (1U << subline)) != 0U) {
    if (out_has_runtime_address != NULL) *out_has_runtime_address = 1U;
    if (out_runtime_address != NULL) *out_runtime_address = row->label_line_runtime_addresses[subline];
  }
  return 1;
}

static void listing_navigation_row_code(char *out, size_t out_size, uint8_t row_kind_id, const char *stripped,
    const char *opcode, const char *operand, const M68kStatementIR *stmt);

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

static int listing_statement_from_plan_row_metadata(const M68kRenderPlanRow *row, M68kStatementIR *stmt) {
  if (row == NULL || stmt == NULL || !row->has_statement_metadata || !row->has_source_range) return 0;
  m68k_ir_statement_init(stmt);
  stmt->kind = row->statement_kind;
  stmt->offset = row->source_offset;
  stmt->source_byte_count = row->source_byte_count;
  if (row->source_byte_count != 0U) memcpy(stmt->source_bytes, row->source_bytes, row->source_byte_count);
  if (row->statement_kind == M68K_STATEMENT_INSTRUCTION) {
    stmt->u.instruction = row->statement_instruction;
  } else if (row->statement_kind == M68K_STATEMENT_DATA) {
    stmt->u.data.kind = M68K_DATA_ITEM_BYTES;
    stmt->u.data.size = row->source_size;
  } else if (row->statement_kind == M68K_STATEMENT_RESERVE) {
    stmt->u.reserve_size = row->source_size;
  }
  return 1;
}

static int append_listing_render_plan_json_row(ListingRenderPlanJsonContext *context, const char *line_start,
    size_t line_length, uint8_t row_kind_id, const char *stripped, const char *opcode, const char *operand,
    const char *comment, int section_index, const M68kStatementIR *stmt, int has_plan_runtime_address,
    uint32_t plan_runtime_address) {
  int emit_row;
  const char *row_kind = listing_row_kind_name(row_kind_id);
  if (context == NULL) return -1;
  if (context->anchor_code != NULL && !context->has_anchor_code_row && stripped != NULL &&
      opcode != NULL && operand != NULL) {
    char row_code[1024];
    listing_navigation_row_code(row_code, sizeof(row_code), row_kind_id, stripped, opcode, operand, stmt);
    if (strcmp(row_code, context->anchor_code) == 0) {
      context->anchor_code_row_index = context->row_index;
      context->has_anchor_code_row = 1;
    }
  }
  if (stmt != NULL && !context->has_anchor_addr && context->row_index == context->window_start) {
    context->anchor_addr = stmt->offset;
    context->has_anchor_addr = 1;
  }
  if (context->row_index_entries != NULL && context->row_index < context->row_index_entry_count) {
    PlatformListingRowIndexEntry *entry = &context->row_index_entries[context->row_index];
    if (context->current_plan_row != NULL && context->render_plan != NULL &&
        context->current_plan_row >= context->render_plan->rows &&
        context->current_plan_row < context->render_plan->rows + context->render_plan->row_count) {
      entry->has_plan_row = 1U;
      entry->plan_row_index = (uint32_t)(context->current_plan_row - context->render_plan->rows);
      entry->subline = context->current_subline;
    } else {
      entry->has_plan_row = 0U;
      entry->plan_row_index = 0U;
      entry->subline = 0U;
    }
    if (stmt != NULL) {
      entry->has_addr = 1U;
      entry->addr = stmt->offset;
    } else {
      entry->has_addr = 0U;
      entry->addr = 0U;
    }
  }
  emit_row = !context->window_enabled ||
    (context->row_index >= context->window_start && context->row_index < context->window_end);
  if (!context->count_only && emit_row) {
    if (context->builder == NULL) return -1;
    if (context->emitted_count != 0U && json_builder_append(context->builder, ",") != 0) return -1;
    if (stripped != NULL && opcode != NULL && operand != NULL && comment != NULL) {
      if (append_listing_row_json_parsed(context->builder, context->row_index, line_start, line_length, row_kind_id,
          stripped, opcode, operand, comment, section_index, stmt, context->analysis_policy,
          context->source_analysis, context->analysis_generation,
          context->current_plan_row != NULL ? context->current_plan_row->data_class : NULL,
          context->current_plan_row != NULL ? context->current_plan_row->data_class_flags : 0U,
          has_plan_runtime_address, plan_runtime_address) != 0)
        return -1;
    } else if (append_listing_row_json(context->builder, context->row_index, line_start, line_length, row_kind_id,
        section_index, stmt, context->analysis_policy, context->source_analysis, context->analysis_generation) != 0)
      return -1;
    if (context->app_slot_analysis != NULL &&
        listing_app_slot_analysis_observe_row(context->app_slot_analysis, context->row_index, row_kind,
          section_index, stmt, context->source_analysis) != 0)
      return -1;
    ++context->emitted_count;
  }
  if (context->navigation != NULL &&
      listing_navigation_observe_row(context->navigation, context->row_index, line_start, line_length, row_kind_id,
        stripped, opcode, operand, comment, section_index, stmt,
        context->current_plan_row != NULL ? context->current_plan_row->data_class : NULL,
        context->current_plan_row != NULL ? context->current_plan_row->data_class_flags : 0U) != 0)
    return -1;
  ++context->row_index;
  return 0;
}

static int append_listing_render_plan_blank_row(ListingRenderPlanJsonContext *context) {
  static const char blank_line[] = "\n";
  if (context != NULL) {
    context->current_plan_row = NULL;
    context->current_subline = 0U;
  }
  return append_listing_render_plan_json_row(context, blank_line, 1U, LISTING_ROW_KIND_BLANK, NULL, NULL, NULL, NULL,
    -1, NULL, 0, 0U);
}

static int append_listing_source_header_rows(ListingRenderPlanJsonContext *context) {
  const M68kRenderPlanRow *saved_plan_row;
  uint32_t saved_subline;
  size_t index;
  int group;
  int emitted_any = 0;
  int result = -1;
  if (context == NULL || context->header_rows == NULL) return -1;
  saved_plan_row = context->current_plan_row;
  saved_subline = context->current_subline;
  for (group = 0; group <= 2; ++group) {
    int emitted_group = 0;
    for (index = 0U; index < context->header_rows->count; ++index) {
      const ListingSourceHeaderRow *row = &context->header_rows->items[index];
      if (row->group != group) continue;
      if (emitted_any && !emitted_group) {
        if (append_listing_render_plan_blank_row(context) != 0) goto done;
      }
      context->current_plan_row = NULL;
      context->current_subline = 0U;
      if (append_listing_render_plan_json_row(context, row->line_start, row->line_length, row->row_kind_id,
          NULL, NULL, NULL, NULL, row->section_index, NULL, 0, 0U) != 0)
        goto done;
      emitted_group = 1;
      emitted_any = 1;
    }
  }
  if (emitted_any && append_listing_render_plan_blank_row(context) != 0) goto done;
  result = 0;

done:
  context->current_plan_row = saved_plan_row;
  context->current_subline = saved_subline;
  return result;
}

static size_t listing_source_header_rows_extra_count(const ListingSourceHeaderRows *header_rows) {
  int groups_seen[3] = {0, 0, 0};
  size_t group_count = 0U;
  size_t index;
  if (header_rows == NULL || header_rows->count == 0U) return 0U;
  for (index = 0U; index < header_rows->count; ++index) {
    int group = header_rows->items[index].group;
    if (group < 0 || group > 2 || groups_seen[group]) continue;
    groups_seen[group] = 1;
    ++group_count;
  }
  return group_count != 0U ? header_rows->count + group_count : 0U;
}

typedef struct ListingRenderPlanHeaderContext {
  ListingSourceHeaderRows *header_rows;
  int stopped;
} ListingRenderPlanHeaderContext;

static int listing_source_header_group_for_plan_row(const M68kRenderPlanRow *row) {
  if (row == NULL) return -1;
  if (row->kind == M68K_RENDER_PLAN_ROW_DIAGNOSTIC) return 0;
  if (row->kind == M68K_RENDER_PLAN_ROW_INCLUDE) return 1;
  if (row->kind == M68K_RENDER_PLAN_ROW_RSSET || row->kind == M68K_RENDER_PLAN_ROW_RS_FIELD ||
      row->kind == M68K_RENDER_PLAN_ROW_EQUATE)
    return 2;
  return -1;
}

static int collect_listing_source_header_plan_line(const M68kRenderPlanRow *row, uint32_t subline, uint32_t line,
    const char *line_start, size_t line_length, void *user) {
  ListingRenderPlanHeaderContext *context = (ListingRenderPlanHeaderContext *)user;
  uint8_t row_kind_id;
  (void)subline;
  (void)line;
  if (context == NULL || context->header_rows == NULL || context->stopped) return 0;
  if (row != NULL && row->kind == M68K_RENDER_PLAN_ROW_SECTION) {
    context->stopped = 1;
    return 0;
  }
  if (row != NULL) {
    int group = listing_source_header_group_for_plan_row(row);
    row_kind_id = listing_row_kind_id_for_plan_row(row);
    if (group >= 0) {
      if (listing_source_header_rows_append(context->header_rows, line_start, line_length, row_kind_id, -1,
          group) != 0)
        return -1;
    }
    return 0;
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

static int append_full_listing_render_plan_line(const M68kRenderPlanRow *row, uint32_t subline, uint32_t line,
    const char *line_start, size_t line_length, void *user) {
  ListingRenderPlanJsonContext *context = (ListingRenderPlanJsonContext *)user;
  int is_section_directive = 0;
  int is_plan_directive_subline = listing_plan_subline_is_directive(row, subline);
  uint32_t label_source_offset = 0U;
  uint8_t label_has_runtime_address = 0U;
  uint32_t label_runtime_address = 0U;
  int is_plan_label_subline = listing_plan_subline_is_label(row, subline, &label_source_offset,
    &label_has_runtime_address, &label_runtime_address);
  int section_index = -1;
  char stripped[1024];
  char opcode[128];
  char operand[1024];
  char comment[512];
  uint8_t row_kind_id;
  const M68kStatementIR *stmt = NULL;
  M68kStatementIR plan_stmt;
  (void)subline;
  (void)line;
  m68k_ir_statement_init(&plan_stmt);
  if (context == NULL) return -1;
  context->current_plan_row = row;
  context->current_subline = subline;
  split_listing_line(line_start, line_length, stripped, sizeof(stripped), opcode, sizeof(opcode), operand,
    sizeof(operand), comment, sizeof(comment));
  row_kind_id = listing_row_kind_id_for_plan_row(row);
  if (is_plan_directive_subline) row_kind_id = LISTING_ROW_KIND_DIRECTIVE;
  else if (is_plan_label_subline) row_kind_id = LISTING_ROW_KIND_LABEL;
  is_section_directive = row != NULL && row->kind == M68K_RENDER_PLAN_ROW_SECTION;
  section_index = listing_section_index_for_plan_row(row);
  if (is_section_directive) {
    if (section_index >= 0) context->active_section_index = section_index;
    else ++context->active_section_index;
    section_index = context->active_section_index;
  } else if (is_plan_label_subline) {
    m68k_ir_statement_init(&plan_stmt);
    plan_stmt.kind = M68K_STATEMENT_LABEL;
    plan_stmt.offset = label_source_offset;
    stmt = &plan_stmt;
    if (section_index >= 0) context->active_section_index = section_index;
  } else if (!is_plan_directive_subline && row != NULL && (row->has_statement || row->has_source_range)) {
    stmt = listing_statement_for_plan_row(context->source_file, row);
    if (stmt == NULL && listing_statement_from_plan_row_metadata(row, &plan_stmt)) stmt = &plan_stmt;
    if (section_index >= 0) context->active_section_index = section_index;
  }
  if (context->emit_preamble_headers && !context->include_source_only_rows &&
      !context->preamble_emitted && is_section_directive) {
    if (append_listing_source_header_rows(context) != 0)
      return -1;
    context->preamble_emitted = 1;
  }
  if (!context->include_source_only_rows && stmt == NULL && !is_section_directive &&
      !listing_should_keep_source_only_body_row(row, row_kind_id, context->active_section_index,
        is_plan_directive_subline)) {
    return 0;
  }
  if (append_listing_render_plan_json_row(context, line_start, line_length, row_kind_id, stripped, opcode, operand,
      comment, section_index, stmt, label_has_runtime_address ? 1 : 0, label_runtime_address) != 0)
    return -1;
  return 0;
}

typedef struct ListingNavigationLabelRef {
  char symbol[128];
  uint8_t access_kind;
  char summary[512];
  char match_text[512];
  char stable_key[128];
  size_t row_index;
  uint32_t addr;
  int section_index;
} ListingNavigationLabelRef;

enum {
  LISTING_LABEL_ACCESS_NONE = 0,
  LISTING_LABEL_ACCESS_DEFINITION = 1,
  LISTING_LABEL_ACCESS_REFERENCE = 2
};

static const char *listing_label_access_name(uint8_t access_kind) {
  switch (access_kind) {
    case LISTING_LABEL_ACCESS_DEFINITION: return "definition";
    case LISTING_LABEL_ACCESS_REFERENCE: return "reference";
    default: return "unknown";
  }
}

typedef struct ListingNavigationLabelBuilder {
  Arena *arena;
  ListingNavigationLabelRef *refs;
  size_t ref_count;
  size_t ref_capacity;
} ListingNavigationLabelBuilder;

typedef struct ListingNavigationTypedDataKey {
  char summary[512];
  uint32_t addr;
  int section_index;
} ListingNavigationTypedDataKey;

struct ListingNavigationJsonContext {
  Arena *arena;
  ListingNavigationTypedDataKey *typed_data_keys;
  size_t typed_data_key_count;
  size_t typed_data_key_capacity;
  JsonBuilder typed_data;
  JsonBuilder typed_gaps;
  JsonBuilder relocations;
  JsonBuilder api_calls;
  JsonBuilder runtime_views;
  JsonBuilder orphan_code;
  JsonBuilder comments;
  ListingNavigationLabelBuilder labels;
  ListingAppSlotAnalysisBuilder app_slot_analysis;
  const M68kAnalysisPolicy *analysis_policy;
  const M68kSourceAnalysisIR *source_analysis;
  uint8_t platform_backend_kind;
  size_t typed_data_count;
  size_t typed_gaps_count;
  size_t relocations_count;
  size_t api_calls_count;
  size_t runtime_views_count;
  size_t orphan_code_count;
  size_t comments_count;
};

static int listing_navigation_label_builder_init(ListingNavigationLabelBuilder *labels) {
  if (labels == NULL) return -1;
  memset(labels, 0, sizeof(*labels));
  labels->arena = arena_create(4096U);
  return labels->arena != NULL ? 0 : -1;
}

static void listing_navigation_label_builder_destroy(ListingNavigationLabelBuilder *labels) {
  if (labels == NULL) return;
  arena_destroy(labels->arena);
  memset(labels, 0, sizeof(*labels));
}

static ListingNavigationLabelRef *listing_navigation_label_append(ListingNavigationLabelBuilder *labels) {
  ListingNavigationLabelRef *grown;
  size_t next_capacity;
  if (labels == NULL) return NULL;
  if (labels->ref_count == labels->ref_capacity) {
    next_capacity = labels->ref_capacity == 0U ? 64U : labels->ref_capacity * 2U;
    grown = (ListingNavigationLabelRef *)listing_arena_grow_array(labels->arena, labels->refs,
      labels->ref_count, next_capacity, sizeof(*grown));
    if (grown == NULL) return NULL;
    labels->refs = grown;
    labels->ref_capacity = next_capacity;
  }
  memset(&labels->refs[labels->ref_count], 0, sizeof(labels->refs[labels->ref_count]));
  return &labels->refs[labels->ref_count++];
}

static int listing_navigation_group_init(JsonBuilder *builder) {
  return json_builder_create(builder) == 0 && json_builder_append(builder, "[") == 0 ? 0 : -1;
}

static void listing_navigation_destroy(ListingNavigationJsonContext *navigation) {
  if (navigation == NULL) return;
  arena_destroy(navigation->arena);
  json_builder_destroy(&navigation->typed_data);
  json_builder_destroy(&navigation->typed_gaps);
  json_builder_destroy(&navigation->relocations);
  json_builder_destroy(&navigation->api_calls);
  json_builder_destroy(&navigation->runtime_views);
  json_builder_destroy(&navigation->orphan_code);
  json_builder_destroy(&navigation->comments);
  listing_navigation_label_builder_destroy(&navigation->labels);
  listing_app_slot_analysis_destroy(&navigation->app_slot_analysis);
  memset(navigation, 0, sizeof(*navigation));
}

static int listing_navigation_init(ListingNavigationJsonContext *navigation, uint8_t platform_backend_kind,
    const M68kSourceAnalysisIR *source_analysis, const M68kAnalysisPolicy *analysis_policy) {
  if (navigation == NULL) return -1;
  memset(navigation, 0, sizeof(*navigation));
  navigation->arena = arena_create(4096U);
  if (navigation->arena == NULL) return -1;
  navigation->platform_backend_kind = platform_backend_kind;
  navigation->source_analysis = source_analysis;
  navigation->analysis_policy = analysis_policy;
  if (listing_navigation_group_init(&navigation->typed_data) != 0 ||
      listing_navigation_group_init(&navigation->typed_gaps) != 0 ||
      listing_navigation_group_init(&navigation->relocations) != 0 ||
      listing_navigation_group_init(&navigation->api_calls) != 0 ||
      listing_navigation_group_init(&navigation->runtime_views) != 0 ||
      listing_navigation_group_init(&navigation->orphan_code) != 0 ||
      listing_navigation_group_init(&navigation->comments) != 0 ||
      listing_navigation_label_builder_init(&navigation->labels) != 0 ||
      listing_app_slot_analysis_init(&navigation->app_slot_analysis, platform_backend_kind, source_analysis) != 0) {
    listing_navigation_destroy(navigation);
    return -1;
  }
  return 0;
}

static void listing_navigation_row_code(char *out, size_t out_size, uint8_t row_kind_id, const char *stripped,
    const char *opcode, const char *operand, const M68kStatementIR *stmt) {
  const char *label = NULL;
  if (out == NULL || out_size == 0U) return;
  out[0] = '\0';
  if (stmt != NULL && stmt->label_name != NULL && stmt->label_name[0] != '\0') label = stmt->label_name;
  if (label == NULL && row_kind_id == LISTING_ROW_KIND_LABEL && stripped != NULL) {
    listing_copy_text(out, out_size, stripped);
    {
      size_t length = strlen(out);
      if (length != 0U && out[length - 1U] == ':') out[length - 1U] = '\0';
    }
    return;
  }
  if (label != NULL) {
    listing_copy_text(out, out_size, label);
    return;
  }
  if (opcode != NULL && opcode[0] != '\0') {
    if (operand != NULL && operand[0] != '\0') snprintf(out, out_size, "%s %s", opcode, operand);
    else listing_copy_text(out, out_size, opcode);
    return;
  }
  listing_copy_text(out, out_size, stripped != NULL ? stripped : "");
}

static int append_listing_navigation_entry(JsonBuilder *builder, const M68kStatementIR *stmt, size_t row_index,
    int section_index, const char *row_kind, const char *summary, const char *match_text,
    uint32_t data_class_flags) {
  char stable_key[128];
  if (builder == NULL || stmt == NULL || summary == NULL || match_text == NULL) return -1;
  listing_row_stable_key(stable_key, sizeof(stable_key), section_index, stmt->offset, row_kind, row_index);
  if (json_builder_appendf(builder, "{\"addr\":%u,\"row_index\":%u,\"summary\":",
        (unsigned)stmt->offset, (unsigned)row_index) != 0)
    return -1;
  if (json_builder_append_json_string(builder, summary) != 0) return -1;
  if (json_builder_append(builder, ",\"match_text\":") != 0) return -1;
  if (json_builder_append_json_string(builder, match_text) != 0) return -1;
  if (json_builder_append(builder, ",\"stable_key\":") != 0) return -1;
  if (json_builder_append_json_string(builder, stable_key) != 0) return -1;
  if (section_index >= 0 &&
      json_builder_appendf(builder, ",\"hunk_index\":%d,\"section_index\":%d", section_index, section_index) != 0)
    return -1;
  if (data_class_flags != 0U &&
      json_builder_appendf(builder, ",\"data_class_flags\":%u", (unsigned)data_class_flags) != 0)
    return -1;
  return json_builder_append(builder, "}");
}

static int listing_navigation_typed_data_is_duplicate(ListingNavigationJsonContext *navigation,
    const M68kStatementIR *stmt, int section_index, const char *summary, int *out_duplicate) {
  ListingNavigationTypedDataKey *grown;
  ListingNavigationTypedDataKey *key;
  size_t index;
  size_t next_capacity;
  if (out_duplicate != NULL) *out_duplicate = 0;
  if (navigation == NULL || stmt == NULL || summary == NULL) return -1;
  for (index = 0U; index < navigation->typed_data_key_count; ++index) {
    const ListingNavigationTypedDataKey *existing = &navigation->typed_data_keys[index];
    if (existing->section_index == section_index && existing->addr == stmt->offset &&
        strcmp(existing->summary, summary) == 0) {
      if (out_duplicate != NULL) *out_duplicate = 1;
      return 0;
    }
  }
  if (navigation->typed_data_key_count == navigation->typed_data_key_capacity) {
    next_capacity = navigation->typed_data_key_capacity == 0U ? 64U :
      navigation->typed_data_key_capacity * 2U;
    grown = (ListingNavigationTypedDataKey *)listing_arena_grow_array(navigation->arena,
      navigation->typed_data_keys, navigation->typed_data_key_count, next_capacity, sizeof(*grown));
    if (grown == NULL) return -1;
    navigation->typed_data_keys = grown;
    navigation->typed_data_key_capacity = next_capacity;
  }
  key = &navigation->typed_data_keys[navigation->typed_data_key_count++];
  memset(key, 0, sizeof(*key));
  key->section_index = section_index;
  key->addr = stmt->offset;
  listing_copy_text(key->summary, sizeof(key->summary), summary);
  return 0;
}

static int append_listing_navigation_typed_data_entry(ListingNavigationJsonContext *navigation,
    const M68kStatementIR *stmt, size_t row_index, int section_index, const char *row_kind, const char *summary,
    const char *match_text, uint32_t data_class_flags) {
  int duplicate = 0;
  if (listing_navigation_typed_data_is_duplicate(navigation, stmt, section_index, summary, &duplicate) != 0)
    return -1;
  if (duplicate) return 0;
  if (navigation->typed_data_count++ != 0U && json_builder_append(&navigation->typed_data, ",") != 0)
    return -1;
  return append_listing_navigation_entry(&navigation->typed_data, stmt, row_index, section_index, row_kind,
    summary, match_text, data_class_flags);
}

static const M68kRecoveredPlatformTypedAccessIR *listing_navigation_typed_access_at(const M68kSectionAnalysisIR *section,
    uint32_t offset) {
  size_t index;
  if (section == NULL) return NULL;
  for (index = 0U; index < section->recovered_platform_typed_access_count; ++index)
    if (section->recovered_platform_typed_accesses[index].offset == offset)
      return &section->recovered_platform_typed_accesses[index];
  return NULL;
}

static void listing_navigation_typed_summary(char *out, size_t out_size,
    const M68kRecoveredPlatformTypedAccessIR *access) {
  const char *owner;
  const char *field;
  if (out == NULL || out_size == 0U) return;
  out[0] = '\0';
  if (access == NULL) return;
  owner = m68k_platform_name_ref_resolve_text_or_fallback(&access->owner_struct_ref, access->owner_struct_name);
  if (owner == NULL || owner[0] == '\0')
    owner = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref, access->root_struct_name);
  field = access->field_expr[0] != '\0' ? access->field_expr : access->field_name;
  if (owner != NULL && owner[0] != '\0' && field != NULL && field[0] != '\0')
    snprintf(out, out_size, "%s.%s", owner, field);
  else if (field != NULL && field[0] != '\0') listing_copy_text(out, out_size, field);
  else if (owner != NULL) listing_copy_text(out, out_size, owner);
}

static void listing_navigation_signed_hex(char *out, size_t out_size, int16_t value) {
  if (out == NULL || out_size == 0U) return;
  if (value < 0) snprintf(out, out_size, "-$%04X", (unsigned)(uint16_t)(-value));
  else snprintf(out, out_size, "$%04X", (unsigned)(uint16_t)value);
}

static void listing_navigation_unresolved_summary(char *out, size_t out_size,
    const M68kRecoveredPlatformUnresolvedTypedAccessIR *access) {
  const char *root;
  const char *container;
  const char *refined;
  char displacement[16];
  const char *joiner;
  if (out == NULL || out_size == 0U) return;
  out[0] = '\0';
  if (access == NULL) return;
  root = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref, access->root_struct_name);
  root = root != NULL && root[0] != '\0' ? root : "typed base";
  container = m68k_platform_name_ref_resolve_text_or_fallback(&access->container_struct_ref,
    access->container_struct_name);
  refined = m68k_platform_name_ref_resolve_text_or_fallback(&access->refined_struct_ref,
    access->refined_struct_name);
  listing_navigation_signed_hex(displacement, sizeof(displacement), access->displacement);
  joiner = access->displacement < 0 ? "" : "+";
  if (access->classification == M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION) {
    if (access->refinement_applied && refined != NULL && refined[0] != '\0')
      snprintf(out, out_size, "%s%s%s refines to %s", root, joiner, displacement, refined);
    else if (container != NULL && container[0] != '\0' && access->container_field_expr[0] != '\0')
      snprintf(out, out_size, "%s%s%s prefix extension: %s.%s", root, joiner, displacement, container,
        access->container_field_expr);
    else if (container != NULL && container[0] != '\0')
      snprintf(out, out_size, "%s%s%s prefix extension: %s", root, joiner, displacement, container);
    else if (access->container_candidate_count != 0U)
      snprintf(out, out_size, "%s%s%s prefix extension (%u candidate types)", root, joiner, displacement,
        (unsigned)access->container_candidate_count);
    else snprintf(out, out_size, "%s%s%s prefix extension", root, joiner, displacement);
  } else if (access->classification == M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_CUSTOM_TAIL_OR_MISTYPED_BASE) {
    snprintf(out, out_size, "%s%s%s unknown extension", root, joiner, displacement);
  } else {
    snprintf(out, out_size, "%s%s%s field metadata gap", root, joiner, displacement);
  }
}

static int append_listing_navigation_unresolved_entry(JsonBuilder *builder, const M68kStatementIR *stmt,
    size_t row_index, int section_index, const char *row_kind, const char *summary, const char *match_text,
    const M68kRecoveredPlatformUnresolvedTypedAccessIR *access) {
  char stable_key[128];
  if (builder == NULL || stmt == NULL || summary == NULL || match_text == NULL || access == NULL) return -1;
  listing_row_stable_key(stable_key, sizeof(stable_key), section_index, stmt->offset, row_kind, row_index);
  if (json_builder_appendf(builder, "{\"addr\":%u,\"row_index\":%u,\"summary\":",
        (unsigned)stmt->offset, (unsigned)row_index) != 0)
    return -1;
  if (json_builder_append_json_string(builder, summary) != 0) return -1;
  if (json_builder_append(builder, ",\"match_text\":") != 0) return -1;
  if (json_builder_append_json_string(builder, match_text) != 0) return -1;
  if (json_builder_append(builder, ",\"stable_key\":") != 0) return -1;
  if (json_builder_append_json_string(builder, stable_key) != 0) return -1;
  if (section_index >= 0 &&
      json_builder_appendf(builder, ",\"hunk_index\":%d,\"section_index\":%d", section_index, section_index) != 0)
    return -1;
  if (json_builder_append(builder, ",\"root_struct_name\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder,
      m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref, access->root_struct_name)) != 0)
    return -1;
  if (json_builder_appendf(builder, ",\"base_register\":\"A%u\",\"operand_index\":%u,\"displacement\":%d,"
        "\"struct_size\":%u,\"classification_id\":%u,\"classification\":",
        (unsigned)access->base_reg, (unsigned)access->operand_index, (int)access->displacement,
        (unsigned)access->struct_size, (unsigned)access->classification) != 0)
    return -1;
  if (json_builder_append_json_string(builder,
      unresolved_typed_access_classification_name(access->classification)) != 0) return -1;
  if (json_builder_appendf(builder, ",\"container_candidate_count\":%u,\"container_struct_name\":",
      (unsigned)access->container_candidate_count) != 0) return -1;
  if (json_builder_append_nullable_string(builder,
      m68k_platform_name_ref_resolve_text_or_fallback(&access->container_struct_ref,
        access->container_struct_name)) != 0)
    return -1;
  if (json_builder_append(builder, ",\"container_field_expr\":") != 0) return -1;
  if (json_builder_append_nullable_string(builder, access->container_field_expr) != 0) return -1;
  if (json_builder_appendf(builder, ",\"refinement_applied\":%s,\"refined_struct_name\":",
      access->refinement_applied ? "true" : "false") != 0)
    return -1;
  if (json_builder_append_nullable_string(builder,
      m68k_platform_name_ref_resolve_text_or_fallback(&access->refined_struct_ref,
        access->refined_struct_name)) != 0)
    return -1;
  if (json_builder_append(builder, ",\"type_provenance_kind\":") != 0) return -1;
  if (json_builder_append_json_string(builder, type_provenance_kind_name(access->type_provenance_kind)) != 0)
    return -1;
  if (access->type_provenance_kind != M68K_PLATFORM_TYPE_PROVENANCE_NONE &&
      json_builder_appendf(builder, ",\"type_provenance_section\":%u,\"type_provenance_offset\":%u",
        (unsigned)access->type_provenance_section_index, (unsigned)access->type_provenance_offset) != 0)
    return -1;
  return json_builder_append(builder, "}");
}

static const M68kRecoveredPlatformCallIR *listing_navigation_call_at(const M68kSectionAnalysisIR *section,
    uint32_t offset) {
  size_t index;
  if (section == NULL) return NULL;
  for (index = 0U; index < section->recovered_platform_call_count; ++index)
    if (section->recovered_platform_calls[index].offset == offset) return &section->recovered_platform_calls[index];
  return NULL;
}

static int listing_navigation_call_same_function(const M68kRecoveredPlatformCallIR *left,
    const M68kRecoveredPlatformCallIR *right) {
  const AmigaOsLibraryVectorInfo *left_vector;
  const AmigaOsLibraryVectorInfo *right_vector;
  if (left == NULL || right == NULL) return 0;
  left_vector = resolve_amiga_call_vector_for_json(left, NULL);
  right_vector = resolve_amiga_call_vector_for_json(right, NULL);
  if (left_vector == NULL || right_vector == NULL) return 0;
  return left_vector->library_id == right_vector->library_id && left_vector->function_id == right_vector->function_id;
}

static int listing_navigation_call_has_near_lvo_reference(const M68kSectionAnalysisIR *section, uint32_t offset,
    const M68kRecoveredPlatformCallIR *call) {
  uint32_t probe;
  uint32_t start = offset > 8U ? offset - 8U : 0U;
  for (probe = start; probe < offset; ++probe) {
    const M68kRecoveredPlatformCallIR *candidate = listing_navigation_call_at(section, probe);
    if (candidate != NULL && candidate->note_kind == M68K_PLATFORM_CALL_NOTE_NONE &&
        listing_navigation_call_same_function(candidate, call))
      return 1;
  }
  return 0;
}

static int listing_navigation_call_is_target(const M68kSectionAnalysisIR *section, uint32_t offset,
    const M68kRecoveredPlatformCallIR *call) {
  if (call == NULL) return 0;
  if (call->note_kind == M68K_PLATFORM_CALL_NOTE_LOCAL_WRAPPER_SYMBOL) return 0;
  if (call->note_kind == M68K_PLATFORM_CALL_NOTE_INDEXED_VECTOR &&
      listing_navigation_call_has_near_lvo_reference(section, offset, call))
    return 0;
  return 1;
}

static int append_listing_navigation_api_call_entry(JsonBuilder *builder, const M68kStatementIR *stmt,
    size_t row_index, int section_index, const char *row_kind, const char *match_text,
    const M68kRecoveredPlatformCallIR *call) {
  const AmigaOsLibraryVectorInfo *amiga_vector = resolve_amiga_call_vector_for_json(call, NULL);
  const char *library_name = resolve_amiga_call_library_name_for_json(call, amiga_vector);
  const char *function_name = amiga_vector != NULL ? amiga_os_name(3U, amiga_vector->function_id) : NULL;
  char summary[256];
  if (function_name == NULL) function_name = "";
  if (library_name == NULL) library_name = "";
  snprintf(summary, sizeof(summary), call->note_kind == M68K_PLATFORM_CALL_NOTE_INDEXED_VECTOR ?
    "%s dispatch (%s)" : "%s (%s)", function_name, library_name);
  return append_listing_navigation_entry(builder, stmt, row_index, section_index, row_kind, summary, match_text, 0U);
}

static int append_listing_navigation_runtime_view_entry(JsonBuilder *builder, const M68kStatementIR *stmt,
    size_t row_index, int section_index, const char *row_kind, const char *match_text,
    const M68kRuntimeViewIR *view) {
  char summary[256];
  const char *state;
  const char *reason;
  if (view == NULL) return -1;
  state = view->materialized ? "materialized" : "suppressed";
  reason = runtime_view_materialization_reason_name(view->materialization_reason);
  snprintf(summary, sizeof(summary), "Runtime view $%04X-$%04X -> $%04X %s/%s",
    (unsigned)view->storage_offset, (unsigned)(view->storage_offset + view->size),
    (unsigned)view->runtime_address, state, reason);
  return append_listing_navigation_entry(builder, stmt, row_index, section_index, row_kind, summary, match_text, 0U);
}

static const M68kOrphanCodeSignalIR *listing_navigation_orphan_signal_at(const M68kSectionAnalysisIR *section,
    uint32_t offset) {
  size_t index;
  if (section == NULL) return NULL;
  for (index = 0U; index < section->orphan_code_signal_count; ++index) {
    const M68kOrphanCodeSignalIR *signal = &section->orphan_code_signals[index];
    if (signal->offset == offset) return signal;
  }
  return NULL;
}

static int append_listing_navigation_orphan_code_entry(JsonBuilder *builder, const M68kStatementIR *stmt,
    size_t row_index, int section_index, const char *row_kind, const char *match_text,
    const M68kOrphanCodeSignalIR *signal) {
  char summary[192];
  if (signal == NULL) return -1;
  snprintf(summary, sizeof(summary), "Orphan code signal $%04X-$%04X %s/%s",
    (unsigned)signal->offset, (unsigned)(signal->offset + signal->size),
    orphan_code_signal_reason_name(signal->reason), orphan_code_signal_status_name(signal->status));
  return append_listing_navigation_entry(builder, stmt, row_index, section_index, row_kind, summary, match_text, 0U);
}

static int listing_navigation_append_label_ref(ListingNavigationJsonContext *navigation, const char *symbol,
    uint8_t access_kind, const char *summary, const char *match_text, const M68kStatementIR *stmt, size_t row_index,
    int section_index, const char *row_kind) {
  ListingNavigationLabelRef *ref;
  if (navigation == NULL || symbol == NULL || symbol[0] == '\0' || stmt == NULL ||
      access_kind == LISTING_LABEL_ACCESS_NONE)
    return 0;
  ref = listing_navigation_label_append(&navigation->labels);
  if (ref == NULL) return -1;
  listing_copy_text(ref->symbol, sizeof(ref->symbol), symbol);
  ref->access_kind = access_kind;
  listing_copy_text(ref->summary, sizeof(ref->summary), summary != NULL ? summary : "");
  listing_copy_text(ref->match_text, sizeof(ref->match_text), match_text != NULL ? match_text : "");
  listing_row_stable_key(ref->stable_key, sizeof(ref->stable_key), section_index, stmt->offset, row_kind, row_index);
  ref->row_index = row_index;
  ref->addr = stmt->offset;
  ref->section_index = section_index;
  return 0;
}

static int listing_navigation_has_label_definition(const ListingNavigationLabelBuilder *labels, const char *symbol) {
  size_t index;
  if (labels == NULL || symbol == NULL) return 0;
  for (index = 0U; index < labels->ref_count; ++index)
    if (strcmp(labels->refs[index].symbol, symbol) == 0 &&
        labels->refs[index].access_kind == LISTING_LABEL_ACCESS_DEFINITION)
      return 1;
  return 0;
}

static int listing_navigation_observe_label_refs(ListingNavigationJsonContext *navigation,
    const M68kStatementIR *stmt, size_t row_index, int section_index, const char *row_kind,
    const char *match_text) {
  size_t operand_index;
  if (stmt == NULL || stmt->kind != M68K_STATEMENT_INSTRUCTION) return 0;
  for (operand_index = 0U; operand_index < stmt->u.instruction.operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &stmt->u.instruction.operands[operand_index];
    if (operand->symbol_ref.has_name == 0U || operand->symbol_ref.name[0] == '\0') continue;
    if (listing_navigation_append_label_ref(navigation, operand->symbol_ref.name, LISTING_LABEL_ACCESS_REFERENCE,
        match_text, match_text, stmt, row_index, section_index, row_kind) != 0)
      return -1;
  }
  return 0;
}

static int listing_navigation_observe_row(ListingNavigationJsonContext *navigation, size_t row_index,
    const char *line_start, size_t line_length, uint8_t row_kind_id, const char *stripped, const char *opcode,
    const char *operand, const char *comment, int section_index, const M68kStatementIR *stmt,
    const char *plan_data_class, uint32_t plan_data_class_flags) {
  const M68kSectionAnalysisIR *section = NULL;
  char match_text[512];
  char summary[512];
  const char *row_kind = listing_row_kind_name(row_kind_id);
  (void)line_start;
  (void)line_length;
  if (navigation == NULL) return 0;
  listing_navigation_row_code(match_text, sizeof(match_text), row_kind_id, stripped, opcode, operand, stmt);
  if (stmt != NULL && section_index >= 0 && navigation->source_analysis != NULL &&
      (size_t)section_index < navigation->source_analysis->section_count)
    section = &navigation->source_analysis->sections[section_index];
  if (listing_app_slot_analysis_observe_row(&navigation->app_slot_analysis, row_index, row_kind, section_index,
      stmt, navigation->source_analysis) != 0)
    return -1;
  if (stmt != NULL && row_kind_id == LISTING_ROW_KIND_LABEL) {
    char symbol[128];
    char label_summary[160];
    listing_copy_text(symbol, sizeof(symbol), match_text);
    snprintf(label_summary, sizeof(label_summary), "%s:", symbol);
    if (listing_navigation_append_label_ref(navigation, symbol, LISTING_LABEL_ACCESS_DEFINITION, label_summary,
        symbol, stmt, row_index, section_index, row_kind) != 0)
      return -1;
  }
  if (listing_navigation_observe_label_refs(navigation, stmt, row_index, section_index, row_kind, match_text) != 0)
    return -1;
  if (stmt != NULL && row_kind_id != LISTING_ROW_KIND_LABEL) {
    const M68kRuntimeViewIR *runtime_view = listing_runtime_view_at_storage_offset(navigation->source_analysis,
      section_index, stmt->offset);
    if (runtime_view != NULL) {
      if (navigation->runtime_views_count++ != 0U && json_builder_append(&navigation->runtime_views, ",") != 0)
        return -1;
      if (append_listing_navigation_runtime_view_entry(&navigation->runtime_views, stmt, row_index, section_index,
          row_kind, match_text, runtime_view) != 0)
        return -1;
    }
  }
  if (stmt != NULL && stmt->kind == M68K_STATEMENT_INSTRUCTION && section != NULL) {
    const M68kRecoveredPlatformTypedAccessIR *typed_access =
      listing_navigation_typed_access_at(section, stmt->offset);
    const M68kRecoveredPlatformCallIR *call = listing_navigation_call_at(section, stmt->offset);
    size_t access_index;
    if (typed_access != NULL) {
      listing_navigation_typed_summary(summary, sizeof(summary), typed_access);
      if (append_listing_navigation_typed_data_entry(navigation, stmt, row_index, section_index, row_kind,
          summary[0] != '\0' ? summary : match_text, match_text, 0U) != 0)
        return -1;
    }
    for (access_index = 0U; access_index < section->recovered_platform_unresolved_typed_access_count;
        ++access_index) {
      const M68kRecoveredPlatformUnresolvedTypedAccessIR *access =
        &section->recovered_platform_unresolved_typed_accesses[access_index];
      if (access->offset != stmt->offset) continue;
      listing_navigation_unresolved_summary(summary, sizeof(summary), access);
      if (navigation->typed_gaps_count++ != 0U && json_builder_append(&navigation->typed_gaps, ",") != 0)
        return -1;
      if (append_listing_navigation_unresolved_entry(&navigation->typed_gaps, stmt, row_index, section_index,
          row_kind, summary, match_text, access) != 0)
        return -1;
    }
    if (listing_stmt_has_runtime_address_refs(stmt, section, comment, 0)) {
      if (navigation->relocations_count++ != 0U && json_builder_append(&navigation->relocations, ",") != 0)
        return -1;
      if (append_listing_navigation_entry(&navigation->relocations, stmt, row_index, section_index, row_kind,
          match_text, match_text, 0U) != 0)
        return -1;
    }
    if (listing_navigation_call_is_target(section, stmt->offset, call)) {
      if (navigation->api_calls_count++ != 0U && json_builder_append(&navigation->api_calls, ",") != 0)
        return -1;
      if (append_listing_navigation_api_call_entry(&navigation->api_calls, stmt, row_index, section_index, row_kind,
          match_text, call) != 0)
        return -1;
    }
  } else if (stmt != NULL && stmt->kind != M68K_STATEMENT_INSTRUCTION && row_kind_id != LISTING_ROW_KIND_LABEL) {
    const M68kOrphanCodeSignalIR *orphan_signal = section != NULL
      ? listing_navigation_orphan_signal_at(section, stmt->offset)
      : NULL;
    const M68kAnalysisStructuredDataItem *structured_item =
      listing_structured_data_item_at_offset(navigation->analysis_policy, section_index, stmt->offset);
    const char *data_class = listing_statement_allows_data_class(stmt)
      ? listing_row_data_class(structured_item, plan_data_class, plan_data_class_flags)
      : NULL;
    uint32_t data_class_flags = listing_statement_allows_data_class(stmt)
      ? listing_row_data_class_flags(structured_item, plan_data_class, plan_data_class_flags)
      : 0U;
    if (listing_structured_data_item_has_json(structured_item) || (comment != NULL && comment[0] != '\0') ||
        data_class != NULL) {
      const char *field = structured_item != NULL && structured_item->field_name[0] != '\0'
        ? structured_item->field_name
        : NULL;
      const char *data_summary = comment != NULL && comment[0] != '\0' ? comment :
        (data_class != NULL ? data_class : (field != NULL ? field : row_kind));
      if (append_listing_navigation_typed_data_entry(navigation, stmt, row_index, section_index, row_kind,
          data_summary, match_text, data_class_flags) != 0)
        return -1;
    }
    if (orphan_signal != NULL) {
      if (navigation->orphan_code_count++ != 0U && json_builder_append(&navigation->orphan_code, ",") != 0)
        return -1;
      if (append_listing_navigation_orphan_code_entry(&navigation->orphan_code, stmt, row_index, section_index,
          row_kind, match_text, orphan_signal) != 0)
        return -1;
    }
  }
  if (stmt != NULL && comment != NULL && comment[0] != '\0') {
    if (navigation->comments_count++ != 0U && json_builder_append(&navigation->comments, ",") != 0) return -1;
    if (append_listing_navigation_entry(&navigation->comments, stmt, row_index, section_index, row_kind, comment,
        match_text, 0U) != 0)
      return -1;
  }
  return 0;
}

static int append_listing_navigation_label_ref_json(JsonBuilder *builder, const ListingNavigationLabelRef *ref) {
  if (json_builder_appendf(builder, "{\"addr\":%u,\"row_index\":%u,\"summary\":",
        (unsigned)ref->addr, (unsigned)ref->row_index) != 0)
    return -1;
  if (json_builder_append_json_string(builder, ref->summary) != 0) return -1;
  if (json_builder_append(builder, ",\"match_text\":") != 0) return -1;
  if (json_builder_append_json_string(builder, ref->match_text) != 0) return -1;
  if (json_builder_append(builder, ",\"stable_key\":") != 0) return -1;
  if (json_builder_append_json_string(builder, ref->stable_key) != 0) return -1;
  if (ref->section_index >= 0 &&
      json_builder_appendf(builder, ",\"hunk_index\":%d,\"section_index\":%d", ref->section_index,
        ref->section_index) != 0)
    return -1;
  if (json_builder_append(builder, ",\"symbol\":") != 0) return -1;
  if (json_builder_append_json_string(builder, ref->symbol) != 0) return -1;
  if (json_builder_appendf(builder, ",\"access_kind\":%u,\"access\":", (unsigned)ref->access_kind) != 0)
    return -1;
  if (json_builder_append_json_string(builder, listing_label_access_name(ref->access_kind)) != 0) return -1;
  return json_builder_append(builder, "}");
}

static int append_listing_navigation_labels_json(JsonBuilder *builder, const ListingNavigationLabelBuilder *labels) {
  size_t def_index;
  int emitted_def = 0;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (labels == NULL) return json_builder_append(builder, "]");
  for (def_index = 0U; def_index < labels->ref_count; ++def_index) {
    const ListingNavigationLabelRef *def = &labels->refs[def_index];
    size_t ref_index;
    size_t ref_count = 0U;
    size_t reference_count = 0U;
    if (def->access_kind != LISTING_LABEL_ACCESS_DEFINITION) continue;
    for (ref_index = 0U; ref_index < labels->ref_count; ++ref_index)
      if (strcmp(labels->refs[ref_index].symbol, def->symbol) == 0 &&
          (labels->refs[ref_index].access_kind == LISTING_LABEL_ACCESS_DEFINITION ||
            labels->refs[ref_index].access_kind == LISTING_LABEL_ACCESS_REFERENCE)) {
        ++ref_count;
        if (labels->refs[ref_index].access_kind == LISTING_LABEL_ACCESS_REFERENCE) ++reference_count;
      }
    if (emitted_def && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_appendf(builder, "{\"addr\":%u,\"row_index\":%u,\"summary\":",
          (unsigned)def->addr, (unsigned)def->row_index) != 0)
      return -1;
    if (json_builder_append_json_string(builder, def->summary) != 0) return -1;
    if (json_builder_append(builder, ",\"match_text\":") != 0) return -1;
    if (json_builder_append_json_string(builder, def->match_text) != 0) return -1;
    if (json_builder_append(builder, ",\"stable_key\":") != 0) return -1;
    if (json_builder_append_json_string(builder, def->stable_key) != 0) return -1;
    if (def->section_index >= 0 &&
        json_builder_appendf(builder, ",\"hunk_index\":%d,\"section_index\":%d", def->section_index,
          def->section_index) != 0)
      return -1;
    if (json_builder_append(builder, ",\"symbol\":") != 0) return -1;
    if (json_builder_append_json_string(builder, def->symbol) != 0) return -1;
    if (json_builder_appendf(builder,
          ",\"ref_count\":%u,\"access_counts\":{\"definition\":1",
          (unsigned)ref_count) != 0)
      return -1;
    if (reference_count != 0U && json_builder_appendf(builder, ",\"reference\":%u", (unsigned)reference_count) != 0)
      return -1;
    if (json_builder_append(builder, "},\"refs\":[") != 0) return -1;
    {
      int emitted_ref = 0;
      for (ref_index = 0U; ref_index < labels->ref_count; ++ref_index) {
        const ListingNavigationLabelRef *ref = &labels->refs[ref_index];
        if (strcmp(ref->symbol, def->symbol) != 0) continue;
        if (ref->access_kind == LISTING_LABEL_ACCESS_REFERENCE &&
            !listing_navigation_has_label_definition(labels, ref->symbol))
          continue;
        if (ref->access_kind != LISTING_LABEL_ACCESS_DEFINITION &&
            ref->access_kind != LISTING_LABEL_ACCESS_REFERENCE)
          continue;
        if (emitted_ref && json_builder_append(builder, ",") != 0) return -1;
        if (append_listing_navigation_label_ref_json(builder, ref) != 0) return -1;
        emitted_ref = 1;
      }
    }
    if (json_builder_append(builder, "]}") != 0) return -1;
    emitted_def = 1;
  }
  return json_builder_append(builder, "]");
}

static int append_listing_navigation_app_slot_ref_json(JsonBuilder *builder, const ListingAppSlotRefRecord *ref) {
  char base_reg[4];
  if (ref == NULL) return -1;
  listing_register_name(base_reg, sizeof(base_reg), ref->base_reg);
  if (json_builder_appendf(builder, "{\"addr\":%u,\"row_index\":%u,\"summary\":",
        (unsigned)ref->addr, (unsigned)ref->row_index) != 0)
    return -1;
  if (json_builder_append_json_string(builder, ref->symbol) != 0) return -1;
  if (json_builder_append(builder, ",\"match_text\":") != 0) return -1;
  if (json_builder_append_json_string(builder, ref->symbol) != 0) return -1;
  if (json_builder_append(builder, ",\"stable_key\":") != 0) return -1;
  if (json_builder_append_json_string(builder, ref->stable_key) != 0) return -1;
  if (ref->section_index >= 0 &&
      json_builder_appendf(builder, ",\"hunk_index\":%d,\"section_index\":%d", ref->section_index,
        ref->section_index) != 0)
    return -1;
  if (json_builder_append(builder, ",\"symbol\":") != 0) return -1;
  if (json_builder_append_json_string(builder, ref->symbol) != 0) return -1;
  if (json_builder_appendf(builder, ",\"displacement\":%d,\"base_register\":", (int)ref->displacement) != 0)
    return -1;
  if (json_builder_append_json_string(builder, base_reg) != 0) return -1;
  if (json_builder_appendf(builder, ",\"operand_index\":%u,\"access\":", (unsigned)ref->operand_index) != 0)
    return -1;
  if (json_builder_append_json_string(builder, app_slot_access_kind_name(ref->access_kind)) != 0) return -1;
  return json_builder_append(builder, "}");
}

static int append_listing_navigation_app_slots_json(JsonBuilder *builder,
    const ListingAppSlotAnalysisBuilder *analysis) {
  ListingAppSlotSummary *summaries;
  size_t summary_count = 0U;
  size_t summary_index;
  summaries = listing_app_slot_build_summaries(analysis, &summary_count);
  if (json_builder_append(builder, "[") != 0) return -1;
  for (summary_index = 0U; summary_index < summary_count; ++summary_index) {
    const ListingAppSlotSummary *summary = &summaries[summary_index];
    size_t ref_index;
    int emitted_ref = 0;
    if (summary_index != 0U && json_builder_append(builder, ",") != 0) return -1;
    if (json_builder_append(builder, "{\"symbol\":") != 0) return -1;
    if (json_builder_append_json_string(builder, summary->symbol) != 0) return -1;
    if (json_builder_append(builder, ",\"summary\":") != 0) return -1;
    if (json_builder_append_json_string(builder, summary->symbol) != 0) return -1;
    if (json_builder_append(builder, ",\"match_text\":") != 0) return -1;
    if (json_builder_append_json_string(builder, summary->symbol) != 0) return -1;
    if (json_builder_appendf(builder, ",\"displacement\":%d,\"ref_count\":%u,\"access_counts\":",
        (int)summary->displacement, (unsigned)summary->ref_count) != 0) return -1;
    if (append_listing_count_object(builder, "read", summary->access_read, "write", summary->access_write,
        "read-write", summary->access_read_write, "address", summary->access_address) != 0)
      return -1;
    if (json_builder_append(builder, ",\"refs\":[") != 0) return -1;
    if (analysis != NULL) {
      for (ref_index = 0U; ref_index < analysis->ref_count; ++ref_index) {
        const ListingAppSlotRefRecord *ref = &analysis->refs[ref_index];
        if (strcmp(ref->symbol, summary->symbol) != 0) continue;
        if (emitted_ref && json_builder_append(builder, ",") != 0) return -1;
        if (append_listing_navigation_app_slot_ref_json(builder, ref) != 0) return -1;
        emitted_ref = 1;
      }
    }
    if (json_builder_append(builder, "],\"base_registers\":") != 0) return -1;
    if (append_listing_app_slot_base_registers(builder, summary->base_regs) != 0) return -1;
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

static void listing_app_slot_field_path_label(char *out, size_t out_size, const char *struct_name,
    const AmigaOsResolvedStructFieldInfo *field) {
  size_t index;
  if (out == NULL || out_size == 0U) return;
  listing_copy_text(out, out_size, struct_name != NULL ? struct_name : "");
  if (field == NULL) return;
  for (index = 0U; index < field->path_count; ++index) {
    const char *field_name = amiga_os_name(8U, field->path_field_ids[index]);
    size_t used;
    if (field_name == NULL || field_name[0] == '\0') continue;
    used = strlen(out);
    if (used + 1U >= out_size) return;
    snprintf(out + used, out_size - used, ".%s", field_name);
  }
}

static int append_listing_app_slot_region_navigation_json(JsonBuilder *builder,
    const ListingAppSlotAnalysisBuilder *analysis) {
  size_t index;
  int emitted = 0;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (analysis == NULL) return json_builder_append(builder, "]");
  for (index = 0U; index < analysis->region_count; ++index) {
    const ListingAppSlotTypedRegion *region = &analysis->regions[index];
    const ListingAppSlotEvidence *evidence = region->evidence_count != 0U ? &region->evidence[0] : NULL;
    ListingAppSlotFieldRefSummary *fields;
    ArenaMark mark = arena_mark(analysis->arena);
    size_t field_count = 0U;
    size_t field_index;
    int emitted_field_path = 0;
    char summary[192];
    fields = listing_app_slot_build_field_refs(analysis, region, &field_count);
    snprintf(summary, sizeof(summary), "%s: %s $%04X-$%04X", region->symbol, region->struct_name,
      (unsigned)(uint16_t)region->offset, (unsigned)(uint16_t)region->end);
    if (emitted && json_builder_append(builder, ",") != 0) {
      arena_rewind(analysis->arena, mark);
      return -1;
    }
    if (json_builder_append(builder, "{\"summary\":") != 0 ||
        json_builder_append_json_string(builder, summary) != 0 ||
        json_builder_append(builder, ",\"match_text\":") != 0 ||
        json_builder_append_json_string(builder, region->symbol) != 0 ||
        json_builder_append(builder, ",\"symbol\":") != 0 ||
        json_builder_append_json_string(builder, region->symbol) != 0 ||
        json_builder_appendf(builder,
          ",\"offset\":%d,\"end\":%d,\"size\":%d,\"source\":\"platform_api_arg\","
          "\"confidence\":\"tool-inferred\",\"struct_name\":",
          (int)region->offset, (int)region->end, (int)region->size) != 0 ||
        json_builder_append_json_string(builder, region->struct_name) != 0 ||
        json_builder_appendf(builder, ",\"field_ref_count\":%u,\"field_paths\":[", (unsigned)field_count) != 0) {
      arena_rewind(analysis->arena, mark);
      return -1;
    }
    for (field_index = 0U; field_index < field_count; ++field_index) {
      const ListingAppSlotFieldRefSummary *field = &fields[field_index];
      char field_path[256];
      if (!field->has_field) continue;
      listing_app_slot_field_path_label(field_path, sizeof(field_path), region->struct_name, &field->field);
      if (emitted_field_path && json_builder_append(builder, ",") != 0) {
        arena_rewind(analysis->arena, mark);
        return -1;
      }
      if (json_builder_append_json_string(builder, field_path) != 0) {
        arena_rewind(analysis->arena, mark);
        return -1;
      }
      emitted_field_path = 1;
    }
    if (json_builder_append(builder, "]") != 0) {
      arena_rewind(analysis->arena, mark);
      return -1;
    }
    if (evidence != NULL &&
        json_builder_appendf(builder, ",\"row_index\":%u,\"addr\":%u,\"hunk_index\":%d",
          (unsigned)evidence->row_index, (unsigned)evidence->addr, evidence->section_index) != 0) {
      arena_rewind(analysis->arena, mark);
      return -1;
    }
    if (evidence != NULL && evidence->stable_key[0] != '\0') {
      if (json_builder_append(builder, ",\"stable_key\":") != 0 ||
          json_builder_append_json_string(builder, evidence->stable_key) != 0) {
        arena_rewind(analysis->arena, mark);
        return -1;
      }
    }
    if (json_builder_append(builder, "}") != 0) {
      arena_rewind(analysis->arena, mark);
      return -1;
    }
    arena_rewind(analysis->arena, mark);
    emitted = 1;
  }
  return json_builder_append(builder, "]");
}

static int append_listing_app_slot_gap_navigation_json(JsonBuilder *builder,
    const ListingAppSlotInterval *intervals, size_t interval_count) {
  size_t index;
  int emitted = 0;
  int16_t current_end;
  const char *current_id;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (interval_count == 0U) return json_builder_append(builder, "]");
  current_end = intervals[0].end;
  current_id = intervals[0].id;
  for (index = 1U; index < interval_count; ++index) {
    if (intervals[index].offset > current_end) {
      char summary[96];
      snprintf(summary, sizeof(summary), "Gap $%04X-$%04X (%d bytes)",
        (unsigned)(uint16_t)current_end, (unsigned)(uint16_t)intervals[index].offset,
        (int)(intervals[index].offset - current_end));
      if (emitted && json_builder_append(builder, ",") != 0) return -1;
      if (json_builder_append(builder, "{\"summary\":") != 0 ||
          json_builder_append_json_string(builder, summary) != 0 ||
          json_builder_append(builder, ",\"match_text\":\"\",\"navigable\":false") != 0 ||
          json_builder_appendf(builder, ",\"start\":%d,\"end\":%d,\"size\":%d,\"after\":",
            (int)current_end, (int)intervals[index].offset, (int)(intervals[index].offset - current_end)) != 0 ||
          json_builder_append_json_string(builder, current_id) != 0 ||
          json_builder_append(builder, ",\"before\":") != 0 ||
          json_builder_append_json_string(builder, intervals[index].id) != 0 ||
          json_builder_append(builder, ",\"coverage\":\"unknown_app_slot_space\"}") != 0)
        return -1;
      emitted = 1;
    }
    if (intervals[index].end > current_end) {
      current_end = intervals[index].end;
      current_id = intervals[index].id;
    }
  }
  return json_builder_append(builder, "]");
}

static int append_listing_app_slot_field_gap_navigation_entry(JsonBuilder *builder,
    const ListingAppSlotTypedRegion *region, int16_t start, int16_t end) {
  AmigaOsResolvedStructFieldInfo resolved;
  int has_field;
  char summary[192];
  char match_text[192];
  if (region == NULL || start >= end) return -1;
  has_field = amiga_os_resolve_struct_field_by_struct_id(region->struct_id, start, 1, &resolved);
  match_text[0] = '\0';
  if (has_field) {
    const char *field_name = amiga_os_name(8U, resolved.field_id);
    snprintf(match_text, sizeof(match_text), "%s.%s", region->struct_name, field_name != NULL ? field_name : "");
  }
  snprintf(summary, sizeof(summary), "Field gap $%04X-$%04X (%d bytes) %s",
    (unsigned)(uint16_t)(region->offset + start), (unsigned)(uint16_t)(region->offset + end),
    (int)(end - start), match_text[0] != '\0' ? match_text : (has_field ? "known_struct_field" : "unknown_struct_area"));
  if (json_builder_append(builder, "{\"summary\":") != 0 ||
      json_builder_append_json_string(builder, summary) != 0 ||
      json_builder_append(builder, ",\"match_text\":") != 0 ||
      json_builder_append_json_string(builder, match_text) != 0 ||
      json_builder_append(builder, ",\"navigable\":false") != 0 ||
      json_builder_appendf(builder, ",\"start\":%d,\"end\":%d,\"size\":%d,\"coverage\":",
        (int)(region->offset + start), (int)(region->offset + end), (int)(end - start)) != 0 ||
      json_builder_append_json_string(builder, has_field ? "known_struct_field" : "unknown_struct_area") != 0 ||
      json_builder_append(builder, ",\"field_path\":") != 0)
    return -1;
  if (has_field) {
    if (append_listing_resolved_field_path_json(builder, &resolved) != 0) return -1;
  } else if (json_builder_append(builder, "[]") != 0) return -1;
  if (json_builder_append(builder, ",\"region_id\":") != 0 ||
      json_builder_append_json_string(builder, region->id) != 0 ||
      json_builder_append(builder, ",\"symbol\":") != 0 ||
      json_builder_append_json_string(builder, region->symbol) != 0 ||
      json_builder_append(builder, ",\"struct_name\":") != 0 ||
      json_builder_append_json_string(builder, region->struct_name) != 0 ||
      json_builder_append(builder, "}") != 0)
    return -1;
  return 0;
}

static int append_listing_app_slot_field_gap_navigation_segments(JsonBuilder *builder,
    const ListingAppSlotTypedRegion *region, int16_t start, int16_t end, int *io_emitted) {
  int16_t cursor = start;
  if (region == NULL || io_emitted == NULL || start > end) return -1;
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
    if (append_listing_app_slot_field_gap_navigation_entry(builder, region, cursor, segment_end) != 0) return -1;
    *io_emitted = 1;
    cursor = segment_end;
  }
  return 0;
}

static int append_listing_app_slot_field_gap_navigation_json(JsonBuilder *builder,
    const ListingAppSlotAnalysisBuilder *analysis) {
  size_t region_index;
  int emitted = 0;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (analysis == NULL) return json_builder_append(builder, "]");
  for (region_index = 0U; region_index < analysis->region_count; ++region_index) {
    const ListingAppSlotTypedRegion *region = &analysis->regions[region_index];
    ListingAppSlotFieldRefSummary *fields;
    ArenaMark mark = arena_mark(analysis->arena);
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
      if (start > cursor &&
          append_listing_app_slot_field_gap_navigation_segments(builder, region, cursor, start, &emitted) != 0) {
        arena_rewind(analysis->arena, mark);
        return -1;
      }
      if (end > cursor) cursor = end;
    }
    if (cursor < region->size && interval_count != 0U &&
        append_listing_app_slot_field_gap_navigation_segments(builder, region, cursor, region->size,
          &emitted) != 0) {
      arena_rewind(analysis->arena, mark);
      return -1;
    }
    arena_rewind(analysis->arena, mark);
  }
  return json_builder_append(builder, "]");
}

static int append_listing_app_slot_suggestion_navigation_json(JsonBuilder *builder,
    const ListingAppSlotAnalysisBuilder *analysis) {
  size_t index;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (analysis == NULL) return json_builder_append(builder, "]");
  for (index = 0U; index < analysis->region_count; ++index) {
    const ListingAppSlotTypedRegion *region = &analysis->regions[index];
    const ListingAppSlotEvidence *evidence = region->evidence_count != 0U ? &region->evidence[0] : NULL;
    char summary[192];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    snprintf(summary, sizeof(summary), "%s at app+0x%x matches %s from platform API usage",
      region->symbol, (unsigned)(uint16_t)region->offset, region->struct_name);
    if (json_builder_append(builder, "{\"summary\":") != 0 ||
        json_builder_append_json_string(builder, summary) != 0 ||
        json_builder_append(builder, ",\"match_text\":") != 0 ||
        json_builder_append_json_string(builder, region->symbol) != 0 ||
        json_builder_append(builder, ",\"symbol\":") != 0 ||
        json_builder_append_json_string(builder, region->symbol) != 0 ||
        json_builder_appendf(builder, ",\"offset\":%d,\"size\":%d,\"struct_name\":",
          (int)region->offset, (int)region->size) != 0 ||
        json_builder_append_json_string(builder, region->struct_name) != 0 ||
        json_builder_append(builder, ",\"action\":\"add_target_metadata\",\"confidence\":\"tool-inferred\","
          "\"metadata\":{\"offset\":") != 0 ||
        json_builder_appendf(builder, "%d,\"size\":%d,\"symbol\":", (int)region->offset, (int)region->size) != 0 ||
        json_builder_append_json_string(builder, region->symbol) != 0 ||
        json_builder_append(builder, ",\"storage_kind\":\"struct_instance\","
          "\"semantic_type\":\"platform_api_buffer\",\"struct_name\":") != 0 ||
        json_builder_append_json_string(builder, region->struct_name) != 0 ||
        json_builder_append(builder, ",\"pointer_struct\":null,\"seed_origin\":\"auto_analysis\","
          "\"review_status\":\"suggested\"}") != 0)
      return -1;
    if (evidence != NULL &&
        json_builder_appendf(builder, ",\"row_index\":%u,\"addr\":%u,\"hunk_index\":%d",
          (unsigned)evidence->row_index, (unsigned)evidence->addr, evidence->section_index) != 0)
      return -1;
    if (evidence != NULL && evidence->stable_key[0] != '\0') {
      if (json_builder_append(builder, ",\"stable_key\":") != 0 ||
          json_builder_append_json_string(builder, evidence->stable_key) != 0)
        return -1;
    }
    if (json_builder_append(builder, "}") != 0) return -1;
  }
  return json_builder_append(builder, "]");
}

static int append_listing_app_slot_api_arg_navigation_json(JsonBuilder *builder,
    const ListingAppSlotAnalysisBuilder *analysis) {
  size_t index;
  if (json_builder_append(builder, "[") != 0) return -1;
  if (analysis == NULL) return json_builder_append(builder, "]");
  for (index = 0U; index < analysis->untyped_api_arg_count; ++index) {
    const ListingAppSlotApiArgCandidate *candidate = &analysis->untyped_api_args[index];
    const ListingAppSlotEvidence *evidence = &candidate->evidence;
    char summary[192];
    if (index != 0U && json_builder_append(builder, ",") != 0) return -1;
    snprintf(summary, sizeof(summary), "%s -> %s %s %s (%s)", candidate->symbol, evidence->function,
      evidence->input_name, evidence->reg, candidate->reason);
    if (json_builder_append(builder, "{\"summary\":") != 0 ||
        json_builder_append_json_string(builder, summary) != 0 ||
        json_builder_append(builder, ",\"match_text\":") != 0 ||
        json_builder_append_json_string(builder, candidate->symbol) != 0 ||
        json_builder_append(builder, ",\"symbol\":") != 0 ||
        json_builder_append_json_string(builder, candidate->symbol) != 0 ||
        json_builder_appendf(builder, ",\"offset\":%d,\"displacement\":%d,\"function\":",
          (int)candidate->displacement, (int)candidate->displacement) != 0 ||
        json_builder_append_json_string(builder, evidence->function) != 0 ||
        json_builder_append(builder, ",\"input_name\":") != 0 ||
        json_builder_append_json_string(builder, evidence->input_name) != 0 ||
        json_builder_append(builder, ",\"register\":") != 0 ||
        json_builder_append_json_string(builder, evidence->reg) != 0 ||
        json_builder_append(builder, ",\"reason\":") != 0 ||
        json_builder_append_json_string(builder, candidate->reason) != 0 ||
        json_builder_append(builder, ",\"type_name\":") != 0 ||
        json_builder_append_nullable_string(builder, candidate->type_name[0] != '\0' ? candidate->type_name : NULL) != 0 ||
        json_builder_appendf(builder,
          ",\"row_index\":%u,\"addr\":%u,\"hunk_index\":%d,\"source_row_index\":%u,"
          "\"source_flow_row_index\":%u,\"stable_key\":",
          (unsigned)evidence->row_index, (unsigned)evidence->addr, evidence->section_index,
          (unsigned)evidence->source_row_index, (unsigned)evidence->source_flow_row_index) != 0 ||
        json_builder_append_json_string(builder, evidence->stable_key) != 0 ||
        json_builder_append(builder, ",\"source_stable_key\":") != 0 ||
        json_builder_append_json_string(builder, evidence->source_stable_key) != 0 ||
        json_builder_append(builder, "}") != 0)
      return -1;
  }
  return json_builder_append(builder, "]");
}

static int listing_navigation_finish_group(JsonBuilder *builder) {
  if (json_builder_append(builder, "]") != 0) return -1;
  return 0;
}

static int append_listing_navigation_groups_json(JsonBuilder *builder, ListingNavigationJsonContext *navigation) {
  ListingAppSlotSummary *summaries = NULL;
  ListingAppSlotInterval *intervals = NULL;
  size_t summary_count = 0U;
  size_t interval_count = 0U;
  ListingAppSlotAnalysisBuilder *app_slot_analysis;
  ArenaMark app_slot_mark;
  if (navigation == NULL) return -1;
  app_slot_analysis = &navigation->app_slot_analysis;
  app_slot_mark = arena_mark(app_slot_analysis->arena);
  if (app_slot_analysis->enabled) {
    qsort(app_slot_analysis->regions, app_slot_analysis->region_count, sizeof(*app_slot_analysis->regions),
      listing_app_slot_region_compare);
    summaries = listing_app_slot_build_summaries(app_slot_analysis, &summary_count);
    intervals = listing_app_slot_build_intervals(app_slot_analysis, summaries, summary_count, &interval_count);
  }
  if (listing_navigation_finish_group(&navigation->typed_data) != 0 ||
      listing_navigation_finish_group(&navigation->typed_gaps) != 0 ||
      listing_navigation_finish_group(&navigation->relocations) != 0 ||
      listing_navigation_finish_group(&navigation->api_calls) != 0 ||
      listing_navigation_finish_group(&navigation->runtime_views) != 0 ||
      listing_navigation_finish_group(&navigation->orphan_code) != 0 ||
      listing_navigation_finish_group(&navigation->comments) != 0)
    goto fail;
  if (json_builder_append(builder, "\"repro-issues\":[],\"typed-data\":") != 0 ||
      json_builder_append_builder(builder, &navigation->typed_data) != 0 ||
      json_builder_append(builder, ",\"typed-gaps\":") != 0 ||
      json_builder_append_builder(builder, &navigation->typed_gaps) != 0 ||
      json_builder_append(builder, ",\"relocations\":") != 0 ||
      json_builder_append_builder(builder, &navigation->relocations) != 0 ||
      json_builder_append(builder, ",\"api-calls\":") != 0 ||
      json_builder_append_builder(builder, &navigation->api_calls) != 0 ||
      json_builder_append(builder, ",\"runtime-views\":") != 0 ||
      json_builder_append_builder(builder, &navigation->runtime_views) != 0 ||
      json_builder_append(builder, ",\"orphan-code\":") != 0 ||
      json_builder_append_builder(builder, &navigation->orphan_code) != 0 ||
      json_builder_append(builder, ",\"app-slots\":") != 0 ||
      append_listing_navigation_app_slots_json(builder, &navigation->app_slot_analysis) != 0 ||
      json_builder_append(builder, ",\"app-slot-regions\":") != 0 ||
      append_listing_app_slot_region_navigation_json(builder, &navigation->app_slot_analysis) != 0 ||
      json_builder_append(builder, ",\"app-slot-gaps\":") != 0 ||
      append_listing_app_slot_gap_navigation_json(builder, intervals, interval_count) != 0 ||
      json_builder_append(builder, ",\"app-slot-field-gaps\":") != 0 ||
      append_listing_app_slot_field_gap_navigation_json(builder, &navigation->app_slot_analysis) != 0 ||
      json_builder_append(builder, ",\"app-slot-suggestions\":") != 0 ||
      append_listing_app_slot_suggestion_navigation_json(builder, &navigation->app_slot_analysis) != 0 ||
      json_builder_append(builder, ",\"app-slot-api-args\":") != 0 ||
      append_listing_app_slot_api_arg_navigation_json(builder, &navigation->app_slot_analysis) != 0 ||
      json_builder_append(builder, ",\"labels\":") != 0 ||
      append_listing_navigation_labels_json(builder, &navigation->labels) != 0 ||
      json_builder_append(builder, ",\"comments\":") != 0 ||
      json_builder_append_builder(builder, &navigation->comments) != 0)
    goto fail;
  arena_rewind(app_slot_analysis->arena, app_slot_mark);
  return 0;

fail:
  arena_rewind(app_slot_analysis->arena, app_slot_mark);
  return -1;
}

int source_file_listing_navigation_from_render_plan_append_json(JsonBuilder *builder,
    const M68kSourceFileIR *source_file,
    const M68kRenderPlan *render_plan, uint8_t platform_backend_kind, const M68kAnalysisPolicy *analysis_policy,
    const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation, int include_source_only_rows,
    M68kDiagSink diagnostics) {
  ListingSourceHeaderRows header_rows = {0};
  ListingNavigationJsonContext navigation;
  ListingRenderPlanJsonContext context;
  memset(&navigation, 0, sizeof(navigation));
  memset(&context, 0, sizeof(context));
  if (builder == NULL || render_plan == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, "bad arguments");
    return -1;
  }
  if (listing_source_header_rows_init(&header_rows) != 0) goto oom;
  if (!include_source_only_rows && collect_listing_source_header_rows_from_plan(render_plan, &header_rows) != 0)
    goto oom;
  if (source_file != NULL) platform_backend_kind = source_file->platform_backend_kind;
  if (listing_navigation_init(&navigation, platform_backend_kind, source_analysis, analysis_policy) != 0) goto oom;
  context.header_rows = &header_rows;
  context.navigation = &navigation;
  context.source_file = source_file;
  context.analysis_policy = analysis_policy;
  context.source_analysis = source_analysis;
  context.analysis_generation = analysis_generation;
  context.active_section_index = -1;
  context.emit_preamble_headers = 1;
  context.include_source_only_rows = include_source_only_rows;
  context.count_only = 1;
  if (m68k_render_plan_visit_row_lines(render_plan, 0U, render_plan->row_count,
      append_full_listing_render_plan_line, &context) != 0)
    goto oom;
  if (json_builder_append(builder, "{\"analysis_generation\":") != 0 ||
      json_builder_append_json_string(builder, analysis_generation != NULL ? analysis_generation : "full") != 0 ||
      json_builder_appendf(builder, ",\"total_rows\":%u,\"groups\":{", (unsigned)context.row_index) != 0 ||
      append_listing_navigation_groups_json(builder, &navigation) != 0 ||
      json_builder_append(builder, "},\"app_slot_analysis\":") != 0 ||
      append_listing_app_slot_analysis_json(builder, &navigation.app_slot_analysis) != 0 ||
      json_builder_append(builder, ",\"type_flow_analysis\":{}}") != 0)
    goto oom;
  listing_navigation_destroy(&navigation);
  listing_source_header_rows_destroy(&header_rows);
  return 0;

oom:
  listing_navigation_destroy(&navigation);
  listing_source_header_rows_destroy(&header_rows);
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
  return -1;
}

int source_file_listing_row_index_from_render_plan(const M68kSourceFileIR *source_file,
    const M68kRenderPlan *render_plan, uint8_t platform_backend_kind, const M68kAnalysisPolicy *analysis_policy,
    const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation, int include_source_only_rows,
    size_t block_size, Arena *arena, PlatformListingRowIndex *out_index, M68kDiagSink diagnostics) {
  ListingSourceHeaderRows header_rows = {0};
  ListingRenderPlanJsonContext index_context;
  PlatformListingRowIndexEntry *entries = NULL;
  PlatformListingRowIndexBlock *blocks = NULL;
  ArenaMark mark;
  const char *failure = "out of memory";
  size_t entry_capacity = 0U;
  size_t block_count = 0U;
  size_t index;
  memset(&index_context, 0, sizeof(index_context));
  if (out_index != NULL) memset(out_index, 0, sizeof(*out_index));
  if (render_plan == NULL || arena == NULL || out_index == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, "bad arguments");
    return -1;
  }
  mark = arena_mark(arena);
  if (block_size == 0U) block_size = 256U;
  if (listing_source_header_rows_init(&header_rows) != 0) goto oom;
  if (!include_source_only_rows) {
    if (collect_listing_source_header_rows_from_plan(render_plan, &header_rows) != 0) {
      failure = "listing row index header collection failed";
      goto oom;
    }
  }
  entry_capacity = (size_t)render_plan->total_lines;
  if (!include_source_only_rows) {
    size_t header_extra = listing_source_header_rows_extra_count(&header_rows);
    if (entry_capacity > ((size_t)-1) - header_extra) goto oom;
    entry_capacity += header_extra;
  }
  if (entry_capacity != 0U) {
    if (entry_capacity > ((size_t)-1) / sizeof(*entries)) goto oom;
    entries = (PlatformListingRowIndexEntry *)arena_alloc(arena, entry_capacity * sizeof(*entries));
    if (entries == NULL) goto oom;
    memset(entries, 0, entry_capacity * sizeof(*entries));
  }
  if (source_file != NULL) platform_backend_kind = source_file->platform_backend_kind;
  (void)platform_backend_kind;
  index_context.header_rows = &header_rows;
  index_context.render_plan = render_plan;
  index_context.source_file = source_file;
  index_context.analysis_policy = analysis_policy;
  index_context.source_analysis = source_analysis;
  index_context.analysis_generation = analysis_generation;
  index_context.active_section_index = -1;
  index_context.emit_preamble_headers = 1;
  index_context.include_source_only_rows = include_source_only_rows;
  index_context.count_only = 1;
  index_context.row_index_entries = entries;
  index_context.row_index_entry_count = entry_capacity;
  if (m68k_render_plan_visit_row_lines(render_plan, 0U, render_plan->row_count,
      append_full_listing_render_plan_line, &index_context) != 0) {
    failure = "listing row index pass failed";
    goto oom;
  }
  if (index_context.row_index > entry_capacity) {
    failure = "listing row index capacity exceeded";
    goto oom;
  }
  if (index_context.row_index != 0U) {
    block_count = (index_context.row_index + block_size - 1U) / block_size;
    if (block_count > ((size_t)-1) / sizeof(*blocks)) goto oom;
    blocks = (PlatformListingRowIndexBlock *)arena_alloc(arena, block_count * sizeof(*blocks));
    if (blocks == NULL) goto oom;
    memset(blocks, 0, block_count * sizeof(*blocks));
  }
  for (index = 0U; index < index_context.row_index; ++index) {
    size_t block_index = index / block_size;
    PlatformListingRowIndexBlock *block = &blocks[block_index];
    if (!entries[index].has_addr) continue;
    if (!block->has_addr || entries[index].addr > block->max_addr) block->max_addr = entries[index].addr;
    block->has_addr = 1U;
  }
  out_index->entries = entries;
  out_index->blocks = blocks;
  out_index->row_count = index_context.row_index;
  out_index->block_count = block_count;
  out_index->block_size = block_size;
  listing_source_header_rows_destroy(&header_rows);
  return 0;

oom:
  arena_rewind(arena, mark);
  listing_source_header_rows_destroy(&header_rows);
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, failure);
  return -1;
}

static int append_source_file_listing_window_range_from_render_plan_json(JsonBuilder *builder,
    const M68kSourceFileIR *source_file,
    const M68kRenderPlan *render_plan, uint8_t platform_backend_kind, const M68kAnalysisPolicy *analysis_policy,
    const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation, int include_source_only_rows,
    size_t total_rows, size_t safe_start, size_t end, int anchor_override_enabled, int anchor_override_has_addr,
    uint32_t anchor_override_addr, const PlatformListingRowIndex *row_index,
    M68kDiagSink diagnostics) {
  ListingSourceHeaderRows header_rows = {0};
  ListingRenderPlanJsonContext emit_context;
  const char *failure = "out of memory";
  size_t visit_first_row = 0U;
  size_t visit_row_count = render_plan != NULL ? render_plan->row_count : 0U;
  size_t display_row_base = 0U;
  int bounded_by_row_index = 0;
  int header_only_window = 0;
  memset(&emit_context, 0, sizeof(emit_context));
  if (builder == NULL || render_plan == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, "bad arguments");
    return -1;
  }
  if (listing_source_header_rows_init(&header_rows) != 0) goto oom;
  if (source_file != NULL) platform_backend_kind = source_file->platform_backend_kind;
  (void)platform_backend_kind;
  if (json_builder_appendf(builder,
        "{\"start\":%u,\"end\":%u,\"has_more_before\":%s,\"has_more_after\":%s,\"total_rows\":%u,\"rows\":[",
        (unsigned)safe_start, (unsigned)end, safe_start > 0U ? "true" : "false",
        end < total_rows ? "true" : "false", (unsigned)total_rows) != 0)
    goto oom;
  if (row_index != NULL && safe_start < end && end <= row_index->row_count &&
      row_index->entries != NULL && row_index->entries[safe_start].has_plan_row &&
      row_index->entries[end - 1U].has_plan_row) {
    size_t first_entry = safe_start;
    size_t last_entry = end - 1U;
    uint32_t first_plan_row;
    uint32_t last_plan_row;
    while (first_entry > 0U && row_index->entries[first_entry - 1U].has_plan_row &&
        row_index->entries[first_entry - 1U].plan_row_index == row_index->entries[safe_start].plan_row_index)
      --first_entry;
    first_plan_row = row_index->entries[first_entry].plan_row_index;
    last_plan_row = row_index->entries[last_entry].plan_row_index;
    if ((size_t)first_plan_row < render_plan->row_count && (size_t)last_plan_row < render_plan->row_count &&
        first_plan_row <= last_plan_row) {
      visit_first_row = first_plan_row;
      visit_row_count = (size_t)last_plan_row - (size_t)first_plan_row + 1U;
      display_row_base = first_entry;
      bounded_by_row_index = 1;
    }
  } else if (safe_start == end) {
    visit_row_count = 0U;
  }
  if (!include_source_only_rows && !bounded_by_row_index && visit_row_count != 0U) {
    size_t preamble_count;
    if (collect_listing_source_header_rows_from_plan(render_plan, &header_rows) != 0) {
      failure = "listing window header collection failed";
      goto oom;
    }
    preamble_count = listing_source_header_rows_extra_count(&header_rows);
    if (end <= preamble_count) {
      header_only_window = 1;
      visit_row_count = 0U;
    } else if (row_index != NULL && safe_start < end && end <= row_index->row_count &&
        row_index->entries != NULL && safe_start < preamble_count && preamble_count < end &&
        row_index->entries[preamble_count].has_plan_row &&
        row_index->entries[end - 1U].has_plan_row) {
      size_t first_body_entry = preamble_count;
      uint32_t first_plan_row = row_index->entries[first_body_entry].plan_row_index;
      uint32_t last_plan_row = row_index->entries[end - 1U].plan_row_index;
      if ((size_t)first_plan_row < render_plan->row_count && (size_t)last_plan_row < render_plan->row_count &&
          first_plan_row <= last_plan_row) {
        visit_first_row = first_plan_row;
        visit_row_count = (size_t)last_plan_row - (size_t)first_plan_row + 1U;
      }
    }
  }
  emit_context.builder = builder;
  emit_context.header_rows = &header_rows;
  emit_context.render_plan = render_plan;
  emit_context.source_file = source_file;
  emit_context.analysis_policy = analysis_policy;
  emit_context.source_analysis = source_analysis;
  emit_context.analysis_generation = analysis_generation;
  emit_context.active_section_index = -1;
  emit_context.emit_preamble_headers = !bounded_by_row_index;
  emit_context.include_source_only_rows = include_source_only_rows;
  emit_context.row_index = display_row_base;
  emit_context.window_enabled = 1;
  emit_context.window_start = safe_start;
  emit_context.window_end = end;
  if (header_only_window) {
    if (append_listing_source_header_rows(&emit_context) != 0) {
      failure = "listing window header emit failed";
      goto oom;
    }
  } else {
    if (m68k_render_plan_visit_row_lines(render_plan, visit_first_row, visit_row_count,
        append_full_listing_render_plan_line, &emit_context) != 0) {
      failure = "listing window emit pass failed";
      goto oom;
    }
  }
  if (json_builder_append(builder, "],\"anchor_addr\":") != 0) goto oom;
  if (anchor_override_enabled && anchor_override_has_addr) {
    if (json_builder_appendf(builder, "%u", (unsigned)anchor_override_addr) != 0) goto oom;
  } else if (anchor_override_enabled) {
    if (json_builder_append(builder, "null") != 0) goto oom;
  } else if (emit_context.has_anchor_addr) {
    if (json_builder_appendf(builder, "%u", (unsigned)emit_context.anchor_addr) != 0) goto oom;
  } else if (json_builder_append(builder, "null") != 0) goto oom;
  if (json_builder_append(builder, "}") != 0) goto oom;
  listing_source_header_rows_destroy(&header_rows);
  return 0;

oom:
  listing_source_header_rows_destroy(&header_rows);
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, failure);
  return -1;
}

int source_file_listing_window_from_render_plan_with_index_append_json(JsonBuilder *builder,
    const M68kSourceFileIR *source_file, const M68kRenderPlan *render_plan, uint8_t platform_backend_kind,
    const M68kAnalysisPolicy *analysis_policy, const M68kSourceAnalysisIR *source_analysis,
    const char *analysis_generation, int include_source_only_rows, const PlatformListingRowIndex *row_index,
    size_t start, size_t count, M68kDiagSink diagnostics) {
  size_t total_rows;
  size_t safe_start;
  size_t end;
  if (row_index == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, "bad arguments");
    return -1;
  }
  total_rows = row_index->row_count;
  if (count == 0U || total_rows == 0U) {
    safe_start = 0U;
  } else {
    size_t max_start = total_rows > count ? total_rows - count : 0U;
    safe_start = start < max_start ? start : max_start;
  }
  end = safe_start + count;
  if (end < safe_start || end > total_rows) end = total_rows;
  return append_source_file_listing_window_range_from_render_plan_json(builder, source_file, render_plan,
    platform_backend_kind, analysis_policy, source_analysis, analysis_generation, include_source_only_rows,
    total_rows, safe_start, end, 0, 0, 0U, row_index, diagnostics);
}

static size_t listing_row_index_find_anchor(const PlatformListingRowIndex *row_index, int has_addr,
    uint32_t addr) {
  size_t block_index;
  if (row_index == NULL || row_index->row_count == 0U || row_index->entries == NULL) return 0U;
  if (!has_addr) return 0U;
  for (block_index = 0U; block_index < row_index->block_count; ++block_index) {
    const PlatformListingRowIndexBlock *block = &row_index->blocks[block_index];
    size_t start;
    size_t end;
    size_t row;
    if (!block->has_addr || block->max_addr < addr) continue;
    start = block_index * row_index->block_size;
    end = start + row_index->block_size;
    if (end < start || end > row_index->row_count) end = row_index->row_count;
    for (row = start; row < end; ++row) {
      const PlatformListingRowIndexEntry *entry = &row_index->entries[row];
      if (entry->has_addr && entry->addr >= addr) return row;
    }
  }
  return row_index->row_count - 1U;
}

int source_file_listing_addr_window_from_render_plan_with_index_append_json(JsonBuilder *builder,
    const M68kSourceFileIR *source_file, const M68kRenderPlan *render_plan, uint8_t platform_backend_kind,
    const M68kAnalysisPolicy *analysis_policy, const M68kSourceAnalysisIR *source_analysis,
    const char *analysis_generation, int include_source_only_rows, const PlatformListingRowIndex *row_index,
    int has_addr, uint32_t addr, size_t before, size_t after, M68kDiagSink diagnostics) {
  size_t total_rows;
  size_t anchor_index;
  size_t safe_start;
  size_t end;
  if (render_plan == NULL || row_index == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, "bad arguments");
    return -1;
  }
  total_rows = row_index->row_count;
  anchor_index = listing_row_index_find_anchor(row_index, has_addr, addr);
  if (anchor_index >= total_rows && total_rows != 0U) anchor_index = total_rows - 1U;
  safe_start = anchor_index > before ? anchor_index - before : 0U;
  if (total_rows == 0U) {
    end = 0U;
  } else if (after > ((size_t)-1) - anchor_index - 1U) {
    end = total_rows;
  } else {
    end = anchor_index + after + 1U;
    if (end > total_rows) end = total_rows;
  }
  return append_source_file_listing_window_range_from_render_plan_json(builder, source_file, render_plan,
    platform_backend_kind, analysis_policy, source_analysis, analysis_generation, include_source_only_rows,
    total_rows, safe_start, end, 1, has_addr, addr, row_index, diagnostics);
}

int source_file_listing_source_offset_row_from_render_plan_with_index(const M68kRenderPlan *render_plan,
    const PlatformListingRowIndex *row_index, uint32_t section_index, uint32_t offset, size_t *out_row,
    int *out_found, M68kDiagSink diagnostics) {
  const M68kRenderPlanRow *plan_row;
  size_t plan_row_index;
  size_t index;
  if (out_row != NULL) *out_row = 0U;
  if (out_found != NULL) *out_found = 0;
  if (render_plan == NULL || row_index == NULL || row_index->entries == NULL || out_row == NULL ||
      out_found == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, "bad arguments");
    return -1;
  }
  plan_row = m68k_render_plan_find_row_for_source_offset(render_plan, section_index, offset);
  if (plan_row == NULL || plan_row < render_plan->rows || plan_row >= render_plan->rows + render_plan->row_count)
    return 0;
  plan_row_index = (size_t)(plan_row - render_plan->rows);
  for (index = 0U; index < row_index->row_count; ++index) {
    const PlatformListingRowIndexEntry *entry = &row_index->entries[index];
    if (entry->has_plan_row && (size_t)entry->plan_row_index == plan_row_index) {
      *out_row = index;
      *out_found = 1;
      return 0;
    }
  }
  return 0;
}

static int listing_plan_row_subline_span(const M68kRenderPlanRow *row, uint32_t wanted_subline,
    const char **out_line_start, size_t *out_line_length) {
  const char *cursor;
  uint32_t subline = 0U;
  if (out_line_start != NULL) *out_line_start = NULL;
  if (out_line_length != NULL) *out_line_length = 0U;
  if (row == NULL || row->text == NULL || out_line_start == NULL || out_line_length == NULL) return 0;
  cursor = row->text;
  while (*cursor != '\0') {
    const char *line_start = cursor;
    size_t line_length;
    while (*cursor != '\0' && *cursor != '\n') ++cursor;
    if (*cursor == '\n') ++cursor;
    line_length = (size_t)(cursor - line_start);
    if (subline == wanted_subline) {
      *out_line_start = line_start;
      *out_line_length = line_length;
      return 1;
    }
    ++subline;
  }
  return 0;
}

static int listing_row_code_matches_anchor_with_kind(const M68kStatementIR *stmt, uint8_t row_kind_id,
    const char *line_start, size_t line_length, const char *wanted) {
  char stripped[1024];
  char opcode[128];
  char operand[1024];
  char comment[512];
  char row_code[1024];
  if (line_start == NULL || wanted == NULL) return 0;
  split_listing_line(line_start, line_length, stripped, sizeof(stripped), opcode, sizeof(opcode), operand,
    sizeof(operand), comment, sizeof(comment));
  listing_navigation_row_code(row_code, sizeof(row_code), row_kind_id, stripped, opcode, operand, stmt);
  return strcmp(row_code, wanted) == 0;
}

static int listing_row_code_matches_anchor(const M68kSourceFileIR *source_file,
    const M68kAnalysisPolicy *analysis_policy, const M68kSourceAnalysisIR *source_analysis,
    const char *analysis_generation, int active_section_index, const M68kRenderPlanRow *row, uint32_t subline,
    const char *line_start, size_t line_length, const char *wanted) {
  uint8_t row_kind_id;
  const M68kStatementIR *stmt = NULL;
  M68kStatementIR plan_stmt;
  (void)analysis_generation;
  (void)analysis_policy;
  (void)active_section_index;
  if (line_start == NULL || wanted == NULL) return 0;
  m68k_ir_statement_init(&plan_stmt);
  row_kind_id = listing_row_kind_id_for_plan_row(row);
  if (listing_plan_subline_is_directive(row, subline)) {
    row_kind_id = LISTING_ROW_KIND_DIRECTIVE;
  } else {
    uint32_t label_source_offset = 0U;
    if (listing_plan_subline_is_label(row, subline, &label_source_offset, NULL, NULL)) {
      row_kind_id = LISTING_ROW_KIND_LABEL;
      plan_stmt.kind = M68K_STATEMENT_LABEL;
      plan_stmt.offset = label_source_offset;
      stmt = &plan_stmt;
    }
  }
  if (stmt == NULL && row != NULL && (row->has_statement || row->has_source_range)) {
    stmt = listing_statement_for_plan_row(source_file, row);
    if (stmt == NULL && listing_statement_from_plan_row_metadata(row, &plan_stmt)) stmt = &plan_stmt;
  }
  (void)source_analysis;
  return listing_row_code_matches_anchor_with_kind(stmt, row_kind_id, line_start, line_length, wanted);
}

static int listing_header_anchor_row(const ListingSourceHeaderRows *header_rows, const char *wanted,
    size_t *row_index, size_t *out_row) {
  int group;
  int emitted_any = 0;
  if (row_index == NULL || out_row == NULL) return -1;
  if (header_rows == NULL || wanted == NULL) return 0;
  for (group = 0; group <= 2; ++group) {
    int emitted_group = 0;
    size_t index;
    for (index = 0U; index < header_rows->count; ++index) {
      const ListingSourceHeaderRow *row = &header_rows->items[index];
      if (row->group != group) continue;
      if (emitted_any && !emitted_group) {
        ++*row_index;
      }
      if (listing_row_code_matches_anchor_with_kind(NULL, row->row_kind_id, row->line_start, row->line_length,
          wanted)) {
        *out_row = *row_index;
        return 1;
      }
      ++*row_index;
      emitted_group = 1;
      emitted_any = 1;
    }
  }
  if (emitted_any) ++*row_index;
  return 0;
}

int source_file_listing_anchor_code_row_from_render_plan_with_index(const M68kSourceFileIR *source_file,
    const M68kRenderPlan *render_plan, uint8_t platform_backend_kind, const M68kAnalysisPolicy *analysis_policy,
    const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation, int include_source_only_rows,
    const PlatformListingRowIndex *row_index, const char *anchor_code, size_t *out_row,
    M68kDiagSink diagnostics) {
  ListingSourceHeaderRows header_rows = {0};
  char wanted[1024];
  const char *failure = "out of memory";
  size_t display_row = 0U;
  size_t index;
  if (out_row != NULL) *out_row = 0U;
  if (render_plan == NULL || row_index == NULL || row_index->entries == NULL || anchor_code == NULL ||
      out_row == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, "bad arguments");
    return -1;
  }
  copy_trimmed(wanted, sizeof(wanted), anchor_code, strlen(anchor_code));
  if (wanted[0] == '\0') return 0;
  if (listing_source_header_rows_init(&header_rows) != 0) goto oom;
  if (!include_source_only_rows) {
    int header_result;
    if (collect_listing_source_header_rows_from_plan(render_plan, &header_rows) != 0) {
      failure = "listing anchor header collection failed";
      goto oom;
    }
    header_result = listing_header_anchor_row(&header_rows, wanted, &display_row, out_row);
    if (header_result < 0) goto oom;
    if (header_result > 0) {
      listing_source_header_rows_destroy(&header_rows);
      return 0;
    }
  }
  if (source_file != NULL) platform_backend_kind = source_file->platform_backend_kind;
  (void)platform_backend_kind;
  for (index = display_row; index < row_index->row_count; ++index) {
    const PlatformListingRowIndexEntry *entry = &row_index->entries[index];
    const M68kRenderPlanRow *row;
    const char *line_start = NULL;
    size_t line_length = 0U;
    if (!entry->has_plan_row || (size_t)entry->plan_row_index >= render_plan->row_count) continue;
    row = &render_plan->rows[entry->plan_row_index];
    if (!listing_plan_row_subline_span(row, entry->subline, &line_start, &line_length)) continue;
    if (listing_row_code_matches_anchor(source_file, analysis_policy, source_analysis, analysis_generation, -1,
        row, entry->subline, line_start, line_length, wanted)) {
      *out_row = index;
      break;
    }
  }
  listing_source_header_rows_destroy(&header_rows);
  return 0;

oom:
  listing_source_header_rows_destroy(&header_rows);
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, failure);
  return -1;
}
