#include "m68k_disassembler.h"
#include "m68k_disassembler_lib.h"
#include "m68k_ir.h"
#include "m68k_ir_codec.h"
#include "m68k_asm_tables.h"

#include "platform_common.h"

#include <stdio.h>
#include <string.h>


static int m68k_disassemble_one_text_impl(const uint8_t *data, size_t size, uint8_t target_cpu, char *out_text,
    size_t out_text_size, size_t *out_byte_count, char *out_error, size_t out_error_size) {
  M68kInstructionIR instruction;
  M68kRenderPolicy policy;
  char decode_error[128];
  m68k_ir_instruction_init(&instruction);
  if (m68k_ir_decode_one(data, size, target_cpu, &instruction, decode_error, sizeof(decode_error)) != 0) {
    m68k_platform_set_error(out_error, out_error_size, decode_error);
    if (out_text != NULL && out_text_size != 0U) out_text[0] = '\0';
    if (out_byte_count != NULL) *out_byte_count = 0U;
    return -1;
  }
  m68k_render_policy_init_default(&policy);
  if (m68k_ir_render_one_with_policy(&instruction, &policy, out_text, out_text_size, decode_error,
      sizeof(decode_error)) != 0) {
    m68k_platform_set_error(out_error, out_error_size, decode_error);
    if (out_text != NULL && out_text_size != 0U) out_text[0] = '\0';
    if (out_byte_count != NULL) *out_byte_count = 0U;
    return -1;
  }
  m68k_platform_set_error(out_error, out_error_size, "");
  if (out_byte_count != NULL) *out_byte_count = instruction.byte_count;
  return 0;
}

int m68k_disassemble_one_text(const uint8_t *data, size_t size, char *out_text, size_t out_text_size,
    size_t *out_byte_count, char *out_error, size_t out_error_size) {
  return m68k_disassemble_one_text_impl(data, size, M68K_ASM_CPU_68000, out_text, out_text_size, out_byte_count,
    out_error, out_error_size);
}

int m68k_disassemble_one_text_for_cpu(const uint8_t *data, size_t size, uint8_t target_cpu, char *out_text,
    size_t out_text_size, size_t *out_byte_count, char *out_error, size_t out_error_size) {
  return m68k_disassemble_one_text_impl(data, size, target_cpu, out_text, out_text_size, out_byte_count, out_error,
    out_error_size);
}


