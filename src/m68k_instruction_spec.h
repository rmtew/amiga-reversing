#ifndef M68K_INSTRUCTION_SPEC_H
#define M68K_INSTRUCTION_SPEC_H

#include "m68k_assembler.h"
#include "m68k_ir.h"

#include <stddef.h>
#include <stdint.h>

#define M68K_INSTRUCTION_SPEC_MAX_PATCH_VALUES 16
#define M68K_INSTRUCTION_SPEC_MAX_OPERANDS 4
#define M68K_INSTRUCTION_SPEC_MAX_LABEL_NAME 64

typedef struct {
  char mnemonic[32];
  uint8_t mnemonic_id;
  char size_suffix;
  uint8_t target_cpu;
  uint16_t form_index;
  size_t operand_count;
  uint16_t patch_values[M68K_INSTRUCTION_SPEC_MAX_PATCH_VALUES];
  size_t patch_value_count;
  M68kAsmOperandValue operands[M68K_INSTRUCTION_SPEC_MAX_OPERANDS];
  char operand_label_names[M68K_INSTRUCTION_SPEC_MAX_OPERANDS][M68K_INSTRUCTION_SPEC_MAX_LABEL_NAME];
  int32_t operand_label_addends[M68K_INSTRUCTION_SPEC_MAX_OPERANDS];
} InstructionSpec;

const char *m68k_instruction_spec_mnemonic_name(const InstructionSpec *instruction);
size_t m68k_instruction_spec_assemble_bytes(const InstructionSpec *instruction, unsigned char *out_bytes, size_t max_bytes);
int m68k_instruction_spec_uses_movem_predecrement_mask(const InstructionSpec *instruction);
uint16_t m68k_reverse_reglist_mask(uint16_t mask);
void m68k_instruction_spec_to_ir(const InstructionSpec *spec, M68kInstructionIR *out_instruction);
void m68k_instruction_ir_to_spec(const M68kInstructionIR *instruction, InstructionSpec *out_spec);
int m68k_instruction_operand_supports_decoded_ea_target(const M68kOperandIR *operand);
uint8_t m68k_instruction_operand_decoded_ea_shape(const M68kOperandIR *operand);
uint8_t m68k_instruction_decoded_ea_target_kind(const M68kOperandIR *operand, uint8_t ea_shape,
    int include_pc_index);
int m68k_instruction_decoded_ea_target(const M68kOperandIR *operand, uint8_t ea_shape, uint32_t pc_base,
    uint32_t section_size, int include_pc_index, uint32_t *out_target);
int m68k_instruction_operand_direct_register(const M68kOperandIR *operand, uint8_t *is_address, uint8_t *reg);

#endif
