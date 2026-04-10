#ifndef M68K_IR_CODEC_H
#define M68K_IR_CODEC_H

#include "m68k_ir.h"

#include <stddef.h>
#include <stdint.h>

int m68k_ir_decode_one(const uint8_t *data, size_t size, uint8_t target_cpu, M68kInstructionIR *out_instruction,
  char *out_error, size_t out_error_size);
int m68k_ir_parse_one(const char *text, uint8_t syntax_mode, uint8_t target_cpu, M68kInstructionIR *out_instruction,
  char *out_error, size_t out_error_size);
int m68k_ir_encode_one(const M68kInstructionIR *instruction, uint8_t *out_bytes, size_t max_bytes, size_t *out_byte_count,
  char *out_error, size_t out_error_size);
int m68k_ir_render_one_at_with_policy(const M68kInstructionIR *instruction, uint32_t offset,
  const M68kRenderPolicy *policy, char *out_text, size_t out_text_size, char *out_error, size_t out_error_size);
int m68k_ir_render_one_with_policy(const M68kInstructionIR *instruction, const M68kRenderPolicy *policy, char *out_text,
  size_t out_text_size, char *out_error, size_t out_error_size);

#endif
