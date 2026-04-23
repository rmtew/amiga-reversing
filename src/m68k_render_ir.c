#include "m68k_render_ir.h"

#include "m68k_assembler.h"
#include "m68k_instruction_spec.h"
#include "m68k_ir_codec.h"
#include "m68k_parse_util.h"
#include "m68k_plain_parse.h"
#include "m68k_simulator.h"
#include "m68k_source_text_util.h"
#include "platform_atari_st.h"
#include "platform_common.h"
#include "generated/amiga_hunk_file_runtime.h"
#include "generated/amiga_os_runtime.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct M68kRenderLookup M68kRenderLookup;

typedef struct M68kRenderPlatformState {
  uint8_t address_base_known[8];
  char address_base_library[8][64];
  uint8_t data_app_base_known[8];
  uint8_t address_app_base_known[8];
  uint8_t d0_lvo_known;
  int16_t d0_lvo;
} M68kRenderPlatformState;

typedef struct M68kRenderGlobalBaseSlot {
  size_t section_index;
  uint32_t offset;
  size_t source_section_index;
  uint32_t source_offset;
  uint8_t has_source;
  char library_name[64];
} M68kRenderGlobalBaseSlot;

typedef struct M68kRenderGlobalBaseObservation {
  size_t section_index;
  uint32_t offset;
  int16_t lvos[32];
  size_t lvo_count;
} M68kRenderGlobalBaseObservation;

typedef struct M68kRenderBaseFieldSlot {
  char owner_name[64];
  int16_t displacement;
  size_t source_section_index;
  uint32_t source_offset;
  uint8_t has_source;
  char library_name[64];
  char symbol_name[64];
  uint8_t value_kind;
  uint8_t conflicted;
} M68kRenderBaseFieldSlot;

#define M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE 0U
#define M68K_RENDER_BASE_FIELD_SLOT_IOREQUEST 1U
#define M68K_RENDER_BASE_FIELD_SLOT_NAMED_VALUE 2U
#define M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS 3U

typedef struct M68kRenderIndexedVectorWrapper {
  size_t section_index;
  uint32_t offset;
  char library_name[64];
} M68kRenderIndexedVectorWrapper;

typedef struct M68kRenderRecoveredFunctionArg {
  size_t section_index;
  uint32_t function_offset;
  uint16_t stack_offset;
  uint8_t reg_kind;
  uint8_t reg_index;
  const AmigaOsCallInputInfo *input;
} M68kRenderRecoveredFunctionArg;

typedef struct M68kRenderRecoveredLocalCallSummary {
  size_t section_index;
  uint32_t target_offset;
  const AmigaOsLibraryVectorInfo *vector;
} M68kRenderRecoveredLocalCallSummary;

typedef struct M68kRenderTypedSlotEffect {
  size_t section_index;
  uint32_t offset;
  int16_t displacement;
  const AmigaOsCallOutputInfo *output;
} M68kRenderTypedSlotEffect;

typedef struct M68kRenderAppSlotRef {
  size_t section_index;
  M68kAppSlotRefIR ref;
} M68kRenderAppSlotRef;

typedef struct M68kRenderTypedRegValue {
  uint8_t known;
  const AmigaOsCallOutputInfo *output;
} M68kRenderTypedRegValue;

typedef struct M68kRenderTypedState {
  M68kRenderTypedRegValue data_regs[8];
  M68kRenderTypedRegValue addr_regs[8];
} M68kRenderTypedState;

typedef struct M68kRenderDataPointerValue {
  uint8_t known;
  size_t section_index;
  uint32_t offset;
} M68kRenderDataPointerValue;

typedef struct M68kRenderDataPointerState {
  M68kRenderDataPointerValue data_regs[8];
  M68kRenderDataPointerValue addr_regs[8];
} M68kRenderDataPointerState;

typedef struct M68kRenderStringSpan {
  size_t section_index;
  uint32_t offset;
  uint32_t size;
} M68kRenderStringSpan;

typedef struct M68kRenderInstructionComment {
  size_t section_index;
  uint32_t offset;
  char comment[384];
} M68kRenderInstructionComment;

typedef struct M68kRenderTraceRegName {
  uint8_t known;
  char name[64];
} M68kRenderTraceRegName;

typedef struct M68kRenderTraceLocalSlot {
  uint8_t valid;
  uint8_t base_reg;
  int16_t displacement;
  char library_name[64];
} M68kRenderTraceLocalSlot;

typedef struct M68kRenderTraceAppAddress {
  uint8_t known;
  int16_t displacement;
} M68kRenderTraceAppAddress;

typedef struct M68kRenderBaseTraceState {
  M68kRenderTraceRegName data_regs[8];
  M68kRenderTraceRegName addr_regs[8];
  M68kRenderTraceAppAddress app_addresses[8];
  M68kRenderTraceLocalSlot local_slots[32];
} M68kRenderBaseTraceState;

static char ascii_lower_local(char c) {
  return (c >= 'A' && c <= 'Z') ? (char)(c - 'A' + 'a') : c;
}

static int ascii_char_is_symbol_local(char c, int first) {
  if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || c == '_' || c == '.') return 1;
  if (!first && c >= '0' && c <= '9') return 1;
  return 0;
}

static int asm_symbol_name_is_safe_local(const char *name) {
  size_t index;
  if (name == NULL || name[0] == '\0') return 0;
  for (index = 0U; name[index] != '\0'; ++index) {
    if (!ascii_char_is_symbol_local(name[index], index == 0U)) return 0;
  }
  return 1;
}

static int ascii_contains_case_local(const char *text, const char *needle) {
  size_t text_index;
  size_t needle_len;
  if (text == NULL || needle == NULL || needle[0] == '\0') return 0;
  needle_len = strlen(needle);
  for (text_index = 0U; text[text_index] != '\0'; ++text_index) {
    size_t needle_index;
    for (needle_index = 0U; needle_index < needle_len; ++needle_index) {
      if (text[text_index + needle_index] == '\0') return 0;
      if (ascii_lower_local(text[text_index + needle_index]) != ascii_lower_local(needle[needle_index])) break;
    }
    if (needle_index == needle_len) return 1;
  }
  return 0;
}

static const char *amiga_library_name_from_base_symbol_name(const char *symbol_name) {
  const char *matched_library = NULL;
  size_t index;
  if (symbol_name == NULL || symbol_name[0] == '\0') return NULL;
  if (ascii_contains_case_local(symbol_name, "ExecBase")) return amiga_os_exec_base_library_name();
  for (index = 0U; index < AMIGA_OS_LIBRARY_VECTOR_COUNT; ++index) {
    const AmigaOsLibraryVectorInfo *vector = amiga_os_library_vector_at(index);
    const char *base_name;
    const char *library_name;
    if (vector == NULL) continue;
    base_name = amiga_os_name(M68K_PLATFORM_NAME_BASE, vector->base_id);
    if (base_name == NULL || base_name[0] == '\0') continue;
    if (!ascii_contains_case_local(symbol_name, base_name)) continue;
    library_name = amiga_os_find_library_name_by_base_name(base_name);
    if (library_name == NULL || library_name[0] == '\0') continue;
    if (matched_library == NULL) {
      matched_library = library_name;
    } else if (strcmp(matched_library, library_name) != 0) {
      return NULL;
    }
  }
  return matched_library;
}

static void format_numeric_value(char *buffer, size_t buffer_size, uint32_t size, uint32_t value);
static void format_lookup_asm_label(const M68kRenderLookup *lookup, char *buf, size_t buf_size,
    size_t section_index, uint32_t offset);
static const M68kAnalysisStructuredDataItem *lookup_structured_data_item_at_offset(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset);
static const M68kAnalysisStructuredDataItem *lookup_structured_data_item_covering_offset(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset);
static int structured_data_item_comment(const M68kAnalysisStructuredDataItem *item, char *comment,
    size_t comment_size);
static int structured_data_item_render_comment(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, char *comment, size_t comment_size);
static int structured_data_item_symbolic_operand_expr(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, char *expr, size_t expr_size);
static int amiga_value_domain_symbolic_expr(const char *domain_name, uint32_t value, char *expr,
    size_t expr_size);
static void record_asm_source_failure(M68kRenderIRPreview *preview, uint32_t kind, size_t section_index,
    uint32_t offset, uint32_t aux_offset);
static int lookup_offset_is_inside_relocation_payload(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset);
static int lookup_has_renderable_label(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
static const char *lookup_global_base_slot_library(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset);
static const char *lookup_base_field_slot_library(const M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement);
static const char *lookup_app_base_field_slot_library(const M68kRenderLookup *lookup, int16_t displacement);
static int library_base_can_use_app_extension_slot(const char *owner_name, int16_t displacement);
static int lookup_base_field_slot_symbol_name(const M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement, char *symbol_name, size_t symbol_name_size);
static int lookup_app_base_field_slot_symbol_name(const M68kRenderLookup *lookup, int16_t displacement,
    char *symbol_name, size_t symbol_name_size);
static const char *lookup_indexed_vector_wrapper_library(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset);
static void render_asm_app_extension_rs(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
  const M68kDecodeIR *decode);
static void platform_state_clear_d0_lvo(M68kRenderPlatformState *state);
static int platform_state_name_is_app_base(const char *name);
static int operand_is_address_displacement_local(const M68kOperandIR *operand, uint8_t *out_reg,
  int16_t *out_displacement);
static int operand_is_data_register_local(const M68kOperandIR *operand, uint8_t *out_reg);
static int operand_address_register_index_local(const M68kOperandIR *operand, uint8_t *out_reg);
static uint8_t app_slot_access_kind_from_instruction(const M68kInstructionIR *instruction, size_t operand_index);
static int reglist_contains_data_register_local(const M68kOperandIR *operand, uint8_t reg_index);
static int accepted_start_at(const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t offset);
static int candidate_direct_target(const M68kDecodeCandidate *candidate, size_t *out_section_index,
  uint32_t *out_target);
static int candidate_direct_control_target(const M68kRenderLookup *lookup, size_t source_section_index,
  const M68kDecodeCandidate *candidate, size_t *out_section_index, uint32_t *out_target);
static int candidate_direct_same_section_target(const M68kDecodeCandidate *candidate, size_t section_index,
  uint32_t *out_target);
static int candidate_terminates_a6_state(const M68kDecodeCandidate *candidate);
static int render_lookup_add_indexed_vector_wrapper(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
  const char *library_name);
static int render_lookup_add_instruction_comment(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
  const char *comment);
static int render_lookup_add_recovered_function_arg(M68kRenderLookup *lookup, size_t section_index,
  uint32_t function_offset, uint16_t stack_offset, uint8_t reg_kind, uint8_t reg_index,
  const AmigaOsCallInputInfo *input);
static int render_lookup_add_recovered_local_call_summary(M68kRenderLookup *lookup, size_t section_index,
  uint32_t target_offset, const AmigaOsLibraryVectorInfo *vector);
static int render_lookup_add_typed_slot_effect(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
  int16_t displacement, const AmigaOsCallOutputInfo *output);
static int render_lookup_add_string_span(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
  uint32_t size);
static const char *lookup_instruction_comment(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
static const M68kRenderStringSpan *lookup_string_span_at_offset(const M68kRenderLookup *lookup, size_t section_index,
  uint32_t offset);
static int append_comment_part_local(char *comment, size_t comment_size, const char *part);
static int render_lookup_infer_amiga_call_input_comments(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
  uint8_t **accepted_start);
static const AmigaOsLibraryVectorInfo *resolve_amiga_direct_wrapper_vector_at(const M68kRenderLookup *lookup,
  const M68kDecodeIR *decode, uint8_t **accepted_start, size_t section_index, uint32_t wrapper_offset,
  unsigned depth);
static const AmigaOsLibraryVectorInfo *resolve_amiga_direct_wrapper_call_vector_depth(const M68kRenderLookup *lookup,
  const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
  const M68kDecodeCandidate *candidate, unsigned depth);
static const AmigaOsLibraryVectorInfo *resolve_amiga_direct_wrapper_call_vector(const M68kRenderLookup *lookup,
  const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
  const M68kDecodeCandidate *candidate);
static const AmigaOsLibraryVectorInfo *resolve_amiga_local_helper_call_vector_depth(const M68kRenderLookup *lookup,
  const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
  const M68kDecodeCandidate *candidate, unsigned depth);
static const AmigaOsLibraryVectorInfo *resolve_amiga_local_helper_call_vector(const M68kRenderLookup *lookup,
  const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
  const M68kDecodeCandidate *candidate);
static void attach_known_instruction_relocations(const M68kRenderLookup *lookup, size_t section_index,
  const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction);

static uint64_t hash_step(uint64_t hash, uint64_t value) {
  hash ^= value;
  hash *= 1099511628211ULL;
  return hash;
}

static void hash_statement(M68kRenderIRPreview *preview, uint8_t kind, size_t section_index, uint32_t offset,
    uint32_t size, uint32_t aux) {
  preview->structural_hash = hash_step(preview->structural_hash, kind);
  preview->structural_hash = hash_step(preview->structural_hash, (uint64_t)section_index);
  preview->structural_hash = hash_step(preview->structural_hash, offset);
  preview->structural_hash = hash_step(preview->structural_hash, size);
  preview->structural_hash = hash_step(preview->structural_hash, aux);
}

static void render_text_line(M68kRenderIRPreview *preview, char kind, size_t section_index, uint32_t offset,
    uint32_t size, uint32_t aux) {
  char line[96];
  int length;
  size_t index;
  if (preview == NULL) return;
  length = snprintf(line, sizeof(line), "%c %u %08X %u %u\n", kind, (unsigned)section_index,
    (unsigned)offset, (unsigned)size, (unsigned)aux);
  if (length <= 0) return;
  preview->text_bytes += (uint32_t)length;
  for (index = 0U; index < (size_t)length && index < sizeof(line); ++index)
    preview->text_hash = hash_step(preview->text_hash, (unsigned char)line[index]);
}

static void hash_asm_text(M68kRenderIRPreview *preview, const char *text) {
  size_t index;
  size_t length;
  if (preview == NULL || text == NULL) return;
  length = strlen(text);
  if (preview->collect_asm_source_text) {
    size_t used = (size_t)preview->asm_source_bytes;
    size_t needed;
    if (used >= (size_t)UINT32_MAX || length > (size_t)UINT32_MAX - used) {
      preview->asm_source_allocation_failed = 1U;
    } else {
      needed = used + length + 1U;
      if (needed > preview->asm_source_text_capacity) {
        size_t next_capacity = preview->asm_source_text_capacity == 0U ? 4096U : preview->asm_source_text_capacity;
        char *grown;
        while (next_capacity < needed) {
          if (next_capacity > ((size_t)-1) / 2U) {
            preview->asm_source_allocation_failed = 1U;
            break;
          }
          next_capacity *= 2U;
        }
        if (!preview->asm_source_allocation_failed) {
          grown = (char *)realloc(preview->asm_source_text, next_capacity);
          if (grown == NULL) preview->asm_source_allocation_failed = 1U;
          else {
            preview->asm_source_text = grown;
            preview->asm_source_text_capacity = next_capacity;
          }
        }
      }
      if (!preview->asm_source_allocation_failed) {
        memcpy(preview->asm_source_text + used, text, length);
        preview->asm_source_text[used + length] = '\0';
      }
    }
  }
  if (preview->collect_asm_source_hash) {
    for (index = 0U; index < length; ++index)
      preview->asm_source_hash = hash_step(preview->asm_source_hash, (unsigned char)text[index]);
  }
  preview->asm_source_bytes += (uint32_t)length;
}

static void format_asm_label(char *buf, size_t buf_size, size_t section_index, uint32_t offset) {
  if (buf == NULL || buf_size == 0U) return;
  snprintf(buf, buf_size, "loc_%u_%08X", (unsigned)section_index, (unsigned)offset);
}

static int render_asm_include_once(M68kRenderIRPreview *preview, const char *include_path) {
  uint16_t index;
  char line[128];
  if (preview == NULL || include_path == NULL || include_path[0] == '\0') return 1;
  if (preview->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 1;
  for (index = 0U; index < preview->asm_source_include_count; ++index) {
    if (strcmp(preview->asm_source_includes[index], include_path) == 0) return 1;
  }
  if (preview->asm_source_include_count >= M68K_RENDER_ASM_INCLUDE_LIMIT) {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, 0U, 0U);
    return 0;
  }
  snprintf(preview->asm_source_includes[preview->asm_source_include_count],
    sizeof(preview->asm_source_includes[preview->asm_source_include_count]), "%s", include_path);
  ++preview->asm_source_include_count;
  snprintf(line, sizeof(line), "    INCLUDE \"%s\"\n", include_path);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  return 1;
}

static int render_asm_declare_symbol_once(M68kRenderIRPreview *preview, const char *symbol_name, int32_t value) {
  uint16_t index;
  char line[160];
  if (preview == NULL || symbol_name == NULL || symbol_name[0] == '\0') return 1;
  if (preview->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 1;
  if (!asm_symbol_name_is_safe_local(symbol_name)) {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, 0U, 0U);
    return 0;
  }
  for (index = 0U; index < preview->asm_source_declaration_count; ++index) {
    if (strcmp(preview->asm_source_declarations[index], symbol_name) == 0) return 1;
  }
  if (preview->asm_source_declaration_count >= M68K_RENDER_ASM_DECLARATION_LIMIT) {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, 0U, 0U);
    return 0;
  }
  snprintf(preview->asm_source_declarations[preview->asm_source_declaration_count],
    sizeof(preview->asm_source_declarations[preview->asm_source_declaration_count]), "%s", symbol_name);
  ++preview->asm_source_declaration_count;
  snprintf(line, sizeof(line), "%s\tEQU\t%d\n", symbol_name, (int)value);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  return 1;
}

static int render_asm_define_amiga_lvo_symbol_once(M68kRenderIRPreview *preview, uint16_t symbol_id) {
  const char *symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, symbol_id);
  const AmigaOsLibraryVectorInfo *vector = amiga_os_find_library_vector_by_symbol_id(symbol_id);
  if (symbol_name == NULL || symbol_name[0] == '\0' || vector == NULL) {
    if (preview != NULL) {
      ++preview->asm_source_instruction_render_failures;
      record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, 0U, 0U);
    }
    return 0;
  }
  return render_asm_declare_symbol_once(preview, symbol_name, (int32_t)vector->lvo);
}

static int render_asm_include_for_amiga_symbol(M68kRenderIRPreview *preview, const char *symbol_name) {
  const char *include_path;
  if (symbol_name == NULL || symbol_name[0] == '\0') return 1;
  include_path = amiga_os_find_symbol_include(symbol_name);
  return render_asm_include_once(preview, include_path);
}

static int render_asm_include_for_symbol_expr(M68kRenderIRPreview *preview, const char *expr) {
  char token[64];
  size_t token_len = 0U;
  size_t index;
  if (expr == NULL || expr[0] == '\0') return 1;
  for (index = 0U;; ++index) {
    char c = expr[index];
    if (c == '|' || c == '\0') {
      if (token_len == 0U || token_len >= sizeof(token)) return 0;
      token[token_len] = '\0';
      if (!asm_symbol_name_is_safe_local(token) || !render_asm_include_for_amiga_symbol(preview, token)) return 0;
      token_len = 0U;
      if (c == '\0') return 1;
    } else {
      if (token_len + 1U >= sizeof(token)) return 0;
      token[token_len++] = c;
    }
  }
}

static int render_asm_include_for_amiga_symbol_id(M68kRenderIRPreview *preview, uint16_t symbol_id) {
  uint16_t include_id = amiga_os_find_symbol_include_id(symbol_id);
  const char *include_path = include_id != AMIGA_OS_INCLUDE_ID_NONE
    ? amiga_os_name(M68K_PLATFORM_NAME_INCLUDE, include_id)
    : NULL;
  if (include_path != NULL && include_path[0] != '\0') return render_asm_include_once(preview, include_path);
  return render_asm_define_amiga_lvo_symbol_once(preview, symbol_id);
}

static int render_asm_includes_for_structured_data_item(M68kRenderIRPreview *preview,
    const M68kAnalysisStructuredDataItem *item) {
  if (item == NULL) return 1;
  return render_asm_include_for_amiga_symbol(preview, item->field_name) &&
    render_asm_include_for_amiga_symbol(preview, item->constant_name);
}

static void render_asm_label(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset) {
  const M68kAnalysisStructuredDataItem *item =
    lookup_structured_data_item_at_offset(lookup, section_index, offset);
  char line[160];
  char name[64];
  if (!render_asm_includes_for_structured_data_item(preview, item)) return;
  format_lookup_asm_label(lookup, name, sizeof(name), section_index, offset);
  if (item != NULL && item->struct_name[0] != '\0') {
    snprintf(line, sizeof(line), "%s:\t; STRUCT %s\n", name, item->struct_name);
  } else {
    snprintf(line, sizeof(line), "%s:\n", name);
  }
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static void platform_state_clear_register(M68kRenderPlatformState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  state->address_base_known[reg_index] = 0U;
  state->address_base_library[reg_index][0] = '\0';
  state->address_app_base_known[reg_index] = 0U;
}

static void platform_state_clear_address_app_base(M68kRenderPlatformState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  state->address_app_base_known[reg_index] = 0U;
}

static void platform_state_clear_data_app_base(M68kRenderPlatformState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  state->data_app_base_known[reg_index] = 0U;
}

static void platform_state_clear_all_app_bases(M68kRenderPlatformState *state) {
  if (state == NULL) return;
  memset(state->data_app_base_known, 0, sizeof(state->data_app_base_known));
  memset(state->address_app_base_known, 0, sizeof(state->address_app_base_known));
}

static void platform_state_clear_d0_lvo(M68kRenderPlatformState *state) {
  if (state == NULL) return;
  state->d0_lvo_known = 0U;
  state->d0_lvo = 0;
}

static void platform_state_set_register_library(M68kRenderPlatformState *state, uint8_t reg_index,
    const char *library_name) {
  if (state == NULL || reg_index >= 8U || library_name == NULL || library_name[0] == '\0') return;
  if (amiga_os_find_library_base_name(library_name) == NULL) return;
  state->address_base_known[reg_index] = 1U;
  state->address_app_base_known[reg_index] = 0U;
  snprintf(state->address_base_library[reg_index], sizeof(state->address_base_library[reg_index]), "%s",
    library_name);
}

static int platform_state_name_is_app_base(const char *name) {
  return name != NULL && strcmp(name, "__amiga_app_base__") == 0;
}

static void platform_state_set_register_app_base(M68kRenderPlatformState *state, uint8_t reg_kind,
    uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == M68K_ANALYSIS_REGISTER_DATA) {
    state->data_app_base_known[reg_index] = 1U;
    if (reg_index == 0U) platform_state_clear_d0_lvo(state);
  } else if (reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS) {
    state->address_base_known[reg_index] = 0U;
    state->address_base_library[reg_index][0] = '\0';
    state->address_app_base_known[reg_index] = 1U;
  }
}

static void preview_record_platform_vector(M68kRenderIRPreview *preview, const AmigaOsLibraryVectorInfo *vector) {
  if (preview == NULL || vector == NULL) return;
  ++preview->platform_call_count;
  preview->platform_effect_count += vector->input_count;
  if (vector->output.reg_kind != AMIGA_OS_REGISTER_NONE ||
      vector->output.output_id != AMIGA_OS_SYMBOL_ID_NONE ||
      vector->output.type_id != AMIGA_OS_TYPE_ID_NONE ||
      vector->output.struct_id != AMIGA_OS_STRUCT_ID_NONE) {
    ++preview->platform_effect_count;
  }
}

static void preview_record_platform_vector_effects(M68kRenderIRPreview *preview,
    M68kSectionAnalysisIR *section_analysis, uint32_t offset, const AmigaOsLibraryVectorInfo *vector) {
  const AmigaOsCallOutputInfo *output;
  const char *output_symbol_name;
  const char *output_type_name;
  const char *output_semantic_kind;
  const char *output_value_domain_name;
  if (preview == NULL || section_analysis == NULL || vector == NULL) return;
  output = &vector->output;
  if (output->reg_kind == AMIGA_OS_REGISTER_NONE || output->reg_index >= 8U) return;
  output_symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, output->output_id);
  output_type_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, output->struct_id);
  if (output_type_name == NULL || output_type_name[0] == '\0')
    output_type_name = amiga_os_name(M68K_PLATFORM_NAME_TYPE, output->type_id);
  output_semantic_kind = amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, output->semantic_kind_id);
  output_value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, output->value_domain_id);
  if ((output_symbol_name == NULL || output_symbol_name[0] == '\0') &&
      (output_type_name == NULL || output_type_name[0] == '\0') &&
      (output_semantic_kind == NULL || output_semantic_kind[0] == '\0') &&
      (output_value_domain_name == NULL || output_value_domain_name[0] == '\0')) {
    return;
  }
  if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis,
      M68K_PLATFORM_BACKEND_AMIGA_HUNK, offset, M68K_PLATFORM_EFFECT_SET_TYPED_REG,
      output->reg_kind, output->reg_index, INT16_MIN, INT16_MIN, NULL,
      output_symbol_name, output_type_name, output_semantic_kind, output_value_domain_name, 0U, 0) != 0) {
    preview->asm_source_allocation_failed = 1U;
  }
}

static void preview_record_platform_vector_call(M68kRenderIRPreview *preview,
    M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t kind, uint8_t note_kind,
    const AmigaOsLibraryVectorInfo *vector) {
  const char *symbol_name;
  const char *note_symbol_name = NULL;
  const char *available_since = NULL;
  const char *library_name;
  const char *note_base_name = NULL;
  if (preview == NULL || vector == NULL) return;
  preview_record_platform_vector(preview, vector);
  if (section_analysis == NULL) return;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, vector->lvo_symbol_id);
  if (symbol_name == NULL || symbol_name[0] == '\0') return;
  if (note_kind != M68K_PLATFORM_CALL_NOTE_NONE) {
    note_symbol_name = symbol_name;
    symbol_name = NULL;
    library_name = amiga_os_name(M68K_PLATFORM_NAME_LIBRARY, vector->library_id);
    note_base_name = amiga_os_find_library_base_name(library_name);
  }
  available_since = amiga_os_compatibility_version_name((AmigaOsCompatVersion)vector->available_since_version);
  if (m68k_ir_section_analysis_append_recovered_platform_call(section_analysis,
      M68K_PLATFORM_BACKEND_AMIGA_HUNK, offset, kind, symbol_name, note_kind,
      note_base_name, note_symbol_name, 0U, INT16_MIN, INT16_MIN, 0U, 0U, 0U,
      available_since != NULL && available_since[0] != '\0' ? available_since : NULL,
      vector->fd_version != NULL && vector->fd_version[0] != '\0' ? vector->fd_version : NULL) != 0) {
    preview->asm_source_allocation_failed = 1U;
  }
  preview_record_platform_vector_effects(preview, section_analysis, offset, vector);
}

static void platform_state_apply_policy_register_seeds(M68kRenderPlatformState *state,
    const M68kAnalysisPolicy *policy, size_t section_index, uint32_t offset) {
  uint16_t index;
  if (state == NULL || policy == NULL) return;
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    if (seed->has_section_index && seed->section_index != (uint32_t)section_index) continue;
    if (seed->has_entry_offset) {
      if (seed->entry_offset != offset) continue;
    } else if (!policy->has_entry_offset || section_index != 0U || policy->entry_offset != offset) continue;
    if (seed->kind != M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE &&
        (seed->kind != M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR || !platform_state_name_is_app_base(seed->name))) {
      continue;
    }
    if (platform_state_name_is_app_base(seed->name)) {
      platform_state_set_register_app_base(state, seed->reg_kind, seed->reg_index);
      continue;
    }
    if (seed->reg_kind != M68K_ANALYSIS_REGISTER_ADDRESS || seed->reg_index >= 8U) continue;
    platform_state_set_register_library(state, seed->reg_index, seed->name);
  }
}

static void render_asm_policy_entry_comments(M68kRenderIRPreview *preview, const M68kAnalysisPolicy *policy,
    size_t section_index, uint32_t offset) {
  uint16_t index;
  if (preview == NULL || policy == NULL) return;
  for (index = 0U; index < policy->entry_comment_count && index < M68K_ANALYSIS_ENTRY_COMMENT_LIMIT; ++index) {
    const M68kAnalysisEntryComment *comment = &policy->entry_comments[index];
    char line[256];
    if (comment->has_section_index && comment->section_index != (uint32_t)section_index) continue;
    if (comment->offset != offset || comment->comment[0] == '\0') continue;
    snprintf(line, sizeof(line), "    ; %s\n", comment->comment);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
  }
}

static void render_asm_comment_line(M68kRenderIRPreview *preview, const char *comment) {
  char line[512];
  if (preview == NULL || comment == NULL || comment[0] == '\0') return;
  snprintf(line, sizeof(line), "    ; %s\n", comment);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static int format_policy_register_seed_comment_local(const M68kAnalysisPolicy *policy, size_t section_index,
    uint32_t offset, char *message, size_t message_size) {
  size_t used = 0U;
  uint8_t emitted[2][8] = {{0}};
  uint16_t index;
  if (message == NULL || message_size == 0U) return 0;
  message[0] = '\0';
  if (policy == NULL) return 0;
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    char reg_name[4];
    const char *kind_text;
    if (seed->has_section_index && seed->section_index != (uint32_t)section_index) continue;
    if (seed->has_entry_offset) {
      if (seed->entry_offset != offset) continue;
    } else if (!policy->has_entry_offset || section_index != 0U || policy->entry_offset != offset) continue;
    if (seed->reg_kind != M68K_ANALYSIS_REGISTER_DATA && seed->reg_kind != M68K_ANALYSIS_REGISTER_ADDRESS) continue;
    if (seed->reg_index >= 8U || seed->name[0] == '\0') continue;
    if (emitted[seed->reg_kind - 1U][seed->reg_index]) continue;
    emitted[seed->reg_kind - 1U][seed->reg_index] = 1U;
    snprintf(reg_name, sizeof(reg_name), "%c%u",
      seed->reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS ? 'A' : 'D', (unsigned)seed->reg_index);
    kind_text = seed->kind == M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE ? "base" : "type";
    if (used == 0U) {
      int wrote = snprintf(message, message_size, "KNOWN: %s %s=%s", kind_text, reg_name, seed->name);
      if (wrote < 0) return 0;
      used = (size_t)wrote < message_size ? (size_t)wrote : message_size - 1U;
    } else if (used + 4U < message_size) {
      int wrote = snprintf(message + used, message_size - used, "; %s %s=%s", kind_text, reg_name, seed->name);
      if (wrote < 0) return 0;
      used += (size_t)wrote < message_size - used ? (size_t)wrote : message_size - used - 1U;
    }
    if (seed->type_name[0] != '\0' && used + strlen(seed->type_name) + 2U < message_size) {
      message[used++] = ':';
      snprintf(message + used, message_size - used, "%s", seed->type_name);
      used = strlen(message);
    }
  }
  return used != 0U;
}

static void render_asm_policy_register_seed_comment(M68kRenderIRPreview *preview, const M68kAnalysisPolicy *policy,
    size_t section_index, uint32_t offset) {
  char comment[256];
  char line[320];
  if (preview == NULL) return;
  if (!format_policy_register_seed_comment_local(policy, section_index, offset, comment, sizeof(comment))) return;
  snprintf(line, sizeof(line), "    ; %s\n", comment);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static void record_asm_source_failure(M68kRenderIRPreview *preview, uint32_t kind, size_t section_index,
    uint32_t offset, uint32_t aux_offset) {
  if (preview == NULL || preview->asm_source_first_failure_kind != M68K_RENDER_IR_ASM_SOURCE_FAILURE_NONE) return;
  preview->asm_source_first_failure_kind = kind;
  preview->asm_source_first_failure_section = (uint32_t)section_index;
  preview->asm_source_first_failure_offset = offset;
  preview->asm_source_first_failure_aux_offset = aux_offset;
}

static const char *section_base_name(const M68kDecodeSectionIR *section) {
  return section != NULL && section->name != NULL && section->name[0] != '\0' ? section->name : "section";
}

static int section_name_needs_suffix(const M68kDecodeIR *decode, size_t section_index) {
  const char *base_name;
  size_t index;
  if (decode == NULL || section_index >= decode->section_count) return 0;
  base_name = section_base_name(&decode->sections[section_index]);
  if ((decode->sections[section_index].name == NULL || decode->sections[section_index].name[0] == '\0') &&
      decode->section_count > 1U) {
    return 1;
  }
  for (index = 0U; index < decode->section_count; ++index) {
    if (index == section_index) continue;
    if (m68k_ascii_equal_ci(section_base_name(&decode->sections[index]), base_name)) return 1;
  }
  return 0;
}

static const char *rendered_section_name(const M68kDecodeIR *decode, size_t section_index, char *buffer,
    size_t buffer_size) {
  const char *base_name;
  if (buffer != NULL && buffer_size != 0U) buffer[0] = '\0';
  if (decode == NULL || section_index >= decode->section_count) return "section";
  base_name = section_base_name(&decode->sections[section_index]);
  if (!section_name_needs_suffix(decode, section_index)) return base_name;
  if (buffer == NULL || buffer_size == 0U) return base_name;
  snprintf(buffer, buffer_size, "%s_%u", base_name, (unsigned)section_index);
  return buffer;
}

static void render_asm_section_header(M68kRenderIRPreview *preview, const M68kDecodeIR *decode,
    size_t section_index) {
  char line[160];
  char name_buffer[96];
  char kind_buffer[32];
  const M68kDecodeSectionIR *section;
  const char *name;
  uint32_t allocation_size;
  if (preview == NULL || decode == NULL || section_index >= decode->section_count) return;
  section = &decode->sections[section_index];
  name = rendered_section_name(decode, section_index, name_buffer, sizeof(name_buffer));
  if (!m68k_format_section_spec(section->kind, section->platform_mem_type, section->platform_mem_attrs,
      kind_buffer, sizeof(kind_buffer))) {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, section_index, 0U, 0U);
    return;
  }
  allocation_size = section->allocation_size != 0U ? section->allocation_size : section->size;
  if (allocation_size != section->size) {
    snprintf(line, sizeof(line), "    SECTION %s,%s,$%X\n", name, kind_buffer, (unsigned)allocation_size);
  } else {
    snprintf(line, sizeof(line), "    SECTION %s,%s\n", name, kind_buffer);
  }
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static void render_asm_hex_blob_comments(M68kRenderIRPreview *preview, const char *first_prefix,
    const char *append_prefix, const uint8_t *data, uint32_t size) {
  enum { BYTES_PER_COMMENT = 64U };
  uint32_t chunk_start = 0U;
  if (preview == NULL || first_prefix == NULL || append_prefix == NULL || data == NULL || size == 0U) return;
  while (chunk_start < size) {
    uint32_t index;
    uint32_t chunk_end = chunk_start + BYTES_PER_COMMENT;
    if (chunk_end > size) chunk_end = size;
    hash_asm_text(preview, chunk_start == 0U ? first_prefix : append_prefix);
    for (index = chunk_start; index < chunk_end; ++index) {
      char token[3];
      snprintf(token, sizeof(token), "%02X", (unsigned)data[index]);
      hash_asm_text(preview, token);
    }
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
    chunk_start = chunk_end;
  }
}

static void render_asm_platform_header(M68kRenderIRPreview *preview, const M68kObject *object) {
  uint32_t program_flags = 0U;
  uint16_t relocation_flag = 0U;
  uint32_t symbol_table_type = 0U;
  const uint8_t *symbol_table = NULL, *relocation_stream = NULL;
  uint32_t symbol_table_size = 0U, relocation_stream_size = 0U;
  char line[64];
  if (preview == NULL || object == NULL) return;
  if (object->platform_backend_kind != M68K_PLATFORM_BACKEND_ATARI_ST) return;
  if (m68k_atari_st_get_program_flags(object, &program_flags) == 0) {
    snprintf(line, sizeof(line), "    COMMENT HEAD=$%x\n", (unsigned)program_flags);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
  }
  if (m68k_atari_st_get_relocation_flag(object, &relocation_flag) == 0 && relocation_flag != 0U) {
    snprintf(line, sizeof(line), "    COMMENT ATARI_RELOC_FLAG=$%04X\n", (unsigned)relocation_flag);
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
  }
  if (m68k_atari_st_get_raw_symbol_table(object, &symbol_table_type, &symbol_table, &symbol_table_size) == 0) {
    if (symbol_table_type != 0U || symbol_table_size != 0U) {
      snprintf(line, sizeof(line), "    COMMENT ATARI_SYMBOL_TYPE=$%x\n", (unsigned)symbol_table_type);
      hash_asm_text(preview, line);
      ++preview->asm_source_lines;
    }
    if (symbol_table != NULL && symbol_table_size != 0U) {
      render_asm_hex_blob_comments(preview, "    COMMENT ATARI_SYMBOLS=$", "    COMMENT ATARI_SYMBOLS+=$",
        symbol_table, symbol_table_size);
    }
  }
  if (m68k_atari_st_get_raw_relocation_stream(object, &relocation_stream, &relocation_stream_size) == 0 &&
      relocation_stream != NULL && relocation_stream_size != 0U) {
    render_asm_hex_blob_comments(preview, "    COMMENT ATARI_RELOC=$", "    COMMENT ATARI_RELOC+=$",
      relocation_stream, relocation_stream_size);
  }
}

static void render_asm_relocation_expr(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kFact *fact) {
  char line[256];
  char name[64];
  char value[32];
  char structured_comment[128];
  const char *directive;
  uint32_t numeric_value;
  if (preview == NULL || lookup == NULL || fact == NULL) return;
  if (fact->size == 4U) directive = "dc.l";
  else if (fact->size == 2U) directive = "dc.w";
  else directive = "dc.b";
  format_lookup_asm_label(lookup, name, sizeof(name), fact->target_section_index, fact->target_offset);
  if (!lookup_has_renderable_label(lookup, fact->target_section_index, fact->target_offset)) {
    numeric_value = fact->target_addend >= 0 && fact->target_addend <= UINT32_MAX
      ? (uint32_t)fact->target_addend : fact->target_offset;
    format_numeric_value(value, sizeof(value), fact->size, numeric_value);
    if (fact->platform_record_kind == AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32) {
      const char *reason = lookup_offset_is_inside_relocation_payload(lookup, fact->target_section_index,
        fact->target_offset) ? "is inside another relocation payload" : "has no renderable statement boundary";
      snprintf(line, sizeof(line),
        "\t%s %s\t; facts_v2 HUNK_RELOC32 numeric: target label %s %s; left numeric\n",
        directive, value, name, reason);
      ++preview->asm_source_lossy_numeric_hunk_relocations;
    } else {
      snprintf(line, sizeof(line),
        "\t%s %s\t; facts_v2 relocation numeric: target label %s is not renderable\n",
        directive, value, name);
      ++preview->asm_source_instruction_relocation_failures;
      record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RELOCATION,
        fact->section_index, fact->offset, fact->target_offset);
    }
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
    return;
  }
  if (structured_data_item_comment(lookup_structured_data_item_at_offset(lookup, fact->section_index, fact->offset),
      structured_comment, sizeof(structured_comment))) {
    snprintf(line, sizeof(line), "\t%s %s\t; %s\n", directive, name, structured_comment);
  } else {
    snprintf(line, sizeof(line), "\t%s %s\n", directive, name);
  }
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  ++preview->asm_source_relocation_exprs;
}

static void render_asm_dc_b(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t size, const char *comment) {
  uint32_t cursor = 0U;
  if (preview == NULL || data == NULL) return;
  while (cursor < size) {
    uint32_t line_count = size - cursor;
    uint32_t index;
    if (line_count > 16U) line_count = 16U;
    hash_asm_text(preview, "\tdc.b ");
    for (index = 0U; index < line_count; ++index) {
      char token[8];
      if (index != 0U) hash_asm_text(preview, ",");
      snprintf(token, sizeof(token), "$%02X", (unsigned)data[offset + cursor + index]);
      hash_asm_text(preview, token);
    }
    if (comment != NULL && comment[0] != '\0') {
      hash_asm_text(preview, "\t; ");
      hash_asm_text(preview, comment);
    }
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
    cursor += line_count;
  }
}

static int byte_is_quoted_string_safe(uint8_t value) {
  return value >= 0x20U && value <= 0x7eU && value != '"' && value != '\\';
}

static void render_asm_dc_b_string(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t size, const char *comment) {
  uint32_t cursor;
  int wrote = 0;
  if (preview == NULL || data == NULL || size == 0U) return;
  hash_asm_text(preview, "\tdc.b ");
  cursor = 0U;
  while (cursor < size) {
    if (byte_is_quoted_string_safe(data[offset + cursor])) {
      char byte_text[2];
      if (wrote) hash_asm_text(preview, ",");
      hash_asm_text(preview, "\"");
      while (cursor < size && byte_is_quoted_string_safe(data[offset + cursor])) {
        byte_text[0] = (char)data[offset + cursor];
        byte_text[1] = '\0';
        hash_asm_text(preview, byte_text);
        ++cursor;
      }
      hash_asm_text(preview, "\"");
      wrote = 1;
    } else {
      char token[8];
      if (wrote) hash_asm_text(preview, ",");
      snprintf(token, sizeof(token), "$%02X", (unsigned)data[offset + cursor]);
      hash_asm_text(preview, token);
      ++cursor;
      wrote = 1;
    }
  }
  if (comment != NULL && comment[0] != '\0') {
    hash_asm_text(preview, "\t; ");
    hash_asm_text(preview, comment);
  }
  hash_asm_text(preview, "\n");
  ++preview->asm_source_lines;
}

static void render_asm_ds_b(M68kRenderIRPreview *preview, uint32_t size, const char *comment) {
  char line[96];
  if (preview == NULL || size == 0U) return;
  if (comment != NULL && comment[0] != '\0')
    snprintf(line, sizeof(line), "\tDS.B $%X\t; %s\n", (unsigned)size, comment);
  else
    snprintf(line, sizeof(line), "\tDS.B $%X\n", (unsigned)size);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static void render_asm_dc_w_values(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t size, const char *comment) {
  uint32_t cursor = 0U;
  if (preview == NULL || data == NULL || size == 0U) return;
  while (cursor + 2U <= size) {
    uint32_t line_count = (size - cursor) / 2U;
    uint32_t index;
    if (line_count > 8U) line_count = 8U;
    hash_asm_text(preview, "\tdc.w ");
    for (index = 0U; index < line_count; ++index) {
      char token[16];
      if (index != 0U) hash_asm_text(preview, ",");
      snprintf(token, sizeof(token), "$%04X", (unsigned)m68k_read_u16be(data + offset + cursor + (index * 2U)));
      hash_asm_text(preview, token);
    }
    if (comment != NULL && comment[0] != '\0') {
      hash_asm_text(preview, "\t; ");
      hash_asm_text(preview, comment);
    }
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
    cursor += line_count * 2U;
  }
  if (cursor < size) render_asm_dc_b(preview, data, offset + cursor, size - cursor, comment);
}

static void render_asm_dc_l_values(M68kRenderIRPreview *preview, const uint8_t *data, uint32_t offset,
    uint32_t size, const char *comment) {
  uint32_t cursor = 0U;
  if (preview == NULL || data == NULL || size == 0U) return;
  while (cursor + 4U <= size) {
    uint32_t line_count = (size - cursor) / 4U;
    uint32_t index;
    if (line_count > 4U) line_count = 4U;
    hash_asm_text(preview, "\tdc.l ");
    for (index = 0U; index < line_count; ++index) {
      char token[16];
      if (index != 0U) hash_asm_text(preview, ",");
      snprintf(token, sizeof(token), "$%08X", (unsigned)m68k_read_u32be(data + offset + cursor + (index * 4U)));
      hash_asm_text(preview, token);
    }
    if (comment != NULL && comment[0] != '\0') {
      hash_asm_text(preview, "\t; ");
      hash_asm_text(preview, comment);
    }
    hash_asm_text(preview, "\n");
    ++preview->asm_source_lines;
    cursor += line_count * 4U;
  }
  if (cursor < size) render_asm_dc_b(preview, data, offset + cursor, size - cursor, comment);
}

static void render_asm_dc_symbol_expr(M68kRenderIRPreview *preview, uint32_t size, const char *expr,
    const char *comment) {
  const char *directive = size == 4U ? "dc.l" : size == 2U ? "dc.w" : "dc.b";
  char line[256];
  if (preview == NULL || expr == NULL || expr[0] == '\0') return;
  if (comment != NULL && comment[0] != '\0')
    snprintf(line, sizeof(line), "\t%s %s\t; %s\n", directive, expr, comment);
  else
    snprintf(line, sizeof(line), "\t%s %s\n", directive, expr);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
}

static void render_asm_structured_data_item(M68kRenderIRPreview *preview, const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item) {
  char comment[128];
  char expr[96];
  const char *comment_text;
  uint32_t available;
  if (preview == NULL || section == NULL || item == NULL || item->size == 0U) return;
  if (!render_asm_includes_for_structured_data_item(preview, item)) return;
  comment[0] = '\0';
  comment_text = structured_data_item_render_comment(section, item, comment, sizeof(comment)) ? comment : NULL;
  if (item->offset >= section->size || section->data == NULL) {
    render_asm_ds_b(preview, item->size, comment_text);
    return;
  }
  available = section->size - item->offset;
  if (available > item->size) available = item->size;
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_STRING && available == item->size) {
    render_asm_dc_b_string(preview, section->data, item->offset, available, comment_text);
    return;
  }
  if (available == item->size &&
      structured_data_item_symbolic_operand_expr(section, item, expr, sizeof(expr))) {
    if (!render_asm_include_for_symbol_expr(preview, expr)) {
      ++preview->asm_source_instruction_render_failures;
      record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER,
        item->has_section_index ? item->section_index : 0U, item->offset, 0U);
      return;
    }
    render_asm_dc_symbol_expr(preview, item->size, expr, comment_text);
    return;
  }
  if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS && available >= 4U) {
    render_asm_dc_l_values(preview, section->data, item->offset, available, comment_text);
  } else if (item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS && available >= 2U) {
    render_asm_dc_w_values(preview, section->data, item->offset, available, comment_text);
  } else {
    render_asm_dc_b(preview, section->data, item->offset, available, comment_text);
  }
  if (available < item->size) render_asm_ds_b(preview, item->size - available, comment_text);
}

static const M68kDecodeCandidate *find_candidate_at_offset_local(const M68kDecodeSectionIR *section,
    uint32_t offset) {
  size_t lo = 0U;
  size_t hi;
  if (section == NULL) return NULL;
  hi = section->candidate_count;
  while (lo < hi) {
    size_t mid = lo + ((hi - lo) / 2U);
    uint32_t candidate_offset = section->candidates[mid].offset;
    if (candidate_offset == offset) return &section->candidates[mid];
    if (candidate_offset < offset) lo = mid + 1U;
    else hi = mid;
  }
  return NULL;
}

static int operand_uses_single_word_extension_local(const M68kAsmOperandValue *operand) {
  if (operand == NULL) return 0;
  return (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
    (operand->ea_mode == 5U || (operand->ea_mode == 7U && operand->ea_reg == 0U) ||
      (operand->ea_mode == 7U && operand->ea_reg == 2U));
}

static int operand_uses_long_address_extension_local(const M68kAsmOperandValue *operand) {
  if (operand == NULL) return 0;
  return (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
    operand->ea_mode == 7U && operand->ea_reg == 1U;
}

static int operand_uses_immediate_extension_local(const M68kAsmOperandValue *operand) {
  if (operand == NULL) return 0;
  return ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->ea_mode == 7U && operand->ea_reg == 4U) || operand->kind == M68K_ASM_OPERAND_IMM;
}

static M68kAsmOperandValue normalized_layout_operand(const M68kDecodeCandidate *candidate, size_t operand_index) {
  M68kAsmOperandValue operand;
  memset(&operand, 0, sizeof(operand));
  if (candidate == NULL || operand_index >= candidate->operand_count) return operand;
  operand = candidate->operands[operand_index];
  operand.kind = candidate->operand_kinds[operand_index];
  switch (candidate->operand_kinds[operand_index]) {
  case M68K_ASM_OPERAND_ABSL:
    operand.kind = M68K_ASM_OPERAND_EA;
    operand.ea_mode = 7U;
    operand.ea_reg = 1U;
    break;
  case M68K_ASM_OPERAND_IND:
    operand.kind = M68K_ASM_OPERAND_EA;
    operand.ea_mode = 2U;
    break;
  case M68K_ASM_OPERAND_POSTINC:
    operand.kind = M68K_ASM_OPERAND_EA;
    operand.ea_mode = 3U;
    break;
  case M68K_ASM_OPERAND_PREDEC:
    operand.kind = M68K_ASM_OPERAND_EA;
    operand.ea_mode = 4U;
    break;
  default:
    break;
  }
  return operand;
}

static size_t relocation_extension_word_count(uint16_t asm_form_index, uint8_t extension_kind,
    const M68kAsmOperandValue *operand, char size_suffix) {
  if (operand == NULL) return 0U;
  switch (extension_kind) {
  case M68K_ASM_EXTENSION_EA_SINGLE_WORD:
    return operand_uses_single_word_extension_local(operand) ? 1U : 0U;
  case M68K_ASM_EXTENSION_EA_LONG_ADDRESS:
    return operand_uses_long_address_extension_local(operand) ? 2U : 0U;
  case M68K_ASM_EXTENSION_EA_IMMEDIATE:
    return operand_uses_immediate_extension_local(operand) ? (size_suffix == 'l' ? 2U : 1U) : 0U;
  case M68K_ASM_EXTENSION_EA_INDEX:
    if (!((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
        (operand->ea_mode == 6U || (operand->ea_mode == 7U && operand->ea_reg == 3U)))) {
      return 0U;
    }
    return m68k_asm_operand_extension_word_count(asm_form_index, operand, size_suffix);
  case M68K_ASM_EXTENSION_LABEL_DISP16_IF_ZERO:
    return size_suffix == 'b' ? 0U : 1U;
  case M68K_ASM_EXTENSION_LABEL_DISP16_ALWAYS:
  case M68K_ASM_EXTENSION_DISP16_ALWAYS:
    return 1U;
  default:
    return 0U;
  }
}

static char candidate_effective_size_suffix(const M68kDecodeCandidate *candidate) {
  M68kAsmOperandValue layout_operands[M68K_DECODE_IR_MAX_OPERANDS];
  const M68kAsmFormDef *form;
  char size_suffix;
  size_t index;
  if (candidate == NULL || candidate->asm_form_index >= M68K_ASM_FORM_SLOT_COUNT)
    return candidate != NULL ? candidate->size_suffix : '\0';
  form = &g_m68k_asm_forms[candidate->asm_form_index];
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) return candidate->size_suffix;
  for (index = 0U; index < candidate->operand_count; ++index)
    layout_operands[index] = normalized_layout_operand(candidate, index);
  size_suffix = m68k_asm_choose_size_suffix(form, layout_operands, candidate->operand_count,
    candidate->size_suffix);
  return size_suffix != '\0' ? size_suffix : candidate->size_suffix;
}

typedef struct ByteImmediateExtensionSite {
  size_t byte_offset;
  uint8_t operand_index;
} ByteImmediateExtensionSite;

static uint16_t instruction_asm_form_index_local(const M68kInstructionIR *instruction,
    M68kAsmOperandValue *out_operands, size_t max_operands) {
  size_t operand_index;
  uint16_t asm_form_index;
  if (instruction == NULL || out_operands == NULL || max_operands < instruction->operand_count)
    return M68K_ASM_FORM_NONE;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index)
    out_operands[operand_index] = instruction->operands[operand_index].value;
  asm_form_index = instruction->asm_form_index;
  if (asm_form_index < M68K_ASM_FORM_SLOT_COUNT &&
      g_m68k_asm_forms[asm_form_index].mnemonic_id != M68K_ASM_MNEMONIC_NONE) {
    return asm_form_index;
  }
  return m68k_asm_form_index_for_operands_id(instruction->mnemonic_id, out_operands,
    instruction->operand_count, instruction->size_suffix, instruction->target_cpu);
}

static size_t collect_byte_immediate_extension_sites(const M68kInstructionIR *instruction,
    ByteImmediateExtensionSite *out_sites, size_t max_sites) {
  M68kAsmOperandValue operands[4];
  uint16_t asm_form_index;
  const M68kAsmFormDef *form;
  char size_suffix;
  size_t site_count = 0U;
  size_t word_index;
  size_t extension_index;
  if (instruction == NULL || instruction->operand_count > 4U) return 0U;
  asm_form_index = instruction_asm_form_index_local(instruction, operands, sizeof(operands) / sizeof(operands[0]));
  if (asm_form_index >= M68K_ASM_FORM_SLOT_COUNT) return 0U;
  form = &g_m68k_asm_forms[asm_form_index];
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) return 0U;
  size_suffix = m68k_asm_choose_size_suffix(form, operands, instruction->operand_count, instruction->size_suffix);
  if (size_suffix == '\0') size_suffix = instruction->size_suffix;
  word_index = 1U + form->bound_word_count;
  for (extension_index = 0U; extension_index < form->extension_count; ++extension_index) {
    const M68kAsmExtensionDef *extension = &g_m68k_asm_extensions[form->extension_start + extension_index];
    const M68kAsmOperandValue *operand;
    if (extension->operand_index >= instruction->operand_count) continue;
    operand = &operands[extension->operand_index];
    switch (extension->kind) {
    case M68K_ASM_EXTENSION_EA_SINGLE_WORD:
      if (operand_uses_single_word_extension_local(operand)) ++word_index;
      break;
    case M68K_ASM_EXTENSION_EA_LONG_ADDRESS:
      if (operand_uses_long_address_extension_local(operand)) word_index += 2U;
      break;
    case M68K_ASM_EXTENSION_EA_IMMEDIATE:
      if (operand_uses_immediate_extension_local(operand)) {
        if (size_suffix == 'b') {
          if (site_count < max_sites) {
            out_sites[site_count].byte_offset = word_index * 2U;
            out_sites[site_count].operand_index = extension->operand_index;
          }
          ++site_count;
        }
        word_index += size_suffix == 'l' ? 2U : 1U;
      }
      break;
    case M68K_ASM_EXTENSION_EA_INDEX:
      word_index += m68k_asm_operand_extension_word_count(asm_form_index, operand, size_suffix);
      break;
    case M68K_ASM_EXTENSION_LABEL_DISP16_IF_ZERO:
    case M68K_ASM_EXTENSION_LABEL_DISP16_ALWAYS:
    case M68K_ASM_EXTENSION_DISP16_ALWAYS:
      ++word_index;
      break;
    default:
      break;
    }
  }
  return site_count;
}

static void apply_exact_byte_immediate_render_values(M68kInstructionIR *instruction, const uint8_t *raw_bytes,
    size_t raw_size) {
  ByteImmediateExtensionSite sites[4];
  size_t site_count;
  size_t site_index;
  if (instruction == NULL || raw_bytes == NULL || raw_size == 0U) return;
  site_count = collect_byte_immediate_extension_sites(instruction, sites, sizeof(sites) / sizeof(sites[0]));
  for (site_index = 0U; site_index < site_count; ++site_index) {
    uint8_t operand_index = sites[site_index].operand_index;
    uint16_t raw_word;
    if (sites[site_index].byte_offset + 1U >= raw_size) continue;
    if (operand_index >= instruction->operand_count) continue;
    raw_word = m68k_read_u16be(raw_bytes + sites[site_index].byte_offset);
    if ((raw_word & 0xFF00U) == 0U) continue;
    if ((raw_word & 0x00FFU) != (instruction->operands[operand_index].value.value & 0xFFU)) continue;
    instruction->operands[operand_index].has_exact_render_value = 1U;
    instruction->operands[operand_index].exact_render_value = raw_word;
  }
}

static int encoded_bytes_match_with_exact_byte_immediates(const M68kInstructionIR *instruction,
    const uint8_t *encoded_bytes, const uint8_t *raw_bytes, size_t raw_size) {
  ByteImmediateExtensionSite sites[4];
  size_t site_count;
  size_t byte_index;
  if (instruction == NULL || encoded_bytes == NULL || raw_bytes == NULL) return 0;
  if (memcmp(encoded_bytes, raw_bytes, raw_size) == 0) return 1;
  site_count = collect_byte_immediate_extension_sites(instruction, sites, sizeof(sites) / sizeof(sites[0]));
  for (byte_index = 0U; byte_index < raw_size; ++byte_index) {
    size_t site_index;
    int allowed_exact_high_byte = 0;
    if (encoded_bytes[byte_index] == raw_bytes[byte_index]) continue;
    for (site_index = 0U; site_index < site_count; ++site_index) {
      uint8_t operand_index = sites[site_index].operand_index;
      uint16_t raw_word;
      uint16_t encoded_word;
      if (sites[site_index].byte_offset != byte_index) continue;
      if (sites[site_index].byte_offset + 1U >= raw_size) continue;
      if (operand_index >= instruction->operand_count) continue;
      if (instruction->operands[operand_index].has_exact_render_value == 0U) continue;
      raw_word = m68k_read_u16be(raw_bytes + sites[site_index].byte_offset);
      encoded_word = m68k_read_u16be(encoded_bytes + sites[site_index].byte_offset);
      if ((uint16_t)instruction->operands[operand_index].exact_render_value == raw_word &&
          (encoded_word & 0x00FFU) == (raw_word & 0x00FFU)) {
        allowed_exact_high_byte = 1;
        break;
      }
    }
    if (!allowed_exact_high_byte) return 0;
  }
  return 1;
}

static int instruction_has_symbolic_or_relative_text(const M68kInstructionIR *instruction) {
  size_t operand_index;
  if (instruction == NULL) return 1;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (operand->kind == M68K_ASM_OPERAND_LABEL) return 1;
    if (operand->symbol_ref.has_name != 0U || operand->symbol_ref.has_symbol != 0 ||
        operand->symbol_ref.has_symbolic_addend != 0U) {
      return 1;
    }
  }
  return 0;
}

static int operand_is_address_register_local(const M68kOperandIR *operand, uint8_t reg_index) {
  if (operand == NULL) return 0;
  return operand->kind == M68K_ASM_OPERAND_AN && operand->value.reg == reg_index;
}

static int operand_is_absolute_address_local(const M68kOperandIR *operand, uint32_t address) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_ABSL) return operand->value.value == address;
  if (operand->kind != M68K_ASM_OPERAND_EA) return 0;
  return operand->value.value == address &&
    operand->value.ea_mode == 7U && (operand->value.ea_reg == 0U || operand->value.ea_reg == 1U);
}

static int operand_absolute_offset_local(const M68kOperandIR *operand, uint32_t *out_offset) {
  if (operand == NULL || out_offset == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_ABSL) {
    *out_offset = operand->value.value;
    return 1;
  }
  if (operand->kind != M68K_ASM_OPERAND_EA) return 0;
  if (operand->value.ea_mode == 7U && (operand->value.ea_reg == 0U || operand->value.ea_reg == 1U)) {
    *out_offset = operand->value.value;
    return 1;
  }
  return 0;
}

static int reglist_contains_address_register_local(const M68kOperandIR *operand, uint8_t reg_index) {
  uint32_t mask;
  if (operand == NULL || operand->kind != M68K_ASM_OPERAND_REGLIST || reg_index >= 8U) return 0;
  mask = operand->value.value;
  return (mask & (1UL << (8U + reg_index))) != 0U;
}

static int platform_state_operand_is_app_base(const M68kRenderPlatformState *state,
    const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  if (state == NULL || operand == NULL) return 0;
  if (operand_is_data_register_local(operand, &reg) && reg < 8U && state->data_app_base_known[reg]) return 1;
  if (operand_address_register_index_local(operand, &reg) && reg < 8U && state->address_app_base_known[reg])
    return 1;
  return 0;
}

static void platform_state_update_app_base_after_instruction(M68kRenderPlatformState *state,
    const M68kInstructionIR *instruction) {
  uint8_t dest_reg = 0U;
  int source_is_app_base;
  if (state == NULL || instruction == NULL) return;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_RTS ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_RTE ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_JMP) {
    platform_state_clear_all_app_bases(state);
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    if (instruction->operand_count >= 2U && instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
      for (dest_reg = 0U; dest_reg < 8U; ++dest_reg) {
        if (reglist_contains_data_register_local(&instruction->operands[1], dest_reg))
          platform_state_clear_data_app_base(state, dest_reg);
        if (reglist_contains_address_register_local(&instruction->operands[1], dest_reg))
          platform_state_clear_address_app_base(state, dest_reg);
      }
    }
    return;
  }
  if (instruction->operand_count < 2U) return;
  source_is_app_base = platform_state_operand_is_app_base(state, &instruction->operands[0]);
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) {
    const M68kOperandIR *dest = &instruction->operands[instruction->operand_count - 1U];
    if (operand_is_data_register_local(dest, &dest_reg)) {
      if (source_is_app_base) platform_state_set_register_app_base(state, M68K_ANALYSIS_REGISTER_DATA, dest_reg);
      else platform_state_clear_data_app_base(state, dest_reg);
    } else if (operand_address_register_index_local(dest, &dest_reg)) {
      if (source_is_app_base) platform_state_set_register_app_base(state, M68K_ANALYSIS_REGISTER_ADDRESS, dest_reg);
      else platform_state_clear_address_app_base(state, dest_reg);
    }
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
      operand_address_register_index_local(&instruction->operands[instruction->operand_count - 1U], &dest_reg)) {
    platform_state_clear_address_app_base(state, dest_reg);
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ &&
      operand_is_data_register_local(&instruction->operands[instruction->operand_count - 1U], &dest_reg)) {
    platform_state_clear_data_app_base(state, dest_reg);
  }
}

static void platform_state_update_after_instruction(M68kRenderPlatformState *state, const M68kRenderLookup *lookup,
    const M68kInstructionIR *instruction) {
  if (state == NULL || instruction == NULL) return;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_RTS ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_RTE ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_JMP) {
    platform_state_clear_register(state, 6U);
    platform_state_update_app_base_after_instruction(state, instruction);
    return;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    if (instruction->operand_count >= 2U && reglist_contains_address_register_local(&instruction->operands[1], 6U))
      platform_state_clear_register(state, 6U);
    platform_state_update_app_base_after_instruction(state, instruction);
    return;
  }
  if (instruction->operand_count >= 2U && operand_is_address_register_local(&instruction->operands[1], 6U)) {
    uint32_t absolute_offset = 0U;
    const char *library_name = instruction->operands[0].symbol_ref.has_name
      ? amiga_library_name_from_base_symbol_name(instruction->operands[0].symbol_ref.name)
      : NULL;
    if (library_name == NULL && instruction->operands[0].symbol_ref.has_section &&
        operand_absolute_offset_local(&instruction->operands[0], &absolute_offset)) {
      library_name = lookup_global_base_slot_library(lookup, instruction->operands[0].symbol_ref.section_index,
        absolute_offset);
    }
    if (library_name == NULL) {
      uint8_t base_reg = 0U;
      int16_t displacement = 0;
      if (operand_is_address_displacement_local(&instruction->operands[0], &base_reg, &displacement) &&
          state->address_base_known[base_reg]) {
        library_name = lookup_base_field_slot_library(lookup, state->address_base_library[base_reg], displacement);
      }
    }
    if (library_name == NULL && instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) {
      uint8_t base_reg = 0U;
      int16_t displacement = 0;
      if (!state->address_base_known[6U] &&
          operand_is_address_displacement_local(&instruction->operands[0], &base_reg, &displacement) &&
          base_reg == 6U) {
        library_name = lookup_app_base_field_slot_library(lookup, displacement);
      }
    }
    if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA &&
        library_name != NULL) {
      platform_state_set_register_library(state, 6U, library_name);
    } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA &&
        operand_is_absolute_address_local(&instruction->operands[0], 4U)) {
      platform_state_set_register_library(state, 6U, amiga_os_exec_base_library_name());
    } else {
      platform_state_clear_register(state, 6U);
    }
  }
  platform_state_update_app_base_after_instruction(state, instruction);
}

static const AmigaOsLibraryVectorInfo *attach_amiga_lvo_symbol_if_known(const M68kRenderPlatformState *state,
    M68kInstructionIR *instruction) {
  M68kOperandIR *operand;
  const char *base_name;
  const AmigaOsLibraryVectorInfo *vector;
  const char *symbol_name;
  int16_t displacement;
  if (state == NULL || instruction == NULL) return NULL;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_JSR &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_JMP)
    return NULL;
  if (instruction->operand_count != 1U) return NULL;
  if (!state->address_base_known[6]) return NULL;
  operand = &instruction->operands[0];
  if (operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_mode != 5U || operand->value.ea_reg != 6U)
    return NULL;
  displacement = (int16_t)(operand->value.value & 0xFFFFU);
  if (displacement >= 0) return NULL;
  base_name = amiga_os_find_library_base_name(state->address_base_library[6]);
  if (base_name == NULL) return NULL;
  vector = amiga_os_find_library_vector(base_name, displacement);
  if (vector == NULL) return NULL;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, vector->lvo_symbol_id);
  if (symbol_name == NULL || symbol_name[0] == '\0') return NULL;
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
  operand->symbol_ref.has_name = 1U;
  operand->symbol_ref.name_is_generated = 0U;
  operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
  operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
  snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol_name);
  return vector;
}

static int attach_amiga_app_base_slot_symbols(const M68kRenderLookup *lookup,
    const M68kRenderPlatformState *state, M68kInstructionIR *instruction) {
  size_t operand_index;
  int attached = 0;
  if (lookup == NULL || state == NULL || instruction == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    uint8_t base_reg = 0U;
    int16_t displacement = 0;
    char symbol_name[64];
    if (operand->symbol_ref.has_name != 0U) continue;
    if (!operand_is_address_displacement_local(operand, &base_reg, &displacement)) continue;
    if (state->address_app_base_known[base_reg]) {
      if (!lookup_app_base_field_slot_symbol_name(lookup, displacement, symbol_name, sizeof(symbol_name))) continue;
    } else if (state->address_base_known[base_reg]) {
      if (!library_base_can_use_app_extension_slot(state->address_base_library[base_reg], displacement) ||
          !lookup_app_base_field_slot_symbol_name(lookup, displacement, symbol_name, sizeof(symbol_name))) {
        if (!lookup_base_field_slot_symbol_name(lookup, state->address_base_library[base_reg], displacement,
            symbol_name, sizeof(symbol_name))) {
          continue;
        }
      }
    } else if (base_reg == 6U) {
      if (!lookup_app_base_field_slot_symbol_name(lookup, displacement, symbol_name, sizeof(symbol_name))) continue;
    } else {
      continue;
    }
    m68k_ir_symbol_ref_init(&operand->symbol_ref);
    operand->symbol_ref.has_name = 1U;
    operand->symbol_ref.name_is_generated = 0U;
    operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
    snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol_name);
    attached = 1;
  }
  return attached;
}

static int attach_amiga_typed_struct_field_symbols(const M68kRenderTypedState *typed_state,
    M68kInstructionIR *instruction) {
  size_t operand_index;
  int attached = 0;
  if (typed_state == NULL || instruction == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    uint8_t base_reg = 0U;
    int16_t displacement = 0;
    const AmigaOsCallOutputInfo *output;
    const AmigaOsStructFieldInfo *field;
    const char *field_name;
    if (operand->symbol_ref.has_name != 0U) continue;
    if (!operand_is_address_displacement_local(operand, &base_reg, &displacement)) continue;
    if (base_reg >= 8U || !typed_state->addr_regs[base_reg].known) continue;
    output = typed_state->addr_regs[base_reg].output;
    if (output == NULL || output->struct_id == AMIGA_OS_STRUCT_ID_NONE) continue;
    field = amiga_os_find_struct_field_by_struct_id(output->struct_id, displacement);
    if (field == NULL) continue;
    field_name = amiga_os_name(M68K_PLATFORM_NAME_FIELD, field->field_id);
    if (field_name == NULL || field_name[0] == '\0') continue;
    m68k_ir_symbol_ref_init(&operand->symbol_ref);
    operand->symbol_ref.has_name = 1U;
    operand->symbol_ref.name_is_generated = 0U;
    operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
    snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", field_name);
    attached = 1;
  }
  return attached;
}

static int render_asm_include_for_instruction_platform_symbols(M68kRenderIRPreview *preview,
    const M68kInstructionIR *instruction) {
  size_t operand_index;
  if (instruction == NULL) return 1;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (operand->symbol_ref.has_name == 0U ||
        operand->symbol_ref.name_provenance != M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA) {
      continue;
    }
    if (!render_asm_include_for_amiga_symbol(preview, operand->symbol_ref.name)) return 0;
  }
  return 1;
}

static int operand_is_immediate_value_local(const M68kOperandIR *operand, uint32_t *out_value) {
  if (out_value != NULL) *out_value = 0U;
  if (operand == NULL || out_value == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_IMM) {
    *out_value = operand->value.value;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 7U && operand->value.ea_reg == 4U) {
    *out_value = operand->value.value;
    return 1;
  }
  return 0;
}

static int instruction_loads_d0_immediate(const M68kInstructionIR *instruction, int16_t *out_value) {
  int32_t value;
  uint32_t immediate = 0U;
  uint8_t dest_reg = 0U;
  if (out_value != NULL) *out_value = 0;
  if (instruction == NULL || out_value == NULL || instruction->operand_count != 2U) return 0;
  if (!operand_is_immediate_value_local(&instruction->operands[0], &immediate)) return 0;
  if (!operand_is_data_register_local(&instruction->operands[1], &dest_reg) || dest_reg != 0U) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ) {
    value = (int8_t)(immediate & 0xFFU);
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE) {
    value = (int32_t)immediate;
  } else {
    return 0;
  }
  if ((value < INT16_MIN || value > INT16_MAX) && instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE &&
      ((immediate & 0x8000U) != 0U)) {
    value = (int16_t)(immediate & 0xFFFFU);
  }
  if (value < INT16_MIN || value > INT16_MAX) return 0;
  *out_value = (int16_t)value;
  return 1;
}

static int instruction_writes_d0_unknown_for_state(const M68kInstructionIR *instruction) {
  const M68kOperandIR *dest;
  uint8_t reg = 0U;
  if (instruction == NULL) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_JSR ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_BSR) {
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    return instruction->operand_count >= 2U && reglist_contains_data_register_local(&instruction->operands[1], 0U);
  }
  if (instruction->operand_count == 0U) return 0;
  dest = &instruction->operands[instruction->operand_count - 1U];
  return operand_is_data_register_local(dest, &reg) && reg == 0U;
}

static void platform_state_update_d0_lvo_after_instruction(M68kRenderPlatformState *state,
    const M68kInstructionIR *instruction) {
  int16_t lvo = 0;
  if (state == NULL || instruction == NULL) return;
  if (instruction_loads_d0_immediate(instruction, &lvo) && lvo < 0) {
    state->d0_lvo_known = 1U;
    state->d0_lvo = lvo;
    return;
  }
  if (instruction_writes_d0_unknown_for_state(instruction)) platform_state_clear_d0_lvo(state);
}

static const AmigaOsLibraryVectorInfo *attach_amiga_lvo_immediate_if_known(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  uint32_t next_offset;
  uint32_t wrapper_offset = 0U;
  int16_t lvo = 0;
  const M68kDecodeCandidate *next_candidate;
  const char *library_name;
  const char *base_name;
  const AmigaOsLibraryVectorInfo *vector;
  const char *symbol_name;
  M68kOperandIR *operand;
  if (lookup == NULL || section == NULL || accepted_start == NULL || candidate == NULL || instruction == NULL)
    return NULL;
  if (!instruction_loads_d0_immediate(instruction, &lvo)) return NULL;
  if (lvo >= 0) return NULL;
  next_offset = candidate->offset + candidate->byte_count;
  if (!accepted_start_at(section, accepted_start, next_offset)) return NULL;
  next_candidate = find_candidate_at_offset_local(section, next_offset);
  if (!candidate_direct_same_section_target(next_candidate, section->section_index, &wrapper_offset)) return NULL;
  library_name = lookup_indexed_vector_wrapper_library(lookup, section->section_index, wrapper_offset);
  if (library_name == NULL) return NULL;
  base_name = amiga_os_find_library_base_name(library_name);
  if (base_name == NULL) return NULL;
  vector = amiga_os_find_library_vector(base_name, lvo);
  if (vector == NULL) return NULL;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, vector->lvo_symbol_id);
  if (symbol_name == NULL || symbol_name[0] == '\0') return NULL;
  operand = &instruction->operands[0];
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
  operand->symbol_ref.has_name = 1U;
  operand->symbol_ref.name_is_generated = 0U;
  operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
  operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
  snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", symbol_name);
  return vector;
}

static const AmigaOsLibraryVectorInfo *resolve_amiga_indexed_wrapper_call_vector(
    const M68kRenderLookup *lookup, const M68kRenderPlatformState *state, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate) {
  uint32_t wrapper_offset = 0U;
  const char *library_name;
  const char *base_name;
  if (lookup == NULL || state == NULL || section == NULL || candidate == NULL) return NULL;
  if (!state->d0_lvo_known) return NULL;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_BSR &&
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR) {
    return NULL;
  }
  size_t wrapper_section_index = 0U;
  if (!candidate_direct_control_target(lookup, section->section_index, candidate, &wrapper_section_index,
      &wrapper_offset)) {
    return NULL;
  }
  library_name = lookup_indexed_vector_wrapper_library(lookup, wrapper_section_index, wrapper_offset);
  if (library_name == NULL || library_name[0] == '\0') return NULL;
  base_name = amiga_os_find_library_base_name(library_name);
  if (base_name == NULL || base_name[0] == '\0') return NULL;
  return amiga_os_find_library_vector(base_name, state->d0_lvo);
}

static int format_amiga_local_wrapper_call_comment(const AmigaOsLibraryVectorInfo *vector,
    char *comment, size_t comment_size) {
  const char *base_name;
  const char *symbol_name;
  if (comment == NULL || comment_size == 0U) return 0;
  comment[0] = '\0';
  if (vector == NULL) return 0;
  base_name = amiga_os_name(M68K_PLATFORM_NAME_BASE, vector->base_id);
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, vector->lvo_symbol_id);
  if (base_name == NULL || base_name[0] == '\0' || symbol_name == NULL || symbol_name[0] == '\0') return 0;
  snprintf(comment, comment_size, "KNOWN: %s %s via local wrapper", base_name, symbol_name);
  return 1;
}

static int format_amiga_local_helper_call_comment(const AmigaOsLibraryVectorInfo *vector,
    char *comment, size_t comment_size) {
  const char *base_name;
  const char *symbol_name;
  if (comment == NULL || comment_size == 0U) return 0;
  comment[0] = '\0';
  if (vector == NULL) return 0;
  base_name = amiga_os_name(M68K_PLATFORM_NAME_BASE, vector->base_id);
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, vector->lvo_symbol_id);
  if (base_name == NULL || base_name[0] == '\0' || symbol_name == NULL || symbol_name[0] == '\0') return 0;
  snprintf(comment, comment_size, "KNOWN: local helper uses %s %s", base_name, symbol_name);
  return 1;
}

static int rendered_text_reencodes_original_bytes(const char *text, const M68kInstructionIR *source_instruction,
    const M68kInstructionIR *render_instruction, const uint8_t *raw_bytes, size_t raw_size) {
  M68kInstructionIR parsed;
  M68kDiagList parse_diagnostics;
  M68kDiagList encode_diagnostics;
  M68kIrEncodeResult encoded;
  uint8_t encoded_bytes[32];
  uint8_t parse_cpu;
  if (text == NULL || source_instruction == NULL || raw_bytes == NULL || raw_size > sizeof(encoded_bytes)) return 0;
  if (instruction_has_symbolic_or_relative_text(source_instruction)) return 1;
  if (source_instruction->has_coprocessor_id != 0U && source_instruction->coprocessor_id != 1U &&
      (source_instruction->mnemonic_id == M68K_ASM_MNEMONIC_CPRESTORE ||
       source_instruction->mnemonic_id == M68K_ASM_MNEMONIC_CPSAVE)) {
    return 1;
  }
  parse_cpu = render_instruction != NULL ? render_instruction->target_cpu : source_instruction->target_cpu;
  m68k_diag_list_reset(&parse_diagnostics);
  parsed = m68k_plain_parse_instruction_to_ir(text, parse_cpu, m68k_diag_sink(&parse_diagnostics));
  if (m68k_diag_has_errors(&parse_diagnostics)) return 0;
  m68k_diag_list_reset(&encode_diagnostics);
  encoded = m68k_ir_encode_one(&parsed, encoded_bytes, sizeof(encoded_bytes), m68k_diag_sink(&encode_diagnostics));
  if (m68k_diag_has_errors(&encode_diagnostics) || encoded.byte_count != raw_size) return 0;
  return memcmp(encoded_bytes, raw_bytes, raw_size) == 0;
}

static int instruction_needs_fpu_id_directive_for_render(const M68kInstructionIR *instruction) {
  if (instruction == NULL || instruction->has_coprocessor_id == 0U || instruction->coprocessor_id == 1U)
    return 0;
  return instruction->mnemonic_id == M68K_ASM_MNEMONIC_CPRESTORE ||
    instruction->mnemonic_id == M68K_ASM_MNEMONIC_CPSAVE;
}

static int instruction_renders_with_fpu_mnemonic_for_render(const M68kInstructionIR *instruction) {
  if (instruction == NULL || instruction->has_coprocessor_id == 0U) return 0;
  return instruction->mnemonic_id == M68K_ASM_MNEMONIC_CPRESTORE ||
    instruction->mnemonic_id == M68K_ASM_MNEMONIC_CPSAVE;
}

static int make_fpu_id_render_instruction_for_preview(const M68kInstructionIR *instruction,
    M68kInstructionIR *out_instruction) {
  M68kAsmOperandValue operands[4];
  uint8_t mnemonic_id;
  size_t operand_index;
  if (instruction == NULL || out_instruction == NULL) return 0;
  if (!instruction_renders_with_fpu_mnemonic_for_render(instruction)) return 0;
  *out_instruction = *instruction;
  mnemonic_id = instruction->mnemonic_id == M68K_ASM_MNEMONIC_CPRESTORE
    ? M68K_ASM_MNEMONIC_FRESTORE : M68K_ASM_MNEMONIC_FSAVE;
  out_instruction->mnemonic_id = mnemonic_id;
  out_instruction->target_cpu = M68K_ASM_CPU_68040;
  out_instruction->has_coprocessor_id = 0U;
  out_instruction->coprocessor_id = 0U;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    m68k_instruction_operand_to_asm_value(&instruction->operands[operand_index], &operands[operand_index]);
  }
  out_instruction->asm_form_index = m68k_asm_form_index_for_operands_id(mnemonic_id, operands,
    instruction->operand_count, instruction->size_suffix, out_instruction->target_cpu);
  return g_m68k_asm_forms[out_instruction->asm_form_index].mnemonic_id != M68K_ASM_MNEMONIC_NONE;
}

struct M68kRenderLookup {
  uint8_t **labels;
  const char ***object_symbol_labels;
  const M68kFact ***relocations;
  const M68kFact ***anchors;
  uint8_t **block_starts;
  uint32_t *label_extents;
  uint32_t *object_symbol_label_extents;
  uint32_t *relocation_extents;
  uint32_t *anchor_extents;
  uint32_t *block_start_extents;
  size_t section_count;
  const M68kObject *object;
  const M68kAnalysisPolicy *policy;
  M68kRenderGlobalBaseSlot *global_base_slots;
  size_t global_base_slot_count;
  size_t global_base_slot_capacity;
  M68kRenderBaseFieldSlot *base_field_slots;
  size_t base_field_slot_count;
  size_t base_field_slot_capacity;
  M68kRenderAppSlotRef *app_slot_refs;
  size_t app_slot_ref_count;
  size_t app_slot_ref_capacity;
  M68kRenderIndexedVectorWrapper *indexed_vector_wrappers;
  size_t indexed_vector_wrapper_count;
  size_t indexed_vector_wrapper_capacity;
  M68kRenderRecoveredFunctionArg *recovered_function_args;
  size_t recovered_function_arg_count;
  size_t recovered_function_arg_capacity;
  M68kRenderRecoveredLocalCallSummary *recovered_local_call_summaries;
  size_t recovered_local_call_summary_count;
  size_t recovered_local_call_summary_capacity;
  M68kRenderTypedSlotEffect *typed_slot_effects;
  size_t typed_slot_effect_count;
  size_t typed_slot_effect_capacity;
  M68kRenderInstructionComment *instruction_comments;
  size_t instruction_comment_count;
  size_t instruction_comment_capacity;
  M68kRenderStringSpan *string_spans;
  size_t string_span_count;
  size_t string_span_capacity;
  size_t **instruction_comment_indices;
  uint32_t *instruction_comment_extents;
};

static uint32_t render_section_extent(const M68kDecodeSectionIR *section) {
  if (section == NULL) return 0U;
  return section->allocation_size > section->size ? section->allocation_size : section->size;
}

static void render_lookup_destroy(M68kRenderLookup *lookup) {
  size_t section_index;
  if (lookup == NULL) return;
  if (lookup->labels != NULL) {
    for (section_index = 0U; section_index < lookup->section_count; ++section_index) free(lookup->labels[section_index]);
  }
  if (lookup->object_symbol_labels != NULL) {
    for (section_index = 0U; section_index < lookup->section_count; ++section_index)
      free(lookup->object_symbol_labels[section_index]);
  }
  if (lookup->relocations != NULL) {
    for (section_index = 0U; section_index < lookup->section_count; ++section_index)
      free(lookup->relocations[section_index]);
  }
  if (lookup->anchors != NULL) {
    for (section_index = 0U; section_index < lookup->section_count; ++section_index)
      free(lookup->anchors[section_index]);
  }
  if (lookup->block_starts != NULL) {
    for (section_index = 0U; section_index < lookup->section_count; ++section_index)
      free(lookup->block_starts[section_index]);
  }
  free(lookup->global_base_slots);
  free(lookup->base_field_slots);
  free(lookup->app_slot_refs);
  free(lookup->indexed_vector_wrappers);
  free(lookup->recovered_function_args);
  free(lookup->recovered_local_call_summaries);
  free(lookup->typed_slot_effects);
  free(lookup->instruction_comments);
  free(lookup->string_spans);
  if (lookup->instruction_comment_indices != NULL) {
    for (section_index = 0U; section_index < lookup->section_count; ++section_index)
      free(lookup->instruction_comment_indices[section_index]);
  }
  free(lookup->labels);
  free(lookup->object_symbol_labels);
  free(lookup->relocations);
  free(lookup->anchors);
  free(lookup->block_starts);
  free(lookup->label_extents);
  free(lookup->object_symbol_label_extents);
  free(lookup->relocation_extents);
  free(lookup->anchor_extents);
  free(lookup->block_start_extents);
  free(lookup->instruction_comment_indices);
  free(lookup->instruction_comment_extents);
  memset(lookup, 0, sizeof(*lookup));
}

static const char *lookup_policy_label_name(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  uint16_t index;
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  if (policy == NULL) return NULL;
  for (index = 0U; index < policy->named_label_count && index < M68K_ANALYSIS_NAMED_LABEL_LIMIT; ++index) {
    const M68kAnalysisNamedLabel *label = &policy->named_labels[index];
    if (label->name[0] == '\0' || label->offset != offset) continue;
    if (label->has_section_index) {
      if (label->section_index != (uint32_t)section_index) continue;
    } else if (section_index != 0U) {
      continue;
    }
    return label->name;
  }
  return NULL;
}

static const char *lookup_object_symbol_label_name(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  size_t index;
  const M68kObject *object = lookup != NULL ? lookup->object : NULL;
  if (lookup != NULL && section_index < lookup->section_count && lookup->object_symbol_labels != NULL &&
      lookup->object_symbol_label_extents != NULL && offset <= lookup->object_symbol_label_extents[section_index] &&
      lookup->object_symbol_labels[section_index] != NULL) {
    return lookup->object_symbol_labels[section_index][offset];
  }
  if (object == NULL) return NULL;
  for (index = 0U; index < object->symbol_count; ++index) {
    const M68kSymbol *symbol = &object->symbols[index];
    if (!symbol->defined || symbol->section_index != section_index || symbol->value != offset) continue;
    if (!asm_symbol_name_is_safe_local(symbol->name)) continue;
    return symbol->name;
  }
  return NULL;
}

static uint8_t format_lookup_asm_label_with_generation(const M68kRenderLookup *lookup, char *buf, size_t buf_size,
    size_t section_index, uint32_t offset) {
  const char *policy_name = lookup_policy_label_name(lookup, section_index, offset);
  const char *object_name = NULL;
  if (buf == NULL || buf_size == 0U) return 1U;
  if (policy_name != NULL && policy_name[0] != '\0') {
    snprintf(buf, buf_size, "%s", policy_name);
    return 0U;
  }
  object_name = lookup_object_symbol_label_name(lookup, section_index, offset);
  if (object_name != NULL && object_name[0] != '\0') {
    snprintf(buf, buf_size, "%s", object_name);
    return 0U;
  }
  if (lookup != NULL && lookup->object != NULL &&
      lookup->object->platform_backend_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    const char *library_name = lookup_global_base_slot_library(lookup, section_index, offset);
    const char *base_name = amiga_os_find_library_base_name(library_name);
    if (base_name == NULL) base_name = library_name;
    if (base_name != NULL &&
        platform_amiga_format_global_base_slot_label(section_index, 'l', base_name, buf, buf_size)) {
      return 0U;
    }
  }
  format_asm_label(buf, buf_size, section_index, offset);
  return 1U;
}

static void format_lookup_asm_label(const M68kRenderLookup *lookup, char *buf, size_t buf_size,
    size_t section_index, uint32_t offset) {
  (void)format_lookup_asm_label_with_generation(lookup, buf, buf_size, section_index, offset);
}

static int structured_item_matches_section(const M68kAnalysisStructuredDataItem *item, size_t section_index) {
  if (item == NULL) return 0;
  if (item->has_section_index) return item->section_index == (uint32_t)section_index;
  return section_index == 0U;
}

static const M68kAnalysisStructuredDataItem *lookup_structured_data_item_at_offset(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  uint16_t index;
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  if (policy == NULL) return NULL;
  for (index = 0U; index < policy->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    if (item->offset == offset && item->size != 0U && structured_item_matches_section(item, section_index))
      return item;
  }
  return NULL;
}

static const M68kAnalysisStructuredDataItem *lookup_structured_data_item_covering_offset(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  uint16_t index;
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  if (policy == NULL) return NULL;
  for (index = 0U; index < policy->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    uint32_t end;
    if (item->size == 0U || !structured_item_matches_section(item, section_index)) continue;
    if (UINT32_MAX - item->offset < item->size) continue;
    end = item->offset + item->size;
    if (offset >= item->offset && offset < end) return item;
  }
  return NULL;
}

static int lookup_has_structured_data_item_at_offset(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  return lookup_structured_data_item_at_offset(lookup, section_index, offset) != NULL;
}

static int structured_data_item_comment(const M68kAnalysisStructuredDataItem *item, char *comment,
    size_t comment_size) {
  const char *field_name;
  const char *type_name;
  if (comment == NULL || comment_size == 0U) return 0;
  comment[0] = '\0';
  if (item == NULL) return 0;
  field_name = item->field_name[0] != '\0' ? item->field_name : item->label;
  if (item->struct_name[0] != '\0' && field_name != NULL && field_name[0] != '\0') {
    type_name = item->field_type[0] != '\0' ? item->field_type : item->c_type;
    if (type_name != NULL && type_name[0] != '\0') {
      snprintf(comment, comment_size, "%s %s", type_name, field_name);
    } else {
      snprintf(comment, comment_size, "FIELD: %s.%s", item->struct_name, field_name);
    }
    return 1;
  }
  if (item->comment[0] != '\0') {
    snprintf(comment, comment_size, "%s", item->comment);
    return 1;
  }
  if (item->semantic_role[0] != '\0') {
    snprintf(comment, comment_size, "%s", item->semantic_role);
    return 1;
  }
  return 0;
}

static int structured_data_item_constant_matches_bytes(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item) {
  uint32_t value = 0U;
  uint32_t mask = 0xFFFFFFFFU;
  if (section == NULL || section->data == NULL || item == NULL || item->has_constant_value == 0U ||
      item->constant_name[0] == '\0' || item->offset >= section->size) {
    return 0;
  }
  if (item->size == 1U && item->offset + 1U <= section->size) {
    value = section->data[item->offset];
    mask = 0xFFU;
  } else if (item->size == 2U && item->offset + 2U <= section->size) {
    value = m68k_read_u16be(section->data + item->offset);
    mask = 0xFFFFU;
  } else if (item->size == 4U && item->offset + 4U <= section->size) {
    value = m68k_read_u32be(section->data + item->offset);
  } else {
    return 0;
  }
  return value == ((uint32_t)item->constant_value & mask);
}

static int structured_data_item_raw_value(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, uint32_t *out_value) {
  if (out_value != NULL) *out_value = 0U;
  if (section == NULL || section->data == NULL || item == NULL || item->offset >= section->size) return 0;
  if (item->size == 1U && item->offset + 1U <= section->size) {
    if (out_value != NULL) *out_value = section->data[item->offset];
    return 1;
  }
  if (item->size == 2U && item->offset + 2U <= section->size) {
    if (out_value != NULL) *out_value = m68k_read_u16be(section->data + item->offset);
    return 1;
  }
  if (item->size == 4U && item->offset + 4U <= section->size) {
    if (out_value != NULL) *out_value = m68k_read_u32be(section->data + item->offset);
    return 1;
  }
  return 0;
}

static int structured_data_item_value_domain_expr(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, char *expr, size_t expr_size) {
  uint32_t value;
  if (expr == NULL || expr_size == 0U || item == NULL) return 0;
  expr[0] = '\0';
  if (item->value_domain[0] == '\0' || !structured_data_item_raw_value(section, item, &value)) return 0;
  return amiga_value_domain_symbolic_expr(item->value_domain, value, expr, expr_size);
}

static int amiga_value_domain_symbolic_expr(const char *domain_name, uint32_t value, char *expr,
    size_t expr_size) {
  const AmigaOsValueDomainInfo *domain;
  const AmigaOsValueDomainMemberInfo *members;
  size_t member_count = 0U;
  uint32_t remaining;
  size_t index;
  int wrote = 0;
  if (expr == NULL || expr_size == 0U || domain_name == NULL || domain_name[0] == '\0') return 0;
  expr[0] = '\0';
  domain = amiga_os_find_value_domain(domain_name);
  if (domain == NULL) return 0;
  members = amiga_os_value_domain_members(domain, &member_count);
  if (members == NULL) return 0;
  for (index = 0U; index < member_count; ++index) {
    const char *name;
    if (!members[index].value_known || (uint32_t)members[index].value != value) continue;
    name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, members[index].name_id);
    if (name == NULL || name[0] == '\0') continue;
    snprintf(expr, expr_size, "%s", name);
    return 1;
  }
  if (value == 0U && domain->zero_name_id != AMIGA_OS_SYMBOL_ID_NONE) {
    const char *name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, domain->zero_name_id);
    if (name == NULL || name[0] == '\0') return 0;
    snprintf(expr, expr_size, "%s", name);
    return 1;
  }
  if (domain->kind != AMIGA_OS_VALUE_DOMAIN_KIND_FLAGS ||
      (domain->composition != AMIGA_OS_VALUE_DOMAIN_COMPOSITION_OR &&
       domain->composition != AMIGA_OS_VALUE_DOMAIN_COMPOSITION_BIT_OR)) {
    return 0;
  }
  remaining = value;
  while (remaining != 0U) {
    uint32_t best_value = 0U;
    const char *best_name = NULL;
    for (index = 0U; index < member_count; ++index) {
      uint32_t member_value;
      const char *name;
      if (!members[index].value_known || members[index].value <= 0) continue;
      member_value = (uint32_t)members[index].value;
      if ((remaining & member_value) != member_value) continue;
      name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, members[index].name_id);
      if (name == NULL || name[0] == '\0') continue;
      if (best_name == NULL || member_value > best_value) {
        best_value = member_value;
        best_name = name;
      }
    }
    if (best_name == NULL) return 0;
    if (wrote) {
      size_t used = strlen(expr);
      if (used + 2U > expr_size) return 0;
      expr[used] = '|';
      expr[used + 1U] = '\0';
    }
    if (strlen(expr) + strlen(best_name) + 1U > expr_size) return 0;
    strcat(expr, best_name);
    remaining &= ~best_value;
    wrote = 1;
  }
  return wrote;
}

static int structured_data_item_symbolic_operand_expr(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, char *expr, size_t expr_size) {
  if (expr == NULL || expr_size == 0U || item == NULL) return 0;
  expr[0] = '\0';
  if (!((item->size == 1U && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_BYTES) ||
        (item->size == 2U && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_WORDS) ||
        (item->size == 4U && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS))) {
    return 0;
  }
  if (item->size == 4U && strcmp(item->struct_name, "resident_autoinit") == 0 &&
      strcmp(item->field_name, "resident_base_size") == 0) {
    snprintf(expr, expr_size, "app_SIZEOF");
    return 1;
  }
  if (structured_data_item_constant_matches_bytes(section, item)) {
    if (!asm_symbol_name_is_safe_local(item->constant_name)) return 0;
    snprintf(expr, expr_size, "%s", item->constant_name);
    return 1;
  }
  if (!structured_data_item_value_domain_expr(section, item, expr, expr_size)) return 0;
  return render_asm_include_for_symbol_expr(NULL, expr);
}

static int structured_data_item_render_comment(const M68kDecodeSectionIR *section,
    const M68kAnalysisStructuredDataItem *item, char *comment, size_t comment_size) {
  char expr[96];
  size_t used;
  if (!structured_data_item_comment(item, comment, comment_size)) return 0;
  if (structured_data_item_constant_matches_bytes(section, item)) {
    snprintf(expr, sizeof(expr), "%s", item->constant_name);
  } else if (!structured_data_item_value_domain_expr(section, item, expr, sizeof(expr))) {
    return 1;
  }
  used = strlen(comment);
  if (used + strlen(expr) + 4U >= comment_size) return 1;
  snprintf(comment + used, comment_size - used, " = %s", expr);
  return 1;
}

static int render_lookup_build(M68kRenderLookup *lookup, const M68kObject *object, const M68kDecodeIR *decode,
    const M68kFactIR *facts, const M68kAnalysisPolicy *policy) {
  size_t section_index;
  size_t fact_index;
  if (lookup == NULL || decode == NULL || facts == NULL) return -1;
  memset(lookup, 0, sizeof(*lookup));
  lookup->section_count = decode->section_count;
  lookup->object = object;
  lookup->policy = policy;
  lookup->labels = (uint8_t **)calloc(decode->section_count, sizeof(*lookup->labels));
  lookup->object_symbol_labels =
    (const char ***)calloc(decode->section_count, sizeof(*lookup->object_symbol_labels));
  lookup->relocations = (const M68kFact ***)calloc(decode->section_count, sizeof(*lookup->relocations));
  lookup->anchors = (const M68kFact ***)calloc(decode->section_count, sizeof(*lookup->anchors));
  lookup->block_starts = (uint8_t **)calloc(decode->section_count, sizeof(*lookup->block_starts));
  lookup->label_extents = (uint32_t *)calloc(decode->section_count, sizeof(*lookup->label_extents));
  lookup->object_symbol_label_extents =
    (uint32_t *)calloc(decode->section_count, sizeof(*lookup->object_symbol_label_extents));
  lookup->relocation_extents = (uint32_t *)calloc(decode->section_count, sizeof(*lookup->relocation_extents));
  lookup->anchor_extents = (uint32_t *)calloc(decode->section_count, sizeof(*lookup->anchor_extents));
  lookup->block_start_extents = (uint32_t *)calloc(decode->section_count, sizeof(*lookup->block_start_extents));
  lookup->instruction_comment_indices =
    (size_t **)calloc(decode->section_count, sizeof(*lookup->instruction_comment_indices));
  lookup->instruction_comment_extents =
    (uint32_t *)calloc(decode->section_count, sizeof(*lookup->instruction_comment_extents));
  if (lookup->labels == NULL || lookup->object_symbol_labels == NULL || lookup->relocations == NULL ||
      lookup->anchors == NULL || lookup->block_starts == NULL || lookup->label_extents == NULL ||
      lookup->object_symbol_label_extents == NULL || lookup->relocation_extents == NULL ||
      lookup->anchor_extents == NULL || lookup->block_start_extents == NULL ||
      lookup->instruction_comment_indices == NULL || lookup->instruction_comment_extents == NULL)
    goto oom;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    uint32_t label_extent = render_section_extent(&decode->sections[section_index]);
    uint32_t relocation_extent = decode->sections[section_index].size;
    uint32_t anchor_extent = decode->sections[section_index].size;
    uint32_t block_start_extent = render_section_extent(&decode->sections[section_index]);
    uint32_t comment_extent = decode->sections[section_index].size;
    lookup->label_extents[section_index] = label_extent;
    lookup->object_symbol_label_extents[section_index] = label_extent;
    lookup->relocation_extents[section_index] = relocation_extent;
    lookup->anchor_extents[section_index] = anchor_extent;
    lookup->block_start_extents[section_index] = block_start_extent;
    lookup->instruction_comment_extents[section_index] = comment_extent;
    lookup->labels[section_index] =
      (uint8_t *)calloc((size_t)label_extent + 1U, sizeof(*lookup->labels[section_index]));
    lookup->object_symbol_labels[section_index] =
      (const char **)calloc((size_t)label_extent + 1U, sizeof(*lookup->object_symbol_labels[section_index]));
    if (relocation_extent != 0U) {
      lookup->relocations[section_index] =
        (const M68kFact **)calloc(relocation_extent, sizeof(*lookup->relocations[section_index]));
    }
    if (anchor_extent != 0U) {
      lookup->anchors[section_index] =
        (const M68kFact **)calloc(anchor_extent, sizeof(*lookup->anchors[section_index]));
    }
    if (block_start_extent != 0U) {
      lookup->block_starts[section_index] =
        (uint8_t *)calloc(block_start_extent, sizeof(*lookup->block_starts[section_index]));
    }
    if (comment_extent != 0U) {
      lookup->instruction_comment_indices[section_index] =
        (size_t *)calloc(comment_extent, sizeof(*lookup->instruction_comment_indices[section_index]));
    }
    if (lookup->labels[section_index] == NULL || lookup->object_symbol_labels[section_index] == NULL ||
        (relocation_extent != 0U && lookup->relocations[section_index] == NULL) ||
        (anchor_extent != 0U && lookup->anchors[section_index] == NULL) ||
        (block_start_extent != 0U && lookup->block_starts[section_index] == NULL) ||
        (comment_extent != 0U && lookup->instruction_comment_indices[section_index] == NULL))
      goto oom;
  }
  if (object != NULL) {
    size_t symbol_index;
    for (symbol_index = 0U; symbol_index < object->symbol_count; ++symbol_index) {
      const M68kSymbol *symbol = &object->symbols[symbol_index];
      if (!symbol->defined || symbol->section_index >= decode->section_count ||
          symbol->value > lookup->object_symbol_label_extents[symbol->section_index] ||
          !asm_symbol_name_is_safe_local(symbol->name)) {
        continue;
      }
      if (lookup->object_symbol_labels[symbol->section_index][symbol->value] == NULL) {
        lookup->object_symbol_labels[symbol->section_index][symbol->value] = symbol->name;
      }
    }
  }
  for (fact_index = 0U; fact_index < facts->fact_count; ++fact_index) {
    const M68kFact *fact = &facts->facts[fact_index];
    if (fact->section_index >= decode->section_count) continue;
    if (fact->kind == M68K_FACT_LABEL_CREATED && fact->offset <= lookup->label_extents[fact->section_index]) {
      lookup->labels[fact->section_index][fact->offset] = 1U;
    } else if (fact->kind == M68K_FACT_CODE_START &&
        fact->reason != M68K_FACT_CODE_START_REASON_FALLTHROUGH &&
        fact->offset < lookup->block_start_extents[fact->section_index]) {
      lookup->block_starts[fact->section_index][fact->offset] = 1U;
    } else if (fact->kind == M68K_FACT_RELOCATION_REF &&
        fact->offset < lookup->relocation_extents[fact->section_index] && fact->size != 0U) {
      lookup->relocations[fact->section_index][fact->offset] = fact;
    } else if (fact->kind == M68K_FACT_RELOCATION_ANCHOR &&
        fact->offset < lookup->anchor_extents[fact->section_index] && fact->size != 0U) {
      lookup->anchors[fact->section_index][fact->offset] = fact;
    } else if (fact->kind == M68K_FACT_VIOLATION) {
      const M68kAnalysisStructuredDataItem *item =
        lookup_structured_data_item_covering_offset(lookup, fact->section_index, fact->offset);
      uint32_t comment_offset = fact->offset;
      char comment[192];
      comment[0] = '\0';
      if (item != NULL) {
        if (fact->offset == item->offset) {
          comment_offset = item->offset;
          snprintf(comment, sizeof(comment),
            "invalid overlap: decoded code at $%04X starts at structured data; emitted as data",
            (unsigned)fact->offset);
        }
      } else if (fact->target_section_index < decode->section_count) {
        item = lookup_structured_data_item_covering_offset(lookup, fact->target_section_index,
          fact->target_offset);
        if (item != NULL && fact->target_section_index == fact->section_index) {
          comment_offset = item->offset;
          snprintf(comment, sizeof(comment),
            "invalid overlap: decoded code at $%04X crosses structured data at $%04X; emitted as data",
            (unsigned)fact->offset, (unsigned)fact->target_offset);
        }
      }
      if (comment[0] != '\0' &&
          render_lookup_add_instruction_comment(lookup, fact->section_index, comment_offset, comment) != 0) {
        goto oom;
      }
    }
  }
  return 0;
oom:
  render_lookup_destroy(lookup);
  return -1;
}

static int lookup_has_label(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->labels == NULL ||
      lookup->label_extents == NULL || offset > lookup->label_extents[section_index] ||
      lookup->labels[section_index] == NULL) {
    return 0;
  }
  return lookup->labels[section_index][offset] != 0U;
}

static const M68kFact *lookup_relocation_at(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->relocations == NULL ||
      lookup->relocation_extents == NULL || offset >= lookup->relocation_extents[section_index] ||
      lookup->relocations[section_index] == NULL) {
    return NULL;
  }
  return lookup->relocations[section_index][offset];
}

static const M68kFact *lookup_anchor_at(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->anchors == NULL ||
      lookup->anchor_extents == NULL || offset >= lookup->anchor_extents[section_index] ||
      lookup->anchors[section_index] == NULL) {
    return NULL;
  }
  return lookup->anchors[section_index][offset];
}

static uint32_t lookup_code_block_start_before_or_at(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  const uint8_t *block_starts;
  uint32_t cursor;
  if (lookup == NULL || section_index >= lookup->section_count || lookup->block_starts == NULL ||
      lookup->block_start_extents == NULL || lookup->block_starts[section_index] == NULL ||
      lookup->block_start_extents[section_index] == 0U) {
    return 0U;
  }
  block_starts = lookup->block_starts[section_index];
  cursor = offset;
  if (cursor >= lookup->block_start_extents[section_index]) {
    cursor = lookup->block_start_extents[section_index] - 1U;
  }
  for (;;) {
    if (block_starts[cursor] != 0U) return cursor;
    if (cursor == 0U) break;
    --cursor;
  }
  return 0U;
}

static int lookup_offset_is_inside_relocation_payload(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  uint32_t back;
  if (lookup == NULL || offset == 0U) return 0;
  for (back = 1U; back <= 4U && back <= offset; ++back) {
    uint32_t start = offset - back;
    const M68kFact *relocation = lookup_relocation_at(lookup, section_index, start);
    const M68kFact *anchor = lookup_anchor_at(lookup, section_index, start);
    if (relocation != NULL && relocation->size > back) return 1;
    if (anchor != NULL && anchor->size > back) return 1;
  }
  return 0;
}

static int lookup_has_renderable_label(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  const M68kAnalysisStructuredDataItem *covering_item;
  if (!lookup_has_label(lookup, section_index, offset)) return 0;
  covering_item = lookup_structured_data_item_covering_offset(lookup, section_index, offset);
  if (covering_item != NULL && covering_item->offset != offset &&
      lookup_structured_data_item_at_offset(lookup, section_index, offset) == NULL &&
      lookup_relocation_at(lookup, section_index, offset) == NULL &&
      lookup_anchor_at(lookup, section_index, offset) == NULL &&
      lookup_string_span_at_offset(lookup, section_index, offset) == NULL) {
    return 0;
  }
  return !lookup_offset_is_inside_relocation_payload(lookup, section_index, offset);
}

static const char *lookup_global_base_slot_library(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->global_base_slot_count; ++index) {
    const M68kRenderGlobalBaseSlot *slot = &lookup->global_base_slots[index];
    if (slot->section_index == section_index && slot->offset == offset && slot->library_name[0] != '\0')
      return slot->library_name;
  }
  return NULL;
}

static int base_field_owner_matches(const char *slot_owner, const char *owner_name) {
  if (slot_owner == NULL || owner_name == NULL || slot_owner[0] == '\0' || owner_name[0] == '\0') return 0;
  if (strcmp(slot_owner, owner_name) == 0) return 1;
  return strcmp(slot_owner, "__amiga_app_base__") == 0 && amiga_os_find_library_base_name(owner_name) != NULL;
}

static int app_base_slot_symbol_name_from_library(const char *library_name, char *symbol_name,
    size_t symbol_name_size) {
  const char *base_name;
  if (symbol_name != NULL && symbol_name_size != 0U) symbol_name[0] = '\0';
  if (library_name == NULL || library_name[0] == '\0') return 0;
  base_name = amiga_os_find_library_base_name(library_name);
  if (base_name == NULL && amiga_os_find_library_name_by_base_name(library_name) != NULL) base_name = library_name;
  if (base_name == NULL) return 0;
  return platform_amiga_format_app_base_slot_name(base_name, symbol_name, symbol_name_size);
}

static int format_app_base_fallback_slot_symbol_name(int16_t displacement, char *symbol_name,
    size_t symbol_name_size) {
  int written;
  if (symbol_name == NULL || symbol_name_size == 0U) return 0;
  written = snprintf(symbol_name, symbol_name_size, "app_%04X", (unsigned)(uint16_t)displacement);
  return written > 0 && (size_t)written < symbol_name_size;
}

static int app_base_slot_symbol_name_from_slot(const M68kRenderBaseFieldSlot *slot, char *symbol_name,
    size_t symbol_name_size) {
  if (symbol_name != NULL && symbol_name_size != 0U) symbol_name[0] = '\0';
  if (slot == NULL || slot->conflicted != 0U) return 0;
  if (slot->symbol_name[0] != '\0') {
    if (symbol_name == NULL || symbol_name_size == 0U) return 0;
    snprintf(symbol_name, symbol_name_size, "%s", slot->symbol_name);
    return strlen(slot->symbol_name) < symbol_name_size;
  }
  if (slot->library_name[0] == '\0') {
    if (strcmp(slot->owner_name, "__amiga_app_base__") == 0) {
      return format_app_base_fallback_slot_symbol_name(slot->displacement, symbol_name, symbol_name_size);
    }
    return 0;
  }
  if (slot->value_kind != M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE) return 0;
  return app_base_slot_symbol_name_from_library(slot->library_name, symbol_name, symbol_name_size);
}

static const char *library_base_struct_name_for_field_lookup(const char *owner_name) {
  const char *library_name;
  const char *struct_name;
  if (owner_name == NULL || owner_name[0] == '\0') return NULL;
  library_name = amiga_os_find_library_base_name(owner_name) != NULL
    ? owner_name
    : amiga_os_find_library_name_by_base_name(owner_name);
  if (library_name == NULL || library_name[0] == '\0') return NULL;
  struct_name = amiga_os_find_library_base_struct_name(library_name);
  if (struct_name != NULL && struct_name[0] != '\0') return struct_name;
  return amiga_os_name(M68K_PLATFORM_NAME_STRUCT, AMIGA_OS_STRUCT_ID_LIB);
}

static int kb_library_base_field_symbol_name(const char *owner_name, int16_t displacement, char *symbol_name,
    size_t symbol_name_size) {
  const char *common_struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, AMIGA_OS_STRUCT_ID_LIB);
  const char *struct_name;
  const AmigaOsStructFieldInfo *field = NULL;
  const char *field_name;
  if (symbol_name != NULL && symbol_name_size != 0U) symbol_name[0] = '\0';
  if (symbol_name == NULL || symbol_name_size == 0U) return 0;
  struct_name = library_base_struct_name_for_field_lookup(owner_name);
  if (struct_name == NULL || struct_name[0] == '\0') return 0;
  field = amiga_os_find_struct_field(struct_name, displacement);
  if (field == NULL && common_struct_name != NULL && strcmp(struct_name, common_struct_name) != 0) {
    field = amiga_os_find_struct_field_by_struct_id(AMIGA_OS_STRUCT_ID_LIB, displacement);
  }
  if (field == NULL) return 0;
  field_name = amiga_os_name(M68K_PLATFORM_NAME_FIELD, field->field_id);
  if (field_name == NULL || field_name[0] == '\0') return 0;
  snprintf(symbol_name, symbol_name_size, "%s", field_name);
  return strlen(field_name) < symbol_name_size;
}

static int library_base_has_specific_struct_name(const char *owner_name) {
  const char *library_name;
  const char *struct_name;
  const char *common_struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, AMIGA_OS_STRUCT_ID_LIB);
  if (owner_name == NULL || owner_name[0] == '\0') return 0;
  library_name = amiga_os_find_library_base_name(owner_name) != NULL
    ? owner_name
    : amiga_os_find_library_name_by_base_name(owner_name);
  if (library_name == NULL || library_name[0] == '\0') return 0;
  struct_name = amiga_os_find_library_base_struct_name(library_name);
  return struct_name != NULL && struct_name[0] != '\0' &&
    (common_struct_name == NULL || strcmp(struct_name, common_struct_name) != 0);
}

static int library_base_can_use_app_extension_slot(const char *owner_name, int16_t displacement) {
  int32_t lib_size = 0;
  char kb_symbol[64];
  if (owner_name == NULL || owner_name[0] == '\0') return 0;
  if (!amiga_os_find_constant_value("LIB_SIZE", &lib_size) || displacement < lib_size) return 0;
  if (library_base_has_specific_struct_name(owner_name) &&
      kb_library_base_field_symbol_name(owner_name, displacement, kb_symbol, sizeof(kb_symbol))) {
    return 0;
  }
  return 1;
}

static int lookup_app_base_field_slot_symbol_has_other_displacement(const M68kRenderLookup *lookup,
    const char *symbol_name, int16_t displacement) {
  size_t index;
  if (lookup == NULL || symbol_name == NULL || symbol_name[0] == '\0') return 0;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    char other_symbol_name[64];
    if (slot->conflicted != 0U || strcmp(slot->owner_name, "__amiga_app_base__") != 0) continue;
    if (!app_base_slot_symbol_name_from_slot(slot, other_symbol_name, sizeof(other_symbol_name))) continue;
    if (strcmp(symbol_name, other_symbol_name) == 0 && slot->displacement != displacement) return 1;
  }
  return 0;
}

static const char *lookup_base_field_slot_library(const M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement) {
  const char *matched_library = NULL;
  size_t index;
  if (lookup == NULL || owner_name == NULL || owner_name[0] == '\0') return NULL;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    char symbol_name[64];
    if (slot->displacement != displacement || slot->conflicted || slot->library_name[0] == '\0' ||
        slot->value_kind != M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE) {
      continue;
    }
    if (!base_field_owner_matches(slot->owner_name, owner_name)) continue;
    if (strcmp(slot->owner_name, "__amiga_app_base__") == 0 &&
        (!app_base_slot_symbol_name_from_slot(slot, symbol_name, sizeof(symbol_name)) ||
          lookup_app_base_field_slot_symbol_has_other_displacement(lookup, symbol_name, displacement))) {
      continue;
    }
    if (matched_library != NULL && strcmp(matched_library, slot->library_name) != 0) return NULL;
    matched_library = slot->library_name;
  }
  return matched_library;
}

static const char *lookup_app_base_field_slot_library(const M68kRenderLookup *lookup, int16_t displacement) {
  const char *matched_library = NULL;
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    char symbol_name[64];
    if (slot->displacement != displacement || slot->conflicted || slot->library_name[0] == '\0' ||
        slot->value_kind != M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE) {
      continue;
    }
    if (strcmp(slot->owner_name, "__amiga_app_base__") != 0) continue;
    if (!app_base_slot_symbol_name_from_slot(slot, symbol_name, sizeof(symbol_name)) ||
        lookup_app_base_field_slot_symbol_has_other_displacement(lookup, symbol_name, displacement)) {
      continue;
    }
    if (matched_library != NULL && strcmp(matched_library, slot->library_name) != 0) return NULL;
    matched_library = slot->library_name;
  }
  return matched_library;
}

static int lookup_base_field_slot_symbol_name(const M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement, char *symbol_name, size_t symbol_name_size) {
  int matched = 0;
  int blocked = 0;
  char matched_symbol[64];
  size_t index;
  if (symbol_name != NULL && symbol_name_size != 0U) symbol_name[0] = '\0';
  if (lookup == NULL || owner_name == NULL || owner_name[0] == '\0' ||
      symbol_name == NULL || symbol_name_size == 0U) {
    return 0;
  }
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    char slot_symbol[64];
    if (slot->displacement != displacement) continue;
    if (strcmp(slot->owner_name, owner_name) != 0) continue;
    if (slot->conflicted != 0U) {
      blocked = 1;
      continue;
    }
    if (slot->library_name[0] == '\0' && slot->symbol_name[0] == '\0' &&
        strcmp(slot->owner_name, "__amiga_app_base__") != 0) {
      continue;
    }
    if (strcmp(slot->owner_name, "__amiga_app_base__") == 0 &&
        (!app_base_slot_symbol_name_from_slot(slot, slot_symbol, sizeof(slot_symbol)) ||
          lookup_app_base_field_slot_symbol_has_other_displacement(lookup, slot_symbol, displacement))) {
      continue;
    }
    if (!app_base_slot_symbol_name_from_slot(slot, slot_symbol, sizeof(slot_symbol))) continue;
    if (matched && strcmp(matched_symbol, slot_symbol) != 0) return 0;
    snprintf(matched_symbol, sizeof(matched_symbol), "%s", slot_symbol);
    matched = 1;
  }
  if (blocked) return 0;
  if (!matched) return kb_library_base_field_symbol_name(owner_name, displacement, symbol_name, symbol_name_size);
  snprintf(symbol_name, symbol_name_size, "%s", matched_symbol);
  return strlen(matched_symbol) < symbol_name_size;
}

static int lookup_app_base_field_slot_symbol_name(const M68kRenderLookup *lookup, int16_t displacement,
    char *symbol_name, size_t symbol_name_size) {
  return lookup_base_field_slot_symbol_name(lookup, "__amiga_app_base__", displacement, symbol_name,
    symbol_name_size);
}

typedef struct M68kRenderAppRsSlot {
  int32_t displacement;
  char name[64];
} M68kRenderAppRsSlot;

static int render_app_rs_slot_compare(const void *left, const void *right) {
  const M68kRenderAppRsSlot *left_slot = (const M68kRenderAppRsSlot *)left;
  const M68kRenderAppRsSlot *right_slot = (const M68kRenderAppRsSlot *)right;
  if (left_slot->displacement < right_slot->displacement) return -1;
  if (left_slot->displacement > right_slot->displacement) return 1;
  return strcmp(left_slot->name, right_slot->name);
}

static int lookup_has_amiga_resident_library_context(const M68kRenderLookup *lookup) {
  const M68kAnalysisPolicy *policy;
  uint16_t index;
  if (lookup == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  policy = lookup->policy;
  if (policy == NULL) return 0;
  for (index = 0U; index < policy->named_label_count && index < M68K_ANALYSIS_NAMED_LABEL_LIMIT; ++index) {
    const char *name = policy->named_labels[index].name;
    if (strcmp(name, "resident") == 0 || strcmp(name, "resident_autoinit") == 0 ||
        strcmp(name, "resident_vectors") == 0) {
      return 1;
    }
  }
  for (index = 0U; index < policy->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    if (strcmp(item->struct_name, "resident") == 0 || strcmp(item->struct_name, "resident_autoinit") == 0 ||
        strcmp(item->struct_name, "resident_vectors") == 0) {
      return 1;
    }
    if (strcmp(item->label, "resident") == 0 || strcmp(item->label, "resident_autoinit") == 0 ||
        strcmp(item->label, "resident_vectors") == 0) {
      return 1;
    }
  }
  return 0;
}

static int render_app_rs_slot_exists(const M68kRenderAppRsSlot *slots, size_t slot_count, const char *name,
    int32_t displacement, int *out_conflict) {
  size_t index;
  if (out_conflict != NULL) *out_conflict = 0;
  for (index = 0U; index < slot_count; ++index) {
    if (strcmp(slots[index].name, name) != 0) continue;
    if (slots[index].displacement != displacement && out_conflict != NULL) *out_conflict = 1;
    return 1;
  }
  return 0;
}

static int render_app_rs_resident_sizeof_value(const M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    int32_t *out_value) {
  const M68kAnalysisPolicy *policy;
  uint16_t index;
  if (out_value != NULL) *out_value = 0;
  if (lookup == NULL || decode == NULL || lookup->policy == NULL) return 0;
  policy = lookup->policy;
  for (index = 0U; index < policy->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    const M68kDecodeSectionIR *section;
    size_t section_index;
    if (item->size != 4U || strcmp(item->struct_name, "resident_autoinit") != 0 ||
        strcmp(item->field_name, "resident_base_size") != 0) {
      continue;
    }
    section_index = item->has_section_index ? (size_t)item->section_index : 0U;
    if (section_index >= decode->section_count) continue;
    section = &decode->sections[section_index];
    if (section->data == NULL || item->offset > section->size || section->size - item->offset < 4U) continue;
    if (out_value != NULL) *out_value = (int32_t)m68k_read_u32be(section->data + item->offset);
    return 1;
  }
  return 0;
}

static void render_asm_app_extension_rs(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode) {
  M68kRenderAppRsSlot *slots = NULL;
  size_t slot_count = 0U;
  size_t slot_capacity = 0U;
  size_t index;
  int32_t lib_size = 0, base_offset = 0, cursor;
  int32_t inferred_sizeof = 0, app_sizeof_value = 0;
  int has_app_sizeof_value;
  int has_resident_context;
  char line[160];
  if (preview == NULL || lookup == NULL) return;
  slot_capacity = lookup->base_field_slot_count != 0U ? lookup->base_field_slot_count : 1U;
  slots = (M68kRenderAppRsSlot *)calloc(slot_capacity, sizeof(*slots));
  if (slots == NULL) {
    preview->asm_source_allocation_failed = 1U;
    return;
  }
  has_resident_context = lookup_has_amiga_resident_library_context(lookup);
  has_app_sizeof_value = render_app_rs_resident_sizeof_value(lookup, decode, &app_sizeof_value);
  if (has_resident_context) {
    if (!amiga_os_find_constant_value("LIB_SIZE", &lib_size) || lib_size <= 0) {
      free(slots);
      return;
    }
    base_offset = lib_size;
  }
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    char symbol_name[64];
    int conflict = 0;
    int32_t extent_end;
    if (slot->conflicted != 0U || strcmp(slot->owner_name, "__amiga_app_base__") != 0) {
      continue;
    }
    if ((int32_t)slot->displacement < base_offset) continue;
    if (!app_base_slot_symbol_name_from_slot(slot, symbol_name, sizeof(symbol_name)) ||
        lookup_app_base_field_slot_symbol_has_other_displacement(lookup, symbol_name, slot->displacement)) {
      continue;
    }
    if (render_app_rs_slot_exists(slots, slot_count, symbol_name, slot->displacement, &conflict)) {
      if (conflict) {
        ++preview->asm_source_instruction_render_failures;
        record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER,
          slot->source_section_index, slot->source_offset, (uint32_t)(uint16_t)slot->displacement);
      }
      continue;
    }
    if (slot_count >= slot_capacity) {
      ++preview->asm_source_instruction_render_failures;
      record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER,
        slot->source_section_index, slot->source_offset, (uint32_t)(uint16_t)slot->displacement);
      continue;
    }
    slots[slot_count].displacement = slot->displacement;
    snprintf(slots[slot_count].name, sizeof(slots[slot_count].name), "%s", symbol_name);
    ++slot_count;
    extent_end = (int32_t)slot->displacement + 4;
    if (extent_end > inferred_sizeof) inferred_sizeof = extent_end;
  }
  if (slot_count == 0U && has_app_sizeof_value == 0) {
    free(slots);
    return;
  }
  qsort(slots, slot_count, sizeof(slots[0]), render_app_rs_slot_compare);
  if (has_resident_context) {
    if (!render_asm_include_for_amiga_symbol(preview, "LIB_SIZE")) {
      ++preview->asm_source_instruction_render_failures;
      record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, 0U, 0U, 0U);
      free(slots);
      return;
    }
    hash_asm_text(preview, "    RSSET LIB_SIZE\n");
  } else {
    hash_asm_text(preview, "    RSSET 0\n");
  }
  ++preview->asm_source_lines;
  cursor = base_offset;
  for (index = 0U; index < slot_count; ++index) {
    if (slots[index].displacement > cursor) {
      snprintf(line, sizeof(line), "    RS.B %d\n", (int)(slots[index].displacement - cursor));
      hash_asm_text(preview, line);
      ++preview->asm_source_lines;
      cursor = slots[index].displacement;
    }
    if (slots[index].displacement < cursor) {
      snprintf(line, sizeof(line), "%s RS.B 0\n", slots[index].name);
    } else if ((cursor & 1) == 0) {
      snprintf(line, sizeof(line), "%s RS.L 1\n", slots[index].name);
      cursor += 4;
    } else {
      snprintf(line, sizeof(line), "%s RS.B 1\n", slots[index].name);
      cursor += 1;
    }
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
  }
  if (has_app_sizeof_value != 0 && app_sizeof_value > inferred_sizeof) inferred_sizeof = app_sizeof_value;
  if (inferred_sizeof > cursor) {
    snprintf(line, sizeof(line), "    RS.B %d\n", (int)(inferred_sizeof - cursor));
    hash_asm_text(preview, line);
    ++preview->asm_source_lines;
  }
  hash_asm_text(preview, "app_SIZEOF EQU __RS\n\n");
  ++preview->asm_source_lines;
  free(slots);
}

static const char *lookup_indexed_vector_wrapper_library(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->indexed_vector_wrapper_count; ++index) {
    const M68kRenderIndexedVectorWrapper *wrapper = &lookup->indexed_vector_wrappers[index];
    if (wrapper->section_index == section_index && wrapper->offset == offset && wrapper->library_name[0] != '\0')
      return wrapper->library_name;
  }
  return NULL;
}

static const char *directive_for_data_size(uint32_t size) {
  if (size == 4U) return "dc.l";
  if (size == 2U) return "dc.w";
  return "dc.b";
}

static void format_numeric_value(char *buffer, size_t buffer_size, uint32_t size, uint32_t value) {
  if (buffer == NULL || buffer_size == 0U) return;
  if (size == 4U) snprintf(buffer, buffer_size, "$%08X", (unsigned)value);
  else if (size == 2U) snprintf(buffer, buffer_size, "$%04X", (unsigned)(value & 0xFFFFU));
  else snprintf(buffer, buffer_size, "$%02X", (unsigned)(value & 0xFFU));
}

static void format_hunk_anchor_expression(char *buffer, size_t buffer_size, const M68kFact *anchor) {
  if (buffer == NULL || buffer_size == 0U) return;
  if (anchor == NULL) {
    buffer[0] = '\0';
    return;
  }
  if (anchor->target_addend < 0) {
    uint64_t magnitude = (uint64_t)(-anchor->target_addend);
    snprintf(buffer, buffer_size, "base(hunk %u)-$%08X",
      (unsigned)anchor->target_section_index, (unsigned)magnitude);
  } else {
    snprintf(buffer, buffer_size, "base(hunk %u)+$%08X",
      (unsigned)anchor->target_section_index, (unsigned)((uint64_t)anchor->target_addend & 0xFFFFFFFFULL));
  }
}

static void format_hunk_anchor_reason(char *buffer, size_t buffer_size, const M68kRenderLookup *lookup,
    const M68kFact *anchor) {
  uint32_t target_extent = 0U;
  if (buffer == NULL || buffer_size == 0U) return;
  if (lookup == NULL || anchor == NULL || anchor->target_section_index >= lookup->section_count ||
      lookup->label_extents == NULL) {
    snprintf(buffer, buffer_size, "target hunk unavailable; left numeric");
    return;
  }
  target_extent = lookup->label_extents[anchor->target_section_index];
  if (anchor->target_addend < 0) {
    snprintf(buffer, buffer_size, "negative addend points before target hunk; left numeric");
  } else if ((uint64_t)anchor->target_addend >= (uint64_t)target_extent) {
    snprintf(buffer, buffer_size, "addend outside target hunk real size $%08X; left numeric",
      (unsigned)target_extent);
  } else {
    snprintf(buffer, buffer_size, "unproven hunk relocation; left numeric");
  }
}

static void format_lossy_hunk_anchor_comment(char *buffer, size_t buffer_size, const M68kRenderLookup *lookup,
    const M68kFact *anchor) {
  char expr[96];
  char reason[160];
  if (buffer == NULL || buffer_size == 0U) return;
  if (anchor == NULL) {
    buffer[0] = '\0';
    return;
  }
  format_hunk_anchor_expression(expr, sizeof(expr), anchor);
  format_hunk_anchor_reason(reason, sizeof(reason), lookup, anchor);
  snprintf(buffer, buffer_size,
    "facts_v2 HUNK_RELOC32 numeric: source hunk %u offset $%08X, target hunk %u, loader result %s; %s",
    (unsigned)anchor->section_index, (unsigned)anchor->offset,
    (unsigned)anchor->target_section_index, expr, reason);
}

static void render_asm_lossy_hunk_relocation(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    const M68kFact *anchor) {
  char line[512];
  char value[32];
  char comment[384];
  const char *directive;
  if (preview == NULL || lookup == NULL || anchor == NULL) return;
  directive = directive_for_data_size(anchor->size);
  format_numeric_value(value, sizeof(value), anchor->size, anchor->target_offset);
  format_lossy_hunk_anchor_comment(comment, sizeof(comment), lookup, anchor);
  snprintf(line, sizeof(line), "\t%s %s\t; %s\n", directive, value, comment);
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  ++preview->asm_source_lossy_numeric_hunk_relocations;
}

static int accepted_start_at(const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t offset) {
  return section != NULL && accepted_start != NULL && offset < section->size && accepted_start[offset] != 0U;
}

static int candidate_is_accepted_start(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kDecodeCandidate *candidate) {
  return candidate != NULL && candidate->byte_count != 0U &&
    accepted_start_at(section, accepted_start, candidate->offset);
}

static int accepted_byte_at(const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes, uint32_t offset) {
  return section != NULL && accepted_bytes != NULL && offset < section->size && accepted_bytes[offset] != 0U;
}

static const M68kSimFormMetadata *render_cfg_candidate_metadata(const M68kDecodeCandidate *candidate,
    M68kInstructionIR *instruction) {
  if (candidate == NULL || instruction == NULL) return NULL;
  if (m68k_decode_candidate_to_instruction(candidate, instruction) != 0) return NULL;
  return m68k_sim_metadata_for_instruction(instruction);
}

static int render_cfg_candidate_has_control_target(const M68kDecodeCandidate *candidate) {
  size_t target_index;
  if (candidate == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_CALL ||
        target->kind == M68K_DECODE_TARGET_JUMP) {
      return 1;
    }
  }
  return 0;
}

static int render_cfg_candidate_has_fallthrough(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata = render_cfg_candidate_metadata(candidate, &instruction);
  if (metadata == NULL) return 1;
  if (metadata->flow_kind == M68K_SIM_FLOW_RETURN) return 0;
  if ((metadata->flow_kind == M68K_SIM_FLOW_JUMP || metadata->flow_kind == M68K_SIM_FLOW_BRANCH) &&
      !metadata->flow_conditional) {
    return 0;
  }
  return 1;
}

static uint8_t render_cfg_edge_kind_for_target(const M68kDecodeCandidate *candidate,
    const M68kDecodeTarget *target) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  if (target != NULL && target->kind == M68K_DECODE_TARGET_CALL) return M68K_CFG_EDGE_CALL;
  if (target != NULL && target->kind == M68K_DECODE_TARGET_JUMP) return M68K_CFG_EDGE_JUMP;
  metadata = render_cfg_candidate_metadata(candidate, &instruction);
  if (metadata != NULL && (metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
      (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && !metadata->flow_conditional))) {
    return M68K_CFG_EDGE_JUMP;
  }
  return M68K_CFG_EDGE_BRANCH;
}

static int render_cfg_append_edge(M68kSectionAnalysisIR *section_analysis, size_t source_block_index,
    uint32_t source_offset, uint32_t target_offset, uint8_t kind) {
  M68kCfgEdgeIR edge;
  memset(&edge, 0, sizeof(edge));
  edge.source_block_index = source_block_index;
  edge.target_block_index = SIZE_MAX;
  edge.source_offset = source_offset;
  edge.target_offset = target_offset;
  edge.kind = kind;
  return m68k_ir_section_analysis_append_edge(section_analysis, &edge);
}

static int render_cfg_resolve_edge_targets(M68kSectionAnalysisIR *section_analysis) {
  size_t edge_index;
  if (section_analysis == NULL) return -1;
  for (edge_index = 0U; edge_index < section_analysis->edge_count; ++edge_index) {
    M68kCfgEdgeIR *edge = &section_analysis->edges[edge_index];
    size_t block_index;
    edge->target_block_index = SIZE_MAX;
    if (edge->target_offset == UINT32_MAX) continue;
    for (block_index = 0U; block_index < section_analysis->block_count; ++block_index) {
      if (section_analysis->blocks[block_index].start_offset == edge->target_offset) {
        edge->target_block_index = block_index;
        break;
      }
    }
  }
  return 0;
}

static int render_cfg_lookup_block_start_at(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  return lookup != NULL && section_index < lookup->section_count && lookup->block_starts != NULL &&
    lookup->block_start_extents != NULL && lookup->block_starts[section_index] != NULL &&
    offset < lookup->block_start_extents[section_index] && lookup->block_starts[section_index][offset] != 0U;
}

static int render_cfg_build_block_start_map(const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const uint8_t *accepted_bytes, uint8_t *block_starts, uint32_t render_extent) {
  uint32_t offset = 0U;
  if (section == NULL || accepted_start == NULL || accepted_bytes == NULL || block_starts == NULL) return -1;
  while (offset < render_extent) {
    const M68kDecodeCandidate *candidate;
    uint32_t next_offset;
    size_t target_index;
    if (!accepted_start_at(section, accepted_start, offset)) {
      ++offset;
      continue;
    }
    candidate = find_candidate_at_offset_local(section, offset);
    if (candidate == NULL || candidate->byte_count == 0U || candidate->byte_count > render_extent - offset)
      return -1;
    if (offset == 0U || !accepted_byte_at(section, accepted_bytes, offset - 1U) ||
        render_cfg_lookup_block_start_at(lookup, section->section_index, offset)) {
      block_starts[offset] = 1U;
    }
    next_offset = offset + candidate->byte_count;
    for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
      const M68kDecodeTarget *target = &candidate->targets[target_index];
      if ((target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_CALL ||
          target->kind == M68K_DECODE_TARGET_JUMP) && target->has_section &&
          target->section_index == section->section_index && target->offset < render_extent &&
          accepted_start_at(section, accepted_start, target->offset)) {
        block_starts[target->offset] = 1U;
      }
    }
    if (render_cfg_candidate_has_control_target(candidate) && render_cfg_candidate_has_fallthrough(candidate) &&
        next_offset < render_extent && accepted_start_at(section, accepted_start, next_offset)) {
      block_starts[next_offset] = 1U;
    }
    offset = next_offset;
  }
  return 0;
}

static int render_analysis_append_cfg_for_section(const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const uint8_t *accepted_bytes, M68kSectionAnalysisIR *section_analysis) {
  uint32_t render_extent;
  uint8_t *block_starts = NULL;
  uint32_t offset = 0U;
  int result = -1;
  if (section == NULL || section_analysis == NULL) return -1;
  render_extent = render_section_extent(section);
  if (render_extent == 0U) return 0;
  block_starts = (uint8_t *)calloc(render_extent, sizeof(*block_starts));
  if (block_starts == NULL) return -1;
  if (render_cfg_build_block_start_map(lookup, section, accepted_start, accepted_bytes, block_starts,
      render_extent) != 0) {
    goto cleanup;
  }
  while (offset < render_extent) {
    M68kCfgBlockIR block;
    uint32_t cursor;
    if (!accepted_start_at(section, accepted_start, offset) || block_starts[offset] == 0U) {
      ++offset;
      continue;
    }
    memset(&block, 0, sizeof(block));
    block.start_offset = offset;
    block.certainty = M68K_CODE_CERTAIN;
    block.edge_start = section_analysis->edge_count;
    cursor = offset;
    while (cursor < render_extent && accepted_start_at(section, accepted_start, cursor)) {
      const M68kDecodeCandidate *candidate = find_candidate_at_offset_local(section, cursor);
      uint32_t next_offset;
      size_t target_index;
      int has_control_target;
      int has_fallthrough;
      if (candidate == NULL || candidate->byte_count == 0U || candidate->byte_count > render_extent - cursor)
        goto cleanup;
      next_offset = cursor + candidate->byte_count;
      has_control_target = render_cfg_candidate_has_control_target(candidate);
      has_fallthrough = render_cfg_candidate_has_fallthrough(candidate);
      for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
        const M68kDecodeTarget *target = &candidate->targets[target_index];
        if ((target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_CALL ||
            target->kind == M68K_DECODE_TARGET_JUMP) && target->has_section &&
            target->section_index == section->section_index) {
          if (render_cfg_append_edge(section_analysis, section_analysis->block_count, cursor, target->offset,
              render_cfg_edge_kind_for_target(candidate, target)) != 0) {
            goto cleanup;
          }
        }
      }
      if (has_control_target) {
        if (has_fallthrough && next_offset < render_extent && accepted_start_at(section, accepted_start, next_offset) &&
            render_cfg_append_edge(section_analysis, section_analysis->block_count, cursor, next_offset,
              M68K_CFG_EDGE_FALLTHROUGH) != 0) {
          goto cleanup;
        }
        cursor = next_offset;
        break;
      }
      if (!has_fallthrough) {
        if (render_cfg_append_edge(section_analysis, section_analysis->block_count, cursor, UINT32_MAX,
            M68K_CFG_EDGE_RETURN) != 0) {
          goto cleanup;
        }
        cursor = next_offset;
        break;
      }
      if (next_offset >= render_extent || !accepted_start_at(section, accepted_start, next_offset) ||
          block_starts[next_offset] != 0U) {
        if (next_offset < render_extent && accepted_start_at(section, accepted_start, next_offset) &&
            render_cfg_append_edge(section_analysis, section_analysis->block_count, cursor, next_offset,
              M68K_CFG_EDGE_FALLTHROUGH) != 0) {
          goto cleanup;
        }
        cursor = next_offset;
        break;
      }
      cursor = next_offset;
    }
    block.end_offset = cursor;
    block.edge_count = section_analysis->edge_count - block.edge_start;
    if (m68k_ir_section_analysis_append_block(section_analysis, &block) != 0) goto cleanup;
    offset = cursor > offset ? cursor : offset + 1U;
  }
  if (render_cfg_resolve_edge_targets(section_analysis) != 0) goto cleanup;
  result = 0;

cleanup:
  free(block_starts);
  return result;
}

static uint8_t symbol_ref_kind_for_operand(const M68kOperandIR *operand) {
  if (operand == NULL) return M68K_IR_SYMBOL_REF_ABS;
  if (operand->kind == M68K_ASM_OPERAND_LABEL) return M68K_IR_SYMBOL_REF_PC_REL;
  if ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->value.ea_mode == 7U && (operand->value.ea_reg == 2U || operand->value.ea_reg == 3U)) {
    return M68K_IR_SYMBOL_REF_PC_REL;
  }
  return M68K_IR_SYMBOL_REF_ABS;
}

static void attach_operand_label_symbol(const M68kRenderLookup *lookup, M68kInstructionIR *instruction,
    size_t operand_index, size_t section_index, uint32_t target_offset) {
  M68kOperandIR *operand;
  if (instruction == NULL || operand_index >= instruction->operand_count) return;
  operand = &instruction->operands[operand_index];
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
  operand->symbol_ref.kind = symbol_ref_kind_for_operand(operand);
  operand->symbol_ref.has_name = 1U;
  operand->symbol_ref.name_is_generated = format_lookup_asm_label_with_generation(lookup,
    operand->symbol_ref.name, sizeof(operand->symbol_ref.name), section_index, target_offset);
  operand->symbol_ref.has_section = 1;
  operand->symbol_ref.section_index = section_index;
}

static int target_matches_relocation(const M68kDecodeTarget *target, const M68kFact *relocation) {
  return target != NULL && relocation != NULL && target->has_section != 0U &&
    target->section_index == relocation->target_section_index && target->offset == relocation->target_offset;
}

static int32_t signed_8(uint32_t value) {
  return (int8_t)(value & 0xFFU);
}

static int32_t signed_16(uint32_t value) {
  return (int16_t)(value & 0xFFFFU);
}

static int exact_operand_relocation_span(const M68kDecodeCandidate *candidate, size_t operand_index,
    uint32_t *out_start, uint32_t *out_size) {
  const M68kAsmFormDef *form;
  M68kAsmOperandValue layout_operands[M68K_DECODE_IR_MAX_OPERANDS];
  char size_suffix;
  size_t word_index;
  size_t extension_index;
  size_t index;
  if (candidate == NULL || out_start == NULL || out_size == NULL || operand_index >= candidate->operand_count)
    return 0;
  if (candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_LABEL && candidate->size_suffix == 'b') {
    *out_start = candidate->offset + 1U;
    *out_size = 1U;
    return 1;
  }
  if (candidate->asm_form_index >= M68K_ASM_FORM_SLOT_COUNT) return 0;
  form = &g_m68k_asm_forms[candidate->asm_form_index];
  if (form->mnemonic_id == M68K_ASM_MNEMONIC_NONE) return 0;
  for (index = 0U; index < candidate->operand_count; ++index)
    layout_operands[index] = normalized_layout_operand(candidate, index);
  size_suffix = candidate_effective_size_suffix(candidate);
  word_index = 1U + form->bound_word_count;
  for (extension_index = 0U; extension_index < form->extension_count; ++extension_index) {
    const M68kAsmExtensionDef *extension = &g_m68k_asm_extensions[form->extension_start + extension_index];
    size_t word_count;
    if (extension->operand_index >= candidate->operand_count) continue;
    word_count = relocation_extension_word_count(candidate->asm_form_index, extension->kind,
      &layout_operands[extension->operand_index], size_suffix);
    if (extension->operand_index == operand_index && word_count != 0U) {
      if (word_index > UINT32_MAX / 2U || word_count > UINT32_MAX / 2U) return 0;
      if (candidate->offset > UINT32_MAX - (uint32_t)(word_index * 2U)) return 0;
      *out_start = candidate->offset + (uint32_t)(word_index * 2U);
      *out_size = (uint32_t)(word_count * 2U);
      return 1;
    }
    word_index += word_count;
  }
  return 0;
}

static int relocation_fits_operand_span(const M68kFact *relocation, uint32_t span_start, uint32_t span_size) {
  uint32_t span_end;
  uint32_t relocation_end;
  if (relocation == NULL || relocation->size == 0U || span_size == 0U) return 0;
  if (span_start > UINT32_MAX - span_size || relocation->offset > UINT32_MAX - relocation->size) return 0;
  span_end = span_start + span_size;
  relocation_end = relocation->offset + relocation->size;
  return relocation->offset == span_start && relocation_end == span_end;
}

static int absolute_operand_value_matches_relocation(const M68kAsmOperandValue *operand, const M68kFact *relocation,
    char size_suffix) {
  uint32_t encoded_value = 0U;
  int has_encoded_value = 0;
  if (operand == NULL || relocation == NULL) return 0;
  if (relocation->target_addend > 0 && relocation->target_addend <= UINT32_MAX) {
    encoded_value = (uint32_t)relocation->target_addend;
    has_encoded_value = 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_IMM) {
    if (size_suffix == 'l' && relocation->size != 4U) return 0;
    if (size_suffix != 'l' && relocation->size != 2U) return 0;
    return operand->value == relocation->target_offset ||
      (has_encoded_value && operand->value == encoded_value);
  }
  if (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) {
    if (operand->ea_mode == 7U && operand->ea_reg == 1U && relocation->size == 4U)
      return operand->value == relocation->target_offset ||
        (has_encoded_value && operand->value == encoded_value);
    if (operand->ea_mode == 7U && operand->ea_reg == 4U) {
      if (size_suffix == 'l' && relocation->size != 4U) return 0;
      if (size_suffix != 'l' && relocation->size != 2U) return 0;
      return operand->value == relocation->target_offset ||
        (has_encoded_value && operand->value == encoded_value);
    }
  }
  if (operand->kind == M68K_ASM_OPERAND_ABSL && relocation->size == 4U)
    return operand->value == relocation->target_offset ||
      (has_encoded_value && operand->value == encoded_value);
  return 0;
}

static int pc_relative_operand_value_matches_relocation(const M68kDecodeCandidate *candidate, size_t operand_index,
    const M68kAsmOperandValue *operand, const M68kFact *relocation) {
  M68kAsmOperandValue asm_operands[M68K_DECODE_IR_MAX_OPERANDS];
  size_t index;
  size_t relative_base;
  int64_t target;
  if (candidate == NULL || operand == NULL || relocation == NULL || operand_index >= candidate->operand_count)
    return 0;
  if (operand->kind == M68K_ASM_OPERAND_LABEL) {
    int32_t disp = relocation->size == 1U ? signed_8(operand->value) : signed_16(operand->value);
    target = (int64_t)candidate->offset + 2 + disp;
    return target >= 0 && target <= UINT32_MAX && (uint32_t)target == relocation->target_offset;
  }
  if (!((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->ea_mode == 7U && (operand->ea_reg == 2U || operand->ea_reg == 3U))) {
    return 0;
  }
  if (operand->ea_reg == 3U &&
      (operand->full_ext_base_suppress != 0U || operand->full_ext_index_suppress != 0U ||
       operand->full_ext_base_disp_size != 0U || operand->full_ext_outer_disp_size != 0U ||
       operand->full_ext_iis != 0U)) {
    return 0;
  }
  for (index = 0U; index < candidate->operand_count; ++index) {
    asm_operands[index] = candidate->operands[index];
    asm_operands[index].kind = candidate->operand_kinds[index];
  }
  relative_base = m68k_asm_operand_relative_base_offset(candidate->asm_form_index, asm_operands,
    candidate->operand_count, candidate_effective_size_suffix(candidate), operand_index, 0);
  target = (int64_t)candidate->offset + (int64_t)relative_base + signed_16(operand->value);
  return target >= 0 && target <= UINT32_MAX && (uint32_t)target == relocation->target_offset;
}

static int operand_value_matches_relocation(const M68kDecodeCandidate *candidate, size_t operand_index,
    const M68kFact *relocation) {
  M68kAsmOperandValue operand;
  if (candidate == NULL || relocation == NULL || operand_index >= candidate->operand_count) return 0;
  operand = candidate->operands[operand_index];
  operand.kind = candidate->operand_kinds[operand_index];
  if (absolute_operand_value_matches_relocation(&operand, relocation, candidate_effective_size_suffix(candidate)))
    return 1;
  return pc_relative_operand_value_matches_relocation(candidate, operand_index, &operand, relocation);
}

static int find_unique_relocation_operand(const M68kDecodeCandidate *candidate, const M68kFact *relocation,
    size_t *out_operand_index) {
  size_t operand_index;
  size_t match_index = 0U;
  size_t match_count = 0U;
  if (candidate == NULL || relocation == NULL || out_operand_index == NULL) return 0;
  for (operand_index = 0U; operand_index < candidate->operand_count; ++operand_index) {
    uint32_t span_start = 0U;
    uint32_t span_size = 0U;
    if (!exact_operand_relocation_span(candidate, operand_index, &span_start, &span_size)) continue;
    if (!relocation_fits_operand_span(relocation, span_start, span_size)) continue;
    if (!operand_value_matches_relocation(candidate, operand_index, relocation)) continue;
    match_index = operand_index;
    ++match_count;
  }
  if (match_count != 1U) return 0;
  *out_operand_index = match_index;
  return 1;
}

static int candidate_loads_relocated_global_slot_to_a6(const M68kRenderLookup *lookup, size_t section_index,
    const M68kDecodeCandidate *candidate, size_t *out_target_section, uint32_t *out_target_offset) {
  M68kInstructionIR instruction;
  uint32_t offset;
  uint32_t end;
  if (lookup == NULL || candidate == NULL || out_target_section == NULL || out_target_offset == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!operand_is_address_register_local(&instruction.operands[1], 6U)) return 0;
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset + 2U; offset < end; ++offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section_index, offset);
    size_t operand_index = 0U;
    if (relocation == NULL) continue;
    if (!lookup_has_renderable_label(lookup, relocation->target_section_index, relocation->target_offset)) continue;
    if (!find_unique_relocation_operand(candidate, relocation, &operand_index) || operand_index != 0U) continue;
    *out_target_section = relocation->target_section_index;
    *out_target_offset = relocation->target_offset;
    return 1;
  }
  return 0;
}

static int candidate_direct_control_target(const M68kRenderLookup *lookup, size_t source_section_index,
    const M68kDecodeCandidate *candidate, size_t *out_section_index, uint32_t *out_target) {
  uint32_t offset;
  uint32_t end;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_target != NULL) *out_target = 0U;
  if (candidate == NULL || out_section_index == NULL || out_target == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_BSR &&
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR &&
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_JMP) {
    return 0;
  }
  if (lookup != NULL && candidate->operand_count == 1U) {
    end = candidate->offset + candidate->byte_count;
    for (offset = candidate->offset + 2U; offset < end; ++offset) {
      const M68kFact *relocation = lookup_relocation_at(lookup, source_section_index, offset);
      size_t operand_index = 0U;
      if (relocation == NULL) continue;
      if (!find_unique_relocation_operand(candidate, relocation, &operand_index) || operand_index != 0U) continue;
      *out_section_index = relocation->target_section_index;
      *out_target = relocation->target_offset;
      return 1;
    }
  }
  return candidate_direct_target(candidate, out_section_index, out_target);
}

static int candidate_calls_a6_lvo(const M68kDecodeCandidate *candidate, int16_t *out_lvo) {
  M68kAsmOperandValue operand;
  int16_t displacement;
  if (candidate == NULL || out_lvo == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR && candidate->mnemonic_id != M68K_ASM_MNEMONIC_JMP)
    return 0;
  if (candidate->operand_count != 1U) return 0;
  operand = candidate->operands[0];
  operand.kind = candidate->operand_kinds[0];
  if (operand.kind != M68K_ASM_OPERAND_EA || operand.ea_mode != 5U || operand.ea_reg != 6U) return 0;
  displacement = (int16_t)(operand.value & 0xFFFFU);
  if (displacement >= 0) return 0;
  *out_lvo = displacement;
  return 1;
}

static int operand_is_postinc_a7_local(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_POSTINC) return operand->value.reg == 7U;
  return operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 3U && operand->value.ea_reg == 7U;
}

static int instruction_is_local_wrapper_cleanup(const M68kInstructionIR *instruction) {
  if (instruction == NULL) return 0;
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDQ || instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADD) &&
      instruction->operand_count == 2U && operand_is_address_register_local(&instruction->operands[1], 7U)) {
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U &&
      operand_is_address_register_local(&instruction->operands[1], 7U)) {
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && instruction->operand_count == 2U &&
      operand_is_postinc_a7_local(&instruction->operands[0])) {
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count == 2U &&
      operand_is_postinc_a7_local(&instruction->operands[0])) {
    return 1;
  }
  return 0;
}

static int candidate_has_non_call_control_target(const M68kDecodeCandidate *candidate) {
  size_t target_index;
  if (candidate == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_JUMP) return 1;
  }
  return 0;
}

static int candidate_calls_a6_d0_indexed_vector(const M68kDecodeCandidate *candidate) {
  M68kAsmOperandValue operand;
  if (candidate == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR && candidate->mnemonic_id != M68K_ASM_MNEMONIC_JMP)
    return 0;
  if (candidate->operand_count != 1U) return 0;
  operand = candidate->operands[0];
  operand.kind = candidate->operand_kinds[0];
  return operand.kind == M68K_ASM_OPERAND_EA && operand.ea_mode == 6U && operand.ea_reg == 6U &&
    operand.index_is_address == 0U && operand.index_reg == 0U && operand.value == 0U;
}

static int candidate_direct_same_section_target(const M68kDecodeCandidate *candidate, size_t section_index,
    uint32_t *out_target) {
  size_t target_section_index = 0U;
  if (out_target != NULL) *out_target = 0U;
  if (!candidate_direct_target(candidate, &target_section_index, out_target)) return 0;
  return target_section_index == section_index;
}

static int candidate_direct_target(const M68kDecodeCandidate *candidate, size_t *out_section_index,
    uint32_t *out_target) {
  size_t target_index;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_target != NULL) *out_target = 0U;
  if (candidate == NULL || out_section_index == NULL || out_target == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_BSR &&
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR &&
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_JMP) {
    return 0;
  }
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->has_section == 0U) continue;
    if ((candidate->mnemonic_id == M68K_ASM_MNEMONIC_BSR ||
         candidate->mnemonic_id == M68K_ASM_MNEMONIC_JSR) &&
        target->kind != M68K_DECODE_TARGET_CALL) {
      continue;
    }
    if (candidate->mnemonic_id == M68K_ASM_MNEMONIC_JMP && target->kind != M68K_DECODE_TARGET_JUMP)
      continue;
    *out_section_index = target->section_index;
    *out_target = target->offset;
    return 1;
  }
  return 0;
}

static int candidate_any_same_section_target(const M68kDecodeCandidate *candidate, size_t section_index,
    uint32_t *out_target) {
  size_t target_index;
  if (out_target != NULL) *out_target = 0U;
  if (candidate == NULL || out_target == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->has_section == 0U || target->section_index != section_index) continue;
    if (target->kind != M68K_DECODE_TARGET_BRANCH && target->kind != M68K_DECODE_TARGET_CALL &&
        target->kind != M68K_DECODE_TARGET_JUMP) {
      continue;
    }
    *out_target = target->offset;
    return 1;
  }
  return 0;
}

static int candidate_loads_d0_lvo_immediate(const M68kDecodeCandidate *candidate, int16_t *out_lvo) {
  M68kInstructionIR instruction;
  if (out_lvo != NULL) *out_lvo = 0;
  if (candidate == NULL || out_lvo == NULL) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!instruction_loads_d0_immediate(&instruction, out_lvo)) return 0;
  return *out_lvo < 0;
}

static int render_lookup_add_indexed_vector_wrapper_branch_aliases(M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t indexed_entry,
    const char *library_name) {
  uint32_t offset = 0U;
  uint32_t segment_entry = 0U;
  int segment_valid = 0;
  if (lookup == NULL || section == NULL || accepted_start == NULL || library_name == NULL) return 0;
  while (offset < section->size) {
    const M68kDecodeCandidate *candidate;
    uint32_t target = 0U;
    if (!accepted_start_at(section, accepted_start, offset)) {
      segment_valid = 0;
      ++offset;
      continue;
    }
    candidate = find_candidate_at_offset_local(section, offset);
    if (candidate == NULL || candidate->byte_count == 0U) {
      segment_valid = 0;
      ++offset;
      continue;
    }
    if (!segment_valid) {
      segment_valid = 1;
      segment_entry = offset;
    }
    if (candidate_any_same_section_target(candidate, section->section_index, &target) && target == indexed_entry &&
        segment_entry != indexed_entry) {
      if (render_lookup_add_indexed_vector_wrapper(lookup, section->section_index, segment_entry, library_name) != 0)
        return -1;
    }
    if (candidate_terminates_a6_state(candidate)) segment_valid = 0;
    offset += candidate->byte_count;
  }
  return 0;
}

static int candidate_writes_a6_unknown(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  if (candidate == NULL) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    return instruction.operand_count >= 2U && reglist_contains_address_register_local(&instruction.operands[1], 6U);
  }
  return instruction.operand_count >= 2U && operand_is_address_register_local(&instruction.operands[1], 6U);
}

static int candidate_terminates_a6_state(const M68kDecodeCandidate *candidate) {
  return candidate != NULL && (candidate->mnemonic_id == M68K_ASM_MNEMONIC_RTS ||
    candidate->mnemonic_id == M68K_ASM_MNEMONIC_RTE || candidate->mnemonic_id == M68K_ASM_MNEMONIC_JMP);
}

static int candidate_has_local_helper_summary_fallthrough(const M68kDecodeCandidate *candidate) {
  if (candidate == NULL) return 0;
  return candidate->mnemonic_id != M68K_ASM_MNEMONIC_RTS &&
    candidate->mnemonic_id != M68K_ASM_MNEMONIC_RTR &&
    candidate->mnemonic_id != M68K_ASM_MNEMONIC_RTE &&
    candidate->mnemonic_id != M68K_ASM_MNEMONIC_STOP &&
    candidate->mnemonic_id != M68K_ASM_MNEMONIC_ILLEGAL &&
    candidate->mnemonic_id != M68K_ASM_MNEMONIC_JMP &&
    candidate->mnemonic_id != M68K_ASM_MNEMONIC_BRA;
}

static const AmigaOsCallInputInfo *amiga_vector_input_by_register(const AmigaOsLibraryVectorInfo *vector,
    uint8_t reg_kind, uint8_t reg_index) {
  const AmigaOsCallInputInfo *inputs;
  size_t input_count = 0U;
  size_t index;
  if (vector == NULL) return NULL;
  inputs = amiga_os_library_vector_inputs(vector, &input_count);
  if (inputs == NULL) return NULL;
  for (index = 0U; index < input_count; ++index) {
    if (inputs[index].reg_kind == reg_kind && inputs[index].reg_index == reg_index) return &inputs[index];
  }
  return NULL;
}

static const AmigaOsCallInputInfo *amiga_vector_input_by_stack_index(const AmigaOsLibraryVectorInfo *vector,
    size_t stack_index) {
  const AmigaOsCallInputInfo *inputs;
  size_t input_count = 0U;
  if (vector == NULL) return NULL;
  inputs = amiga_os_library_vector_inputs(vector, &input_count);
  if (inputs == NULL || stack_index >= input_count) return NULL;
  return &inputs[stack_index];
}

static const char *amiga_input_type_or_struct_name(const AmigaOsCallInputInfo *input) {
  const char *name;
  if (input == NULL) return NULL;
  if (input->struct_id != AMIGA_OS_STRUCT_ID_NONE) {
    name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, input->struct_id);
    if (name != NULL && name[0] != '\0') return name;
  }
  if (input->type_id != AMIGA_OS_TYPE_ID_NONE) {
    name = amiga_os_name(M68K_PLATFORM_NAME_TYPE, input->type_id);
    if (name != NULL && name[0] != '\0') return name;
  }
  return NULL;
}

static const char *amiga_output_type_or_struct_name(const AmigaOsCallOutputInfo *output) {
  const char *name;
  if (output == NULL) return NULL;
  if (output->struct_id != AMIGA_OS_STRUCT_ID_NONE) {
    name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, output->struct_id);
    if (name != NULL && name[0] != '\0') return name;
  }
  if (output->type_id != AMIGA_OS_TYPE_ID_NONE) {
    name = amiga_os_name(M68K_PLATFORM_NAME_TYPE, output->type_id);
    if (name != NULL && name[0] != '\0') return name;
  }
  return NULL;
}

static int format_amiga_call_input_note_render(uint16_t stack_offset, const AmigaOsCallInputInfo *input,
    char *buf, size_t buf_size) {
  const char *symbol_name;
  const char *type_name;
  const char *semantic_kind;
  const char *value_domain_name;
  size_t used;
  if (buf == NULL || buf_size == 0U || input == NULL || stack_offset == 0U) return 0;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, input->input_id);
  type_name = amiga_input_type_or_struct_name(input);
  semantic_kind = amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, input->semantic_kind_id);
  value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, input->value_domain_id);
  snprintf(buf, buf_size, "KNOWN: arg +%u", (unsigned)stack_offset);
  used = strlen(buf);
  if (symbol_name != NULL && symbol_name[0] != '\0' && used + strlen(symbol_name) + 2U < buf_size) {
    snprintf(buf + used, buf_size - used, " %s", symbol_name);
    used = strlen(buf);
  }
  if (type_name != NULL && type_name[0] != '\0' && used + strlen(type_name) + 2U < buf_size) {
    snprintf(buf + used, buf_size - used, " %s", type_name);
    used = strlen(buf);
  }
  if (semantic_kind != NULL && semantic_kind[0] != '\0' && used + strlen(semantic_kind) + 2U < buf_size) {
    snprintf(buf + used, buf_size - used, " %s", semantic_kind);
    used = strlen(buf);
  }
  if (value_domain_name != NULL && value_domain_name[0] != '\0' &&
      used + strlen(value_domain_name) + 2U < buf_size) {
    snprintf(buf + used, buf_size - used, " %s", value_domain_name);
  }
  return 1;
}

static int operand_is_predec_a7_local(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_PREDEC) return operand->value.reg == 7U;
  return operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 4U && operand->value.ea_reg == 7U;
}

static int instruction_is_long_stack_push_for_comment(const M68kInstructionIR *instruction) {
  if (instruction == NULL) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_PEA && instruction->operand_count == 1U) return 1;
  return instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction->size_suffix == 'l' &&
    instruction->operand_count == 2U && operand_is_predec_a7_local(&instruction->operands[1]);
}

static uint16_t reglist_long_stack_size_local(uint32_t mask) {
  uint16_t size = 0U;
  unsigned bit;
  for (bit = 0U; bit < 16U; ++bit) {
    if ((mask & (1UL << bit)) != 0U) size = (uint16_t)(size + 4U);
  }
  return size;
}

static int operand_is_stack_displacement_local(const M68kOperandIR *operand, int16_t *out_displacement);

static int instruction_stack_delta_for_comment(const M68kInstructionIR *instruction, int32_t *out_delta) {
  size_t operand_index;
  if (out_delta != NULL) *out_delta = 0;
  if (instruction == NULL || out_delta == NULL) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_PEA && instruction->operand_count == 1U) {
    *out_delta = 4;
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U && operand_is_predec_a7_local(&instruction->operands[1])) {
    *out_delta = 4;
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U && operand_is_postinc_a7_local(&instruction->operands[0])) {
    *out_delta = -4;
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U) {
    if (instruction->operands[0].kind == M68K_ASM_OPERAND_REGLIST &&
        operand_is_predec_a7_local(&instruction->operands[1])) {
      *out_delta = reglist_long_stack_size_local(instruction->operands[0].value.value);
      return 1;
    }
    if (operand_is_postinc_a7_local(&instruction->operands[0]) &&
        instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
      *out_delta = -(int32_t)reglist_long_stack_size_local(instruction->operands[1].value.value);
      return 1;
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U &&
      operand_is_address_register_local(&instruction->operands[1], 7U)) {
    int16_t displacement = 0;
    if (!operand_is_stack_displacement_local(&instruction->operands[0], &displacement)) return 0;
    *out_delta = -(int32_t)displacement;
    return 1;
  }
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADD ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDA ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDI ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDQ ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUB ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBA ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBI ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBQ) &&
      instruction->operand_count == 2U && operand_is_address_register_local(&instruction->operands[1], 7U)) {
    uint32_t value = 0U;
    if (!operand_is_immediate_value_local(&instruction->operands[0], &value) || value > INT16_MAX) return 0;
    *out_delta = (instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUB ||
                  instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBA ||
                  instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBI ||
                  instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBQ)
      ? (int32_t)value
      : -(int32_t)value;
    return 1;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    if (operand_is_predec_a7_local(&instruction->operands[operand_index]) ||
        operand_is_postinc_a7_local(&instruction->operands[operand_index])) {
      return 0;
    }
  }
  if (instruction->operand_count > 0U &&
      operand_is_address_register_local(&instruction->operands[instruction->operand_count - 1U], 7U)) {
    return 0;
  }
  return 1;
}

static int operand_is_stack_displacement_local(const M68kOperandIR *operand, int16_t *out_displacement) {
  uint8_t reg = 0U;
  int16_t displacement = 0;
  if (out_displacement != NULL) *out_displacement = 0;
  if (!operand_is_address_displacement_local(operand, &reg, &displacement) || reg != 7U) return 0;
  if (out_displacement != NULL) *out_displacement = displacement;
  return 1;
}

static int render_lookup_add_stack_load_input_comments(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, const M68kInstructionIR *instruction, const AmigaOsLibraryVectorInfo *vector,
    uint16_t stack_frame_depth) {
  int16_t displacement = 0;
  if (lookup == NULL || instruction == NULL || vector == NULL) return 0;
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) &&
      instruction->size_suffix == 'l' && instruction->operand_count == 2U &&
      operand_is_stack_displacement_local(&instruction->operands[0], &displacement)) {
    uint8_t reg = 0U;
    uint8_t reg_kind = 0U;
    const AmigaOsCallInputInfo *input;
    char comment[192];
    if (operand_is_data_register_local(&instruction->operands[1], &reg)) reg_kind = 1U;
    else if (instruction->operands[1].kind == M68K_ASM_OPERAND_AN) {
      reg = (uint8_t)instruction->operands[1].value.reg;
      reg_kind = 2U;
    }
    input = amiga_vector_input_by_register(vector, reg_kind, reg);
    if (input != NULL && displacement > (int16_t)stack_frame_depth &&
        format_amiga_call_input_note_render((uint16_t)(displacement - (int16_t)stack_frame_depth), input,
          comment, sizeof(comment))) {
      return render_lookup_add_instruction_comment(lookup, section_index, offset, comment) == 0;
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U && operand_is_stack_displacement_local(&instruction->operands[0], &displacement) &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST && displacement > (int16_t)stack_frame_depth) {
    uint32_t mask = instruction->operands[1].value.value;
    uint16_t stack_offset = (uint16_t)(displacement - (int16_t)stack_frame_depth);
    unsigned bit;
    int added = 0;
    for (bit = 0U; bit < 16U; ++bit) {
      uint8_t reg_kind;
      uint8_t reg_index;
      const AmigaOsCallInputInfo *input;
      char comment[192];
      if ((mask & (1UL << bit)) == 0U) continue;
      reg_kind = bit < 8U ? 1U : 2U;
      reg_index = (uint8_t)(bit < 8U ? bit : bit - 8U);
      input = amiga_vector_input_by_register(vector, reg_kind, reg_index);
      if (input != NULL && format_amiga_call_input_note_render(stack_offset, input, comment, sizeof(comment)) &&
          render_lookup_add_instruction_comment(lookup, section_index, offset, comment) != 0) {
        return 0;
      }
      if (input != NULL) added = 1;
      stack_offset = (uint16_t)(stack_offset + 4U);
    }
    return added;
  }
  return 0;
}

static const M68kDecodeCandidate *find_previous_accepted_candidate(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, uint32_t before_offset) {
  uint32_t probe;
  if (section == NULL || accepted_start == NULL || before_offset == 0U) return NULL;
  probe = before_offset;
  while (probe > 0U) {
    --probe;
    if (accepted_start_at(section, accepted_start, probe)) return find_candidate_at_offset_local(section, probe);
  }
  return NULL;
}

static int stack_frame_depth_before_candidate(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    uint32_t before_offset, uint16_t *out_depth) {
  const M68kDecodeCandidate *candidates[32];
  size_t count = 0U;
  int32_t depth = 0;
  uint32_t cursor;
  if (out_depth != NULL) *out_depth = 0U;
  if (section == NULL || accepted_start == NULL || out_depth == NULL) return 0;
  cursor = before_offset;
  while (count < sizeof(candidates) / sizeof(candidates[0])) {
    const M68kDecodeCandidate *candidate = find_previous_accepted_candidate(section, accepted_start, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    if (candidate->offset + candidate->byte_count != cursor) break;
    candidates[count++] = candidate;
    cursor = candidate->offset;
  }
  while (count > 0U) {
    M68kInstructionIR instruction;
    int32_t delta = 0;
    --count;
    if (m68k_decode_candidate_to_instruction(candidates[count], &instruction) != 0) return 0;
    if (!instruction_stack_delta_for_comment(&instruction, &delta)) return 0;
    depth += delta;
    if (depth < 0 || depth > UINT16_MAX) return 0;
  }
  *out_depth = (uint16_t)depth;
  return 1;
}

static int render_lookup_add_call_setup_comments_for_vector(M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t call_offset,
    const AmigaOsLibraryVectorInfo *vector, int allow_register_stack_loads) {
  uint32_t cursor;
  uint16_t push_stack_offset = 4U;
  size_t scan_count = 0U;
  if (lookup == NULL || section == NULL || accepted_start == NULL || vector == NULL) return 0;
  cursor = call_offset;
  while (scan_count < 12U) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    uint16_t stack_frame_depth = 0U;
    candidate = find_previous_accepted_candidate(section, accepted_start, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    if (allow_register_stack_loads &&
        stack_frame_depth_before_candidate(section, accepted_start, candidate->offset, &stack_frame_depth) &&
        render_lookup_add_stack_load_input_comments(lookup, section->section_index, candidate->offset, &instruction,
        vector, stack_frame_depth)) {
      cursor = candidate->offset;
      ++scan_count;
      continue;
    }
    if (instruction_is_long_stack_push_for_comment(&instruction)) {
      const AmigaOsCallInputInfo *input =
        amiga_vector_input_by_stack_index(vector, (size_t)((push_stack_offset / 4U) - 1U));
      char comment[192];
      if (input == NULL ||
          !format_amiga_call_input_note_render(push_stack_offset, input, comment, sizeof(comment)) ||
          render_lookup_add_instruction_comment(lookup, section->section_index, candidate->offset, comment) != 0) {
        break;
      }
      push_stack_offset = (uint16_t)(push_stack_offset + 4U);
      cursor = candidate->offset;
      ++scan_count;
      continue;
    }
    break;
  }
  return 0;
}

static int recovered_function_arg_temp_add(M68kRenderRecoveredFunctionArg *args, size_t *arg_count,
    size_t arg_capacity, size_t section_index, uint32_t function_offset, uint16_t stack_offset,
    uint8_t reg_kind, uint8_t reg_index, const AmigaOsCallInputInfo *input) {
  size_t index;
  if (args == NULL || arg_count == NULL || input == NULL || stack_offset == 0U ||
      reg_kind == 0U || reg_index >= 8U) {
    return 0;
  }
  for (index = 0U; index < *arg_count; ++index) {
    M68kRenderRecoveredFunctionArg *arg = &args[index];
    if (arg->section_index == section_index && arg->function_offset == function_offset &&
        arg->stack_offset == stack_offset && arg->reg_kind == reg_kind && arg->reg_index == reg_index) {
      return arg->input == input ? 0 : -1;
    }
  }
  if (*arg_count >= arg_capacity) return -1;
  memset(&args[*arg_count], 0, sizeof(args[*arg_count]));
  args[*arg_count].section_index = section_index;
  args[*arg_count].function_offset = function_offset;
  args[*arg_count].stack_offset = stack_offset;
  args[*arg_count].reg_kind = reg_kind;
  args[*arg_count].reg_index = reg_index;
  args[*arg_count].input = input;
  *arg_count += 1U;
  return 0;
}

static int collect_recovered_function_args_from_stack_load_instruction(
    M68kRenderRecoveredFunctionArg *args, size_t *arg_count, size_t arg_capacity,
    size_t section_index, uint32_t function_offset, const M68kInstructionIR *instruction,
    const AmigaOsLibraryVectorInfo *vector, uint16_t stack_frame_depth) {
  int16_t displacement = 0;
  if (args == NULL || arg_count == NULL || instruction == NULL || vector == NULL) return 0;
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) &&
      instruction->size_suffix == 'l' && instruction->operand_count == 2U &&
      operand_is_stack_displacement_local(&instruction->operands[0], &displacement) &&
      displacement > (int16_t)stack_frame_depth) {
    uint8_t reg = 0U;
    uint8_t reg_kind = 0U;
    const AmigaOsCallInputInfo *input;
    if (operand_is_data_register_local(&instruction->operands[1], &reg)) reg_kind = 1U;
    else if (instruction->operands[1].kind == M68K_ASM_OPERAND_AN) {
      reg = (uint8_t)instruction->operands[1].value.reg;
      reg_kind = 2U;
    }
    input = amiga_vector_input_by_register(vector, reg_kind, reg);
    if (input != NULL) {
      return recovered_function_arg_temp_add(args, arg_count, arg_capacity, section_index, function_offset,
        (uint16_t)(displacement - (int16_t)stack_frame_depth), reg_kind, reg, input);
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U &&
      operand_is_stack_displacement_local(&instruction->operands[0], &displacement) &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST &&
      displacement > (int16_t)stack_frame_depth) {
    uint32_t mask = instruction->operands[1].value.value;
    uint16_t stack_offset = (uint16_t)(displacement - (int16_t)stack_frame_depth);
    unsigned bit;
    for (bit = 0U; bit < 16U; ++bit) {
      uint8_t reg_kind;
      uint8_t reg_index;
      const AmigaOsCallInputInfo *input;
      if ((mask & (1UL << bit)) == 0U) continue;
      reg_kind = bit < 8U ? 1U : 2U;
      reg_index = (uint8_t)(bit < 8U ? bit : bit - 8U);
      input = amiga_vector_input_by_register(vector, reg_kind, reg_index);
      if (input != NULL && recovered_function_arg_temp_add(args, arg_count, arg_capacity, section_index,
          function_offset, stack_offset, reg_kind, reg_index, input) != 0) {
        return -1;
      }
      stack_offset = (uint16_t)(stack_offset + 4U);
    }
  }
  return 0;
}

static int render_lookup_collect_recovered_function_args_from_wrapper(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t wrapper_section_index, uint32_t wrapper_offset,
    const AmigaOsLibraryVectorInfo *expected_vector) {
  const M68kDecodeSectionIR *section;
  M68kRenderPlatformState state;
  M68kRenderRecoveredFunctionArg args[16];
  size_t arg_count = 0U;
  uint32_t cursor;
  uint16_t stack_frame_depth = 0U;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || expected_vector == NULL ||
      wrapper_section_index >= decode->section_count) {
    return 0;
  }
  section = &decode->sections[wrapper_section_index];
  if (!accepted_start_at(section, accepted_start[wrapper_section_index], wrapper_offset)) return 0;
  memset(&state, 0, sizeof(state));
  memset(args, 0, sizeof(args));
  cursor = wrapper_offset;
  while (cursor < section->size && cursor - wrapper_offset < 256U) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const AmigaOsLibraryVectorInfo *vector;
    int32_t delta = 0;
    if (!accepted_start_at(section, accepted_start[wrapper_section_index], cursor)) break;
    candidate = find_candidate_at_offset_local(section, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    platform_state_apply_policy_register_seeds(&state, lookup->policy, section->section_index, cursor);
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
    vector = attach_amiga_lvo_symbol_if_known(&state, &instruction);
    if (vector == NULL) {
      vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start[wrapper_section_index],
        candidate, &instruction);
    }
    if (vector == NULL) {
      vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &state, section, candidate);
    }
    if (vector == expected_vector) {
      size_t index;
      for (index = 0U; index < arg_count; ++index) {
        if (render_lookup_add_recovered_function_arg(lookup, args[index].section_index, args[index].function_offset,
            args[index].stack_offset, args[index].reg_kind, args[index].reg_index, args[index].input) != 0) {
          return -1;
        }
      }
      return 0;
    }
    if (vector != NULL || candidate_has_non_call_control_target(candidate)) break;
    if (collect_recovered_function_args_from_stack_load_instruction(args, &arg_count,
        sizeof(args) / sizeof(args[0]), section->section_index, wrapper_offset, &instruction, expected_vector,
        stack_frame_depth) != 0) {
      return -1;
    }
    if (!instruction_stack_delta_for_comment(&instruction, &delta)) break;
    if (delta < 0 && (uint32_t)(-delta) > (uint32_t)stack_frame_depth) break;
    if (delta > 0 && (uint32_t)delta > UINT16_MAX - (uint32_t)stack_frame_depth) break;
    stack_frame_depth = (uint16_t)((int32_t)stack_frame_depth + delta);
    platform_state_update_d0_lvo_after_instruction(&state, &instruction);
    platform_state_update_after_instruction(&state, lookup, &instruction);
    if (!candidate_has_local_helper_summary_fallthrough(candidate)) break;
    cursor += candidate->byte_count;
  }
  return 0;
}

static int render_lookup_infer_amiga_recovered_local_call_summaries(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  M68kRenderPlatformState platform_state;
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  memset(&platform_state, 0, sizeof(platform_state));
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      const AmigaOsLibraryVectorInfo *wrapper_call_vector;
      const AmigaOsLibraryVectorInfo *direct_wrapper_vector;
      const AmigaOsLibraryVectorInfo *helper_call_vector;
      const AmigaOsLibraryVectorInfo *vector;
      size_t target_section_index = 0U;
      uint32_t target_offset = 0U;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      platform_state_apply_policy_register_seeds(&platform_state, lookup->policy, section->section_index,
        candidate->offset);
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
      wrapper_call_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &platform_state, section, candidate);
      direct_wrapper_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start,
        section->section_index, candidate);
      helper_call_vector = (wrapper_call_vector == NULL && direct_wrapper_vector == NULL)
        ? resolve_amiga_local_helper_call_vector(lookup, decode, accepted_start, section->section_index, candidate)
        : NULL;
      vector = direct_wrapper_vector != NULL ? direct_wrapper_vector :
        (wrapper_call_vector != NULL ? wrapper_call_vector : helper_call_vector);
      if (vector != NULL &&
          candidate_direct_control_target(lookup, section->section_index, candidate, &target_section_index,
            &target_offset) &&
          render_lookup_add_recovered_local_call_summary(lookup, target_section_index, target_offset, vector) != 0) {
        return -1;
      }
      platform_state_update_d0_lvo_after_instruction(&platform_state, &instruction);
      platform_state_update_after_instruction(&platform_state, lookup, &instruction);
    }
  }
  return 0;
}

static int render_lookup_infer_amiga_recovered_function_args(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  M68kRenderPlatformState platform_state;
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  memset(&platform_state, 0, sizeof(platform_state));
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      const AmigaOsLibraryVectorInfo *wrapper_call_vector;
      const AmigaOsLibraryVectorInfo *direct_wrapper_vector;
      const AmigaOsLibraryVectorInfo *vector;
      size_t target_section_index = 0U;
      uint32_t target_offset = 0U;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      platform_state_apply_policy_register_seeds(&platform_state, lookup->policy, section->section_index,
        candidate->offset);
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
      wrapper_call_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &platform_state, section, candidate);
      direct_wrapper_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start,
        section->section_index, candidate);
      vector = direct_wrapper_vector != NULL ? direct_wrapper_vector : wrapper_call_vector;
      if (vector != NULL &&
          candidate_direct_control_target(lookup, section->section_index, candidate, &target_section_index,
            &target_offset) &&
          render_lookup_collect_recovered_function_args_from_wrapper(lookup, decode, accepted_start,
            target_section_index, target_offset, vector) != 0) {
        return -1;
      }
      platform_state_update_d0_lvo_after_instruction(&platform_state, &instruction);
      platform_state_update_after_instruction(&platform_state, lookup, &instruction);
    }
  }
  return 0;
}

static int amiga_output_has_typed_info(const AmigaOsCallOutputInfo *output) {
  if (output == NULL || output->reg_kind == AMIGA_OS_REGISTER_NONE || output->reg_index >= 8U) return 0;
  return amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, output->output_id) != NULL ||
    amiga_output_type_or_struct_name(output) != NULL ||
    amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, output->semantic_kind_id) != NULL ||
    amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, output->value_domain_id) != NULL;
}

static void typed_state_clear_reg(M68kRenderTypedState *state, uint8_t reg_kind, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == 1U) {
    state->data_regs[reg_index].known = 0U;
    state->data_regs[reg_index].output = NULL;
  } else if (reg_kind == 2U) {
    state->addr_regs[reg_index].known = 0U;
    state->addr_regs[reg_index].output = NULL;
  }
}

static void typed_state_set_reg(M68kRenderTypedState *state, uint8_t reg_kind, uint8_t reg_index,
    const AmigaOsCallOutputInfo *output) {
  if (state == NULL || output == NULL || reg_index >= 8U || !amiga_output_has_typed_info(output)) return;
  if (reg_kind == 1U) {
    state->data_regs[reg_index].known = 1U;
    state->data_regs[reg_index].output = output;
  } else if (reg_kind == 2U) {
    state->addr_regs[reg_index].known = 1U;
    state->addr_regs[reg_index].output = output;
  }
}

static void typed_state_clear_all(M68kRenderTypedState *state) {
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
}

static const AmigaOsCallOutputInfo *typed_state_output_for_operand(const M68kRenderTypedState *state,
    const M68kOperandIR *operand, uint8_t *out_reg_kind, uint8_t *out_reg_index) {
  uint8_t reg = 0U;
  if (out_reg_kind != NULL) *out_reg_kind = 0U;
  if (out_reg_index != NULL) *out_reg_index = 0U;
  if (state == NULL || operand == NULL) return NULL;
  if (operand_is_data_register_local(operand, &reg)) {
    if (out_reg_kind != NULL) *out_reg_kind = 1U;
    if (out_reg_index != NULL) *out_reg_index = reg;
    return state->data_regs[reg].known ? state->data_regs[reg].output : NULL;
  }
  if (operand_address_register_index_local(operand, &reg)) {
    if (out_reg_kind != NULL) *out_reg_kind = 2U;
    if (out_reg_index != NULL) *out_reg_index = reg;
    return state->addr_regs[reg].known ? state->addr_regs[reg].output : NULL;
  }
  return NULL;
}

static int instruction_stores_typed_reg_to_a6_slot(const M68kRenderTypedState *state,
    const M68kInstructionIR *instruction, int a6_is_known_library_base, int16_t *out_displacement,
    const AmigaOsCallOutputInfo **out_output) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  const AmigaOsCallOutputInfo *output;
  if (out_displacement != NULL) *out_displacement = 0;
  if (out_output != NULL) *out_output = NULL;
  if (state == NULL || instruction == NULL || out_displacement == NULL || out_output == NULL) return 0;
  if (a6_is_known_library_base) return 0;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || instruction->size_suffix != 'l' ||
      instruction->operand_count != 2U) {
    return 0;
  }
  output = typed_state_output_for_operand(state, &instruction->operands[0], NULL, NULL);
  if (output == NULL) return 0;
  if (!operand_is_address_displacement_local(&instruction->operands[1], &base_reg, &displacement) ||
      base_reg != 6U) {
    return 0;
  }
  *out_displacement = displacement;
  *out_output = output;
  return 1;
}

static int instruction_operand_writes_register_from_metadata(const M68kInstructionIR *instruction,
    size_t operand_index) {
  const M68kSimFormMetadata *metadata;
  uint8_t access_kind;
  if (instruction == NULL || operand_index >= instruction->operand_count) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return operand_index + 1U == instruction->operand_count;
  access_kind = metadata->operand_access_kinds[operand_index];
  return access_kind == M68K_SIM_ACCESS_REGISTER_WRITE ||
    access_kind == M68K_SIM_ACCESS_REGISTER_LIST_WRITE;
}

static void typed_state_update_after_instruction(M68kRenderTypedState *state, const M68kInstructionIR *instruction,
    const AmigaOsLibraryVectorInfo *vector) {
  const AmigaOsCallOutputInfo *source_output = NULL;
  uint8_t dest_reg = 0U;
  size_t operand_index;
  uint8_t bit;
  if (state == NULL || instruction == NULL) return;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_JSR ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_BSR) {
    typed_state_clear_all(state);
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count >= 2U &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
    for (bit = 0U; bit < 8U; ++bit) {
      if ((instruction->operands[1].value.value & (1UL << bit)) != 0U) typed_state_clear_reg(state, 1U, bit);
      if ((instruction->operands[1].value.value & (1UL << (8U + bit))) != 0U) typed_state_clear_reg(state, 2U, bit);
    }
  } else if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
              instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) &&
      instruction->operand_count == 2U) {
    source_output = typed_state_output_for_operand(state, &instruction->operands[0], NULL, NULL);
    if (operand_is_data_register_local(&instruction->operands[1], &dest_reg)) {
      typed_state_clear_reg(state, 1U, dest_reg);
      if (source_output != NULL) typed_state_set_reg(state, 1U, dest_reg, source_output);
    } else if (operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
      typed_state_clear_reg(state, 2U, dest_reg);
      if (source_output != NULL) typed_state_set_reg(state, 2U, dest_reg, source_output);
    }
  } else if (instruction->operand_count != 0U) {
    for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
      const M68kOperandIR *operand = &instruction->operands[operand_index];
      if (!instruction_operand_writes_register_from_metadata(instruction, operand_index)) continue;
      if (operand_is_data_register_local(operand, &dest_reg)) {
        typed_state_clear_reg(state, 1U, dest_reg);
      } else if (operand_address_register_index_local(operand, &dest_reg)) {
        typed_state_clear_reg(state, 2U, dest_reg);
      }
    }
  }
  if (vector != NULL && amiga_output_has_typed_info(&vector->output)) {
    typed_state_set_reg(state, vector->output.reg_kind, vector->output.reg_index, &vector->output);
  }
}

static int render_lookup_infer_amiga_typed_slot_effects(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  M68kRenderPlatformState platform_state;
  M68kRenderTypedState typed_state;
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  memset(&platform_state, 0, sizeof(platform_state));
  typed_state_clear_all(&typed_state);
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    uint32_t expected_offset = 0U;
    int have_expected_offset = 0;
    platform_state_clear_d0_lvo(&platform_state);
    typed_state_clear_all(&typed_state);
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      const AmigaOsLibraryVectorInfo *platform_vector;
      const AmigaOsLibraryVectorInfo *immediate_vector;
      const AmigaOsLibraryVectorInfo *wrapper_call_vector;
      const AmigaOsLibraryVectorInfo *direct_wrapper_vector;
      const AmigaOsLibraryVectorInfo *helper_call_vector = NULL;
      const AmigaOsLibraryVectorInfo *chosen_vector;
      const AmigaOsCallOutputInfo *stored_output = NULL;
      int16_t slot_displacement = 0;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      if (have_expected_offset && candidate->offset != expected_offset) {
        memset(&platform_state, 0, sizeof(platform_state));
        typed_state_clear_all(&typed_state);
      }
      platform_state_apply_policy_register_seeds(&platform_state, lookup->policy, section->section_index,
        candidate->offset);
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
      platform_vector = attach_amiga_lvo_symbol_if_known(&platform_state, &instruction);
      immediate_vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start[section_index],
        candidate, &instruction);
      wrapper_call_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &platform_state, section, candidate);
      direct_wrapper_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start,
        section->section_index, candidate);
      if (platform_vector == NULL && immediate_vector == NULL && wrapper_call_vector == NULL &&
          direct_wrapper_vector == NULL) {
        helper_call_vector = resolve_amiga_local_helper_call_vector(lookup, decode, accepted_start,
          section->section_index, candidate);
      }
      chosen_vector = platform_vector != NULL ? platform_vector :
        (direct_wrapper_vector != NULL ? direct_wrapper_vector :
        (wrapper_call_vector != NULL ? wrapper_call_vector :
        (immediate_vector != NULL ? immediate_vector : helper_call_vector)));
      if (instruction_stores_typed_reg_to_a6_slot(&typed_state, &instruction,
          platform_state.address_base_known[6U] != 0U, &slot_displacement, &stored_output) &&
          render_lookup_add_typed_slot_effect(lookup, section->section_index, candidate->offset,
            slot_displacement, stored_output) != 0) {
        return -1;
      }
      typed_state_update_after_instruction(&typed_state, &instruction, chosen_vector);
      platform_state_update_d0_lvo_after_instruction(&platform_state, &instruction);
      platform_state_update_after_instruction(&platform_state, lookup, &instruction);
      if (candidate_terminates_a6_state(candidate)) {
        typed_state_clear_all(&typed_state);
      }
      expected_offset = candidate->offset + candidate->byte_count;
      have_expected_offset = 1;
    }
  }
  return 0;
}

static void data_pointer_state_clear_all(M68kRenderDataPointerState *state) {
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
}

static void data_pointer_state_clear_reg(M68kRenderDataPointerState *state, uint8_t reg_kind, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == AMIGA_OS_REGISTER_DATA) state->data_regs[reg_index].known = 0U;
  else if (reg_kind == AMIGA_OS_REGISTER_ADDRESS) state->addr_regs[reg_index].known = 0U;
}

static void data_pointer_state_set_reg(M68kRenderDataPointerState *state, uint8_t reg_kind, uint8_t reg_index,
    size_t section_index, uint32_t offset) {
  M68kRenderDataPointerValue *value;
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == AMIGA_OS_REGISTER_DATA) value = &state->data_regs[reg_index];
  else if (reg_kind == AMIGA_OS_REGISTER_ADDRESS) value = &state->addr_regs[reg_index];
  else return;
  value->known = 1U;
  value->section_index = section_index;
  value->offset = offset;
}

static const M68kRenderDataPointerValue *data_pointer_state_value_for_operand(
    const M68kRenderDataPointerState *state, const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  if (state == NULL || operand == NULL) return NULL;
  if (operand_is_data_register_local(operand, &reg)) return state->data_regs[reg].known ? &state->data_regs[reg] : NULL;
  if (operand_address_register_index_local(operand, &reg)) return state->addr_regs[reg].known ? &state->addr_regs[reg] : NULL;
  return NULL;
}

static int candidate_loads_data_target_to_address_reg(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, size_t *out_section_index, uint32_t *out_offset, uint8_t *out_reg) {
  size_t target_index;
  uint8_t dest_reg = 0U;
  if (candidate == NULL || instruction == NULL || out_section_index == NULL || out_offset == NULL ||
      out_reg == NULL || instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA || instruction->operand_count != 2U ||
      !operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
    return 0;
  }
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind != M68K_DECODE_TARGET_DATA || target->has_section == 0U ||
        target->has_operand == 0U || target->operand_index != 0U) {
      continue;
    }
    *out_section_index = target->section_index;
    *out_offset = target->offset;
    *out_reg = dest_reg;
    return 1;
  }
  return 0;
}

static void data_pointer_state_update_after_instruction(M68kRenderDataPointerState *state,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction) {
  const M68kRenderDataPointerValue *source_value = NULL;
  size_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  uint8_t dest_reg = 0U;
  size_t operand_index;
  if (state == NULL || instruction == NULL) return;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_JSR ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_BSR) {
    data_pointer_state_clear_all(state);
    return;
  }
  if (candidate_loads_data_target_to_address_reg(candidate, instruction, &target_section_index, &target_offset,
      &dest_reg)) {
    data_pointer_state_set_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, target_section_index, target_offset);
    return;
  }
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) &&
      instruction->operand_count == 2U) {
    source_value = data_pointer_state_value_for_operand(state, &instruction->operands[0]);
    if (operand_is_data_register_local(&instruction->operands[1], &dest_reg)) {
      data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_DATA, dest_reg);
      if (source_value != NULL)
        data_pointer_state_set_reg(state, AMIGA_OS_REGISTER_DATA, dest_reg, source_value->section_index,
          source_value->offset);
      return;
    }
    if (operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
      data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg);
      if (source_value != NULL)
        data_pointer_state_set_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, source_value->section_index,
          source_value->offset);
      return;
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count >= 2U &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
    uint8_t bit;
    for (bit = 0U; bit < 8U; ++bit) {
      if ((instruction->operands[1].value.value & (1UL << bit)) != 0U)
        data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_DATA, bit);
      if ((instruction->operands[1].value.value & (1UL << (8U + bit))) != 0U)
        data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_ADDRESS, bit);
    }
    return;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (!instruction_operand_writes_register_from_metadata(instruction, operand_index)) continue;
    if (operand_is_data_register_local(operand, &dest_reg))
      data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_DATA, dest_reg);
    else if (operand_address_register_index_local(operand, &dest_reg))
      data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg);
  }
}

static int render_find_c_string_span(const M68kDecodeSectionIR *section, uint32_t offset, uint32_t *out_size) {
  uint32_t cursor;
  uint32_t text_size = 0U;
  if (out_size != NULL) *out_size = 0U;
  if (section == NULL || section->data == NULL || offset >= section->size || out_size == NULL) return 0;
  cursor = offset;
  while (cursor < section->size && section->data[cursor] != 0U) {
    if (!byte_is_quoted_string_safe(section->data[cursor])) return 0;
    ++cursor;
    ++text_size;
  }
  if (cursor >= section->size || section->data[cursor] != 0U || text_size < 2U) return 0;
  *out_size = text_size + 1U;
  return 1;
}

static int render_lookup_add_string_spans_for_vector_inputs(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    const AmigaOsLibraryVectorInfo *vector, const M68kRenderDataPointerState *state) {
  const AmigaOsCallInputInfo *inputs;
  size_t input_count = 0U;
  size_t index;
  if (lookup == NULL || decode == NULL || vector == NULL || state == NULL) return 0;
  inputs = amiga_os_library_vector_inputs(vector, &input_count);
  if (inputs == NULL) return 0;
  for (index = 0U; index < input_count; ++index) {
    const AmigaOsCallInputInfo *input = &inputs[index];
    const M68kRenderDataPointerValue *value = NULL;
    const M68kDecodeSectionIR *section;
    uint32_t string_size = 0U;
    if (input->semantic_kind_id != AMIGA_OS_SEMANTIC_KIND_ID_STRING_PTR || input->reg_index >= 8U) continue;
    if (input->reg_kind == AMIGA_OS_REGISTER_DATA) value = state->data_regs[input->reg_index].known ?
      &state->data_regs[input->reg_index] : NULL;
    else if (input->reg_kind == AMIGA_OS_REGISTER_ADDRESS) value = state->addr_regs[input->reg_index].known ?
      &state->addr_regs[input->reg_index] : NULL;
    if (value == NULL || value->section_index >= decode->section_count) continue;
    section = &decode->sections[value->section_index];
    if (!render_find_c_string_span(section, value->offset, &string_size)) continue;
    if (render_lookup_add_string_span(lookup, value->section_index, value->offset, string_size) != 0) return -1;
  }
  return 0;
}

static int append_render_lookup_recovered_local_call_summaries_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->recovered_local_call_summary_count; ++index) {
    const M68kRenderRecoveredLocalCallSummary *summary = &lookup->recovered_local_call_summaries[index];
    const AmigaOsCallOutputInfo *output;
    const char *symbol_name;
    const char *type_name;
    const char *semantic_kind;
    const char *value_domain_name;
    if (summary->section_index != section_analysis->section_index || summary->vector == NULL) continue;
    output = &summary->vector->output;
    if (output->reg_kind == AMIGA_OS_REGISTER_NONE || output->reg_index >= 8U) continue;
    symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, output->output_id);
    type_name = amiga_output_type_or_struct_name(output);
    semantic_kind = amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, output->semantic_kind_id);
    value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, output->value_domain_id);
    if ((symbol_name == NULL || symbol_name[0] == '\0') &&
        (type_name == NULL || type_name[0] == '\0') &&
        (semantic_kind == NULL || semantic_kind[0] == '\0') &&
        (value_domain_name == NULL || value_domain_name[0] == '\0')) {
      continue;
    }
    if (m68k_ir_section_analysis_append_recovered_local_call_summary(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, summary->target_offset, M68K_PLATFORM_EFFECT_SET_TYPED_REG,
        output->reg_kind, output->reg_index, 0U, 0U, 0U, 0, NULL, symbol_name, type_name, semantic_kind,
        value_domain_name, 0U, 0) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_render_lookup_recovered_function_args_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->recovered_function_arg_count; ++index) {
    const M68kRenderRecoveredFunctionArg *arg = &lookup->recovered_function_args[index];
    const AmigaOsCallInputInfo *input = arg->input;
    const char *symbol_name;
    const char *type_name;
    const char *semantic_kind;
    const char *value_domain_name;
    if (arg->section_index != section_analysis->section_index || input == NULL) continue;
    symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, input->input_id);
    type_name = amiga_input_type_or_struct_name(input);
    semantic_kind = amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, input->semantic_kind_id);
    value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, input->value_domain_id);
    if (m68k_ir_section_analysis_append_recovered_function_arg(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, arg->function_offset, arg->stack_offset, arg->reg_kind, arg->reg_index,
        NULL, symbol_name, type_name, semantic_kind, value_domain_name, 0U, 0) != 0) {
      return -1;
    }
  }
  return 0;
}

static int global_base_observation_add(M68kRenderGlobalBaseObservation **observations, size_t *count,
    size_t *capacity, size_t section_index, uint32_t offset, int16_t lvo) {
  size_t index;
  if (observations == NULL || count == NULL || capacity == NULL) return -1;
  for (index = 0U; index < *count; ++index) {
    M68kRenderGlobalBaseObservation *observation = &(*observations)[index];
    size_t lvo_index;
    if (observation->section_index != section_index || observation->offset != offset) continue;
    for (lvo_index = 0U; lvo_index < observation->lvo_count; ++lvo_index)
      if (observation->lvos[lvo_index] == lvo) return 0;
    if (observation->lvo_count < sizeof(observation->lvos) / sizeof(observation->lvos[0]))
      observation->lvos[observation->lvo_count++] = lvo;
    return 0;
  }
  if (*count == *capacity) {
    size_t next_capacity = *capacity == 0U ? 16U : *capacity * 2U;
    M68kRenderGlobalBaseObservation *grown =
      (M68kRenderGlobalBaseObservation *)realloc(*observations, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    *observations = grown;
    *capacity = next_capacity;
  }
  memset(&(*observations)[*count], 0, sizeof((*observations)[*count]));
  (*observations)[*count].section_index = section_index;
  (*observations)[*count].offset = offset;
  (*observations)[*count].lvos[0] = lvo;
  (*observations)[*count].lvo_count = 1U;
  ++(*count);
  return 0;
}

static int library_has_all_observed_lvos(const char *base_name, const M68kRenderGlobalBaseObservation *observation) {
  size_t index;
  if (base_name == NULL || observation == NULL || observation->lvo_count == 0U) return 0;
  for (index = 0U; index < observation->lvo_count; ++index) {
    if (amiga_os_find_library_vector(base_name, observation->lvos[index]) == NULL) return 0;
  }
  return 1;
}

static int library_id_seen_local(const uint16_t *ids, size_t count, uint16_t id) {
  size_t index;
  for (index = 0U; index < count; ++index)
    if (ids[index] == id) return 1;
  return 0;
}

static const char *unique_library_for_observed_lvos(const M68kRenderGlobalBaseObservation *observation) {
  uint16_t seen_ids[AMIGA_OS_LIBRARY_VECTOR_COUNT];
  size_t seen_count = 0U;
  const char *matched_library = NULL;
  size_t index;
  if (observation == NULL || observation->lvo_count == 0U) return NULL;
  for (index = 0U; index < AMIGA_OS_LIBRARY_VECTOR_COUNT; ++index) {
    const AmigaOsLibraryVectorInfo *vector = amiga_os_library_vector_at(index);
    const char *library_name;
    const char *base_name;
    if (vector == NULL) continue;
    if (library_id_seen_local(seen_ids, seen_count, vector->library_id)) continue;
    if (seen_count < sizeof(seen_ids) / sizeof(seen_ids[0])) seen_ids[seen_count++] = vector->library_id;
    library_name = amiga_os_name(M68K_PLATFORM_NAME_LIBRARY, vector->library_id);
    base_name = amiga_os_find_library_base_name(library_name);
    if (library_name == NULL || base_name == NULL) continue;
    if (!library_has_all_observed_lvos(base_name, observation)) continue;
    if (matched_library != NULL && strcmp(matched_library, library_name) != 0) return NULL;
    matched_library = library_name;
  }
  return matched_library;
}

static int render_lookup_add_global_base_slot(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    const char *library_name, size_t source_section_index, uint32_t source_offset) {
  size_t index;
  M68kRenderGlobalBaseSlot *grown;
  size_t next_capacity;
  uint8_t has_source = source_section_index != SIZE_MAX && source_offset != UINT32_MAX;
  if (lookup == NULL || library_name == NULL || library_name[0] == '\0') return 0;
  for (index = 0U; index < lookup->global_base_slot_count; ++index) {
    M68kRenderGlobalBaseSlot *slot = &lookup->global_base_slots[index];
    if (slot->section_index == section_index && slot->offset == offset) {
      snprintf(slot->library_name, sizeof(slot->library_name), "%s", library_name);
      if (has_source && slot->has_source == 0U) {
        slot->source_section_index = source_section_index;
        slot->source_offset = source_offset;
        slot->has_source = 1U;
      }
      return 0;
    }
  }
  if (lookup->global_base_slot_count == lookup->global_base_slot_capacity) {
    next_capacity = lookup->global_base_slot_capacity == 0U ? 8U : lookup->global_base_slot_capacity * 2U;
    grown = (M68kRenderGlobalBaseSlot *)realloc(lookup->global_base_slots, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->global_base_slots = grown;
    lookup->global_base_slot_capacity = next_capacity;
  }
  memset(&lookup->global_base_slots[lookup->global_base_slot_count], 0,
    sizeof(lookup->global_base_slots[lookup->global_base_slot_count]));
  lookup->global_base_slots[lookup->global_base_slot_count].section_index = section_index;
  lookup->global_base_slots[lookup->global_base_slot_count].offset = offset;
  lookup->global_base_slots[lookup->global_base_slot_count].source_section_index = source_section_index;
  lookup->global_base_slots[lookup->global_base_slot_count].source_offset = source_offset;
  lookup->global_base_slots[lookup->global_base_slot_count].has_source = has_source;
  snprintf(lookup->global_base_slots[lookup->global_base_slot_count].library_name,
    sizeof(lookup->global_base_slots[lookup->global_base_slot_count].library_name), "%s", library_name);
  ++lookup->global_base_slot_count;
  return 0;
}

static int render_lookup_add_base_field_slot_with_symbol(M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement, const char *library_name, const char *symbol_name, uint8_t value_kind,
    size_t source_section_index, uint32_t source_offset) {
  size_t index;
  M68kRenderBaseFieldSlot *grown;
  size_t next_capacity;
  uint8_t has_source = source_section_index != SIZE_MAX && source_offset != UINT32_MAX;
  const char *slot_library_name = library_name != NULL ? library_name : "";
  if (lookup == NULL || owner_name == NULL || owner_name[0] == '\0') return 0;
  if (value_kind == M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE) {
    if (slot_library_name[0] == '\0' || amiga_os_find_library_base_name(slot_library_name) == NULL) return 0;
  } else if (value_kind == M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS) {
    if (strcmp(owner_name, "__amiga_app_base__") != 0) return 0;
  } else if (symbol_name == NULL || symbol_name[0] == '\0') {
    return 0;
  }
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    if (strcmp(slot->owner_name, owner_name) != 0 || slot->displacement != displacement) continue;
    if (slot->conflicted) return 0;
    if (slot->value_kind == M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS && value_kind != M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS) {
      slot->value_kind = value_kind;
      if (slot_library_name[0] != '\0') {
        snprintf(slot->library_name, sizeof(slot->library_name), "%s", slot_library_name);
      }
      if (symbol_name != NULL && symbol_name[0] != '\0') {
        snprintf(slot->symbol_name, sizeof(slot->symbol_name), "%s", symbol_name);
      }
    } else if (value_kind == M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS) {
      /* The generic app-state access confirms the slot exists but must not erase a better name. */
    } else if (slot->value_kind != value_kind ||
        (slot->library_name[0] != '\0' && strcmp(slot->library_name, slot_library_name) != 0) ||
        (slot->symbol_name[0] != '\0' && (symbol_name == NULL || strcmp(slot->symbol_name, symbol_name) != 0)) ||
        (slot->symbol_name[0] == '\0' && symbol_name != NULL && symbol_name[0] != '\0')) {
      slot->library_name[0] = '\0';
      slot->symbol_name[0] = '\0';
      slot->conflicted = 1U;
    } else if (slot->library_name[0] == '\0' && slot_library_name[0] != '\0') {
      snprintf(slot->library_name, sizeof(slot->library_name), "%s", slot_library_name);
    }
    if (has_source && slot->has_source == 0U) {
      slot->source_section_index = source_section_index;
      slot->source_offset = source_offset;
      slot->has_source = 1U;
    }
    return 0;
  }
  if (lookup->base_field_slot_count == lookup->base_field_slot_capacity) {
    next_capacity = lookup->base_field_slot_capacity == 0U ? 8U : lookup->base_field_slot_capacity * 2U;
    grown = (M68kRenderBaseFieldSlot *)realloc(lookup->base_field_slots, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->base_field_slots = grown;
    lookup->base_field_slot_capacity = next_capacity;
  }
  memset(&lookup->base_field_slots[lookup->base_field_slot_count], 0,
    sizeof(lookup->base_field_slots[lookup->base_field_slot_count]));
  snprintf(lookup->base_field_slots[lookup->base_field_slot_count].owner_name,
    sizeof(lookup->base_field_slots[lookup->base_field_slot_count].owner_name), "%s", owner_name);
  lookup->base_field_slots[lookup->base_field_slot_count].displacement = displacement;
  lookup->base_field_slots[lookup->base_field_slot_count].source_section_index = source_section_index;
  lookup->base_field_slots[lookup->base_field_slot_count].source_offset = source_offset;
  lookup->base_field_slots[lookup->base_field_slot_count].has_source = has_source;
  if (slot_library_name[0] != '\0') {
    snprintf(lookup->base_field_slots[lookup->base_field_slot_count].library_name,
      sizeof(lookup->base_field_slots[lookup->base_field_slot_count].library_name), "%s", slot_library_name);
  }
  if (symbol_name != NULL && symbol_name[0] != '\0') {
    snprintf(lookup->base_field_slots[lookup->base_field_slot_count].symbol_name,
      sizeof(lookup->base_field_slots[lookup->base_field_slot_count].symbol_name), "%s", symbol_name);
  }
  lookup->base_field_slots[lookup->base_field_slot_count].value_kind = value_kind;
  ++lookup->base_field_slot_count;
  return 0;
}

static int render_lookup_add_base_field_slot(M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement, const char *library_name, size_t source_section_index, uint32_t source_offset) {
  return render_lookup_add_base_field_slot_with_symbol(lookup, owner_name, displacement, library_name, NULL,
    M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE, source_section_index, source_offset);
}

static int render_lookup_add_named_app_field_slot(M68kRenderLookup *lookup, int16_t displacement,
    const char *symbol_name, size_t source_section_index, uint32_t source_offset) {
  return render_lookup_add_base_field_slot_with_symbol(lookup, "__amiga_app_base__", displacement, "", symbol_name,
    M68K_RENDER_BASE_FIELD_SLOT_NAMED_VALUE, source_section_index, source_offset);
}

static int render_lookup_add_app_access_slot(M68kRenderLookup *lookup, int16_t displacement,
    size_t source_section_index, uint32_t source_offset) {
  return render_lookup_add_base_field_slot_with_symbol(lookup, "__amiga_app_base__", displacement, "", NULL,
    M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS, source_section_index, source_offset);
}

static int render_lookup_add_app_access_ref(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint8_t base_reg, int16_t displacement, uint8_t operand_index, uint8_t access_kind) {
  size_t index;
  M68kRenderAppSlotRef *grown;
  size_t next_capacity;
  if (lookup == NULL || base_reg >= 8U || operand_index >= 4U ||
      access_kind == M68K_APP_SLOT_ACCESS_NONE) {
    return 0;
  }
  if (render_lookup_add_app_access_slot(lookup, displacement, section_index, offset) != 0) return -1;
  for (index = 0U; index < lookup->app_slot_ref_count; ++index) {
    const M68kRenderAppSlotRef *existing = &lookup->app_slot_refs[index];
    if (existing->section_index == section_index && existing->ref.offset == offset &&
        existing->ref.displacement == displacement && existing->ref.base_reg == base_reg &&
        existing->ref.operand_index == operand_index && existing->ref.access_kind == access_kind) {
      return 0;
    }
  }
  if (lookup->app_slot_ref_count == lookup->app_slot_ref_capacity) {
    next_capacity = lookup->app_slot_ref_capacity == 0U ? 32U : lookup->app_slot_ref_capacity * 2U;
    grown = (M68kRenderAppSlotRef *)realloc(lookup->app_slot_refs, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->app_slot_refs = grown;
    lookup->app_slot_ref_capacity = next_capacity;
  }
  memset(&lookup->app_slot_refs[lookup->app_slot_ref_count], 0,
    sizeof(lookup->app_slot_refs[lookup->app_slot_ref_count]));
  lookup->app_slot_refs[lookup->app_slot_ref_count].section_index = section_index;
  lookup->app_slot_refs[lookup->app_slot_ref_count].ref.offset = offset;
  lookup->app_slot_refs[lookup->app_slot_ref_count].ref.displacement = displacement;
  lookup->app_slot_refs[lookup->app_slot_ref_count].ref.base_reg = base_reg;
  lookup->app_slot_refs[lookup->app_slot_ref_count].ref.operand_index = operand_index;
  lookup->app_slot_refs[lookup->app_slot_ref_count].ref.access_kind = access_kind;
  ++lookup->app_slot_ref_count;
  return 0;
}

static int render_lookup_add_indexed_vector_wrapper(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    const char *library_name) {
  size_t index;
  M68kRenderIndexedVectorWrapper *grown;
  size_t next_capacity;
  if (lookup == NULL || library_name == NULL || library_name[0] == '\0') return 0;
  if (amiga_os_find_library_base_name(library_name) == NULL) return 0;
  for (index = 0U; index < lookup->indexed_vector_wrapper_count; ++index) {
    M68kRenderIndexedVectorWrapper *wrapper = &lookup->indexed_vector_wrappers[index];
    if (wrapper->section_index != section_index || wrapper->offset != offset) continue;
    if (strcmp(wrapper->library_name, library_name) != 0) wrapper->library_name[0] = '\0';
    return 0;
  }
  if (lookup->indexed_vector_wrapper_count == lookup->indexed_vector_wrapper_capacity) {
    next_capacity = lookup->indexed_vector_wrapper_capacity == 0U ? 8U :
      lookup->indexed_vector_wrapper_capacity * 2U;
    grown = (M68kRenderIndexedVectorWrapper *)realloc(lookup->indexed_vector_wrappers,
      next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->indexed_vector_wrappers = grown;
    lookup->indexed_vector_wrapper_capacity = next_capacity;
  }
  memset(&lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count], 0,
    sizeof(lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count]));
  lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count].section_index = section_index;
  lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count].offset = offset;
  snprintf(lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count].library_name,
    sizeof(lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count].library_name), "%s", library_name);
  ++lookup->indexed_vector_wrapper_count;
  return 0;
}

static int comment_contains_part(const char *comment, const char *part) {
  if (comment == NULL || part == NULL || part[0] == '\0') return 1;
  return strstr(comment, part) != NULL;
}

static int append_comment_part_local(char *comment, size_t comment_size, const char *part) {
  size_t used;
  size_t needed;
  if (comment == NULL || comment_size == 0U || part == NULL || part[0] == '\0') return 1;
  if (comment_contains_part(comment, part)) return 1;
  used = strlen(comment);
  needed = strlen(part) + (used != 0U ? 3U : 0U) + 1U;
  if (needed > comment_size - used) return 0;
  if (used != 0U) strcat(comment, " | ");
  strcat(comment, part);
  return 1;
}

static size_t *lookup_instruction_comment_index_slot(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->instruction_comment_indices == NULL ||
      lookup->instruction_comment_extents == NULL || offset >= lookup->instruction_comment_extents[section_index] ||
      lookup->instruction_comment_indices[section_index] == NULL) {
    return NULL;
  }
  return &lookup->instruction_comment_indices[section_index][offset];
}

static const size_t *lookup_instruction_comment_index_slot_const(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->instruction_comment_indices == NULL ||
      lookup->instruction_comment_extents == NULL || offset >= lookup->instruction_comment_extents[section_index] ||
      lookup->instruction_comment_indices[section_index] == NULL) {
    return NULL;
  }
  return &lookup->instruction_comment_indices[section_index][offset];
}

static int render_lookup_add_instruction_comment(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    const char *comment) {
  size_t index;
  size_t *index_slot;
  M68kRenderInstructionComment *grown;
  size_t next_capacity;
  if (lookup == NULL || comment == NULL || comment[0] == '\0') return 0;
  index_slot = lookup_instruction_comment_index_slot(lookup, section_index, offset);
  if (index_slot != NULL && *index_slot != 0U && *index_slot <= lookup->instruction_comment_count) {
    M68kRenderInstructionComment *entry = &lookup->instruction_comments[*index_slot - 1U];
    if (entry->section_index == section_index && entry->offset == offset) {
      (void)append_comment_part_local(entry->comment, sizeof(entry->comment), comment);
      return 0;
    }
    *index_slot = 0U;
  }
  for (index = 0U; index < lookup->instruction_comment_count; ++index) {
    M68kRenderInstructionComment *entry = &lookup->instruction_comments[index];
    if (entry->section_index != section_index || entry->offset != offset) continue;
    if (index_slot != NULL) *index_slot = index + 1U;
    (void)append_comment_part_local(entry->comment, sizeof(entry->comment), comment);
    return 0;
  }
  if (lookup->instruction_comment_count == lookup->instruction_comment_capacity) {
    next_capacity = lookup->instruction_comment_capacity == 0U ? 32U : lookup->instruction_comment_capacity * 2U;
    grown = (M68kRenderInstructionComment *)realloc(lookup->instruction_comments, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->instruction_comments = grown;
    lookup->instruction_comment_capacity = next_capacity;
  }
  memset(&lookup->instruction_comments[lookup->instruction_comment_count], 0,
    sizeof(lookup->instruction_comments[lookup->instruction_comment_count]));
  lookup->instruction_comments[lookup->instruction_comment_count].section_index = section_index;
  lookup->instruction_comments[lookup->instruction_comment_count].offset = offset;
  snprintf(lookup->instruction_comments[lookup->instruction_comment_count].comment,
    sizeof(lookup->instruction_comments[lookup->instruction_comment_count].comment), "%s", comment);
  if (index_slot != NULL) *index_slot = lookup->instruction_comment_count + 1U;
  ++lookup->instruction_comment_count;
  return 0;
}

static int render_lookup_add_recovered_function_arg(M68kRenderLookup *lookup, size_t section_index,
    uint32_t function_offset, uint16_t stack_offset, uint8_t reg_kind, uint8_t reg_index,
    const AmigaOsCallInputInfo *input) {
  size_t index;
  M68kRenderRecoveredFunctionArg *grown;
  size_t next_capacity;
  if (lookup == NULL || input == NULL || stack_offset == 0U || reg_kind == 0U || reg_index >= 8U) return 0;
  for (index = 0U; index < lookup->recovered_function_arg_count; ++index) {
    M68kRenderRecoveredFunctionArg *entry = &lookup->recovered_function_args[index];
    if (entry->section_index == section_index && entry->function_offset == function_offset &&
        entry->stack_offset == stack_offset && entry->reg_kind == reg_kind && entry->reg_index == reg_index) {
      if (entry->input != input) entry->input = NULL;
      return 0;
    }
  }
  if (lookup->recovered_function_arg_count == lookup->recovered_function_arg_capacity) {
    next_capacity = lookup->recovered_function_arg_capacity == 0U ? 16U :
      lookup->recovered_function_arg_capacity * 2U;
    grown = (M68kRenderRecoveredFunctionArg *)realloc(lookup->recovered_function_args,
      next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->recovered_function_args = grown;
    lookup->recovered_function_arg_capacity = next_capacity;
  }
  memset(&lookup->recovered_function_args[lookup->recovered_function_arg_count], 0,
    sizeof(lookup->recovered_function_args[lookup->recovered_function_arg_count]));
  lookup->recovered_function_args[lookup->recovered_function_arg_count].section_index = section_index;
  lookup->recovered_function_args[lookup->recovered_function_arg_count].function_offset = function_offset;
  lookup->recovered_function_args[lookup->recovered_function_arg_count].stack_offset = stack_offset;
  lookup->recovered_function_args[lookup->recovered_function_arg_count].reg_kind = reg_kind;
  lookup->recovered_function_args[lookup->recovered_function_arg_count].reg_index = reg_index;
  lookup->recovered_function_args[lookup->recovered_function_arg_count].input = input;
  ++lookup->recovered_function_arg_count;
  return 0;
}

static int render_lookup_add_recovered_local_call_summary(M68kRenderLookup *lookup, size_t section_index,
    uint32_t target_offset, const AmigaOsLibraryVectorInfo *vector) {
  size_t index;
  M68kRenderRecoveredLocalCallSummary *grown;
  size_t next_capacity;
  if (lookup == NULL || vector == NULL) return 0;
  for (index = 0U; index < lookup->recovered_local_call_summary_count; ++index) {
    M68kRenderRecoveredLocalCallSummary *entry = &lookup->recovered_local_call_summaries[index];
    if (entry->section_index == section_index && entry->target_offset == target_offset) {
      if (entry->vector != vector) entry->vector = NULL;
      return 0;
    }
  }
  if (lookup->recovered_local_call_summary_count == lookup->recovered_local_call_summary_capacity) {
    next_capacity = lookup->recovered_local_call_summary_capacity == 0U ? 16U :
      lookup->recovered_local_call_summary_capacity * 2U;
    grown = (M68kRenderRecoveredLocalCallSummary *)realloc(lookup->recovered_local_call_summaries,
      next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->recovered_local_call_summaries = grown;
    lookup->recovered_local_call_summary_capacity = next_capacity;
  }
  memset(&lookup->recovered_local_call_summaries[lookup->recovered_local_call_summary_count], 0,
    sizeof(lookup->recovered_local_call_summaries[lookup->recovered_local_call_summary_count]));
  lookup->recovered_local_call_summaries[lookup->recovered_local_call_summary_count].section_index = section_index;
  lookup->recovered_local_call_summaries[lookup->recovered_local_call_summary_count].target_offset = target_offset;
  lookup->recovered_local_call_summaries[lookup->recovered_local_call_summary_count].vector = vector;
  ++lookup->recovered_local_call_summary_count;
  return 0;
}

static int render_lookup_add_typed_slot_effect(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    int16_t displacement, const AmigaOsCallOutputInfo *output) {
  size_t index;
  M68kRenderTypedSlotEffect *grown;
  size_t next_capacity;
  if (lookup == NULL || output == NULL || output->reg_kind == AMIGA_OS_REGISTER_NONE ||
      output->reg_index >= 8U) {
    return 0;
  }
  for (index = 0U; index < lookup->typed_slot_effect_count; ++index) {
    M68kRenderTypedSlotEffect *entry = &lookup->typed_slot_effects[index];
    if (entry->section_index == section_index && entry->offset == offset &&
        entry->displacement == displacement) {
      if (entry->output != output) entry->output = NULL;
      return 0;
    }
  }
  if (lookup->typed_slot_effect_count == lookup->typed_slot_effect_capacity) {
    next_capacity = lookup->typed_slot_effect_capacity == 0U ? 16U : lookup->typed_slot_effect_capacity * 2U;
    grown = (M68kRenderTypedSlotEffect *)realloc(lookup->typed_slot_effects, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->typed_slot_effects = grown;
    lookup->typed_slot_effect_capacity = next_capacity;
  }
  memset(&lookup->typed_slot_effects[lookup->typed_slot_effect_count], 0,
    sizeof(lookup->typed_slot_effects[lookup->typed_slot_effect_count]));
  lookup->typed_slot_effects[lookup->typed_slot_effect_count].section_index = section_index;
  lookup->typed_slot_effects[lookup->typed_slot_effect_count].offset = offset;
  lookup->typed_slot_effects[lookup->typed_slot_effect_count].displacement = displacement;
  lookup->typed_slot_effects[lookup->typed_slot_effect_count].output = output;
  ++lookup->typed_slot_effect_count;
  return 0;
}

static int render_lookup_add_string_span(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint32_t size) {
  size_t index;
  M68kRenderStringSpan *grown;
  size_t next_capacity;
  if (lookup == NULL || size == 0U) return 0;
  for (index = 0U; index < lookup->string_span_count; ++index) {
    M68kRenderStringSpan *entry = &lookup->string_spans[index];
    if (entry->section_index == section_index && entry->offset == offset) {
      if (entry->size != size) entry->size = 0U;
      return 0;
    }
  }
  if (lookup->string_span_count == lookup->string_span_capacity) {
    next_capacity = lookup->string_span_capacity == 0U ? 16U : lookup->string_span_capacity * 2U;
    grown = (M68kRenderStringSpan *)realloc(lookup->string_spans, next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    lookup->string_spans = grown;
    lookup->string_span_capacity = next_capacity;
  }
  lookup->string_spans[lookup->string_span_count].section_index = section_index;
  lookup->string_spans[lookup->string_span_count].offset = offset;
  lookup->string_spans[lookup->string_span_count].size = size;
  ++lookup->string_span_count;
  return 0;
}

static const char *lookup_instruction_comment(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  size_t index;
  const size_t *index_slot;
  if (lookup == NULL) return NULL;
  index_slot = lookup_instruction_comment_index_slot_const(lookup, section_index, offset);
  if (index_slot != NULL && *index_slot != 0U && *index_slot <= lookup->instruction_comment_count) {
    const M68kRenderInstructionComment *entry = &lookup->instruction_comments[*index_slot - 1U];
    if (entry->section_index == section_index && entry->offset == offset && entry->comment[0] != '\0')
      return entry->comment;
  }
  for (index = 0U; index < lookup->instruction_comment_count; ++index) {
    const M68kRenderInstructionComment *entry = &lookup->instruction_comments[index];
    if (entry->section_index == section_index && entry->offset == offset && entry->comment[0] != '\0')
      return entry->comment;
  }
  return NULL;
}

static const M68kRenderStringSpan *lookup_string_span_at_offset(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->string_span_count; ++index) {
    const M68kRenderStringSpan *entry = &lookup->string_spans[index];
    if (entry->section_index == section_index && entry->offset == offset && entry->size != 0U) return entry;
  }
  return NULL;
}

static const char *amiga_library_base_name_for_render_effect(const char *library_name) {
  const char *base_name;
  if (library_name == NULL || library_name[0] == '\0') return NULL;
  base_name = amiga_os_find_library_base_name(library_name);
  return base_name != NULL && base_name[0] != '\0' ? base_name : NULL;
}

static int append_render_lookup_platform_effects_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->global_base_slot_count; ++index) {
    const M68kRenderGlobalBaseSlot *slot = &lookup->global_base_slots[index];
    const char *base_name = amiga_library_base_name_for_render_effect(slot->library_name);
    if (slot->has_source == 0U || slot->source_section_index != section_analysis->section_index ||
        base_name == NULL) {
      continue;
    }
    if (m68k_ir_section_analysis_append_recovered_platform_global_base_slot_effect(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->source_offset, slot->section_index, slot->offset,
        base_name) != 0) {
      return -1;
    }
  }
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    const char *base_name = amiga_library_base_name_for_render_effect(slot->library_name);
    if (slot->has_source == 0U || slot->source_section_index != section_analysis->section_index ||
        slot->conflicted != 0U || slot->value_kind != M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE ||
        base_name == NULL) {
      continue;
    }
    if (strcmp(slot->owner_name, "__amiga_app_base__") != 0) continue;
    if (m68k_ir_section_analysis_append_recovered_platform_base_slot(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->displacement, base_name) != 0 ||
        m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->source_offset, M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT,
        0U, 0U, slot->displacement, INT16_MIN, base_name, NULL, NULL, NULL, NULL, 0U, 0) != 0) {
      return -1;
    }
  }
  for (index = 0U; index < lookup->typed_slot_effect_count; ++index) {
    const M68kRenderTypedSlotEffect *effect = &lookup->typed_slot_effects[index];
    const AmigaOsCallOutputInfo *output = effect->output;
    const char *symbol_name;
    const char *type_name;
    const char *semantic_kind;
    const char *value_domain_name;
    if (effect->section_index != section_analysis->section_index || output == NULL) continue;
    symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, output->output_id);
    type_name = amiga_output_type_or_struct_name(output);
    semantic_kind = amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, output->semantic_kind_id);
    value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, output->value_domain_id);
    if ((symbol_name == NULL || symbol_name[0] == '\0') &&
        (type_name == NULL || type_name[0] == '\0') &&
        (semantic_kind == NULL || semantic_kind[0] == '\0') &&
        (value_domain_name == NULL || value_domain_name[0] == '\0')) {
      continue;
    }
    if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, effect->offset, M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT,
        0U, 0U, effect->displacement, INT16_MIN, NULL, symbol_name, type_name, semantic_kind,
        value_domain_name, 0U, 0) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_render_lookup_app_slot_refs_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->app_slot_ref_count; ++index) {
    const M68kRenderAppSlotRef *ref = &lookup->app_slot_refs[index];
    if (ref->section_index != section_analysis->section_index) continue;
    if (m68k_ir_section_analysis_append_app_slot_ref(section_analysis, &ref->ref) != 0) return -1;
  }
  return 0;
}

static void trace_reg_set(M68kRenderTraceRegName *reg, const char *name) {
  if (reg == NULL || name == NULL || name[0] == '\0') return;
  reg->known = 1U;
  snprintf(reg->name, sizeof(reg->name), "%s", name);
}

static void trace_reg_clear(M68kRenderTraceRegName *reg) {
  if (reg == NULL) return;
  reg->known = 0U;
  reg->name[0] = '\0';
}

static void trace_addr_reg_set_name(M68kRenderBaseTraceState *state, uint8_t reg, const char *name) {
  if (state == NULL || reg >= 8U) return;
  trace_reg_set(&state->addr_regs[reg], name);
  state->app_addresses[reg].known = 0U;
  state->app_addresses[reg].displacement = 0;
}

static void trace_addr_reg_clear(M68kRenderBaseTraceState *state, uint8_t reg) {
  if (state == NULL || reg >= 8U) return;
  trace_reg_clear(&state->addr_regs[reg]);
  state->app_addresses[reg].known = 0U;
  state->app_addresses[reg].displacement = 0;
}

static void trace_addr_reg_set_app_address(M68kRenderBaseTraceState *state, uint8_t reg, int16_t displacement) {
  if (state == NULL || reg >= 8U) return;
  trace_reg_clear(&state->addr_regs[reg]);
  state->app_addresses[reg].known = 1U;
  state->app_addresses[reg].displacement = displacement;
}

static void trace_state_reset(M68kRenderBaseTraceState *state) {
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
}

static void trace_state_apply_policy_register_seeds(M68kRenderBaseTraceState *state,
    const M68kAnalysisPolicy *policy, size_t section_index, uint32_t offset) {
  uint16_t index;
  if (state == NULL || policy == NULL) return;
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    if ((seed->kind != M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE &&
         seed->kind != M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR) ||
        seed->reg_index >= 8U || seed->name[0] == '\0')
      continue;
    if (seed->has_section_index && seed->section_index != (uint32_t)section_index) continue;
    if (seed->has_entry_offset) {
      if (seed->entry_offset != offset) continue;
    } else if (!policy->has_entry_offset || section_index != 0U || policy->entry_offset != offset) continue;
    if (seed->reg_kind == M68K_ANALYSIS_REGISTER_DATA) trace_reg_set(&state->data_regs[seed->reg_index], seed->name);
    else if (seed->reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS)
      trace_addr_reg_set_name(state, seed->reg_index, seed->name);
  }
}

static int operand_is_data_register_local(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_DN) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_RN && !operand->value.reg_is_address) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 0U) {
    if (out_reg != NULL) *out_reg = operand->value.ea_reg;
    return 1;
  }
  return 0;
}

static int operand_address_register_index_local(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_AN) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_RN && operand->value.reg_is_address) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 1U) {
    if (out_reg != NULL) *out_reg = operand->value.ea_reg;
    return 1;
  }
  return 0;
}

static int operand_is_address_displacement_local(const M68kOperandIR *operand, uint8_t *out_reg,
    int16_t *out_displacement) {
  if (operand == NULL ||
      (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) ||
      operand->value.ea_mode != 5U || operand->value.ea_reg >= 8U) {
    return 0;
  }
  if (out_reg != NULL) *out_reg = operand->value.ea_reg;
  if (out_displacement != NULL) *out_displacement = (int16_t)(operand->value.value & 0xFFFFU);
  return 1;
}

static const char *trace_name_from_operand(const M68kRenderBaseTraceState *state,
    const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  if (state == NULL || operand == NULL) return NULL;
  if (operand_is_data_register_local(operand, &reg) && state->data_regs[reg].known) return state->data_regs[reg].name;
  if (operand_address_register_index_local(operand, &reg) && state->addr_regs[reg].known)
    return state->addr_regs[reg].name;
  return NULL;
}

static const char *trace_library_from_operand(const M68kRenderBaseTraceState *state,
    const M68kOperandIR *operand) {
  const char *name = trace_name_from_operand(state, operand);
  const char *library_name;
  if (name == NULL || name[0] == '\0') return NULL;
  if (amiga_os_find_library_base_name(name) != NULL) return name;
  library_name = amiga_library_name_from_base_symbol_name(name);
  return library_name != NULL && amiga_os_find_library_base_name(library_name) != NULL ? library_name : NULL;
}

static const char *trace_known_library_from_operand(const M68kRenderLookup *lookup,
    const M68kRenderBaseTraceState *state, const M68kOperandIR *operand) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  const char *library_name = trace_library_from_operand(state, operand);
  if (library_name != NULL) return library_name;
  if (lookup == NULL || operand == NULL) return NULL;
  if (operand_is_address_displacement_local(operand, &base_reg, &displacement)) {
    if (state != NULL && state->addr_regs[base_reg].known) {
      library_name = lookup_base_field_slot_library(lookup, state->addr_regs[base_reg].name, displacement);
      if (library_name != NULL) return library_name;
    }
    if (base_reg == 6U && (state == NULL || !state->addr_regs[6].known))
      return lookup_app_base_field_slot_library(lookup, displacement);
  }
  return NULL;
}

static void trace_state_update_register_names_after_candidate(M68kRenderBaseTraceState *state,
    const M68kRenderLookup *lookup, const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  const char *source_name;
  const char *source_library;
  uint8_t dest_reg = 0U;
  if (state == NULL || candidate == NULL) return;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE &&
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA) {
    return;
  }
  if (candidate->operand_count != 2U || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return;
  source_name = trace_name_from_operand(state, &instruction.operands[0]);
  source_library = trace_known_library_from_operand(lookup, state, &instruction.operands[0]);
  if (operand_is_data_register_local(&instruction.operands[1], &dest_reg)) {
    if (source_name != NULL) trace_reg_set(&state->data_regs[dest_reg], source_name);
    else trace_reg_clear(&state->data_regs[dest_reg]);
  } else if (operand_address_register_index_local(&instruction.operands[1], &dest_reg)) {
    if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && source_library != NULL) {
      trace_addr_reg_set_name(state, dest_reg, source_library);
    } else if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEA &&
        operand_is_absolute_address_local(&instruction.operands[0], 4U)) {
      trace_addr_reg_set_name(state, dest_reg, amiga_os_exec_base_library_name());
    } else if (source_name != NULL) trace_addr_reg_set_name(state, dest_reg, source_name);
    else trace_addr_reg_clear(state, dest_reg);
  }
}

static void trace_local_slot_set(M68kRenderBaseTraceState *state, uint8_t base_reg, int16_t displacement,
    const char *library_name) {
  size_t index;
  if (state == NULL || base_reg >= 8U || library_name == NULL || library_name[0] == '\0') return;
  for (index = 0U; index < sizeof(state->local_slots) / sizeof(state->local_slots[0]); ++index) {
    M68kRenderTraceLocalSlot *slot = &state->local_slots[index];
    if (slot->valid && slot->base_reg == base_reg && slot->displacement == displacement) {
      snprintf(slot->library_name, sizeof(slot->library_name), "%s", library_name);
      return;
    }
  }
  for (index = 0U; index < sizeof(state->local_slots) / sizeof(state->local_slots[0]); ++index) {
    M68kRenderTraceLocalSlot *slot = &state->local_slots[index];
    if (slot->valid) continue;
    slot->valid = 1U;
    slot->base_reg = base_reg;
    slot->displacement = displacement;
    snprintf(slot->library_name, sizeof(slot->library_name), "%s", library_name);
    return;
  }
}

static const char *trace_local_slot_library(const M68kRenderBaseTraceState *state, uint8_t base_reg,
    int16_t displacement) {
  size_t index;
  if (state == NULL || base_reg >= 8U) return NULL;
  for (index = 0U; index < sizeof(state->local_slots) / sizeof(state->local_slots[0]); ++index) {
    const M68kRenderTraceLocalSlot *slot = &state->local_slots[index];
    if (slot->valid && slot->base_reg == base_reg && slot->displacement == displacement)
      return slot->library_name;
  }
  return NULL;
}

static int read_library_name_string_at(const M68kDecodeSectionIR *section, uint32_t offset, char *out_name,
    size_t out_size) {
  size_t index = 0U;
  if (section == NULL || section->data == NULL || out_name == NULL || out_size == 0U || offset >= section->size)
    return 0;
  while (offset + index < section->size && index + 1U < out_size) {
    uint8_t value = section->data[offset + index];
    if (value == 0U) {
      out_name[index] = '\0';
      return index != 0U && amiga_os_find_library_base_name(out_name) != NULL;
    }
    if (value < 0x20U || value > 0x7EU) return 0;
    out_name[index++] = (char)value;
  }
  return 0;
}

static int format_lower_symbol_component(const char *text, char *out, size_t out_size) {
  size_t in_index;
  size_t out_index = 0U;
  int previous_sep = 0;
  if (out == NULL || out_size == 0U) return 0;
  out[0] = '\0';
  if (text == NULL || text[0] == '\0') return 0;
  for (in_index = 0U; text[in_index] != '\0'; ++in_index) {
    char ch = text[in_index];
    int is_alnum = (ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9');
    if (is_alnum) {
      if (out_index + 1U >= out_size) return 0;
      out[out_index++] = ascii_lower_local(ch);
      previous_sep = 0;
    } else if (out_index != 0U && !previous_sep) {
      if (out_index + 1U >= out_size) return 0;
      out[out_index++] = '_';
      previous_sep = 1;
    }
  }
  while (out_index != 0U && out[out_index - 1U] == '_') --out_index;
  out[out_index] = '\0';
  return out_index != 0U;
}

static int format_app_named_value_slot_symbol(const char *source_name, char *symbol_name, size_t symbol_name_size) {
  char name_part[48];
  int written;
  if (symbol_name == NULL || symbol_name_size == 0U) return 0;
  symbol_name[0] = '\0';
  if (source_name == NULL || source_name[0] == '\0') return 0;
  if (strcmp(source_name, "SegList") == 0 || strcmp(source_name, "seglist") == 0) {
    written = snprintf(symbol_name, symbol_name_size, "app_SegList");
    return written > 0 && (size_t)written < symbol_name_size;
  }
  if (!format_lower_symbol_component(source_name, name_part, sizeof(name_part))) return 0;
  written = snprintf(symbol_name, symbol_name_size, "app_%s", name_part);
  return written > 0 && (size_t)written < symbol_name_size;
}

static const AmigaOsCallInputInfo *open_device_iorequest_input_info(void) {
  const AmigaOsLibraryVectorInfo *open_device = amiga_os_find_library_vector_by_symbol_name("_LVOOpenDevice");
  const AmigaOsCallInputInfo *inputs;
  size_t count = 0U;
  size_t index;
  if (open_device == NULL) return NULL;
  inputs = amiga_os_library_vector_inputs(open_device, &count);
  if (inputs == NULL) return NULL;
  for (index = 0U; index < count; ++index) {
    const AmigaOsCallInputInfo *input = &inputs[index];
    if (input->reg_kind == AMIGA_OS_REGISTER_ADDRESS && input->reg_index == 1U &&
        input->struct_id == AMIGA_OS_STRUCT_ID_IO) {
      return input;
    }
  }
  return NULL;
}

static int format_open_device_app_iorequest_slot_name(const char *device_name, char *symbol_name,
    size_t symbol_name_size) {
  const AmigaOsCallInputInfo *input = open_device_iorequest_input_info();
  const char *input_name = input != NULL ? amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, input->input_id) : NULL;
  char device_part[48];
  char input_part[32];
  int written;
  if (symbol_name == NULL || symbol_name_size == 0U) return 0;
  symbol_name[0] = '\0';
  if (!format_lower_symbol_component(device_name, device_part, sizeof(device_part)) ||
      !format_lower_symbol_component(input_name, input_part, sizeof(input_part))) {
    return 0;
  }
  written = snprintf(symbol_name, symbol_name_size, "app_%s_%s", device_part, input_part);
  return written > 0 && (size_t)written < symbol_name_size;
}

static int candidate_lea_known_amiga_name_to_address_reg(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint8_t *out_reg, char *out_name, size_t out_size) {
  M68kInstructionIR instruction;
  uint32_t absolute_offset = 0U;
  uint8_t dest_reg = 0U;
  int16_t displacement;
  int64_t target;
  if (section == NULL || candidate == NULL || out_name == NULL || out_size == 0U) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_LEA || candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!operand_address_register_index_local(&instruction.operands[1], &dest_reg)) return 0;
  if (instruction.operands[0].kind == M68K_ASM_OPERAND_EA &&
      instruction.operands[0].value.ea_mode == 7U && instruction.operands[0].value.ea_reg == 2U) {
    displacement = (int16_t)(instruction.operands[0].value.value & 0xFFFFU);
    target = (int64_t)candidate->offset + 2 + displacement;
    if (target < 0 || target > UINT32_MAX) return 0;
    if (!read_library_name_string_at(section, (uint32_t)target, out_name, out_size)) return 0;
    if (out_reg != NULL) *out_reg = dest_reg;
    return 1;
  }
  if (operand_absolute_offset_local(&instruction.operands[0], &absolute_offset)) {
    if (!read_library_name_string_at(section, absolute_offset, out_name, out_size)) return 0;
    if (out_reg != NULL) *out_reg = dest_reg;
    return 1;
  }
  return 0;
}

static int candidate_lea_app_base_address_to_address_reg(const M68kDecodeCandidate *candidate, uint8_t *out_reg,
    int16_t *out_displacement) {
  M68kInstructionIR instruction;
  uint8_t base_reg = 0U;
  uint8_t dest_reg = 0U;
  int16_t displacement = 0;
  if (candidate == NULL || out_reg == NULL || out_displacement == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_LEA || candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!operand_is_address_displacement_local(&instruction.operands[0], &base_reg, &displacement) ||
      base_reg != 6U) {
    return 0;
  }
  if (!operand_address_register_index_local(&instruction.operands[1], &dest_reg)) return 0;
  *out_reg = dest_reg;
  *out_displacement = displacement;
  return 1;
}

static int candidate_is_exec_open_library_call(const M68kRenderBaseTraceState *state,
    const M68kDecodeCandidate *candidate) {
  int16_t lvo = 0;
  const AmigaOsLibraryVectorInfo *open_library;
  const AmigaOsLibraryVectorInfo *old_open_library;
  if (state == NULL || !state->addr_regs[6].known) return 0;
  if (strcmp(state->addr_regs[6].name, amiga_os_exec_base_library_name()) != 0) return 0;
  if (!candidate_calls_a6_lvo(candidate, &lvo)) return 0;
  open_library = amiga_os_find_library_vector_by_symbol_name("_LVOOpenLibrary");
  old_open_library = amiga_os_find_library_vector_by_symbol_name("_LVOOldOpenLibrary");
  return (open_library != NULL && open_library->lvo == lvo) ||
    (old_open_library != NULL && old_open_library->lvo == lvo);
}

static int candidate_is_exec_open_device_call(const M68kRenderBaseTraceState *state,
    const M68kDecodeCandidate *candidate) {
  int16_t lvo = 0;
  const AmigaOsLibraryVectorInfo *open_device;
  if (state == NULL || !state->addr_regs[6].known) return 0;
  if (strcmp(state->addr_regs[6].name, amiga_os_exec_base_library_name()) != 0) return 0;
  if (!candidate_calls_a6_lvo(candidate, &lvo)) return 0;
  open_device = amiga_os_find_library_vector_by_symbol_name("_LVOOpenDevice");
  return open_device != NULL && open_device->lvo == lvo;
}

static int candidate_stores_library_to_local_slot(const M68kRenderBaseTraceState *state,
    const M68kDecodeCandidate *candidate, uint8_t *out_base_reg, int16_t *out_displacement,
    const char **out_library_name) {
  M68kInstructionIR instruction;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  const char *library_name;
  if (state == NULL || candidate == NULL || out_base_reg == NULL || out_displacement == NULL ||
      out_library_name == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  library_name = trace_library_from_operand(state, &instruction.operands[0]);
  if (library_name == NULL || amiga_os_find_library_base_name(library_name) == NULL) return 0;
  if (!operand_is_address_displacement_local(&instruction.operands[1], &base_reg, &displacement)) return 0;
  *out_base_reg = base_reg;
  *out_displacement = displacement;
  *out_library_name = library_name;
  return 1;
}

static int candidate_stores_d0_to_a6_slot(const M68kDecodeCandidate *candidate, int16_t *out_displacement) {
  M68kInstructionIR instruction;
  uint8_t source_reg = 0U;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  if (out_displacement != NULL) *out_displacement = 0;
  if (candidate == NULL || out_displacement == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!operand_is_data_register_local(&instruction.operands[0], &source_reg) || source_reg != 0U) return 0;
  if (!operand_is_address_displacement_local(&instruction.operands[1], &base_reg, &displacement) ||
      base_reg != 6U) return 0;
  *out_displacement = displacement;
  return 1;
}

static int reglist_contains_data_register_local(const M68kOperandIR *operand, uint8_t reg_index) {
  uint32_t mask;
  if (operand == NULL || operand->kind != M68K_ASM_OPERAND_REGLIST || reg_index >= 8U) return 0;
  mask = operand->value.value;
  return (mask & (1UL << reg_index)) != 0U;
}

static int candidate_writes_d0_unknown(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  if (candidate == NULL) return 0;
  if (candidate->mnemonic_id == M68K_ASM_MNEMONIC_JSR ||
      candidate->mnemonic_id == M68K_ASM_MNEMONIC_BSR) return 1;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEM)
    return instruction.operand_count >= 2U && reglist_contains_data_register_local(&instruction.operands[1], 0U);
  if (instruction.operand_count >= 2U) {
    const M68kOperandIR *dest = &instruction.operands[instruction.operand_count - 1U];
    uint8_t dest_reg = 0U;
    if (operand_is_data_register_local(dest, &dest_reg) && dest_reg == 0U) return 1;
  }
  return 0;
}

static int candidate_stops_open_library_store_scan(const M68kDecodeCandidate *candidate) {
  if (candidate == NULL) return 1;
  return candidate->mnemonic_id == M68K_ASM_MNEMONIC_RTS ||
    candidate->mnemonic_id == M68K_ASM_MNEMONIC_RTR ||
    candidate->mnemonic_id == M68K_ASM_MNEMONIC_RTE ||
    candidate->mnemonic_id == M68K_ASM_MNEMONIC_STOP ||
    candidate->mnemonic_id == M68K_ASM_MNEMONIC_ILLEGAL ||
    candidate->mnemonic_id == M68K_ASM_MNEMONIC_JMP;
}

static int candidate_has_open_library_store_scan_fallthrough(const M68kDecodeCandidate *candidate) {
  if (candidate_stops_open_library_store_scan(candidate)) return 0;
  return candidate->mnemonic_id != M68K_ASM_MNEMONIC_BRA;
}

static void update_open_library_store_scan_a6_state(const M68kDecodeCandidate *candidate, int *a6_is_exec) {
  M68kInstructionIR instruction;
  if (candidate == NULL || a6_is_exec == NULL) return;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return;
  if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    if (instruction.operand_count >= 2U && reglist_contains_address_register_local(&instruction.operands[1], 6U))
      *a6_is_exec = 0;
    return;
  }
  if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && instruction.operand_count >= 2U &&
      operand_is_address_register_local(&instruction.operands[1], 6U)) {
    *a6_is_exec = operand_is_absolute_address_local(&instruction.operands[0], 4U) ? 1 : 0;
  }
}

static int open_library_store_scan_enqueue(uint32_t *queue_offsets, uint8_t *queue_a6_is_exec, size_t *queue_count,
    const uint32_t *visited_offsets, const uint8_t *visited_a6_is_exec, size_t visited_count, uint32_t offset,
    int a6_is_exec) {
  size_t index;
  if (queue_offsets == NULL || queue_a6_is_exec == NULL || queue_count == NULL ||
      visited_offsets == NULL || visited_a6_is_exec == NULL) return 0;
  for (index = 0U; index < visited_count; ++index)
    if (visited_offsets[index] == offset && visited_a6_is_exec[index] == (uint8_t)(a6_is_exec != 0)) return 0;
  for (index = 0U; index < *queue_count; ++index)
    if (queue_offsets[index] == offset && queue_a6_is_exec[index] == (uint8_t)(a6_is_exec != 0)) return 0;
  if (*queue_count >= 64U) return 0;
  queue_offsets[*queue_count] = offset;
  queue_a6_is_exec[*queue_count] = (uint8_t)(a6_is_exec != 0);
  ++(*queue_count);
  return 1;
}

static int render_lookup_add_open_library_result_app_base_slots(M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t start_offset,
    const char *library_name) {
  uint32_t queue_offsets[64];
  uint32_t visited_offsets[64];
  uint8_t queue_a6_is_exec[64];
  uint8_t visited_a6_is_exec[64];
  size_t queue_head = 0U;
  size_t queue_count = 0U;
  size_t visited_count = 0U;
  int result = 0;
  if (lookup == NULL || section == NULL || accepted_start == NULL ||
      library_name == NULL || library_name[0] == '\0') return 0;
  open_library_store_scan_enqueue(queue_offsets, queue_a6_is_exec, &queue_count,
    visited_offsets, visited_a6_is_exec, visited_count, start_offset, 1);
  while (queue_head < queue_count && visited_count < sizeof(visited_offsets) / sizeof(visited_offsets[0])) {
    uint32_t offset = queue_offsets[queue_head];
    int a6_is_exec = queue_a6_is_exec[queue_head] != 0U;
    const M68kDecodeCandidate *candidate;
    int16_t displacement = 0;
    size_t target_index;
    int next_a6_is_exec;
    ++queue_head;
    visited_offsets[visited_count] = offset;
    visited_a6_is_exec[visited_count] = (uint8_t)(a6_is_exec != 0);
    ++visited_count;
    if (!accepted_start_at(section, accepted_start, offset)) continue;
    candidate = find_candidate_at_offset_local(section, offset);
    if (candidate == NULL || candidate->byte_count == 0U) continue;
    if (!a6_is_exec && candidate_stores_d0_to_a6_slot(candidate, &displacement)) {
      if (render_lookup_add_base_field_slot(lookup, "__amiga_app_base__", displacement, library_name,
          section->section_index, candidate->offset) != 0)
        return -1;
      result = 1;
      continue;
    }
    if (candidate_writes_d0_unknown(candidate)) continue;
    next_a6_is_exec = a6_is_exec;
    update_open_library_store_scan_a6_state(candidate, &next_a6_is_exec);
    for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
      const M68kDecodeTarget *target = &candidate->targets[target_index];
      if (target->has_section == 0U || target->section_index != section->section_index) continue;
      open_library_store_scan_enqueue(queue_offsets, queue_a6_is_exec, &queue_count,
        visited_offsets, visited_a6_is_exec, visited_count, target->offset, next_a6_is_exec);
    }
    if (candidate_has_open_library_store_scan_fallthrough(candidate)) {
      open_library_store_scan_enqueue(queue_offsets, queue_a6_is_exec, &queue_count,
        visited_offsets, visited_a6_is_exec, visited_count, candidate->offset + candidate->byte_count,
        next_a6_is_exec);
    }
  }
  return result;
}

static int candidate_copies_local_slot_to_global_slot(const M68kRenderLookup *lookup,
    const M68kRenderBaseTraceState *state, size_t section_index, const M68kDecodeCandidate *candidate,
    size_t *out_target_section, uint32_t *out_target_offset, const char **out_library_name) {
  M68kInstructionIR instruction;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  const char *library_name;
  uint32_t offset;
  uint32_t end;
  if (lookup == NULL || state == NULL || candidate == NULL || out_target_section == NULL ||
      out_target_offset == NULL || out_library_name == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!operand_is_address_displacement_local(&instruction.operands[0], &base_reg, &displacement)) return 0;
  library_name = trace_local_slot_library(state, base_reg, displacement);
  if (library_name == NULL || amiga_os_find_library_base_name(library_name) == NULL) return 0;
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset + 2U; offset < end; ++offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section_index, offset);
    size_t operand_index = 0U;
    if (relocation == NULL) continue;
    if (!find_unique_relocation_operand(candidate, relocation, &operand_index) || operand_index != 1U) continue;
    *out_target_section = relocation->target_section_index;
    *out_target_offset = relocation->target_offset;
    *out_library_name = library_name;
    return 1;
  }
  return 0;
}

static int candidate_stores_named_value_to_app_slot(const M68kRenderBaseTraceState *state,
    const M68kDecodeCandidate *candidate, int16_t *out_displacement, char *out_symbol_name,
    size_t out_symbol_name_size) {
  M68kInstructionIR instruction;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  const char *source_name;
  if (out_symbol_name != NULL && out_symbol_name_size != 0U) out_symbol_name[0] = '\0';
  if (state == NULL || candidate == NULL || out_displacement == NULL ||
      out_symbol_name == NULL || out_symbol_name_size == 0U) {
    return 0;
  }
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) {
    return 0;
  }
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  source_name = trace_name_from_operand(state, &instruction.operands[0]);
  if (source_name == NULL || source_name[0] == '\0' || platform_state_name_is_app_base(source_name)) return 0;
  if (amiga_os_find_library_base_name(source_name) != NULL ||
      amiga_os_find_library_name_by_base_name(source_name) != NULL) {
    return 0;
  }
  if (!operand_is_address_displacement_local(&instruction.operands[1], &base_reg, &displacement)) return 0;
  if (base_reg >= 8U || !state->addr_regs[base_reg].known ||
      !platform_state_name_is_app_base(state->addr_regs[base_reg].name)) {
    return 0;
  }
  if (!format_app_named_value_slot_symbol(source_name, out_symbol_name, out_symbol_name_size)) return 0;
  *out_displacement = displacement;
  return 1;
}

static int app_slot_access_memory_write_is_readwrite(const M68kSimFormMetadata *metadata) {
  if (metadata == NULL) return 0;
  switch (metadata->operation_type) {
  case M68K_SIM_OP_MOVE:
  case M68K_SIM_OP_CLEAR:
  case M68K_SIM_OP_SET_COND:
  case M68K_SIM_OP_MOVE_MULTIPLE:
  case M68K_SIM_OP_MOVE_PERIPHERAL:
    return 0;
  default:
    return 1;
  }
}

static uint8_t app_slot_access_kind_from_instruction(const M68kInstructionIR *instruction, size_t operand_index) {
  const M68kSimFormMetadata *metadata;
  uint8_t access_kind;
  if (instruction == NULL || operand_index >= instruction->operand_count || operand_index >= 4U)
    return M68K_APP_SLOT_ACCESS_NONE;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return M68K_APP_SLOT_ACCESS_NONE;
  access_kind = metadata->operand_access_kinds[operand_index];
  if (access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS || access_kind == M68K_SIM_ACCESS_BRANCH_TARGET)
    return M68K_APP_SLOT_ACCESS_ADDRESS;
  if (access_kind == M68K_SIM_ACCESS_MEMORY_READ || access_kind == M68K_SIM_ACCESS_REGISTER_READ)
    return M68K_APP_SLOT_ACCESS_READ;
  if (access_kind == M68K_SIM_ACCESS_MEMORY_WRITE || access_kind == M68K_SIM_ACCESS_REGISTER_WRITE) {
    return app_slot_access_memory_write_is_readwrite(metadata)
      ? M68K_APP_SLOT_ACCESS_READ_WRITE
      : M68K_APP_SLOT_ACCESS_WRITE;
  }
  return M68K_APP_SLOT_ACCESS_NONE;
}

static int render_state_operand_uses_app_base(const M68kRenderPlatformState *state, uint8_t base_reg,
    int16_t displacement) {
  if (state == NULL || base_reg >= 8U) return 0;
  if (state->address_app_base_known[base_reg]) return 1;
  if (state->address_base_known[base_reg])
    return library_base_can_use_app_extension_slot(state->address_base_library[base_reg], displacement);
  return base_reg == 6U && !state->address_base_known[6U];
}

static int render_lookup_analyze_amiga_app_state_slots(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start) {
  size_t section_index;
  int32_t min_app_displacement = 0;
  if (lookup == NULL || decode == NULL || accepted_start == NULL) return -1;
  if (lookup->object == NULL || lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK)
    return 0;
  if (lookup_has_amiga_resident_library_context(lookup) &&
      !amiga_os_find_constant_value("LIB_SIZE", &min_app_displacement)) {
    return 0;
  }
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kRenderPlatformState state;
    size_t candidate_index;
    memset(&state, 0, sizeof(state));
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      size_t operand_index;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      platform_state_apply_policy_register_seeds(&state, lookup->policy, section->section_index,
        candidate->offset);
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      for (operand_index = 0U; operand_index < instruction.operand_count && operand_index < 4U; ++operand_index) {
        uint8_t base_reg = 0U;
        int16_t displacement = 0;
        uint8_t access_kind;
        if (!operand_is_address_displacement_local(&instruction.operands[operand_index], &base_reg,
            &displacement)) {
          continue;
        }
        if ((int32_t)displacement < min_app_displacement) continue;
        if (!render_state_operand_uses_app_base(&state, base_reg, displacement)) continue;
        access_kind = app_slot_access_kind_from_instruction(&instruction, operand_index);
        if (access_kind == M68K_APP_SLOT_ACCESS_NONE) continue;
        if (render_lookup_add_app_access_ref(lookup, section->section_index, candidate->offset, base_reg,
            displacement, (uint8_t)operand_index, access_kind) != 0) {
          return -1;
        }
      }
      platform_state_update_after_instruction(&state, lookup, &instruction);
    }
  }
  return 0;
}

static int render_lookup_infer_global_base_slots(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start) {
  M68kRenderGlobalBaseObservation *observations = NULL;
  M68kRenderGlobalBaseObservation *wrapper_observations = NULL;
  size_t observation_count = 0U;
  size_t observation_capacity = 0U;
  size_t wrapper_observation_count = 0U;
  size_t wrapper_observation_capacity = 0U;
  size_t section_index;
  int result = -1;
  if (lookup == NULL || decode == NULL || accepted_start == NULL) return -1;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kRenderBaseTraceState trace_state;
    size_t candidate_index;
    uint32_t expected_offset = 0U;
    int have_expected_offset = 0;
    int current_slot_valid = 0;
    int current_segment_valid = 0;
    uint32_t current_segment_entry = 0U;
    size_t current_slot_section = 0U;
    uint32_t current_slot_offset = 0U;
    trace_state_reset(&trace_state);
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      size_t slot_section = 0U;
      uint32_t slot_offset = 0U;
      const char *library_name = NULL;
      uint8_t local_base_reg = 0U, loaded_address_reg = 0U, app_address_reg = 0U;
      int16_t local_displacement = 0, app_address_displacement = 0, named_app_slot_displacement = 0;
      char loaded_library_name[64], named_app_slot_symbol[64];
      int16_t lvo = 0, wrapper_lvo = 0;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      if (have_expected_offset && candidate->offset != expected_offset) {
        current_segment_valid = 0;
      }
      if (!current_segment_valid) {
        current_segment_valid = 1;
        current_segment_entry = candidate->offset;
      }
      trace_state_apply_policy_register_seeds(&trace_state, lookup->policy, section->section_index,
        candidate->offset);
      if (candidate_lea_known_amiga_name_to_address_reg(section, candidate, &loaded_address_reg,
          loaded_library_name, sizeof(loaded_library_name))) {
        trace_addr_reg_set_name(&trace_state, loaded_address_reg, loaded_library_name);
      }
      if (candidate_lea_app_base_address_to_address_reg(candidate, &app_address_reg, &app_address_displacement)) {
        trace_addr_reg_set_app_address(&trace_state, app_address_reg, app_address_displacement);
      }
      if (candidate_is_exec_open_library_call(&trace_state, candidate) && trace_state.addr_regs[1].known) {
        trace_reg_set(&trace_state.data_regs[0], trace_state.addr_regs[1].name);
        if (render_lookup_add_open_library_result_app_base_slots(lookup, section, accepted_start[section_index],
            candidate->offset + candidate->byte_count, trace_state.addr_regs[1].name) < 0) {
          goto cleanup;
        }
      }
      if (candidate_is_exec_open_device_call(&trace_state, candidate) &&
          trace_state.addr_regs[0].known && trace_state.app_addresses[1].known) {
        char iorequest_slot_name[64];
        int32_t device_base_displacement = (int32_t)trace_state.app_addresses[1].displacement +
          (int32_t)AMIGA_OS_STRUCT_IO_FIELD_IO_DEVICE_OFFSET;
        if (format_open_device_app_iorequest_slot_name(trace_state.addr_regs[0].name, iorequest_slot_name,
            sizeof(iorequest_slot_name))) {
          if (render_lookup_add_base_field_slot_with_symbol(lookup, "__amiga_app_base__",
              trace_state.app_addresses[1].displacement, trace_state.addr_regs[0].name, iorequest_slot_name,
              M68K_RENDER_BASE_FIELD_SLOT_IOREQUEST, section->section_index, candidate->offset) != 0) {
            goto cleanup;
          }
        }
        if (device_base_displacement >= -32768 && device_base_displacement <= 32767) {
          if (render_lookup_add_base_field_slot(lookup, "__amiga_app_base__",
              (int16_t)device_base_displacement, trace_state.addr_regs[0].name, section->section_index,
              candidate->offset) != 0) {
            goto cleanup;
          }
        }
      }
      if (candidate_stores_library_to_local_slot(&trace_state, candidate, &local_base_reg, &local_displacement,
          &library_name)) {
        const char *owner_name = trace_state.addr_regs[local_base_reg].known
          ? trace_state.addr_regs[local_base_reg].name
          : (local_base_reg == 6U ? "__amiga_app_base__" : NULL);
        trace_local_slot_set(&trace_state, local_base_reg, local_displacement, library_name);
        if (owner_name != NULL &&
            render_lookup_add_base_field_slot(lookup, owner_name, local_displacement, library_name,
              section->section_index, candidate->offset) != 0) {
          goto cleanup;
        }
      }
      if (candidate_stores_named_value_to_app_slot(&trace_state, candidate, &named_app_slot_displacement,
          named_app_slot_symbol, sizeof(named_app_slot_symbol))) {
        if (render_lookup_add_named_app_field_slot(lookup, named_app_slot_displacement, named_app_slot_symbol,
            section->section_index, candidate->offset) != 0) {
          goto cleanup;
        }
      }
      if (candidate_copies_local_slot_to_global_slot(lookup, &trace_state, section->section_index, candidate,
          &slot_section, &slot_offset, &library_name)) {
        if (render_lookup_add_global_base_slot(lookup, slot_section, slot_offset, library_name,
            section->section_index, candidate->offset) != 0) goto cleanup;
      }
      if (candidate_loads_relocated_global_slot_to_a6(lookup, section->section_index, candidate,
          &slot_section, &slot_offset)) {
        current_slot_valid = 1;
        current_slot_section = slot_section;
        current_slot_offset = slot_offset;
      } else if (candidate_writes_a6_unknown(candidate)) {
        current_slot_valid = 0;
      }
      if (current_slot_valid && candidate_calls_a6_lvo(candidate, &lvo)) {
        if (global_base_observation_add(&observations, &observation_count, &observation_capacity,
          current_slot_section, current_slot_offset, lvo) != 0) goto cleanup;
      }
      if (candidate_loads_d0_lvo_immediate(candidate, &wrapper_lvo)) {
        uint32_t next_offset = candidate->offset + candidate->byte_count;
        const M68kDecodeCandidate *next_candidate = NULL;
        uint32_t wrapper_offset = 0U;
        if (accepted_start_at(section, accepted_start[section_index], next_offset))
          next_candidate = find_candidate_at_offset_local(section, next_offset);
        if (candidate_direct_same_section_target(next_candidate, section->section_index, &wrapper_offset)) {
          if (global_base_observation_add(&wrapper_observations, &wrapper_observation_count,
              &wrapper_observation_capacity, section->section_index, wrapper_offset, wrapper_lvo) != 0) {
            goto cleanup;
          }
        }
      }
      if (trace_state.addr_regs[6].known && candidate_calls_a6_d0_indexed_vector(candidate)) {
        if (render_lookup_add_indexed_vector_wrapper(lookup, section->section_index, current_segment_entry,
            trace_state.addr_regs[6].name) != 0 ||
            render_lookup_add_indexed_vector_wrapper(lookup, section->section_index, candidate->offset,
            trace_state.addr_regs[6].name) != 0 ||
            render_lookup_add_indexed_vector_wrapper_branch_aliases(lookup, section, accepted_start[section_index],
            current_segment_entry, trace_state.addr_regs[6].name) != 0) {
          goto cleanup;
        }
      }
      if (candidate_terminates_a6_state(candidate)) {
        current_slot_valid = 0;
        current_segment_valid = 0;
        trace_state_reset(&trace_state);
      } else {
        trace_state_update_register_names_after_candidate(&trace_state, lookup, candidate);
      }
      expected_offset = candidate->offset + candidate->byte_count;
      have_expected_offset = 1;
    }
  }
  for (section_index = 0U; section_index < observation_count; ++section_index) {
    const M68kRenderGlobalBaseObservation *observation = &observations[section_index];
    const char *library_name = unique_library_for_observed_lvos(observation);
    if (library_name == NULL) continue;
    if (render_lookup_add_global_base_slot(lookup, observation->section_index, observation->offset,
        library_name, SIZE_MAX, UINT32_MAX) != 0) goto cleanup;
  }
  for (section_index = 0U; section_index < wrapper_observation_count; ++section_index) {
    const M68kRenderGlobalBaseObservation *observation = &wrapper_observations[section_index];
    const char *library_name = unique_library_for_observed_lvos(observation);
    if (library_name == NULL) continue;
    if (render_lookup_add_indexed_vector_wrapper(lookup, observation->section_index, observation->offset,
        library_name) != 0) goto cleanup;
  }
  result = 0;
cleanup:
  free(observations);
  free(wrapper_observations);
  return result;
}

static const AmigaOsLibraryVectorInfo *resolve_amiga_direct_wrapper_vector_at(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t section_index, uint32_t wrapper_offset,
    unsigned depth) {
  const M68kDecodeSectionIR *section;
  M68kRenderPlatformState state;
  const AmigaOsLibraryVectorInfo *pending_vector = NULL;
  uint32_t cursor;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || section_index >= decode->section_count)
    return NULL;
  if (depth > 4U) return NULL;
  section = &decode->sections[section_index];
  if (!accepted_start_at(section, accepted_start[section_index], wrapper_offset)) return NULL;
  memset(&state, 0, sizeof(state));
  cursor = wrapper_offset;
  while (cursor < section->size && cursor - wrapper_offset < 128U) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    uint32_t relocation_offset;
    uint32_t relocation_end;
    const AmigaOsLibraryVectorInfo *vector;
    candidate = find_candidate_at_offset_local(section, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    if (!accepted_start_at(section, accepted_start[section_index], cursor)) break;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    relocation_end = candidate->offset + candidate->byte_count;
    for (relocation_offset = candidate->offset; relocation_offset < relocation_end; ++relocation_offset) {
      const M68kFact *relocation = lookup_relocation_at(lookup, section->section_index, relocation_offset);
      size_t operand_index = 0U;
      if (relocation == NULL) continue;
      if (!find_unique_relocation_operand(candidate, relocation, &operand_index) ||
          operand_index >= instruction.operand_count) {
        continue;
      }
      attach_operand_label_symbol(lookup, &instruction, operand_index, relocation->target_section_index,
        relocation->target_offset);
    }
    if (pending_vector != NULL) {
      if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_RTS) return pending_vector;
      if (!instruction_is_local_wrapper_cleanup(&instruction)) return NULL;
      cursor += candidate->byte_count;
      continue;
    }
    if (candidate_has_non_call_control_target(candidate)) return NULL;
    vector = resolve_amiga_direct_wrapper_call_vector_depth(lookup, decode, accepted_start, section->section_index,
      candidate, depth + 1U);
    if (vector != NULL) {
      pending_vector = vector;
      cursor += candidate->byte_count;
      continue;
    }
    vector = attach_amiga_lvo_symbol_if_known(&state, &instruction);
    if (vector != NULL) {
      if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_JMP) return vector;
      pending_vector = vector;
      cursor += candidate->byte_count;
      continue;
    }
    platform_state_update_after_instruction(&state, lookup, &instruction);
    if (candidate_terminates_a6_state(candidate)) break;
    cursor += candidate->byte_count;
  }
  return NULL;
}

static const AmigaOsLibraryVectorInfo *resolve_amiga_direct_wrapper_call_vector_depth(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
    const M68kDecodeCandidate *candidate, unsigned depth) {
  size_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  if (depth > 4U) return NULL;
  if (candidate == NULL ||
      (candidate->mnemonic_id != M68K_ASM_MNEMONIC_BSR &&
       candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR)) {
    return NULL;
  }
  if (!candidate_direct_control_target(lookup, source_section_index, candidate, &target_section_index, &target_offset))
    return NULL;
  if (target_section_index == source_section_index && target_offset == candidate->offset) return NULL;
  return resolve_amiga_direct_wrapper_vector_at(lookup, decode, accepted_start, target_section_index, target_offset,
    depth);
}

static const AmigaOsLibraryVectorInfo *resolve_amiga_direct_wrapper_call_vector(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
    const M68kDecodeCandidate *candidate) {
  return resolve_amiga_direct_wrapper_call_vector_depth(lookup, decode, accepted_start, source_section_index,
    candidate, 0U);
}

static void attach_known_instruction_relocations(const M68kRenderLookup *lookup, size_t section_index,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  uint32_t relocation_offset;
  uint32_t relocation_end;
  if (lookup == NULL || candidate == NULL || instruction == NULL) return;
  relocation_end = candidate->offset + candidate->byte_count;
  for (relocation_offset = candidate->offset; relocation_offset < relocation_end; ++relocation_offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section_index, relocation_offset);
    size_t operand_index = 0U;
    if (relocation == NULL) continue;
    if (!find_unique_relocation_operand(candidate, relocation, &operand_index) ||
        operand_index >= instruction->operand_count) {
      continue;
    }
    attach_operand_label_symbol(lookup, instruction, operand_index, relocation->target_section_index,
      relocation->target_offset);
  }
}

static const AmigaOsLibraryVectorInfo *resolve_amiga_local_helper_primary_vector_at(
    const M68kRenderLookup *lookup, const M68kDecodeIR *decode, uint8_t **accepted_start, size_t section_index,
    uint32_t helper_offset, unsigned depth) {
  const M68kDecodeSectionIR *section;
  M68kRenderPlatformState state;
  uint32_t cursor;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK ||
      section_index >= decode->section_count || depth > 4U) {
    return NULL;
  }
  section = &decode->sections[section_index];
  if (!accepted_start_at(section, accepted_start[section_index], helper_offset)) return NULL;
  memset(&state, 0, sizeof(state));
  cursor = helper_offset;
  while (cursor < section->size && cursor - helper_offset < 256U) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const AmigaOsLibraryVectorInfo *vector;
    const AmigaOsLibraryVectorInfo *nested_vector;
    if (!accepted_start_at(section, accepted_start[section_index], cursor)) break;
    candidate = find_candidate_at_offset_local(section, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    platform_state_apply_policy_register_seeds(&state, lookup->policy, section->section_index, cursor);
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
    vector = attach_amiga_lvo_symbol_if_known(&state, &instruction);
    if (vector != NULL) return vector;
    vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start[section_index], candidate,
      &instruction);
    if (vector != NULL) return vector;
    vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &state, section, candidate);
    if (vector != NULL) return vector;
    vector = resolve_amiga_direct_wrapper_call_vector_depth(lookup, decode, accepted_start, section->section_index,
      candidate, depth + 1U);
    if (vector != NULL) return vector;
    nested_vector = resolve_amiga_local_helper_call_vector_depth(lookup, decode, accepted_start,
      section->section_index, candidate, depth + 1U);
    if (nested_vector != NULL) return nested_vector;
    if (candidate->mnemonic_id == M68K_ASM_MNEMONIC_BSR ||
        candidate->mnemonic_id == M68K_ASM_MNEMONIC_JSR) {
      return NULL;
    }
    platform_state_update_d0_lvo_after_instruction(&state, &instruction);
    platform_state_update_after_instruction(&state, lookup, &instruction);
    if (!candidate_has_local_helper_summary_fallthrough(candidate)) break;
    cursor += candidate->byte_count;
  }
  return NULL;
}

static const AmigaOsLibraryVectorInfo *resolve_amiga_local_helper_call_vector_depth(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
    const M68kDecodeCandidate *candidate, unsigned depth) {
  size_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  if (depth > 4U || candidate == NULL ||
      (candidate->mnemonic_id != M68K_ASM_MNEMONIC_BSR &&
       candidate->mnemonic_id != M68K_ASM_MNEMONIC_JSR)) {
    return NULL;
  }
  if (!candidate_direct_control_target(lookup, source_section_index, candidate, &target_section_index, &target_offset))
    return NULL;
  if (target_section_index == source_section_index && target_offset == candidate->offset) return NULL;
  return resolve_amiga_local_helper_primary_vector_at(lookup, decode, accepted_start, target_section_index,
    target_offset, depth);
}

static const AmigaOsLibraryVectorInfo *resolve_amiga_local_helper_call_vector(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
    const M68kDecodeCandidate *candidate) {
  return resolve_amiga_local_helper_call_vector_depth(lookup, decode, accepted_start, source_section_index,
    candidate, 0U);
}

static int render_lookup_infer_amiga_call_input_comments(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start) {
  M68kRenderPlatformState platform_state;
  M68kRenderDataPointerState data_pointer_state;
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  memset(&platform_state, 0, sizeof(platform_state));
  data_pointer_state_clear_all(&data_pointer_state);
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    data_pointer_state_clear_all(&data_pointer_state);
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      const AmigaOsLibraryVectorInfo *platform_vector;
      const AmigaOsLibraryVectorInfo *immediate_vector;
      const AmigaOsLibraryVectorInfo *wrapper_call_vector;
      const AmigaOsLibraryVectorInfo *direct_wrapper_vector;
      const AmigaOsLibraryVectorInfo *vector;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      platform_state_apply_policy_register_seeds(&platform_state, lookup->policy, section->section_index,
        candidate->offset);
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
      platform_vector = attach_amiga_lvo_symbol_if_known(&platform_state, &instruction);
      immediate_vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start[section_index],
        candidate, &instruction);
      wrapper_call_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &platform_state, section, candidate);
      direct_wrapper_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start,
        section->section_index, candidate);
      vector = platform_vector != NULL ? platform_vector :
        (direct_wrapper_vector != NULL ? direct_wrapper_vector :
        (wrapper_call_vector != NULL ? wrapper_call_vector : immediate_vector));
      if (vector != NULL &&
          render_lookup_add_call_setup_comments_for_vector(lookup, section, accepted_start[section_index],
            candidate->offset, vector, platform_vector != NULL || immediate_vector != NULL) != 0) {
        return -1;
      }
      if (vector != NULL && render_lookup_add_string_spans_for_vector_inputs(lookup, decode, vector,
          &data_pointer_state) != 0) {
        return -1;
      }
      data_pointer_state_update_after_instruction(&data_pointer_state, candidate, &instruction);
      platform_state_update_d0_lvo_after_instruction(&platform_state, &instruction);
      platform_state_update_after_instruction(&platform_state, lookup, &instruction);
    }
  }
  return 0;
}

static int attach_symbolic_targets(const M68kRenderLookup *lookup, const M68kDecodeCandidate *candidate,
    M68kInstructionIR *instruction) {
  size_t target_index;
  if (lookup == NULL || candidate == NULL || instruction == NULL) return -1;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->has_section == 0U || target->has_operand == 0U ||
        target->operand_index >= instruction->operand_count) {
      continue;
    }
    if (!lookup_has_renderable_label(lookup, target->section_index, target->offset)) continue;
    if (symbol_ref_kind_for_operand(&instruction->operands[target->operand_index]) == M68K_IR_SYMBOL_REF_ABS)
      continue;
    attach_operand_label_symbol(lookup, instruction, target->operand_index, target->section_index, target->offset);
  }
  return 0;
}

static int instruction_relocation_is_proven_operand(const M68kRenderLookup *lookup, const M68kDecodeCandidate *candidate,
    const M68kFact *relocation, M68kInstructionIR *instruction) {
  size_t target_index;
  if (lookup == NULL || candidate == NULL || relocation == NULL || instruction == NULL) return 0;
  if (!lookup_has_renderable_label(lookup, relocation->target_section_index, relocation->target_offset)) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->has_operand == 0U || target->operand_index >= instruction->operand_count) continue;
    if (!target_matches_relocation(target, relocation)) continue;
    attach_operand_label_symbol(lookup, instruction, target->operand_index, relocation->target_section_index,
      relocation->target_offset);
    return 1;
  }
  {
    size_t operand_index = 0U;
    if (find_unique_relocation_operand(candidate, relocation, &operand_index) &&
        operand_index < instruction->operand_count) {
      attach_operand_label_symbol(lookup, instruction, operand_index, relocation->target_section_index,
        relocation->target_offset);
      return 1;
    }
  }
  return 0;
}

static int attach_proven_instruction_relocations(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    size_t section_index, const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  uint32_t offset;
  uint32_t end;
  int ok = 1;
  if (preview == NULL || lookup == NULL || candidate == NULL || instruction == NULL) return 0;
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset; offset < end; ++offset) {
    const M68kFact *fact = lookup_relocation_at(lookup, section_index, offset);
    if (fact == NULL) continue;
    if (!instruction_relocation_is_proven_operand(lookup, candidate, fact, instruction)) {
      ++preview->asm_source_instruction_relocation_failures;
      record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_INSTRUCTION_RELOCATION,
        section_index, candidate->offset, fact->offset);
      ok = 0;
    }
  }
  return ok;
}

static const M68kFact *first_anchor_in_candidate(const M68kRenderLookup *lookup, size_t section_index,
    const M68kDecodeCandidate *candidate, uint32_t *out_count) {
  uint32_t offset;
  uint32_t end;
  const M68kFact *first = NULL;
  uint32_t count = 0U;
  if (out_count != NULL) *out_count = 0U;
  if (lookup == NULL || candidate == NULL) return NULL;
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset; offset < end; ++offset) {
    const M68kFact *anchor = lookup_anchor_at(lookup, section_index, offset);
    if (anchor == NULL) continue;
    if (first == NULL) first = anchor;
    ++count;
  }
  if (out_count != NULL) *out_count = count;
  return first;
}

static int instruction_loads_immediate_to_register(const M68kInstructionIR *instruction, uint8_t *out_reg_kind,
    uint8_t *out_reg_index, uint32_t *out_value) {
  uint32_t value = 0U;
  uint8_t reg = 0U;
  if (out_reg_kind != NULL) *out_reg_kind = 0U;
  if (out_reg_index != NULL) *out_reg_index = 0U;
  if (out_value != NULL) *out_value = 0U;
  if (instruction == NULL || instruction->operand_count != 2U ||
      !operand_is_immediate_value_local(&instruction->operands[0], &value)) {
    return 0;
  }
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEQ) {
    return 0;
  }
  if (operand_is_data_register_local(&instruction->operands[1], &reg)) {
    if (out_reg_kind != NULL) *out_reg_kind = 1U;
  } else if (operand_address_register_index_local(&instruction->operands[1], &reg)) {
    if (out_reg_kind != NULL) *out_reg_kind = 2U;
  } else {
    return 0;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ) value = (uint32_t)(int32_t)(int8_t)(value & 0xFFU);
  else if (instruction->size_suffix == 'b') value = (uint32_t)(int32_t)(int8_t)(value & 0xFFU);
  else if (instruction->size_suffix == 'w') value = (uint32_t)(int32_t)(int16_t)(value & 0xFFFFU);
  if (out_reg_index != NULL) *out_reg_index = reg;
  if (out_value != NULL) *out_value = value;
  return 1;
}

static int instruction_writes_register(const M68kInstructionIR *instruction, uint8_t reg_kind,
    uint8_t reg_index) {
  size_t operand_index;
  uint8_t reg = 0U;
  if (instruction == NULL || reg_kind == 0U || reg_index >= 8U) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count >= 2U &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
    if (reg_kind == 1U) return reglist_contains_data_register_local(&instruction->operands[1], reg_index);
    return reglist_contains_address_register_local(&instruction->operands[1], reg_index);
  }
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (!instruction_operand_writes_register_from_metadata(instruction, operand_index)) continue;
    if (reg_kind == 1U && operand_is_data_register_local(operand, &reg) && reg == reg_index) return 1;
    if (reg_kind == 2U && operand_address_register_index_local(operand, &reg) && reg == reg_index) return 1;
  }
  return 0;
}

static int attach_amiga_next_call_input_immediate_symbol(M68kRenderIRPreview *preview,
    const M68kRenderLookup *lookup, const M68kRenderPlatformState *platform_state, const M68kDecodeIR *decode,
    uint8_t **accepted_start_all, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    M68kInstructionIR *instruction) {
  M68kRenderPlatformState state;
  uint8_t reg_kind = 0U;
  uint8_t reg_index = 0U;
  uint32_t value = 0U;
  uint32_t cursor;
  size_t scan_count = 0U;
  if (preview == NULL || lookup == NULL || platform_state == NULL || decode == NULL || accepted_start_all == NULL ||
      section == NULL || candidate == NULL || instruction == NULL) {
    return 0;
  }
  if (lookup->object == NULL || lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK)
    return 0;
  if (!instruction_loads_immediate_to_register(instruction, &reg_kind, &reg_index, &value)) return 0;
  state = *platform_state;
  cursor = candidate->offset + candidate->byte_count;
  while (cursor < section->size && scan_count < 12U) {
    const M68kDecodeCandidate *next_candidate;
    M68kInstructionIR next_instruction;
    const AmigaOsLibraryVectorInfo *platform_vector;
    const AmigaOsLibraryVectorInfo *immediate_vector;
    const AmigaOsLibraryVectorInfo *wrapper_call_vector;
    const AmigaOsLibraryVectorInfo *direct_wrapper_vector;
    const AmigaOsLibraryVectorInfo *helper_call_vector;
    const AmigaOsLibraryVectorInfo *vector;
    const AmigaOsCallInputInfo *input;
    const char *value_domain_name;
    char symbol_expr[64];
    if (!accepted_start_at(section, accepted_start_all[section->section_index], cursor)) break;
    next_candidate = find_candidate_at_offset_local(section, cursor);
    if (next_candidate == NULL || next_candidate->byte_count == 0U) break;
    platform_state_apply_policy_register_seeds(&state, lookup->policy, section->section_index, cursor);
    if (m68k_decode_candidate_to_instruction(next_candidate, &next_instruction) != 0) break;
    attach_known_instruction_relocations(lookup, section->section_index, next_candidate, &next_instruction);
    platform_vector = attach_amiga_lvo_symbol_if_known(&state, &next_instruction);
    immediate_vector = attach_amiga_lvo_immediate_if_known(lookup, section,
      accepted_start_all[section->section_index], next_candidate, &next_instruction);
    wrapper_call_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &state, section, next_candidate);
    direct_wrapper_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start_all,
      section->section_index, next_candidate);
    helper_call_vector = (platform_vector == NULL && immediate_vector == NULL && wrapper_call_vector == NULL &&
      direct_wrapper_vector == NULL)
      ? resolve_amiga_local_helper_call_vector(lookup, decode, accepted_start_all, section->section_index,
          next_candidate)
      : NULL;
    vector = platform_vector != NULL ? platform_vector :
      (direct_wrapper_vector != NULL ? direct_wrapper_vector :
      (wrapper_call_vector != NULL ? wrapper_call_vector :
      (immediate_vector != NULL ? immediate_vector : helper_call_vector)));
    if (vector != NULL) {
      input = amiga_vector_input_by_register(vector, reg_kind, reg_index);
      if (input == NULL) return 0;
      value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, input->value_domain_id);
      if (value_domain_name == NULL ||
          !amiga_value_domain_symbolic_expr(value_domain_name, value, symbol_expr, sizeof(symbol_expr))) {
        return 0;
      }
      if (!render_asm_include_for_symbol_expr(preview, symbol_expr)) {
        ++preview->asm_source_instruction_render_failures;
        record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, section->section_index,
          candidate->offset, 0U);
        return -1;
      }
      m68k_ir_symbol_ref_init(&instruction->operands[0].symbol_ref);
      instruction->operands[0].symbol_ref.has_name = 1U;
      instruction->operands[0].symbol_ref.name_is_generated = 0U;
      instruction->operands[0].symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
      instruction->operands[0].symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
      snprintf(instruction->operands[0].symbol_ref.name, sizeof(instruction->operands[0].symbol_ref.name), "%s",
        symbol_expr);
      return 1;
    }
    if (instruction_writes_register(&next_instruction, reg_kind, reg_index)) break;
    if (next_candidate->mnemonic_id == M68K_ASM_MNEMONIC_BSR ||
        next_candidate->mnemonic_id == M68K_ASM_MNEMONIC_JSR) {
      break;
    }
    platform_state_update_d0_lvo_after_instruction(&state, &next_instruction);
    platform_state_update_after_instruction(&state, lookup, &next_instruction);
    if (!candidate_has_local_helper_summary_fallthrough(next_candidate)) break;
    cursor += next_candidate->byte_count;
    ++scan_count;
  }
  return 0;
}

static void record_facts_v2_platform_call(M68kRenderIRPreview *preview,
    M68kSectionAnalysisIR *section_analysis, uint32_t offset,
    const PlatformFactsV2ResolvedCall *call_info) {
  if (preview == NULL || call_info == NULL || call_info->platform_kind == 0U) return;
  ++preview->platform_call_count;
  if (section_analysis == NULL) return;
  if (m68k_ir_section_analysis_append_recovered_platform_call(section_analysis, call_info->platform_kind,
      offset, call_info->kind, NULL, call_info->note_kind,
      call_info->note_base_name[0] != '\0' ? call_info->note_base_name : NULL,
      call_info->note_symbol_name[0] != '\0' ? call_info->note_symbol_name : NULL,
      0U, INT16_MIN, INT16_MIN, call_info->note_stack_cleanup_known,
      call_info->note_stack_cleanup_bytes, call_info->note_return_kind, NULL, NULL) != 0) {
    preview->asm_source_allocation_failed = 1U;
  }
}

static int record_platform_trap_call_for_render(M68kRenderIRPreview *preview,
    const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kDecodeCandidate *candidate, M68kSectionAnalysisIR *section_analysis) {
  PlatformFactsV2ResolvedCall call_info;
  uint32_t block_start;
  if (preview == NULL || lookup == NULL || lookup->object == NULL || section == NULL || candidate == NULL)
    return 0;
  block_start = lookup_code_block_start_before_or_at(lookup, section->section_index, candidate->offset);
  if (!platform_facts_v2_resolve_trap_call(lookup->object->platform_backend_kind, section, accepted_start,
      block_start, candidate->offset, &call_info)) {
    return 0;
  }
  record_facts_v2_platform_call(preview, section_analysis, candidate->offset, &call_info);
  return 1;
}

static void attach_platform_stack_cleanup_comment_for_render(M68kRenderIRPreview *preview,
    const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction,
    M68kSectionAnalysisIR *section_analysis, char *comment, size_t comment_size) {
  PlatformFactsV2ResolvedCall call_info;
  uint32_t block_start;
  char note[160];
  if (preview == NULL || lookup == NULL || lookup->object == NULL || section == NULL || accepted_start == NULL ||
      candidate == NULL || instruction == NULL || comment == NULL || comment_size == 0U) {
    return;
  }
  block_start = lookup_code_block_start_before_or_at(lookup, section->section_index, candidate->offset);
  if (!platform_facts_v2_resolve_stack_cleanup_call(lookup->object->platform_backend_kind, section,
      accepted_start, block_start, candidate->offset, instruction, &call_info)) {
    return;
  }
  if (call_info.note_symbol_name[0] == '\0') return;
  snprintf(note, sizeof(note), "KNOWN: stack cleanup for %s pop %u", call_info.note_symbol_name,
    (unsigned)call_info.note_stack_cleanup_bytes);
  (void)append_comment_part_local(comment, comment_size, note);
  record_facts_v2_platform_call(preview, section_analysis, candidate->offset, &call_info);
}

static int render_asm_instruction(M68kRenderIRPreview *preview, const M68kRenderLookup *lookup,
    M68kRenderPlatformState *platform_state, const M68kDecodeIR *decode, uint8_t **accepted_start_all,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const M68kDecodeCandidate *candidate,
    M68kRenderTypedState *typed_state, M68kSectionAnalysisIR *section_analysis) {
  M68kInstructionIR instruction;
  M68kInstructionIR render_instruction;
  M68kRenderPolicy policy;
  M68kDiagList render_diagnostics;
  M68kDiagList encode_diagnostics;
  M68kIrRenderResult rendered;
  M68kIrEncodeResult encoded;
  const AmigaOsLibraryVectorInfo *platform_vector = NULL;
  const AmigaOsLibraryVectorInfo *immediate_vector = NULL;
  const AmigaOsLibraryVectorInfo *wrapper_call_vector = NULL;
  const AmigaOsLibraryVectorInfo *direct_wrapper_vector = NULL;
  const AmigaOsLibraryVectorInfo *helper_call_vector = NULL;
  const AmigaOsLibraryVectorInfo *chosen_vector = NULL;
  uint8_t chosen_kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL;
  uint8_t chosen_note_kind = M68K_PLATFORM_CALL_NOTE_NONE;
  uint8_t encoded_bytes[32];
  char platform_comment[160];
  char instruction_comment[640];
  char line[1024];
  if (preview == NULL || lookup == NULL || section == NULL || candidate == NULL) return 0;
  platform_comment[0] = '\0';
  instruction_comment[0] = '\0';
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, section->section_index,
      candidate->offset, 0U);
    return 0;
  }
  if (attach_symbolic_targets(lookup, candidate, &instruction) != 0 ||
      !attach_proven_instruction_relocations(preview, lookup, section->section_index, candidate, &instruction)) {
    return 0;
  }
  platform_vector = attach_amiga_lvo_symbol_if_known(platform_state, &instruction);
  immediate_vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start, candidate, &instruction);
  wrapper_call_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, platform_state, section, candidate);
  direct_wrapper_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start_all,
    section->section_index, candidate);
  (void)record_platform_trap_call_for_render(preview, lookup, section, accepted_start, candidate, section_analysis);
  if (platform_vector == NULL && immediate_vector == NULL && wrapper_call_vector == NULL &&
      direct_wrapper_vector == NULL) {
    helper_call_vector = resolve_amiga_local_helper_call_vector(lookup, decode, accepted_start_all,
      section->section_index, candidate);
  }
  if (platform_vector != NULL &&
      !render_asm_include_for_amiga_symbol_id(preview, platform_vector->lvo_symbol_id)) {
    return 0;
  }
  if (immediate_vector != NULL &&
      !render_asm_include_for_amiga_symbol_id(preview, immediate_vector->lvo_symbol_id)) {
    return 0;
  }
  if (wrapper_call_vector != NULL &&
      !render_asm_include_for_amiga_symbol_id(preview, wrapper_call_vector->lvo_symbol_id)) {
    return 0;
  }
  if (direct_wrapper_vector != NULL &&
      !render_asm_include_for_amiga_symbol_id(preview, direct_wrapper_vector->lvo_symbol_id)) {
    return 0;
  }
  if (helper_call_vector != NULL &&
      !render_asm_include_for_amiga_symbol_id(preview, helper_call_vector->lvo_symbol_id)) {
    return 0;
  }
  if (attach_amiga_next_call_input_immediate_symbol(preview, lookup, platform_state, decode, accepted_start_all,
      section, candidate, &instruction) < 0) {
    return 0;
  }
  (void)attach_amiga_app_base_slot_symbols(lookup, platform_state, &instruction);
  (void)attach_amiga_typed_struct_field_symbols(typed_state, &instruction);
  if (!render_asm_include_for_instruction_platform_symbols(preview, &instruction)) return 0;
  if (!format_amiga_local_wrapper_call_comment(direct_wrapper_vector != NULL ? direct_wrapper_vector : wrapper_call_vector,
      platform_comment, sizeof(platform_comment))) {
    (void)format_amiga_local_helper_call_comment(helper_call_vector, platform_comment, sizeof(platform_comment));
  }
  attach_platform_stack_cleanup_comment_for_render(preview, lookup, section, accepted_start, candidate, &instruction,
    section_analysis, platform_comment, sizeof(platform_comment));
  (void)append_comment_part_local(instruction_comment, sizeof(instruction_comment),
    lookup_instruction_comment(lookup, section->section_index, candidate->offset));
  (void)append_comment_part_local(instruction_comment, sizeof(instruction_comment), platform_comment);
  apply_exact_byte_immediate_render_values(&instruction, section->data + candidate->offset, candidate->byte_count);
  render_instruction = instruction;
  if (instruction_renders_with_fpu_mnemonic_for_render(&instruction) &&
      !make_fpu_id_render_instruction_for_preview(&instruction, &render_instruction)) {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, section->section_index,
      candidate->offset, 0U);
    return 0;
  }
  m68k_render_policy_init_default(&policy);
  m68k_diag_list_reset(&render_diagnostics);
  rendered = m68k_ir_render_one_at_with_policy(&render_instruction, candidate->offset, &policy,
    m68k_diag_sink(&render_diagnostics));
  if (m68k_diag_has_errors(&render_diagnostics) || rendered.text[0] == '\0') {
    ++preview->asm_source_instruction_render_failures;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_RENDER, section->section_index,
      candidate->offset, 0U);
    return 0;
  }
  m68k_diag_list_reset(&encode_diagnostics);
  encoded = m68k_ir_encode_one(&instruction, encoded_bytes, sizeof(encoded_bytes), m68k_diag_sink(&encode_diagnostics));
  if (m68k_diag_has_errors(&encode_diagnostics) || encoded.byte_count != candidate->byte_count ||
      !encoded_bytes_match_with_exact_byte_immediates(&instruction, encoded_bytes, section->data + candidate->offset,
        candidate->byte_count)) {
    ++preview->asm_source_instruction_byte_mismatches;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_BYTE_MISMATCH, section->section_index,
      candidate->offset, 0U);
    return 0;
  }
  if (!rendered_text_reencodes_original_bytes(rendered.text, &instruction, &render_instruction, section->data + candidate->offset,
      candidate->byte_count)) {
    ++preview->asm_source_instruction_byte_mismatches;
    record_asm_source_failure(preview, M68K_RENDER_IR_ASM_SOURCE_FAILURE_BYTE_MISMATCH, section->section_index,
      candidate->offset, 0U);
    return 0;
  }
  {
    uint32_t anchor_count = 0U;
    const M68kFact *anchor = first_anchor_in_candidate(lookup, section->section_index, candidate, &anchor_count);
    if (anchor != NULL) {
      char comment[384];
      format_lossy_hunk_anchor_comment(comment, sizeof(comment), lookup, anchor);
      if (anchor_count > 1U) {
        char count_suffix[64];
        snprintf(count_suffix, sizeof(count_suffix), "; %u lossy hunk relocations in instruction",
          (unsigned)anchor_count);
        strncat(comment, count_suffix, sizeof(comment) - strlen(comment) - 1U);
      }
      if (instruction_comment[0] != '\0') {
        snprintf(line, sizeof(line), "\t%s\t; %s; %s\n", rendered.text, instruction_comment, comment);
      } else {
        snprintf(line, sizeof(line), "\t%s\t; %s\n", rendered.text, comment);
      }
      preview->asm_source_lossy_numeric_hunk_relocations += anchor_count;
    } else if (instruction_comment[0] != '\0') {
      snprintf(line, sizeof(line), "\t%s\t; %s\n", rendered.text, instruction_comment);
    } else {
      snprintf(line, sizeof(line), "\t%s\n", rendered.text);
    }
    if (instruction_needs_fpu_id_directive_for_render(&instruction)) {
      char scoped_line[1200];
      snprintf(scoped_line, sizeof(scoped_line), "\tFPU     %u\n%s\tFPU     1\n",
        (unsigned)instruction.coprocessor_id, line);
      snprintf(line, sizeof(line), "%s", scoped_line);
      preview->asm_source_lines += 2U;
    }
  }
  hash_asm_text(preview, line);
  ++preview->asm_source_lines;
  ++preview->asm_source_symbolic_instructions;
  chosen_vector = platform_vector != NULL ? platform_vector :
    (direct_wrapper_vector != NULL ? direct_wrapper_vector :
    (wrapper_call_vector != NULL ? wrapper_call_vector :
    (immediate_vector != NULL ? immediate_vector : helper_call_vector)));
  if (wrapper_call_vector != NULL) {
    chosen_kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH;
    chosen_note_kind = M68K_PLATFORM_CALL_NOTE_INDEXED_VECTOR;
  } else if (direct_wrapper_vector != NULL || helper_call_vector != NULL) {
    chosen_note_kind = M68K_PLATFORM_CALL_NOTE_LOCAL_WRAPPER_SYMBOL;
  }
  preview_record_platform_vector_call(preview, section_analysis, candidate->offset, chosen_kind,
    chosen_note_kind, chosen_vector);
  typed_state_update_after_instruction(typed_state, &instruction, chosen_vector);
  platform_state_update_d0_lvo_after_instruction(platform_state, &instruction);
  platform_state_update_after_instruction(platform_state, lookup, &instruction);
  return 1;
}

void m68k_render_ir_preview_init(M68kRenderIRPreview *preview) {
  if (preview == NULL) return;
  memset(preview, 0, sizeof(*preview));
  preview->structural_hash = 1469598103934665603ULL;
  preview->text_hash = 1469598103934665603ULL;
  preview->asm_source_hash = 1469598103934665603ULL;
}

void m68k_render_ir_preview_destroy(M68kRenderIRPreview *preview) {
  if (preview == NULL) return;
  free(preview->asm_source_text);
  memset(preview, 0, sizeof(*preview));
}

int m68k_render_ir_preview_build(const M68kObject *object, const M68kDecodeIR *decode, const M68kFactIR *facts,
    const M68kAnalysisPolicy *policy, uint8_t **accepted_start, uint8_t **accepted_bytes, int render_text_preview,
    int render_asm_source, int collect_asm_source_text, M68kRenderIRPreview *out_preview,
    M68kSourceAnalysisIR *out_source_analysis) {
  size_t section_index;
  M68kRenderLookup lookup;
  M68kRenderPlatformState platform_state;
  M68kRenderTypedState render_typed_state;
  M68kSectionAnalysisIR section_analysis;
  int section_analysis_live = 0;
  int result = -1;
  if (decode == NULL || facts == NULL || accepted_start == NULL || accepted_bytes == NULL || out_preview == NULL)
    return -1;
  memset(&lookup, 0, sizeof(lookup));
  memset(&platform_state, 0, sizeof(platform_state));
  typed_state_clear_all(&render_typed_state);
  memset(&section_analysis, 0, sizeof(section_analysis));
  m68k_render_ir_preview_init(out_preview);
  out_preview->platform_backend_kind = object->platform_backend_kind;
  if (out_source_analysis != NULL) {
    if (m68k_ir_source_analysis_create(out_source_analysis) != 0) goto cleanup;
    out_source_analysis->file_kind = object->platform_file_kind;
    if (policy != NULL) out_source_analysis->policy = *policy;
  }
  if (render_lookup_build(&lookup, object, decode, facts, policy) != 0) goto cleanup;
  if (render_asm_source && render_lookup_infer_global_base_slots(&lookup, decode, accepted_start) != 0)
    goto cleanup;
  if (render_asm_source && render_lookup_infer_amiga_recovered_local_call_summaries(&lookup, decode,
      accepted_start) != 0)
    goto cleanup;
  if (render_asm_source && render_lookup_infer_amiga_recovered_function_args(&lookup, decode, accepted_start) != 0)
    goto cleanup;
  if (render_asm_source && render_lookup_infer_amiga_typed_slot_effects(&lookup, decode, accepted_start) != 0)
    goto cleanup;
  if (render_asm_source && render_lookup_infer_amiga_call_input_comments(&lookup, decode, accepted_start) != 0)
    goto cleanup;
  if (render_asm_source && render_lookup_analyze_amiga_app_state_slots(&lookup, decode, accepted_start) != 0)
    goto cleanup;
  if (render_asm_source) {
    out_preview->platform_base_slot_count = (uint32_t)(lookup.global_base_slot_count + lookup.base_field_slot_count);
  }
  out_preview->collect_asm_source_text = render_asm_source && collect_asm_source_text ? 1U : 0U;
  out_preview->collect_asm_source_hash = out_preview->collect_asm_source_text;
  if (render_asm_source) render_asm_platform_header(out_preview, object);
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kSectionAnalysisIR *current_section_analysis = NULL;
    uint32_t offset = 0U;
    uint32_t render_extent = render_section_extent(section);
    size_t render_candidate_index = 0U;
    typed_state_clear_all(&render_typed_state);
    out_preview->structural_hash = hash_step(out_preview->structural_hash, section_index);
    out_preview->structural_hash = hash_step(out_preview->structural_hash, render_extent);
    if (out_source_analysis != NULL) {
      if (m68k_ir_section_analysis_create(&section_analysis) != 0) goto cleanup;
      section_analysis_live = 1;
      section_analysis.section_index = section->section_index;
      section_analysis.section_kind = section->kind;
      section_analysis.section_size = section->allocation_size != 0U ? section->allocation_size : section->size;
      if (m68k_ir_section_analysis_set_name(&section_analysis, section->name) != 0 ||
          m68k_ir_section_analysis_set_code_map(&section_analysis, accepted_start[section_index],
            accepted_bytes[section_index], section->size) != 0) {
        goto cleanup;
      }
      if (append_render_lookup_platform_effects_for_section(&lookup, &section_analysis) != 0) goto cleanup;
      if (append_render_lookup_app_slot_refs_for_section(&lookup, &section_analysis) != 0) goto cleanup;
      if (append_render_lookup_recovered_local_call_summaries_for_section(&lookup, &section_analysis) != 0)
        goto cleanup;
      if (append_render_lookup_recovered_function_args_for_section(&lookup, &section_analysis) != 0) goto cleanup;
      current_section_analysis = &section_analysis;
    }
    if (render_asm_source) {
      render_asm_section_header(out_preview, decode, section_index);
      if (section_index == 0U) render_asm_app_extension_rs(out_preview, &lookup, decode);
    }
    while (offset < render_extent) {
      if (render_asm_source) {
        platform_state_apply_policy_register_seeds(&platform_state, policy, section->section_index, offset);
        render_asm_policy_entry_comments(out_preview, policy, section->section_index, offset);
        render_asm_policy_register_seed_comment(out_preview, policy, section->section_index, offset);
      }
      if (lookup_has_renderable_label(&lookup, section->section_index, offset)) {
        ++out_preview->statement_count;
        ++out_preview->label_statement_count;
        hash_statement(out_preview, 'L', section->section_index, offset, 0U, 0U);
        if (current_section_analysis != NULL &&
            m68k_ir_section_analysis_add_label(current_section_analysis, offset) != 0) {
          goto cleanup;
        }
        if (render_text_preview) render_text_line(out_preview, 'L', section->section_index, offset, 0U, 0U);
        if (render_asm_source) render_asm_label(out_preview, &lookup, section->section_index, offset);
      }
      if (accepted_start_at(section, accepted_start[section_index], offset)) {
        const M68kDecodeCandidate *candidate = NULL;
        while (render_candidate_index < section->candidate_count &&
            section->candidates[render_candidate_index].offset < offset) {
          ++render_candidate_index;
        }
        if (render_candidate_index < section->candidate_count &&
            section->candidates[render_candidate_index].offset == offset) {
          candidate = &section->candidates[render_candidate_index];
        }
        if (candidate == NULL || candidate->byte_count == 0U) goto cleanup;
        ++out_preview->statement_count;
        ++out_preview->instruction_statement_count;
        hash_statement(out_preview, 'I', section->section_index, offset, candidate->byte_count,
          candidate->mnemonic_id);
        if (render_text_preview) render_text_line(out_preview, 'I', section->section_index, offset,
          candidate->byte_count, candidate->mnemonic_id);
        if (render_asm_source) (void)render_asm_instruction(out_preview, &lookup, &platform_state, decode,
          accepted_start, section, accepted_start[section_index], candidate, &render_typed_state,
          current_section_analysis);
        offset += candidate->byte_count;
      } else {
        const M68kFact *anchor = lookup_anchor_at(&lookup, section->section_index, offset);
        const M68kFact *relocation = lookup_relocation_at(&lookup, section->section_index, offset);
        if (anchor != NULL && offset + anchor->size <= section->size &&
            !accepted_byte_at(section, accepted_bytes[section_index], offset)) {
          ++out_preview->statement_count;
          ++out_preview->data_statement_count;
          hash_statement(out_preview, 'A', section->section_index, offset, anchor->size,
            (uint32_t)anchor->target_section_index ^ anchor->target_offset);
          if (render_text_preview) render_text_line(out_preview, 'A', section->section_index, offset,
            anchor->size, anchor->target_offset);
          if (render_asm_source) {
            render_asm_comment_line(out_preview,
              lookup_instruction_comment(&lookup, section->section_index, offset));
            render_asm_lossy_hunk_relocation(out_preview, &lookup, anchor);
          }
          offset += anchor->size;
        } else if (relocation != NULL && offset + relocation->size <= section->size &&
            !accepted_byte_at(section, accepted_bytes[section_index], offset)) {
          ++out_preview->statement_count;
          ++out_preview->data_statement_count;
          hash_statement(out_preview, 'R', section->section_index, offset, relocation->size,
            (uint32_t)relocation->target_section_index ^ relocation->target_offset);
          if (render_text_preview) render_text_line(out_preview, 'R', section->section_index, offset,
            relocation->size, relocation->target_offset);
          if (render_asm_source) {
            render_asm_comment_line(out_preview,
              lookup_instruction_comment(&lookup, section->section_index, offset));
            render_asm_relocation_expr(out_preview, &lookup, relocation);
          }
          offset += relocation->size;
        } else {
          const M68kAnalysisStructuredDataItem *structured_item =
            lookup_structured_data_item_at_offset(&lookup, section->section_index, offset);
          int structured_item_clear = structured_item != NULL && structured_item->size != 0U &&
            structured_item->size <= render_extent - offset &&
            !accepted_byte_at(section, accepted_bytes[section_index], offset);
          if (structured_item_clear) {
            uint32_t probe;
            for (probe = offset + 1U; probe < offset + structured_item->size; ++probe) {
              if (accepted_byte_at(section, accepted_bytes[section_index], probe) ||
                  lookup_has_renderable_label(&lookup, section->section_index, probe) ||
                  lookup_relocation_at(&lookup, section->section_index, probe) != NULL ||
                  lookup_anchor_at(&lookup, section->section_index, probe) != NULL ||
                  lookup_string_span_at_offset(&lookup, section->section_index, probe) != NULL ||
                  lookup_has_structured_data_item_at_offset(&lookup, section->section_index, probe)) {
                structured_item_clear = 0;
                break;
              }
            }
          }
          if (structured_item != NULL && structured_item_clear) {
            ++out_preview->statement_count;
            ++out_preview->data_statement_count;
            hash_statement(out_preview, 'S', section->section_index, offset, structured_item->size,
              structured_item->kind);
            if (render_text_preview) render_text_line(out_preview, 'S', section->section_index, offset,
              structured_item->size, structured_item->kind);
            if (render_asm_source) {
              render_asm_comment_line(out_preview,
                lookup_instruction_comment(&lookup, section->section_index, offset));
              render_asm_structured_data_item(out_preview, section, structured_item);
            }
            offset += structured_item->size;
          } else {
            const M68kRenderStringSpan *string_span =
              lookup_string_span_at_offset(&lookup, section->section_index, offset);
            int string_span_clear = string_span != NULL && string_span->size != 0U &&
              string_span->size <= render_extent - offset && offset + string_span->size <= section->size &&
              section->data != NULL && !accepted_byte_at(section, accepted_bytes[section_index], offset);
            if (string_span_clear) {
              uint32_t probe;
              for (probe = offset + 1U; probe < offset + string_span->size; ++probe) {
                if (accepted_byte_at(section, accepted_bytes[section_index], probe) ||
                    lookup_has_renderable_label(&lookup, section->section_index, probe) ||
                    lookup_relocation_at(&lookup, section->section_index, probe) != NULL ||
                    lookup_anchor_at(&lookup, section->section_index, probe) != NULL ||
                    lookup_has_structured_data_item_at_offset(&lookup, section->section_index, probe) ||
                    lookup_instruction_comment(&lookup, section->section_index, probe) != NULL) {
                  string_span_clear = 0;
                  break;
                }
              }
            }
            if (string_span != NULL && string_span_clear) {
              ++out_preview->statement_count;
              ++out_preview->data_statement_count;
              hash_statement(out_preview, 'D', section->section_index, offset, string_span->size, 0U);
              if (render_text_preview) render_text_line(out_preview, 'D', section->section_index, offset,
                string_span->size, 0U);
              if (render_asm_source) {
                render_asm_comment_line(out_preview,
                  lookup_instruction_comment(&lookup, section->section_index, offset));
                render_asm_dc_b_string(out_preview, section->data, offset, string_span->size, NULL);
              }
              offset += string_span->size;
            } else {
              uint32_t start = offset;
              int initialized_span = section->data != NULL && start < section->size;
              while (offset < render_extent &&
                  !accepted_byte_at(section, accepted_bytes[section_index], offset) &&
                  (offset == start || !lookup_has_renderable_label(&lookup, section->section_index, offset)) &&
                  lookup_relocation_at(&lookup, section->section_index, offset) == NULL &&
                  lookup_anchor_at(&lookup, section->section_index, offset) == NULL &&
                  (offset == start ||
                   !lookup_has_structured_data_item_at_offset(&lookup, section->section_index, offset)) &&
                  (offset == start ||
                   lookup_string_span_at_offset(&lookup, section->section_index, offset) == NULL) &&
                  (offset == start ||
                   lookup_instruction_comment(&lookup, section->section_index, offset) == NULL) &&
                  ((section->data != NULL && offset < section->size) == initialized_span)) {
                ++offset;
              }
              if (offset == start) ++offset;
              else {
              ++out_preview->statement_count;
              ++out_preview->data_statement_count;
              hash_statement(out_preview, 'D', section->section_index, start, offset - start, 0U);
              if (render_text_preview) render_text_line(out_preview, 'D', section->section_index, start,
                offset - start, 0U);
              if (render_asm_source) {
                render_asm_comment_line(out_preview,
                  lookup_instruction_comment(&lookup, section->section_index, start));
                if (initialized_span) render_asm_dc_b(out_preview, section->data, start, offset - start, NULL);
                else render_asm_ds_b(out_preview, offset - start, "facts_v2 uninitialized bytes");
              }
              }
            }
          }
        }
      }
    }
    if (lookup_has_renderable_label(&lookup, section->section_index, render_extent)) {
      if (render_asm_source) {
        render_asm_policy_entry_comments(out_preview, policy, section->section_index, render_extent);
        render_asm_policy_register_seed_comment(out_preview, policy, section->section_index, render_extent);
      }
      ++out_preview->statement_count;
      ++out_preview->label_statement_count;
      hash_statement(out_preview, 'L', section->section_index, render_extent, 0U, 0U);
      if (current_section_analysis != NULL &&
          m68k_ir_section_analysis_add_label(current_section_analysis, render_extent) != 0) {
        goto cleanup;
      }
      if (render_text_preview) render_text_line(out_preview, 'L', section->section_index, render_extent, 0U, 0U);
      if (render_asm_source) render_asm_label(out_preview, &lookup, section->section_index, render_extent);
    }
    if (out_source_analysis != NULL) {
      if (render_analysis_append_cfg_for_section(&lookup, section, accepted_start[section_index],
          accepted_bytes[section_index], current_section_analysis) != 0) {
        goto cleanup;
      }
      if (m68k_ir_source_analysis_append_section(out_source_analysis, current_section_analysis) != 0) goto cleanup;
      m68k_ir_section_analysis_destroy(&section_analysis);
      section_analysis_live = 0;
    }
  }
  if (out_preview->asm_source_allocation_failed) goto cleanup;
  result = 0;
cleanup:
  if (section_analysis_live) {
    m68k_ir_section_analysis_destroy(&section_analysis);
  }
  if (result != 0 && out_source_analysis != NULL) {
    m68k_ir_source_analysis_destroy(out_source_analysis);
  }
  render_lookup_destroy(&lookup);
  return result;
}
