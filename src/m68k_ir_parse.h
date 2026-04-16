#ifndef M68K_IR_PARSE_H
#define M68K_IR_PARSE_H

#include "m68k_diagnostics.h"
#include "m68k_ir.h"

#include <stddef.h>
#include <stdint.h>

M68kInstructionIR m68k_ir_parse_one(const char *text, uint8_t syntax_mode, uint8_t target_cpu,
  M68kDiagSink diagnostics);

#endif
