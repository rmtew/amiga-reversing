#ifndef M68K_SOURCE_QUALITY_H
#define M68K_SOURCE_QUALITY_H

#include "m68k_decode_ir.h"
#include "m68k_ir.h"

int m68k_source_quality_analyze(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, uint8_t *const *accepted_start, uint8_t *const *accepted_bytes);

#endif
