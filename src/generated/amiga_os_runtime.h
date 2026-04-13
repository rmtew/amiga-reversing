/* Generated Amiga OS runtime metadata. Do not edit directly. */
#ifndef AMIGA_OS_RUNTIME_H
#define AMIGA_OS_RUNTIME_H

#include <stddef.h>
#include <stdint.h>

typedef struct AmigaOsLibraryVectorInfo {
  const char *library_name;
  const char *base_name;
  int16_t lvo;
  const char *function_name;
  const char *lvo_symbol_name;
  const char *returns_base_reg_name;
  const char *returns_base_name_reg_name;
  const char *output_reg_name;
  const char *output_struct_name;
  const char *input_a1_struct_name;
} AmigaOsLibraryVectorInfo;

const char *amiga_os_find_library_base_name(const char *library_name);
const AmigaOsLibraryVectorInfo *amiga_os_find_library_vector(const char *base_name, int16_t lvo);
const AmigaOsLibraryVectorInfo *amiga_os_find_library_vector_by_symbol_name(const char *lvo_symbol_name);

#define AMIGA_OS_LIBRARY_VECTOR_COUNT 1110u
#define AMIGA_OS_STRUCT_IO_FIELD_IO_DEVICE_OFFSET 20u

#endif
