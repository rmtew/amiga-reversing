#include "m68k_object.h"

#include "platform_common.h"

#include <string.h>

static void *grow_array(M68kObject *object, void *items, size_t item_size, size_t *capacity, size_t count) {
  size_t next_capacity;
  void *grown;
  Arena *arena;
  if (object == NULL || object->arena == NULL) return NULL;
  arena = object->arena;
  if (arena == NULL) return NULL;
  if (count < *capacity) return items;
  next_capacity = (*capacity == 0) ? 4U : (*capacity * 2U);
  grown = arena_realloc_copy(arena, items, count * item_size, next_capacity * item_size);
  if (grown == NULL) return NULL;
  *capacity = next_capacity;
  return grown;
}

int m68k_object_create(M68kObject *object) {
  if (object == NULL) return -1;
  memset(object, 0, sizeof(*object));
  object->arena = arena_create(16384U);
  return object->arena != NULL ? 0 : -1;
}

void m68k_object_destroy(M68kObject *object) {
  if (object == NULL) return;
  arena_destroy(object->arena);
  memset(object, 0, sizeof(*object));
}

void *m68k_object_alloc(M68kObject *object, size_t size) {
  if (object == NULL || object->arena == NULL) return NULL;
  return arena_alloc(object->arena, size);
}

void *m68k_object_memdup(M68kObject *object, const void *data, size_t size) {
  if (object == NULL || object->arena == NULL) return NULL;
  return arena_memdup(object->arena, data, size);
}

M68kObjectAddResult m68k_object_add_section(M68kObject *object, const M68kSection *section) {
  M68kObjectAddResult result = {0};
  M68kSection copy;
  const char *name = section->name != NULL ? section->name : "";
  object->sections = (M68kSection *)grow_array(object, object->sections, sizeof(*object->sections),
    &object->section_capacity, object->section_count);
  if (object->sections == NULL) return result;
  memset(&copy, 0, sizeof(copy));
  copy = *section;
  copy.name = (char *)m68k_object_memdup(object, name, strlen(name) + 1U);
  if (copy.name == NULL && section->name != NULL) return result;
  if (section->data_size != 0U && section->data != NULL) {
    copy.data = (uint8_t *)m68k_object_memdup(object, section->data, section->data_size);
    if (copy.data == NULL) return result;
  }
  if (section->debug_size != 0U && section->debug_data != NULL) {
    copy.debug_data = (uint8_t *)m68k_object_memdup(object, section->debug_data, section->debug_size);
    if (copy.debug_data == NULL) return result;
  }
  object->sections[object->section_count] = copy;
  result.ok = 1U;
  result.index = object->section_count;
  object->section_count += 1;
  return result;
}

int m68k_object_set_section_data(M68kObject *object, size_t section_index, const uint8_t *data, uint32_t data_size) {
  uint8_t *copy = NULL;
  if (object == NULL || section_index >= object->section_count) return -1;
  if (data_size != 0U) {
    copy = (uint8_t *)m68k_object_memdup(object, data, data_size);
    if (copy == NULL) return -1;
  }
  object->sections[section_index].data = copy;
  object->sections[section_index].data_size = data_size;
  if (object->sections[section_index].size < data_size) object->sections[section_index].size = data_size;
  return 0;
}

int m68k_object_set_section_debug_data(M68kObject *object, size_t section_index, const uint8_t *data, uint32_t debug_size) {
  uint8_t *copy = NULL;
  if (object == NULL || section_index >= object->section_count) return -1;
  if (debug_size != 0U) {
    copy = (uint8_t *)m68k_object_memdup(object, data, debug_size);
    if (copy == NULL) return -1;
  }
  object->sections[section_index].debug_data = copy;
  object->sections[section_index].debug_size = debug_size;
  return 0;
}

M68kObjectAddResult m68k_object_add_symbol(M68kObject *object, const M68kSymbol *symbol) {
  M68kObjectAddResult result = {0};
  M68kSymbol copy = *symbol;
  const char *name = symbol->name != NULL ? symbol->name : "";
  object->symbols = (M68kSymbol *)grow_array(object, object->symbols, sizeof(*object->symbols), &object->symbol_capacity,
    object->symbol_count);
  if (object->symbols == NULL) return result;
  copy.name = (char *)m68k_object_memdup(object, name, strlen(name) + 1U);
  if (copy.name == NULL && symbol->name != NULL) return result;
  object->symbols[object->symbol_count] = copy;
  result.ok = 1U;
  result.index = object->symbol_count;
  object->symbol_count += 1;
  return result;
}

M68kObjectAddResult m68k_object_add_fixup(M68kObject *object, const M68kFixup *fixup) {
  M68kObjectAddResult result = {0};
  object->fixups = (M68kFixup *)grow_array(object, object->fixups, sizeof(*object->fixups), &object->fixup_capacity,
    object->fixup_count);
  if (object->fixups == NULL) return result;
  object->fixups[object->fixup_count] = *fixup;
  result.ok = 1U;
  result.index = object->fixup_count;
  object->fixup_count += 1;
  return result;
}

int m68k_object_add_platform_storage_layout(M68kObject *object, const M68kPlatformStorageLayoutIR *layout) {
  size_t index;
  if (object == NULL || layout == NULL || layout->layout_kind == M68K_PLATFORM_STORAGE_LAYOUT_NONE ||
      layout->region_kind == M68K_PLATFORM_STORAGE_REGION_NONE || layout->size == 0U || layout->base_reg >= 8U) {
    return -1;
  }
  for (index = 0U; index < object->platform_storage_layout_count; ++index) {
    const M68kPlatformStorageLayoutIR *existing = &object->platform_storage_layouts[index];
    if (existing->platform_kind == layout->platform_kind &&
        existing->layout_kind == layout->layout_kind &&
        existing->region_kind == layout->region_kind &&
        existing->base_reg == layout->base_reg &&
        existing->start == layout->start &&
        existing->size == layout->size &&
        existing->owner_resource_id == layout->owner_resource_id) {
      return 0;
    }
  }
  object->platform_storage_layouts = (M68kPlatformStorageLayoutIR *)grow_array(object,
    object->platform_storage_layouts, sizeof(*object->platform_storage_layouts),
    &object->platform_storage_layout_capacity, object->platform_storage_layout_count);
  if (object->platform_storage_layouts == NULL) return -1;
  object->platform_storage_layouts[object->platform_storage_layout_count] = *layout;
  object->platform_storage_layout_count += 1U;
  return 0;
}

void m68k_object_add_container_layout(M68kObject *object, uint16_t kind, uint16_t flags, uint32_t id, uint32_t aux) {
  M68kContainerMetadata *metadata;
  M68kContainerLayoutMetadata *item;
  if (object == NULL) return;
  metadata = &object->container_metadata;
  if (metadata->layout_count >= M68K_CONTAINER_METADATA_CAPACITY) {
    metadata->layout_overflow = 1U;
    return;
  }
  item = &metadata->layout[metadata->layout_count++];
  item->kind = kind;
  item->flags = flags;
  item->id = id;
  item->aux = aux;
}

void m68k_object_add_container_encoding(M68kObject *object, uint16_t kind, uint16_t flags, uint32_t id, uint32_t aux) {
  M68kContainerMetadata *metadata;
  M68kContainerEncodingMetadata *item;
  if (object == NULL) return;
  metadata = &object->container_metadata;
  if (metadata->encoding_count >= M68K_CONTAINER_METADATA_CAPACITY) {
    metadata->encoding_overflow = 1U;
    return;
  }
  item = &metadata->encoding[metadata->encoding_count++];
  item->kind = kind;
  item->flags = flags;
  item->id = id;
  item->aux = aux;
}

void m68k_object_mark_no_container(M68kObject *object) {
  if (object == NULL) return;
  m68k_object_add_container_layout(object, M68K_CONTAINER_LAYOUT_NO_CONTAINER, 0U, 0U, 0U);
  m68k_object_add_container_encoding(object, M68K_CONTAINER_ENCODING_NO_CONTAINER, 0U, 0U, 0U);
}
