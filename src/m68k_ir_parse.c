#include "m68k_ir_parse.h"
#include "m68k_assembler_lib.h"
#include "m68k_ir_codec.h"
#include "m68k_parse_util.h"
#include "m68k_plain_parse.h"

#include "platform_common.h"

#include <stdio.h>


M68kInstructionIR m68k_ir_parse_one(const char *text, uint8_t syntax_mode, uint8_t target_cpu,
    M68kDiagSink diagnostics) {
  M68kInstructionIR instruction;
  m68k_ir_instruction_init(&instruction);
  if (text == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_BAD_ARGUMENT, "bad arguments");
    return instruction;
  }
  if (syntax_mode == M68K_IR_SYNTAX_CANONICAL && m68k_text_uses_short_branch_suffix(text)) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_DECODE_FAILED,
      "canonical syntax uses .b for short branches");
    return instruction;
  }
  return m68k_plain_parse_instruction_to_ir(text, target_cpu, diagnostics);
}


