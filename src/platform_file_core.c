/* Internal section analysis implementation for platform_file_lib. */
#include "platform_file_internal.h"

typedef struct SectionDecodeCacheEntry {
  M68kInstructionIR instruction;
  uint32_t explicit_target;
  uint8_t state;
  uint8_t has_explicit_target;
  uint8_t is_call;
  uint8_t is_unconditional_transfer;
  uint8_t is_conditional_transfer;
  uint8_t stops_fallthrough;
} SectionDecodeCacheEntry;

typedef struct SectionDecodeCache {
  SectionDecodeCacheEntry *entries;
  size_t entry_count;
} SectionDecodeCache;

struct SectionAnalysisContext {
  const M68kObject *object;
  const M68kSection *section;
  const M68kAnalysisPolicy *analysis_policy;
  SectionDecodeCache decode_cache;
};

static int section_decode_cache_init(SectionDecodeCache *cache, Arena *arena, size_t section_size);
static void apply_sim_memory_writes(M68kSimMemoryState *state, const M68kSimStepResult *result);
static int section_analysis_context_init(SectionAnalysisContext *ctx, const M68kObject *object, const M68kSection *section,
    const M68kAnalysisPolicy *analysis_policy, Arena *arena);
static int section_analysis_context_decode(const SectionAnalysisContext *ctx, uint32_t offset,
    M68kAnalysisFindings *findings, SectionDecodeResult *out_result);
int section_analysis_context_probe_decode(const SectionAnalysisContext *ctx, uint32_t offset,
    SectionDecodeResult *out_result);
uint8_t section_analysis_context_backend_kind(const SectionAnalysisContext *ctx);
const M68kObject *section_analysis_context_object(const SectionAnalysisContext *ctx);
const M68kSection *section_analysis_context_section(const SectionAnalysisContext *ctx);
size_t section_analysis_find_block_index_containing(const M68kSectionAnalysisIR *section_analysis, uint32_t offset);
int instruction_writes_address_reg_approx(const M68kInstructionIR *instruction, uint8_t reg);
int instruction_writes_data_reg_approx(const M68kInstructionIR *instruction, uint8_t reg);
static int recompute_section_findings(const SectionAnalysisContext *ctx, const M68kSectionAnalysisIR *section_analysis,
    M68kAnalysisFindings *out_findings);
static int rebuild_cpu_violations(const SectionAnalysisContext *ctx, M68kSectionAnalysisIR *section_analysis);
static int rebuild_decode_fail_violations(const SectionAnalysisContext *ctx, M68kSectionAnalysisIR *section_analysis);
int build_section_analysis(const M68kObject *object, size_t section_index, const M68kSection *section,
    Arena *scratch_arena,
    const M68kAnalysisPolicy *analysis_policy, M68kAnalysisFindings *findings, M68kSectionAnalysisIR *out_analysis,
    M68kDiagSink diagnostics);
int finalize_section_analysis(const M68kSection *section, const M68kAnalysisPolicy *analysis_policy,
    M68kSectionAnalysisIR *section_analysis, M68kAnalysisFindings *out_findings);
typedef struct RecoveredWordDispatchTable RecoveredWordDispatchTable;
int operand_is_indirect_an(const M68kOperandIR *operand, uint8_t *out_reg);
int operand_is_indirect_disp_an(const M68kOperandIR *operand, uint8_t *out_reg, int16_t *out_disp);
int operand_is_brief_indexed_an(const M68kOperandIR *operand, uint8_t *out_base_reg,
    uint8_t *out_index_is_address, uint8_t *out_index_reg, int32_t *out_disp);
const M68kRecoveredPlatformCallIR *find_recovered_platform_call(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint8_t kind);
const M68kRecoveredPlatformCallIR *find_any_recovered_platform_call(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset);
const M68kRecoveredPlatformEffectIR *find_recovered_platform_effect(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint8_t kind);
void load_recovered_platform_call_info(const M68kRecoveredPlatformCallIR *recovered,
    PlatformResolvedIndirectInfo *out_info);
void platform_resolved_indirect_info_init(PlatformResolvedIndirectInfo *info);
static int format_platform_resolved_indirect_note(const PlatformResolvedIndirectInfo *info, char *buf, size_t buf_size);
static uint32_t find_enclosing_code_start(const M68kSectionAnalysisIR *section_analysis, uint32_t offset);
static int sim_operand_direct_register_local(const M68kOperandIR *operand, uint8_t *is_address, uint8_t *reg);
const char *const AMIGA_APP_BASE_TAG = "__amiga_app_base__";
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
    M68kDiagSink diagnostics) {
  uint8_t max_cpu = effective_analysis_max_cpu(policy);
  uint8_t cpu;
  (void)offset;
  for (cpu = M68K_ASM_CPU_68000; cpu <= M68K_ASM_CPU_68060; ++cpu) {
    M68kDiagList decode_diagnostics;
    m68k_diag_list_reset(&decode_diagnostics);
    *out_instruction = m68k_ir_decode_one(data, size, cpu, m68k_diag_sink(&decode_diagnostics));
    if (!m68k_diag_has_errors(&decode_diagnostics) && out_instruction->byte_count != 0U) {
      uint8_t required_cpu = instruction_required_cpu(out_instruction);
      update_required_cpu(findings, required_cpu);
      if (required_cpu > max_cpu)
        if (findings != NULL) findings->cpu_violation_count += 1U;
      return 1;
    }
    if (cpu == M68K_ASM_CPU_68060) break;
  }
  (void)diagnostics;
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
  return m68k_ir_section_analysis_add_violation(section_analysis, offset, M68K_VIOLATION_CPU_POLICY, message);
}
static const M68kAsmFormDef *instruction_assembler_form_local(const M68kInstructionIR *instruction,
    M68kInstructionIR *out_parsed_instruction) {
  const M68kAsmFormDef *form;
  M68kRenderPolicy policy;
  M68kDiagList diagnostics;
  M68kIrRenderResult rendered;
  uint8_t mnemonic_id;
  if (out_parsed_instruction != NULL) m68k_ir_instruction_init(out_parsed_instruction);
  if (instruction == NULL) return NULL;
  mnemonic_id = instruction->mnemonic_id;
  if (instruction->form_index != M68K_IR_INVALID_FORM_INDEX &&
      (size_t)instruction->form_index < m68k_asm_form_count()) {
    form = &g_m68k_asm_forms[instruction->form_index];
    if (form->mnemonic_id == mnemonic_id) return form;
  }
  if (out_parsed_instruction == NULL) return NULL;
  m68k_render_policy_init_default(&policy);
  m68k_diag_list_reset(&diagnostics);
  rendered = m68k_ir_render_one_with_policy(instruction, &policy, m68k_diag_sink(&diagnostics));
  if (m68k_diag_has_errors(&diagnostics)) return NULL;
  m68k_diag_list_reset(&diagnostics);
  *out_parsed_instruction = m68k_plain_parse_instruction_to_ir(rendered.text, instruction->target_cpu,
    m68k_diag_sink(&diagnostics));
  if (m68k_diag_has_errors(&diagnostics)) return NULL;
  if (out_parsed_instruction->form_index == M68K_IR_INVALID_FORM_INDEX) return NULL;
  if ((size_t)out_parsed_instruction->form_index >= m68k_asm_form_count()) return NULL;
  return &g_m68k_asm_forms[out_parsed_instruction->form_index];
}

static char instruction_effective_size_suffix_local(const M68kInstructionIR *instruction, const M68kAsmFormDef *form) {
  M68kAsmOperandValue operands[4];
  size_t operand_index;
  char size_suffix;
  if (instruction == NULL) return '\0';
  if (form == NULL) return instruction->size_suffix;
  for (operand_index = 0; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index)
    operands[operand_index] = instruction->operands[operand_index].value;
  size_suffix = m68k_asm_choose_size_suffix(form, operands, instruction->operand_count, instruction->size_suffix);
  if (size_suffix != '\0') return size_suffix;
  return instruction->size_suffix;
}

static int operand_uses_single_word_extension_local(const M68kAsmOperandValue *operand) {
  if (operand == NULL) return 0;
  return (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
    (operand->ea_mode == 5 || (operand->ea_mode == 7 && operand->ea_reg == 0) ||
      (operand->ea_mode == 7 && operand->ea_reg == 2));
}

static int operand_uses_long_address_extension_local(const M68kAsmOperandValue *operand) {
  if (operand == NULL) return 0;
  return (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
    operand->ea_mode == 7 && operand->ea_reg == 1;
}

static int operand_uses_immediate_extension_local(const M68kAsmOperandValue *operand) {
  if (operand == NULL) return 0;
  return ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
      operand->ea_mode == 7 && operand->ea_reg == 4) || operand->kind == M68K_ASM_OPERAND_IMM;
}

typedef struct ByteImmediateExtensionSite {
  size_t byte_offset;
  uint8_t operand_index;
} ByteImmediateExtensionSite;

static size_t collect_byte_immediate_extension_sites(const M68kInstructionIR *instruction,
    ByteImmediateExtensionSite *out_sites, size_t max_sites) {
  M68kInstructionIR parsed_instruction;
  const M68kInstructionIR *layout_instruction = instruction;
  const M68kAsmFormDef *form = instruction_assembler_form_local(instruction, &parsed_instruction);
  char size_suffix;
  size_t site_count = 0U;
  size_t word_index;
  size_t extension_index;
  if (form == NULL) return 0U;
  if (parsed_instruction.form_index != M68K_IR_INVALID_FORM_INDEX) layout_instruction = &parsed_instruction;
  size_suffix = instruction_effective_size_suffix_local(layout_instruction, form);
  if (size_suffix != 'b') return 0U;
  word_index = 1U + form->bound_word_count;
  for (extension_index = 0; extension_index < form->extension_count; ++extension_index) {
    const M68kAsmExtensionDef *extension = &g_m68k_asm_extensions[form->extension_start + extension_index];
    const M68kAsmOperandValue *operand = &layout_instruction->operands[extension->operand_index].value;
    switch (extension->kind) {
    case M68K_ASM_EXTENSION_EA_SINGLE_WORD:
      if (operand_uses_single_word_extension_local(operand)) word_index += 1U;
      break;
    case M68K_ASM_EXTENSION_EA_LONG_ADDRESS:
      if (operand_uses_long_address_extension_local(operand)) word_index += 2U;
      break;
    case M68K_ASM_EXTENSION_EA_IMMEDIATE:
      if (operand_uses_immediate_extension_local(operand)) {
        if (site_count < max_sites) {
          out_sites[site_count].byte_offset = word_index * 2U;
          out_sites[site_count].operand_index = extension->operand_index;
        }
        ++site_count;
        word_index += 1U;
      }
      break;
    case M68K_ASM_EXTENSION_EA_INDEX:
      word_index += m68k_asm_operand_extension_word_count(form, operand, size_suffix);
      break;
    case M68K_ASM_EXTENSION_LABEL_DISP16_IF_ZERO:
    case M68K_ASM_EXTENSION_LABEL_DISP16_ALWAYS:
    case M68K_ASM_EXTENSION_DISP16_ALWAYS:
      word_index += 1U;
      break;
    default:
      break;
    }
  }
  return site_count;
}

static int instruction_requires_exact_byte_immediate_preservation(const M68kInstructionIR *instruction,
    const uint8_t *raw_bytes, size_t raw_size) {
  ByteImmediateExtensionSite sites[4];
  size_t site_count;
  size_t site_index;
  M68kInstructionIR parsed_instruction;
  const M68kInstructionIR *layout_instruction = instruction;
  if (instruction == NULL || raw_bytes == NULL || raw_size == 0U) return 0;
  m68k_ir_instruction_init(&parsed_instruction);
  if (instruction_assembler_form_local(instruction, &parsed_instruction) != NULL &&
      parsed_instruction.form_index != M68K_IR_INVALID_FORM_INDEX)
    layout_instruction = &parsed_instruction;
  site_count = collect_byte_immediate_extension_sites(layout_instruction, sites, sizeof(sites) / sizeof(sites[0]));
  if (site_count == 0U) return 0;
  for (site_index = 0; site_index < site_count; ++site_index) {
    size_t byte_offset = sites[site_index].byte_offset;
    uint8_t operand_index = sites[site_index].operand_index;
    uint16_t raw_word;
    uint32_t operand_value;
    if (byte_offset + 1U >= raw_size) continue;
    if (operand_index >= layout_instruction->operand_count) continue;
    raw_word = m68k_read_u16be(raw_bytes + byte_offset);
    if ((raw_word & 0xFF00u) == 0u) continue;
    operand_value = layout_instruction->operands[operand_index].value.value;
    if ((raw_word & 0xFFu) != (operand_value & 0xFFu)) return 0;
    return 1;
  }
  return 0;
}

static int apply_exact_byte_immediate_render_values(M68kInstructionIR *instruction, const uint8_t *raw_bytes,
    size_t raw_size) {
  ByteImmediateExtensionSite sites[4];
  size_t site_count;
  size_t site_index;
  if (instruction == NULL || raw_bytes == NULL || raw_size == 0U) return 0;
  if (!instruction_requires_exact_byte_immediate_preservation(instruction, raw_bytes, raw_size)) return 0;
  site_count = collect_byte_immediate_extension_sites(instruction, sites, sizeof(sites) / sizeof(sites[0]));
  for (site_index = 0; site_index < site_count; ++site_index) {
    uint8_t operand_index = sites[site_index].operand_index;
    uint16_t raw_word;
    if (sites[site_index].byte_offset + 1U >= raw_size) continue;
    if (operand_index >= instruction->operand_count) continue;
    raw_word = m68k_read_u16be(raw_bytes + sites[site_index].byte_offset);
    if ((raw_word & 0xFF00u) == 0u) continue;
    instruction->operands[operand_index].has_exact_render_value = 1U;
    instruction->operands[operand_index].exact_render_value = raw_word;
  }
  return 1;
}

static void append_vasm_normalized_byte_immediate_note(char *buf, size_t buf_size, const M68kInstructionIR *instruction,
    const uint8_t *raw_bytes, size_t raw_size) {
  ByteImmediateExtensionSite sites[4];
  size_t site_count;
  if (buf == NULL || buf_size == 0U || instruction == NULL || raw_bytes == NULL || raw_size == 0U) return;
  if (!instruction_requires_exact_byte_immediate_preservation(instruction, raw_bytes, raw_size)) return;
  site_count = collect_byte_immediate_extension_sites(instruction, sites, sizeof(sites) / sizeof(sites[0]));
  if (site_count == 0U) return;
  if (sites[0].byte_offset + 1U >= raw_size) return;
  snprintf(buf, buf_size, "NOTE: vasm-normalized from exact immediate word $%04X",
    (unsigned)m68k_read_u16be(raw_bytes + sites[0].byte_offset));
}

static int instruction_roundtrips_exact_bytes(const M68kInstructionIR *instruction,
    const uint8_t *raw_bytes, size_t raw_size) {
  uint8_t encoded[32];
  M68kDiagList diagnostics;
  M68kIrEncodeResult encoded_result;
  M68kInstructionIR parsed_instruction;
  const M68kInstructionIR *layout_instruction = instruction;
  if (instruction == NULL || raw_bytes == NULL || raw_size == 0U) return 0;
  m68k_ir_instruction_init(&parsed_instruction);
  if (instruction_assembler_form_local(instruction, &parsed_instruction) != NULL &&
      parsed_instruction.form_index != M68K_IR_INVALID_FORM_INDEX) {
    layout_instruction = &parsed_instruction;
  }
  m68k_diag_list_reset(&diagnostics);
  encoded_result = m68k_ir_encode_one(layout_instruction, encoded, sizeof(encoded), m68k_diag_sink(&diagnostics));
  if (m68k_diag_has_errors(&diagnostics)) return 0;
  return encoded_result.byte_count == raw_size && memcmp(encoded, raw_bytes, raw_size) == 0;
}

static int instruction_has_symbolic_operands(const M68kInstructionIR *instruction) {
  size_t operand_index;
  if (instruction == NULL) return 0;
  for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
    const M68kSymbolRefIR *symbol_ref = &instruction->operands[operand_index].symbol_ref;
    if (symbol_ref->kind != M68K_IR_SYMBOL_REF_NONE) return 1;
    if (symbol_ref->has_name != 0U && symbol_ref->name[0] != '\0') return 1;
  }
  return 0;
}

typedef struct SectionDiscoveryMap {
  uint8_t *is_code_start;
  uint8_t *is_code_byte;
  size_t size;
} SectionDiscoveryMap;

static int derive_block_starts(const SectionAnalysisContext *ctx, SectionDiscoveryMap *discovery,
    const M68kSimTargetSet *sim_targets, const uint8_t *sim_stops, M68kAnalysisFindings *findings,
    M68kSectionAnalysisIR *out_analysis, uint8_t *block_starts);
static int build_cfg_blocks(const SectionAnalysisContext *ctx, SectionDiscoveryMap *discovery,
    const M68kSimTargetSet *sim_targets, const uint8_t *sim_stops, const uint8_t *sim_conditional_known,
    const uint8_t *block_starts, M68kAnalysisFindings *findings, M68kSectionAnalysisIR *out_analysis);
static int merge_sim_target_set(M68kSimTargetSet *dst, const M68kSimTargetSet *src);
static int instruction_target_operand_is_brief_indexed_pc(const M68kInstructionIR *instruction);
static int recover_entry_relative_word_dispatch_targets(const SectionDiscoveryMap *discovery,
    const M68kInstructionIR *instruction, const M68kInstructionIR *prev_instruction,
    const M68kInstructionIR *prev_prev_instruction, uint32_t prev_prev_offset, const SectionAnalysisContext *ctx,
    M68kSimTargetSet *out_targets);
static int recover_brief_word_offset_dispatch_targets(const SectionDiscoveryMap *discovery,
    const M68kInstructionIR *instruction, const M68kInstructionIR *prev_instruction,
    const M68kInstructionIR *prev_prev_instruction, const M68kInstructionIR *prev_prev_prev_instruction,
    uint32_t prev_prev_prev_offset, const SectionAnalysisContext *ctx, M68kSimTargetSet *out_targets);
static int recover_pc_index_inline_dispatch_targets(const SectionDiscoveryMap *discovery,
    const M68kInstructionIR *instruction, uint32_t instruction_offset, const SectionAnalysisContext *ctx,
    M68kSimTargetSet *out_targets);
static int collect_pc_index_inline_dispatch_table(const SectionDiscoveryMap *discovery,
    const M68kInstructionIR *instruction, uint32_t instruction_offset, const SectionAnalysisContext *ctx,
    M68kSectionAnalysisIR *out_analysis);
static int build_word_offset_dispatch_exprs(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, GeneratedLabelKind *label_kinds, size_t label_kind_count,
    uint8_t *generated_label_flags, const M68kPresentationPolicy *presentation, Arena *scratch_arena,
    char **out_word_exprs);
static int build_relative_word_expr(char *out_expr, size_t out_expr_size, const SectionAnalysisContext *ctx,
    uint32_t base_target, uint32_t target, GeneratedLabelKind *label_kinds, size_t label_kind_count,
    const M68kSectionAnalysisIR *section_analysis, uint8_t *generated_label_flags,
    const M68kPresentationPolicy *presentation);
static int build_relative_word_expr_here(char *out_expr, size_t out_expr_size, const SectionAnalysisContext *ctx,
    uint32_t base_target, uint32_t target, GeneratedLabelKind *label_kinds, size_t label_kind_count,
    const M68kSectionAnalysisIR *section_analysis, uint8_t *generated_label_flags,
    const M68kPresentationPolicy *presentation);
static int build_literal_word_expr(char *out_expr, size_t out_expr_size, uint16_t value);
static int set_word_expr_slot(Arena *scratch_arena, char **out_word_exprs, uint32_t slot_offset, const char *expr);
static int append_recovered_word_dispatch_table(M68kSectionAnalysisIR *section_analysis,
    const RecoveredWordDispatchTable *table);
static int append_recovered_string_dispatch_edges(M68kSectionAnalysisIR *section_analysis);
static int enqueue_recovered_string_dispatch_targets(const M68kObject *object, size_t section_index,
    const M68kSection *section, const SectionDiscoveryMap *discovery, M68kSectionAnalysisIR *section_analysis,
    Arena *scratch_arena, uint32_t **queue, size_t *queue_count, size_t *queue_capacity, M68kSimCpuState *entry_states,
    M68kSimMemoryState *entry_memory_states, uint8_t *entry_state_valid);
static int resolve_section_edge_target_blocks(M68kSectionAnalysisIR *section_analysis);
int instruction_direct_target_local(const SectionAnalysisContext *ctx, const M68kInstructionIR *instruction,
    uint32_t instruction_offset, uint32_t *out_target);
static int instruction_matches_indexed_an_lea(const M68kInstructionIR *instruction, uint8_t dest_reg,
    uint8_t *out_base_reg, uint8_t *out_index_reg, int32_t *out_disp);
static int analysis_has_code_start_at(const M68kSectionAnalysisIR *section_analysis, uint32_t target_offset);

static int section_analysis_has_block_start(const M68kSectionAnalysisIR *section_analysis, uint32_t offset);
static int section_analysis_has_string_dispatch_target(const M68kSectionAnalysisIR *section_analysis, uint32_t offset);
static int section_analysis_has_string_dispatch_site(const M68kSectionAnalysisIR *section_analysis, uint32_t offset);
static int add_recovered_string_dispatch_target_labels(M68kSectionAnalysisIR *section_analysis);
static int should_render_code_at_offset(const M68kSection *section, const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint8_t prev_rendered_as_code, uint8_t have_prev_instruction,
    const M68kInstructionIR *prev_instruction);

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

static void discovery_map_cleanup(SectionDiscoveryMap *map, Arena *scratch_arena) {
  if (map == NULL) return;
  (void)scratch_arena;
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

static uint32_t find_enclosing_code_start(const M68kSectionAnalysisIR *section_analysis, uint32_t offset);
static int offset_decodes_as_instruction(const SectionAnalysisContext *ctx, uint32_t target);
static int offset_decodes_as_speculative_platform_instruction(const SectionAnalysisContext *ctx, uint32_t target);
static int offset_is_known_code_byte(const M68kSectionAnalysisIR *section_analysis, uint32_t offset);
static int section_has_emittable_label(const SectionAnalysisContext *ctx, const M68kSectionAnalysisIR *section_analysis,
    const uint8_t *generated_label_flags, size_t generated_label_count, uint32_t offset);
static uint32_t find_nearest_emittable_label(const SectionAnalysisContext *ctx, const M68kSectionAnalysisIR *section_analysis,
    const uint8_t *generated_label_flags, size_t generated_label_count, uint32_t target, int prefer_non_code_only);
static uint32_t find_enclosing_instruction_start(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, M68kAnalysisFindings *findings, uint32_t target, uint32_t *out_end);

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

static int mnemonic_id_is_branch_family(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_BHI:
  case M68K_ASM_MNEMONIC_BLS:
  case M68K_ASM_MNEMONIC_BCC:
  case M68K_ASM_MNEMONIC_BCS:
  case M68K_ASM_MNEMONIC_BNE:
  case M68K_ASM_MNEMONIC_BEQ:
  case M68K_ASM_MNEMONIC_BVC:
  case M68K_ASM_MNEMONIC_BVS:
  case M68K_ASM_MNEMONIC_BPL:
  case M68K_ASM_MNEMONIC_BMI:
  case M68K_ASM_MNEMONIC_BGE:
  case M68K_ASM_MNEMONIC_BLT:
  case M68K_ASM_MNEMONIC_BGT:
  case M68K_ASM_MNEMONIC_BLE:
  case M68K_ASM_MNEMONIC_BRA:
  case M68K_ASM_MNEMONIC_BSR:
    return 1;
  default:
    return 0;
  }
}

const M68kSimFormMetadata *instruction_sim_metadata(const M68kInstructionIR *instruction) {
  return m68k_sim_metadata_for_instruction(instruction);
}

int instruction_branch_target(const M68kInstructionIR *instruction, uint32_t offset, uint32_t *out_target) {
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
  if (instruction->byte_count == 2U && size >= 2U &&
      mnemonic_id_is_branch_family(instruction->mnemonic_id)) {
    *out_target = offset + 2U + (uint32_t)((int32_t)(int8_t)data[1]);
    return 1;
  }
  if (instruction_branch_target(instruction, offset, out_target)) return 1;
  return 0;
}

static uint8_t instruction_effective_ea_shape(const M68kSimFormMetadata *metadata, const M68kInstructionIR *instruction,
    uint8_t operand_index) {
  const M68kOperandIR *operand;
  if (metadata == NULL || instruction == NULL || operand_index >= instruction->operand_count) return M68K_SIM_EA_SHAPE_NONE;
  if (metadata->operand_ea_address_shapes[operand_index] != M68K_SIM_EA_SHAPE_NONE)
    return metadata->operand_ea_address_shapes[operand_index];
  if (metadata->operand_ea_address_formulas[operand_index] != M68K_SIM_EA_FORMULA_DECODED_EA) return M68K_SIM_EA_SHAPE_NONE;
  operand = &instruction->operands[operand_index];
  return m68k_instruction_operand_decoded_ea_shape(operand);
}

static int instruction_metadata_operand_target(const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata,
    uint8_t operand_index, uint32_t offset, uint32_t section_size, uint32_t *out_target) {
  const M68kOperandIR *operand;
  uint8_t pc_bias;
  if (instruction == NULL || metadata == NULL || out_target == NULL || operand_index >= instruction->operand_count) return 0;
  operand = &instruction->operands[operand_index];
  if (operand->kind == M68K_ASM_OPERAND_LABEL) {
    return instruction_branch_target(instruction, offset, out_target) && *out_target < section_size;
  }
  if (metadata->operand_ea_address_formulas[operand_index] == M68K_SIM_EA_FORMULA_ABSOLUTE_LITERAL &&
      metadata->operand_ea_address_literal_width_bytes[operand_index] != 0U) {
    *out_target = operand->value.value;
    return *out_target < section_size;
  }
  if (metadata->operand_ea_address_formulas[operand_index] == M68K_SIM_EA_FORMULA_PC_PLUS_DISP &&
      metadata->operand_ea_displacement_sources[operand_index] == M68K_SIM_EA_DISP_OPERAND_VALUE &&
      metadata->operand_ea_uses_displacement[operand_index] &&
      !metadata->operand_ea_uses_index[operand_index]) {
    pc_bias = metadata->operand_ea_pc_base_bias_bytes[operand_index] != 0U
      ? metadata->operand_ea_pc_base_bias_bytes[operand_index]
      : 2U;
    *out_target = (uint32_t)((int32_t)offset + (int32_t)pc_bias + (int32_t)operand->value.value);
    return *out_target < section_size;
  }
  if (metadata->operand_result_kinds[operand_index] == M68K_SIM_RESULT_ADDRESS &&
      metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_IMMEDIATE) {
    *out_target = operand->value.value;
    return *out_target < section_size;
  }
  return 0;
}

int instruction_render_operand_target(const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata,
    uint8_t operand_index, uint32_t offset, uint32_t section_size, uint32_t *out_target) {
  const M68kOperandIR *operand;
  uint8_t formula;
  uint8_t pc_bias;
  if (instruction == NULL || metadata == NULL || out_target == NULL || operand_index >= instruction->operand_count) return 0;
  operand = &instruction->operands[operand_index];
  formula = metadata->operand_ea_address_formulas[operand_index];
  if (formula == M68K_SIM_EA_FORMULA_PC_PLUS_DISP &&
      metadata->operand_ea_displacement_sources[operand_index] == M68K_SIM_EA_DISP_OPERAND_VALUE &&
      metadata->operand_ea_uses_displacement[operand_index] &&
      !metadata->operand_ea_uses_index[operand_index]) {
    pc_bias = metadata->operand_ea_pc_base_bias_bytes[operand_index] != 0U
      ? metadata->operand_ea_pc_base_bias_bytes[operand_index]
      : 2U;
    *out_target = (uint32_t)((int32_t)offset + (int32_t)pc_bias + (int32_t)operand->value.value);
    return *out_target < section_size;
  }
  if (formula == M68K_SIM_EA_FORMULA_DECODED_EA &&
      metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_COMPUTE_ADDRESS &&
      metadata->operand_result_kinds[operand_index] == M68K_SIM_RESULT_ADDRESS) {
    pc_bias = metadata->operand_ea_pc_base_bias_bytes[operand_index] != 0U
      ? metadata->operand_ea_pc_base_bias_bytes[operand_index]
      : 2U;
    return m68k_instruction_decoded_ea_target(operand,
      instruction_effective_ea_shape(metadata, instruction, operand_index),
      offset + (uint32_t)pc_bias, section_size, 1, out_target);
  }
  if (instruction_metadata_operand_target(instruction, metadata, operand_index, offset, section_size, out_target)) return 1;
  return 0;
}

static int instruction_operand_is_render_pc_relative(const M68kInstructionIR *instruction,
    const M68kSimFormMetadata *metadata, uint8_t operand_index) {
  uint8_t formula;
  if (instruction == NULL || metadata == NULL || operand_index >= instruction->operand_count) return 0;
  formula = metadata->operand_ea_address_formulas[operand_index];
  if (formula == M68K_SIM_EA_FORMULA_PC_PLUS_DISP || formula == M68K_SIM_EA_FORMULA_PC_PLUS_DISP_PLUS_INDEX)
    return 1;
  if (formula != M68K_SIM_EA_FORMULA_DECODED_EA) return 0;
  return m68k_instruction_decoded_ea_target_kind(&instruction->operands[operand_index],
    instruction_effective_ea_shape(metadata, instruction, operand_index), 1) == 2U;
}

static int instruction_pc_relative_ea_target(const M68kInstructionIR *instruction, const M68kSimFormMetadata *metadata,
    uint8_t operand_index, uint32_t offset, uint32_t section_size, uint32_t *out_target) {
  const M68kOperandIR *operand;
  uint8_t pc_bias;
  if (instruction == NULL || metadata == NULL || out_target == NULL || operand_index >= instruction->operand_count) return 0;
  operand = &instruction->operands[operand_index];
  if (operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_mode != 7U ||
      (operand->value.ea_reg != 2U && operand->value.ea_reg != 3U)) {
    return 0;
  }
  pc_bias = metadata->operand_ea_pc_base_bias_bytes[operand_index] != 0U
    ? metadata->operand_ea_pc_base_bias_bytes[operand_index]
    : 2U;
  return m68k_instruction_decoded_ea_target(operand,
    m68k_instruction_operand_decoded_ea_shape(operand), offset + (uint32_t)pc_bias, section_size, 1, out_target);
}

static int instruction_transfer_target(const M68kInstructionIR *instruction, const uint8_t *data, size_t size,
    uint32_t offset, uint32_t section_size, uint32_t *out_target) {
  const M68kSimFormMetadata *metadata;
  uint8_t operand_index;
  if (instruction == NULL || out_target == NULL) return 0;
  if (instruction_branch_target_from_bytes(instruction, data, size, offset, out_target)) {
    if (*out_target < section_size) return 1;
    return 0;
  }
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL || metadata->target_operand_index >= instruction->operand_count) return 0;
  operand_index = metadata->target_operand_index;
  return instruction_metadata_operand_target(instruction, metadata, operand_index, offset, section_size, out_target);
}

static int instruction_is_unconditional_transfer(const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata = instruction_sim_metadata(instruction);
  if (instruction == NULL) return 0;
  if (metadata == NULL) return 0;
  return (metadata->flow_kind == M68K_SIM_FLOW_JUMP) ||
    (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional == 0U);
}

int instruction_is_call_transfer(const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata = instruction_sim_metadata(instruction);
  if (instruction == NULL) return 0;
  if (metadata == NULL) return 0;
  return metadata->flow_kind == M68K_SIM_FLOW_CALL;
}

int instruction_stops_fallthrough(const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata = instruction_sim_metadata(instruction);
  if (instruction == NULL) return 0;
  if (metadata == NULL) return 0;
  return metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
    metadata->flow_kind == M68K_SIM_FLOW_RETURN ||
    (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional == 0U);
}

static int is_conditional_transfer(const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata = instruction_sim_metadata(instruction);
  if (instruction == NULL) return 0;
  if (metadata == NULL) return 0;
  return metadata->flow_conditional != 0U &&
    (metadata->flow_kind == M68K_SIM_FLOW_BRANCH || metadata->flow_kind == M68K_SIM_FLOW_JUMP);
}

int instruction_target_operand_local(const M68kInstructionIR *instruction, const M68kOperandIR **out_operand) {
  const M68kSimFormMetadata *metadata = instruction_sim_metadata(instruction);
  uint8_t operand_index;
  if (out_operand != NULL) *out_operand = NULL;
  if (instruction == NULL || metadata == NULL) return 0;
  operand_index = metadata->target_operand_index;
  if (operand_index == 0xFFU || operand_index >= instruction->operand_count) return 0;
  if (out_operand != NULL) *out_operand = &instruction->operands[operand_index];
  return 1;
}

void platform_resolved_indirect_info_init(PlatformResolvedIndirectInfo *info) {
  if (info == NULL) return;
  memset(info, 0, sizeof(*info));
  info->note_disp = INT16_MIN;
  info->note_field_disp = INT16_MIN;
}

PlatformResolvedIndirectInfo platform_resolved_indirect_info_none(void) {
  PlatformResolvedIndirectInfo info;
  platform_resolved_indirect_info_init(&info);
  return info;
}

int operand_is_absolute_short_value(const M68kOperandIR *operand, uint16_t value) {
  if (operand == NULL) return 0;
  if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) return 0;
  return operand->value.ea_mode == 7U && operand->value.ea_reg == 0U &&
    (operand->value.value & 0xFFFFU) == value;
}

int operand_is_app_base_disp_ea(const M68kOperandIR *operand, uint8_t reg, int16_t *out_displacement) {
  if (out_displacement != NULL) *out_displacement = 0;
  if (operand == NULL) return 0;
  if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) return 0;
  if (operand->value.ea_mode != 5U || operand->value.ea_reg != reg) return 0;
  if (out_displacement != NULL) *out_displacement = (int16_t)(operand->value.value & 0xFFFFU);
  return 1;
}

int operand_is_data_reg_direct(const M68kOperandIR *operand, uint8_t reg) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_DN) return operand->value.reg == reg;
  return (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
    operand->value.ea_mode == 0U && operand->value.ea_reg == reg;
}

static int operand_is_address_reg_direct(const M68kOperandIR *operand, uint8_t reg) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_AN) return operand->value.reg == reg;
  return (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
    operand->value.ea_mode == 1U && operand->value.ea_reg == reg;
}

static int instruction_has_mnemonic_id_local(const M68kInstructionIR *instruction, uint8_t mnemonic_id) {
  return instruction != NULL && instruction->mnemonic_id == mnemonic_id;
}

static int instruction_is_compare_or_test_like_local(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_CMP:
  case M68K_ASM_MNEMONIC_CMPI:
  case M68K_ASM_MNEMONIC_CMPA:
  case M68K_ASM_MNEMONIC_CMPM:
  case M68K_ASM_MNEMONIC_TST:
  case M68K_ASM_MNEMONIC_BTST:
  case M68K_ASM_MNEMONIC_BCHG:
  case M68K_ASM_MNEMONIC_BCLR:
  case M68K_ASM_MNEMONIC_BSET:
    return 1;
  default:
    return 0;
  }
}

static int instruction_is_compare_like_address_write_local(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_CMP:
  case M68K_ASM_MNEMONIC_CMPI:
  case M68K_ASM_MNEMONIC_CMPA:
  case M68K_ASM_MNEMONIC_CMPM:
  case M68K_ASM_MNEMONIC_TST:
    return 1;
  default:
    return 0;
  }
}

int instruction_is_address_move(const M68kInstructionIR *instruction, uint8_t *out_dest_reg,
    const M68kOperandIR **out_source) {
  uint8_t dest_reg;
  uint8_t mnemonic_id;
  if (out_dest_reg != NULL) *out_dest_reg = 0U;
  if (out_source != NULL) *out_source = NULL;
  if (instruction == NULL || instruction->operand_count != 2U) return 0;
  mnemonic_id = instruction->mnemonic_id;
  if (mnemonic_id != M68K_ASM_MNEMONIC_MOVEA && mnemonic_id != M68K_ASM_MNEMONIC_MOVE) return 0;
  for (dest_reg = 0U; dest_reg < 8U; ++dest_reg) {
    if (operand_is_address_reg_direct(&instruction->operands[1], dest_reg)) {
      if (out_dest_reg != NULL) *out_dest_reg = dest_reg;
      if (out_source != NULL) *out_source = &instruction->operands[0];
      return 1;
    }
  }
  return 0;
}

int instruction_is_data_move(const M68kInstructionIR *instruction, uint8_t *out_dest_reg,
    const M68kOperandIR **out_source) {
  uint8_t dest_reg;
  if (out_dest_reg != NULL) *out_dest_reg = 0U;
  if (out_source != NULL) *out_source = NULL;
  if (instruction == NULL || instruction->operand_count != 2U) return 0;
  if (!instruction_has_mnemonic_id_local(instruction, M68K_ASM_MNEMONIC_MOVE)) return 0;
  for (dest_reg = 0U; dest_reg < 8U; ++dest_reg) {
    if (operand_is_data_reg_direct(&instruction->operands[1], dest_reg)) {
      if (out_dest_reg != NULL) *out_dest_reg = dest_reg;
      if (out_source != NULL) *out_source = &instruction->operands[0];
      return 1;
    }
  }
  return 0;
}

int instruction_is_register_to_app_slot_store(const M68kInstructionIR *instruction, uint8_t *out_source_kind,
    uint8_t *out_source_reg, int16_t *out_displacement) {
  const M68kOperandIR *src;
  const M68kOperandIR *dst;
  uint8_t mnemonic_id;
  if (out_source_kind != NULL) *out_source_kind = 0U;
  if (out_source_reg != NULL) *out_source_reg = 0U;
  if (out_displacement != NULL) *out_displacement = 0;
  if (instruction == NULL || instruction->operand_count != 2U) return 0;
  mnemonic_id = instruction->mnemonic_id;
  if (mnemonic_id != M68K_ASM_MNEMONIC_MOVE && mnemonic_id != M68K_ASM_MNEMONIC_MOVEA) return 0;
  src = &instruction->operands[0];
  dst = &instruction->operands[1];
  if (!operand_is_app_base_disp_ea(dst, 6U, out_displacement)) return 0;
  if (operand_is_data_reg_direct(src, src->kind == M68K_ASM_OPERAND_DN ? src->value.reg : src->value.ea_reg)) {
    if (out_source_kind != NULL) *out_source_kind = 1U;
    if (out_source_reg != NULL) *out_source_reg =
      (src->kind == M68K_ASM_OPERAND_DN) ? src->value.reg : src->value.ea_reg;
    return 1;
  }
  if (operand_is_address_reg_direct(src, src->kind == M68K_ASM_OPERAND_AN ? src->value.reg : src->value.ea_reg)) {
    if (out_source_kind != NULL) *out_source_kind = 2U;
    if (out_source_reg != NULL) *out_source_reg =
      (src->kind == M68K_ASM_OPERAND_AN) ? src->value.reg : src->value.ea_reg;
    return 1;
  }
  return 0;
}

int instruction_is_app_slot_load(const M68kInstructionIR *instruction, uint8_t *out_dest_kind,
    uint8_t *out_dest_reg, int16_t *out_displacement) {
  const M68kOperandIR *src;
  const M68kOperandIR *dst;
  uint8_t mnemonic_id;
  if (out_dest_kind != NULL) *out_dest_kind = 0U;
  if (out_dest_reg != NULL) *out_dest_reg = 0U;
  if (out_displacement != NULL) *out_displacement = 0;
  if (instruction == NULL || instruction->operand_count != 2U) return 0;
  mnemonic_id = instruction->mnemonic_id;
  if (mnemonic_id != M68K_ASM_MNEMONIC_MOVE && mnemonic_id != M68K_ASM_MNEMONIC_MOVEA) return 0;
  src = &instruction->operands[0];
  dst = &instruction->operands[1];
  if (!operand_is_app_base_disp_ea(src, 6U, out_displacement)) return 0;
  if (operand_is_data_reg_direct(dst, dst->kind == M68K_ASM_OPERAND_DN ? dst->value.reg : dst->value.ea_reg)) {
    if (out_dest_kind != NULL) *out_dest_kind = 1U;
    if (out_dest_reg != NULL) *out_dest_reg =
      (dst->kind == M68K_ASM_OPERAND_DN) ? dst->value.reg : dst->value.ea_reg;
    return 1;
  }
  if (operand_is_address_reg_direct(dst, dst->kind == M68K_ASM_OPERAND_AN ? dst->value.reg : dst->value.ea_reg)) {
    if (out_dest_kind != NULL) *out_dest_kind = 2U;
    if (out_dest_reg != NULL) *out_dest_reg =
      (dst->kind == M68K_ASM_OPERAND_AN) ? dst->value.reg : dst->value.ea_reg;
    return 1;
  }
  return 0;
}

PlatformRegisterMatch instruction_push_address_reg_to_stack(const M68kInstructionIR *instruction) {
  PlatformRegisterMatch result = {0};
  uint8_t is_address = 0U;
  uint8_t reg = 0U;
  if (instruction == NULL || instruction->operand_count != 2U) return result;
  if (!instruction_has_mnemonic_id_local(instruction, M68K_ASM_MNEMONIC_MOVE)) return result;
  if (!sim_operand_direct_register_local(&instruction->operands[0], &is_address, &reg) || is_address == 0U)
    return result;
  if (instruction->operands[1].kind == M68K_ASM_OPERAND_PREDEC) {
    if (instruction->operands[1].value.ea_reg != 7U) return result;
  } else if ((instruction->operands[1].kind == M68K_ASM_OPERAND_EA ||
      instruction->operands[1].kind == M68K_ASM_OPERAND_BF_EA) &&
      instruction->operands[1].value.ea_mode == 4U) {
    if (instruction->operands[1].value.ea_reg != 7U) return result;
  } else return result;
  result.ok = 1U;
  result.reg = reg;
  return result;
}

PlatformRegisterMatch instruction_pop_address_reg_from_stack(const M68kInstructionIR *instruction) {
  PlatformRegisterMatch result = {0};
  const M68kOperandIR *source;
  uint8_t dest_reg;
  if (instruction == NULL || instruction->operand_count != 2U) return result;
  if (!instruction_is_address_move(instruction, &dest_reg, &source) || source == NULL) return result;
  if (source->kind == M68K_ASM_OPERAND_POSTINC && source->value.ea_reg == 7U) {
    result.ok = 1U;
    result.reg = dest_reg;
    return result;
  }
  if ((source->kind == M68K_ASM_OPERAND_EA || source->kind == M68K_ASM_OPERAND_BF_EA) &&
      source->value.ea_mode == 3U && source->value.ea_reg == 7U) {
    result.ok = 1U;
    result.reg = dest_reg;
    return result;
  }
  return result;
}

PlatformAddressExgInfo instruction_address_exg(const M68kInstructionIR *instruction) {
  PlatformAddressExgInfo result = {0};
  if (instruction == NULL || instruction->operand_count != 2U) return result;
  if (!instruction_has_mnemonic_id_local(instruction, M68K_ASM_MNEMONIC_EXG)) return result;
  if (instruction->operands[0].kind != M68K_ASM_OPERAND_AN || instruction->operands[1].kind != M68K_ASM_OPERAND_AN)
    return result;
  result.ok = 1U;
  result.left_reg = instruction->operands[0].value.reg;
  result.right_reg = instruction->operands[1].value.reg;
  return result;
}

const M68kRecoveredPlatformCallIR *find_recovered_platform_call(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint8_t kind) {
  size_t index;
  if (section_analysis == NULL) return NULL;
  for (index = 0; index < section_analysis->recovered_platform_call_count; ++index) {
    const M68kRecoveredPlatformCallIR *call = &section_analysis->recovered_platform_calls[index];
    if (call->offset == offset && call->kind == kind) return call;
  }
  return NULL;
}

const M68kRecoveredPlatformCallIR *find_any_recovered_platform_call(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset) {
  size_t index;
  if (section_analysis == NULL) return NULL;
  for (index = 0; index < section_analysis->recovered_platform_call_count; ++index) {
    const M68kRecoveredPlatformCallIR *call = &section_analysis->recovered_platform_calls[index];
    if (call->offset == offset) return call;
  }
  return NULL;
}

const M68kRecoveredPlatformEffectIR *find_recovered_platform_effect(const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint8_t kind) {
  size_t index;
  if (section_analysis == NULL) return NULL;
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    if (effect->offset == offset && effect->kind == kind) return effect;
  }
  return NULL;
}

static int format_platform_resolved_indirect_note(const PlatformResolvedIndirectInfo *info, char *buf, size_t buf_size) {
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (info == NULL) return 0;
  switch (info->note_kind) {
  case M68K_PLATFORM_CALL_NOTE_INDEXED_VECTOR:
    if (info->note_base_name[0] == '\0') return 0;
    snprintf(buf, buf_size, "KNOWN: %s indexed vector via d%u", info->note_base_name, (unsigned)info->note_reg);
    return 1;
  case M68K_PLATFORM_CALL_NOTE_CALLBACK_FIELD:
    if (info->note_field_disp == INT16_MIN) return 0;
    if (info->note_symbol_name[0] != '\0' && info->note_base_name[0] != '\0') {
      snprintf(buf, buf_size, "KNOWN: callback field %s from %s", info->note_symbol_name, info->note_base_name);
      return 1;
    }
    if (info->note_symbol_name[0] != '\0' && info->note_disp != INT16_MIN) {
      snprintf(buf, buf_size, "KNOWN: callback field %s from $%04X(a6)", info->note_symbol_name,
        (unsigned)(uint16_t)info->note_disp);
      return 1;
    }
    if (info->note_base_name[0] != '\0') {
      snprintf(buf, buf_size, "KNOWN: callback field %+d from %s", (int)info->note_field_disp, info->note_base_name);
      return 1;
    }
    if (info->note_disp == INT16_MIN) return 0;
    snprintf(buf, buf_size, "KNOWN: callback field %+d from $%04X(a6)", (int)info->note_field_disp,
      (unsigned)(uint16_t)info->note_disp);
    return 1;
  case M68K_PLATFORM_CALL_NOTE_LOCAL_WRAPPER_SYMBOL:
    if (info->note_base_name[0] == '\0' || info->note_symbol_name[0] == '\0') return 0;
    snprintf(buf, buf_size, "KNOWN: %s %s fallback via local wrapper", info->note_base_name, info->note_symbol_name);
    return 1;
  case M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL:
    if (info->note_symbol_name[0] == '\0') return 0;
    if (info->note_stack_cleanup_known != 0U) {
      const char *ret_text = info->note_return_kind == ATARI_ST_OS_RETURN_VOID ? "void"
        : (info->note_return_kind == ATARI_ST_OS_RETURN_WORD ? "d0.w" : "d0.l");
      snprintf(buf, buf_size, "KNOWN: direct OS call %s pop %u return %s", info->note_symbol_name,
          (unsigned)info->note_stack_cleanup_bytes, ret_text);
    } else {
      snprintf(buf, buf_size, "KNOWN: direct OS call %s", info->note_symbol_name);
    }
    return 1;
  case M68K_PLATFORM_CALL_NOTE_STACK_CLEANUP:
    if (info->note_symbol_name[0] == '\0') return 0;
    if (info->note_stack_cleanup_known != 0U) {
      snprintf(buf, buf_size, "KNOWN: stack cleanup for %s pop %u", info->note_symbol_name,
          (unsigned)info->note_stack_cleanup_bytes);
    } else {
      snprintf(buf, buf_size, "KNOWN: stack cleanup for %s", info->note_symbol_name);
    }
    return 1;
  default:
    return 0;
  }
}

void load_recovered_platform_call_info(const M68kRecoveredPlatformCallIR *recovered,
    PlatformResolvedIndirectInfo *out_info) {
  const char *symbol_name;
  const char *note_base_name;
  const char *note_symbol_name;
  if (recovered == NULL || out_info == NULL) return;
  platform_resolved_indirect_info_init(out_info);
  symbol_name = m68k_platform_name_ref_name_or_text(&recovered->symbol_ref, recovered->symbol_name);
  note_base_name = m68k_platform_name_ref_name_or_text(&recovered->note_base_ref, recovered->note_base_name);
  note_symbol_name = m68k_platform_name_ref_name_or_text(&recovered->note_symbol_ref, recovered->note_symbol_name);
  out_info->kind = recovered->kind;
  out_info->has_symbol_name = symbol_name != NULL ? 1U : 0U;
  out_info->note_kind = recovered->note_kind;
  out_info->note_reg = recovered->note_reg;
  out_info->note_stack_cleanup_known = recovered->note_stack_cleanup_known;
  out_info->note_return_kind = recovered->note_return_kind;
  out_info->note_disp = recovered->note_disp;
  out_info->note_field_disp = recovered->note_field_disp;
  out_info->note_stack_cleanup_bytes = recovered->note_stack_cleanup_bytes;
  if (symbol_name != NULL)
    snprintf(out_info->symbol_name, sizeof(out_info->symbol_name), "%s", symbol_name);
  if (note_base_name != NULL)
    snprintf(out_info->note_base_name, sizeof(out_info->note_base_name), "%s", note_base_name);
  if (note_symbol_name != NULL)
    snprintf(out_info->note_symbol_name, sizeof(out_info->note_symbol_name), "%s", note_symbol_name);
  if (recovered->available_since != NULL)
    snprintf(out_info->available_since, sizeof(out_info->available_since), "%s", recovered->available_since);
  if (recovered->fd_version != NULL)
    snprintf(out_info->fd_version, sizeof(out_info->fd_version), "%s", recovered->fd_version);
}

uint32_t resolve_analysis_trace_start(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  size_t block_index;
  uint32_t start;
  uint32_t candidate_start;
  if (section_analysis == NULL) return UINT32_MAX;
  block_index = section_analysis_find_block_index_containing(section_analysis, offset);
  if (block_index != SIZE_MAX && block_index < section_analysis->block_count) {
    start = section_analysis->blocks[block_index].start_offset;
    if (ctx != NULL && start < offset) {
      SectionDecodeResult decode;
      if (section_analysis_context_probe_decode(ctx, start, &decode) &&
          instruction_pop_address_reg_from_stack(&decode.instruction).ok) {
        uint32_t low = start > 32U ? (start - 32U) : 0U;
        for (candidate_start = low; candidate_start < start; ++candidate_start) {
          uint32_t cursor = candidate_start;
          while (cursor < start) {
            SectionDecodeResult prior_decode;
            if (!section_analysis_context_probe_decode(ctx, cursor, &prior_decode)) break;
            if (prior_decode.instruction.byte_count == 0U) break;
            if (cursor + (uint32_t)prior_decode.instruction.byte_count > start) break;
            cursor += (uint32_t)prior_decode.instruction.byte_count;
          }
          if (cursor == start) return candidate_start;
        }
      }
    }
    if (start < offset) return start;
  }
  start = find_enclosing_code_start(section_analysis, offset);
  if (start != UINT32_MAX && start < offset) return start;
  candidate_start = offset;
  while (candidate_start-- > ((offset > 32U) ? (offset - 32U) : 0U)) {
    uint32_t cursor = candidate_start;
    while (cursor < offset) {
      SectionDecodeResult decode;
      if (ctx == NULL || !section_analysis_context_probe_decode(ctx, cursor, &decode)) break;
      if (decode.instruction.byte_count == 0U) break;
      if (cursor + (uint32_t)decode.instruction.byte_count > offset) break;
      cursor += (uint32_t)decode.instruction.byte_count;
    }
    if (cursor == offset) return candidate_start;
  }
  return UINT32_MAX;
}

static int operand_is_direct_control_target(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  if (operand->kind != M68K_ASM_OPERAND_EA) return 0;
  switch (operand->value.ea_mode) {
    case 7U:
      return operand->value.ea_reg == 0U || operand->value.ea_reg == 1U || operand->value.ea_reg == 2U;
    default:
      return 0;
  }
}

static int instruction_control_transfer_target( const M68kInstructionIR *instruction, const uint8_t *data, size_t size,
    uint32_t offset, uint32_t section_size, uint32_t *out_target) {
  const M68kSimFormMetadata *metadata;
  uint8_t operand_index;
  if (instruction == NULL) return 0;
  if (!instruction_is_call_transfer(instruction) && !instruction_is_unconditional_transfer(instruction) &&
      !is_conditional_transfer(instruction)) {
    return 0;
  }
  if (instruction_branch_target_from_bytes(instruction, data, size, offset, out_target)) {
    if (*out_target < section_size) return 1;
    return 0;
  }
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL || metadata->target_operand_index >= instruction->operand_count) return 0;
  operand_index = metadata->target_operand_index;
  if (!operand_is_direct_control_target(&instruction->operands[operand_index])) return 0;
  return instruction_metadata_operand_target(instruction, metadata, operand_index, offset, section_size, out_target);
}

static int prune_entry_skip_range(const SectionAnalysisContext *ctx, M68kAnalysisFindings *findings,
    M68kSectionAnalysisIR *section_analysis, SectionDiscoveryMap *map) {
  M68kInstructionIR instruction;
  uint32_t target;
  uint32_t start_offset;
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  if (section == NULL || section_analysis == NULL || map == NULL || section->data_size < 2U) return 0;
  {
    SectionDecodeResult decode;
    if (!section_analysis_context_decode(ctx, 0U, findings, &decode)) return 0;
    instruction = decode.instruction;
  }
  if (!instruction_is_unconditional_transfer(&instruction)) return 0;
  if (!instruction_transfer_target(&instruction, section->data, section->data_size, 0U, section->data_size,
    &target)) return 0;
  start_offset = (uint32_t)instruction.byte_count;
  if (target <= start_offset) return 0;
  clear_code_range(map, start_offset, target);
  analysis_remove_label_range(section_analysis, start_offset, target);
  return 0;
}

static int enrich_analysis_labels(const SectionAnalysisContext *ctx, M68kAnalysisFindings *findings,
    SectionDiscoveryMap *map, M68kSectionAnalysisIR *section_analysis) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  size_t scan_offset;
  if (section == NULL || map == NULL || section_analysis == NULL || map->is_code_start == NULL || map->is_code_byte == NULL)
    return 0;
  for (scan_offset = 0; scan_offset < section->data_size; ++scan_offset) {
    uint32_t cursor;
    if (map->is_code_byte[scan_offset] == 0U) continue;
    if (scan_offset != 0U && map->is_code_byte[scan_offset - 1U] != 0U && map->is_code_start[scan_offset] == 0U)
      continue;
    cursor = (uint32_t)scan_offset;
    while (cursor < section->data_size && map->is_code_byte[cursor] != 0U) {
      M68kInstructionIR instruction;
      SectionDecodeResult decode;
      const M68kSimFormMetadata *metadata;
      uint32_t target;
      uint32_t next_offset;
      size_t operand_index;
      if (!section_analysis_context_decode(ctx, cursor, findings, &decode))
        break;
      instruction = decode.instruction;
      next_offset = cursor + (uint32_t)instruction.byte_count;
      metadata = instruction_sim_metadata(&instruction);
      if (instruction_transfer_target(&instruction, section->data + cursor, section->data_size - cursor,
          cursor, section->data_size, &target)) {
        map->is_code_start[target] = 1U;
        if (m68k_ir_section_analysis_add_label(section_analysis, target) != 0) return -1;
      }
      if (metadata != NULL) {
        for (operand_index = 0; operand_index < instruction.operand_count; ++operand_index) {
          if (instruction_metadata_operand_target(&instruction, metadata, (uint8_t)operand_index, cursor,
              section->data_size, &target) &&
              m68k_ir_section_analysis_add_label(section_analysis, target) != 0) {
            return -1;
          }
        }
      }
      cursor = next_offset;
    }
  }
  return 0;
}

static int prune_disconnected_blocks(M68kSectionAnalysisIR *section_analysis, SectionDiscoveryMap *discovery,
    Arena *scratch_arena) {
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
  if (section_analysis == NULL || discovery == NULL || scratch_arena == NULL) return -1;
  if (section_analysis->block_count == 0U) return 0;
  reachable_blocks = (uint8_t *)arena_calloc(scratch_arena, section_analysis->block_count, 1U);
  reachable_queue = (size_t *)arena_alloc(scratch_arena, section_analysis->block_count * sizeof(*reachable_queue));
  block_remap = (size_t *)arena_alloc(scratch_arena, section_analysis->block_count * sizeof(*block_remap));
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
  new_blocks = (M68kCfgBlockIR *)arena_calloc(section_analysis->arena, new_block_count != 0U ? new_block_count : 1U,
    sizeof(*new_blocks));
  new_edges = (M68kCfgEdgeIR *)arena_calloc(section_analysis->arena,
    section_analysis->edge_count != 0U ? section_analysis->edge_count : 1U, sizeof(*new_edges));
  new_violations = (M68kViolationIR *)arena_calloc(section_analysis->arena, section_analysis->violation_count != 0U
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
  }
  section_analysis->blocks = new_blocks;
  section_analysis->block_count = new_block_count;
  section_analysis->block_capacity = new_block_count;
  section_analysis->edges = new_edges;
  section_analysis->edge_count = new_edge_count;
  section_analysis->edge_capacity = new_edge_count;
  section_analysis->violations = new_violations;
  section_analysis->violation_count = new_violation_count;
  section_analysis->violation_capacity = new_violation_count;
  return 0;

fail:
  return -1;
}

static int recompute_section_findings(const SectionAnalysisContext *ctx, const M68kSectionAnalysisIR *section_analysis,
    M68kAnalysisFindings *out_findings) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
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
      SectionDecodeResult decode;
      if (!section_analysis_context_decode(ctx, offset, &findings, &decode) ||
          offset + decode.instruction.byte_count > block->end_offset) {
        break;
      }
      instruction = decode.instruction;
      offset += (uint32_t)instruction.byte_count;
    }
  }
  *out_findings = findings;
  return 0;
}

static int rebuild_code_map_from_blocks(const SectionAnalysisContext *ctx, M68kSectionAnalysisIR *section_analysis) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
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
      size_t byte_index;
      SectionDecodeResult decode;
      if (!section_analysis_context_decode(ctx, offset, NULL, &decode) ||
          offset + decode.instruction.byte_count > block->end_offset) {
        break;
      }
      instruction = decode.instruction;
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
    if (violation.kind == kind) continue;
    section_analysis->violations[write_index++] = violation;
  }
  section_analysis->violation_count = write_index;
}

static int rebuild_cpu_violations(const SectionAnalysisContext *ctx, M68kSectionAnalysisIR *section_analysis) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  size_t block_index;
  if (section == NULL || section_analysis == NULL || section_analysis->certain_code_start == NULL)
    return 0;
  remove_section_violations_by_kind(section_analysis, M68K_VIOLATION_CPU_POLICY);
  for (block_index = 0; block_index < section_analysis->block_count; ++block_index) {
    const M68kCfgBlockIR *block = &section_analysis->blocks[block_index];
    uint32_t offset = block->start_offset;
    while (offset < block->end_offset && offset < section->data_size) {
      M68kInstructionIR instruction;
      SectionDecodeResult decode;
      if (!section_analysis_context_decode(ctx, offset, NULL, &decode) ||
          offset + decode.instruction.byte_count > block->end_offset) {
        break;
      }
      instruction = decode.instruction;
      if (add_cpu_violation(section_analysis, offset, &instruction, ctx->analysis_policy) != 0)
        return -1;
      offset += (uint32_t)instruction.byte_count;
    }
  }
  return 0;
}

static int rebuild_decode_fail_violations(const SectionAnalysisContext *ctx, M68kSectionAnalysisIR *section_analysis) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  size_t block_index;
  if (section == NULL || section_analysis == NULL) return -1;
  remove_section_violations_by_kind(section_analysis, M68K_VIOLATION_DECODE_FAILED_REACHABLE);
  for (block_index = 0; block_index < section_analysis->block_count; ++block_index) {
    const M68kCfgBlockIR *block = &section_analysis->blocks[block_index];
    uint32_t offset = block->start_offset;
    while (offset < block->end_offset && offset < section->data_size) {
      M68kInstructionIR instruction;
      SectionDecodeResult decode;
      if (!section_analysis_context_decode(ctx, offset, NULL, &decode) ||
          offset + decode.instruction.byte_count > block->end_offset) {
        if (m68k_ir_section_analysis_add_violation( section_analysis, offset, M68K_VIOLATION_DECODE_FAILED_REACHABLE,
            "decode failed in reachable code; region emitted as data") != 0) {
          return -1;
        }
        break;
      }
      instruction = decode.instruction;
      offset += (uint32_t)instruction.byte_count;
    }
  }
  return 0;
}

int finalize_section_analysis(const M68kSection *section, const M68kAnalysisPolicy *analysis_policy,
    M68kSectionAnalysisIR *section_analysis, M68kAnalysisFindings *out_findings) {
  SectionAnalysisContext analysis_ctx = {0};
  if (section == NULL || section_analysis == NULL || out_findings == NULL) return -1;
  m68k_analysis_findings_init(out_findings);
  if (section_analysis_context_init(&analysis_ctx, NULL, section, analysis_policy, section_analysis->arena) != 0) return -1;
  if (rebuild_cpu_violations(&analysis_ctx, section_analysis) != 0) return -1;
  if (rebuild_decode_fail_violations(&analysis_ctx, section_analysis) != 0) return -1;
  return recompute_section_findings(&analysis_ctx, section_analysis, out_findings);
}

static int promote_direct_control_targets(const SectionAnalysisContext *ctx, M68kAnalysisFindings *findings,
    SectionDiscoveryMap *discovery) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  int changed;
  if (section == NULL || ctx->analysis_policy == NULL || discovery == NULL || discovery->is_code_start == NULL)
    return 0;
  do {
    size_t offset;
    changed = 0;
    for (offset = 0; offset < section->data_size; ++offset) {
      SectionDecodeResult decode;
      uint32_t target;
      if (discovery->is_code_start[offset] == 0U) continue;
      if (!section_analysis_context_decode(ctx, (uint32_t)offset, findings, &decode))
        continue;
      if (decode.has_explicit_target &&
          (target = decode.explicit_target, 1) &&
          target < section->data_size && discovery->is_code_start[target] == 0U &&
          offset_decodes_as_instruction(ctx, target)) {
        discovery->is_code_start[target] = 1U;
        changed = 1;
      }
      if (decode.instruction.byte_count > 1U) offset += decode.instruction.byte_count - 1U;
    }
  } while (changed != 0);
  return 0;
}

static int rebuild_unresolved_indirect_violations(const SectionAnalysisContext *ctx, M68kSectionAnalysisIR *section_analysis) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  size_t block_index;
  if (section == NULL || section_analysis == NULL) return -1;
  remove_section_violations_by_kind(section_analysis, M68K_VIOLATION_UNRESOLVED_INDIRECT);
  for (block_index = 0; block_index < section_analysis->block_count; ++block_index) {
    const M68kCfgBlockIR *block = &section_analysis->blocks[block_index];
    uint32_t offset = block->start_offset;
    while (offset < block->end_offset && offset < section->data_size) {
      SectionDecodeResult decode;
      M68kInstructionIR instruction;
      uint32_t direct_target = 0U;
      int has_control_edge = 0;
      size_t edge_index;
      if (!section_analysis_context_decode(ctx, offset, NULL, &decode) ||
          offset + decode.instruction.byte_count > block->end_offset)
        break;
      instruction = decode.instruction;
      if ((instruction_is_call_transfer(&instruction) || instruction_is_unconditional_transfer(&instruction)) &&
          !(decode.has_explicit_target && (direct_target = decode.explicit_target, 1))) {
        if (section_analysis_has_string_dispatch_site(section_analysis, offset)) {
          offset += (uint32_t)instruction.byte_count;
          continue;
        }
        if (platform_resolve_indirect_control(ctx, section_analysis, offset, &instruction).kind !=
            PLATFORM_RESOLVED_INDIRECT_NONE) {
          offset += (uint32_t)instruction.byte_count;
          continue;
        }
        for (edge_index = block->edge_start; edge_index < block->edge_start + block->edge_count; ++edge_index) {
          const M68kCfgEdgeIR *edge = &section_analysis->edges[edge_index];
          if (edge->source_offset != offset) continue;
          if (edge->kind == M68K_CFG_EDGE_CALL || edge->kind == M68K_CFG_EDGE_JUMP || edge->kind == M68K_CFG_EDGE_BRANCH) {
            has_control_edge = 1;
            break;
          }
        }
        if (!has_control_edge) {
          const char *message = instruction_is_call_transfer(&instruction)
            ? "CANDIDATE: indirect_call index unresolved"
            : "CANDIDATE: indirect_jump index unresolved";
          if (m68k_ir_section_analysis_add_violation(section_analysis, offset, M68K_VIOLATION_UNRESOLVED_INDIRECT,
                message) != 0) {
            return -1;
          }
        }
      }
      offset += (uint32_t)instruction.byte_count;
    }
  }
  return 0;
}

static int build_generated_label_kinds(const SectionAnalysisContext *ctx, M68kAnalysisFindings *findings,
    const M68kSectionAnalysisIR *section_analysis, GeneratedLabelKind *label_kinds, uint8_t *label_flags) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  size_t offset;
  if (section == NULL || section_analysis == NULL || label_kinds == NULL ||
      section_analysis->certain_code_start == NULL)
    return 0;
  for (offset = 0; offset < section->data_size; ++offset) {
    M68kInstructionIR instruction;
    SectionDecodeResult decode;
    const M68kSimFormMetadata *metadata;
    size_t operand_index;
    if (section_analysis->certain_code_size <= offset || section_analysis->certain_code_start[offset] == 0U) continue;
    if (!section_analysis_context_decode(ctx, (uint32_t)offset, findings, &decode))
      continue;
    instruction = decode.instruction;
    metadata = instruction_sim_metadata(&instruction);
    for (operand_index = 0; operand_index < instruction.operand_count; ++operand_index) {
      const M68kOperandIR *operand = &instruction.operands[operand_index];
      uint32_t target;
      GeneratedLabelKind kind;
      if (operand->kind == M68K_ASM_OPERAND_LABEL) {
        if (!instruction_transfer_target(&instruction, section->data + offset, section->data_size - offset,
              (uint32_t)offset, (uint32_t)section->data_size, &target) &&
            !instruction_branch_target(&instruction, (uint32_t)offset, &target)) {
          continue;
        }
        if (target < section->data_size) {
          kind = instruction_is_call_transfer(&instruction) ? GENERATED_LABEL_SUB : GENERATED_LABEL_LOC;
          update_generated_label_kind(label_kinds, section->data_size, target, kind);
          if (label_flags != NULL) label_flags[target] = 1U;
        }
        continue;
      }
      if (metadata == NULL) continue;
      if (instruction_pc_relative_ea_target(&instruction, metadata, (uint8_t)operand_index, (uint32_t)offset,
            section->data_size, &target)) {
        uint32_t base = find_enclosing_code_start(section_analysis, target);
        if (!instruction_is_call_transfer(&instruction) && !instruction_is_unconditional_transfer(&instruction)) {
          GeneratedLabelKind exact_kind = GENERATED_LABEL_DAT;
          if (target < section_analysis->certain_code_size && section_analysis->certain_code_byte != NULL &&
              section_analysis->certain_code_byte[target] != 0U &&
              offset_decodes_as_instruction(ctx, target)) {
            exact_kind = GENERATED_LABEL_LOC;
          }
          update_generated_label_kind(label_kinds, section->data_size, target, exact_kind);
          if (label_flags != NULL) label_flags[target] = 1U;
          continue;
        }
        if (base != UINT32_MAX && base != target) {
          update_generated_label_kind(label_kinds, section->data_size, base, GENERATED_LABEL_LOC);
          if (label_flags != NULL) label_flags[base] = 1U;
          continue;
        }
        if (base == target) {
          update_generated_label_kind(label_kinds, section->data_size, target, GENERATED_LABEL_LOC);
          if (label_flags != NULL) label_flags[target] = 1U;
          continue;
        }
        kind = instruction_is_call_transfer(&instruction) ? GENERATED_LABEL_SUB : GENERATED_LABEL_LOC;
        update_generated_label_kind(label_kinds, section->data_size, target, kind);
        if (label_flags != NULL) label_flags[target] = 1U;
        continue;
      } else if (!instruction_metadata_operand_target(&instruction, metadata, (uint8_t)operand_index, (uint32_t)offset,
            section->data_size, &target)) {
        continue;
      }
      kind = instruction_is_call_transfer(&instruction) ? GENERATED_LABEL_SUB : GENERATED_LABEL_DAT;
      update_generated_label_kind(label_kinds, section->data_size, target, kind);
      if (label_flags != NULL) label_flags[target] = 1U;
    }
    if (instruction.byte_count > 1U) offset += instruction.byte_count - 1U;
  }
  return 0;
}

static void finalize_generated_label_kinds(const M68kSectionAnalysisIR *section_analysis,
    GeneratedLabelKind *label_kinds, size_t label_kind_count) {
  size_t offset;
  if (section_analysis == NULL || label_kinds == NULL) return;
  for (offset = 0; offset < label_kind_count; ++offset) {
    size_t edge_index;
    int has_incoming_call = 0;
    int has_incoming_non_call = 0;
    if (!section_analysis_has_block_start(section_analysis, (uint32_t)offset)) continue;
    for (edge_index = 0; edge_index < section_analysis->edge_count; ++edge_index) {
      const M68kCfgEdgeIR *edge = &section_analysis->edges[edge_index];
      if (edge->target_offset != (uint32_t)offset) continue;
      if (edge->kind == M68K_CFG_EDGE_CALL) has_incoming_call = 1;
      else has_incoming_non_call = 1;
    }
    if (!has_incoming_non_call && has_incoming_call)
      label_kinds[offset] = GENERATED_LABEL_SUB;
    else
      label_kinds[offset] = GENERATED_LABEL_LOC;
  }
}

static uint32_t find_enclosing_code_start(const M68kSectionAnalysisIR *section_analysis, uint32_t offset);
static int section_analysis_has_block_start(const M68kSectionAnalysisIR *section_analysis, uint32_t offset);
static int append_statement_comment(char *buf, size_t buf_size, const char *message);
static void mark_data_fixup_labels(const M68kObject *object, const M68kSectionAnalysisIR *section_analysis,
    GeneratedLabelKind *label_kinds, uint8_t *generated_label_flags);
static int build_self_section_long_exprs(const M68kObject *object, const M68kSectionAnalysisIR *section_analysis,
    GeneratedLabelKind *label_kinds, size_t label_kind_count, uint8_t *generated_label_flags, Arena *scratch_arena,
    char **out_long_exprs);

static int scan_interior_pc_relative_refs(const SectionAnalysisContext *ctx, M68kAnalysisFindings *findings,
    M68kSectionAnalysisIR *section_analysis, GeneratedLabelKind *label_kinds, uint8_t *label_flags) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  size_t offset;
  if (section == NULL || section_analysis == NULL || label_kinds == NULL || label_flags == NULL ||
      section_analysis->certain_code_byte == NULL)
    return 0;
  for (offset = 0; offset < section->data_size; ++offset) {
    M68kInstructionIR instruction;
    SectionDecodeResult decode;
    const M68kSimFormMetadata *metadata;
    size_t operand_index;
    if (!offset_is_known_code_byte(section_analysis, (uint32_t)offset)) continue;
    if (!section_analysis_context_decode(ctx, (uint32_t)offset, findings, &decode))
      continue;
    instruction = decode.instruction;
    metadata = instruction_sim_metadata(&instruction);
    if (metadata == NULL) continue;
    for (operand_index = 0; operand_index < instruction.operand_count; ++operand_index) {
      uint32_t target;
      uint32_t base;
      uint32_t end;
      char message[128];
      if (!instruction_pc_relative_ea_target(&instruction, metadata, (uint8_t)operand_index, (uint32_t)offset,
            section->data_size, &target)) {
        continue;
      }
      base = find_enclosing_instruction_start(ctx, section_analysis, findings, target, &end);
      if (base == UINT32_MAX || base == target) continue;
      label_flags[base] = 1U;
      update_generated_label_kind(label_kinds, section->data_size, base, GENERATED_LABEL_LOC);
      if (end < section->data_size) {
        GeneratedLabelKind end_kind = GENERATED_LABEL_DAT;
        if (offset_is_known_code_byte(section_analysis, end) &&
            offset_decodes_as_instruction(ctx, end)) {
          end_kind = GENERATED_LABEL_LOC;
        }
        label_flags[end] = 1U;
        update_generated_label_kind(label_kinds, section->data_size, end, end_kind);
      }
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
    if (instruction.byte_count > 1U) offset += instruction.byte_count - 1U;
  }
  return 0;
}

static int queue_push(uint32_t **queue, size_t *queue_count, size_t *queue_capacity, Arena *scratch_arena,
    uint32_t value) {
  if (scratch_arena == NULL) return -1;
  if (*queue_count == *queue_capacity) {
    size_t grown_capacity = *queue_capacity * 2U;
    uint32_t *grown = NULL;
    grown = (uint32_t *)arena_alloc(scratch_arena, grown_capacity * sizeof(**queue));
    if (grown != NULL && *queue != NULL)
      memcpy(grown, *queue, *queue_count * sizeof(**queue));
    if (grown == NULL) return -1;
    *queue = grown;
    *queue_capacity = grown_capacity;
  }
  (*queue)[(*queue_count)++] = value;
  return 0;
}

static int queue_target_with_state(uint32_t **queue, size_t *queue_count, size_t *queue_capacity, Arena *scratch_arena,
    M68kSimCpuState *entry_states, uint8_t *entry_state_valid, uint32_t target, const M68kSimCpuState *state) {
  int changed = 0;
  if (entry_states == NULL || entry_state_valid == NULL || state == NULL) return -1;
  if (entry_state_valid[target] == 0U) {
    entry_states[target] = *state;
    entry_state_valid[target] = 1U;
    changed = 1;
  } else {
    changed = m68k_sim_cpu_state_join(&entry_states[target], state);
  }
  if (changed) return queue_push(queue, queue_count, queue_capacity, scratch_arena, target);
  return 0;
}

static int queue_target_with_sim_state(uint32_t **queue, size_t *queue_count, size_t *queue_capacity, Arena *scratch_arena,
    M68kSimCpuState *entry_states, M68kSimMemoryState *entry_memory_states, uint8_t *entry_state_valid,
    uint32_t target, const M68kSimCpuState *state, const M68kSimMemoryState *memory_state) {
  int changed = 0;
  if (entry_states == NULL || entry_memory_states == NULL || entry_state_valid == NULL || state == NULL ||
      memory_state == NULL) return -1;
  if (entry_state_valid[target] == 0U) {
    entry_states[target] = *state;
    entry_memory_states[target] = *memory_state;
    entry_state_valid[target] = 1U;
    changed = 1;
  } else {
    changed |= m68k_sim_cpu_state_join(&entry_states[target], state);
    changed |= m68k_sim_memory_state_join(&entry_memory_states[target], memory_state);
  }
  if (changed) return queue_push(queue, queue_count, queue_capacity, scratch_arena, target);
  return 0;
}

typedef struct LocalCallSummaryEntry {
  M68kSimCpuState input_state;
  M68kSimMemoryState input_memory;
  M68kSimCpuState output_state;
  M68kSimMemoryState output_memory;
  uint8_t has_input;
  uint8_t valid;
  uint8_t active;
} LocalCallSummaryEntry;

typedef struct LocalCallSummaryCache {
  Arena *arena;
  LocalCallSummaryEntry *entries;
  size_t entry_count;
} LocalCallSummaryCache;

typedef struct SummaryStateEntry {
  uint32_t offset;
  M68kSimCpuState state;
  M68kSimMemoryState memory_state;
} SummaryStateEntry;

typedef struct SummaryStateMap {
  Arena *arena;
  SummaryStateEntry *entries;
  size_t entry_count;
  size_t entry_capacity;
} SummaryStateMap;

typedef struct LocalCallSummaryIterationResult {
  M68kSimCpuState return_state;
  M68kSimMemoryState return_memory;
  uint8_t have_return;
} LocalCallSummaryIterationResult;

#define RECENT_INSTRUCTION_WINDOW_SIZE 5U
/* PC-relative dispatch recovery currently needs up to five preceding instructions. */
typedef struct RecentInstructionWindow {
  M68kInstructionIR instructions[RECENT_INSTRUCTION_WINDOW_SIZE];
  uint32_t instruction_offsets[RECENT_INSTRUCTION_WINDOW_SIZE];
  uint8_t valid[RECENT_INSTRUCTION_WINDOW_SIZE];
} RecentInstructionWindow;

static int recover_pc_relative_word_dispatch_targets(const SectionDiscoveryMap *discovery,
    const M68kInstructionIR *instruction, uint32_t instruction_offset, const RecentInstructionWindow *recent_window,
    const SectionAnalysisContext *ctx, M68kSimTargetSet *out_targets);
static int recover_string_dispatch_targets_from_decoder_call(const SectionAnalysisContext *ctx,
    M68kSectionAnalysisIR *section_analysis, const M68kInstructionIR *instruction, uint32_t dispatch_site,
    const RecentInstructionWindow *recent_window, M68kSimTargetSet *out_targets);
static int find_recent_string_dispatch_decoder_call(const SectionAnalysisContext *ctx, const RecentInstructionWindow *recent_window,
    uint8_t target_reg, uint32_t *out_decoder_entry);

typedef struct DiscoveryStep {
  SectionDecodeResult decode;
  M68kInstructionIR instruction;
  M68kSimStepResult sim_result;
  const M68kSimFormMetadata *metadata;
  M68kSimMemoryState local_call_summary_memory_state;
  uint32_t target;
  int conditional_outcome_known;
  int state_stops_fallthrough;
  int local_call_summary_valid;
} DiscoveryStep;

static int compute_resolved_local_call_summary_raw(const M68kObject *object, const SectionAnalysisContext *ctx,
    size_t section_index, uint32_t entry_offset, const M68kSimCpuState *input_state,
    const M68kSimMemoryState *input_memory, Arena *scratch_arena, LocalCallSummaryCache *cache,
    M68kSimCpuState *out_state, M68kSimMemoryState *out_memory, int *out_valid);
static int discovery_decode_and_step(const M68kObject *object, size_t section_index, Arena *scratch_arena,
    const SectionAnalysisContext *ctx, M68kAnalysisFindings *findings, LocalCallSummaryCache *call_summary_cache,
    M68kSectionAnalysisIR *out_analysis, SectionDiscoveryMap *discovery, uint32_t work_offset,
    const M68kSimCpuState *current_state, const M68kSimMemoryState *current_memory_state, DiscoveryStep *out_step);
static int discovery_recover_indirect_targets(const SectionAnalysisContext *ctx, const SectionDiscoveryMap *discovery,
    M68kSectionAnalysisIR *out_analysis, uint32_t work_offset, const RecentInstructionWindow *recent_window,
    DiscoveryStep *step);
static int discovery_enqueue_control_targets(const M68kSection *section, size_t section_index, Arena *scratch_arena,
    M68kSectionAnalysisIR *out_analysis, uint32_t **queue, size_t *queue_count, size_t *queue_capacity,
    M68kSimCpuState *entry_states, M68kSimMemoryState *entry_memory_states, uint8_t *entry_state_valid,
    M68kSimTargetSet *sim_targets, uint32_t work_offset, const M68kSimCpuState *current_state,
    const M68kSimMemoryState *current_memory_state, const DiscoveryStep *step);
static void recent_instruction_window_reset(RecentInstructionWindow *window);
static void recent_instruction_window_push(RecentInstructionWindow *window, const M68kInstructionIR *instruction,
    uint32_t instruction_offset);

static int local_call_summary_cache_init(LocalCallSummaryCache *cache, Arena *arena, size_t section_size) {
  if (cache == NULL || arena == NULL) return -1;
  memset(cache, 0, sizeof(*cache));
  cache->arena = arena;
  cache->entries = (LocalCallSummaryEntry *)arena_alloc(arena,
    (section_size != 0U ? section_size : 1U) * sizeof(*cache->entries));
  if (cache->entries == NULL) return -1;
  memset(cache->entries, 0, (section_size != 0U ? section_size : 1U) * sizeof(*cache->entries));
  cache->entry_count = section_size;
  return 0;
}

static int section_decode_cache_init(SectionDecodeCache *cache, Arena *arena, size_t section_size) {
  if (cache == NULL || arena == NULL) return -1;
  memset(cache, 0, sizeof(*cache));
  cache->entries = (SectionDecodeCacheEntry *)arena_alloc(arena,
    (section_size != 0U ? section_size : 1U) * sizeof(*cache->entries));
  if (cache->entries == NULL) return -1;
  memset(cache->entries, 0, (section_size != 0U ? section_size : 1U) * sizeof(*cache->entries));
  cache->entry_count = section_size;
  return 0;
}

int section_analysis_context_init(SectionAnalysisContext *ctx, const M68kObject *object, const M68kSection *section,
    const M68kAnalysisPolicy *analysis_policy, Arena *arena) {
  if (ctx == NULL || section == NULL || analysis_policy == NULL || arena == NULL) return -1;
  memset(ctx, 0, sizeof(*ctx));
  ctx->object = object;
  ctx->section = section;
  ctx->analysis_policy = analysis_policy;
  return section_decode_cache_init(&ctx->decode_cache, arena, section->data_size);
}

static void update_findings_for_cached_instruction(const M68kInstructionIR *instruction,
    const M68kAnalysisPolicy *analysis_policy, M68kAnalysisFindings *findings) {
  uint8_t required_cpu;
  uint8_t max_cpu;
  if (instruction == NULL || findings == NULL) return;
  required_cpu = instruction_required_cpu(instruction);
  update_required_cpu(findings, required_cpu);
  max_cpu = effective_analysis_max_cpu(analysis_policy);
  if (required_cpu > max_cpu) findings->cpu_violation_count += 1U;
}

int section_analysis_context_decode(const SectionAnalysisContext *ctx, uint32_t offset,
    M68kAnalysisFindings *findings, SectionDecodeResult *out_result) {
  SectionDecodeCacheEntry *entry;
  int decode_result;
  if (out_result != NULL) memset(out_result, 0, sizeof(*out_result));
  if (ctx == NULL || ctx->section == NULL || ctx->analysis_policy == NULL || ctx->decode_cache.entries == NULL ||
      offset >= ctx->section->data_size || offset >= ctx->decode_cache.entry_count) {
    return 0;
  }
  entry = &ctx->decode_cache.entries[offset];
  if (entry->state == 0U) {
    decode_result = decode_instruction_with_policy(ctx->section->data + offset, ctx->section->data_size - offset,
      offset, ctx->analysis_policy, NULL, &entry->instruction, m68k_diag_sink(NULL));
    if (decode_result <= 0 || entry->instruction.byte_count == 0U ||
        offset + entry->instruction.byte_count > ctx->section->data_size) {
      entry->state = 1U;
      return 0;
    }
    entry->state = 2U;
    if (instruction_control_transfer_target(&entry->instruction, ctx->section->data + offset,
          ctx->section->data_size - offset, offset, (uint32_t)ctx->section->data_size, &entry->explicit_target)) {
      entry->has_explicit_target = 1U;
    }
    entry->is_call = (uint8_t)instruction_is_call_transfer(&entry->instruction);
    entry->is_unconditional_transfer = (uint8_t)instruction_is_unconditional_transfer(&entry->instruction);
    entry->is_conditional_transfer = (uint8_t)is_conditional_transfer(&entry->instruction);
    entry->stops_fallthrough = (uint8_t)instruction_stops_fallthrough(&entry->instruction);
  }
  if (entry->state != 2U) return 0;
  update_findings_for_cached_instruction(&entry->instruction, ctx->analysis_policy, findings);
  if (out_result != NULL) {
    out_result->instruction = entry->instruction;
    out_result->has_explicit_target = entry->has_explicit_target;
    out_result->explicit_target = entry->explicit_target;
    out_result->is_call = entry->is_call;
    out_result->is_unconditional_transfer = entry->is_unconditional_transfer;
    out_result->is_conditional_transfer = entry->is_conditional_transfer;
    out_result->stops_fallthrough = entry->stops_fallthrough;
  }
  return 1;
}

int section_analysis_context_probe_decode(const SectionAnalysisContext *ctx, uint32_t offset,
    SectionDecodeResult *out_result) {
  M68kInstructionIR instruction;
  int decode_result;
  uint32_t explicit_target = 0U;
  uint8_t has_explicit_target = 0U;
  if (ctx == NULL || ctx->section == NULL || offset >= ctx->section->data_size) return 0;
  decode_result = decode_instruction_with_policy(ctx->section->data + offset, ctx->section->data_size - offset, offset,
    ctx->analysis_policy, NULL, &instruction, m68k_diag_sink(NULL));
  if (decode_result <= 0 || instruction.byte_count == 0U || offset + instruction.byte_count > ctx->section->data_size)
    return 0;
  if (instruction_control_transfer_target(&instruction, ctx->section->data + offset, ctx->section->data_size - offset,
        offset, (uint32_t)ctx->section->data_size, &explicit_target)) {
    has_explicit_target = 1U;
  }
  if (out_result != NULL) {
    out_result->instruction = instruction;
    out_result->explicit_target = explicit_target;
    out_result->has_explicit_target = has_explicit_target;
    out_result->is_call = (uint8_t)instruction_is_call_transfer(&instruction);
    out_result->is_unconditional_transfer = (uint8_t)instruction_is_unconditional_transfer(&instruction);
    out_result->is_conditional_transfer = (uint8_t)is_conditional_transfer(&instruction);
    out_result->stops_fallthrough = (uint8_t)instruction_stops_fallthrough(&instruction);
  }
  return 1;
}

uint8_t section_analysis_context_backend_kind(const SectionAnalysisContext *ctx) {
  if (ctx == NULL || ctx->object == NULL) return M68K_PLATFORM_BACKEND_UNKNOWN;
  return ctx->object->platform_backend_kind;
}

const M68kObject *section_analysis_context_object(const SectionAnalysisContext *ctx) {
  return ctx != NULL ? ctx->object : NULL;
}

const M68kSection *section_analysis_context_section(const SectionAnalysisContext *ctx) {
  return ctx != NULL ? ctx->section : NULL;
}

static int summary_state_map_find_index(const SummaryStateMap *map, uint32_t offset, size_t *out_index) {
  size_t index;
  if (map == NULL || out_index == NULL) return 0;
  for (index = 0; index < map->entry_count; ++index) {
    if (map->entries[index].offset == offset) {
      *out_index = index;
      return 1;
    }
  }
  return 0;
}

static int summary_state_map_join_or_enqueue(SummaryStateMap *map, uint32_t **queue, size_t *queue_count,
    size_t *queue_capacity, Arena *scratch_arena, uint32_t offset, const M68kSimCpuState *state,
    const M68kSimMemoryState *memory_state) {
  size_t index;
  if (map == NULL || queue == NULL || queue_count == NULL || queue_capacity == NULL || scratch_arena == NULL ||
      state == NULL || memory_state == NULL) {
    return -1;
  }
  if (summary_state_map_find_index(map, offset, &index)) {
    int changed = 0;
    changed |= m68k_sim_cpu_state_join(&map->entries[index].state, state);
    changed |= m68k_sim_memory_state_join(&map->entries[index].memory_state, memory_state);
    if (changed) return queue_push(queue, queue_count, queue_capacity, scratch_arena, offset);
    return 0;
  }
  if (map->entry_count >= map->entry_capacity) {
    size_t next_capacity = map->entry_capacity == 0U ? 16U : (map->entry_capacity * 2U);
    SummaryStateEntry *grown = (SummaryStateEntry *)arena_realloc_copy(map->arena, map->entries,
      map->entry_count * sizeof(*map->entries), next_capacity * sizeof(*map->entries));
    if (grown == NULL) return -1;
    map->entries = grown;
    map->entry_capacity = next_capacity;
  }
  if (map->entries == NULL) return -1;
  index = map->entry_count++;
  map->entries[index].offset = offset;
  map->entries[index].state = *state;
  map->entries[index].memory_state = *memory_state;
  return queue_push(queue, queue_count, queue_capacity, scratch_arena, offset);
}

static int local_call_summary_prepare(LocalCallSummaryEntry *entry, const M68kSimCpuState *input_state,
    const M68kSimMemoryState *input_memory, M68kSimCpuState *out_state, M68kSimMemoryState *out_memory,
    int *out_valid, int *out_input_changed) {
  int input_changed = 0;
  if (entry == NULL || input_state == NULL || input_memory == NULL || out_input_changed == NULL) return -1;
  if (out_valid != NULL) *out_valid = 0;
  if (out_state != NULL) m68k_sim_cpu_state_init_unknown(out_state);
  if (out_memory != NULL) m68k_sim_memory_state_init(out_memory);
  if (entry->has_input == 0U) {
    entry->input_state = *input_state;
    entry->input_memory = *input_memory;
    entry->has_input = 1U;
    input_changed = 1;
  } else {
    input_changed |= m68k_sim_cpu_state_join(&entry->input_state, input_state);
    input_changed |= m68k_sim_memory_state_join(&entry->input_memory, input_memory);
  }
  if (entry->active != 0U) {
    if (entry->valid != 0U) {
      if (out_state != NULL) *out_state = entry->output_state;
      if (out_memory != NULL) *out_memory = entry->output_memory;
      if (out_valid != NULL) *out_valid = 1;
    } else if (out_valid != NULL) {
      *out_valid = -1;
    }
    *out_input_changed = input_changed;
    return 1;
  }
  if (entry->valid != 0U && !input_changed) {
    if (out_state != NULL) *out_state = entry->output_state;
    if (out_memory != NULL) *out_memory = entry->output_memory;
    if (out_valid != NULL) *out_valid = 1;
    *out_input_changed = input_changed;
    return 1;
  }
  *out_input_changed = input_changed;
  return 0;
}

static int local_call_summary_run_iteration(const M68kObject *object, const SectionAnalysisContext *ctx,
    size_t section_index, uint32_t entry_offset, Arena *scratch_arena, LocalCallSummaryCache *cache,
    LocalCallSummaryEntry *entry, LocalCallSummaryIterationResult *out_result) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  ArenaMark mark;
  uint32_t *queue = NULL;
  SummaryStateMap state_map = {0};
  size_t queue_count = 0U;
  size_t queue_capacity = 32U;
  size_t pop_index = 0U;
  if (object == NULL || section == NULL || ctx->analysis_policy == NULL || scratch_arena == NULL ||
      cache == NULL || cache->entries == NULL || entry == NULL || out_result == NULL ||
      entry_offset >= section->data_size || entry_offset >= cache->entry_count) {
    return -1;
  }
  mark = arena_mark(scratch_arena);
  state_map.arena = scratch_arena;
  queue = (uint32_t *)arena_calloc(scratch_arena, queue_capacity, sizeof(*queue));
  if (queue == NULL) {
    arena_rewind(scratch_arena, mark);
    return -1;
  }
  if (summary_state_map_join_or_enqueue(&state_map, &queue, &queue_count, &queue_capacity, scratch_arena, entry_offset,
        &entry->input_state, &entry->input_memory) != 0) {
    arena_rewind(scratch_arena, mark);
    return -1;
  }
  m68k_sim_cpu_state_init_unknown(&out_result->return_state);
  m68k_sim_memory_state_init(&out_result->return_memory);
  out_result->have_return = 0U;

  while (pop_index < queue_count) {
      size_t state_index;
      uint32_t work_offset = queue[pop_index++];
      uint32_t segment_start = work_offset;
      M68kSimCpuState current_state;
      M68kSimMemoryState current_memory_state;
      if (!summary_state_map_find_index(&state_map, work_offset, &state_index)) continue;
      current_state = state_map.entries[state_index].state;
      current_memory_state = state_map.entries[state_index].memory_state;
      while (work_offset < section->data_size) {
        SectionDecodeResult decode;
        M68kInstructionIR instruction;
        M68kSimStepResult sim_result;
        const M68kSimFormMetadata *metadata;
        M68kSimMemoryState next_memory_state;
        uint32_t target = 0U;
        uint32_t next_offset;
        int conditional_outcome_known = 0;
        int use_local_summary = 0;
        if (work_offset != segment_start && summary_state_map_find_index(&state_map, work_offset, &state_index)) break;
        if (!section_analysis_context_decode(ctx, work_offset, NULL, &decode)) break;
        instruction = decode.instruction;
        if (decode.has_explicit_target) target = decode.explicit_target;
        if (m68k_simulate_step_with_memory(object, section_index, section, work_offset, &instruction, &current_state,
              &current_memory_state, &sim_result) != 0) {
          arena_rewind(scratch_arena, mark);
          return -1;
        }
        metadata = instruction_sim_metadata(&instruction);
        conditional_outcome_known = decode.is_conditional_transfer &&
          metadata != NULL &&
          metadata->operation_type != M68K_SIM_OP_DBCC &&
          current_state.sr_known != 0U;
        next_offset = work_offset + (uint32_t)instruction.byte_count;
        next_memory_state = current_memory_state;
        apply_sim_memory_writes(&next_memory_state, &sim_result);
        if (decode.is_call && decode.has_explicit_target && target < section->data_size) {
          M68kSimCpuState callee_state;
          M68kSimMemoryState callee_memory;
          int callee_valid = 0;
          if (compute_resolved_local_call_summary_raw(object, ctx, section_index, target,
                &current_state, &current_memory_state, scratch_arena, cache, &callee_state,
                &callee_memory, &callee_valid) != 0) {
            arena_rewind(scratch_arena, mark);
            return -1;
          }
          if (callee_valid) {
            sim_result.next_state = callee_state;
            sim_result.next_state.pc = next_offset;
            next_memory_state = callee_memory;
            use_local_summary = 1;
          } else if (callee_valid < 0) {
            break;
          }
        }
        if (decode.is_call) {
          current_state = sim_result.next_state;
          current_memory_state = next_memory_state;
          work_offset = next_offset;
          if (work_offset >= section->data_size) break;
          continue;
        }
        if (decode.has_explicit_target && (!conditional_outcome_known || sim_result.control_targets.count != 0U)) {
          if (summary_state_map_join_or_enqueue(&state_map, &queue, &queue_count, &queue_capacity, scratch_arena,
                target, &sim_result.next_state, &next_memory_state) != 0) {
            arena_rewind(scratch_arena, mark);
            return -1;
          }
        }
        current_state = sim_result.next_state;
        current_memory_state = next_memory_state;
        work_offset = next_offset;
        if (metadata != NULL && metadata->flow_kind == M68K_SIM_FLOW_RETURN) {
          if (!out_result->have_return) {
            out_result->return_state = current_state;
            out_result->return_memory = current_memory_state;
            out_result->have_return = 1U;
          } else {
            m68k_sim_cpu_state_join(&out_result->return_state, &current_state);
            m68k_sim_memory_state_join(&out_result->return_memory, &current_memory_state);
          }
          break;
        }
        if (sim_result.stops_fallthrough || decode.stops_fallthrough) break;
        if (!use_local_summary && decode.has_explicit_target && decode.is_unconditional_transfer) break;
      }
    }
  arena_rewind(scratch_arena, mark);
  return 0;
}

static int local_call_summary_merge_output(LocalCallSummaryEntry *entry,
    const LocalCallSummaryIterationResult *result, int *out_output_changed) {
  int output_changed = 0;
  if (entry == NULL || result == NULL || out_output_changed == NULL) return -1;
  if (result->have_return == 0U) {
    *out_output_changed = 0;
    return 1;
  }
  if (entry->valid == 0U) {
    entry->output_state = result->return_state;
    entry->output_memory = result->return_memory;
    entry->valid = 1U;
    output_changed = 1;
  } else {
    output_changed |= m68k_sim_cpu_state_join(&entry->output_state, &result->return_state);
    output_changed |= m68k_sim_memory_state_join(&entry->output_memory, &result->return_memory);
  }
  *out_output_changed = output_changed;
  return 0;
}

static int discovery_decode_and_step(const M68kObject *object, size_t section_index, Arena *scratch_arena,
    const SectionAnalysisContext *ctx, M68kAnalysisFindings *findings, LocalCallSummaryCache *call_summary_cache,
    M68kSectionAnalysisIR *out_analysis, SectionDiscoveryMap *discovery, uint32_t work_offset,
    const M68kSimCpuState *current_state, const M68kSimMemoryState *current_memory_state, DiscoveryStep *out_step) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  size_t index;
  if (object == NULL || scratch_arena == NULL || section == NULL || call_summary_cache == NULL || out_analysis == NULL ||
      discovery == NULL || current_state == NULL || current_memory_state == NULL || out_step == NULL) {
    return -1;
  }
  memset(out_step, 0, sizeof(*out_step));
  if (!section_analysis_context_decode(ctx, work_offset, findings, &out_step->decode)) {
    if (m68k_ir_section_analysis_add_violation(out_analysis, work_offset, M68K_VIOLATION_DECODE_FAILED_REACHABLE,
          "decode failed in reachable code; stopping segment") != 0) {
      return -1;
    }
    return 0;
  }
  out_step->instruction = out_step->decode.instruction;
  if (add_cpu_violation(out_analysis, work_offset, &out_step->instruction, ctx->analysis_policy) != 0) return -1;
  discovery->is_code_start[work_offset] = 1U;
  for (index = 0; index < out_step->instruction.byte_count; ++index) discovery->is_code_byte[work_offset + index] = 1U;
  if (out_step->decode.has_explicit_target) {
    out_step->target = out_step->decode.explicit_target;
    if (m68k_ir_section_analysis_add_label(out_analysis, out_step->target) != 0) return -1;
  }
  if (m68k_simulate_step_with_memory(object, section_index, section, work_offset, &out_step->instruction, current_state,
        current_memory_state, &out_step->sim_result) != 0) {
    return -1;
  }
  out_step->metadata = instruction_sim_metadata(&out_step->instruction);
  if (out_step->decode.is_call && out_step->decode.has_explicit_target && out_step->target < section->data_size) {
    M68kSimCpuState callee_state;
    if (compute_resolved_local_call_summary_raw(object, ctx, section_index, out_step->target, current_state,
          current_memory_state, scratch_arena, call_summary_cache, &callee_state, &out_step->local_call_summary_memory_state,
          &out_step->local_call_summary_valid) != 0) {
      return -1;
    }
    if (out_step->local_call_summary_valid) {
      out_step->sim_result.next_state = callee_state;
      out_step->sim_result.next_state.pc = work_offset + (uint32_t)out_step->instruction.byte_count;
    }
  }
  out_step->conditional_outcome_known = out_step->decode.is_conditional_transfer &&
    out_step->metadata != NULL &&
    out_step->metadata->operation_type != M68K_SIM_OP_DBCC &&
    current_state->sr_known != 0U;
  out_step->state_stops_fallthrough = out_step->sim_result.stops_fallthrough;
  return 1;
}

static int discovery_recover_indirect_targets(const SectionAnalysisContext *ctx, const SectionDiscoveryMap *discovery,
    M68kSectionAnalysisIR *out_analysis, uint32_t work_offset, const RecentInstructionWindow *recent_window,
    DiscoveryStep *step) {
  M68kSimTargetSet recovered_targets;
  if (ctx == NULL || discovery == NULL || out_analysis == NULL || recent_window == NULL || step == NULL) return -1;
  if (!step->decode.has_explicit_target &&
      (step->decode.is_call || step->decode.is_unconditional_transfer) &&
      instruction_target_operand_is_brief_indexed_pc(&step->instruction)) {
    m68k_sim_target_set_init(&step->sim_result.control_targets);
  }
  if (step->decode.has_explicit_target &&
      (!step->conditional_outcome_known || step->sim_result.control_targets.count != 0U) &&
      m68k_sim_target_set_add(&step->sim_result.control_targets, step->target) == 0) {
    return -1;
  }
  m68k_sim_target_set_init(&recovered_targets);
  if (!step->decode.has_explicit_target &&
      step->decode.is_call &&
      recover_string_dispatch_targets_from_decoder_call(ctx, out_analysis, &step->instruction, work_offset, recent_window,
        NULL)) {
    return 0;
  }
  if (!step->decode.has_explicit_target &&
      (step->decode.is_call || step->decode.is_unconditional_transfer) &&
      recover_pc_relative_word_dispatch_targets(discovery, &step->instruction, work_offset, recent_window, ctx,
        &recovered_targets)) {
    size_t recovered_index;
    step->sim_result.control_targets = recovered_targets;
    for (recovered_index = 0; recovered_index < recovered_targets.count; ++recovered_index)
      m68k_sim_target_set_add(&step->sim_result.discovered_labels, recovered_targets.targets[recovered_index]);
    return 0;
  }
  if (!step->decode.has_explicit_target &&
      (step->decode.is_call || step->decode.is_unconditional_transfer) &&
      recover_pc_index_inline_dispatch_targets(discovery, &step->instruction, work_offset, ctx, &recovered_targets)) {
    size_t recovered_index;
    if (collect_pc_index_inline_dispatch_table(discovery, &step->instruction, work_offset, ctx, out_analysis) < 0)
      return -1;
    step->sim_result.control_targets = recovered_targets;
    for (recovered_index = 0; recovered_index < recovered_targets.count; ++recovered_index)
      m68k_sim_target_set_add(&step->sim_result.discovered_labels, recovered_targets.targets[recovered_index]);
    return 0;
  }
  if (!step->decode.has_explicit_target &&
      (step->decode.is_call || step->decode.is_unconditional_transfer) &&
      recent_window->valid[0] != 0U && recent_window->valid[1] != 0U &&
      recent_window->valid[2] != 0U &&
      recover_brief_word_offset_dispatch_targets(discovery, &step->instruction, &recent_window->instructions[0],
        &recent_window->instructions[1], &recent_window->instructions[2],
        recent_window->instruction_offsets[2], ctx, &recovered_targets)) {
    size_t recovered_index;
    step->sim_result.control_targets = recovered_targets;
    for (recovered_index = 0; recovered_index < recovered_targets.count; ++recovered_index)
      m68k_sim_target_set_add(&step->sim_result.discovered_labels, recovered_targets.targets[recovered_index]);
    return 0;
  }
  if ((step->decode.is_call || step->decode.is_unconditional_transfer) &&
      recent_window->valid[0] != 0U && recent_window->valid[1] != 0U &&
      recover_entry_relative_word_dispatch_targets(discovery, &step->instruction, &recent_window->instructions[0],
        &recent_window->instructions[1], recent_window->instruction_offsets[1], ctx, &recovered_targets)) {
    size_t recovered_index;
    merge_sim_target_set(&step->sim_result.control_targets, &recovered_targets);
    for (recovered_index = 0; recovered_index < recovered_targets.count; ++recovered_index)
      m68k_sim_target_set_add(&step->sim_result.discovered_labels, recovered_targets.targets[recovered_index]);
  }
  return 0;
}

static int discovery_enqueue_control_targets(const M68kSection *section, size_t section_index, Arena *scratch_arena,
    M68kSectionAnalysisIR *out_analysis, uint32_t **queue, size_t *queue_count, size_t *queue_capacity,
    M68kSimCpuState *entry_states, M68kSimMemoryState *entry_memory_states, uint8_t *entry_state_valid,
    M68kSimTargetSet *sim_targets, uint32_t work_offset, const M68kSimCpuState *current_state,
    const M68kSimMemoryState *current_memory_state, const DiscoveryStep *step) {
  size_t index;
  if (section == NULL || scratch_arena == NULL || out_analysis == NULL || queue == NULL || queue_count == NULL ||
      queue_capacity == NULL || entry_states == NULL || entry_memory_states == NULL || entry_state_valid == NULL ||
      sim_targets == NULL || current_state == NULL || current_memory_state == NULL || step == NULL) {
    return -1;
  }
  if (merge_sim_target_set(&sim_targets[work_offset], &step->sim_result.control_targets)) {
    for (index = 0; index < sim_targets[work_offset].count; ++index) {
      uint32_t sim_target = sim_targets[work_offset].targets[index];
      M68kSimMemoryState next_memory_state;
      if (sim_target >= section->data_size) continue;
      if (m68k_ir_section_analysis_add_label(out_analysis, sim_target) != 0) return -1;
      if (step->decode.is_call) {
        if (queue_target_with_sim_state(queue, queue_count, queue_capacity, scratch_arena, entry_states,
              entry_memory_states, entry_state_valid, sim_target, current_state, current_memory_state) != 0) {
          return -1;
        }
      } else {
        next_memory_state = *current_memory_state;
        apply_sim_memory_writes(&next_memory_state, &step->sim_result);
        if (queue_target_with_sim_state(queue, queue_count, queue_capacity, scratch_arena, entry_states,
              entry_memory_states, entry_state_valid, sim_target, &step->sim_result.next_state, &next_memory_state) != 0) {
          return -1;
        }
      }
    }
  }
  for (index = 0; index < step->sim_result.discovered_labels.count; ++index) {
    uint32_t label_target = step->sim_result.discovered_labels.targets[index];
    if (label_target >= section->data_size) continue;
    if (m68k_ir_section_analysis_add_label(out_analysis, label_target) != 0) return -1;
  }
  (void)section_index;
  return 0;
}

static void recent_instruction_window_reset(RecentInstructionWindow *window) {
  if (window == NULL) return;
  memset(window, 0, sizeof(*window));
}

static void recent_instruction_window_push(RecentInstructionWindow *window, const M68kInstructionIR *instruction,
    uint32_t instruction_offset) {
  size_t index;
  if (window == NULL || instruction == NULL) return;
  for (index = RECENT_INSTRUCTION_WINDOW_SIZE - 1U; index > 0U; --index) {
    window->instructions[index] = window->instructions[index - 1U];
    window->instruction_offsets[index] = window->instruction_offsets[index - 1U];
    window->valid[index] = window->valid[index - 1U];
  }
  window->instructions[0] = *instruction;
  window->instruction_offsets[0] = instruction_offset;
  window->valid[0] = 1U;
}

static int compute_resolved_local_call_summary_raw(const M68kObject *object, const SectionAnalysisContext *ctx,
    size_t section_index, uint32_t entry_offset, const M68kSimCpuState *input_state,
    const M68kSimMemoryState *input_memory, Arena *scratch_arena, LocalCallSummaryCache *cache,
    M68kSimCpuState *out_state, M68kSimMemoryState *out_memory, int *out_valid) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  const M68kAnalysisPolicy *analysis_policy = ctx != NULL ? ctx->analysis_policy : NULL;
  int iteration;
  int input_changed = 0;
  LocalCallSummaryEntry *entry = NULL;
  if (out_valid != NULL) *out_valid = 0;
  if (out_state != NULL) m68k_sim_cpu_state_init_unknown(out_state);
  if (out_memory != NULL) m68k_sim_memory_state_init(out_memory);
  if (object == NULL || section == NULL || analysis_policy == NULL || scratch_arena == NULL ||
      cache == NULL || cache->entries == NULL || input_state == NULL || input_memory == NULL ||
      entry_offset >= section->data_size || entry_offset >= cache->entry_count) {
    return 0;
  }
  entry = &cache->entries[entry_offset];
  {
    int prepare_result = local_call_summary_prepare(entry, input_state, input_memory, out_state, out_memory, out_valid,
      &input_changed);
    if (prepare_result != 0) return prepare_result < 0 ? -1 : 0;
  }
  entry->active = 1U;
  for (iteration = 0; iteration < 8; ++iteration) {
    LocalCallSummaryIterationResult iteration_result;
    int output_changed = 0;
    int merge_result;
    if (local_call_summary_run_iteration(object, ctx, section_index, entry_offset, scratch_arena, cache, entry,
          &iteration_result) != 0) {
      entry->active = 0U;
      return -1;
    }
    merge_result = local_call_summary_merge_output(entry, &iteration_result, &output_changed);
    if (merge_result < 0) {
      entry->active = 0U;
      return -1;
    }
    if (merge_result > 0 || !output_changed) break;
  }
  entry->active = 0U;
  if (entry->valid != 0U) {
    if (out_state != NULL) *out_state = entry->output_state;
    if (out_memory != NULL) *out_memory = entry->output_memory;
    if (out_valid != NULL) *out_valid = 1;
  }
  return 0;
}

static void apply_sim_memory_writes(M68kSimMemoryState *state, const M68kSimStepResult *result) {
  size_t write_index;
  if (state == NULL || result == NULL) return;
  for (write_index = 0; write_index < result->memory_write_count; ++write_index) {
    const M68kSimMemoryCell *cell = &result->memory_writes[write_index];
    size_t state_index;
    for (state_index = 0; state_index < state->cell_count; ++state_index) {
      M68kSimMemoryCell *dst_cell = &state->cells[state_index];
      if (dst_cell->offset == cell->offset && dst_cell->width == cell->width &&
          dst_cell->section_index == cell->section_index) {
        dst_cell->value = cell->value;
        break;
      }
    }
    if (state_index == state->cell_count && state->cell_count < M68K_SIM_MEMORY_CELL_LIMIT)
      state->cells[state->cell_count++] = *cell;
  }
}

static int merge_sim_target_set(M68kSimTargetSet *dst, const M68kSimTargetSet *src) {
  size_t index;
  int changed = 0;
  if (dst == NULL || src == NULL) return 0;
  for (index = 0; index < src->count; ++index) {
    size_t before = dst->count;
    m68k_sim_target_set_add(dst, src->targets[index]);
    if (dst->count != before) changed = 1;
  }
  return changed;
}

static int sim_operand_direct_register_local(const M68kOperandIR *operand, uint8_t *is_address, uint8_t *reg) {
  return m68k_instruction_operand_direct_register(operand, is_address, reg);
}

static const M68kSimValue *sim_lookup_register_value_local(const M68kSimCpuState *state, uint8_t is_address, uint8_t reg) {
  if (state == NULL || reg >= 8U) return NULL;
  return is_address ? &state->a[reg] : &state->d[reg];
}

static void merge_sim_value_targets(M68kSimTargetSet *dst, const M68kSimValue *value) {
  size_t index;
  if (dst == NULL || value == NULL) return;
  if (value->kind == M68K_SIM_VALUE_SECTION_PTR) {
    m68k_sim_target_set_add(dst, value->value);
    return;
  }
  if (value->kind == M68K_SIM_VALUE_TABLE_REGION) {
    uint32_t cursor;
    uint32_t end = value->table_end;
    uint32_t stride = value->table_stride == 0U ? 4U : value->table_stride;
    for (cursor = value->table_start; stride != 0U && cursor < end; cursor += stride)
      m68k_sim_target_set_add(dst, cursor);
    return;
  }
  if (value->kind != M68K_SIM_VALUE_TARGET_SET) return;
  for (index = 0; index < value->target_set.count; ++index)
    m68k_sim_target_set_add(dst, value->target_set.targets[index]);
}

static int sim_target_set_is_only_zero(const M68kSimTargetSet *set) {
  return set != NULL && set->count == 1U && set->targets[0] == 0U;
}

int operand_is_brief_indexed_an(const M68kOperandIR *operand, uint8_t *out_base_reg,
    uint8_t *out_index_is_address, uint8_t *out_index_reg, int32_t *out_disp) {
  if (operand == NULL || out_base_reg == NULL || out_index_is_address == NULL || out_index_reg == NULL ||
      out_disp == NULL) {
    return 0;
  }
  if (operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_mode != 6U) return 0;
  *out_base_reg = operand->value.ea_reg;
  *out_index_is_address = operand->value.index_is_address;
  *out_index_reg = operand->value.index_reg;
  *out_disp = (int32_t)m68k_sign_extend32(operand->value.value, 8U);
  return 1;
}

static int operand_is_brief_indexed_pc(const M68kOperandIR *operand, uint8_t *out_index_is_address,
    uint8_t *out_index_reg, uint8_t *out_index_long, uint8_t *out_index_scale, int32_t *out_disp) {
  if (operand == NULL || out_index_is_address == NULL || out_index_reg == NULL || out_index_long == NULL ||
      out_index_scale == NULL || out_disp == NULL) {
    return 0;
  }
  if (operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_mode != 7U || operand->value.ea_reg != 3U) return 0;
  *out_index_is_address = operand->value.index_is_address;
  *out_index_reg = operand->value.index_reg;
  *out_index_long = operand->value.index_long;
  *out_index_scale = operand->value.scale;
  *out_disp = (int32_t)m68k_sign_extend32(operand->value.value, 8U);
  return 1;
}

static int instruction_target_operand_is_brief_indexed_pc(const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  uint8_t index_is_address;
  uint8_t index_reg;
  uint8_t index_long;
  uint8_t index_scale;
  int32_t disp;
  if (instruction == NULL) return 0;
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL || metadata->target_operand_index >= instruction->operand_count) return 0;
  return operand_is_brief_indexed_pc(&instruction->operands[metadata->target_operand_index], &index_is_address,
    &index_reg, &index_long, &index_scale, &disp);
}

int operand_is_indirect_an(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL || out_reg == NULL) return 0;
  if (operand->kind != M68K_ASM_OPERAND_IND && operand->kind != M68K_ASM_OPERAND_EA) return 0;
  if (operand->value.ea_mode != 2U) return 0;
  *out_reg = operand->value.ea_reg;
  return 1;
}

int operand_is_indirect_disp_an(const M68kOperandIR *operand, uint8_t *out_reg, int16_t *out_disp) {
  if (operand == NULL || out_reg == NULL || out_disp == NULL) return 0;
  if (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) return 0;
  if (operand->value.ea_mode != 5U) return 0;
  *out_reg = operand->value.ea_reg;
  *out_disp = (int16_t)(operand->value.value & 0xFFFFU);
  return 1;
}

int operand_is_indirect_or_disp_an(const M68kOperandIR *operand, uint8_t *out_reg, int16_t *out_disp) {
  if (operand == NULL || out_reg == NULL || out_disp == NULL) return 0;
  if (operand_is_indirect_an(operand, out_reg)) {
    *out_disp = 0;
    return 1;
  }
  return operand_is_indirect_disp_an(operand, out_reg, out_disp);
}

static int instruction_is_add_word_self(const M68kInstructionIR *instruction, uint8_t reg) {
  uint8_t src_is_address, dst_is_address, src_reg, dst_reg;
  if (instruction == NULL || instruction->mnemonic_id != M68K_ASM_MNEMONIC_ADD ||
      instruction->size_suffix != 'w' ||
      instruction->operand_count != 2U) {
    return 0;
  }
  if (!sim_operand_direct_register_local(&instruction->operands[0], &src_is_address, &src_reg) ||
      !sim_operand_direct_register_local(&instruction->operands[1], &dst_is_address, &dst_reg)) {
    return 0;
  }
  return src_is_address == 0U && dst_is_address == 0U && src_reg == reg && dst_reg == reg;
}

static int instruction_is_adda_word_indirect_self(const M68kInstructionIR *instruction, uint8_t reg) {
  uint8_t dst_is_address;
  uint8_t dst_reg;
  uint8_t src_reg;
  if (instruction == NULL || instruction->mnemonic_id != M68K_ASM_MNEMONIC_ADDA ||
      instruction->size_suffix != 'w' ||
      instruction->operand_count != 2U) {
    return 0;
  }
  if (!operand_is_indirect_an(&instruction->operands[0], &src_reg) ||
      !sim_operand_direct_register_local(&instruction->operands[1], &dst_is_address, &dst_reg)) {
    return 0;
  }
  return dst_is_address != 0U && src_reg == reg && dst_reg == reg;
}

static int add_signed_offset_local(uint32_t base, int32_t offset, uint32_t limit, uint32_t *out_value) {
  int64_t value;
  if (out_value == NULL) return 0;
  value = (int64_t)base + (int64_t)offset;
  if (value < 0 || (uint64_t)value >= (uint64_t)limit) return 0;
  *out_value = (uint32_t)value;
  return 1;
}

static int instruction_matches_offset_table_load(const M68kInstructionIR *instruction, uint8_t base_reg,
    uint8_t index_reg, uint8_t index_is_address, int32_t *out_table_base_offset) {
  uint8_t dest_is_address, dest_reg;
  uint8_t source_base_reg, source_index_is_address, source_index_reg;
  int32_t source_disp;
  if (instruction == NULL || out_table_base_offset == NULL ||
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE ||
      instruction->size_suffix != 'w' || instruction->operand_count != 2U) {
    return 0;
  }
  if (!sim_operand_direct_register_local(&instruction->operands[1], &dest_is_address, &dest_reg) ||
      dest_is_address != 0U || dest_reg != index_reg) {
    return 0;
  }
  if (!operand_is_brief_indexed_an(&instruction->operands[0], &source_base_reg, &source_index_is_address,
        &source_index_reg, &source_disp)) {
    return 0;
  }
  if (source_base_reg != base_reg || source_index_is_address != index_is_address || source_index_reg != index_reg) return 0;
  *out_table_base_offset = source_disp;
  return 1;
}

static int instruction_matches_pc_relative_lea(const M68kInstructionIR *instruction, uint32_t instruction_offset,
    const M68kSection *section, const M68kPresentationPolicy *presentation, uint8_t base_reg, uint32_t *out_target) {
  const M68kSimFormMetadata *metadata;
  uint8_t dest_is_address;
  uint8_t dest_reg;
  uint32_t target;
  (void)presentation;
  if (instruction == NULL || section == NULL || out_target == NULL ||
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA ||
      instruction->operand_count != 2U) {
    return 0;
  }
  if (!sim_operand_direct_register_local(&instruction->operands[1], &dest_is_address, &dest_reg) ||
      dest_is_address == 0U || dest_reg != base_reg) {
    return 0;
  }
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL || metadata->source_operand_index >= instruction->operand_count) return 0;
  if (!instruction_render_operand_target(instruction, metadata, metadata->source_operand_index, instruction_offset,
        section->data_size, &target)) {
    return 0;
  }
  *out_target = target;
  return 1;
}

static int instruction_matches_pc_indexed_lea(const M68kInstructionIR *instruction, uint32_t instruction_offset,
    const M68kSection *section, const M68kPresentationPolicy *presentation, uint8_t base_reg,
    uint8_t *out_index_is_address, uint8_t *out_index_reg, uint8_t *out_index_long, uint8_t *out_index_scale,
    uint32_t *out_target) {
  const M68kSimFormMetadata *metadata;
  const M68kOperandIR *source_operand;
  uint8_t dest_is_address;
  uint8_t dest_reg;
  uint8_t pc_bias;
  uint32_t target;
  (void)presentation;
  if (instruction == NULL || section == NULL || out_target == NULL ||
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA ||
      instruction->operand_count != 2U) {
    return 0;
  }
  if (!sim_operand_direct_register_local(&instruction->operands[1], &dest_is_address, &dest_reg) ||
      dest_is_address == 0U || dest_reg != base_reg) {
    return 0;
  }
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL || metadata->source_operand_index >= instruction->operand_count) return 0;
  source_operand = &instruction->operands[metadata->source_operand_index];
  if (source_operand->kind != M68K_ASM_OPERAND_EA || source_operand->value.ea_mode != 7U || source_operand->value.ea_reg != 3U)
    return 0;
  pc_bias = metadata->operand_ea_pc_base_bias_bytes[metadata->source_operand_index] != 0U
    ? metadata->operand_ea_pc_base_bias_bytes[metadata->source_operand_index]
    : 2U;
  target = (uint32_t)((int32_t)instruction_offset + (int32_t)pc_bias + (int32_t)source_operand->value.value);
  if (target >= section->data_size) return 0;
  if (out_index_is_address != NULL) *out_index_is_address = source_operand->value.index_is_address;
  if (out_index_reg != NULL) *out_index_reg = source_operand->value.index_reg;
  if (out_index_long != NULL) *out_index_long = source_operand->value.index_long;
  if (out_index_scale != NULL) *out_index_scale = source_operand->value.scale;
  *out_target = target;
  return 1;
}

static int instruction_pc_relative_lea_target(const M68kInstructionIR *instruction, uint32_t instruction_offset,
    const M68kSection *section, uint8_t *out_dest_reg, uint32_t *out_target) {
  const M68kSimFormMetadata *metadata;
  uint8_t dest_is_address;
  uint8_t dest_reg;
  uint32_t target;
  if (instruction == NULL || section == NULL || out_dest_reg == NULL || out_target == NULL ||
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA || instruction->operand_count != 2U) {
    return 0;
  }
  if (!sim_operand_direct_register_local(&instruction->operands[1], &dest_is_address, &dest_reg) ||
      dest_is_address == 0U) {
    return 0;
  }
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL || metadata->source_operand_index >= instruction->operand_count) return 0;
  if (!instruction_render_operand_target(instruction, metadata, metadata->source_operand_index, instruction_offset,
        section->data_size, &target)) {
    return 0;
  }
  *out_dest_reg = dest_reg;
  *out_target = target;
  return 1;
}

static int brief_indexed_pc_base_target(const M68kInstructionIR *instruction, uint8_t operand_index,
    uint32_t instruction_offset, uint32_t section_size, uint32_t *out_target) {
  const M68kSimFormMetadata *metadata;
  uint8_t index_is_address, index_reg, index_long, index_scale;
  uint8_t pc_bias;
  int32_t disp;
  int64_t target;
  if (instruction == NULL || out_target == NULL || operand_index >= instruction->operand_count) return 0;
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL) return 0;
  if (!operand_is_brief_indexed_pc(&instruction->operands[operand_index], &index_is_address, &index_reg, &index_long,
        &index_scale, &disp)) {
    return 0;
  }
  pc_bias = metadata->operand_ea_pc_base_bias_bytes[operand_index] != 0U
    ? metadata->operand_ea_pc_base_bias_bytes[operand_index]
    : 2U;
  target = (int64_t)instruction_offset + (int64_t)pc_bias + (int64_t)disp;
  if (target < 0 || (uint64_t)target >= (uint64_t)section_size) return 0;
  *out_target = (uint32_t)target;
  return 1;
}

static int instruction_matches_pc_relative_word_table_load(const M68kInstructionIR *instruction,
    uint32_t instruction_offset, const M68kSection *section, uint8_t dest_reg, uint8_t *out_source_index_reg,
    uint32_t *out_base_target) {
  uint8_t dest_is_address, direct_dest_reg;
  uint8_t index_is_address, index_reg, index_long, index_scale;
  int32_t disp;
  uint32_t base_target;
  if (instruction == NULL || section == NULL || out_base_target == NULL ||
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || instruction->size_suffix != 'w' ||
      instruction->operand_count != 2U) {
    return 0;
  }
  if (!sim_operand_direct_register_local(&instruction->operands[1], &dest_is_address, &direct_dest_reg) ||
      dest_is_address != 0U || direct_dest_reg != dest_reg) {
    return 0;
  }
  if (!operand_is_brief_indexed_pc(&instruction->operands[0], &index_is_address, &index_reg, &index_long, &index_scale,
        &disp) || index_is_address != 0U) {
    return 0;
  }
  if (!brief_indexed_pc_base_target(instruction, 0U, instruction_offset, (uint32_t)section->data_size, &base_target)) return 0;
  if (out_source_index_reg != NULL) *out_source_index_reg = index_reg;
  *out_base_target = base_target;
  return 1;
}

int instruction_writes_data_reg_approx(const M68kInstructionIR *instruction, uint8_t reg) {
  uint8_t dest_is_address;
  uint8_t dest_reg;
  uint8_t mnemonic_id;
  if (instruction == NULL) return 0;
  if (instruction->operand_count == 0U) return 0;
  if (!sim_operand_direct_register_local(&instruction->operands[instruction->operand_count - 1U], &dest_is_address, &dest_reg) ||
      dest_is_address != 0U || dest_reg != reg) {
    return 0;
  }
  mnemonic_id = instruction->mnemonic_id;
  if (instruction_is_compare_or_test_like_local(mnemonic_id)) return 0;
  return 1;
}

static int find_recent_pc_relative_word_dispatch_seed(const M68kInstructionIR *instruction, uint32_t instruction_offset,
    const M68kSection *section, const RecentInstructionWindow *recent_window, uint32_t *out_base_target) {
  const M68kSimFormMetadata *metadata;
  uint8_t index_is_address, index_reg, index_long, index_scale;
  int32_t target_disp;
  uint32_t base_target;
  size_t index;
  if (instruction == NULL || section == NULL || recent_window == NULL || out_base_target == NULL) return 0;
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL || metadata->target_operand_index >= instruction->operand_count) return 0;
  if (!operand_is_brief_indexed_pc(&instruction->operands[metadata->target_operand_index], &index_is_address, &index_reg,
        &index_long, &index_scale, &target_disp) ||
      index_is_address != 0U ||
      !brief_indexed_pc_base_target(instruction, metadata->target_operand_index, instruction_offset,
        (uint32_t)section->data_size, &base_target)) {
    return 0;
  }
  for (index = 0U; index < RECENT_INSTRUCTION_WINDOW_SIZE; ++index) {
    uint32_t candidate_base_target;
    if (recent_window->valid[index] == 0U) continue;
    if (instruction_matches_pc_relative_word_table_load(&recent_window->instructions[index],
          recent_window->instruction_offsets[index], section,
          index_reg, NULL, &candidate_base_target) &&
        candidate_base_target == base_target) {
      *out_base_target = base_target;
      return 1;
    }
    if (instruction_writes_data_reg_approx(&recent_window->instructions[index], index_reg)) return 0;
  }
  return 0;
}

static void annotate_platform_symbol_refs(const SectionAnalysisContext *ctx, const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, M68kInstructionIR *instruction) {
  const M68kOperandIR *target_operand = NULL;
  PlatformResolvedIndirectInfo info;
  M68kOperandIR *operand;
  size_t operand_index;
  uint8_t mnemonic_id;
  platform_resolved_indirect_info_init(&info);
  if (instruction == NULL) return;
  mnemonic_id = instruction->mnemonic_id;
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    int16_t displacement;
    operand = &instruction->operands[operand_index];
    if (!operand_is_app_base_disp_ea(operand, 6U, &displacement)) continue;
    {
      uint8_t dest_reg;
      const M68kOperandIR *source = NULL;
      int treat_as_value = 1;
      if (operand_index == 0U && mnemonic_id == M68K_ASM_MNEMONIC_LEA) {
        treat_as_value = 0;
      } else if (operand_index == 0U && mnemonic_id == M68K_ASM_MNEMONIC_PEA) {
        treat_as_value = 0;
      } else if (instruction_is_address_move(instruction, &dest_reg, &source) && source == operand) {
        treat_as_value = 0;
      }
      if (!platform_resolve_app_base_slot_symbol_ref(ctx, section_analysis, displacement, treat_as_value,
            &operand->symbol_ref)) {
        continue;
      }
    }
    operand->symbol_ref.name_is_generated = 0U;
    operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
    operand->symbol_ref.addend = 0;
  }
  platform_annotate_instruction_symbol_refs(ctx, section_analysis, offset, instruction);
  info = platform_resolve_indirect_control(ctx, section_analysis, offset, instruction);
  if (info.kind == PLATFORM_RESOLVED_INDIRECT_NONE) return;
  if (info.has_symbol_name == 0U || info.symbol_name[0] == '\0') return;
  if (!instruction_target_operand_local(instruction, &target_operand) || target_operand == NULL) return;
  operand = &instruction->operands[(size_t)(target_operand - instruction->operands)];
  operand->symbol_ref.has_name = 1U;
  operand->symbol_ref.name_is_generated = 0U;
  if (ctx != NULL && section_analysis_context_object(ctx) != NULL) {
    if (section_analysis_context_object(ctx)->platform_backend_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK)
      operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
    else if (section_analysis_context_object(ctx)->platform_backend_kind == M68K_PLATFORM_BACKEND_ATARI_ST)
      operand->symbol_ref.name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_ATARI_ST;
  }
  operand->symbol_ref.kind = M68K_IR_SYMBOL_REF_NONE;
  operand->symbol_ref.addend = 0;
  snprintf(operand->symbol_ref.name, sizeof(operand->symbol_ref.name), "%s", info.symbol_name);
}

static int recover_string_dispatch_targets_from_decoder_call(const SectionAnalysisContext *ctx,
    M68kSectionAnalysisIR *section_analysis, const M68kInstructionIR *instruction, uint32_t dispatch_site,
    const RecentInstructionWindow *recent_window, M68kSimTargetSet *out_targets) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  uint8_t target_reg;
  uint32_t decoder_entry = UINT32_MAX;
  uint32_t table_base = UINT32_MAX;
  uint32_t table_end = UINT32_MAX;
  uint32_t lea_targets[8];
  uint8_t lea_target_known[8];
  uint8_t saw_skip = 0U;
  uint8_t saw_target_calc = 0U;
  uint8_t end_reg = 0xFFu;
  uint32_t cursor;
  size_t step_count = 0U;
  if (section == NULL || section_analysis == NULL || instruction == NULL || recent_window == NULL) return 0;
  if (instruction->operand_count == 0U || !operand_is_indirect_an(&instruction->operands[0], &target_reg))
    return 0;
  if (!find_recent_string_dispatch_decoder_call(ctx, recent_window, target_reg, &decoder_entry))
    return 0;
  memset(lea_targets, 0, sizeof(lea_targets));
  memset(lea_target_known, 0, sizeof(lea_target_known));
  for (cursor = decoder_entry; cursor < section->data_size && step_count < 256U; ++step_count) {
    SectionDecodeResult decode;
    M68kInstructionIR sub_instruction;
    uint32_t lea_target;
    uint8_t lea_dest_reg;
    if (table_base != UINT32_MAX && cursor >= table_base) break;
    if (!section_analysis_context_decode(ctx, cursor, NULL, &decode) || decode.instruction.byte_count == 0U)
      return 0;
    sub_instruction = decode.instruction;
    if (instruction_pc_relative_lea_target(&sub_instruction, cursor, section, &lea_dest_reg, &lea_target)) {
      lea_targets[lea_dest_reg] = lea_target;
      lea_target_known[lea_dest_reg] = 1U;
      if (lea_dest_reg == target_reg && table_base == UINT32_MAX) table_base = lea_target;
      if (end_reg != 0xFFu && lea_dest_reg == end_reg) table_end = lea_target;
    }
    {
      uint8_t base_reg;
      uint8_t index_reg;
      int32_t disp;
      if (instruction_matches_indexed_an_lea(&sub_instruction, target_reg, &base_reg, &index_reg, &disp)) {
        if (base_reg == target_reg && disp == 2) saw_skip = 1U;
        else if (disp == -2) saw_target_calc = 1U;
      }
    }
    if (sub_instruction.mnemonic_id == M68K_ASM_MNEMONIC_CMPA &&
        sub_instruction.operand_count == 2U) {
      uint8_t lhs_is_address, lhs_reg, rhs_is_address, rhs_reg;
      if (sim_operand_direct_register_local(&sub_instruction.operands[0], &lhs_is_address, &lhs_reg) &&
          sim_operand_direct_register_local(&sub_instruction.operands[1], &rhs_is_address, &rhs_reg) &&
          lhs_is_address != 0U && rhs_is_address != 0U && rhs_reg == target_reg) {
        end_reg = lhs_reg;
        if (lhs_reg < 8U && lea_target_known[lhs_reg] != 0U) table_end = lea_targets[lhs_reg];
      }
    }
    cursor += (uint32_t)sub_instruction.byte_count;
  }
  if (table_base == UINT32_MAX || table_end == UINT32_MAX || table_end <= table_base || !saw_skip || !saw_target_calc)
    return 0;
  {
    uint32_t pos = table_base;
    uint32_t entry_offsets[128];
    uint32_t offset_offsets[128];
    uint32_t targets[128];
    size_t entry_count = 0U;
    while (pos < table_end && entry_count < 128U) {
      uint8_t name_len = section->data[pos];
      uint32_t next_pos;
      uint32_t offset_pos;
      int16_t rel;
      uint32_t target;
      if (name_len == 0U) break;
      next_pos = pos + 1U + (uint32_t)name_len + 2U;
      if (next_pos > table_end || next_pos > section->data_size) break;
      offset_pos = pos + 1U + (uint32_t)name_len;
      rel = (int16_t)m68k_read_u16be(section->data + offset_pos);
      target = (uint32_t)((int32_t)offset_pos + (int32_t)rel);
      if (analysis_has_code_start_at(section_analysis, target) || offset_decodes_as_instruction(ctx, target)) {
        entry_offsets[entry_count] = pos;
        offset_offsets[entry_count] = offset_pos;
        targets[entry_count] = target;
        if (out_targets != NULL && m68k_sim_target_set_add(out_targets, target) == 0) return 0;
        entry_count += 1U;
      }
      pos = next_pos;
    }
    if (entry_count >= 2U) {
      M68kRecoveredStringDispatchIR dispatch;
      memset(&dispatch, 0, sizeof(dispatch));
      dispatch.table_base = table_base;
      dispatch.table_end = table_end;
      dispatch.dispatch_site = dispatch_site;
      dispatch.decoder_entry = decoder_entry;
      dispatch.entry_count = entry_count;
      dispatch.entry_offsets = entry_offsets;
      dispatch.offset_offsets = offset_offsets;
      dispatch.targets = targets;
      if (m68k_ir_section_analysis_append_recovered_string_dispatch(section_analysis, &dispatch) != 0) return 0;
      return 1;
    }
  }
  return 0;
}

static int offset_decodes_as_instruction(const SectionAnalysisContext *ctx, uint32_t target) {
  SectionDecodeResult decode;
  if (ctx == NULL || ctx->section == NULL || target >= ctx->section->data_size) return 0;
  return section_analysis_context_decode(ctx, target, NULL, &decode);
}

static uint8_t speculative_platform_max_cpu(const SectionAnalysisContext *ctx) {
  const M68kObject *object = section_analysis_context_object(ctx);
  if (object != NULL && object->platform_file_kind == M68K_PLATFORM_FILE_EXECUTABLE) {
    switch (object->platform_backend_kind) {
    case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    case M68K_PLATFORM_BACKEND_ATARI_ST:
      return M68K_ASM_CPU_68000;
    default:
      break;
    }
  }
  return effective_analysis_max_cpu(ctx != NULL ? ctx->analysis_policy : NULL);
}

static int offset_decodes_as_speculative_platform_instruction(const SectionAnalysisContext *ctx, uint32_t target) {
  if (section_analysis_context_backend_kind(ctx) != M68K_PLATFORM_BACKEND_ATARI_ST) return offset_decodes_as_instruction(ctx, target);
  uint32_t cursor = target;
  uint32_t byte_budget = 16U;
  uint32_t step_budget = 6U;
  if (ctx == NULL || ctx->section == NULL || target >= ctx->section->data_size) return 0;
  while (step_budget-- != 0U && cursor < ctx->section->data_size && byte_budget != 0U) {
    SectionDecodeResult decode;
    uint32_t byte_count;
    if (!section_analysis_context_decode(ctx, cursor, NULL, &decode)) return 0;
    if (instruction_required_cpu(&decode.instruction) > speculative_platform_max_cpu(ctx)) return 0;
    byte_count = (uint32_t)decode.instruction.byte_count;
    if (byte_count == 0U || byte_count > byte_budget) return 0;
    if (!instruction_roundtrips_exact_bytes(&decode.instruction, ctx->section->data + cursor,
          (size_t)decode.instruction.byte_count)) {
      return 0;
    }
    if (decode.stops_fallthrough != 0U) return 1;
    cursor += byte_count;
    byte_budget -= byte_count;
  }
  return 1;
}

static int analysis_has_code_start_at(const M68kSectionAnalysisIR *section_analysis, uint32_t target_offset) {
  return section_analysis != NULL && section_analysis->certain_code_start != NULL &&
    target_offset < section_analysis->section_size && section_analysis->certain_code_start[target_offset] != 0U;
}

static uint32_t limit_scan_to_next_code_start(const uint8_t *is_code_start, size_t size,
    uint32_t table_base, uint32_t max_scan) {
  uint32_t offset;
  if (is_code_start == NULL || table_base >= size) return max_scan;
  for (offset = table_base + 2U; offset < size; ++offset) {
    uint32_t distance = offset - table_base;
    if (distance >= max_scan) break;
    if (is_code_start[offset] != 0U) return distance;
  }
  return max_scan;
}

static int dispatch_target_overlaps_scanned_table(uint32_t table_base, uint32_t scanned_bytes, uint32_t target) {
  return target >= table_base && target < table_base + scanned_bytes;
}

typedef enum RecoveredWordDispatchPattern {
  RECOVERED_WORD_DISPATCH_BRIEF_OFFSET = 1,
  RECOVERED_WORD_DISPATCH_ENTRY_RELATIVE = 2,
  RECOVERED_WORD_DISPATCH_PC_RELATIVE = 3,
} RecoveredWordDispatchPattern;

#define WORD_DISPATCH_MAX_SCAN_BYTES 512U
#define WORD_DISPATCH_MAX_SLOTS (WORD_DISPATCH_MAX_SCAN_BYTES / 2U)
#define WORD_DISPATCH_INVALID_RUN_LIMIT 4

typedef struct RecoveredWordDispatchSeed {
  RecoveredWordDispatchPattern pattern;
  uint32_t table_base;
  uint32_t base_target;
  uint32_t max_scan;
  uint32_t target_window_slack;
  uint8_t relative_to_slot;
  uint8_t preserve_zero_slots;
} RecoveredWordDispatchSeed;

struct RecoveredWordDispatchTable {
  RecoveredWordDispatchPattern pattern;
  uint32_t table_base;
  uint32_t base_target;
  uint32_t scanned_bytes;
  uint32_t slot_count;
  uint8_t relative_to_slot;
  uint8_t preserve_zero_slots;
  uint8_t found;
  int16_t entry_words[WORD_DISPATCH_MAX_SLOTS];
  uint32_t targets[WORD_DISPATCH_MAX_SLOTS];
  uint8_t target_valid[WORD_DISPATCH_MAX_SLOTS];
};

typedef int (*RecoveredWordDispatchResolveFn)(const void *ctx, uint32_t slot_offset, int16_t entry_word,
    uint32_t *out_target);
typedef int (*RecoveredWordDispatchAcceptFn)(const void *ctx, uint32_t target);

typedef struct RecoveredWordDispatchScanConfig {
  const M68kSection *section;
  const RecoveredWordDispatchSeed *seed;
  RecoveredWordDispatchResolveFn resolve_target;
  const void *resolve_ctx;
  RecoveredWordDispatchAcceptFn accept_target;
  const void *accept_ctx;
} RecoveredWordDispatchScanConfig;

typedef struct AnalysisDispatchTargetAcceptContext {
  const SectionAnalysisContext *analysis_ctx;
  const SectionDiscoveryMap *discovery;
} AnalysisDispatchTargetAcceptContext;

typedef struct AnalysisWordOffsetAcceptContext {
  const AnalysisDispatchTargetAcceptContext *target_ctx;
  uint32_t base_target;
} AnalysisWordOffsetAcceptContext;

typedef struct RenderWordTargetAcceptContext {
  const M68kSectionAnalysisIR *section_analysis;
} RenderWordTargetAcceptContext;

static uint32_t clamp_word_dispatch_scan_bytes(const M68kSection *section, uint32_t table_base) {
  uint32_t max_scan;
  if (section == NULL || table_base >= section->data_size) return 0U;
  max_scan = section->data_size - table_base;
  if (max_scan > WORD_DISPATCH_MAX_SCAN_BYTES) max_scan = WORD_DISPATCH_MAX_SCAN_BYTES;
  return max_scan;
}

static int analysis_accept_dispatch_target(const void *user_ctx, uint32_t target) {
  const AnalysisDispatchTargetAcceptContext *ctx = (const AnalysisDispatchTargetAcceptContext *)user_ctx;
  if (ctx == NULL || ctx->analysis_ctx == NULL || ctx->discovery == NULL || target >= ctx->discovery->size) return 0;
  if (ctx->discovery->is_code_start != NULL && ctx->discovery->is_code_start[target] != 0U) return 1;
  return offset_decodes_as_speculative_platform_instruction(ctx->analysis_ctx, target);
}

static int analysis_accept_word_offset_dispatch_target(const void *user_ctx, uint32_t target) {
  const AnalysisWordOffsetAcceptContext *ctx = (const AnalysisWordOffsetAcceptContext *)user_ctx;
  if (ctx == NULL || ctx->target_ctx == NULL || target == ctx->base_target) return 0;
  return analysis_accept_dispatch_target(ctx->target_ctx, target);
}

static int render_accept_dispatch_target(const void *user_ctx, uint32_t target) {
  const RenderWordTargetAcceptContext *ctx = (const RenderWordTargetAcceptContext *)user_ctx;
  return ctx != NULL && analysis_has_code_start_at(ctx->section_analysis, target);
}

static int resolve_entry_relative_dispatch_target(const void *user_ctx, uint32_t slot_offset, int16_t entry_word,
    uint32_t *out_target) {
  const M68kSection *section = (const M68kSection *)user_ctx;
  int64_t candidate;
  if (section == NULL || out_target == NULL) return 0;
  candidate = (int64_t)slot_offset + (int64_t)entry_word;
  if (candidate < 0 || (uint64_t)candidate >= (uint64_t)section->data_size) return 0;
  *out_target = (uint32_t)candidate;
  return 1;
}

int instruction_writes_address_reg_approx(const M68kInstructionIR *instruction, uint8_t reg) {
  uint8_t dest_is_address;
  uint8_t dest_reg;
  uint8_t mnemonic_id;
  if (instruction == NULL) return 0;
  if (instruction->operand_count == 0U) return 0;
  if (!sim_operand_direct_register_local(&instruction->operands[instruction->operand_count - 1U], &dest_is_address, &dest_reg) ||
      dest_is_address == 0U || dest_reg != reg) {
    return 0;
  }
  mnemonic_id = instruction->mnemonic_id;
  if (instruction_is_compare_like_address_write_local(mnemonic_id)) return 0;
  return 1;
}

static int find_recent_string_dispatch_decoder_call(const SectionAnalysisContext *ctx, const RecentInstructionWindow *recent_window,
    uint8_t target_reg, uint32_t *out_decoder_entry) {
  size_t call_index;
  if (ctx == NULL || recent_window == NULL || out_decoder_entry == NULL) return 0;
  for (call_index = 0U; call_index < RECENT_INSTRUCTION_WINDOW_SIZE; ++call_index) {
    size_t guard_index;
    if (recent_window->valid[call_index] == 0U) continue;
    if (!instruction_is_call_transfer(&recent_window->instructions[call_index])) continue;
    if (!instruction_direct_target_local(ctx, &recent_window->instructions[call_index],
          recent_window->instruction_offsets[call_index], out_decoder_entry)) {
      continue;
    }
    for (guard_index = 0U; guard_index < call_index; ++guard_index) {
      if (recent_window->valid[guard_index] == 0U) continue;
      if (instruction_writes_address_reg_approx(&recent_window->instructions[guard_index], target_reg)) break;
    }
    if (guard_index == call_index) return 1;
  }
  return 0;
}

static int resolve_word_offset_dispatch_target(const void *user_ctx, uint32_t slot_offset, int16_t entry_word,
    uint32_t *out_target) {
  const uint32_t *base_target = (const uint32_t *)user_ctx;
  const int32_t base = base_target != NULL ? (int32_t)(*base_target) : 0;
  (void)slot_offset;
  if (base_target == NULL || out_target == NULL) return 0;
  *out_target = (uint32_t)(base + (int32_t)entry_word);
  return 1;
}

static int scan_recovered_word_dispatch_table(const RecoveredWordDispatchScanConfig *config,
    RecoveredWordDispatchTable *out_table) {
  uint32_t cursor;
  uint32_t min_target = 0U;
  uint32_t max_target = 0U;
  uint8_t found = 0U;
  uint32_t invalid_run = 0U;
  if (config == NULL || config->section == NULL || config->seed == NULL || config->resolve_target == NULL ||
      config->accept_target == NULL || out_table == NULL) {
    return 0;
  }
  if (config->seed->max_scan == 0U || config->seed->table_base >= config->section->data_size) return 0;
  memset(out_table, 0, sizeof(*out_table));
  out_table->pattern = config->seed->pattern;
  out_table->table_base = config->seed->table_base;
  out_table->base_target = config->seed->base_target;
  out_table->relative_to_slot = config->seed->relative_to_slot;
  out_table->preserve_zero_slots = config->seed->preserve_zero_slots;
  for (cursor = 0U; cursor + 2U <= config->seed->max_scan && out_table->slot_count < WORD_DISPATCH_MAX_SLOTS; cursor += 2U) {
    uint32_t slot_offset = config->seed->table_base + cursor;
    int16_t entry_word = (int16_t)m68k_read_u16be(config->section->data + slot_offset);
    uint32_t target = 0U;
    int accepted = 0;
    if (config->resolve_target(config->resolve_ctx, slot_offset, entry_word, &target) &&
        !dispatch_target_overlaps_scanned_table(config->seed->table_base, cursor + 2U, target) &&
        (!found ||
          ((target + config->seed->target_window_slack >= min_target) &&
            (target <= max_target + config->seed->target_window_slack))) &&
        config->accept_target(config->accept_ctx, target)) {
      accepted = 1;
    }
    if (!accepted && found && invalid_run + 1U >= WORD_DISPATCH_INVALID_RUN_LIMIT) break;
    out_table->entry_words[out_table->slot_count] = entry_word;
    if (accepted) {
      out_table->targets[out_table->slot_count] = target;
      out_table->target_valid[out_table->slot_count] = 1U;
      if (!found || target < min_target) min_target = target;
      if (!found || target > max_target) max_target = target;
      found = 1U;
      invalid_run = 0U;
    } else if (found) {
      invalid_run += 1U;
    }
    out_table->slot_count += 1U;
  }
  out_table->scanned_bytes = out_table->slot_count * 2U;
  out_table->found = found;
  return found != 0U;
}

static void recovered_word_dispatch_targets_to_set(const RecoveredWordDispatchTable *table,
    M68kSimTargetSet *out_targets) {
  uint32_t slot_index;
  if (table == NULL || out_targets == NULL) return;
  for (slot_index = 0U; slot_index < table->slot_count; ++slot_index) {
    if (table->target_valid[slot_index] == 0U) continue;
    m68k_sim_target_set_add(out_targets, table->targets[slot_index]);
  }
}

static int emit_recovered_word_dispatch_exprs(const RecoveredWordDispatchTable *table, const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, GeneratedLabelKind *label_kinds, size_t label_kind_count,
    uint8_t *generated_label_flags, const M68kPresentationPolicy *presentation, Arena *scratch_arena,
    char **out_word_exprs) {
  uint32_t slot_index;
  if (table == NULL || ctx == NULL || section_analysis == NULL || generated_label_flags == NULL || scratch_arena == NULL ||
      out_word_exprs == NULL) {
    return -1;
  }
  for (slot_index = 0U; slot_index < table->slot_count; ++slot_index) {
    char expr[80];
    uint32_t slot_offset = table->table_base + slot_index * 2U;
    if (table->entry_words[slot_index] == 0 && table->preserve_zero_slots != 0U) {
      if (build_literal_word_expr(expr, sizeof(expr), 0U) != 0) return -1;
      if (set_word_expr_slot(scratch_arena, out_word_exprs, slot_offset, expr) != 0) return -1;
      continue;
    }
    if (table->target_valid[slot_index] == 0U) continue;
    if (table->relative_to_slot != 0U) {
      if (build_relative_word_expr_here(expr, sizeof(expr), ctx, slot_offset, table->targets[slot_index], label_kinds,
            label_kind_count, section_analysis, generated_label_flags, presentation) != 0) {
        return -1;
      }
    } else {
      if (build_relative_word_expr(expr, sizeof(expr), ctx, table->base_target, table->targets[slot_index], label_kinds,
            label_kind_count, section_analysis, generated_label_flags, presentation) != 0) {
        return -1;
      }
    }
    if (set_word_expr_slot(scratch_arena, out_word_exprs, slot_offset, expr) != 0) return -1;
  }
  return 0;
}

static int append_recovered_word_dispatch_table(M68kSectionAnalysisIR *section_analysis,
    const RecoveredWordDispatchTable *table) {
  M68kRecoveredWordDispatchIR copy;
  if (section_analysis == NULL || table == NULL || table->found == 0U) return 0;
  memset(&copy, 0, sizeof(copy));
  copy.pattern = (uint8_t)table->pattern;
  copy.relative_to_slot = table->relative_to_slot;
  copy.preserve_zero_slots = table->preserve_zero_slots;
  copy.table_base = table->table_base;
  copy.base_target = table->base_target;
  copy.scanned_bytes = table->scanned_bytes;
  copy.slot_count = table->slot_count;
  copy.entry_words = (int16_t *)table->entry_words;
  copy.targets = (uint32_t *)table->targets;
  copy.target_valid = (uint8_t *)table->target_valid;
  return m68k_ir_section_analysis_append_recovered_word_dispatch(section_analysis, &copy);
}

static int recover_entry_relative_word_dispatch_seed(const SectionDiscoveryMap *discovery,
    const M68kInstructionIR *instruction, const M68kInstructionIR *prev_instruction,
    const M68kInstructionIR *prev_prev_instruction, uint32_t prev_prev_offset, const SectionAnalysisContext *ctx,
    RecoveredWordDispatchSeed *out_seed) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  const M68kSimFormMetadata *metadata;
  const M68kOperandIR *target_operand;
  uint8_t base_reg, index_is_address, index_reg, index_long, index_scale;
  uint32_t table_base;
  uint32_t max_scan;
  if (section == NULL || discovery == NULL || instruction == NULL || prev_instruction == NULL ||
      prev_prev_instruction == NULL || out_seed == NULL) {
    return 0;
  }
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL || metadata->target_operand_index >= instruction->operand_count) return 0;
  target_operand = &instruction->operands[metadata->target_operand_index];
  if (!operand_is_indirect_an(target_operand, &base_reg) ||
      !instruction_is_adda_word_indirect_self(prev_instruction, base_reg) ||
      !instruction_matches_pc_indexed_lea(prev_prev_instruction, prev_prev_offset, section, NULL, base_reg,
        &index_is_address, &index_reg, &index_long, &index_scale, &table_base)) {
    return 0;
  }
  if (index_is_address != 0U || index_long != 0U || index_scale != 0U || table_base >= section->data_size) return 0;
  (void)index_reg;
  max_scan = clamp_word_dispatch_scan_bytes(section, table_base);
  max_scan = limit_scan_to_next_code_start(discovery->is_code_start, discovery->size, table_base, max_scan);
  memset(out_seed, 0, sizeof(*out_seed));
  out_seed->pattern = RECOVERED_WORD_DISPATCH_ENTRY_RELATIVE;
  out_seed->table_base = table_base;
  out_seed->base_target = table_base;
  out_seed->max_scan = max_scan;
  out_seed->target_window_slack = 2048U;
  out_seed->relative_to_slot = 1U;
  return 1;
}

static int recover_brief_word_offset_dispatch_seed(const M68kInstructionIR *instruction,
    const M68kInstructionIR *prev_instruction, const M68kInstructionIR *prev_prev_instruction,
    const M68kInstructionIR *prev_prev_prev_instruction, uint32_t prev_prev_prev_offset,
    const SectionAnalysisContext *ctx, const M68kPresentationPolicy *presentation,
    RecoveredWordDispatchSeed *out_seed) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  const M68kSimFormMetadata *metadata;
  const M68kOperandIR *target_operand;
  uint8_t target_base_reg, target_index_is_address, target_index_reg;
  int32_t table_offset;
  uint32_t base_target;
  uint32_t table_base;
  int32_t target_disp;
  if (section == NULL || instruction == NULL || prev_instruction == NULL || prev_prev_instruction == NULL ||
      prev_prev_prev_instruction == NULL || out_seed == NULL) {
    return 0;
  }
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL || metadata->target_operand_index >= instruction->operand_count) return 0;
  target_operand = &instruction->operands[metadata->target_operand_index];
  if (!operand_is_brief_indexed_an(target_operand, &target_base_reg, &target_index_is_address, &target_index_reg,
        &target_disp) ||
      target_disp != 0 || target_index_is_address != 0U) {
    return 0;
  }
  if (!instruction_matches_offset_table_load(prev_instruction, target_base_reg, target_index_reg,
        target_index_is_address, &table_offset) ||
      !instruction_is_add_word_self(prev_prev_instruction, target_index_reg) ||
      !instruction_matches_pc_relative_lea(prev_prev_prev_instruction, prev_prev_prev_offset, section, presentation,
        target_base_reg, &base_target)) {
    return 0;
  }
  if (base_target >= section->data_size ||
      !add_signed_offset_local(base_target, table_offset, (uint32_t)section->data_size, &table_base)) {
    return 0;
  }
  memset(out_seed, 0, sizeof(*out_seed));
  out_seed->pattern = RECOVERED_WORD_DISPATCH_BRIEF_OFFSET;
  out_seed->table_base = table_base;
  out_seed->base_target = base_target;
  out_seed->max_scan = clamp_word_dispatch_scan_bytes(section, table_base);
  out_seed->target_window_slack = (uint32_t)section->data_size;
  return 1;
}

static int recover_pc_relative_word_dispatch_seed(const M68kInstructionIR *instruction, uint32_t instruction_offset,
    const RecentInstructionWindow *recent_window, const SectionAnalysisContext *ctx, RecoveredWordDispatchSeed *out_seed) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  uint32_t table_base;
  if (section == NULL || recent_window == NULL || out_seed == NULL) return 0;
  if (!find_recent_pc_relative_word_dispatch_seed(instruction, instruction_offset, section, recent_window, &table_base)) return 0;
  memset(out_seed, 0, sizeof(*out_seed));
  out_seed->pattern = RECOVERED_WORD_DISPATCH_PC_RELATIVE;
  out_seed->table_base = table_base;
  out_seed->base_target = table_base;
  out_seed->max_scan = clamp_word_dispatch_scan_bytes(section, table_base);
  out_seed->target_window_slack = 2048U;
  out_seed->preserve_zero_slots = 1U;
  return 1;
}

typedef struct DispatchScanState {
  uint32_t table_base;
  uint32_t cursor;
  uint32_t target;
  int found;
  int invalid_run;
} DispatchScanState;

typedef int (*DispatchScanVisitFn)(const DispatchScanState *state, void *user_ctx);

static int dispatch_scan_word_entries(uint32_t max_scan, DispatchScanState *state, DispatchScanVisitFn visit,
    void *user_ctx) {
  if (state == NULL || visit == NULL) return 0;
  for (state->cursor = 0U; state->cursor + 2U <= max_scan; state->cursor += 2U) {
    int accepted = visit(state, user_ctx);
    if (accepted > 0) {
      state->found = 1;
      state->invalid_run = 0;
      continue;
    }
    if (accepted < 0) return -1;
    if (state->found != 0 && ++state->invalid_run >= 4) break;
  }
  return state->found;
}

typedef struct InlinePcDispatchVisitContext {
  const M68kSection *section;
  const SectionAnalysisContext *analysis_ctx;
  const SectionDiscoveryMap *discovery;
  M68kSimTargetSet *out_targets;
} InlinePcDispatchVisitContext;

static int visit_inline_pc_dispatch_target(const DispatchScanState *state, void *user_ctx) {
  InlinePcDispatchVisitContext *ctx = (InlinePcDispatchVisitContext *)user_ctx;
  SectionDecodeResult entry_decode;
  M68kInstructionIR entry_instruction;
  uint32_t entry_offset;
  uint32_t target;
  if (ctx == NULL || ctx->section == NULL || ctx->analysis_ctx == NULL || ctx->discovery == NULL) return -1;
  entry_offset = state->table_base + state->cursor;
  if (!section_analysis_context_decode(ctx->analysis_ctx, entry_offset, NULL, &entry_decode)) return 0;
  entry_instruction = entry_decode.instruction;
  if (entry_offset + entry_instruction.byte_count > ctx->section->data_size ||
      !instruction_is_unconditional_transfer(&entry_instruction) ||
      !(entry_decode.has_explicit_target && (target = entry_decode.explicit_target, 1)) ||
      ((ctx->discovery->is_code_start != NULL && ctx->discovery->is_code_start[target] == 0U) &&
        !offset_decodes_as_instruction(ctx->analysis_ctx, target))) {
    return 0;
  }
  m68k_sim_target_set_add(ctx->out_targets, entry_offset);
  return 1;
}

static int recover_entry_relative_word_dispatch_targets(const SectionDiscoveryMap *discovery,
    const M68kInstructionIR *instruction, const M68kInstructionIR *prev_instruction,
    const M68kInstructionIR *prev_prev_instruction, uint32_t prev_prev_offset, const SectionAnalysisContext *ctx,
    M68kSimTargetSet *out_targets) {
  RecoveredWordDispatchSeed seed;
  RecoveredWordDispatchTable table;
  AnalysisDispatchTargetAcceptContext accept_ctx;
  RecoveredWordDispatchScanConfig scan_config;
  if (ctx == NULL || ctx->section == NULL || discovery == NULL || out_targets == NULL) return 0;
  if (!recover_entry_relative_word_dispatch_seed(discovery, instruction, prev_instruction, prev_prev_instruction,
        prev_prev_offset, ctx, &seed)) {
    return 0;
  }
  memset(&accept_ctx, 0, sizeof(accept_ctx));
  accept_ctx.analysis_ctx = ctx;
  accept_ctx.discovery = discovery;
  memset(&scan_config, 0, sizeof(scan_config));
  scan_config.section = ctx->section;
  scan_config.seed = &seed;
  scan_config.resolve_target = resolve_entry_relative_dispatch_target;
  scan_config.resolve_ctx = ctx->section;
  scan_config.accept_target = analysis_accept_dispatch_target;
  scan_config.accept_ctx = &accept_ctx;
  if (!scan_recovered_word_dispatch_table(&scan_config, &table)) return 0;
  recovered_word_dispatch_targets_to_set(&table, out_targets);
  return 1;
}

static int recover_brief_word_offset_dispatch_targets(const SectionDiscoveryMap *discovery,
    const M68kInstructionIR *instruction, const M68kInstructionIR *prev_instruction,
    const M68kInstructionIR *prev_prev_instruction, const M68kInstructionIR *prev_prev_prev_instruction,
    uint32_t prev_prev_prev_offset, const SectionAnalysisContext *ctx, M68kSimTargetSet *out_targets) {
  RecoveredWordDispatchSeed seed;
  RecoveredWordDispatchTable table;
  AnalysisDispatchTargetAcceptContext target_ctx;
  AnalysisWordOffsetAcceptContext accept_ctx;
  RecoveredWordDispatchScanConfig scan_config;
  if (ctx == NULL || ctx->section == NULL || discovery == NULL || out_targets == NULL) return 0;
  if (!recover_brief_word_offset_dispatch_seed(instruction, prev_instruction, prev_prev_instruction,
        prev_prev_prev_instruction, prev_prev_prev_offset, ctx, NULL, &seed)) {
    return 0;
  }
  memset(&target_ctx, 0, sizeof(target_ctx));
  target_ctx.analysis_ctx = ctx;
  target_ctx.discovery = discovery;
  memset(&accept_ctx, 0, sizeof(accept_ctx));
  accept_ctx.target_ctx = &target_ctx;
  accept_ctx.base_target = seed.base_target;
  memset(&scan_config, 0, sizeof(scan_config));
  scan_config.section = ctx->section;
  scan_config.seed = &seed;
  scan_config.resolve_target = resolve_word_offset_dispatch_target;
  scan_config.resolve_ctx = &seed.base_target;
  scan_config.accept_target = analysis_accept_word_offset_dispatch_target;
  scan_config.accept_ctx = &accept_ctx;
  if (!scan_recovered_word_dispatch_table(&scan_config, &table)) return 0;
  recovered_word_dispatch_targets_to_set(&table, out_targets);
  return 1;
}

static int recover_pc_index_inline_dispatch_targets(const SectionDiscoveryMap *discovery,
    const M68kInstructionIR *instruction, uint32_t instruction_offset, const SectionAnalysisContext *ctx,
    M68kSimTargetSet *out_targets) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  InlinePcDispatchVisitContext visit_ctx;
  const M68kSimFormMetadata *metadata;
  const M68kOperandIR *target_operand;
  uint8_t index_is_address, index_reg, index_long, index_scale;
  int32_t target_disp;
  uint32_t table_base, max_scan;
  DispatchScanState scan_state;
  if (section == NULL || discovery == NULL || instruction == NULL || ctx == NULL || ctx->analysis_policy == NULL ||
      out_targets == NULL) return 0;
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL || metadata->target_operand_index >= instruction->operand_count) return 0;
  target_operand = &instruction->operands[metadata->target_operand_index];
  if (!operand_is_brief_indexed_pc(target_operand, &index_is_address, &index_reg, &index_long, &index_scale, &target_disp))
    return 0;
  if (!brief_indexed_pc_base_target(instruction, metadata->target_operand_index, instruction_offset,
        (uint32_t)section->data_size, &table_base)) return 0;
  if (table_base >= section->data_size) return 0;
  (void)index_is_address;
  (void)index_reg;
  (void)index_long;
  (void)index_scale;
  (void)target_disp;
  max_scan = section->data_size - table_base;
  if (max_scan > 512U) max_scan = 512U;
  memset(&scan_state, 0, sizeof(scan_state));
  scan_state.table_base = table_base;
  memset(&visit_ctx, 0, sizeof(visit_ctx));
  visit_ctx.section = section;
  visit_ctx.analysis_ctx = ctx;
  visit_ctx.discovery = discovery;
  visit_ctx.out_targets = out_targets;
  return dispatch_scan_word_entries(max_scan, &scan_state, visit_inline_pc_dispatch_target, &visit_ctx);
}

static int collect_pc_index_inline_dispatch_table(const SectionDiscoveryMap *discovery,
    const M68kInstructionIR *instruction, uint32_t instruction_offset, const SectionAnalysisContext *ctx,
    M68kSectionAnalysisIR *out_analysis) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  M68kRecoveredInlineDispatchIR dispatch;
  const M68kSimFormMetadata *metadata;
  const M68kOperandIR *target_operand;
  uint8_t index_is_address, index_reg, index_long, index_scale;
  int32_t target_disp;
  uint32_t table_base, max_scan, cursor;
  uint32_t entry_offsets[WORD_DISPATCH_MAX_SLOTS];
  uint32_t targets[WORD_DISPATCH_MAX_SLOTS];
  size_t entry_count = 0U;
  if (section == NULL || discovery == NULL || instruction == NULL || out_analysis == NULL) return 0;
  metadata = instruction_sim_metadata(instruction);
  if (metadata == NULL || metadata->target_operand_index >= instruction->operand_count) return 0;
  target_operand = &instruction->operands[metadata->target_operand_index];
  if (!operand_is_brief_indexed_pc(target_operand, &index_is_address, &index_reg, &index_long, &index_scale, &target_disp))
    return 0;
  if (!brief_indexed_pc_base_target(instruction, metadata->target_operand_index, instruction_offset,
        (uint32_t)section->data_size, &table_base) || table_base >= section->data_size) {
    return 0;
  }
  max_scan = clamp_word_dispatch_scan_bytes(section, table_base);
  for (cursor = 0U; cursor + 2U <= max_scan && entry_count < WORD_DISPATCH_MAX_SLOTS; cursor += 2U) {
    SectionDecodeResult entry_decode;
    M68kInstructionIR entry_instruction;
    uint32_t entry_offset = table_base + cursor;
    uint32_t target;
    if (!section_analysis_context_decode(ctx, entry_offset, NULL, &entry_decode)) break;
    entry_instruction = entry_decode.instruction;
    if (entry_offset + entry_instruction.byte_count > section->data_size ||
        !instruction_is_unconditional_transfer(&entry_instruction) ||
        !(entry_decode.has_explicit_target && (target = entry_decode.explicit_target, 1)) ||
        ((discovery->is_code_start != NULL && discovery->is_code_start[target] == 0U) &&
          !offset_decodes_as_instruction(ctx, target))) {
      if (entry_count != 0U) break;
      continue;
    }
    entry_offsets[entry_count] = entry_offset;
    targets[entry_count] = target;
    entry_count += 1U;
  }
  if (entry_count == 0U) return 0;
  memset(&dispatch, 0, sizeof(dispatch));
  dispatch.table_base = table_base;
  dispatch.scanned_bytes = (uint32_t)entry_count * 2U;
  dispatch.entry_count = entry_count;
  dispatch.entry_offsets = entry_offsets;
  dispatch.targets = targets;
  return m68k_ir_section_analysis_append_recovered_inline_dispatch(out_analysis, &dispatch) == 0 ? 1 : -1;
}

static int recover_pc_relative_word_dispatch_targets(const SectionDiscoveryMap *discovery,
    const M68kInstructionIR *instruction, uint32_t instruction_offset, const RecentInstructionWindow *recent_window,
    const SectionAnalysisContext *ctx, M68kSimTargetSet *out_targets) {
  RecoveredWordDispatchSeed seed;
  RecoveredWordDispatchTable table;
  AnalysisDispatchTargetAcceptContext target_ctx;
  AnalysisWordOffsetAcceptContext accept_ctx;
  RecoveredWordDispatchScanConfig scan_config;
  if (ctx == NULL || ctx->section == NULL || discovery == NULL || instruction == NULL || recent_window == NULL ||
      out_targets == NULL) {
    return 0;
  }
  if (!recover_pc_relative_word_dispatch_seed(instruction, instruction_offset, recent_window, ctx, &seed)) return 0;
  memset(&target_ctx, 0, sizeof(target_ctx));
  target_ctx.analysis_ctx = ctx;
  target_ctx.discovery = discovery;
  memset(&accept_ctx, 0, sizeof(accept_ctx));
  accept_ctx.target_ctx = &target_ctx;
  accept_ctx.base_target = seed.base_target;
  memset(&scan_config, 0, sizeof(scan_config));
  scan_config.section = ctx->section;
  scan_config.seed = &seed;
  scan_config.resolve_target = resolve_word_offset_dispatch_target;
  scan_config.resolve_ctx = &seed.base_target;
  scan_config.accept_target = analysis_accept_word_offset_dispatch_target;
  scan_config.accept_ctx = &accept_ctx;
  if (!scan_recovered_word_dispatch_table(&scan_config, &table)) return 0;
  recovered_word_dispatch_targets_to_set(&table, out_targets);
  return 1;
}

static uint32_t find_previous_code_start_local(const M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  uint32_t cursor;
  if (section_analysis == NULL || section_analysis->certain_code_start == NULL || offset == 0U) return UINT32_MAX;
  for (cursor = offset; cursor-- > 0U;) {
    if (section_analysis->certain_code_start[cursor] != 0U) return cursor;
  }
  return UINT32_MAX;
}

static int build_relative_word_expr(char *out_expr, size_t out_expr_size, const SectionAnalysisContext *ctx,
    uint32_t base_target, uint32_t target, GeneratedLabelKind *label_kinds, size_t label_kind_count,
    const M68kSectionAnalysisIR *section_analysis, uint8_t *generated_label_flags,
    const M68kPresentationPolicy *presentation) {
  GeneratedLabelKind base_kind = GENERATED_LABEL_DAT;
  uint32_t target_anchor = target;
  int32_t target_addend = 0;
  (void)presentation;
  if (out_expr == NULL || out_expr_size == 0U || section_analysis == NULL || generated_label_flags == NULL) return -1;
  if (label_kinds != NULL && base_target < label_kind_count) base_kind = label_kinds[base_target];
  if (label_kinds != NULL) update_generated_label_kind(label_kinds, label_kind_count, base_target, GENERATED_LABEL_DAT);
  base_kind = GENERATED_LABEL_DAT;
  if (!section_has_emittable_label(ctx, section_analysis, generated_label_flags, label_kind_count, target)) {
    uint32_t anchor = find_nearest_emittable_label(ctx, section_analysis, generated_label_flags, label_kind_count, target, 0);
    if (anchor != UINT32_MAX) {
      target_anchor = anchor;
      target_addend = (int32_t)(target - anchor);
    }
  }
  if (label_kinds != NULL && target_anchor < label_kind_count)
    update_generated_label_kind(label_kinds, label_kind_count, target_anchor, GENERATED_LABEL_LOC);
  generated_label_flags[base_target] = 1U;
  generated_label_flags[target_anchor] = 1U;
  snprintf(out_expr, out_expr_size, "@rel:%04X:%04X:%d", (unsigned)target_anchor, (unsigned)base_target, (int)target_addend);
  return 0;
}

static int build_relative_word_expr_here(char *out_expr, size_t out_expr_size, const SectionAnalysisContext *ctx,
    uint32_t base_target, uint32_t target, GeneratedLabelKind *label_kinds, size_t label_kind_count,
    const M68kSectionAnalysisIR *section_analysis, uint8_t *generated_label_flags,
    const M68kPresentationPolicy *presentation) {
  uint32_t target_anchor = target;
  int32_t target_addend = 0;
  (void)presentation;
  if (out_expr == NULL || out_expr_size == 0U || section_analysis == NULL || generated_label_flags == NULL) return -1;
  if (label_kinds != NULL) update_generated_label_kind(label_kinds, label_kind_count, base_target, GENERATED_LABEL_DAT);
  if (!section_has_emittable_label(ctx, section_analysis, generated_label_flags, label_kind_count, target)) {
    uint32_t anchor = find_nearest_emittable_label(ctx, section_analysis, generated_label_flags, label_kind_count, target, 0);
    if (anchor != UINT32_MAX) {
      target_anchor = anchor;
      target_addend = (int32_t)(target - anchor);
    }
  }
  if (label_kinds != NULL && target_anchor < label_kind_count)
    update_generated_label_kind(label_kinds, label_kind_count, target_anchor, GENERATED_LABEL_LOC);
  generated_label_flags[base_target] = 1U;
  generated_label_flags[target_anchor] = 1U;
  snprintf(out_expr, out_expr_size, "@relhere:%04X:%d", (unsigned)target_anchor, (int)target_addend);
  return 0;
}

static int build_literal_word_expr(char *out_expr, size_t out_expr_size, uint16_t value) {
  if (out_expr == NULL || out_expr_size == 0U) return -1;
  snprintf(out_expr, out_expr_size, "$%04X", (unsigned)value);
  return 0;
}

static int set_word_expr_slot(Arena *scratch_arena, char **out_word_exprs, uint32_t slot_offset, const char *expr) {
  if (scratch_arena == NULL || out_word_exprs == NULL || expr == NULL) return -1;
  if (out_word_exprs[slot_offset] != NULL) return 0;
  out_word_exprs[slot_offset] = arena_strdup(scratch_arena, expr);
  return out_word_exprs[slot_offset] != NULL ? 0 : -1;
}

static int parse_relative_word_expr_targets(const char *expr, uint32_t *out_target, uint32_t *out_base, int32_t *out_target_addend) {
  unsigned target = 0U;
  unsigned base = 0U;
  int addend = 0;
  if (expr == NULL || out_target == NULL || out_base == NULL) return 0;
  if (out_target_addend != NULL) *out_target_addend = 0;
  if (sscanf(expr, "@rel:%x:%x:%d", &target, &base, &addend) != 3 &&
      sscanf(expr, "@rel:%x:%x", &target, &base) != 2) {
    return 0;
  }
  *out_target = (uint32_t)target;
  *out_base = (uint32_t)base;
  if (out_target_addend != NULL) *out_target_addend = addend;
  return 1;
}

static int parse_relative_word_expr_here(const char *expr, uint32_t *out_target, int32_t *out_target_addend) {
  unsigned target = 0U;
  int addend = 0;
  if (expr == NULL || out_target == NULL) return 0;
  if (out_target_addend != NULL) *out_target_addend = 0;
  if (sscanf(expr, "@relhere:%x:%d", &target, &addend) != 2 &&
      sscanf(expr, "@relhere:%x", &target) != 1) {
    return 0;
  }
  *out_target = (uint32_t)target;
  if (out_target_addend != NULL) *out_target_addend = addend;
  return 1;
}

static int build_absolute_long_expr(char *out_expr, size_t out_expr_size, uint32_t target) {
  if (out_expr == NULL || out_expr_size == 0U) return -1;
  snprintf(out_expr, out_expr_size, "@abs:%04X", (unsigned)target);
  return 0;
}

static int parse_absolute_long_expr_target(const char *expr, uint32_t *out_target) {
  unsigned target = 0U;
  if (expr == NULL || out_target == NULL) return 0;
  if (sscanf(expr, "@abs:%x", &target) != 1) return 0;
  *out_target = (uint32_t)target;
  return 1;
}

static size_t section_analysis_find_block_index_by_start(const M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  size_t index;
  if (section_analysis == NULL) return SIZE_MAX;
  for (index = 0; index < section_analysis->block_count; ++index)
    if (section_analysis->blocks[index].start_offset == offset) return index;
  return SIZE_MAX;
}

size_t section_analysis_find_block_index_containing(const M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  size_t index;
  if (section_analysis == NULL) return SIZE_MAX;
  for (index = 0; index < section_analysis->block_count; ++index) {
    const M68kCfgBlockIR *block = &section_analysis->blocks[index];
    if (offset >= block->start_offset && offset < block->end_offset) return index;
  }
  return SIZE_MAX;
}

static int analysis_append_unique_edge(M68kSectionAnalysisIR *section_analysis, const M68kCfgEdgeIR *edge) {
  size_t index;
  if (section_analysis == NULL || edge == NULL) return -1;
  for (index = 0; index < section_analysis->edge_count; ++index) {
    const M68kCfgEdgeIR *existing = &section_analysis->edges[index];
    if (existing->source_block_index == edge->source_block_index &&
        existing->source_offset == edge->source_offset &&
        existing->target_offset == edge->target_offset &&
        existing->kind == edge->kind) {
      return 0;
    }
  }
  return m68k_ir_section_analysis_append_edge(section_analysis, edge);
}

static int reindex_section_edges_by_block(M68kSectionAnalysisIR *section_analysis) {
  M68kCfgEdgeIR *reordered;
  size_t write_index = 0U;
  size_t block_index;
  size_t edge_index;
  if (section_analysis == NULL || section_analysis->arena == NULL) return -1;
  reordered = (M68kCfgEdgeIR *)arena_calloc(section_analysis->arena,
    section_analysis->edge_count != 0U ? section_analysis->edge_count : 1U, sizeof(*reordered));
  if (reordered == NULL) return -1;
  for (block_index = 0; block_index < section_analysis->block_count; ++block_index) {
    M68kCfgBlockIR *block = &section_analysis->blocks[block_index];
    size_t count = 0U;
    block->edge_start = write_index;
    for (edge_index = 0; edge_index < section_analysis->edge_count; ++edge_index) {
      if (section_analysis->edges[edge_index].source_block_index != block_index) continue;
      reordered[write_index++] = section_analysis->edges[edge_index];
      count += 1U;
    }
    block->edge_count = count;
  }
  section_analysis->edges = reordered;
  section_analysis->edge_capacity = section_analysis->edge_count;
  return 0;
}

static int resolve_section_edge_target_blocks(M68kSectionAnalysisIR *section_analysis) {
  size_t block_index;
  if (section_analysis == NULL) return -1;
  for (block_index = 0; block_index < section_analysis->block_count; ++block_index) {
    size_t edge_index;
    for (edge_index = section_analysis->blocks[block_index].edge_start;
         edge_index < section_analysis->blocks[block_index].edge_start + section_analysis->blocks[block_index].edge_count;
         ++edge_index) {
      size_t target_index;
      if (section_analysis->edges[edge_index].target_offset == UINT32_MAX) continue;
      section_analysis->edges[edge_index].target_block_index = SIZE_MAX;
      for (target_index = 0; target_index < section_analysis->block_count; ++target_index) {
        if (section_analysis->blocks[target_index].start_offset == section_analysis->edges[edge_index].target_offset) {
          section_analysis->edges[edge_index].target_block_index = target_index;
          break;
        }
      }
    }
  }
  {
    size_t write_index = 0U;
    for (block_index = 0; block_index < section_analysis->block_count; ++block_index) {
      M68kCfgBlockIR *block = &section_analysis->blocks[block_index];
      size_t read_start = block->edge_start;
      size_t read_end = block->edge_start + block->edge_count;
      size_t kept = 0U;
      block->edge_start = write_index;
      while (read_start < read_end) {
        M68kCfgEdgeIR edge = section_analysis->edges[read_start++];
        if (edge.target_offset != UINT32_MAX && edge.target_block_index == SIZE_MAX) continue;
        section_analysis->edges[write_index++] = edge;
        ++kept;
      }
      block->edge_count = kept;
    }
    section_analysis->edge_count = write_index;
  }
  return reindex_section_edges_by_block(section_analysis);
}

static int add_recovered_string_dispatch_target_labels(M68kSectionAnalysisIR *section_analysis) {
  size_t dispatch_index;
  if (section_analysis == NULL) return -1;
  for (dispatch_index = 0; dispatch_index < section_analysis->recovered_string_dispatch_count; ++dispatch_index) {
    const M68kRecoveredStringDispatchIR *dispatch = &section_analysis->recovered_string_dispatches[dispatch_index];
    size_t entry_index;
    for (entry_index = 0; entry_index < dispatch->entry_count; ++entry_index) {
      if (m68k_ir_section_analysis_add_label(section_analysis, dispatch->targets[entry_index]) != 0) return -1;
    }
  }
  return 0;
}

int instruction_direct_target_local(const SectionAnalysisContext *ctx, const M68kInstructionIR *instruction,
    uint32_t instruction_offset, uint32_t *out_target) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  if (section == NULL || instruction == NULL || out_target == NULL || instruction_offset >= section->data_size) return 0;
  return instruction_control_transfer_target(instruction, section->data + instruction_offset,
    section->data_size - instruction_offset, instruction_offset, (uint32_t)section->data_size, out_target);
}

static int instruction_matches_indexed_an_lea(const M68kInstructionIR *instruction, uint8_t dest_reg,
    uint8_t *out_base_reg, uint8_t *out_index_reg, int32_t *out_disp) {
  uint8_t dest_is_address;
  uint8_t direct_dest_reg;
  uint8_t index_is_address;
  uint8_t index_reg;
  int32_t disp;
  if (instruction == NULL || instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA ||
      instruction->operand_count != 2U) {
    return 0;
  }
  if (!sim_operand_direct_register_local(&instruction->operands[1], &dest_is_address, &direct_dest_reg) ||
      dest_is_address == 0U || direct_dest_reg != dest_reg) {
    return 0;
  }
  if (!operand_is_brief_indexed_an(&instruction->operands[0], out_base_reg, &index_is_address, &index_reg, &disp) ||
      index_is_address != 0U) {
    return 0;
  }
  if (out_index_reg != NULL) *out_index_reg = index_reg;
  if (out_disp != NULL) *out_disp = disp;
  return 1;
}

static int append_recovered_string_dispatch_edges(M68kSectionAnalysisIR *section_analysis) {
  size_t dispatch_index;
  if (section_analysis == NULL) return 0;
  if (add_recovered_string_dispatch_target_labels(section_analysis) != 0) return -1;
  for (dispatch_index = 0; dispatch_index < section_analysis->recovered_string_dispatch_count; ++dispatch_index) {
    const M68kRecoveredStringDispatchIR *dispatch = &section_analysis->recovered_string_dispatches[dispatch_index];
    size_t source_block_index = section_analysis_find_block_index_containing(section_analysis, dispatch->dispatch_site);
    size_t entry_index;
    for (entry_index = 0; entry_index < dispatch->entry_count; ++entry_index) {
      M68kCfgEdgeIR edge;
      size_t target_block_index = section_analysis_find_block_index_by_start(section_analysis, dispatch->targets[entry_index]);
      memset(&edge, 0, sizeof(edge));
      edge.source_block_index = source_block_index;
      edge.target_block_index = target_block_index;
      edge.source_offset = dispatch->dispatch_site;
      edge.target_offset = dispatch->targets[entry_index];
      edge.kind = M68K_CFG_EDGE_CALL;
      if (analysis_append_unique_edge(section_analysis, &edge) != 0) return -1;
    }
  }
  return resolve_section_edge_target_blocks(section_analysis);
}

static int enqueue_recovered_string_dispatch_targets(const M68kObject *object, size_t section_index,
    const M68kSection *section, const SectionDiscoveryMap *discovery, M68kSectionAnalysisIR *section_analysis,
    Arena *scratch_arena, uint32_t **queue, size_t *queue_count, size_t *queue_capacity, M68kSimCpuState *entry_states,
    M68kSimMemoryState *entry_memory_states, uint8_t *entry_state_valid) {
  M68kSimCpuState unknown_state;
  M68kSimMemoryState unknown_memory_state;
  size_t dispatch_index;
  if (object == NULL || section == NULL || discovery == NULL || section_analysis == NULL || scratch_arena == NULL ||
      queue == NULL || queue_count == NULL || queue_capacity == NULL || entry_states == NULL ||
      entry_memory_states == NULL || entry_state_valid == NULL) {
    return -1;
  }
  if (add_recovered_string_dispatch_target_labels(section_analysis) != 0) return -1;
  m68k_sim_cpu_state_init_unknown(&unknown_state);
  m68k_sim_memory_state_seed_same_section_fixups(object, section_index, section, &unknown_memory_state);
  for (dispatch_index = 0; dispatch_index < section_analysis->recovered_string_dispatch_count; ++dispatch_index) {
    const M68kRecoveredStringDispatchIR *dispatch = &section_analysis->recovered_string_dispatches[dispatch_index];
    size_t entry_index;
    for (entry_index = 0; entry_index < dispatch->entry_count; ++entry_index) {
      uint32_t target = dispatch->targets[entry_index];
      int needs_queue;
      if (target >= section->data_size) continue;
      needs_queue = discovery->is_code_start == NULL || discovery->is_code_start[target] == 0U;
      if (m68k_ir_section_analysis_add_label(section_analysis, target) != 0) return -1;
      if (queue_target_with_sim_state(queue, queue_count, queue_capacity, scratch_arena, entry_states,
            entry_memory_states, entry_state_valid, target, &unknown_state, &unknown_memory_state) != 0) {
        return -1;
      }
      if (needs_queue && queue_push(queue, queue_count, queue_capacity, scratch_arena, target) != 0) return -1;
    }
  }
  return 0;
}

static int collect_recovered_word_dispatch_tables(const SectionAnalysisContext *ctx,
    M68kSectionAnalysisIR *section_analysis, const M68kPresentationPolicy *presentation) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  SectionDiscoveryMap discovery;
  AnalysisDispatchTargetAcceptContext target_ctx;
  RenderWordTargetAcceptContext render_accept_ctx;
  size_t block_index;
  RecentInstructionWindow recent_window;
  uint32_t expected_offset = UINT32_MAX;
  if (section == NULL || section_analysis == NULL) return 0;
  memset(&discovery, 0, sizeof(discovery));
  discovery.is_code_start = section_analysis->certain_code_start;
  discovery.is_code_byte = section_analysis->certain_code_byte;
  discovery.size = section_analysis->section_size;
  memset(&target_ctx, 0, sizeof(target_ctx));
  target_ctx.analysis_ctx = ctx;
  target_ctx.discovery = &discovery;
  memset(&render_accept_ctx, 0, sizeof(render_accept_ctx));
  render_accept_ctx.section_analysis = section_analysis;
  recent_instruction_window_reset(&recent_window);
  for (block_index = 0; block_index < section_analysis->block_count; ++block_index) {
    const M68kCfgBlockIR *block = &section_analysis->blocks[block_index];
    uint32_t offset = block->start_offset;
    if (expected_offset == UINT32_MAX || block->start_offset != expected_offset) recent_instruction_window_reset(&recent_window);
    while (offset < block->end_offset && offset < section->data_size) {
      SectionDecodeResult decode;
      M68kInstructionIR instruction;
      RecoveredWordDispatchSeed seed;
      RecoveredWordDispatchTable table;
      RecoveredWordDispatchScanConfig scan_config;
      if (!section_analysis_context_decode(ctx, offset, NULL, &decode) ||
          decode.instruction.byte_count == 0U || offset + decode.instruction.byte_count > block->end_offset) {
        break;
      }
      instruction = decode.instruction;
      if ((instruction_is_call_transfer(&instruction) || instruction_is_unconditional_transfer(&instruction)) &&
          recent_window.valid[0] != 0U && recent_window.valid[1] != 0U && recent_window.valid[2] != 0U) {
        if (recover_brief_word_offset_dispatch_seed(&instruction, &recent_window.instructions[0], &recent_window.instructions[1],
              &recent_window.instructions[2], recent_window.instruction_offsets[2], ctx, presentation, &seed)) {
          AnalysisWordOffsetAcceptContext accept_ctx;
          memset(&accept_ctx, 0, sizeof(accept_ctx));
          accept_ctx.target_ctx = &target_ctx;
          accept_ctx.base_target = seed.base_target;
          memset(&scan_config, 0, sizeof(scan_config));
          scan_config.section = section;
          scan_config.seed = &seed;
          scan_config.resolve_target = resolve_word_offset_dispatch_target;
          scan_config.resolve_ctx = &seed.base_target;
          scan_config.accept_target = analysis_accept_word_offset_dispatch_target;
          scan_config.accept_ctx = &accept_ctx;
          if (scan_recovered_word_dispatch_table(&scan_config, &table) &&
              append_recovered_word_dispatch_table(section_analysis, &table) != 0) return -1;
        }
        if (recover_entry_relative_word_dispatch_seed(&discovery, &instruction, &recent_window.instructions[0],
              &recent_window.instructions[1], recent_window.instruction_offsets[1], ctx, &seed)) {
          memset(&scan_config, 0, sizeof(scan_config));
          scan_config.section = section;
          scan_config.seed = &seed;
          scan_config.resolve_target = resolve_entry_relative_dispatch_target;
          scan_config.resolve_ctx = section;
          scan_config.accept_target = render_accept_dispatch_target;
          scan_config.accept_ctx = &render_accept_ctx;
          if (scan_recovered_word_dispatch_table(&scan_config, &table) &&
              append_recovered_word_dispatch_table(section_analysis, &table) != 0) return -1;
        }
        if (recover_pc_relative_word_dispatch_seed(&instruction, offset, &recent_window, ctx, &seed)) {
          AnalysisWordOffsetAcceptContext accept_ctx;
          memset(&accept_ctx, 0, sizeof(accept_ctx));
          accept_ctx.target_ctx = &target_ctx;
          accept_ctx.base_target = seed.base_target;
          memset(&scan_config, 0, sizeof(scan_config));
          scan_config.section = section;
          scan_config.seed = &seed;
          scan_config.resolve_target = resolve_word_offset_dispatch_target;
          scan_config.resolve_ctx = &seed.base_target;
          scan_config.accept_target = analysis_accept_word_offset_dispatch_target;
          scan_config.accept_ctx = &accept_ctx;
          if (scan_recovered_word_dispatch_table(&scan_config, &table) &&
              append_recovered_word_dispatch_table(section_analysis, &table) != 0) return -1;
        }
      }
      recent_instruction_window_push(&recent_window, &instruction, offset);
      offset += (uint32_t)instruction.byte_count;
      expected_offset = offset;
    }
  }
  return 0;
}

static int build_word_offset_dispatch_exprs(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, GeneratedLabelKind *label_kinds, size_t label_kind_count,
    uint8_t *generated_label_flags, const M68kPresentationPolicy *presentation, Arena *scratch_arena,
    char **out_word_exprs) {
  size_t index;
  (void)ctx;
  if (section_analysis == NULL || generated_label_flags == NULL || scratch_arena == NULL || out_word_exprs == NULL)
    return 0;
  for (index = 0; index < section_analysis->recovered_word_dispatch_count; ++index) {
    const M68kRecoveredWordDispatchIR *dispatch = &section_analysis->recovered_word_dispatches[index];
    RecoveredWordDispatchTable table;
    memset(&table, 0, sizeof(table));
    table.pattern = (RecoveredWordDispatchPattern)dispatch->pattern;
    table.relative_to_slot = dispatch->relative_to_slot;
    table.preserve_zero_slots = dispatch->preserve_zero_slots;
    table.table_base = dispatch->table_base;
    table.base_target = dispatch->base_target;
    table.scanned_bytes = dispatch->scanned_bytes;
    table.slot_count = (uint32_t)dispatch->slot_count;
    if (dispatch->slot_count > WORD_DISPATCH_MAX_SLOTS) return -1;
    if (dispatch->slot_count != 0U) {
      memcpy(table.entry_words, dispatch->entry_words, dispatch->slot_count * sizeof(*dispatch->entry_words));
      memcpy(table.targets, dispatch->targets, dispatch->slot_count * sizeof(*dispatch->targets));
      memcpy(table.target_valid, dispatch->target_valid, dispatch->slot_count);
    }
    table.found = 1U;
    if (emit_recovered_word_dispatch_exprs(&table, ctx, section_analysis, label_kinds, label_kind_count,
          generated_label_flags, presentation, scratch_arena, out_word_exprs) != 0) {
      return -1;
    }
  }
  for (index = 0; index < section_analysis->recovered_string_dispatch_count; ++index) {
    const M68kRecoveredStringDispatchIR *dispatch = &section_analysis->recovered_string_dispatches[index];
    size_t entry_index;
    for (entry_index = 0; entry_index < dispatch->entry_count; ++entry_index) {
      char expr[80];
      if (build_relative_word_expr_here(expr, sizeof(expr), ctx, dispatch->offset_offsets[entry_index],
            dispatch->targets[entry_index], label_kinds, label_kind_count, section_analysis,
            generated_label_flags, presentation) != 0) {
        return -1;
      }
      if (set_word_expr_slot(scratch_arena, out_word_exprs, dispatch->offset_offsets[entry_index], expr) != 0)
        return -1;
    }
  }
  return 0;
}

static int derive_block_starts(const SectionAnalysisContext *ctx, SectionDiscoveryMap *discovery,
    const M68kSimTargetSet *sim_targets, const uint8_t *sim_stops, M68kAnalysisFindings *findings,
    M68kSectionAnalysisIR *out_analysis, uint8_t *block_starts) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  size_t dispatch_index;
  size_t scan_offset;
  if (section == NULL || discovery == NULL || sim_targets == NULL || sim_stops == NULL || out_analysis == NULL ||
      block_starts == NULL) {
    return -1;
  }
  block_starts[0] = 1U;
  if (add_recovered_string_dispatch_target_labels(out_analysis) != 0) return -1;
  for (dispatch_index = 0; dispatch_index < out_analysis->recovered_string_dispatch_count; ++dispatch_index) {
    const M68kRecoveredStringDispatchIR *dispatch = &out_analysis->recovered_string_dispatches[dispatch_index];
    size_t entry_index;
    for (entry_index = 0; entry_index < dispatch->entry_count; ++entry_index) {
      uint32_t target = dispatch->targets[entry_index];
      if (target >= section->data_size) continue;
      discovery->is_code_start[target] = 1U;
      block_starts[target] = 1U;
    }
  }
  for (scan_offset = 0; scan_offset < section->data_size; ++scan_offset) {
    uint32_t cursor;
    if (discovery->is_code_byte[scan_offset] == 0U) continue;
    if (scan_offset != 0U && discovery->is_code_byte[scan_offset - 1U] != 0U &&
        discovery->is_code_start[scan_offset] == 0U) {
      continue;
    }
    cursor = (uint32_t)scan_offset;
    while (cursor < section->data_size && discovery->is_code_byte[cursor] != 0U) {
      SectionDecodeResult decode;
      M68kInstructionIR instruction;
      uint32_t target;
      uint32_t next_offset;
      if (!section_analysis_context_decode(ctx, cursor, findings, &decode)) {
        if (m68k_ir_section_analysis_add_violation(out_analysis, cursor,
              M68K_VIOLATION_DECODE_FAILED_REACHABLE, "decode failed in reachable code; region emitted as data") != 0)
          return -1;
        break;
      }
      instruction = decode.instruction;
      if (add_cpu_violation(out_analysis, cursor, &instruction, ctx->analysis_policy) != 0) return -1;
      next_offset = cursor + (uint32_t)instruction.byte_count;
      if (decode.has_explicit_target && (target = decode.explicit_target, 1)) {
        discovery->is_code_start[target] = 1U;
        if (m68k_ir_section_analysis_add_label(out_analysis, target) != 0) return -1;
        block_starts[target] = 1U;
      if ((decode.is_call || decode.is_conditional_transfer) &&
          next_offset < section->data_size && sim_stops[cursor] == 0U) {
          block_starts[next_offset] = 1U;
        }
      } else if (sim_targets[cursor].count != 0U) {
        size_t sim_target_index;
        for (sim_target_index = 0; sim_target_index < sim_targets[cursor].count; ++sim_target_index) {
          target = sim_targets[cursor].targets[sim_target_index];
          if (target >= section->data_size) continue;
          discovery->is_code_start[target] = 1U;
          if (m68k_ir_section_analysis_add_label(out_analysis, target) != 0) return -1;
          block_starts[target] = 1U;
        }
        if ((decode.is_call || decode.is_conditional_transfer) &&
            next_offset < section->data_size && sim_stops[cursor] == 0U) {
          block_starts[next_offset] = 1U;
        }
      } else if (!sim_stops[cursor] && decode.is_call && next_offset < section->data_size) {
        block_starts[next_offset] = 1U;
      }
      cursor = next_offset;
    }
  }
  return 0;
}

static int build_cfg_blocks(const SectionAnalysisContext *ctx, SectionDiscoveryMap *discovery,
    const M68kSimTargetSet *sim_targets, const uint8_t *sim_stops, const uint8_t *sim_conditional_known,
    const uint8_t *block_starts, M68kAnalysisFindings *findings, M68kSectionAnalysisIR *out_analysis) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  size_t scan_offset;
  if (section == NULL || discovery == NULL || sim_targets == NULL || sim_stops == NULL || sim_conditional_known == NULL ||
      block_starts == NULL || out_analysis == NULL) {
    return -1;
  }
  for (scan_offset = 0; scan_offset < section->data_size; ++scan_offset) {
    M68kCfgBlockIR block;
    uint32_t cursor;
    if (discovery->is_code_start[scan_offset] == 0U || block_starts[scan_offset] == 0U) continue;
    memset(&block, 0, sizeof(block));
    block.start_offset = (uint32_t)scan_offset;
    block.certainty = M68K_CODE_CERTAIN;
    block.edge_start = out_analysis->edge_count;
    cursor = (uint32_t)scan_offset;
    for (;;) {
      SectionDecodeResult decode;
      M68kInstructionIR instruction;
      uint32_t next_offset;
      size_t target_count;
      if (!section_analysis_context_decode(ctx, cursor, findings, &decode)) {
        if (m68k_ir_section_analysis_add_violation(out_analysis, cursor, M68K_VIOLATION_DECODE_FAILED_REACHABLE,
              "decode failed in reachable code; region emitted as data") != 0) return -1;
        break;
      }
      instruction = decode.instruction;
      if (add_cpu_violation(out_analysis, cursor, &instruction, ctx->analysis_policy) != 0) return -1;
      next_offset = cursor + (uint32_t)instruction.byte_count;
      target_count = sim_targets[cursor].count != 0U ? sim_targets[cursor].count :
        (decode.has_explicit_target ? (block.end_offset = decode.explicit_target, 1U) : 0U);
      if (decode.has_explicit_target || sim_targets[cursor].count != 0U) {
        M68kCfgEdgeIR edge;
        size_t sim_target_index;
        if (!(sim_conditional_known[cursor] != 0U && sim_targets[cursor].count == 0U && sim_stops[cursor] == 0U)) {
          for (sim_target_index = 0; sim_target_index < target_count; ++sim_target_index) {
            memset(&edge, 0, sizeof(edge));
            edge.source_block_index = out_analysis->block_count;
            edge.target_block_index = SIZE_MAX;
            edge.source_offset = cursor;
            edge.target_offset = sim_targets[cursor].count != 0U ? sim_targets[cursor].targets[sim_target_index]
                                                                 : block.end_offset;
            edge.kind = decode.is_call
              ? M68K_CFG_EDGE_CALL : decode.is_unconditional_transfer
              ? M68K_CFG_EDGE_JUMP : M68K_CFG_EDGE_BRANCH;
            if (m68k_ir_section_analysis_append_edge(out_analysis, &edge) != 0) return -1;
          }
        }
        if (sim_targets[cursor].count != 0U) block.end_offset = sim_targets[cursor].targets[0];
        if ((decode.is_call || decode.is_conditional_transfer) &&
            next_offset < section->data_size && sim_stops[cursor] == 0U) {
          memset(&edge, 0, sizeof(edge));
          edge.source_block_index = out_analysis->block_count;
          edge.target_block_index = SIZE_MAX;
          edge.source_offset = cursor;
          edge.target_offset = next_offset;
          edge.kind = M68K_CFG_EDGE_FALLTHROUGH;
          if (m68k_ir_section_analysis_append_edge(out_analysis, &edge) != 0) return -1;
        }
        cursor = next_offset;
        break;
      }
      if (sim_stops[cursor] || decode.stops_fallthrough) {
        M68kCfgEdgeIR edge;
        memset(&edge, 0, sizeof(edge));
        edge.source_block_index = out_analysis->block_count;
        edge.target_block_index = SIZE_MAX;
        edge.source_offset = cursor;
        edge.target_offset = UINT32_MAX;
        edge.kind = M68K_CFG_EDGE_RETURN;
        if (m68k_ir_section_analysis_append_edge(out_analysis, &edge) != 0) return -1;
        cursor = next_offset;
        break;
      }
      if (next_offset >= section->data_size || block_starts[next_offset] != 0U) {
        if (next_offset < section->data_size && block_starts[next_offset] != 0U) {
          M68kCfgEdgeIR edge;
          memset(&edge, 0, sizeof(edge));
          edge.source_block_index = out_analysis->block_count;
          edge.target_block_index = SIZE_MAX;
          edge.source_offset = cursor;
          edge.target_offset = next_offset;
          edge.kind = M68K_CFG_EDGE_FALLTHROUGH;
          if (m68k_ir_section_analysis_append_edge(out_analysis, &edge) != 0) return -1;
        }
        cursor = next_offset;
        break;
      }
      cursor = next_offset;
    }
    block.end_offset = cursor;
    block.edge_count = out_analysis->edge_count - block.edge_start;
    if (m68k_ir_section_analysis_append_block(out_analysis, &block) != 0) return -1;
  }
  return resolve_section_edge_target_blocks(out_analysis);
}

static int run_section_discovery_pass(const M68kObject *object, size_t section_index, Arena *scratch_arena,
    const SectionAnalysisContext *ctx, M68kAnalysisFindings *findings, M68kSectionAnalysisIR *out_analysis,
    SectionDiscoveryMap *discovery, uint32_t **queue, size_t *queue_count, size_t *queue_capacity, M68kSimCpuState *entry_states,
    M68kSimMemoryState *entry_memory_states, uint8_t *entry_state_valid, LocalCallSummaryCache *call_summary_cache,
    M68kSimTargetSet *sim_targets, uint8_t *sim_stops, uint8_t *sim_conditional_known) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  size_t pop_index = 0U;
  if (object == NULL || scratch_arena == NULL || ctx == NULL || out_analysis == NULL || discovery == NULL || queue == NULL ||
      queue_count == NULL || queue_capacity == NULL || entry_states == NULL || entry_memory_states == NULL ||
      entry_state_valid == NULL || call_summary_cache == NULL ||
      sim_targets == NULL || sim_stops == NULL || sim_conditional_known == NULL || section == NULL) {
    return -1;
  }
  while (pop_index < *queue_count) {
    uint32_t work_offset = (*queue)[pop_index++];
    uint32_t segment_start = work_offset;
    uint32_t segment_end = work_offset;
    M68kSimCpuState current_state;
    M68kSimMemoryState current_memory_state;
    RecentInstructionWindow recent_window;
    int segment_terminated_cleanly = 0;
    recent_instruction_window_reset(&recent_window);
    if (entry_state_valid[work_offset] != 0U) current_state = entry_states[work_offset];
    else m68k_sim_cpu_state_init_unknown(&current_state);
    if (entry_state_valid[work_offset] != 0U) current_memory_state = entry_memory_states[work_offset];
    else m68k_sim_memory_state_seed_same_section_fixups(object, section_index, section, &current_memory_state);
    while (work_offset < section->data_size) {
      DiscoveryStep step;
      if (discovery->is_code_start[work_offset] && work_offset != segment_start) break;
      {
        int step_result = discovery_decode_and_step(object, section_index, scratch_arena, ctx, findings, call_summary_cache,
          out_analysis, discovery, work_offset, &current_state, &current_memory_state, &step);
        if (step_result < 0) return -1;
        if (step_result == 0) {
          segment_end = work_offset;
          segment_terminated_cleanly = 1;
          break;
        }
      }
      segment_end = work_offset + (uint32_t)step.instruction.byte_count;
      if (step.conditional_outcome_known) sim_conditional_known[work_offset] = 1U;
      if (step.state_stops_fallthrough) sim_stops[work_offset] = 1U;
      if (discovery_recover_indirect_targets(ctx, discovery, out_analysis, work_offset, &recent_window, &step) != 0)
        return -1;
      if (discovery_enqueue_control_targets(section, section_index, scratch_arena, out_analysis, queue, queue_count,
            queue_capacity, entry_states, entry_memory_states, entry_state_valid, sim_targets, work_offset, &current_state,
            &current_memory_state, &step) != 0) {
        return -1;
      }
      work_offset += (uint32_t)step.instruction.byte_count;
      current_state = step.sim_result.next_state;
      apply_sim_memory_writes(&current_memory_state, &step.sim_result);
      if (step.local_call_summary_valid) current_memory_state = step.local_call_summary_memory_state;
      recent_instruction_window_push(&recent_window, &step.instruction, work_offset - (uint32_t)step.instruction.byte_count);
      if (step.state_stops_fallthrough || step.decode.stops_fallthrough) {
        segment_end = work_offset;
        segment_terminated_cleanly = 1;
        break;
      }
      if (step.decode.is_call && work_offset < section->data_size &&
          m68k_ir_section_analysis_add_label(out_analysis, work_offset) != 0) {
        return -1;
      }
    }
    if (!segment_terminated_cleanly && work_offset >= section->data_size && segment_end > segment_start) {
      if (m68k_ir_section_analysis_add_violation(out_analysis, segment_start, M68K_VIOLATION_DECODE_FAILED_REACHABLE,
            "reachable segment runs to section end without terminating control transfer") != 0) return -1;
    }
  }
  return 0;
}

int build_section_analysis(const M68kObject *object, size_t section_index, const M68kSection *section,
    Arena *scratch_arena, const M68kAnalysisPolicy *analysis_policy, M68kAnalysisFindings *findings, M68kSectionAnalysisIR *out_analysis,
    M68kDiagSink diagnostics) {
  ArenaMark prune_mark;
  SectionDiscoveryMap discovery = {0};
  GeneratedLabelKind *generated_label_kinds = NULL;
  uint8_t *generated_label_flags = NULL;
  char **word_exprs = NULL;
  char **long_exprs = NULL;
  uint32_t *queue = NULL;
  M68kSimCpuState *entry_states = NULL;
  M68kSimMemoryState *entry_memory_states = NULL;
  uint8_t *entry_state_valid = NULL;
  LocalCallSummaryCache call_summary_cache = {0};
  SectionAnalysisContext analysis_ctx = {0};
  M68kSimTargetSet *sim_targets = NULL;
  uint8_t *sim_stops = NULL;
  uint8_t *sim_conditional_known = NULL;
  size_t queue_count = 0, queue_capacity = 0, fixup_index;
  uint8_t *block_starts = NULL;
  (void)diagnostics;
  if (scratch_arena == NULL || out_analysis == NULL) return -1;
  if (m68k_ir_section_analysis_create(out_analysis) != 0) return -1;
  out_analysis->section_index = section_index;
  out_analysis->section_kind = section->kind;
  out_analysis->section_size = section->size;
  if (m68k_ir_section_analysis_set_name(out_analysis,
        (section->name != NULL && section->name[0] != '\0') ? section->name : "section") != 0) return -1;
  if (section->kind != M68K_SECTION_CODE || section->data_size == 0U) {
    out_analysis->certain_code_size = section->data_size;
    return 0;
  }

  discovery.is_code_start = (uint8_t *)arena_calloc(scratch_arena, section->data_size != 0U ? section->data_size : 1U,
    1U);
  discovery.is_code_byte = (uint8_t *)arena_calloc(scratch_arena, section->data_size != 0U ? section->data_size : 1U,
    1U);
  entry_states = (M68kSimCpuState *)arena_calloc(scratch_arena, section->data_size != 0U ? section->data_size : 1U,
    sizeof(*entry_states));
  entry_memory_states = (M68kSimMemoryState *)arena_calloc(scratch_arena,
    section->data_size != 0U ? section->data_size : 1U, sizeof(*entry_memory_states));
  entry_state_valid = (uint8_t *)arena_calloc(scratch_arena, section->data_size != 0U ? section->data_size : 1U, 1U);
  sim_targets = (M68kSimTargetSet *)arena_calloc(scratch_arena, section->data_size != 0U ? section->data_size : 1U,
    sizeof(*sim_targets));
  sim_stops = (uint8_t *)arena_calloc(scratch_arena, section->data_size != 0U ? section->data_size : 1U, 1U);
  sim_conditional_known = (uint8_t *)arena_calloc(scratch_arena, section->data_size != 0U ? section->data_size : 1U, 1U);
  if (discovery.is_code_start == NULL || discovery.is_code_byte == NULL || entry_states == NULL ||
      entry_memory_states == NULL || entry_state_valid == NULL || sim_targets == NULL || sim_stops == NULL ||
      sim_conditional_known == NULL) {
    discovery_map_cleanup(&discovery, scratch_arena);
    goto fail;
  }
  if (local_call_summary_cache_init(&call_summary_cache, out_analysis->arena, section->data_size) != 0) {
    discovery_map_cleanup(&discovery, scratch_arena);
    goto fail;
  }
  if (section_analysis_context_init(&analysis_ctx, object, section, analysis_policy, out_analysis->arena) != 0) {
    discovery_map_cleanup(&discovery, scratch_arena);
    goto fail;
  }

  discovery.size = section->data_size;
  if (m68k_ir_section_analysis_add_label(out_analysis, 0U) != 0) goto fail;

  queue_capacity = 32U;
  queue = (uint32_t *)arena_calloc(scratch_arena, queue_capacity, sizeof(*queue));
  if (queue == NULL) goto fail;

  m68k_sim_cpu_state_init_unknown(&entry_states[0]);
  m68k_sim_memory_state_seed_same_section_fixups(object, section_index, section, &entry_memory_states[0]);
  entry_state_valid[0] = 1U;
  queue[queue_count++] = 0U;
  for (fixup_index = 0; fixup_index < object->fixup_count; ++fixup_index) {
    const M68kFixup *fixup = &object->fixups[fixup_index];
    if (fixup->section_index != section_index) continue;
    if (!fixup->has_target_section || fixup->target_section_index != section_index) continue;
    if (fixup->offset + 4U <= section->data_size) {
      uint32_t raw_target = m68k_read_u32be(section->data + fixup->offset);
      uint32_t target = raw_target;
      if (target >= section->data_size) {
        if (fixup->addend < 0 || (uint32_t)fixup->addend >= section->data_size) continue;
        target = (uint32_t)fixup->addend;
      }
      if (m68k_ir_section_analysis_add_label(out_analysis, target) != 0) goto fail;

      if (object->platform_file_kind == M68K_PLATFORM_FILE_OBJECT) {
        M68kSimCpuState unknown_state;
        M68kSimMemoryState unknown_memory_state;
        m68k_sim_cpu_state_init_unknown(&unknown_state);
        m68k_sim_memory_state_seed_same_section_fixups(object, section_index, section, &unknown_memory_state);
        if (queue_target_with_sim_state(&queue, &queue_count, &queue_capacity, scratch_arena, entry_states,
            entry_memory_states, entry_state_valid, target, &unknown_state, &unknown_memory_state) != 0)
          goto fail;
      }
    }
  }

  if (run_section_discovery_pass(object, section_index, scratch_arena, &analysis_ctx, findings, out_analysis, &discovery,
        &queue, &queue_count, &queue_capacity, entry_states, entry_memory_states, entry_state_valid,
        &call_summary_cache, sim_targets, sim_stops, sim_conditional_known) != 0)
    goto fail;
  if (enqueue_recovered_string_dispatch_targets(object, section_index, section, &discovery, out_analysis, scratch_arena,
        &queue, &queue_count, &queue_capacity, entry_states, entry_memory_states, entry_state_valid) != 0) {
    goto fail;
  }
  if (out_analysis->recovered_string_dispatch_count != 0U &&
      run_section_discovery_pass(object, section_index, scratch_arena, &analysis_ctx, findings, out_analysis, &discovery,
        &queue, &queue_count, &queue_capacity, entry_states, entry_memory_states, entry_state_valid,
        &call_summary_cache, sim_targets, sim_stops, sim_conditional_known) != 0) {
    goto fail;
  }
  if (prune_entry_skip_range(&analysis_ctx, findings, out_analysis, &discovery) != 0)
    goto fail;
  if (promote_direct_control_targets(&analysis_ctx, findings, &discovery) != 0)
    goto fail;
  if (enrich_analysis_labels(&analysis_ctx, findings, &discovery, out_analysis) != 0)
    goto fail;
  if (m68k_ir_section_analysis_set_code_map( out_analysis, discovery.is_code_start, discovery.is_code_byte, discovery.size) != 0)
    goto fail;
  block_starts = (uint8_t *)arena_calloc(scratch_arena, section->data_size != 0U ? section->data_size : 1U, 1U);
  if (block_starts == NULL)
    goto fail;
  if (derive_block_starts(&analysis_ctx, &discovery, sim_targets, sim_stops, findings, out_analysis, block_starts) != 0)
    goto fail;
  if (build_cfg_blocks(&analysis_ctx, &discovery, sim_targets, sim_stops, sim_conditional_known, block_starts, findings,
        out_analysis) != 0)
    goto fail;
  if (append_recovered_string_dispatch_edges(out_analysis) != 0)
    goto fail;
  if (object->platform_file_kind == M68K_PLATFORM_FILE_EXECUTABLE) {
    prune_mark = arena_mark(scratch_arena);
    if (prune_disconnected_blocks(out_analysis, &discovery, scratch_arena) != 0)
      goto fail;
    if (m68k_ir_section_analysis_set_code_map( out_analysis, discovery.is_code_start, discovery.is_code_byte, discovery.size) != 0)
      goto fail;
    if (rebuild_code_map_from_blocks(&analysis_ctx, out_analysis) !=
        0)
      goto fail;
    arena_rewind(scratch_arena, prune_mark);
  }
  if (platform_collect_recovered_platform_facts(&analysis_ctx, out_analysis) != 0)
    goto fail;
  if (rebuild_unresolved_indirect_violations(&analysis_ctx, out_analysis) != 0)
    goto fail;
  if (section->data_size != 0U) {
    generated_label_kinds = (GeneratedLabelKind *)arena_calloc(scratch_arena,
      section->data_size != 0U ? section->data_size : 1U, sizeof(*generated_label_kinds));
    generated_label_flags = (uint8_t *)arena_calloc(scratch_arena, section->data_size != 0U ? section->data_size : 1U, 1U);
    word_exprs = (char **)arena_calloc(scratch_arena, section->data_size != 0U ? section->data_size : 1U, sizeof(*word_exprs));
    long_exprs = (char **)arena_calloc(scratch_arena, section->data_size != 0U ? section->data_size : 1U, sizeof(*long_exprs));
    if (generated_label_kinds == NULL || generated_label_flags == NULL || word_exprs == NULL || long_exprs == NULL)
      goto fail;
    if (build_generated_label_kinds(&analysis_ctx, findings, out_analysis, generated_label_kinds,
          generated_label_flags) != 0)
      goto fail;
    mark_data_fixup_labels(object, out_analysis, generated_label_kinds, generated_label_flags);
    if (scan_interior_pc_relative_refs(&analysis_ctx, findings, out_analysis, generated_label_kinds,
          generated_label_flags) != 0)
      goto fail;
    finalize_generated_label_kinds(out_analysis, generated_label_kinds, section->data_size);
    if (m68k_ir_section_analysis_set_generated_labels(out_analysis, generated_label_kinds,
          generated_label_flags, section->data_size) != 0)
      goto fail;
    if (collect_recovered_word_dispatch_tables(&analysis_ctx, out_analysis, NULL) != 0)
      goto fail;
    if (build_word_offset_dispatch_exprs(&analysis_ctx, out_analysis, generated_label_kinds, section->data_size,
          generated_label_flags, NULL, scratch_arena, word_exprs) != 0)
      goto fail;
    if (m68k_ir_section_analysis_set_word_exprs(out_analysis, word_exprs, section->data_size) != 0)
      goto fail;
    if (build_self_section_long_exprs(object, out_analysis, generated_label_kinds, section->data_size,
          generated_label_flags, scratch_arena, long_exprs) != 0)
      goto fail;
    if (m68k_ir_section_analysis_set_long_exprs(out_analysis, long_exprs, section->data_size) != 0)
      goto fail;
  }
  discovery_map_cleanup(&discovery, scratch_arena);
  return 0;

fail:
  discovery_map_cleanup(&discovery, scratch_arena);
  m68k_ir_section_analysis_destroy(out_analysis);
  return -1;
}




static int analysis_has_label(const M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  size_t index;
  if (section_analysis == NULL) return 0;
  for (index = 0; index < section_analysis->label_count; ++index)
    if (section_analysis->label_offsets[index] == offset) return 1;
  return 0;
}

static int section_has_renderable_explicit_label(const M68kSectionAnalysisIR *section_analysis,
    const uint8_t *generated_label_flags, size_t generated_label_count, uint32_t offset) {
  if (section_analysis_has_string_dispatch_target(section_analysis, offset)) return 1;
  if (!analysis_has_label(section_analysis, offset)) return 0;
  if (section_analysis_has_block_start(section_analysis, offset)) return 1;
  if (generated_label_flags != NULL && offset < generated_label_count && generated_label_flags[offset] != 0U) return 1;
  return section_analysis != NULL && section_analysis->certain_code_start != NULL &&
    offset < section_analysis->certain_code_size && section_analysis->certain_code_start[offset] != 0U;
}

static int section_has_any_label(const M68kSectionAnalysisIR *section_analysis, const uint8_t *generated_label_flags,
    size_t generated_label_count, uint32_t offset) {
  if (section_has_renderable_explicit_label(section_analysis, generated_label_flags, generated_label_count, offset))
    return 1;
  if (section_analysis_has_block_start(section_analysis, offset)) return 1;
  return generated_label_flags != NULL && offset < generated_label_count && generated_label_flags[offset] != 0U;
}

static int section_has_emittable_label(const SectionAnalysisContext *ctx, const M68kSectionAnalysisIR *section_analysis,
    const uint8_t *generated_label_flags, size_t generated_label_count, uint32_t offset) {
  SectionDecodeResult decode;
  if (section_has_renderable_explicit_label(section_analysis, generated_label_flags, generated_label_count, offset))
    return 1;
  if (section_analysis_has_block_start(section_analysis, offset)) return 1;
  if (generated_label_flags == NULL || offset >= generated_label_count || generated_label_flags[offset] == 0U) return 0;
  if (section_analysis == NULL || section_analysis->certain_code_byte == NULL || offset >= section_analysis->certain_code_size)
    return 1;
  if (section_analysis->certain_code_byte[offset] == 0U || section_analysis->certain_code_start[offset] != 0U) return 1;
  return ctx != NULL && section_analysis_context_decode(ctx, offset, NULL, &decode) != 0;
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

static int append_statement_comment(char *buf, size_t buf_size, const char *message) {
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
    append_statement_comment(buf, buf_size, violation->message);
  }
}

static void collect_recovered_platform_call_comments(const M68kSectionAnalysisIR *section_analysis, uint32_t offset,
    char *buf, size_t buf_size) {
  size_t index;
  char note[160];
  if (buf == NULL || buf_size == 0U || section_analysis == NULL) return;
  for (index = 0; index < section_analysis->recovered_platform_call_count; ++index) {
    const M68kRecoveredPlatformCallIR *call = &section_analysis->recovered_platform_calls[index];
    PlatformResolvedIndirectInfo info;
    if (call->offset != offset) continue;
    if (call->kind == 0U) continue;
    load_recovered_platform_call_info(call, &info);
    if (!format_platform_resolved_indirect_note(&info, note, sizeof(note))) continue;
    append_statement_comment(buf, buf_size, note);
  }
}

static int section_analysis_has_block_start(const M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  size_t block_index;
  if (section_analysis == NULL) return 0;
  for (block_index = 0; block_index < section_analysis->block_count; ++block_index) {
    if (section_analysis->blocks[block_index].start_offset == offset) return 1;
  }
  return 0;
}

static int section_analysis_has_string_dispatch_target(const M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  size_t dispatch_index;
  if (section_analysis == NULL) return 0;
  for (dispatch_index = 0; dispatch_index < section_analysis->recovered_string_dispatch_count; ++dispatch_index) {
    const M68kRecoveredStringDispatchIR *dispatch = &section_analysis->recovered_string_dispatches[dispatch_index];
    size_t entry_index;
    for (entry_index = 0; entry_index < dispatch->entry_count; ++entry_index) {
      if (dispatch->targets[entry_index] == offset) return 1;
    }
  }
  return 0;
}

static int section_analysis_has_string_dispatch_site(const M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  size_t dispatch_index;
  if (section_analysis == NULL) return 0;
  for (dispatch_index = 0; dispatch_index < section_analysis->recovered_string_dispatch_count; ++dispatch_index) {
    if (section_analysis->recovered_string_dispatches[dispatch_index].dispatch_site == offset) return 1;
  }
  return 0;
}

static uint32_t find_enclosing_any_label(const M68kSectionAnalysisIR *section_analysis,
    const uint8_t *generated_label_flags, size_t generated_label_count, uint32_t offset) {
  uint32_t cursor;
  if (section_analysis == NULL) return UINT32_MAX;
  if (offset >= generated_label_count) return UINT32_MAX;
  for (cursor = offset; ; --cursor) {
    if (section_has_any_label(section_analysis, generated_label_flags, generated_label_count, cursor))
      return cursor;
    if (cursor == 0U) break;
  }
  return UINT32_MAX;
}

static int offset_is_known_code_byte(const M68kSectionAnalysisIR *section_analysis, uint32_t offset) {
  return section_analysis != NULL && section_analysis->certain_code_byte != NULL &&
    offset < section_analysis->certain_code_size && section_analysis->certain_code_byte[offset] != 0U;
}

static uint32_t find_enclosing_instruction_start(const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, M68kAnalysisFindings *findings, uint32_t target, uint32_t *out_end) {
  const M68kSection *section = ctx != NULL ? ctx->section : NULL;
  uint32_t cursor;
  if (out_end != NULL) *out_end = UINT32_MAX;
  if (section == NULL || section_analysis == NULL || section_analysis->certain_code_start == NULL ||
      section_analysis->certain_code_byte == NULL || target >= section_analysis->certain_code_size ||
      section_analysis->certain_code_byte[target] == 0U) {
    return UINT32_MAX;
  }
  cursor = target;
  while (1) {
    M68kInstructionIR instruction;
    SectionDecodeResult decode;
    uint32_t end;
    if (section_analysis->certain_code_start[cursor] != 0U &&
        section_analysis_context_decode(ctx, cursor, findings, &decode)) {
      instruction = decode.instruction;
      end = cursor + (uint32_t)instruction.byte_count;
      if (cursor <= target && target < end) {
        if (out_end != NULL) *out_end = end;
        return cursor;
      }
    }
    if (cursor == 0U || target - cursor >= 16U || section_analysis->certain_code_byte[cursor - 1U] == 0U) break;
    --cursor;
  }
  return UINT32_MAX;
}

static uint32_t find_nearest_emittable_label(const SectionAnalysisContext *ctx, const M68kSectionAnalysisIR *section_analysis,
    const uint8_t *generated_label_flags, size_t generated_label_count, uint32_t target, int prefer_non_code_only) {
  uint32_t delta;
  if (section_has_emittable_label(ctx, section_analysis, generated_label_flags, generated_label_count, target)) {
    if (!prefer_non_code_only || !offset_is_known_code_byte(section_analysis, target)) return target;
  }
  for (delta = 1U; delta < generated_label_count; ++delta) {
    uint32_t forward = target + delta;
    if (forward < generated_label_count &&
        section_has_emittable_label(ctx, section_analysis, generated_label_flags, generated_label_count, forward) &&
        (!prefer_non_code_only || !offset_is_known_code_byte(section_analysis, forward))) {
      return forward;
    }
    if (delta <= target) {
      uint32_t backward = target - delta;
      if (section_has_emittable_label(ctx, section_analysis, generated_label_flags, generated_label_count, backward) &&
          (!prefer_non_code_only || !offset_is_known_code_byte(section_analysis, backward))) {
        return backward;
      }
    }
    if (forward >= generated_label_count && delta > target) break;
  }
  return UINT32_MAX;
}

static uint32_t find_best_pc_relative_anchor(const SectionAnalysisContext *ctx, const M68kSectionAnalysisIR *section_analysis,
    const uint8_t *generated_label_flags, size_t generated_label_count, uint32_t target) {
  uint32_t anchor = find_nearest_emittable_label(ctx, section_analysis, generated_label_flags, generated_label_count, target, 1);
  if (anchor != UINT32_MAX) return anchor;
  return find_nearest_emittable_label(ctx, section_analysis, generated_label_flags, generated_label_count, target, 0);
}

static int append_label_statement(M68kSectionIR *section_ir, uint32_t offset, const GeneratedLabelKind *label_kinds,
    size_t label_kind_count, const M68kPresentationPolicy *presentation) {
  M68kStatementIR statement;
  char label_name[32];
  GeneratedLabelKind kind = GENERATED_LABEL_LOC;
  m68k_ir_statement_init(&statement);
  statement.kind = M68K_STATEMENT_LABEL;
  statement.offset = offset;
  if (label_kinds != NULL && offset < label_kind_count) kind = label_kinds[offset];
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
  while (offset + chunk < section_size) {
    uint32_t cursor = (uint32_t)(offset + chunk);
    if (section_analysis->certain_code_start != NULL &&
        offset + chunk < section_analysis->certain_code_size &&
        section_analysis->certain_code_start[offset + chunk] != 0U) {
      if (chunk != 0U) break;
    } else if (chunk != 0U &&
        section_has_any_label(section_analysis, generated_label_flags, generated_label_count, cursor)) {
      break;
    }
    ++chunk;
  }
  return chunk != 0U ? chunk : 1U;
}

static void set_generated_label_name(M68kSymbolRefIR *symbol_ref, uint32_t target, GeneratedLabelKind kind,
    const M68kPresentationPolicy *presentation);

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

static int annotate_immediate_fixup_label(const M68kObject *object, size_t section_index, uint32_t instruction_offset,
    M68kInstructionIR *instruction, size_t operand_index, M68kSectionAnalysisIR *section_analysis,
    uint8_t *generated_label_flags, size_t generated_label_count, GeneratedLabelKind *label_kinds,
    size_t label_kind_count, const M68kPresentationPolicy *presentation) {
  M68kInstructionIR parsed_instruction;
  const M68kInstructionIR *layout_instruction = instruction;
  const M68kAsmFormDef *form = instruction_assembler_form_local(instruction, &parsed_instruction);
  const M68kSection *section;
  char size_suffix;
  size_t word_index;
  size_t extension_index;
  if (object == NULL || instruction == NULL || section_analysis == NULL || operand_index >= instruction->operand_count)
    return 0;
  if (form == NULL) return 0;
  if (parsed_instruction.form_index != M68K_IR_INVALID_FORM_INDEX) layout_instruction = &parsed_instruction;
  if (section_index >= object->section_count) return 0;
  section = &object->sections[section_index];
  size_suffix = instruction_effective_size_suffix_local(layout_instruction, form);
  word_index = 1U + form->bound_word_count;
  for (extension_index = 0; extension_index < form->extension_count; ++extension_index) {
    const M68kAsmExtensionDef *extension = &g_m68k_asm_extensions[form->extension_start + extension_index];
    const M68kAsmOperandValue *operand = &layout_instruction->operands[extension->operand_index].value;
    switch (extension->kind) {
    case M68K_ASM_EXTENSION_EA_SINGLE_WORD:
      if (operand_uses_single_word_extension_local(operand)) word_index += 1U;
      break;
    case M68K_ASM_EXTENSION_EA_LONG_ADDRESS:
      if (operand_uses_long_address_extension_local(operand)) word_index += 2U;
      break;
    case M68K_ASM_EXTENSION_EA_IMMEDIATE:
      if (operand_uses_immediate_extension_local(operand)) {
        size_t extension_words = m68k_asm_operand_extension_word_count(form, operand, size_suffix);
        if (extension->operand_index == operand_index && extension_words >= 2U) {
          const M68kFixup *fixup = find_section_fixup_at_offset(object, section_index,
            instruction_offset + (uint32_t)(word_index * 2U), M68K_FIXUP_WIDTH_32);
          if (fixup != NULL && fixup->target_section_index == section_index &&
              fixup->offset + 4U <= section->data_size) {
            uint32_t target = m68k_read_u32be(section->data + fixup->offset);
            if (target < section_analysis->section_size &&
                section_has_any_label(section_analysis, generated_label_flags, generated_label_count, target)) {
              GeneratedLabelKind kind = GENERATED_LABEL_DAT;
              if (label_kinds != NULL && target < label_kind_count) kind = label_kinds[target];
              set_generated_label_name(&instruction->operands[operand_index].symbol_ref, target, kind, presentation);
              return 1;
            }
          }
        }
        word_index += extension_words;
      }
      break;
    case M68K_ASM_EXTENSION_EA_INDEX:
      word_index += m68k_asm_operand_extension_word_count(form, operand, size_suffix);
      break;
    case M68K_ASM_EXTENSION_LABEL_DISP16_IF_ZERO:
    case M68K_ASM_EXTENSION_LABEL_DISP16_ALWAYS:
    case M68K_ASM_EXTENSION_DISP16_ALWAYS:
      word_index += 1U;
      break;
    default:
      break;
    }
  }
  return 0;
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
    target = m68k_read_u32be(section->data + fixup->offset);
    if (target >= section_analysis->section_size) continue;
    update_generated_label_kind(label_kinds, section_analysis->section_size, target, GENERATED_LABEL_DAT);
    generated_label_flags[target] = 1U;
  }
}

static int build_self_section_long_exprs(const M68kObject *object, const M68kSectionAnalysisIR *section_analysis,
    GeneratedLabelKind *label_kinds, size_t label_kind_count, uint8_t *generated_label_flags, Arena *scratch_arena,
    char **out_long_exprs) {
  size_t fixup_index;
  if (object == NULL || section_analysis == NULL || generated_label_flags == NULL || scratch_arena == NULL ||
      out_long_exprs == NULL) return 0;
  for (fixup_index = 0; fixup_index < object->fixup_count; ++fixup_index) {
    const M68kFixup *fixup = &object->fixups[fixup_index];
    const M68kSection *section;
    uint32_t target;
    char expr[32];
    if (fixup->section_index != section_analysis->section_index ||
        fixup->kind != M68K_FIXUP_ABS || fixup->width != M68K_FIXUP_WIDTH_32 || !fixup->has_target_section ||
        fixup->target_section_index != section_analysis->section_index)
      continue;
    section = &object->sections[section_analysis->section_index];
    if (fixup->offset + 4U > section->data_size) continue;
    target = m68k_read_u32be(section->data + fixup->offset);
    if (target >= section_analysis->section_size) continue;
    if (build_absolute_long_expr(expr, sizeof(expr), target) != 0) return -1;
    out_long_exprs[fixup->offset] = arena_strdup(scratch_arena, expr);
    if (out_long_exprs[fixup->offset] == NULL) return -1;
    if (label_kinds != NULL) update_generated_label_kind(label_kinds, label_kind_count, target, GENERATED_LABEL_DAT);
    generated_label_flags[target] = 1U;
  }
  return 0;
}

static int word_expr_present_in_range(const char *const *word_exprs, size_t section_size, uint32_t start, size_t span) {
  size_t index;
  if (word_exprs == NULL) return 0;
  for (index = 0; index < span; ++index) {
    uint32_t offset = start + (uint32_t)index;
    if (offset >= section_size) break;
    if (word_exprs[offset] != NULL) return 1;
  }
  return 0;
}

static int long_expr_present_in_range(const char *const *long_exprs, size_t section_size, uint32_t start, size_t span) {
  size_t index;
  if (long_exprs == NULL) return 0;
  for (index = 0; index < span; ++index) {
    uint32_t offset = start + (uint32_t)index;
    if (offset >= section_size) break;
    if (long_exprs[offset] != NULL) return 1;
  }
  return 0;
}

static int append_shaped_data_span(const M68kObject *object, size_t section_index, const SectionAnalysisContext *ctx,
    const M68kSectionAnalysisIR *section_analysis, const GeneratedLabelKind *label_kinds, M68kSectionIR *section_ir,
    uint32_t offset, const uint8_t *data, size_t size, const char *const *word_exprs, const char *const *long_exprs,
    const M68kPresentationPolicy *presentation, const char *comment) {
  int prefer_strings = (presentation == NULL) ? 1 : (presentation->prefer_strings != 0U);
  int prefer_long_data = (presentation == NULL) ? 1 : (presentation->prefer_long_data != 0U);
  size_t cursor = 0U;
  int span_has_word_expr = 0;
  if (word_exprs != NULL) {
    size_t probe;
    for (probe = 0; probe < size; ++probe) {
      if (offset + probe < section_analysis->section_size && word_exprs[offset + probe] != NULL) {
        span_has_word_expr = 1;
        break;
      }
    }
  }
  while (cursor < size) {
    uint32_t next_fixup_offset = 0U;
    int has_next_fixup = find_next_section_fixup_offset(object, section_index, offset + (uint32_t)cursor + 1U,
      M68K_FIXUP_WIDTH_32, &next_fixup_offset);
    uint32_t target = 0U;
    if (word_exprs != NULL && offset + cursor < section_analysis->section_size &&
        word_exprs[offset + cursor] != NULL && (size - cursor) >= 2U) {
      char expr_text[80];
      uint32_t expr_target = 0U;
      uint32_t expr_base = 0U;
      int32_t expr_target_addend = 0;
      if (parse_relative_word_expr_targets(word_exprs[offset + cursor], &expr_target, &expr_base, &expr_target_addend)) {
        GeneratedLabelKind base_kind = GENERATED_LABEL_DAT;
        GeneratedLabelKind target_kind = GENERATED_LABEL_LOC;
        char base_name[32];
        char target_name[32];
        uint32_t target_anchor = expr_target;
        if (ctx != NULL &&
            !section_has_emittable_label(ctx, section_analysis, section_analysis->generated_label_flags,
              section_analysis->generated_label_size, expr_target)) {
          uint32_t anchor = find_nearest_emittable_label(ctx, section_analysis, section_analysis->generated_label_flags,
            section_analysis->generated_label_size, expr_target, 0);
          if (anchor != UINT32_MAX) {
            expr_target_addend += (int32_t)(expr_target - anchor);
            target_anchor = anchor;
          }
        }
        if (label_kinds != NULL && expr_base < section_analysis->generated_label_size)
          base_kind = label_kinds[expr_base];
        if (label_kinds != NULL && target_anchor < section_analysis->generated_label_size)
          target_kind = label_kinds[target_anchor];
        set_generated_name(base_name, sizeof(base_name), expr_base, base_kind, presentation);
        set_generated_name(target_name, sizeof(target_name), target_anchor, target_kind, presentation);
        if (expr_target_addend != 0) {
          snprintf(expr_text, sizeof(expr_text), "%s%+d-%s", target_name, (int)expr_target_addend, base_name);
        } else {
          snprintf(expr_text, sizeof(expr_text), "%s-%s", target_name, base_name);
        }
      } else if (parse_relative_word_expr_here(word_exprs[offset + cursor], &expr_target, &expr_target_addend)) {
        GeneratedLabelKind target_kind = GENERATED_LABEL_LOC;
        char target_name[32];
        uint32_t target_anchor = expr_target;
        if (ctx != NULL &&
            !section_has_emittable_label(ctx, section_analysis, section_analysis->generated_label_flags,
              section_analysis->generated_label_size, expr_target)) {
          uint32_t anchor = find_nearest_emittable_label(ctx, section_analysis, section_analysis->generated_label_flags,
            section_analysis->generated_label_size, expr_target, 0);
          if (anchor != UINT32_MAX) {
            expr_target_addend += (int32_t)(expr_target - anchor);
            target_anchor = anchor;
          }
        }
        if (label_kinds != NULL && target_anchor < section_analysis->generated_label_size)
          target_kind = label_kinds[target_anchor];
        set_generated_name(target_name, sizeof(target_name), target_anchor, target_kind, presentation);
        if (expr_target_addend != 0) {
          snprintf(expr_text, sizeof(expr_text), "%s%+d-*", target_name, (int)expr_target_addend);
        } else {
          snprintf(expr_text, sizeof(expr_text), "%s-*", target_name);
        }
      } else {
        snprintf(expr_text, sizeof(expr_text), "%s", word_exprs[offset + cursor]);
      }
      if (append_expr_data_statement(section_ir, offset + (uint32_t)cursor, M68K_DATA_ITEM_WORDS, data + cursor, 2U,
            expr_text, cursor == 0U ? comment : NULL) != 0) {
        return -1;
      }
      cursor += 2U;
      continue;
    }
    if (long_exprs != NULL && offset + cursor < section_analysis->section_size &&
        long_exprs[offset + cursor] != NULL && (size - cursor) >= 4U) {
      char expr_name[32];
      GeneratedLabelKind kind = GENERATED_LABEL_DAT;
      if (!parse_absolute_long_expr_target(long_exprs[offset + cursor], &target) ||
          target >= section_analysis->section_size) goto no_fixup_expr;
      if (label_kinds != NULL) kind = label_kinds[target];
      set_generated_name(expr_name, sizeof(expr_name), target, kind, presentation);
      if (append_expr_data_statement(section_ir, offset + (uint32_t)cursor, M68K_DATA_ITEM_LONGS, data + cursor, 4U,
          expr_name, cursor == 0U ? comment : NULL) != 0) {
        return -1;
      }
      cursor += 4U;
      continue;
    }
no_fixup_expr:
    if (size <= 16U && cursor == 0U && !span_has_word_expr &&
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
        !word_expr_present_in_range(word_exprs, section_analysis->section_size, offset + (uint32_t)cursor, 4U) &&
        !long_expr_present_in_range(long_exprs, section_analysis->section_size, offset + (uint32_t)cursor, 4U) &&
        (!has_next_fixup || next_fixup_offset >= offset + (uint32_t)cursor + 4U)) {
      size_t long_count = 4U;
      while (cursor + long_count + 4U <= size && (((offset + (uint32_t)cursor + (uint32_t)long_count) & 3U) == 0U) &&
          !word_expr_present_in_range(word_exprs, section_analysis->section_size,
            offset + (uint32_t)cursor + (uint32_t)long_count, 4U) &&
          !long_expr_present_in_range(long_exprs, section_analysis->section_size,
            offset + (uint32_t)cursor + (uint32_t)long_count, 4U) &&
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
        if (word_exprs != NULL && offset + (uint32_t)cursor + (uint32_t)byte_run < section_analysis->section_size &&
            word_exprs[offset + (uint32_t)cursor + (uint32_t)byte_run] != NULL) {
          break;
        }
        if (long_exprs != NULL && offset + (uint32_t)cursor + (uint32_t)byte_run < section_analysis->section_size &&
            long_exprs[offset + (uint32_t)cursor + (uint32_t)byte_run] != NULL) {
          break;
        }
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

static void set_current_relative_symbol_name(M68kSymbolRefIR *symbol_ref, int32_t delta) {
  if (symbol_ref == NULL) return;
  symbol_ref->has_name = 1;
  symbol_ref->name_is_generated = 0U;
  symbol_ref->kind = M68K_IR_SYMBOL_REF_PC_REL;
  symbol_ref->addend = 0;
  if (delta == 0) {
    snprintf(symbol_ref->name, sizeof(symbol_ref->name), "*");
  } else if (delta > 0) {
    snprintf(symbol_ref->name, sizeof(symbol_ref->name), "*+%d", (int)delta);
  } else {
    snprintf(symbol_ref->name, sizeof(symbol_ref->name), "*%d", (int)delta);
  }
}

static void add_unstable_branch_target_violation(M68kSectionAnalysisIR *section_analysis, uint32_t offset,
    uint32_t target) {
  char message[128];
  if (section_analysis == NULL) return;
  snprintf(message, sizeof(message),
    "branch target $%04X has no stable label; forced generated label", (unsigned)target);
  m68k_ir_section_analysis_add_violation(section_analysis, offset, M68K_VIOLATION_INVALID_INTERIOR_REFERENCE, message);
}

static int operand_has_symbol_name(const M68kOperandIR *operand) {
  return operand != NULL && operand->symbol_ref.has_name != 0U && operand->symbol_ref.name[0] != '\0';
}

static void annotate_instruction_labels(const M68kObject *object, size_t section_index, M68kInstructionIR *instruction,
    uint32_t offset, const SectionAnalysisContext *ctx, M68kSectionAnalysisIR *section_analysis,
    uint8_t *generated_label_flags, size_t generated_label_count, GeneratedLabelKind *label_kinds,
    size_t label_kind_count, const M68kPresentationPolicy *presentation) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  uint32_t label_base;
  if (instruction == NULL || section_analysis == NULL) return;
  metadata = instruction_sim_metadata(instruction);
  label_base = offset + 2U;
  for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    if (annotate_immediate_fixup_label(object, section_index, offset, instruction, operand_index, section_analysis,
          generated_label_flags, generated_label_count, label_kinds, label_kind_count, presentation))
      continue;
    if (operand->kind == M68K_ASM_OPERAND_LABEL) {
      uint32_t target = label_base + (uint32_t)((int32_t)operand->value.value);
      const M68kSection *section = (object != NULL && section_index < object->section_count)
        ? &object->sections[section_index] : NULL;
      if (section != NULL &&
          !instruction_transfer_target(instruction, section->data + offset, section->data_size - offset, offset,
            (uint32_t)section->data_size, &target) &&
          !instruction_branch_target(instruction, offset, &target)) {}
      else if (section == NULL && !instruction_branch_target(instruction, offset, &target)) {}
      if (section_has_any_label(section_analysis, generated_label_flags, generated_label_count, target)) {
        GeneratedLabelKind kind = GENERATED_LABEL_LOC;
        if (label_kinds != NULL && target < label_kind_count) {
          kind = label_kinds[target];
        } else if (instruction_is_call_transfer(instruction)) {
          kind = GENERATED_LABEL_SUB;
        }
        set_generated_label_name(&operand->symbol_ref, target, kind, presentation);
      } else if (section != NULL && target < generated_label_count &&
          offset_decodes_as_instruction(ctx, target)) {
        GeneratedLabelKind kind = instruction_is_call_transfer(instruction) ? GENERATED_LABEL_SUB : GENERATED_LABEL_LOC;
        generated_label_flags[target] = 1U;
        if (label_kinds != NULL && target < label_kind_count && kind > label_kinds[target]) label_kinds[target] = kind;
        set_generated_label_name(&operand->symbol_ref, target, kind, presentation);
      } else if (target < generated_label_count) {
        GeneratedLabelKind kind = instruction_is_call_transfer(instruction) ? GENERATED_LABEL_SUB : GENERATED_LABEL_LOC;
        add_unstable_branch_target_violation(section_analysis, offset, target);
        generated_label_flags[target] = 1U;
        if (label_kinds != NULL && target < label_kind_count && kind > label_kinds[target]) label_kinds[target] = kind;
        set_generated_label_name(&operand->symbol_ref, target, kind, presentation);
      } else {
        add_unstable_branch_target_violation(section_analysis, offset, target);
      }
      continue;
    }
    if (metadata == NULL) continue;
    {
      uint32_t target;
      if (instruction_pc_relative_ea_target(instruction, metadata, (uint8_t)operand_index, (uint32_t)offset,
            (uint32_t)generated_label_count, &target)) {
        uint32_t base = find_enclosing_code_start(section_analysis, target);
        uint32_t anchor = UINT32_MAX;
        const M68kSection *section = (object != NULL && section_index < object->section_count) ? &object->sections[section_index] : NULL;
        uint32_t end = UINT32_MAX;
        uint32_t interior_start = find_enclosing_instruction_start(ctx, section_analysis, NULL, target, &end);
        GeneratedLabelKind kind;
        if (section_has_any_label(section_analysis, generated_label_flags, generated_label_count, target) &&
            (interior_start == UINT32_MAX || interior_start == target)) {
          kind = GENERATED_LABEL_DAT;
          if (label_kinds != NULL && target < label_kind_count) kind = label_kinds[target];
          set_generated_label_name(&operand->symbol_ref, target, kind, presentation);
        } else if (interior_start != UINT32_MAX && interior_start != target) {
          if (interior_start != UINT32_MAX && end < generated_label_count) {
            kind = (section != NULL && offset_is_known_code_byte(section_analysis, end) &&
                offset_decodes_as_instruction(ctx, end)) ? GENERATED_LABEL_LOC : GENERATED_LABEL_DAT;
            generated_label_flags[end] = 1U;
            if (label_kinds != NULL && end < label_kind_count && kind > label_kinds[end]) label_kinds[end] = kind;
            set_generated_label_name(&operand->symbol_ref, end, kind, presentation);
            operand->symbol_ref.addend = (int32_t)(target - end);
          } else {
            char message[128];
            snprintf(message, sizeof(message), "no stable label anchor for pc-relative target $%04X", (unsigned)target);
            m68k_ir_section_analysis_add_violation(section_analysis, offset, M68K_VIOLATION_INVALID_INTERIOR_REFERENCE, message);
            set_current_relative_symbol_name(&operand->symbol_ref, (int32_t)(target - offset));
          }
        } else if ((anchor = find_best_pc_relative_anchor(ctx, section_analysis, generated_label_flags, generated_label_count, target))
            != UINT32_MAX) {
          kind = GENERATED_LABEL_DAT;
          if (label_kinds != NULL && anchor < label_kind_count) kind = label_kinds[anchor];
          set_generated_label_name(&operand->symbol_ref, anchor, kind, presentation);
          operand->symbol_ref.addend = (int32_t)(target - anchor);
        } else if (base != UINT32_MAX &&
            section_has_emittable_label(ctx, section_analysis, generated_label_flags, generated_label_count, base)) {
          kind = GENERATED_LABEL_LOC;
          if (label_kinds != NULL && base < label_kind_count) kind = label_kinds[base];
          set_generated_label_name(&operand->symbol_ref, base, kind, presentation);
        } else {
          base = find_enclosing_any_label(section_analysis, generated_label_flags, generated_label_count, target);
          if (base != UINT32_MAX && base != target) {
            kind = GENERATED_LABEL_DAT;
            if (label_kinds != NULL && base < label_kind_count) kind = label_kinds[base];
            if (kind == GENERATED_LABEL_DAT) {
              set_generated_label_name(&operand->symbol_ref, base, kind, presentation);
              operand->symbol_ref.addend = (int32_t)(target - base);
            } else {
              set_current_relative_symbol_name(&operand->symbol_ref, (int32_t)(target - offset));
            }
          } else if (base == target) {
            kind = GENERATED_LABEL_DAT;
            if (label_kinds != NULL && base < label_kind_count) kind = label_kinds[base];
            set_generated_label_name(&operand->symbol_ref, base, kind, presentation);
          }
        }
      } else if (instruction_render_operand_target(instruction, metadata, (uint8_t)operand_index, (uint32_t)offset,
            (uint32_t)generated_label_count, &target)) {
        const M68kSection *section = (object != NULL && section_index < object->section_count)
          ? &object->sections[section_index] : NULL;
        uint32_t end = UINT32_MAX;
        uint32_t interior_start = UINT32_MAX;
        if (instruction_target_operand_is_brief_indexed_pc(instruction)) {
          interior_start = find_enclosing_instruction_start(ctx, section_analysis, NULL, target, &end);
          if (interior_start != UINT32_MAX && interior_start != target) {
            GeneratedLabelKind kind = GENERATED_LABEL_DAT;
            if (end < generated_label_count) {
              if (section != NULL && offset_is_known_code_byte(section_analysis, end) &&
                  offset_decodes_as_instruction(ctx, end)) {
                kind = GENERATED_LABEL_LOC;
              }
              generated_label_flags[end] = 1U;
              if (label_kinds != NULL && end < label_kind_count && kind > label_kinds[end]) label_kinds[end] = kind;
              set_generated_label_name(&operand->symbol_ref, end, kind, presentation);
              operand->symbol_ref.addend = (int32_t)(target - end);
              continue;
            }
            set_current_relative_symbol_name(&operand->symbol_ref, (int32_t)(target - offset));
            continue;
          }
        }
        if (!section_has_any_label(section_analysis, generated_label_flags, generated_label_count, target)) {
          if (instruction_operand_is_render_pc_relative(instruction, metadata, (uint8_t)operand_index) &&
              target < generated_label_count) {
            GeneratedLabelKind generated_kind = GENERATED_LABEL_DAT;
            if (offset_is_known_code_byte(section_analysis, target) &&
                section_analysis_context_decode(ctx, target, NULL, NULL) != 0) {
              generated_kind = GENERATED_LABEL_LOC;
            }
            generated_label_flags[target] = 1U;
            if (label_kinds != NULL && target < label_kind_count && generated_kind > label_kinds[target]) {
              label_kinds[target] = generated_kind;
            }
          } else {
            continue;
          }
        }
        GeneratedLabelKind kind = instruction_is_call_transfer(instruction) ? GENERATED_LABEL_SUB : GENERATED_LABEL_LOC;
        if (label_kinds != NULL && target < label_kind_count) {
          kind = label_kinds[target];
        }
        set_generated_label_name(&operand->symbol_ref, target, kind, presentation);
      }
    }
  }
}

static void stabilize_direct_control_labels(const M68kSection *section, M68kInstructionIR *instruction, uint32_t offset,
    const SectionAnalysisContext *ctx, M68kSectionAnalysisIR *section_analysis,
    uint8_t *generated_label_flags, size_t generated_label_count, GeneratedLabelKind *label_kinds, size_t label_kind_count,
    const M68kPresentationPolicy *presentation) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (section == NULL || instruction == NULL || section_analysis == NULL) return;
  if (!instruction_is_call_transfer(instruction) &&
      !instruction_is_unconditional_transfer(instruction) &&
      !is_conditional_transfer(instruction)) {
    return;
  }
  metadata = instruction_sim_metadata(instruction);
  for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    uint32_t target;
    GeneratedLabelKind kind;
    if (metadata != NULL && metadata->target_operand_index != 0xFFU && operand_index != metadata->target_operand_index)
      continue;
    if (!instruction_transfer_target(instruction, section->data + offset, section->data_size - offset, offset,
          (uint32_t)section->data_size, &target) &&
        !instruction_branch_target(instruction, offset, &target)) {
      continue;
    }
    if (section_has_any_label(section_analysis, generated_label_flags, generated_label_count, target)) {
      kind = instruction_is_call_transfer(instruction) ? GENERATED_LABEL_SUB : GENERATED_LABEL_LOC;
      if (label_kinds != NULL && target < label_kind_count) kind = label_kinds[target];
      set_generated_label_name(&operand->symbol_ref, target, kind, presentation);
      continue;
    }
    if (target < generated_label_count && offset_decodes_as_instruction(ctx, target)) {
      kind = instruction_is_call_transfer(instruction) ? GENERATED_LABEL_SUB : GENERATED_LABEL_LOC;
      generated_label_flags[target] = 1U;
      if (label_kinds != NULL && target < label_kind_count && kind > label_kinds[target]) label_kinds[target] = kind;
      set_generated_label_name(&operand->symbol_ref, target, kind, presentation);
      continue;
    }
    if (target < generated_label_count) {
      kind = instruction_is_call_transfer(instruction) ? GENERATED_LABEL_SUB : GENERATED_LABEL_LOC;
      add_unstable_branch_target_violation(section_analysis, offset, target);
      generated_label_flags[target] = 1U;
      if (label_kinds != NULL && target < label_kind_count && kind > label_kinds[target]) label_kinds[target] = kind;
      set_generated_label_name(&operand->symbol_ref, target, kind, presentation);
      continue;
    }
    add_unstable_branch_target_violation(section_analysis, offset, target);
  }
}

static void preseed_direct_control_labels(const M68kObject *object, const M68kSection *section,
    const SectionAnalysisContext *ctx, M68kSectionAnalysisIR *section_analysis, uint8_t *generated_label_flags,
    size_t generated_label_count, GeneratedLabelKind *label_kinds, size_t label_kind_count,
    const M68kPresentationPolicy *presentation) {
  uint32_t offset;
  M68kInstructionIR prev_instruction;
  uint8_t have_prev_instruction = 0U;
  uint8_t prev_rendered_as_code = 0U;
  if (section == NULL || ctx == NULL || section_analysis == NULL || generated_label_flags == NULL) return;
  for (offset = 0U; offset < section->data_size;) {
    SectionDecodeResult decode;
    M68kInstructionIR instruction;
    if (should_render_code_at_offset(section, section_analysis, offset, prev_rendered_as_code,
          have_prev_instruction, &prev_instruction)) {
      if (section_analysis_context_decode(ctx, offset, NULL, &decode)) {
        instruction = decode.instruction;
        annotate_instruction_labels(object, section_analysis->section_index, &instruction, offset, ctx,
          section_analysis, generated_label_flags, generated_label_count, label_kinds, label_kind_count, presentation);
        stabilize_direct_control_labels(section, &instruction, offset, ctx, section_analysis, generated_label_flags,
          generated_label_count, label_kinds, label_kind_count, presentation);
        prev_instruction = instruction;
        have_prev_instruction = 1U;
        prev_rendered_as_code = 1U;
        offset += (uint32_t)instruction.byte_count;
        continue;
      }
      prev_rendered_as_code = 0U;
      offset += (uint32_t)compute_data_span_chunk(section_analysis, generated_label_flags, section->data_size, offset,
        section->data_size);
      continue;
    }
    prev_rendered_as_code = 0U;
    offset += (uint32_t)compute_data_span_chunk(section_analysis, generated_label_flags, section->data_size, offset,
      section->data_size);
  }
}

static int should_render_code_at_offset(const M68kSection *section, const M68kSectionAnalysisIR *section_analysis,
    uint32_t offset, uint8_t prev_rendered_as_code, uint8_t have_prev_instruction,
    const M68kInstructionIR *prev_instruction) {
  if (section == NULL || section_analysis == NULL) return 0;
  if (section->kind != M68K_SECTION_CODE) return 0;
  if (offset >= section_analysis->certain_code_size) return 0;
  if (section_analysis->certain_code_start != NULL && section_analysis->certain_code_start[offset] != 0U) return 1;
  if (section_analysis_has_string_dispatch_target(section_analysis, offset)) return 1;
  return prev_rendered_as_code != 0U && have_prev_instruction != 0U &&
    prev_instruction != NULL && !instruction_stops_fallthrough(prev_instruction);
}

static void append_unstable_direct_control_violation_comment(const M68kSection *section, M68kInstructionIR *instruction,
    uint32_t offset, char *buf, size_t buf_size) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  uint32_t target;
  char message[160];
  if (section == NULL || instruction == NULL || buf == NULL || buf_size == 0U) return;
  if (!instruction_is_call_transfer(instruction) &&
      !instruction_is_unconditional_transfer(instruction) &&
      !is_conditional_transfer(instruction)) {
    return;
  }
  metadata = instruction_sim_metadata(instruction);
  for (operand_index = 0; operand_index < instruction->operand_count; ++operand_index) {
    M68kOperandIR *operand = &instruction->operands[operand_index];
    if (metadata != NULL && metadata->target_operand_index != 0xFFU && operand_index != metadata->target_operand_index)
      continue;
    if (operand->kind != M68K_ASM_OPERAND_LABEL || operand_has_symbol_name(operand)) continue;
    if (!instruction_transfer_target(instruction, section->data + offset, section->data_size - offset, offset,
          (uint32_t)section->data_size, &target) &&
        !instruction_branch_target(instruction, offset, &target)) {
      continue;
    }
    snprintf(message, sizeof(message),
      "VIOLATION: branch target $%04X has no stable label; rendered as current-relative", (unsigned)target);
    append_statement_comment(buf, buf_size, message);
  }
}

int build_section_ir(const M68kObject *object, const M68kSection *section,
    M68kSectionAnalysisIR *section_analysis,
    const M68kAnalysisPolicy *analysis_policy, M68kAnalysisFindings *findings, const M68kRenderPolicy *policy,
    M68kSectionIR *out_section_ir, M68kDiagSink diagnostics) {
  GeneratedLabelKind *label_kinds = NULL;
  uint8_t *generated_label_flags = NULL;
  SectionAnalysisContext analysis_ctx = {0};
  size_t offset = 0;
  int result = -1;
  M68kInstructionIR prev_instruction = {0};
  uint8_t have_prev_instruction = 0U;
  uint8_t prev_rendered_as_code = 0U;
  (void)findings; (void)diagnostics;
  if (m68k_ir_section_create(out_section_ir) != 0) goto cleanup;
  if (m68k_ir_section_set_name(out_section_ir,
        (section->name != NULL && section->name[0] != '\0') ? section->name : "section") != 0) goto cleanup;
  out_section_ir->kind = section->kind;
  out_section_ir->size = section->size;
  if (section->kind == M68K_SECTION_BSS) {
    result = 0;
    goto cleanup;
  }
  if (section_analysis_context_init(&analysis_ctx, object, section, analysis_policy, section_analysis->arena) != 0) goto cleanup;
  if (section_analysis->generated_label_size == section->data_size) {
    label_kinds = section_analysis->generated_label_kinds;
    generated_label_flags = section_analysis->generated_label_flags;
  }
  preseed_direct_control_labels(object, section, &analysis_ctx, section_analysis, generated_label_flags,
    section->data_size, label_kinds, section->data_size, policy != NULL ? &policy->presentation : NULL);
  while (offset < section->data_size) {
    M68kInstructionIR instruction;
    SectionDecodeResult decode;
    if (section_has_any_label(section_analysis, generated_label_flags, section->data_size, (uint32_t)offset) &&
        append_label_statement(out_section_ir, (uint32_t)offset, label_kinds, section->data_size,
          policy != NULL ? &policy->presentation : NULL) != 0) goto cleanup;
    if (should_render_code_at_offset(section, section_analysis, (uint32_t)offset, prev_rendered_as_code,
          have_prev_instruction, &prev_instruction)) {
      char violation[128];
      violation[0] = '\0';
      if (section_analysis_context_decode(&analysis_ctx, (uint32_t)offset, NULL, &decode)) {
        instruction = decode.instruction;
        annotate_instruction_labels(object, section_analysis->section_index, &instruction, (uint32_t)offset,
          &analysis_ctx, section_analysis, generated_label_flags, section->data_size, label_kinds,
          section->data_size, policy != NULL ? &policy->presentation : NULL);
        stabilize_direct_control_labels(section, &instruction, (uint32_t)offset, &analysis_ctx,
          section_analysis, generated_label_flags, section->data_size, label_kinds, section->data_size,
          policy != NULL ? &policy->presentation : NULL);
        annotate_platform_symbol_refs(&analysis_ctx, section_analysis, (uint32_t)offset, &instruction);
        collect_section_violation_comments(section_analysis, (uint32_t)offset, violation, sizeof(violation));
        append_unstable_direct_control_violation_comment(section, &instruction, (uint32_t)offset, violation,
          sizeof(violation));
        if (policy != NULL && policy->syntax.syntax_mode == M68K_IR_SYNTAX_VASM) {
          append_vasm_normalized_byte_immediate_note(violation, sizeof(violation), &instruction,
            section->data + offset, instruction.byte_count);
        } else {
          apply_exact_byte_immediate_render_values(&instruction, section->data + offset, instruction.byte_count);
        }
        collect_recovered_platform_call_comments(section_analysis, (uint32_t)offset, violation, sizeof(violation));
        if (find_any_recovered_platform_call(section_analysis, (uint32_t)offset) == NULL) {
          PlatformResolvedIndirectInfo platform_info;
          char note[160];
          platform_info = platform_resolve_indirect_control(&analysis_ctx, section_analysis, (uint32_t)offset,
            &instruction);
          if (platform_info.kind != PLATFORM_RESOLVED_INDIRECT_NONE &&
              format_platform_resolved_indirect_note(&platform_info, note, sizeof(note))) {
            append_statement_comment(violation, sizeof(violation), note);
          }
        }
        if (find_any_recovered_platform_call(section_analysis, (uint32_t)offset) == NULL) {
          PlatformResolvedIndirectInfo platform_info;
          char note[160];
          platform_info = platform_resolve_additional_indirect_note(&analysis_ctx, section_analysis, (uint32_t)offset,
            &instruction);
          if (platform_info.kind != PLATFORM_RESOLVED_INDIRECT_NONE &&
              format_platform_resolved_indirect_note(&platform_info, note, sizeof(note))) {
            append_statement_comment(violation, sizeof(violation), note);
          }
        }
        if (append_instruction_statement( out_section_ir, (uint32_t)offset, &instruction,
              violation[0] != '\0' ? violation : NULL) != 0) goto cleanup;
        prev_instruction = instruction;
        have_prev_instruction = 1U;
        prev_rendered_as_code = 1U;
        offset += instruction.byte_count;
      } else {
        size_t chunk = compute_data_span_chunk(section_analysis, generated_label_flags, section->data_size, offset,
          section->data_size);
        if (append_shaped_data_span( object, section_analysis->section_index, &analysis_ctx, section_analysis, label_kinds,
            out_section_ir, (uint32_t)offset, section->data + offset, chunk, (const char *const *)section_analysis->word_exprs,
            (const char *const *)section_analysis->long_exprs,
            policy != NULL ? &policy->presentation : NULL,
            "decode failed in reachable code; region emitted as data") != 0) goto cleanup;
        prev_rendered_as_code = 0U;
        offset += chunk;
      }
    } else {
      size_t chunk = compute_data_span_chunk(section_analysis, generated_label_flags, section->data_size, offset,
        section->data_size);
      if (append_shaped_data_span( object, section_analysis->section_index, &analysis_ctx, section_analysis, label_kinds,
          out_section_ir, (uint32_t)offset, section->data + offset, chunk, (const char *const *)section_analysis->word_exprs,
          (const char *const *)section_analysis->long_exprs,
          policy != NULL ? &policy->presentation : NULL, NULL) != 0) goto cleanup;
      prev_rendered_as_code = 0U;
      offset += chunk;
    }
  }
  result = 0;

cleanup:
  return result;
}
