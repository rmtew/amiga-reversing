#include "m68k_decode_ir.h"

#include "m68k_assembler.h"
#include "m68k_disassembler.h"
#include "m68k_instruction_spec.h"
#include "m68k_simulator.h"
#include "platform_common.h"

#include <string.h>

static int append_decode_section(ArenaBuilder *builder, M68kDecodeSectionIR **out_section) {
  if (builder == NULL || out_section == NULL) return -1;
  *out_section = ARENA_BUILDER_APPEND_TYPED(builder, M68kDecodeSectionIR);
  if (*out_section == NULL) return -1;
  memset(*out_section, 0, sizeof(**out_section));
  return 0;
}

static int candidate_index_at_offset(const M68kDecodeSectionIR *section, uint32_t offset,
    size_t *out_index, int *out_found) {
  size_t lo = 0U;
  size_t hi;
  if (section == NULL || out_index == NULL || out_found == NULL) return -1;
  hi = section->candidate_count;
  while (lo < hi) {
    size_t mid = lo + ((hi - lo) / 2U);
    uint32_t candidate_offset = section->candidates[mid].offset;
    if (candidate_offset == offset) {
      *out_index = mid;
      *out_found = 1;
      return 0;
    }
    if (candidate_offset < offset) lo = mid + 1U;
    else hi = mid;
  }
  *out_index = lo;
  *out_found = 0;
  return 0;
}

static int insert_candidate_sorted(M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    const M68kDecodeCandidate **out_candidate) {
  M68kDecodeCandidate *grown;
  size_t next_capacity;
  size_t index = 0U;
  int found = 0;
  if (section == NULL || candidate == NULL) return -1;
  if (candidate_index_at_offset(section, candidate->offset, &index, &found) != 0) return -1;
  if (found) {
    if (out_candidate != NULL) *out_candidate = &section->candidates[index];
    return 0;
  }
  if (section->candidate_count == section->candidate_capacity) {
    next_capacity = section->candidate_capacity == 0U ? 32U : section->candidate_capacity * 2U;
    grown = (M68kDecodeCandidate *)arena_realloc_copy(section->owner_arena, section->candidates,
      section->candidate_capacity * sizeof(*grown), next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    section->candidates = grown;
    section->candidate_capacity = next_capacity;
  }
  if (index < section->candidate_count) {
    memmove(&section->candidates[index + 1U], &section->candidates[index],
      (section->candidate_count - index) * sizeof(section->candidates[0]));
  }
  section->candidates[index] = *candidate;
  ++section->candidate_count;
  if (out_candidate != NULL) *out_candidate = &section->candidates[index];
  return 0;
}

static int append_target(M68kDecodeCandidate *candidate, uint8_t kind, size_t section_index, uint32_t offset,
    uint8_t has_operand, uint8_t operand_index) {
  M68kDecodeTarget *target;
  if (candidate == NULL || candidate->target_count >= M68K_DECODE_IR_MAX_TARGETS) return 0;
  target = &candidate->targets[candidate->target_count++];
  memset(target, 0, sizeof(*target));
  target->kind = kind;
  target->has_section = 1U;
  target->has_operand = has_operand;
  target->operand_index = operand_index;
  target->section_index = section_index;
  target->offset = offset;
  return 0;
}

static int target_in_section(uint32_t target_offset, uint32_t section_size) {
  return target_offset < section_size;
}

static int32_t signed_operand_value(const M68kAsmOperandValue *operand) {
  return (int32_t)operand->value;
}

static uint8_t decode_target_kind_for_flow(uint8_t flow_kind) {
  switch (flow_kind) {
    case M68K_SIM_FLOW_BRANCH: return M68K_DECODE_TARGET_BRANCH;
    case M68K_SIM_FLOW_CALL: return M68K_DECODE_TARGET_CALL;
    case M68K_SIM_FLOW_JUMP: return M68K_DECODE_TARGET_JUMP;
    default: return 0U;
  }
}

static void collect_control_targets(M68kDecodeCandidate *candidate, const M68kDisasmResult *decoded,
    size_t section_index, uint32_t section_size) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  const M68kAsmOperandValue *operand;
  uint8_t target_kind;
  uint8_t target_operand_index;
  uint32_t branch_base;
  uint32_t target_offset;
  int32_t disp;
  if (candidate == NULL || decoded == NULL || decoded->operand_count == 0U) return;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || metadata->target_operand_index >= decoded->operand_count ||
      metadata->target_operand_index >= M68K_DECODE_IR_MAX_OPERANDS) {
    return;
  }
  target_kind = decode_target_kind_for_flow(metadata->flow_kind);
  if (target_kind == 0U) return;
  target_operand_index = metadata->target_operand_index;
  if (metadata->operand_access_kinds[target_operand_index] != M68K_SIM_ACCESS_BRANCH_TARGET) return;
  operand = &decoded->operands[target_operand_index];
  branch_base = candidate->offset + 2U;
  if (operand->kind == M68K_ASM_OPERAND_LABEL) {
    disp = signed_operand_value(operand);
    target_offset = (uint32_t)((int32_t)branch_base + disp);
    (void)append_target(candidate, target_kind, section_index, target_offset, 1U, target_operand_index);
  } else if (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 7U && operand->ea_reg == 1U &&
      target_in_section(operand->value, section_size)) {
    (void)append_target(candidate, target_kind, section_index, operand->value, 1U, target_operand_index);
  }
}

static void collect_pc_relative_ea_targets(M68kDecodeCandidate *candidate, size_t section_index,
    uint32_t section_size) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  M68kAsmOperandValue layout_operands[M68K_DECODE_IR_MAX_OPERANDS];
  size_t operand_index;
  if (candidate == NULL || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  for (operand_index = 0U; operand_index < candidate->operand_count; ++operand_index) {
    layout_operands[operand_index] = candidate->operands[operand_index];
    layout_operands[operand_index].kind = candidate->operand_kinds[operand_index];
  }
  for (operand_index = 0U; operand_index < instruction.operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction.operands[operand_index];
    uint8_t shape = m68k_instruction_operand_decoded_ea_shape(operand);
    size_t relative_base;
    uint32_t pc_base;
    uint32_t target_offset = 0U;
    uint8_t target_kind = M68K_DECODE_TARGET_DATA;
    if (m68k_instruction_decoded_ea_target_kind(operand, shape, 1) != 2U) continue;
    relative_base = m68k_asm_operand_relative_base_offset(candidate->asm_form_index, layout_operands,
      candidate->operand_count, candidate->size_suffix, operand_index, 0);
    if (relative_base > UINT32_MAX - candidate->offset) continue;
    pc_base = candidate->offset + (uint32_t)relative_base;
    if (!m68k_instruction_decoded_ea_target(operand, shape, pc_base, section_size, 1, &target_offset))
      continue;
    if (shape != M68K_SIM_EA_SHAPE_PC_INDEX && metadata != NULL && metadata->target_operand_index == operand_index) {
      uint8_t flow_target_kind = decode_target_kind_for_flow(metadata->flow_kind);
      if (flow_target_kind != 0U) target_kind = flow_target_kind;
    }
    (void)append_target(candidate, target_kind, section_index, target_offset, 1U, (uint8_t)operand_index);
  }
}

const M68kDecodeCandidate *m68k_decode_ir_find_candidate_at_offset(const M68kDecodeSectionIR *section,
    uint32_t offset) {
  size_t index = 0U;
  int found = 0;
  if (candidate_index_at_offset(section, offset, &index, &found) != 0 || !found) return NULL;
  return &section->candidates[index];
}

static uint8_t decode_cpu_ceiling(uint8_t max_cpu) {
  return max_cpu <= M68K_ASM_CPU_68060 ? max_cpu : M68K_ASM_CPU_68060;
}

static int candidate_absent_cached_for_cpu(const M68kDecodeSectionIR *section, uint32_t offset,
    uint8_t max_cpu) {
  uint8_t cached;
  uint8_t required;
  if (section == NULL || section->candidate_absent_cpu == NULL || offset >= section->candidate_absent_size)
    return 0;
  cached = section->candidate_absent_cpu[offset];
  required = (uint8_t)(decode_cpu_ceiling(max_cpu) + 1U);
  return cached >= required;
}

static void candidate_absent_remember(M68kDecodeSectionIR *section, uint32_t offset, uint8_t max_cpu) {
  uint8_t ceiling;
  uint8_t value;
  if (section == NULL || offset >= section->size) return;
  if (section->candidate_absent_cpu == NULL) {
    section->candidate_absent_cpu = (uint8_t *)arena_calloc(section->owner_arena, section->size != 0U ? section->size : 1U,
      sizeof(*section->candidate_absent_cpu));
    if (section->candidate_absent_cpu == NULL) return;
    section->candidate_absent_size = section->size;
  }
  if (offset >= section->candidate_absent_size) return;
  ceiling = decode_cpu_ceiling(max_cpu);
  value = (uint8_t)(ceiling + 1U);
  if (section->candidate_absent_cpu[offset] < value) section->candidate_absent_cpu[offset] = value;
}

static M68kDisasmResult disassemble_for_cpu_ceiling(const uint8_t *data, size_t size, uint8_t max_cpu) {
  M68kDisasmResult decoded;
  uint8_t cpu;
  memset(&decoded, 0, sizeof(decoded));
  for (cpu = M68K_ASM_CPU_68000; cpu <= decode_cpu_ceiling(max_cpu); ++cpu) {
    decoded = m68k_disassemble_one_for_cpu(data, size, cpu, m68k_diag_sink(NULL));
    if (decoded.byte_count != 0U) return decoded;
    if (cpu == M68K_ASM_CPU_68060) break;
  }
  return decoded;
}

static int decode_candidate_at_section(M68kDecodeSectionIR *section, uint32_t offset, uint8_t max_cpu,
    M68kDecodeCandidate *out_candidate) {
  M68kDisasmResult decoded;
  size_t operand_index;
  if (section == NULL || out_candidate == NULL || section->data == NULL || (offset & 1U) != 0U ||
      offset + 2U > section->size) {
    return 0;
  }
  decoded = disassemble_for_cpu_ceiling(section->data + offset, section->size - offset, max_cpu);
  if (decoded.byte_count == 0U || decoded.byte_count > UINT8_MAX || decoded.byte_count > section->size - offset) return 0;
  memset(out_candidate, 0, sizeof(*out_candidate));
  out_candidate->offset = offset;
  out_candidate->asm_form_index = decoded.asm_form_index;
  out_candidate->disasm_form_index = decoded.disasm_form_index;
  out_candidate->mnemonic_id = decoded.mnemonic_id;
  out_candidate->target_cpu = decoded.target_cpu;
  out_candidate->has_coprocessor_id = decoded.has_coprocessor_id;
  out_candidate->coprocessor_id = decoded.coprocessor_id;
  out_candidate->byte_count = (uint8_t)decoded.byte_count;
  out_candidate->size_suffix = decoded.size_suffix;
  out_candidate->operand_count = (uint8_t)(decoded.operand_count < M68K_DECODE_IR_MAX_OPERANDS
    ? decoded.operand_count : M68K_DECODE_IR_MAX_OPERANDS);
  for (operand_index = 0U; operand_index < out_candidate->operand_count; ++operand_index) {
    out_candidate->operand_kinds[operand_index] = decoded.operand_kinds[operand_index];
    out_candidate->operands[operand_index] = decoded.operands[operand_index];
  }
  collect_control_targets(out_candidate, &decoded, section->section_index, section->size);
  collect_pc_relative_ea_targets(out_candidate, section->section_index, section->size);
  return 1;
}

void m68k_decode_ir_init(M68kDecodeIR *ir) {
  if (ir == NULL) return;
  memset(ir, 0, sizeof(*ir));
  ir->arena = arena_create(4096U);
}

void m68k_decode_ir_destroy(M68kDecodeIR *ir) {
  Arena *arena;
  if (ir == NULL) return;
  arena = ir->arena;
  memset(ir, 0, sizeof(*ir));
  arena_destroy(arena);
}

static void set_instruction_operand_from_candidate(M68kOperandIR *operand, uint8_t kind,
    const M68kAsmOperandValue *value) {
  if (operand == NULL || value == NULL) return;
  operand->kind = kind;
  operand->value = *value;
  switch (kind) {
    case M68K_ASM_OPERAND_IND:
      operand->kind = M68K_ASM_OPERAND_EA;
      operand->value.kind = M68K_ASM_OPERAND_EA;
      operand->value.ea_mode = 2U;
      break;
    case M68K_ASM_OPERAND_POSTINC:
      operand->kind = M68K_ASM_OPERAND_EA;
      operand->value.kind = M68K_ASM_OPERAND_EA;
      operand->value.ea_mode = 3U;
      break;
    case M68K_ASM_OPERAND_PREDEC:
      operand->kind = M68K_ASM_OPERAND_EA;
      operand->value.kind = M68K_ASM_OPERAND_EA;
      operand->value.ea_mode = 4U;
      break;
    case M68K_ASM_OPERAND_ABSL:
      operand->kind = M68K_ASM_OPERAND_EA;
      operand->value.kind = M68K_ASM_OPERAND_EA;
      operand->value.ea_mode = 7U;
      operand->value.ea_reg = 1U;
      break;
    default:
      break;
  }
  m68k_ir_symbol_ref_init(&operand->symbol_ref);
}

int m68k_decode_candidate_to_instruction(const M68kDecodeCandidate *candidate,
    M68kInstructionIR *out_instruction) {
  size_t operand_index;
  if (candidate == NULL || out_instruction == NULL || candidate->operand_count > 4U) return -1;
  m68k_ir_instruction_init(out_instruction);
  out_instruction->asm_form_index = candidate->asm_form_index;
  out_instruction->canonical_form_id = candidate->asm_form_index < M68K_ASM_FORM_COUNT
    ? g_m68k_asm_forms[candidate->asm_form_index].canonical_form_id
    : M68K_FORM_ID_NONE;
  out_instruction->mnemonic_id = candidate->mnemonic_id;
  out_instruction->target_cpu = candidate->target_cpu;
  out_instruction->has_coprocessor_id = candidate->has_coprocessor_id;
  out_instruction->coprocessor_id = candidate->coprocessor_id;
  out_instruction->size_suffix = candidate->size_suffix;
  out_instruction->operand_count = candidate->operand_count;
  out_instruction->byte_count = candidate->byte_count;
  for (operand_index = 0U; operand_index < candidate->operand_count; ++operand_index) {
    set_instruction_operand_from_candidate(&out_instruction->operands[operand_index],
      candidate->operand_kinds[operand_index], &candidate->operands[operand_index]);
  }
  return 0;
}

int m68k_decode_ir_build_object_sections(M68kDecodeIR *ir, const M68kObject *object,
    M68kDiagSink diagnostics) {
  size_t section_index;
  ArenaBuilder section_builder;
  size_t finalized_section_count = 0U;
  (void)diagnostics;
  if (ir == NULL || object == NULL) return -1;
  if (ir->arena == NULL) {
    m68k_decode_ir_init(ir);
  } else {
    Arena *arena = ir->arena;
    arena_reset(arena);
    memset(ir, 0, sizeof(*ir));
    ir->arena = arena;
  }
  if (ir->arena == NULL) goto oom;
  if (!ARENA_BUILDER_INIT_TYPED(&section_builder, ir->arena, M68kDecodeSectionIR, 4U)) goto oom;
  for (section_index = 0U; section_index < object->section_count; ++section_index) {
    const M68kSection *object_section = &object->sections[section_index];
    M68kDecodeSectionIR *section_ir;
    if (append_decode_section(&section_builder, &section_ir) != 0) goto oom;
    section_ir->section_index = section_index;
    section_ir->owner_arena = ir->arena;
    section_ir->name = object_section->name;
    section_ir->kind = object_section->kind;
    section_ir->platform_mem_type = object_section->platform_mem_type;
    section_ir->platform_mem_attrs = object_section->platform_mem_attrs;
    section_ir->allocation_size = object_section->size;
    section_ir->size = object_section->data_size;
    section_ir->data = object_section->data;
  }
  ir->sections = ARENA_BUILDER_FINALIZE_TYPED(&section_builder, M68kDecodeSectionIR, &finalized_section_count);
  if (ir->sections == NULL) goto oom;
  ir->section_count = finalized_section_count;
  ir->section_capacity = finalized_section_count;
  return 0;
oom:
  m68k_decode_ir_destroy(ir);
  m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
  return -1;
}

int m68k_decode_ir_ensure_candidate_at(M68kDecodeIR *ir, size_t section_index, uint32_t offset,
    uint8_t max_cpu, const M68kDecodeCandidate **out_candidate, M68kDiagSink diagnostics) {
  M68kDecodeSectionIR *section;
  M68kDecodeCandidate candidate;
  const M68kDecodeCandidate *existing;
  if (out_candidate != NULL) *out_candidate = NULL;
  if (ir == NULL || section_index >= ir->section_count) return -1;
  section = &ir->sections[section_index];
  if (section->owner_arena == NULL) section->owner_arena = ir->arena;
  existing = m68k_decode_ir_find_candidate_at_offset(section, offset);
  if (existing != NULL) {
    if (out_candidate != NULL) *out_candidate = existing;
    return 0;
  }
  if (candidate_absent_cached_for_cpu(section, offset, max_cpu)) return 0;
  if (!decode_candidate_at_section(section, offset, max_cpu, &candidate)) {
    candidate_absent_remember(section, offset, max_cpu);
    return 0;
  }
  if (insert_candidate_sorted(section, &candidate, out_candidate) != 0) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
    return -1;
  }
  ++ir->decoded_candidate_count;
  return 0;
}

int m68k_decode_ir_build_object(M68kDecodeIR *ir, const M68kObject *object, uint8_t max_cpu,
    M68kDiagSink diagnostics) {
  size_t section_index;
  if (m68k_decode_ir_build_object_sections(ir, object, diagnostics) != 0) return -1;
  for (section_index = 0U; section_index < ir->section_count; ++section_index) {
    uint32_t offset;
    M68kDecodeSectionIR *section = &ir->sections[section_index];
    if (section->kind == M68K_SECTION_BSS || section->data == NULL) continue;
    for (offset = 0U; offset + 2U <= section->size; offset += 2U) {
      const M68kDecodeCandidate *candidate = NULL;
      if (m68k_decode_ir_ensure_candidate_at(ir, section_index, offset, max_cpu, &candidate, diagnostics) != 0) {
        m68k_decode_ir_destroy(ir);
        return -1;
      }
    }
  }
  return 0;
}
