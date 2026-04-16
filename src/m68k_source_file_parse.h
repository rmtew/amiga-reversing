#ifndef M68K_SOURCE_FILE_PARSE_H
#define M68K_SOURCE_FILE_PARSE_H

#include "m68k_diagnostics.h"
#include "m68k_source_model.h"

#include <stddef.h>

int m68k_source_file_parse(AsmSourceFile *source, const char *path, M68kDiagSink diagnostics);

#endif
