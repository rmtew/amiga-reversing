#ifndef M68K_IR_CODEC_H
#define M68K_IR_CODEC_H

#include "m68k_diagnostics.h"
#include "m68k_ir.h"

#include <stddef.h>
#include <stdint.h>

#define M68K_IR_RENDER_TEXT_SIZE 512U

typedef struct M68kIrRenderResult {
  char text[M68K_IR_RENDER_TEXT_SIZE];
  uint8_t rendered_operand_symbol_mask;
} M68kIrRenderResult;

typedef struct M68kIrEncodeResult {
  size_t byte_count;
} M68kIrEncodeResult;

M68kInstructionIR m68k_ir_decode_one(const uint8_t *data, size_t size, uint8_t target_cpu,
  M68kDiagSink diagnostics);
M68kInstructionIR m68k_ir_parse_one(const char *text, uint8_t syntax_mode, uint8_t target_cpu,
  M68kDiagSink diagnostics);
M68kIrEncodeResult m68k_ir_encode_one(const M68kInstructionIR *instruction, uint8_t *out_bytes, size_t max_bytes,
  M68kDiagSink diagnostics);
M68kIrRenderResult m68k_ir_render_one_at_with_policy(const M68kInstructionIR *instruction, uint32_t offset,
  const M68kRenderPolicy *policy, M68kDiagSink diagnostics);
M68kIrRenderResult m68k_ir_render_one_with_policy(const M68kInstructionIR *instruction,
  const M68kRenderPolicy *policy, M68kDiagSink diagnostics);

#endif
