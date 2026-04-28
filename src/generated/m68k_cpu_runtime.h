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
} M68kCpuExceptionVectorInfo;

#define M68K_CPU_EXCEPTION_VECTOR_COUNT 36u

static const M68kCpuExceptionVectorInfo g_m68k_cpu_exception_vectors[] = {
  { 0u, 0x0000u, M68K_CPU_VECTOR_KIND_RESET, "Initial SSP" },
  { 1u, 0x0004u, M68K_CPU_VECTOR_KIND_RESET, "Initial PC" },
  { 2u, 0x0008u, M68K_CPU_VECTOR_KIND_EXCEPTION, "Bus Error" },
  { 3u, 0x000Cu, M68K_CPU_VECTOR_KIND_EXCEPTION, "Address Error" },
  { 4u, 0x0010u, M68K_CPU_VECTOR_KIND_EXCEPTION, "Illegal Instruction" },
  { 5u, 0x0014u, M68K_CPU_VECTOR_KIND_EXCEPTION, "Division by Zero" },
  { 6u, 0x0018u, M68K_CPU_VECTOR_KIND_EXCEPTION, "CHK Instruction" },
  { 7u, 0x001Cu, M68K_CPU_VECTOR_KIND_EXCEPTION, "TRAPV Instruction" },
  { 8u, 0x0020u, M68K_CPU_VECTOR_KIND_EXCEPTION, "Privilege Violation" },
  { 9u, 0x0024u, M68K_CPU_VECTOR_KIND_EXCEPTION, "Trace" },
  { 10u, 0x0028u, M68K_CPU_VECTOR_KIND_EXCEPTION, "Line 1010 Emulator" },
  { 11u, 0x002Cu, M68K_CPU_VECTOR_KIND_EXCEPTION, "Line 1111 Emulator" },
  { 24u, 0x0060u, M68K_CPU_VECTOR_KIND_INTERRUPT, "Spurious Interrupt" },
  { 25u, 0x0064u, M68K_CPU_VECTOR_KIND_INTERRUPT, "Level 1 Interrupt Autovector" },
  { 26u, 0x0068u, M68K_CPU_VECTOR_KIND_INTERRUPT, "Level 2 Interrupt Autovector" },
  { 27u, 0x006Cu, M68K_CPU_VECTOR_KIND_INTERRUPT, "Level 3 Interrupt Autovector" },
  { 28u, 0x0070u, M68K_CPU_VECTOR_KIND_INTERRUPT, "Level 4 Interrupt Autovector" },
  { 29u, 0x0074u, M68K_CPU_VECTOR_KIND_INTERRUPT, "Level 5 Interrupt Autovector" },
  { 30u, 0x0078u, M68K_CPU_VECTOR_KIND_INTERRUPT, "Level 6 Interrupt Autovector" },
  { 31u, 0x007Cu, M68K_CPU_VECTOR_KIND_INTERRUPT, "Level 7 Interrupt Autovector" },
  { 32u, 0x0080u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #0 Instruction Vector" },
  { 33u, 0x0084u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #1 Instruction Vector" },
  { 34u, 0x0088u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #2 Instruction Vector" },
  { 35u, 0x008Cu, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #3 Instruction Vector" },
  { 36u, 0x0090u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #4 Instruction Vector" },
  { 37u, 0x0094u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #5 Instruction Vector" },
  { 38u, 0x0098u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #6 Instruction Vector" },
  { 39u, 0x009Cu, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #7 Instruction Vector" },
  { 40u, 0x00A0u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #8 Instruction Vector" },
  { 41u, 0x00A4u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #9 Instruction Vector" },
  { 42u, 0x00A8u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #10 Instruction Vector" },
  { 43u, 0x00ACu, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #11 Instruction Vector" },
  { 44u, 0x00B0u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #12 Instruction Vector" },
  { 45u, 0x00B4u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #13 Instruction Vector" },
  { 46u, 0x00B8u, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #14 Instruction Vector" },
  { 47u, 0x00BCu, M68K_CPU_VECTOR_KIND_TRAP, "TRAP #15 Instruction Vector" },
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

static inline int m68k_cpu_exception_vector_address_has_kind(uint32_t address, uint8_t kind) {
  const M68kCpuExceptionVectorInfo *entry = m68k_cpu_find_exception_vector_by_address(address);
  return entry != NULL && entry->kind == kind;
}

#endif
