#include "platform_file_lib.h"
#include "m68k_parse_util.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int inspect_file_to_stdout(const char *platform_name, const char *path) {
  char *json = NULL;
  char error[256];
  if (platform_file_inspect_path_json(platform_name, path, &json, error, sizeof(error)) != 0) {
    fprintf(stderr, "%s\n", error);
    return 1;
  }
  puts(json);
  platform_file_free_text(json);
  return 0;
}

static int analyze_file_to_stdout(const char *platform_name, const char *path,
    const M68kAnalysisPolicy *analysis_policy) {
  char *json = NULL;
  char error[256];
  if (platform_file_analyze_path_json(platform_name, path, analysis_policy, &json, error, sizeof(error)) != 0) {
    fprintf(stderr, "%s\n", error);
    return 1;
  }
  puts(json);
  platform_file_free_text(json);
  return 0;
}

static int disassemble_file_to_stdout_with_policy( const char *platform_name, const char *path,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy) {
  M68kSourceFileIR source_file;
  char *text = NULL;
  char error[256];
  int result;
  m68k_ir_source_file_init(&source_file);
  result = platform_file_to_ir_with_policy(platform_name, path, policy, analysis_policy, &source_file, error,
    sizeof(error));
  if (result != 0) {
    fprintf(stderr, "%s\n", error);
    return 1;
  }
  result = platform_file_render_ir_with_policy(&source_file, policy, &text, error, sizeof(error));
  m68k_ir_source_file_free(&source_file);
  if (result != 0) {
    fprintf(stderr, "%s\n", error);
    return 1;
  }
  puts(text);
  platform_file_free_text(text);
  return 0;
}

int main(int argc, char **argv) {
  M68kRenderPolicy policy;
  M68kAnalysisPolicy analysis_policy;
  char parse_error[64];
  int argi;
  if (argc == 4 && strcmp(argv[1], "inspect-file") == 0) return inspect_file_to_stdout(argv[2], argv[3]);
  if (argc == 4 && strcmp(argv[1], "analyze-file") == 0) return analyze_file_to_stdout(argv[2], argv[3], NULL);
  if (argc >= 4 && strcmp(argv[1], "analyze-file") == 0) {
    const char *platform_name = NULL;
    const char *path = NULL;
    m68k_analysis_policy_init_default(&analysis_policy);
    for (argi = 2; argi < argc; ++argi) {
      if (strcmp(argv[argi], "--max-cpu") == 0) {
        if (argi + 1 >= argc || !m68k_parse_cpu_name(argv[argi + 1], &analysis_policy.max_cpu)) {
          fprintf(stderr, "unknown cpu: %s\n", (argi + 1 < argc) ? argv[argi + 1] : "");
          return 2;
        }
        ++argi;
        continue;
      }
      if (platform_name == NULL) {
        platform_name = argv[argi];
        continue;
      }
      if (path == NULL) {
        path = argv[argi];
        continue;
      }
      fprintf(stderr, "unexpected argument: %s\n", argv[argi]);
      return 2;
    }
    if (platform_name == NULL || path == NULL) {
      fprintf(stderr, "missing platform/file\n");
      return 2;
    }
    return analyze_file_to_stdout(platform_name, path, &analysis_policy);
  }
  if (argc >= 4 && strcmp(argv[1], "disassemble-file") == 0) {
    const char *platform_name = NULL;
    const char *path = NULL;
    m68k_render_policy_init_for_syntax(&policy, M68K_IR_SYNTAX_CANONICAL);
    m68k_analysis_policy_init_default(&analysis_policy);
    for (argi = 2; argi < argc; ++argi) {
      if (strcmp(argv[argi], "--max-cpu") == 0) {
        if (argi + 1 >= argc || !m68k_parse_cpu_name(argv[argi + 1], &analysis_policy.max_cpu)) {
          fprintf(stderr, "unknown cpu: %s\n", (argi + 1 < argc) ? argv[argi + 1] : "");
          return 2;
        }
        ++argi;
        continue;
      }
      {
        int parse_result = m68k_parse_render_policy_option(argc, argv, &argi, &policy, parse_error,
          sizeof(parse_error));
        if (parse_result < 0) {
          fprintf(stderr, "%s\n", parse_error);
          return 2;
        }
        if (parse_result > 0) continue;
      }
      if (platform_name == NULL) {
        platform_name = argv[argi];
        continue;
      }
      if (path == NULL) {
        path = argv[argi];
        continue;
      }
      fprintf(stderr, "unexpected argument: %s\n", argv[argi]);
      return 2;
    }
    if (platform_name == NULL || path == NULL) {
      fprintf(stderr, "missing platform/file\n");
      return 2;
    }
    return disassemble_file_to_stdout_with_policy(platform_name, path, &policy, &analysis_policy);
  }
  fprintf(stderr, "usage: %s inspect-file <amiga-hunk|atari-st> <file>\n", argv[0]);
  fprintf( stderr, "   or: %s analyze-file [--max-cpu " "<68000|68010|68020|68030|68040|68060>] <amiga-hunk|atari-st> "
    "<file>\n", argv[0]);
  fprintf(stderr, "   or: %s disassemble-file [--max-cpu <68000|68010|68020|68030|68040|68060>] [--syntax "
    "canonical|genam|vasm] [--no-strings] [--no-longs]\n", argv[0]);
  fprintf(stderr, "          [--no-generated-names] [--code-label-prefix p] [--call-label-prefix p] "
    "[--data-label-prefix p]\n");
  fprintf(stderr, "          <amiga-hunk|atari-st> <file>\n");
  return 2;
}
