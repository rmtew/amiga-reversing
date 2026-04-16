#ifndef M68K_PLAIN_PARSE_H
#define M68K_PLAIN_PARSE_H

#include "m68k_diagnostics.h"
#include "m68k_ir.h"
#include "m68k_instruction_spec.h"

#include <stddef.h>
#include <stdint.h>

int m68k_plain_parse_instruction_to_spec(const char *text, uint8_t target_cpu, InstructionSpec *out_instruction);
M68kInstructionIR m68k_plain_parse_instruction_to_ir(const char *text, uint8_t target_cpu,
    M68kDiagSink diagnostics);

#endif
