#include "m68k_simple_source.h"

#include "m68k_assembler.h"
#include "m68k_source_text_util.h"

#include "platform_common.h"

#include <ctype.h>
#include <stdio.h>
#include <string.h>


#define MAX_CASE_BYTES 64
#define MAX_SOURCE_LINES 256
#define MAX_LABELS 256
#define MAX_LABEL_NAME 64

typedef struct {
    char name[MAX_LABEL_NAME];
    size_t offset;
} LabelDef;

typedef struct {
    int has_label;
    int has_instruction;
    char label_name[MAX_LABEL_NAME];
    InstructionSpec instruction;
    size_t offset;
} SourceLine;

static int simple_is_symbol_name(const char *text) {
    size_t index;
    if (text == NULL || text[0] == '\0') return 0;
    if (!(isalpha((unsigned char)text[0]) || text[0] == '_')) return 0;
    for (index = 1; text[index] != '\0'; ++index) {
        if (!(isalnum((unsigned char)text[index]) || text[index] == '_')) return 0;
    }
    return 1;
}

static int parse_source_line(const char *line_text, SourceLine *out_line, uint8_t target_cpu,
    M68kSimpleSourceParseInstructionFn parse_instruction_fn) {
    char line[256];
    char *comment;
    char *colon;
    char *rest;
    memset(out_line, 0, sizeof(*out_line));
    strcpy(line, line_text);
    comment = strchr(line, ';');
    if (comment != NULL) *comment = '\0';
    rest = m68k_trim_in_place(line);
    if (*rest == '\0') return 0;
    colon = strchr(rest, ':');
    if (colon != NULL) {
        *colon = '\0';
        strcpy(out_line->label_name, m68k_trim_in_place(rest));
        if (!simple_is_symbol_name(out_line->label_name)) return -1;
        out_line->has_label = 1;
        rest = m68k_trim_in_place(colon + 1);
    }
    if (*rest != '\0') {
        if (!parse_instruction_fn(rest, &out_line->instruction, 1, target_cpu)) return -1;
        out_line->has_instruction = 1;
    }
    return out_line->has_label || out_line->has_instruction;
}

static size_t find_label_offset(const LabelDef *labels, size_t label_count, const char *name, int *found) {
    size_t index;
    for (index = 0; index < label_count; ++index) {
        if (strcmp(labels[index].name, name) == 0) {
            *found = 1;
            return labels[index].offset;
        }
    }
    *found = 0;
    return 0;
}

static int estimate_instruction_size(const InstructionSpec *instruction, size_t *out_size) {
    unsigned char bytes[MAX_CASE_BYTES];
    *out_size = m68k_instruction_spec_assemble_bytes(instruction, bytes, MAX_CASE_BYTES);
    return 1;
}
static int resolve_instruction_labels(InstructionSpec *instruction, size_t instruction_offset,
    const LabelDef *labels, size_t label_count) {
    size_t operand_index;
    uint16_t asm_form_index = m68k_asm_form_index_for_operands_id(instruction->mnemonic_id,
        instruction->operands, instruction->operand_count, instruction->size_suffix, instruction->target_cpu);
    const M68kAsmFormDef *form = &g_m68k_asm_forms[asm_form_index];
    if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) return 0;
    for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
        int found = 0;
        size_t target_offset;
        M68kAsmOperandValue *operand = &instruction->operands[operand_index];
        if (instruction->operand_label_names[operand_index][0] == '\0') continue;
        target_offset = find_label_offset(labels, label_count, instruction->operand_label_names[operand_index], &found);
        if (!found) return 0;
        if (instruction->operand_label_ref_kinds[operand_index] == M68K_IR_SYMBOL_REF_ABS) {
            if (operand->kind == M68K_ASM_OPERAND_LABEL) {
                operand->kind = M68K_ASM_OPERAND_EA;
                operand->ea_mode = 7;
                operand->ea_reg = instruction->size_suffix == 'l' ? 1 : 0;
            }
            operand->value = (uint32_t)target_offset;
        } else if (operand->kind == M68K_ASM_OPERAND_EA &&
            ((operand->ea_mode == 7 && operand->ea_reg == 2) || (operand->ea_mode == 7 && operand->ea_reg == 3))) {
            operand->value = (uint32_t)(target_offset - (instruction_offset +
                m68k_asm_operand_relative_base_offset(asm_form_index, instruction->operands,
                    instruction->operand_count, instruction->size_suffix, operand_index, 0)));
        } else {
            operand->value = (uint32_t)(target_offset - (instruction_offset + 2U));
        }
    }
    asm_form_index = m68k_asm_form_index_for_operands_id(instruction->mnemonic_id,
        instruction->operands, instruction->operand_count, instruction->size_suffix, instruction->target_cpu);
    form = &g_m68k_asm_forms[asm_form_index];
    if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) return 0;
    if (m68k_asm_build_patch_values(asm_form_index, instruction->size_suffix, instruction->operands,
        instruction->operand_count, instruction->patch_values, M68K_INSTRUCTION_SPEC_MAX_PATCH_VALUES) != 0) {
        return 0;
    }
    instruction->patch_value_count = form->patch_count;
    return 1;
}

static M68kSimpleSourceAssembleResult assemble_source_lines_to_bytes(const SourceLine *lines, size_t line_count,
    uint8_t *out_bytes, size_t max_bytes, M68kDiagSink diagnostics) {
    M68kSimpleSourceAssembleResult result;
    LabelDef labels[MAX_LABELS];
    size_t label_count = 0;
    size_t offset = 0;
    size_t output_offset = 0;
    size_t index;
    memset(&result, 0, sizeof(result));
    for (index = 0; index < line_count; ++index) {
        size_t instruction_size = 0;
        if (lines[index].has_label) {
            if (label_count >= MAX_LABELS) {
                m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_ENCODE_FAILED,
                    "too many labels");
                return result;
            }
            strcpy(labels[label_count].name, lines[index].label_name);
            labels[label_count].offset = offset;
            ++label_count;
        }
        if (!lines[index].has_instruction) continue;
        if (!estimate_instruction_size(&lines[index].instruction, &instruction_size)) {
            m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_ENCODE_FAILED,
                "unable to size instruction");
            return result;
        }
        offset += instruction_size;
    }
    for (index = 0; index < line_count; ++index) {
        unsigned char bytes[MAX_CASE_BYTES];
        size_t size = 0;
        SourceLine line = lines[index];
        if (!line.has_instruction) continue;
        if (!resolve_instruction_labels(&line.instruction, line.offset, labels, label_count)) {
            m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_ENCODE_FAILED,
                "unable to resolve labels");
            return result;
        }
        size = m68k_instruction_spec_assemble_bytes(&line.instruction, bytes, MAX_CASE_BYTES);
        if (output_offset + size > max_bytes) {
            m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_ENCODE_FAILED,
                "output buffer too small");
            return result;
        }
        memcpy(out_bytes + output_offset, bytes, size);
        output_offset += size;
    }
    result.byte_count = output_offset;
    return result;
}

int m68k_simple_source_assemble_file_to_binary(const char *input_path, const char *output_path, uint8_t target_cpu,
    M68kSimpleSourceParseInstructionFn parse_instruction_fn) {
    FILE *input = fopen(input_path, "r");
    FILE *output = fopen(output_path, "wb");
    char line[256];
    SourceLine lines[MAX_SOURCE_LINES];
    LabelDef labels[MAX_LABELS];
    size_t line_count = 0;
    size_t label_count = 0;
    size_t offset = 0;
    size_t index;
    if (input == NULL || output == NULL || parse_instruction_fn == NULL) {
        fprintf(stderr, "unable to open input/output\n");
        return 1;
    }
    while (fgets(line, sizeof(line), input) != NULL) {
        int parse_result;
        if (line_count >= MAX_SOURCE_LINES) {
            fclose(output);
            fclose(input);
            fprintf(stderr, "too many source lines\n");
            return 1;
        }
        parse_result = parse_source_line(line, &lines[line_count], target_cpu, parse_instruction_fn);
        if (parse_result < 0) {
            fclose(output);
            fclose(input);
            fprintf(stderr, "unable to parse source line\n");
            return 1;
        }
        if (parse_result == 0) continue;
        lines[line_count].offset = offset;
        if (lines[line_count].has_label) {
            if (label_count >= MAX_LABELS) {
                fclose(output);
                fclose(input);
                fprintf(stderr, "too many labels\n");
                return 1;
            }
            strcpy(labels[label_count].name, lines[line_count].label_name);
            labels[label_count].offset = offset;
            ++label_count;
        }
        if (lines[line_count].has_instruction) {
            size_t instruction_size = 0;
            if (!estimate_instruction_size(&lines[line_count].instruction, &instruction_size)) {
                fclose(output);
                fclose(input);
                fprintf(stderr, "unable to size instruction\n");
                return 1;
            }
            offset += instruction_size;
        }
        ++line_count;
    }
    for (index = 0; index < line_count; ++index) {
        unsigned char bytes[MAX_CASE_BYTES];
        size_t size;
        if (!lines[index].has_instruction) continue;
        if (!resolve_instruction_labels(&lines[index].instruction, lines[index].offset, labels, label_count)) {
            fclose(output);
            fclose(input);
            fprintf(stderr, "unable to resolve labels\n");
            return 1;
        }
        size = m68k_instruction_spec_assemble_bytes(&lines[index].instruction, bytes, MAX_CASE_BYTES);
        if (fwrite(bytes, 1, size, output) != size) {
            fclose(output);
            fclose(input);
            fprintf(stderr, "write failed\n");
            return 1;
        }
    }
    fclose(output);
    fclose(input);
    return 0;
}

M68kSimpleSourceAssembleResult m68k_simple_source_assemble_text(const char *source_text, uint8_t target_cpu,
    uint8_t *out_bytes, size_t max_bytes, M68kDiagSink diagnostics,
    M68kSimpleSourceParseInstructionFn parse_instruction_fn) {
    SourceLine lines[MAX_SOURCE_LINES];
    M68kSimpleSourceAssembleResult result;
    char buffer[8192];
    char *line_start = buffer;
    char *cursor = buffer;
    size_t line_count = 0;
    size_t offset = 0;
    int parse_result = 0;
    memset(&result, 0, sizeof(result));
    if (source_text == NULL || parse_instruction_fn == NULL) {
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_BAD_ARGUMENT, "source text is null");
        return result;
    }
    if (strlen(source_text) >= sizeof(buffer)) {
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_ENCODE_FAILED,
            "source text too large");
        return result;
    }
    strcpy(buffer, source_text);
    while (1) {
        if (*cursor == '\r') {
            *cursor = '\0';
        } else if (*cursor == '\n' || *cursor == '\0') {
            char saved = *cursor;
            *cursor = '\0';
            if (line_count >= MAX_SOURCE_LINES) {
                m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_ENCODE_FAILED,
                    "too many source lines");
                return result;
            }
            parse_result = parse_source_line(line_start, &lines[line_count], target_cpu, parse_instruction_fn);
            if (parse_result < 0) {
                m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_DECODE_FAILED,
                    "unable to parse source line");
                return result;
            }
            if (parse_result > 0) {
                lines[line_count].offset = offset;
                if (lines[line_count].has_instruction) {
                    size_t instruction_size = 0;
                    if (!estimate_instruction_size(&lines[line_count].instruction, &instruction_size)) {
                        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_ENCODE_FAILED,
                            "unable to size instruction");
                        return result;
                    }
                    offset += instruction_size;
                }
                ++line_count;
            }
            if (saved == '\0') break;
            line_start = cursor + 1;
        }
        ++cursor;
    }
    return assemble_source_lines_to_bytes(lines, line_count, out_bytes, max_bytes, diagnostics);
}


