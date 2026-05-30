#include "m68k_c_unit_test.h"
#include "m68k_simulator.h"
#include "generated/m68k_asm_tables.h"

#include <string.h>

static int test_external_write_allowed(void *user, uint32_t address, uint8_t width) {
  (void)user;
  return address == 0x30U && width == 1U;
}

static int test_external_long_access_allowed(void *user, uint32_t address, uint8_t width) {
  (void)user;
  return address == 0x30U && width == 4U;
}

static int test_external_long_read(void *user, uint32_t address, uint8_t width, uint32_t *out_value) {
  (void)user;
  if (address != 0x30U || width != 4U || out_value == NULL) return 0;
  *out_value = 0x11111111U;
  return 1;
}

static M68kFormId test_form_id_by_syntax(const char *syntax) {
  uint16_t row;
  for (row = 0; row < M68K_CANONICAL_FORM_COUNT; ++row) {
    if (strcmp(g_m68k_canonical_forms[row].syntax, syntax) == 0) return g_m68k_canonical_forms[row].id;
  }
  return M68K_FORM_ID_NONE;
}

static int test_metadata_lookup_uses_canonical_form_id(void) {
  const M68kSimFormMetadata *metadata = NULL;
  M68kFormId form_id = test_form_id_by_syntax("NOP");
  M68K_C_ASSERT(form_id != M68K_FORM_ID_NONE);
  M68K_C_ASSERT_INT(M68K_SIM_METADATA_OK, m68k_sim_metadata_for_canonical_form_id(form_id, &metadata));
  M68K_C_ASSERT(metadata != NULL);
  M68K_C_ASSERT_INT(M68K_SIM_FLOW_SEQUENTIAL, metadata->flow_kind);
  return 0;
}

static int test_metadata_lookup_uses_generated_ccr_formulas(void) {
  const M68kSimFormMetadata *metadata = NULL;
  M68kFormId form_id = test_form_id_by_syntax("MOVE <ea>,<ea>");
  M68K_C_ASSERT(form_id != M68K_FORM_ID_NONE);
  M68K_C_ASSERT_INT(M68K_SIM_METADATA_OK, m68k_sim_metadata_for_canonical_form_id(form_id, &metadata));
  M68K_C_ASSERT(metadata != NULL);
  M68K_C_ASSERT_U32(M68K_SIM_CCR_FORMULA_MOVE_FLAGS, metadata->ccr_formula);

  form_id = test_form_id_by_syntax("MOVEA <ea>,An");
  M68K_C_ASSERT(form_id != M68K_FORM_ID_NONE);
  M68K_C_ASSERT_INT(M68K_SIM_METADATA_OK, m68k_sim_metadata_for_canonical_form_id(form_id, &metadata));
  M68K_C_ASSERT(metadata != NULL);
  M68K_C_ASSERT_U32(M68K_SIM_CCR_FORMULA_NONE, metadata->ccr_formula);

  form_id = test_form_id_by_syntax("MOVE <ea>,CCR");
  M68K_C_ASSERT(form_id != M68K_FORM_ID_NONE);
  M68K_C_ASSERT_INT(M68K_SIM_METADATA_OK, m68k_sim_metadata_for_canonical_form_id(form_id, &metadata));
  M68K_C_ASSERT(metadata != NULL);
  M68K_C_ASSERT_U32(M68K_SIM_CCR_FORMULA_WRITE_CCR, metadata->ccr_formula);
  return 0;
}

static int test_metadata_lookup_reports_missing_generated_semantics(void) {
  const M68kSimFormMetadata *metadata = NULL;
  M68kFormId form_id = test_form_id_by_syntax("MOVE16 (Ax)+,(Ay)+");
  M68K_C_ASSERT(form_id != M68K_FORM_ID_NONE);
  M68K_C_ASSERT_INT(M68K_SIM_METADATA_GENERATED_SEMANTICS_MISSING,
    m68k_sim_metadata_for_canonical_form_id(form_id, &metadata));
  M68K_C_ASSERT(metadata == NULL);
  return 0;
}

static int test_metadata_lookup_reports_missing_for_canonical_form_without_sim_row(void) {
  const M68kSimFormMetadata *metadata = NULL;
  M68kFormId form_id = test_form_id_by_syntax("cpBcc <label>");
  M68K_C_ASSERT(form_id != M68K_FORM_ID_NONE);
  M68K_C_ASSERT_INT(M68K_SIM_METADATA_GENERATED_SEMANTICS_MISSING,
    m68k_sim_metadata_for_canonical_form_id(form_id, &metadata));
  M68K_C_ASSERT(metadata == NULL);
  return 0;
}

static int test_metadata_lookup_does_not_fallback_to_mnemonic_shape(void) {
  M68kInstructionIR instruction;
  m68k_ir_instruction_init(&instruction);
  instruction.mnemonic_id = M68K_ASM_MNEMONIC_NOP;
  instruction.operand_count = 0;
  M68K_C_ASSERT(m68k_sim_metadata_for_instruction(&instruction) == NULL);
  return 0;
}

static int test_concrete_run_stops_on_pc_range(void) {
  uint8_t memory[] = {0x70U, 0x01U, 0x52U, 0x80U};
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 8U, 4U,
    6U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_PC_RANGE, result.stop_reason);
  M68K_C_ASSERT_U32(2U, (uint32_t)result.step_count);
  M68K_C_ASSERT_U32(0U, result.start_pc);
  M68K_C_ASSERT_U32(4U, result.stop_pc);
  M68K_C_ASSERT_U32(4U, state.pc);
  M68K_C_ASSERT_U32(2U, state.d[0]);
  return 0;
}

static int test_concrete_run_stops_on_instruction_limit(void) {
  uint8_t memory[] = {0x70U, 0x01U, 0x52U, 0x80U};
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 1U, 0U,
    0U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_INSTRUCTION_LIMIT, result.stop_reason);
  M68K_C_ASSERT_U32(1U, (uint32_t)result.step_count);
  M68K_C_ASSERT_U32(2U, result.stop_pc);
  M68K_C_ASSERT_U32(2U, state.pc);
  M68K_C_ASSERT_U32(1U, state.d[0]);
  return 0;
}

static int test_concrete_run_accepts_generated_noop_semantics(void) {
  uint8_t memory[] = {0x4EU, 0x71U, 0x70U, 0x01U};
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 2U, 0U,
    0U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_INSTRUCTION_LIMIT, result.stop_reason);
  M68K_C_ASSERT_U32(2U, (uint32_t)result.step_count);
  M68K_C_ASSERT_U32(4U, state.pc);
  M68K_C_ASSERT_U32(1U, state.d[0]);
  return 0;
}

static int test_concrete_run_reports_pc_out_of_range(void) {
  uint8_t memory[] = {0x70U, 0x01U};
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  state.pc = 4U;
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 8U, 0U,
    0U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_PC_OUT_OF_RANGE, result.stop_reason);
  M68K_C_ASSERT_U32(0U, (uint32_t)result.step_count);
  M68K_C_ASSERT_U32(4U, result.start_pc);
  M68K_C_ASSERT_U32(4U, result.stop_pc);
  return 0;
}

static int test_concrete_run_reports_bad_arguments(void) {
  uint8_t memory[] = {0x70U, 0x01U};
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  M68K_C_ASSERT_INT(-1, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, NULL, sizeof(memory), &state, 8U, 0U,
    0U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_BAD_ARGUMENT, result.stop_reason);
  return 0;
}

static int test_concrete_run_applies_move_postincrement_update(void) {
  uint8_t memory[32] = {
    0x41U, 0xF9U, 0x00U, 0x00U, 0x00U, 0x10U,
    0x10U, 0xFCU, 0x00U, 0x12U,
    0x10U, 0xFCU, 0x00U, 0x34U,
  };
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 3U, 0U,
    0U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_INSTRUCTION_LIMIT, result.stop_reason);
  M68K_C_ASSERT_U32(3U, (uint32_t)result.step_count);
  M68K_C_ASSERT_U32(2U, (uint32_t)result.memory_write_count);
  M68K_C_ASSERT_U32(0x10U, result.memory_write_start);
  M68K_C_ASSERT_U32(0x12U, result.memory_write_end);
  M68K_C_ASSERT_U32(0x12U, state.a[0]);
  M68K_C_ASSERT_U32(0x12U, memory[0x10]);
  M68K_C_ASSERT_U32(0x34U, memory[0x11]);
  return 0;
}

static int test_concrete_run_move_updates_condition_codes(void) {
  uint8_t memory[16] = {0x12U, 0x18U};
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  state.a[0] = 8U;
  state.d[1] = 0xAAAAAAAAU;
  state.sr = 0x2717U;
  memory[8] = 0x05U;
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 1U, 0U,
    0U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_INSTRUCTION_LIMIT, result.stop_reason);
  M68K_C_ASSERT_U32(1U, (uint32_t)result.step_count);
  M68K_C_ASSERT_U32(2U, state.pc);
  M68K_C_ASSERT_U32(9U, state.a[0]);
  M68K_C_ASSERT_U32(0xAAAAAA05U, state.d[1]);
  M68K_C_ASSERT_U32(0x10U, state.sr & 0x1FU);
  return 0;
}

static int test_concrete_run_records_merged_write_ranges(void) {
  uint8_t memory[32] = {
    0x41U, 0xF9U, 0x00U, 0x00U, 0x00U, 0x08U,
    0x10U, 0xFCU, 0x00U, 0xAAU,
    0x10U, 0xFCU, 0x00U, 0xBBU,
    0x41U, 0xF9U, 0x00U, 0x00U, 0x00U, 0x10U,
    0x10U, 0xFCU, 0x00U, 0x12U,
    0x10U, 0xFCU, 0x00U, 0x34U,
  };
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 6U, 0U,
    0U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_INSTRUCTION_LIMIT, result.stop_reason);
  M68K_C_ASSERT_U32(4U, (uint32_t)result.memory_write_count);
  M68K_C_ASSERT_U32(0x08U, result.memory_write_start);
  M68K_C_ASSERT_U32(0x12U, result.memory_write_end);
  M68K_C_ASSERT_U32(2U, (uint32_t)result.memory_write_range_count);
  M68K_C_ASSERT_U32(0U, result.memory_write_range_overflow);
  M68K_C_ASSERT_U32(0x08U, result.memory_write_ranges[0].start);
  M68K_C_ASSERT_U32(0x0AU, result.memory_write_ranges[0].end);
  M68K_C_ASSERT_U32(0x10U, result.memory_write_ranges[1].start);
  M68K_C_ASSERT_U32(0x12U, result.memory_write_ranges[1].end);
  return 0;
}

static int test_concrete_run_allows_policy_external_write(void) {
  uint8_t memory[32] = {
    0x41U, 0xF9U, 0x00U, 0x00U, 0x00U, 0x30U,
    0x10U, 0xFCU, 0x00U, 0xAAU,
    0x41U, 0xF9U, 0x00U, 0x00U, 0x00U, 0x10U,
    0x10U, 0xFCU, 0x00U, 0x12U,
  };
  M68kSimConcreteState state;
  M68kSimConcreteMemoryPolicy memory_policy;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  memset(&memory_policy, 0, sizeof(memory_policy));
  memory_policy.external_write_allowed = test_external_write_allowed;
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 4U, 0U,
    0U, &memory_policy, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_INSTRUCTION_LIMIT, result.stop_reason);
  M68K_C_ASSERT_U32(1U, (uint32_t)result.memory_write_count);
  M68K_C_ASSERT_U32(0x10U, result.memory_write_start);
  M68K_C_ASSERT_U32(0x11U, result.memory_write_end);
  M68K_C_ASSERT_U32(0x12U, memory[0x10]);
  return 0;
}

static int test_concrete_run_allows_policy_external_read_modify_write(void) {
  uint8_t memory[6] = {
    0x00U, 0x9EU, 0x4EU, 0xF9U, 0x00U, 0x05U,
  };
  M68kSimConcreteState state;
  M68kSimConcreteMemoryPolicy memory_policy;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  memset(&memory_policy, 0, sizeof(memory_policy));
  state.a[6] = 0x30U;
  memory_policy.external_read = test_external_long_read;
  memory_policy.external_write_allowed = test_external_long_access_allowed;
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 1U, 0U,
    0U, &memory_policy, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_INSTRUCTION_LIMIT, result.stop_reason);
  M68K_C_ASSERT_U32(1U, (uint32_t)result.step_count);
  M68K_C_ASSERT_U32(6U, state.pc);
  M68K_C_ASSERT_U32(0x34U, state.a[6]);
  return 0;
}

static int test_concrete_run_rejects_unmapped_external_read(void) {
  uint8_t memory[6] = {
    0x00U, 0x9EU, 0x4EU, 0xF9U, 0x00U, 0x05U,
  };
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  state.a[6] = 0x30U;
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 1U, 0U,
    0U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_SIMULATION_ERROR, result.stop_reason);
  M68K_C_ASSERT_U32(0U, (uint32_t)result.step_count);
  M68K_C_ASSERT_U32(0x30U, state.a[6]);
  return 0;
}

static int test_concrete_run_shifts_memory_indirect_without_ea_update(void) {
  uint8_t memory[16] = {
    0xE2U, 0xD0U,
  };
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  state.a[0] = 8U;
  memory[8] = 0x80U;
  memory[9] = 0x01U;
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 1U, 0U,
    0U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_INSTRUCTION_LIMIT, result.stop_reason);
  M68K_C_ASSERT_U32(8U, state.a[0]);
  M68K_C_ASSERT_U32(0x40U, memory[8]);
  M68K_C_ASSERT_U32(0x00U, memory[9]);
  return 0;
}

static int test_concrete_run_moves_immediate_to_ccr_from_metadata(void) {
  uint8_t memory[4] = {0x44U, 0xFCU, 0x00U, 0x10U};
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  state.sr = 0x2700U;
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 1U, 0U,
    0U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_INSTRUCTION_LIMIT, result.stop_reason);
  M68K_C_ASSERT_U32(1U, (uint32_t)result.step_count);
  M68K_C_ASSERT_U32(4U, state.pc);
  M68K_C_ASSERT_U32(0x2710U, state.sr);
  return 0;
}

static int test_concrete_run_branches_on_carry_from_ccr(void) {
  uint8_t memory[12] = {
    0x44U, 0xFCU, 0x00U, 0x11U,
    0x65U, 0x04U,
    0x70U, 0x01U,
    0x60U, 0x02U,
    0x70U, 0x02U,
  };
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 4U, 12U,
    14U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_PC_RANGE, result.stop_reason);
  M68K_C_ASSERT_U32(2U, state.d[0]);
  return 0;
}

static int test_concrete_run_branches_on_signed_less_than_compare(void) {
  uint8_t memory[16] = {
    0x70U, 0x01U,
    0x0CU, 0x00U, 0x00U, 0x02U,
    0x6DU, 0x04U,
    0x70U, 0x03U,
    0x60U, 0x02U,
    0x70U, 0x04U,
  };
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 5U, 14U,
    16U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_PC_RANGE, result.stop_reason);
  M68K_C_ASSERT_U32(4U, state.d[0]);
  return 0;
}

static int test_concrete_run_roxr_uses_extend_and_sets_carry(void) {
  uint8_t memory[16] = {
    0x44U, 0xFCU, 0x00U, 0x10U,
    0x20U, 0x3CU, 0x00U, 0x00U, 0x00U, 0x01U,
    0xE2U, 0x90U,
  };
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 3U, 12U,
    14U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_PC_RANGE, result.stop_reason);
  M68K_C_ASSERT_U32(0x80000000U, state.d[0]);
  M68K_C_ASSERT_U32(0x19U, state.sr & 0x1FU);
  return 0;
}

static int test_concrete_run_add_register_zero_is_not_quick_8(void) {
  uint8_t memory[8] = {
    0x76U, 0x05U,
    0x78U, 0x00U,
    0xD6U, 0x44U,
  };
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 3U, 6U,
    8U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_PC_RANGE, result.stop_reason);
  M68K_C_ASSERT_U32(5U, state.d[3]);
  return 0;
}

static int test_concrete_run_addq_zero_encoding_means_8(void) {
  uint8_t memory[8] = {
    0x70U, 0x01U,
    0x50U, 0x40U,
  };
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 2U, 4U,
    6U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_PC_RANGE, result.stop_reason);
  M68K_C_ASSERT_U32(9U, state.d[0]);
  return 0;
}

static int test_concrete_run_takes_metadata_only_conditional_branch(void) {
  uint8_t memory[8] = {
    0xB3U, 0xCCU,
    0x6EU, 0x02U,
    0x70U, 0x01U,
    0x70U, 0x02U,
  };
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  state.a[1] = 0x20U;
  state.a[4] = 0x10U;
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 3U, 0U,
    0U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_INSTRUCTION_LIMIT, result.stop_reason);
  M68K_C_ASSERT_U32(3U, (uint32_t)result.step_count);
  M68K_C_ASSERT_U32(8U, state.pc);
  M68K_C_ASSERT_U32(2U, state.d[0]);
  return 0;
}

static int test_concrete_run_applies_move_source_predecrement_update(void) {
  uint8_t memory[32] = {0x14U, 0x22U};
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  state.a[2] = 0x10U;
  state.d[2] = 0x12345678U;
  memory[0x0F] = 0x5AU;
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 1U, 0U,
    0U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_INSTRUCTION_LIMIT, result.stop_reason);
  M68K_C_ASSERT_U32(1U, (uint32_t)result.step_count);
  M68K_C_ASSERT_U32(2U, state.pc);
  M68K_C_ASSERT_U32(0x0FU, state.a[2]);
  M68K_C_ASSERT_U32(0x1234565AU, state.d[2]);
  return 0;
}

static int test_concrete_run_rejects_wrapped_predecrement_read(void) {
  uint8_t memory[16] = {0x20U, 0x27U};
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  state.a[7] = 0U;
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 1U, 0U,
    0U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_SIMULATION_ERROR, result.stop_reason);
  M68K_C_ASSERT_U32(0U, (uint32_t)result.step_count);
  return 0;
}

static int test_concrete_run_applies_move_dest_predecrement_update(void) {
  uint8_t memory[32] = {0x15U, 0x02U};
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  state.a[2] = 0x10U;
  state.d[2] = 0xAAU;
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 1U, 0U,
    0U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_INSTRUCTION_LIMIT, result.stop_reason);
  M68K_C_ASSERT_U32(1U, (uint32_t)result.step_count);
  M68K_C_ASSERT_U32(1U, (uint32_t)result.memory_write_count);
  M68K_C_ASSERT_U32(0x0FU, result.memory_write_start);
  M68K_C_ASSERT_U32(0x10U, result.memory_write_end);
  M68K_C_ASSERT_U32(2U, state.pc);
  M68K_C_ASSERT_U32(0x0FU, state.a[2]);
  M68K_C_ASSERT_U32(0xAAU, memory[0x0F]);
  return 0;
}

static int test_concrete_run_sign_extends_index_word_address(void) {
  uint8_t memory[32] = {0x10U, 0x32U, 0x20U, 0xFFU};
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  state.a[2] = 0x10U;
  state.d[2] = 0xFFFFU;
  state.d[0] = 0x12345678U;
  memory[0x0E] = 0x5AU;
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 1U, 0U,
    0U, NULL, &result));
  M68K_C_ASSERT_U32(M68K_SIM_CONCRETE_RUN_STOP_INSTRUCTION_LIMIT, result.stop_reason);
  M68K_C_ASSERT_U32(1U, (uint32_t)result.step_count);
  M68K_C_ASSERT_U32(4U, state.pc);
  M68K_C_ASSERT_U32(0x1234565AU, state.d[0]);
  return 0;
}

int m68k_c_simulator_tests(void) {
  static const M68kCTestCase cases[] = {
    {"metadata_lookup_uses_canonical_form_id", test_metadata_lookup_uses_canonical_form_id},
    {"metadata_lookup_uses_generated_ccr_formulas", test_metadata_lookup_uses_generated_ccr_formulas},
    {"metadata_lookup_reports_missing_generated_semantics",
      test_metadata_lookup_reports_missing_generated_semantics},
    {"metadata_lookup_reports_missing_for_canonical_form_without_sim_row",
      test_metadata_lookup_reports_missing_for_canonical_form_without_sim_row},
    {"metadata_lookup_does_not_fallback_to_mnemonic_shape",
      test_metadata_lookup_does_not_fallback_to_mnemonic_shape},
    {"concrete_run_stops_on_pc_range", test_concrete_run_stops_on_pc_range},
    {"concrete_run_stops_on_instruction_limit", test_concrete_run_stops_on_instruction_limit},
    {"concrete_run_accepts_generated_noop_semantics", test_concrete_run_accepts_generated_noop_semantics},
    {"concrete_run_reports_pc_out_of_range", test_concrete_run_reports_pc_out_of_range},
    {"concrete_run_reports_bad_arguments", test_concrete_run_reports_bad_arguments},
    {"concrete_run_applies_move_postincrement_update", test_concrete_run_applies_move_postincrement_update},
    {"concrete_run_move_updates_condition_codes", test_concrete_run_move_updates_condition_codes},
    {"concrete_run_records_merged_write_ranges", test_concrete_run_records_merged_write_ranges},
    {"concrete_run_allows_policy_external_write", test_concrete_run_allows_policy_external_write},
    {"concrete_run_allows_policy_external_read_modify_write",
      test_concrete_run_allows_policy_external_read_modify_write},
    {"concrete_run_rejects_unmapped_external_read", test_concrete_run_rejects_unmapped_external_read},
    {"concrete_run_shifts_memory_indirect_without_ea_update",
      test_concrete_run_shifts_memory_indirect_without_ea_update},
    {"concrete_run_moves_immediate_to_ccr_from_metadata",
      test_concrete_run_moves_immediate_to_ccr_from_metadata},
    {"concrete_run_branches_on_carry_from_ccr", test_concrete_run_branches_on_carry_from_ccr},
    {"concrete_run_branches_on_signed_less_than_compare",
      test_concrete_run_branches_on_signed_less_than_compare},
    {"concrete_run_roxr_uses_extend_and_sets_carry",
      test_concrete_run_roxr_uses_extend_and_sets_carry},
    {"concrete_run_add_register_zero_is_not_quick_8",
      test_concrete_run_add_register_zero_is_not_quick_8},
    {"concrete_run_addq_zero_encoding_means_8",
      test_concrete_run_addq_zero_encoding_means_8},
    {"concrete_run_takes_metadata_only_conditional_branch",
      test_concrete_run_takes_metadata_only_conditional_branch},
    {"concrete_run_applies_move_source_predecrement_update",
      test_concrete_run_applies_move_source_predecrement_update},
    {"concrete_run_rejects_wrapped_predecrement_read",
      test_concrete_run_rejects_wrapped_predecrement_read},
    {"concrete_run_applies_move_dest_predecrement_update",
      test_concrete_run_applies_move_dest_predecrement_update},
    {"concrete_run_sign_extends_index_word_address",
      test_concrete_run_sign_extends_index_word_address},
  };
  return m68k_c_test_run_suite("m68k_simulator", cases, sizeof(cases) / sizeof(cases[0]));
}
