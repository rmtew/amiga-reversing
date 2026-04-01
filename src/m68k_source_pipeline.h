#ifndef M68K_SOURCE_PIPELINE_H
#define M68K_SOURCE_PIPELINE_H

#include "m68k_ir.h"
#include "m68k_object.h"
#include "m68k_source_model.h"

#include <stddef.h>
#include <stdint.h>

int m68k_source_pipeline_parse_and_layout(AsmSourceFile *source, const char *path, char *out_error, size_t out_error_size);
int m68k_source_pipeline_emit_object(AsmSourceFile *source, M68kObject *out_object, char *out_error, size_t out_error_size);
int m68k_source_pipeline_build_ir(AsmSourceFile *source, M68kSourceFileIR *out_source_file, char *out_error, size_t out_error_size);

#endif
