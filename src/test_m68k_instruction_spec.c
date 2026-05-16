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
  M68kOperandIR indirect = make_ea_operand(2u, 0u, 0u);
  M68kOperandIR postinc = make_ea_operand(3u, 1u, 0u);
  M68kOperandIR predec = make_ea_operand(4u, 2u, 0u);
  M68kOperandIR disp = make_ea_operand(5u, 3u, 0x10u);
  M68kOperandIR index = make_ea_operand(6u, 0u, 0x10u);
  M68kOperandIR pcdisp = make_ea_operand(7u, 2u, 0xFFFFFFF8u);
  M68kOperandIR pcindex = make_ea_operand(7u, 3u, 0x10u);

  M68K_C_ASSERT_INT(M68K_SIM_EA_SHAPE_INDIRECT, m68k_instruction_operand_decoded_ea_shape(&indirect));
  M68K_C_ASSERT_INT(M68K_SIM_EA_SHAPE_POSTINCREMENT, m68k_instruction_operand_decoded_ea_shape(&postinc));
  M68K_C_ASSERT_INT(M68K_SIM_EA_SHAPE_PREDECREMENT, m68k_instruction_operand_decoded_ea_shape(&predec));
  M68K_C_ASSERT_INT(M68K_SIM_EA_SHAPE_DISPLACEMENT, m68k_instruction_operand_decoded_ea_shape(&disp));
  M68K_C_ASSERT_INT(M68K_SIM_EA_SHAPE_ABSOLUTE_WORD, m68k_instruction_operand_decoded_ea_shape(&absw));
  M68K_C_ASSERT_INT(M68K_SIM_EA_SHAPE_ABSOLUTE_LONG, m68k_instruction_operand_decoded_ea_shape(&absl));
  M68K_C_ASSERT_INT(M68K_SIM_EA_SHAPE_INDEX, m68k_instruction_operand_decoded_ea_shape(&index));
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

static int test_instruction_spec_mnemonic_resolution(void) {
  InstructionSpec instruction;
  const M68kAsmFormDef *form;

  memset(&instruction, 0, sizeof(instruction));
  instruction.asm_form_index = M68K_ASM_FORM_NONE;
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_NONE, instruction.mnemonic_id);
  M68K_C_ASSERT_STR("", m68k_instruction_spec_mnemonic_name(&instruction));
  instruction.mnemonic_id = M68K_ASM_MNEMONIC_JSR;
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_JSR, instruction.mnemonic_id);
  M68K_C_ASSERT_STR("jsr", m68k_instruction_spec_mnemonic_name(&instruction));

  memset(&instruction, 0, sizeof(instruction));
  instruction.asm_form_index = M68K_ASM_FORM_NONE;
  instruction.mnemonic_id = M68K_ASM_MNEMONIC_MOVEQ;
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_MOVEQ, instruction.mnemonic_id);
  M68K_C_ASSERT_STR("moveq", m68k_instruction_spec_mnemonic_name(&instruction));

  memset(&instruction, 0, sizeof(instruction));
  form = &g_m68k_asm_forms[m68k_asm_form_index_for_id(M68K_ASM_MNEMONIC_MOVE, 2U)];
  M68K_C_ASSERT(form->mnemonic_id != M68K_ASM_MNEMONIC_NONE);
  instruction.asm_form_index = form->asm_form_index;
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_NONE, instruction.mnemonic_id);
  M68K_C_ASSERT_STR("", m68k_instruction_spec_mnemonic_name(&instruction));
  instruction.mnemonic_id = M68K_ASM_MNEMONIC_MOVE;
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_MOVE, instruction.mnemonic_id);
  M68K_C_ASSERT_STR(form->mnemonic, m68k_instruction_spec_mnemonic_name(&instruction));
  return 0;
}

static int test_assembler_canonical_form_resolution(void) {
  M68kAsmOperandValue operands[2];
  M68kFormId form_id;
  uint16_t asm_form_index;
  const M68kAsmFormDef *form;

  memset(operands, 0, sizeof(operands));
  operands[0].kind = M68K_ASM_OPERAND_EA;
  operands[0].ea_mode = 2u;
  operands[0].ea_reg = 0u;
  operands[1].kind = M68K_ASM_OPERAND_DN;
  operands[1].reg = 1u;

  form_id = m68k_asm_canonical_form_id_for_operands_id(M68K_ASM_MNEMONIC_ADD, operands, 2U, '\0', M68K_ASM_CPU_68000);
  M68K_C_ASSERT_U32(0U, (uint32_t)M68K_FORM_ID_NONE);
  M68K_C_ASSERT(form_id != M68K_FORM_ID_NONE);

  asm_form_index = m68k_asm_form_index_for_canonical_id(form_id);
  M68K_C_ASSERT(asm_form_index != M68K_ASM_FORM_NONE);
  form = &g_m68k_asm_forms[asm_form_index];
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_ADD, form->mnemonic_id);
  M68K_C_ASSERT_U32(form_id, form->canonical_form_id);
  M68K_C_ASSERT_U32((uint32_t)asm_form_index, (uint32_t)form->asm_form_index);
  return 0;
}

int m68k_c_instruction_spec_tests(void) {
  static const M68kCTestCase cases[] = {
    {"direct_register_detection", test_direct_register_detection},
    {"decoded_ea_shape_and_target_kind", test_decoded_ea_shape_and_target_kind},
    {"decoded_ea_target_resolution", test_decoded_ea_target_resolution},
    {"instruction_spec_mnemonic_resolution", test_instruction_spec_mnemonic_resolution},
    {"assembler_canonical_form_resolution", test_assembler_canonical_form_resolution},
  };
  return m68k_c_test_run_suite("m68k_instruction_spec", cases, sizeof(cases) / sizeof(cases[0]));
}

