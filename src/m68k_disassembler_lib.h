#ifndef M68K_DISASSEMBLER_LIB_H
#define M68K_DISASSEMBLER_LIB_H

#include <stddef.h>
#include <stdint.h>

#include "m68k_simulator.h"

#ifdef _WIN32
#define M68K_DISASM_EXPORT __declspec(dllexport)
#else
#define M68K_DISASM_EXPORT
#endif

M68K_DISASM_EXPORT int m68k_disassemble_one_text(const uint8_t *data, size_t size, char *out_text, size_t out_text_size,
  size_t *out_byte_count, char *out_error, size_t out_error_size);
M68K_DISASM_EXPORT int m68k_disassemble_one_text_for_cpu(const uint8_t *data, size_t size, uint8_t target_cpu, char *out_text,
  size_t out_text_size, size_t *out_byte_count, char *out_error, size_t out_error_size);
M68K_DISASM_EXPORT int m68k_simulate_one_concrete_for_cpu(const uint8_t *data, size_t size, uint8_t target_cpu,
  uint8_t *memory, size_t memory_size, M68kSimConcreteState *io_state, char *out_error, size_t out_error_size);
M68K_DISASM_EXPORT int m68k_simulate_one_abstract_for_cpu(const uint8_t *data, size_t size, uint8_t target_cpu,
  const M68kSimCpuState *state, M68kSimStepResult *out_result, char *out_error, size_t out_error_size);

#endif
