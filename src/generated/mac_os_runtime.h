/* Generated Classic Mac OS runtime metadata from MPW includes. Do not edit directly. */
#ifndef MAC_OS_RUNTIME_H
#define MAC_OS_RUNTIME_H

#include <stddef.h>
#include <stdint.h>

typedef enum MacOsCallKind {
  MAC_OS_CALL_KIND_OPWORD = 1,
  MAC_OS_CALL_KIND_PACKAGE_MACRO = 2
} MacOsCallKind;

typedef struct MacOsRecordInfo {
  const char *name;
  uint16_t size;
  const char *source_path;
  uint32_t line;
  uint32_t line_end;
  uint16_t first_field;
  uint16_t field_count;
} MacOsRecordInfo;

typedef struct MacOsRecordFieldInfo {
  const char *record_name;
  const char *name;
  const char *type_name;
  const char *storage;
  uint16_t offset;
  uint16_t size;
  const char *source_path;
  uint32_t line;
} MacOsRecordFieldInfo;

typedef struct MacOsCallInfo {
  const char *name;
  const char *family;
  uint16_t kind;
  uint16_t opword;
  uint16_t package_word;
  const char *source_path;
  uint32_t line;
  const char *prototype;
  const char *prototype_source_path;
  uint32_t prototype_line;
  const char *parameter_register;
  const char *result_register;
} MacOsCallInfo;

#define MAC_OS_RECORD_COUNT 8u
#define MAC_OS_CALL_COUNT 5u

const MacOsRecordInfo *mac_os_find_record(const char *name);
const MacOsRecordFieldInfo *mac_os_find_record_field(const char *record_name, const char *field_name);
const MacOsCallInfo *mac_os_find_call_by_name(const char *name);
const MacOsCallInfo *mac_os_find_call_by_opword(uint16_t opword);

#endif
