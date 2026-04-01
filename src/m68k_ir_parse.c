#include "m68k_ir_parse.h"
#include "m68k_assembler_lib.h"
#include "m68k_ir_codec.h"
#include "m68k_parse_util.h"
#include "m68k_plain_parse.h"

#include "platform_common.h"

#include <stdio.h>


int m68k_ir_parse_one(const char *text, uint8_t syntax_mode, uint8_t target_cpu, M68kInstructionIR *out_instruction,
    char *out_error, size_t out_error_size) {
  if (text == NULL || out_instruction == NULL) {
    m68k_platform_set_error(out_error, out_error_size, "bad arguments");
    return -1;
  }
  if (syntax_mode == M68K_IR_SYNTAX_CANONICAL && m68k_text_uses_short_branch_suffix(text)) {
    m68k_platform_set_error(out_error, out_error_size, "canonical syntax uses .b for short branches");
    return -1;
  }
  return m68k_plain_parse_instruction_to_ir(text, target_cpu, out_instruction, out_error, out_error_size);
}


