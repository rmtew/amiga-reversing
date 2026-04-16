#include "m68k_assembler_lib.h"

#include "m68k_corpus_spec.h"
#include "m68k_corpus_support.h"

#include <string.h>

M68kVerifyResult m68k_verify_manifest(const char *manifest_path, const M68kAsmVerifyOptions *options) {
  M68kVerifyResult result;
  memset(&result, 0, sizeof(result));
  if (options == NULL) {
    m68k_diag_add(m68k_diag_sink(&result.diagnostics), M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_BAD_ARGUMENT,
      "verify options are null");
    return result;
  }
  if (m68k_corpus_verify_manifest(manifest_path, options->target_cpu, m68k_corpus_parse_instruction_spec) != 0) {
    m68k_diag_add(m68k_diag_sink(&result.diagnostics), M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_ENCODE_FAILED,
      "verify manifest failed");
  }
  return result;
}

M68kVerifyResult m68k_verify_corpus(const char *manifest_path, const char *binary_path,
    const M68kAsmVerifyOptions *options) {
  M68kVerifyResult result;
  memset(&result, 0, sizeof(result));
  if (options == NULL) {
    m68k_diag_add(m68k_diag_sink(&result.diagnostics), M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_BAD_ARGUMENT,
      "verify options are null");
    return result;
  }
  if (m68k_corpus_verify_binary(manifest_path, binary_path, options->target_cpu,
      m68k_corpus_parse_instruction_spec) != 0) {
    m68k_diag_add(m68k_diag_sink(&result.diagnostics), M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_ENCODE_FAILED,
      "verify corpus failed");
  }
  return result;
}
