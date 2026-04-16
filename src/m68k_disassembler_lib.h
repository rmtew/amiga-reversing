#ifndef M68K_DISASSEMBLER_LIB_H
#define M68K_DISASSEMBLER_LIB_H

#include <stddef.h>
#include <stdint.h>

#include "m68k_diagnostics.h"
#include "m68k_simulator.h"

#ifdef _WIN32
#define M68K_DISASM_EXPORT __declspec(dllexport)
#else
#define M68K_DISASM_EXPORT
#endif

#define M68K_DISASM_TEXT_SIZE 256U

typedef struct M68kDisasmTextResult {
  size_t byte_count;
  char text[M68K_DISASM_TEXT_SIZE];
  M68kDiagList diagnostics;
} M68kDisasmTextResult;

typedef struct M68kDisasmInfoResult {
  size_t byte_count;
  uint16_t asm_form_index;
  uint8_t mnemonic_id;
  uint8_t target_cpu;
  char mnemonic[32];
  char size_suffix;
  size_t operand_count;
  M68kDiagList diagnostics;
} M68kDisasmInfoResult;

typedef struct M68kSimConcreteRunResult {
  M68kDiagList diagnostics;
} M68kSimConcreteRunResult;

typedef struct M68kSimAbstractRunResult {
  M68kSimStepResult step;
  M68kDiagList diagnostics;
} M68kSimAbstractRunResult;

M68K_DISASM_EXPORT M68kDisasmTextResult m68k_disassemble_one_text(const uint8_t *data, size_t size);
M68K_DISASM_EXPORT M68kDisasmTextResult m68k_disassemble_one_text_for_cpu(const uint8_t *data, size_t size,
  uint8_t target_cpu);
M68K_DISASM_EXPORT M68kDisasmInfoResult m68k_disassemble_one_info_for_cpu(const uint8_t *data, size_t size,
  uint8_t target_cpu);
M68K_DISASM_EXPORT M68kSimConcreteRunResult m68k_simulate_one_concrete_for_cpu(const uint8_t *data, size_t size,
  uint8_t target_cpu, uint8_t *memory, size_t memory_size, M68kSimConcreteState *io_state);
M68K_DISASM_EXPORT M68kSimAbstractRunResult m68k_simulate_one_abstract_for_cpu(const uint8_t *data, size_t size,
  uint8_t target_cpu, const M68kSimCpuState *state);

#endif
