#include "platform_file_lib.h"
#include "platform_file_decompression.h"
#include "m68k_parse_util.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int write_benchmark_json_file(const char *benchmark_json_path, const char *benchmark_json);
static int write_text_file(const char *path, const char *text);

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

static int facts_v2_analysis_file_to_stdout(const char *platform_name, const char *path,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result = platform_file_facts_v2_analysis_path_json(platform_name, path, analysis_policy);
  if (m68k_diag_has_errors(&result.diagnostics)) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&result.diagnostics));
    return 1;
  }
  puts(result.text);
  platform_file_free_text(result.text);
  return 0;
}

static int facts_v2_analysis_raw_to_stdout(const char *platform_name, const char *path, uint32_t entry_offset,
    const M68kAnalysisPolicy *analysis_policy) {
  PlatformFileTextResult result = platform_file_facts_v2_analysis_raw_path_json(platform_name, path, entry_offset,
    analysis_policy);
  if (m68k_diag_has_errors(&result.diagnostics)) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&result.diagnostics));
    return 1;
  }
  puts(result.text);
  platform_file_free_text(result.text);
  return 0;
}

static int type_catalog_to_stdout(const char *platform_name) {
  PlatformFileTextResult result = platform_file_type_catalog_json(platform_name);
  if (m68k_diag_has_errors(&result.diagnostics)) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&result.diagnostics));
    return 1;
  }
  puts(result.text);
  platform_file_free_text(result.text);
  return 0;
}

static int naming_catalog_to_stdout(const char *platform_name) {
  PlatformFileTextResult result = platform_file_naming_catalog_json(platform_name);
  if (m68k_diag_has_errors(&result.diagnostics)) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&result.diagnostics));
    return 1;
  }
  puts(result.text);
  platform_file_free_text(result.text);
  return 0;
}

static int os_metadata_catalog_to_stdout(const char *platform_name) {
  PlatformFileTextResult result = platform_file_os_metadata_catalog_json(platform_name);
  if (m68k_diag_has_errors(&result.diagnostics)) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&result.diagnostics));
    return 1;
  }
  puts(result.text);
  platform_file_free_text(result.text);
  return 0;
}

static int api_input_struct_to_stdout(const char *platform_name, const char *library_name, const char *function_name,
    const char *input_name, const char *struct_name) {
  PlatformFileTextResult result = platform_file_api_input_struct_json(platform_name, library_name, function_name,
    input_name, struct_name);
  if (m68k_diag_has_errors(&result.diagnostics)) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&result.diagnostics));
    return 1;
  }
  puts(result.text);
  platform_file_free_text(result.text);
  return 0;
}

static int identify_packed_range_to_stdout(const char *provider_id, const char *provider_path,
    const char *path, uint32_t offset, uint32_t size) {
  char *text = NULL;
  int result = platform_decompression_identify_path_range_json_alloc(provider_id, provider_path, path, offset, size,
    &text);
  if (result != 0) {
    fprintf(stderr, "%s\n", text != NULL ? text : "failed identifying packed range");
    platform_decompression_free_text(text);
    return 1;
  }
  puts(text);
  platform_decompression_free_text(text);
  return 0;
}

static int decompress_packed_range_to_stdout(const char *provider_id, const char *provider_path,
    const char *path, uint32_t offset, uint32_t size, const char *output_path) {
  char *text = NULL;
  int result = platform_decompression_decompress_path_range_json_alloc(provider_id, provider_path, path, offset, size,
    output_path, &text);
  if (result != 0) {
    fprintf(stderr, "%s\n", text != NULL ? text : "failed decompressing packed range");
    platform_decompression_free_text(text);
    return 1;
  }
  puts(text);
  platform_decompression_free_text(text);
  return 0;
}

static int append_entry_offset_option(char *buffer, size_t buffer_size, const char *entry_arg) {
  size_t used;
  size_t arg_len;
  if (buffer == NULL || buffer_size == 0U || entry_arg == NULL) return 0;
  used = strlen(buffer);
  arg_len = strlen(entry_arg);
  if (used + (used != 0U ? 1U : 0U) + arg_len + 1U > buffer_size) return 0;
  if (used != 0U) buffer[used++] = ',';
  memcpy(buffer + used, entry_arg, arg_len + 1U);
  return 1;
}

static int effective_policy_file_to_stdout(const char *platform_name, const char *path, const char *metadata_path,
    const char *entry_offsets) {
  char *text = NULL;
  int result = platform_file_effective_policy_path_json_alloc(platform_name, path,
    metadata_path != NULL ? metadata_path : "", entry_offsets != NULL ? entry_offsets : "", &text);
  if (result != 0) {
    fprintf(stderr, "%s\n", text != NULL ? text : "failed building effective policy");
    platform_file_free_text(text);
    return 1;
  }
  puts(text);
  platform_file_free_text(text);
  return 0;
}

static int effective_policy_raw_to_stdout(const char *platform_name, const char *path, uint32_t entry_offset,
    const char *metadata_path, const char *entry_offsets) {
  char *text = NULL;
  int result = platform_file_effective_policy_raw_path_json_alloc(platform_name, path, entry_offset,
    metadata_path != NULL ? metadata_path : "", entry_offsets != NULL ? entry_offsets : "", &text);
  if (result != 0) {
    fprintf(stderr, "%s\n", text != NULL ? text : "failed building effective policy");
    platform_file_free_text(text);
    return 1;
  }
  puts(text);
  platform_file_free_text(text);
  return 0;
}

static int disassemble_file_to_stdout_with_policy(const char *platform_name, const char *path,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy, const char *metadata_path,
    const char *benchmark_json_path, const char *also_syntax, const char *also_output_path) {
  char *source_text = NULL;
  char *profile_json = NULL;
  char *error = NULL;
  PlatformFileListingArtifact *artifact = NULL;
  int result;
  (void)policy;
  (void)analysis_policy;
  (void)also_syntax;
  result = platform_file_facts_v2_listing_artifact_path_create(platform_name, path,
    metadata_path != NULL ? metadata_path : "", "", &artifact, &error);
  if (result != 0) {
    fprintf(stderr, "%s\n", error != NULL ? error : "facts_v2 listing artifact failed");
    platform_file_free_text(error);
    return 1;
  }
  result = platform_file_facts_v2_listing_artifact_source_text_alloc(artifact, &source_text);
  if (result == 0)
    result = platform_file_facts_v2_listing_artifact_profile_json_alloc(artifact, &profile_json);
  if (result != 0) {
    fprintf(stderr, "%s\n", source_text != NULL ? source_text : "facts_v2 listing artifact source failed");
    platform_file_free_text(source_text);
    platform_file_free_text(profile_json);
    platform_file_facts_v2_listing_artifact_destroy(artifact);
    return 1;
  }
  if (write_benchmark_json_file(benchmark_json_path, profile_json) != 0) {
    platform_file_free_text(source_text);
    platform_file_free_text(profile_json);
    platform_file_facts_v2_listing_artifact_destroy(artifact);
    fprintf(stderr, "failed writing benchmark json: %s\n", benchmark_json_path);
    return 1;
  }
  if (also_output_path != NULL && write_text_file(also_output_path, source_text) != 0) {
    platform_file_free_text(source_text);
    platform_file_free_text(profile_json);
    platform_file_facts_v2_listing_artifact_destroy(artifact);
    fprintf(stderr, "failed writing syntax output: %s\n", also_output_path);
    return 1;
  }
  puts(source_text);
  platform_file_free_text(source_text);
  platform_file_free_text(profile_json);
  platform_file_facts_v2_listing_artifact_destroy(artifact);
  return 0;
}

static int disassemble_raw_to_stdout_with_policy(const char *platform_name, const char *path, uint32_t entry_offset,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy, const char *metadata_path,
    const char *benchmark_json_path) {
  char *source_text = NULL;
  char *profile_json = NULL;
  char *error = NULL;
  PlatformFileListingArtifact *artifact = NULL;
  int result;
  (void)policy;
  (void)analysis_policy;
  result = platform_file_facts_v2_listing_artifact_raw_path_create(platform_name, path, entry_offset,
    metadata_path != NULL ? metadata_path : "", "", &artifact, &error);
  if (result != 0) {
    fprintf(stderr, "%s\n", error != NULL ? error : "facts_v2 listing artifact failed");
    platform_file_free_text(error);
    return 1;
  }
  result = platform_file_facts_v2_listing_artifact_source_text_alloc(artifact, &source_text);
  if (result == 0)
    result = platform_file_facts_v2_listing_artifact_profile_json_alloc(artifact, &profile_json);
  if (result != 0) {
    fprintf(stderr, "%s\n", source_text != NULL ? source_text : "facts_v2 listing artifact source failed");
    platform_file_free_text(source_text);
    platform_file_free_text(profile_json);
    platform_file_facts_v2_listing_artifact_destroy(artifact);
    return 1;
  }
  if (write_benchmark_json_file(benchmark_json_path, profile_json) != 0) {
    platform_file_free_text(source_text);
    platform_file_free_text(profile_json);
    platform_file_facts_v2_listing_artifact_destroy(artifact);
    fprintf(stderr, "failed writing benchmark json: %s\n", benchmark_json_path);
    return 1;
  }
  puts(source_text);
  platform_file_free_text(source_text);
  platform_file_free_text(profile_json);
  platform_file_facts_v2_listing_artifact_destroy(artifact);
  return 0;
}

static int parse_u32_arg(const char *text, uint32_t *out_value) {
  M68kParseU32Result result;
  if (text == NULL || out_value == NULL) return 0;
  result = m68k_parse_number_u32(text);
  if (!result.ok) return 0;
  *out_value = result.value;
  return 1;
}

static int parse_analysis_policy_option(int argc, char **argv, int *argi, M68kAnalysisPolicy *policy,
    const char **metadata_path) {
  M68kParseCpuResult cpu_result;
  if (argc <= 0 || argv == NULL || argi == NULL || policy == NULL) return 0;
  if (strcmp(argv[*argi], "--max-cpu") == 0) {
    cpu_result = (*argi + 1 < argc) ? m68k_parse_cpu_name(argv[*argi + 1]) : (M68kParseCpuResult){0};
    if (!cpu_result.ok) {
      fprintf(stderr, "unknown cpu: %s\n", (*argi + 1 < argc) ? argv[*argi + 1] : "");
      return -1;
    }
    policy->max_cpu = cpu_result.cpu;
    *argi += 1;
    return 1;
  }
  if (strcmp(argv[*argi], "--entry-register-seed") == 0) {
    if (*argi + 1 >= argc || !platform_file_analysis_policy_add_register_seed_arg(policy, argv[*argi + 1])) {
      fprintf(stderr, "bad entry register seed: %s\n", (*argi + 1 < argc) ? argv[*argi + 1] : "");
      return -1;
    }
    *argi += 1;
    return 1;
  }
  if (strcmp(argv[*argi], "--entry-offset") == 0) {
    if (*argi + 1 >= argc || !platform_file_analysis_policy_add_entry_point_arg(policy, argv[*argi + 1])) {
      fprintf(stderr, "bad entry offset: %s\n", (*argi + 1 < argc) ? argv[*argi + 1] : "");
      return -1;
    }
    *argi += 1;
    return 1;
  }
  if (strcmp(argv[*argi], "--target-metadata") == 0) {
    if (*argi + 1 >= argc || metadata_path == NULL) {
      fprintf(stderr, "bad target metadata: %s\n", (*argi + 1 < argc) ? argv[*argi + 1] : "");
      return -1;
    }
    *metadata_path = argv[*argi + 1];
    *argi += 1;
    return 1;
  }
  return 0;
}

static int load_analysis_policy_metadata_option(M68kAnalysisPolicy *policy, const char *metadata_path,
    const char *platform_name) {
  M68kDiagList diagnostics;
  if (metadata_path == NULL || metadata_path[0] == '\0') return 0;
  m68k_diag_list_reset(&diagnostics);
  if (platform_file_analysis_policy_load_target_metadata_for_platform(policy, metadata_path, platform_name,
      m68k_diag_sink(&diagnostics)) == 0)
    return 0;
  fprintf(stderr, "%s\n", m68k_diag_first_message(&diagnostics));
  return -1;
}

static int write_benchmark_json_file(const char *benchmark_json_path, const char *benchmark_json) {
  FILE *out = NULL;
  size_t size;
  if (benchmark_json_path == NULL || benchmark_json == NULL) return 0;
  out = fopen(benchmark_json_path, "wb");
  if (out == NULL) return -1;
  size = strlen(benchmark_json);
  if (fwrite(benchmark_json, 1, size, out) != size) {
    fclose(out);
    return -1;
  }
  if (fclose(out) != 0) return -1;
  return 0;
}

static int write_text_file(const char *path, const char *text) {
  FILE *out;
  size_t size;
  if (path == NULL || text == NULL) return 0;
  out = fopen(path, "wb");
  if (out == NULL) return -1;
  size = strlen(text);
  if (fwrite(text, 1, size, out) != size) {
    fclose(out);
    return -1;
  }
  if (fclose(out) != 0) return -1;
  return 0;
}

int main(int argc, char **argv) {
  M68kRenderPolicy policy;
  M68kAnalysisPolicy *analysis_policy = NULL;
  M68kDiagList parse_diagnostics;
  int argi;
  if (argc == 4 && strcmp(argv[1], "inspect-file") == 0) return inspect_file_to_stdout(argv[2], argv[3]);
  if (argc == 3 && strcmp(argv[1], "type-catalog") == 0) return type_catalog_to_stdout(argv[2]);
  if (argc == 3 && strcmp(argv[1], "naming-catalog") == 0) return naming_catalog_to_stdout(argv[2]);
  if (argc == 3 && strcmp(argv[1], "os-metadata-catalog") == 0) return os_metadata_catalog_to_stdout(argv[2]);
  if (argc == 7 && strcmp(argv[1], "api-input-struct") == 0)
    return api_input_struct_to_stdout(argv[2], argv[3], argv[4], argv[5], argv[6]);
  if ((argc == 5 || argc == 7) && strcmp(argv[1], "identify-packed-range") == 0) {
    const char *provider_id = "ancient-cli", *provider_path = "", *path;
    uint32_t offset, size;
    int base_arg = 2;
    if (argc == 7) {
      if (strcmp(argv[2], "--provider") != 0) {
        fprintf(stderr, "expected --provider\n");
        return 2;
      }
      provider_path = argv[3];
      base_arg = 4;
    }
    path = argv[base_arg];
    if (!parse_u32_arg(argv[base_arg + 1], &offset) || !parse_u32_arg(argv[base_arg + 2], &size)) {
      fprintf(stderr, "bad packed range\n");
      return 2;
    }
    return identify_packed_range_to_stdout(provider_id, provider_path, path, offset, size);
  }
  if ((argc == 6 || argc == 8) && strcmp(argv[1], "decompress-packed-range") == 0) {
    const char *provider_id = "ancient-cli", *provider_path = "", *path, *output_path;
    uint32_t offset, size;
    int base_arg = 2;
    if (argc == 8) {
      if (strcmp(argv[2], "--provider") != 0) {
        fprintf(stderr, "expected --provider\n");
        return 2;
      }
      provider_path = argv[3];
      base_arg = 4;
    }
    path = argv[base_arg];
    output_path = argv[base_arg + 3];
    if (!parse_u32_arg(argv[base_arg + 1], &offset) || !parse_u32_arg(argv[base_arg + 2], &size)) {
      fprintf(stderr, "bad packed range\n");
      return 2;
    }
    return decompress_packed_range_to_stdout(provider_id, provider_path, path, offset, size, output_path);
  }
  analysis_policy = (M68kAnalysisPolicy *)calloc(1U, sizeof(*analysis_policy));
  if (analysis_policy == NULL) {
    fprintf(stderr, "out of memory\n");
    return 1;
  }
  if (argc == 4 && strcmp(argv[1], "analyze-file") == 0) {
    m68k_analysis_policy_init_default(analysis_policy);
    return facts_v2_analysis_file_to_stdout(argv[2], argv[3], analysis_policy);
  }
  if (argc >= 4 && strcmp(argv[1], "effective-policy-file") == 0) {
    const char *platform_name = NULL;
    const char *path = NULL;
    const char *metadata_path = "";
    char entry_offsets[512];
    entry_offsets[0] = '\0';
    for (argi = 2; argi < argc; ++argi) {
      if (strcmp(argv[argi], "--target-metadata") == 0) {
        if (argi + 1 >= argc) {
          fprintf(stderr, "missing target metadata path\n");
          return 2;
        }
        metadata_path = argv[++argi];
        continue;
      }
      if (strcmp(argv[argi], "--entry-offset") == 0) {
        if (argi + 1 >= argc || !append_entry_offset_option(entry_offsets, sizeof(entry_offsets), argv[argi + 1])) {
          fprintf(stderr, "bad entry offset: %s\n", (argi + 1 < argc) ? argv[argi + 1] : "");
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
    return effective_policy_file_to_stdout(platform_name, path, metadata_path, entry_offsets);
  }
  if (argc >= 5 && strcmp(argv[1], "effective-policy-raw") == 0) {
    const char *platform_name = NULL;
    const char *path = NULL;
    const char *metadata_path = "";
    char entry_offsets[512];
    uint32_t entry_offset = 0U;
    int have_entry_offset = 0;
    entry_offsets[0] = '\0';
    for (argi = 2; argi < argc; ++argi) {
      if (strcmp(argv[argi], "--target-metadata") == 0) {
        if (argi + 1 >= argc) {
          fprintf(stderr, "missing target metadata path\n");
          return 2;
        }
        metadata_path = argv[++argi];
        continue;
      }
      if (strcmp(argv[argi], "--entry-offset") == 0) {
        if (argi + 1 >= argc || !append_entry_offset_option(entry_offsets, sizeof(entry_offsets), argv[argi + 1])) {
          fprintf(stderr, "bad entry offset: %s\n", (argi + 1 < argc) ? argv[argi + 1] : "");
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
      if (!have_entry_offset) {
        if (!parse_u32_arg(argv[argi], &entry_offset)) {
          fprintf(stderr, "bad entry offset: %s\n", argv[argi]);
          return 2;
        }
        have_entry_offset = 1;
        continue;
      }
      fprintf(stderr, "unexpected argument: %s\n", argv[argi]);
      return 2;
    }
    if (platform_name == NULL || path == NULL || !have_entry_offset) {
      fprintf(stderr, "missing platform/file/entry-offset\n");
      return 2;
    }
    return effective_policy_raw_to_stdout(platform_name, path, entry_offset, metadata_path, entry_offsets);
  }
  if (argc >= 5 && strcmp(argv[1], "analyze-raw") == 0) {
    const char *platform_name = NULL;
    const char *path = NULL;
    const char *metadata_path = NULL;
    uint32_t entry_offset = 0U;
    int have_entry_offset = 0;
    m68k_analysis_policy_init_default(analysis_policy);
    for (argi = 2; argi < argc; ++argi) {
      int policy_result = parse_analysis_policy_option(argc, argv, &argi, analysis_policy, &metadata_path);
      if (policy_result < 0) return 2;
      if (policy_result > 0) continue;
      if (platform_name == NULL) {
        platform_name = argv[argi];
        continue;
      }
      if (path == NULL) {
        path = argv[argi];
        continue;
      }
      if (!have_entry_offset) {
        if (!parse_u32_arg(argv[argi], &entry_offset)) {
          fprintf(stderr, "bad entry offset: %s\n", argv[argi]);
          return 2;
        }
        have_entry_offset = 1;
        continue;
      }
      fprintf(stderr, "unexpected argument: %s\n", argv[argi]);
      return 2;
    }
    if (platform_name == NULL || path == NULL || !have_entry_offset) {
      fprintf(stderr, "missing platform/file/entry-offset\n");
      return 2;
    }
    if (load_analysis_policy_metadata_option(analysis_policy, metadata_path, platform_name) != 0) return 2;
    return facts_v2_analysis_raw_to_stdout(platform_name, path, entry_offset, analysis_policy);
  }
  if (argc >= 4 && strcmp(argv[1], "analyze-file") == 0) {
    const char *platform_name = NULL;
    const char *path = NULL;
    const char *metadata_path = NULL;
    m68k_analysis_policy_init_default(analysis_policy);
    for (argi = 2; argi < argc; ++argi) {
      int policy_result = parse_analysis_policy_option(argc, argv, &argi, analysis_policy, &metadata_path);
      if (policy_result < 0) return 2;
      if (policy_result > 0) continue;
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
    if (load_analysis_policy_metadata_option(analysis_policy, metadata_path, platform_name) != 0) return 2;
    return facts_v2_analysis_file_to_stdout(platform_name, path, analysis_policy);
  }
  if (argc >= 4 && strcmp(argv[1], "disassemble-file") == 0) {
    const char *platform_name = NULL, *path = NULL, *metadata_path = NULL;
    const char *benchmark_json_path = NULL, *also_syntax = NULL, *also_output_path = NULL;
    m68k_render_policy_init_for_syntax(&policy, M68K_IR_SYNTAX_CANONICAL);
    m68k_analysis_policy_init_default(analysis_policy);
    for (argi = 2; argi < argc; ++argi) {
      int policy_result = parse_analysis_policy_option(argc, argv, &argi, analysis_policy, &metadata_path);
      if (policy_result < 0) return 2;
      if (policy_result > 0) continue;
      if (strcmp(argv[argi], "--benchmark-json-out") == 0) {
        if (argi + 1 >= argc) {
          fprintf(stderr, "missing benchmark json output path\n");
          return 2;
        }
        benchmark_json_path = argv[++argi];
        continue;
      }
      if (strcmp(argv[argi], "--also-syntax-output") == 0) {
        if (argi + 2 >= argc) {
          fprintf(stderr, "missing syntax output arguments\n");
          return 2;
        }
        also_syntax = argv[++argi];
        also_output_path = argv[++argi];
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
    if (load_analysis_policy_metadata_option(analysis_policy, metadata_path, platform_name) != 0) return 2;
    return disassemble_file_to_stdout_with_policy(platform_name, path, &policy, analysis_policy, metadata_path,
      benchmark_json_path, also_syntax, also_output_path);
  }
  if (argc >= 5 && strcmp(argv[1], "disassemble-raw") == 0) {
    const char *platform_name = NULL;
    const char *path = NULL;
    const char *metadata_path = NULL;
    const char *benchmark_json_path = NULL;
    uint32_t entry_offset = 0U;
    int have_entry_offset = 0;
    m68k_render_policy_init_for_syntax(&policy, M68K_IR_SYNTAX_CANONICAL);
    m68k_analysis_policy_init_default(analysis_policy);
    for (argi = 2; argi < argc; ++argi) {
      int policy_result = parse_analysis_policy_option(argc, argv, &argi, analysis_policy, &metadata_path);
      if (policy_result < 0) return 2;
      if (policy_result > 0) continue;
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
      if (!have_entry_offset) {
        if (!parse_u32_arg(argv[argi], &entry_offset)) {
          fprintf(stderr, "bad entry offset: %s\n", argv[argi]);
          return 2;
        }
        have_entry_offset = 1;
        continue;
      }
      fprintf(stderr, "unexpected argument: %s\n", argv[argi]);
      return 2;
    }
    if (platform_name == NULL || path == NULL || !have_entry_offset) {
      fprintf(stderr, "missing platform/file/entry-offset\n");
      return 2;
    }
    if (load_analysis_policy_metadata_option(analysis_policy, metadata_path, platform_name) != 0) return 2;
    return disassemble_raw_to_stdout_with_policy(platform_name, path, entry_offset, &policy, analysis_policy,
      metadata_path,
      benchmark_json_path);
  }
  fprintf(stderr, "usage: %s inspect-file <amiga-hunk|atari-st> <file>\n", argv[0]);
  fprintf(stderr, "   or: %s type-catalog <amiga-hunk|atari-st>\n", argv[0]);
  fprintf(stderr, "   or: %s naming-catalog <amiga-hunk|atari-st>\n", argv[0]);
  fprintf(stderr, "   or: %s os-metadata-catalog <amiga-hunk|atari-st>\n", argv[0]);
  fprintf(stderr, "   or: %s api-input-struct <amiga-hunk|atari-st> <library> <function> <input> <struct>\n", argv[0]);
  fprintf(stderr, "   or: %s effective-policy-file [--target-metadata file] [--entry-offset offset] "
    "<amiga-hunk|atari-st> <file>\n", argv[0]);
  fprintf(stderr, "   or: %s effective-policy-raw [--target-metadata file] [--entry-offset offset] "
    "<amiga-raw|atari-st-raw> <file> <entry-offset>\n", argv[0]);
  fprintf(stderr, "   or: %s analyze-raw <amiga-raw|atari-st-raw> <file> <entry-offset>\n", argv[0]);
  fprintf( stderr, "   or: %s analyze-file [--max-cpu " "<68000|68010|68020|68030|68040|68060>] <amiga-hunk|atari-st> "
    "<file>\n", argv[0]);
  fprintf(stderr, "   or: %s disassemble-file [--max-cpu <68000|68010|68020|68030|68040|68060>] [--syntax "
    "canonical|genam|vasm] [--no-strings] [--no-longs]\n", argv[0]);
  fprintf(stderr, "          [--no-generated-names] [--min-os-version <1.3|2.0|3.1|3.5>] [--benchmark-json-out file]\n");
  fprintf(stderr, "          [--code-label-prefix p] [--call-label-prefix p] [--data-label-prefix p]\n");
  fprintf(stderr, "          <amiga-hunk|atari-st> <file>\n");
  fprintf(stderr, "   or: %s disassemble-raw [--syntax canonical|genam|vasm] <amiga-raw|atari-st-raw> "
    "<file> <entry-offset>\n", argv[0]);
  return 2;
}
