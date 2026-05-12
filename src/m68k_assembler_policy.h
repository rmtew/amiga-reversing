#ifndef M68K_ASSEMBLER_POLICY_H
#define M68K_ASSEMBLER_POLICY_H

#include "m68k_object.h"

#include <stdint.h>

#define M68K_ASSEMBLER_POLICY_HUNK_RELOCATION_RECORD_CAPACITY 8U

typedef enum M68kAssemblerPolicyKind {
  M68K_ASSEMBLER_POLICY_IDEAL = 1,
  M68K_ASSEMBLER_POLICY_PRESERVE_ORIGINAL = 2
} M68kAssemblerPolicyKind;

typedef enum M68kAssemblerPolicyFlag {
  M68K_ASSEMBLER_POLICY_PRESERVE_CONTAINER_LAYOUT = 1U << 0,
  M68K_ASSEMBLER_POLICY_PRESERVE_CONTAINER_ENCODING = 1U << 1,
  M68K_ASSEMBLER_POLICY_PRESERVE_HUNK_RELOCATION_ENCODING = 1U << 2,
  M68K_ASSEMBLER_POLICY_CONTAINER_LAYOUT_OVERFLOW = 1U << 3,
  M68K_ASSEMBLER_POLICY_CONTAINER_ENCODING_OVERFLOW = 1U << 4
} M68kAssemblerPolicyFlag;

typedef struct M68kAssemblerPolicy {
  uint8_t kind;
  uint8_t platform_backend_kind;
  uint16_t flags;
  uint8_t hunk_relocation_record_count;
  uint8_t hunk_relocation_record_overflow;
  uint16_t reserved;
  uint32_t hunk_relocation_record_wire_ids[M68K_ASSEMBLER_POLICY_HUNK_RELOCATION_RECORD_CAPACITY];
} M68kAssemblerPolicy;

void m68k_assembler_policy_init_ideal(M68kAssemblerPolicy *policy);
void m68k_assembler_policy_derive_preservation(const M68kObject *object, M68kAssemblerPolicy *policy);

#endif
