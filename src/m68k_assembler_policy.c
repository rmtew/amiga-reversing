#include "m68k_assembler_policy.h"

#include <string.h>

static int policy_has_hunk_relocation_record(const M68kAssemblerPolicy *policy, uint32_t wire_id) {
  uint8_t index;
  if (policy == NULL) return 0;
  for (index = 0U; index < policy->hunk_relocation_record_count; ++index) {
    if (policy->hunk_relocation_record_wire_ids[index] == wire_id) return 1;
  }
  return 0;
}

static void policy_add_hunk_relocation_record(M68kAssemblerPolicy *policy, uint32_t wire_id) {
  if (policy == NULL || wire_id == 0U || policy_has_hunk_relocation_record(policy, wire_id)) return;
  if (policy->hunk_relocation_record_count >= M68K_ASSEMBLER_POLICY_HUNK_RELOCATION_RECORD_CAPACITY) {
    policy->hunk_relocation_record_overflow = 1U;
    return;
  }
  policy->hunk_relocation_record_wire_ids[policy->hunk_relocation_record_count++] = wire_id;
  policy->flags |= M68K_ASSEMBLER_POLICY_PRESERVE_HUNK_RELOCATION_ENCODING;
}

void m68k_assembler_policy_init_ideal(M68kAssemblerPolicy *policy) {
  if (policy == NULL) return;
  memset(policy, 0, sizeof(*policy));
  policy->kind = M68K_ASSEMBLER_POLICY_IDEAL;
}

void m68k_assembler_policy_derive_preservation(const M68kObject *object, M68kAssemblerPolicy *policy) {
  const M68kContainerMetadata *metadata;
  uint8_t index;
  if (policy == NULL) return;
  m68k_assembler_policy_init_ideal(policy);
  if (object == NULL) return;
  metadata = &object->container_metadata;
  policy->kind = M68K_ASSEMBLER_POLICY_PRESERVE_ORIGINAL;
  policy->platform_backend_kind = (uint8_t)object->platform_backend_kind;
  if (metadata->layout_overflow) policy->flags |= M68K_ASSEMBLER_POLICY_CONTAINER_LAYOUT_OVERFLOW;
  if (metadata->encoding_overflow) policy->flags |= M68K_ASSEMBLER_POLICY_CONTAINER_ENCODING_OVERFLOW;
  for (index = 0U; index < metadata->layout_count; ++index) {
    if (metadata->layout[index].kind != M68K_CONTAINER_LAYOUT_NONE &&
        metadata->layout[index].kind != M68K_CONTAINER_LAYOUT_NO_CONTAINER) {
      policy->flags |= M68K_ASSEMBLER_POLICY_PRESERVE_CONTAINER_LAYOUT;
      break;
    }
  }
  for (index = 0U; index < metadata->encoding_count; ++index) {
    const M68kContainerEncodingMetadata *encoding = &metadata->encoding[index];
    if (encoding->kind != M68K_CONTAINER_ENCODING_NONE &&
        encoding->kind != M68K_CONTAINER_ENCODING_NO_CONTAINER) {
      policy->flags |= M68K_ASSEMBLER_POLICY_PRESERVE_CONTAINER_ENCODING;
    }
    if (encoding->kind == M68K_CONTAINER_ENCODING_AMIGA_HUNK_RELOCATION_WIRE_ID) {
      policy_add_hunk_relocation_record(policy, encoding->id);
    }
    if (encoding->kind == M68K_CONTAINER_ENCODING_ATARI_ST_PRG_HEADER_FIELD ||
        encoding->kind == M68K_CONTAINER_ENCODING_ATARI_ST_PRG_RELOCATION_TERMINATOR) {
      policy->flags |= M68K_ASSEMBLER_POLICY_PRESERVE_ATARI_ST_CONTAINER_ENCODING;
    }
  }
}
