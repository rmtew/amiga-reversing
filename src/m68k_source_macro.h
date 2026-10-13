#ifndef M68K_SOURCE_MACRO_H
#define M68K_SOURCE_MACRO_H
#include "m68k_diagnostics.h"
/* Literal source-local MACRO/ENDM definitions with positional arguments 1..9.
 * No include-file expansion, recursion, conditionals or assembler metaprogramming.
 * The caller owns the returned expanded text. */
int m68k_source_macro_expand(const char *text, char **expanded, M68kDiagSink diagnostics);
#endif
