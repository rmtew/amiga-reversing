/* Generated M68K CPU runtime metadata. Do not edit directly. */
#ifndef M68K_CPU_RUNTIME_H
#define M68K_CPU_RUNTIME_H

#include <stddef.h>
#include <stdint.h>

typedef enum M68kCpuVectorKind {
  M68K_CPU_VECTOR_KIND_UNKNOWN = 0,
  M68K_CPU_VECTOR_KIND_RESET = 1,
  M68K_CPU_VECTOR_KIND_EXCEPTION = 2,
  M68K_CPU_VECTOR_KIND_INTERRUPT = 3,
  M68K_CPU_VECTOR_KIND_TRAP = 4
} M68kCpuVectorKind;

typedef struct M68kCpuExceptionVectorInfo {
  uint16_t vector;
  uint16_t address;
  uint8_t kind;
  const char *name;
  const char *symbol_name;
} M68kCpuExceptionVectorInfo;

#define M68K_CPU_EXCEPTION_VECTOR_COUNT 36u

static const M68kCpuExceptionVectorInfo g_m68k_cpu_exception_vectors[] = {
  { 0u, 0x0000u, M68K_CPU_VECTOR_KIND_RESET, "Initial SSP", "m68k_vector_initial_ssp" },
  { 1u, 0x0004u, M68K_CPU_VECTOR_KIND_RESET, "Initial PC", "m68k_vector_initial_pc" },
  { 2u, 0x0008u, M68K_CPU_VECTOR_KIND_EXCEPTION, "Bus Error", "m68k_vector_bus_error" },
  { 3u, 0x000Cu, M68K_CPU_VECTOR_KIND_EXCEPTION, "Address Error", "m68k_vector_address_error" },
  { 4u, 0x0010u, M68K_CPU_VECTOR_KIND_EXCEPTION, "Illegal Instruction", "m68k_vector_illegal_instruction" },
  { 5u, 0x0014u, M68K_CPU_VECTOR_KIND_EXCEPTION, "Division by Zero", "m68k_vector_division_by_zero" },
  { 6u, 0x0018u, M68K_CPU_VECTOR_KIND_EXCEPTION, "CHK Instruction", "m68k_vector_chk_instruction" },
  { 7u, 0x001Cu, M68K_CPU_VECTOR_KIND_EXCEPTION, "TRAPV Instruction", "m68k_vector_trapv_instruction" },
  { 8u, 0x0020u, M68K_CPU_VECTOR_KIND_EXCEPTION, "Privilege Violation", "m68k_vector_privilege_violation" },
  { 9u, 0x0024u, M68K_CPU_VECTOR_KIND_EXCEPTION, "Trace", "m68k_vector_trace" },
  { 10u, 0x0028u, M68K_CPU_VECTOR_KIND_EXCEPTION, "Line 1010 Emulator", "m68k_vector_line_1010_emulator" },
  { 11u, 0x002Cu, M68K_CPU_VECTOR_KIND_EXCEPTION, "Line 1111 Emulator", "m68k_vector_line_1111_emulator" },
  { 24u, 0x0060u, M68K_CPU_VECTOR_KIND_INTERRUPT, "Spurious Interrupt", "m68k_vector_spurious_interrupt" },
  { 25u, 0x0064u, M68K_CPU_VECTOR_KIND_INTERRUPT, "Level 1 Interrupt Autovector", "m68k_vector_level_1_interrupt_autovector" },
  { 26u, 0x0068u, M68K_CPU_VECTOR_KIND_INTERRUPT, "Level 2 Interrupt Autovector", "m68k_vector_level_2_interrupt_autovector" },
  { 27u, 0x006Cu, M68K_CPU_VECTOR_KIND_INTERRUPT, "Level 3 Interrupt Autovector", "m68k_vector_level_3_interrupt_autovector" },
  { 28u, 0x0070u, M68K_CPU_VECTOR_KIND_INTERRUPT, "Level 4 Interrupt Autovector", "m68k_vector_level_4_interrupt_autovector" },
  { 29u, 0x0074u, M68K_CPU_VECTOR_KIND_INTERRUPT, "Level 5 Interrupt Autovector", "m68k_vector_level_5_interrupt_autovector" },
  { 30u, 0x0078u, M68K_CPU_VECTOR_KIND_INTERRUPT, "Level 6 Interrupt Autovector", "m68k_vector_level_6_interrupt_autovector" },
  { 31u, 0x007Cu, M68K_CPU_VECTOR_KIND_INTERRUPT, "Level 7 Interrupt Autovector", "m68k_vector_level_7_interrupt_autovector" },
  { 32u, 0x0080u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #0 Instruction Vector", "m68k_vector_trap_0_instruction_vector" },
  { 33u, 0x0084u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #1 Instruction Vector", "m68k_vector_trap_1_instruction_vector" },
  { 34u, 0x0088u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #2 Instruction Vector", "m68k_vector_trap_2_instruction_vector" },
  { 35u, 0x008Cu, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #3 Instruction Vector", "m68k_vector_trap_3_instruction_vector" },
  { 36u, 0x0090u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #4 Instruction Vector", "m68k_vector_trap_4_instruction_vector" },
  { 37u, 0x0094u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #5 Instruction Vector", "m68k_vector_trap_5_instruction_vector" },
  { 38u, 0x0098u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #6 Instruction Vector", "m68k_vector_trap_6_instruction_vector" },
  { 39u, 0x009Cu, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #7 Instruction Vector", "m68k_vector_trap_7_instruction_vector" },
  { 40u, 0x00A0u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #8 Instruction Vector", "m68k_vector_trap_8_instruction_vector" },
  { 41u, 0x00A4u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #9 Instruction Vector", "m68k_vector_trap_9_instruction_vector" },
  { 42u, 0x00A8u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #10 Instruction Vector", "m68k_vector_trap_10_instruction_vector" },
  { 43u, 0x00ACu, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #11 Instruction Vector", "m68k_vector_trap_11_instruction_vector" },
  { 44u, 0x00B0u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #12 Instruction Vector", "m68k_vector_trap_12_instruction_vector" },
  { 45u, 0x00B4u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #13 Instruction Vector", "m68k_vector_trap_13_instruction_vector" },
  { 46u, 0x00B8u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #14 Instruction Vector", "m68k_vector_trap_14_instruction_vector" },
  { 47u, 0x00BCu, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #15 Instruction Vector", "m68k_vector_trap_15_instruction_vector" },
};

static inline const M68kCpuExceptionVectorInfo *m68k_cpu_exception_vector_at(size_t index) {
  if (index >= M68K_CPU_EXCEPTION_VECTOR_COUNT) return NULL;
  return &g_m68k_cpu_exception_vectors[index];
}

static inline const M68kCpuExceptionVectorInfo *m68k_cpu_find_exception_vector_by_address(uint32_t address) {
  size_t index;
  for (index = 0U; index < M68K_CPU_EXCEPTION_VECTOR_COUNT; ++index) {
    const M68kCpuExceptionVectorInfo *entry = &g_m68k_cpu_exception_vectors[index];
    if (entry->address == address) return entry;
  }
  return NULL;
}

static inline const M68kCpuExceptionVectorInfo *m68k_cpu_find_exception_vector_by_symbol_name(const char *symbol_name) {
  size_t index;
  if (symbol_name == NULL || symbol_name[0] == '\0') return NULL;
  for (index = 0U; index < M68K_CPU_EXCEPTION_VECTOR_COUNT; ++index) {
    const M68kCpuExceptionVectorInfo *entry = &g_m68k_cpu_exception_vectors[index];
    const char *left = entry->symbol_name;
    const char *right = symbol_name;
    if (left == NULL) continue;
    while (*left != '\0' && *right != '\0' && *left == *right) { ++left; ++right; }
    if (*left == '\0' && *right == '\0') return entry;
  }
  return NULL;
}

static inline int m68k_cpu_exception_vector_address_has_kind(uint32_t address, uint8_t kind) {
  const M68kCpuExceptionVectorInfo *entry = m68k_cpu_find_exception_vector_by_address(address);
  return entry != NULL && entry->kind == kind;
}

#endif
