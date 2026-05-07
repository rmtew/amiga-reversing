#include "m68k_c_unit_test.h"
#include "m68k_simulator.h"
#include "generated/m68k_asm_tables.h"

#include <string.h>

static int test_external_write_allowed(void *user, uint32_t address, uint8_t width) {
  (void)user;
  return address == 0x30U && width == 1U;
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
    {"concrete_run_stops_on_pc_range", test_concrete_run_stops_on_pc_range},
    {"concrete_run_stops_on_instruction_limit", test_concrete_run_stops_on_instruction_limit},
    {"concrete_run_reports_pc_out_of_range", test_concrete_run_reports_pc_out_of_range},
    {"concrete_run_reports_bad_arguments", test_concrete_run_reports_bad_arguments},
    {"concrete_run_applies_move_postincrement_update", test_concrete_run_applies_move_postincrement_update},
    {"concrete_run_records_merged_write_ranges", test_concrete_run_records_merged_write_ranges},
    {"concrete_run_allows_policy_external_write", test_concrete_run_allows_policy_external_write},
    {"concrete_run_moves_immediate_to_ccr_from_metadata",
      test_concrete_run_moves_immediate_to_ccr_from_metadata},
    {"concrete_run_takes_metadata_only_conditional_branch",
      test_concrete_run_takes_metadata_only_conditional_branch},
    {"concrete_run_applies_move_source_predecrement_update",
      test_concrete_run_applies_move_source_predecrement_update},
    {"concrete_run_applies_move_dest_predecrement_update",
      test_concrete_run_applies_move_dest_predecrement_update},
    {"concrete_run_sign_extends_index_word_address",
      test_concrete_run_sign_extends_index_word_address},
  };
  return m68k_c_test_run_suite("m68k_simulator", cases, sizeof(cases) / sizeof(cases[0]));
}
