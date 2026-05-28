#include "m68k_ir_symbol_resolve.h"

#include "m68k_assembler.h"

#include <stdio.h>
#include <string.h>

M68kIrSymbolApplyResult m68k_ir_apply_symbol_refs(const M68kIrResolveContext *context,
    M68kInstructionIR instruction, const M68kAsmFormDef *form, uint32_t instruction_offset, size_t line_number,
    int allow_undefined, M68kDiagSink diagnostics) {
  M68kIrSymbolApplyResult result;
  size_t operand_index;
  memset(&result, 0, sizeof(result));
  result.instruction = instruction;
  for (operand_index = 0; operand_index < result.instruction.operand_count; ++operand_index) {
    const char *label_name = result.instruction.operands[operand_index].symbol_ref.has_name
      ? result.instruction.operands[operand_index].symbol_ref.name : "";
    M68kAsmOperandValue *operand = &result.instruction.operands[operand_index].value;
    M68kSourceLookupResult symbol;
    uint32_t symbol_value;
    if (label_name[0] == '\0') continue;
    symbol = context->lookup_symbol(label_name, context->user_data);
    if (!symbol.ok) {
      m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_SOURCE_FAILED,
        "undefined label at line %u: %s", (unsigned)line_number, label_name);
      return result;
    }
    if (!symbol.defined) {
      if (!allow_undefined) {
        m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_SOURCE_FAILED,
          "undefined label at line %u: %s", (unsigned)line_number, label_name);
        return result;
      }
      symbol_value = 0;
    } else symbol_value = symbol.value;
    symbol_value = (uint32_t)((int32_t)symbol_value +
      result.instruction.operands[operand_index].symbol_ref.addend);
    if (result.instruction.operands[operand_index].symbol_ref.kind == M68K_IR_SYMBOL_REF_ABS) {
      if (operand->kind == M68K_ASM_OPERAND_LABEL) {
        operand->kind = M68K_ASM_OPERAND_EA;
        operand->ea_mode = 7;
        operand->ea_reg = result.instruction.size_suffix == 'l' ? 1 : 0;
      }
      operand->value = symbol_value;
    } else if (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 7 &&
        (operand->ea_reg == 2 || operand->ea_reg == 3)) {
      operand->value = (uint32_t)(symbol_value - (instruction_offset +
        m68k_asm_operand_relative_base_offset(form->asm_form_index, &result.instruction.operands[0].value,
          result.instruction.operand_count, result.instruction.size_suffix, operand_index, 0)));
    } else if (operand->kind == M68K_ASM_OPERAND_LABEL) {
      operand->value = (uint32_t)(symbol_value - (instruction_offset + 2U));
    } else {
      operand->value = symbol_value;
    }
    if (symbol.defined && !symbol.is_constant) {
      result.instruction.operands[operand_index].symbol_ref.has_section = 1;
      result.instruction.operands[operand_index].symbol_ref.section_index = symbol.section_index;
    }
  }
  result.ok = 1;
  return result;
}


