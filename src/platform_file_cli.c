#include "platform_file_lib.h"
#include "m68k_parse_util.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

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
  result = platform_file_to_ir_with_policy(platform_name, path, policy, analysis_policy, &source_file, error,
    sizeof(error));
  if (result != 0) {
    fprintf(stderr, "%s\n", error);
    return 1;
  }
  result = platform_file_render_ir_with_policy(&source_file, policy, &text, error, sizeof(error));
  m68k_ir_source_file_destroy(&source_file);
  if (result != 0) {
    fprintf(stderr, "%s\n", error);
    return 1;
  }
  puts(text);
  platform_file_free_text(text);
  return 0;
}

static double elapsed_seconds(clock_t start_ticks, clock_t end_ticks) {
  return ((double)(end_ticks - start_ticks)) / (double)CLOCKS_PER_SEC;
}

static void print_json_escaped(const char *text) {
  const unsigned char *cursor = (const unsigned char *)text;
  putchar('"');
  while (*cursor != '\0') {
    unsigned char ch = *cursor++;
    switch (ch) {
      case '\\':
        fputs("\\\\", stdout);
        break;
      case '"':
        fputs("\\\"", stdout);
        break;
      case '\b':
        fputs("\\b", stdout);
        break;
      case '\f':
        fputs("\\f", stdout);
        break;
      case '\n':
        fputs("\\n", stdout);
        break;
      case '\r':
        fputs("\\r", stdout);
        break;
      case '\t':
        fputs("\\t", stdout);
        break;
      default:
        if (ch < 0x20u) printf("\\u%04X", (unsigned int)ch);
        else putchar((int)ch);
        break;
    }
  }
  putchar('"');
}

static const char *section_kind_name(uint8_t kind) {
  switch (kind) {
    case M68K_SECTION_CODE:
      return "code";
    case M68K_SECTION_DATA:
      return "data";
    case M68K_SECTION_BSS:
      return "bss";
    default:
      return "unknown";
  }
}

static const char *file_kind_name(uint8_t kind) {
  switch (kind) {
    case M68K_PLATFORM_FILE_EXECUTABLE:
      return "executable";
    case M68K_PLATFORM_FILE_OBJECT:
      return "object";
    default:
      return "unknown";
  }
}

static uint32_t count_set_bytes(const uint8_t *values, size_t count) {
  size_t index;
  uint32_t total = 0;
  if (values == NULL) return 0;
  for (index = 0; index < count; ++index) {
    if (values[index] != 0) ++total;
  }
  return total;
}

typedef struct BenchmarkStats {
  double analysis_seconds, ir_with_analysis_seconds, render_seconds, total_seconds;
  uint32_t section_bytes, code_section_bytes, data_section_bytes, bss_section_bytes;
  uint32_t certain_code_bytes, label_count, generated_label_count, block_count, edge_count;
  uint32_t violation_count, recovered_word_dispatch_count, recovered_inline_dispatch_count;
  uint32_t recovered_string_dispatch_count, recovered_platform_base_slot_count, recovered_platform_effect_count;
  uint32_t recovered_platform_call_count, statement_count, label_statement_count;
  uint32_t generated_label_statement_count, instruction_statement_count, data_statement_count;
  uint32_t align_statement_count, instruction_bytes, data_bytes, symbol_ref_count;
  uint32_t symbol_ref_abs_count, symbol_ref_pc_relative_count, symbol_ref_section_relative_count;
  uint32_t vasm_normalized_count;
} BenchmarkStats;

static uint32_t count_unique_platform_base_slot_effects(const M68kSectionAnalysisIR *section_analysis) {
  uint32_t total = 0;
  size_t index;
  if (section_analysis == NULL) return 0;
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    size_t prev_index;
    int seen = 0;
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT) continue;
    for (prev_index = 0; prev_index < index; ++prev_index) {
      const M68kRecoveredPlatformEffectIR *prev = &section_analysis->recovered_platform_effects[prev_index];
      if (prev->kind != M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT) continue;
      if (prev->displacement == effect->displacement) {
        seen = 1;
        break;
      }
    }
    if (!seen) ++total;
  }
  return total;
}

static void collect_benchmark_stats(const M68kSourceAnalysisIR *source_analysis, const M68kSourceFileIR *source_file,
    const char *text, BenchmarkStats *stats) {
  size_t section_index;
  memset(stats, 0, sizeof(*stats));
  for (section_index = 0; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    stats->section_bytes += section_analysis->section_size;
    stats->certain_code_bytes += count_set_bytes(section_analysis->certain_code_byte, section_analysis->certain_code_size);
    stats->label_count += (uint32_t)section_analysis->label_count;
    stats->block_count += (uint32_t)section_analysis->block_count;
    stats->edge_count += (uint32_t)section_analysis->edge_count;
    stats->violation_count += (uint32_t)section_analysis->violation_count;
    stats->recovered_word_dispatch_count += (uint32_t)section_analysis->recovered_word_dispatch_count;
    stats->recovered_inline_dispatch_count += (uint32_t)section_analysis->recovered_inline_dispatch_count;
    stats->recovered_string_dispatch_count += (uint32_t)section_analysis->recovered_string_dispatch_count;
    stats->recovered_platform_base_slot_count += count_unique_platform_base_slot_effects(section_analysis);
    stats->recovered_platform_effect_count += (uint32_t)section_analysis->recovered_platform_effect_count;
    stats->recovered_platform_call_count += (uint32_t)section_analysis->recovered_platform_call_count;
    stats->generated_label_count += count_set_bytes(section_analysis->generated_label_flags, section_analysis->generated_label_size);
    switch (section_analysis->section_kind) {
      case M68K_SECTION_CODE:
        stats->code_section_bytes += section_analysis->section_size;
        break;
      case M68K_SECTION_DATA:
        stats->data_section_bytes += section_analysis->section_size;
        break;
      case M68K_SECTION_BSS:
        stats->bss_section_bytes += section_analysis->section_size;
        break;
      default:
        break;
    }
  }

  for (section_index = 0; section_index < source_file->section_count; ++section_index) {
    const M68kSectionIR *section = &source_file->sections[section_index];
    size_t statement_index;
    stats->statement_count += (uint32_t)section->statement_count;
    for (statement_index = 0; statement_index < section->statement_count; ++statement_index) {
      const M68kStatementIR *statement = &section->statements[statement_index];
      size_t operand_index;
      switch (statement->kind) {
        case M68K_STATEMENT_LABEL:
          ++stats->label_statement_count;
          if (statement->label_is_generated) ++stats->generated_label_statement_count;
          break;
        case M68K_STATEMENT_INSTRUCTION:
          ++stats->instruction_statement_count;
          stats->instruction_bytes += (uint32_t)statement->u.instruction.byte_count;
          for (operand_index = 0; operand_index < statement->u.instruction.operand_count; ++operand_index) {
            const M68kSymbolRefIR *symbol_ref = &statement->u.instruction.operands[operand_index].symbol_ref;
            if (!symbol_ref->has_name) continue;
            ++stats->symbol_ref_count;
            switch (symbol_ref->kind) {
              case M68K_IR_SYMBOL_REF_ABS:
                ++stats->symbol_ref_abs_count;
                break;
              case M68K_IR_SYMBOL_REF_PC_REL:
                ++stats->symbol_ref_pc_relative_count;
                break;
              case M68K_IR_SYMBOL_REF_SECTION_REL:
                ++stats->symbol_ref_section_relative_count;
                break;
              default:
                break;
            }
          }
          break;
        case M68K_STATEMENT_DATA:
          ++stats->data_statement_count;
          stats->data_bytes += (uint32_t)statement->u.data.size;
          break;
        case M68K_STATEMENT_ALIGN:
          ++stats->align_statement_count;
          break;
        default:
          break;
      }
      if (statement->comment != NULL &&
          strstr(statement->comment, "vasm-normalized from exact immediate word") != NULL) {
        ++stats->vasm_normalized_count;
      }
    }
  }
  (void)text;
}

static void print_benchmark_json(const char *platform_name, const char *path, const M68kSourceAnalysisIR *source_analysis,
    const M68kSourceFileIR *source_file, const char *text, const BenchmarkStats *stats) {
  size_t section_index;
  puts("{");
  printf("  \"benchmark_version\": 1,\n");
  printf("  \"platform\": ");
  print_json_escaped(platform_name);
  printf(",\n  \"path\": ");
  print_json_escaped(path);
  printf(",\n  \"timing\": {\n");
  printf("    \"analysis_seconds\": %.6f,\n", stats->analysis_seconds);
  printf("    \"ir_build_with_analysis_seconds\": %.6f,\n", stats->ir_with_analysis_seconds);
  printf("    \"render_seconds\": %.6f,\n", stats->render_seconds);
  printf("    \"total_seconds\": %.6f\n", stats->total_seconds);
  printf("  },\n");
  printf("  \"file\": {\n");
  printf("    \"file_kind\": ");
  print_json_escaped(file_kind_name(source_analysis->file_kind));
  printf(",\n    \"section_count\": %" PRIuPTR ",\n", source_analysis->section_count);
  printf("    \"section_bytes\": %" PRIu32 ",\n", stats->section_bytes);
  printf("    \"code_section_bytes\": %" PRIu32 ",\n", stats->code_section_bytes);
  printf("    \"data_section_bytes\": %" PRIu32 ",\n", stats->data_section_bytes);
  printf("    \"bss_section_bytes\": %" PRIu32 "\n", stats->bss_section_bytes);
  printf("  },\n");
  printf("  \"analysis\": {\n");
  printf("    \"required_cpu\": %u,\n", (unsigned int)source_analysis->findings.required_cpu);
  printf("    \"cpu_violation_count\": %" PRIu32 ",\n", source_analysis->findings.cpu_violation_count);
  printf("    \"certain_code_bytes\": %" PRIu32 ",\n", stats->certain_code_bytes);
  printf("    \"certain_code_ratio\": %.6f,\n",
    stats->section_bytes == 0 ? 0.0 : ((double)stats->certain_code_bytes / (double)stats->section_bytes));
  printf("    \"label_count\": %" PRIu32 ",\n", stats->label_count);
  printf("    \"generated_label_count\": %" PRIu32 ",\n", stats->generated_label_count);
  printf("    \"block_count\": %" PRIu32 ",\n", stats->block_count);
  printf("    \"edge_count\": %" PRIu32 ",\n", stats->edge_count);
  printf("    \"violation_count\": %" PRIu32 ",\n", stats->violation_count);
  printf("    \"recovered_word_dispatch_count\": %" PRIu32 ",\n", stats->recovered_word_dispatch_count);
  printf("    \"recovered_inline_dispatch_count\": %" PRIu32 ",\n", stats->recovered_inline_dispatch_count);
  printf("    \"recovered_string_dispatch_count\": %" PRIu32 ",\n", stats->recovered_string_dispatch_count);
  printf("    \"recovered_platform_base_slot_count\": %" PRIu32 ",\n", stats->recovered_platform_base_slot_count);
  printf("    \"recovered_platform_effect_count\": %" PRIu32 ",\n", stats->recovered_platform_effect_count);
  printf("    \"recovered_platform_call_count\": %" PRIu32 "\n", stats->recovered_platform_call_count);
  printf("  },\n");
  printf("  \"render\": {\n");
  printf("    \"statement_count\": %" PRIu32 ",\n", stats->statement_count);
  printf("    \"label_statement_count\": %" PRIu32 ",\n", stats->label_statement_count);
  printf("    \"generated_label_statement_count\": %" PRIu32 ",\n", stats->generated_label_statement_count);
  printf("    \"instruction_statement_count\": %" PRIu32 ",\n", stats->instruction_statement_count);
  printf("    \"data_statement_count\": %" PRIu32 ",\n", stats->data_statement_count);
  printf("    \"align_statement_count\": %" PRIu32 ",\n", stats->align_statement_count);
  printf("    \"instruction_bytes\": %" PRIu32 ",\n", stats->instruction_bytes);
  printf("    \"data_bytes\": %" PRIu32 ",\n", stats->data_bytes);
  printf("    \"instruction_byte_ratio\": %.6f,\n",
    (stats->instruction_bytes + stats->data_bytes) == 0 ? 0.0
      : ((double)stats->instruction_bytes / (double)(stats->instruction_bytes + stats->data_bytes)));
  printf("    \"symbol_ref_count\": %" PRIu32 ",\n", stats->symbol_ref_count);
  printf("    \"symbol_ref_abs_count\": %" PRIu32 ",\n", stats->symbol_ref_abs_count);
  printf("    \"symbol_ref_pc_relative_count\": %" PRIu32 ",\n", stats->symbol_ref_pc_relative_count);
  printf("    \"symbol_ref_section_relative_count\": %" PRIu32 ",\n", stats->symbol_ref_section_relative_count);
  printf("    \"vasm_normalized_count\": %" PRIu32 ",\n", stats->vasm_normalized_count);
  printf("    \"text_bytes\": %" PRIuPTR "\n", strlen(text));
  printf("  },\n");
  printf("  \"sections\": [\n");
  for (section_index = 0; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section_analysis = &source_analysis->sections[section_index];
    const M68kSectionIR *section = (section_index < source_file->section_count) ? &source_file->sections[section_index] : NULL;
    uint32_t emitted_instruction_count = 0;
    uint32_t emitted_data_count = 0;
    uint32_t emitted_label_count = 0;
    size_t statement_index;
    if (section != NULL) {
      for (statement_index = 0; statement_index < section->statement_count; ++statement_index) {
        const M68kStatementIR *statement = &section->statements[statement_index];
        if (statement->kind == M68K_STATEMENT_LABEL) ++emitted_label_count;
        else if (statement->kind == M68K_STATEMENT_INSTRUCTION) ++emitted_instruction_count;
        else if (statement->kind == M68K_STATEMENT_DATA) ++emitted_data_count;
      }
    }
    printf("    {\n");
    printf("      \"name\": ");
    print_json_escaped(section_analysis->section_name != NULL ? section_analysis->section_name : "");
    printf(",\n      \"kind\": ");
    print_json_escaped(section_kind_name(section_analysis->section_kind));
    printf(",\n      \"size\": %" PRIu32 ",\n", section_analysis->section_size);
    printf("      \"certain_code_bytes\": %" PRIu32 ",\n",
      count_set_bytes(section_analysis->certain_code_byte, section_analysis->certain_code_size));
    printf("      \"label_count\": %" PRIuPTR ",\n", section_analysis->label_count);
    printf("      \"block_count\": %" PRIuPTR ",\n", section_analysis->block_count);
    printf("      \"edge_count\": %" PRIuPTR ",\n", section_analysis->edge_count);
    printf("      \"violation_count\": %" PRIuPTR ",\n", section_analysis->violation_count);
    printf("      \"emitted_instruction_count\": %" PRIu32 ",\n", emitted_instruction_count);
    printf("      \"emitted_data_count\": %" PRIu32 ",\n", emitted_data_count);
    printf("      \"emitted_label_count\": %" PRIu32 "\n", emitted_label_count);
    printf(section_index + 1 < source_analysis->section_count ? "    },\n" : "    }\n");
  }
  printf("  ]\n}\n");
}

static int benchmark_file_to_stdout(const char *platform_name, const char *path,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy) {
  M68kSourceAnalysisIR source_analysis;
  M68kSourceFileIR source_file;
  char *text = NULL;
  char error[256];
  clock_t total_start, total_end, analysis_start, analysis_end, ir_start, ir_end, render_start, render_end;
  BenchmarkStats stats;
  int result;

  total_start = clock();
  analysis_start = clock();
  result = platform_file_analyze_path(platform_name, path, analysis_policy, &source_analysis, error, sizeof(error));
  analysis_end = clock();
  if (result != 0) {
    fprintf(stderr, "%s\n", error);
    return 1;
  }

  ir_start = clock();
  result = platform_file_to_ir_with_policy(platform_name, path, policy, analysis_policy, &source_file, error, sizeof(error));
  ir_end = clock();
  if (result != 0) {
    platform_file_source_analysis_free(&source_analysis);
    fprintf(stderr, "%s\n", error);
    return 1;
  }

  render_start = clock();
  result = platform_file_render_ir_with_policy(&source_file, policy, &text, error, sizeof(error));
  render_end = clock();
  if (result != 0) {
    platform_file_source_ir_free(&source_file);
    platform_file_source_analysis_free(&source_analysis);
    fprintf(stderr, "%s\n", error);
    return 1;
  }

  collect_benchmark_stats(&source_analysis, &source_file, text, &stats);
  stats.analysis_seconds = elapsed_seconds(analysis_start, analysis_end);
  stats.ir_with_analysis_seconds = elapsed_seconds(ir_start, ir_end);
  stats.render_seconds = elapsed_seconds(render_start, render_end);
  total_end = clock();
  stats.total_seconds = elapsed_seconds(total_start, total_end);
  print_benchmark_json(platform_name, path, &source_analysis, &source_file, text, &stats);

  platform_file_free_text(text);
  platform_file_source_ir_free(&source_file);
  platform_file_source_analysis_free(&source_analysis);
  return 0;
}

int main(int argc, char **argv) {
  M68kRenderPolicy policy;
  M68kAnalysisPolicy analysis_policy;
  char parse_error[64];
  int argi;
  if (argc == 4 && strcmp(argv[1], "inspect-file") == 0) return inspect_file_to_stdout(argv[2], argv[3]);
  if (argc == 4 && strcmp(argv[1], "analyze-file") == 0) return analyze_file_to_stdout(argv[2], argv[3], NULL);
  if (argc == 4 && strcmp(argv[1], "benchmark-file") == 0) {
    m68k_render_policy_init_for_syntax(&policy, M68K_IR_SYNTAX_GENAM);
    m68k_analysis_policy_init_default(&analysis_policy);
    return benchmark_file_to_stdout(argv[2], argv[3], &policy, &analysis_policy);
  }
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
  fprintf(stderr, "   or: %s benchmark-file <amiga-hunk|atari-st> <file>\n", argv[0]);
  fprintf( stderr, "   or: %s analyze-file [--max-cpu " "<68000|68010|68020|68030|68040|68060>] <amiga-hunk|atari-st> "
    "<file>\n", argv[0]);
  fprintf(stderr, "   or: %s disassemble-file [--max-cpu <68000|68010|68020|68030|68040|68060>] [--syntax "
    "canonical|genam|vasm] [--no-strings] [--no-longs]\n", argv[0]);
  fprintf(stderr, "          [--no-generated-names] [--code-label-prefix p] [--call-label-prefix p] "
    "[--data-label-prefix p]\n");
  fprintf(stderr, "          <amiga-hunk|atari-st> <file>\n");
  return 2;
}
