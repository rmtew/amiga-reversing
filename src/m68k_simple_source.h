#ifndef M68K_SIMPLE_SOURCE_H
#define M68K_SIMPLE_SOURCE_H

#include "m68k_instruction_spec.h"

#include <stddef.h>
#include <stdint.h>

typedef int (*M68kSimpleSourceParseInstructionFn)(const char *line_text, InstructionSpec *out_instruction,
    int allow_label_symbols, uint8_t target_cpu);

int m68k_simple_source_assemble_file_to_binary(const char *input_path, const char *output_path, uint8_t target_cpu,
    M68kSimpleSourceParseInstructionFn parse_instruction_fn);
int m68k_simple_source_assemble_text(const char *source_text, uint8_t target_cpu, uint8_t *out_bytes, size_t max_bytes,
    size_t *out_byte_count, char *out_error, size_t out_error_size, M68kSimpleSourceParseInstructionFn parse_instruction_fn);

#endif
