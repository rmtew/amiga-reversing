#include "platform_common.h"

#include "m68k_decode_ir.h"
#include "m68k_ir.h"
#include "m68k_parse_util.h"
#include "m68k_simulator.h"
#include "generated/m68k_cpu_runtime.h"
#include "generated/amiga_os_runtime.h"
#include "generated/atari_st_os_runtime.h"
#include "generated/mac_os_runtime.h"

#include <stdio.h>
#include <string.h>

void platform_facts_v2_resolved_call_init(PlatformFactsV2ResolvedCall *info) {
  if (info == NULL) return;
  memset(info, 0, sizeof(*info));
}

static int amiga_is_callback_vector_slot(uint32_t address) {
  return m68k_cpu_exception_vector_address_has_kind(address, M68K_CPU_VECTOR_KIND_EXCEPTION) ||
    m68k_cpu_exception_vector_address_has_kind(address, M68K_CPU_VECTOR_KIND_INTERRUPT) ||
    m68k_cpu_exception_vector_address_has_kind(address, M68K_CPU_VECTOR_KIND_TRAP);
}

uint8_t platform_facts_v2_address_use_shape_from_observation(uint8_t platform_kind,
    const M68kAddressObservationIR *observation) {
  if (observation == NULL || !observation->has_address) return M68K_PLATFORM_ADDRESS_USE_SHAPE_UNKNOWN;
  if (observation->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_CPU_VECTOR) {
    if (observation->access_kind == M68K_SIM_ACCESS_MEMORY_WRITE)
      return M68K_PLATFORM_ADDRESS_USE_SHAPE_TRUE_VECTOR_INSTALL;
    if (observation->access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS)
      return M68K_PLATFORM_ADDRESS_USE_SHAPE_LOW_MEMORY_BASE;
    return M68K_PLATFORM_ADDRESS_USE_SHAPE_LOW_MEMORY_STORAGE;
  }
  if (observation->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER ||
      observation->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER_RANGE) {
    if (platform_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK &&
        observation->access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS &&
        amiga_os_find_hardware_base_id_by_address(observation->address) != AMIGA_OS_HARDWARE_BASE_ID_NONE) {
      return M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_BASE_ADDRESS;
    }
    return M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_REGISTER_ACCESS;
  }
  if (observation->owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_EXECBASE_LITERAL) {
    return M68K_PLATFORM_ADDRESS_USE_SHAPE_EXECBASE_LITERAL;
  }
  if (observation->address < 0x400U &&
      (observation->access_kind == M68K_SIM_ACCESS_MEMORY_READ ||
       observation->access_kind == M68K_SIM_ACCESS_MEMORY_WRITE ||
       observation->access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS)) {
    return observation->access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS ?
      M68K_PLATFORM_ADDRESS_USE_SHAPE_LOW_MEMORY_BASE : M68K_PLATFORM_ADDRESS_USE_SHAPE_LOW_MEMORY_STORAGE;
  }
  return M68K_PLATFORM_ADDRESS_USE_SHAPE_UNKNOWN;
}

const char *platform_facts_v2_address_use_symbol_from_observation(uint8_t platform_kind,
    const M68kAddressObservationIR *observation, uint8_t shape, char *symbol_buf, size_t symbol_buf_size) {
  if (symbol_buf != NULL && symbol_buf_size != 0U) symbol_buf[0] = '\0';
  if (observation == NULL || !observation->has_address) return NULL;
  switch (shape) {
    case M68K_PLATFORM_ADDRESS_USE_SHAPE_TRUE_VECTOR_INSTALL: {
      const M68kCpuExceptionVectorInfo *vector = m68k_cpu_find_exception_vector_by_address(observation->address);
      return vector != NULL && vector->symbol_name != NULL && vector->symbol_name[0] != '\0'
        ? vector->symbol_name
        : NULL;
    }
    case M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_BASE_ADDRESS:
      return platform_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK ?
        amiga_os_find_hardware_base_symbol_by_address(observation->address) : NULL;
    case M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_REGISTER_ACCESS: {
      const AmigaOsHardwareRegisterFieldInfo *hardware_field;
      const AmigaOsHardwareRegisterInfo *hardware_register;
      const AmigaOsHardwareRegisterRangeInfo *hardware_range;
      if (platform_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return NULL;
      hardware_field = amiga_os_find_hardware_register_field_by_cpu_address(observation->address);
      if (hardware_field != NULL &&
          platform_amiga_format_hardware_register_field_symbol(hardware_field, 1, symbol_buf, symbol_buf_size)) {
        return symbol_buf;
      }
      hardware_register = amiga_os_find_hardware_register_by_cpu_address(observation->address);
      if (hardware_register != NULL && hardware_register->base_symbol != NULL &&
          hardware_register->base_symbol[0] != '\0' && hardware_register->symbol_name != NULL &&
          hardware_register->symbol_name[0] != '\0') {
        int written = snprintf(symbol_buf, symbol_buf_size, "%s+%s", hardware_register->base_symbol,
          hardware_register->symbol_name);
        return written > 0 && (size_t)written < symbol_buf_size ? symbol_buf : NULL;
      }
      hardware_range = amiga_os_find_hardware_register_range_by_cpu_address(observation->address);
      if (hardware_range != NULL &&
          platform_amiga_format_hardware_register_range_symbol(hardware_range,
            observation->address - hardware_range->base_address, 1, symbol_buf, symbol_buf_size)) {
        return symbol_buf;
      }
      return amiga_os_find_hardware_base_symbol_by_address(observation->address);
    }
    case M68K_PLATFORM_ADDRESS_USE_SHAPE_EXECBASE_LITERAL:
      return platform_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK ? "ExecBase" : NULL;
    default:
      return NULL;
  }
}

const char *platform_facts_v2_hardware_base_offset_symbol(uint8_t platform_kind, uint16_t base_id,
    uint32_t offset, char *symbol_buf, size_t symbol_buf_size) {
  const AmigaOsHardwareRegisterFieldInfo *hardware_field;
  const AmigaOsHardwareRegisterInfo *hardware_register;
  const AmigaOsHardwareRegisterRangeInfo *hardware_range;
  if (symbol_buf != NULL && symbol_buf_size != 0U) symbol_buf[0] = '\0';
  if (platform_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK || base_id == AMIGA_OS_HARDWARE_BASE_ID_NONE) return NULL;
  hardware_field = amiga_os_find_hardware_register_field_by_base_id_offset(base_id, offset);
  if (hardware_field != NULL &&
      platform_amiga_format_hardware_register_field_symbol(hardware_field, 0, symbol_buf, symbol_buf_size)) {
    return symbol_buf;
  }
  hardware_register = amiga_os_find_hardware_register_by_base_id_offset(base_id, offset);
  if (hardware_register != NULL && hardware_register->symbol_name != NULL &&
      hardware_register->symbol_name[0] != '\0') {
    return hardware_register->symbol_name;
  }
  hardware_range = amiga_os_find_hardware_register_range_by_base_id_offset(base_id, offset);
  if (hardware_range != NULL &&
      platform_amiga_format_hardware_register_range_symbol(hardware_range, offset, 0, symbol_buf,
        symbol_buf_size)) {
    return symbol_buf;
  }
  return NULL;
}

int platform_facts_v2_hardware_base_offset_known(uint8_t platform_kind, uint16_t base_id, uint32_t offset) {
  char symbol_buf[64];
  return platform_facts_v2_hardware_base_offset_symbol(platform_kind, base_id, offset, symbol_buf,
    sizeof(symbol_buf)) != NULL;
}

int platform_facts_v2_hardware_base_address(uint8_t platform_kind, uint16_t base_id, uint32_t *out_address) {
  const char *base_symbol;
  if (out_address != NULL) *out_address = 0U;
  if (platform_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK || base_id == AMIGA_OS_HARDWARE_BASE_ID_NONE) return 0;
  base_symbol = amiga_os_hardware_base_symbol(base_id);
  return base_symbol != NULL && amiga_os_find_hardware_base_address(base_symbol, out_address);
}

int platform_facts_v2_hardware_base_offset_for_address(uint8_t platform_kind, uint32_t address,
    uint16_t *out_base_id, uint32_t *out_offset) {
  const AmigaOsHardwareRegisterFieldInfo *hardware_field;
  const AmigaOsHardwareRegisterInfo *hardware_register;
  const AmigaOsHardwareRegisterRangeInfo *hardware_range;
  if (out_base_id != NULL) *out_base_id = AMIGA_OS_HARDWARE_BASE_ID_NONE;
  if (out_offset != NULL) *out_offset = 0U;
  if (platform_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 0;
  hardware_field = amiga_os_find_hardware_register_field_by_cpu_address(address);
  if (hardware_field != NULL) {
    if (out_base_id != NULL) *out_base_id = hardware_field->base_id;
    if (out_offset != NULL) *out_offset = hardware_field->register_offset + hardware_field->field_offset;
    return 1;
  }
  hardware_register = amiga_os_find_hardware_register_by_cpu_address(address);
  if (hardware_register != NULL) {
    if (out_base_id != NULL) *out_base_id = hardware_register->base_id;
    if (out_offset != NULL) *out_offset = hardware_register->offset;
    return 1;
  }
  hardware_range = amiga_os_find_hardware_register_range_by_cpu_address(address);
  if (hardware_range == NULL) return 0;
  if (out_base_id != NULL) *out_base_id = hardware_range->base_id;
  if (out_offset != NULL) *out_offset = address - hardware_range->base_address;
  return 1;
}

int platform_facts_v2_address_has_hardware_owner(uint8_t platform_kind, uint32_t address) {
  if (platform_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 0;
  return amiga_os_find_hardware_base_symbol_by_address(address) != NULL ||
    amiga_os_find_hardware_register_by_cpu_address(address) != NULL ||
    amiga_os_find_hardware_register_field_by_cpu_address(address) != NULL ||
    amiga_os_find_hardware_register_range_by_cpu_address(address) != NULL;
}

int platform_facts_v2_address_has_symbolic_owner(uint8_t platform_kind, uint32_t address) {
  if (m68k_cpu_find_exception_vector_by_address(address) != NULL) return 1;
  return platform_facts_v2_address_has_hardware_owner(platform_kind, address);
}

static int facts_v2_accepted_start_at(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    uint32_t offset) {
  return section != NULL && accepted_start != NULL && offset < section->size && accepted_start[offset] != 0U;
}

static int atari_operand_is_sp_address_reg(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  return (operand->kind == M68K_ASM_OPERAND_AN && operand->value.reg == 7U) ||
    (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 1U && operand->value.ea_reg == 7U);
}

static int atari_operand_is_immediate(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  return operand->kind == M68K_ASM_OPERAND_IMM ||
    (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 7U && operand->value.ea_reg == 4U);
}

static int atari_operand_is_indirect_disp_an(const M68kOperandIR *operand, uint8_t *out_reg,
    int16_t *out_displacement) {
  if (operand == NULL || operand->kind != M68K_ASM_OPERAND_EA ||
      operand->value.ea_mode != 5U || operand->value.ea_reg >= 8U) {
    return 0;
  }
  if (out_reg != NULL) *out_reg = operand->value.ea_reg;
  if (out_displacement != NULL) *out_displacement = (int16_t)(operand->value.value & 0xFFFFU);
  return 1;
}

static int atari_mnemonic_is_stack_add_family(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_ADDQ:
  case M68K_ASM_MNEMONIC_ADD:
  case M68K_ASM_MNEMONIC_ADDI:
  case M68K_ASM_MNEMONIC_ADDA:
    return 1;
  default:
    return 0;
  }
}

static int atari_mnemonic_is_stack_sub_family(uint8_t mnemonic_id) {
  switch (mnemonic_id) {
  case M68K_ASM_MNEMONIC_SUBQ:
  case M68K_ASM_MNEMONIC_SUB:
  case M68K_ASM_MNEMONIC_SUBI:
  case M68K_ASM_MNEMONIC_SUBA:
    return 1;
  default:
    return 0;
  }
}

static int atari_instruction_trap_vector(const M68kInstructionIR *instruction, uint8_t *out_vector) {
  if (out_vector != NULL) *out_vector = 0U;
  if (instruction == NULL || instruction->mnemonic_id != M68K_ASM_MNEMONIC_TRAP ||
      instruction->operand_count != 1U) {
    return 0;
  }
  if (out_vector != NULL) *out_vector = (uint8_t)(instruction->operands[0].value.value & 0xFFU);
  return 1;
}

static int atari_instruction_stack_adjust_delta(const M68kInstructionIR *instruction, int32_t *out_delta) {
  const M68kOperandIR *src;
  const M68kOperandIR *dst;
  uint8_t base_reg;
  int16_t disp16;
  int32_t value;
  if (out_delta != NULL) *out_delta = 0;
  if (instruction == NULL || out_delta == NULL) return 0;
  if ((atari_mnemonic_is_stack_add_family(instruction->mnemonic_id) ||
       atari_mnemonic_is_stack_sub_family(instruction->mnemonic_id)) &&
      instruction->operand_count == 2U) {
    src = &instruction->operands[0];
    dst = &instruction->operands[1];
    if (!atari_operand_is_sp_address_reg(dst) || !atari_operand_is_immediate(src)) return 0;
    value = (instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDQ ||
             instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBQ)
      ? (int32_t)m68k_sign_extend32(src->value.value, 3U)
      : (int32_t)m68k_sign_extend32(src->value.value, instruction->size_suffix == 'w' ? 16U : 32U);
    *out_delta = atari_mnemonic_is_stack_sub_family(instruction->mnemonic_id) ? -value : value;
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U) {
    src = &instruction->operands[0];
    dst = &instruction->operands[1];
    if (!atari_operand_is_sp_address_reg(dst)) return 0;
    if (!atari_operand_is_indirect_disp_an(src, &base_reg, &disp16) || base_reg != 7U) return 0;
    *out_delta = (int32_t)disp16;
    return 1;
  }
  return 0;
}

static int atari_extract_stack_word_write(const M68kInstructionIR *instruction, uint8_t *out_has_value,
    uint16_t *out_value, uint32_t *out_write_disp, uint32_t *out_write_size, uint8_t *out_consumes_depth) {
  const M68kOperandIR *src;
  const M68kOperandIR *dst;
  if (out_has_value != NULL) *out_has_value = 0U;
  if (out_value != NULL) *out_value = 0U;
  if (out_write_disp != NULL) *out_write_disp = 0U;
  if (out_write_size != NULL) *out_write_size = 0U;
  if (out_consumes_depth != NULL) *out_consumes_depth = 0U;
  if (instruction == NULL || instruction->operand_count != 2U || instruction->size_suffix != 'w')
    return 0;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_CLR) {
    return 0;
  }
  src = &instruction->operands[0];
  dst = &instruction->operands[1];
  if ((dst->kind == M68K_ASM_OPERAND_PREDEC && dst->value.reg == 7U) ||
      (dst->kind == M68K_ASM_OPERAND_EA && dst->value.ea_mode == 4U && dst->value.ea_reg == 7U)) {
    if (out_write_size != NULL) *out_write_size = 2U;
    if (out_consumes_depth != NULL) *out_consumes_depth = 1U;
  } else if ((dst->kind == M68K_ASM_OPERAND_IND && dst->value.reg == 7U) ||
      (dst->kind == M68K_ASM_OPERAND_EA && dst->value.ea_mode == 2U && dst->value.ea_reg == 7U)) {
    if (out_write_size != NULL) *out_write_size = 2U;
  } else {
    return 0;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_CLR) {
    if (out_has_value != NULL) *out_has_value = 1U;
    return 1;
  }
  if (atari_operand_is_immediate(src)) {
    if (out_has_value != NULL) *out_has_value = 1U;
    if (out_value != NULL) *out_value = (uint16_t)(src->value.value & 0xFFFFU);
  }
  return 1;
}

static int atari_find_previous_accepted_instruction_ending_at(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, uint32_t offset, uint32_t *out_prev_offset,
    M68kInstructionIR *out_instruction) {
  uint32_t start = offset > 12U ? offset - 12U : 0U;
  uint32_t probe;
  if (out_prev_offset != NULL) *out_prev_offset = 0U;
  if (out_instruction != NULL) memset(out_instruction, 0, sizeof(*out_instruction));
  if (section == NULL || accepted_start == NULL || out_prev_offset == NULL || out_instruction == NULL)
    return 0;
  for (probe = start; probe < offset; ++probe) {
    const M68kDecodeCandidate *candidate;
    if (!facts_v2_accepted_start_at(section, accepted_start, probe)) continue;
    candidate = m68k_decode_ir_find_candidate_at_offset(section, probe);
    if (candidate == NULL || candidate->byte_count == 0U || probe + candidate->byte_count != offset) continue;
    if (m68k_decode_candidate_to_instruction(candidate, out_instruction) != 0) continue;
    *out_prev_offset = probe;
    return 1;
  }
  return 0;
}

static int atari_instruction_is_stack_cleanup_candidate(const M68kInstructionIR *instruction,
    uint16_t cleanup_bytes) {
  const M68kOperandIR *src;
  const M68kOperandIR *dst;
  uint8_t base_reg;
  int16_t disp16;
  if (instruction == NULL || cleanup_bytes == 0U) return 0;
  if (atari_mnemonic_is_stack_add_family(instruction->mnemonic_id) && instruction->operand_count == 2U) {
    dst = &instruction->operands[1];
    return atari_operand_is_sp_address_reg(dst) ||
      (dst->kind == M68K_ASM_OPERAND_POSTINC && dst->value.reg == 7U);
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U) {
    src = &instruction->operands[0];
    dst = &instruction->operands[1];
    if (!atari_operand_is_sp_address_reg(dst)) return 0;
    if (!atari_operand_is_indirect_disp_an(src, &base_reg, &disp16) || base_reg != 7U) return 0;
    return (uint16_t)(disp16 & 0xFFFF) == cleanup_bytes;
  }
  return 0;
}

static void atari_populate_resolved_call(const AtariStOsCallInfo *call_info, uint8_t kind, uint8_t note_kind,
    PlatformFactsV2ResolvedCall *out_info) {
  const char *family_name;
  const char *symbol_name;
  if (out_info == NULL) return;
  platform_facts_v2_resolved_call_init(out_info);
  if (call_info == NULL) return;
  family_name = atari_st_os_name(M68K_PLATFORM_NAME_FAMILY, call_info->family_id);
  symbol_name = atari_st_os_name(M68K_PLATFORM_NAME_SYMBOL, call_info->symbol_id);
  out_info->platform_kind = M68K_PLATFORM_BACKEND_ATARI_ST;
  out_info->kind = kind;
  out_info->note_kind = note_kind;
  out_info->note_stack_cleanup_known = call_info->stack_cleanup_known;
  out_info->note_stack_cleanup_bytes = call_info->stack_cleanup_bytes;
  out_info->note_return_kind = call_info->return_kind;
  if (family_name != NULL)
    snprintf(out_info->note_base_name, sizeof(out_info->note_base_name), "%s", family_name);
  if (symbol_name != NULL)
    snprintf(out_info->note_symbol_name, sizeof(out_info->note_symbol_name), "%s", symbol_name);
}

static void macos_populate_resolved_call(const MacOsCallInfo *call_info,
    PlatformFactsV2ResolvedCall *out_info) {
  if (out_info == NULL) return;
  platform_facts_v2_resolved_call_init(out_info);
  if (call_info == NULL) return;
  out_info->platform_kind = M68K_PLATFORM_BACKEND_MACOS;
  out_info->kind = 0U;
  out_info->note_kind = M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL;
  if (call_info->family != NULL)
    snprintf(out_info->note_base_name, sizeof(out_info->note_base_name), "%s", call_info->family);
  if (call_info->name != NULL)
    snprintf(out_info->note_symbol_name, sizeof(out_info->note_symbol_name), "%s", call_info->name);
}

static int atari_resolve_trap_call(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    uint32_t block_start, uint32_t trap_offset, PlatformFactsV2ResolvedCall *out_info) {
  const M68kDecodeCandidate *trap_candidate;
  M68kInstructionIR trap_instruction;
  uint8_t trap_vector = 0U;
  uint32_t cursor = trap_offset;
  int32_t target_disp = 0;
  if (out_info != NULL) platform_facts_v2_resolved_call_init(out_info);
  if (section == NULL || accepted_start == NULL ||
      !facts_v2_accepted_start_at(section, accepted_start, trap_offset)) {
    return 0;
  }
  trap_candidate = m68k_decode_ir_find_candidate_at_offset(section, trap_offset);
  if (trap_candidate == NULL || m68k_decode_candidate_to_instruction(trap_candidate, &trap_instruction) != 0)
    return 0;
  if (!atari_instruction_trap_vector(&trap_instruction, &trap_vector)) return 0;
  while (cursor > block_start) {
    M68kInstructionIR prev_instruction;
    uint32_t prev_offset;
    uint32_t write_disp, write_size;
    int32_t stack_delta;
    uint8_t has_value, consumes_depth;
    uint16_t value;
    if (!atari_find_previous_accepted_instruction_ending_at(section, accepted_start, cursor, &prev_offset,
        &prev_instruction)) {
      break;
    }
    if (atari_instruction_stack_adjust_delta(&prev_instruction, &stack_delta)) {
      target_disp += stack_delta;
      if (target_disp < 0) return 0;
      cursor = prev_offset;
      continue;
    }
    if (atari_extract_stack_word_write(&prev_instruction, &has_value, &value, &write_disp, &write_size,
        &consumes_depth)) {
      if (target_disp >= (int32_t)write_disp && target_disp < (int32_t)(write_disp + write_size)) {
        const AtariStOsCallInfo *call_info = has_value ? atari_st_os_find_call(trap_vector, value) : NULL;
        if (call_info == NULL) return 0;
        atari_populate_resolved_call(call_info, 0U, M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL, out_info);
        return 1;
      }
      if (consumes_depth != 0U) {
        target_disp -= (int32_t)write_size;
        if (target_disp < 0) target_disp = 0;
      }
      cursor = prev_offset;
      continue;
    }
    cursor = prev_offset;
  }
  return 0;
}

static int atari_resolve_stack_cleanup_call(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    uint32_t block_start, uint32_t cleanup_offset, const M68kInstructionIR *cleanup_instruction,
    PlatformFactsV2ResolvedCall *out_info) {
  M68kInstructionIR prev_instruction;
  uint32_t prev_offset;
  PlatformFactsV2ResolvedCall trap_info;
  if (out_info != NULL) platform_facts_v2_resolved_call_init(out_info);
  if (section == NULL || accepted_start == NULL || cleanup_instruction == NULL) return 0;
  if (!atari_find_previous_accepted_instruction_ending_at(section, accepted_start, cleanup_offset,
      &prev_offset, &prev_instruction)) {
    return 0;
  }
  if (!atari_instruction_trap_vector(&prev_instruction, NULL)) return 0;
  if (!atari_resolve_trap_call(section, accepted_start, block_start, prev_offset, &trap_info)) return 0;
  if (!trap_info.note_stack_cleanup_known ||
      !atari_instruction_is_stack_cleanup_candidate(cleanup_instruction,
        trap_info.note_stack_cleanup_bytes)) {
    return 0;
  }
  if (out_info != NULL) {
    *out_info = trap_info;
    out_info->kind = 1U;
    out_info->note_kind = M68K_PLATFORM_CALL_NOTE_STACK_CLEANUP;
  }
  return 1;
}

int platform_facts_v2_resolve_trap_call(uint8_t platform_kind,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t block_start,
    uint32_t trap_offset, PlatformFactsV2ResolvedCall *out_info) {
  if (out_info != NULL) platform_facts_v2_resolved_call_init(out_info);
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_ATARI_ST:
    return atari_resolve_trap_call(section, accepted_start, block_start, trap_offset, out_info);
  default:
    return 0;
  }
}

int platform_facts_v2_resolve_opcode_call(uint8_t platform_kind, uint16_t opcode,
    PlatformFactsV2ResolvedCall *out_info) {
  if (out_info != NULL) platform_facts_v2_resolved_call_init(out_info);
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_MACOS:
  {
    const MacOsCallInfo *call_info = mac_os_find_call_by_opword(opcode);
    if (call_info == NULL) return 0;
    macos_populate_resolved_call(call_info, out_info);
    return 1;
  }
  default:
    return 0;
  }
}

int platform_facts_v2_resolve_stack_cleanup_call(uint8_t platform_kind,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t block_start,
    uint32_t cleanup_offset, const M68kInstructionIR *cleanup_instruction,
    PlatformFactsV2ResolvedCall *out_info) {
  if (out_info != NULL) platform_facts_v2_resolved_call_init(out_info);
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_ATARI_ST:
    return atari_resolve_stack_cleanup_call(section, accepted_start, block_start, cleanup_offset,
      cleanup_instruction, out_info);
  default:
    return 0;
  }
}

int platform_facts_v2_is_callback_vector_slot(uint8_t platform_kind, uint32_t address) {
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    return amiga_is_callback_vector_slot(address);
  default:
    return 0;
  }
}

int platform_facts_v2_is_runtime_address_sink(uint8_t platform_kind, uint32_t address) {
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
  {
    const AmigaOsHardwareRegisterInfo *hardware_register =
      amiga_os_find_hardware_register_by_cpu_address(address);
    return hardware_register != NULL &&
      (hardware_register->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) != 0U;
  }
  default:
    return 0;
  }
}

uint16_t platform_facts_v2_runtime_address_sink_kind(uint8_t platform_kind, uint32_t address) {
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
  {
    const AmigaOsHardwareRegisterInfo *hardware_register =
      amiga_os_find_hardware_register_by_cpu_address(address);
    if (hardware_register == NULL ||
        (hardware_register->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) == 0U) {
      return AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_NONE;
    }
    return hardware_register->runtime_target_kind;
  }
  default:
    return 0U;
  }
}

static uint32_t amiga_runtime_target_kind_data_class_flags(uint16_t kind) {
  switch (kind) {
  case AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_COPPER_LIST:
    return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_COPPER_LIST;
  case AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_DISK_BUFFER:
    return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_DISK_BUFFER;
  case AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_BLITTER_SOURCE:
    return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BLITTER_SOURCE;
  case AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_BLITTER_DESTINATION:
    return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BLITTER_DESTINATION;
  case AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_BITMAP:
    return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP;
  case AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_SPRITE:
    return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SPRITE;
  case AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_SOUND_SAMPLE:
    return M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SOUND_SAMPLE;
  default:
    return 0U;
  }
}

const char *platform_facts_v2_runtime_address_sink_data_class(uint8_t platform_kind, uint32_t address) {
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    return amiga_os_hardware_runtime_target_kind_name(
      platform_facts_v2_runtime_address_sink_kind(platform_kind, address));
  default:
    return NULL;
  }
}

uint32_t platform_facts_v2_runtime_address_sink_data_class_flags(uint8_t platform_kind, uint32_t address) {
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    return amiga_runtime_target_kind_data_class_flags(
      platform_facts_v2_runtime_address_sink_kind(platform_kind, address));
  default:
    return 0U;
  }
}

uint16_t platform_facts_v2_runtime_address_storage_sink_kind(uint8_t platform_kind,
    const uint8_t *data, uint32_t size, uint32_t value_offset) {
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
  {
    const AmigaOsHardwareRegisterInfo *hardware_register;
    const AmigaOsHardwareRegisterRangeInfo *hardware_range;
    uint16_t register_word;
    uint32_t register_offset;
    if (data == NULL || value_offset < 2U || value_offset > size - 2U)
      return AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_NONE;
    register_word = m68k_read_u16be(data + value_offset - 2U);
    if ((register_word & 1U) != 0U) return AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_NONE;
    register_offset = (uint32_t)(register_word & 0x01FEU);
    hardware_register = amiga_os_find_hardware_register_by_base_id_offset(AMIGA_OS_HARDWARE_BASE_ID_CUSTOM,
      register_offset);
    if (hardware_register == NULL) {
      hardware_range = amiga_os_find_hardware_register_range_by_base_id_offset(AMIGA_OS_HARDWARE_BASE_ID_CUSTOM,
        register_offset);
      if (hardware_range != NULL) {
        hardware_register =
          amiga_os_find_hardware_register_by_base_id_offset(AMIGA_OS_HARDWARE_BASE_ID_CUSTOM, hardware_range->offset);
      }
    }
    if (hardware_register == NULL ||
        (hardware_register->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) == 0U) {
      return AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_NONE;
    }
    return hardware_register->runtime_target_kind;
  }
  default:
    return 0U;
  }
}

const char *platform_facts_v2_runtime_address_storage_sink_data_class(uint8_t platform_kind,
    const uint8_t *data, uint32_t size, uint32_t value_offset) {
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    return amiga_os_hardware_runtime_target_kind_name(
      platform_facts_v2_runtime_address_storage_sink_kind(platform_kind, data, size, value_offset));
  default:
    return NULL;
  }
}

uint32_t platform_facts_v2_runtime_address_storage_sink_data_class_flags(uint8_t platform_kind,
    const uint8_t *data, uint32_t size, uint32_t value_offset) {
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    return amiga_runtime_target_kind_data_class_flags(
      platform_facts_v2_runtime_address_storage_sink_kind(platform_kind, data, size, value_offset));
  default:
    return 0U;
  }
}

int platform_facts_v2_absolute_memory_owner(uint8_t platform_kind, uint32_t address,
    uint8_t *out_owner_kind, uint32_t *out_owner_offset) {
  if (out_owner_kind != NULL) *out_owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_UNKNOWN;
  if (out_owner_offset != NULL) *out_owner_offset = 0U;
  if (out_owner_kind == NULL || out_owner_offset == NULL) return 0;
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK: {
    const AmigaOsHardwareRegisterInfo *hardware_register;
    const AmigaOsHardwareRegisterFieldInfo *hardware_field;
    const AmigaOsHardwareRegisterRangeInfo *hardware_range;
    if (address == 4U) {
      *out_owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_EXECBASE_LITERAL;
      return 1;
    }
    hardware_register = amiga_os_find_hardware_register_by_cpu_address(address);
    if (hardware_register != NULL) {
      *out_owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER;
      *out_owner_offset = hardware_register->offset;
      return 1;
    }
    hardware_field = amiga_os_find_hardware_register_field_by_cpu_address(address);
    if (hardware_field != NULL) {
      *out_owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER;
      *out_owner_offset = hardware_field->register_offset + hardware_field->field_offset;
      return 1;
    }
    hardware_range = amiga_os_find_hardware_register_range_by_cpu_address(address);
    if (hardware_range != NULL) {
      *out_owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER_RANGE;
      *out_owner_offset = address - hardware_range->base_address;
      return 1;
    }
    return 0;
  }
  default:
    return 0;
  }
}

int platform_facts_v2_absolute_memory_owner_stays_literal(uint8_t platform_kind, uint32_t address) {
  uint8_t owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_UNKNOWN;
  uint32_t owner_offset = 0U;
  return platform_facts_v2_absolute_memory_owner(platform_kind, address, &owner_kind, &owner_offset) &&
    owner_kind == M68K_ABSOLUTE_MEMORY_OWNER_EXECBASE_LITERAL;
}

uint32_t platform_facts_v2_relocation_anchor_kind(uint8_t platform_kind, uint8_t platform_file_kind,
    uint8_t fixup_kind, uint32_t width, uint32_t raw_value) {
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    if (platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE || width != 4U ||
        (fixup_kind != M68K_FIXUP_ABS && fixup_kind != M68K_FIXUP_SECTION_REL)) {
      return PLATFORM_FACTS_V2_RELOCATION_ANCHOR_NONE;
    }
    return (int32_t)raw_value < 0
      ? PLATFORM_FACTS_V2_RELOCATION_ANCHOR_NEGATIVE
      : PLATFORM_FACTS_V2_RELOCATION_ANCHOR_POSITIVE;
  default:
    return PLATFORM_FACTS_V2_RELOCATION_ANCHOR_NONE;
  }
}

int platform_facts_v2_fixup_addend_is_normalized_target(uint8_t platform_kind, uint8_t platform_file_kind,
    uint8_t fixup_kind, uint8_t has_target_section, int64_t addend, uint32_t width, uint32_t target_extent,
    uint32_t *out_offset) {
  if (out_offset == NULL) return 0;
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_ATARI_ST:
    if (platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE || fixup_kind != M68K_FIXUP_ABS || width != 4U ||
        !has_target_section || addend < 0 || addend >= (int64_t)(uint64_t)target_extent) {
      return 0;
    }
    *out_offset = (uint32_t)addend;
    return 1;
  default:
    return 0;
  }
}

int platform_facts_v2_image_offset_target(uint8_t platform_kind, uint8_t platform_file_kind, uint8_t fixup_kind,
    uint32_t width, uint32_t raw_value, uint32_t code_size, uint32_t data_size, uint8_t has_bss,
    uint32_t bss_size, uint8_t *out_target_kind, uint32_t *out_offset) {
  uint32_t remaining;
  if (out_target_kind != NULL) *out_target_kind = PLATFORM_FACTS_V2_IMAGE_OFFSET_TARGET_NONE;
  if (out_offset != NULL) *out_offset = 0U;
  if (out_target_kind == NULL || out_offset == NULL) return 0;
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_ATARI_ST:
    if (platform_file_kind != M68K_PLATFORM_FILE_EXECUTABLE || fixup_kind != M68K_FIXUP_ABS || width != 4U)
      return 0;
    if (raw_value < code_size) {
      *out_target_kind = PLATFORM_FACTS_V2_IMAGE_OFFSET_TARGET_CODE;
      *out_offset = raw_value;
      return 1;
    }
    remaining = raw_value - code_size;
    if (remaining < data_size) {
      *out_target_kind = PLATFORM_FACTS_V2_IMAGE_OFFSET_TARGET_DATA;
      *out_offset = remaining;
      return 1;
    }
    remaining -= data_size;
    if (has_bss && remaining <= bss_size) {
      *out_target_kind = PLATFORM_FACTS_V2_IMAGE_OFFSET_TARGET_BSS;
      *out_offset = remaining;
      return 1;
    }
    return 0;
  default:
    return 0;
  }
}

int platform_facts_v2_supports_linkage_api_entry_labels(uint8_t platform_kind) {
  return platform_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK;
}

int platform_facts_v2_lvo_is_api(uint8_t platform_kind, int16_t lvo) {
  size_t index;
  if (!platform_facts_v2_supports_linkage_api_entry_labels(platform_kind)) return 0;
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    for (index = 0U;; ++index) {
      const AmigaOsLibraryVectorInfo *vector = amiga_os_library_vector_at(index);
      if (vector == NULL) return 0;
      if (vector->lvo == lvo) return 1;
    }
  default:
    return 0;
  }
}

int platform_facts_v2_pc_relative_section_anchor_for_target(uint8_t platform_kind, int64_t target,
    uint32_t *out_base_offset, int32_t *out_addend, uint8_t *out_symbol_provenance) {
  if (out_base_offset != NULL) *out_base_offset = 0U;
  if (out_addend != NULL) *out_addend = 0;
  if (out_symbol_provenance != NULL) *out_symbol_provenance = M68K_IR_SYMBOL_PROVENANCE_NONE;
  if (out_base_offset == NULL || out_addend == NULL) return 0;
  switch (platform_kind) {
  case M68K_PLATFORM_BACKEND_AMIGA_HUNK:
    if (target != -4) return 0;
    *out_base_offset = 0U;
    *out_addend = -4;
    if (out_symbol_provenance != NULL) *out_symbol_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
    return 1;
  default:
    return 0;
  }
}

int platform_facts_v2_supports_loadseg_segment_chain(uint8_t platform_kind) {
  return platform_kind == M68K_PLATFORM_BACKEND_AMIGA_HUNK;
}

int platform_facts_v2_loadseg_segment_body_for_hops(uint8_t platform_kind, size_t section_count,
    size_t anchor_section_index, uint32_t link_hops, size_t *out_section_index) {
  size_t target_section;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_section_index == NULL || !platform_facts_v2_supports_loadseg_segment_chain(platform_kind) ||
      link_hops == 0U || anchor_section_index >= section_count) {
    return 0;
  }
  target_section = anchor_section_index + (size_t)link_hops;
  if (target_section < anchor_section_index || target_section >= section_count) return 0;
  *out_section_index = target_section;
  return 1;
}
