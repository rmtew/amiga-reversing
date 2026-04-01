#include "m68k_source_resolve_rewrite.h"

#include "m68k_plain_parse.h"

#include "platform_common.h"

#include <stdio.h>
#include <string.h>


#define M68K_SOURCE_RESOLVE_MAX_CASE_BYTES 64

static size_t pc_relative_ea_base_offset_local(const M68kAsmFormDef *form,
    const InstructionSpec *instruction, size_t operand_index) {
    size_t base_offset = 2U;
    size_t index;
    if (form != NULL) {
        base_offset += (size_t)form->bound_word_count * 2U;
    }
    if (instruction == NULL) return base_offset;
    for (index = 0; index <= operand_index && index < instruction->operand_count; ++index) {
        base_offset += m68k_asm_operand_extension_word_count(form, &instruction->operands[index],
            instruction->size_suffix) * 2U;
    }
    return base_offset;
}

static int encode_instruction_with_form_local(const InstructionSpec *instruction, const M68kAsmFormDef *form,
    char requested_size_suffix, unsigned char *out_bytes, size_t max_bytes, size_t *out_byte_count,
    char *out_error, size_t out_error_size) {
    InstructionSpec working = *instruction;
    M68kAsmInstructionSpec spec;
    if (working.size_suffix == '\0') working.size_suffix = requested_size_suffix;
    if (form->bound_word_count != 0U && working.patch_value_count < (size_t)form->bound_word_count) {
        m68k_platform_set_error(out_error, out_error_size, "missing patch values for form");
        return 0;
    }
    if (m68k_instruction_spec_uses_movem_predecrement_mask(&working)) {
        working.operands[0].value = m68k_reverse_reglist_mask((uint16_t)working.operands[0].value);
    }
    spec.mnemonic = working.mnemonic;
    spec.size_suffix = working.size_suffix;
    spec.target_cpu = working.target_cpu;
    spec.operand_count = working.operand_count;
    spec.patch_values = working.patch_values;
    spec.patch_value_count = working.patch_value_count;
    spec.operands = working.operands;
    if (m68k_asm_assemble_instruction(&spec, out_bytes, max_bytes, out_byte_count) != 0) {
        m68k_platform_set_error(out_error, out_error_size, "assemble instruction failed");
        return 0;
    }
    return 1;
}

int m68k_try_rewrite_local_call_to_branch(const M68kSourceResolveRewriteContext *context,
    size_t stmt_section_index, char requested_size_suffix, InstructionSpec *instruction,
    const M68kAsmFormDef **out_form, uint32_t instruction_offset, char *out_error, size_t out_error_size) {
    const char *branch_mnemonic = NULL;
    const char *label_name = NULL;
    uint32_t symbol_value = 0;
    size_t symbol_section_index = (size_t)-1;
    int symbol_defined = 0;
    int32_t displacement = 0;
    char branch_text[64];
    InstructionSpec candidate;
    const M68kAsmFormDef *candidate_form = NULL;
    unsigned char bytes[M68K_SOURCE_RESOLVE_MAX_CASE_BYTES];
    size_t byte_count = 0;
    if (instruction->operand_count != 1U) return 0;
    if (_stricmp(instruction->mnemonic, "jsr") == 0) {
        branch_mnemonic = "bsr";
    } else if (_stricmp(instruction->mnemonic, "jmp") == 0) {
        branch_mnemonic = "bra";
    } else {
        return 0;
    }
    label_name = instruction->operand_label_names[0];
    if (label_name[0] == '\0') return 0;
    if (!context->lookup_symbol(label_name, &symbol_value, &symbol_section_index, &symbol_defined, context->user_data)
        || !symbol_defined
        || symbol_section_index != stmt_section_index) {
        return 0;
    }
    displacement = (int32_t)symbol_value - (int32_t)(instruction_offset + 2U);
    if (displacement < -32768 || displacement > 32767) return 0;
    snprintf(branch_text, sizeof(branch_text), "%s %d", branch_mnemonic, (int)displacement);
    if (!m68k_plain_parse_instruction_to_spec(branch_text, instruction->target_cpu, &candidate)) return 0;
    candidate_form = m68k_asm_find_form_for_operands(candidate.mnemonic, candidate.operands,
        candidate.operand_count, requested_size_suffix, candidate.target_cpu);
    if (candidate_form == NULL) return 0;
    if (!encode_instruction_with_form_local(&candidate, candidate_form, requested_size_suffix,
            bytes, sizeof(bytes), &byte_count, out_error, out_error_size)) {
        return 0;
    }
    *instruction = candidate;
    *out_form = candidate_form;
    return 1;
}

void m68k_try_rewrite_local_ea_symbols_to_pc_relative(const M68kSourceResolveRewriteContext *context,
    size_t stmt_section_index, char requested_size_suffix, InstructionSpec *instruction,
    const M68kAsmFormDef **out_form, uint32_t instruction_offset, char *out_error, size_t out_error_size) {
    size_t operand_index;
    unsigned char current_bytes[M68K_SOURCE_RESOLVE_MAX_CASE_BYTES];
    size_t current_size = 0;
    if (!encode_instruction_with_form_local(instruction, *out_form, requested_size_suffix,
            current_bytes, sizeof(current_bytes), &current_size, out_error, out_error_size)) {
        return;
    }
    for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
        const char *label_name = instruction->operand_label_names[operand_index];
        uint32_t symbol_value = 0;
        size_t symbol_section_index = (size_t)-1;
        int symbol_defined = 0;
        InstructionSpec candidate;
        const M68kAsmFormDef *candidate_form = NULL;
        unsigned char candidate_bytes[M68K_SOURCE_RESOLVE_MAX_CASE_BYTES];
        size_t candidate_size = 0;
        int32_t displacement = 0;
        if (label_name[0] == '\0') continue;
        if (instruction->operands[operand_index].kind != M68K_ASM_OPERAND_EA) continue;
        if (!context->lookup_symbol(label_name, &symbol_value, &symbol_section_index, &symbol_defined, context->user_data)
            || !symbol_defined
            || symbol_section_index != stmt_section_index) {
            continue;
        }
        candidate = *instruction;
        candidate.operands[operand_index].ea_mode = 7;
        candidate.operands[operand_index].ea_reg = 2;
        candidate.operands[operand_index].value = 0U;
        candidate_form = m68k_asm_find_form_for_operands(candidate.mnemonic, candidate.operands,
            candidate.operand_count, requested_size_suffix, candidate.target_cpu);
        if (candidate_form == NULL) continue;
        displacement = (int32_t)symbol_value
            - (int32_t)(instruction_offset +
                pc_relative_ea_base_offset_local(candidate_form, &candidate, operand_index));
        if (displacement < -32768 || displacement > 32767) continue;
        candidate.operands[operand_index].value = (uint32_t)displacement;
        if (!encode_instruction_with_form_local(&candidate, candidate_form, requested_size_suffix,
                candidate_bytes, sizeof(candidate_bytes), &candidate_size, out_error, out_error_size)) {
            continue;
        }
        if (candidate_size >= current_size) continue;
        *instruction = candidate;
        *out_form = candidate_form;
        current_size = candidate_size;
    }
}


