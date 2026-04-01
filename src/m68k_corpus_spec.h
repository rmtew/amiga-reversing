#ifndef M68K_CORPUS_SPEC_H
#define M68K_CORPUS_SPEC_H

#include "m68k_instruction_spec.h"

int m68k_corpus_parse_instruction_spec(char *text, InstructionSpec *out_spec);

#endif
