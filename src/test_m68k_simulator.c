#include "m68k_c_unit_test.h"
#include "m68k_simulator.h"
#include "generated/m68k_asm_tables.h"

#include <string.h>

static int test_concrete_run_stops_on_pc_range(void) {
  uint8_t memory[] = {0x70U, 0x01U, 0x52U, 0x80U};
  M68kSimConcreteState state;
  M68kSimConcreteRunTraceResult result;
  memset(&state, 0, sizeof(state));
  M68K_C_ASSERT_INT(0, m68k_simulate_run_concrete(M68K_ASM_CPU_68000, memory, sizeof(memory), &state, 8U, 4U,
    6U, &result));
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
    0U, &result));
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
    0U, &result));
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
    0U, &result));
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
    0U, &result));
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

int m68k_c_simulator_tests(void) {
  static const M68kCTestCase cases[] = {
    {"concrete_run_stops_on_pc_range", test_concrete_run_stops_on_pc_range},
    {"concrete_run_stops_on_instruction_limit", test_concrete_run_stops_on_instruction_limit},
    {"concrete_run_reports_pc_out_of_range", test_concrete_run_reports_pc_out_of_range},
    {"concrete_run_reports_bad_arguments", test_concrete_run_reports_bad_arguments},
    {"concrete_run_applies_move_postincrement_update", test_concrete_run_applies_move_postincrement_update},
  };
  return m68k_c_test_run_suite("m68k_simulator", cases, sizeof(cases) / sizeof(cases[0]));
}
