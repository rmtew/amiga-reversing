#ifndef M68K_ASSEMBLER_LIB_H
#define M68K_ASSEMBLER_LIB_H

#include "m68k_diagnostics.h"
#include "m68k_ir.h"

#include <stddef.h>
#include <stdint.h>

#ifdef _WIN32
#define M68K_ASM_EXPORT __declspec(dllexport)
#else
#define M68K_ASM_EXPORT
#endif

typedef enum M68kAsmInputMode {
    M68K_ASM_INPUT_LINE = 0,
    M68K_ASM_INPUT_SOURCE = 1,
} M68kAsmInputMode;

typedef struct M68kAsmOptions {
    uint8_t target_cpu;
    uint8_t input_mode;
} M68kAsmOptions;

typedef struct M68kAsmVerifyOptions {
    uint8_t target_cpu;
} M68kAsmVerifyOptions;

typedef struct M68kAssembleResult {
  size_t byte_count;
  M68kDiagList diagnostics;
} M68kAssembleResult;

typedef struct M68kVerifyResult {
  M68kDiagList diagnostics;
} M68kVerifyResult;

typedef struct M68kSourceIrParseResult {
  M68kSourceFileIR source_file;
  M68kDiagList diagnostics;
} M68kSourceIrParseResult;

typedef struct M68kSourceIrRenderResult {
  char *text;
  M68kDiagList diagnostics;
} M68kSourceIrRenderResult;

M68K_ASM_EXPORT M68kAssembleResult m68k_assemble(const char *text, const M68kAsmOptions *options,
    uint8_t *out_bytes, size_t max_bytes);
M68K_ASM_EXPORT M68kVerifyResult m68k_verify_manifest(const char *manifest_path,
    const M68kAsmVerifyOptions *options);
M68K_ASM_EXPORT M68kVerifyResult m68k_verify_corpus(const char *manifest_path, const char *binary_path,
    const M68kAsmVerifyOptions *options);
M68K_ASM_EXPORT M68kSourceIrParseResult m68k_source_ir_parse_file(const char *path, const char *include_dir,
    uint8_t target_cpu);
M68K_ASM_EXPORT M68kSourceIrRenderResult m68k_source_ir_render_with_policy(const M68kSourceFileIR *source_file,
    const M68kRenderPolicy *policy);
M68K_ASM_EXPORT void m68k_source_ir_free(M68kSourceFileIR *source_file);
M68K_ASM_EXPORT void m68k_free_text(char *text);

#endif
