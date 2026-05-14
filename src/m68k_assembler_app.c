#include "m68k_assembler_app.h"
#include "m68k_assembler_lib.h"
#include "m68k_backend.h"
#include "m68k_instruction_spec.h"
#include "m68k_ir.h"
#include "m68k_ir_codec.h"
#include "m68k_plain_parse.h"
#include "m68k_simple_source.h"
#include "m68k_source_ir_render.h"
#include "m68k_source_model.h"
#include "m68k_source_pipeline.h"
#include "platform_atari_st.h"
#include "platform_common.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_CASE_BYTES 64

static double assembler_elapsed_seconds(clock_t start_ticks, clock_t end_ticks) {
  return ((double)(end_ticks - start_ticks)) / (double)CLOCKS_PER_SEC;
}

static void assembler_add_error(M68kDiagSink diagnostics, const char *message) {
  if (message == NULL || message[0] == '\0') message = "platform assembler failed";
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED, message);
}

static M68kPlatformBackendKind platform_backend_kind_for_name(const char *backend_name) {
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  return backend != NULL ? backend->platform_kind : M68K_PLATFORM_BACKEND_UNKNOWN;
}

static M68kPlatformBackendKind raw_platform_backend_kind_for_name(const char *backend_name) {
  if (backend_name != NULL && strcmp(backend_name, "amiga-raw") == 0)
    return M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  if (backend_name != NULL && strcmp(backend_name, "atari-st-raw") == 0)
    return M68K_PLATFORM_BACKEND_ATARI_ST;
  return platform_backend_kind_for_name(backend_name);
}

static uint32_t file_size_u32(const char *path) {
  FILE *input;
  int64_t size;
  if (path == NULL) return 0U;
  input = fopen(path, "rb");
  if (input == NULL) return 0U;
  if (fseek(input, 0, SEEK_END) != 0) {
    fclose(input);
    return 0U;
  }
  size = (int64_t)ftell(input);
  fclose(input);
  if (size <= 0L) return 0U;
  if ((uint64_t)size > 0xFFFFFFFFULL) return 0xFFFFFFFFU;
  return (uint32_t)size;
}

static int make_temp_output_path(char *path_buf, size_t path_buf_size) {
  char temp_name[L_tmpnam];
  if (path_buf == NULL || path_buf_size == 0U) return -1;
  if (tmpnam_s(temp_name, sizeof(temp_name)) != 0) return -1;
  if (strlen(temp_name) + 4U >= path_buf_size) return -1;
  strcpy(path_buf, temp_name);
  strcat(path_buf, ".bin");
  return 0;
}

static int read_binary_file_alloc(const char *path, unsigned char **out_data, size_t *out_size,
    M68kDiagSink diagnostics) {
  FILE *input = NULL;
  int64_t file_size_value;
  size_t file_size;
  unsigned char *buffer = NULL;
  if (path == NULL || out_data == NULL || out_size == NULL) {
    assembler_add_error(diagnostics, "bad arguments");
    return -1;
  }
  input = fopen(path, "rb");
  if (input == NULL) {
    assembler_add_error(diagnostics, "failed opening assembler output");
    return -1;
  }
  if (fseek(input, 0, SEEK_END) != 0) {
    fclose(input);
    assembler_add_error(diagnostics, "failed sizing assembler output");
    return -1;
  }
  file_size_value = (int64_t)ftell(input);
  if (file_size_value < 0L) {
    fclose(input);
    assembler_add_error(diagnostics, "failed sizing assembler output");
    return -1;
  }
  if (fseek(input, 0, SEEK_SET) != 0) {
    fclose(input);
    assembler_add_error(diagnostics, "failed seeking assembler output");
    return -1;
  }
  file_size = (size_t)file_size_value;
  buffer = (unsigned char *)malloc(file_size != 0U ? file_size : 1U);
  if (buffer == NULL) {
    fclose(input);
    assembler_add_error(diagnostics, "out of memory");
    return -1;
  }
  if (file_size != 0U && fread(buffer, 1, file_size, input) != file_size) {
    fclose(input);
    free(buffer);
    assembler_add_error(diagnostics, "failed reading assembler output");
    return -1;
  }
  fclose(input);
  *out_data = buffer;
  *out_size = file_size;
  return 0;
}

static int write_binary_file(const char *path, const unsigned char *data, size_t size, M68kDiagSink diagnostics) {
  FILE *output = NULL;
  if (path == NULL || path[0] == '\0') {
    assembler_add_error(diagnostics, "bad output path");
    return -1;
  }
  if (data == NULL && size != 0U) {
    assembler_add_error(diagnostics, "bad assembler output buffer");
    return -1;
  }
  output = fopen(path, "wb");
  if (output == NULL) {
    assembler_add_error(diagnostics, "failed opening assembler output");
    return -1;
  }
  if (size != 0U && fwrite(data, 1, size, output) != size) {
    fclose(output);
    assembler_add_error(diagnostics, "failed writing assembler output");
    return -1;
  }
  fclose(output);
  return 0;
}

static int simple_source_parse_instruction_callback(const char *line_text, InstructionSpec *out_instruction,
    int allow_label_symbols, uint8_t target_cpu) {
  (void)allow_label_symbols;
  return m68k_plain_parse_instruction_to_spec(line_text, target_cpu, out_instruction);
}

static int assemble_line_text_for_cpu(const char *line_text, uint8_t target_cpu, uint8_t *out_bytes, size_t max_bytes,
    size_t *out_byte_count, M68kDiagSink diagnostics) {
  M68kInstructionIR instruction;
  M68kIrEncodeResult encoded;
  instruction = m68k_plain_parse_instruction_to_ir(line_text, target_cpu, diagnostics);
  if (m68k_diag_has_errors(diagnostics.list)) {
    if (out_byte_count != NULL) *out_byte_count = 0U;
    return -1;
  }
  encoded = m68k_ir_encode_one(&instruction, out_bytes, max_bytes, diagnostics);
  if (m68k_diag_has_errors(diagnostics.list)) {
    if (out_byte_count != NULL) *out_byte_count = 0U;
    return -1;
  }
  if (out_byte_count != NULL) *out_byte_count = encoded.byte_count;
  return 0;
}

int m68k_assemble_line_to_stdout(const char *line_text, uint8_t target_cpu) {
  unsigned char bytes[MAX_CASE_BYTES];
  size_t size = 0;
  size_t index;
  M68kDiagList diagnostics;
  m68k_diag_list_reset(&diagnostics);
  if (assemble_line_text_for_cpu(line_text, target_cpu, bytes, sizeof(bytes), &size,
      m68k_diag_sink(&diagnostics)) != 0) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&diagnostics)[0] != '\0'
      ? m68k_diag_first_message(&diagnostics) : "unable to parse line");
    return 1;
  }
  for (index = 0; index < size; ++index) printf("%02x", bytes[index]);
  printf("\n");
  return 0;
}

int m68k_assemble_file_to_binary(const char *input_path, const char *output_path, uint8_t target_cpu) {
  return m68k_simple_source_assemble_file_to_binary(input_path, output_path, target_cpu,
    simple_source_parse_instruction_callback);
}

static int assemble_platform_source_to_object_common(const char *input_path, const char *source_text,
    const char *include_dir, uint8_t target_cpu, M68kPlatformBackendKind platform_backend_kind, M68kObject *out_object,
    M68kPlatformAssembleProfile *profile, M68kDiagSink diagnostics) {
  AsmSourceFile source;
  clock_t phase_start;
  size_t index;
  if (m68k_source_model_create(&source) != 0) {
    assembler_add_error(diagnostics, "out of memory");
    return 0;
  }
  snprintf(source.include_dir, sizeof(source.include_dir), "%s", include_dir);
  source.target_cpu = target_cpu;
  source.platform_backend_kind = platform_backend_kind;
  source.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  phase_start = clock();
  if (!((source_text != NULL)
      ? m68k_source_pipeline_parse_text_and_layout(&source, source_text, diagnostics)
      : m68k_source_pipeline_parse_and_layout(&source, input_path, diagnostics))) {
    if (profile != NULL) profile->parse_layout_seconds += assembler_elapsed_seconds(phase_start, clock());
    m68k_source_model_free(&source);
    return 0;
  }
  if (profile != NULL) profile->parse_layout_seconds += assembler_elapsed_seconds(phase_start, clock());
  if (getenv("M68K_ASM_DUMP_LABELS") != NULL) {
    for (index = 0; index < source.symbol_count; ++index) {
      if (source.symbols[index].defined && source.symbols[index].kind == ASM_SOURCE_SYMBOL_LABEL) {
        fprintf(stderr, "%08x %s\n", (unsigned)source.symbols[index].value, source.symbols[index].name);
      }
    }
  }
  phase_start = clock();
  if (!m68k_source_pipeline_emit_object(&source, out_object, diagnostics)) {
    if (profile != NULL) profile->emit_object_seconds += assembler_elapsed_seconds(phase_start, clock());
    m68k_source_model_free(&source);
    return 0;
  }
  if (profile != NULL) profile->emit_object_seconds += assembler_elapsed_seconds(phase_start, clock());
  phase_start = clock();
  if (source.has_atari_st_program_flags && m68k_atari_st_set_program_flags(out_object, source.atari_st_program_flags) != 0) {
    if (profile != NULL) profile->platform_finalize_seconds += assembler_elapsed_seconds(phase_start, clock());
    m68k_source_model_free(&source);
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
      "failed setting Atari ST program flags");
    return 0;
  }
  if (source.has_atari_st_relocation_flag &&
      m68k_atari_st_set_relocation_flag(out_object, (uint16_t)source.atari_st_relocation_flag) != 0) {
    if (profile != NULL) profile->platform_finalize_seconds += assembler_elapsed_seconds(phase_start, clock());
    m68k_source_model_free(&source);
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
      "failed setting Atari ST relocation flag");
    return 0;
  }
  if (source.has_atari_st_symbol_table &&
      m68k_atari_st_set_raw_symbol_table(out_object, source.atari_st_symbol_table_type,
        source.atari_st_symbol_table_data, source.atari_st_symbol_table_size) != 0) {
    if (profile != NULL) profile->platform_finalize_seconds += assembler_elapsed_seconds(phase_start, clock());
    m68k_source_model_free(&source);
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
      "failed setting Atari ST symbol table");
    return 0;
  }
  if (source.has_atari_st_relocation_stream &&
      m68k_atari_st_set_raw_relocation_stream(out_object, source.atari_st_relocation_stream_data,
        source.atari_st_relocation_stream_size) != 0) {
    if (profile != NULL) profile->platform_finalize_seconds += assembler_elapsed_seconds(phase_start, clock());
    m68k_source_model_free(&source);
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
      "failed setting Atari ST relocation stream");
    return 0;
  }
  if (profile != NULL) profile->platform_finalize_seconds += assembler_elapsed_seconds(phase_start, clock());
  m68k_source_model_free(&source);
  return 1;
}

static int assemble_platform_source_to_object(const char *input_path, const char *include_dir, uint8_t target_cpu,
    M68kPlatformBackendKind platform_backend_kind, M68kObject *out_object, M68kPlatformAssembleProfile *profile,
    M68kDiagSink diagnostics) {
  return assemble_platform_source_to_object_common(input_path, NULL, include_dir, target_cpu,
    platform_backend_kind, out_object, profile, diagnostics);
}

static int assemble_platform_source_text_to_object(const char *source_text, const char *include_dir,
    uint8_t target_cpu, M68kPlatformBackendKind platform_backend_kind, M68kObject *out_object,
    M68kPlatformAssembleProfile *profile, M68kDiagSink diagnostics) {
  return assemble_platform_source_to_object_common(NULL, source_text, include_dir, target_cpu,
    platform_backend_kind, out_object, profile, diagnostics);
}

int m68k_assemble_platform_file_to_output(const char *backend_name, const char *include_dir, const char *input_path,
    const char *output_path, uint8_t target_cpu) {
  const M68kBackend *backend = NULL;
  M68kObject object;
  M68kDiagList diagnostics;
  M68kPlatformBackendKind platform_backend_kind = M68K_PLATFORM_BACKEND_UNKNOWN;
  m68k_diag_list_reset(&diagnostics);
  backend = m68k_backend_by_name(backend_name);
  if (backend == NULL || backend->write_file == NULL) {
    fprintf(stderr, "backend unavailable: %s\n", backend_name);
    return 2;
  }
  platform_backend_kind = platform_backend_kind_for_name(backend_name);
  if (!assemble_platform_source_to_object(input_path, include_dir, target_cpu,
      platform_backend_kind, &object, NULL, m68k_diag_sink(&diagnostics))) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&diagnostics));
    return 1;
  }
  m68k_diag_list_reset(&diagnostics);
  if (backend->write_file(output_path, &object, m68k_diag_sink(&diagnostics)) != 0) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&diagnostics));
    m68k_object_destroy(&object);
    return 1;
  }
  m68k_object_destroy(&object);
  return 0;
}

static int assemble_platform_source_to_output_buffer_alloc_impl(const char *backend_name, const char *include_dir,
    const char *input_path, const char *source_text, const char *output_path, int remove_output_after_read,
    uint8_t target_cpu, unsigned char **out_data, size_t *out_size,
    M68kPlatformAssembleProfile *out_profile, M68kDiagSink diagnostics) {
  const M68kBackend *backend;
  M68kPlatformAssembleProfile profile;
  M68kPlatformBackendKind platform_backend_kind;
  M68kObject object;
  char temp_path[512];
  const char *write_path;
  clock_t total_start;
  clock_t phase_start;
  memset(&profile, 0, sizeof(profile));
  temp_path[0] = '\0';
  if (out_data == NULL || out_size == NULL || (input_path == NULL && source_text == NULL)) {
    assembler_add_error(diagnostics, "bad arguments");
    return -1;
  }
  *out_data = NULL;
  *out_size = 0U;
  total_start = clock();
  profile.source_bytes = source_text != NULL
    ? (uint32_t)((strlen(source_text) > 0xFFFFFFFFUL) ? 0xFFFFFFFFUL : strlen(source_text))
    : file_size_u32(input_path);
  backend = m68k_backend_by_name(backend_name);
  if (backend == NULL || (backend->write_buffer == NULL && backend->write_file == NULL)) {
    assembler_add_error(diagnostics, "backend unavailable");
    if (out_profile != NULL) {
      profile.total_seconds = assembler_elapsed_seconds(total_start, clock());
      *out_profile = profile;
    }
    return -1;
  }
  platform_backend_kind = platform_backend_kind_for_name(backend_name);
  if (!(source_text != NULL
      ? assemble_platform_source_text_to_object(source_text, include_dir != NULL ? include_dir : "", target_cpu,
          platform_backend_kind, &object, &profile, diagnostics)
      : assemble_platform_source_to_object(input_path, include_dir != NULL ? include_dir : "", target_cpu,
          platform_backend_kind, &object, &profile, diagnostics))) {
    if (out_profile != NULL) {
      profile.total_seconds = assembler_elapsed_seconds(total_start, clock());
      *out_profile = profile;
    }
    return -1;
  }
  if (backend->write_buffer != NULL) {
    phase_start = clock();
    if (backend->write_buffer(&object, out_data, out_size, diagnostics) != 0) {
      m68k_object_destroy(&object);
      if (out_profile != NULL) {
        profile.write_buffer_seconds += assembler_elapsed_seconds(phase_start, clock());
        profile.total_seconds = assembler_elapsed_seconds(total_start, clock());
        *out_profile = profile;
      }
      return -1;
    }
    profile.write_buffer_seconds += assembler_elapsed_seconds(phase_start, clock());
    m68k_object_destroy(&object);
    if (output_path != NULL && output_path[0] != '\0') {
      remove(output_path);
      phase_start = clock();
      if (write_binary_file(output_path, *out_data, *out_size, diagnostics) != 0) {
        remove(output_path);
        free(*out_data);
        *out_data = NULL;
        *out_size = 0U;
        if (out_profile != NULL) {
          profile.write_file_seconds += assembler_elapsed_seconds(phase_start, clock());
          profile.total_seconds = assembler_elapsed_seconds(total_start, clock());
          *out_profile = profile;
        }
        return -1;
      }
      profile.write_file_seconds += assembler_elapsed_seconds(phase_start, clock());
    }
    profile.rebuilt_bytes = *out_size > 0xFFFFFFFFU ? 0xFFFFFFFFU : (uint32_t)*out_size;
    profile.total_seconds = assembler_elapsed_seconds(total_start, clock());
    if (out_profile != NULL) *out_profile = profile;
    return 0;
  }
  write_path = output_path;
  if (write_path == NULL || write_path[0] == '\0') {
    if (make_temp_output_path(temp_path, sizeof(temp_path)) != 0) {
      m68k_object_destroy(&object);
      assembler_add_error(diagnostics, "failed creating temp path");
      if (out_profile != NULL) {
        profile.total_seconds = assembler_elapsed_seconds(total_start, clock());
        *out_profile = profile;
      }
      return -1;
    }
    write_path = temp_path;
    remove_output_after_read = 1;
  } else {
    remove(write_path);
  }
  phase_start = clock();
  if (backend->write_file(write_path, &object, diagnostics) != 0) {
    remove(write_path);
    m68k_object_destroy(&object);
    if (out_profile != NULL) {
      profile.write_file_seconds += assembler_elapsed_seconds(phase_start, clock());
      profile.total_seconds = assembler_elapsed_seconds(total_start, clock());
      *out_profile = profile;
    }
    return -1;
  }
  profile.write_file_seconds += assembler_elapsed_seconds(phase_start, clock());
  m68k_object_destroy(&object);
  phase_start = clock();
  if (read_binary_file_alloc(write_path, out_data, out_size, diagnostics) != 0) {
    if (remove_output_after_read) remove(write_path);
    if (out_profile != NULL) {
      profile.read_output_seconds += assembler_elapsed_seconds(phase_start, clock());
      profile.total_seconds = assembler_elapsed_seconds(total_start, clock());
      *out_profile = profile;
    }
    return -1;
  }
  profile.read_output_seconds += assembler_elapsed_seconds(phase_start, clock());
  if (remove_output_after_read) remove(write_path);
  profile.rebuilt_bytes = *out_size > 0xFFFFFFFFU ? 0xFFFFFFFFU : (uint32_t)*out_size;
  profile.total_seconds = assembler_elapsed_seconds(total_start, clock());
  if (out_profile != NULL) *out_profile = profile;
  return 0;
}

int m68k_assemble_platform_file_to_buffer_alloc(const char *backend_name, const char *include_dir,
    const char *input_path, uint8_t target_cpu, unsigned char **out_data, size_t *out_size,
    M68kPlatformAssembleProfile *out_profile, M68kDiagSink diagnostics) {
  return assemble_platform_source_to_output_buffer_alloc_impl(backend_name, include_dir, input_path, NULL, NULL, 1,
    target_cpu, out_data, out_size, out_profile, diagnostics);
}

int m68k_assemble_platform_file_to_output_buffer_alloc(const char *backend_name, const char *include_dir,
    const char *input_path, const char *output_path, uint8_t target_cpu, unsigned char **out_data, size_t *out_size,
    M68kPlatformAssembleProfile *out_profile, M68kDiagSink diagnostics) {
  if (output_path == NULL || output_path[0] == '\0') {
    assembler_add_error(diagnostics, "bad output path");
    return -1;
  }
  return assemble_platform_source_to_output_buffer_alloc_impl(backend_name, include_dir, input_path, NULL,
    output_path, 0, target_cpu, out_data, out_size, out_profile, diagnostics);
}

int m68k_assemble_platform_source_text_to_buffer_alloc(const char *backend_name, const char *include_dir,
    const char *source_text, uint8_t target_cpu, unsigned char **out_data, size_t *out_size,
    M68kPlatformAssembleProfile *out_profile, M68kDiagSink diagnostics) {
  return assemble_platform_source_to_output_buffer_alloc_impl(backend_name, include_dir, NULL, source_text, NULL, 1,
    target_cpu, out_data, out_size, out_profile, diagnostics);
}

int m68k_assemble_platform_source_text_to_output_buffer_alloc(const char *backend_name, const char *include_dir,
    const char *source_text, const char *output_path, uint8_t target_cpu, unsigned char **out_data, size_t *out_size,
    M68kPlatformAssembleProfile *out_profile, M68kDiagSink diagnostics) {
  if (output_path == NULL || output_path[0] == '\0') {
    assembler_add_error(diagnostics, "bad output path");
    return -1;
  }
  return assemble_platform_source_to_output_buffer_alloc_impl(backend_name, include_dir, NULL, source_text,
    output_path, 0, target_cpu, out_data, out_size, out_profile, diagnostics);
}

int m68k_assemble_platform_source_text_to_raw_buffer_alloc(const char *backend_name, const char *include_dir,
    const char *source_text, const char *output_path, uint8_t target_cpu, unsigned char **out_data, size_t *out_size,
    M68kPlatformAssembleProfile *out_profile, M68kDiagSink diagnostics) {
  M68kPlatformAssembleProfile profile;
  M68kPlatformBackendKind platform_backend_kind;
  M68kObject object;
  const M68kSection *section;
  clock_t total_start;
  clock_t phase_start;
  memset(&profile, 0, sizeof(profile));
  memset(&object, 0, sizeof(object));
  if (out_data == NULL || out_size == NULL || source_text == NULL) {
    assembler_add_error(diagnostics, "bad arguments");
    return -1;
  }
  *out_data = NULL;
  *out_size = 0U;
  total_start = clock();
  profile.source_bytes = strlen(source_text) > 0xFFFFFFFFUL ? 0xFFFFFFFFU : (uint32_t)strlen(source_text);
  platform_backend_kind = raw_platform_backend_kind_for_name(backend_name);
  if (platform_backend_kind == M68K_PLATFORM_BACKEND_UNKNOWN) {
    assembler_add_error(diagnostics, "raw backend unavailable");
    if (out_profile != NULL) {
      profile.total_seconds = assembler_elapsed_seconds(total_start, clock());
      *out_profile = profile;
    }
    return -1;
  }
  if (!assemble_platform_source_text_to_object(source_text, include_dir != NULL ? include_dir : "", target_cpu,
      platform_backend_kind, &object, &profile, diagnostics)) {
    if (out_profile != NULL) {
      profile.total_seconds = assembler_elapsed_seconds(total_start, clock());
      *out_profile = profile;
    }
    return -1;
  }
  if (object.section_count != 1U) {
    m68k_object_destroy(&object);
    assembler_add_error(diagnostics, "raw output requires exactly one section");
    if (out_profile != NULL) {
      profile.total_seconds = assembler_elapsed_seconds(total_start, clock());
      *out_profile = profile;
    }
    return -1;
  }
  section = &object.sections[0];
  if (section->size != section->data_size || (section->size != 0U && section->data == NULL)) {
    m68k_object_destroy(&object);
    assembler_add_error(diagnostics, "raw output cannot contain uninitialised section bytes");
    if (out_profile != NULL) {
      profile.total_seconds = assembler_elapsed_seconds(total_start, clock());
      *out_profile = profile;
    }
    return -1;
  }
  phase_start = clock();
  if (section->data_size != 0U) {
    *out_data = (unsigned char *)malloc(section->data_size);
    if (*out_data == NULL) {
      m68k_object_destroy(&object);
      assembler_add_error(diagnostics, "out of memory");
      if (out_profile != NULL) {
        profile.write_buffer_seconds += assembler_elapsed_seconds(phase_start, clock());
        profile.total_seconds = assembler_elapsed_seconds(total_start, clock());
        *out_profile = profile;
      }
      return -1;
    }
    memcpy(*out_data, section->data, section->data_size);
  }
  *out_size = section->data_size;
  profile.write_buffer_seconds += assembler_elapsed_seconds(phase_start, clock());
  m68k_object_destroy(&object);
  if (output_path != NULL && output_path[0] != '\0') {
    remove(output_path);
    phase_start = clock();
    if (write_binary_file(output_path, *out_data, *out_size, diagnostics) != 0) {
      remove(output_path);
      free(*out_data);
      *out_data = NULL;
      *out_size = 0U;
      if (out_profile != NULL) {
        profile.write_file_seconds += assembler_elapsed_seconds(phase_start, clock());
        profile.total_seconds = assembler_elapsed_seconds(total_start, clock());
        *out_profile = profile;
      }
      return -1;
    }
    profile.write_file_seconds += assembler_elapsed_seconds(phase_start, clock());
  }
  profile.rebuilt_bytes = *out_size > 0xFFFFFFFFU ? 0xFFFFFFFFU : (uint32_t)*out_size;
  profile.total_seconds = assembler_elapsed_seconds(total_start, clock());
  if (out_profile != NULL) *out_profile = profile;
  return 0;
}

int m68k_render_source_file_to_stdout(const char *input_path, const char *include_dir, uint8_t target_cpu,
    const M68kRenderPolicy *policy) {
  M68kSourceIrParseResult parsed;
  M68kSourceIrRenderResult rendered;
  M68kSourceFileIR source_file;
  parsed = m68k_source_ir_parse_file(input_path, include_dir, target_cpu);
  if (m68k_diag_has_errors(&parsed.diagnostics)) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&parsed.diagnostics));
    return 1;
  }
  source_file = parsed.source_file;
  if (source_file.section_count == 0U) {
    fprintf(stderr, "empty source ir\n");
    m68k_ir_source_file_destroy(&source_file);
    return 1;
  }
  rendered = m68k_source_ir_render_with_policy(&source_file, policy);
  m68k_ir_source_file_destroy(&source_file);
  if (m68k_diag_has_errors(&rendered.diagnostics)) {
    fprintf(stderr, "%s\n", m68k_diag_first_message(&rendered.diagnostics));
    return 1;
  }
  if (rendered.text == NULL || rendered.text[0] == '\0') {
    fprintf(stderr, "empty rendered source ir\n");
    free(rendered.text);
    return 1;
  }
  puts(rendered.text);
  free(rendered.text);
  return 0;
}
