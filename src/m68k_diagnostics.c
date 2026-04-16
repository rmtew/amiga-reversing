#include "m68k_diagnostics.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>

M68kDiagSink m68k_diag_sink(M68kDiagList *list) {
  M68kDiagSink sink;
  sink.list = list;
  return sink;
}

void m68k_diag_list_reset(M68kDiagList *list) {
  if (list == NULL) return;
  memset(list, 0, sizeof(*list));
}

void m68k_diag_add(M68kDiagSink sink, uint32_t severity, uint32_t code, const char *message) {
  M68kDiag *diag;
  if (sink.list == NULL) return;
  if (sink.list->count >= M68K_DIAG_LIST_CAPACITY) {
    sink.list->dropped_count += 1U;
    return;
  }
  diag = &sink.list->items[sink.list->count++];
  memset(diag, 0, sizeof(*diag));
  diag->severity = severity;
  diag->code = code;
  if (message != NULL) snprintf(diag->message, sizeof(diag->message), "%s", message);
}

void m68k_diag_addf(M68kDiagSink sink, uint32_t severity, uint32_t code, const char *fmt, ...) {
  M68kDiag *diag;
  va_list args;
  if (sink.list == NULL) return;
  if (sink.list->count >= M68K_DIAG_LIST_CAPACITY) {
    sink.list->dropped_count += 1U;
    return;
  }
  diag = &sink.list->items[sink.list->count++];
  memset(diag, 0, sizeof(*diag));
  diag->severity = severity;
  diag->code = code;
  if (fmt == NULL) return;
  va_start(args, fmt);
  vsnprintf(diag->message, sizeof(diag->message), fmt, args);
  va_end(args);
}

int m68k_diag_has_errors(const M68kDiagList *list) {
  size_t index;
  if (list == NULL) return 0;
  for (index = 0; index < list->count; ++index)
    if (list->items[index].severity == M68K_DIAG_SEVERITY_ERROR) return 1;
  return 0;
}

const M68kDiag *m68k_diag_first_error(const M68kDiagList *list) {
  size_t index;
  if (list == NULL) return NULL;
  for (index = 0; index < list->count; ++index)
    if (list->items[index].severity == M68K_DIAG_SEVERITY_ERROR) return &list->items[index];
  return NULL;
}

const char *m68k_diag_first_message(const M68kDiagList *list) {
  const M68kDiag *diag = m68k_diag_first_error(list);
  if (diag != NULL) return diag->message;
  if (list != NULL && list->count != 0U) return list->items[0].message;
  return "";
}
