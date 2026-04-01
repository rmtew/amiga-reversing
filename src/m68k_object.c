#include "m68k_object.h"

#include "platform_common.h"

#include <stdlib.h>
#include <string.h>

static void *grow_array(void *items, size_t item_size, size_t *capacity, size_t count) {
  size_t next_capacity;
  void *grown;
  if (count < *capacity) return items;
  next_capacity = (*capacity == 0) ? 4 : (*capacity * 2);
  grown = realloc(items, next_capacity * item_size);
  if (grown == NULL) return NULL;
  *capacity = next_capacity;
  return grown;
}

void m68k_object_init(M68kObject *object) {
  memset(object, 0, sizeof(*object));
}

void m68k_object_free(M68kObject *object) {
  size_t i;
  if (object == NULL) return;
  for (i = 0; i < object->section_count; ++i) {
    free(object->sections[i].name);
    free(object->sections[i].data);
    free(object->sections[i].debug_data);
  }
  for (i = 0; i < object->symbol_count; ++i) {
    free(object->symbols[i].name);
  }
  if (object->platform_data_free != NULL) {
    object->platform_data_free(object->platform_data);
  }
  free(object->sections);
  free(object->symbols);
  free(object->fixups);
  memset(object, 0, sizeof(*object));
}

int m68k_object_add_section(M68kObject *object, const M68kSection *section, size_t *out_index) {
  M68kSection copy;
  uint8_t *data_copy = NULL;
  uint8_t *debug_copy = NULL;
  object->sections = (M68kSection *)grow_array(object->sections, sizeof(*object->sections),
    &object->section_capacity, object->section_count);
  if (object->sections == NULL) return -1;
  memset(&copy, 0, sizeof(copy));
  copy = *section;
  copy.name = m68k_platform_dup_string(section->name != NULL ? section->name : "");
  if (copy.name == NULL && section->name != NULL) return -1;
  if (section->data_size != 0U && section->data != NULL) {
    data_copy = (uint8_t *)malloc(section->data_size);
    if (data_copy == NULL) {
      free(copy.name);
      return -1;
    }
    memcpy(data_copy, section->data, section->data_size);
  }
  if (section->debug_size != 0U && section->debug_data != NULL) {
    debug_copy = (uint8_t *)malloc(section->debug_size);
    if (debug_copy == NULL) {
      free(copy.name);
      free(data_copy);
      return -1;
    }
    memcpy(debug_copy, section->debug_data, section->debug_size);
  }
  copy.data = data_copy;
  copy.debug_data = debug_copy;
  object->sections[object->section_count] = copy;
  if (out_index != NULL) *out_index = object->section_count;
  object->section_count += 1;
  return 0;
}

int m68k_object_add_symbol(M68kObject *object, const M68kSymbol *symbol, size_t *out_index) {
  M68kSymbol copy = *symbol;
  object->symbols = (M68kSymbol *)grow_array(object->symbols, sizeof(*object->symbols), &object->symbol_capacity,
    object->symbol_count);
  if (object->symbols == NULL) return -1;
  copy.name = m68k_platform_dup_string(symbol->name != NULL ? symbol->name : "");
  if (copy.name == NULL && symbol->name != NULL) return -1;
  object->symbols[object->symbol_count] = copy;
  if (out_index != NULL) *out_index = object->symbol_count;
  object->symbol_count += 1;
  return 0;
}

int m68k_object_add_fixup(M68kObject *object, const M68kFixup *fixup, size_t *out_index) {
  object->fixups = (M68kFixup *)grow_array(object->fixups, sizeof(*object->fixups), &object->fixup_capacity,
    object->fixup_count);
  if (object->fixups == NULL) return -1;
  object->fixups[object->fixup_count] = *fixup;
  if (out_index != NULL) *out_index = object->fixup_count;
  object->fixup_count += 1;
  return 0;
}
