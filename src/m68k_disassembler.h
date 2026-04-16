/* Static disassembler runtime interface over generated KB-derived tables. */
#ifndef M68K_DISASSEMBLER_H
#define M68K_DISASSEMBLER_H

#include <stddef.h>
#include <stdint.h>
#include "m68k_asm_tables.h"
#include "m68k_diagnostics.h"

typedef struct {
  size_t byte_count;
  uint16_t form_index;
  uint8_t mnemonic_id;
  uint8_t target_cpu;
  char mnemonic[32];
  char size_suffix;
  size_t operand_count;
  uint8_t operand_kinds[4];
  M68kAsmOperandValue operands[4];
  char text[128];
} M68kDisasmResult;

M68kDisasmResult m68k_disassemble_one(const uint8_t *data, size_t size, M68kDiagSink diagnostics);
M68kDisasmResult m68k_disassemble_one_for_cpu(const uint8_t *data, size_t size, uint8_t target_cpu,
  M68kDiagSink diagnostics);

#endif
