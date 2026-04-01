#ifndef M68K_CORPUS_SUPPORT_H
#define M68K_CORPUS_SUPPORT_H

#include "m68k_instruction_spec.h"

#include <stddef.h>
#include <stdint.h>

#define M68K_CORPUS_MAX_CASE_BYTES 64
#define M68K_CORPUS_MAX_CASE_INSTRUCTIONS 8

typedef struct {
  char case_id[96];
  InstructionSpec instructions[M68K_CORPUS_MAX_CASE_INSTRUCTIONS];
  size_t instruction_count;
  unsigned char expected_bytes[M68K_CORPUS_MAX_CASE_BYTES];
  size_t expected_size;
} M68kCorpusCase;

typedef int (*M68kCorpusParseInstructionSpecFn)(char *text, InstructionSpec *out_spec);

int m68k_corpus_verify_binary(const char *manifest_path, const char *binary_path, uint8_t target_cpu,
  M68kCorpusParseInstructionSpecFn parse_instruction_spec_fn);
int m68k_corpus_verify_manifest(const char *manifest_path, uint8_t target_cpu,
  M68kCorpusParseInstructionSpecFn parse_instruction_spec_fn);
int m68k_corpus_assemble_case_to_stdout(const char *manifest_path, const char *case_id, uint8_t target_cpu,
  M68kCorpusParseInstructionSpecFn parse_instruction_spec_fn);
int m68k_corpus_assemble_manifest_to_file(const char *manifest_path, const char *output_path, uint8_t target_cpu,
  M68kCorpusParseInstructionSpecFn parse_instruction_spec_fn);

#endif
