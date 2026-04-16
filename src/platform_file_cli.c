#include "platform_file_lib.h"
#include "m68k_parse_util.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int write_benchmark_json_file(const char *benchmark_json_path, const char *platform_name, const char *path,
    const PlatformFileRunMetrics *metrics);

static int inspect_file_to_stdout(const char *platform_name, const char *path) {
  PlatformFileTextResult result = platform_file_inspect_path_json(platform_name, path);
  if (m68k_diag_has_errors(&result.diagnostics)) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&result.diagnostics));
    return 1;
  }
  puts(result.text);
  platform_file_free_text(result.text);
  return 0;
}

static int analyze_file_to_stdout(const char *platform_name, const char *path,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result = platform_file_analyze_path_json(platform_name, path, analysis_policy);
  if (m68k_diag_has_errors(&result.diagnostics)) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&result.diagnostics));
    return 1;
  }
  puts(result.text);
  platform_file_free_text(result.text);
  return 0;
}

static int disassemble_file_to_stdout_with_policy( const char *platform_name, const char *path,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy, const char *benchmark_json_path) {
  PlatformFileRunResult result = platform_file_run_path_with_policy(platform_name, path, policy, analysis_policy);
  if (m68k_diag_has_errors(&result.diagnostics)) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&result.diagnostics));
    return 1;
  }
  if (write_benchmark_json_file(benchmark_json_path, platform_name, path, &result.metrics) != 0) {
    platform_file_free_text(result.text);
    platform_file_run_metrics_free(&result.metrics);
    platform_file_source_ir_free(&result.source_file);
    fprintf(stderr, "failed writing benchmark json: %s\n", benchmark_json_path);
    return 1;
  }
  puts(result.text);
  platform_file_free_text(result.text);
  platform_file_run_metrics_free(&result.metrics);
  platform_file_source_ir_free(&result.source_file);
  return 0;
}

static int write_benchmark_json_file(const char *benchmark_json_path, const char *platform_name, const char *path,
    const PlatformFileRunMetrics *metrics) {
  FILE *out = NULL;
  PlatformFileTextResult result;
  if (benchmark_json_path == NULL || metrics == NULL) return 0;
  result = platform_file_run_metrics_json(platform_name, path, metrics);
  if (m68k_diag_has_errors(&result.diagnostics))
    return -1;
  out = fopen(benchmark_json_path, "wb");
  if (out == NULL) {
    platform_file_free_text(result.text);
    return -1;
  }
  if (fwrite(result.text, 1, strlen(result.text), out) != strlen(result.text)) {
    fclose(out);
    platform_file_free_text(result.text);
    return -1;
  }
  platform_file_free_text(result.text);
  fclose(out);
  return 0;
}

int main(int argc, char **argv) {
  M68kRenderPolicy policy;
  M68kAnalysisPolicy analysis_policy;
  M68kDiagList parse_diagnostics;
  M68kParseCpuResult cpu_result;
  int argi;
  if (argc == 4 && strcmp(argv[1], "inspect-file") == 0) return inspect_file_to_stdout(argv[2], argv[3]);
  if (argc == 4 && strcmp(argv[1], "analyze-file") == 0) return analyze_file_to_stdout(argv[2], argv[3], NULL);
  if (argc >= 4 && strcmp(argv[1], "analyze-file") == 0) {
    const char *platform_name = NULL;
    const char *path = NULL;
    m68k_analysis_policy_init_default(&analysis_policy);
    for (argi = 2; argi < argc; ++argi) {
      if (strcmp(argv[argi], "--max-cpu") == 0) {
        cpu_result = (argi + 1 < argc) ? m68k_parse_cpu_name(argv[argi + 1]) : (M68kParseCpuResult){0};
        if (!cpu_result.ok) {
          fprintf(stderr, "unknown cpu: %s\n", (argi + 1 < argc) ? argv[argi + 1] : "");
          return 2;
        }
        analysis_policy.max_cpu = cpu_result.cpu;
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
    const char *benchmark_json_path = NULL;
    m68k_render_policy_init_for_syntax(&policy, M68K_IR_SYNTAX_CANONICAL);
    m68k_analysis_policy_init_default(&analysis_policy);
    for (argi = 2; argi < argc; ++argi) {
      if (strcmp(argv[argi], "--max-cpu") == 0) {
        cpu_result = (argi + 1 < argc) ? m68k_parse_cpu_name(argv[argi + 1]) : (M68kParseCpuResult){0};
        if (!cpu_result.ok) {
          fprintf(stderr, "unknown cpu: %s\n", (argi + 1 < argc) ? argv[argi + 1] : "");
          return 2;
        }
        analysis_policy.max_cpu = cpu_result.cpu;
        ++argi;
        continue;
      }
      if (strcmp(argv[argi], "--benchmark-json-out") == 0) {
        if (argi + 1 >= argc) {
          fprintf(stderr, "missing benchmark json output path\n");
          return 2;
        }
        benchmark_json_path = argv[++argi];
        continue;
      }
      {
        int parse_result;
        m68k_diag_list_reset(&parse_diagnostics);
        parse_result = m68k_parse_render_policy_option(argc, argv, &argi, &policy,
          m68k_diag_sink(&parse_diagnostics));
        if (parse_result < 0) {
          fprintf(stderr, "%s\n", m68k_diag_first_message(&parse_diagnostics));
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
    return disassemble_file_to_stdout_with_policy(platform_name, path, &policy, &analysis_policy,
      benchmark_json_path);
  }
  fprintf(stderr, "usage: %s inspect-file <amiga-hunk|atari-st> <file>\n", argv[0]);
  fprintf( stderr, "   or: %s analyze-file [--max-cpu " "<68000|68010|68020|68030|68040|68060>] <amiga-hunk|atari-st> "
    "<file>\n", argv[0]);
  fprintf(stderr, "   or: %s disassemble-file [--max-cpu <68000|68010|68020|68030|68040|68060>] [--syntax "
    "canonical|genam|vasm] [--no-strings] [--no-longs]\n", argv[0]);
  fprintf(stderr, "          [--no-generated-names] [--min-os-version <1.3|2.0|3.1|3.5>] [--benchmark-json-out file]\n");
  fprintf(stderr, "          [--code-label-prefix p] [--call-label-prefix p] [--data-label-prefix p]\n");
  fprintf(stderr, "          <amiga-hunk|atari-st> <file>\n");
  return 2;
}
