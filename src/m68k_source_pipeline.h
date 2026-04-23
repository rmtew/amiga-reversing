#ifndef M68K_SOURCE_PIPELINE_H
#define M68K_SOURCE_PIPELINE_H

#include "m68k_diagnostics.h"
#include "m68k_ir.h"
#include "m68k_object.h"
#include "m68k_source_model.h"

#include <stddef.h>
#include <stdint.h>

int m68k_source_pipeline_parse_and_layout(AsmSourceFile *source, const char *path, M68kDiagSink diagnostics);
int m68k_source_pipeline_parse_text_and_layout(AsmSourceFile *source, const char *source_text,
  M68kDiagSink diagnostics);
int m68k_source_pipeline_emit_object(AsmSourceFile *source, M68kObject *out_object, M68kDiagSink diagnostics);
int m68k_source_pipeline_build_ir(AsmSourceFile *source, M68kSourceFileIR *out_source_file, M68kDiagSink diagnostics);

#endif
