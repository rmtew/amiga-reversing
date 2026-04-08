#include "m68k_c_unit_test.h"
#include "m68k_instruction_spec.h"
#include "m68k_simulator.h"

#include <string.h>

static M68kOperandIR make_ea_operand(uint8_t mode, uint8_t reg, uint32_t value) {
  M68kOperandIR operand;
  memset(&operand, 0, sizeof(operand));
  operand.kind = M68K_ASM_OPERAND_EA;
  operand.value.ea_mode = mode;
  operand.value.ea_reg = reg;
  operand.value.value = value;
  return operand;
}

static int test_direct_register_detection(void) {
  M68kOperandIR operand;
  uint8_t is_address = 0xFFu;
  uint8_t reg = 0xFFu;

  memset(&operand, 0, sizeof(operand));
  operand.kind = M68K_ASM_OPERAND_DN;
  operand.value.reg = 3u;
  M68K_C_ASSERT(m68k_instruction_operand_direct_register(&operand, &is_address, &reg));
  M68K_C_ASSERT_INT(0, is_address);
  M68K_C_ASSERT_INT(3, reg);

  memset(&operand, 0, sizeof(operand));
  operand.kind = M68K_ASM_OPERAND_EA;
  operand.value.ea_mode = 1u;
  operand.value.ea_reg = 6u;
  M68K_C_ASSERT(m68k_instruction_operand_direct_register(&operand, &is_address, &reg));
  M68K_C_ASSERT_INT(1, is_address);
  M68K_C_ASSERT_INT(6, reg);

  operand.value.ea_mode = 2u;
  M68K_C_ASSERT(!m68k_instruction_operand_direct_register(&operand, &is_address, &reg));
  return 0;
}

static int test_decoded_ea_shape_and_target_kind(void) {
  M68kOperandIR absw = make_ea_operand(7u, 0u, 0x1234u);
  M68kOperandIR absl = make_ea_operand(7u, 1u, 0x12345678u);
  M68kOperandIR pcdisp = make_ea_operand(7u, 2u, 0xFFFFFFF8u);
  M68kOperandIR pcindex = make_ea_operand(7u, 3u, 0x10u);

  M68K_C_ASSERT_INT(M68K_SIM_EA_SHAPE_ABSOLUTE_WORD, m68k_instruction_operand_decoded_ea_shape(&absw));
  M68K_C_ASSERT_INT(M68K_SIM_EA_SHAPE_ABSOLUTE_LONG, m68k_instruction_operand_decoded_ea_shape(&absl));
  M68K_C_ASSERT_INT(M68K_SIM_EA_SHAPE_PC_DISPLACEMENT, m68k_instruction_operand_decoded_ea_shape(&pcdisp));
  M68K_C_ASSERT_INT(M68K_SIM_EA_SHAPE_PC_INDEX, m68k_instruction_operand_decoded_ea_shape(&pcindex));

  M68K_C_ASSERT_INT(1, m68k_instruction_decoded_ea_target_kind(&absl,
    m68k_instruction_operand_decoded_ea_shape(&absl), 0));
  M68K_C_ASSERT_INT(2, m68k_instruction_decoded_ea_target_kind(&pcdisp,
    m68k_instruction_operand_decoded_ea_shape(&pcdisp), 0));
  M68K_C_ASSERT_INT(0, m68k_instruction_decoded_ea_target_kind(&pcindex,
    m68k_instruction_operand_decoded_ea_shape(&pcindex), 0));
  M68K_C_ASSERT_INT(2, m68k_instruction_decoded_ea_target_kind(&pcindex,
    m68k_instruction_operand_decoded_ea_shape(&pcindex), 1));
  return 0;
}

static int test_decoded_ea_target_resolution(void) {
  M68kOperandIR absolute = make_ea_operand(7u, 1u, 0x200u);
  M68kOperandIR pcdisp = make_ea_operand(7u, 2u, 0xFFFFFFF0u);
  uint32_t target = 0;

  M68K_C_ASSERT(m68k_instruction_decoded_ea_target(&absolute,
    m68k_instruction_operand_decoded_ea_shape(&absolute), 0x100u, 0x1000u, 0, &target));
  M68K_C_ASSERT_U32(0x200u, target);

  M68K_C_ASSERT(m68k_instruction_decoded_ea_target(&pcdisp,
    m68k_instruction_operand_decoded_ea_shape(&pcdisp), 0x120u, 0x1000u, 0, &target));
  M68K_C_ASSERT_U32(0x110u, target);

  absolute.value.value = 0x2000u;
  M68K_C_ASSERT(!m68k_instruction_decoded_ea_target(&absolute,
    m68k_instruction_operand_decoded_ea_shape(&absolute), 0x100u, 0x1000u, 0, &target));
  return 0;
}

int m68k_c_instruction_spec_tests(void) {
  static const M68kCTestCase cases[] = {
    {"direct_register_detection", test_direct_register_detection},
    {"decoded_ea_shape_and_target_kind", test_decoded_ea_shape_and_target_kind},
    {"decoded_ea_target_resolution", test_decoded_ea_target_resolution},
  };
  return m68k_c_test_run_suite("m68k_instruction_spec", cases, sizeof(cases) / sizeof(cases[0]));
}
