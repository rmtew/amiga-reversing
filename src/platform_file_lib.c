#include "platform_file_lib.h"
#include "json_builder.h"
#include "m68k_backend.h"
#include "m68k_ir_codec.h"
#include "m68k_object.h"
#include "m68k_source_ir_render.h"
#include "platform_atari_st.h"
#include "platform_common.h"

#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


static const char *file_kind_name(M68kPlatformFileKind kind) {
  if (kind == M68K_PLATFORM_FILE_EXECUTABLE) return "executable";
  if (kind == M68K_PLATFORM_FILE_OBJECT) return "object";
  return "unknown";
}

static const char *section_kind_name(M68kSectionKind kind) {
  if (kind == M68K_SECTION_CODE) return "code";
  if (kind == M68K_SECTION_DATA) return "data";
  return "bss";
}

static const char *cpu_name(uint8_t cpu) {
  switch (cpu) {
  case M68K_ASM_CPU_68000: return "68000";
  case M68K_ASM_CPU_68010: return "68010";
  case M68K_ASM_CPU_68020: return "68020";
  case M68K_ASM_CPU_68030: return "68030";
  case M68K_ASM_CPU_68040: return "68040";
  case M68K_ASM_CPU_68060: return "68060";
  default: return "unknown";
  }
}

static uint8_t effective_analysis_max_cpu(const M68kAnalysisPolicy *policy) {
  if (policy == NULL) return M68K_ASM_CPU_68060;
  if (policy->max_cpu > M68K_ASM_CPU_68060) return M68K_ASM_CPU_68060;
  return policy->max_cpu;
}

static uint8_t instruction_required_cpu(const M68kInstructionIR *instruction) {
  const M68kAsmFormDef *form;
  uint8_t cpu;
  if (instruction == NULL) return M68K_ASM_CPU_68000;
  if (instruction->target_cpu <= M68K_ASM_CPU_68060) return instruction->target_cpu;
  if ((size_t)instruction->form_index >= m68k_asm_form_count()) return instruction->target_cpu;
  form = &g_m68k_asm_forms[instruction->form_index];
  for (cpu = M68K_ASM_CPU_68000; cpu <= M68K_ASM_CPU_68060; ++cpu) {
    if ((form->cpu_mask & (1u << cpu)) != 0u) return cpu;
  }
  return instruction->target_cpu;
}

static void update_required_cpu(M68kAnalysisFindings *findings, uint8_t required_cpu) {
  if (findings == NULL) return;
  if (required_cpu > findings->required_cpu) findings->required_cpu = required_cpu;
}

static int decode_instruction_with_policy(const uint8_t *data, size_t size, uint32_t offset,
    const M68kAnalysisPolicy *policy, M68kAnalysisFindings *findings, M68kInstructionIR *out_instruction,
    char *out_error, size_t out_error_size) {
  uint8_t max_cpu = effective_analysis_max_cpu(policy);
  uint8_t cpu;
  char decode_error[128];
  (void)offset;
  for (cpu = M68K_ASM_CPU_68000; cpu <= M68K_ASM_CPU_68060; ++cpu) {
    if (m68k_ir_decode_one(data, size, cpu, out_instruction, decode_error, sizeof(decode_error)) == 0) {
      uint8_t required_cpu = instruction_required_cpu(out_instruction);
      update_required_cpu(findings, required_cpu);
      if (required_cpu > max_cpu)
        if (findings != NULL) findings->cpu_violation_count += 1U;
      m68k_platform_set_error(out_error, out_error_size, "");
      return 1;
    }
    if (cpu == M68K_ASM_CPU_68060) break;
  }
  m68k_platform_set_error(out_error, out_error_size, "unknown instruction bytes");
  return 0;
}

static int format_cpu_violation_comment(char *buf, size_t buf_size, const M68kInstructionIR *instruction,
    const M68kAnalysisPolicy *policy) {
  uint8_t max_cpu = effective_analysis_max_cpu(policy);
  uint8_t required_cpu = instruction_required_cpu(instruction);
  if (buf == NULL || buf_size == 0U) return 0;
  if (required_cpu <= max_cpu) {
    buf[0] = '\0';
    return 0;
  }
  snprintf(buf, buf_size, "requires %s beyond policy max %s", cpu_name(required_cpu), cpu_name(max_cpu));
  return 1;
}

static int add_cpu_violation(M68kSectionAnalysisIR *section_analysis, uint32_t offset,
    const M68kInstructionIR *instruction, const M68kAnalysisPolicy *policy) {
  char message[128];
  if (!format_cpu_violation_comment(message, sizeof(message), instruction, policy)) return 0;
  return m68k_ir_section_analysis_add_violation( section_analysis, offset, M68K_VIOLATION_CPU_POLICY, message);
}

static int make_temp_output_path(char *path_buf, size_t path_buf_size) {
  char temp_name[L_tmpnam];
  if (tmpnam_s(temp_name, sizeof(temp_name)) != 0)
    return -1;
  if (strlen(temp_name) + 4U >= path_buf_size)
    return -1;
  strcpy(path_buf, temp_name);
  strcat(path_buf, ".bin");
  return 0;
}

static int json_builder_append_hex_bytes(JsonBuilder *builder,
                                         const unsigned char *data,
                                         size_t size) {
  static const char hex[] = "0123456789abcdef";
  size_t i;
  if (json_builder_reserve(builder, size * 2U) != 0)
    return -1;
  for (i = 0; i < size; ++i) {
    builder->data[builder->size++] = hex[data[i] >> 4];
    builder->data[builder->size++] = hex[data[i] & 0x0F];
  }
  builder->data[builder->size] = '\0';
  return 0;
}

static int inspect_object_json(const M68kBackend *backend, const M68kObject *object, char **out_json) {
  JsonBuilder builder = {0};
  size_t i;
  size_t local_count = 0, global_count = 0, external_count = 0;

  for (i = 0; i < object->symbol_count; ++i) {
    if (object->symbols[i].binding == M68K_SYMBOL_LOCAL) ++local_count;
    else if (object->symbols[i].binding == M68K_SYMBOL_GLOBAL) ++global_count;
    else if (object->symbols[i].binding == M68K_SYMBOL_EXTERNAL) ++external_count;
  }
  if (json_builder_append(&builder, "{\"platform\":") != 0)
    goto fail;
  if (json_builder_append_json_string(&builder, backend->name) != 0)
    goto fail;
  if (json_builder_append(&builder, ",\"file_kind\":") != 0)
    goto fail;
  if (json_builder_append_json_string( &builder, file_kind_name(object->platform_file_kind)) != 0)
    goto fail;
  if (json_builder_appendf( &builder, ",\"section_count\":%zu,\"symbol_count\":%zu,\"fixup_count\":%zu",
      object->section_count, object->symbol_count,
      object->fixup_count) != 0)
    goto fail;
  if (json_builder_appendf(&builder, ",\"local_symbol_count\":%zu,\"global_symbol_count\":%zu,"
      "\"external_symbol_count\":%zu", local_count, global_count, external_count) != 0)
    goto fail;
  if (json_builder_append(&builder, ",\"sections\":[") != 0)
    goto fail;
  for (i = 0; i < object->section_count; ++i) {
    const M68kSection *section = &object->sections[i];
    size_t section_symbol_count = 0, section_fixup_count = 0, j;
    if (i != 0U && json_builder_append(&builder, ",") != 0)
      goto fail;
    for (j = 0; j < object->symbol_count; ++j) {
      const M68kSymbol *symbol = &object->symbols[j];
      if (symbol->defined && symbol->section_index == i) ++section_symbol_count;
    }
    for (j = 0; j < object->fixup_count; ++j) {
      if (object->fixups[j].section_index == i) ++section_fixup_count;
    }
    if (json_builder_append(&builder, "{\"name\":") != 0)
      goto fail;
    if (json_builder_append_json_string( &builder, section->name != NULL ? section->name : "") != 0)
      goto fail;
    if (json_builder_append(&builder, ",\"kind\":") != 0)
      goto fail;
    if (json_builder_append_json_string(&builder, section_kind_name(section->kind)) != 0)
      goto fail;
    if (json_builder_appendf( &builder, ",\"size\":%u,\"data_size\":%u,\"alloc_size\":%u,\"stored_size\":%u,"
        "\"debug_size\":%u,\"mem_type\":%u,\"mem_attrs\":%u,"
        "\"symbol_count\":%zu,\"fixup_count\":%zu", section->size, section->data_size, section->size,
        section->data_size, section->debug_size, (unsigned)section->platform_mem_type, section->platform_mem_attrs,
        section_symbol_count, section_fixup_count) != 0)
      goto fail;
    if (json_builder_append(&builder, ",\"data_hex\":\"") != 0)
      goto fail;
    if (section->data_size != 0U && json_builder_append_hex_bytes(&builder, section->data, section->data_size) != 0)
      goto fail;
    if (json_builder_append(&builder, "\"}") != 0)
      goto fail;
  }
  if (json_builder_append(&builder, "]}") != 0)
    goto fail;
  *out_json = builder.data;
  return 0;

fail:
  json_builder_free(&builder);
  return -1;
}

int platform_file_inspect_path_json(const char *backend_name, const char *path, char **out_json, char *error_buf,
    size_t error_buf_size) {
  char error[256];
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  if (backend == NULL || backend->read_file == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "unknown platform file backend");
    return -1;
  }
  m68k_object_init(&object);
  if (backend->read_file(path, &object, error, sizeof(error)) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, error);
    m68k_object_free(&object);
    return -1;
  }
  if (inspect_object_json(backend, &object, out_json) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, "failed building inspect json");
    m68k_object_free(&object);
    return -1;
  }
  m68k_object_free(&object);
  return 0;
}

int platform_file_inspect_buffer_json(const char *backend_name, const unsigned char *data, size_t size,
    char **out_json, char *error_buf, size_t error_buf_size) {
  char error[256];
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  if (backend == NULL || backend->read_buffer == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "unknown platform file backend");
    return -1;
  }
  m68k_object_init(&object);
  if (backend->read_buffer(data, size, &object, error, sizeof(error)) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, error);
    m68k_object_free(&object);
    return -1;
  }
  if (inspect_object_json(backend, &object, out_json) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, "failed building inspect json");
    m68k_object_free(&object);
    return -1;
  }
  m68k_object_free(&object);
  return 0;
}

int platform_file_roundtrip_buffer(const char *backend_name, const unsigned char *data, size_t size,
    unsigned char **out_data, size_t *out_size, char *error_buf, size_t error_buf_size) {
  char error[256];
  char temp_path[512];
  FILE *output = NULL;
  int64_t output_size_value;
  size_t output_size;
  unsigned char *buffer = NULL;
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  if (backend == NULL || backend->read_buffer == NULL || backend->write_file == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "unknown platform file backend");
    return -1;
  }
  if (make_temp_output_path(temp_path, sizeof(temp_path)) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, "failed creating temp path");
    return -1;
  }
  m68k_object_init(&object);
  if (backend->read_buffer(data, size, &object, error, sizeof(error)) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, error);
    m68k_object_free(&object);
    remove(temp_path);
    return -1;
  }
  if (backend->write_file(temp_path, &object, error, sizeof(error)) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, error);
    m68k_object_free(&object);
    remove(temp_path);
    return -1;
  }
  m68k_object_free(&object);
  output = fopen(temp_path, "rb");
  if (output == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "failed opening roundtrip output");
    remove(temp_path);
    return -1;
  }
  if (fseek(output, 0, SEEK_END) != 0) {
    fclose(output);
    remove(temp_path);
    m68k_platform_set_error(error_buf, error_buf_size, "failed sizing roundtrip output");
    return -1;
  }
  output_size_value = (int64_t)ftell(output);
  if (output_size_value < 0 || fseek(output, 0, SEEK_SET) != 0) {
    fclose(output);
    remove(temp_path);
    m68k_platform_set_error(error_buf, error_buf_size, "failed sizing roundtrip output");
    return -1;
  }
  output_size = (size_t)output_size_value;
  buffer = (unsigned char *)malloc(output_size != 0U ? output_size : 1U);
  if (buffer == NULL) {
    fclose(output);
    remove(temp_path);
    m68k_platform_set_error(error_buf, error_buf_size, "out of memory");
    return -1;
  }
  if (output_size != 0U && fread(buffer, 1, output_size, output) != output_size) {
    fclose(output);
    free(buffer);
    remove(temp_path);
    m68k_platform_set_error(error_buf, error_buf_size, "failed reading roundtrip output");
    return -1;
  }
  fclose(output);
  remove(temp_path);
  *out_data = buffer;
  *out_size = output_size;
  return 0;
}

void platform_file_free_text(char *text) { free(text); }
void platform_file_free_buffer(unsigned char *data) { free(data); }

typedef struct SectionDiscoveryMap {
  uint8_t *is_code_start;
  uint8_t *is_code_byte;
  size_t size;
} SectionDiscoveryMap;

typedef enum GeneratedLabelKind {
  GENERATED_LABEL_LOC = 0,
  GENERATED_LABEL_SUB = 1,
  GENERATED_LABEL_DAT = 2
} GeneratedLabelKind;

static void analysis_remove_label_range(M68kSectionAnalysisIR *section_analysis, uint32_t start_offset,
    uint32_t end_offset) {
  size_t read_index;
  size_t write_index = 0U;
  if (section_analysis == NULL || start_offset >= end_offset) return;
  for (read_index = 0; read_index < section_analysis->label_count; ++read_index) {
    uint32_t offset = section_analysis->label_offsets[read_index];
    if (offset >= start_offset && offset < end_offset) continue;
    section_analysis->label_offsets[write_index++] = offset;
  }
  section_analysis->label_count = write_index;
}

static void discovery_map_free(SectionDiscoveryMap *map) {
  if (map == NULL) return;
  free(map->is_code_start);
  free(map->is_code_byte);
  memset(map, 0, sizeof(*map));
}

static const char *generated_label_prefix(const M68kPresentationPolicy *presentation, GeneratedLabelKind kind) {
  if (presentation == NULL || presentation->prefer_generated_names == 0U) return "L";
  if (kind == GENERATED_LABEL_SUB && presentation->call_label_prefix[0] != '\0') return presentation->call_label_prefix;
  if (kind == GENERATED_LABEL_DAT && presentation->data_label_prefix[0] != '\0') return presentation->data_label_prefix;
  if (presentation->code_label_prefix[0] != '\0') return presentation->code_label_prefix;
  return "loc";
}

static void set_generated_name(char *out_name, size_t out_name_size, uint32_t target, GeneratedLabelKind kind,
    const M68kPresentationPolicy *presentation) {
  const char *prefix = generated_label_prefix(presentation, kind);
  if (out_name == NULL || out_name_size == 0U) return;
  snprintf(out_name, out_name_size, "%s_%04X", prefix, (unsigned)target);
}

static void update_generated_label_kind(GeneratedLabelKind *kinds, size_t size, uint32_t target,
    GeneratedLabelKind kind) {
  if (kinds == NULL || target >= size) return;
  if (kind > kinds[target]) kinds[target] = kind;
}

static void clear_code_range(SectionDiscoveryMap *map, uint32_t start_offset, uint32_t end_offset) {
  uint32_t offset;
  if (map == NULL || map->size == 0U || start_offset >= end_offset) return;
  if (start_offset > map->size) start_offset = (uint32_t)map->size;
  if (end_offset > map->size) end_offset = (uint32_t)map->size;
  for (offset = start_offset; offset < end_offset; ++offset) {
    if (map->is_code_start != NULL) map->is_code_start[offset] = 0U;
    if (map->is_code_byte != NULL) map->is_code_byte[offset] = 0U;
  }
}

static int mnemonic_equals(const M68kInstructionIR *instruction, const char *text) {
  return instruction != NULL && text != NULL && _stricmp(instruction->mnemonic, text) == 0;
}

static int mnemonic_starts_with(const M68kInstructionIR *instruction, const char *prefix) {
  size_t prefix_len;
  if (instruction == NULL || prefix == NULL) return 0;
  prefix_len = strlen(prefix);
  return _strnicmp(instruction->mnemonic, prefix, prefix_len) == 0;
}

static int instruction_branch_target(const M68kInstructionIR *instruction, uint32_t offset, uint32_t *out_target) {
  size_t operand_index;
  uint32_t base_offset;
  if (instruction == NULL || out_target == NULL) return 0;
  base_offset = offset + 2U;
  for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (operand->kind == M68K_ASM_OPERAND_LABEL) {
      *out_target = base_offset + (uint32_t)((int32_t)operand->value.value);
      return 1;
    }
  }
  return 0;
}

static int instruction_branch_target_from_bytes(const M68kInstructionIR *instruction, const uint8_t *data, size_t size,
    uint32_t offset, uint32_t *out_target) {
  if (instruction == NULL || data == NULL || out_target == NULL) return 0;
  if (instruction->byte_count == 2U && size >= 2U && mnemonic_starts_with(instruction, "b")) {
    *out_target = offset + 2U + (uint32_t)((int32_t)(int8_t)data[1]);
    return 1;
  }
  if (instruction_branch_target(instruction, offset, out_target)) return 1;
  return 0;
}

static int instruction_transfer_target(const M68kInstructionIR *instruction, const uint8_t *data, size_t size,
    uint32_t offset, uint32_t section_size, uint32_t *out_target) {
  size_t operand_index;
  uint32_t pc_base;
  if (instruction == NULL || out_target == NULL) return 0;
  if (instruction_branch_target_from_bytes(instruction, data, size, offset, out_target)) {
    if (*out_target < section_size) return 1;
    return 0;
  }
  pc_base = offset + (uint32_t)instruction->byte_count;
  for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_IND &&
        operand->kind != M68K_ASM_OPERAND_POSTINC && operand->kind != M68K_ASM_OPERAND_ABSL &&
        operand->kind != M68K_ASM_OPERAND_BF_EA)
      continue;
    if (operand->value.ea_mode == 7 && (operand->value.ea_reg == 2 || operand->value.ea_reg == 3)) {
      *out_target = (uint32_t)((int32_t)pc_base + (int32_t)operand->value.value);
      return *out_target < section_size;
    }
    if (operand->value.ea_mode == 7 && (operand->value.ea_reg == 0 || operand->value.ea_reg == 1)) {
      *out_target = operand->value.value;
      return *out_target < section_size;
    }
  }
  return 0;
}

static int instruction_is_unconditional_transfer(const M68kInstructionIR *instruction) {
  if (instruction == NULL) return 0;
  return mnemonic_equals(instruction, "bra") || mnemonic_equals(instruction, "jmp");
}

static int instruction_is_call_transfer(const M68kInstructionIR *instruction) {
  if (instruction == NULL) return 0;
  return mnemonic_equals(instruction, "bsr") || mnemonic_equals(instruction, "jsr");
}

static int instruction_stops_fallthrough(const M68kInstructionIR *instruction) {
  if (instruction == NULL) return 0;
  if (instruction_is_unconditional_transfer(instruction)) return 1;
  return mnemonic_equals(instruction, "rts") || mnemonic_equals(instruction, "rte") ||
    mnemonic_equals(instruction, "rtr") || mnemonic_equals(instruction, "rtd") ||
    mnemonic_equals(instruction, "stop") || mnemonic_equals(instruction, "illegal") ||
    mnemonic_starts_with(instruction, "trap");
}

static int is_conditional_transfer(const M68kInstructionIR *instruction) {
  if (instruction == NULL) return 0;
  if (instruction_is_call_transfer(instruction)) return 0;
  if (instruction_is_unconditional_transfer(instruction)) return 0;
  if (mnemonic_starts_with(instruction, "b")) return 1;
  return mnemonic_starts_with(instruction, "db");
}

static int instruction_control_transfer_target( const M68kInstructionIR *instruction, const uint8_t *data, size_t size,
    uint32_t offset, uint32_t section_size, uint32_t *out_target) {
  if (instruction == NULL) return 0;
  if (!instruction_is_call_transfer(instruction) && !instruction_is_unconditional_transfer(instruction) &&
      !is_conditional_transfer(instruction)) {
    return 0;
  }
  return instruction_transfer_target(instruction, data, size, offset, section_size, out_target);
}

static int prune_entry_skip_range(const M68kSection *section, const M68kAnalysisPolicy *analysis_policy,
    M68kAnalysisFindings *findings, M68kSectionAnalysisIR *section_analysis, SectionDiscoveryMap *map, char *out_error,
    size_t out_error_size) {
  M68kInstructionIR instruction;
  char error[128];
  uint32_t target;
  uint32_t start_offset;
  int decode_result;
  if (section == NULL || section_analysis == NULL || map == NULL || section->data_size < 2U) return 0;
  decode_result = decode_instruction_with_policy( section->data, section->data_size, 0U, analysis_policy, findings,
      &instruction, error, sizeof(error));
  if (decode_result < 0) {
    m68k_platform_set_error(out_error, out_error_size, error);
    return -1;
  }
  if (decode_result == 0) return 0;
  if (!instruction_is_unconditional_transfer(&instruction)) return 0;
  if (!instruction_transfer_target(&instruction, section->data, section->data_size, 0U, section->data_size,
    &target)) return 0;
  start_offset = (uint32_t)instruction.byte_count;
  if (target <= start_offset) return 0;
  clear_code_range(map, start_offset, target);
  analysis_remove_label_range(section_analysis, start_offset, target);
  return 0;
}

static int enrich_analysis_labels(const M68kSection *section, const M68kAnalysisPolicy *analysis_policy,
    M68kAnalysisFindings *findings, const SectionDiscoveryMap *map, M68kSectionAnalysisIR *section_analysis) {
  size_t scan_offset;
  if (section == NULL || map == NULL || section_analysis == NULL || map->is_code_start == NULL)
    return 0;
  for (scan_offset = 0; scan_offset < section->data_size; ++scan_offset) {
    M68kInstructionIR instruction;
    char error[128];
    uint32_t target;
    if (map->is_code_start[scan_offset] == 0U) continue;
    int decode_result = decode_instruction_with_policy( section->data + scan_offset, section->data_size - scan_offset,
      (uint32_t)scan_offset, analysis_policy, findings, &instruction, error, sizeof(error));
    if (decode_result < 0) return -1;
    if (decode_result == 0) continue;
    if (instruction_transfer_target(&instruction, section->data + scan_offset, section->data_size - scan_offset,
        (uint32_t)scan_offset, section->data_size, &target)) {
      if (m68k_ir_section_analysis_add_label(section_analysis, target) != 0) return -1;
    }
    for (size_t operand_index = 0; operand_index < instruction.operand_count; ++operand_index) {
      const M68kOperandIR *operand = &instruction.operands[operand_index];
      uint32_t abs_target;
      if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_IND &&
          operand->kind != M68K_ASM_OPERAND_POSTINC && operand->kind != M68K_ASM_OPERAND_ABSL &&
          operand->kind != M68K_ASM_OPERAND_BF_EA)
        continue;
      if (operand->value.ea_mode == 7U && (operand->value.ea_reg == 1U || (operand->value.ea_reg == 4U &&
          mnemonic_equals(&instruction, "movea") && operand_index == 0U))) {
        abs_target = operand->value.value;
        if (abs_target < section->data_size && m68k_ir_section_analysis_add_label(section_analysis, abs_target) != 0)
          return -1;
      }
    }
  }
  return 0;
}

static int prune_disconnected_blocks(M68kSectionAnalysisIR *section_analysis, SectionDiscoveryMap *discovery) {
  uint8_t *reachable_blocks = NULL;
  size_t *reachable_queue = NULL;
  M68kCfgBlockIR *new_blocks = NULL;
  M68kCfgEdgeIR *new_edges = NULL;
  M68kViolationIR *new_violations = NULL;
  size_t *block_remap = NULL;
  size_t new_block_count = 0U;
  size_t new_edge_count = 0U;
  size_t new_violation_count = 0U;
  size_t block_index;
  if (section_analysis == NULL || discovery == NULL) return -1;
  if (section_analysis->block_count == 0U) return 0;
  reachable_blocks = (uint8_t *)calloc(section_analysis->block_count, 1U);
  reachable_queue = (size_t *)malloc(section_analysis->block_count * sizeof(*reachable_queue));
  block_remap = (size_t *)malloc(section_analysis->block_count * sizeof(*block_remap));
  if (reachable_blocks == NULL || reachable_queue == NULL || block_remap == NULL)
    goto fail;
  for (block_index = 0; block_index < section_analysis->block_count; ++block_index)
    block_remap[block_index] = SIZE_MAX;
  reachable_blocks[0] = 1U;
  reachable_queue[0] = 0U;
  {
    size_t queue_read = 0U;
    size_t queue_write = 1U;
    while (queue_read < queue_write) {
      size_t current = reachable_queue[queue_read++];
      size_t scan_index;
      for (scan_index = section_analysis->blocks[current].edge_start;
           scan_index < section_analysis->blocks[current].edge_start + section_analysis->blocks[current].edge_count;
           ++scan_index) {
        size_t target = section_analysis->edges[scan_index].target_block_index;
        if (target == SIZE_MAX || target >= section_analysis->block_count || reachable_blocks[target] != 0U)
          continue;
        reachable_blocks[target] = 1U;
        reachable_queue[queue_write++] = target;
      }
    }
  }
  for (block_index = 0; block_index < section_analysis->block_count; ++block_index) {
    const M68kCfgBlockIR *block = &section_analysis->blocks[block_index];
    if (reachable_blocks[block_index] == 0U) {
      clear_code_range(discovery, block->start_offset, block->end_offset);
      analysis_remove_label_range(section_analysis, block->start_offset, block->end_offset);
      continue;
    }
    block_remap[block_index] = new_block_count++;
  }
  new_blocks = (M68kCfgBlockIR *)calloc( new_block_count != 0U ? new_block_count : 1U, sizeof(*new_blocks));
  new_edges = (M68kCfgEdgeIR *)calloc( section_analysis->edge_count != 0U ? section_analysis->edge_count : 1U,
    sizeof(*new_edges));
  new_violations = (M68kViolationIR *)calloc(section_analysis->violation_count != 0U
    ? section_analysis->violation_count : 1U, sizeof(*new_violations));
  if (new_blocks == NULL || new_edges == NULL || new_violations == NULL)
    goto fail;
  for (block_index = 0; block_index < section_analysis->block_count; ++block_index) {
    const M68kCfgBlockIR *old_block = &section_analysis->blocks[block_index];
    M68kCfgBlockIR *new_block;
    size_t edge_index;
    if (reachable_blocks[block_index] == 0U) continue;
    new_block = &new_blocks[block_remap[block_index]];
    *new_block = *old_block;
    new_block->edge_start = new_edge_count;
    new_block->edge_count = 0U;
    for (edge_index = old_block->edge_start; edge_index < old_block->edge_start + old_block->edge_count;
         ++edge_index) {
      M68kCfgEdgeIR edge = section_analysis->edges[edge_index];
      if (edge.target_block_index != SIZE_MAX) {
        if (edge.target_block_index >= section_analysis->block_count || reachable_blocks[edge.target_block_index] == 0U)
          continue;
        edge.target_block_index = block_remap[edge.target_block_index];
      }
      edge.source_block_index = block_remap[block_index];
      new_edges[new_edge_count++] = edge;
      new_block->edge_count += 1U;
    }
  }
  for (block_index = 0; block_index < section_analysis->violation_count; ++block_index) {
    M68kViolationIR violation = section_analysis->violations[block_index];
    size_t owner_index;
    int keep = 0;
    for (owner_index = 0; owner_index < section_analysis->block_count; ++owner_index) {
      const M68kCfgBlockIR *block = &section_analysis->blocks[owner_index];
      if (reachable_blocks[owner_index] == 0U) continue;
      if (violation.offset >= block->start_offset && violation.offset < block->end_offset) {
        keep = 1;
        break;
      }
    }
    if (keep) new_violations[new_violation_count++] = violation;
    else free(violation.message);
  }
  free(section_analysis->blocks);
  free(section_analysis->edges);
  free(section_analysis->violations);
  section_analysis->blocks = new_blocks;
  section_analysis->block_count = new_block_count;
  section_analysis->block_capacity = new_block_count;
  section_analysis->edges = new_edges;
  section_analysis->edge_count = new_edge_count;
  section_analysis->edge_capacity = new_edge_count;
  section_analysis->violations = new_violations;
  section_analysis->violation_count = new_violation_count;
  section_analysis->violation_capacity = new_violation_count;
  free(reachable_blocks);
  free(reachable_queue);
  free(block_remap);
  return 0;

fail:
  free(reachable_blocks);
  free(reachable_queue);
  free(block_remap);
  free(new_blocks);
  free(new_edges);
  free(new_violations);
  return -1;
}

static int recompute_section_findings(const M68kSection *section, const M68kSectionAnalysisIR *section_analysis,
    const M68kAnalysisPolicy *analysis_policy, M68kAnalysisFindings *out_findings) {
  size_t block_index;
  M68kAnalysisFindings findings;
  m68k_analysis_findings_init(&findings);
  if (section == NULL || section_analysis == NULL || out_findings == NULL) return -1;
  if (section->kind != M68K_SECTION_CODE) {
    *out_findings = findings;
    return 0;
  }
  for (block_index = 0; block_index < section_analysis->block_count; ++block_index) {
    const M68kCfgBlockIR *block = &section_analysis->blocks[block_index];
    uint32_t offset = block->start_offset;
    while (offset < block->end_offset && offset < section->data_size) {
      M68kInstructionIR instruction;
      char error[128];
      int decode_result = decode_instruction_with_policy( section->data + offset, section->data_size - offset, offset,
          analysis_policy, &findings, &instruction, error, sizeof(error));
      if (decode_result <= 0 || instruction.byte_count == 0U || offset + instruction.byte_count > block->end_offset)
        break;
      offset += (uint32_t)instruction.byte_count;
    }
  }
  *out_findings = findings;
  return 0;
}

static int rebuild_code_map_from_blocks(const M68kSection *section, M68kSectionAnalysisIR *section_analysis,
    const M68kAnalysisPolicy *analysis_policy) {
  size_t block_index;
  if (section == NULL || section_analysis == NULL) return -1;
  if (section_analysis->certain_code_start == NULL || section_analysis->certain_code_byte == NULL) return 0;
  memset(section_analysis->certain_code_start, 0, section_analysis->certain_code_size);
  memset(section_analysis->certain_code_byte, 0, section_analysis->certain_code_size);
  for (block_index = 0; block_index < section_analysis->block_count; ++block_index) {
    const M68kCfgBlockIR *block = &section_analysis->blocks[block_index];
    uint32_t offset = block->start_offset;
    while (offset < block->end_offset && offset < section_analysis->certain_code_size) {
      M68kInstructionIR instruction;
      char error[128];
      int decode_result = decode_instruction_with_policy( section->data + offset, section->data_size - offset, offset,
          analysis_policy, NULL, &instruction, error, sizeof(error));
      size_t byte_index;
      if (decode_result <= 0 || instruction.byte_count == 0U || offset + instruction.byte_count > block->end_offset)
        break;
      section_analysis->certain_code_start[offset] = 1U;
      for (byte_index = 0; byte_index < instruction.byte_count &&
          offset + byte_index < section_analysis->certain_code_size; ++byte_index) {
        section_analysis->certain_code_byte[offset + byte_index] = 1U;
      }
      offset += (uint32_t)instruction.byte_count;
    }
  }
  return 0;
}

static void remove_section_violations_by_kind(M68kSectionAnalysisIR *section_analysis, uint8_t kind) {
  size_t read_index;
  size_t write_index = 0U;
  if (section_analysis == NULL) return;
  for (read_index = 0; read_index < section_analysis->violation_count; ++read_index) {
    M68kViolationIR violation = section_analysis->violations[read_index];
    if (violation.kind == kind) {
      free(violation.message);
      continue;
    }
    section_analysis->violations[write_index++] = violation;
  }
  section_analysis->violation_count = write_index;
}

static int rebuild_cpu_violations(const M68kSection *section, M68kSectionAnalysisIR *section_analysis,
    const M68kAnalysisPolicy *analysis_policy) {
  size_t block_index;
  if (section == NULL || section_analysis == NULL || section_analysis->certain_code_start == NULL)
    return 0;
  remove_section_violations_by_kind(section_analysis, M68K_VIOLATION_CPU_POLICY);
  for (block_index = 0; block_index < section_analysis->block_count; ++block_index) {
    const M68kCfgBlockIR *block = &section_analysis->blocks[block_index];
    uint32_t offset = block->start_offset;
    while (offset < block->end_offset && offset < section->data_size) {
      M68kInstructionIR instruction;
      char error[128];
      int decode_result = decode_instruction_with_policy( section->data + offset, section->data_size - offset, offset,
          analysis_policy, NULL, &instruction, error, sizeof(error));
      if (decode_result <= 0 || instruction.byte_count == 0U ||
          offset + instruction.byte_count > block->end_offset) {
        break;
      }
      if (add_cpu_violation(section_analysis, offset, &instruction, analysis_policy) != 0)
        return -1;
      offset += (uint32_t)instruction.byte_count;
    }
  }
  return 0;
}

static int
rebuild_decode_fail_violations(const M68kSection *section, M68kSectionAnalysisIR *section_analysis,
    const M68kAnalysisPolicy *analysis_policy) {
  size_t block_index;
  if (section == NULL || section_analysis == NULL) return -1;
  remove_section_violations_by_kind(section_analysis, M68K_VIOLATION_DECODE_FAILED_REACHABLE);
  for (block_index = 0; block_index < section_analysis->block_count; ++block_index) {
    const M68kCfgBlockIR *block = &section_analysis->blocks[block_index];
    uint32_t offset = block->start_offset;
    while (offset < block->end_offset && offset < section->data_size) {
      M68kInstructionIR instruction;
      char error[128];
      int decode_result = decode_instruction_with_policy( section->data + offset, section->data_size - offset, offset,
          analysis_policy, NULL, &instruction, error, sizeof(error));
      if (decode_result <= 0 || instruction.byte_count == 0U || offset + instruction.byte_count > block->end_offset) {
        if (m68k_ir_section_analysis_add_violation( section_analysis, offset, M68K_VIOLATION_DECODE_FAILED_REACHABLE,
            "decode failed in reachable code; region emitted as data") != 0) {
          return -1;
        }
        break;
      }
      offset += (uint32_t)instruction.byte_count;
    }
  }
  return 0;
}

static int build_generated_label_kinds(const M68kSection *section, const M68kAnalysisPolicy *analysis_policy,
    M68kAnalysisFindings *findings, const M68kSectionAnalysisIR *section_analysis, GeneratedLabelKind *label_kinds,
    uint8_t *label_flags) {
  size_t offset;
  if (section == NULL || section_analysis == NULL || label_kinds == NULL ||
      section_analysis->certain_code_start == NULL)
    return 0;
  for (offset = 0; offset < section->data_size; ++offset) {
    M68kInstructionIR instruction;
    char error[128];
    size_t operand_index;
    if (section_analysis->certain_code_start[offset] == 0U) continue;
    int decode_result = decode_instruction_with_policy( section->data + offset, section->data_size - offset,
        (uint32_t)offset, analysis_policy, findings, &instruction, error, sizeof(error));
    if (decode_result < 0) return -1;
    if (decode_result == 0) continue;
    for (operand_index = 0; operand_index < instruction.operand_count; ++operand_index) {
      const M68kOperandIR *operand = &instruction.operands[operand_index];
      if (operand->kind == M68K_ASM_OPERAND_LABEL) {
        uint32_t target = (uint32_t)offset + 2U + (uint32_t)((int32_t)operand->value.value);
        if (target < section->data_size) {
          update_generated_label_kind(label_kinds, section->data_size, target, GENERATED_LABEL_LOC);
          if (label_flags != NULL) label_flags[target] = 1U;
        }
        continue;
      }
      if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_IND &&
          operand->kind != M68K_ASM_OPERAND_POSTINC && operand->kind != M68K_ASM_OPERAND_ABSL &&
          operand->kind != M68K_ASM_OPERAND_BF_EA)
        continue;
      if (operand->value.ea_mode == 7U && operand->value.ea_reg == 1U) {
        uint32_t target = operand->value.value;
        GeneratedLabelKind kind = GENERATED_LABEL_DAT;
        if (target >= section->data_size) continue;
        if (instruction_is_call_transfer(&instruction) || instruction_is_unconditional_transfer(&instruction))
          kind = GENERATED_LABEL_SUB;
        update_generated_label_kind(label_kinds, section->data_size, target, kind);
        if (label_flags != NULL) label_flags[target] = 1U;
      }
    }
  }
  return 0;
}

static uint32_t find_enclosing_code_start(const M68kSectionAnalysisIR *section_analysis, uint32_t offset);

static int scan_interior_pc_relative_refs(const M68kSection *section, const M68kAnalysisPolicy *analysis_policy,
    M68kAnalysisFindings *findings, M68kSectionAnalysisIR *section_analysis, GeneratedLabelKind *label_kinds,
    uint8_t *label_flags) {
  size_t offset;
  if (section == NULL || section_analysis == NULL || label_kinds == NULL || label_flags == NULL ||
      section_analysis->certain_code_start == NULL)
    return 0;
  for (offset = 0; offset < section->data_size; ++offset) {
    M68kInstructionIR instruction;
    char error[128];
    size_t operand_index;
    if (section_analysis->certain_code_start[offset] == 0U) continue;
    if (decode_instruction_with_policy(section->data + offset, section->data_size - offset, (uint32_t)offset,
          analysis_policy, findings, &instruction, error, sizeof(error)) <= 0)
      continue;
    for (operand_index = 0; operand_index < instruction.operand_count; ++operand_index) {
      const M68kOperandIR *operand = &instruction.operands[operand_index];
      uint32_t target;
      uint32_t base;
      char message[128];
      if (!(operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_IND ||
            operand->kind == M68K_ASM_OPERAND_POSTINC || operand->kind == M68K_ASM_OPERAND_ABSL ||
            operand->kind == M68K_ASM_OPERAND_BF_EA))
        continue;
      if (!(operand->value.ea_mode == 7U && (operand->value.ea_reg == 2U || operand->value.ea_reg == 3U)))
        continue;
      target = (uint32_t)((int32_t)offset + (int32_t)instruction.byte_count + (int32_t)operand->value.value);
      base = find_enclosing_code_start(section_analysis, target);
      if (base == UINT32_MAX || base == target) continue;
      label_flags[base] = 1U;
      snprintf(message, sizeof(message), "invalid overlap: pc-relative reference targets +%u into instruction at $%04X",
        (unsigned)(target - base), (unsigned)base);
      if (m68k_ir_section_analysis_add_violation(section_analysis, (uint32_t)offset,
            M68K_VIOLATION_INVALID_INTERIOR_REFERENCE, message) != 0)
        return -1;
      snprintf(message, sizeof(message),
        "invalid overlap: instruction bytes at +%u are referenced by reachable pc-relative operand",
        (unsigned)(target - base));
      if (m68k_ir_section_analysis_add_violation(section_analysis, base, M68K_VIOLATION_INVALID_INTERIOR_REFERENCE,
            message) != 0)
        return -1;
    }
  }
  return 0;
}

static int queue_push(uint32_t **queue, size_t *queue_count, size_t *queue_capacity, uint32_t value) {
  if (*queue_count == *queue_capacity) {
    uint32_t *grown = (uint32_t *)realloc(*queue, *queue_capacity * 2U * sizeof(**queue));
    if (grown == NULL) return -1;
    *queue = grown;
    *queue_capacity *= 2U;
  }
  (*queue)[(*queue_count)++] = value;
  return 0;
}

static int build_section_analysis(const M68kObject *object, size_t section_index, const M68kSection *section,
    const M68kAnalysisPolicy *analysis_policy, M68kAnalysisFindings *findings, M68kSectionAnalysisIR *out_analysis,
    char *out_error, size_t out_error_size) {
  SectionDiscoveryMap discovery = {0};
  uint32_t *queue = NULL;
  size_t queue_count = 0, queue_capacity = 0, fixup_index, pop_index = 0;
  uint8_t *block_starts = NULL;
  size_t scan_offset, block_index;
  if (out_analysis == NULL) return -1;
  m68k_ir_section_analysis_init(out_analysis);
  out_analysis->section_index = section_index;
  out_analysis->section_kind = section->kind;
  out_analysis->section_size = section->size;
  out_analysis->section_name = _strdup( (section->name != NULL && section->name[0] != '\0') ? section->name : "section");
  if (out_analysis->section_name == NULL) return -1;
  if (section->kind != M68K_SECTION_CODE || section->data_size == 0U) {
    out_analysis->certain_code_size = section->data_size;
    return 0;
  }
  discovery.is_code_start = (uint8_t *)calloc(section->data_size != 0U ? section->data_size : 1U, 1U);
  discovery.is_code_byte = (uint8_t *)calloc(section->data_size != 0U ? section->data_size : 1U, 1U);
  if (discovery.is_code_start == NULL || discovery.is_code_byte == NULL) {
    discovery_map_free(&discovery);
    goto fail;
  }
  discovery.size = section->data_size;
  if (m68k_ir_section_analysis_add_label(out_analysis, 0U) != 0)
    goto fail;
  queue_capacity = 32U;
  queue = (uint32_t *)malloc(queue_capacity * sizeof(*queue));
  if (queue == NULL)
    goto fail;
  queue[queue_count++] = 0U;
  for (fixup_index = 0; fixup_index < object->fixup_count; ++fixup_index) {
    const M68kFixup *fixup = &object->fixups[fixup_index];
    if (fixup->section_index != section_index)
      continue;
    if (!fixup->has_target_section || fixup->target_section_index != section_index)
      continue;
    if (fixup->addend >= 0 && (uint32_t)fixup->addend < section->data_size) {
      uint32_t target = (uint32_t)fixup->addend;
      if (m68k_ir_section_analysis_add_label(out_analysis, target) != 0)
        goto fail;
      if (object->platform_file_kind == M68K_PLATFORM_FILE_OBJECT) {
        if (queue_push(&queue, &queue_count, &queue_capacity, target) != 0)
          goto fail;
      }
    }
  }
  while (pop_index < queue_count) {
    uint32_t work_offset = queue[pop_index++];
    uint32_t segment_start = work_offset;
    uint32_t segment_end = work_offset;
    int segment_needs_demotion = 0;
    int segment_terminated_cleanly = 0;
    while (work_offset < section->data_size) {
      M68kInstructionIR instruction;
      char error[128];
      uint32_t target = 0;
      size_t index;
      if (discovery.is_code_start[work_offset]) break;
      int decode_result = decode_instruction_with_policy( section->data + work_offset, section->data_size - work_offset,
          work_offset, analysis_policy, findings, &instruction, error, sizeof(error));
      if (decode_result < 0) {
        if (out_error != NULL && out_error_size != 0U) snprintf(out_error, out_error_size, "%s", error);
        goto fail;
      }
      if (decode_result == 0 || instruction.byte_count == 0U ||
          work_offset + instruction.byte_count > section->data_size) {
        if (m68k_ir_section_analysis_add_violation( out_analysis, work_offset, M68K_VIOLATION_DECODE_FAILED_REACHABLE,
            "decode failed in reachable code; region emitted as data") != 0)
          goto fail;
        segment_end = work_offset;
        segment_needs_demotion = 1;
        break;
      }
      if (add_cpu_violation(out_analysis, work_offset, &instruction, analysis_policy) != 0)
        goto fail;
      discovery.is_code_start[work_offset] = 1U;
      for (index = 0; index < instruction.byte_count; ++index) discovery.is_code_byte[work_offset + index] = 1U;
      segment_end = work_offset + (uint32_t)instruction.byte_count;
      if (instruction_control_transfer_target( &instruction, section->data + work_offset,
          section->data_size - work_offset, work_offset, section->data_size, &target)) {
        if (m68k_ir_section_analysis_add_label(out_analysis, target) != 0)
          goto fail;
        if (!discovery.is_code_start[target]) {
          if (queue_push(&queue, &queue_count, &queue_capacity, target) != 0)
            goto fail;
        }
      }
      work_offset += (uint32_t)instruction.byte_count;
      if (instruction_stops_fallthrough(&instruction)) {
        segment_terminated_cleanly = 1;
        break;
      }
      if (instruction_is_call_transfer(&instruction) && work_offset < section->data_size &&
          m68k_ir_section_analysis_add_label(out_analysis, work_offset) != 0) {
        goto fail;
      }
    }
    if (!segment_needs_demotion && !segment_terminated_cleanly && work_offset >= section->data_size &&
        segment_end > segment_start) {
      if (m68k_ir_section_analysis_add_violation( out_analysis, segment_start, M68K_VIOLATION_DECODE_FAILED_REACHABLE,
          "unterminated reachable region demoted to data") != 0)
        goto fail;
      segment_needs_demotion = 1;
    }
    if (segment_needs_demotion && segment_end > segment_start) {
      clear_code_range(&discovery, segment_start, segment_end);
      analysis_remove_label_range(out_analysis, segment_start, segment_end);
      if (m68k_ir_section_analysis_add_label(out_analysis, segment_start) != 0)
        goto fail;
    }
  }
  if (prune_entry_skip_range(section, analysis_policy, findings, out_analysis, &discovery, out_error,
      out_error_size) != 0)
    goto fail;
  if (enrich_analysis_labels(section, analysis_policy, findings, &discovery, out_analysis) != 0)
    goto fail;
  if (m68k_ir_section_analysis_set_code_map( out_analysis, discovery.is_code_start, discovery.is_code_byte, discovery.size) != 0)
    goto fail;
  block_starts = (uint8_t *)calloc(section->data_size, 1U);
  if (block_starts == NULL)
    goto fail;
  block_starts[0] = 1U;
  for (scan_offset = 0; scan_offset < section->data_size; ++scan_offset) {
    M68kInstructionIR instruction;
    char error[128];
    uint32_t target;
    uint32_t next_offset;
    if (discovery.is_code_start[scan_offset] == 0U)
      continue;
    int decode_result = decode_instruction_with_policy( section->data + scan_offset, section->data_size - scan_offset,
        (uint32_t)scan_offset, analysis_policy, findings, &instruction, error, sizeof(error));
    if (decode_result < 0) {
      if (out_error != NULL && out_error_size != 0U) snprintf(out_error, out_error_size, "%s", error);
      goto fail;
    }
    if (decode_result == 0) {
      if (m68k_ir_section_analysis_add_violation( out_analysis, (uint32_t)scan_offset,
          M68K_VIOLATION_DECODE_FAILED_REACHABLE,
          "decode failed in reachable code; region emitted as data") != 0)
        goto fail;
      continue;
    }
    if (add_cpu_violation(out_analysis, (uint32_t)scan_offset, &instruction, analysis_policy) != 0)
      goto fail;
    next_offset = (uint32_t)scan_offset + (uint32_t)instruction.byte_count;
    if (instruction_control_transfer_target( &instruction, section->data + scan_offset,
        section->data_size - scan_offset, (uint32_t)scan_offset, section->data_size, &target)) {
      block_starts[target] = 1U;
      if ((instruction_is_call_transfer(&instruction) || is_conditional_transfer(&instruction)) &&
          next_offset < section->data_size) {
        block_starts[next_offset] = 1U;
      }
    } else if (instruction_is_call_transfer(&instruction) && next_offset < section->data_size) {
      block_starts[next_offset] = 1U;
    }
  }
  for (scan_offset = 0; scan_offset < section->data_size; ++scan_offset) {
    M68kCfgBlockIR block;
    uint32_t cursor;
    if (discovery.is_code_start[scan_offset] == 0U || block_starts[scan_offset] == 0U)
      continue;
    memset(&block, 0, sizeof(block));
    block.start_offset = (uint32_t)scan_offset;
    block.certainty = M68K_CODE_CERTAIN;
    block.edge_start = out_analysis->edge_count;
    cursor = (uint32_t)scan_offset;
    for (;;) {
      M68kInstructionIR instruction;
      char error[128];
      uint32_t next_offset;
      int decode_result = decode_instruction_with_policy( section->data + cursor, section->data_size - cursor, cursor,
          analysis_policy, findings, &instruction, error, sizeof(error));
      if (decode_result < 0) {
        if (out_error != NULL && out_error_size != 0U) snprintf(out_error, out_error_size, "%s", error);
        goto fail;
      }
      if (decode_result == 0) {
        if (m68k_ir_section_analysis_add_violation( out_analysis, cursor, M68K_VIOLATION_DECODE_FAILED_REACHABLE,
            "decode failed in reachable code; region emitted as data") != 0)
          goto fail;
        break;
      }
      if (add_cpu_violation(out_analysis, cursor, &instruction, analysis_policy) != 0)
        goto fail;
      next_offset = cursor + (uint32_t)instruction.byte_count;
      if (instruction_control_transfer_target( &instruction, section->data + cursor, section->data_size - cursor,
              cursor, section->data_size, &block.end_offset)) {
        M68kCfgEdgeIR edge;
        memset(&edge, 0, sizeof(edge));
        edge.source_block_index = out_analysis->block_count;
        edge.target_block_index = SIZE_MAX;
        edge.source_offset = cursor;
        edge.target_offset = block.end_offset;
        edge.kind = instruction_is_call_transfer(&instruction)
          ? M68K_CFG_EDGE_CALL : instruction_is_unconditional_transfer(&instruction)
          ? M68K_CFG_EDGE_JUMP : M68K_CFG_EDGE_BRANCH;
        if (m68k_ir_section_analysis_append_edge(out_analysis, &edge) != 0)
          goto fail;
        if ((instruction_is_call_transfer(&instruction) || is_conditional_transfer(&instruction)) &&
            next_offset < section->data_size) {
          memset(&edge, 0, sizeof(edge));
          edge.source_block_index = out_analysis->block_count;
          edge.target_block_index = SIZE_MAX;
          edge.source_offset = cursor;
          edge.target_offset = next_offset;
          edge.kind = M68K_CFG_EDGE_FALLTHROUGH;
          if (m68k_ir_section_analysis_append_edge(out_analysis, &edge) != 0)
            goto fail;
        }
        cursor = next_offset;
        break;
      }
      if (instruction_stops_fallthrough(&instruction)) {
        M68kCfgEdgeIR edge;
        memset(&edge, 0, sizeof(edge));
        edge.source_block_index = out_analysis->block_count;
        edge.target_block_index = SIZE_MAX;
        edge.source_offset = cursor;
        edge.target_offset = UINT32_MAX;
        edge.kind = M68K_CFG_EDGE_RETURN;
        if (m68k_ir_section_analysis_append_edge(out_analysis, &edge) != 0)
          goto fail;
        cursor = next_offset;
        break;
      }
      if (next_offset >= section->data_size || discovery.is_code_start[next_offset] == 0U ||
          block_starts[next_offset] != 0U) {
        if (next_offset < section->data_size && discovery.is_code_start[next_offset] != 0U &&
            block_starts[next_offset] != 0U) {
          M68kCfgEdgeIR edge;
          memset(&edge, 0, sizeof(edge));
          edge.source_block_index = out_analysis->block_count;
          edge.target_block_index = SIZE_MAX;
          edge.source_offset = cursor;
          edge.target_offset = next_offset;
          edge.kind = M68K_CFG_EDGE_FALLTHROUGH;
          if (m68k_ir_section_analysis_append_edge(out_analysis, &edge) != 0)
            goto fail;
        }
        cursor = next_offset;
        break;
      }
      cursor = next_offset;
    }
    block.end_offset = cursor;
    block.edge_count = out_analysis->edge_count - block.edge_start;
    if (m68k_ir_section_analysis_append_block(out_analysis, &block) != 0)
      goto fail;
  }
  for (block_index = 0; block_index < out_analysis->block_count; ++block_index) {
    size_t edge_index;
    for (edge_index = out_analysis->blocks[block_index].edge_start;
        edge_index < out_analysis->blocks[block_index].edge_start +
        out_analysis->blocks[block_index].edge_count; ++edge_index) {
      size_t target_index;
      if (out_analysis->edges[edge_index].target_offset == UINT32_MAX) continue;
      for (target_index = 0; target_index < out_analysis->block_count; ++target_index) {
        if (out_analysis->blocks[target_index].start_offset == out_analysis->edges[edge_index].target_offset) {
          out_analysis->edges[edge_index].target_block_index = target_index;
          break;
        }
      }
    }
  }
  if (object->platform_file_kind == M68K_PLATFORM_FILE_EXECUTABLE) {
    if (prune_disconnected_blocks(out_analysis, &discovery) != 0)
      goto fail;
    if (m68k_ir_section_analysis_set_code_map( out_analysis, discovery.is_code_start, discovery.is_code_byte, discovery.size) != 0)
      goto fail;
    if (rebuild_code_map_from_blocks(section, out_analysis, analysis_policy) !=
        0)
      goto fail;
  }
  free(block_starts);
  free(queue);
  discovery_map_free(&discovery);
  return 0;

fail:
  free(block_starts);
  free(queue);
  discovery_map_free(&discovery);
  m68k_ir_section_analysis_free(out_analysis);
  return -1;
}

static int analysis_has_label(const M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  size_t index;
  if (section_analysis == NULL) return 0;
  for (index = 0; index < section_analysis->label_count; ++index)
    if (section_analysis->label_offsets[index] == offset) return 1;
  return 0;
}

static int section_has_any_label(const M68kSectionAnalysisIR *section_analysis, const uint8_t *generated_label_flags,
    size_t generated_label_count, uint32_t offset) {
  if (analysis_has_label(section_analysis, offset)) return 1;
  return generated_label_flags != NULL && offset < generated_label_count && generated_label_flags[offset] != 0U;
}

static uint32_t find_enclosing_code_start(const M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  uint32_t cursor;
  if (section_analysis == NULL || section_analysis->certain_code_start == NULL || section_analysis->certain_code_byte == NULL ||
      offset >= section_analysis->certain_code_size || section_analysis->certain_code_byte[offset] == 0U)
    return UINT32_MAX;
  cursor = offset;
  while (cursor > 0U && section_analysis->certain_code_start[cursor] == 0U &&
      section_analysis->certain_code_byte[cursor - 1U] != 0U)
    --cursor;
  return section_analysis->certain_code_start[cursor] != 0U ? cursor : UINT32_MAX;
}

static int append_statement_violation_comment(char *buf, size_t buf_size, const char *message) {
  size_t used;
  if (buf == NULL || buf_size == 0U || message == NULL || message[0] == '\0') return 0;
  used = strlen(buf);
  if (used != 0U) {
    if (used + 3U >= buf_size) return 0;
    snprintf(buf + used, buf_size - used, " | ");
    used = strlen(buf);
  }
  if (used + strlen(message) + 1U > buf_size) return 0;
  snprintf(buf + used, buf_size - used, "%s", message);
  return 1;
}

static void collect_section_violation_comments(const M68kSectionAnalysisIR *section_analysis, uint32_t offset, char *buf,
    size_t buf_size) {
  size_t index;
  if (buf == NULL || buf_size == 0U) return;
  buf[0] = '\0';
  if (section_analysis == NULL) return;
  for (index = 0; index < section_analysis->violation_count; ++index) {
    const M68kViolationIR *violation = &section_analysis->violations[index];
    if (violation->offset != offset || violation->message == NULL || violation->message[0] == '\0') continue;
    append_statement_violation_comment(buf, buf_size, violation->message);
  }
}

static GeneratedLabelKind effective_label_kind(uint32_t offset, GeneratedLabelKind kind,
    const M68kSectionAnalysisIR *section_analysis) {
  if (section_analysis != NULL && section_analysis->certain_code_start != NULL &&
      offset < section_analysis->certain_code_size && section_analysis->certain_code_start[offset] != 0U &&
      kind != GENERATED_LABEL_SUB) {
    return GENERATED_LABEL_LOC;
  }
  return kind;
}

static int append_label_statement(M68kSectionIR *section_ir, uint32_t offset, const GeneratedLabelKind *label_kinds,
    size_t label_kind_count, const M68kSectionAnalysisIR *section_analysis,
    const M68kPresentationPolicy *presentation) {
  M68kStatementIR statement;
  char label_name[32];
  GeneratedLabelKind kind = GENERATED_LABEL_LOC;
  m68k_ir_statement_init(&statement);
  statement.kind = M68K_STATEMENT_LABEL;
  statement.offset = offset;
  if (label_kinds != NULL && offset < label_kind_count) kind = label_kinds[offset];
  kind = effective_label_kind(offset, kind, section_analysis);
  set_generated_name(label_name, sizeof(label_name), offset, kind, presentation);
  statement.label_name = label_name;
  statement.label_is_generated = 1U;
  return m68k_ir_section_append_statement(section_ir, &statement);
}

static int append_instruction_statement(M68kSectionIR *section_ir, uint32_t offset,
    const M68kInstructionIR *instruction, const char *comment) {
  M68kStatementIR statement;
  m68k_ir_statement_init(&statement);
  statement.kind = M68K_STATEMENT_INSTRUCTION;
  statement.offset = offset;
  statement.u.instruction = *instruction;
  statement.comment = (char *)comment;
  return m68k_ir_section_append_statement(section_ir, &statement);
}

static int append_data_statement(M68kSectionIR *section_ir, uint32_t offset, const uint8_t *data, size_t size,
    const char *comment) {
  M68kStatementIR statement;
  m68k_ir_statement_init(&statement);
  statement.kind = M68K_STATEMENT_DATA;
  statement.offset = offset;
  statement.u.data.kind = M68K_DATA_ITEM_BYTES;
  statement.u.data.data = (uint8_t *)data;
  statement.u.data.size = size;
  statement.comment = (char *)comment;
  return m68k_ir_section_append_statement(section_ir, &statement);
}

static int append_typed_data_statement(M68kSectionIR *section_ir, uint32_t offset, uint8_t kind,
    const uint8_t *data, size_t size, const char *comment) {
  M68kStatementIR statement;
  m68k_ir_statement_init(&statement);
  statement.kind = M68K_STATEMENT_DATA;
  statement.offset = offset;
  statement.u.data.kind = kind;
  statement.u.data.data = (uint8_t *)data;
  statement.u.data.size = size;
  statement.comment = (char *)comment;
  return m68k_ir_section_append_statement(section_ir, &statement);
}

static int append_expr_data_statement(M68kSectionIR *section_ir, uint32_t offset, uint8_t kind,
    const uint8_t *data, size_t size, const char *expr_text, const char *comment) {
  M68kStatementIR statement;
  m68k_ir_statement_init(&statement);
  statement.kind = M68K_STATEMENT_DATA;
  statement.offset = offset;
  statement.u.data.kind = kind;
  statement.u.data.data = (uint8_t *)data;
  statement.u.data.size = size;
  statement.u.data.expr_text = (char *)expr_text;
  statement.comment = (char *)comment;
  return m68k_ir_section_append_statement(section_ir, &statement);
}

static int is_printable_ascii(uint8_t value) {
  return value >= 32U && value <= 126U;
}

static size_t detect_string_run(const uint8_t *data, size_t size) {
  size_t index = 0U;
  while (index < size && is_printable_ascii(data[index])) ++index;
  if (index >= 4U) {
    if (index < size && data[index] == 0U) return index + 1U;
    return index;
  }
  return 0U;
}

static int chunk_has_non_printable(const uint8_t *data, size_t size) {
  size_t index;
  for (index = 0; index < size; ++index) if (!is_printable_ascii(data[index])) return 1;
  return 0;
}

static size_t compute_data_span_chunk(const M68kSectionAnalysisIR *section_analysis,
    const uint8_t *generated_label_flags, size_t generated_label_count, size_t offset, size_t section_size) {
  size_t chunk = 0U;
  while (offset + chunk < section_size && ((section_analysis->certain_code_start == NULL ||
      section_analysis->certain_code_start[offset + chunk] == 0U) && chunk == 0U ||
      !section_has_any_label(section_analysis, generated_label_flags, generated_label_count,
      (uint32_t)(offset + chunk)))) {
    ++chunk;
  }
  return chunk != 0U ? chunk : 1U;
}

static const M68kFixup *find_section_fixup_at_offset(const M68kObject *object, size_t section_index, uint32_t offset,
    M68kFixupWidth width) {
  size_t fixup_index;
  if (object == NULL) return NULL;
  for (fixup_index = 0; fixup_index < object->fixup_count; ++fixup_index) {
    const M68kFixup *fixup = &object->fixups[fixup_index];
    if (fixup->section_index == section_index && fixup->offset == offset && fixup->kind == M68K_FIXUP_ABS &&
        fixup->width == width && fixup->has_target_section) {
      return fixup;
    }
  }
  return NULL;
}

static int find_next_section_fixup_offset(const M68kObject *object, size_t section_index, uint32_t start_offset,
    M68kFixupWidth width, uint32_t *out_offset) {
  size_t fixup_index;
  int found = 0;
  uint32_t best = 0U;
  if (out_offset == NULL || object == NULL) return 0;
  for (fixup_index = 0; fixup_index < object->fixup_count; ++fixup_index) {
    const M68kFixup *fixup = &object->fixups[fixup_index];
    if (fixup->section_index != section_index || fixup->kind != M68K_FIXUP_ABS || fixup->width != width) continue;
    if (fixup->offset < start_offset) continue;
    if (!found || fixup->offset < best) {
      best = fixup->offset;
      found = 1;
    }
  }
  if (found) *out_offset = best;
  return found;
}

static uint32_t read_be_u32_local(const uint8_t *data) {
  return ((uint32_t)data[0] << 24) | ((uint32_t)data[1] << 16) | ((uint32_t)data[2] << 8) | (uint32_t)data[3];
}

static void mark_data_fixup_labels(const M68kObject *object, const M68kSectionAnalysisIR *section_analysis,
    GeneratedLabelKind *label_kinds, uint8_t *generated_label_flags) {
  size_t fixup_index;
  if (object == NULL || section_analysis == NULL || label_kinds == NULL || generated_label_flags == NULL) return;
  for (fixup_index = 0; fixup_index < object->fixup_count; ++fixup_index) {
    const M68kFixup *fixup = &object->fixups[fixup_index];
    const M68kSection *section;
    uint32_t target;
    if (fixup->section_index != section_analysis->section_index ||
        fixup->kind != M68K_FIXUP_ABS || fixup->width != M68K_FIXUP_WIDTH_32 || !fixup->has_target_section ||
        fixup->target_section_index != section_analysis->section_index)
      continue;
    section = &object->sections[section_analysis->section_index];
    if (fixup->offset + 4U > section->data_size) continue;
    target = read_be_u32_local(section->data + fixup->offset);
    if (target >= section_analysis->section_size) continue;
    update_generated_label_kind(label_kinds, section_analysis->section_size, target, GENERATED_LABEL_DAT);
    generated_label_flags[target] = 1U;
  }
}

static int append_shaped_data_span(const M68kObject *object, size_t section_index,
    const M68kSectionAnalysisIR *section_analysis, const GeneratedLabelKind *label_kinds, M68kSectionIR *section_ir,
    uint32_t offset, const uint8_t *data, size_t size,const M68kPresentationPolicy *presentation, const char *comment) {
  int prefer_strings = (presentation == NULL) ? 1 : (presentation->prefer_strings != 0U);
  int prefer_long_data = (presentation == NULL) ? 1 : (presentation->prefer_long_data != 0U);
  size_t cursor = 0U;
  const M68kSection *section = object != NULL ? &object->sections[section_index] : NULL;
  while (cursor < size) {
    const M68kFixup *fixup = find_section_fixup_at_offset(object, section_index, offset + (uint32_t)cursor,
      M68K_FIXUP_WIDTH_32);
    uint32_t next_fixup_offset = 0U;
    int has_next_fixup = find_next_section_fixup_offset(object, section_index, offset + (uint32_t)cursor + 1U,
      M68K_FIXUP_WIDTH_32, &next_fixup_offset);
    uint32_t target = 0U;
    if (fixup != NULL && fixup->target_section_index == section_index && (size - cursor) >= 4U && section != NULL &&
        fixup->offset + 4U <= section->data_size) {
      char expr_name[32];
      GeneratedLabelKind kind = GENERATED_LABEL_DAT;
      target = read_be_u32_local(section->data + fixup->offset);
      if (target >= section_analysis->section_size) goto no_fixup_expr;
      if (label_kinds != NULL) kind = label_kinds[target];
      set_generated_name(expr_name, sizeof(expr_name), target, effective_label_kind(target, kind, section_analysis),
        presentation);
      if (append_expr_data_statement(section_ir, offset + (uint32_t)cursor, M68K_DATA_ITEM_LONGS, data + cursor, 4U,
          expr_name, cursor == 0U ? comment : NULL) != 0) {
        return -1;
      }
      cursor += 4U;
      continue;
    }
no_fixup_expr:
    if (size <= 16U && cursor == 0U &&
        !(prefer_long_data && size == 4U && (offset & 3U) == 0U && chunk_has_non_printable(data, 4U)))
      return append_data_statement(section_ir, offset, data, size, comment);
    size_t string_run = prefer_strings ? detect_string_run(data + cursor, size - cursor) : 0U;
    if (string_run != 0U) {
      if (append_typed_data_statement( section_ir, offset + (uint32_t)cursor, M68K_DATA_ITEM_STRING,
          data + cursor, string_run, cursor == 0U ? comment : NULL) != 0) {
        return -1;
      }
      cursor += string_run;
      continue;
    }
    if (prefer_long_data && (((offset + (uint32_t)cursor) & 3U) == 0U) &&
        (size - cursor) >= 4U && chunk_has_non_printable(data + cursor, 4U) &&
        (!has_next_fixup || next_fixup_offset >= offset + (uint32_t)cursor + 4U)) {
      size_t long_count = 4U;
      while (cursor + long_count + 4U <= size && (((offset + (uint32_t)cursor + (uint32_t)long_count) & 3U) == 0U) &&
          (!has_next_fixup || next_fixup_offset >= offset + (uint32_t)cursor + (uint32_t)long_count + 4U) &&
          find_section_fixup_at_offset(object, section_index, offset + (uint32_t)cursor + (uint32_t)long_count,
            M68K_FIXUP_WIDTH_32) == NULL &&
          chunk_has_non_printable(data + cursor + long_count, 4U) && (!prefer_strings ||
          detect_string_run(data + cursor + long_count, size - cursor - long_count) == 0U)) {
        long_count += 4U;
      }
      if (append_typed_data_statement( section_ir, offset + (uint32_t)cursor, M68K_DATA_ITEM_LONGS,
          data + cursor, long_count, cursor == 0U ? comment : NULL) != 0) {
        return -1;
      }
      cursor += long_count;
      continue;
    }
    {
      size_t byte_run = 1U;
      while (cursor + byte_run < size) {
        if (find_section_fixup_at_offset(object, section_index, offset + (uint32_t)cursor + (uint32_t)byte_run,
            M68K_FIXUP_WIDTH_32) != NULL) {
          break;
        }
        size_t next_string_run = prefer_strings ?
          detect_string_run(data + cursor + byte_run, size - cursor - byte_run) : 0U;
        if (next_string_run != 0U) break;
        if (prefer_long_data && (((offset + (uint32_t)cursor + (uint32_t)byte_run) & 3U) == 0U) &&
            (size - cursor - byte_run) >= 4U && chunk_has_non_printable(data + cursor + byte_run, 4U)) {
          break;
        }
        ++byte_run;
      }
      if (append_data_statement(section_ir, offset + (uint32_t)cursor, data + cursor, byte_run,
          cursor == 0U ? comment : NULL) != 0)
        return -1;
      cursor += byte_run;
    }
  }
  return 0;
}

static void set_generated_label_name(M68kSymbolRefIR *symbol_ref, uint32_t target, GeneratedLabelKind kind,
    const M68kPresentationPolicy *presentation) {
  if (symbol_ref == NULL) return;
  symbol_ref->has_name = 1;
  symbol_ref->name_is_generated = 1U;
  symbol_ref->addend = 0;
  set_generated_name(symbol_ref->name, sizeof(symbol_ref->name), target, kind, presentation);
}

static void annotate_instruction_labels(M68kInstructionIR *instruction, uint32_t offset,
    M68kSectionAnalysisIR *section_analysis, uint8_t *generated_label_flags, size_t generated_label_count,
    GeneratedLabelKind *label_kinds, size_t label_kind_count, const M68kPresentationPolicy *presentation) {
  size_t operand_index;
  uint32_t pc_base;
  uint32_t label_base;
  if (instruction == NULL || section_analysis == NULL) return;
  pc_base = offset + (uint32_t)instruction->byte_count;
  label_base = offset + 2U;
  for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    if (operand->kind == M68K_ASM_OPERAND_LABEL) {
      uint32_t target = label_base + (uint32_t)((int32_t)operand->value.value);
      if (section_has_any_label(section_analysis, generated_label_flags, generated_label_count, target)) {
        GeneratedLabelKind kind = (label_kinds != NULL && target < label_kind_count) ? label_kinds[target]
          : GENERATED_LABEL_LOC;
        set_generated_label_name(&operand->symbol_ref, target, effective_label_kind(target, kind, section_analysis),
          presentation);
      }
      continue;
    }
    if (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_IND ||
        operand->kind == M68K_ASM_OPERAND_POSTINC || operand->kind == M68K_ASM_OPERAND_ABSL ||
        operand->kind == M68K_ASM_OPERAND_BF_EA) {
      if (operand->value.ea_mode == 7 && (operand->value.ea_reg == 2 || operand->value.ea_reg == 3)) {
        uint32_t target = (uint32_t)((int32_t)pc_base + (int32_t)operand->value.value);
        uint32_t base = find_enclosing_code_start(section_analysis, target);
        if (base != UINT32_MAX && base != target) {
          GeneratedLabelKind kind = GENERATED_LABEL_LOC;
          if (label_kinds != NULL && base < label_kind_count) kind = label_kinds[base];
          set_generated_label_name(&operand->symbol_ref, base, effective_label_kind(base, kind, section_analysis),
            presentation);
          operand->symbol_ref.addend = (int32_t)(target - base);
        }
      } else if (operand->value.ea_mode == 7 && (operand->value.ea_reg == 1 || (operand->value.ea_reg == 4 &&
          mnemonic_equals(instruction, "movea") && operand_index == 0U))) {
        uint32_t target = operand->value.value;
        if (section_has_any_label(section_analysis, generated_label_flags, generated_label_count, target)) {
          GeneratedLabelKind kind = GENERATED_LABEL_DAT;
          if (instruction_is_call_transfer(instruction) || instruction_is_unconditional_transfer(instruction))
            kind = GENERATED_LABEL_SUB;
          if (label_kinds != NULL && target < label_kind_count)
            kind = label_kinds[target];
          set_generated_label_name(&operand->symbol_ref, target, effective_label_kind(target, kind, section_analysis),
            presentation);
        }
      }
    }
  }
}

static int build_section_ir(const M68kObject *object, const M68kSection *section,
    M68kSectionAnalysisIR *section_analysis,
    const M68kAnalysisPolicy *analysis_policy, M68kAnalysisFindings *findings, const M68kRenderPolicy *policy,
    M68kSectionIR *out_section_ir, char *out_error, size_t out_error_size) {
  GeneratedLabelKind *label_kinds = NULL;
  uint8_t *generated_label_flags = NULL;
  size_t offset = 0;
  (void)findings; (void)out_error; (void)out_error_size;
  m68k_ir_section_init(out_section_ir);
  out_section_ir->name = _strdup( (section->name != NULL && section->name[0] != '\0') ? section->name : "section");
  if (out_section_ir->name == NULL) return -1;
  out_section_ir->kind = section->kind;
  out_section_ir->size = section->size;
  if (section->kind == M68K_SECTION_BSS) return 0;
  if (section->data_size != 0U) {
    label_kinds = (GeneratedLabelKind *)calloc(section->data_size, sizeof(*label_kinds));
    generated_label_flags = (uint8_t *)calloc(section->data_size, 1U);
    if (label_kinds == NULL || generated_label_flags == NULL) {
      free(label_kinds);
      free(generated_label_flags);
      return -1;
    }
    if (build_generated_label_kinds(section, analysis_policy, findings, section_analysis, label_kinds,
        generated_label_flags) != 0) {
      free(label_kinds);
      free(generated_label_flags);
      return -1;
    }
    mark_data_fixup_labels(object, section_analysis, label_kinds, generated_label_flags);
    if (scan_interior_pc_relative_refs(section, analysis_policy, findings, section_analysis, label_kinds,
          generated_label_flags) != 0) {
      free(label_kinds);
      free(generated_label_flags);
      return -1;
    }
  }
  while (offset < section->data_size) {
    M68kInstructionIR instruction;
    char error[128];
    if (section_has_any_label(section_analysis, generated_label_flags, section->data_size, (uint32_t)offset) &&
        append_label_statement(out_section_ir, (uint32_t)offset, label_kinds, section->data_size, section_analysis,
          policy != NULL ? &policy->presentation : NULL) != 0) {
      free(label_kinds);
      free(generated_label_flags);
      return -1;
    }
    if (section->kind == M68K_SECTION_CODE && offset < section_analysis->certain_code_size &&
        section_analysis->certain_code_start != NULL && section_analysis->certain_code_start[offset] != 0U) {
      int decode_result = 0;
      char violation[128];
      char cpu_violation[128];
      violation[0] = '\0';
      cpu_violation[0] = '\0';
      decode_result = decode_instruction_with_policy( section->data + offset, section->data_size - offset,
          (uint32_t)offset, analysis_policy, NULL, &instruction, error, sizeof(error));
      if (decode_result > 0 && instruction.byte_count != 0U) {
        annotate_instruction_labels( &instruction, (uint32_t)offset, section_analysis, generated_label_flags,
          section->data_size, label_kinds, section->data_size, policy != NULL ? &policy->presentation : NULL);
        collect_section_violation_comments(section_analysis, (uint32_t)offset, violation, sizeof(violation));
        if (format_cpu_violation_comment(cpu_violation, sizeof(cpu_violation), &instruction, analysis_policy))
          append_statement_violation_comment(violation, sizeof(violation), cpu_violation);
        if (append_instruction_statement( out_section_ir, (uint32_t)offset, &instruction, violation[0] != '\0' ? violation : NULL) != 0) {
          free(label_kinds);
          free(generated_label_flags);
          return -1;
        }
        offset += instruction.byte_count;
      } else {
        size_t chunk = compute_data_span_chunk(section_analysis, generated_label_flags, section->data_size, offset,
          section->data_size);
        if (append_shaped_data_span( object, section_analysis->section_index, section_analysis, label_kinds,
            out_section_ir, (uint32_t)offset, section->data + offset, chunk,
            policy != NULL ? &policy->presentation : NULL,
            "decode failed in reachable code; region emitted as data") != 0) {
          free(label_kinds);
          free(generated_label_flags);
          return -1;
        }
        offset += chunk;
      }
    } else {
      size_t chunk = compute_data_span_chunk(section_analysis, generated_label_flags, section->data_size, offset,
        section->data_size);
      if (append_shaped_data_span( object, section_analysis->section_index, section_analysis, label_kinds,
          out_section_ir, (uint32_t)offset, section->data + offset, chunk,
          policy != NULL ? &policy->presentation : NULL, NULL) != 0) {
        free(label_kinds);
        free(generated_label_flags);
        return -1;
      }
      offset += chunk;
    }
  }
  free(label_kinds);
  free(generated_label_flags);
  return 0;
}

int platform_file_to_ir_with_policy(const char *backend_name, const char *path, const M68kRenderPolicy *policy,
    const M68kAnalysisPolicy *analysis_policy, M68kSourceFileIR *out_source_file, char *error_buf,
    size_t error_buf_size) {
  char error[256];
  M68kObject object;
  M68kSectionIR section_ir;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  size_t section_index;
  M68kRenderPolicy default_policy;
  M68kAnalysisPolicy default_analysis_policy;
  M68kAnalysisFindings findings;
  const M68kRenderPolicy *active_policy = policy;
  const M68kAnalysisPolicy *active_analysis_policy = analysis_policy;
  if (backend == NULL || backend->read_file == NULL || out_source_file == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "unknown platform file backend");
    return -1;
  }
  if (active_policy == NULL) {
    m68k_render_policy_init_for_syntax(&default_policy, M68K_IR_SYNTAX_CANONICAL);
    active_policy = &default_policy;
  }
  if (active_analysis_policy == NULL) {
    m68k_analysis_policy_init_default(&default_analysis_policy);
    active_analysis_policy = &default_analysis_policy;
  }
  m68k_analysis_findings_init(&findings);
  m68k_ir_source_file_init(out_source_file);
  m68k_object_init(&object);
  if (backend->read_file(path, &object, error, sizeof(error)) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, error);
    m68k_object_free(&object);
    return -1;
  }
  out_source_file->file_kind = object.platform_file_kind;
  if (strcmp(backend->name, "atari-st") == 0) {
    uint32_t program_flags = 0;
    if (m68k_atari_st_read_program_flags(path, &program_flags) == 0) {
      out_source_file->has_atari_st_program_flags = 1U;
      out_source_file->atari_st_program_flags = program_flags;
    }
  }
  for (section_index = 0; section_index < object.section_count; ++section_index) {
    M68kSectionAnalysisIR section_analysis;
    int append_result;
    m68k_ir_section_analysis_init(&section_analysis);
    if (build_section_analysis(&object, section_index, &object.sections[section_index], active_analysis_policy,
        &findings, &section_analysis, error_buf, error_buf_size) != 0 ||
        build_section_ir(&object, &object.sections[section_index], &section_analysis, active_analysis_policy, &findings,
          active_policy, &section_ir, error_buf, error_buf_size) != 0) {
      if (error_buf != NULL && error_buf_size != 0U && error_buf[0] == '\0')
        m68k_platform_set_error(error_buf, error_buf_size, "failed building source ir");
      m68k_ir_section_analysis_free(&section_analysis);
      m68k_object_free(&object);
      m68k_ir_source_file_free(out_source_file);
      return -1;
    }
    append_result = m68k_ir_source_file_append_section(out_source_file, &section_ir);
    m68k_ir_section_free(&section_ir);
    if (append_result != 0) {
      m68k_platform_set_error(error_buf, error_buf_size, "failed building source ir");
      m68k_ir_section_analysis_free(&section_analysis);
      m68k_object_free(&object);
      m68k_ir_source_file_free(out_source_file);
      return -1;
    }
    m68k_ir_section_analysis_free(&section_analysis);
  }
  m68k_object_free(&object);
  if (error_buf != NULL && error_buf_size != 0U) error_buf[0] = '\0';
  return 0;
}

int platform_file_analyze_path(const char *backend_name, const char *path, const M68kAnalysisPolicy *analysis_policy,
    M68kSourceAnalysisIR *out_source_analysis, char *error_buf, size_t error_buf_size) {
  char error[256];
  M68kObject object;
  const M68kBackend *backend = m68k_backend_by_name(backend_name);
  size_t section_index;
  M68kAnalysisPolicy default_analysis_policy;
  const M68kAnalysisPolicy *active_analysis_policy = analysis_policy;
  if (backend == NULL || backend->read_file == NULL || out_source_analysis == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "unknown platform file backend");
    return -1;
  }
  m68k_ir_source_analysis_init(out_source_analysis);
  if (active_analysis_policy == NULL) {
    m68k_analysis_policy_init_default(&default_analysis_policy);
    active_analysis_policy = &default_analysis_policy;
  }
  out_source_analysis->policy = *active_analysis_policy;
  m68k_object_init(&object);
  if (backend->read_file(path, &object, error, sizeof(error)) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, error);
    m68k_object_free(&object);
    return -1;
  }
  out_source_analysis->file_kind = object.platform_file_kind;
  m68k_analysis_findings_init(&out_source_analysis->findings);
  for (section_index = 0; section_index < object.section_count; ++section_index) {
    M68kSectionAnalysisIR section_analysis;
    M68kAnalysisFindings scratch_findings;
    M68kAnalysisFindings section_findings;
    m68k_ir_section_analysis_init(&section_analysis);
    m68k_analysis_findings_init(&scratch_findings);
    m68k_analysis_findings_init(&section_findings);
    if (build_section_analysis( &object, section_index, &object.sections[section_index], active_analysis_policy,
        &scratch_findings, &section_analysis, error_buf, error_buf_size) != 0 ||
        rebuild_cpu_violations(&object.sections[section_index], &section_analysis, active_analysis_policy) != 0 ||
        rebuild_decode_fail_violations(&object.sections[section_index], &section_analysis,
          active_analysis_policy) != 0 ||
        recompute_section_findings(&object.sections[section_index], &section_analysis, active_analysis_policy,
          &section_findings) != 0 ||
        m68k_ir_source_analysis_append_section(out_source_analysis, &section_analysis) != 0) {
      if (error_buf != NULL && error_buf_size != 0U && error_buf[0] == '\0')
        m68k_platform_set_error(error_buf, error_buf_size, "failed building cfg analysis");
      m68k_ir_section_analysis_free(&section_analysis);
      m68k_ir_source_analysis_free(out_source_analysis);
      m68k_object_free(&object);
      return -1;
    }
    if (section_findings.required_cpu > out_source_analysis->findings.required_cpu) {
      out_source_analysis->findings.required_cpu = section_findings.required_cpu;
    }
    out_source_analysis->findings.cpu_violation_count += section_findings.cpu_violation_count;
    m68k_ir_section_analysis_free(&section_analysis);
  }
  m68k_object_free(&object);
  if (error_buf != NULL && error_buf_size != 0U) error_buf[0] = '\0';
  return 0;
}

int platform_file_analyze_path_json(const char *backend_name, const char *path,
    const M68kAnalysisPolicy *analysis_policy, char **out_json, char *error_buf, size_t error_buf_size) {
  M68kSourceAnalysisIR source_analysis;
  JsonBuilder builder = {0};
  size_t section_index;
  int result;
  if (out_json == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "null output");
    return -1;
  }
  *out_json = NULL;
  m68k_ir_source_analysis_init(&source_analysis);
  result = platform_file_analyze_path(backend_name, path, analysis_policy, &source_analysis, error_buf, error_buf_size);
  if (result != 0)
    return result;
  if (json_builder_appendf( &builder,
      "{\"file_kind\":%u,\"analysis_policy\":{\"max_cpu\":%u},\"findings\":{\"required_cpu\":%u,"
      "\"cpu_violation_count\":%u},\"section_count\":%u,\"sections\":[",
      (unsigned)source_analysis.file_kind, (unsigned)source_analysis.policy.max_cpu,
      (unsigned)source_analysis.findings.required_cpu, (unsigned)source_analysis.findings.cpu_violation_count,
      (unsigned)source_analysis.section_count) != 0) {
    goto oom;
  }
  for (section_index = 0; section_index < source_analysis.section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis.sections[section_index];
    size_t block_index;
    size_t edge_index;
    size_t violation_index;
    if (section_index != 0U && json_builder_append(&builder, ",") != 0)
      goto oom;
    if (json_builder_appendf( &builder,
        "{\"section_index\":%u,\"section_kind\":%u,\"section_size\":%u,\"label_count\":%u,\"block_count\":%u,"
        "\"edge_count\":%u,\"violation_count\":%u,\"blocks\":[",
        (unsigned)section->section_index, (unsigned)section->section_kind, (unsigned)section->section_size,
        (unsigned)section->label_count, (unsigned)section->block_count, (unsigned)section->edge_count,
        (unsigned)section->violation_count) != 0) {
      goto oom;
    }
    for (block_index = 0; block_index < section->block_count; ++block_index) {
      const M68kCfgBlockIR *block = &section->blocks[block_index];
      if (block_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf( &builder,
          "{\"start_offset\":%u,\"end_offset\":%u,\"certainty\":%u,\"edge_start\":%u,\"edge_count\":%u}",
          (unsigned)block->start_offset, (unsigned)block->end_offset, (unsigned)block->certainty,
          (unsigned)block->edge_start, (unsigned)block->edge_count) != 0) {
        goto oom;
      }
    }
    if (json_builder_append(&builder, "],\"edges\":[") != 0)
      goto oom;
    for (edge_index = 0; edge_index < section->edge_count; ++edge_index) {
      const M68kCfgEdgeIR *edge = &section->edges[edge_index];
      if (edge_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf( &builder,
          "{\"source_block_index\":%u,\"target_block_index\":%u,\"source_offset\":%u,\"target_offset\":%u,\"kind\":%u}",
          (unsigned)edge->source_block_index, (unsigned)edge->target_block_index, (unsigned)edge->source_offset,
          (unsigned)edge->target_offset, (unsigned)edge->kind) != 0) {
        goto oom;
      }
    }
    if (json_builder_append(&builder, "],\"violations\":[") != 0)
      goto oom;
    for (violation_index = 0; violation_index < section->violation_count; ++violation_index) {
      const M68kViolationIR *violation = &section->violations[violation_index];
      if (violation_index != 0U && json_builder_append(&builder, ",") != 0)
        goto oom;
      if (json_builder_appendf( &builder, "{\"offset\":%u,\"kind\":%u,\"message\":",
          (unsigned)violation->offset, (unsigned)violation->kind) != 0)
        goto oom;
      if (json_builder_append_json_string(&builder, violation->message != NULL ? violation->message : "") != 0)
        goto oom;
      if (json_builder_append(&builder, "}") != 0)
        goto oom;
    }
    if (json_builder_append(&builder, "]}") != 0)
      goto oom;
  }
  if (json_builder_append(&builder, "]}") != 0)
    goto oom;
  m68k_ir_source_analysis_free(&source_analysis);
  if (error_buf != NULL && error_buf_size != 0U) error_buf[0] = '\0';
  *out_json = builder.data;
  return 0;

oom:
  json_builder_free(&builder);
  m68k_ir_source_analysis_free(&source_analysis);
  m68k_platform_set_error(error_buf, error_buf_size, "out of memory");
  return -1;
}

int platform_file_render_ir_with_policy(const M68kSourceFileIR *source_file, const M68kRenderPolicy *policy,
    char **out_text, char *error_buf, size_t error_buf_size) {
  return m68k_source_ir_render_text_with_policy(source_file, policy, out_text, error_buf, error_buf_size);
}

void platform_file_source_ir_free(M68kSourceFileIR *source_file) {
  m68k_ir_source_file_free(source_file);
}

void platform_file_source_analysis_free(M68kSourceAnalysisIR *source_analysis) {
  m68k_ir_source_analysis_free(source_analysis);
}
