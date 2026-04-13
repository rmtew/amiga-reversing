/* Generated Atari ST OS runtime metadata from EmuTOS headers.
 * Sources:
 *  - resources/clone_atari_st/emutos/include/bdosbind.h
 *  - resources/clone_atari_st/emutos/include/biosbind.h
 *  - resources/clone_atari_st/emutos/include/xbiosbind.h
 *  - resources/clone_atari_st/emutos/doc/status.txt
 * Do not edit directly.
 */
#ifndef ATARI_ST_OS_RUNTIME_H
#define ATARI_ST_OS_RUNTIME_H

#include <stddef.h>
#include <stdint.h>

typedef enum AtariStOsReturnKind {
  ATARI_ST_OS_RETURN_VOID = 0,
  ATARI_ST_OS_RETURN_WORD = 1,
  ATARI_ST_OS_RETURN_LONG = 2
} AtariStOsReturnKind;

typedef struct AtariStOsCallInfo {
  const char *family_name;
  uint8_t trap_vector;
  uint16_t opcode;
  const char *function_name;
  const char *symbol_name;
  const char *source_header;
  uint8_t stack_cleanup_known;
  uint16_t stack_cleanup_bytes;
  uint8_t arg_count;
  uint8_t return_kind;
} AtariStOsCallInfo;

#define ATARI_ST_OS_CALL_COUNT 114u

const AtariStOsCallInfo *atari_st_os_find_call(uint8_t trap_vector, uint16_t opcode);
const AtariStOsCallInfo *atari_st_os_find_call_by_symbol_name(const char *symbol_name);

#endif
