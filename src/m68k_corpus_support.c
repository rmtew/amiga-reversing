#include "m68k_corpus_support.h"
#include "m68k_source_text_util.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned hex_nibble(char ch) {
  if (ch >= '0' && ch <= '9') return (unsigned)(ch - '0');
  ch = (char)tolower((unsigned char)ch);
  if (ch >= 'a' && ch <= 'f') return (unsigned)(10 + (ch - 'a'));
  fprintf(stderr, "invalid hex nibble: %c\n", ch);
  exit(1);
}

static size_t parse_hex_bytes(const char *text, unsigned char *out_bytes) {
  size_t size;
  size_t index;
  if (*text == '\0' || strcmp(text, "-") == 0) return 0;
  size = strlen(text) / 2;
  for (index = 0; index < size; ++index) {
    out_bytes[index] = (unsigned char)((hex_nibble(text[index * 2]) << 4)
      | hex_nibble(text[index * 2 + 1]));
  }
  return size;
}

static int parse_case_line(char *line, M68kCorpusCase *out_case, uint8_t target_cpu,
  M68kCorpusParseInstructionSpecFn parse_instruction_spec_fn) {
  char *parts[3 + M68K_CORPUS_MAX_CASE_INSTRUCTIONS];
  size_t count = m68k_split_delimited_in_place(line, '|', parts, sizeof(parts) / sizeof(parts[0]));
  if (count < 3 || parse_instruction_spec_fn == NULL) return 0;
  strcpy(out_case->case_id, parts[0]);
  out_case->expected_size = parse_hex_bytes(parts[1], out_case->expected_bytes);
  out_case->instruction_count = (size_t)strtoul(parts[2], NULL, 10);
  if (count != 3 + out_case->instruction_count) return 0;
  {
    size_t index;
    for (index = 0; index < out_case->instruction_count; ++index) {
      if (!parse_instruction_spec_fn(parts[3 + index], &out_case->instructions[index])) return 0;
      out_case->instructions[index].target_cpu = target_cpu;
    }
  }
  return 1;
}

static size_t assemble_case_bytes(const M68kCorpusCase *corpus_case, unsigned char *out_bytes) {
  size_t case_offset = 0;
  size_t index;
  for (index = 0; index < corpus_case->instruction_count; ++index) {
    case_offset += m68k_instruction_spec_assemble_bytes(&corpus_case->instructions[index],
      out_bytes + case_offset, M68K_CORPUS_MAX_CASE_BYTES);
  }
  return case_offset;
}

int m68k_corpus_verify_binary(const char *manifest_path, const char *binary_path, uint8_t target_cpu,
  M68kCorpusParseInstructionSpecFn parse_instruction_spec_fn) {
  FILE *manifest = fopen(manifest_path, "r");
  FILE *binary = fopen(binary_path, "rb");
  char line[1024];
  if (manifest == NULL || binary == NULL) {
    fprintf(stderr, "unable to open corpus files\n");
    return 1;
  }
  while (fgets(line, sizeof(line), manifest) != NULL) {
    M68kCorpusCase corpus_case;
    unsigned char actual_bytes[M68K_CORPUS_MAX_CASE_BYTES];
    unsigned char oracle_bytes[M68K_CORPUS_MAX_CASE_BYTES];
    size_t actual_size;
    char *trimmed = m68k_trim_in_place(line);
    size_t index;
    if (*trimmed == '\0') continue;
    if (!parse_case_line(trimmed, &corpus_case, target_cpu, parse_instruction_spec_fn)) {
      fprintf(stderr, "bad manifest line\n");
      return 1;
    }
    actual_size = assemble_case_bytes(&corpus_case, actual_bytes);
    if (actual_size != corpus_case.expected_size || memcmp(actual_bytes, corpus_case.expected_bytes, corpus_case.expected_size) != 0) {
      fprintf(stderr, "case mismatch: %s\nexpected:", corpus_case.case_id);
      for (index = 0; index < corpus_case.expected_size; ++index) fprintf(stderr, " %02x", corpus_case.expected_bytes[index]);
      fprintf(stderr, "\nactual:");
      for (index = 0; index < actual_size; ++index) fprintf(stderr, " %02x", actual_bytes[index]);
      fprintf(stderr, "\n");
      return 1;
    }
    if (fread(oracle_bytes, 1, corpus_case.expected_size, binary) != corpus_case.expected_size) {
      fprintf(stderr, "oracle binary too short\n");
      return 1;
    }
    if (memcmp(oracle_bytes, corpus_case.expected_bytes, corpus_case.expected_size) != 0) {
      fprintf(stderr, "oracle mismatch: %s\n", corpus_case.case_id);
      return 1;
    }
  }
  fclose(binary);
  fclose(manifest);
  return 0;
}

int m68k_corpus_verify_manifest(const char *manifest_path, uint8_t target_cpu,
    M68kCorpusParseInstructionSpecFn parse_instruction_spec_fn) {
  FILE *manifest = fopen(manifest_path, "r");
  char line[1024];
  if (manifest == NULL) {
    fprintf(stderr, "unable to open manifest\n");
    return 1;
  }
  while (fgets(line, sizeof(line), manifest) != NULL) {
    M68kCorpusCase corpus_case;
    unsigned char actual_bytes[M68K_CORPUS_MAX_CASE_BYTES];
    size_t actual_size;
    size_t index;
    char *trimmed = m68k_trim_in_place(line);
    if (*trimmed == '\0') continue;
    if (!parse_case_line(trimmed, &corpus_case, target_cpu, parse_instruction_spec_fn)) {
      fclose(manifest);
      fprintf(stderr, "bad manifest line\n");
      return 1;
    }
    actual_size = assemble_case_bytes(&corpus_case, actual_bytes);
    if (actual_size != corpus_case.expected_size ||
        memcmp(actual_bytes, corpus_case.expected_bytes, corpus_case.expected_size) != 0) {
      fclose(manifest);
      fprintf(stderr, "case mismatch: %s\nexpected:", corpus_case.case_id);
      for (index = 0; index < corpus_case.expected_size; ++index)
        fprintf(stderr, " %02x", corpus_case.expected_bytes[index]);
      fprintf(stderr, "\nactual:");
      for (index = 0; index < actual_size; ++index) fprintf(stderr, " %02x", actual_bytes[index]);
      fprintf(stderr, "\n");
      return 1;
    }
  }
  fclose(manifest);
  return 0;
}

int m68k_corpus_assemble_case_to_stdout(const char *manifest_path, const char *case_id, uint8_t target_cpu,
    M68kCorpusParseInstructionSpecFn parse_instruction_spec_fn) {
  FILE *manifest = fopen(manifest_path, "r");
  char line[1024];
  if (manifest == NULL) {
    fprintf(stderr, "unable to open manifest\n");
    return 1;
  }
  while (fgets(line, sizeof(line), manifest) != NULL) {
    M68kCorpusCase corpus_case;
    unsigned char actual_bytes[M68K_CORPUS_MAX_CASE_BYTES];
    size_t actual_size;
    size_t index;
    char *trimmed = m68k_trim_in_place(line);
    if (*trimmed == '\0') continue;
    if (!parse_case_line(trimmed, &corpus_case, target_cpu, parse_instruction_spec_fn)) {
      fclose(manifest);
      fprintf(stderr, "bad manifest line\n");
      return 1;
    }
    if (strcmp(corpus_case.case_id, case_id) != 0) continue;
    actual_size = assemble_case_bytes(&corpus_case, actual_bytes);
    for (index = 0; index < actual_size; ++index) printf("%02x", actual_bytes[index]);
    printf("\n");
    fclose(manifest);
    return 0;
  }
  fclose(manifest);
  fprintf(stderr, "unknown case id: %s\n", case_id);
  return 1;
}

int m68k_corpus_assemble_manifest_to_file(const char *manifest_path, const char *output_path, uint8_t target_cpu,
    M68kCorpusParseInstructionSpecFn parse_instruction_spec_fn) {
  FILE *manifest = fopen(manifest_path, "r");
  FILE *output = fopen(output_path, "wb");
  char line[1024];
  if (manifest == NULL || output == NULL) {
    fprintf(stderr, "unable to open manifest/output\n");
    return 1;
  }
  while (fgets(line, sizeof(line), manifest) != NULL) {
    M68kCorpusCase corpus_case;
    unsigned char actual_bytes[M68K_CORPUS_MAX_CASE_BYTES];
    size_t actual_size;
    char *trimmed = m68k_trim_in_place(line);
    if (*trimmed == '\0') continue;
    if (!parse_case_line(trimmed, &corpus_case, target_cpu, parse_instruction_spec_fn)) {
      fclose(output);
      fclose(manifest);
      fprintf(stderr, "bad manifest line\n");
      return 1;
    }
    actual_size = assemble_case_bytes(&corpus_case, actual_bytes);
    if (fwrite(actual_bytes, 1, actual_size, output) != actual_size) {
      fclose(output);
      fclose(manifest);
      fprintf(stderr, "write failed\n");
      return 1;
    }
  }
  fclose(output);
  fclose(manifest);
  return 0;
}
