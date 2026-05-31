/* Compact decode-only IR for facts_v2 analysis. */
#ifndef M68K_DECODE_IR_H
#define M68K_DECODE_IR_H

#include "m68k_asm_metadata.h"
#include "m68k_diagnostics.h"
#include "m68k_ir.h"
#include "m68k_object.h"
#include "util_arena.h"

#include <stddef.h>
#include <stdint.h>

#define M68K_DECODE_IR_MAX_OPERANDS 4U
#define M68K_DECODE_IR_MAX_TARGETS 4U

typedef enum M68kDecodeTargetKind {
  M68K_DECODE_TARGET_BRANCH = 1,
  M68K_DECODE_TARGET_CALL = 2,
  M68K_DECODE_TARGET_JUMP = 3,
  M68K_DECODE_TARGET_DATA = 4
} M68kDecodeTargetKind;

typedef struct M68kDecodeTarget {
  uint8_t kind;
  uint8_t has_section;
  uint8_t has_operand;
  uint8_t operand_index;
  size_t section_index;
  uint32_t offset;
  uint32_t address;
} M68kDecodeTarget;

typedef struct M68kDecodeCandidate {
  uint32_t offset;
  uint16_t asm_form_index;
  uint16_t disasm_form_index;
  uint8_t mnemonic_id;
  uint8_t target_cpu;
  uint8_t has_coprocessor_id;
  uint8_t coprocessor_id;
  uint8_t byte_count;
  char size_suffix;
  uint8_t operand_count;
  uint8_t operand_kinds[M68K_DECODE_IR_MAX_OPERANDS];
  M68kAsmOperandValue operands[M68K_DECODE_IR_MAX_OPERANDS];
  uint8_t target_count;
  M68kDecodeTarget targets[M68K_DECODE_IR_MAX_TARGETS];
} M68kDecodeCandidate;

typedef struct M68kDecodeSectionIR {
  Arena *owner_arena;
  size_t section_index;
  const char *name;
  M68kSectionKind kind;
  uint8_t platform_mem_type;
  uint32_t platform_mem_attrs;
  uint32_t allocation_size;
  uint32_t size;
  const uint8_t *data;
  M68kDecodeCandidate *candidates;
  size_t candidate_count;
  size_t candidate_capacity;
  uint8_t *candidate_absent_cpu;
  uint32_t candidate_absent_size;
} M68kDecodeSectionIR;

typedef struct M68kDecodeIR {
  Arena *arena;
  M68kDecodeSectionIR *sections;
  size_t section_count;
  size_t section_capacity;
  uint32_t decoded_candidate_count;
} M68kDecodeIR;

void m68k_decode_ir_init(M68kDecodeIR *ir);
void m68k_decode_ir_destroy(M68kDecodeIR *ir);
int m68k_decode_ir_build_object_sections(M68kDecodeIR *ir, const M68kObject *object,
  M68kDiagSink diagnostics);
int m68k_decode_ir_build_object(M68kDecodeIR *ir, const M68kObject *object, uint8_t max_cpu,
  M68kDiagSink diagnostics);
const M68kDecodeCandidate *m68k_decode_ir_find_candidate_at_offset(const M68kDecodeSectionIR *section,
  uint32_t offset);
int m68k_decode_ir_ensure_candidate_at(M68kDecodeIR *ir, size_t section_index, uint32_t offset,
  uint8_t max_cpu, const M68kDecodeCandidate **out_candidate, M68kDiagSink diagnostics);
int m68k_decode_candidate_to_instruction(const M68kDecodeCandidate *candidate,
  M68kInstructionIR *out_instruction);
char m68k_decode_candidate_effective_size_suffix(const M68kDecodeCandidate *candidate);
M68kAsmOperandValue m68k_decode_candidate_normalized_layout_operand(const M68kDecodeCandidate *candidate,
  size_t operand_index);
size_t m68k_decode_asm_extension_word_count(uint16_t asm_form_index, uint8_t extension_kind,
  const M68kAsmOperandValue *operand, char size_suffix);
int m68k_decode_candidate_operand_storage_span(const M68kDecodeCandidate *candidate, size_t operand_index,
  uint32_t *out_start, uint32_t *out_size);

#endif
