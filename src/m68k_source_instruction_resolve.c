#include "m68k_source_instruction_resolve.h"

#include "m68k_ir_symbol_resolve.h"
#include "m68k_source_resolve_rewrite.h"

#include "platform_common.h"

#include <stdio.h>
#include <string.h>


static int instruction_uses_movem_predecrement_mask_ir_local(const M68kInstructionIR *instruction) {
    if (instruction == NULL || instruction->operand_count != 2U) return 0;
    if (_stricmp(instruction->mnemonic, "movem") != 0) return 0;
    if (instruction->operands[0].kind != M68K_ASM_OPERAND_REGLIST) return 0;
    if (instruction->operands[1].kind != M68K_ASM_OPERAND_EA) return 0;
    return instruction->operands[1].value.ea_mode == 4U;
}

int m68k_source_resolve_instruction_operands(const M68kSourceInstructionResolveContext *context,
    size_t stmt_section_index, size_t line_number, char requested_size_suffix, uint32_t instruction_offset,
    int allow_undefined, const M68kInstructionIR *parsed_instruction, const M68kAsmFormDef **out_form,
    M68kInstructionIR *out_instruction, int *out_abs_fixup_operands, size_t *out_abs_fixup_count,
    char *out_error, size_t out_error_size) {
    M68kIrResolveContext ir_resolve_context;
    M68kSourceResolveRewriteContext rewrite_context;
    InstructionSpec temp_spec;
    M68kAsmOperandValue form_operands[4];
    size_t operand_index;
    memset(&ir_resolve_context, 0, sizeof(ir_resolve_context));
    memset(&rewrite_context, 0, sizeof(rewrite_context));
    ir_resolve_context.user_data = context->user_data;
    ir_resolve_context.lookup_symbol = context->lookup_symbol;
    rewrite_context.user_data = context->user_data;
    rewrite_context.lookup_symbol = context->lookup_symbol;
    *out_instruction = *parsed_instruction;
    *out_abs_fixup_count = 0U;
    for (operand_index = 0; operand_index < out_instruction->operand_count && operand_index < 4U; ++operand_index) {
        form_operands[operand_index] = out_instruction->operands[operand_index].value;
    }
    if (instruction_uses_movem_predecrement_mask_ir_local(out_instruction)) {
        form_operands[0].value = m68k_reverse_reglist_mask((uint16_t)form_operands[0].value);
    }
    *out_form = m68k_asm_find_form_for_operands(out_instruction->mnemonic, form_operands,
        out_instruction->operand_count, requested_size_suffix, out_instruction->target_cpu);
    if (*out_form == NULL) {
        m68k_platform_set_errorf(out_error, out_error_size,
            "failed resolving instruction form: %s size=%c cpu=%u op0=%u:%u/%u op1=%u:%u/%u",
            out_instruction->mnemonic,
            requested_size_suffix != '\0' ? requested_size_suffix : '-',
            (unsigned)out_instruction->target_cpu,
            out_instruction->operand_count > 0U ? (unsigned)form_operands[0].kind : 0U,
            out_instruction->operand_count > 0U ? (unsigned)form_operands[0].ea_mode : 0U,
            out_instruction->operand_count > 0U ? (unsigned)form_operands[0].value : 0U,
            out_instruction->operand_count > 1U ? (unsigned)form_operands[1].kind : 0U,
            out_instruction->operand_count > 1U ? (unsigned)form_operands[1].ea_mode : 0U,
            out_instruction->operand_count > 1U ? (unsigned)form_operands[1].value : 0U);
        return 0;
    }
    if (!m68k_ir_apply_symbol_refs(&ir_resolve_context, out_instruction, *out_form, instruction_offset,
            line_number, allow_undefined, out_abs_fixup_operands, out_abs_fixup_count,
            out_error, out_error_size)) {
        return 0;
    }
    if (context->enable_vasm_compat_rewrites) {
        m68k_instruction_ir_to_spec(out_instruction, &temp_spec);
        if (m68k_try_rewrite_local_call_to_branch(&rewrite_context, stmt_section_index, requested_size_suffix,
                &temp_spec, out_form, instruction_offset, out_error, out_error_size)) {
            m68k_instruction_spec_to_ir(&temp_spec, out_instruction);
            *out_abs_fixup_count = 0U;
            return 1;
        }
        m68k_try_rewrite_local_ea_symbols_to_pc_relative(&rewrite_context, stmt_section_index, requested_size_suffix,
            &temp_spec, out_form, instruction_offset, out_error, out_error_size);
        m68k_instruction_spec_to_ir(&temp_spec, out_instruction);
    }
    *out_abs_fixup_count = 0U;
    for (operand_index = 0; operand_index < out_instruction->operand_count; ++operand_index) {
        const M68kOperandIR *operand = &out_instruction->operands[operand_index];
        if (!operand->symbol_ref.has_name) continue;
        if (!operand->symbol_ref.has_section) continue;
        if (operand->value.kind == M68K_ASM_OPERAND_EA
            && operand->value.ea_mode == 7
            && (operand->value.ea_reg == 2 || operand->value.ea_reg == 3)) {
            continue;
        }
        if (operand->value.kind == M68K_ASM_OPERAND_LABEL) continue;
        out_abs_fixup_operands[*out_abs_fixup_count] = (int)operand_index;
        *out_abs_fixup_count += 1U;
    }
    return 1;
}


