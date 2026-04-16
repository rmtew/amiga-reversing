#ifndef M68K_BACKEND_H
#define M68K_BACKEND_H

#include <stddef.h>

#include "m68k_diagnostics.h"
#include "m68k_object.h"

typedef struct M68kBackend {
  const char *name;
  int (*read_file)(const char *path, M68kObject *out_object, M68kDiagSink diagnostics);
  int (*read_buffer)(const unsigned char *data, size_t size, M68kObject *out_object, M68kDiagSink diagnostics);
  int (*write_file)(const char *path, const M68kObject *object, M68kDiagSink diagnostics);
} M68kBackend;

extern const M68kBackend M68K_BACKEND_AMIGA_HUNK;
extern const M68kBackend M68K_BACKEND_ATARI_ST;

const M68kBackend *m68k_backend_by_name(const char *name);

#endif
