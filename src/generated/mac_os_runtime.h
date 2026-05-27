/* Generated Classic Mac OS runtime metadata from MPW includes. Do not edit directly. */
#ifndef MAC_OS_RUNTIME_H
#define MAC_OS_RUNTIME_H

#include <stddef.h>
#include <stdint.h>

typedef enum MacOsCallKind {
  MAC_OS_CALL_KIND_OPWORD = 1,
  MAC_OS_CALL_KIND_PACKAGE_MACRO = 2,
  MAC_OS_CALL_KIND_TRAP_CONSTANT = 3
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

typedef struct MacOsCallParameterInfo {
  const char *call_name;
  uint16_t index;
  const char *name;
  const char *type_name;
  uint16_t pointer_depth;
  const char *direction;
} MacOsCallParameterInfo;

typedef struct MacOsCallInfo {
  const char *name;
  const char *c_name;
  const char *family;
  uint16_t kind;
  uint16_t opword;
  uint16_t package_word;
  const char *source_path;
  uint32_t line;
  const char *prototype;
  const char *prototype_source_path;
  uint32_t prototype_line;
  const char *return_type;
  uint16_t first_parameter;
  uint16_t parameter_count;
  const char *parameter_register;
  const char *result_register;
} MacOsCallInfo;

#define MAC_OS_RECORD_COUNT 8u
#define MAC_OS_CALL_COUNT 1733u

const MacOsRecordInfo *mac_os_find_record(const char *name);
const MacOsRecordFieldInfo *mac_os_find_record_field(const char *record_name, const char *field_name);
const MacOsCallInfo *mac_os_find_call_by_name(const char *name);
const MacOsCallInfo *mac_os_find_call_by_opword(uint16_t opword);
const MacOsCallParameterInfo *mac_os_call_parameter(const MacOsCallInfo *call, uint16_t parameter_index);

#endif
