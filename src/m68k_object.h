/* Neutral M68K object model shared by platform backends. */
#ifndef M68K_OBJECT_H
#define M68K_OBJECT_H

#include <stddef.h>
#include <stdint.h>

typedef enum M68kPlatformFileKind {
  M68K_PLATFORM_FILE_UNKNOWN = 0,
  M68K_PLATFORM_FILE_EXECUTABLE = 1,
  M68K_PLATFORM_FILE_OBJECT = 2
} M68kPlatformFileKind;

typedef enum M68kSectionKind {
  M68K_SECTION_CODE = 1,
  M68K_SECTION_DATA = 2,
  M68K_SECTION_BSS = 3
} M68kSectionKind;

typedef enum M68kSymbolBinding {
  M68K_SYMBOL_LOCAL = 1,
  M68K_SYMBOL_GLOBAL = 2,
  M68K_SYMBOL_EXTERNAL = 3
} M68kSymbolBinding;

typedef enum M68kFixupKind {
  M68K_FIXUP_ABS = 1,
  M68K_FIXUP_PC_REL = 2,
  M68K_FIXUP_SECTION_REL = 3
} M68kFixupKind;

typedef enum M68kFixupWidth {
  M68K_FIXUP_WIDTH_8 = 1,
  M68K_FIXUP_WIDTH_16 = 2,
  M68K_FIXUP_WIDTH_32 = 4
} M68kFixupWidth;

typedef struct M68kSection {
  char *name;
  M68kSectionKind kind;
  uint32_t alignment;
  uint32_t flags;
  uint8_t platform_mem_type;
  uint32_t platform_mem_attrs;
  uint32_t size;
  uint8_t *data;
  uint32_t data_size;
  uint8_t *debug_data;
  uint32_t debug_size;
} M68kSection;

typedef struct M68kSymbol {
  char *name;
  M68kSymbolBinding binding;
  int defined;
  size_t section_index;
  uint32_t value;
} M68kSymbol;

typedef struct M68kFixup {
  size_t section_index;
  uint32_t offset;
  M68kFixupKind kind;
  M68kFixupWidth width;
  int32_t addend;
  size_t target_section_index;
  int has_target_section;
  size_t symbol_index;
  int has_symbol;
} M68kFixup;

typedef struct M68kObject {
  M68kPlatformFileKind platform_file_kind;
  M68kSection *sections;
  size_t section_count;
  size_t section_capacity;
  M68kSymbol *symbols;
  size_t symbol_count;
  size_t symbol_capacity;
  M68kFixup *fixups;
  size_t fixup_count;
  size_t fixup_capacity;
  void *platform_data;
  void (*platform_data_free)(void *);
} M68kObject;

void m68k_object_init(M68kObject *object);
void m68k_object_free(M68kObject *object);
int m68k_object_add_section(M68kObject *object, const M68kSection *section, size_t *out_index);
int m68k_object_add_symbol(M68kObject *object, const M68kSymbol *symbol, size_t *out_index);
int m68k_object_add_fixup(M68kObject *object, const M68kFixup *fixup, size_t *out_index);

#endif
