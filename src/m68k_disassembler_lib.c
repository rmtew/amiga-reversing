#include "m68k_disassembler.h"
#include "m68k_disassembler_lib.h"
#include "m68k_assembler.h"
#include "m68k_ir.h"
#include "m68k_ir_codec.h"
#include "m68k_simulator.h"

#include <stdio.h>
#include <string.h>

static M68kDisasmTextResult m68k_disassemble_one_text_impl(const uint8_t *data, size_t size, uint8_t target_cpu) {
  M68kDisasmTextResult result;
  M68kInstructionIR instruction;
  M68kRenderPolicy policy;
  M68kIrRenderResult rendered;
  memset(&result, 0, sizeof(result));
  instruction = m68k_ir_decode_one(data, size, target_cpu, m68k_diag_sink(&result.diagnostics));
  if (m68k_diag_has_errors(&result.diagnostics) || instruction.byte_count == 0U) return result;
  m68k_render_policy_init_default(&policy);
  rendered = m68k_ir_render_one_with_policy(&instruction, &policy, m68k_diag_sink(&result.diagnostics));
  if (m68k_diag_has_errors(&result.diagnostics)) return result;
  snprintf(result.text, sizeof(result.text), "%s", rendered.text);
  result.byte_count = instruction.byte_count;
  return result;
}

M68kDisasmTextResult m68k_disassemble_one_text(const uint8_t *data, size_t size) {
  return m68k_disassemble_one_text_impl(data, size, M68K_ASM_CPU_68000);
}

M68kDisasmTextResult m68k_disassemble_one_text_for_cpu(const uint8_t *data, size_t size, uint8_t target_cpu) {
  return m68k_disassemble_one_text_impl(data, size, target_cpu);
}

M68kDisasmInfoResult m68k_disassemble_one_info_for_cpu(const uint8_t *data, size_t size, uint8_t target_cpu) {
  M68kDisasmInfoResult result;
  M68kDisasmResult disasm;
  memset(&result, 0, sizeof(result));
  disasm = m68k_disassemble_one_for_cpu(data, size, target_cpu, m68k_diag_sink(&result.diagnostics));
  if (m68k_diag_has_errors(&result.diagnostics) || disasm.byte_count == 0U) return result;
  result.byte_count = disasm.byte_count;
  result.asm_form_index = disasm.asm_form_index;
  result.mnemonic_id = disasm.mnemonic_id;
  result.target_cpu = disasm.target_cpu;
  snprintf(result.mnemonic, sizeof(result.mnemonic), "%s", disasm.mnemonic);
  result.size_suffix = disasm.size_suffix;
  result.operand_count = disasm.operand_count;
  return result;
}

M68kSimConcreteRunResult m68k_simulate_one_concrete_for_cpu(const uint8_t *data, size_t size, uint8_t target_cpu,
    uint8_t *memory, size_t memory_size, M68kSimConcreteState *io_state) {
  M68kSimConcreteRunResult result;
  M68kInstructionIR instruction;
  memset(&result, 0, sizeof(result));
  instruction = m68k_ir_decode_one(data, size, target_cpu, m68k_diag_sink(&result.diagnostics));
  if (m68k_diag_has_errors(&result.diagnostics) || instruction.byte_count == 0U) return result;
  m68k_simulate_step_concrete(&instruction, target_cpu, data, size, memory, memory_size, io_state,
    m68k_diag_sink(&result.diagnostics));
  return result;
}

M68kSimAbstractRunResult m68k_simulate_one_abstract_for_cpu(const uint8_t *data, size_t size, uint8_t target_cpu,
    const M68kSimCpuState *state) {
  M68kSimAbstractRunResult result;
  M68kInstructionIR instruction;
  M68kSection section;
  memset(&result, 0, sizeof(result));
  if (state == NULL) {
    m68k_diag_add(m68k_diag_sink(&result.diagnostics), M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_BAD_ARGUMENT,
      "bad arguments");
    return result;
  }
  instruction = m68k_ir_decode_one(data, size, target_cpu, m68k_diag_sink(&result.diagnostics));
  if (m68k_diag_has_errors(&result.diagnostics) || instruction.byte_count == 0U) return result;
  memset(&section, 0, sizeof(section));
  section.data = (uint8_t *)data;
  section.data_size = (uint32_t)size;
  if (m68k_simulate_step(NULL, 0U, &section, 0U, &instruction, state, &result.step) != 0) {
    m68k_diag_add(m68k_diag_sink(&result.diagnostics), M68K_DIAG_SEVERITY_ERROR,
      M68K_DIAG_CODE_SIMULATION_FAILED, "abstract simulation failed");
  }
  return result;
}
