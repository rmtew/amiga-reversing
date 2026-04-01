#ifndef M68K_SOURCE_FILE_PARSE_H
#define M68K_SOURCE_FILE_PARSE_H

#include "m68k_source_model.h"

#include <stddef.h>

int m68k_source_file_parse(AsmSourceFile *source, const char *path, char *out_error, size_t out_error_size);

#endif
