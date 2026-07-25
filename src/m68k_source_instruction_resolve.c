#include "m68k_source_instruction_resolve.h"

#include "m68k_ir_symbol_resolve.h"

#include <stdio.h>
#include <string.h>


static int instruction_uses_movem_predecrement_mask_ir_local(const M68kInstructionIR *instruction) {
    if (instruction->operand_count != 2U) return 0;
    if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEM) return 0;
    if (instruction->operands[0].kind != M68K_ASM_OPERAND_REGLIST) return 0;
    if (instruction->operands[1].kind != M68K_ASM_OPERAND_EA) return 0;
    return instruction->operands[1].value.ea_mode == 4U;
}

static int normalize_symbolic_zero_address_displacements_local(const M68kSourceInstructionResolveContext *context,
    M68kInstructionIR *instruction) {
    size_t operand_index;
    int changed = 0;
    if (instruction == NULL) return 0;
    for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
        M68kOperandIR *operand = &instruction->operands[operand_index];
        if (!operand->symbol_ref.has_name || operand->symbol_ref.has_section) continue;
        if (operand->symbol_ref.force_word_displacement) continue;
        if (context == NULL || context->lookup_symbol == NULL) continue;
        {
            M68kSourceLookupResult symbol = context->lookup_symbol(operand->symbol_ref.name, context->user_data);
            /* A zero-valued absolute constant is semantically identical to
             * address-register indirect.  Preserve section-relative labels,
             * whose relocation meaning requires the displacement extension. */
            if (!symbol.ok || !symbol.defined || !symbol.is_constant) continue;
        }
        if (operand->value.kind != M68K_ASM_OPERAND_EA || operand->value.ea_mode != 5U) continue;
        if (operand->value.value != 0U) continue;
        operand->value.ea_mode = 2U;
        changed = 1;
    }
    return changed;
}

M68kSourceResolvedInstruction m68k_source_resolve_instruction_operands(const M68kSourceInstructionResolveContext *context,
    size_t line_number, char requested_size_suffix, uint32_t instruction_offset, int allow_undefined,
    const M68kInstructionIR *parsed_instruction, M68kDiagSink diagnostics) {
    M68kSourceResolvedInstruction result;
    M68kIrResolveContext ir_resolve_context;
    M68kIrSymbolApplyResult symbol_result;
    M68kAsmOperandValue form_operands[4];
    uint16_t asm_form_index;
    size_t operand_index;
    memset(&result, 0, sizeof(result));
    memset(&ir_resolve_context, 0, sizeof(ir_resolve_context));
    ir_resolve_context.user_data = context->user_data;
    ir_resolve_context.lookup_symbol = context->lookup_symbol;
    result.instruction = *parsed_instruction;
    for (operand_index = 0; operand_index < result.instruction.operand_count && operand_index < 4U; ++operand_index) {
        form_operands[operand_index] = result.instruction.operands[operand_index].value;
    }
    if (instruction_uses_movem_predecrement_mask_ir_local(&result.instruction)) {
        form_operands[0].value = m68k_reverse_reglist_mask((uint16_t)form_operands[0].value);
    }
    asm_form_index = m68k_asm_form_index_for_operands_id(result.instruction.mnemonic_id, form_operands,
        result.instruction.operand_count, requested_size_suffix, result.instruction.target_cpu);
    if (g_m68k_asm_forms[asm_form_index].mnemonic_id == M68K_ASM_MNEMONIC_NONE) {
        m68k_diag_addf(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_SOURCE_FAILED,
            "failed resolving instruction form: %s size=%c cpu=%u op0=%u:%u/%u op1=%u:%u/%u",
            m68k_ir_instruction_mnemonic_name(&result.instruction),
            requested_size_suffix != '\0' ? requested_size_suffix : '-',
            (unsigned)result.instruction.target_cpu,
            result.instruction.operand_count > 0U ? (unsigned)form_operands[0].kind : 0U,
            result.instruction.operand_count > 0U ? (unsigned)form_operands[0].ea_mode : 0U,
            result.instruction.operand_count > 0U ? (unsigned)form_operands[0].value : 0U,
            result.instruction.operand_count > 1U ? (unsigned)form_operands[1].kind : 0U,
            result.instruction.operand_count > 1U ? (unsigned)form_operands[1].ea_mode : 0U,
            result.instruction.operand_count > 1U ? (unsigned)form_operands[1].value : 0U);
        return result;
    }
    symbol_result = m68k_ir_apply_symbol_refs(&ir_resolve_context, result.instruction, &g_m68k_asm_forms[asm_form_index],
        instruction_offset, line_number, allow_undefined, diagnostics);
    if (!symbol_result.ok) return result;
    result.instruction = symbol_result.instruction;
    for (operand_index = 0; operand_index < result.instruction.operand_count && operand_index < 4U; ++operand_index) {
        form_operands[operand_index] = result.instruction.operands[operand_index].value;
    }
    asm_form_index = m68k_asm_form_index_for_operands_id(result.instruction.mnemonic_id, form_operands,
        result.instruction.operand_count, requested_size_suffix, result.instruction.target_cpu);
    if (g_m68k_asm_forms[asm_form_index].mnemonic_id == M68K_ASM_MNEMONIC_NONE) {
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_SOURCE_FAILED,
            "failed resolving symbolic instruction form");
        return result;
    }
    if (normalize_symbolic_zero_address_displacements_local(context, &result.instruction)) {
        for (operand_index = 0; operand_index < result.instruction.operand_count && operand_index < 4U; ++operand_index) {
            form_operands[operand_index] = result.instruction.operands[operand_index].value;
        }
        asm_form_index = m68k_asm_form_index_for_operands_id(result.instruction.mnemonic_id, form_operands,
            result.instruction.operand_count, requested_size_suffix, result.instruction.target_cpu);
        if (g_m68k_asm_forms[asm_form_index].mnemonic_id == M68K_ASM_MNEMONIC_NONE) {
            m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_SOURCE_FAILED,
                "failed resolving zero displacement instruction form");
            return result;
        }
    }
    result.instruction.asm_form_index = asm_form_index;
    result.instruction.canonical_form_id = g_m68k_asm_forms[asm_form_index].canonical_form_id;
    for (operand_index = 0; operand_index < result.instruction.operand_count; ++operand_index) {
        const M68kOperandIR *operand = &result.instruction.operands[operand_index];
        if (!operand->symbol_ref.has_name) continue;
        if (!operand->symbol_ref.has_section) continue;
        if (operand->value.kind == M68K_ASM_OPERAND_EA
            && operand->value.ea_mode == 7
            && (operand->value.ea_reg == 2 || operand->value.ea_reg == 3)) {
            continue;
        }
        if (operand->value.kind == M68K_ASM_OPERAND_LABEL) continue;
        if (result.abs_fixups.count < M68K_SOURCE_RESOLVE_MAX_ABS_FIXUP_OPERANDS) {
            result.abs_fixups.operands[result.abs_fixups.count] = (uint8_t)operand_index;
            result.abs_fixups.count += 1U;
        }
    }
    result.ok = 1;
    return result;
}


