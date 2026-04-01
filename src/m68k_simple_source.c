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

static size_t pc_relative_ea_base_offset(const M68kAsmFormDef *form,
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

static int resolve_instruction_labels(InstructionSpec *instruction, size_t instruction_offset,
    const LabelDef *labels, size_t label_count) {
    size_t operand_index;
    const M68kAsmFormDef *form = m68k_asm_find_form_for_operands(instruction->mnemonic,
        instruction->operands, instruction->operand_count, instruction->size_suffix, instruction->target_cpu);
    if (form == NULL) return 0;
    for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
        int found = 0;
        size_t target_offset;
        M68kAsmOperandValue *operand = &instruction->operands[operand_index];
        if (instruction->operand_label_names[operand_index][0] == '\0') continue;
        target_offset = find_label_offset(labels, label_count, instruction->operand_label_names[operand_index], &found);
        if (!found) return 0;
        if (operand->kind == M68K_ASM_OPERAND_EA &&
            ((operand->ea_mode == 7 && operand->ea_reg == 2) || (operand->ea_mode == 7 && operand->ea_reg == 3))) {
            operand->value = (uint32_t)(target_offset - (instruction_offset +
                pc_relative_ea_base_offset(form, instruction, operand_index)));
        } else {
            operand->value = (uint32_t)(target_offset - (instruction_offset + 2U));
        }
    }
    if (m68k_asm_build_patch_values(form, instruction->size_suffix, instruction->operands,
        instruction->operand_count, instruction->patch_values, M68K_INSTRUCTION_SPEC_MAX_PATCH_VALUES) != 0) {
        return 0;
    }
    instruction->patch_value_count = form->patch_count;
    return 1;
}

static int assemble_source_lines_to_bytes(const SourceLine *lines, size_t line_count, uint8_t *out_bytes, size_t max_bytes,
    size_t *out_byte_count, char *out_error, size_t out_error_size) {
    LabelDef labels[MAX_LABELS];
    size_t label_count = 0;
    size_t offset = 0;
    size_t output_offset = 0;
    size_t index;
    for (index = 0; index < line_count; ++index) {
        size_t instruction_size = 0;
        if (lines[index].has_label) {
            if (label_count >= MAX_LABELS) {
                m68k_platform_set_error(out_error, out_error_size, "too many labels");
                return -1;
            }
            strcpy(labels[label_count].name, lines[index].label_name);
            labels[label_count].offset = offset;
            ++label_count;
        }
        if (!lines[index].has_instruction) continue;
        if (!estimate_instruction_size(&lines[index].instruction, &instruction_size)) {
            m68k_platform_set_error(out_error, out_error_size, "unable to size instruction");
            return -1;
        }
        offset += instruction_size;
    }
    for (index = 0; index < line_count; ++index) {
        unsigned char bytes[MAX_CASE_BYTES];
        size_t size = 0;
        SourceLine line = lines[index];
        if (!line.has_instruction) continue;
        if (!resolve_instruction_labels(&line.instruction, line.offset, labels, label_count)) {
            m68k_platform_set_error(out_error, out_error_size, "unable to resolve labels");
            return -1;
        }
        size = m68k_instruction_spec_assemble_bytes(&line.instruction, bytes, MAX_CASE_BYTES);
        if (output_offset + size > max_bytes) {
            m68k_platform_set_error(out_error, out_error_size, "output buffer too small");
            return -1;
        }
        memcpy(out_bytes + output_offset, bytes, size);
        output_offset += size;
    }
    m68k_platform_set_error(out_error, out_error_size, "");
    if (out_byte_count != NULL) *out_byte_count = output_offset;
    return 0;
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

int m68k_simple_source_assemble_text(const char *source_text, uint8_t target_cpu, uint8_t *out_bytes, size_t max_bytes,
    size_t *out_byte_count, char *out_error, size_t out_error_size, M68kSimpleSourceParseInstructionFn parse_instruction_fn) {
    SourceLine lines[MAX_SOURCE_LINES];
    char buffer[8192];
    char *line_start = buffer;
    char *cursor = buffer;
    size_t line_count = 0;
    size_t offset = 0;
    int parse_result = 0;
    if (source_text == NULL || parse_instruction_fn == NULL) {
        m68k_platform_set_error(out_error, out_error_size, "source text is null");
        if (out_byte_count != NULL) *out_byte_count = 0U;
        return -1;
    }
    if (strlen(source_text) >= sizeof(buffer)) {
        m68k_platform_set_error(out_error, out_error_size, "source text too large");
        if (out_byte_count != NULL) *out_byte_count = 0U;
        return -1;
    }
    strcpy(buffer, source_text);
    while (1) {
        if (*cursor == '\r') {
            *cursor = '\0';
        } else if (*cursor == '\n' || *cursor == '\0') {
            char saved = *cursor;
            *cursor = '\0';
            if (line_count >= MAX_SOURCE_LINES) {
                m68k_platform_set_error(out_error, out_error_size, "too many source lines");
                if (out_byte_count != NULL) *out_byte_count = 0U;
                return -1;
            }
            parse_result = parse_source_line(line_start, &lines[line_count], target_cpu, parse_instruction_fn);
            if (parse_result < 0) {
                m68k_platform_set_error(out_error, out_error_size, "unable to parse source line");
                if (out_byte_count != NULL) *out_byte_count = 0U;
                return -1;
            }
            if (parse_result > 0) {
                lines[line_count].offset = offset;
                if (lines[line_count].has_instruction) {
                    size_t instruction_size = 0;
                    if (!estimate_instruction_size(&lines[line_count].instruction, &instruction_size)) {
                        m68k_platform_set_error(out_error, out_error_size, "unable to size instruction");
                        if (out_byte_count != NULL) *out_byte_count = 0U;
                        return -1;
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
    return assemble_source_lines_to_bytes(lines, line_count, out_bytes, max_bytes, out_byte_count, out_error, out_error_size);
}


