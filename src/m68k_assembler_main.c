#include "m68k_assembler_app.h"
#include "m68k_corpus_spec.h"
#include "m68k_corpus_support.h"
#include "m68k_parse_util.h"

#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
  uint8_t target_cpu = M68K_ASM_CPU_68000;
  M68kRenderPolicy render_policy;
  char parse_error[64];
  int argi;
  if (argc == 3 && strcmp(argv[1], "verify-manifest") == 0) {
    return m68k_corpus_verify_manifest(argv[2], M68K_ASM_CPU_68000, m68k_corpus_parse_instruction_spec);
  }
  if (argc == 5 && strcmp(argv[1], "verify-manifest") == 0 && strcmp(argv[2], "--cpu") == 0) {
    if (!m68k_parse_cpu_name(argv[3], &target_cpu)) {
      fprintf(stderr, "unknown cpu: %s\n", argv[3]);
      return 2;
    }
    return m68k_corpus_verify_manifest(argv[4], target_cpu, m68k_corpus_parse_instruction_spec);
  }
  if (argc == 4 && strcmp(argv[1], "verify") == 0) {
    return m68k_corpus_verify_binary(argv[2], argv[3], M68K_ASM_CPU_68000, m68k_corpus_parse_instruction_spec);
  }
  if (argc == 6 && strcmp(argv[1], "verify") == 0 && strcmp(argv[2], "--cpu") == 0) {
    if (!m68k_parse_cpu_name(argv[3], &target_cpu)) {
      fprintf(stderr, "unknown cpu: %s\n", argv[3]);
      return 2;
    }
    return m68k_corpus_verify_binary(argv[4], argv[5], target_cpu, m68k_corpus_parse_instruction_spec);
  }
  if (argc == 4 && strcmp(argv[1], "assemble-case") == 0) {
    return m68k_corpus_assemble_case_to_stdout(argv[2], argv[3], M68K_ASM_CPU_68000,
      m68k_corpus_parse_instruction_spec);
  }
  if (argc == 6 && strcmp(argv[1], "assemble-case") == 0 && strcmp(argv[2], "--cpu") == 0) {
    if (!m68k_parse_cpu_name(argv[3], &target_cpu)) {
      fprintf(stderr, "unknown cpu: %s\n", argv[3]);
      return 2;
    }
    return m68k_corpus_assemble_case_to_stdout(argv[4], argv[5], target_cpu, m68k_corpus_parse_instruction_spec);
  }
  if (argc == 4 && strcmp(argv[1], "assemble-manifest") == 0) {
    return m68k_corpus_assemble_manifest_to_file(argv[2], argv[3], M68K_ASM_CPU_68000,
      m68k_corpus_parse_instruction_spec);
  }
  if (argc == 6 && strcmp(argv[1], "assemble-manifest") == 0 && strcmp(argv[2], "--cpu") == 0) {
    if (!m68k_parse_cpu_name(argv[3], &target_cpu)) {
      fprintf(stderr, "unknown cpu: %s\n", argv[3]);
      return 2;
    }
    return m68k_corpus_assemble_manifest_to_file(argv[4], argv[5], target_cpu, m68k_corpus_parse_instruction_spec);
  }
  if (argc == 3 && strcmp(argv[1], "assemble-line") == 0)
    return m68k_assemble_line_to_stdout(argv[2], target_cpu);
  if (argc == 5 && strcmp(argv[1], "assemble-line") == 0 && strcmp(argv[2], "--cpu") == 0) {
    if (!m68k_parse_cpu_name(argv[3], &target_cpu)) {
      fprintf(stderr, "unknown cpu: %s\n", argv[3]);
      return 2;
    }
    return m68k_assemble_line_to_stdout(argv[4], target_cpu);
  }
  if (argc == 4 && strcmp(argv[1], "assemble-file") == 0)
    return m68k_assemble_file_to_binary(argv[2], argv[3], target_cpu);
  if (argc == 6 && strcmp(argv[1], "assemble-file") == 0 && strcmp(argv[2], "--cpu") == 0) {
    if (!m68k_parse_cpu_name(argv[3], &target_cpu)) {
      fprintf(stderr, "unknown cpu: %s\n", argv[3]);
      return 2;
    }
    return m68k_assemble_file_to_binary(argv[4], argv[5], target_cpu);
  }
  if (argc == 8 && strcmp(argv[1], "assemble-platform-file") == 0 && strcmp(argv[2], "--backend") == 0 &&
      strcmp(argv[4], "--include-dir") == 0) {
    return m68k_assemble_platform_file_to_output(argv[3], argv[5], argv[6], argv[7], target_cpu, 0);
  }
  if (argc == 10 && strcmp(argv[1], "assemble-platform-file") == 0 && strcmp(argv[2], "--cpu") == 0 &&
      strcmp(argv[4], "--backend") == 0 && strcmp(argv[6], "--include-dir") == 0) {
    if (!m68k_parse_cpu_name(argv[3], &target_cpu)) {
      fprintf(stderr, "unknown cpu: %s\n", argv[3]);
      return 2;
    }
    return m68k_assemble_platform_file_to_output(argv[5], argv[7], argv[8], argv[9], target_cpu, 0);
  }
  if (argc == 10 && strcmp(argv[1], "assemble-platform-file") == 0 && strcmp(argv[2], "--syntax-compat") == 0 &&
      strcmp(argv[3], "vasm") == 0 && strcmp(argv[4], "--backend") == 0 && strcmp(argv[6], "--include-dir") == 0) {
    return m68k_assemble_platform_file_to_output(argv[5], argv[7], argv[8], argv[9], target_cpu, 1);
  }
  if (argc == 12 && strcmp(argv[1], "assemble-platform-file") == 0 && strcmp(argv[2], "--cpu") == 0 &&
      strcmp(argv[4], "--syntax-compat") == 0 && strcmp(argv[5], "vasm") == 0 && strcmp(argv[6], "--backend") == 0 &&
      strcmp(argv[8], "--include-dir") == 0) {
    if (!m68k_parse_cpu_name(argv[3], &target_cpu)) {
      fprintf(stderr, "unknown cpu: %s\n", argv[3]);
      return 2;
    }
    return m68k_assemble_platform_file_to_output(argv[7], argv[9], argv[10], argv[11], target_cpu, 1);
  }
  if (argc >= 5 && strcmp(argv[1], "render-source-file") == 0) {
    const char *input_path = NULL;
    const char *include_dir = NULL;
    int enable_vasm_compat_rewrites = 0;
    m68k_render_policy_init_for_syntax(&render_policy, M68K_IR_SYNTAX_CANONICAL);
    for (argi = 2; argi < argc; ++argi) {
      if (strcmp(argv[argi], "--cpu") == 0) {
        if (argi + 1 >= argc || !m68k_parse_cpu_name(argv[argi + 1], &target_cpu)) {
          fprintf(stderr, "unknown cpu: %s\n", (argi + 1 < argc) ? argv[argi + 1] : "");
          return 2;
        }
        ++argi;
        continue;
      }
      if (strcmp(argv[argi], "--include-dir") == 0) {
        if (argi + 1 >= argc) {
          fprintf(stderr, "missing include dir\n");
          return 2;
        }
        include_dir = argv[++argi];
        continue;
      }
      if (strcmp(argv[argi], "--syntax-compat") == 0) {
        if (argi + 1 >= argc || _stricmp(argv[argi + 1], "vasm") != 0) {
          fprintf(stderr, "unknown syntax compat: %s\n", (argi + 1 < argc) ? argv[argi + 1] : "");
          return 2;
        }
        enable_vasm_compat_rewrites = 1;
        ++argi;
        continue;
      }
      {
        int parse_result = m68k_parse_render_policy_option(argc, argv, &argi, &render_policy, parse_error,
          sizeof(parse_error));
        if (parse_result < 0) {
          fprintf(stderr, "%s\n", parse_error);
          return 2;
        }
        if (parse_result > 0) continue;
      }
      if (input_path == NULL) {
        input_path = argv[argi];
        continue;
      }
      fprintf(stderr, "unexpected argument: %s\n", argv[argi]);
      return 2;
    }
    if (input_path == NULL || include_dir == NULL) {
      fprintf(stderr, "render-source-file requires --include-dir <dir> <input.s>\n");
      return 2;
    }
    return m68k_render_source_file_to_stdout( input_path, include_dir, target_cpu, enable_vasm_compat_rewrites, &render_policy);
  }
  fprintf(stderr, "usage: %s verify <all_cases.txt> <all_cases.bin>\n", argv[0]);
  fprintf(stderr, "   or: %s verify --cpu <68000|68010|68020|68030|68040|68060> <all_cases.txt> <all_cases.bin>\n",
    argv[0]);
  fprintf(stderr, "   or: %s verify-manifest <cases.txt>\n", argv[0]);
  fprintf(stderr, "   or: %s verify-manifest --cpu <68000|68010|68020|68030|68040|68060> <cases.txt>\n", argv[0]);
  fprintf(stderr, "   or: %s assemble-case <all_cases.txt> <case_id>\n", argv[0]);
  fprintf(stderr, "   or: %s assemble-case --cpu <68000|68010|68020|68030|68040|68060> <all_cases.txt> <case_id>\n",
    argv[0]);
  fprintf(stderr, "   or: %s assemble-manifest <all_cases.txt> <out.bin>\n", argv[0]);
  fprintf(stderr, "   or: %s assemble-manifest --cpu <68000|68010|68020|68030|68040|68060> <all_cases.txt> <out.bin>\n",
    argv[0]);
  fprintf(stderr, "   or: %s assemble-line \"<asm>\"\n", argv[0]);
  fprintf(stderr, "   or: %s assemble-line --cpu <68000|68010|68020|68030|68040|68060> \"<asm>\"\n", argv[0]);
  fprintf(stderr, "   or: %s assemble-file <input.s> <out.bin>\n", argv[0]);
  fprintf(stderr, "   or: %s assemble-file --cpu <68000|68010|68020|68030|68040|68060> <input.s> <out.bin>\n", argv[0]);
  fprintf(stderr, "   or: %s assemble-platform-file --backend <amiga-hunk|atari-st> --include-dir <dir> <input.s> <out>\n",
    argv[0]);
  fprintf(stderr, "   or: %s assemble-platform-file --cpu <68000|68010|68020|68030|68040|68060> --backend <amiga-hunk|atari-st> "
    "--include-dir <dir> <input.s> <out>\n", argv[0]);
  fprintf(stderr, "   or: %s assemble-platform-file --syntax-compat vasm --backend <amiga-hunk|atari-st> --include-dir <dir> "
    "<input.s> <out>\n", argv[0]);
  fprintf(stderr, "   or: %s assemble-platform-file --cpu <68000|68010|68020|68030|68040|68060> --syntax-compat vasm "
    "--backend <amiga-hunk|atari-st> --include-dir <dir> <input.s> <out>\n", argv[0]);
  fprintf(stderr, "   or: %s render-source-file --include-dir <dir> <input.s>\n", argv[0]);
  fprintf(stderr, "   or: %s render-source-file [--cpu <68000|68010|68020|68030|68040|68060>] [--syntax "
    "canonical|genam|vasm]\n", argv[0]);
  fprintf(stderr, "          [--syntax-compat vasm] [--no-strings] [--no-longs] [--no-generated-names]\n");
  fprintf(stderr, "          [--code-label-prefix p] [--call-label-prefix p] [--data-label-prefix p] --include-dir "
    "<dir> <input.s>\n");
  return 2;
}
