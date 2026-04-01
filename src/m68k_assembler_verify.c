#include "m68k_assembler_lib.h"

#include "m68k_corpus_spec.h"
#include "m68k_corpus_support.h"

#include "platform_common.h"

#include <stdio.h>


int m68k_verify_manifest(const char *manifest_path, const M68kAsmVerifyOptions *options, char *out_error,
    size_t out_error_size) {
  int result = 0;
  if (options == NULL) {
    m68k_platform_set_error(out_error, out_error_size, "verify options are null");
    return -1;
  }
  result = m68k_corpus_verify_manifest(manifest_path, options->target_cpu, m68k_corpus_parse_instruction_spec);
  if (result != 0) {
    m68k_platform_set_error(out_error, out_error_size, "verify manifest failed");
    return -1;
  }
  m68k_platform_set_error(out_error, out_error_size, "");
  return 0;
}

int m68k_verify_corpus(const char *manifest_path, const char *binary_path, const M68kAsmVerifyOptions *options, char *out_error,
    size_t out_error_size) {
  int result = 0;
  if (options == NULL) {
    m68k_platform_set_error(out_error, out_error_size, "verify options are null");
    return -1;
  }
  result = m68k_corpus_verify_binary(manifest_path, binary_path, options->target_cpu, m68k_corpus_parse_instruction_spec);
  if (result != 0) {
    m68k_platform_set_error(out_error, out_error_size, "verify corpus failed");
    return -1;
  }
  m68k_platform_set_error(out_error, out_error_size, "");
  return 0;
}


