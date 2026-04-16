#ifndef M68K_DIAGNOSTICS_H
#define M68K_DIAGNOSTICS_H

#include <stddef.h>
#include <stdint.h>

#define M68K_DIAG_MESSAGE_SIZE 160U
#define M68K_DIAG_LIST_CAPACITY 8U

typedef enum M68kDiagSeverity {
  M68K_DIAG_SEVERITY_NONE = 0,
  M68K_DIAG_SEVERITY_INFO = 1,
  M68K_DIAG_SEVERITY_WARNING = 2,
  M68K_DIAG_SEVERITY_ERROR = 3
} M68kDiagSeverity;

typedef enum M68kDiagCode {
  M68K_DIAG_CODE_NONE = 0,
  M68K_DIAG_CODE_BAD_ARGUMENT = 1,
  M68K_DIAG_CODE_DECODE_FAILED = 2,
  M68K_DIAG_CODE_RENDER_FAILED = 3,
  M68K_DIAG_CODE_SIMULATION_FAILED = 4,
  M68K_DIAG_CODE_OUT_OF_MEMORY = 5,
  M68K_DIAG_CODE_ENCODE_FAILED = 6,
  M68K_DIAG_CODE_PARSE_FAILED = 7,
  M68K_DIAG_CODE_PLATFORM_FILE_FAILED = 8,
  M68K_DIAG_CODE_PLATFORM_DISK_FAILED = 9,
  M68K_DIAG_CODE_SOURCE_FAILED = 10
} M68kDiagCode;

typedef struct M68kDiag {
  uint32_t severity;
  uint32_t code;
  char message[M68K_DIAG_MESSAGE_SIZE];
} M68kDiag;

typedef struct M68kDiagList {
  size_t count;
  size_t dropped_count;
  M68kDiag items[M68K_DIAG_LIST_CAPACITY];
} M68kDiagList;

typedef struct M68kDiagSink {
  M68kDiagList *list;
} M68kDiagSink;

M68kDiagSink m68k_diag_sink(M68kDiagList *list);
void m68k_diag_list_reset(M68kDiagList *list);
void m68k_diag_add(M68kDiagSink sink, uint32_t severity, uint32_t code, const char *message);
void m68k_diag_addf(M68kDiagSink sink, uint32_t severity, uint32_t code, const char *fmt, ...);
int m68k_diag_has_errors(const M68kDiagList *list);
const M68kDiag *m68k_diag_first_error(const M68kDiagList *list);
const char *m68k_diag_first_message(const M68kDiagList *list);

#endif
