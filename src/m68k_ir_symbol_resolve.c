#include "m68k_ir_symbol_resolve.h"

#include "m68k_assembler.h"
#include "platform_common.h"

#include <stdio.h>


static size_t pc_relative_ea_base_offset_local(const M68kAsmFormDef *form, const M68kInstructionIR *instruction,
    size_t operand_index) {
  size_t base_offset = 2U;
  size_t index;
  if (form != NULL) base_offset += (size_t)form->bound_word_count * 2U;
  if (instruction == NULL) return base_offset;
  for (index = 0; index <= operand_index && index < instruction->operand_count; ++index) {
    base_offset += m68k_asm_operand_extension_word_count(form, &instruction->operands[index].value,
      instruction->size_suffix) * 2U;
  }
  return base_offset;
}

int m68k_ir_apply_symbol_refs(const M68kIrResolveContext *context, M68kInstructionIR *instruction,
    const M68kAsmFormDef *form, uint32_t instruction_offset, size_t line_number, int allow_undefined,
    int *out_abs_fixup_operands, size_t *out_abs_fixup_count, char *out_error, size_t out_error_size) {
  size_t operand_index;
  *out_abs_fixup_count = 0U;
  for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
    const char *label_name = instruction->operands[operand_index].symbol_ref.has_name
      ? instruction->operands[operand_index].symbol_ref.name : "";
    M68kAsmOperandValue *operand = &instruction->operands[operand_index].value;
    uint32_t symbol_value = 0;
    size_t symbol_section_index = (size_t)-1;
    int symbol_defined = 0;
    if (label_name[0] == '\0') continue;
    if (!context->lookup_symbol(label_name, &symbol_value, &symbol_section_index, &symbol_defined, context->user_data)) {
      m68k_platform_set_errorf(out_error, out_error_size, "undefined label at line %u: %s", (unsigned)line_number,
        label_name);
      return 0;
    }
    if (!symbol_defined) {
      if (!allow_undefined) {
        m68k_platform_set_errorf(out_error, out_error_size, "undefined label at line %u: %s", (unsigned)line_number,
          label_name);
        return 0;
      }
      symbol_value = 0;
    }
    symbol_value = (uint32_t)((int32_t)symbol_value + instruction->operands[operand_index].symbol_ref.addend);
    if (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 7 &&
        (operand->ea_reg == 2 || operand->ea_reg == 3)) {
      operand->value = (uint32_t)(symbol_value - (instruction_offset +
        pc_relative_ea_base_offset_local(form, instruction, operand_index)));
    } else if (operand->kind == M68K_ASM_OPERAND_LABEL) {
      operand->value = (uint32_t)(symbol_value - (instruction_offset + 2U));
    } else {
      operand->value = symbol_value;
      out_abs_fixup_operands[*out_abs_fixup_count] = (int)operand_index;
      *out_abs_fixup_count += 1U;
    }
    if (symbol_defined) {
      instruction->operands[operand_index].symbol_ref.has_section = 1;
      instruction->operands[operand_index].symbol_ref.section_index = symbol_section_index;
    }
  }
  return 1;
}


