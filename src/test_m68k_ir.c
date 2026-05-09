#include "m68k_c_unit_test.h"
#include "m68k_analysis_facts_v2.h"
#include "m68k_backend.h"
#include "m68k_decode_ir.h"
#include "m68k_fact_ir.h"
#include "m68k_ir.h"
#include "m68k_ir_codec.h"
#include "m68k_object.h"
#include "m68k_plain_parse.h"
#include "m68k_render_ir.h"
#include "m68k_render_lookup_internal.h"
#include "m68k_simulator.h"
#include "m68k_source_model.h"
#include "m68k_source_pipeline.h"
#include "platform_common.h"
#include "platform_file_internal.h"
#include "platform_atari_st.h"
#include "util_arena.h"
#include "generated/amiga_hunk_file_runtime.h"
#include "generated/amiga_os_runtime.h"
#include "generated/m68k_cpu_runtime.h"

#include <stdlib.h>
#include <string.h>

static int test_render_policy_defaults(void) {
  M68kRenderPolicy policy;
  memset(&policy, 0xA5, sizeof(policy));
  m68k_render_policy_init_default(&policy);
  M68K_C_ASSERT_INT(M68K_IR_SYNTAX_CANONICAL, policy.syntax.syntax_mode);
  M68K_C_ASSERT_INT(1, policy.presentation.prefer_generated_names);
  M68K_C_ASSERT_INT(1, policy.presentation.prefer_strings);
  M68K_C_ASSERT_INT(1, policy.presentation.prefer_long_data);
  M68K_C_ASSERT_STR("loc", policy.presentation.code_label_prefix);
  M68K_C_ASSERT_STR("sub", policy.presentation.call_label_prefix);
  M68K_C_ASSERT_STR("dat", policy.presentation.data_label_prefix);
  return 0;
}

static int test_source_statement_renderer_renders_single_statement(void) {
  M68kStatementIR stmt;
  uint8_t bytes[3] = {0x41u, 0x42u, 0x00u};
  char *text = NULL;
  m68k_ir_statement_init(&stmt);
  stmt.kind = M68K_STATEMENT_DATA;
  stmt.offset = 0x20U;
  stmt.u.data.kind = M68K_DATA_ITEM_BYTES;
  stmt.u.data.data = bytes;
  stmt.u.data.size = sizeof(bytes);
  M68K_C_ASSERT_INT(0, m68k_source_ir_render_statement_text_with_policy(&stmt, NULL, &text,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(text != NULL);
  M68K_C_ASSERT(strstr(text, "DC.B") != NULL);
  M68K_C_ASSERT(strstr(text, "$41,$42,$00") != NULL);
  free(text);
  return 0;
}

static int test_parse_syntax_mode_name(void) {
  uint8_t mode = 0xFFu;
  M68K_C_ASSERT(m68k_ir_parse_syntax_mode_name("canonical", &mode));
  M68K_C_ASSERT_INT(M68K_IR_SYNTAX_CANONICAL, mode);
  M68K_C_ASSERT(m68k_ir_parse_syntax_mode_name("GENAM", &mode));
  M68K_C_ASSERT_INT(M68K_IR_SYNTAX_GENAM, mode);
  M68K_C_ASSERT(m68k_ir_parse_syntax_mode_name("vasm", &mode));
  M68K_C_ASSERT_INT(M68K_IR_SYNTAX_VASM, mode);
  M68K_C_ASSERT(!m68k_ir_parse_syntax_mode_name("other", &mode));
  return 0;
}

static int test_render_index_scale_uses_scale_value_not_bits(void) {
  M68kRenderPolicy policy;
  M68kInstructionIR instruction;
  M68kIrRenderResult rendered;
  uint8_t bytes[4] = {0x44u, 0x33u, 0x33u, 0x54u};
  m68k_render_policy_init_default(&policy);
  instruction = m68k_ir_decode_one(bytes, sizeof(bytes), M68K_ASM_CPU_68020, m68k_diag_sink(NULL));
  M68K_C_ASSERT_U32(4U, instruction.byte_count);
  rendered = m68k_ir_render_one_with_policy(&instruction, &policy, m68k_diag_sink(NULL));
  M68K_C_ASSERT(strstr(rendered.text, "d3.w*2") != NULL);
  M68K_C_ASSERT(strstr(rendered.text, "d3.w*1") == NULL);
  return 0;
}

static int assert_decode_render_parse_encode_68030(const uint8_t *bytes, size_t byte_count,
    const char *expected_text) {
  M68kRenderPolicy policy;
  M68kInstructionIR decoded;
  M68kInstructionIR parsed;
  M68kIrRenderResult rendered;
  M68kIrEncodeResult encoded;
  uint8_t out_bytes[16];
  m68k_render_policy_init_default(&policy);
  decoded = m68k_ir_decode_one(bytes, byte_count, M68K_ASM_CPU_68030, m68k_diag_sink(NULL));
  M68K_C_ASSERT_U32((uint32_t)byte_count, (uint32_t)decoded.byte_count);
  rendered = m68k_ir_render_one_with_policy(&decoded, &policy, m68k_diag_sink(NULL));
  M68K_C_ASSERT_STR(expected_text, rendered.text);
  encoded = m68k_ir_encode_one(&decoded, out_bytes, sizeof(out_bytes), m68k_diag_sink(NULL));
  M68K_C_ASSERT_U32((uint32_t)byte_count, (uint32_t)encoded.byte_count);
  M68K_C_ASSERT(memcmp(out_bytes, bytes, byte_count) == 0);
  parsed = m68k_plain_parse_instruction_to_ir(expected_text, M68K_ASM_CPU_68030, m68k_diag_sink(NULL));
  encoded = m68k_ir_encode_one(&parsed, out_bytes, sizeof(out_bytes), m68k_diag_sink(NULL));
  M68K_C_ASSERT_U32((uint32_t)byte_count, (uint32_t)encoded.byte_count);
  M68K_C_ASSERT(memcmp(out_bytes, bytes, byte_count) == 0);
  return 0;
}

static int test_68030_pmmu_fc_forms_roundtrip_from_kb(void) {
  const uint8_t ptestr_imm[4] = {0xF0u, 0x12u, 0x9Eu, 0x15u};
  const uint8_t ptestr_dn[4] = {0xF0u, 0x12u, 0x9Eu, 0x0Au};
  const uint8_t pmove_psr[4] = {0xF0u, 0x17u, 0x62u, 0x00u};
  const uint8_t pmove_tc[6] = {0xF0u, 0x2Eu, 0x40u, 0x00u, 0x07u, 0x8Au};
  const uint8_t pmove_crp[6] = {0xF0u, 0x2Eu, 0x4Cu, 0x00u, 0x07u, 0x8Au};
  const uint8_t ploadr_imm[4] = {0xF0u, 0x12u, 0x22u, 0x15u};
  const uint8_t pflush_imm[4] = {0xF0u, 0x12u, 0x38u, 0xF5u};
  const uint8_t pflush_dn[4] = {0xF0u, 0x12u, 0x38u, 0xEAu};
  M68K_C_ASSERT_INT(0, assert_decode_render_parse_encode_68030(ptestr_imm, sizeof(ptestr_imm),
    "ptestr #5,(a2),#7"));
  M68K_C_ASSERT_INT(0, assert_decode_render_parse_encode_68030(ptestr_dn, sizeof(ptestr_dn),
    "ptestr d2,(a2),#7"));
  M68K_C_ASSERT_INT(0, assert_decode_render_parse_encode_68030(pmove_psr, sizeof(pmove_psr),
    "pmove psr,(a7)"));
  M68K_C_ASSERT_INT(0, assert_decode_render_parse_encode_68030(pmove_tc, sizeof(pmove_tc),
    "pmove $078A(a6),tc"));
  M68K_C_ASSERT_INT(0, assert_decode_render_parse_encode_68030(pmove_crp, sizeof(pmove_crp),
    "pmove $078A(a6),crp"));
  M68K_C_ASSERT_INT(0, assert_decode_render_parse_encode_68030(ploadr_imm, sizeof(ploadr_imm),
    "ploadr #5,(a2)"));
  M68K_C_ASSERT_INT(0, assert_decode_render_parse_encode_68030(pflush_imm, sizeof(pflush_imm),
    "pflush #5,#7,(a2)"));
  M68K_C_ASSERT_INT(0, assert_decode_render_parse_encode_68030(pflush_dn, sizeof(pflush_dn),
    "pflush d2,#7,(a2)"));
  return 0;
}

static int test_movec_control_register_cpu_mask_from_kb(void) {
  M68kRenderPolicy policy;
  M68kInstructionIR decoded;
  M68kIrRenderResult rendered;
  uint8_t bytes[4] = {0x4Eu, 0x7Au, 0x00u, 0x02u};
  m68k_render_policy_init_default(&policy);
  decoded = m68k_ir_decode_one(bytes, sizeof(bytes), M68K_ASM_CPU_68010, m68k_diag_sink(NULL));
  M68K_C_ASSERT_U32(0U, (uint32_t)decoded.byte_count);
  decoded = m68k_ir_decode_one(bytes, sizeof(bytes), M68K_ASM_CPU_68020, m68k_diag_sink(NULL));
  M68K_C_ASSERT_U32(4U, (uint32_t)decoded.byte_count);
  rendered = m68k_ir_render_one_with_policy(&decoded, &policy, m68k_diag_sink(NULL));
  M68K_C_ASSERT_STR("movec cacr,d0", rendered.text);
  return 0;
}

static int test_coprocessor_id_roundtrips_from_kb_id_field(void) {
  M68kInstructionIR decoded;
  M68kIrEncodeResult encoded;
  M68kRenderPolicy policy;
  M68kIrRenderResult rendered;
  uint8_t out_bytes[4];
  const uint8_t bytes[2] = {0xFBu, 0x54u};
  decoded = m68k_ir_decode_one(bytes, sizeof(bytes), M68K_ASM_CPU_68020, m68k_diag_sink(NULL));
  M68K_C_ASSERT_U32(2U, (uint32_t)decoded.byte_count);
  M68K_C_ASSERT_U32(M68K_ASM_MNEMONIC_CPRESTORE, decoded.mnemonic_id);
  M68K_C_ASSERT_U32(1U, decoded.has_coprocessor_id);
  M68K_C_ASSERT_U32(5U, decoded.coprocessor_id);
  m68k_render_policy_init_default(&policy);
  rendered = m68k_ir_render_one_with_policy(&decoded, &policy, m68k_diag_sink(NULL));
  M68K_C_ASSERT_STR("cprestore (a4)", rendered.text);
  encoded = m68k_ir_encode_one(&decoded, out_bytes, sizeof(out_bytes), m68k_diag_sink(NULL));
  M68K_C_ASSERT_U32(2U, (uint32_t)encoded.byte_count);
  M68K_C_ASSERT(memcmp(out_bytes, bytes, sizeof(bytes)) == 0);
  return 0;
}

static int test_analysis_defaults_and_inits(void) {
  M68kAnalysisPolicy policy;
  M68kAnalysisFindings findings;
  M68kInstructionIR instruction;
  M68kSymbolRefIR symbol_ref;
  memset(&policy, 0xA5, sizeof(policy));
  memset(&findings, 0xA5, sizeof(findings));
  memset(&instruction, 0xA5, sizeof(instruction));
  memset(&symbol_ref, 0xA5, sizeof(symbol_ref));
  m68k_analysis_policy_init_default(&policy);
  m68k_analysis_findings_init(&findings);
  m68k_ir_instruction_init(&instruction);
  m68k_ir_symbol_ref_init(&symbol_ref);
  M68K_C_ASSERT_INT(M68K_ASM_CPU_68060, policy.max_cpu);
  M68K_C_ASSERT_INT(M68K_ASM_CPU_68000, findings.required_cpu);
  M68K_C_ASSERT_INT(0, findings.cpu_violation_count);
  M68K_C_ASSERT_U32(M68K_ASM_FORM_NONE, instruction.asm_form_index);
  M68K_C_ASSERT_INT(0, symbol_ref.kind);
  M68K_C_ASSERT_INT(0, symbol_ref.has_name);
  return 0;
}

static int test_instruction_mnemonic_helpers_use_id(void) {
  M68kInstructionIR instruction;
  memset(&instruction, 0, sizeof(instruction));
  m68k_ir_instruction_init(&instruction);
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_NONE, instruction.mnemonic_id);
  M68K_C_ASSERT_STR("", m68k_ir_instruction_mnemonic_name(&instruction));
  instruction.mnemonic_id = M68K_ASM_MNEMONIC_NOP;
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_NOP, instruction.mnemonic_id);
  M68K_C_ASSERT_STR("nop", m68k_ir_instruction_mnemonic_name(&instruction));

  instruction.asm_form_index = 0U;
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_NOP, instruction.mnemonic_id);
  M68K_C_ASSERT_STR("nop", m68k_ir_instruction_mnemonic_name(&instruction));
  return 0;
}

static int test_section_append_statement_copies_data(void) {
  M68kSectionIR section;
  M68kStatementIR statement;
  uint8_t bytes[2] = {0x12u, 0x34u};

  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));
  m68k_ir_statement_init(&statement);
  statement.kind = M68K_STATEMENT_DATA;
  statement.label_name = "lbl";
  statement.comment = "comment";
  statement.u.data.kind = M68K_DATA_ITEM_BYTES;
  statement.u.data.data = bytes;
  statement.u.data.size = sizeof(bytes);
  statement.u.data.expr_text = "expr";

  M68K_C_ASSERT_INT(0, m68k_ir_section_append_statement(&section, &statement));
  M68K_C_ASSERT_INT(1, (int)section.statement_count);
  M68K_C_ASSERT(section.statements[0].label_name != statement.label_name);
  M68K_C_ASSERT(section.statements[0].comment != statement.comment);
  M68K_C_ASSERT(section.statements[0].u.data.data != statement.u.data.data);
  M68K_C_ASSERT(section.statements[0].u.data.expr_text != statement.u.data.expr_text);
  M68K_C_ASSERT_STR("lbl", section.statements[0].label_name);
  M68K_C_ASSERT_STR("comment", section.statements[0].comment);
  M68K_C_ASSERT_STR("expr", section.statements[0].u.data.expr_text);
  M68K_C_ASSERT_U32(0x12u, section.statements[0].u.data.data[0]);
  M68K_C_ASSERT_U32(0x34u, section.statements[0].u.data.data[1]);

  m68k_ir_section_destroy(&section);
  return 0;
}

static int test_section_analysis_label_dedupes(void) {
  M68kSectionAnalysisIR analysis;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_create(&analysis));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_add_label(&analysis, 0x20u));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_add_label(&analysis, 0x20u));
  M68K_C_ASSERT_INT(1, (int)analysis.label_count);
  M68K_C_ASSERT_U32(0x20u, analysis.label_offsets[0]);
  m68k_ir_section_analysis_destroy(&analysis);
  return 0;
}

static int test_source_model_symbol_index_preserves_lookup_semantics(void) {
  AsmSourceFile source;
  size_t index;
  M68kSourceModelIndexResult found;
  memset(&source, 0, sizeof(source));
  for (index = 0U; index < 80U; ++index) {
    char name[32];
    M68kSourceModelIndexResult added;
    snprintf(name, sizeof(name), "Label_%02u", (unsigned)index);
    added = m68k_source_model_ensure_symbol(&source, name, ASM_SOURCE_SYMBOL_LABEL);
    M68K_C_ASSERT(added.ok);
    M68K_C_ASSERT_INT((int)index, (int)added.index);
  }
  M68K_C_ASSERT(source.symbol_index_slots != NULL);
  found = m68k_source_model_find_symbol_index(&source, "Label_42");
  M68K_C_ASSERT(found.ok);
  M68K_C_ASSERT_INT(42, (int)found.index);
  found = m68k_source_model_find_symbol_index(&source, "label_42");
  M68K_C_ASSERT(found.ok);
  M68K_C_ASSERT_INT(42, (int)found.index);
  M68K_C_ASSERT(m68k_source_model_ensure_symbol(&source, "CaseDup", ASM_SOURCE_SYMBOL_LABEL).ok);
  M68K_C_ASSERT(m68k_source_model_ensure_symbol(&source, "casedup", ASM_SOURCE_SYMBOL_LABEL).ok);
  found = m68k_source_model_find_symbol_index(&source, "CaseDup");
  M68K_C_ASSERT(found.ok);
  found = m68k_source_model_find_symbol_index(&source, "CASEDUP");
  M68K_C_ASSERT(!found.ok);
  m68k_source_model_free(&source);
  return 0;
}

static int test_source_analysis_append_section_copies_recovered_dispatches(void) {
  M68kSectionAnalysisIR section;
  M68kSourceAnalysisIR source;
  M68kRecoveredWordDispatchIR word_dispatch;
  M68kRecoveredInlineDispatchIR inline_dispatch;
  int16_t word_entries[2] = {0x0010, 0x0000};
  uint32_t word_targets[2] = {0x120u, 0x000u};
  uint8_t word_valid[2] = {1u, 0u};
  uint32_t inline_entries[2] = {0x200u, 0x202u};
  uint32_t inline_targets[2] = {0x300u, 0x320u};

  memset(&word_dispatch, 0, sizeof(word_dispatch));
  memset(&inline_dispatch, 0, sizeof(inline_dispatch));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_create(&section));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_create(&source));

  word_dispatch.pattern = 1u;
  word_dispatch.table_base = 0x100u;
  word_dispatch.base_target = 0x110u;
  word_dispatch.scanned_bytes = 4u;
  word_dispatch.slot_count = 2u;
  word_dispatch.entry_words = word_entries;
  word_dispatch.targets = word_targets;
  word_dispatch.target_valid = word_valid;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_word_dispatch(&section, &word_dispatch));

  inline_dispatch.table_base = 0x200u;
  inline_dispatch.scanned_bytes = 4u;
  inline_dispatch.entry_count = 2u;
  inline_dispatch.entry_offsets = inline_entries;
  inline_dispatch.targets = inline_targets;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_inline_dispatch(&section, &inline_dispatch));

  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_append_section(&source, &section));
  M68K_C_ASSERT_INT(1, (int)source.section_count);
  M68K_C_ASSERT_INT(1, (int)source.sections[0].recovered_word_dispatch_count);
  M68K_C_ASSERT_INT(1, (int)source.sections[0].recovered_inline_dispatch_count);
  M68K_C_ASSERT(source.sections[0].recovered_word_dispatches[0].entry_words != word_entries);
  M68K_C_ASSERT(source.sections[0].recovered_inline_dispatches[0].entry_offsets != inline_entries);
  M68K_C_ASSERT_U32(0x120u, source.sections[0].recovered_word_dispatches[0].targets[0]);
  M68K_C_ASSERT_U32(0x320u, source.sections[0].recovered_inline_dispatches[0].targets[1]);

  m68k_ir_source_analysis_destroy(&source);
  m68k_ir_section_analysis_destroy(&section);
  return 0;
}

static int test_source_analysis_append_section_rehydrates_platform_name_refs(void) {
  M68kSectionAnalysisIR section;
  M68kSourceAnalysisIR source;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_create(&section));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_create(&source));

  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_platform_base_slot(&section,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, -30, "DOSBase"));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_platform_effect(&section,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x40u, M68K_PLATFORM_EFFECT_SET_TYPED_REG, 1U, 0U, 0, 0,
    NULL, NULL, "IO", NULL, NULL, 0U, 0));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_local_call_summary(&section,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x80u, M68K_PLATFORM_EFFECT_SET_TYPED_REG, 1U, 0U, 1U, 0U,
    0U, 0, "DOSBase", "_LVOOpen", "IO", NULL, NULL, 0U, 0));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_platform_call(&section,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0xA0u, 1U, "_LVOOpen", M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL,
    "DOSBase", NULL, 0U, 0, 0, 0U, 0U, 0U, "1.3", "36"));

  section.recovered_platform_base_slots[0].base_name = "DOSBase";
  section.recovered_platform_effects[0].payload.typed.type_name = "IO";
  section.recovered_local_call_summaries[0].payload.typed.context_name = "DOSBase";
  section.recovered_local_call_summaries[0].payload.typed.symbol_name = "_LVOOpen";
  section.recovered_local_call_summaries[0].payload.typed.type_name = "IO";
  section.recovered_platform_calls[0].symbol_name = "_LVOOpen";
  section.recovered_platform_calls[0].note_base_name = "DOSBase";
  memset(&section.recovered_platform_base_slots[0].base_ref, 0, sizeof(section.recovered_platform_base_slots[0].base_ref));
  memset(&section.recovered_platform_effects[0].payload.typed.type_ref, 0,
    sizeof(section.recovered_platform_effects[0].payload.typed.type_ref));
  memset(&section.recovered_platform_effects[0].payload.typed.semantic_kind_ref, 0,
    sizeof(section.recovered_platform_effects[0].payload.typed.semantic_kind_ref));
  memset(&section.recovered_platform_effects[0].payload.typed.value_domain_ref, 0,
    sizeof(section.recovered_platform_effects[0].payload.typed.value_domain_ref));
  memset(&section.recovered_local_call_summaries[0].payload.typed.type_ref, 0,
    sizeof(section.recovered_local_call_summaries[0].payload.typed.type_ref));
  memset(&section.recovered_local_call_summaries[0].payload.typed.context_ref, 0,
    sizeof(section.recovered_local_call_summaries[0].payload.typed.context_ref));
  memset(&section.recovered_local_call_summaries[0].payload.typed.symbol_ref, 0,
    sizeof(section.recovered_local_call_summaries[0].payload.typed.symbol_ref));
  memset(&section.recovered_local_call_summaries[0].payload.typed.semantic_kind_ref, 0,
    sizeof(section.recovered_local_call_summaries[0].payload.typed.semantic_kind_ref));
  memset(&section.recovered_local_call_summaries[0].payload.typed.value_domain_ref, 0,
    sizeof(section.recovered_local_call_summaries[0].payload.typed.value_domain_ref));
  memset(&section.recovered_platform_calls[0].symbol_ref, 0, sizeof(section.recovered_platform_calls[0].symbol_ref));
  memset(&section.recovered_platform_calls[0].note_base_ref, 0, sizeof(section.recovered_platform_calls[0].note_base_ref));
  memset(&section.recovered_platform_calls[0].note_symbol_ref, 0, sizeof(section.recovered_platform_calls[0].note_symbol_ref));

  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_append_section(&source, &section));
  M68K_C_ASSERT_INT(1, (int)source.section_count);
  M68K_C_ASSERT_INT(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
    source.sections[0].recovered_platform_base_slots[0].base_ref.platform_kind);
  M68K_C_ASSERT(source.sections[0].recovered_platform_base_slots[0].base_ref.id != 0U);
  M68K_C_ASSERT_INT(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
    source.sections[0].recovered_platform_effects[0].payload.typed.type_ref.platform_kind);
  M68K_C_ASSERT(source.sections[0].recovered_platform_effects[0].payload.typed.type_ref.id != 0U);
  M68K_C_ASSERT_INT(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
    source.sections[0].recovered_local_call_summaries[0].payload.typed.type_ref.platform_kind);
  M68K_C_ASSERT(source.sections[0].recovered_local_call_summaries[0].payload.typed.type_ref.id != 0U);
  M68K_C_ASSERT_INT(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
    source.sections[0].recovered_local_call_summaries[0].payload.typed.context_ref.platform_kind);
  M68K_C_ASSERT(source.sections[0].recovered_local_call_summaries[0].payload.typed.context_ref.id != 0U);
  M68K_C_ASSERT_INT(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
    source.sections[0].recovered_local_call_summaries[0].payload.typed.symbol_ref.platform_kind);
  M68K_C_ASSERT(source.sections[0].recovered_local_call_summaries[0].payload.typed.symbol_ref.id != 0U);
  M68K_C_ASSERT_INT(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
    source.sections[0].recovered_platform_calls[0].symbol_ref.platform_kind);
  M68K_C_ASSERT(source.sections[0].recovered_platform_calls[0].symbol_ref.id != 0U);
  M68K_C_ASSERT_INT(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
    source.sections[0].recovered_platform_calls[0].note_base_ref.platform_kind);
  M68K_C_ASSERT(source.sections[0].recovered_platform_calls[0].note_base_ref.id != 0U);

  m68k_ir_source_analysis_destroy(&source);
  m68k_ir_section_analysis_destroy(&section);
  return 0;
}

static int test_source_analysis_append_section_copies_ref_only_platform_names(void) {
  M68kSectionAnalysisIR section;
  M68kSourceAnalysisIR source;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_create(&section));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_create(&source));

  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_platform_base_slot(&section,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, -30, "DOSBase"));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_platform_effect(&section,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x40u, M68K_PLATFORM_EFFECT_SET_TYPED_REG, 1U, 0U, 0, 0,
    NULL, NULL, "IO", NULL, NULL, 0U, 0));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_local_call_summary(&section,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x80u, M68K_PLATFORM_EFFECT_SET_TYPED_REG, 1U, 0U, 1U, 0U,
    0U, 0, "DOSBase", "_LVOOpen", "IO", NULL, NULL, 0U, 0));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_platform_call(&section,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0xA0u, 1U, "_LVOOpen", M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL,
    "DOSBase", NULL, 0U, 0, 0, 0U, 0U, 0U, "1.3", "36"));

  M68K_C_ASSERT(section.recovered_platform_base_slots[0].base_name == NULL);
  M68K_C_ASSERT(section.recovered_platform_effects[0].payload.typed.type_name == NULL);
  M68K_C_ASSERT(section.recovered_local_call_summaries[0].payload.typed.context_name == NULL);
  M68K_C_ASSERT(section.recovered_local_call_summaries[0].payload.typed.symbol_name == NULL);
  M68K_C_ASSERT(section.recovered_local_call_summaries[0].payload.typed.type_name == NULL);
  M68K_C_ASSERT(section.recovered_platform_calls[0].symbol_name == NULL);
  M68K_C_ASSERT(section.recovered_platform_calls[0].note_base_name == NULL);
  M68K_C_ASSERT_STR("DOSBase",
    m68k_platform_name_ref_resolve_text_or_fallback(&section.recovered_platform_base_slots[0].base_ref,
      section.recovered_platform_base_slots[0].base_name));
  M68K_C_ASSERT_STR("IO",
    m68k_platform_name_ref_resolve_text_or_fallback(&section.recovered_platform_effects[0].payload.typed.type_ref,
      section.recovered_platform_effects[0].payload.typed.type_name));
  M68K_C_ASSERT_STR("DOSBase",
    m68k_platform_name_ref_resolve_text_or_fallback(&section.recovered_local_call_summaries[0].payload.typed.context_ref,
      section.recovered_local_call_summaries[0].payload.typed.context_name));
  M68K_C_ASSERT_STR("_LVOOpen",
    m68k_platform_name_ref_resolve_text_or_fallback(&section.recovered_local_call_summaries[0].payload.typed.symbol_ref,
      section.recovered_local_call_summaries[0].payload.typed.symbol_name));
  M68K_C_ASSERT_STR("_LVOOpen",
    m68k_platform_name_ref_resolve_text_or_fallback(&section.recovered_platform_calls[0].symbol_ref,
      section.recovered_platform_calls[0].symbol_name));

  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_append_section(&source, &section));
  M68K_C_ASSERT(source.sections[0].recovered_platform_base_slots[0].base_name == NULL);
  M68K_C_ASSERT(source.sections[0].recovered_platform_effects[0].payload.typed.type_name == NULL);
  M68K_C_ASSERT(source.sections[0].recovered_local_call_summaries[0].payload.typed.context_name == NULL);
  M68K_C_ASSERT(source.sections[0].recovered_local_call_summaries[0].payload.typed.symbol_name == NULL);
  M68K_C_ASSERT(source.sections[0].recovered_local_call_summaries[0].payload.typed.type_name == NULL);
  M68K_C_ASSERT(source.sections[0].recovered_platform_calls[0].symbol_name == NULL);
  M68K_C_ASSERT(source.sections[0].recovered_platform_calls[0].note_base_name == NULL);
  M68K_C_ASSERT_STR("DOSBase",
    m68k_platform_name_ref_resolve_text_or_fallback(&source.sections[0].recovered_platform_base_slots[0].base_ref,
      source.sections[0].recovered_platform_base_slots[0].base_name));
  M68K_C_ASSERT_STR("IO",
    m68k_platform_name_ref_resolve_text_or_fallback(&source.sections[0].recovered_platform_effects[0].payload.typed.type_ref,
      source.sections[0].recovered_platform_effects[0].payload.typed.type_name));
  M68K_C_ASSERT_STR("DOSBase",
    m68k_platform_name_ref_resolve_text_or_fallback(&source.sections[0].recovered_local_call_summaries[0].payload.typed.context_ref,
      source.sections[0].recovered_local_call_summaries[0].payload.typed.context_name));
  M68K_C_ASSERT_STR("_LVOOpen",
    m68k_platform_name_ref_resolve_text_or_fallback(&source.sections[0].recovered_local_call_summaries[0].payload.typed.symbol_ref,
      source.sections[0].recovered_local_call_summaries[0].payload.typed.symbol_name));
  M68K_C_ASSERT_STR("_LVOOpen",
    m68k_platform_name_ref_resolve_text_or_fallback(&source.sections[0].recovered_platform_calls[0].symbol_ref,
      source.sections[0].recovered_platform_calls[0].symbol_name));
  M68K_C_ASSERT_STR("DOSBase",
    m68k_platform_name_ref_resolve_text_or_fallback(&source.sections[0].recovered_platform_calls[0].note_base_ref,
      source.sections[0].recovered_platform_calls[0].note_base_name));

  m68k_ir_source_analysis_destroy(&source);
  m68k_ir_section_analysis_destroy(&section);
  return 0;
}

static int test_section_analysis_records_typed_global_slot_effects(void) {
  M68kSectionAnalysisIR section;
  M68kSourceAnalysisIR source;
  const M68kRecoveredPlatformEffectIR *effect;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_create(&section));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_create(&source));

  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_platform_typed_global_slot_effect(&section,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x20u, 1U, 0x100u, "TimerBase", "LIB", "library_base", NULL));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_platform_typed_global_slot_effect(&section,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x20u, 1U, 0x100u, "TimerBase", "LIB", "library_base", NULL));
  M68K_C_ASSERT_INT(-1, m68k_ir_section_analysis_append_recovered_platform_typed_global_slot_effect(&section,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x20u, 1U, 0x100u, "TimerBase", "DD", "library_base", NULL));
  M68K_C_ASSERT_INT(1, (int)section.recovered_platform_effect_count);
  effect = &section.recovered_platform_effects[0];
  M68K_C_ASSERT_INT(M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT, effect->kind);
  M68K_C_ASSERT_U32(1U, (uint32_t)effect->target_section_index);
  M68K_C_ASSERT_U32(0x100u, effect->target_offset);
  M68K_C_ASSERT_STR("TimerBase",
    m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.symbol_ref,
      effect->payload.typed.symbol_name));
  M68K_C_ASSERT_STR("LIB",
    m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.type_ref,
      effect->payload.typed.type_name));

  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_append_section(&source, &section));
  effect = &source.sections[0].recovered_platform_effects[0];
  M68K_C_ASSERT_INT(M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT, effect->kind);
  M68K_C_ASSERT_U32(1U, (uint32_t)effect->target_section_index);
  M68K_C_ASSERT_U32(0x100u, effect->target_offset);
  M68K_C_ASSERT_STR("LIB",
    m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.type_ref,
      effect->payload.typed.type_name));

  m68k_ir_source_analysis_destroy(&source);
  m68k_ir_section_analysis_destroy(&section);
  return 0;
}

static int test_section_many_interleaved_labels_and_data(void) {
  M68kSectionIR section;
  size_t index;
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));

  for (index = 0; index < 70000; ++index) {
    M68kStatementIR label_stmt;
    M68kStatementIR data_stmt;
    char label_name[32];
    uint8_t byte = (uint8_t)(index & 0xFFu);

    m68k_ir_statement_init(&label_stmt);
    label_stmt.kind = M68K_STATEMENT_LABEL;
    snprintf(label_name, sizeof(label_name), "dat_%04X", (unsigned)index);
    label_stmt.label_name = label_name;
    M68K_C_ASSERT_INT(0, m68k_ir_section_append_statement(&section, &label_stmt));

    m68k_ir_statement_init(&data_stmt);
    data_stmt.kind = M68K_STATEMENT_DATA;
    data_stmt.u.data.kind = M68K_DATA_ITEM_BYTES;
    data_stmt.u.data.data = &byte;
    data_stmt.u.data.size = 1U;
    M68K_C_ASSERT_INT(0, m68k_ir_section_append_statement(&section, &data_stmt));
  }

  M68K_C_ASSERT_INT(140000, (int)section.statement_count);
  m68k_ir_section_destroy(&section);
  return 0;
}

static int test_section_many_interleaved_labels_and_expr_data(void) {
  M68kSectionIR section;
  size_t index;
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));

  for (index = 0; index < 70000; ++index) {
    M68kStatementIR label_stmt;
    M68kStatementIR data_stmt;
    char label_name[32];
    uint8_t word_bytes[2];
    char expr[48];

    m68k_ir_statement_init(&label_stmt);
    label_stmt.kind = M68K_STATEMENT_LABEL;
    snprintf(label_name, sizeof(label_name), "dat_%04X", (unsigned)index);
    label_stmt.label_name = label_name;
    M68K_C_ASSERT_INT(0, m68k_ir_section_append_statement(&section, &label_stmt));

    word_bytes[0] = (uint8_t)((index >> 8) & 0xFFu);
    word_bytes[1] = (uint8_t)(index & 0xFFu);
    snprintf(expr, sizeof(expr), "loc_%04X-dat_%04X", (unsigned)(index + 2U), (unsigned)index);

    m68k_ir_statement_init(&data_stmt);
    data_stmt.kind = M68K_STATEMENT_DATA;
    data_stmt.u.data.kind = M68K_DATA_ITEM_WORDS;
    data_stmt.u.data.data = word_bytes;
    data_stmt.u.data.size = 2U;
    data_stmt.u.data.expr_text = expr;
    M68K_C_ASSERT_INT(0, m68k_ir_section_append_statement(&section, &data_stmt));
  }

  M68K_C_ASSERT_INT(140000, (int)section.statement_count);
  m68k_ir_section_destroy(&section);
  return 0;
}

static int test_arena_mark_rewind_reuses_same_block_range(void) {
  Arena *arena = arena_create(64U);
  char *first;
  ArenaMark mark;
  char *second;
  char *third;
  M68K_C_ASSERT(arena != NULL);
  first = (char *)arena_alloc(arena, 16U);
  M68K_C_ASSERT(first != NULL);
  mark = arena_mark(arena);
  second = (char *)arena_alloc(arena, 24U);
  M68K_C_ASSERT(second != NULL);
  memset(second, 0x11, 24U);
  arena_rewind(arena, mark);
#if defined(_DEBUG)
  {
    size_t index;
    for (index = 0; index < 24U; ++index) M68K_C_ASSERT_U32(0xDDu, (unsigned char)second[index]);
  }
#endif
  third = (char *)arena_alloc(arena, 24U);
  M68K_C_ASSERT(third != NULL);
  M68K_C_ASSERT(second == third);
  arena_destroy(arena);
  return 0;
}

static int test_arena_rewind_discards_later_blocks(void) {
  Arena *arena = arena_create(64U);
  char *first;
  ArenaMark mark;
  char *large;
  char *again;
  M68K_C_ASSERT(arena != NULL);
  first = (char *)arena_alloc(arena, 32U);
  M68K_C_ASSERT(first != NULL);
  mark = arena_mark(arena);
  large = (char *)arena_alloc(arena, 5000U);
  M68K_C_ASSERT(large != NULL);
  arena_rewind(arena, mark);
  again = (char *)arena_alloc(arena, 32U);
  M68K_C_ASSERT(again != NULL);
  M68K_C_ASSERT(again == first + 32);
  arena_destroy(arena);
  return 0;
}

static int test_arena_reset_poisons_head_block_range(void) {
  Arena *arena = arena_create(64U);
  char *data;
  size_t index;
  M68K_C_ASSERT(arena != NULL);
  data = (char *)arena_alloc(arena, 32U);
  M68K_C_ASSERT(data != NULL);
  memset(data, 0x22, 32U);
  arena_reset(arena);
#if defined(_DEBUG)
  for (index = 0; index < 32U; ++index) M68K_C_ASSERT_U32(0xDDu, (unsigned char)data[index]);
#else
  (void)index;
#endif
  arena_destroy(arena);
  return 0;
}

static int test_arena_rejects_overflow_allocations(void) {
  Arena *arena = arena_create(64U);
  M68K_C_ASSERT(arena != NULL);
  M68K_C_ASSERT(arena_calloc(arena, (((size_t)-1) / 2U) + 1U, 2U) == NULL);
  M68K_C_ASSERT(arena_strndup(arena, "x", (size_t)-1) == NULL);
  arena_destroy(arena);
  return 0;
}

static int test_decode_ir_decodes_aligned_candidates(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kDecodeIR decode;
  uint8_t bytes[4] = {0x4eu, 0x71u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_decode_ir_init(&decode);
  M68K_C_ASSERT_INT(0, m68k_decode_ir_build_object(&decode, &object, M68K_ASM_CPU_68060, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(1, (int)decode.section_count);
  M68K_C_ASSERT_U32(2U, decode.decoded_candidate_count);
  M68K_C_ASSERT_U32(0U, decode.sections[0].candidates[0].offset);
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_NOP, decode.sections[0].candidates[0].mnemonic_id);
  M68K_C_ASSERT_U32(2U, decode.sections[0].candidates[1].offset);
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_RTS, decode.sections[0].candidates[1].mnemonic_id);
  m68k_decode_ir_destroy(&decode);
  m68k_object_destroy(&object);
  return 0;
}

static int test_decode_ir_treats_cpu_policy_as_ceiling(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kDecodeIR decode;
  const M68kDecodeCandidate *candidate;
  uint8_t bytes[4] = {0xf0u, 0x12u, 0x9eu, 0x15u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_decode_ir_init(&decode);
  M68K_C_ASSERT_INT(0, m68k_decode_ir_build_object(&decode, &object, M68K_ASM_CPU_68060, m68k_diag_sink(NULL)));
  candidate = m68k_decode_ir_find_candidate_at_offset(&decode.sections[0], 0U);
  M68K_C_ASSERT(candidate != NULL);
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_PTESTR, candidate->mnemonic_id);
  M68K_C_ASSERT_INT(M68K_ASM_CPU_68030, candidate->target_cpu);
  m68k_decode_ir_destroy(&decode);
  m68k_object_destroy(&object);
  return 0;
}

static int test_generated_cpu_vector_metadata_marks_interrupt_autovectors(void) {
  M68K_C_ASSERT(m68k_cpu_exception_vector_address_has_kind(0x0068U, M68K_CPU_VECTOR_KIND_INTERRUPT));
  M68K_C_ASSERT(!m68k_cpu_exception_vector_address_has_kind(0x0090U, M68K_CPU_VECTOR_KIND_INTERRUPT));
  return 0;
}

static int test_generated_call_ea_metadata_marks_control_target(void) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  uint8_t bytes[4] = {0x4eu, 0xaeu, 0xfeu, 0xf2u};
  instruction = m68k_ir_decode_one(bytes, sizeof(bytes), M68K_ASM_CPU_68000, m68k_diag_sink(NULL));
  M68K_C_ASSERT_U32(4U, instruction.byte_count);
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  M68K_C_ASSERT(metadata != NULL);
  M68K_C_ASSERT_U32(M68K_SIM_FLOW_CALL, metadata->flow_kind);
  M68K_C_ASSERT_U32(M68K_SIM_ACCESS_BRANCH_TARGET, metadata->operand_access_kinds[0]);
  M68K_C_ASSERT_U32(M68K_SIM_RESULT_CONTROL_TARGET, metadata->operand_result_kinds[0]);
  M68K_C_ASSERT_U32(M68K_SIM_EA_FORMULA_DECODED_EA, metadata->operand_ea_address_formulas[0]);
  return 0;
}

static int test_source_parse_treats_cpu_policy_as_ceiling(void) {
  AsmSourceFile source;
  M68kDiagList diagnostics;
  const char *source_text =
    "SECTION section_0,code\n"
    "\tmovec cacr,d0\n";
  memset(&source, 0, sizeof(source));
  m68k_diag_list_reset(&diagnostics);
  source.target_cpu = M68K_ASM_CPU_68060;
  M68K_C_ASSERT(m68k_source_pipeline_parse_text_and_layout(&source, source_text,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_U32(2U, source.statement_count);
  M68K_C_ASSERT_INT(ASM_SOURCE_STMT_INSTRUCTION, source.statements[1].kind);
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_MOVEC, source.statements[1].u.instruction.parsed_ir.mnemonic_id);
  M68K_C_ASSERT_INT(M68K_ASM_CPU_68020, source.statements[1].u.instruction.parsed_ir.target_cpu);
  m68k_source_model_free(&source);
  return 0;
}

static int test_source_fpu_directive_encodes_external_coprocessor_id(void) {
  AsmSourceFile source;
  M68kObject object;
  M68kDiagList diagnostics;
  const char *source_text =
    "SECTION section_0,code\n"
    "\tFPU 5\n"
    "\tfrestore (a4)\n"
    "\tFPU 1\n"
    "\tfsave (a6)\n";
  memset(&source, 0, sizeof(source));
  memset(&object, 0, sizeof(object));
  m68k_diag_list_reset(&diagnostics);
  source.target_cpu = M68K_ASM_CPU_68020;
  M68K_C_ASSERT(m68k_source_pipeline_parse_text_and_layout(&source, source_text,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_INT(1, m68k_source_pipeline_emit_object(&source, &object, m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_U32(1U, (uint32_t)object.section_count);
  M68K_C_ASSERT_U32(4U, object.sections[0].data_size);
  M68K_C_ASSERT_U32(0xFBU, object.sections[0].data[0]);
  M68K_C_ASSERT_U32(0x54U, object.sections[0].data[1]);
  M68K_C_ASSERT_U32(0xF3U, object.sections[0].data[2]);
  M68K_C_ASSERT_U32(0x16U, object.sections[0].data[3]);
  m68k_object_destroy(&object);
  m68k_source_model_free(&source);
  return 0;
}

static int test_source_fpu_directive_uses_external_id_under_cpu_ceiling(void) {
  AsmSourceFile source;
  M68kObject object;
  M68kDiagList diagnostics;
  const char *source_text =
    "SECTION section_0,code\n"
    "\tFPU 5\n"
    "\tfrestore (a4)\n";
  memset(&source, 0, sizeof(source));
  memset(&object, 0, sizeof(object));
  m68k_diag_list_reset(&diagnostics);
  /* target_cpu is a ceiling here; the directive still encodes the external 68881/68882 cpID. */
  source.target_cpu = M68K_ASM_CPU_68040;
  M68K_C_ASSERT(m68k_source_pipeline_parse_text_and_layout(&source, source_text,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_INT(1, m68k_source_pipeline_emit_object(&source, &object, m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_U32(1U, (uint32_t)object.section_count);
  M68K_C_ASSERT_U32(2U, object.sections[0].data_size);
  M68K_C_ASSERT_U32(0xFBU, object.sections[0].data[0]);
  M68K_C_ASSERT_U32(0x54U, object.sections[0].data[1]);
  m68k_object_destroy(&object);
  m68k_source_model_free(&source);
  return 0;
}

static int test_source_fpu_zero_disables_fpu_alias_instruction(void) {
  AsmSourceFile source;
  M68kDiagList diagnostics;
  const char *source_text =
    "SECTION section_0,code\n"
    "\tFPU 0\n"
    "\tfrestore (a4)\n";
  memset(&source, 0, sizeof(source));
  m68k_diag_list_reset(&diagnostics);
  source.target_cpu = M68K_ASM_CPU_68040;
  M68K_C_ASSERT(!m68k_source_pipeline_parse_text_and_layout(&source, source_text,
    m68k_diag_sink(&diagnostics)));
  m68k_source_model_free(&source);
  return 0;
}

static int test_source_org_sets_logical_pc_without_padding(void) {
  AsmSourceFile source;
  M68kObject object;
  M68kDiagList diagnostics;
  M68kSourceModelIndexResult start_symbol;
  M68kSourceModelIndexResult target_symbol;
  const char *source_text =
    "SECTION section_0,code\n"
    "\tORG $400\n"
    "start:\n"
    "\tbra.b target\n"
    "\tnop\n"
    "target:\n"
    "\trts\n";
  memset(&source, 0, sizeof(source));
  memset(&object, 0, sizeof(object));
  m68k_diag_list_reset(&diagnostics);
  source.target_cpu = M68K_ASM_CPU_68000;
  M68K_C_ASSERT(m68k_source_pipeline_parse_text_and_layout(&source, source_text,
    m68k_diag_sink(&diagnostics)));
  start_symbol = m68k_source_model_find_symbol_index(&source, "start");
  target_symbol = m68k_source_model_find_symbol_index(&source, "target");
  M68K_C_ASSERT(start_symbol.ok);
  M68K_C_ASSERT(target_symbol.ok);
  M68K_C_ASSERT_U32(0x400U, source.symbols[start_symbol.index].value);
  M68K_C_ASSERT_U32(0x404U, source.symbols[target_symbol.index].value);
  M68K_C_ASSERT_INT(1, m68k_source_pipeline_emit_object(&source, &object, m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_U32(1U, (uint32_t)object.section_count);
  M68K_C_ASSERT_U32(6U, object.sections[0].data_size);
  M68K_C_ASSERT_U32(0x60U, object.sections[0].data[0]);
  M68K_C_ASSERT_U32(0x02U, object.sections[0].data[1]);
  M68K_C_ASSERT_U32(0x4EU, object.sections[0].data[2]);
  M68K_C_ASSERT_U32(0x71U, object.sections[0].data[3]);
  M68K_C_ASSERT_U32(0x4EU, object.sections[0].data[4]);
  M68K_C_ASSERT_U32(0x75U, object.sections[0].data[5]);
  m68k_object_destroy(&object);
  m68k_source_model_free(&source);
  return 0;
}

static int test_decode_ir_negative_cache_preserves_higher_cpu_decode(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kDecodeIR decode;
  const M68kDecodeCandidate *candidate = NULL;
  uint8_t bytes[4] = {0xf0u, 0x12u, 0x9eu, 0x15u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_decode_ir_init(&decode);
  M68K_C_ASSERT_INT(0, m68k_decode_ir_build_object_sections(&decode, &object, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(0, m68k_decode_ir_ensure_candidate_at(&decode, 0U, 0U, M68K_ASM_CPU_68000, &candidate,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(candidate == NULL);
  M68K_C_ASSERT(decode.sections[0].candidate_absent_cpu != NULL);
  M68K_C_ASSERT_U32((uint32_t)M68K_ASM_CPU_68000 + 1U, decode.sections[0].candidate_absent_cpu[0]);
  M68K_C_ASSERT_INT(0, m68k_decode_ir_ensure_candidate_at(&decode, 0U, 0U, M68K_ASM_CPU_68060, &candidate,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(candidate != NULL);
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_PTESTR, candidate->mnemonic_id);
  M68K_C_ASSERT_INT(M68K_ASM_CPU_68030, candidate->target_cpu);
  m68k_decode_ir_destroy(&decode);
  m68k_object_destroy(&object);
  return 0;
}

static int test_decode_ir_records_branch_target_candidate(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kDecodeIR decode;
  uint8_t bytes[6] = {0x60u, 0x02u, 0x4eu, 0x71u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_decode_ir_init(&decode);
  M68K_C_ASSERT_INT(0, m68k_decode_ir_build_object(&decode, &object, M68K_ASM_CPU_68060, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_BRA, decode.sections[0].candidates[0].mnemonic_id);
  M68K_C_ASSERT_INT(1, decode.sections[0].candidates[0].target_count);
  M68K_C_ASSERT_INT(M68K_DECODE_TARGET_BRANCH, decode.sections[0].candidates[0].targets[0].kind);
  M68K_C_ASSERT_INT(1, decode.sections[0].candidates[0].targets[0].has_operand);
  M68K_C_ASSERT_U32(0U, decode.sections[0].candidates[0].targets[0].operand_index);
  M68K_C_ASSERT_U32(4U, decode.sections[0].candidates[0].targets[0].offset);
  m68k_decode_ir_destroy(&decode);
  m68k_object_destroy(&object);
  return 0;
}

static int test_decode_ir_branch_word_target_uses_opcode_pc(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kDecodeIR decode;
  uint8_t bytes[8] = {0x60u, 0x00u, 0x00u, 0x02u, 0x4eu, 0x71u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_decode_ir_init(&decode);
  M68K_C_ASSERT_INT(0, m68k_decode_ir_build_object(&decode, &object, M68K_ASM_CPU_68060, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_BRA, decode.sections[0].candidates[0].mnemonic_id);
  M68K_C_ASSERT_U32(4U, decode.sections[0].candidates[0].byte_count);
  M68K_C_ASSERT_INT(1, decode.sections[0].candidates[0].target_count);
  M68K_C_ASSERT_INT(1, decode.sections[0].candidates[0].targets[0].has_operand);
  M68K_C_ASSERT_U32(0U, decode.sections[0].candidates[0].targets[0].operand_index);
  M68K_C_ASSERT_U32(4U, decode.sections[0].candidates[0].targets[0].offset);
  m68k_decode_ir_destroy(&decode);
  m68k_object_destroy(&object);
  return 0;
}

static int test_decode_ir_records_pc_relative_data_target_candidate(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kDecodeIR decode;
  uint8_t bytes[10] = {0x43u, 0xfau, 0x00u, 0x06u, 0x4eu, 0x75u, 0x00u, 0x00u, 0xdeu, 0xadu};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_decode_ir_init(&decode);
  M68K_C_ASSERT_INT(0, m68k_decode_ir_build_object(&decode, &object, M68K_ASM_CPU_68060, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_LEA, decode.sections[0].candidates[0].mnemonic_id);
  M68K_C_ASSERT_INT(1, decode.sections[0].candidates[0].target_count);
  M68K_C_ASSERT_INT(M68K_DECODE_TARGET_DATA, decode.sections[0].candidates[0].targets[0].kind);
  M68K_C_ASSERT_INT(1, decode.sections[0].candidates[0].targets[0].has_operand);
  M68K_C_ASSERT_U32(0U, decode.sections[0].candidates[0].targets[0].operand_index);
  M68K_C_ASSERT_U32(8U, decode.sections[0].candidates[0].targets[0].offset);
  m68k_decode_ir_destroy(&decode);
  m68k_object_destroy(&object);
  return 0;
}

static int test_decode_ir_records_pc_index_data_target_candidate(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kDecodeIR decode;
  uint8_t bytes[10] = {0xd0u, 0xfbu, 0x00u, 0x06u, 0x4eu, 0x75u, 0x00u, 0x00u, 0xdeu, 0xadu};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_decode_ir_init(&decode);
  M68K_C_ASSERT_INT(0, m68k_decode_ir_build_object(&decode, &object, M68K_ASM_CPU_68060, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(M68K_ASM_MNEMONIC_ADDA, decode.sections[0].candidates[0].mnemonic_id);
  M68K_C_ASSERT_INT(1, decode.sections[0].candidates[0].target_count);
  M68K_C_ASSERT_INT(M68K_DECODE_TARGET_DATA, decode.sections[0].candidates[0].targets[0].kind);
  M68K_C_ASSERT_INT(1, decode.sections[0].candidates[0].targets[0].has_operand);
  M68K_C_ASSERT_U32(0U, decode.sections[0].candidates[0].targets[0].operand_index);
  M68K_C_ASSERT_U32(8U, decode.sections[0].candidates[0].targets[0].offset);
  m68k_decode_ir_destroy(&decode);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_pc_index_data_target_auto_classifies_lookup_scalar(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  uint16_t index;
  uint8_t bytes[10] = {0xd0u, 0xfbu, 0x00u, 0x06u, 0x4eu, 0x75u, 0x00u, 0x00u, 0xdeu, 0xadu};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tadda.w loc_0_00000008(pc,d0.w),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000008:\n\tdc.w $DEAD\t; lookup_table\n") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && item->offset == 8U &&
        strcmp(item->semantic_role, "lookup_table") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(2U, auto_item->size);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_WORDS, auto_item->kind);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_pc_index_data_target_auto_classifies_lookup_span(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  uint16_t index;
  uint8_t bytes[16] = {
    0xd0u, 0xfbu, 0x00u, 0x06u,
    0x60u, 0x08u,
    0x4eu, 0x71u,
    0x00u, 0x00u, 0xdeu, 0xadu, 0x12u, 0x34u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tadda.w loc_0_00000008(pc,d0.w),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000008:\n\tdc.w $0000,$DEAD,$1234\t; lookup_table\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_0000000E:\n\trts\n") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && item->offset == 8U &&
        strcmp(item->semantic_role, "lookup_table") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(6U, auto_item->size);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_WORDS, auto_item->kind);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_indexed_postincrement_reads_auto_classify_word_table(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  uint16_t index;
  uint8_t bytes[20] = {
    0x41u, 0xfbu, 0x00u, 0x08u,
    0x32u, 0x18u,
    0x34u, 0x18u,
    0x60u, 0x08u,
    0x11u, 0x22u, 0x33u, 0x44u, 0x55u, 0x66u, 0x77u, 0x88u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l loc_0_0000000A(pc,d0.w),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "loc_0_0000000A:\n\tdc.w $1122,$3344,$5566,$7788\t; lookup_table\n") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && item->offset == 10U &&
        strcmp(item->semantic_role, "lookup_table") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(8U, auto_item->size);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_WORDS, auto_item->kind);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_genam_byte_postincrement_table_stays_byte_data(void) {
  AsmSourceFile parsed_source;
  M68kObject object;
  M68kDiagList diagnostics;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint16_t index;
  const char *source_text =
    "SECTION section_0,code\n"
    "start:\n"
    "\tmove.w d1,-(a7)\n"
    "\tlea.l table(pc,d1.w),a0\n"
    "\tmove.w (a7)+,d1\n"
    "\tmove.b (a0)+,(a3)+\n"
    "\tmove.b (a0)+,(a3)+\n"
    "\tmove.b (a0)+,(a3)+\n"
    "\tbra.s after\n"
    "table:\n"
    "\tdc.b $30,$31,$32,$33,$34,$35\n"
    "after:\n"
    "\trts\n";
  memset(&parsed_source, 0, sizeof(parsed_source));
  memset(&object, 0, sizeof(object));
  m68k_diag_list_reset(&diagnostics);
  parsed_source.target_cpu = M68K_ASM_CPU_68000;
  M68K_C_ASSERT(m68k_source_pipeline_parse_text_and_layout(&parsed_source, source_text,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_INT(1, m68k_source_pipeline_emit_object(&parsed_source, &object, m68k_diag_sink(&diagnostics)));
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l loc_0_00000010(pc,d1.w),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000010:\n\tdc.b $30,$31,$32,$33,$34,$35\n") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    M68K_C_ASSERT(strcmp(item->semantic_role, "lookup_table") != 0 ||
      item->kind == M68K_ANALYSIS_STRUCTURED_DATA_BYTES);
  }
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  m68k_source_model_free(&parsed_source);
  return 0;
}

static int test_facts_v2_indexed_local_base_auto_classifies_scalar_table(void) {
  AsmSourceFile parsed_source;
  M68kObject object;
  M68kDiagList diagnostics;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  uint16_t index;
  const char *source_text =
    "SECTION section_0,code\n"
    "start:\n"
    "\tlea.l table.l,a0\n"
    "\tlea.l base.l,a1\n"
    "\tadd.w d0,d0\n"
    "\tadda.w $0(a0,d0.w),a1\n"
    "\tbra.s after\n"
    "table:\n"
    "\tdc.w $0000,$0002,$0004\n"
    "after:\n"
    "\trts\n"
    "base:\n"
    "\trts\n"
    "next:\n"
    "\trts\n"
    "last:\n"
    "\trts\n";
  memset(&parsed_source, 0, sizeof(parsed_source));
  memset(&object, 0, sizeof(object));
  m68k_diag_list_reset(&diagnostics);
  parsed_source.target_cpu = M68K_ASM_CPU_68000;
  M68K_C_ASSERT(m68k_source_pipeline_parse_text_and_layout(&parsed_source, source_text,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_INT(1, m68k_source_pipeline_emit_object(&parsed_source, &object, m68k_diag_sink(&diagnostics)));
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tadda.w $0(a0,d0.w),a1\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "loc_0_00000014:\n\tdc.w $0000,$0002,$0004\t; lookup_table\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_0000001A:\n\trts\n") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && item->offset == 20U &&
        strcmp(item->semantic_role, "lookup_table") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(6U, auto_item->size);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_WORDS, auto_item->kind);
  M68K_C_ASSERT_U32(0U, auto_item->has_target);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  m68k_source_model_free(&parsed_source);
  return 0;
}

static int test_facts_v2_genam_indexed_word_read_stays_unclassified_data(void) {
  AsmSourceFile parsed_source;
  M68kObject object;
  M68kDiagList diagnostics;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint16_t index;
  const char *source_text =
    "SECTION section_0,code\n"
    "start:\n"
    "\tlea.l table.l,a0\n"
    "\tmove.w $0(a0,d0.w),d1\n"
    "\tbra.s after\n"
    "table:\n"
    "\tdc.w $0000,$0008,$0010\n"
    "after:\n"
    "\trts\n";
  memset(&parsed_source, 0, sizeof(parsed_source));
  memset(&object, 0, sizeof(object));
  m68k_diag_list_reset(&diagnostics);
  parsed_source.target_cpu = M68K_ASM_CPU_68000;
  M68K_C_ASSERT(m68k_source_pipeline_parse_text_and_layout(&parsed_source, source_text,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_INT(1, m68k_source_pipeline_emit_object(&parsed_source, &object, m68k_diag_sink(&diagnostics)));
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w $0(a0,d0.w),d1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "; lookup_table") == NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    M68K_C_ASSERT(strcmp(item->semantic_role, "lookup_table") != 0);
  }
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  m68k_source_model_free(&parsed_source);
  return 0;
}

static int test_facts_v2_indexed_local_base_auto_classifies_pointer_table(void) {
  AsmSourceFile parsed_source;
  M68kObject object;
  M68kDiagList diagnostics;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  uint16_t index;
  const char *source_text =
    "SECTION section_0,code\n"
    "start:\n"
    "\tbsr.s target0\n"
    "\tbsr.s target1\n"
    "\tlea.l table.l,a0\n"
    "\tmove.l $0(a0,d0.w),d1\n"
    "\trts\n"
    "target0:\n"
    "\trts\n"
    "target1:\n"
    "\trts\n"
    "table:\n"
    "\tdc.l $00000010,$00000012\n"
    "after:\n"
    "\trts\n";
  memset(&parsed_source, 0, sizeof(parsed_source));
  memset(&object, 0, sizeof(object));
  m68k_diag_list_reset(&diagnostics);
  parsed_source.target_cpu = M68K_ASM_CPU_68000;
  M68K_C_ASSERT(m68k_source_pipeline_parse_text_and_layout(&parsed_source, source_text,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_INT(1, m68k_source_pipeline_emit_object(&parsed_source, &object, m68k_diag_sink(&diagnostics)));
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l $0(a0,d0.w),d1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l loc_0_00000010\t; pointer_table\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l loc_0_00000012\n") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && strcmp(item->semantic_role, "pointer_table") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(8U, auto_item->size);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_LONGS, auto_item->kind);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  m68k_source_model_free(&parsed_source);
  return 0;
}

static int test_facts_v2_data_ascii_span_auto_classifies_ff_string(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  uint16_t index;
  uint8_t bytes[] = {
    0x12u, 0x13u,
    'P', 'R', 'E', 'S', 'S', ' ', 'F', 'I', 'R', 'E', 0xffu,
    0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "dc.b \"PRESS FIRE\",$FF") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && item->offset == 2U &&
        strcmp(item->semantic_role, "string") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(11U, auto_item->size);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_STRING, auto_item->kind);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING, auto_item->semantic_role_flags);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_data_ascii_span_respects_accepted_code_overlap(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[] = {
    0x70u, 0x41u,
    0x70u, 0x42u,
    0x70u, 0x43u,
    0x70u, 0x44u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\"pApBpCpD\"") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  M68K_C_ASSERT_U32(5U, profile.accepted_instructions);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_data_ascii_span_rejects_length_prefixed_text(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint16_t index;
  uint32_t string_items = 0U;
  uint8_t bytes[] = {
    10u, 'P', 'R', 'E', 'S', 'S', ' ', 'F', 'I', 'R', 'E', 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "dc.b \"PRESS FIRE\",$00") == NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && strcmp(item->semantic_role, "string") == 0)
      ++string_items;
  }
  M68K_C_ASSERT_U32(0U, string_items);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_data_ascii_span_rejects_printable_length_sequence(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint16_t index;
  uint32_t string_items = 0U;
  uint8_t bytes[] = {
    4u, 'F', 'O', 'U', 'R',
    33u, 'T', 'H', 'I', 'S', ' ', 'I', 'S', ' ', 'A', ' ', 'T', 'H', 'I', 'R', 'T', 'Y',
    ' ', 'T', 'W', 'O', ' ', 'B', 'Y', 'T', 'E', ' ', 'M', 'E', 'S', 'S', 'A', 'G', 'E',
    0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "dc.b \"FOUR!THIS IS A THIRTY TWO BYTE MESSAGE\",$00") == NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && strcmp(item->semantic_role, "string") == 0)
      ++string_items;
  }
  M68K_C_ASSERT_U32(0U, string_items);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_adjacent_short_ascii_spans_auto_classify_string_sequence(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint16_t index;
  uint32_t string_items = 0U;
  uint8_t bytes[] = {
    'M', 'I', 'S', 'S', 0xffu,
    'H', 'I', 'T', 'S', 0xffu,
    'R', 'U', 'N', 'S', 0xffu
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "dc.b \"MISS\",$FF") != NULL);
  M68K_C_ASSERT(strstr(source, "dc.b \"HITS\",$FF") != NULL);
  M68K_C_ASSERT(strstr(source, "dc.b \"RUNS\",$FF") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && strcmp(item->semantic_role, "string") == 0)
      ++string_items;
  }
  M68K_C_ASSERT_U32(3U, string_items);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_two_short_ascii_spans_remain_raw_data(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint16_t index;
  uint32_t string_items = 0U;
  uint8_t bytes[] = {
    'M', 'I', 'S', 'S', 0xffu,
    'H', 'I', 'T', 'S', 0xffu
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "dc.b \"MISS\",$FF") == NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && strcmp(item->semantic_role, "string") == 0)
      ++string_items;
  }
  M68K_C_ASSERT_U32(0U, string_items);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_label_bounded_ascii_span_auto_classifies_string(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  uint16_t index;
  uint8_t bytes[] = {
    0x60u, 0x0au,
    ' ', 'T', 'E', 'T', 'R', 'A', 'G', 'O', 'N', ' ',
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.named_label_count = 1U;
  policy.named_labels[0].has_section_index = 1U;
  policy.named_labels[0].section_index = 0U;
  policy.named_labels[0].offset = 2U;
  snprintf(policy.named_labels[0].name, sizeof(policy.named_labels[0].name), "title");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "dc.b \" TETRAGON \"\t; string\n") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && strcmp(item->semantic_role, "string") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(10U, auto_item->size);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_STRING, auto_item->kind);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_decode_ir_keeps_odd_branch_target_for_analysis(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kDecodeIR decode;
  uint8_t bytes[6] = {0x66u, 0x01u, 0x4eu, 0x71u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_decode_ir_init(&decode);
  M68K_C_ASSERT_INT(0, m68k_decode_ir_build_object(&decode, &object, M68K_ASM_CPU_68060, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(1, decode.sections[0].candidates[0].target_count);
  M68K_C_ASSERT_U32(3U, decode.sections[0].candidates[0].targets[0].offset);
  m68k_decode_ir_destroy(&decode);
  m68k_object_destroy(&object);
  return 0;
}

static int test_fact_ir_label_creation_dedupes(void) {
  M68kFactIR facts;
  m68k_fact_ir_init(&facts);
  M68K_C_ASSERT_INT(0, m68k_fact_ir_create_label(&facts, 0U, 4U, M68K_FACT_CONFIDENCE_REQUIRED));
  M68K_C_ASSERT_INT(0, m68k_fact_ir_create_label(&facts, 0U, 4U, M68K_FACT_CONFIDENCE_REQUIRED));
  M68K_C_ASSERT_INT(1, (int)facts.label_created_count);
  M68K_C_ASSERT(m68k_fact_ir_has_label(&facts, 0U, 4U));
  m68k_fact_ir_destroy(&facts);
  return 0;
}

static int test_facts_v2_profile_collects_decode_and_label_facts(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  uint8_t bytes[6] = {0x60u, 0x02u, 0x4eu, 0x71u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(2U, profile.decoded_candidates);
  M68K_C_ASSERT_U32(2U, profile.accepted_instructions);
  M68K_C_ASSERT_U32(2U, profile.code_start_facts);
  M68K_C_ASSERT_U32(1U, profile.code_start_section_entries);
  M68K_C_ASSERT_U32(1U, profile.code_start_control_targets);
  M68K_C_ASSERT_U32(0U, profile.code_start_fallthroughs);
  M68K_C_ASSERT_U32(1U, profile.data_spans);
  M68K_C_ASSERT_U32(2U, profile.labels_created);
  M68K_C_ASSERT_U32(1U, profile.labels_referenced);
  M68K_C_ASSERT_U32(0U, profile.unresolved_labels);
  M68K_C_ASSERT_U32(2U, profile.queue_iterations);
  M68K_C_ASSERT_U32(5U, profile.render_ir_statements);
  M68K_C_ASSERT_U32(2U, profile.render_ir_labels);
  M68K_C_ASSERT_U32(2U, profile.render_ir_instructions);
  M68K_C_ASSERT_U32(1U, profile.render_ir_data_spans);
  M68K_C_ASSERT(profile.render_ir_hash != 0U);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_implicit_entry_only_first_code_section(void) {
  M68kObject object;
  M68kSection first_section;
  M68kSection second_section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  uint8_t first_bytes[2] = {0x4eu, 0x75u};
  uint8_t second_bytes[2] = {0x4eu, 0x75u};
  memset(&first_section, 0, sizeof(first_section));
  memset(&second_section, 0, sizeof(second_section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  first_section.kind = M68K_SECTION_CODE;
  first_section.size = sizeof(first_bytes);
  first_section.data_size = sizeof(first_bytes);
  first_section.data = first_bytes;
  second_section.kind = M68K_SECTION_CODE;
  second_section.size = sizeof(second_bytes);
  second_section.data_size = sizeof(second_bytes);
  second_section.data = second_bytes;
  added = m68k_object_add_section(&object, &first_section);
  M68K_C_ASSERT(added.ok);
  added = m68k_object_add_section(&object, &second_section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(1U, profile.code_start_section_entries);
  M68K_C_ASSERT_U32(1U, profile.accepted_instructions);
  M68K_C_ASSERT_U32(1U, profile.render_ir_instructions);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_implicit_entry_does_not_scan_to_later_code_section(void) {
  M68kObject object;
  M68kSection data_section;
  M68kSection code_section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  uint8_t data_bytes[2] = {0x00u, 0x00u};
  uint8_t code_bytes[2] = {0x4eu, 0x75u};
  /* AmigaOS 3.1 dos/loadseg.asm returns the first linked load segment and does
     not scan forward for the next CODE hunk; keep this isolated from any real
     target so corpus quirks cannot define the rule. */
  memset(&data_section, 0, sizeof(data_section));
  memset(&code_section, 0, sizeof(code_section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  data_section.kind = M68K_SECTION_DATA;
  data_section.size = sizeof(data_bytes);
  data_section.data_size = sizeof(data_bytes);
  data_section.data = data_bytes;
  code_section.kind = M68K_SECTION_CODE;
  code_section.size = sizeof(code_bytes);
  code_section.data_size = sizeof(code_bytes);
  code_section.data = code_bytes;
  added = m68k_object_add_section(&object, &data_section);
  M68K_C_ASSERT(added.ok);
  added = m68k_object_add_section(&object, &code_section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(0U, profile.code_start_section_entries);
  M68K_C_ASSERT_U32(0U, profile.accepted_instructions);
  M68K_C_ASSERT_U32(0U, profile.render_ir_instructions);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_required_entry_without_decode_is_hard_failure(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  uint8_t bytes[4] = {0x53u, 0xbeu, 0x00u, 0x00u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(1U, profile.code_start_section_entries);
  M68K_C_ASSERT_U32(0U, profile.decoded_candidates);
  M68K_C_ASSERT_U32(0U, profile.accepted_instructions);
  M68K_C_ASSERT_U32(1U, profile.required_instruction_failures);
  M68K_C_ASSERT_U32(0U, profile.first_required_instruction_failure_section);
  M68K_C_ASSERT_U32(0U, profile.first_required_instruction_failure_offset);
  M68K_C_ASSERT_U32(M68K_FACTS_V2_CODE_START_REASON_SECTION_ENTRY,
    profile.first_required_instruction_failure_reason);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_work_queue_dedupes_same_confidence_starts(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  uint8_t bytes[6] = {0x66u, 0x02u, 0x4eu, 0x71u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(4U, profile.code_start_facts);
  M68K_C_ASSERT_U32(3U, profile.queue_iterations);
  M68K_C_ASSERT_U32(3U, profile.accepted_instructions);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_work_queue_dedupes_same_runtime_view_starts(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile single_profile;
  M68kFactsV2Profile duplicate_profile;
  uint8_t bytes[6] = {0x66u, 0x02u, 0x4eu, 0x71u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = (uint32_t)sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0x100U;
  policy.runtime_entry_point_count = 1U;
  policy.runtime_entry_points[0].has_section_index = 1U;
  policy.runtime_entry_points[0].section_index = 0U;
  policy.runtime_entry_points[0].runtime_address = 0x100U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &single_profile, m68k_diag_sink(NULL)));
  policy.runtime_entry_point_count = 2U;
  policy.runtime_entry_points[1] = policy.runtime_entry_points[0];
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &duplicate_profile, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(single_profile.runtime_address_view_starts != 0U);
  M68K_C_ASSERT_U32(single_profile.queue_iterations, duplicate_profile.queue_iterations);
  M68K_C_ASSERT_U32(single_profile.accepted_instructions, duplicate_profile.accepted_instructions);
  M68K_C_ASSERT_U32(single_profile.render_ir_hash, duplicate_profile.render_ir_hash);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_records_mid_instruction_required_label(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  uint8_t bytes[14] = {
    0x4eu, 0x71u, 0x20u, 0x3cu, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x75u, 0x00u, 0x00u, 0x00u, 0x04u
  };
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 10U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(2U, profile.accepted_instructions);
  M68K_C_ASSERT_U32(0U, profile.unresolved_labels);
  M68K_C_ASSERT_U32(1U, profile.interior_conflicts);
  M68K_C_ASSERT_U32(1U, profile.interior_conflicts_resolved_by_demote);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_odd_code_target_is_hard_failure(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[6] = {0x66u, 0x01u, 0x4eu, 0x71u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  _putenv_s("AMIGA_REVERSING_FACTS_V2_ASM_SOURCE", "1");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)));
  _putenv_s("AMIGA_REVERSING_FACTS_V2_ASM_SOURCE", "");
  M68K_C_ASSERT_U32(1U, profile.required_instruction_failures);
  M68K_C_ASSERT_U32(1U, profile.asm_source_refused);
  M68K_C_ASSERT_INT(-1, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source == NULL);
  M68K_C_ASSERT_U32(1U, profile.required_instruction_failures);
  M68K_C_ASSERT_U32(1U, profile.asm_source_refused);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_direct_rebuild_profile_marks_source_refusal_without_rendering(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  uint8_t bytes[6] = {0x66u, 0x01u, 0x4eu, 0x71u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_direct_rebuild_profile(&object, &policy, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(1U, profile.required_instruction_failures);
  M68K_C_ASSERT_U32(1U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_enabled);
  M68K_C_ASSERT_U32(0U, profile.asm_source_symbolic_instructions);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_rejects_tool_inferred_interior_target_label(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[8] = {0x4eu, 0x71u, 0x48u, 0x78u, 0x00u, 0x34u, 0x60u, 0xfcu};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000004:") == NULL);
  M68K_C_ASSERT_U32(3U, profile.accepted_instructions);
  M68K_C_ASSERT_U32(0U, profile.labels_referenced);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_materializes_required_data_boundary_label(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  uint8_t bytes[8] = {0x66u, 0x05u, 0x4eu, 0x71u, 0x4eu, 0x75u, 0x12u, 0x34u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(0U, profile.unresolved_labels);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  M68K_C_ASSERT_U32(2U, profile.labels_created);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_relocation_uses_payload_target_before_addend(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  uint8_t bytes[10] = {0x4eu, 0x71u, 0x4eu, 0x71u, 0x4eu, 0x75u, 0x00u, 0x00u, 0x00u, 0x03u};
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 6U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.addend = 4;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(2U, profile.accepted_instructions);
  M68K_C_ASSERT_U32(0U, profile.unresolved_labels);
  M68K_C_ASSERT_U32(1U, profile.interior_conflicts);
  M68K_C_ASSERT_U32(1U, profile.interior_conflicts_resolved_by_demote);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_invalid_relocation_payload_records_violation(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  uint8_t bytes[10] = {0x4eu, 0x71u, 0x4eu, 0x75u, 0x00u, 0x00u, 0x00u, 0x00u, 0xffu, 0xffu};
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 6U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.addend = 2;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(2U, profile.accepted_instructions);
  M68K_C_ASSERT_U32(0U, profile.unresolved_labels);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_resolved_by_demote);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  M68K_C_ASSERT_U32(1U, profile.relocation_failures);
  M68K_C_ASSERT_U32(M68K_FACTS_V2_RELOCATION_FAILURE_TARGET_OUT_OF_RANGE,
    profile.first_relocation_failure_reason);
  M68K_C_ASSERT_U32(0U, profile.first_relocation_failure_section);
  M68K_C_ASSERT_U32(6U, profile.first_relocation_failure_offset);
  M68K_C_ASSERT_U32(0U, profile.first_relocation_failure_target_section);
  M68K_C_ASSERT_U32(4U, profile.first_relocation_failure_width);
  M68K_C_ASSERT_U32(65535U, profile.first_relocation_failure_raw_value);
  M68K_C_ASSERT_INT(65535, (int)profile.first_relocation_failure_computed_target);
  M68K_C_ASSERT_U32(1U, profile.labels_created);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_atari_relocation_uses_platform_normalized_addend(void) {
  M68kObject object;
  M68kSection code_section;
  M68kSection data_section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  uint8_t code_bytes[8] = {0x4eu, 0x71u, 0x4eu, 0x75u, 0x00u, 0x00u, 0x00u, 0x0au};
  uint8_t data_bytes[8] = {0};
  memset(&code_section, 0, sizeof(code_section));
  memset(&data_section, 0, sizeof(data_section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_ATARI_ST;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  code_section.kind = M68K_SECTION_CODE;
  code_section.size = sizeof(code_bytes);
  code_section.data_size = sizeof(code_bytes);
  code_section.data = code_bytes;
  added = m68k_object_add_section(&object, &code_section);
  M68K_C_ASSERT(added.ok);
  data_section.kind = M68K_SECTION_DATA;
  data_section.size = sizeof(data_bytes);
  data_section.data_size = sizeof(data_bytes);
  data_section.data = data_bytes;
  added = m68k_object_add_section(&object, &data_section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 4U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.addend = 2;
  fixup.target_section_index = 1U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(0U, profile.relocation_failures);
  M68K_C_ASSERT_U32(0U, profile.relocation_anchors);
  M68K_C_ASSERT_U32(0U, profile.unresolved_labels);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_atari_bss_image_relocation_renders_symbolic_instruction(void) {
  M68kObject object;
  M68kSection code_section;
  M68kSection data_section;
  M68kSection bss_section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t code_bytes[8] = {0x49u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x10u, 0x4eu, 0x75u};
  uint8_t data_bytes[8] = {0};
  memset(&code_section, 0, sizeof(code_section));
  memset(&data_section, 0, sizeof(data_section));
  memset(&bss_section, 0, sizeof(bss_section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_ATARI_ST;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  code_section.kind = M68K_SECTION_CODE;
  code_section.size = sizeof(code_bytes);
  code_section.data_size = sizeof(code_bytes);
  code_section.data = code_bytes;
  added = m68k_object_add_section(&object, &code_section);
  M68K_C_ASSERT(added.ok);
  data_section.kind = M68K_SECTION_DATA;
  data_section.size = sizeof(data_bytes);
  data_section.data_size = sizeof(data_bytes);
  data_section.data = data_bytes;
  added = m68k_object_add_section(&object, &data_section);
  M68K_C_ASSERT(added.ok);
  bss_section.kind = M68K_SECTION_BSS;
  bss_section.size = 4U;
  bss_section.data_size = 0U;
  added = m68k_object_add_section(&object, &bss_section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 2U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "loc_2_00000000") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_relocation_failures);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_recovers_atari_trap_call(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kRecoveredPlatformCallIR *call;
  const char *note_symbol_name;
  char *source = NULL;
  char *analysis_json = NULL;
  uint8_t bytes[6] = {0x3fu, 0x3cu, 0x00u, 0x4au, 0x4eu, 0x41u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_ATARI_ST;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source, &profile,
    &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT_U32(1U, profile.platform_call_count);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.section_count);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.sections[0].recovered_platform_call_count);
  call = &source_analysis.sections[0].recovered_platform_calls[0];
  note_symbol_name = m68k_platform_name_ref_resolve_text_or_fallback(&call->note_symbol_ref, call->note_symbol_name);
  M68K_C_ASSERT_U32(4U, call->offset);
  M68K_C_ASSERT_U32(M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL, call->note_kind);
  M68K_C_ASSERT_STR("m_shrink", note_symbol_name);
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"outputs\":[{\"name\":\"return\",\"regs\":[\"D0\"]") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"value_domain\":\"atari.st.os.return.long\"") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  free(analysis_json);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_atari_invalid_image_relocation_refuses_source(void) {
  M68kObject object;
  M68kSection code_section;
  M68kSection data_section;
  M68kSection bss_section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t code_bytes[8] = {0x4eu, 0x71u, 0x54u, 0x23u, 0xcau, 0x00u, 0x4eu, 0x75u};
  uint8_t data_bytes[8] = {0};
  memset(&code_section, 0, sizeof(code_section));
  memset(&data_section, 0, sizeof(data_section));
  memset(&bss_section, 0, sizeof(bss_section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_ATARI_ST;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  code_section.kind = M68K_SECTION_CODE;
  code_section.size = sizeof(code_bytes);
  code_section.data_size = sizeof(code_bytes);
  code_section.data = code_bytes;
  added = m68k_object_add_section(&object, &code_section);
  M68K_C_ASSERT(added.ok);
  data_section.kind = M68K_SECTION_DATA;
  data_section.size = sizeof(data_bytes);
  data_section.data_size = sizeof(data_bytes);
  data_section.data = data_bytes;
  added = m68k_object_add_section(&object, &data_section);
  M68K_C_ASSERT(added.ok);
  bss_section.kind = M68K_SECTION_BSS;
  bss_section.size = 4U;
  bss_section.data_size = 0U;
  added = m68k_object_add_section(&object, &bss_section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 2U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(-1, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source == NULL);
  M68K_C_ASSERT_U32(1U, profile.relocation_failures);
  M68K_C_ASSERT_U32(M68K_FACTS_V2_RELOCATION_FAILURE_TARGET_OUT_OF_RANGE,
    profile.first_relocation_failure_reason);
  M68K_C_ASSERT_U32(1U, profile.asm_source_refused);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_asm_source_preserves_atari_program_flags(void) {
  M68kObject object;
  M68kSection code_section;
  M68kSection data_section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t code_bytes[2] = {0x4eu, 0x75u};
  uint8_t symbol_table[68];
  uint8_t relocation_stream[68];
  memset(&code_section, 0, sizeof(code_section));
  memset(&data_section, 0, sizeof(data_section));
  memset(symbol_table, 0xA5, sizeof(symbol_table));
  memset(relocation_stream, 0, sizeof(relocation_stream));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_ATARI_ST;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  code_section.name = "TEXT";
  code_section.kind = M68K_SECTION_CODE;
  code_section.size = sizeof(code_bytes);
  code_section.data_size = sizeof(code_bytes);
  code_section.data = code_bytes;
  added = m68k_object_add_section(&object, &code_section);
  M68K_C_ASSERT(added.ok);
  data_section.name = "DATA";
  data_section.kind = M68K_SECTION_DATA;
  data_section.size = 0U;
  data_section.data_size = 0U;
  added = m68k_object_add_section(&object, &data_section);
  M68K_C_ASSERT(added.ok);
  M68K_C_ASSERT_INT(0, m68k_atari_st_set_program_flags(&object, 7U));
  M68K_C_ASSERT_INT(0, m68k_atari_st_set_relocation_flag(&object, 0xFFFFU));
  M68K_C_ASSERT_INT(0, m68k_atari_st_set_raw_symbol_table(&object, 1U, symbol_table,
    sizeof(symbol_table)));
  M68K_C_ASSERT_INT(0, m68k_atari_st_set_raw_relocation_stream(&object, relocation_stream,
    sizeof(relocation_stream)));
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "    COMMENT HEAD=$7\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    COMMENT ATARI_RELOC_FLAG=$FFFF\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    COMMENT ATARI_SYMBOL_TYPE=$1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    COMMENT ATARI_SYMBOLS=$A5A5A5A5A5A5A5A5") != NULL);
  M68K_C_ASSERT(strstr(source, "    COMMENT ATARI_SYMBOLS+=$A5A5A5A5\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    COMMENT ATARI_RELOC=$0000000000000000") != NULL);
  M68K_C_ASSERT(strstr(source, "    COMMENT ATARI_RELOC+=$00000000\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "    COMMENT HEAD=$7\n    COMMENT ATARI_RELOC_FLAG=$FFFF\n"
    "    COMMENT ATARI_SYMBOL_TYPE=$1\n"
    "    COMMENT ATARI_SYMBOLS=$") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_classifies_hunk_positive_relocation_anchor(void) {
  M68kObject object;
  M68kSection code_section;
  M68kSection data_section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t code_bytes[8] = {0x49u, 0xf9u, 0x00u, 0x00u, 0x7fu, 0xfeu, 0x4eu, 0x75u};
  uint8_t data_bytes[8] = {0};
  memset(&code_section, 0, sizeof(code_section));
  memset(&data_section, 0, sizeof(data_section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  code_section.kind = M68K_SECTION_CODE;
  code_section.size = sizeof(code_bytes);
  code_section.data_size = sizeof(code_bytes);
  code_section.data = code_bytes;
  added = m68k_object_add_section(&object, &code_section);
  M68K_C_ASSERT(added.ok);
  data_section.kind = M68K_SECTION_DATA;
  data_section.size = sizeof(data_bytes);
  data_section.data_size = sizeof(data_bytes);
  data_section.data = data_bytes;
  added = m68k_object_add_section(&object, &data_section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 2U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 1U;
  fixup.has_target_section = 1;
  fixup.platform_relocation_record_kind = AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "HUNK_RELOC32 numeric") != NULL);
  M68K_C_ASSERT(strstr(source, "base(hunk 1)+$00007FFE") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(1U, profile.asm_source_lossy_numeric_hunk_relocations);
  M68K_C_ASSERT_U32(0U, profile.relocation_failures);
  M68K_C_ASSERT_U32(1U, profile.relocation_anchors);
  M68K_C_ASSERT_U32(0U, profile.asm_source_relocation_anchor_refusals);
  M68K_C_ASSERT_U32(0U, profile.asm_source_unassemblable_hunk_base_register_relocation_refusals);
  M68K_C_ASSERT_U32(M68K_FACTS_V2_RELOCATION_ANCHOR_POSITIVE, profile.first_relocation_anchor_kind);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32,
    profile.first_relocation_anchor_platform_record_kind);
  M68K_C_ASSERT_U32(32766U, profile.first_relocation_anchor_raw_value);
  M68K_C_ASSERT_INT(32766, (int)profile.first_relocation_anchor_addend);
  M68K_C_ASSERT_U32(0U, profile.relocation_anchor_instruction_bytes);
  M68K_C_ASSERT_U32(0U, profile.relocation_anchor_data_payloads);
  M68K_C_ASSERT_U32(0U, profile.relocation_anchor_unknown_contexts);
  M68K_C_ASSERT_U32(0U, profile.unassemblable_hunk_data_relocations);
  M68K_C_ASSERT_U32(1U, profile.unassemblable_hunk_base_register_relocations);
  M68K_C_ASSERT_U32(M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_BASE_REGISTER,
    profile.first_relocation_anchor_context);
  M68K_C_ASSERT_U32(0U, profile.first_relocation_anchor_instruction_offset);
  M68K_C_ASSERT_U32(M68K_RENDER_IR_ASM_SOURCE_FAILURE_NONE, profile.asm_source_first_failure_kind);
  M68K_C_ASSERT_U32(0U, profile.asm_source_first_failure_section);
  M68K_C_ASSERT_U32(0U, profile.asm_source_first_failure_offset);
  M68K_C_ASSERT_U32(0U, profile.asm_source_first_failure_aux_offset);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_classifies_hunk_positive_data_relocation_anchor(void) {
  M68kObject object;
  M68kSection code_section;
  M68kSection data_section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t code_bytes[8] = {0x4eu, 0x71u, 0x4eu, 0x75u, 0x00u, 0x00u, 0x7fu, 0xfeu};
  uint8_t data_bytes[8] = {0};
  memset(&code_section, 0, sizeof(code_section));
  memset(&data_section, 0, sizeof(data_section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  code_section.kind = M68K_SECTION_CODE;
  code_section.size = sizeof(code_bytes);
  code_section.data_size = sizeof(code_bytes);
  code_section.data = code_bytes;
  added = m68k_object_add_section(&object, &code_section);
  M68K_C_ASSERT(added.ok);
  data_section.kind = M68K_SECTION_DATA;
  data_section.size = sizeof(data_bytes);
  data_section.data_size = sizeof(data_bytes);
  data_section.data = data_bytes;
  added = m68k_object_add_section(&object, &data_section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 4U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 1U;
  fixup.has_target_section = 1;
  fixup.platform_relocation_record_kind = AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l __section_1_base+$00007FFE") != NULL);
  M68K_C_ASSERT(strstr(source, "HUNK_RELOC32 numeric") == NULL);
  M68K_C_ASSERT(strstr(source, "base(hunk 1)+$00007FFE") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_lossy_numeric_hunk_relocations);
  M68K_C_ASSERT_U32(1U, profile.asm_source_relocation_exprs);
  M68K_C_ASSERT_U32(0U, profile.relocation_failures);
  M68K_C_ASSERT_U32(1U, profile.relocation_anchors);
  M68K_C_ASSERT_U32(0U, profile.asm_source_relocation_anchor_refusals);
  M68K_C_ASSERT_U32(0U, profile.asm_source_unassemblable_hunk_data_relocation_refusals);
  M68K_C_ASSERT_U32(0U, profile.asm_source_unassemblable_hunk_base_register_relocation_refusals);
  M68K_C_ASSERT_U32(M68K_FACTS_V2_RELOCATION_ANCHOR_POSITIVE, profile.first_relocation_anchor_kind);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32,
    profile.first_relocation_anchor_platform_record_kind);
  M68K_C_ASSERT_U32(32766U, profile.first_relocation_anchor_raw_value);
  M68K_C_ASSERT_INT(32766, (int)profile.first_relocation_anchor_addend);
  M68K_C_ASSERT_U32(0U, profile.relocation_anchor_instruction_bytes);
  M68K_C_ASSERT_U32(1U, profile.relocation_anchor_data_payloads);
  M68K_C_ASSERT_U32(0U, profile.relocation_anchor_unknown_contexts);
  M68K_C_ASSERT_U32(1U, profile.unassemblable_hunk_data_relocations);
  M68K_C_ASSERT_U32(0U, profile.unassemblable_hunk_base_register_relocations);
  M68K_C_ASSERT_U32(M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_DATA_PAYLOAD,
    profile.first_relocation_anchor_context);
  M68K_C_ASSERT_U32(M68K_RENDER_IR_ASM_SOURCE_FAILURE_NONE, profile.asm_source_first_failure_kind);
  M68K_C_ASSERT_U32(0U, profile.asm_source_first_failure_section);
  M68K_C_ASSERT_U32(0U, profile.asm_source_first_failure_offset);
  M68K_C_ASSERT_U32(0U, profile.asm_source_first_failure_aux_offset);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_classifies_hunk_negative_relocation_anchor(void) {
  M68kObject object;
  M68kObject rebuilt;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  AsmSourceFile parsed_source;
  M68kDiagList diagnostics;
  char *source = NULL;
  uint8_t bytes[8] = {0x4eu, 0x71u, 0x4eu, 0x75u, 0xffu, 0xffu, 0xffu, 0xfcu};
  memset(&rebuilt, 0, sizeof(rebuilt));
  memset(&parsed_source, 0, sizeof(parsed_source));
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  m68k_diag_list_reset(&diagnostics);
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 4U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  fixup.platform_relocation_record_kind = AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l __section_0_base-$00000004") != NULL);
  M68K_C_ASSERT(strstr(source, "HUNK_RELOC32 numeric") == NULL);
  M68K_C_ASSERT(strstr(source, "base(hunk 0)-$00000004") != NULL);
  parsed_source.target_cpu = M68K_ASM_CPU_68000;
  M68K_C_ASSERT(m68k_source_pipeline_parse_text_and_layout(&parsed_source, source,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_INT(1, m68k_source_pipeline_emit_object(&parsed_source, &rebuilt,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_U32(1U, (uint32_t)rebuilt.fixup_count);
  M68K_C_ASSERT_U32(0U, rebuilt.fixups[0].target_section_index);
  M68K_C_ASSERT_INT(-4, rebuilt.fixups[0].addend);
  M68K_C_ASSERT_U32(0xffU, rebuilt.sections[0].data[4]);
  M68K_C_ASSERT_U32(0xfcU, rebuilt.sections[0].data[7]);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_lossy_numeric_hunk_relocations);
  M68K_C_ASSERT_U32(1U, profile.asm_source_relocation_exprs);
  M68K_C_ASSERT_U32(0U, profile.relocation_failures);
  M68K_C_ASSERT_U32(1U, profile.relocation_anchors);
  M68K_C_ASSERT_U32(0U, profile.asm_source_relocation_anchor_refusals);
  M68K_C_ASSERT_U32(0U, profile.asm_source_unassemblable_hunk_data_relocation_refusals);
  M68K_C_ASSERT_U32(0U, profile.asm_source_unassemblable_hunk_base_register_relocation_refusals);
  M68K_C_ASSERT_U32(M68K_FACTS_V2_RELOCATION_ANCHOR_NEGATIVE, profile.first_relocation_anchor_kind);
  M68K_C_ASSERT_U32(AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32,
    profile.first_relocation_anchor_platform_record_kind);
  M68K_C_ASSERT_U32(0xfffffffcu, profile.first_relocation_anchor_raw_value);
  M68K_C_ASSERT_INT(-4, (int)profile.first_relocation_anchor_addend);
  M68K_C_ASSERT_U32(0U, profile.relocation_anchor_instruction_bytes);
  M68K_C_ASSERT_U32(1U, profile.relocation_anchor_data_payloads);
  M68K_C_ASSERT_U32(0U, profile.relocation_anchor_unknown_contexts);
  M68K_C_ASSERT_U32(1U, profile.unassemblable_hunk_data_relocations);
  M68K_C_ASSERT_U32(0U, profile.unassemblable_hunk_base_register_relocations);
  M68K_C_ASSERT_U32(M68K_FACTS_V2_RELOCATION_ANCHOR_CONTEXT_DATA_PAYLOAD,
    profile.first_relocation_anchor_context);
  M68K_C_ASSERT_U32(M68K_RENDER_IR_ASM_SOURCE_FAILURE_NONE, profile.asm_source_first_failure_kind);
  M68K_C_ASSERT_U32(0U, profile.asm_source_first_failure_section);
  M68K_C_ASSERT_U32(0U, profile.asm_source_first_failure_offset);
  M68K_C_ASSERT_U32(0U, profile.asm_source_first_failure_aux_offset);
  m68k_object_destroy(&rebuilt);
  m68k_source_model_free(&parsed_source);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_asm_source_renders_valid_relocation_expr(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  uint8_t bytes[8] = {0x00u, 0x00u, 0x00u, 0x04u, 0xdeu, 0xadu, 0xbeu, 0xefu};
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 0U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  _putenv_s("AMIGA_REVERSING_FACTS_V2_ASM_SOURCE", "1");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)));
  _putenv_s("AMIGA_REVERSING_FACTS_V2_ASM_SOURCE", "");
  M68K_C_ASSERT_U32(1U, profile.asm_source_enabled);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(1U, profile.asm_source_relocation_exprs);
  M68K_C_ASSERT(profile.asm_source_hash != 0U);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_hunk_relocation_target_inside_relocation_payload_is_numeric(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[8] = {0x00u, 0x00u, 0x00u, 0x05u, 0x00u, 0x00u, 0x00u, 0x00u};
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 0U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  fixup.platform_relocation_record_kind = AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  fixup.offset = 4U;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "dc.l $00000005") != NULL);
  M68K_C_ASSERT(strstr(source, "HUNK_RELOC32 numeric") != NULL);
  M68K_C_ASSERT(strstr(source, "dc.l loc_0_00000005") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(1U, profile.asm_source_lossy_numeric_hunk_relocations);
  M68K_C_ASSERT_U32(1U, profile.asm_source_relocation_exprs);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_relocation_failures);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_amiga_hunk_writer_preserves_reloc32_group_shape(void) {
  static const unsigned char input[] = {
    0x00, 0x00, 0x03, 0xF3, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x02,
    0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x03, 0xE9, 0x00, 0x00, 0x00, 0x02,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x03, 0xEC,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x00, 0x04,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x03, 0xF2,
    0x00, 0x00, 0x03, 0xEA, 0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x03, 0xF2,
  };
  M68kObject object;
  M68kDiagList diagnostics;
  unsigned char *output = NULL;
  size_t output_size = 0U;
  m68k_diag_list_reset(&diagnostics);
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  M68K_C_ASSERT_INT(0, M68K_BACKEND_AMIGA_HUNK.read_buffer(input, sizeof(input), &object,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_U32(2U, (uint32_t)object.fixup_count);
  M68K_C_ASSERT_U32(1U, object.fixups[0].platform_relocation_block_index);
  M68K_C_ASSERT_U32(1U, object.fixups[0].platform_relocation_group_index);
  M68K_C_ASSERT_U32(2U, object.fixups[1].platform_relocation_group_index);
  M68K_C_ASSERT_INT(0, M68K_BACKEND_AMIGA_HUNK.write_buffer(&object, &output, &output_size,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_U32((uint32_t)sizeof(input), (uint32_t)output_size);
  M68K_C_ASSERT(memcmp(output, input, sizeof(input)) == 0);
  free(output);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_asm_source_allows_demoted_interior_label(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[14] = {
    0x4eu, 0x71u, 0x20u, 0x3cu, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x75u, 0x00u, 0x00u, 0x00u, 0x04u
  };
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 10U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT_U32(1U, profile.asm_source_enabled);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT(profile.asm_source_bytes > 0U);
  M68K_C_ASSERT(strstr(source, "loc_0_00000004:") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000004:\n\tdc.b $00,$00,$00,$00") != NULL);
  M68K_C_ASSERT(strstr(source, "dc.l loc_0_00000004") != NULL);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_asm_source_hashes_clean_byte_source(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  uint8_t bytes[6] = {0x60u, 0x02u, 0x4eu, 0x71u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  _putenv_s("AMIGA_REVERSING_FACTS_V2_ASM_SOURCE", "1");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)));
  _putenv_s("AMIGA_REVERSING_FACTS_V2_ASM_SOURCE", "");
  M68K_C_ASSERT_U32(1U, profile.asm_source_enabled);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT(profile.asm_source_bytes > 0U);
  M68K_C_ASSERT(profile.asm_source_lines > 0U);
  M68K_C_ASSERT(profile.asm_source_hash != 0U);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_renders_symbolic_branch(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kRenderPlan source_plan;
  M68kRenderPlan listing_plan;
  M68kSourceAnalysisIR source_analysis;
  M68kSourceAnalysisIR listing_analysis;
  char *source = NULL;
  char *plan_source = NULL;
  M68kFactsV2Profile listing_profile;
  size_t row_index;
  int saw_section_row = 0;
  int saw_label_row = 0;
  int saw_instruction_source_row = 0;
  uint8_t bytes[6] = {0x60u, 0x02u, 0x4eu, 0x71u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_plan_analysis_profile_alloc(&object, &policy, &source,
    &source_plan, &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT_INT(0, m68k_render_plan_emit_all_alloc(&source_plan, &plan_source));
  M68K_C_ASSERT_STR(source, plan_source);
  M68K_C_ASSERT(strstr(source, "    SECTION section,code") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000004:") != NULL);
  M68K_C_ASSERT(strstr(source, "bra") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000004") != NULL);
  M68K_C_ASSERT(strstr(source, "facts_v2 instruction bytes") == NULL);
  for (row_index = 0U; row_index < source_plan.row_count; ++row_index) {
    const M68kRenderPlanRow *row = &source_plan.rows[row_index];
    M68K_C_ASSERT_U32(0U, row->kind == M68K_RENDER_PLAN_ROW_DIAGNOSTIC ? 1U : 0U);
    if (row->kind == M68K_RENDER_PLAN_ROW_SECTION) saw_section_row = 1;
    if (row->kind == M68K_RENDER_PLAN_ROW_LABEL && row->has_source_range) saw_label_row = 1;
    if (row->kind == M68K_RENDER_PLAN_ROW_INSTRUCTION && row->has_source_range &&
        row->source_offset == 0U && row->source_size == 2U)
      saw_instruction_source_row = 1;
  }
  M68K_C_ASSERT(saw_section_row);
  M68K_C_ASSERT(saw_label_row);
  M68K_C_ASSERT(saw_instruction_source_row);
  M68K_C_ASSERT_U32(profile.asm_source_lines, profile.asm_source_plan_rows);
  M68K_C_ASSERT_U32(profile.asm_source_lines, profile.asm_source_plan_lines);
  M68K_C_ASSERT_U32(profile.asm_source_bytes, profile.asm_source_plan_bytes);
  M68K_C_ASSERT_U32(2U, profile.asm_source_symbolic_instructions);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_render_failures);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_relocation_failures);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_plan_analysis_profile_alloc(&object, &policy, NULL,
    &listing_plan, &listing_profile, &listing_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(listing_plan.row_count != 0U);
  M68K_C_ASSERT_U32(listing_profile.asm_source_bytes, listing_profile.asm_source_plan_bytes);
  M68K_C_ASSERT_U32(listing_profile.asm_source_lines, listing_profile.asm_source_plan_lines);
  m68k_render_plan_destroy(&listing_plan);
  m68k_ir_source_analysis_destroy(&listing_analysis);
  m68k_render_plan_free_text(plan_source);
  m68k_render_plan_destroy(&source_plan);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_renders_symbolic_pc_relative_data_target(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[10] = {0x43u, 0xfau, 0x00u, 0x04u, 0x4eu, 0x75u, 'd', 'o', 's', 0x00u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l loc_0_00000006(pc),a1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000006:\n\tdc.b") != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l $4(pc),a1\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_accepts_reachable_68030_pmmu(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[14] = {
    0x60u, 0x02u, 0x4eu, 0x71u, 0xf0u, 0x12u, 0x9eu, 0x15u,
    0xf0u, 0x17u, 0x62u, 0x00u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tptestr #5,(a2),#7\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tpmove psr,(a7)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "dc.b $F0,$12,$9E,$15") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.unsupported_instruction_demotes);
  M68K_C_ASSERT_U32(0U, profile.required_instruction_failures);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_keeps_unrelocated_abs_call_numeric(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[8] = {0x4eu, 0xb9u, 0x00u, 0x00u, 0x00u, 0x06u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr $00000006.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "jsr loc_0_00000006") == NULL);
  M68K_C_ASSERT(strstr(source, "runtime_") == NULL);
  M68K_C_ASSERT(strstr(source, "jsr") != NULL);
  M68K_C_ASSERT(strstr(source, ".l") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_relocation_failures);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_symbolizes_local_abs_word_call(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t bytes[6] = {0x4eu, 0xb8u, 0x00u, 0x04u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.entry_point_count = 1U;
  policy.entry_points[0].has_section_index = 1U;
  policy.entry_points[0].section_index = 0U;
  policy.entry_points[0].offset = 4U;
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy,
    &source, &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000004:") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr loc_0_00000004.w\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr $0004.w\n") == NULL);
  M68K_C_ASSERT_U32(0U, (uint32_t)source_analysis.sections[0].recovered_indirect_site_count);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_relocation_failures);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_prefers_lower_cpu_fallthrough_over_inferred_interior_target(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t bytes[14] = {
    0x4eu, 0xb9u, 0x00u, 0x00u, 0x00u, 0x08u,
    0x30u, 0x3cu, 0x4eu, 0x7au, 0x00u, 0x00u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #$4E7A,d0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "movec") == NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000008:") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_prefers_same_cpu_fallthrough_over_inferred_interior_target(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[12] = {
    0x4eu, 0xb9u, 0x00u, 0x00u, 0x00u, 0x08u,
    0x30u, 0x3cu, 0x4eu, 0x75u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #$4E75,d0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000008:") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_detects_runtime_copy_jump_target(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *analysis_json = NULL;
  size_t code_start_index;
  int saw_runtime_entry = 0;
  char *source = NULL;
  uint8_t bytes[36] = {
    0x41u, 0xfau, 0x00u, 0x1eu,
    0x43u, 0xf9u, 0x00u, 0x00u, 0x01u, 0x00u,
    0x70u, 0x20u,
    0x12u, 0xd8u,
    0x53u, 0x80u,
    0x64u, 0xfau,
    0x4eu, 0xf9u, 0x00u, 0x00u, 0x01u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "runtime_") == NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp abs_0_00000100.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $100\nabs_0_00000100:\n\tnop\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000104") == NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000020:\n\tdc.b $4E,$71,$4E,$75") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_facts_v2_free_text(source);
  source = NULL;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "runtime_") == NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000100:\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp abs_0_00000100.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp $00000100.l\n") == NULL);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.section_count);
  for (code_start_index = 0U; code_start_index < source_analysis.sections[0].code_start_ref_count;
      ++code_start_index) {
    const M68kCodeStartRefIR *ref = &source_analysis.sections[0].code_start_refs[code_start_index];
    if (ref->offset == 32U && ref->reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET &&
        ref->has_runtime_address && ref->runtime_address == 0x100U) {
      saw_runtime_entry = 1;
    }
  }
  M68K_C_ASSERT(saw_runtime_entry);
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"reason_name\":\"control_target\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"runtime_address\":256") != NULL);
  free(analysis_json);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_traced_indirect_call_promotes_known_target(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  size_t code_start_index;
  int saw_indirect_target = 0;
  uint8_t bytes[14] = {
    0x41u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x0au,
    0x4eu, 0x90u,
    0x4eu, 0x75u,
    0x70u, 0x01u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_0000000A:\n\tmoveq.l #1,d0\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr (a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.b $70,$01,$4E,$75") == NULL);
  for (code_start_index = 0U; code_start_index < source_analysis.sections[0].code_start_ref_count;
      ++code_start_index) {
    const M68kCodeStartRefIR *ref = &source_analysis.sections[0].code_start_refs[code_start_index];
    if (ref->offset == 0x0AU && ref->reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET &&
        ref->source_offset == 0x06U) {
      saw_indirect_target = 1;
    }
  }
  M68K_C_ASSERT(saw_indirect_target);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_traced_displacement_indirect_jump_promotes_runtime_copy_target(void) {
  AsmSourceFile parsed_source;
  M68kDiagList diagnostics;
  M68kObject object;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  size_t code_start_index;
  int saw_runtime_entry = 0;
  const char *source_text =
    "SECTION section_0,code\n"
    "\tlea copied(pc),a0\n"
    "\tlea $00000100.l,a1\n"
    "\tmovea.l a1,a2\n"
    "\tmoveq #7,d0\n"
    "copy:\n"
    "\tmove.b (a0)+,(a1)+\n"
    "\tdbf d0,copy\n"
    "\tjmp $0004(a2)\n"
    "\trts\n"
    "copied:\n"
    "\tnop\n"
    "\tnop\n"
    "entry:\n"
    "\tnop\n"
    "\trts\n";
  memset(&parsed_source, 0, sizeof(parsed_source));
  memset(&object, 0, sizeof(object));
  memset(&source_analysis, 0, sizeof(source_analysis));
  m68k_diag_list_reset(&diagnostics);
  parsed_source.target_cpu = M68K_ASM_CPU_68000;
  M68K_C_ASSERT(m68k_source_pipeline_parse_text_and_layout(&parsed_source, source_text,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_INT(1, m68k_source_pipeline_emit_object(&parsed_source, &object,
    m68k_diag_sink(&diagnostics)));
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy,
    &source, &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp $0004(a2)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000104:\n\tnop\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000104:\n\tdc.b $4E,$71,$4E,$75") == NULL);
  for (code_start_index = 0U; code_start_index < source_analysis.sections[0].code_start_ref_count;
      ++code_start_index) {
    const M68kCodeStartRefIR *ref = &source_analysis.sections[0].code_start_refs[code_start_index];
    if (ref->reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET &&
        ref->has_runtime_address && ref->runtime_address == 0x104U) {
      saw_runtime_entry = 1;
    }
  }
  M68K_C_ASSERT(saw_runtime_entry);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  m68k_source_model_free(&parsed_source);
  return 0;
}

static int test_facts_v2_unmaterialized_runtime_copy_code_address_renders_equ_symbol(void) {
  AsmSourceFile parsed_source;
  M68kDiagList diagnostics;
  M68kObject object;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  size_t code_start_index;
  int saw_handler_entry = 0;
  int saw_payload_entry = 0;
  const char *source_text =
    "SECTION section_0,code\n"
    "\tlea handler(pc),a0\n"
    "\tlea $00000090.l,a1\n"
    "\tmoveq #5,d0\n"
    "copy_handler:\n"
    "\tmove.b (a0)+,(a1)+\n"
    "\tdbf d0,copy_handler\n"
    "\tlea payload(pc),a0\n"
    "\tlea $00000400.l,a1\n"
    "\tmoveq #3,d0\n"
    "copy_payload:\n"
    "\tmove.b (a0)+,(a1)+\n"
    "\tdbf d0,copy_payload\n"
    "\tmove.l #$00000090,$00000080.l\n"
    "\ttrap #0\n"
    "\trts\n"
    "handler:\n"
    "\tjmp $00000400.l\n"
    "payload:\n"
    "\tnop\n"
    "\trts\n";
  memset(&parsed_source, 0, sizeof(parsed_source));
  memset(&object, 0, sizeof(object));
  memset(&source_analysis, 0, sizeof(source_analysis));
  m68k_diag_list_reset(&diagnostics);
  parsed_source.target_cpu = M68K_ASM_CPU_68000;
  M68K_C_ASSERT(m68k_source_pipeline_parse_text_and_layout(&parsed_source, source_text,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_INT(1, m68k_source_pipeline_emit_object(&parsed_source, &object,
    m68k_diag_sink(&diagnostics)));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy,
    &source, &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "runtime_code_00000090\tEQU\t$90\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l runtime_code_00000090.l,a1\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.l #runtime_code_00000090,m68k_vector_trap_0_instruction_vector.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $90\n") == NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000090:") == NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $400\nabs_0_00000400:\n\tnop\n\trts\n") != NULL);
  for (code_start_index = 0U; code_start_index < source_analysis.sections[0].code_start_ref_count;
      ++code_start_index) {
    const M68kCodeStartRefIR *ref = &source_analysis.sections[0].code_start_refs[code_start_index];
    if (ref->reason != M68K_FACT_CODE_START_REASON_CONTROL_TARGET || !ref->has_runtime_address) continue;
    if (ref->runtime_address == 0x90U) saw_handler_entry = 1;
    if (ref->runtime_address == 0x400U) saw_payload_entry = 1;
  }
  M68K_C_ASSERT(saw_handler_entry);
  M68K_C_ASSERT(saw_payload_entry);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  m68k_source_model_free(&parsed_source);
  return 0;
}

static int test_facts_v2_absolute_stack_top_load_renders_equ_symbol(void) {
  AsmSourceFile parsed_source;
  M68kDiagList diagnostics;
  M68kObject object;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  const char *source_text =
    "SECTION section_0,code\n"
    "\tlea $00080000.l,a7\n"
    "\tmovea.l #$0007FFFC,a7\n"
    "\tadda.w #$12,a7\n"
    "\tmovea.l $00000004.l,a6\n"
    "\trts\n";
  memset(&parsed_source, 0, sizeof(parsed_source));
  memset(&object, 0, sizeof(object));
  memset(&source_analysis, 0, sizeof(source_analysis));
  m68k_diag_list_reset(&diagnostics);
  parsed_source.target_cpu = M68K_ASM_CPU_68000;
  M68K_C_ASSERT(m68k_source_pipeline_parse_text_and_layout(&parsed_source, source_text,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_INT(1, m68k_source_pipeline_emit_object(&parsed_source, &object,
    m68k_diag_sink(&diagnostics)));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy,
    &source, &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "stack_top_00080000\tEQU\t$80000\n") != NULL);
  M68K_C_ASSERT(strstr(source, "stack_top_0007FFFC\tEQU\t$7FFFC\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l stack_top_00080000.l,a7\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l #stack_top_0007FFFC,a7\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tadda.w #$12,a7\n") != NULL);
  M68K_C_ASSERT(strstr(source, "stack_top_00000012") == NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l $00000004.l,a6\n") != NULL);
  M68K_C_ASSERT(strstr(source, "stack_top_00000004") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  m68k_source_model_free(&parsed_source);
  return 0;
}

static int test_facts_v2_records_unresolved_indirect_jump_site(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  char *analysis_json = NULL;
  uint8_t bytes[4] = {
    0x4eu, 0xd0u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp (a0)\n") != NULL);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.section_count);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.sections[0].recovered_indirect_site_count);
  M68K_C_ASSERT_U32(0U, source_analysis.sections[0].recovered_indirect_sites[0].offset);
  M68K_C_ASSERT_U32(M68K_RECOVERED_INDIRECT_FLOW_JUMP,
    source_analysis.sections[0].recovered_indirect_sites[0].flow_kind);
  M68K_C_ASSERT_U32(M68K_RECOVERED_INDIRECT_SHAPE_IND,
    source_analysis.sections[0].recovered_indirect_sites[0].shape);
  M68K_C_ASSERT_U32(M68K_RECOVERED_INDIRECT_STATUS_UNRESOLVED,
    source_analysis.sections[0].recovered_indirect_sites[0].status);
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"recovered_indirect_site_count\":1") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"flow\":\"jump\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"shape\":\"ind\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"status\":\"unresolved\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"source_offset\":0,\"source_size\":2,\"operand_index\":0") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"table_candidate_record_count\":1,\"table_candidate_records\":[{\"section_index\":0,\"offset\":0") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"source_pattern\":\"indirect\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"conflict_state_id\":2,\"conflict_state\":\"unresolved\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"conflict_state\":\"unresolved\"") != NULL);
  free(analysis_json);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_records_rejected_indirect_table_bounds(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kRecoveredIndirectSiteIR *site;
  char *source = NULL;
  char *analysis_json = NULL;
  uint8_t bytes[14] = {
    0x4eu, 0xfbu, 0x10u, 0x04u,
    0x4eu, 0x71u,
    0x60u, 0x04u,
    0x4eu, 0x71u,
    0x4eu, 0x71u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.sections[0].recovered_indirect_site_count);
  site = &source_analysis.sections[0].recovered_indirect_sites[0];
  M68K_C_ASSERT_U32(0U, site->offset);
  M68K_C_ASSERT_U32(M68K_RECOVERED_INDIRECT_SHAPE_INDEX_BRIEF, site->shape);
  M68K_C_ASSERT_U32(M68K_RECOVERED_INDIRECT_STATUS_UNRESOLVED, site->status);
  M68K_C_ASSERT_U32(1U, site->has_table_bounds);
  M68K_C_ASSERT_U32(M68K_RECOVERED_INDIRECT_TABLE_BOUNDS_REJECTED_INSUFFICIENT_ENTRIES,
    site->table_bounds_status);
  M68K_C_ASSERT_U32(6U, site->table_offset);
  M68K_C_ASSERT_U32(2U, site->table_size);
  M68K_C_ASSERT_U32(2U, site->table_entry_size);
  M68K_C_ASSERT_U32(1U, site->table_entry_count);
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"table_candidate_record_count\":1") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"source_pattern\":\"indexed_indirect\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"table_offset\":6,\"table_size\":2,\"table_entry_size\":2,\"table_entry_count\":1") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"table_bounds_status\":\"rejected_insufficient_entries\"") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  free(analysis_json);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_reports_orphan_terminal_code_signal_without_promoting(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  char *analysis_json = NULL;
  uint8_t bytes[8] = {
    0x4eu, 0x75u,
    0x70u, 0x01u,
    0x4eu, 0x75u,
    0x12u, 0x34u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.structured_data_item_count = 1U;
  policy.structured_data_items[0].has_section_index = 1U;
  policy.structured_data_items[0].section_index = 0U;
  policy.structured_data_items[0].offset = 6U;
  policy.structured_data_items[0].size = 2U;
  policy.structured_data_items[0].kind = M68K_ANALYSIS_STRUCTURED_DATA_WORDS;
  snprintf(policy.structured_data_items[0].semantic_role,
    sizeof(policy.structured_data_items[0].semantic_role), "lookup_table");
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmoveq.l #1,d0\n") == NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.b $70,$01,$4E,$75\n") != NULL);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.section_count);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.sections[0].orphan_code_signal_count);
  M68K_C_ASSERT_U32(2U, source_analysis.sections[0].orphan_code_signals[0].offset);
  M68K_C_ASSERT_U32(4U, source_analysis.sections[0].orphan_code_signals[0].size);
  M68K_C_ASSERT_U32(4U, source_analysis.sections[0].orphan_code_signals[0].terminal_offset);
  M68K_C_ASSERT_U32(M68K_SIM_FLOW_RETURN, source_analysis.sections[0].orphan_code_signals[0].terminal_flow_kind);
  M68K_C_ASSERT_U32(M68K_ASM_CPU_68000, source_analysis.sections[0].orphan_code_signals[0].required_cpu);
  M68K_C_ASSERT_U32(2U, source_analysis.sections[0].orphan_code_signals[0].instruction_count);
  M68K_C_ASSERT_U32(0U, source_analysis.sections[0].orphan_code_signals[0].decode_conflict_count);
  M68K_C_ASSERT_U32(M68K_ORPHAN_CODE_SIGNAL_TERMINAL_DECODE,
    source_analysis.sections[0].orphan_code_signals[0].reason);
  M68K_C_ASSERT_U32(M68K_ORPHAN_CODE_SIGNAL_UNRESOLVED,
    source_analysis.sections[0].orphan_code_signals[0].status);
  M68K_C_ASSERT_U32(M68K_ORPHAN_CODE_SIGNAL_CONTEXT_ACCEPTED_CODE_BOUNDARY,
    source_analysis.sections[0].orphan_code_signals[0].context);
  M68K_C_ASSERT_U32(M68K_ORPHAN_CODE_SIGNAL_INBOUND_JUMP_TABLE,
    source_analysis.sections[0].orphan_code_signals[0].missing_inbound);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE,
    source_analysis.sections[0].orphan_code_signals[0].nearby_data_flags);
  M68K_C_ASSERT_STR("lookup_table", source_analysis.sections[0].orphan_code_signals[0].nearby_data_class);
  M68K_C_ASSERT_STR("after", source_analysis.sections[0].orphan_code_signals[0].nearby_data_relation);
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"findings\":{\"required_cpu\":0,\"cpu_violation_count\":0},"
    "\"orphan_code_signal_count\":1") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"orphan_code_signal_count\":1") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"terminal_flow_kind\":5,\"terminal_flow\":\"return\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"required_cpu\":0,\"instruction_count\":2,"
    "\"decode_conflict_count\":0") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"reason_id\":1,\"reason\":\"terminal_decode\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"status_id\":1,\"status\":\"unresolved\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"context_id\":1,\"context\":\"accepted_code_boundary\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"missing_inbound_id\":2,\"missing_inbound\":\"jump_table\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"nearby_data_class\":\"lookup_table\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"nearby_data_flags\":8") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"nearby_data_relation\":\"after\"") != NULL);
  free(analysis_json);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_orphan_signal_records_label_context(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t bytes[8] = {
    0x60u, 0x04u,
    0x70u, 0x01u,
    0x4eu, 0x75u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.named_label_count = 1U;
  policy.named_labels[0].has_section_index = 1U;
  policy.named_labels[0].section_index = 0U;
  policy.named_labels[0].offset = 2U;
  snprintf(policy.named_labels[0].name, sizeof(policy.named_labels[0].name), "maybe_callback");
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "maybe_callback:") != NULL);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.sections[0].orphan_code_signal_count);
  M68K_C_ASSERT_U32(2U, source_analysis.sections[0].orphan_code_signals[0].offset);
  M68K_C_ASSERT_U32(M68K_ORPHAN_CODE_SIGNAL_CONTEXT_RENDERABLE_LABEL,
    source_analysis.sections[0].orphan_code_signals[0].context);
  M68K_C_ASSERT_U32(M68K_ORPHAN_CODE_SIGNAL_INBOUND_METADATA,
    source_analysis.sections[0].orphan_code_signals[0].missing_inbound);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_orphan_signal_classifies_adjacent_pointer_table_as_callback(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  char *analysis_json = NULL;
  uint8_t bytes[10] = {
    0x4eu, 0x75u,
    0x70u, 0x01u,
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x02u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.structured_data_item_count = 1U;
  policy.structured_data_items[0].has_section_index = 1U;
  policy.structured_data_items[0].section_index = 0U;
  policy.structured_data_items[0].offset = 6U;
  policy.structured_data_items[0].size = 4U;
  policy.structured_data_items[0].kind = M68K_ANALYSIS_STRUCTURED_DATA_LONGS;
  snprintf(policy.structured_data_items[0].semantic_role,
    sizeof(policy.structured_data_items[0].semantic_role), "pointer_table");
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmoveq.l #1,d0\n") == NULL);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.sections[0].orphan_code_signal_count);
  M68K_C_ASSERT_U32(M68K_ORPHAN_CODE_SIGNAL_INBOUND_CALLBACK,
    source_analysis.sections[0].orphan_code_signals[0].missing_inbound);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE,
    source_analysis.sections[0].orphan_code_signals[0].nearby_data_flags);
  M68K_C_ASSERT_STR("pointer_table", source_analysis.sections[0].orphan_code_signals[0].nearby_data_class);
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"missing_inbound_id\":3,\"missing_inbound\":\"callback\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"nearby_data_class\":\"pointer_table\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"nearby_data_flags\":4") != NULL);
  free(analysis_json);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_orphan_signal_records_minimum_decode_cpu(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t bytes[10] = {
    0x4eu, 0x75u,
    0xf0u, 0x12u, 0x9eu, 0x15u,
    0x4eu, 0x75u,
    0x12u, 0x34u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.structured_data_item_count = 1U;
  policy.structured_data_items[0].has_section_index = 1U;
  policy.structured_data_items[0].section_index = 0U;
  policy.structured_data_items[0].offset = 8U;
  policy.structured_data_items[0].size = 2U;
  policy.structured_data_items[0].kind = M68K_ANALYSIS_STRUCTURED_DATA_WORDS;
  snprintf(policy.structured_data_items[0].semantic_role,
    sizeof(policy.structured_data_items[0].semantic_role), "lookup_table");
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tptestr #5,(a2),#7\n") == NULL);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.sections[0].orphan_code_signal_count);
  M68K_C_ASSERT_U32(M68K_ASM_CPU_68030, source_analysis.sections[0].orphan_code_signals[0].required_cpu);
  M68K_C_ASSERT_U32(2U, source_analysis.sections[0].orphan_code_signals[0].instruction_count);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_reached_terminal_island_is_not_orphan_signal(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t bytes[8] = {
    0x61u, 0x02u,
    0x4eu, 0x75u,
    0x70u, 0x01u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tbsr.b loc_0_00000004\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmoveq.l #1,d0\n") != NULL);
  M68K_C_ASSERT_U32(0U, (uint32_t)source_analysis.sections[0].orphan_code_signal_count);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_resolved_platform_call_not_unresolved_indirect_site(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t bytes[10] = {
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xffu, 0x7cu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOForbid(a6)\n") != NULL);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.sections[0].recovered_platform_call_count);
  M68K_C_ASSERT_U32(4U, source_analysis.sections[0].recovered_platform_calls[0].offset);
  M68K_C_ASSERT_U32(0U, (uint32_t)source_analysis.sections[0].recovered_indirect_site_count);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_open_library_d0_movea_promotes_a6_base(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t bytes[] = {
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x43u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x16u,
    0x4eu, 0xaeu, 0xfeu, 0x68u,
    0x2cu, 0x40u,
    0x4eu, 0xaeu, 0xffu, 0xc4u,
    0x4eu, 0x75u,
    'd', 'o', 's', '.', 'l', 'i', 'b', 'r', 'a', 'r', 'y', 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOOldOpenLibrary(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l d0,a6\n\tjsr _LVOOutput(a6)\n") != NULL);
  M68K_C_ASSERT_U32(2U, (uint32_t)source_analysis.sections[0].recovered_platform_call_count);
  M68K_C_ASSERT_U32(0U, (uint32_t)source_analysis.sections[0].recovered_indirect_site_count);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_open_library_cross_section_name_promotes_a6_base(void) {
  M68kObject object;
  M68kSection code_section;
  M68kSection data_section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t code_bytes[] = {
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x43u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0xaeu, 0xfeu, 0x68u,
    0x23u, 0xc0u, 0x00u, 0x00u, 0x00u, 0x0cu,
    0x2cu, 0x40u,
    0x4eu, 0xaeu, 0xffu, 0xc4u,
    0x23u, 0xc0u, 0x00u, 0x00u, 0x00u, 0x10u,
    0x4eu, 0x75u
  };
  uint8_t data_bytes[] = {
    'd', 'o', 's', '.', 'l', 'i', 'b', 'r', 'a', 'r', 'y', 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u
  };
  memset(&code_section, 0, sizeof(code_section));
  memset(&data_section, 0, sizeof(data_section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  code_section.kind = M68K_SECTION_CODE;
  code_section.size = sizeof(code_bytes);
  code_section.data_size = sizeof(code_bytes);
  code_section.data = code_bytes;
  added = m68k_object_add_section(&object, &code_section);
  M68K_C_ASSERT(added.ok);
  data_section.kind = M68K_SECTION_DATA;
  data_section.size = sizeof(data_bytes);
  data_section.data_size = sizeof(data_bytes);
  data_section.data = data_bytes;
  added = m68k_object_add_section(&object, &data_section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 6U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 1U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  fixup.offset = 16U;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  fixup.offset = 28U;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l loc_1_00000000.l,a1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOOldOpenLibrary(a6)\n\tmove.l d0,h1dl_DOSBase.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l d0,a6\n\tjsr _LVOOutput(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOOutput(a6)\n\tmove.l d0,loc_1_00000010.l\n") != NULL);
  M68K_C_ASSERT_U32(2U, (uint32_t)source_analysis.sections[0].recovered_platform_call_count);
  M68K_C_ASSERT_U32(0U, (uint32_t)source_analysis.sections[0].recovered_indirect_site_count);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_stack_stored_callback_vector_promotes_target(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  size_t code_start_index;
  int saw_vector_target = 0;
  uint8_t bytes[22] = {
    0x48u, 0x7au, 0x00u, 0x10u,
    0x23u, 0xdfu, 0x00u, 0x00u, 0x00u, 0x10u,
    0x4au, 0xfcu,
    0xd5u, 0x03u, 0xffu, 0xe1u, 0x60u, 0x1eu,
    0x70u, 0x01u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tpea.l loc_0_00000012(pc)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l (a7)+,m68k_vector_illegal_instruction.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\taddx.b d3,d2\n") == NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.b $D5,$03,$FF,$E1,$60,$1E") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000012:\n\tmoveq.l #1,d0\n\trts\n") != NULL);
  for (code_start_index = 0U; code_start_index < source_analysis.sections[0].code_start_ref_count;
      ++code_start_index) {
    const M68kCodeStartRefIR *ref = &source_analysis.sections[0].code_start_refs[code_start_index];
    if (ref->offset == 0x12U && ref->reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET &&
        ref->source_offset == 0x04U) {
      saw_vector_target = 1;
    }
  }
  M68K_C_ASSERT(saw_vector_target);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_traced_indirect_jump_promotes_long_table_targets(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint32_t saw_targets = 0U;
  size_t code_start_index;
  uint8_t bytes[36] = {
    0x41u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x0cu,
    0x20u, 0x70u, 0x00u, 0x00u,
    0x4eu, 0xd0u,
    0x00u, 0x00u, 0x00u, 0x1cu,
    0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x20u,
    0x4eu, 0x71u, 0x4eu, 0x71u,
    0x70u, 0x01u, 0x4eu, 0x75u,
    0x70u, 0x02u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp (a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_0000001C:\n\tmoveq.l #1,d0\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000020:\n\tmoveq.l #2,d0\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.b $70,$01,$4E,$75") == NULL);
  for (code_start_index = 0U; code_start_index < source_analysis.sections[0].code_start_ref_count;
      ++code_start_index) {
    const M68kCodeStartRefIR *ref = &source_analysis.sections[0].code_start_refs[code_start_index];
    if (ref->reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET && ref->source_offset == 0x0AU) {
      if (ref->offset == 0x1CU) saw_targets |= 1U;
      if (ref->offset == 0x20U) saw_targets |= 2U;
    }
  }
  M68K_C_ASSERT_U32(3U, saw_targets);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.sections[0].recovered_indirect_site_count);
  M68K_C_ASSERT_U32(0x0AU, source_analysis.sections[0].recovered_indirect_sites[0].offset);
  M68K_C_ASSERT_U32(M68K_RECOVERED_INDIRECT_STATUS_JUMP_TABLE,
    source_analysis.sections[0].recovered_indirect_sites[0].status);
  M68K_C_ASSERT_U32(1U, source_analysis.sections[0].recovered_indirect_sites[0].has_target_count);
  M68K_C_ASSERT_U32(2U, source_analysis.sections[0].recovered_indirect_sites[0].target_count);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_long_jump_table_base_renders_label_addend(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[40] = {
    0x70u, 0x01u,
    0xe5u, 0x40u,
    0x41u, 0xf9u, 0x00u, 0x00u, 0x01u, 0x0Cu,
    0x20u, 0x70u, 0x00u, 0x00u,
    0x4eu, 0xd0u,
    0x00u, 0x00u, 0x01u, 0x20u,
    0x00u, 0x00u, 0x01u, 0x24u,
    0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x75u, 0x4eu, 0x71u,
    0x4eu, 0x75u, 0x4eu, 0x71u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0x100U;
  policy.runtime_entry_point_count = 1U;
  policy.runtime_entry_points[0].has_section_index = 1U;
  policy.runtime_entry_points[0].section_index = 0U;
  policy.runtime_entry_points[0].runtime_address = 0x100U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l abs_0_00000110-4.l,a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000110:\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l $0000010C.l,a0\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_traced_indirect_jump_keeps_later_table_state(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint32_t saw_targets = 0U;
  size_t code_start_index;
  uint8_t bytes[30] = {
    0x67u, 0x0au,
    0x41u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x0eu,
    0x20u, 0x70u, 0x00u, 0x00u,
    0x4eu, 0xd0u,
    0x00u, 0x00u, 0x00u, 0x16u,
    0x00u, 0x00u, 0x00u, 0x1au,
    0x70u, 0x01u, 0x4eu, 0x75u,
    0x70u, 0x02u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tbeq.b loc_0_0000000C\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp (a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000016:\n\tmoveq.l #1,d0\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_0000001A:\n\tmoveq.l #2,d0\n\trts\n") != NULL);
  for (code_start_index = 0U; code_start_index < source_analysis.sections[0].code_start_ref_count;
      ++code_start_index) {
    const M68kCodeStartRefIR *ref = &source_analysis.sections[0].code_start_refs[code_start_index];
    if (ref->reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET && ref->source_offset == 0x0CU) {
      if (ref->offset == 0x16U) saw_targets |= 1U;
      if (ref->offset == 0x1AU) saw_targets |= 2U;
    }
  }
  M68K_C_ASSERT_U32(3U, saw_targets);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.sections[0].recovered_indirect_site_count);
  M68K_C_ASSERT_U32(0x0CU, source_analysis.sections[0].recovered_indirect_sites[0].offset);
  M68K_C_ASSERT_U32(M68K_RECOVERED_INDIRECT_STATUS_JUMP_TABLE,
    source_analysis.sections[0].recovered_indirect_sites[0].status);
  M68K_C_ASSERT_U32(1U, source_analysis.sections[0].recovered_indirect_sites[0].has_target_count);
  M68K_C_ASSERT_U32(2U, source_analysis.sections[0].recovered_indirect_sites[0].target_count);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_runtime_mapped_long_dispatch_promotes_table_targets(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint32_t saw_targets = 0U;
  size_t code_start_index;
  uint8_t bytes[28] = {
    0x41u, 0xf9u, 0x00u, 0x00u, 0x01u, 0x0cu,
    0x20u, 0x70u, 0x00u, 0x00u,
    0x4eu, 0xd0u,
    0x00u, 0x00u, 0x01u, 0x14u,
    0x00u, 0x00u, 0x01u, 0x18u,
    0x70u, 0x01u, 0x4eu, 0x75u,
    0x70u, 0x02u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = (uint32_t)sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0x100U;
  policy.runtime_entry_point_count = 1U;
  policy.runtime_entry_points[0].has_section_index = 1U;
  policy.runtime_entry_points[0].section_index = 0U;
  policy.runtime_entry_points[0].runtime_address = 0x100U;
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp (a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmoveq.l #1,d0\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmoveq.l #2,d0\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l abs_0_00000114\t; pointer_table\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l abs_0_00000118\n") != NULL);
  for (code_start_index = 0U; code_start_index < source_analysis.sections[0].code_start_ref_count;
      ++code_start_index) {
    const M68kCodeStartRefIR *ref = &source_analysis.sections[0].code_start_refs[code_start_index];
    if (ref->reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET && ref->source_offset == 0x0AU) {
      if (ref->offset == 0x14U) saw_targets |= 1U;
      if (ref->offset == 0x18U) saw_targets |= 2U;
    }
  }
  M68K_C_ASSERT_U32(3U, saw_targets);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.sections[0].recovered_indirect_site_count);
  M68K_C_ASSERT_U32(0x0AU, source_analysis.sections[0].recovered_indirect_sites[0].offset);
  M68K_C_ASSERT_U32(M68K_RECOVERED_INDIRECT_STATUS_JUMP_TABLE,
    source_analysis.sections[0].recovered_indirect_sites[0].status);
  M68K_C_ASSERT_U32(1U, source_analysis.sections[0].recovered_indirect_sites[0].has_target_count);
  M68K_C_ASSERT_U32(2U, source_analysis.sections[0].recovered_indirect_sites[0].target_count);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static void test_store_u32be(uint8_t *bytes, uint32_t offset, uint32_t value) {
  bytes[offset] = (uint8_t)((value >> 24) & 0xFFU);
  bytes[offset + 1U] = (uint8_t)((value >> 16) & 0xFFU);
  bytes[offset + 2U] = (uint8_t)((value >> 8) & 0xFFU);
  bytes[offset + 3U] = (uint8_t)(value & 0xFFU);
}

static int test_facts_v2_long_dispatch_promotes_targets_beyond_small_trace_set(void) {
  enum {
    ENTRY_COUNT = 40,
    TABLE_OFFSET = 12,
    TARGET_START = TABLE_OFFSET + (ENTRY_COUNT * 4),
    TOTAL_SIZE = TARGET_START + (ENTRY_COUNT * 4)
  };
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint32_t late_target = TARGET_START + (34U * 4U);
  uint32_t saw_late_target = 0U;
  size_t code_start_index;
  uint32_t index;
  uint8_t bytes[TOTAL_SIZE];
  memset(bytes, 0, sizeof(bytes));
  bytes[0] = 0x41U;
  bytes[1] = 0xF9U;
  test_store_u32be(bytes, 2U, TABLE_OFFSET);
  bytes[6] = 0x20U;
  bytes[7] = 0x70U;
  bytes[8] = 0x00U;
  bytes[9] = 0x00U;
  bytes[10] = 0x4EU;
  bytes[11] = 0xD0U;
  for (index = 0U; index < ENTRY_COUNT; ++index) {
    uint32_t target = TARGET_START + (index * 4U);
    test_store_u32be(bytes, TABLE_OFFSET + (index * 4U), target);
    bytes[target] = 0x70U;
    bytes[target + 1U] = (uint8_t)index;
    bytes[target + 2U] = 0x4EU;
    bytes[target + 3U] = 0x75U;
  }
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp (a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000134:\n\tmoveq.l #34,d0\n\trts\n") != NULL);
  for (code_start_index = 0U; code_start_index < source_analysis.sections[0].code_start_ref_count;
      ++code_start_index) {
    const M68kCodeStartRefIR *ref = &source_analysis.sections[0].code_start_refs[code_start_index];
    if (ref->reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET && ref->source_offset == 0x0AU &&
        ref->offset == late_target) {
      saw_late_target = 1U;
    }
  }
  M68K_C_ASSERT_U32(1U, saw_late_target);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_traced_indirect_jump_promotes_word_relative_table_targets(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  char *analysis_json = NULL;
  uint32_t saw_targets = 0U;
  size_t code_start_index;
  uint8_t bytes[30] = {
    0x43u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x16u,
    0x41u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x12u,
    0xd2u, 0xf0u, 0x10u, 0x00u,
    0x4eu, 0xd1u,
    0x00u, 0x00u, 0x00u, 0x04u,
    0x70u, 0x01u, 0x4eu, 0x75u,
    0x70u, 0x02u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp (a1)\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tdc.w loc_0_00000016-loc_0_00000016,loc_0_0000001A-loc_0_00000016\t; lookup_table\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.b $00,$00,$00,$04") == NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000016:\n\tmoveq.l #1,d0\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_0000001A:\n\tmoveq.l #2,d0\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.b $70,$01,$4E,$75") == NULL);
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"offset\":18,\"size\":4,\"kind\":2,\"semantic_role\":\"lookup_table\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"has_target\":true,\"target_section\":0,\"target_offset\":22") != NULL);
  for (code_start_index = 0U; code_start_index < source_analysis.sections[0].code_start_ref_count;
      ++code_start_index) {
    const M68kCodeStartRefIR *ref = &source_analysis.sections[0].code_start_refs[code_start_index];
    if (ref->reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET && ref->source_offset == 0x10U) {
      if (ref->offset == 0x16U) saw_targets |= 1U;
      if (ref->offset == 0x1AU) saw_targets |= 2U;
    }
  }
  M68K_C_ASSERT_U32(3U, saw_targets);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.sections[0].recovered_indirect_site_count);
  M68K_C_ASSERT_U32(0x10U, source_analysis.sections[0].recovered_indirect_sites[0].offset);
  M68K_C_ASSERT_U32(M68K_RECOVERED_INDIRECT_STATUS_JUMP_TABLE,
    source_analysis.sections[0].recovered_indirect_sites[0].status);
  M68K_C_ASSERT_U32(1U, source_analysis.sections[0].recovered_indirect_sites[0].has_target_count);
  M68K_C_ASSERT_U32(2U, source_analysis.sections[0].recovered_indirect_sites[0].target_count);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  free(analysis_json);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_word_dispatch_promotes_far_relative_targets(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  char *analysis_json = NULL;
  uint32_t saw_far_target = 0U;
  uint32_t saw_table_consumer = 0U;
  size_t code_start_index;
  uint16_t item_index;
  uint8_t bytes[0x101EU];
  memset(bytes, 0, sizeof(bytes));
  bytes[0x00] = 0x43u;
  bytes[0x01] = 0xf9u;
  bytes[0x05] = 0x16u;
  bytes[0x06] = 0x41u;
  bytes[0x07] = 0xf9u;
  bytes[0x0b] = 0x12u;
  bytes[0x0c] = 0xd2u;
  bytes[0x0d] = 0xf0u;
  bytes[0x0e] = 0x10u;
  bytes[0x10] = 0x4eu;
  bytes[0x11] = 0xd1u;
  bytes[0x14] = 0x10u;
  bytes[0x15] = 0x04u;
  bytes[0x16] = 0x70u;
  bytes[0x17] = 0x01u;
  bytes[0x18] = 0x4eu;
  bytes[0x19] = 0x75u;
  bytes[0x101a] = 0x70u;
  bytes[0x101b] = 0x02u;
  bytes[0x101c] = 0x4eu;
  bytes[0x101d] = 0x75u;
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tdc.w loc_0_00000016-loc_0_00000016,loc_0_0000101A-loc_0_00000016\t; lookup_table\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w $1004") == NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_0000101A:\n\tmoveq.l #2,d0\n\trts\n") != NULL);
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"offset\":18,\"size\":4,\"kind\":2,\"semantic_role\":\"lookup_table\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"source_pattern\":\"indexed_word_dispatch\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"has_target\":true,\"target_section\":0,\"target_offset\":22") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"table_record_count\":1,\"table_records\":[{\"section_index\":0,"
    "\"offset\":18,\"size\":4,\"entry_size\":2,\"entry_count\":2,\"role\":\"lookup_table\","
    "\"table_kind\":\"relative_code_dispatch\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"base_expression\":\"target_label\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"consumer_section\":0,\"consumer_offset\":12") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"source_pattern\":\"indexed_word_dispatch\"") != NULL);
  for (item_index = 0U; item_index < source_analysis.policy.structured_data_item_count; ++item_index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[item_index];
    if (item->has_section_index && item->section_index == 0U && item->offset == 18U &&
        strcmp(item->semantic_role, "lookup_table") == 0) {
      M68K_C_ASSERT_U32(1U, item->has_consumer);
      M68K_C_ASSERT_U32(0U, item->consumer_section);
      M68K_C_ASSERT_U32(0x0CU, item->consumer_offset);
      M68K_C_ASSERT(strcmp(item->source_pattern, "indexed_word_dispatch") == 0);
      saw_table_consumer = 1U;
    }
  }
  M68K_C_ASSERT_U32(1U, saw_table_consumer);
  for (code_start_index = 0U; code_start_index < source_analysis.sections[0].code_start_ref_count;
      ++code_start_index) {
    const M68kCodeStartRefIR *ref = &source_analysis.sections[0].code_start_refs[code_start_index];
    if (ref->reason == M68K_FACT_CODE_START_REASON_CONTROL_TARGET && ref->source_offset == 0x10U &&
        ref->offset == 0x101AU) {
      saw_far_target = 1U;
    }
  }
  M68K_C_ASSERT_U32(1U, saw_far_target);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.sections[0].recovered_indirect_site_count);
  M68K_C_ASSERT_U32(0x10U, source_analysis.sections[0].recovered_indirect_sites[0].offset);
  M68K_C_ASSERT_U32(M68K_RECOVERED_INDIRECT_STATUS_JUMP_TABLE,
    source_analysis.sections[0].recovered_indirect_sites[0].status);
  M68K_C_ASSERT_U32(1U, source_analysis.sections[0].recovered_indirect_sites[0].has_target_count);
  M68K_C_ASSERT_U32(2U, source_analysis.sections[0].recovered_indirect_sites[0].target_count);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  free(analysis_json);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_source_analysis_table_record_marks_code_overlap_conflict(void) {
  M68kSourceAnalysisIR source_analysis;
  M68kSectionAnalysisIR section_analysis;
  uint8_t certain_code[4] = {1U, 1U, 0U, 0U};
  char *analysis_json = NULL;
  memset(&source_analysis, 0, sizeof(source_analysis));
  memset(&section_analysis, 0, sizeof(section_analysis));
  m68k_analysis_policy_init_default(&source_analysis.policy);
  source_analysis.section_count = 1U;
  source_analysis.sections = &section_analysis;
  section_analysis.section_index = 0U;
  section_analysis.section_size = sizeof(certain_code);
  section_analysis.certain_code_byte = certain_code;
  section_analysis.certain_code_size = sizeof(certain_code);
  source_analysis.policy.structured_data_item_count = 1U;
  source_analysis.policy.structured_data_items[0].has_section_index = 1U;
  source_analysis.policy.structured_data_items[0].section_index = 0U;
  source_analysis.policy.structured_data_items[0].offset = 0U;
  source_analysis.policy.structured_data_items[0].size = 2U;
  source_analysis.policy.structured_data_items[0].kind = M68K_ANALYSIS_STRUCTURED_DATA_WORDS;
  snprintf(source_analysis.policy.structured_data_items[0].semantic_role,
    sizeof(source_analysis.policy.structured_data_items[0].semantic_role), "lookup_table");
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"table_record_count\":1,\"table_records\":[{\"section_index\":0,\"offset\":0") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"conflicted\":true") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"conflict_state_id\":1,\"conflict_state\":\"code_overlap\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"conflict_state\":\"code_overlap\"") != NULL);
  free(analysis_json);
  return 0;
}

static int test_facts_v2_word_dispatch_stops_far_table_at_zero_boundary(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t bytes[0x1046U];
  memset(bytes, 0, sizeof(bytes));
  bytes[0x00] = 0x43u;
  bytes[0x01] = 0xf9u;
  bytes[0x05] = 0x40u;
  bytes[0x06] = 0x41u;
  bytes[0x07] = 0xf9u;
  bytes[0x0b] = 0x20u;
  bytes[0x0c] = 0xd2u;
  bytes[0x0d] = 0xf0u;
  bytes[0x0e] = 0x10u;
  bytes[0x10] = 0x4eu;
  bytes[0x11] = 0xd1u;
  bytes[0x22] = 0x10u;
  bytes[0x23] = 0x02u;
  bytes[0x28] = 0x01u;
  bytes[0x29] = 0x00u;
  bytes[0x40] = 0x70u;
  bytes[0x41] = 0x01u;
  bytes[0x42] = 0x4eu;
  bytes[0x43] = 0x75u;
  bytes[0x1042] = 0x70u;
  bytes[0x1043] = 0x02u;
  bytes[0x1044] = 0x4eu;
  bytes[0x1045] = 0x75u;
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tdc.w loc_0_00000040-loc_0_00000040,loc_0_00001042-loc_0_00000040\t; lookup_table\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000140:") == NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w loc_0_00000040-loc_0_00000040,loc_0_00000040-loc_0_00000040") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_pc_word_dispatch_renders_labels_across_saved_register(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t bytes[0x44U];
  memset(bytes, 0, sizeof(bytes));
  bytes[0x00] = 0x41u;
  bytes[0x01] = 0xf9u;
  bytes[0x05] = 0x30u;
  bytes[0x06] = 0xd0u;
  bytes[0x07] = 0xfbu;
  bytes[0x08] = 0x10u;
  bytes[0x09] = 0x18u;
  bytes[0x0a] = 0x2fu;
  bytes[0x0b] = 0x00u;
  bytes[0x0c] = 0x4eu;
  bytes[0x0d] = 0x90u;
  bytes[0x0e] = 0x4eu;
  bytes[0x0f] = 0x75u;
  bytes[0x22] = 0x00u;
  bytes[0x23] = 0x10u;
  bytes[0x30] = 0x70u;
  bytes[0x31] = 0x01u;
  bytes[0x32] = 0x4eu;
  bytes[0x33] = 0x75u;
  bytes[0x40] = 0x70u;
  bytes[0x41] = 0x02u;
  bytes[0x42] = 0x4eu;
  bytes[0x43] = 0x75u;
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.entry_point_count = 3U;
  policy.entry_points[0].has_section_index = 1U;
  policy.entry_points[0].section_index = 0U;
  policy.entry_points[0].offset = 0U;
  policy.entry_points[1].has_section_index = 1U;
  policy.entry_points[1].section_index = 0U;
  policy.entry_points[1].offset = 0x30U;
  policy.entry_points[2].has_section_index = 1U;
  policy.entry_points[2].section_index = 0U;
  policy.entry_points[2].offset = 0x40U;
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l d0,-(a7)\n\tjsr (a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tadda.w loc_0_00000020(pc,d1.w),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tdc.w loc_0_00000030-loc_0_00000030,loc_0_00000040-loc_0_00000030") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w $0000,$0010\t; lookup_table\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_pc_word_dispatch_renders_labels_across_address_preserving_local_call(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t bytes[0x44U];
  memset(bytes, 0, sizeof(bytes));
  bytes[0x00] = 0x41u;
  bytes[0x01] = 0xf9u;
  bytes[0x05] = 0x30u;
  bytes[0x06] = 0xd0u;
  bytes[0x07] = 0xfbu;
  bytes[0x08] = 0x10u;
  bytes[0x09] = 0x18u;
  bytes[0x0a] = 0x61u;
  bytes[0x0d] = 0x08u;
  bytes[0x0e] = 0x4eu;
  bytes[0x0f] = 0xd0u;
  bytes[0x10] = 0x4eu;
  bytes[0x11] = 0x75u;
  bytes[0x14] = 0x70u;
  bytes[0x15] = 0x00u;
  bytes[0x16] = 0x4eu;
  bytes[0x17] = 0x75u;
  bytes[0x22] = 0x00u;
  bytes[0x23] = 0x10u;
  bytes[0x30] = 0x70u;
  bytes[0x31] = 0x01u;
  bytes[0x32] = 0x4eu;
  bytes[0x33] = 0x75u;
  bytes[0x40] = 0x70u;
  bytes[0x41] = 0x02u;
  bytes[0x42] = 0x4eu;
  bytes[0x43] = 0x75u;
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.entry_point_count = 3U;
  policy.entry_points[0].has_section_index = 1U;
  policy.entry_points[0].section_index = 0U;
  policy.entry_points[0].offset = 0U;
  policy.entry_points[1].has_section_index = 1U;
  policy.entry_points[1].section_index = 0U;
  policy.entry_points[1].offset = 0x30U;
  policy.entry_points[2].has_section_index = 1U;
  policy.entry_points[2].section_index = 0U;
  policy.entry_points[2].offset = 0x40U;
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tbsr.w loc_0_00000014\n\tjmp (a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tdc.w loc_0_00000030-loc_0_00000030,loc_0_00000040-loc_0_00000030") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w $0000,$0010\t; lookup_table\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_runtime_mapped_word_dispatch_renders_lookup_table(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint32_t saw_runtime_refs = 0U;
  size_t index;
  uint8_t bytes[30] = {
    0x43u, 0xf9u, 0x00u, 0x00u, 0x01u, 0x16u,
    0x41u, 0xf9u, 0x00u, 0x00u, 0x01u, 0x12u,
    0xd2u, 0xf0u, 0x10u, 0x00u,
    0x4eu, 0xd1u,
    0x00u, 0x00u, 0x00u, 0x04u,
    0x70u, 0x01u, 0x4eu, 0x75u,
    0x70u, 0x02u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = (uint32_t)sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0x100U;
  policy.runtime_entry_point_count = 3U;
  policy.runtime_entry_points[0].has_section_index = 1U;
  policy.runtime_entry_points[0].section_index = 0U;
  policy.runtime_entry_points[0].runtime_address = 0x100U;
  policy.runtime_entry_points[1].has_section_index = 1U;
  policy.runtime_entry_points[1].section_index = 0U;
  policy.runtime_entry_points[1].runtime_address = 0x116U;
  policy.runtime_entry_points[2].has_section_index = 1U;
  policy.runtime_entry_points[2].section_index = 0U;
  policy.runtime_entry_points[2].runtime_address = 0x11AU;
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp (a1)\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tdc.w abs_0_00000116-abs_0_00000116,abs_0_0000011A-abs_0_00000116\t; lookup_table\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.b $00,$00,$00,$04") == NULL);
  M68K_C_ASSERT(strstr(source, "\tmoveq.l #1,d0\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmoveq.l #2,d0\n\trts\n") != NULL);
  for (index = 0U; index < source_analysis.sections[0].runtime_address_ref_count; ++index) {
    const M68kRuntimeAddressRefIR *ref = &source_analysis.sections[0].runtime_address_refs[index];
    if (ref->offset == 0U && ref->operand_index == 0U && ref->target_offset == 0x16U &&
        ref->has_runtime_address && ref->runtime_address == 0x116U) {
      saw_runtime_refs |= 1U;
    }
    if (ref->offset == 6U && ref->operand_index == 0U && ref->target_offset == 0x12U &&
        ref->has_runtime_address && ref->runtime_address == 0x112U) {
      saw_runtime_refs |= 2U;
    }
  }
  M68K_C_ASSERT_U32(3U, saw_runtime_refs);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_amiga_execbase_load_does_not_use_runtime_alias(void) {
  M68kObject object;
  M68kSection section;
  M68kFixup fixup;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kRenderPlan source_plan;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  char *plan_source = NULL;
  uint8_t bytes[26] = {
    0x2cu, 0x79u, 0x00u, 0x00u, 0x00u, 0x04u,
    0x41u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x18u,
    0x43u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x04u,
    0x4eu, 0xf9u, 0x00u, 0x00u, 0x00u, 0x04u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  memset(&fixup, 0, sizeof(fixup));
  fixup.section_index = 0U;
  fixup.offset = 8U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0x18U;
  policy.runtime_ranges[0].size = 2U;
  policy.runtime_ranges[0].runtime_address = 4U;
  policy.runtime_entry_point_count = 1U;
  policy.runtime_entry_points[0].has_section_index = 1U;
  policy.runtime_entry_points[0].section_index = 0U;
  policy.runtime_entry_points[0].runtime_address = 4U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_plan_analysis_profile_alloc(&object, &policy, &source,
    &source_plan, &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT_INT(0, m68k_render_plan_emit_all_alloc(&source_plan, &plan_source));
  M68K_C_ASSERT_STR(source, plan_source);
  M68K_C_ASSERT(strstr(source, "\tmovea.l $00000004.l,a6\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l loc_0_00000004.l,a6\n") == NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l loc_0_00000018.l,a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l abs_0_00000004.l,a0\n") == NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l abs_0_00000004.l,a1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp abs_0_00000004.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000018:\n    ORG $4\nabs_0_00000004:\n\trts\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_render_plan_free_text(plan_source);
  m68k_render_plan_destroy(&source_plan);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_word_dispatch_renders_bounded_unaccepted_lookup_table(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t bytes[22] = {
    0x43u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x0eu,
    0xd4u, 0x42u,
    0xd2u, 0xf1u, 0x20u, 0x00u,
    0x4eu, 0xd1u,
    0x00u, 0x04u, 0x00u, 0x06u,
    0x12u, 0x34u, 0x56u, 0x78u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp (a1)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w $0004,$0006\t; lookup_table\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.b $00,$04,$00,$06") == NULL);
  M68K_C_ASSERT_U32(0U, profile.unsupported_instruction_demotes);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_adjacent_runtime_ranges_do_not_org_back_to_storage(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t bytes[36] = {
    0x41u, 0xfau, 0x00u, 0x1eu,
    0x4eu, 0xf9u, 0x00u, 0x00u, 0x00u, 0x80u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0xf9u, 0x00u, 0x00u, 0x01u, 0x00u,
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  policy.runtime_range_count = 2U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0x10U;
  policy.runtime_ranges[0].size = 0x10U;
  policy.runtime_ranges[0].runtime_address = 0x80U;
  policy.runtime_ranges[1].has_section_index = 1U;
  policy.runtime_ranges[1].section_index = 0U;
  policy.runtime_ranges[1].offset = 0x20U;
  policy.runtime_ranges[1].size = 0x04U;
  policy.runtime_ranges[1].runtime_address = 0x100U;
  policy.runtime_entry_point_count = 2U;
  policy.runtime_entry_points[0].has_section_index = 1U;
  policy.runtime_entry_points[0].section_index = 0U;
  policy.runtime_entry_points[0].runtime_address = 0x80U;
  policy.runtime_entry_points[1].has_section_index = 1U;
  policy.runtime_entry_points[1].section_index = 0U;
  policy.runtime_entry_points[1].runtime_address = 0x100U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l loc_0_00000020(pc),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp $00000080.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000020:\n    ORG $100\nabs_0_00000100:\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $20\n") == NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $80\n") == NULL);
  M68K_C_ASSERT(strstr(source, "src_0_") == NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000020 EQU") == NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $100\nabs_0_00000100:\n\tnop\n\trts\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(1U, profile.asm_source_numeric_runtime_refs);
  M68K_C_ASSERT_U32(0U, profile.asm_source_first_numeric_runtime_ref_section);
  M68K_C_ASSERT_U32(4U, profile.asm_source_first_numeric_runtime_ref_offset);
  M68K_C_ASSERT_U32(0U, profile.asm_source_first_numeric_runtime_ref_target_section);
  M68K_C_ASSERT_U32(0x10U, profile.asm_source_first_numeric_runtime_ref_target_offset);
  M68K_C_ASSERT_U32(0x80U, profile.asm_source_first_numeric_runtime_ref_runtime_address);
  m68k_facts_v2_free_text(source);
  source = NULL;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l loc_0_00000020(pc),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000020:\n    ORG $100\nabs_0_00000100:\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $20\n") == NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $80\n") == NULL);
  M68K_C_ASSERT(strstr(source, "src_0_") == NULL);
  M68K_C_ASSERT_U32(1U, profile.asm_source_numeric_runtime_refs);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_contained_runtime_range_does_not_emit_second_org(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  char *analysis_json = NULL;
  size_t runtime_view_index;
  int found_contained_view = 0;
  uint8_t bytes[24] = {
    0x4eu, 0xf9u, 0x00u, 0x00u, 0x00u, 0x80u,
    0x4eu, 0xf9u, 0x00u, 0x00u, 0x00u, 0x84u,
    0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x75u,
    0x4eu, 0x71u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  memset(&source_analysis, 0, sizeof(source_analysis));
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.entry_point_count = 2U;
  policy.entry_points[0].has_section_index = 1U;
  policy.entry_points[0].section_index = 0U;
  policy.entry_points[0].offset = 0U;
  policy.entry_points[1].has_section_index = 1U;
  policy.entry_points[1].section_index = 0U;
  policy.entry_points[1].offset = 6U;
  policy.runtime_range_count = 2U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0x10U;
  policy.runtime_ranges[0].size = 8U;
  policy.runtime_ranges[0].runtime_address = 0x80U;
  policy.runtime_ranges[1].has_section_index = 1U;
  policy.runtime_ranges[1].section_index = 0U;
  policy.runtime_ranges[1].offset = 0x14U;
  policy.runtime_ranges[1].size = 4U;
  policy.runtime_ranges[1].runtime_address = 0x84U;
  policy.runtime_entry_point_count = 2U;
  policy.runtime_entry_points[0].has_section_index = 1U;
  policy.runtime_entry_points[0].section_index = 0U;
  policy.runtime_entry_points[0].runtime_address = 0x80U;
  policy.runtime_entry_points[1].has_section_index = 1U;
  policy.runtime_entry_points[1].section_index = 0U;
  policy.runtime_entry_points[1].runtime_address = 0x84U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp abs_0_00000080.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp abs_0_00000084.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000010:\n    ORG $80\nabs_0_00000080:\n") != NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000084:\n\tnop\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $84\n") == NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $14\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &source_analysis, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source_analysis.section_count == 1U);
  for (runtime_view_index = 0U; runtime_view_index < source_analysis.sections[0].runtime_view_count;
       ++runtime_view_index) {
    const M68kRuntimeViewIR *view = &source_analysis.sections[0].runtime_views[runtime_view_index];
    if (view->storage_offset == 0x14U && view->runtime_address == 0x84U) {
      M68K_C_ASSERT_U32(0U, view->materialized);
      M68K_C_ASSERT_U32(M68K_RUNTIME_VIEW_SUPPRESSED_REDUNDANT_CONTAINED_VIEW,
        view->materialization_reason);
      M68K_C_ASSERT_U32(M68K_RUNTIME_VIEW_RELATIONSHIP_CONTAINED_BY_RUNTIME_RANGE,
        view->relationship.kind);
      M68K_C_ASSERT_U32(0U, view->relationship.runtime_view_id);
      M68K_C_ASSERT_U32(0x10U, view->relationship.storage_offset);
      M68K_C_ASSERT_U32(0x80U, view->relationship.runtime_address);
      M68K_C_ASSERT_U32(8U, view->relationship.size);
      found_contained_view = 1;
    }
  }
  M68K_C_ASSERT(found_contained_view);
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"relationship_kind_name\":\"contained_by_runtime_range\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"related_runtime_address\":128") != NULL);
  free(analysis_json);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_mid_section_runtime_stub_does_not_org_back_to_storage(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kDecodeIR decode;
  M68kFactIR facts;
  M68kRenderIRPreview preview;
  M68kFact fact;
  uint8_t *accepted_start[1];
  uint8_t *accepted_bytes[1];
  uint8_t start_map[24];
  uint8_t byte_map[24];
  uint8_t bytes[24] = {
    0x4eu, 0xf9u, 0x00u, 0x00u, 0x50u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x30u, 0x3cu, 0x12u, 0x34u,
    0x4eu, 0x71u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(start_map, 0, sizeof(start_map));
  memset(byte_map, 0, sizeof(byte_map));
  accepted_start[0] = start_map;
  accepted_bytes[0] = byte_map;
  start_map[0] = 1U;
  memset(&byte_map[0], 1, 6U);
  start_map[0x10] = 1U;
  memset(&byte_map[0x10], 1, 4U);
  start_map[0x14] = 1U;
  memset(&byte_map[0x14], 1, 4U);
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_decode_ir_init(&decode);
  m68k_fact_ir_init(&facts);
  m68k_render_ir_preview_init(&preview);
  M68K_C_ASSERT_INT(0, m68k_decode_ir_build_object(&decode, &object, M68K_ASM_CPU_68060,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(0, m68k_fact_ir_create_label(&facts, 0U, 0U, M68K_FACT_CONFIDENCE_TOOL_INFERRED));
  M68K_C_ASSERT_INT(0, m68k_fact_ir_create_label(&facts, 0U, 0x10U, M68K_FACT_CONFIDENCE_TOOL_INFERRED));
  M68K_C_ASSERT_INT(0, m68k_fact_ir_create_label(&facts, 0U, 0x14U, M68K_FACT_CONFIDENCE_TOOL_INFERRED));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_CODE_START;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  fact.section_index = 0U;
  fact.offset = 0x10U;
  fact.reason = M68K_FACT_CODE_START_REASON_CONTROL_TARGET;
  fact.has_runtime_address = 1U;
  fact.runtime_address = 0x5000U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_RUNTIME_ADDRESS_RANGE;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  fact.section_index = 0U;
  fact.offset = 0x10U;
  fact.has_runtime_address = 1U;
  fact.runtime_kind = M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY;
  fact.runtime_address = 0x5000U;
  fact.size = 4U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_RUNTIME_ADDRESS_REF;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  fact.section_index = 0U;
  fact.offset = 0U;
  fact.target_section_index = 0U;
  fact.target_offset = 0x10U;
  fact.has_runtime_address = 1U;
  fact.runtime_address = 0x5000U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  M68K_C_ASSERT_INT(0, m68k_render_ir_preview_build(&object, &decode, &facts, NULL,
    accepted_start, accepted_bytes, 0, 1, 1, 1, &preview, NULL));
  M68K_C_ASSERT(preview.asm_source_text != NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "    ORG $5000\n") == NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "    ORG $14\n") == NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "runtime_code_00005000\tEQU\t$5000\n") != NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "\tjmp runtime_code_00005000.l\n") != NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "loc_0_00000010:\n\tmove.w #$1234,d0\n") != NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "loc_0_00000014:\n\tnop\n") != NULL);
  M68K_C_ASSERT_U32(0U, preview.asm_source_instruction_render_failures);
  m68k_render_ir_preview_destroy(&preview);
  m68k_fact_ir_destroy(&facts);
  m68k_decode_ir_destroy(&decode);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_detects_interrupt_vector_store_target(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t bytes[20] = {
    0x21u, 0xfcu, 0x00u, 0x00u, 0x00u, 0x10u, 0x00u, 0x68u,
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x73u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000010:\n\tnop\n\trte\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000010:\n\tdc.b $4E,$71,$4E,$73") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_detects_traced_register_interrupt_vector_store_target(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[24] = {
    0x41u, 0xfau, 0x00u, 0x12u,
    0x4eu, 0x71u,
    0x23u, 0xc8u, 0x00u, 0x00u, 0x00u, 0x10u,
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x73u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l a0,m68k_vector_illegal_instruction.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000014:\n\tnop\n\trte\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000014:\n\tdc.b $4E,$71,$4E,$73") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_detects_register_copied_interrupt_vector_store_target(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[28] = {
    0x22u, 0x3cu, 0x00u, 0x00u, 0x00u, 0x18u,
    0x24u, 0x01u,
    0x23u, 0xc2u, 0x00u, 0x00u, 0x00u, 0x10u,
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x73u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l #$18,d1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l d2,m68k_vector_illegal_instruction.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000018:\n\tnop\n\trte\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000018:\n\tdc.b $4E,$71,$4E,$73") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_traced_interrupt_vector_bad_target_does_not_refuse_source(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[28] = {
    0x60u, 0x0au,
    'a', 'i', 'n', 'b', 'i', 'r', 'd', ',', ' ', 'L',
    0x41u, 0xfau, 0xffu, 0xf4u,
    0x23u, 0xc8u, 0x00u, 0x00u, 0x00u, 0x64u,
    0x4eu, 0x75u,
    0x4eu, 0x71u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.required_instruction_failures);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_detects_interrupt_vector_fill_target(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[28] = {
    0x20u, 0x3cu, 0x00u, 0x00u, 0x00u, 0x18u,
    0x41u, 0xf8u, 0x00u, 0x60u,
    0x72u, 0x07u,
    0x20u, 0xc0u,
    0x51u, 0xc9u, 0xffu, 0xfau,
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x73u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000018:\n\trte\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000018:\n\tdc.b $4E,$73,$4E,$75") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_maps_copied_runtime_vector_target_to_source_offset(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[52] = {
    0x41u, 0xfau, 0x00u, 0x1eu,
    0x43u, 0xf9u, 0x00u, 0x00u, 0x01u, 0x00u,
    0x70u, 0x20u,
    0x12u, 0xd8u,
    0x53u, 0x80u,
    0x64u, 0xfau,
    0x4eu, 0xf9u, 0x00u, 0x00u, 0x01u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x21u, 0xfcu, 0x00u, 0x00u, 0x01u, 0x10u, 0x00u, 0x68u,
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x73u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "runtime_") == NULL);
  M68K_C_ASSERT(strstr(source, "m68k_vector_level_2_interrupt_autovector\tEQU\t$68") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.l #abs_0_00000110,m68k_vector_level_2_interrupt_autovector.w\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $100\nabs_0_00000100:\n") != NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000110:\n\tnop\n\trte\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000030:\n\tnop\n\trte\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_maps_copied_runtime_absolute_call_to_source_offset(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[52] = {
    0x41u, 0xfau, 0x00u, 0x1eu,
    0x43u, 0xf9u, 0x00u, 0x00u, 0x01u, 0x00u,
    0x70u, 0x20u,
    0x12u, 0xd8u,
    0x53u, 0x80u,
    0x64u, 0xfau,
    0x4eu, 0xf9u, 0x00u, 0x00u, 0x01u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0xb9u, 0x00u, 0x00u, 0x01u, 0x10u,
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "runtime_") == NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr abs_0_00000110.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $100\nabs_0_00000100:\n\tjsr abs_0_00000110.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000110:\n\tnop\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr $00000110.l\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_unmapped_absolute_jump_inside_copied_source_stays_numeric(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kRenderPlan source_plan;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  char *plan_source = NULL;
  uint8_t bytes[44] = {
    0x41u, 0xfau, 0x00u, 0x1eu,
    0x43u, 0xf9u, 0x00u, 0x00u, 0x01u, 0x00u,
    0x70u, 0x08u,
    0x12u, 0xd8u,
    0x53u, 0x80u,
    0x64u, 0xfau,
    0x4eu, 0xf9u, 0x00u, 0x00u, 0x00u, 0x24u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x75u, 0x4eu, 0x71u, 0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_plan_analysis_profile_alloc(&object, &policy, &source,
    &source_plan, &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT_INT(0, m68k_render_plan_emit_all_alloc(&source_plan, &plan_source));
  M68K_C_ASSERT_STR(source, plan_source);
  M68K_C_ASSERT(strstr(source, "\tjmp $00000024.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp abs_0_00000104.l\n") == NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000104:") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_render_plan_free_text(plan_source);
  m68k_render_plan_destroy(&source_plan);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_runtime_trampoline_copy_does_not_force_low_org(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kDecodeIR decode;
  M68kFactIR facts;
  M68kRenderIRPreview preview;
  M68kFact fact;
  uint8_t *accepted_start[1];
  uint8_t *accepted_bytes[1];
  uint8_t start_map[48];
  uint8_t byte_map[48];
  uint8_t bytes[48] = {
    0x4eu, 0xf9u, 0x00u, 0x00u, 0x00u, 0x04u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0xf9u, 0x00u, 0x00u, 0x00u, 0x64u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  memset(start_map, 0, sizeof(start_map));
  memset(byte_map, 0, sizeof(byte_map));
  accepted_start[0] = start_map;
  accepted_bytes[0] = byte_map;
  start_map[0] = 1U;
  memset(&byte_map[0], 1, 6U);
  start_map[0x10] = 1U;
  memset(&byte_map[0x10], 1, 6U);
  start_map[0x20] = 1U;
  memset(&byte_map[0x20], 1, 4U);
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_decode_ir_init(&decode);
  m68k_fact_ir_init(&facts);
  m68k_render_ir_preview_init(&preview);
  M68K_C_ASSERT_INT(0, m68k_decode_ir_build_object(&decode, &object, M68K_ASM_CPU_68060,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(0, m68k_fact_ir_create_label(&facts, 0U, 0U, M68K_FACT_CONFIDENCE_TOOL_INFERRED));
  M68K_C_ASSERT_INT(0, m68k_fact_ir_create_label(&facts, 0U, 0x10U, M68K_FACT_CONFIDENCE_TOOL_INFERRED));
  M68K_C_ASSERT_INT(0, m68k_fact_ir_create_label(&facts, 0U, 0x20U, M68K_FACT_CONFIDENCE_TOOL_INFERRED));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_CODE_START;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  fact.section_index = 0U;
  fact.offset = 0x10U;
  fact.reason = M68K_FACT_CODE_START_REASON_CONTROL_TARGET;
  fact.has_runtime_address = 1U;
  fact.runtime_address = 4U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_RUNTIME_ADDRESS_RANGE;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  fact.section_index = 0U;
  fact.offset = 0x10U;
  fact.has_runtime_address = 1U;
  fact.runtime_kind = M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY;
  fact.runtime_address = 4U;
  fact.size = 6U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_RUNTIME_ADDRESS_RANGE;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  fact.section_index = 0U;
  fact.offset = 0x20U;
  fact.has_runtime_address = 1U;
  fact.runtime_kind = M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY;
  fact.runtime_address = 0x64U;
  fact.size = 16U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_RUNTIME_ADDRESS_REF;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  fact.section_index = 0U;
  fact.offset = 0U;
  fact.target_section_index = 0U;
  fact.target_offset = 0x10U;
  fact.has_runtime_address = 1U;
  fact.runtime_address = 4U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_RUNTIME_ADDRESS_REF;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  fact.section_index = 0U;
  fact.offset = 0x10U;
  fact.target_section_index = 0U;
  fact.target_offset = 0x20U;
  fact.has_runtime_address = 1U;
  fact.runtime_address = 0x64U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  M68K_C_ASSERT_INT(0, m68k_render_ir_preview_build(&object, &decode, &facts, NULL,
    accepted_start, accepted_bytes, 0, 1, 1, 1, &preview, NULL));
  M68K_C_ASSERT(preview.asm_source_text != NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "    ORG $4\n") == NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "runtime_code_00000004\tEQU\t$4\n") != NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "\tjmp runtime_code_00000004.l\n") != NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "loc_0_00000010:\n\tjmp abs_0_00000064.l\n") != NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "loc_0_00000020:\n    ORG $64\nabs_0_00000064:\n") != NULL);
  M68K_C_ASSERT_U32(0U, preview.asm_source_instruction_render_failures);
  m68k_render_ir_preview_destroy(&preview);
  m68k_fact_ir_destroy(&facts);
  m68k_decode_ir_destroy(&decode);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_policy_runtime_entrypoint_maps_absolute_load(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[20] = {
    0x4eu, 0xb9u, 0x00u, 0x00u, 0x04u, 0x10u,
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0x400U;
  policy.runtime_entry_point_count = 1U;
  policy.runtime_entry_points[0].has_section_index = 1U;
  policy.runtime_entry_points[0].section_index = 0U;
  policy.runtime_entry_points[0].runtime_address = 0x400U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "runtime_") == NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr abs_0_00000410.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $400\nabs_0_00000400:\n\tjsr abs_0_00000410.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000410:\n\tnop\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr $00000410.l\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_full_policy_load_view_materializes_without_runtime_entrypoint(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[6] = {0x4eu, 0xf9u, 0x00u, 0x04u, 0x00u, 0x00u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0x40000U;
  policy.has_entry_offset = 1U;
  policy.entry_offset = 0U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $40000\nabs_0_00040000:\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp abs_0_00040000.l\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_full_load_view_does_not_label_alternate_copied_address_with_addend(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kDecodeIR decode;
  M68kFactIR facts;
  M68kRenderIRPreview preview;
  M68kFact fact;
  uint8_t *accepted_start[1];
  uint8_t *accepted_bytes[1];
  uint8_t start_map[18];
  uint8_t byte_map[18];
  uint8_t bytes[18] = {
    0x43u, 0xf9u, 0x00u, 0x00u, 0x04u, 0x00u,
    0x4eu, 0x75u,
    0x4eu, 0x75u,
    0x4eu, 0x71u,
    0x4eu, 0x71u,
    0x4eu, 0x71u,
    0x4eu, 0x71u
  };
  memset(&section, 0, sizeof(section));
  memset(start_map, 0, sizeof(start_map));
  memset(byte_map, 0, sizeof(byte_map));
  accepted_start[0] = start_map;
  accepted_bytes[0] = byte_map;
  start_map[0] = 1U;
  memset(&byte_map[0], 1, 8U);
  start_map[8] = 1U;
  memset(&byte_map[8], 1, 2U);
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_decode_ir_init(&decode);
  m68k_fact_ir_init(&facts);
  m68k_render_ir_preview_init(&preview);
  M68K_C_ASSERT_INT(0, m68k_decode_ir_build_object(&decode, &object, M68K_ASM_CPU_68060,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(0, m68k_fact_ir_create_label(&facts, 0U, 0U, M68K_FACT_CONFIDENCE_TOOL_INFERRED));
  M68K_C_ASSERT_INT(0, m68k_fact_ir_create_label(&facts, 0U, 8U, M68K_FACT_CONFIDENCE_TOOL_INFERRED));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_RUNTIME_ADDRESS_RANGE;
  fact.confidence = M68K_FACT_CONFIDENCE_REQUIRED;
  fact.section_index = 0U;
  fact.offset = 0U;
  fact.has_runtime_address = 1U;
  fact.runtime_kind = M68K_FACT_RUNTIME_RANGE_KIND_POLICY;
  fact.runtime_address = 0x70000U;
  fact.size = sizeof(bytes);
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_RUNTIME_ADDRESS_RANGE;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  fact.section_index = 0U;
  fact.offset = 8U;
  fact.has_runtime_address = 1U;
  fact.runtime_kind = M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY;
  fact.runtime_address = 0x400U;
  fact.size = 2U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_CODE_START;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  fact.section_index = 0U;
  fact.offset = 8U;
  fact.reason = M68K_FACT_CODE_START_REASON_CONTROL_TARGET;
  fact.has_runtime_address = 1U;
  fact.runtime_address = 0x400U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_RUNTIME_ADDRESS_REF;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  fact.section_index = 0U;
  fact.offset = 0U;
  fact.reason = 0U;
  fact.target_section_index = 0U;
  fact.target_offset = 8U;
  fact.has_runtime_address = 1U;
  fact.runtime_address = 0x400U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  M68K_C_ASSERT_INT(0, m68k_render_ir_preview_build(&object, &decode, &facts, NULL,
    accepted_start, accepted_bytes, 0, 1, 1, 1, &preview, NULL));
  M68K_C_ASSERT(preview.asm_source_text != NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "    ORG $70000\n") != NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "runtime_code_00000400\tEQU\t$400\n") != NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "\tlea.l runtime_code_00000400.l,a1\n") != NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "abs_0_00070008-") == NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "    ORG $400\n") == NULL);
  M68K_C_ASSERT_U32(0U, preview.asm_source_instruction_render_failures);
  m68k_render_ir_preview_destroy(&preview);
  m68k_fact_ir_destroy(&facts);
  m68k_decode_ir_destroy(&decode);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_runtime_ref_inside_accepted_instruction_stays_numeric(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[56] = {
    0x20u, 0x7cu, 0x00u, 0x00u, 0x01u, 0x32u,
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x30u, 0x3cu, 0x12u, 0x34u,
    0x4eu, 0x75u,
    0x00u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0x100U;
  policy.runtime_entry_point_count = 2U;
  policy.runtime_entry_points[0].has_section_index = 1U;
  policy.runtime_entry_points[0].section_index = 0U;
  policy.runtime_entry_points[0].runtime_address = 0x100U;
  policy.runtime_entry_points[1].has_section_index = 1U;
  policy.runtime_entry_points[1].section_index = 0U;
  policy.runtime_entry_points[1].runtime_address = 0x130U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l #$132,a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000132") == NULL);
  M68K_C_ASSERT(strstr(source, "+$") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_pointer_table_storage_value_stays_numeric_under_runtime_org(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[20] = {
    0x00u, 0x00u, 0x00u, 0x10u,
    0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.structured_data_item_count = 1U;
  policy.structured_data_items[0].has_section_index = 1U;
  policy.structured_data_items[0].section_index = 0U;
  policy.structured_data_items[0].offset = 0U;
  policy.structured_data_items[0].size = 4U;
  policy.structured_data_items[0].kind = M68K_ANALYSIS_STRUCTURED_DATA_LONGS;
  snprintf(policy.structured_data_items[0].semantic_role,
    sizeof(policy.structured_data_items[0].semantic_role), "pointer_table");
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0x10U;
  policy.runtime_ranges[0].size = 4U;
  policy.runtime_ranges[0].runtime_address = 0x80U;
  policy.runtime_entry_point_count = 1U;
  policy.runtime_entry_points[0].has_section_index = 1U;
  policy.runtime_entry_points[0].section_index = 0U;
  policy.runtime_entry_points[0].runtime_address = 0x80U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l $00000010\t; pointer_table\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l abs_0_00000080") == NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $80\nabs_0_00000080:\n\tnop\n\trts\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_pointer_table_runtime_data_targets_get_labels(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[24] = {
    0x00u, 0x00u, 0x00u, 0x84u,
    0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x75u,
    0x12u, 0x34u, 0x56u, 0x78u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.disable_implicit_entry_points = 1U;
  policy.structured_data_item_count = 1U;
  policy.structured_data_items[0].has_section_index = 1U;
  policy.structured_data_items[0].section_index = 0U;
  policy.structured_data_items[0].offset = 0U;
  policy.structured_data_items[0].size = 4U;
  policy.structured_data_items[0].kind = M68K_ANALYSIS_STRUCTURED_DATA_LONGS;
  snprintf(policy.structured_data_items[0].semantic_role,
    sizeof(policy.structured_data_items[0].semantic_role), "pointer_table");
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0x10U;
  policy.runtime_ranges[0].size = 8U;
  policy.runtime_ranges[0].runtime_address = 0x80U;
  policy.runtime_entry_point_count = 1U;
  policy.runtime_entry_points[0].has_section_index = 1U;
  policy.runtime_entry_points[0].section_index = 0U;
  policy.runtime_entry_points[0].runtime_address = 0x80U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l abs_0_00000084\t; pointer_table\n") != NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000084:\n\tdc.b $12,$34,$56,$78\n") != NULL);
  M68K_C_ASSERT(strstr(source, "ORG $4") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_absolute_long_lookup_table_renders_labels_and_nulls(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[24] = {
    0x00u, 0x00u, 0x00u, 0x10u,
    0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x12u,
    0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x75u,
    0x4eu, 0x71u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.structured_data_item_count = 1U;
  policy.structured_data_items[0].has_section_index = 1U;
  policy.structured_data_items[0].section_index = 0U;
  policy.structured_data_items[0].offset = 0U;
  policy.structured_data_items[0].size = 12U;
  policy.structured_data_items[0].kind = M68K_ANALYSIS_STRUCTURED_DATA_LONGS;
  snprintf(policy.structured_data_items[0].semantic_role,
    sizeof(policy.structured_data_items[0].semantic_role), "lookup_table");
  policy.entry_point_count = 2U;
  policy.entry_points[0].has_section_index = 1U;
  policy.entry_points[0].section_index = 0U;
  policy.entry_points[0].offset = 0x10U;
  policy.entry_points[1].has_section_index = 1U;
  policy.entry_points[1].section_index = 0U;
  policy.entry_points[1].offset = 0x12U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tdc.l loc_0_00000010,$00000000,loc_0_00000012\t; lookup_table\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l $00000010,$00000000,$00000012") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_word_lookup_table_mixes_labels_and_raw_without_duplicate_fallback(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[16] = {
    0x00u, 0x00u, 0x00u, 0x04u, 0x22u, 0x22u,
    0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x75u,
    0x4eu, 0x71u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.structured_data_item_count = 1U;
  policy.structured_data_items[0].has_section_index = 1U;
  policy.structured_data_items[0].section_index = 0U;
  policy.structured_data_items[0].offset = 0U;
  policy.structured_data_items[0].size = 6U;
  policy.structured_data_items[0].kind = M68K_ANALYSIS_STRUCTURED_DATA_WORDS;
  policy.structured_data_items[0].has_target = 1U;
  policy.structured_data_items[0].target_section = 0U;
  policy.structured_data_items[0].target_offset = 8U;
  snprintf(policy.structured_data_items[0].semantic_role,
    sizeof(policy.structured_data_items[0].semantic_role), "lookup_table");
  policy.entry_point_count = 2U;
  policy.entry_points[0].has_section_index = 1U;
  policy.entry_points[0].section_index = 0U;
  policy.entry_points[0].offset = 8U;
  policy.entry_points[1].has_section_index = 1U;
  policy.entry_points[1].section_index = 0U;
  policy.entry_points[1].offset = 12U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tdc.w loc_0_00000008-loc_0_00000008,loc_0_0000000C-loc_0_00000008,$2222\t; lookup_table\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w $0000,$0004,$2222") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_policy_runtime_range_uses_first_class_labels(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t bytes[20] = {
    0x4eu, 0xb9u, 0x00u, 0x00u, 0x04u, 0x10u,
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0x400U;
  policy.runtime_entry_point_count = 1U;
  policy.runtime_entry_points[0].has_section_index = 1U;
  policy.runtime_entry_points[0].section_index = 0U;
  policy.runtime_entry_points[0].runtime_address = 0x400U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy,
    &source, &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "runtime_") == NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr abs_0_00000410.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $400\nabs_0_00000400:\n\tjsr abs_0_00000410.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000410:\n\tnop\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr $00000410.l\n") == NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000010+$") == NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000010+1024") == NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000410 EQU") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_runtime_alias_refs_emit_first_class_labels(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[20] = {
    0x4eu, 0xb9u, 0x00u, 0x00u, 0x04u, 0x10u,
    0x4eu, 0xb9u, 0x00u, 0x00u, 0x08u, 0x10u,
    0x4eu, 0x75u,
    0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 2U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0x400U;
  policy.runtime_ranges[1].has_section_index = 1U;
  policy.runtime_ranges[1].section_index = 0U;
  policy.runtime_ranges[1].offset = 0U;
  policy.runtime_ranges[1].size = sizeof(bytes);
  policy.runtime_ranges[1].runtime_address = 0x800U;
  policy.runtime_entry_point_count = 1U;
  policy.runtime_entry_points[0].has_section_index = 1U;
  policy.runtime_entry_points[0].section_index = 0U;
  policy.runtime_entry_points[0].runtime_address = 0x400U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr abs_0_00000410.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr abs_0_00000810.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000410:\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $810\nabs_0_00000810:\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000010+$") == NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000810 EQU") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_policy_runtime_entrypoint_starts_inside_view(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[20] = {
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0x400U;
  policy.runtime_entry_point_count = 1U;
  policy.runtime_entry_points[0].has_section_index = 1U;
  policy.runtime_entry_points[0].section_index = 0U;
  policy.runtime_entry_points[0].runtime_address = 0x410U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $400\n") != NULL);
  M68K_C_ASSERT(strstr(source, "abs_0_00000410:\n\tnop\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000010:\n\tnop\n\trts\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_runtime_range_conflict_fails_instead_of_last_map(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[8] = {0x4eu, 0x71u, 0x4eu, 0x71u, 0x4eu, 0x71u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 2U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = 4U;
  policy.runtime_ranges[0].runtime_address = 0x400U;
  policy.runtime_ranges[1].has_section_index = 1U;
  policy.runtime_ranges[1].section_index = 0U;
  policy.runtime_ranges[1].offset = 2U;
  policy.runtime_ranges[1].size = 4U;
  policy.runtime_ranges[1].runtime_address = 0x400U;
  M68K_C_ASSERT_INT(-1, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source == NULL);
  M68K_C_ASSERT_U32(1U, profile.runtime_address_range_conflicts);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_tool_inferred_runtime_copy_conflict_does_not_abort(void) {
  AsmSourceFile parsed_source;
  M68kDiagList diagnostics;
  M68kObject object;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  char *analysis_json = NULL;
  size_t runtime_view_index;
  int found_conflicting_copy = 0;
  const char *source_text =
    "SECTION section_0,code\n"
    "\tlea source1(pc),a0\n"
    "\tmovea.l #$400,a1\n"
    "\tmoveq #1,d0\n"
    "\tmove.l (a0)+,(a1)+\n"
    "\tlea source2(pc),a0\n"
    "\tmovea.l #$400,a1\n"
    "\tmoveq #1,d0\n"
    "\tmove.l (a0)+,(a1)+\n"
    "\trts\n"
    "source1:\n"
    "\tdc.l $11111111,$22222222\n"
    "source2:\n"
    "\tdc.l $33333333,$44444444\n";
  memset(&parsed_source, 0, sizeof(parsed_source));
  memset(&object, 0, sizeof(object));
  m68k_diag_list_reset(&diagnostics);
  parsed_source.target_cpu = M68K_ASM_CPU_68000;
  M68K_C_ASSERT(m68k_source_pipeline_parse_text_and_layout(&parsed_source, source_text,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_INT(1, m68k_source_pipeline_emit_object(&parsed_source, &object,
    m68k_diag_sink(&diagnostics)));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  m68k_analysis_policy_init_default(&policy);
  memset(&source_analysis, 0, sizeof(source_analysis));
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT_U32(1U, profile.runtime_address_range_conflicts);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &source_analysis, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(1U, profile.runtime_address_range_conflicts);
  M68K_C_ASSERT(source_analysis.section_count == 1U);
  for (runtime_view_index = 0U; runtime_view_index < source_analysis.sections[0].runtime_view_count;
       ++runtime_view_index) {
    const M68kRuntimeViewIR *view = &source_analysis.sections[0].runtime_views[runtime_view_index];
    if (view->kind == M68K_FACT_RUNTIME_RANGE_KIND_CONFLICTING_DISCOVERED_COPY &&
        view->runtime_address == 0x400U && view->size == 8U) {
      M68K_C_ASSERT_U32(0U, view->materialized);
      M68K_C_ASSERT_U32(M68K_RUNTIME_VIEW_SUPPRESSED_CONFLICTING_DISCOVERED_COPY,
        view->materialization_reason);
      found_conflicting_copy = 1;
    }
  }
  M68K_C_ASSERT(found_conflicting_copy);
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"record_kind\":\"runtime_view\",\"memory_kind\":\"runtime_view_candidate\",\"section_index\":0") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"runtime_address\":1024,\"runtime_size\":8") != NULL);
  free(analysis_json);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  m68k_source_model_free(&parsed_source);
  return 0;
}

static int test_facts_v2_policy_runtime_range_wins_over_inferred_copy_conflict(void) {
  AsmSourceFile parsed_source;
  M68kDiagList diagnostics;
  M68kObject object;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  const char *source_text =
    "SECTION section_0,code\n"
    "\tlea payload(pc),a0\n"
    "\tmovea.l #$400,a1\n"
    "\tmoveq #1,d0\n"
    "\tmove.l (a0)+,(a1)+\n"
    "\trts\n"
    "payload:\n"
    "\tdc.l $11111111,$22222222\n";
  memset(&parsed_source, 0, sizeof(parsed_source));
  memset(&object, 0, sizeof(object));
  m68k_diag_list_reset(&diagnostics);
  parsed_source.target_cpu = M68K_ASM_CPU_68000;
  M68K_C_ASSERT(m68k_source_pipeline_parse_text_and_layout(&parsed_source, source_text,
    m68k_diag_sink(&diagnostics)));
  M68K_C_ASSERT_INT(1, m68k_source_pipeline_emit_object(&parsed_source, &object,
    m68k_diag_sink(&diagnostics)));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = (uint32_t)object.sections[0].size;
  policy.runtime_ranges[0].runtime_address = 0x400U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT_U32(1U, profile.runtime_address_range_conflicts);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  m68k_source_model_free(&parsed_source);
  return 0;
}

static int test_facts_v2_render_asm_source_preserves_exact_byte_immediate_word(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[6] = {0x00u, 0x24u, 0xdeu, 0x92u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "ori.b #$DE92,-(a4)") != NULL);
  M68K_C_ASSERT(strstr(source, "ori.b #146,-(a4)") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_render_failures);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_preserves_move_byte_immediate_high_word(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[6] = {0x10u, 0x3cu, 0xffu, 0x80u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "move.b #$FF80,d0") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_formats_all_bits_set_long_immediate_as_hex(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[8] = {0x0cu, 0x95u, 0xffu, 0xffu, 0xffu, 0xffu, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "cmpi.l #$FFFFFFFF,(a5)") != NULL);
  M68K_C_ASSERT(strstr(source, "#4294967295") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_refuses_unmapped_code_relocation(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[4] = {0x70u, 0x00u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 1U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_8;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(-1, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source == NULL);
  M68K_C_ASSERT_U32(1U, profile.asm_source_enabled);
  M68K_C_ASSERT_U32(1U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(1U, profile.asm_source_instruction_relocation_failures);
  M68K_C_ASSERT_U32(M68K_RENDER_IR_ASM_SOURCE_FAILURE_INSTRUCTION_RELOCATION,
    profile.asm_source_first_failure_kind);
  M68K_C_ASSERT_U32(0U, profile.asm_source_first_failure_section);
  M68K_C_ASSERT_U32(0U, profile.asm_source_first_failure_offset);
  M68K_C_ASSERT_U32(1U, profile.asm_source_first_failure_aux_offset);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_maps_immediate_code_relocation(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[8] = {0x20u, 0x3cu, 0x00u, 0x00u, 0x00u, 0x06u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 2U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "#loc_0_00000006") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_relocation_failures);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  M68K_C_ASSERT_U32(M68K_RENDER_IR_ASM_SOURCE_FAILURE_NONE, profile.asm_source_first_failure_kind);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_maps_relocation_after_imm_operand(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[12] = {
    0x00u, 0xb9u, 0x00u, 0x00u, 0x00u, 0x10u, 0x00u, 0x00u, 0x00u, 0x0au, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 6U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "ori.l #16,loc_0_0000000A.l") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_relocation_failures);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_maps_bss_relocation_label(void) {
  M68kObject object;
  M68kSection code_section;
  M68kSection bss_section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[8] = {0x20u, 0x3cu, 0x00u, 0x00u, 0x00u, 0x04u, 0x4eu, 0x75u};
  memset(&code_section, 0, sizeof(code_section));
  memset(&bss_section, 0, sizeof(bss_section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  code_section.kind = M68K_SECTION_CODE;
  code_section.size = sizeof(bytes);
  code_section.data_size = sizeof(bytes);
  code_section.data = bytes;
  added = m68k_object_add_section(&object, &code_section);
  M68K_C_ASSERT(added.ok);
  bss_section.kind = M68K_SECTION_BSS;
  bss_section.size = 0x10U;
  bss_section.data_size = 0U;
  bss_section.data = NULL;
  added = m68k_object_add_section(&object, &bss_section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 2U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 1U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "#loc_1_00000004") != NULL);
  M68K_C_ASSERT(strstr(source, "    SECTION section_1,bss,$10") != NULL);
  M68K_C_ASSERT(strstr(source, "DS.L $1") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_1_00000004:") != NULL);
  M68K_C_ASSERT(strstr(source, "DS.L $3") != NULL);
  M68K_C_ASSERT(strstr(source, "facts_v2 uninitialized") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.relocation_failures);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_relocation_failures);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_renders_pure_bss_as_ds_reserve(void) {
  M68kObject object;
  M68kSection code_section;
  M68kSection bss_section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[2] = {0x4eu, 0x75u};
  memset(&code_section, 0, sizeof(code_section));
  memset(&bss_section, 0, sizeof(bss_section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  code_section.kind = M68K_SECTION_CODE;
  code_section.size = sizeof(bytes);
  code_section.data_size = sizeof(bytes);
  code_section.data = bytes;
  added = m68k_object_add_section(&object, &code_section);
  M68K_C_ASSERT(added.ok);
  bss_section.kind = M68K_SECTION_BSS;
  bss_section.size = 0x14U;
  bss_section.data_size = 0U;
  bss_section.data = NULL;
  added = m68k_object_add_section(&object, &bss_section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "    SECTION section_1,bss,$14") != NULL);
  M68K_C_ASSERT(strstr(source, "DS.L $5") != NULL);
  M68K_C_ASSERT(strstr(source, "DS.B $14") == NULL);
  M68K_C_ASSERT(strstr(source, "facts_v2 uninitialized") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_symbols_amiga_loadseg_segment_link(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[6] = {0x43u, 0xFAu, 0xFFu, 0xFAu, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "amiga_loadseg_segment_link\tEQU\t-4") != NULL);
  M68K_C_ASSERT(strstr(source, "lea.l amiga_loadseg_segment_link(pc),a1") != NULL);
  M68K_C_ASSERT(strstr(source, "lea.l -$6(pc),a1") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_demotes_speculative_unencodable_instruction(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t bytes[6] = {0x4eu, 0x71u, 0xf0u, 0x9cu, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT_U32(1U, profile.accepted_instructions);
  M68K_C_ASSERT_U32(1U, profile.unsupported_instruction_demotes);
  M68K_C_ASSERT_U32(0U, profile.first_unsupported_instruction_demote_section);
  M68K_C_ASSERT_U32(2U, profile.first_unsupported_instruction_demote_offset);
  M68K_C_ASSERT_U32(M68K_FACTS_V2_CODE_START_REASON_FALLTHROUGH,
    profile.first_unsupported_instruction_demote_reason);
  M68K_C_ASSERT_U32(0U, profile.first_unsupported_instruction_demote_source_section);
  M68K_C_ASSERT_U32(0U, profile.first_unsupported_instruction_demote_source_offset);
  M68K_C_ASSERT_U32(1U, profile.code_start_section_entries);
  M68K_C_ASSERT_U32(1U, profile.code_start_fallthroughs);
  M68K_C_ASSERT_U32(0U, profile.required_instruction_failures);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  M68K_C_ASSERT_U32(1U, source_analysis.sections[0].violation_count);
  M68K_C_ASSERT_U32(2U, source_analysis.sections[0].violations[0].offset);
  M68K_C_ASSERT_U32(M68K_VIOLATION_DECODE_FAILED_REACHABLE, source_analysis.sections[0].violations[0].kind);
  M68K_C_ASSERT(strstr(source_analysis.sections[0].violations[0].message,
    "fallthrough code candidate at $0002 rejected after source $0000; emitted as data") != NULL);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_demotes_speculative_reserved_full_extension(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  uint8_t bytes[8] = {0x4eu, 0x71u, 0x44u, 0x33u, 0x33u, 0x44u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  _putenv_s("AMIGA_REVERSING_FACTS_V2_ASM_SOURCE", "1");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)));
  _putenv_s("AMIGA_REVERSING_FACTS_V2_ASM_SOURCE", "");
  M68K_C_ASSERT_U32(1U, profile.accepted_instructions);
  M68K_C_ASSERT_U32(1U, profile.unsupported_instruction_demotes);
  M68K_C_ASSERT_U32(0U, profile.first_unsupported_instruction_demote_section);
  M68K_C_ASSERT_U32(2U, profile.first_unsupported_instruction_demote_offset);
  M68K_C_ASSERT_U32(0U, profile.required_instruction_failures);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_required_unencodable_instruction_is_hard_failure(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[4] = {0xf0u, 0x9cu, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  _putenv_s("AMIGA_REVERSING_FACTS_V2_ASM_SOURCE", "1");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)));
  _putenv_s("AMIGA_REVERSING_FACTS_V2_ASM_SOURCE", "");
  M68K_C_ASSERT_U32(1U, profile.required_instruction_failures);
  M68K_C_ASSERT_U32(0U, profile.first_required_instruction_failure_section);
  M68K_C_ASSERT_U32(0U, profile.first_required_instruction_failure_offset);
  M68K_C_ASSERT_U32(M68K_FACTS_V2_CODE_START_REASON_SECTION_ENTRY,
    profile.first_required_instruction_failure_reason);
  M68K_C_ASSERT_U32(0U, profile.first_required_instruction_failure_source_section);
  M68K_C_ASSERT_U32(0U, profile.first_required_instruction_failure_source_offset);
  M68K_C_ASSERT_U32(0U, profile.unsupported_instruction_demotes);
  M68K_C_ASSERT_U32(1U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  M68K_C_ASSERT_INT(-1, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source == NULL);
  M68K_C_ASSERT_U32(1U, profile.required_instruction_failures);
  M68K_C_ASSERT_U32(1U, profile.asm_source_refused);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_reencodes_restricted_ea_instruction(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[4] = {0xb3u, 0x88u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "cmpm.l (a0)+,(a1)+") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  M68K_C_ASSERT_U32(2U, profile.asm_source_symbolic_instructions);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_renders_policy_entry_comment(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[2] = {0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.entry_comment_count = 1U;
  policy.entry_comments[0].has_section_index = 1U;
  policy.entry_comments[0].section_index = 0U;
  policy.entry_comments[0].offset = 0U;
  snprintf(policy.entry_comments[0].comment, sizeof(policy.entry_comments[0].comment),
    "KNOWN: base A6=exec.library:LIB");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "    ; KNOWN: base A6=exec.library:LIB\nloc_0_00000000:") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_renders_policy_register_seed_comment(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[2] = {0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  snprintf(policy.register_seeds[0].type_name, sizeof(policy.register_seeds[0].type_name), "LIB");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "    ; KNOWN: base A6=exec.library:LIB\nloc_0_00000000:") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_renders_seeded_lvo_symbol(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[6] = {0x4eu, 0xaeu, 0xffu, 0x94u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOAlert(a6)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_symbols_amiga_hardware_registers(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  const char *section_line;
  const char *custom_include_line;
  const char *intf_decl_line;
  uint8_t bytes[] = {
    0x41u, 0xF9u, 0x00u, 0xDFu, 0xF0u, 0x00u,
    0x31u, 0x7Cu, 0x7Fu, 0xFFu, 0x00u, 0x9Au,
    0x31u, 0x7Cu, 0xC0u, 0x00u, 0x00u, 0x9Au,
    0x31u, 0x7Cu, 0x82u, 0x00u, 0x00u, 0x96u,
    0x31u, 0x7Cu, 0x7Fu, 0xFFu, 0x00u, 0x96u,
    0x31u, 0x7Cu, 0x7Fu, 0xFFu, 0x00u, 0x9Eu,
    0x31u, 0x7Cu, 0x00u, 0x40u, 0x00u, 0xA4u,
    0x31u, 0x7Cu, 0x01u, 0x23u, 0x00u, 0xA6u,
    0x31u, 0x7Cu, 0x00u, 0x40u, 0x00u, 0xA8u,
    0x33u, 0xFCu, 0x12u, 0x34u, 0x00u, 0xDFu, 0xF0u, 0xA4u,
    0x33u, 0xFCu, 0x42u, 0x00u, 0x00u, 0xDFu, 0xF1u, 0x00u,
    0x33u, 0xFCu, 0x00u, 0x24u, 0x00u, 0xDFu, 0xF1u, 0x04u,
    0x33u, 0xFCu, 0x00u, 0x20u, 0x00u, 0xDFu, 0xF1u, 0xDCu,
    0x33u, 0xFCu, 0x1Eu, 0x12u, 0x00u, 0xDFu, 0xF0u, 0x58u,
    0x31u, 0x7Cu, 0x1Eu, 0x12u, 0x00u, 0x58u,
    0x33u, 0xFCu, 0x00u, 0x40u, 0x00u, 0xDFu, 0xF0u, 0x58u,
    0x33u, 0xFCu, 0x00u, 0x01u, 0x00u, 0xDFu, 0xF0u, 0x58u,
    0x31u, 0x7Cu, 0x00u, 0x00u, 0x01u, 0x02u,
    0x31u, 0x7Cu, 0x44u, 0x89u, 0x00u, 0x7Eu,
    0x33u, 0xC0u, 0x00u, 0xDFu, 0xF0u, 0xA6u,
    0x33u, 0xD0u, 0x00u, 0xDFu, 0xF0u, 0xAAu,
    0x30u, 0x39u, 0x00u, 0xDFu, 0xF0u, 0x0Au,
    0x30u, 0x39u, 0x00u, 0xDFu, 0xF0u, 0x0Cu,
    0x30u, 0x39u, 0x00u, 0xDFu, 0xF0u, 0x1Eu,
    0x23u, 0xC8u, 0x00u, 0xDFu, 0xF1u, 0x80u,
    0x21u, 0xFCu, 0x12u, 0x34u, 0x56u, 0x78u, 0x00u, 0x6Cu,
    0x33u, 0xC0u, 0x00u, 0xDFu, 0xF1u, 0x9Eu,
    0x31u, 0x40u, 0x00u, 0xE2u,
    0x31u, 0x40u, 0x01u, 0x3Eu,
    0x43u, 0xF8u, 0x00u, 0x60u,
    0x41u, 0xF9u, 0x00u, 0x00u, 0x00u, 0x10u,
    0x22u, 0x39u, 0x00u, 0x00u, 0x00u, 0x10u,
    0x2Cu, 0x78u, 0x00u, 0x04u,
    0x4Eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  section_line = strstr(source, "    SECTION");
  custom_include_line = strstr(source, "INCLUDE \"hardware/custom.i\"");
  intf_decl_line = strstr(source, "INTF_CLRALL\tEQU\t$7FFF");
  M68K_C_ASSERT(section_line != NULL);
  M68K_C_ASSERT(custom_include_line != NULL && custom_include_line < section_line);
  M68K_C_ASSERT(intf_decl_line != NULL && intf_decl_line < section_line);
  M68K_C_ASSERT(strstr(source, "INCLUDE \"hardware/custom.i\"") != NULL);
  M68K_C_ASSERT(strstr(source, "INCLUDE \"hardware/dmabits.i\"") != NULL);
  M68K_C_ASSERT(strstr(source, "INCLUDE \"hardware/intbits.i\"") != NULL);
  M68K_C_ASSERT(strstr(source, "INCLUDE \"graphics/display.i\"") != NULL);
  M68K_C_ASSERT(strstr(source, "_custom\tEQU\t$DFF000") != NULL);
  M68K_C_ASSERT(strstr(source, "ADKF_CLRALL\tEQU\t$7FFF") != NULL);
  M68K_C_ASSERT(strstr(source, "BEAMCON0_PAL\tEQU\t$20") != NULL);
  M68K_C_ASSERT(strstr(source, "BPLCON2_PF1P2\tEQU\t$4") != NULL);
  M68K_C_ASSERT(strstr(source, "BPLCON2_PF2P2\tEQU\t$20") != NULL);
  M68K_C_ASSERT(strstr(source, "DMAF_CLRALL\tEQU\t$7FFF") != NULL);
  M68K_C_ASSERT(strstr(source, "INTF_CLRALL\tEQU\t$7FFF") != NULL);
  M68K_C_ASSERT(strstr(source, "m68k_vector_level_3_interrupt_autovector\tEQU\t$6C") != NULL);
  M68K_C_ASSERT(strstr(source, "BPLCON0_") == NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l _custom.l,a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #INTF_CLRALL,intena(a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #INTF_SETCLR|INTF_INTEN,intena(a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #DMAF_SETCLR|DMAF_MASTER,dmacon(a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #DMAF_CLRALL,dmacon(a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #ADKF_CLRALL,adkcon(a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #$40,aud0+ac_len(a0)\t; sound sample length 128 bytes\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #$123,aud0+ac_per(a0)\t; audio period 291\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #$40,aud0+ac_vol(a0)\t; audio volume 64\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.w #$1234,_custom+aud0+ac_len.l\t; sound sample length 9320 bytes\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.w #(4<<PLNCNTSHFT)|COLORON,_custom+bplcon0.l\t; display 4 bitplanes lores color\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.w #BPLCON2_PF2P2|BPLCON2_PF1P2,_custom+bplcon2.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #BEAMCON0_PAL,_custom+beamcon0.l\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.w #(120<<6)|18,_custom+bltsize.l\t; blitter size 120 rows x 18 words (36 bytes/row)\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.w #(120<<6)|18,bltsize(a0)\t; blitter size 120 rows x 18 words (36 bytes/row)\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.w #(1<<6)|0,_custom+bltsize.l\t; blitter size 1 rows x 64 words (128 bytes/row)\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.w #(0<<6)|1,_custom+bltsize.l\t; blitter size 1024 rows x 1 words (2 bytes/row)\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.w #$0,bplcon1(a0)\t; display scroll pf1=0 pf2=0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #$4489,dsksync(a0)\t; disk sync word $4489\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w d0,_custom+aud0+ac_per.l\t; audio period\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w (a0),_custom+aud0+ac_dat.l\t; audio data word\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.l #$12345678,m68k_vector_level_3_interrupt_autovector.w\n") != NULL);
  M68K_C_ASSERT(strstr(source, "m68k_vector_spurious_interrupt\tEQU\t$60") != NULL);
  M68K_C_ASSERT(strstr(source, "m68k_vector_illegal_instruction\tEQU\t$10") != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l m68k_vector_spurious_interrupt.w,a1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l $00000010.l,a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l m68k_vector_illegal_instruction.l,d1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w d0,_custom+color+$1E.l\t; palette color 15\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l a0,_custom+color.l\t; palette colors 0-1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w _custom+joy0dat.l,d0\t; joystick/mouse port 0 data\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w _custom+joy1dat.l,d0\t; joystick/mouse port 1 data\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w _custom+intreqr.l,d0\t; interrupt request state\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w d0,bplpt+$02(a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w d0,sprpt+$1E(a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l $0004.w,a6\n") != NULL);
  M68K_C_ASSERT(strstr(source, "m68k_vector_initial_pc") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_amiga_runtime_address_sinks_are_generated_from_hardware_metadata(void) {
  char symbol_expr[64];
  const AmigaOsHardwareRegisterInfo *cop1lc =
    amiga_os_find_hardware_register_by_cpu_address(0x00DFF080U);
  const AmigaOsHardwareRegisterInfo *intena =
    amiga_os_find_hardware_register_by_cpu_address(0x00DFF09AU);
  const AmigaOsHardwareRegisterInfo *dskpt =
    amiga_os_find_hardware_register_by_cpu_address(0x00DFF020U);
  const AmigaOsHardwareRegisterInfo *bltcpt =
    amiga_os_find_hardware_register_by_cpu_address(0x00DFF048U);
  const AmigaOsHardwareRegisterInfo *bltdpt =
    amiga_os_find_hardware_register_by_cpu_address(0x00DFF054U);
  const AmigaOsHardwareRegisterInfo *aud0 =
    amiga_os_find_hardware_register_by_cpu_address(0x00DFF0A0U);
  const AmigaOsHardwareRegisterInfo *bplpt =
    amiga_os_find_hardware_register_by_cpu_address(0x00DFF0E0U);
  const AmigaOsHardwareRegisterInfo *sprpt =
    amiga_os_find_hardware_register_by_cpu_address(0x00DFF120U);
  const AmigaOsHardwareRegisterFieldInfo *aud0_len =
    amiga_os_find_hardware_register_field_by_cpu_address(0x00DFF0A4U);
  const AmigaOsHardwareRegisterFieldInfo *aud0_len_by_base =
    amiga_os_find_hardware_register_field_by_base_offset("_custom", 0x00A4U);
  const AmigaOsHardwareRegisterFieldInfo *spr1_dataa =
    amiga_os_find_hardware_register_field_by_base_offset("_custom", 0x014CU);
  const AmigaOsHardwareRegisterRangeInfo *spr_range =
    amiga_os_find_hardware_register_range_by_base_offset("_custom", 0x014CU);
  const AmigaOsHardwareRegisterRangeInfo *bplpt_tail =
    amiga_os_find_hardware_register_range_by_base_offset("_custom", 0x00E2U);
  const AmigaOsHardwareRegisterRangeInfo *bplpt_past_end =
    amiga_os_find_hardware_register_range_by_base_offset("_custom", 0x00F8U);
  const AmigaOsHardwareRegisterRangeInfo *sprpt_tail =
    amiga_os_find_hardware_register_range_by_base_offset("_custom", 0x013EU);
  const AmigaOsHardwareRegisterRangeInfo *sprpt_past_end =
    amiga_os_find_hardware_register_range_by_base_offset("_custom", 0x0140U);
  const AmigaOsHardwareRegisterRangeInfo *aud0_len_as_range =
    amiga_os_find_hardware_register_range_by_base_offset("_custom", 0x00A4U);
  M68K_C_ASSERT(cop1lc != NULL);
  M68K_C_ASSERT(dskpt != NULL);
  M68K_C_ASSERT(bltcpt != NULL);
  M68K_C_ASSERT(bltdpt != NULL);
  M68K_C_ASSERT(aud0 != NULL);
  M68K_C_ASSERT(bplpt != NULL);
  M68K_C_ASSERT(sprpt != NULL);
  M68K_C_ASSERT(intena != NULL);
  M68K_C_ASSERT(aud0_len != NULL);
  M68K_C_ASSERT(aud0_len_by_base == aud0_len);
  M68K_C_ASSERT_STR("aud", aud0_len->register_symbol);
  M68K_C_ASSERT_STR("ac_len", aud0_len->field_symbol);
  M68K_C_ASSERT_U32(AMIGA_OS_SYMBOL_ID_AUD, aud0_len->register_symbol_id);
  M68K_C_ASSERT_U32(AMIGA_OS_SYMBOL_ID_AC_LEN, aud0_len->field_symbol_id);
  M68K_C_ASSERT(spr1_dataa != NULL);
  M68K_C_ASSERT_STR("spr", spr1_dataa->register_symbol);
  M68K_C_ASSERT_STR("sd_dataa", spr1_dataa->field_symbol);
  M68K_C_ASSERT(format_amiga_hardware_register_field_symbol(spr1_dataa, 0, symbol_expr, sizeof(symbol_expr)));
  M68K_C_ASSERT_STR("spr1+sd_dataa", symbol_expr);
  M68K_C_ASSERT(spr_range != NULL);
  M68K_C_ASSERT_STR("spr", spr_range->symbol_name);
  M68K_C_ASSERT(bplpt_tail != NULL);
  M68K_C_ASSERT(sprpt_tail != NULL);
  M68K_C_ASSERT_STR("bplpt", bplpt_tail->symbol_name);
  M68K_C_ASSERT_STR("sprpt", sprpt_tail->symbol_name);
  M68K_C_ASSERT(bplpt_past_end == NULL);
  M68K_C_ASSERT(sprpt_past_end != NULL);
  M68K_C_ASSERT_STR("spr", sprpt_past_end->symbol_name);
  M68K_C_ASSERT(aud0_len_as_range == NULL);
  M68K_C_ASSERT_STR("copper_list", cop1lc->runtime_target_role);
  M68K_C_ASSERT_U32(AMIGA_OS_SYMBOL_ID_COP1LC, cop1lc->symbol_id);
  M68K_C_ASSERT_U32(AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_COPPER_LIST, cop1lc->runtime_target_kind);
  M68K_C_ASSERT_STR("disk_buffer", dskpt->runtime_target_role);
  M68K_C_ASSERT_U32(AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_DISK_BUFFER, dskpt->runtime_target_kind);
  M68K_C_ASSERT_STR("blitter_source", bltcpt->runtime_target_role);
  M68K_C_ASSERT_U32(AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_BLITTER_SOURCE, bltcpt->runtime_target_kind);
  M68K_C_ASSERT_STR("blitter_destination", bltdpt->runtime_target_role);
  M68K_C_ASSERT_U32(AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_BLITTER_DESTINATION, bltdpt->runtime_target_kind);
  M68K_C_ASSERT_STR("sound_sample", aud0->runtime_target_role);
  M68K_C_ASSERT_U32(AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_SOUND_SAMPLE, aud0->runtime_target_kind);
  M68K_C_ASSERT_STR("bitmap", bplpt->runtime_target_role);
  M68K_C_ASSERT_U32(AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_BITMAP, bplpt->runtime_target_kind);
  M68K_C_ASSERT_STR("sprite", sprpt->runtime_target_role);
  M68K_C_ASSERT_U32(AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_SPRITE, sprpt->runtime_target_kind);
  M68K_C_ASSERT((cop1lc->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) != 0U);
  M68K_C_ASSERT((dskpt->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) != 0U);
  M68K_C_ASSERT((bltcpt->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) != 0U);
  M68K_C_ASSERT((bltdpt->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) != 0U);
  M68K_C_ASSERT((aud0->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) != 0U);
  M68K_C_ASSERT((bplpt->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) != 0U);
  M68K_C_ASSERT((sprpt->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) != 0U);
  M68K_C_ASSERT((intena->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) == 0U);
  M68K_C_ASSERT_STR("copper_list",
    platform_facts_v2_runtime_address_sink_data_class(M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x00DFF080U));
  M68K_C_ASSERT_STR("disk_buffer",
    platform_facts_v2_runtime_address_sink_data_class(M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x00DFF020U));
  M68K_C_ASSERT_STR("blitter_source",
    platform_facts_v2_runtime_address_sink_data_class(M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x00DFF048U));
  M68K_C_ASSERT_STR("blitter_destination",
    platform_facts_v2_runtime_address_sink_data_class(M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x00DFF054U));
  M68K_C_ASSERT_STR("sound_sample",
    platform_facts_v2_runtime_address_sink_data_class(M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x00DFF0A0U));
  M68K_C_ASSERT_STR("bitmap",
    platform_facts_v2_runtime_address_sink_data_class(M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x00DFF0E0U));
  M68K_C_ASSERT_STR("sprite",
    platform_facts_v2_runtime_address_sink_data_class(M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x00DFF120U));
  M68K_C_ASSERT_U32(AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_BITMAP,
    platform_facts_v2_runtime_address_sink_kind(M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x00DFF0E0U));
  M68K_C_ASSERT_U32(AMIGA_OS_HARDWARE_RUNTIME_TARGET_KIND_NONE,
    platform_facts_v2_runtime_address_sink_kind(M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x00DFF09AU));
  M68K_C_ASSERT(platform_facts_v2_is_runtime_address_sink(M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x00DFF080U));
  M68K_C_ASSERT(platform_facts_v2_is_runtime_address_sink(M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x00DFF020U));
  M68K_C_ASSERT(!platform_facts_v2_is_runtime_address_sink(M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x00DFF09AU));
  return 0;
}

static int test_amiga_runtime_struct_id_none_is_zero_safe(void) {
  uint32_t first_real_struct_id = (uint32_t)AMIGA_OS_STRUCT_ID_AMIGAGUIDEMSG;
  M68K_C_ASSERT_U32(0U, (uint32_t)AMIGA_OS_STRUCT_ID_NONE);
  M68K_C_ASSERT(first_real_struct_id < (uint32_t)AMIGA_OS_STRUCT_ID_COUNT);
  M68K_C_ASSERT(first_real_struct_id != (uint32_t)AMIGA_OS_STRUCT_ID_NONE);
  M68K_C_ASSERT(amiga_os_name(M68K_PLATFORM_NAME_STRUCT, AMIGA_OS_STRUCT_ID_NONE) == NULL);
  M68K_C_ASSERT_STR("AmigaGuideMsg", amiga_os_name(M68K_PLATFORM_NAME_STRUCT,
    AMIGA_OS_STRUCT_ID_AMIGAGUIDEMSG));
  M68K_C_ASSERT_U32((uint32_t)AMIGA_OS_STRUCT_ID_NONE,
    (uint32_t)amiga_os_name_id(M68K_PLATFORM_NAME_STRUCT, NULL));
  M68K_C_ASSERT_U32((uint32_t)AMIGA_OS_STRUCT_ID_NONE,
    (uint32_t)amiga_os_name_id(M68K_PLATFORM_NAME_STRUCT, ""));
  M68K_C_ASSERT_U32((uint32_t)AMIGA_OS_STRUCT_ID_NONE,
    (uint32_t)amiga_os_name_id(M68K_PLATFORM_NAME_STRUCT, "NotARealStruct"));
  return 0;
}

static int test_amiga_runtime_resolves_recursive_struct_fields(void) {
  AmigaOsResolvedStructFieldInfo resolved;
  char expr[96];

  M68K_C_ASSERT(amiga_os_resolve_struct_field_by_struct_id(AMIGA_OS_STRUCT_ID_INPUTEVENT, 18, 0, &resolved));
  M68K_C_ASSERT_INT(AMIGA_OS_FIELD_ID_TV_MICRO, resolved.field_id);
  M68K_C_ASSERT_INT(AMIGA_OS_STRUCT_ID_TIMEVAL, resolved.owner_struct_id);
  M68K_C_ASSERT_INT(18, resolved.offset);
  M68K_C_ASSERT_INT(0, resolved.inherited);
  M68K_C_ASSERT_INT(1, resolved.nested);
  M68K_C_ASSERT_INT(2, resolved.path_count);
  M68K_C_ASSERT_INT(AMIGA_OS_FIELD_ID_IE_TIMESTAMP, resolved.path_field_ids[0]);
  M68K_C_ASSERT_INT(AMIGA_OS_FIELD_ID_TV_MICRO, resolved.path_field_ids[1]);
  M68K_C_ASSERT(amiga_os_resolve_struct_field_symbol_expr_by_struct_id(AMIGA_OS_STRUCT_ID_INPUTEVENT, 18, 0, expr,
    sizeof(expr)));
  M68K_C_ASSERT_STR("ie_TimeStamp+TV_MICRO", expr);

  M68K_C_ASSERT(amiga_os_resolve_struct_field_symbol_expr("InputEvent", 14, 0, expr, sizeof(expr)));
  M68K_C_ASSERT_STR("ie_TimeStamp", expr);

  M68K_C_ASSERT(amiga_os_resolve_struct_field("IO", 14, 0, &resolved));
  M68K_C_ASSERT_INT(AMIGA_OS_FIELD_ID_MN_REPLYPORT, resolved.field_id);
  M68K_C_ASSERT_INT(AMIGA_OS_STRUCT_ID_MN, resolved.owner_struct_id);
  M68K_C_ASSERT_INT(1, resolved.inherited);
  M68K_C_ASSERT_INT(0, resolved.nested);
  M68K_C_ASSERT(amiga_os_resolve_struct_field_symbol_expr("IO", 14, 0, expr, sizeof(expr)));
  M68K_C_ASSERT_STR("MN_REPLYPORT", expr);
  M68K_C_ASSERT(amiga_os_resolve_struct_field("IO", 14, 1, &resolved));
  M68K_C_ASSERT_INT(AMIGA_OS_FIELD_ID_MN_REPLYPORT, resolved.field_id);
  M68K_C_ASSERT_INT(AMIGA_OS_STRUCT_ID_MN, resolved.owner_struct_id);
  M68K_C_ASSERT_INT(1, resolved.inherited);
  M68K_C_ASSERT_INT(0, resolved.nested);
  M68K_C_ASSERT(amiga_os_resolve_struct_field_symbol_expr("ConUnit", 64, 0, expr, sizeof(expr)));
  M68K_C_ASSERT_STR("cu_YCCP", expr);
  M68K_C_ASSERT(amiga_os_resolve_struct_field_symbol_expr("AmigaGuideMsg", 48, 0, expr, sizeof(expr)));
  M68K_C_ASSERT_STR("agm_System2", expr);
  M68K_C_ASSERT(!amiga_os_resolve_struct_field_symbol_expr("AmigaGuideMsg", 54, 0, expr, sizeof(expr)));
  return 0;
}

static void test_set_instruction_operand_symbol(M68kInstructionIR *instruction, size_t operand_index,
    const char *name) {
  M68kSymbolRefIR *ref;
  if (instruction == NULL || operand_index >= instruction->operand_count || name == NULL) return;
  ref = &instruction->operands[operand_index].symbol_ref;
  m68k_ir_symbol_ref_init(ref);
  ref->kind = M68K_IR_SYMBOL_REF_ABS;
  ref->has_name = 1U;
  ref->name_is_generated = 0U;
  ref->name_provenance = M68K_IR_SYMBOL_PROVENANCE_PLATFORM_AMIGA;
  snprintf(ref->name, sizeof(ref->name), "%s", name);
}

static int test_append_parsed_instruction(M68kSectionIR *section, uint32_t offset, const char *parse_text,
    size_t symbol_operand_index, const char *symbol_name) {
  M68kStatementIR stmt;
  m68k_ir_statement_init(&stmt);
  stmt.kind = M68K_STATEMENT_INSTRUCTION;
  stmt.offset = offset;
  stmt.u.instruction = m68k_plain_parse_instruction_to_ir(parse_text, M68K_ASM_CPU_68000, m68k_diag_sink(NULL));
  M68K_C_ASSERT(stmt.u.instruction.mnemonic_id != M68K_ASM_MNEMONIC_NONE);
  M68K_C_ASSERT(stmt.u.instruction.byte_count != 0U);
  if (symbol_name != NULL) test_set_instruction_operand_symbol(&stmt.u.instruction, symbol_operand_index, symbol_name);
  return m68k_ir_section_append_statement(section, &stmt);
}

static int test_append_typed_plan_source_row(M68kRenderPlan *render_plan, uint32_t kind, const char *text,
    uint32_t section_index, uint32_t offset, uint32_t size) {
  M68kRenderPlanRow *row = NULL;
  if (m68k_render_plan_append_text_row(render_plan, kind, section_index, text, &row) != 0) return -1;
  m68k_render_plan_row_set_source_range(row, section_index, offset, size);
  return 0;
}

static int test_listing_full_window_from_render_plan_to_json(const M68kSourceFileIR *source_file,
    const M68kRenderPlan *render_plan, uint8_t platform_backend_kind, const M68kAnalysisPolicy *analysis_policy,
    const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation, int include_source_only_rows,
    char **out_json, M68kDiagSink diagnostics) {
  Arena *arena = NULL;
  PlatformListingRowIndex row_index;
  int result = -1;
  memset(&row_index, 0, sizeof(row_index));
  if (out_json != NULL) *out_json = NULL;
  arena = arena_create(4096U);
  if (arena == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
    return -1;
  }
  if (source_file_listing_row_index_from_render_plan(source_file, render_plan, platform_backend_kind,
      analysis_policy, source_analysis, analysis_generation, include_source_only_rows, 256U, arena, &row_index,
      diagnostics) != 0)
    goto done;
  {
    JsonBuilder builder = {0};
    if (json_builder_create(&builder) != 0) {
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
      goto done;
    }
    if (source_file_listing_window_from_render_plan_with_index_append_json(&builder, source_file, render_plan,
        platform_backend_kind, analysis_policy, source_analysis, analysis_generation, include_source_only_rows,
        &row_index, 0U, row_index.row_count, diagnostics) == 0) {
      *out_json = json_builder_build(&builder);
      result = *out_json != NULL ? 0 : -1;
      if (result != 0) {
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY,
          "listing window payload build failed");
      }
    }
    json_builder_destroy(&builder);
  }

done:
  arena_destroy(arena);
  return result;
}

static int test_listing_window_from_render_plan_with_index_to_json(const M68kSourceFileIR *source_file,
    const M68kRenderPlan *render_plan, uint8_t platform_backend_kind, const M68kAnalysisPolicy *analysis_policy,
    const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation, int include_source_only_rows,
    const PlatformListingRowIndex *row_index, size_t start, size_t count, char **out_json,
    M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  int result = -1;
  if (out_json != NULL) *out_json = NULL;
  if (out_json == NULL) return -1;
  if (json_builder_create(&builder) != 0) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
    return -1;
  }
  if (source_file_listing_window_from_render_plan_with_index_append_json(&builder, source_file, render_plan,
      platform_backend_kind, analysis_policy, source_analysis, analysis_generation, include_source_only_rows,
      row_index, start, count, diagnostics) == 0) {
    *out_json = json_builder_build(&builder);
    result = *out_json != NULL ? 0 : -1;
    if (result != 0) {
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY,
        "listing window payload build failed");
    }
  }
  json_builder_destroy(&builder);
  return result;
}

static int test_listing_addr_window_from_render_plan_with_index_to_json(const M68kSourceFileIR *source_file,
    const M68kRenderPlan *render_plan, uint8_t platform_backend_kind, const M68kAnalysisPolicy *analysis_policy,
    const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation, int include_source_only_rows,
    const PlatformListingRowIndex *row_index, int has_addr, uint32_t addr, size_t before, size_t after,
    char **out_json, M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  int result = -1;
  if (out_json != NULL) *out_json = NULL;
  if (out_json == NULL) return -1;
  if (json_builder_create(&builder) != 0) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
    return -1;
  }
  if (source_file_listing_addr_window_from_render_plan_with_index_append_json(&builder, source_file, render_plan,
      platform_backend_kind, analysis_policy, source_analysis, analysis_generation, include_source_only_rows,
      row_index, has_addr, addr, before, after, diagnostics) == 0) {
    *out_json = json_builder_build(&builder);
    result = *out_json != NULL ? 0 : -1;
    if (result != 0) {
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY,
        "listing window payload build failed");
    }
  }
  json_builder_destroy(&builder);
  return result;
}

static int test_listing_navigation_from_render_plan_to_json(const M68kSourceFileIR *source_file,
    const M68kRenderPlan *render_plan, uint8_t platform_backend_kind, const M68kAnalysisPolicy *analysis_policy,
    const M68kSourceAnalysisIR *source_analysis, const char *analysis_generation, int include_source_only_rows,
    char **out_json, M68kDiagSink diagnostics) {
  JsonBuilder builder = {0};
  int result = -1;
  if (out_json != NULL) *out_json = NULL;
  if (out_json == NULL) return -1;
  if (json_builder_create(&builder) != 0) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
    return -1;
  }
  if (source_file_listing_navigation_from_render_plan_append_json(&builder, source_file, render_plan,
      platform_backend_kind, analysis_policy, source_analysis, analysis_generation, include_source_only_rows,
      diagnostics) == 0) {
    *out_json = json_builder_build(&builder);
    result = *out_json != NULL ? 0 : -1;
    if (result != 0) {
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY,
        "listing navigation payload build failed");
    }
  }
  json_builder_destroy(&builder);
  return result;
}

static int test_listing_json_header_collection_stops_at_first_section(void) {
  M68kSourceFileIR source_file;
  M68kSectionIR section;
  M68kRenderPlan render_plan;
  char *rows_json = NULL;

  M68K_C_ASSERT_INT(0, m68k_ir_source_file_create(&source_file));
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));
  m68k_render_plan_init(&render_plan);
  source_file.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  source_file.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = 4U;
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 0U, "rts", 0U, NULL));
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 2U, "rts", 0U, NULL));
  M68K_C_ASSERT_INT(0, m68k_ir_source_file_append_section(&source_file, &section));

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_INCLUDE, 0U,
    "    INCLUDE \"hardware/custom.i\"\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_BLANK, 0U,
    "\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_SECTION, 0U,
    "    SECTION section_0,code\n", NULL));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\trts\n", 0U, 0U, 2U));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_INCLUDE, 0U,
    "    INCLUDE \"hardware/dmabits.i\"\n", NULL));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\trts\n", 0U, 2U, 2U));
  M68K_C_ASSERT_INT(0, test_listing_full_window_from_render_plan_to_json(&source_file, &render_plan,
    source_file.platform_backend_kind, NULL, NULL, "full", 0, &rows_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(rows_json != NULL);
  M68K_C_ASSERT(strstr(rows_json, "hardware/custom.i") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "hardware/dmabits.i") == NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"start_offset\":0") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"start_offset\":2") != NULL);

  free(rows_json);
  m68k_render_plan_destroy(&render_plan);
  m68k_ir_section_destroy(&section);
  m68k_ir_source_file_destroy(&source_file);
  return 0;
}

static int test_listing_json_header_collection_uses_typed_plan_rows(void) {
  M68kSourceFileIR source_file;
  M68kSectionIR section;
  M68kRenderPlan render_plan;
  char *rows_json = NULL;

  M68K_C_ASSERT_INT(0, m68k_ir_source_file_create(&source_file));
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));
  m68k_render_plan_init(&render_plan);
  source_file.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  source_file.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = 2U;
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 0U, "rts", 0U, NULL));
  M68K_C_ASSERT_INT(0, m68k_ir_source_file_append_section(&source_file, &section));

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_INCLUDE, 0U,
    "    INCLUDE \"hardware/custom.i\"\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_EQUATE, 0U,
    "_custom EQU $DFF000\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_SECTION, 0U,
    "    SECTION section_0,code\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_INCLUDE, 0U,
    "    INCLUDE \"hardware/cia.i\"\n", NULL));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\trts\n", 0U, 0U, 2U));

  M68K_C_ASSERT_INT(0, test_listing_full_window_from_render_plan_to_json(&source_file, &render_plan,
    source_file.platform_backend_kind, NULL, NULL, "full", 0, &rows_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(rows_json != NULL);
  M68K_C_ASSERT(strstr(rows_json, "hardware/custom.i") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "_custom") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "hardware/cia.i") == NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"kind\":\"instruction\"") != NULL);

  free(rows_json);
  m68k_render_plan_destroy(&render_plan);
  m68k_ir_section_destroy(&section);
  m68k_ir_source_file_destroy(&source_file);
  return 0;
}

static int test_listing_json_typed_plan_emits_expected_rows(void) {
  M68kSourceFileIR source_file;
  M68kSectionIR section;
  M68kStatementIR data_stmt;
  M68kRenderPlan render_plan;
  char *rows_json = NULL;
  uint8_t data_bytes[2] = {0x12U, 0x34U};

  M68K_C_ASSERT_INT(0, m68k_ir_source_file_create(&source_file));
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));
  m68k_render_plan_init(&render_plan);
  source_file.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  source_file.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = 4U;
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 0U, "rts", 0U, NULL));
  m68k_ir_statement_init(&data_stmt);
  data_stmt.kind = M68K_STATEMENT_DATA;
  data_stmt.offset = 2U;
  data_stmt.u.data.kind = M68K_DATA_ITEM_BYTES;
  data_stmt.u.data.data = data_bytes;
  data_stmt.u.data.size = 2U;
  M68K_C_ASSERT_INT(0, m68k_ir_section_append_statement(&section, &data_stmt));
  M68K_C_ASSERT_INT(0, m68k_ir_source_file_append_section(&source_file, &section));

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_INCLUDE, 0U,
    "    INCLUDE \"hardware/custom.i\"\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_BLANK, 0U,
    "\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_SECTION, 0U,
    "    SECTION section_0,code\n", NULL));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\trts\n", 0U, 0U, 2U));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_LABEL,
    "loc_0_00000002:\n", 0U, 2U, 0U));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_DATA,
    "\tdc.b $12,$34\n", 0U, 2U, 2U));
  M68K_C_ASSERT_INT(0, test_listing_full_window_from_render_plan_to_json(&source_file, &render_plan,
    source_file.platform_backend_kind, NULL, NULL, "full", 0, &rows_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(strstr(rows_json, "hardware/custom.i") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"kind\":\"instruction\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"kind\":\"data\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"start_offset\":0") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"start_offset\":2") != NULL);

  free(rows_json);
  m68k_render_plan_destroy(&render_plan);
  m68k_ir_section_destroy(&section);
  m68k_ir_source_file_destroy(&source_file);
  return 0;
}

static int test_listing_navigation_reports_orphan_code_signals(void) {
  M68kSourceFileIR source_file;
  M68kSectionIR section;
  M68kStatementIR data_stmt;
  M68kSourceAnalysisIR source_analysis;
  M68kSectionAnalysisIR section_analysis;
  M68kOrphanCodeSignalIR signal;
  M68kRenderPlan render_plan;
  char *rows_json = NULL;
  uint8_t data_bytes[4] = {0x70U, 0x01U, 0x4EU, 0x75U};

  M68K_C_ASSERT_INT(0, m68k_ir_source_file_create(&source_file));
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_create(&source_analysis));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_create(&section_analysis));
  m68k_render_plan_init(&render_plan);
  source_file.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  source_file.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  source_analysis.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = 6U;
  section_analysis.section_index = 0U;
  section_analysis.section_kind = M68K_SECTION_CODE;
  section_analysis.section_size = 6U;
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 0U, "rts", 0U, NULL));
  m68k_ir_statement_init(&data_stmt);
  data_stmt.kind = M68K_STATEMENT_DATA;
  data_stmt.offset = 2U;
  data_stmt.u.data.kind = M68K_DATA_ITEM_BYTES;
  data_stmt.u.data.data = data_bytes;
  data_stmt.u.data.size = sizeof(data_bytes);
  M68K_C_ASSERT_INT(0, m68k_ir_section_append_statement(&section, &data_stmt));
  M68K_C_ASSERT_INT(0, m68k_ir_source_file_append_section(&source_file, &section));

  memset(&signal, 0, sizeof(signal));
  signal.offset = 2U;
  signal.size = 4U;
  signal.terminal_offset = 4U;
  signal.terminal_flow_kind = M68K_SIM_FLOW_RETURN;
  signal.reason = M68K_ORPHAN_CODE_SIGNAL_TERMINAL_DECODE;
  signal.status = M68K_ORPHAN_CODE_SIGNAL_UNRESOLVED;
  signal.confidence = 70U;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_orphan_code_signal(&section_analysis, &signal));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_append_section(&source_analysis, &section_analysis));

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_SECTION, 0U,
    "    SECTION section_0,code\n", NULL));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\trts\n", 0U, 0U, 2U));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_DATA,
    "\tdc.b $70,$01,$4E,$75\n", 0U, 2U, 4U));
  M68K_C_ASSERT_INT(0, test_listing_navigation_from_render_plan_to_json(&source_file, &render_plan,
    source_file.platform_backend_kind, NULL, &source_analysis, "full", 1, &rows_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(rows_json != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"orphan-code\":[{\"addr\":2") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"summary\":\"Orphan code signal $0002-$0006") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "terminal_decode/unresolved") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"match_text\":\"dc.b $70,$01,$4E,$75\"") != NULL);

  free(rows_json);
  m68k_render_plan_destroy(&render_plan);
  m68k_ir_section_analysis_destroy(&section_analysis);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_ir_section_destroy(&section);
  m68k_ir_source_file_destroy(&source_file);
  return 0;
}

static int test_listing_navigation_reports_runtime_views(void) {
  M68kSourceFileIR source_file;
  M68kSectionIR section;
  M68kStatementIR data_stmt;
  M68kSourceAnalysisIR source_analysis;
  M68kSectionAnalysisIR section_analysis;
  M68kRuntimeViewIR view;
  M68kRenderPlan render_plan;
  char *rows_json = NULL;
  uint8_t data_bytes[4] = {0x70U, 0x01U, 0x4EU, 0x75U};

  M68K_C_ASSERT_INT(0, m68k_ir_source_file_create(&source_file));
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_create(&source_analysis));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_create(&section_analysis));
  m68k_render_plan_init(&render_plan);
  source_file.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  source_file.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  source_analysis.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = 6U;
  section_analysis.section_index = 0U;
  section_analysis.section_kind = M68K_SECTION_CODE;
  section_analysis.section_size = 6U;
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 0U, "rts", 0U, NULL));
  m68k_ir_statement_init(&data_stmt);
  data_stmt.kind = M68K_STATEMENT_DATA;
  data_stmt.offset = 2U;
  data_stmt.u.data.kind = M68K_DATA_ITEM_BYTES;
  data_stmt.u.data.data = data_bytes;
  data_stmt.u.data.size = sizeof(data_bytes);
  M68K_C_ASSERT_INT(0, m68k_ir_section_append_statement(&section, &data_stmt));
  M68K_C_ASSERT_INT(0, m68k_ir_source_file_append_section(&source_file, &section));

  memset(&view, 0, sizeof(view));
  view.runtime_view_id = 1U;
  view.storage_offset = 2U;
  view.size = 4U;
  view.runtime_address = 0x400U;
  view.kind = 2U;
  view.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  view.materialized = 0U;
  view.materialization_reason = M68K_RUNTIME_VIEW_SUPPRESSED_EXIT_TO_LARGER_RUNTIME_RANGE;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_runtime_view(&section_analysis, &view));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_append_section(&source_analysis, &section_analysis));

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_SECTION, 0U,
    "    SECTION section_0,code\n", NULL));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\trts\n", 0U, 0U, 2U));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_DATA,
    "\tdc.b $70,$01,$4E,$75\n", 0U, 2U, 4U));
  M68K_C_ASSERT_INT(0, test_listing_navigation_from_render_plan_to_json(&source_file, &render_plan,
    source_file.platform_backend_kind, NULL, &source_analysis, "full", 1, &rows_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(rows_json != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"runtime-views\":[{\"addr\":2") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "Runtime view $0002-$0006 -> $0400 suppressed/exit_to_larger_runtime_range")
    != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"match_text\":\"dc.b $70,$01,$4E,$75\"") != NULL);

  free(rows_json);
  m68k_render_plan_destroy(&render_plan);
  m68k_ir_section_analysis_destroy(&section_analysis);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_ir_section_destroy(&section);
  m68k_ir_source_file_destroy(&source_file);
  return 0;
}

static int test_listing_json_uses_render_plan_statement_provenance(void) {
  M68kSourceFileIR source_file;
  M68kSectionIR section;
  M68kRenderPlan render_plan;
  M68kRenderPlanRow *row = NULL;
  char *rows_json = NULL;

  M68K_C_ASSERT_INT(0, m68k_ir_source_file_create(&source_file));
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));
  m68k_render_plan_init(&render_plan);
  source_file.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  source_file.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = 2U;
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 0U, "rts", 0U, NULL));
  M68K_C_ASSERT_INT(0, m68k_ir_source_file_append_section(&source_file, &section));

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan,
    M68K_RENDER_PLAN_ROW_INSTRUCTION, 0U, "\trts\n", &row));
  m68k_render_plan_row_set_source_range(row, 0U, 0U, 2U);
  row->has_statement = 1U;
  row->statement_index = 0U;

  M68K_C_ASSERT_INT(0, test_listing_full_window_from_render_plan_to_json(&source_file, &render_plan,
    source_file.platform_backend_kind, NULL, NULL, "full", 1, &rows_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(rows_json != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"kind\":\"instruction\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"section_index\":0") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"start_offset\":0") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"end_offset\":2") != NULL);

  free(rows_json);
  m68k_render_plan_destroy(&render_plan);
  m68k_ir_section_destroy(&section);
  m68k_ir_source_file_destroy(&source_file);
  return 0;
}

static int test_listing_json_uses_render_plan_source_range_provenance(void) {
  M68kSourceFileIR source_file;
  M68kSectionIR section;
  M68kRenderPlan render_plan;
  M68kRenderPlanRow *row = NULL;
  char *rows_json = NULL;

  M68K_C_ASSERT_INT(0, m68k_ir_source_file_create(&source_file));
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));
  m68k_render_plan_init(&render_plan);
  source_file.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  source_file.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = 2U;
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 0U, "rts", 0U, NULL));
  M68K_C_ASSERT_INT(0, m68k_ir_source_file_append_section(&source_file, &section));

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan,
    M68K_RENDER_PLAN_ROW_INSTRUCTION, 0U, "\trts\n", &row));
  m68k_render_plan_row_set_source_range(row, 0U, 0U, 2U);

  M68K_C_ASSERT_INT(0, test_listing_full_window_from_render_plan_to_json(&source_file, &render_plan,
    source_file.platform_backend_kind, NULL, NULL, "full", 1, &rows_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(rows_json != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"kind\":\"instruction\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"section_index\":0") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"start_offset\":0") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"end_offset\":2") != NULL);

  free(rows_json);
  m68k_render_plan_destroy(&render_plan);
  m68k_ir_section_destroy(&section);
  m68k_ir_source_file_destroy(&source_file);
  return 0;
}

static int test_listing_json_uses_plan_statement_metadata_without_source_file(void) {
  M68kSourceFileIR source_file;
  M68kSectionIR section;
  M68kRenderPlan render_plan;
  M68kRenderPlanRow *row = NULL;
  char *rows_json = NULL;
  const uint8_t bytes[2] = {0x4eU, 0x75U};

  M68K_C_ASSERT_INT(0, m68k_ir_source_file_create(&source_file));
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));
  m68k_render_plan_init(&render_plan);
  source_file.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  source_file.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = 2U;
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 0U, "rts", 0U, NULL));
  M68K_C_ASSERT_INT(0, m68k_ir_source_file_append_section(&source_file, &section));

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan,
    M68K_RENDER_PLAN_ROW_INSTRUCTION, 0U, "\trts\n", &row));
  m68k_render_plan_row_set_source_range(row, 0U, 0U, 2U);
  m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_INSTRUCTION,
    &source_file.sections[0].statements[0].u.instruction, bytes, sizeof(bytes));

  M68K_C_ASSERT_INT(0, test_listing_full_window_from_render_plan_to_json(NULL, &render_plan,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 1, &rows_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(rows_json != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"kind\":\"instruction\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"start_offset\":0") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"bytes\":\"4e75\"") != NULL);

  free(rows_json);
  m68k_render_plan_destroy(&render_plan);
  m68k_ir_section_destroy(&section);
  m68k_ir_source_file_destroy(&source_file);
  return 0;
}

static int test_listing_json_classifies_org_subline_as_directive(void) {
  M68kRenderPlan render_plan;
  M68kRenderPlanRow *row = NULL;
  char *rows_json = NULL;

  m68k_render_plan_init(&render_plan);
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_LABEL, 0U,
    "    ORG $400\nabs_0_00000400:\n", &row));
  row->directive_line_mask = 1U;
  m68k_render_plan_row_set_source_range(row, 0U, 0U, 0U);
  m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_LABEL, NULL, NULL, 0U);

  M68K_C_ASSERT_INT(0, test_listing_full_window_from_render_plan_to_json(NULL, &render_plan,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 1, &rows_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(rows_json != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"row_id\":\"c:0\",\"kind\":\"directive\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"row_id\":\"c:1\",\"kind\":\"label\"") != NULL);

  free(rows_json);
  m68k_render_plan_destroy(&render_plan);
  return 0;
}

static int test_render_plan_marks_emitted_org_subline_as_directive(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kDecodeIR decode;
  M68kFactIR facts;
  M68kRenderIRPreview preview;
  M68kFact fact;
  uint8_t *accepted_start[1];
  uint8_t *accepted_bytes[1];
  uint8_t start_map[24];
  uint8_t byte_map[24];
  const M68kRenderPlanRow *org_row = NULL;
  size_t row_index;
  uint8_t bytes[20] = {
    0x4eu, 0xf9u, 0x00u, 0x00u, 0x00u, 0x80u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(start_map, 0, sizeof(start_map));
  memset(byte_map, 0, sizeof(byte_map));
  accepted_start[0] = start_map;
  accepted_bytes[0] = byte_map;
  start_map[0] = 1U;
  memset(&byte_map[0], 1, 6U);
  start_map[0x10] = 1U;
  memset(&byte_map[0x10], 1, 4U);
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_decode_ir_init(&decode);
  m68k_fact_ir_init(&facts);
  m68k_render_ir_preview_init(&preview);
  M68K_C_ASSERT_INT(0, m68k_decode_ir_build_object(&decode, &object, M68K_ASM_CPU_68060,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(0, m68k_fact_ir_create_label(&facts, 0U, 0U, M68K_FACT_CONFIDENCE_TOOL_INFERRED));
  M68K_C_ASSERT_INT(0, m68k_fact_ir_create_label(&facts, 0U, 0x10U, M68K_FACT_CONFIDENCE_TOOL_INFERRED));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_CODE_START;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  fact.section_index = 0U;
  fact.offset = 0x10U;
  fact.reason = M68K_FACT_CODE_START_REASON_CONTROL_TARGET;
  fact.has_runtime_address = 1U;
  fact.runtime_address = 0x80U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_RUNTIME_ADDRESS_RANGE;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  fact.section_index = 0U;
  fact.offset = 0x10U;
  fact.has_runtime_address = 1U;
  fact.runtime_kind = M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY;
  fact.runtime_address = 0x80U;
  fact.size = 4U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_RUNTIME_ADDRESS_REF;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  fact.section_index = 0U;
  fact.offset = 0U;
  fact.target_section_index = 0U;
  fact.target_offset = 0x10U;
  fact.has_runtime_address = 1U;
  fact.runtime_address = 0x80U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  M68K_C_ASSERT_INT(0, m68k_render_ir_preview_build(&object, &decode, &facts, NULL,
    accepted_start, accepted_bytes, 0, 1, 1, 1, &preview, NULL));
  for (row_index = 0U; row_index < preview.asm_source_plan.row_count; ++row_index) {
    const M68kRenderPlanRow *row = &preview.asm_source_plan.rows[row_index];
    if (row->text != NULL && strstr(row->text, "    ORG $80\n") != NULL) {
      org_row = row;
      break;
    }
  }
  M68K_C_ASSERT(org_row != NULL);
  M68K_C_ASSERT(strstr(org_row->text, "loc_0_00000010:\n    ORG $80\nabs_0_00000080:\n") != NULL);
  M68K_C_ASSERT_U32(2U, org_row->directive_line_mask);
  M68K_C_ASSERT_U32(M68K_RENDER_PLAN_ROW_LABEL, org_row->kind);
  M68K_C_ASSERT_U32(0U, preview.asm_source_instruction_render_failures);
  m68k_render_ir_preview_destroy(&preview);
  m68k_fact_ir_destroy(&facts);
  m68k_decode_ir_destroy(&decode);
  m68k_object_destroy(&object);
  return 0;
}

static int test_listing_json_uses_render_plan_data_class(void) {
  M68kRenderPlan render_plan;
  M68kRenderPlanRow *row = NULL;
  char *rows_json = NULL;
  const uint8_t bytes[2] = {0x00U, 0x00U};
  const char *first_data_class;

  m68k_render_plan_init(&render_plan);
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_LABEL, 0U,
    "loc_0_00000020:\n", &row));
  m68k_render_plan_row_set_source_range(row, 0U, 0x20U, 0U);
  m68k_render_plan_row_set_data_class(row, "lookup_table");
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_DATA, 0U,
    "\tdc.w $0000\t; lookup_table\n", &row));
  m68k_render_plan_row_set_source_range(row, 0U, 0x20U, sizeof(bytes));
  m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_DATA, NULL, bytes, sizeof(bytes));
  m68k_render_plan_row_set_data_class(row, "lookup_table");
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE, row->data_class_flags);

  M68K_C_ASSERT_INT(0, test_listing_full_window_from_render_plan_to_json(NULL, &render_plan,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 1, &rows_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(rows_json != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"kind\":\"data\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"data_class\":\"lookup_table\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"data_class_flags\":8") != NULL);
  first_data_class = strstr(rows_json, "\"data_class\":\"lookup_table\"");
  M68K_C_ASSERT(first_data_class != NULL);
  M68K_C_ASSERT(strstr(first_data_class + 1, "\"data_class\":\"lookup_table\"") == NULL);

  free(rows_json);
  m68k_render_plan_destroy(&render_plan);
  return 0;
}

static int test_listing_json_uses_render_plan_data_class_flags(void) {
  M68kRenderPlan render_plan;
  M68kRenderPlanRow *row = NULL;
  char *rows_json = NULL;
  const uint8_t bytes[2] = {0x00U, 0x00U};

  m68k_render_plan_init(&render_plan);
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_DATA, 0U,
    "\tdc.w $0000\t; sprite\n", &row));
  m68k_render_plan_row_set_source_range(row, 0U, 0x20U, sizeof(bytes));
  m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_DATA, NULL, bytes, sizeof(bytes));
  m68k_render_plan_row_set_data_class(row, "sprite");
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SPRITE, row->data_class_flags);

  M68K_C_ASSERT_INT(0, test_listing_full_window_from_render_plan_to_json(NULL, &render_plan,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 1, &rows_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(rows_json != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"data_class\":\"sprite\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"data_class_flags\":4096") != NULL);

  free(rows_json);
  m68k_render_plan_destroy(&render_plan);
  return 0;
}

static int test_listing_navigation_uses_render_plan_data_class(void) {
  M68kRenderPlan render_plan;
  M68kRenderPlanRow *row = NULL;
  char *navigation_json = NULL;
  const char *first_summary;
  const uint8_t bytes[2] = {0x00U, 0x00U};

  m68k_render_plan_init(&render_plan);
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_DATA, 0U,
    "\tdc.w $0000\n", &row));
  m68k_render_plan_row_set_source_range(row, 0U, 0x20U, sizeof(bytes));
  m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_DATA, NULL, bytes, sizeof(bytes));
  m68k_render_plan_row_set_data_class(row, "lookup_table");
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_DATA, 0U,
    "\tdc.w $0001\n", &row));
  m68k_render_plan_row_set_source_range(row, 0U, 0x20U, sizeof(bytes));
  m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_DATA, NULL, bytes, sizeof(bytes));
  m68k_render_plan_row_set_data_class(row, "lookup_table");

  M68K_C_ASSERT_INT(0, test_listing_navigation_from_render_plan_to_json(NULL, &render_plan,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 1, &navigation_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(navigation_json != NULL);
  M68K_C_ASSERT(strstr(navigation_json, "\"typed-data\":[{\"addr\":32,\"row_index\":0,\"summary\":\"lookup_table\"") != NULL);
  M68K_C_ASSERT(strstr(navigation_json, "\"data_class_flags\":8") != NULL);
  first_summary = strstr(navigation_json, "\"summary\":\"lookup_table\"");
  M68K_C_ASSERT(first_summary != NULL);
  M68K_C_ASSERT(strstr(first_summary + 1, "\"summary\":\"lookup_table\"") == NULL);

  free(navigation_json);
  m68k_render_plan_destroy(&render_plan);
  return 0;
}

static int test_listing_json_window_matches_full_render_plan_slice(void) {
  M68kRenderPlan render_plan;
  M68kRenderPlanRow *row = NULL;
  char *indexed_window_json = NULL;
  char *indexed_addr_window_json = NULL;
  PlatformListingRowIndex row_index;
  Arena *index_arena = NULL;
  size_t anchor_row = 99U;
  const uint8_t bytes[2] = {0x4eU, 0x75U};
  M68kInstructionIR instruction;

  memset(&row_index, 0, sizeof(row_index));
  m68k_render_plan_init(&render_plan);
  index_arena = arena_create(4096U);
  M68K_C_ASSERT(index_arena != NULL);
  instruction = m68k_plain_parse_instruction_to_ir("rts", M68K_ASM_CPU_68000, m68k_diag_sink(NULL));
  M68K_C_ASSERT(instruction.mnemonic_id != M68K_ASM_MNEMONIC_NONE);
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_SECTION, 0U,
    "    SECTION section_0,code\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_LABEL, 0U,
    "loc_0_00000000:\n", &row));
  m68k_render_plan_row_set_source_range(row, 0U, 0U, 0U);
  m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_LABEL, NULL, NULL, 0U);
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION, 0U,
    "\trts\n", &row));
  m68k_render_plan_row_set_source_range(row, 0U, 0U, 2U);
  m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_INSTRUCTION, &instruction, bytes,
    sizeof(bytes));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_DATA, 0U,
    "\tdc.b $00,$01\n", &row));
  m68k_render_plan_row_set_source_range(row, 0U, 2U, 2U);
  m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_DATA, NULL, NULL, 0U);

  M68K_C_ASSERT_INT(0, source_file_listing_row_index_from_render_plan(NULL, &render_plan,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 1, 2U, index_arena, &row_index,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(0, test_listing_addr_window_from_render_plan_with_index_to_json(NULL, &render_plan,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 1, &row_index, 1, 1U, 1U, 0U,
    &indexed_addr_window_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(0, test_listing_window_from_render_plan_with_index_to_json(NULL, &render_plan,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 1, &row_index, 1U, 2U, &indexed_window_json,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(0, source_file_listing_anchor_code_row_from_render_plan_with_index(NULL, &render_plan,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 1, &row_index, "SECTION section_0,code",
    &anchor_row, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(0U, (uint32_t)anchor_row);
  M68K_C_ASSERT_INT(0, source_file_listing_anchor_code_row_from_render_plan_with_index(NULL, &render_plan,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 1, &row_index, "loc_0_00000000", &anchor_row,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(1U, (uint32_t)anchor_row);
  M68K_C_ASSERT(indexed_window_json != NULL);
  M68K_C_ASSERT(indexed_addr_window_json != NULL);
  M68K_C_ASSERT_U32(4U, row_index.row_count);
  M68K_C_ASSERT_U32(2U, row_index.block_count);
  M68K_C_ASSERT(row_index.entries[0].has_addr == 0U);
  M68K_C_ASSERT(row_index.entries[1].has_addr != 0U);
  M68K_C_ASSERT_U32(0U, row_index.entries[1].addr);
  M68K_C_ASSERT(row_index.entries[1].has_plan_row != 0U);
  M68K_C_ASSERT_U32(1U, row_index.entries[1].plan_row_index);
  M68K_C_ASSERT_U32(0U, row_index.entries[1].subline);
  M68K_C_ASSERT(row_index.blocks[0].has_addr != 0U);
  M68K_C_ASSERT_U32(0U, row_index.blocks[0].max_addr);
  M68K_C_ASSERT(row_index.blocks[1].has_addr != 0U);
  M68K_C_ASSERT_U32(2U, row_index.blocks[1].max_addr);
  M68K_C_ASSERT(strstr(indexed_window_json, "\"start\":1") != NULL);
  M68K_C_ASSERT(strstr(indexed_window_json, "\"end\":3") != NULL);
  M68K_C_ASSERT(strstr(indexed_window_json, "\"total_rows\":4") != NULL);
  M68K_C_ASSERT(strstr(indexed_window_json, "\"row_id\":\"c:1\"") != NULL);
  M68K_C_ASSERT(strstr(indexed_window_json, "\"row_id\":\"c:2\"") != NULL);
  M68K_C_ASSERT(strstr(indexed_window_json, "\"row_id\":\"c:3\"") == NULL);
  M68K_C_ASSERT(strstr(indexed_addr_window_json, "\"start\":2") != NULL);
  M68K_C_ASSERT(strstr(indexed_addr_window_json, "\"end\":4") != NULL);
  M68K_C_ASSERT(strstr(indexed_addr_window_json, "\"anchor_addr\":1") != NULL);
  M68K_C_ASSERT(strstr(indexed_addr_window_json, "\"row_id\":\"c:2\"") != NULL);
  M68K_C_ASSERT(strstr(indexed_addr_window_json, "\"row_id\":\"c:3\"") != NULL);

  free(indexed_window_json);
  free(indexed_addr_window_json);
  arena_destroy(index_arena);
  m68k_render_plan_destroy(&render_plan);
  return 0;
}

static int test_listing_json_indexed_window_does_not_reemit_headers(void) {
  M68kRenderPlan render_plan;
  M68kRenderPlanRow *row = NULL;
  PlatformListingRowIndex row_index;
  Arena *index_arena = NULL;
  char *indexed_window_json = NULL;
  char *indexed_header_window_json = NULL;
  char *indexed_mixed_window_json = NULL;
  const uint8_t bytes[2] = {0x4eU, 0x75U};
  M68kInstructionIR instruction;

  memset(&row_index, 0, sizeof(row_index));
  m68k_render_plan_init(&render_plan);
  index_arena = arena_create(4096U);
  M68K_C_ASSERT(index_arena != NULL);
  instruction = m68k_plain_parse_instruction_to_ir("rts", M68K_ASM_CPU_68000, m68k_diag_sink(NULL));
  M68K_C_ASSERT(instruction.mnemonic_id != M68K_ASM_MNEMONIC_NONE);
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_INCLUDE, 0U,
    "    INCLUDE \"hardware/custom.i\"\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_SECTION, 0U,
    "    SECTION section_0,code\n", NULL));
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_LABEL, 0U,
    "loc_0_00000000:\n", &row));
  m68k_render_plan_row_set_source_range(row, 0U, 0U, 0U);
  m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_LABEL, NULL, NULL, 0U);
  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION, 0U,
    "\trts\n", &row));
  m68k_render_plan_row_set_source_range(row, 0U, 0U, 2U);
  m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_INSTRUCTION, &instruction, bytes,
    sizeof(bytes));

  M68K_C_ASSERT_INT(0, source_file_listing_row_index_from_render_plan(NULL, &render_plan,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 0, 2U, index_arena, &row_index,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(5U, row_index.row_count);
  M68K_C_ASSERT(row_index.entries[0].has_plan_row == 0U);
  M68K_C_ASSERT(row_index.entries[1].has_plan_row == 0U);
  M68K_C_ASSERT(row_index.entries[2].has_plan_row != 0U);
  M68K_C_ASSERT_INT(0, test_listing_window_from_render_plan_with_index_to_json(NULL, &render_plan,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 0, &row_index, 2U, 2U, &indexed_window_json,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(0, test_listing_window_from_render_plan_with_index_to_json(NULL, &render_plan,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 0, &row_index, 0U, 2U,
    &indexed_header_window_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_INT(0, test_listing_window_from_render_plan_with_index_to_json(NULL, &render_plan,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 0, &row_index, 1U, 3U,
    &indexed_mixed_window_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(indexed_window_json != NULL);
  M68K_C_ASSERT(indexed_header_window_json != NULL);
  M68K_C_ASSERT(indexed_mixed_window_json != NULL);
  M68K_C_ASSERT(strstr(indexed_header_window_json, "\"start\":0") != NULL);
  M68K_C_ASSERT(strstr(indexed_header_window_json, "\"end\":2") != NULL);
  M68K_C_ASSERT(strstr(indexed_header_window_json, "\"row_id\":\"c:0\"") != NULL);
  M68K_C_ASSERT(strstr(indexed_header_window_json, "hardware/custom.i") != NULL);
  M68K_C_ASSERT(strstr(indexed_header_window_json, "SECTION section_0,code") == NULL);
  M68K_C_ASSERT(strstr(indexed_mixed_window_json, "\"start\":1") != NULL);
  M68K_C_ASSERT(strstr(indexed_mixed_window_json, "\"end\":4") != NULL);
  M68K_C_ASSERT(strstr(indexed_mixed_window_json, "\"row_id\":\"c:1\"") != NULL);
  M68K_C_ASSERT(strstr(indexed_mixed_window_json, "\"row_id\":\"c:2\"") != NULL);
  M68K_C_ASSERT(strstr(indexed_mixed_window_json, "\"row_id\":\"c:3\"") != NULL);
  M68K_C_ASSERT(strstr(indexed_mixed_window_json, "hardware/custom.i") == NULL);
  M68K_C_ASSERT(strstr(indexed_mixed_window_json, "SECTION section_0,code") != NULL);
  M68K_C_ASSERT(strstr(indexed_window_json, "\"start\":2") != NULL);
  M68K_C_ASSERT(strstr(indexed_window_json, "\"end\":4") != NULL);
  M68K_C_ASSERT(strstr(indexed_window_json, "\"row_id\":\"c:2\"") != NULL);
  M68K_C_ASSERT(strstr(indexed_window_json, "\"row_id\":\"c:3\"") != NULL);
  M68K_C_ASSERT(strstr(indexed_window_json, "hardware/custom.i") == NULL);
  {
    size_t anchor_row = 99U;
    M68K_C_ASSERT_INT(0, source_file_listing_anchor_code_row_from_render_plan_with_index(NULL, &render_plan,
      M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 0, &row_index, "INCLUDE \"hardware/custom.i\"",
      &anchor_row, m68k_diag_sink(NULL)));
    M68K_C_ASSERT_U32(0U, (uint32_t)anchor_row);
    M68K_C_ASSERT_INT(0, source_file_listing_anchor_code_row_from_render_plan_with_index(NULL, &render_plan,
      M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 0, &row_index, "SECTION section_0,code",
      &anchor_row, m68k_diag_sink(NULL)));
    M68K_C_ASSERT_U32(2U, (uint32_t)anchor_row);
    M68K_C_ASSERT_INT(0, source_file_listing_anchor_code_row_from_render_plan_with_index(NULL, &render_plan,
      M68K_PLATFORM_BACKEND_AMIGA_HUNK, NULL, NULL, "full", 0, &row_index, "loc_0_00000000", &anchor_row,
      m68k_diag_sink(NULL)));
    M68K_C_ASSERT_U32(3U, (uint32_t)anchor_row);
  }

  free(indexed_window_json);
  free(indexed_header_window_json);
  free(indexed_mixed_window_json);
  arena_destroy(index_arena);
  m68k_render_plan_destroy(&render_plan);
  return 0;
}

static int test_listing_json_emits_rsset_layout_regions_from_platform_api_inputs(void) {
  M68kSourceFileIR source_file;
  M68kSectionIR section;
  M68kSourceAnalysisIR source_analysis;
  M68kSectionAnalysisIR section_analysis;
  M68kAppSlotRefIR ref;
  M68kBaseLayoutFieldIR layout_field;
  M68kRenderPlan render_plan;
  char *rows_json = NULL;

  M68K_C_ASSERT_INT(0, m68k_ir_source_file_create(&source_file));
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_create(&source_analysis));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_create(&section_analysis));
  m68k_render_plan_init(&render_plan);
  source_file.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  source_file.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  source_analysis.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = 14U;
  section_analysis.section_index = 0U;
  section_analysis.section_kind = M68K_SECTION_CODE;
  section_analysis.section_size = 14U;

  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 0U, "lea.l $0100(a6),a0", 0U,
    "app_input_event"));
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 4U, "jsr $FFD0(a6)", 0U, NULL));
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 8U, "move.w $0106(a6),d0", 0U,
    "app_input_event_code"));
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 12U, "move.b $0120(a6),d0", 0U,
    "app_after_event"));
  M68K_C_ASSERT_INT(0, m68k_ir_source_file_append_section(&source_file, &section));

  memset(&ref, 0, sizeof(ref));
  ref.offset = 0U;
  ref.displacement = 0x0100;
  ref.base_reg = 6U;
  ref.operand_index = 0U;
  ref.access_kind = M68K_APP_SLOT_ACCESS_ADDRESS;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_app_slot_ref(&section_analysis, &ref));
  ref.offset = 8U;
  ref.displacement = 0x0106;
  ref.access_kind = M68K_APP_SLOT_ACCESS_READ;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_app_slot_ref(&section_analysis, &ref));
  ref.offset = 12U;
  ref.displacement = 0x0120;
  ref.access_kind = M68K_APP_SLOT_ACCESS_READ;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_app_slot_ref(&section_analysis, &ref));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_platform_call(&section_analysis,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, 4U, PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL,
    "_LVORawKeyConvert", M68K_PLATFORM_CALL_NOTE_NONE, NULL, NULL, 0U, INT16_MIN, INT16_MIN, 0U, 0U, 0U,
    NULL, NULL));
  memset(&layout_field, 0, sizeof(layout_field));
  layout_field.layout_name = "app";
  layout_field.base_symbol = "__amiga_app_base__";
  layout_field.sizeof_symbol = "app_SIZEOF";
  layout_field.symbol = "app_input_event";
  layout_field.offset = 0x0100U;
  layout_field.size = 0x16U;
  layout_field.source_kind = M68K_BASE_LAYOUT_FIELD_SOURCE_APP_SLOT_ACCESS;
  layout_field.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_append_base_layout_field(&source_analysis, &layout_field));
  layout_field.symbol = "app_input_event_code";
  layout_field.offset = 0x0106U;
  layout_field.size = 2U;
  layout_field.alias = 1U;
  layout_field.has_alias_of = 1U;
  layout_field.alias_of_symbol = "app_input_event";
  layout_field.alias_of_offset = 0x0100U;
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_append_base_layout_field(&source_analysis, &layout_field));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_append_section(&source_analysis, &section_analysis));

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_SECTION, 0U,
    "SECTION section_0,CODE\n", NULL));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\tlea.l app_input_event(a6),a0\n", 0U, 0U, 4U));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\tjsr _LVORawKeyConvert(a6)\n", 0U, 4U, 4U));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\tmove.w app_input_event_code(a6),d0\n", 0U, 8U, 4U));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\tmove.b app_after_event(a6),d0\n", 0U, 12U, 2U));
  M68K_C_ASSERT_INT(0, test_listing_navigation_from_render_plan_to_json(&source_file, &render_plan,
    source_file.platform_backend_kind, NULL, &source_analysis, "full", 1, &rows_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(rows_json != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"slot_count\":3") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"layout_field_count\":2") != NULL);
  M68K_C_ASSERT(strstr(rows_json,
    "\"layout_fields\":[{\"layout_name\":\"app\",\"base_symbol\":\"__amiga_app_base__\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json,
    "\"symbol\":\"app_input_event_code\",\"owner_struct_name\":null,\"offset\":262,\"size\":2,\"alias\":true") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"confidence\":2,\"conflicted\":false,\"conflict_reason\":null") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"alias_of_symbol\":\"app_input_event\",\"alias_of_offset\":256") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"typed_region_count\":1") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"gap_count\":1") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"suggestion_count\":1") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"symbol\":\"app_input_event\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"source\":\"platform_api_arg\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"struct_name\":\"InputEvent\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"base_symbol\":\"app_input_event\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"field_name\":\"ie_Code\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"field_path\":[\"ie_Code\"]") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"field_expr\":\"ie_Code\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"coverage\":\"unknown_app_slot_space\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"coverage\":\"known_struct_field\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"semantic_type\":\"platform_api_buffer\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"app-slot-regions\":[{\"summary\":\"app_input_event: InputEvent $0100-$0116\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"field_paths\":[\"InputEvent.ie_Code\"]") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"app-slot-gaps\":[{\"summary\":\"Gap $0116-$0120 (10 bytes)\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"app-slot-field-gaps\":[{\"summary\":\"Field gap $") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"app-slot-suggestions\":[{\"summary\":\"app_input_event at app+0x100 matches InputEvent") != NULL);

  free(rows_json);
  m68k_render_plan_destroy(&render_plan);
  m68k_ir_section_analysis_destroy(&section_analysis);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_ir_section_destroy(&section);
  m68k_ir_source_file_destroy(&source_file);
  return 0;
}

static int test_listing_json_tracks_app_slot_address_through_lea_copy(void) {
  M68kSourceFileIR source_file;
  M68kSectionIR section;
  M68kSourceAnalysisIR source_analysis;
  M68kSectionAnalysisIR section_analysis;
  M68kAppSlotRefIR ref;
  M68kRenderPlan render_plan;
  char *rows_json = NULL;

  M68K_C_ASSERT_INT(0, m68k_ir_source_file_create(&source_file));
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_create(&source_analysis));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_create(&section_analysis));
  m68k_render_plan_init(&render_plan);
  source_file.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  source_file.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  source_analysis.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = 10U;
  section_analysis.section_index = 0U;
  section_analysis.section_kind = M68K_SECTION_CODE;
  section_analysis.section_size = 10U;

  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 0U, "lea.l $0100(a6),a1", 0U,
    "app_input_event"));
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 4U, "lea.l (a1),a0", 0U, NULL));
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 6U, "jsr $FFD0(a6)", 0U, NULL));
  M68K_C_ASSERT_INT(0, m68k_ir_source_file_append_section(&source_file, &section));

  memset(&ref, 0, sizeof(ref));
  ref.offset = 0U;
  ref.displacement = 0x0100;
  ref.base_reg = 6U;
  ref.operand_index = 0U;
  ref.access_kind = M68K_APP_SLOT_ACCESS_ADDRESS;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_app_slot_ref(&section_analysis, &ref));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_platform_call(&section_analysis,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, 6U, PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL,
    "_LVORawKeyConvert", M68K_PLATFORM_CALL_NOTE_NONE, NULL, NULL, 0U, INT16_MIN, INT16_MIN, 0U, 0U, 0U,
    NULL, NULL));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_append_section(&source_analysis, &section_analysis));

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_SECTION, 0U,
    "SECTION section_0,CODE\n", NULL));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\tlea.l app_input_event(a6),a1\n", 0U, 0U, 4U));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\tlea.l (a1),a0\n", 0U, 4U, 2U));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\tjsr _LVORawKeyConvert(a6)\n", 0U, 6U, 4U));
  M68K_C_ASSERT_INT(0, test_listing_navigation_from_render_plan_to_json(&source_file, &render_plan,
    source_file.platform_backend_kind, NULL, &source_analysis, "full", 1, &rows_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(rows_json != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"typed_region_count\":1") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"struct_name\":\"InputEvent\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"source_via_register\":\"A1\"") != NULL);

  free(rows_json);
  m68k_render_plan_destroy(&render_plan);
  m68k_ir_section_analysis_destroy(&section_analysis);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_ir_section_destroy(&section);
  m68k_ir_source_file_destroy(&source_file);
  return 0;
}

static int test_listing_json_reports_untyped_app_slot_api_args(void) {
  M68kSourceFileIR source_file;
  M68kSectionIR section;
  M68kSourceAnalysisIR source_analysis;
  M68kSectionAnalysisIR section_analysis;
  M68kAppSlotRefIR ref;
  M68kRenderPlan render_plan;
  char *rows_json = NULL;

  M68K_C_ASSERT_INT(0, m68k_ir_source_file_create(&source_file));
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_create(&source_analysis));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_create(&section_analysis));
  m68k_render_plan_init(&render_plan);
  source_file.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  source_file.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  source_analysis.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = 8U;
  section_analysis.section_index = 0U;
  section_analysis.section_kind = M68K_SECTION_CODE;
  section_analysis.section_size = 8U;

  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 0U, "lea.l $0200(a6),a1", 0U,
    "app_key_buffer"));
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 4U, "jsr $FFD0(a6)", 0U, NULL));
  M68K_C_ASSERT_INT(0, m68k_ir_source_file_append_section(&source_file, &section));

  memset(&ref, 0, sizeof(ref));
  ref.offset = 0U;
  ref.displacement = 0x0200;
  ref.base_reg = 6U;
  ref.operand_index = 0U;
  ref.access_kind = M68K_APP_SLOT_ACCESS_ADDRESS;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_app_slot_ref(&section_analysis, &ref));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_platform_call(&section_analysis,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, 4U, PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL,
    "_LVORawKeyConvert", M68K_PLATFORM_CALL_NOTE_NONE, NULL, NULL, 0U, INT16_MIN, INT16_MIN, 0U, 0U, 0U,
    NULL, NULL));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_append_section(&source_analysis, &section_analysis));

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_SECTION, 0U,
    "SECTION section_0,CODE\n", NULL));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\tlea.l app_key_buffer(a6),a1\n", 0U, 0U, 4U));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\tjsr _LVORawKeyConvert(a6)\n", 0U, 4U, 4U));
  M68K_C_ASSERT_INT(0, test_listing_navigation_from_render_plan_to_json(&source_file, &render_plan,
    source_file.platform_backend_kind, NULL, &source_analysis, "full", 1, &rows_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(rows_json != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"typed_region_count\":0") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"untyped_api_arg_count\":1") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"untyped_api_args\":[") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"symbol\":\"app_key_buffer\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"function\":\"RawKeyConvert\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"register\":\"A1\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"reason\":\"missing_struct_metadata\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"stable_key\":\"s0:00000004:instruction:2\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"source_stable_key\":\"s0:00000000:instruction:1\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json,
    "\"app-slot-api-args\":[{\"summary\":\"app_key_buffer -> RawKeyConvert buffer A1 (missing_struct_metadata)\"") != NULL);

  free(rows_json);
  m68k_render_plan_destroy(&render_plan);
  m68k_ir_section_analysis_destroy(&section_analysis);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_ir_section_destroy(&section);
  m68k_ir_source_file_destroy(&source_file);
  return 0;
}

static int test_listing_json_tracks_app_slot_address_immediate_adjust(void) {
  M68kSourceFileIR source_file;
  M68kSectionIR section;
  M68kSourceAnalysisIR source_analysis;
  M68kSectionAnalysisIR section_analysis;
  M68kAppSlotRefIR ref;
  M68kRenderPlan render_plan;
  char *rows_json = NULL;

  M68K_C_ASSERT_INT(0, m68k_ir_source_file_create(&source_file));
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_create(&source_analysis));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_create(&section_analysis));
  m68k_render_plan_init(&render_plan);
  source_file.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  source_file.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  source_analysis.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = 10U;
  section_analysis.section_index = 0U;
  section_analysis.section_kind = M68K_SECTION_CODE;
  section_analysis.section_size = 10U;

  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 0U, "lea.l $0100(a6),a1", 0U,
    "app_key_buffer"));
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 4U, "addq.l #$04,a1", 0U, NULL));
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 6U, "jsr $FFD0(a6)", 0U, NULL));
  M68K_C_ASSERT_INT(0, m68k_ir_source_file_append_section(&source_file, &section));

  memset(&ref, 0, sizeof(ref));
  ref.offset = 0U;
  ref.displacement = 0x0100;
  ref.base_reg = 6U;
  ref.operand_index = 0U;
  ref.access_kind = M68K_APP_SLOT_ACCESS_ADDRESS;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_app_slot_ref(&section_analysis, &ref));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_platform_call(&section_analysis,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, 6U, PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL,
    "_LVORawKeyConvert", M68K_PLATFORM_CALL_NOTE_NONE, NULL, NULL, 0U, INT16_MIN, INT16_MIN, 0U, 0U, 0U,
    NULL, NULL));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_append_section(&source_analysis, &section_analysis));

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_SECTION, 0U,
    "SECTION section_0,CODE\n", NULL));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\tlea.l app_key_buffer(a6),a1\n", 0U, 0U, 4U));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\taddq.l #$04,a1\n", 0U, 4U, 2U));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\tjsr _LVORawKeyConvert(a6)\n", 0U, 6U, 4U));
  M68K_C_ASSERT_INT(0, test_listing_navigation_from_render_plan_to_json(&source_file, &render_plan,
    source_file.platform_backend_kind, NULL, &source_analysis, "full", 1, &rows_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(rows_json != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"untyped_api_arg_count\":1") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"id\":\"app_slot_api_arg_0104_RawKeyConvert_A1\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json,
    "\"displacement\":260,\"base_displacement\":256,\"effective_displacement\":260") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"source_flow_row_index\":2") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"stable_key\":\"s0:00000006:instruction:3\"") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"source_stable_key\":\"s0:00000000:instruction:1\"") != NULL);

  free(rows_json);
  m68k_render_plan_destroy(&render_plan);
  m68k_ir_section_analysis_destroy(&section_analysis);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_ir_section_destroy(&section);
  m68k_ir_source_file_destroy(&source_file);
  return 0;
}

static int test_listing_json_clears_app_slot_address_source_on_register_clobber(void) {
  M68kSourceFileIR source_file;
  M68kSectionIR section;
  M68kSourceAnalysisIR source_analysis;
  M68kSectionAnalysisIR section_analysis;
  M68kAppSlotRefIR ref;
  M68kRenderPlan render_plan;
  char *rows_json = NULL;

  M68K_C_ASSERT_INT(0, m68k_ir_source_file_create(&source_file));
  M68K_C_ASSERT_INT(0, m68k_ir_section_create(&section));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_create(&source_analysis));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_create(&section_analysis));
  m68k_render_plan_init(&render_plan);
  source_file.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  source_file.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  source_analysis.file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = 10U;
  section_analysis.section_index = 0U;
  section_analysis.section_kind = M68K_SECTION_CODE;
  section_analysis.section_size = 10U;

  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 0U, "lea.l $0100(a6),a0", 0U,
    "app_input_event"));
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 4U, "movea.l a2,a0", 0U, NULL));
  M68K_C_ASSERT_INT(0, test_append_parsed_instruction(&section, 6U, "jsr $FFD0(a6)", 0U, NULL));
  M68K_C_ASSERT_INT(0, m68k_ir_source_file_append_section(&source_file, &section));

  memset(&ref, 0, sizeof(ref));
  ref.offset = 0U;
  ref.displacement = 0x0100;
  ref.base_reg = 6U;
  ref.operand_index = 0U;
  ref.access_kind = M68K_APP_SLOT_ACCESS_ADDRESS;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_app_slot_ref(&section_analysis, &ref));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_recovered_platform_call(&section_analysis,
    M68K_PLATFORM_BACKEND_AMIGA_HUNK, 6U, PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL,
    "_LVORawKeyConvert", M68K_PLATFORM_CALL_NOTE_NONE, NULL, NULL, 0U, INT16_MIN, INT16_MIN, 0U, 0U, 0U,
    NULL, NULL));
  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_append_section(&source_analysis, &section_analysis));

  M68K_C_ASSERT_INT(0, m68k_render_plan_append_text_row(&render_plan, M68K_RENDER_PLAN_ROW_SECTION, 0U,
    "SECTION section_0,CODE\n", NULL));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\tlea.l app_input_event(a6),a0\n", 0U, 0U, 4U));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\tmovea.l a2,a0\n", 0U, 4U, 2U));
  M68K_C_ASSERT_INT(0, test_append_typed_plan_source_row(&render_plan, M68K_RENDER_PLAN_ROW_INSTRUCTION,
    "\tjsr _LVORawKeyConvert(a6)\n", 0U, 6U, 4U));
  M68K_C_ASSERT_INT(0, test_listing_navigation_from_render_plan_to_json(&source_file, &render_plan,
    source_file.platform_backend_kind, NULL, &source_analysis, "full", 1, &rows_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(rows_json != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"slot_count\":1") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"typed_region_count\":0") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"suggestion_count\":0") != NULL);
  M68K_C_ASSERT(strstr(rows_json, "\"source\":\"platform_api_arg\"") == NULL);

  free(rows_json);
  m68k_render_plan_destroy(&render_plan);
  m68k_ir_section_analysis_destroy(&section_analysis);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_ir_section_destroy(&section);
  m68k_ir_source_file_destroy(&source_file);
  return 0;
}

static int test_facts_v2_render_asm_source_applies_entry_register_seed_without_seed_offset(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[8] = {0x4eu, 0x71u, 0x4eu, 0xaeu, 0xffu, 0x94u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.has_entry_offset = 1U;
  policy.entry_offset = 2U;
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  snprintf(policy.register_seeds[0].type_name, sizeof(policy.register_seeds[0].type_name), "LIB");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "    ; KNOWN: base A6=exec.library:LIB\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOAlert(a6)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_defines_private_lvo_symbol(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[6] = {0x4eu, 0xaeu, 0xffu, 0xdcu, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "SysBase");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "_LVOexecPrivate1\tEQU\t-36\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOexecPrivate1(a6)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_render_failures);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_preserves_base_across_movem_save(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[10] = {0x48u, 0xe7u, 0x00u, 0xc0u, 0x4eu, 0xaeu, 0xffu, 0x94u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovem.l a0-a1,-(a7)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOAlert(a6)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_uses_policy_label_for_branch(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[6] = {0x60u, 0x02u, 0x4eu, 0x71u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.named_label_count = 1U;
  policy.named_labels[0].has_section_index = 1U;
  policy.named_labels[0].section_index = 0U;
  policy.named_labels[0].offset = 4U;
  snprintf(policy.named_labels[0].name, sizeof(policy.named_labels[0].name), "branch_target");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "branch_target:") != NULL);
  M68K_C_ASSERT(strstr(source, "\tbra.b branch_target\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000004") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_uses_policy_label_for_data_relocation(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[8] = {0x00u, 0x00u, 0x00u, 0x04u, 0xdeu, 0xadu, 0xbeu, 0xefu};
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 0U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.named_label_count = 1U;
  policy.named_labels[0].has_section_index = 1U;
  policy.named_labels[0].section_index = 0U;
  policy.named_labels[0].offset = 4U;
  snprintf(policy.named_labels[0].name, sizeof(policy.named_labels[0].name), "reloc_target");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "reloc_target:") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l reloc_target") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000004") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(1U, profile.asm_source_relocation_exprs);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_relocation_backed_data_longs_auto_classify_pointer_table(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  uint16_t index;
  uint8_t bytes[16] = {
    0x00u, 0x00u, 0x00u, 0x08u,
    0x00u, 0x00u, 0x00u, 0x0Cu,
    0xDEu, 0xADu, 0xBEu, 0xEFu,
    0xCAu, 0xFEu, 0xBAu, 0xBEu
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  memset(&fixup, 0, sizeof(fixup));
  fixup.section_index = 0U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  fixup.offset = 0U;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  fixup.offset = 4U;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l loc_0_00000008\t; pointer_table\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l loc_0_0000000C\n") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && item->offset == 0U &&
        strcmp(item->semantic_role, "pointer_table") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(8U, auto_item->size);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_LONGS, auto_item->kind);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_uses_object_symbol_label(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kSymbol symbol;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[8] = {0x00u, 0x00u, 0x00u, 0x04u, 0xdeu, 0xadu, 0xbeu, 0xefu};
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  memset(&symbol, 0, sizeof(symbol));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object,
    m68k_object_add_section(&object, &section).index, bytes, sizeof(bytes)));
  fixup.section_index = 0U;
  fixup.offset = 0U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  symbol.name = "h0dl_ExecBase";
  symbol.binding = M68K_SYMBOL_LOCAL;
  symbol.defined = 1;
  symbol.section_index = 0U;
  symbol.value = 4U;
  added = m68k_object_add_symbol(&object, &symbol);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "h0dl_ExecBase:") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l h0dl_ExecBase\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_infers_lvo_from_object_base_symbol(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kSymbol symbol;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[16] = {
    0x2cu, 0x79u, 0x00u, 0x00u, 0x00u, 0x0cu,
    0x4eu, 0xaeu, 0xffu, 0x3au,
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  memset(&symbol, 0, sizeof(symbol));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object,
    m68k_object_add_section(&object, &section).index, bytes, sizeof(bytes)));
  fixup.section_index = 0U;
  fixup.offset = 2U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  symbol.name = "h0dl_ExecBase";
  symbol.binding = M68K_SYMBOL_LOCAL;
  symbol.defined = 1;
  symbol.section_index = 0U;
  symbol.value = 12U;
  added = m68k_object_add_symbol(&object, &symbol);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l h0dl_ExecBase.l,a6\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOAllocMem(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "h0dl_ExecBase:\n\tdc.b") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_infers_global_base_slot_from_lvo_set(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[32] = {
    0x2cu, 0x79u, 0x00u, 0x00u, 0x00u, 0x1cu,
    0x4eu, 0xaeu, 0xfcu, 0x04u,
    0x4eu, 0x75u,
    0x2cu, 0x79u, 0x00u, 0x00u, 0x00u, 0x1cu,
    0x4eu, 0xaeu, 0xfcu, 0x10u,
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object,
    m68k_object_add_section(&object, &section).index, bytes, sizeof(bytes)));
  fixup.section_index = 0U;
  fixup.offset = 2U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  fixup.offset = 14U;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.entry_point_count = 1U;
  policy.entry_points[0].has_section_index = 1U;
  policy.entry_points[0].section_index = 0U;
  policy.entry_points[0].offset = 12U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l h0dl_GfxBase.l,a6\n") != NULL);
  M68K_C_ASSERT(strstr(source, "h0dl_GfxBase:") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOAllocSpriteDataA(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOFindColor(a6)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_app_slot_overlap_uses_rsset_alias(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  char *analysis_json = NULL;
  uint8_t bytes[10] = {
    0x2du, 0x40u, 0x00u, 0x0cu,
    0x1du, 0x41u, 0x00u, 0x0eu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "__amiga_app_base__");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT_U32(2U, (uint32_t)source_analysis.base_layout_field_count);
  M68K_C_ASSERT_STR("app_000C", source_analysis.base_layout_fields[0].symbol);
  M68K_C_ASSERT_U32(0U, source_analysis.base_layout_fields[0].alias);
  M68K_C_ASSERT_STR("app_000E", source_analysis.base_layout_fields[1].symbol);
  M68K_C_ASSERT_U32(1U, source_analysis.base_layout_fields[1].alias);
  M68K_C_ASSERT_U32(1U, source_analysis.base_layout_fields[1].has_alias_of);
  M68K_C_ASSERT_U32(M68K_FACT_CONFIDENCE_TOOL_INFERRED, source_analysis.base_layout_fields[1].confidence);
  M68K_C_ASSERT_U32(0U, source_analysis.base_layout_fields[1].conflicted);
  M68K_C_ASSERT_STR("app_000C", source_analysis.base_layout_fields[1].alias_of_symbol);
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"base_layout_field_count\":2") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"memory_layout_record_count\":3") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"record_kind\":\"base_layout\",\"memory_kind\":\"base_layout\",\"layout_name\":\"app\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"field_count\":2") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"range_space_kind\":1,\"range_space\":\"base_relative\",\"range_start\":12,\"range_size\":4,"
    "\"range_end\":16") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"record_kind\":\"base_layout_field\",\"memory_kind\":\"base_layout_alias\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"range_space_kind\":1,\"range_space\":\"base_relative\",\"range_start\":14,\"range_size\":1,"
    "\"range_end\":15") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"symbol\":\"app_000E\",\"owner_struct_name\":null,\"offset\":14,\"size\":1,\"alias\":true") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"confidence\":2,\"conflicted\":false,\"conflict_reason\":null") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"alias_of_symbol\":\"app_000C\",\"alias_of_offset\":12") != NULL);
  M68K_C_ASSERT(strstr(source, "app_000C RS.L 1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    RSSET $000E\napp_000E RS.B 1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "app_000E EQU $000E\n") == NULL);
  M68K_C_ASSERT(strstr(source, "RS.B 0") == NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l d0,app_000C(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.b d1,app_000E(a6)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  free(analysis_json);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_does_not_infer_app_slot_from_unknown_a6_custom_offset(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[6] = {0x2du, 0x40u, 0x00u, 0x44u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "app_0044") == NULL);
  M68K_C_ASSERT(strstr(source, "app_SIZEOF") == NULL);
  M68K_C_ASSERT(strstr(source, "RSSET") == NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l d0,$0044(a6)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_uses_observed_app_slot_widths(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[10] = {
    0x3du, 0x40u, 0x00u, 0x0au,
    0x3du, 0x41u, 0x00u, 0x0cu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "__amiga_app_base__");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "app_000A RS.W 1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "app_000C RS.W 1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "app_000A RS.L 1\n") == NULL);
  M68K_C_ASSERT(strstr(source, "app_000C EQU $000C\n") == NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w d0,app_000A(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w d1,app_000C(a6)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_keeps_untyped_app_slot_untyped(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  const M68kSectionAnalysisIR *analysis_section;
  char *source = NULL;
  size_t index;
  uint8_t bytes[14] = {
    0x2du, 0x4fu, 0x02u, 0x34u,
    0x20u, 0x6eu, 0x02u, 0x34u,
    0x20u, 0x28u, 0x00u, 0x14u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "__amiga_app_base__");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(1U, (uint32_t)analysis.section_count);
  analysis_section = &analysis.sections[0];
  M68K_C_ASSERT_U32(0U, (uint32_t)analysis_section->recovered_platform_typed_access_count);
  M68K_C_ASSERT_U32(0U, (uint32_t)analysis_section->recovered_platform_unresolved_typed_access_count);
  for (index = 0U; index < analysis_section->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &analysis_section->recovered_platform_effects[index];
    const char *type_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.type_ref,
      effect->payload.typed.type_name);
    M68K_C_ASSERT(type_name == NULL || strcmp(type_name, "AmigaGuideMsg") != 0);
  }
  m68k_ir_source_analysis_destroy(&analysis);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "AmigaGuideMsg") == NULL);
  M68K_C_ASSERT(strstr(source, "agm_") == NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l a7,app_0234(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l app_0234(a6),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l $0014(a0),d0\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_uses_policy_rsset_layout_region_symbol(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[10] = {
    0x2du, 0x40u, 0x02u, 0x2cu,
    0x20u, 0x6eu, 0x02u, 0x2cu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "__amiga_app_base__");
  policy.rsset_layout_region_count = 1U;
  policy.rsset_layout_regions[0].offset = 0x022CU;
  policy.rsset_layout_regions[0].size = 4U;
  policy.rsset_layout_regions[0].flags = M68K_ANALYSIS_RSSET_LAYOUT_REGION_FLAG_APP_LAYOUT;
  snprintf(policy.rsset_layout_regions[0].symbol, sizeof(policy.rsset_layout_regions[0].symbol),
    "app_startup_options_buffer");
  snprintf(policy.rsset_layout_regions[0].storage_kind, sizeof(policy.rsset_layout_regions[0].storage_kind), "pointer");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "app_startup_options_buffer RS.L 1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "app_022C RS.L") == NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l d0,app_startup_options_buffer(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l app_startup_options_buffer(a6),a0\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_supports_named_rsset_layouts(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[2] = {0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.rsset_layout_region_count = 2U;
  policy.rsset_layout_regions[0].offset = 0x0004U;
  policy.rsset_layout_regions[0].size = 4U;
  policy.rsset_layout_regions[0].flags = M68K_ANALYSIS_RSSET_LAYOUT_REGION_FLAG_APP_LAYOUT;
  snprintf(policy.rsset_layout_regions[0].layout_name, sizeof(policy.rsset_layout_regions[0].layout_name), "app");
  snprintf(policy.rsset_layout_regions[0].base_symbol, sizeof(policy.rsset_layout_regions[0].base_symbol),
    "__amiga_app_base__");
  snprintf(policy.rsset_layout_regions[0].symbol, sizeof(policy.rsset_layout_regions[0].symbol), "app_Window");
  snprintf(policy.rsset_layout_regions[1].layout_name, sizeof(policy.rsset_layout_regions[1].layout_name), "work");
  snprintf(policy.rsset_layout_regions[1].base_symbol, sizeof(policy.rsset_layout_regions[1].base_symbol),
    "__game_work_base__");
  snprintf(policy.rsset_layout_regions[1].sizeof_symbol, sizeof(policy.rsset_layout_regions[1].sizeof_symbol),
    "work_SIZEOF");
  policy.rsset_layout_regions[1].offset = 0x0002U;
  policy.rsset_layout_regions[1].size = 2U;
  snprintf(policy.rsset_layout_regions[1].symbol, sizeof(policy.rsset_layout_regions[1].symbol), "work_flags");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "app_Window RS.L 1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "app_SIZEOF EQU __RS\n") != NULL);
  M68K_C_ASSERT(strstr(source, "work_flags RS.W 1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "work_SIZEOF EQU __RS\n") != NULL);
  M68K_C_ASSERT(source != NULL && strstr(source, "app_Window RS.L 1\n") <
    strstr(source, "work_flags RS.W 1\n"));
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_infers_lvo_from_base_field_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[20] = {
    0x24u, 0x40u,
    0x25u, 0x4eu, 0x00u, 0x22u,
    0x2cu, 0x6fu, 0x00u, 0x08u,
    0x2cu, 0x6eu, 0x00u, 0x22u,
    0x4eu, 0xaeu, 0xfeu, 0xdau,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 2U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_DATA;
  policy.register_seeds[0].reg_index = 0U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "__amiga_app_base__");
  policy.register_seeds[1].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[1].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[1].reg_index = 6U;
  policy.register_seeds[1].has_entry_offset = 1U;
  policy.register_seeds[1].has_section_index = 1U;
  policy.register_seeds[1].entry_offset = 0U;
  policy.register_seeds[1].section_index = 0U;
  snprintf(policy.register_seeds[1].name, sizeof(policy.register_seeds[1].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l d0,a2\n") != NULL);
  M68K_C_ASSERT(strstr(source, "app_ExecBase RS.L 1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l a6,app_ExecBase(a2)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l $0008(a7),a6\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l app_ExecBase(a6),a6\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOFindTask(a6)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_infers_openlibrary_base_field_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[62] = {
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xffu, 0x3au,
    0x2cu, 0x40u,
    0x43u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x2cu,
    0x2fu, 0x0eu,
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xfdu, 0xd8u,
    0x2cu, 0x5fu,
    0x2du, 0x40u, 0x00u, 0xbeu,
    0x2cu, 0x6eu, 0x00u, 0xbeu,
    0x4eu, 0xaeu, 0xfeu, 0xf2u,
    0x4eu, 0x75u,
    0x00u, 0x00u,
    0x69u, 0x6eu, 0x74u, 0x75u, 0x69u, 0x74u, 0x69u, 0x6fu,
    0x6eu, 0x2eu, 0x6cu, 0x69u, 0x62u, 0x72u, 0x61u, 0x72u,
    0x79u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOOpenLibrary(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "app_IntuitionBase RS.L 1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l d0,app_IntuitionBase(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l app_IntuitionBase(a6),a6\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOSetPointer(a6)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_infers_openlibrary_unowned_base_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[45] = {
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x43u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x1cu,
    0x4eu, 0xaeu, 0xfdu, 0xd8u,
    0x29u, 0x40u, 0x80u, 0x0eu,
    0x2cu, 0x6cu, 0x80u, 0x0eu,
    0x4eu, 0xaeu, 0xfeu, 0xf2u,
    0x4eu, 0x75u,
    0x67u, 0x72u, 0x61u, 0x70u, 0x68u, 0x69u, 0x63u, 0x73u,
    0x2eu, 0x6cu, 0x69u, 0x62u, 0x72u, 0x61u, 0x72u, 0x79u,
    0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOOpenLibrary(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l d0,-$7FF2(a4)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l -$7FF2(a4),a6\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOWaitTOF(a6)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_infers_openlibrary_helper_unowned_base_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kSectionAnalysisIR *analysis_section;
  char *source = NULL;
  uint8_t bytes[59] = {
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x43u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x2au,
    0x61u, 0x00u, 0x00u, 0x10u,
    0x29u, 0x40u, 0x80u, 0x0eu,
    0x2cu, 0x6cu, 0x80u, 0x0eu,
    0x4eu, 0xaeu, 0xfeu, 0xf2u,
    0x4eu, 0x75u,
    0x2fu, 0x0eu,
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xfdu, 0xd8u,
    0x2cu, 0x5fu,
    0x4eu, 0x75u,
    0x67u, 0x72u, 0x61u, 0x70u, 0x68u, 0x69u, 0x63u, 0x73u,
    0x2eu, 0x6cu, 0x69u, 0x62u, 0x72u, 0x61u, 0x72u, 0x79u,
    0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tbsr.w loc_0_0000001C\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOOpenLibrary(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l d0,-$7FF2(a4)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l -$7FF2(a4),a6\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOWaitTOF(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "__amiga_local_base") == NULL);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.section_count);
  analysis_section = &source_analysis.sections[0];
  M68K_C_ASSERT_U32(0U, (uint32_t)analysis_section->recovered_platform_base_slot_count);
  M68K_C_ASSERT_U32(0U, (uint32_t)analysis_section->recovered_platform_unresolved_typed_access_count);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_infers_openlibrary_global_base_slot(void) {
  M68kObject object;
  M68kSection code_section;
  M68kSection data_section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kSymbol symbol;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t code_bytes[49] = {
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x43u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x20u,
    0x4eu, 0xaeu, 0xfdu, 0xd8u,
    0x23u, 0xc0u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x2cu, 0x79u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0xaeu, 0xfeu, 0xf2u,
    0x4eu, 0x75u,
    0x67u, 0x72u, 0x61u, 0x70u, 0x68u, 0x69u, 0x63u, 0x73u,
    0x2eu, 0x6cu, 0x69u, 0x62u, 0x72u, 0x61u, 0x72u, 0x79u,
    0x00u
  };
  uint8_t data_bytes[4] = {0};
  memset(&code_section, 0, sizeof(code_section));
  memset(&data_section, 0, sizeof(data_section));
  memset(&fixup, 0, sizeof(fixup));
  memset(&symbol, 0, sizeof(symbol));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  code_section.kind = M68K_SECTION_CODE;
  code_section.size = sizeof(code_bytes);
  code_section.data_size = sizeof(code_bytes);
  code_section.data = code_bytes;
  data_section.kind = M68K_SECTION_DATA;
  data_section.size = sizeof(data_bytes);
  data_section.data_size = sizeof(data_bytes);
  data_section.data = data_bytes;
  added = m68k_object_add_section(&object, &code_section);
  M68K_C_ASSERT(added.ok);
  added = m68k_object_add_section(&object, &data_section);
  M68K_C_ASSERT(added.ok);
  symbol.name = "GfxBase";
  symbol.binding = M68K_SYMBOL_LOCAL;
  symbol.defined = 1;
  symbol.section_index = 1U;
  symbol.value = 0U;
  M68K_C_ASSERT(m68k_object_add_symbol(&object, &symbol).ok);
  fixup.section_index = 0U;
  fixup.offset = 0x10U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 1U;
  fixup.has_target_section = 1;
  M68K_C_ASSERT(m68k_object_add_fixup(&object, &fixup).ok);
  memset(&fixup, 0, sizeof(fixup));
  fixup.section_index = 0U;
  fixup.offset = 0x16U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 1U;
  fixup.has_target_section = 1;
  M68K_C_ASSERT(m68k_object_add_fixup(&object, &fixup).ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOOpenLibrary(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l d0,GfxBase.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l GfxBase.l,a6\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOWaitTOF(a6)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_infers_openlibrary_helper_output_global_base_slot(void) {
  M68kObject object;
  M68kSection code_section;
  M68kSection data_section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kSymbol symbol;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t code_bytes[63] = {
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x43u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x2eu,
    0x61u, 0x00u, 0x00u, 0x14u,
    0x23u, 0xc0u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x2cu, 0x79u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0xaeu, 0xfeu, 0xf2u,
    0x4eu, 0x75u,
    0x2fu, 0x0eu,
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xfdu, 0xd8u,
    0x2cu, 0x5fu,
    0x4eu, 0x75u,
    0x67u, 0x72u, 0x61u, 0x70u, 0x68u, 0x69u, 0x63u, 0x73u,
    0x2eu, 0x6cu, 0x69u, 0x62u, 0x72u, 0x61u, 0x72u, 0x79u,
    0x00u
  };
  uint8_t data_bytes[4] = {0};
  memset(&code_section, 0, sizeof(code_section));
  memset(&data_section, 0, sizeof(data_section));
  memset(&fixup, 0, sizeof(fixup));
  memset(&symbol, 0, sizeof(symbol));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  code_section.kind = M68K_SECTION_CODE;
  code_section.size = sizeof(code_bytes);
  code_section.data_size = sizeof(code_bytes);
  code_section.data = code_bytes;
  data_section.kind = M68K_SECTION_DATA;
  data_section.size = sizeof(data_bytes);
  data_section.data_size = sizeof(data_bytes);
  data_section.data = data_bytes;
  added = m68k_object_add_section(&object, &code_section);
  M68K_C_ASSERT(added.ok);
  added = m68k_object_add_section(&object, &data_section);
  M68K_C_ASSERT(added.ok);
  symbol.name = "GfxBase";
  symbol.binding = M68K_SYMBOL_LOCAL;
  symbol.defined = 1;
  symbol.section_index = 1U;
  symbol.value = 0U;
  M68K_C_ASSERT(m68k_object_add_symbol(&object, &symbol).ok);
  fixup.section_index = 0U;
  fixup.offset = 0x10U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 1U;
  fixup.has_target_section = 1;
  M68K_C_ASSERT(m68k_object_add_fixup(&object, &fixup).ok);
  memset(&fixup, 0, sizeof(fixup));
  fixup.section_index = 0U;
  fixup.offset = 0x16U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 1U;
  fixup.has_target_section = 1;
  M68K_C_ASSERT(m68k_object_add_fixup(&object, &fixup).ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tbsr.w loc_0_00000020\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOOpenLibrary(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l d0,GfxBase.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l GfxBase.l,a6\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOWaitTOF(a6)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_infers_opendevice_base_field_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[69] = {
    0x41u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x38u,
    0x43u, 0xeeu, 0x00u, 0x40u,
    0x33u, 0x7cu, 0x00u, 0x09u, 0x00u, 0x1cu,
    0x2fu, 0x0eu,
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xfeu, 0x44u,
    0x2cu, 0x5fu,
    0x20u, 0x6eu, 0x00u, 0x54u,
    0x0cu, 0x68u, 0x00u, 0x24u, 0x00u, 0x14u,
    0x2cu, 0x6eu, 0x00u, 0x54u,
    0x4eu, 0xaeu, 0xffu, 0xbeu,
    0x2cu, 0x6eu, 0x00u, 0x54u,
    0x4eu, 0xaeu, 0xffu, 0xd0u,
    0x4eu, 0x75u,
    0x74u, 0x69u, 0x6du, 0x65u, 0x72u, 0x2eu, 0x64u,
    0x65u, 0x76u, 0x69u, 0x63u, 0x65u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOOpenDevice(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "app_timer_device_iorequest RS.B ") != NULL);
  M68K_C_ASSERT(strstr(source, "app_TimerBase ") != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l app_timer_device_iorequest(a6),a1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #$9,IO_COMMAND(a1)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l app_TimerBase(a6),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tcmpi.w #36,LIB_VERSION(a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l app_TimerBase(a6),a6\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOGetSysTime(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOSubTime(a6)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(2U, profile.platform_base_slot_count);
  M68K_C_ASSERT_U32(3U, profile.platform_call_count);
  M68K_C_ASSERT(profile.platform_effect_count > 0U);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_renders_typed_app_slot_field_region(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  const char *timer_include, *custom_include, *rsset_line, *app_sizeof_line, *intf_equ_line, *section_line;
  uint8_t bytes[22] = {
    0x41u, 0xecu, 0x01u, 0x00u,
    0x4eu, 0xaeu, 0xffu, 0xbeu,
    0x20u, 0x2cu, 0x01u, 0x04u,
    0x33u, 0xfcu, 0x7fu, 0xffu, 0x00u, 0xdfu, 0xf0u, 0x9au,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 2U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 4U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "__amiga_app_base__");
  policy.register_seeds[1].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[1].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[1].reg_index = 6U;
  policy.register_seeds[1].has_entry_offset = 1U;
  policy.register_seeds[1].has_section_index = 1U;
  policy.register_seeds[1].entry_offset = 0U;
  policy.register_seeds[1].section_index = 0U;
  snprintf(policy.register_seeds[1].name, sizeof(policy.register_seeds[1].name), "timer.device");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  timer_include = strstr(source, "    INCLUDE \"devices/timer.i\"\n");
  custom_include = strstr(source, "    INCLUDE \"hardware/custom.i\"\n");
  rsset_line = strstr(source, "    RSSET ");
  app_sizeof_line = strstr(source, "app_SIZEOF EQU __RS\n");
  intf_equ_line = strstr(source, "INTF_CLRALL\tEQU\t$7FFF\n");
  section_line = strstr(source, "    SECTION ");
  M68K_C_ASSERT(timer_include != NULL);
  M68K_C_ASSERT(custom_include != NULL);
  M68K_C_ASSERT(rsset_line != NULL);
  M68K_C_ASSERT(app_sizeof_line != NULL);
  M68K_C_ASSERT(intf_equ_line != NULL);
  M68K_C_ASSERT(section_line != NULL);
  M68K_C_ASSERT(timer_include < custom_include);
  M68K_C_ASSERT(custom_include < rsset_line);
  M68K_C_ASSERT(rsset_line < app_sizeof_line);
  M68K_C_ASSERT(app_sizeof_line < intf_equ_line);
  M68K_C_ASSERT(intf_equ_line < section_line);
  M68K_C_ASSERT(strstr(source, "app_0100 RS.B 8\n") != NULL);
  M68K_C_ASSERT(strstr(source, "app_0104") == NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l app_0100(a4),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOGetSysTime(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l app_0100+TV_MICRO(a4),d0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #INTF_CLRALL,_custom+intena.l\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_keeps_typed_app_slot_interior_out_of_flat_rsset(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  char *analysis_json = NULL;
  uint8_t bytes[14] = {
    0x41u, 0xecu, 0x01u, 0x00u,
    0x4eu, 0xaeu, 0xffu, 0xbeu,
    0x30u, 0x2cu, 0x01u, 0x02u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 2U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 4U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "__amiga_app_base__");
  policy.register_seeds[1].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[1].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[1].reg_index = 6U;
  policy.register_seeds[1].has_entry_offset = 1U;
  policy.register_seeds[1].has_section_index = 1U;
  policy.register_seeds[1].entry_offset = 0U;
  policy.register_seeds[1].section_index = 0U;
  snprintf(policy.register_seeds[1].name, sizeof(policy.register_seeds[1].name), "timer.device");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT_U32(1U, (uint32_t)source_analysis.base_layout_field_count);
  M68K_C_ASSERT_STR("app_0100", source_analysis.base_layout_fields[0].symbol);
  M68K_C_ASSERT_STR("TIMEVAL", m68k_platform_name_ref_resolve_text_or_fallback(
    &source_analysis.base_layout_fields[0].owner_struct_ref,
    source_analysis.base_layout_fields[0].owner_struct_name));
  M68K_C_ASSERT_U32(0x0100U, source_analysis.base_layout_fields[0].offset);
  M68K_C_ASSERT_U32(8U, source_analysis.base_layout_fields[0].size);
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"record_kind\":\"base_layout_field\",\"memory_kind\":\"base_layout_field\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"owner_struct_name\":\"TIMEVAL\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"root_struct_name\":\"TIMEVAL\"") != NULL);
  M68K_C_ASSERT(strstr(source, "app_0100 RS.B 8\n") != NULL);
  M68K_C_ASSERT(strstr(source, "app_0102") == NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w app_0100+TV_SECS+2(a4),d0\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  free(analysis_json);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_keeps_app_slot_aliases_in_rs_region(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  const char *rsset_line, *slot_line, *app_sizeof_line, *alias_rsset_line, *alias_line, *section_line;
  uint8_t bytes[10] = {
    0x20u, 0x2cu, 0x00u, 0x00u,
    0x12u, 0x2cu, 0x00u, 0x01u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 4U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "__amiga_app_base__");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT_U32(2U, (uint32_t)source_analysis.base_layout_field_count);
  M68K_C_ASSERT_STR("app", source_analysis.base_layout_fields[0].layout_name);
  M68K_C_ASSERT_STR("__amiga_app_base__", source_analysis.base_layout_fields[0].base_symbol);
  M68K_C_ASSERT_U32(M68K_BASE_LAYOUT_FIELD_SOURCE_APP_SLOT_ACCESS,
    source_analysis.base_layout_fields[0].source_kind);
  M68K_C_ASSERT_U32(M68K_FACT_CONFIDENCE_TOOL_INFERRED, source_analysis.base_layout_fields[0].confidence);
  M68K_C_ASSERT_U32(0U, source_analysis.base_layout_fields[0].conflicted);
  M68K_C_ASSERT_U32(1U, source_analysis.base_layout_fields[1].alias);
  M68K_C_ASSERT_STR("app_0000", source_analysis.base_layout_fields[1].alias_of_symbol);
  rsset_line = strstr(source, "    RSSET 0\n");
  slot_line = strstr(source, "app_0000 RS.L 1\n");
  app_sizeof_line = strstr(source, "app_SIZEOF EQU __RS\n");
  alias_rsset_line = strstr(source, "    RSSET $0001\n");
  alias_line = strstr(source, "app_0001 RS.B 1\n");
  section_line = strstr(source, "    SECTION ");
  M68K_C_ASSERT(rsset_line != NULL);
  M68K_C_ASSERT(slot_line != NULL);
  M68K_C_ASSERT(app_sizeof_line != NULL);
  M68K_C_ASSERT(alias_rsset_line != NULL);
  M68K_C_ASSERT(alias_line != NULL);
  M68K_C_ASSERT(section_line != NULL);
  M68K_C_ASSERT(rsset_line < slot_line);
  M68K_C_ASSERT(slot_line < app_sizeof_line);
  M68K_C_ASSERT(app_sizeof_line < alias_rsset_line);
  M68K_C_ASSERT(alias_rsset_line < alias_line);
  M68K_C_ASSERT(alias_line < section_line);
  M68K_C_ASSERT(strstr(source, "app_0001 EQU $0001\n") == NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l app_0000(a4),d0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.b app_0001(a4),d1\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_propagates_typed_base_through_stack_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[55] = {
    0x41u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x2au,
    0x43u, 0xeeu, 0x00u, 0x40u,
    0x2fu, 0x0eu,
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xfeu, 0x44u,
    0x2cu, 0x5fu,
    0x20u, 0x6eu, 0x00u, 0x54u,
    0x2fu, 0x48u, 0x01u, 0x00u,
    0x20u, 0x6fu, 0x01u, 0x00u,
    0x0cu, 0x68u, 0x00u, 0x24u, 0x00u, 0x14u,
    0x4eu, 0x75u,
    0x74u, 0x69u, 0x6du, 0x65u, 0x72u, 0x2eu, 0x64u,
    0x65u, 0x76u, 0x69u, 0x63u, 0x65u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOOpenDevice(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l app_TimerBase(a6),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l $0100(a7),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tcmpi.w #36,LIB_VERSION(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_propagates_typed_base_through_absolute_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[59] = {
    0x41u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x2eu,
    0x43u, 0xeeu, 0x00u, 0x40u,
    0x2fu, 0x0eu,
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xfeu, 0x44u,
    0x2cu, 0x5fu,
    0x20u, 0x6eu, 0x00u, 0x54u,
    0x23u, 0xc8u, 0x00u, 0x00u, 0x00u, 0x80u,
    0x20u, 0x79u, 0x00u, 0x00u, 0x00u, 0x80u,
    0x0cu, 0x68u, 0x00u, 0x24u, 0x00u, 0x14u,
    0x4eu, 0x75u,
    0x74u, 0x69u, 0x6du, 0x65u, 0x72u, 0x2eu, 0x64u,
    0x65u, 0x76u, 0x69u, 0x63u, 0x65u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOOpenDevice(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l app_TimerBase(a6),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tcmpi.w #36,LIB_VERSION(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_propagates_api_output_type_to_access(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[12] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x20u, 0x40u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOCreateMsgPort(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l d0,a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_uses_makelibrary_output_type(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[14] = {
    0x4eu, 0xaeu, 0xffu, 0xacu,
    0x20u, 0x40u,
    0x0cu, 0x68u, 0x00u, 0x24u, 0x00u, 0x14u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOMakeLibrary(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tcmpi.w #36,LIB_VERSION(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_records_unresolved_typed_field_without_rendering_field(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  const M68kSectionAnalysisIR *analysis_section;
  const M68kRecoveredPlatformUnresolvedTypedAccessIR *unresolved = NULL;
  char *analysis_json = NULL;
  char *source = NULL;
  size_t index;
  uint8_t bytes[12] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x20u, 0x40u,
    0x4au, 0x28u, 0x01u, 0x00u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(1U, (uint32_t)analysis.section_count);
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_unresolved_typed_access_count; ++index) {
    const M68kRecoveredPlatformUnresolvedTypedAccessIR *access =
      &analysis_section->recovered_platform_unresolved_typed_accesses[index];
    const char *root_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref,
      access->root_struct_name);
    if (access->offset == 6U && access->operand_index == 0U && access->base_reg == 0U &&
        access->displacement == 0x0100 && root_struct_name != NULL && strcmp(root_struct_name, "MP") == 0) {
      unresolved = access;
      break;
    }
  }
  M68K_C_ASSERT(unresolved != NULL);
  M68K_C_ASSERT(unresolved->struct_size > 0U);
  M68K_C_ASSERT_INT(M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_CUSTOM_TAIL_OR_MISTYPED_BASE,
    unresolved->classification);
  M68K_C_ASSERT_U32(0U, unresolved->container_candidate_count);
  M68K_C_ASSERT_INT(M68K_PLATFORM_TYPE_PROVENANCE_API_OUTPUT, unresolved->type_provenance_kind);
  M68K_C_ASSERT_U32(0U, unresolved->type_provenance_offset);
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"classification_id\":2,\"classification\":\"custom_tail_or_mistyped_base\"") != NULL);
  free(analysis_json);
  m68k_ir_source_analysis_destroy(&analysis);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b $0100(a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_classifies_unique_prefix_extension_without_rendering_field(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  const M68kSectionAnalysisIR *analysis_section;
  const M68kRecoveredPlatformUnresolvedTypedAccessIR *unresolved = NULL;
  const char *container_struct_name;
  const char *refined_struct_name;
  char *source = NULL;
  size_t index;
  uint8_t bytes[16] = {
    0x4eu, 0xaeu, 0xfeu, 0x7au,
    0x20u, 0x40u,
    0x20u, 0x28u, 0x00u, 0x40u,
    0x4au, 0x68u, 0x00u, 0x40u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(1U, (uint32_t)analysis.section_count);
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_unresolved_typed_access_count; ++index) {
    const M68kRecoveredPlatformUnresolvedTypedAccessIR *access =
      &analysis_section->recovered_platform_unresolved_typed_accesses[index];
    const char *root_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref,
      access->root_struct_name);
    if (access->offset == 6U && access->operand_index == 0U && access->base_reg == 0U &&
        access->displacement == 0x0040 && root_struct_name != NULL && strcmp(root_struct_name, "MP") == 0) {
      unresolved = access;
      break;
    }
  }
  M68K_C_ASSERT(unresolved != NULL);
  M68K_C_ASSERT_INT(M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION, unresolved->classification);
  M68K_C_ASSERT_U32(1U, unresolved->container_candidate_count);
  container_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&unresolved->container_struct_ref,
    unresolved->container_struct_name);
  M68K_C_ASSERT_STR("ConUnit", container_struct_name);
  M68K_C_ASSERT_STR("cu_YCCP", unresolved->container_field_expr);
  M68K_C_ASSERT_INT(1, unresolved->refinement_applied);
  refined_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&unresolved->refined_struct_ref,
    unresolved->refined_struct_name);
  M68K_C_ASSERT_STR("ConUnit", refined_struct_name);
  m68k_ir_source_analysis_destroy(&analysis);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l $0040(a0),d0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.w cu_YCCP(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_refines_ambiguous_prefix_by_exact_access_size(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  const M68kSectionAnalysisIR *analysis_section;
  const M68kRecoveredPlatformUnresolvedTypedAccessIR *unresolved = NULL;
  const char *container_struct_name;
  const char *refined_struct_name;
  char *source = NULL;
  size_t index;
  uint8_t bytes[16] = {
    0x4eu, 0xaeu, 0xfdu, 0xd8u,
    0x20u, 0x40u,
    0x30u, 0x28u, 0x00u, 0xceu,
    0x4au, 0x68u, 0x00u, 0xceu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(1U, (uint32_t)analysis.section_count);
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_unresolved_typed_access_count; ++index) {
    const M68kRecoveredPlatformUnresolvedTypedAccessIR *access =
      &analysis_section->recovered_platform_unresolved_typed_accesses[index];
    const char *root_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref,
      access->root_struct_name);
    if (access->offset == 6U && access->operand_index == 0U && access->base_reg == 0U &&
        access->displacement == 0x00CE && root_struct_name != NULL && strcmp(root_struct_name, "LIB") == 0) {
      unresolved = access;
      break;
    }
  }
  M68K_C_ASSERT(unresolved != NULL);
  M68K_C_ASSERT_INT(M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION, unresolved->classification);
  M68K_C_ASSERT(unresolved->container_candidate_count > 1U);
  container_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&unresolved->container_struct_ref,
    unresolved->container_struct_name);
  M68K_C_ASSERT_STR("GfxBase", container_struct_name);
  M68K_C_ASSERT_STR("gb_DisplayFlags", unresolved->container_field_expr);
  M68K_C_ASSERT_INT(1, unresolved->refinement_applied);
  refined_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&unresolved->refined_struct_ref,
    unresolved->refined_struct_name);
  M68K_C_ASSERT_STR("GfxBase", refined_struct_name);
  M68K_C_ASSERT_INT(M68K_PLATFORM_TYPE_PROVENANCE_PREFIX_REFINEMENT, unresolved->type_provenance_kind);
  M68K_C_ASSERT_U32(6U, unresolved->type_provenance_offset);
  m68k_ir_source_analysis_destroy(&analysis);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w $00CE(a0),d0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.w gb_DisplayFlags(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_propagates_prefix_output_through_base_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  const M68kSectionAnalysisIR *analysis_section;
  const M68kRecoveredPlatformUnresolvedTypedAccessIR *unresolved = NULL;
  char *source = NULL;
  size_t index;
  uint8_t bytes[20] = {
    0x4eu, 0xaeu, 0xfeu, 0x80u,
    0x2bu, 0x40u, 0x00u, 0x04u,
    0x20u, 0x6du, 0x00u, 0x04u,
    0x20u, 0x28u, 0x00u, 0x24u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(1U, (uint32_t)analysis.section_count);
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_unresolved_typed_access_count; ++index) {
    const M68kRecoveredPlatformUnresolvedTypedAccessIR *access =
      &analysis_section->recovered_platform_unresolved_typed_accesses[index];
    const char *root_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref,
      access->root_struct_name);
    if (access->offset == 12U && access->operand_index == 0U && access->base_reg == 0U &&
        access->displacement == 0x0024 && root_struct_name != NULL && strcmp(root_struct_name, "MN") == 0) {
      unresolved = access;
      break;
    }
  }
  M68K_C_ASSERT(unresolved != NULL);
  M68K_C_ASSERT_INT(M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION, unresolved->classification);
  M68K_C_ASSERT(unresolved->container_candidate_count > 1U);
  M68K_C_ASSERT_INT(0, unresolved->refinement_applied);
  M68K_C_ASSERT(m68k_platform_name_ref_resolve_text_or_fallback(&unresolved->container_struct_ref,
    unresolved->container_struct_name) == NULL);
  M68K_C_ASSERT(m68k_platform_name_ref_resolve_text_or_fallback(&unresolved->refined_struct_ref,
    unresolved->refined_struct_name) == NULL);
  m68k_ir_source_analysis_destroy(&analysis);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l d0,$0004(a5)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l $0004(a5),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l $0024(a0),d0\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_refines_prefix_storage_from_api_input(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[26] = {
    0x4eu, 0xaeu, 0xfeu, 0x8cu,
    0x2bu, 0x40u, 0x00u, 0x04u,
    0x22u, 0x6du, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xfeu, 0x38u,
    0x20u, 0x6du, 0x00u, 0x04u,
    0x20u, 0x28u, 0x00u, 0x24u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOGetMsg(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVODoIO(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l IO_LENGTH(a0),d0\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_promotes_unique_prefix_type_through_base_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  const M68kSectionAnalysisIR *analysis_section;
  const M68kRecoveredPlatformUnresolvedTypedAccessIR *unresolved = NULL;
  const char *refined_struct_name;
  char *source = NULL;
  size_t index;
  uint8_t bytes[26] = {
    0x4eu, 0xaeu, 0xfeu, 0x7au,
    0x2bu, 0x40u, 0x00u, 0x04u,
    0x20u, 0x6du, 0x00u, 0x04u,
    0x20u, 0x28u, 0x00u, 0x40u,
    0x22u, 0x6du, 0x00u, 0x04u,
    0x4au, 0x69u, 0x00u, 0x40u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(1U, (uint32_t)analysis.section_count);
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_unresolved_typed_access_count; ++index) {
    const M68kRecoveredPlatformUnresolvedTypedAccessIR *access =
      &analysis_section->recovered_platform_unresolved_typed_accesses[index];
    const char *root_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref,
      access->root_struct_name);
    if (access->offset == 12U && access->operand_index == 0U && access->base_reg == 0U &&
        access->displacement == 0x0040 && root_struct_name != NULL && strcmp(root_struct_name, "MP") == 0) {
      unresolved = access;
      break;
    }
  }
  M68K_C_ASSERT(unresolved != NULL);
  M68K_C_ASSERT_INT(M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION, unresolved->classification);
  M68K_C_ASSERT_INT(1, unresolved->refinement_applied);
  refined_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&unresolved->refined_struct_ref,
    unresolved->refined_struct_name);
  M68K_C_ASSERT_STR("ConUnit", refined_struct_name);
  m68k_ir_source_analysis_destroy(&analysis);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l $0040(a0),d0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l $0004(a5),a1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.w cu_YCCP(a1)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_refines_rexxmsg_prefix_by_exact_field_size(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  const M68kSectionAnalysisIR *analysis_section;
  const M68kRecoveredPlatformUnresolvedTypedAccessIR *unresolved = NULL;
  const char *refined_struct_name;
  char *source = NULL;
  size_t index;
  uint8_t bytes[16] = {
    0x4eu, 0xaeu, 0xfeu, 0x80u,
    0x20u, 0x40u,
    0x20u, 0x28u, 0x00u, 0x1cu,
    0x4au, 0xa8u, 0x00u, 0x1cu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_unresolved_typed_access_count; ++index) {
    const M68kRecoveredPlatformUnresolvedTypedAccessIR *access =
      &analysis_section->recovered_platform_unresolved_typed_accesses[index];
    const char *root_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref,
      access->root_struct_name);
    if (access->offset == 6U && access->operand_index == 0U && access->base_reg == 0U &&
        access->displacement == 0x001C && root_struct_name != NULL && strcmp(root_struct_name, "MN") == 0) {
      unresolved = access;
      break;
    }
  }
  M68K_C_ASSERT(unresolved != NULL);
  M68K_C_ASSERT_INT(M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION, unresolved->classification);
  M68K_C_ASSERT_INT(1, unresolved->refinement_applied);
  refined_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&unresolved->refined_struct_ref,
    unresolved->refined_struct_name);
  M68K_C_ASSERT_STR("RexxMsg", refined_struct_name);
  M68K_C_ASSERT_STR("rm_Action", unresolved->container_field_expr);
  m68k_ir_source_analysis_destroy(&analysis);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l $001C(a0),d0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.l rm_Action(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_refines_textfont_common_prefix_by_exact_field_size(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  const M68kSectionAnalysisIR *analysis_section;
  const M68kRecoveredPlatformUnresolvedTypedAccessIR *unresolved = NULL;
  const char *refined_struct_name;
  char *source = NULL;
  size_t index;
  uint8_t bytes[16] = {
    0x4eu, 0xaeu, 0xfeu, 0x80u,
    0x20u, 0x40u,
    0x30u, 0x28u, 0x00u, 0x18u,
    0x4au, 0x68u, 0x00u, 0x18u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_unresolved_typed_access_count; ++index) {
    const M68kRecoveredPlatformUnresolvedTypedAccessIR *access =
      &analysis_section->recovered_platform_unresolved_typed_accesses[index];
    const char *root_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref,
      access->root_struct_name);
    if (access->offset == 6U && access->operand_index == 0U && access->base_reg == 0U &&
        access->displacement == 0x0018 && root_struct_name != NULL && strcmp(root_struct_name, "MN") == 0) {
      unresolved = access;
      break;
    }
  }
  M68K_C_ASSERT(unresolved != NULL);
  M68K_C_ASSERT_INT(M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION, unresolved->classification);
  M68K_C_ASSERT(unresolved->container_candidate_count > 1U);
  M68K_C_ASSERT_INT(1, unresolved->refinement_applied);
  refined_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&unresolved->refined_struct_ref,
    unresolved->refined_struct_name);
  M68K_C_ASSERT_STR("TextFont", refined_struct_name);
  M68K_C_ASSERT_STR("tf_XSize", unresolved->container_field_expr);
  m68k_ir_source_analysis_destroy(&analysis);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w $0018(a0),d0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.w tf_XSize(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_propagates_api_output_type_through_lea_copy(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[14] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x20u, 0x40u,
    0x43u, 0xd0u,
    0x4au, 0x29u, 0x00u, 0x0fu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOCreateMsgPort(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l (a0),a1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a1)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_propagates_api_output_type_through_global_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  char *analysis_json = NULL;
  char *source = NULL;
  const M68kSectionAnalysisIR *analysis_section;
  size_t index;
  int saw_global_slot = 0;
  int saw_typed_access = 0;
  uint8_t bytes[22] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x23u, 0xc0u, 0x00u, 0x00u, 0x01u, 0x00u,
    0x20u, 0x79u, 0x00u, 0x00u, 0x01u, 0x00u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(1U, (uint32_t)analysis.section_count);
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &analysis_section->recovered_platform_effects[index];
    const char *type_name;
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT) continue;
    type_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.type_ref,
      effect->payload.typed.type_name);
    if (effect->target_section_index == 0U && effect->target_offset == 0x100U &&
        type_name != NULL && strcmp(type_name, "MP") == 0) {
      saw_global_slot = 1;
    }
  }
  for (index = 0U; index < analysis_section->recovered_platform_typed_access_count; ++index) {
    const M68kRecoveredPlatformTypedAccessIR *access =
      &analysis_section->recovered_platform_typed_accesses[index];
    if (access->offset == 16U && access->operand_index == 0U &&
        access->field_expr != NULL && strcmp(access->field_expr, "MP_SIGBIT") == 0) {
      M68K_C_ASSERT(access->struct_size > 0U);
      M68K_C_ASSERT_U32(1U, (uint32_t)access->field_size);
      M68K_C_ASSERT_U32((uint32_t)M68K_PLATFORM_TYPE_PROVENANCE_API_OUTPUT,
        (uint32_t)access->type_provenance_kind);
      M68K_C_ASSERT_U32(0U, (uint32_t)access->type_provenance_section_index);
      M68K_C_ASSERT_U32(0U, access->type_provenance_offset);
      saw_typed_access = 1;
    }
  }
  M68K_C_ASSERT(saw_global_slot);
  M68K_C_ASSERT(saw_typed_access);
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"record_kind\":\"platform_typed_access\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"memory_kind\":\"platform_struct_field\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"record_kind\":\"platform_storage_effect\",\"memory_kind\":\"typed_global_slot\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"effect_kind_name\":\"write_typed_global_slot\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"target_section_index\":0,\"target_offset\":256") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"range_space_kind\":4,\"range_space\":\"section_relative\",\"range_start\":256,"
    "\"range_size\":4,\"range_end\":260") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"struct_size\":") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"field_size\":1") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"field_expr\":\"MP_SIGBIT\"") != NULL);
  free(analysis_json);
  m68k_ir_source_analysis_destroy(&analysis);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_propagates_global_slot_reload_through_data_register_copy(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  char *source = NULL;
  const M68kSectionAnalysisIR *analysis_section;
  size_t index;
  int saw_global_slot = 0;
  int saw_typed_access = 0;
  uint8_t bytes[28] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x23u, 0xc0u, 0x00u, 0x00u, 0x01u, 0x00u,
    0x4eu, 0xaeu, 0xffu, 0x7cu,
    0x22u, 0x39u, 0x00u, 0x00u, 0x01u, 0x00u,
    0x20u, 0x41u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  M68K_C_ASSERT_U32(1U, (uint32_t)analysis.section_count);
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &analysis_section->recovered_platform_effects[index];
    const char *type_name;
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT) continue;
    type_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.type_ref,
      effect->payload.typed.type_name);
    if (effect->target_section_index == 0U && effect->target_offset == 0x100U &&
        type_name != NULL && strcmp(type_name, "MP") == 0) {
      saw_global_slot = 1;
    }
  }
  for (index = 0U; index < analysis_section->recovered_platform_typed_access_count; ++index) {
    const M68kRecoveredPlatformTypedAccessIR *access =
      &analysis_section->recovered_platform_typed_accesses[index];
    if (access->offset == 22U && access->operand_index == 0U &&
        access->field_expr != NULL && strcmp(access->field_expr, "MP_SIGBIT") == 0) {
      saw_typed_access = 1;
    }
  }
  M68K_C_ASSERT(saw_global_slot);
  M68K_C_ASSERT(saw_typed_access);
  m68k_ir_source_analysis_destroy(&analysis);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOForbid(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l d1,a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_reports_lookup_storage_write_site_provenance(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  const M68kSectionAnalysisIR *analysis_section;
  const M68kRecoveredPlatformUnresolvedTypedAccessIR *unresolved = NULL;
  size_t index;
  uint8_t bytes[32] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x23u, 0xc0u, 0x00u, 0x00u, 0x01u, 0x00u,
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x23u, 0xc0u, 0x00u, 0x00u, 0x01u, 0x00u,
    0x20u, 0x79u, 0x00u, 0x00u, 0x01u, 0x00u,
    0x4au, 0x28u, 0x01u, 0x00u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_unresolved_typed_access_count; ++index) {
    const M68kRecoveredPlatformUnresolvedTypedAccessIR *access =
      &analysis_section->recovered_platform_unresolved_typed_accesses[index];
    const char *root_struct_name = m68k_platform_name_ref_resolve_text_or_fallback(&access->root_struct_ref,
      access->root_struct_name);
    if (access->offset == 26U && access->operand_index == 0U && access->base_reg == 0U &&
        access->displacement == 0x0100 && root_struct_name != NULL && strcmp(root_struct_name, "MP") == 0) {
      unresolved = access;
      break;
    }
  }
  M68K_C_ASSERT(unresolved != NULL);
  M68K_C_ASSERT_INT(M68K_PLATFORM_TYPE_PROVENANCE_LOOKUP_STORAGE, unresolved->type_provenance_kind);
  M68K_C_ASSERT_U32(14U, unresolved->type_provenance_offset);
  m68k_ir_source_analysis_destroy(&analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_propagates_api_output_type_through_base_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[38] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x2bu, 0x40u, 0x00u, 0x04u,
    0x20u, 0x6du, 0x00u, 0x04u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x2bu, 0x40u, 0x00u, 0x04u,
    0x4bu, 0xedu, 0x00u, 0x10u,
    0x20u, 0x6du, 0x00u, 0x04u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l d0,$0004(a5)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l $0004(a5),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l $0010(a5),a5\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b $000F(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_merges_api_output_base_slots_at_join(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[22] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x67u, 0x02u,
    0x60u, 0x04u,
    0x2bu, 0x40u, 0x00u, 0x04u,
    0x20u, 0x6du, 0x00u, 0x04u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l d0,$0004(a5)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l $0004(a5),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b $000F(a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_keeps_typed_base_only_across_platform_preserved_regs(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[32] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x24u, 0x40u,
    0x4eu, 0xaeu, 0xffu, 0x7cu,
    0x4au, 0x2au, 0x00u, 0x0fu,
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x20u, 0x40u,
    0x4eu, 0xaeu, 0xffu, 0x7cu,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOCreateMsgPort(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOForbid(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a2)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b $000F(a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_propagates_local_helper_api_output_type(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[20] = {
    0x61u, 0x08u,
    0x20u, 0x40u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u,
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOCreateMsgPort(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l d0,a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_propagates_helper_return_alias_type(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[20] = {
    0x61u, 0x06u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u,
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x20u, 0x40u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tbsr.b loc_0_00000008\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_propagates_nested_helper_return_alias_type(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[32] = {
    0x61u, 0x06u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u,
    0x61u, 0x0au,
    0x67u, 0x04u,
    0x4eu, 0x75u,
    0x4eu, 0x71u,
    0x70u, 0x01u,
    0x4eu, 0x75u,
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x20u, 0x40u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tbsr.b loc_0_00000008\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tbsr.b loc_0_00000014\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_propagates_api_output_type_through_app_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[18] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x2du, 0x40u, 0x01u, 0x00u,
    0x20u, 0x6eu, 0x01u, 0x00u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOCreateMsgPort(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_propagates_field_pointer_type_through_app_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[24] = {
    0x4eu, 0xaeu, 0xfeu, 0x80u,
    0x20u, 0x40u,
    0x22u, 0x68u, 0x00u, 0x0eu,
    0x2du, 0x49u, 0x01u, 0x00u,
    0x20u, 0x6eu, 0x01u, 0x00u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOWaitPort(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l MN_REPLYPORT(a0),a1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_tracks_app_slot_address_through_data_register_copy(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  const M68kSectionAnalysisIR *analysis_section;
  size_t index;
  int saw_typed_slot = 0;
  uint8_t bytes[14] = {
    0x43u, 0xedu, 0x01u, 0x00u,
    0x20u, 0x09u,
    0x20u, 0x40u,
    0x4eu, 0xaeu, 0xffu, 0xd0u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 2U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 5U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "__amiga_app_base__");
  policy.register_seeds[1].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[1].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[1].reg_index = 6U;
  policy.register_seeds[1].has_entry_offset = 1U;
  policy.register_seeds[1].has_section_index = 1U;
  policy.register_seeds[1].entry_offset = 0U;
  policy.register_seeds[1].section_index = 0U;
  snprintf(policy.register_seeds[1].name, sizeof(policy.register_seeds[1].name), "console.device");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &analysis_section->recovered_platform_effects[index];
    const char *type_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.type_ref,
      effect->payload.typed.type_name);
    if (effect->kind == M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT && effect->displacement == 0x0100 &&
        type_name != NULL && strcmp(type_name, "InputEvent") == 0) {
      saw_typed_slot = 1;
    }
  }
  M68K_C_ASSERT(saw_typed_slot);
  m68k_ir_source_analysis_destroy(&analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_propagates_direct_field_pointer_store_through_app_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  const M68kSectionAnalysisIR *analysis_section;
  char *source = NULL;
  size_t index;
  int saw_typed_access = 0;
  uint8_t bytes[22] = {
    0x4eu, 0xaeu, 0xfeu, 0x80u,
    0x20u, 0x40u,
    0x2du, 0x68u, 0x00u, 0x0eu, 0x01u, 0x00u,
    0x20u, 0x6eu, 0x01u, 0x00u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_typed_access_count; ++index) {
    const M68kRecoveredPlatformTypedAccessIR *access =
      &analysis_section->recovered_platform_typed_accesses[index];
    if (access->offset == 16U && access->operand_index == 0U &&
        access->field_expr != NULL && strcmp(access->field_expr, "MP_SIGBIT") == 0) {
      M68K_C_ASSERT_U32((uint32_t)M68K_PLATFORM_TYPE_PROVENANCE_FIELD_POINTER,
        (uint32_t)access->type_provenance_kind);
      M68K_C_ASSERT_U32(6U, access->type_provenance_offset);
      saw_typed_access = 1;
    }
  }
  M68K_C_ASSERT(saw_typed_access);
  m68k_ir_source_analysis_destroy(&analysis);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l MN_REPLYPORT(a0),app_0100(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_propagates_api_output_type_through_stack_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  const M68kSectionAnalysisIR *analysis_section;
  char *source = NULL;
  size_t index;
  int saw_typed_access = 0;
  uint8_t bytes[18] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x2fu, 0x40u, 0x01u, 0x00u,
    0x20u, 0x6fu, 0x01u, 0x00u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_typed_access_count; ++index) {
    const M68kRecoveredPlatformTypedAccessIR *access =
      &analysis_section->recovered_platform_typed_accesses[index];
    if (access->offset == 12U && access->operand_index == 0U &&
        access->field_expr != NULL && strcmp(access->field_expr, "MP_SIGBIT") == 0) {
      M68K_C_ASSERT_U32((uint32_t)M68K_PLATFORM_TYPE_PROVENANCE_API_OUTPUT,
        (uint32_t)access->type_provenance_kind);
      M68K_C_ASSERT_U32(0U, access->type_provenance_offset);
      saw_typed_access = 1;
    }
  }
  M68K_C_ASSERT(saw_typed_access);
  m68k_ir_source_analysis_destroy(&analysis);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_propagates_direct_field_pointer_store_through_stack_and_global_slots(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  const M68kSectionAnalysisIR *analysis_section;
  char *source = NULL;
  size_t index;
  int saw_stack_access = 0;
  int saw_global_access = 0;
  uint8_t bytes[46] = {
    0x4eu, 0xaeu, 0xfeu, 0x80u,
    0x20u, 0x40u,
    0x2fu, 0x68u, 0x00u, 0x0eu, 0x01u, 0x00u,
    0x22u, 0x6fu, 0x01u, 0x00u,
    0x4au, 0x29u, 0x00u, 0x0fu,
    0x4eu, 0xaeu, 0xfeu, 0x80u,
    0x20u, 0x40u,
    0x23u, 0xe8u, 0x00u, 0x0eu, 0x00u, 0x00u, 0x00u, 0x80u,
    0x22u, 0x79u, 0x00u, 0x00u, 0x00u, 0x80u,
    0x4au, 0x29u, 0x00u, 0x0fu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_typed_access_count; ++index) {
    const M68kRecoveredPlatformTypedAccessIR *access =
      &analysis_section->recovered_platform_typed_accesses[index];
    if (access->operand_index != 0U || access->field_expr == NULL ||
        strcmp(access->field_expr, "MP_SIGBIT") != 0) {
      continue;
    }
    M68K_C_ASSERT_U32((uint32_t)M68K_PLATFORM_TYPE_PROVENANCE_FIELD_POINTER,
      (uint32_t)access->type_provenance_kind);
    if (access->offset == 16U) {
      M68K_C_ASSERT_U32(6U, access->type_provenance_offset);
      saw_stack_access = 1;
    } else if (access->offset == 40U) {
      M68K_C_ASSERT_U32(26U, access->type_provenance_offset);
      saw_global_access = 1;
    }
  }
  M68K_C_ASSERT(saw_stack_access);
  M68K_C_ASSERT(saw_global_access);
  m68k_ir_source_analysis_destroy(&analysis);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a1)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_propagates_lea_substructure_type_through_stack_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  const M68kSectionAnalysisIR *analysis_section;
  char *source = NULL;
  size_t index;
  int saw_typed_access = 0;
  uint8_t bytes[24] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x20u, 0x40u,
    0x43u, 0xe8u, 0x00u, 0x14u,
    0x2fu, 0x49u, 0x01u, 0x00u,
    0x24u, 0x6fu, 0x01u, 0x00u,
    0x4au, 0x2au, 0x00u, 0x0cu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_typed_access_count; ++index) {
    const M68kRecoveredPlatformTypedAccessIR *access =
      &analysis_section->recovered_platform_typed_accesses[index];
    if (access->offset == 18U && access->operand_index == 0U &&
        access->field_expr != NULL && strcmp(access->field_expr, "LH_TYPE") == 0) {
      M68K_C_ASSERT_U32((uint32_t)M68K_PLATFORM_TYPE_PROVENANCE_FIELD_ADDRESS,
        (uint32_t)access->type_provenance_kind);
      M68K_C_ASSERT_U32(6U, access->type_provenance_offset);
      saw_typed_access = 1;
    }
  }
  M68K_C_ASSERT(saw_typed_access);
  m68k_ir_source_analysis_destroy(&analysis);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l MP_MSGLIST(a0),a1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b LH_TYPE(a2)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_propagates_api_output_type_through_data_base_slot_after_call(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  const M68kSectionAnalysisIR *analysis_section;
  char *source = NULL;
  size_t index;
  int saw_global_slot = 0;
  int saw_typed_access = 0;
  uint8_t bytes[38] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x4bu, 0xfau, 0x00u, 0x18u,
    0x2bu, 0x40u, 0x00u, 0x04u,
    0x61u, 0x0eu,
    0x4bu, 0xfau, 0x00u, 0x0eu,
    0x20u, 0x6du, 0x00u, 0x04u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u,
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  memset(&analysis, 0, sizeof(analysis));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &analysis_section->recovered_platform_effects[index];
    const char *type_name;
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT) continue;
    type_name = m68k_platform_name_ref_resolve_text_or_fallback(&effect->payload.typed.type_ref,
      effect->payload.typed.type_name);
    if (effect->target_section_index == 0U && effect->target_offset == 0x22U &&
        type_name != NULL && strcmp(type_name, "MP") == 0) {
      saw_global_slot = 1;
    }
  }
  for (index = 0U; index < analysis_section->recovered_platform_typed_access_count; ++index) {
    const M68kRecoveredPlatformTypedAccessIR *access =
      &analysis_section->recovered_platform_typed_accesses[index];
    if (access->offset == 22U && access->operand_index == 0U &&
        access->field_expr != NULL && strcmp(access->field_expr, "MP_SIGBIT") == 0) {
      M68K_C_ASSERT_U32((uint32_t)M68K_PLATFORM_TYPE_PROVENANCE_API_OUTPUT,
        (uint32_t)access->type_provenance_kind);
      M68K_C_ASSERT_U32(0U, access->type_provenance_offset);
      saw_typed_access = 1;
    }
  }
  M68K_C_ASSERT(saw_global_slot);
  M68K_C_ASSERT(saw_typed_access);
  m68k_ir_source_analysis_destroy(&analysis);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_typed_flow_node_visit_guard_preserves_source_rendering(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[10] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x20u, 0x40u,
    0x4au, 0x28u, 0x00u, 0x0fu
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  _putenv_s("AMIGA_REVERSING_TYPED_FLOW_MAX_NODE_VISITS", "1");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  _putenv_s("AMIGA_REVERSING_TYPED_FLOW_MAX_NODE_VISITS", "");
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOCreateMsgPort(a6)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_typed_flow_worklist_reaches_seed_after_untyped_root(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR analysis;
  const M68kSectionAnalysisIR *analysis_section;
  size_t index;
  int saw_typed_access = 0;
  uint8_t bytes[12] = {
    0x20u, 0x40u,
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x20u, 0x40u,
    0x4au, 0x28u, 0x00u, 0x0fu
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 2U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_source_analysis_profile(&object, &policy, &profile,
    &analysis, m68k_diag_sink(NULL)));
  analysis_section = &analysis.sections[0];
  for (index = 0U; index < analysis_section->recovered_platform_typed_access_count; ++index) {
    const M68kRecoveredPlatformTypedAccessIR *access =
      &analysis_section->recovered_platform_typed_accesses[index];
    if (access->offset == 8U && access->operand_index == 0U &&
        access->field_expr != NULL && strcmp(access->field_expr, "MP_SIGBIT") == 0) {
      saw_typed_access = 1;
    }
  }
  M68K_C_ASSERT(saw_typed_access);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_ir_source_analysis_destroy(&analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_conflicts_untyped_app_slot_write(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[22] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x2du, 0x40u, 0x01u, 0x00u,
    0x42u, 0xaeu, 0x01u, 0x00u,
    0x20u, 0x6eu, 0x01u, 0x00u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l app_0100(a6),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_conflicts_untyped_absolute_slot_write(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[28] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x23u, 0xc0u, 0x00u, 0x00u, 0x00u, 0x80u,
    0x42u, 0xb9u, 0x00u, 0x00u, 0x00u, 0x80u,
    0x20u, 0x79u, 0x00u, 0x00u, 0x00u, 0x80u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_unknown_call_clobbers_stack_slot_type(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[20] = {
    0x4eu, 0xaeu, 0xfdu, 0x66u,
    0x2fu, 0x40u, 0x01u, 0x00u,
    0x4eu, 0x91u,
    0x20u, 0x6fu, 0x01u, 0x00u,
    0x4au, 0x28u, 0x00u, 0x0fu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr (a1)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b $000F(a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b MP_SIGBIT(a0)\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_propagates_zero_offset_field_pointer_type(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[14] = {
    0x4eu, 0xaeu, 0xfeu, 0xecu,
    0x20u, 0x40u,
    0x22u, 0x50u,
    0x4au, 0x29u, 0x00u, 0x08u,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.register_seed_count = 1U;
  policy.register_seeds[0].kind = M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE;
  policy.register_seeds[0].reg_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
  policy.register_seeds[0].reg_index = 6U;
  policy.register_seeds[0].has_entry_offset = 1U;
  policy.register_seeds[0].has_section_index = 1U;
  policy.register_seeds[0].entry_offset = 0U;
  policy.register_seeds[0].section_index = 0U;
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOFindName(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l (a0),a1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\ttst.b LN_TYPE(a1)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_propagates_typed_base_across_branch_target(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[55] = {
    0x41u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x2au,
    0x43u, 0xeeu, 0x00u, 0x40u,
    0x2fu, 0x0eu,
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xfeu, 0x44u,
    0x2cu, 0x5fu,
    0x20u, 0x6eu, 0x00u, 0x54u,
    0x60u, 0x06u,
    0x20u, 0x7cu, 0x00u, 0x00u, 0x00u, 0x00u,
    0x0cu, 0x68u, 0x00u, 0x24u, 0x00u, 0x14u,
    0x4eu, 0x75u,
    0x74u, 0x69u, 0x6du, 0x65u, 0x72u, 0x2eu, 0x64u,
    0x65u, 0x76u, 0x69u, 0x63u, 0x65u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tbra.b loc_0_00000022\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tcmpi.w #36,LIB_VERSION(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_drops_conflicting_typed_base_at_branch_merge(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[55] = {
    0x41u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x2au,
    0x43u, 0xeeu, 0x00u, 0x40u,
    0x2fu, 0x0eu,
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xfeu, 0x44u,
    0x2cu, 0x5fu,
    0x20u, 0x6eu, 0x00u, 0x54u,
    0x66u, 0x06u,
    0x20u, 0x7cu, 0x00u, 0x00u, 0x00u, 0x00u,
    0x0cu, 0x68u, 0x00u, 0x24u, 0x00u, 0x14u,
    0x4eu, 0x75u,
    0x74u, 0x69u, 0x6du, 0x65u, 0x72u, 0x2eu, 0x64u,
    0x65u, 0x76u, 0x69u, 0x63u, 0x65u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tcmpi.w #36,LIB_VERSION(a0)\n") == NULL);
  M68K_C_ASSERT(strstr(source, "\tcmpi.w #36,$0014(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_length_prefixed_ascii_sequence_renders_strings(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint16_t index;
  uint32_t string_items = 0U;
  uint8_t bytes[] = {
    5u, 'A', 'L', 'P', 'H', 'A',
    33u, 'T', 'H', 'I', 'S', ' ', 'I', 'S', ' ', 'A', ' ', 'T', 'H', 'I', 'R', 'T', 'Y',
    ' ', 'T', 'W', 'O', ' ', 'B', 'Y', 'T', 'E', ' ', 'M', 'E', 'S', 'S', 'A', 'G', 'E',
    5u, 'G', 'A', 'M', 'M', 'A',
    0u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "dc.b $05,\"ALPHA\"") != NULL);
  M68K_C_ASSERT(strstr(source, "dc.b $21,\"THIS IS A THIRTY TWO BYTE MESSAGE\"") != NULL);
  M68K_C_ASSERT(strstr(source, "dc.b $05,\"GAMMA\"") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U &&
        strcmp(item->semantic_role, "length_prefixed_string") == 0) {
      M68K_C_ASSERT_U32(
        M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING | M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LENGTH_PREFIXED_STRING,
        item->semantic_role_flags);
      ++string_items;
    }
  }
  M68K_C_ASSERT_U32(3U, string_items);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_length_prefixed_ascii_sequence_respects_code_overlap(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[] = {
    5u, 'A', 'L', 'P', 'H', 'A',
    8u, 'B', 'E', 'T', 'A', ' ', 'T', 'W', 'O',
    5u, 'G', 'A', 'M', 'M', 'A',
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "dc.b $05,\"ALPHA\"") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_source_analysis_caps_many_auto_structured_strings(void) {
  M68kObject object;
  M68kSection section;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint8_t *bytes = NULL;
  uint32_t offset = 0U, index, string_items = 0U;
  const uint32_t record_count = 300U;
  const uint32_t record_size = 6U;
  memset(&section, 0, sizeof(section));
  bytes = (uint8_t *)malloc(record_count * record_size);
  M68K_C_ASSERT(bytes != NULL);
  for (index = 0U; index < record_count; ++index) {
    bytes[offset++] = 5U;
    bytes[offset++] = 'A';
    bytes[offset++] = (uint8_t)('A' + (index % 26U));
    bytes[offset++] = 'T';
    bytes[offset++] = 'X';
    bytes[offset++] = 'T';
  }
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_DATA;
  section.size = offset;
  section.data_size = offset;
  section.data = bytes;
  M68K_C_ASSERT(m68k_object_add_section(&object, &section).ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U &&
        strcmp(item->semantic_role, "length_prefixed_string") == 0)
      ++string_items;
  }
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT, string_items);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  free(bytes);
  return 0;
}

static int test_facts_v2_render_asm_source_infers_lvo_immediate_for_indexed_wrapper(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[92] = {
    0x43u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x50u,
    0x2fu, 0x0eu,
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xfdu, 0xd8u,
    0x2cu, 0x5fu,
    0x4au, 0x80u,
    0x66u, 0x08u,
    0x20u, 0x3cu, 0x00u, 0x00u, 0x11u, 0x40u,
    0x4eu, 0x75u,
    0x2du, 0x40u, 0x00u, 0xbeu,
    0x70u, 0xe2u,
    0x61u, 0x00u, 0x00u, 0x0eu,
    0x20u, 0x3cu, 0xffu, 0xffu, 0xffu, 0x40u,
    0x61u, 0x00u, 0x00u, 0x04u,
    0x4eu, 0x75u,
    0x2fu, 0x0eu,
    0x2cu, 0x6eu, 0x00u, 0xbeu,
    0x4eu, 0xb6u, 0x00u, 0x00u,
    0x2cu, 0x5fu,
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x64u, 0x6fu, 0x73u, 0x2eu, 0x6cu, 0x69u,
    0x62u, 0x72u, 0x61u, 0x72u, 0x79u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmoveq.l #_LVOOpen,d0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "; KNOWN: DOSBase _LVOOpen via local wrapper") == NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l #_LVODateStamp,d0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "; KNOWN: DOSBase _LVODateStamp via local wrapper") == NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr $0(a6,d0.w)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_ignores_ambiguous_wrapper_stack_arg(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[96] = {
    0x43u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x54u,
    0x2fu, 0x0eu,
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xfdu, 0xd8u,
    0x2cu, 0x5fu,
    0x4au, 0x80u,
    0x66u, 0x08u,
    0x20u, 0x3cu, 0x00u, 0x00u, 0x11u, 0x40u,
    0x4eu, 0x75u,
    0x2du, 0x40u, 0x00u, 0xbeu,
    0x70u, 0xe2u,
    0x61u, 0x00u, 0x00u, 0x0eu,
    0x20u, 0x3cu, 0xffu, 0xffu, 0xffu, 0x40u,
    0x61u, 0x00u, 0x00u, 0x04u,
    0x4eu, 0x75u,
    0x2fu, 0x0eu,
    0x2cu, 0x6eu, 0x00u, 0xbeu,
    0x22u, 0x2fu, 0x00u, 0x08u,
    0x4eu, 0xb6u, 0x00u, 0x00u,
    0x2cu, 0x5fu,
    0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x64u, 0x6fu, 0x73u, 0x2eu, 0x6cu, 0x69u,
    0x62u, 0x72u, 0x61u, 0x72u, 0x79u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l $0008(a7),d1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmoveq.l #_LVOOpen,d0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l #_LVODateStamp,d0\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_render_failures);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_tracks_cross_section_local_wrapper_without_inline_comment(void) {
  M68kObject object;
  M68kSection caller_section;
  M68kSection wrapper_section;
  M68kSection data_section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kSymbol symbol;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t caller_bytes[8] = {
    0x4eu, 0xb9u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x75u
  };
  uint8_t wrapper_bytes[18] = {
    0x2fu, 0x0eu,
    0x2cu, 0x79u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0xaeu, 0xffu, 0x3au,
    0x2cu, 0x5fu,
    0x4eu, 0x75u,
    0x00u, 0x00u
  };
  uint8_t data_bytes[4] = {0};
  memset(&caller_section, 0, sizeof(caller_section));
  memset(&wrapper_section, 0, sizeof(wrapper_section));
  memset(&data_section, 0, sizeof(data_section));
  memset(&fixup, 0, sizeof(fixup));
  memset(&symbol, 0, sizeof(symbol));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  caller_section.kind = M68K_SECTION_CODE;
  caller_section.size = sizeof(caller_bytes);
  caller_section.data_size = sizeof(caller_bytes);
  wrapper_section.kind = M68K_SECTION_CODE;
  wrapper_section.size = sizeof(wrapper_bytes);
  wrapper_section.data_size = sizeof(wrapper_bytes);
  data_section.kind = M68K_SECTION_DATA;
  data_section.size = sizeof(data_bytes);
  data_section.data_size = sizeof(data_bytes);
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object,
    m68k_object_add_section(&object, &caller_section).index, caller_bytes, sizeof(caller_bytes)));
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object,
    m68k_object_add_section(&object, &wrapper_section).index, wrapper_bytes, sizeof(wrapper_bytes)));
  added = m68k_object_add_section(&object, &data_section);
  M68K_C_ASSERT(added.ok);
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object, added.index, data_bytes, sizeof(data_bytes)));
  symbol.name = "SysBase";
  symbol.binding = M68K_SYMBOL_LOCAL;
  symbol.defined = 1;
  symbol.section_index = 2U;
  symbol.value = 0U;
  M68K_C_ASSERT(m68k_object_add_symbol(&object, &symbol).ok);
  fixup.section_index = 0U;
  fixup.offset = 2U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 1U;
  fixup.has_target_section = 1;
  M68K_C_ASSERT(m68k_object_add_fixup(&object, &fixup).ok);
  memset(&fixup, 0, sizeof(fixup));
  fixup.section_index = 1U;
  fixup.offset = 4U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 2U;
  fixup.has_target_section = 1;
  M68K_C_ASSERT(m68k_object_add_fixup(&object, &fixup).ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr loc_1_00000000.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "via local wrapper") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_tracks_non_wrapper_local_helper_without_inline_comment(void) {
  M68kObject object;
  M68kSection caller_section;
  M68kSection target_section;
  M68kSection data_section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kSymbol symbol;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t caller_bytes[8] = {
    0x4eu, 0xb9u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x75u
  };
  uint8_t target_bytes[22] = {
    0x2fu, 0x0eu,
    0x2cu, 0x79u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4au, 0x80u,
    0x67u, 0x06u,
    0x4eu, 0xaeu, 0xffu, 0x3au,
    0x4au, 0x80u,
    0x2cu, 0x5fu,
    0x4eu, 0x75u
  };
  uint8_t data_bytes[4] = {0};
  memset(&caller_section, 0, sizeof(caller_section));
  memset(&target_section, 0, sizeof(target_section));
  memset(&data_section, 0, sizeof(data_section));
  memset(&fixup, 0, sizeof(fixup));
  memset(&symbol, 0, sizeof(symbol));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  caller_section.kind = M68K_SECTION_CODE;
  caller_section.size = sizeof(caller_bytes);
  caller_section.data_size = sizeof(caller_bytes);
  target_section.kind = M68K_SECTION_CODE;
  target_section.size = sizeof(target_bytes);
  target_section.data_size = sizeof(target_bytes);
  data_section.kind = M68K_SECTION_DATA;
  data_section.size = sizeof(data_bytes);
  data_section.data_size = sizeof(data_bytes);
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object,
    m68k_object_add_section(&object, &caller_section).index, caller_bytes, sizeof(caller_bytes)));
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object,
    m68k_object_add_section(&object, &target_section).index, target_bytes, sizeof(target_bytes)));
  added = m68k_object_add_section(&object, &data_section);
  M68K_C_ASSERT(added.ok);
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object, added.index, data_bytes, sizeof(data_bytes)));
  symbol.name = "SysBase";
  symbol.binding = M68K_SYMBOL_LOCAL;
  symbol.defined = 1;
  symbol.section_index = 2U;
  symbol.value = 0U;
  M68K_C_ASSERT(m68k_object_add_symbol(&object, &symbol).ok);
  fixup.section_index = 0U;
  fixup.offset = 2U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 1U;
  fixup.has_target_section = 1;
  M68K_C_ASSERT(m68k_object_add_fixup(&object, &fixup).ok);
  memset(&fixup, 0, sizeof(fixup));
  fixup.section_index = 1U;
  fixup.offset = 4U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 2U;
  fixup.has_target_section = 1;
  M68K_C_ASSERT(m68k_object_add_fixup(&object, &fixup).ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr loc_1_00000000.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "local helper uses") == NULL);
  M68K_C_ASSERT(strstr(source, "via local wrapper") == NULL);
  M68K_C_ASSERT_U32(2U, profile.platform_call_count);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_annotates_wrapper_stack_args_without_wrapper_comment(void) {
  M68kObject object;
  M68kSection caller_section;
  M68kSection wrapper_section;
  M68kSection data_section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kSymbol symbol;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t caller_bytes[22] = {
    0x22u, 0x2fu, 0x00u, 0x08u,
    0x2fu, 0x3cu, 0x00u, 0x01u, 0x00u, 0x00u,
    0x48u, 0x78u, 0x00u, 0x60u,
    0x4eu, 0xb9u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0x75u
  };
  uint8_t wrapper_bytes[22] = {
    0x2fu, 0x0eu,
    0x2cu, 0x79u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4cu, 0xefu, 0x00u, 0x03u, 0x00u, 0x08u,
    0x4eu, 0xaeu, 0xffu, 0x3au,
    0x2cu, 0x5fu,
    0x4eu, 0x75u
  };
  uint8_t data_bytes[4] = {0};
  memset(&caller_section, 0, sizeof(caller_section));
  memset(&wrapper_section, 0, sizeof(wrapper_section));
  memset(&data_section, 0, sizeof(data_section));
  memset(&fixup, 0, sizeof(fixup));
  memset(&symbol, 0, sizeof(symbol));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  caller_section.kind = M68K_SECTION_CODE;
  caller_section.size = sizeof(caller_bytes);
  caller_section.data_size = sizeof(caller_bytes);
  wrapper_section.kind = M68K_SECTION_CODE;
  wrapper_section.size = sizeof(wrapper_bytes);
  wrapper_section.data_size = sizeof(wrapper_bytes);
  data_section.kind = M68K_SECTION_DATA;
  data_section.size = sizeof(data_bytes);
  data_section.data_size = sizeof(data_bytes);
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object,
    m68k_object_add_section(&object, &caller_section).index, caller_bytes, sizeof(caller_bytes)));
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object,
    m68k_object_add_section(&object, &wrapper_section).index, wrapper_bytes, sizeof(wrapper_bytes)));
  added = m68k_object_add_section(&object, &data_section);
  M68K_C_ASSERT(added.ok);
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object, added.index, data_bytes, sizeof(data_bytes)));
  symbol.name = "SysBase";
  symbol.binding = M68K_SYMBOL_LOCAL;
  symbol.defined = 1;
  symbol.section_index = 2U;
  symbol.value = 0U;
  M68K_C_ASSERT(m68k_object_add_symbol(&object, &symbol).ok);
  fixup.section_index = 0U;
  fixup.offset = 16U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 1U;
  fixup.has_target_section = 1;
  M68K_C_ASSERT(m68k_object_add_fixup(&object, &fixup).ok);
  memset(&fixup, 0, sizeof(fixup));
  fixup.section_index = 1U;
  fixup.offset = 4U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 2U;
  fixup.has_target_section = 1;
  M68K_C_ASSERT(m68k_object_add_fixup(&object, &fixup).ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l $0008(a7),d1\t; KNOWN:") == NULL);
  M68K_C_ASSERT(strstr(source, "\tpea.l $0060.w\t; KNOWN: arg +4 byteSize") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l #$10000,-(a7)\t; KNOWN: arg +8 attributes") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovem.l $0008(a7),d0-d1\t; KNOWN: arg +4 byteSize") != NULL);
  M68K_C_ASSERT(strstr(source, "KNOWN: arg +8 attributes") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr loc_1_00000000.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "via local wrapper") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_relocated_absolute_jsr_seeds_cross_section_code_target(void) {
  M68kObject object;
  M68kSection code_section;
  M68kSection target_section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t code_bytes[8] = {0x4eu, 0xb9u, 0x00u, 0x00u, 0x00u, 0x04u, 0x4eu, 0x75u};
  uint8_t target_bytes[6] = {0x4eu, 0x75u, 0x00u, 0x00u, 0x4eu, 0x75u};
  memset(&code_section, 0, sizeof(code_section));
  memset(&target_section, 0, sizeof(target_section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  code_section.kind = M68K_SECTION_CODE;
  code_section.size = sizeof(code_bytes);
  code_section.data_size = sizeof(code_bytes);
  target_section.kind = M68K_SECTION_CODE;
  target_section.size = sizeof(target_bytes);
  target_section.data_size = sizeof(target_bytes);
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object,
    m68k_object_add_section(&object, &code_section).index, code_bytes, sizeof(code_bytes)));
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object,
    m68k_object_add_section(&object, &target_section).index, target_bytes, sizeof(target_bytes)));
  fixup.section_index = 0U;
  fixup.offset = 2U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 1U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr loc_1_00000004.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_1_00000004:\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_1_00000000:\n\trts\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(3U, profile.accepted_instructions);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_relocated_absolute_jmp_stub_table_promotes_sibling_entry(void) {
  M68kObject object;
  M68kSection code_section;
  M68kSection target_section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t code_bytes[18] = {
    0x60u, 0x00u, 0x00u, 0x04u,
    0x00u, 0x00u,
    0x4eu, 0xf9u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4eu, 0xf9u, 0x00u, 0x00u, 0x00u, 0x02u
  };
  uint8_t target_bytes[4] = {0x4eu, 0x75u, 0x4eu, 0x75u};
  memset(&code_section, 0, sizeof(code_section));
  memset(&target_section, 0, sizeof(target_section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  code_section.kind = M68K_SECTION_CODE;
  code_section.size = sizeof(code_bytes);
  code_section.data_size = sizeof(code_bytes);
  target_section.kind = M68K_SECTION_CODE;
  target_section.size = sizeof(target_bytes);
  target_section.data_size = sizeof(target_bytes);
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object,
    m68k_object_add_section(&object, &code_section).index, code_bytes, sizeof(code_bytes)));
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object,
    m68k_object_add_section(&object, &target_section).index, target_bytes, sizeof(target_bytes)));
  memset(&fixup, 0, sizeof(fixup));
  fixup.section_index = 0U;
  fixup.offset = 8U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 1U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  fixup.offset = 14U;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000000:\n\tbra.w loc_0_00000006\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000006:\n\tjmp loc_1_00000000.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_0000000C:\n\tjmp loc_1_00000002.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.b $4E,$F9\n\tdc.l loc_1_00000002\n") == NULL);
  M68K_C_ASSERT(strstr(source, "loc_1_00000000:\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_1_00000002:\n\trts\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(5U, profile.accepted_instructions);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_renders_structured_data_comment(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  const char *include_line;
  const char *section_line;
  uint8_t bytes[4] = {0x4Au, 0xFCu, 0x80u, 0x09u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.named_label_count = 1U;
  policy.named_labels[0].has_section_index = 1U;
  policy.named_labels[0].section_index = 0U;
  policy.named_labels[0].offset = 0U;
  snprintf(policy.named_labels[0].name, sizeof(policy.named_labels[0].name), "resident");
  policy.structured_data_item_count = 3U;
  policy.structured_data_items[0].has_section_index = 1U;
  policy.structured_data_items[0].section_index = 0U;
  policy.structured_data_items[0].offset = 0U;
  policy.structured_data_items[0].size = 2U;
  policy.structured_data_items[0].kind = M68K_ANALYSIS_STRUCTURED_DATA_WORDS;
  policy.structured_data_items[0].has_constant_value = 1U;
  policy.structured_data_items[0].constant_value = 0x4AFC;
  snprintf(policy.structured_data_items[0].constant_name,
    sizeof(policy.structured_data_items[0].constant_name), "RTC_MATCHWORD");
  snprintf(policy.structured_data_items[0].struct_name, sizeof(policy.structured_data_items[0].struct_name),
    "RT");
  snprintf(policy.structured_data_items[0].field_name, sizeof(policy.structured_data_items[0].field_name),
    "RT_MATCHWORD");
  snprintf(policy.structured_data_items[0].field_type, sizeof(policy.structured_data_items[0].field_type),
    "UWORD");
  snprintf(policy.structured_data_items[0].comment, sizeof(policy.structured_data_items[0].comment),
    "NOTE: resident flags");
  policy.structured_data_items[1].has_section_index = 1U;
  policy.structured_data_items[1].section_index = 0U;
  policy.structured_data_items[1].offset = 2U;
  policy.structured_data_items[1].size = 1U;
  policy.structured_data_items[1].kind = M68K_ANALYSIS_STRUCTURED_DATA_BYTES;
  snprintf(policy.structured_data_items[1].struct_name, sizeof(policy.structured_data_items[1].struct_name),
    "RT");
  snprintf(policy.structured_data_items[1].field_name, sizeof(policy.structured_data_items[1].field_name),
    "RT_FLAGS");
  snprintf(policy.structured_data_items[1].field_type, sizeof(policy.structured_data_items[1].field_type),
    "UBYTE");
  snprintf(policy.structured_data_items[1].value_domain, sizeof(policy.structured_data_items[1].value_domain),
    "exec.resident.flags");
  snprintf(policy.structured_data_items[1].comment, sizeof(policy.structured_data_items[1].comment),
    "NOTE: resident flags");
  policy.structured_data_items[2].has_section_index = 1U;
  policy.structured_data_items[2].section_index = 0U;
  policy.structured_data_items[2].offset = 3U;
  policy.structured_data_items[2].size = 1U;
  policy.structured_data_items[2].kind = M68K_ANALYSIS_STRUCTURED_DATA_BYTES;
  snprintf(policy.structured_data_items[2].struct_name, sizeof(policy.structured_data_items[2].struct_name),
    "RT");
  snprintf(policy.structured_data_items[2].field_name, sizeof(policy.structured_data_items[2].field_name),
    "RT_TYPE");
  snprintf(policy.structured_data_items[2].field_type, sizeof(policy.structured_data_items[2].field_type),
    "UBYTE");
  snprintf(policy.structured_data_items[2].value_domain, sizeof(policy.structured_data_items[2].value_domain),
    "exec.node.type");
  snprintf(policy.structured_data_items[2].comment, sizeof(policy.structured_data_items[2].comment),
    "NOTE: resident type");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "    SECTION section,data\n") != NULL);
  include_line = strstr(source, "    INCLUDE \"exec/resident.i\"\n");
  section_line = strstr(source, "    SECTION section,data\n");
  M68K_C_ASSERT(include_line != NULL && section_line != NULL && include_line < section_line);
  M68K_C_ASSERT(strstr(source, "resident:\t; STRUCT RT\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w RTC_MATCHWORD\t; UWORD RT_MATCHWORD = RTC_MATCHWORD\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.b RTF_AUTOINIT\t; UBYTE RT_FLAGS = RTF_AUTOINIT\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.b NT_LIBRARY\t; UBYTE RT_TYPE = NT_LIBRARY\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_render_ir_suppresses_orphan_structured_field_label(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kDecodeIR decode;
  M68kFactIR facts;
  M68kFact fact;
  M68kAnalysisPolicy policy;
  M68kRenderIRPreview preview;
  uint8_t *accepted_start[1];
  uint8_t *accepted_bytes[1];
  uint8_t accepted_start_0[64];
  uint8_t accepted_bytes_0[64];
  uint8_t bytes[64];
  memset(&section, 0, sizeof(section));
  memset(bytes, 0, sizeof(bytes));
  bytes[18] = 0x00U;
  bytes[19] = 0x00U;
  bytes[20] = 0x00U;
  bytes[21] = 0x1EU;
  bytes[30] = 'n';
  bytes[31] = 'a';
  bytes[32] = 'm';
  bytes[33] = 'e';
  bytes[34] = 0U;
  memset(accepted_start_0, 0, sizeof(accepted_start_0));
  memset(accepted_bytes_0, 0, sizeof(accepted_bytes_0));
  accepted_start[0] = accepted_start_0;
  accepted_bytes[0] = accepted_bytes_0;
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_decode_ir_init(&decode);
  m68k_fact_ir_init(&facts);
  m68k_analysis_policy_init_default(&policy);
  m68k_render_ir_preview_init(&preview);
  policy.named_label_count = 1U;
  policy.named_labels[0].has_section_index = 1U;
  policy.named_labels[0].section_index = 0U;
  policy.named_labels[0].offset = 30U;
  snprintf(policy.named_labels[0].name, sizeof(policy.named_labels[0].name), "resident_name");
  policy.structured_data_item_count = 1U;
  policy.structured_data_items[0].has_section_index = 1U;
  policy.structured_data_items[0].section_index = 0U;
  policy.structured_data_items[0].offset = 18U;
  policy.structured_data_items[0].size = 4U;
  policy.structured_data_items[0].kind = M68K_ANALYSIS_STRUCTURED_DATA_LONGS;
  snprintf(policy.structured_data_items[0].struct_name, sizeof(policy.structured_data_items[0].struct_name), "RT");
  snprintf(policy.structured_data_items[0].field_name, sizeof(policy.structured_data_items[0].field_name),
    "RT_NAME");
  snprintf(policy.structured_data_items[0].field_type, sizeof(policy.structured_data_items[0].field_type),
    "APTR");
  M68K_C_ASSERT_INT(0, m68k_decode_ir_build_object(&decode, &object, M68K_ASM_CPU_68000,
    m68k_diag_sink(NULL)));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_LABEL_CREATED;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  fact.section_index = 0U;
  fact.offset = 18U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_LABEL_CREATED;
  fact.confidence = M68K_FACT_CONFIDENCE_REQUIRED;
  fact.section_index = 0U;
  fact.offset = 30U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_RELOCATION_REF;
  fact.confidence = M68K_FACT_CONFIDENCE_REQUIRED;
  fact.section_index = 0U;
  fact.offset = 18U;
  fact.target_section_index = 0U;
  fact.target_offset = 30U;
  fact.size = 4U;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  M68K_C_ASSERT_INT(0, m68k_render_ir_preview_build(&object, &decode, &facts, &policy,
    accepted_start, accepted_bytes, 0, 1, 1, 1, &preview, NULL));
  M68K_C_ASSERT(preview.asm_source_text != NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "loc_0_00000012:") == NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "\tdc.l resident_name\t; APTR RT_NAME\n") != NULL);
  M68K_C_ASSERT(strstr(preview.asm_source_text, "resident_name:\n") != NULL);
  m68k_render_ir_preview_destroy(&preview);
  m68k_fact_ir_destroy(&facts);
  m68k_decode_ir_destroy(&decode);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_resident_sizeof_defines_app_sizeof_without_slots(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[4] = {0x00u, 0x00u, 0x00u, 0x2Eu};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.structured_data_item_count = 1U;
  policy.structured_data_items[0].has_section_index = 1U;
  policy.structured_data_items[0].section_index = 0U;
  policy.structured_data_items[0].offset = 0U;
  policy.structured_data_items[0].size = 4U;
  policy.structured_data_items[0].kind = M68K_ANALYSIS_STRUCTURED_DATA_LONGS;
  snprintf(policy.structured_data_items[0].struct_name, sizeof(policy.structured_data_items[0].struct_name),
    "resident_autoinit");
  snprintf(policy.structured_data_items[0].field_name, sizeof(policy.structured_data_items[0].field_name),
    "resident_base_size");
  snprintf(policy.structured_data_items[0].field_type, sizeof(policy.structured_data_items[0].field_type),
    "ULONG");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "    INCLUDE \"exec/devices.i\"\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    RSSET LIB_SIZE\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    RS.B 12\n") != NULL);
  M68K_C_ASSERT(strstr(source, "app_SIZEOF EQU __RS\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l app_SIZEOF\t; ULONG resident_base_size\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_resident_lib_size_omits_empty_app_sizeof(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  int32_t lib_size = 0;
  uint8_t bytes[4];
  M68K_C_ASSERT(amiga_os_find_constant_value("LIB_SIZE", &lib_size));
  M68K_C_ASSERT(lib_size > 0 && lib_size <= 0xFFFF);
  bytes[0] = (uint8_t)(((uint32_t)lib_size >> 24) & 0xFFU);
  bytes[1] = (uint8_t)(((uint32_t)lib_size >> 16) & 0xFFU);
  bytes[2] = (uint8_t)(((uint32_t)lib_size >> 8) & 0xFFU);
  bytes[3] = (uint8_t)((uint32_t)lib_size & 0xFFU);
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.structured_data_item_count = 1U;
  policy.structured_data_items[0].has_section_index = 1U;
  policy.structured_data_items[0].section_index = 0U;
  policy.structured_data_items[0].offset = 0U;
  policy.structured_data_items[0].size = 4U;
  policy.structured_data_items[0].kind = M68K_ANALYSIS_STRUCTURED_DATA_LONGS;
  snprintf(policy.structured_data_items[0].struct_name, sizeof(policy.structured_data_items[0].struct_name),
    "resident_autoinit");
  snprintf(policy.structured_data_items[0].field_name, sizeof(policy.structured_data_items[0].field_name),
    "resident_base_size");
  snprintf(policy.structured_data_items[0].field_type, sizeof(policy.structured_data_items[0].field_type),
    "ULONG");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "    INCLUDE \"exec/devices.i\"\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    RSSET LIB_SIZE\n") == NULL);
  M68K_C_ASSERT(strstr(source, "app_SIZEOF EQU __RS\n") == NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l LIB_SIZE\t; ULONG resident_base_size\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.l app_SIZEOF\t; ULONG resident_base_size\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_renders_copper_list_structured_data(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[60] = {
    0x00u, 0x8Eu, 0x2Cu, 0x81u,
    0x00u, 0x90u, 0x2Cu, 0xC1u,
    0x00u, 0x92u, 0x00u, 0x38u,
    0x00u, 0x94u, 0x00u, 0xD0u,
    0x01u, 0x00u, 0x42u, 0x00u,
    0x00u, 0xE0u, 0x12u, 0x34u,
    0x00u, 0xE2u, 0x56u, 0x78u,
    0x01u, 0x08u, 0x00u, 0x00u,
    0x01u, 0x0Au, 0x00u, 0x28u,
    0x01u, 0x20u, 0x00u, 0x00u,
    0x01u, 0x22u, 0x00u, 0x00u,
    0x01u, 0x3Eu, 0x00u, 0x00u,
    0x00u, 0x9Cu, 0x80u, 0x10u,
    0x2Cu, 0x07u, 0xFFu, 0xFEu,
    0xFFu, 0xFFu, 0xFFu, 0xFEu
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.named_label_count = 2U;
  policy.named_labels[0].has_section_index = 1U;
  policy.named_labels[0].section_index = 0U;
  policy.named_labels[0].offset = 0U;
  snprintf(policy.named_labels[0].name, sizeof(policy.named_labels[0].name), "copper_list");
  policy.named_labels[1].has_section_index = 1U;
  policy.named_labels[1].section_index = 0U;
  policy.named_labels[1].offset = 20U;
  snprintf(policy.named_labels[1].name, sizeof(policy.named_labels[1].name), "copper_patch");
  policy.structured_data_item_count = 1U;
  policy.structured_data_items[0].has_section_index = 1U;
  policy.structured_data_items[0].section_index = 0U;
  policy.structured_data_items[0].offset = 0U;
  policy.structured_data_items[0].size = (uint32_t)sizeof(bytes);
  policy.structured_data_items[0].kind = M68K_ANALYSIS_STRUCTURED_DATA_WORDS;
  snprintf(policy.structured_data_items[0].semantic_role,
    sizeof(policy.structured_data_items[0].semantic_role), "copper_list");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "INCLUDE \"hardware/custom.i\"") != NULL);
  M68K_C_ASSERT(strstr(source, "INCLUDE \"graphics/copper.i\"") != NULL);
  M68K_C_ASSERT(strstr(source, "INCLUDE \"graphics/display.i\"") != NULL);
  M68K_C_ASSERT(strstr(source, "INCLUDE \"hardware/intbits.i\"") != NULL);
  M68K_C_ASSERT(strstr(source, "copper_list:\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tdc.w diwstrt,$2C81\t; display window start v=$2C h=$81\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tdc.w diwstop,$2CC1\t; display window stop v=$2C h=$C1\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tdc.w ddfstrt,$0038\t; display fetch start $38\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tdc.w ddfstop,$00D0\t; display fetch stop $D0\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tdc.w bplcon0,(4<<PLNCNTSHFT)|COLORON\t; display 4 bitplanes lores color\n") != NULL);
  M68K_C_ASSERT(strstr(source, "bitmap_12345678\tEQU\t$12345678\n") != NULL);
  M68K_C_ASSERT(strstr(source, "bitmap_12345678_hi\tEQU\tbitmap_12345678/$10000\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "bitmap_12345678_lo\tEQU\tbitmap_12345678-(bitmap_12345678_hi*$10000)\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "copper_patch:\n\tdc.w bplpt,bitmap_12345678_hi\t; bitmap pointer $12345678\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w bplpt,bitmap_12345678_hi\t; bitmap pointer $12345678\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w bplpt+$02,bitmap_12345678_lo\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w bpl1mod,$0000\t; bitplane modulo 0 bytes\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w bpl2mod,$0028\t; bitplane modulo 40 bytes\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w sprpt,$0000\t; sprite pointer 0 disabled\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w sprpt+$1E,$0000\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w intreq,INTF_SETCLR|INTF_COPER\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tdc.w COPPER_WAIT|$2C06,$FFFE\t; copper wait v=$2C h=$06 mask $FFFE\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w $FFFF,$FFFE\n") != NULL);
  M68K_C_ASSERT(strstr(source, "; copper_list") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_runtime_copper_pointer_auto_classifies_copper_list(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  uint16_t index;
  uint8_t bytes[24] = {
    0x23u, 0xFCu, 0x00u, 0x00u, 0x00u, 0x0Cu, 0x00u, 0xDFu, 0xF0u, 0x80u,
    0x4Eu, 0x75u,
    0x01u, 0x00u, 0x42u, 0x00u,
    0x00u, 0xE0u, 0x12u, 0x34u,
    0xFFu, 0xFFu, 0xFFu, 0xFEu
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = (uint32_t)sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.l #loc_0_0000000C,_custom+cop1lc.l\t; copper_list pointer\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "loc_0_0000000C:\n\tdc.w bplcon0,(4<<PLNCNTSHFT)|COLORON\t; display 4 bitplanes lores color\n"
    "\tdc.w bplpt,$1234\n"
    "\tdc.w $FFFF,$FFFE\n") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && item->offset == 0x0CU &&
        strcmp(item->semantic_role, "copper_list") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(12U, auto_item->size);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_register_runtime_sink_auto_classifies_copper_list(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  char *analysis_json = NULL;
  uint16_t index;
  uint8_t bytes[26] = {
    0x20u, 0x3Cu, 0x00u, 0x00u, 0x00u, 0x0Eu,
    0x23u, 0xC0u, 0x00u, 0xDFu, 0xF0u, 0x80u,
    0x4Eu, 0x75u,
    0x01u, 0x00u, 0x42u, 0x00u,
    0x00u, 0xE0u, 0x12u, 0x34u,
    0xFFu, 0xFFu, 0xFFu, 0xFEu
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = (uint32_t)sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l d0,_custom+cop1lc.l\t; copper_list pointer\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "loc_0_0000000E:\n\tdc.w bplcon0,(4<<PLNCNTSHFT)|COLORON\t; display 4 bitplanes lores color\n"
    "\tdc.w bplpt,$1234\n"
    "\tdc.w $FFFF,$FFFE\n") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && item->offset == 0x0EU &&
        strcmp(item->semantic_role, "copper_list") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(12U, auto_item->size);
  M68K_C_ASSERT_U32(1U, source_analysis.sections[0].runtime_address_ref_count);
  M68K_C_ASSERT_U32(6U, source_analysis.sections[0].runtime_address_refs[0].offset);
  M68K_C_ASSERT_U32(UINT32_MAX, source_analysis.sections[0].runtime_address_refs[0].operand_index);
  M68K_C_ASSERT_U32(14U, source_analysis.sections[0].runtime_address_refs[0].target_offset);
  M68K_C_ASSERT_U32(14U, source_analysis.sections[0].runtime_address_refs[0].runtime_address);
  M68K_C_ASSERT_U32(1U, source_analysis.sections[0].runtime_address_refs[0].has_sink_address);
  M68K_C_ASSERT_U32(0xDFF080U, source_analysis.sections[0].runtime_address_refs[0].sink_address);
  M68K_C_ASSERT_STR("copper_list", source_analysis.sections[0].runtime_address_refs[0].data_class);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_ROLE_COPPER_LIST,
    source_analysis.sections[0].runtime_address_refs[0].data_class_flags);
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"runtime_address_ref_count\":1") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"offset\":6,\"operand_index\":null,\"target_section_index\":0,\"target_offset\":14") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"sink_address\":14676096") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"runtime_address\":14") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"range_space_kind\":2,\"range_space\":\"runtime_absolute\",\"range_start\":14") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"confidence\":2,\"data_class\":\"copper_list\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"memory_layout_record_count\":") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"record_kind\":\"runtime_address_ref\",\"memory_kind\":\"copper_list\",\"section_index\":0,"
    "\"source_offset\":6") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"sink_address\":14676096") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  free(analysis_json);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_analysis_records_absolute_memory_refs(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAbsoluteMemoryRefIR *exec_ref = NULL;
  const M68kAbsoluteMemoryRefIR *custom_ref = NULL;
  const M68kAbsoluteMemoryRefIR *absolute_ref = NULL;
  const M68kAbsoluteMemoryRefIR *code_ref = NULL;
  char *source = NULL;
  char *analysis_json = NULL;
  size_t index;
  uint8_t bytes[28] = {
    0x2Cu, 0x78u, 0x00u, 0x04u,
    0x33u, 0xFCu, 0x12u, 0x34u, 0x00u, 0xDFu, 0xF0u, 0x9Au,
    0x41u, 0xF9u, 0x00u, 0x07u, 0x00u, 0x00u,
    0x33u, 0xFCu, 0x12u, 0x34u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x4Eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT_U32(4U, (uint32_t)source_analysis.sections[0].absolute_memory_ref_count);
  for (index = 0U; index < source_analysis.sections[0].absolute_memory_ref_count; ++index) {
    const M68kAbsoluteMemoryRefIR *ref = &source_analysis.sections[0].absolute_memory_refs[index];
    if (ref->address == 4U) exec_ref = ref;
    else if (ref->address == 0x00DFF09AU) custom_ref = ref;
    else if (ref->address == 0x00070000U) absolute_ref = ref;
    else if (ref->address == 0U) code_ref = ref;
  }
  M68K_C_ASSERT(exec_ref != NULL);
  M68K_C_ASSERT_U32(M68K_ABSOLUTE_MEMORY_OWNER_EXECBASE_LITERAL, exec_ref->owner_kind);
  M68K_C_ASSERT_U32(M68K_SIM_ACCESS_MEMORY_READ, exec_ref->access_kind);
  M68K_C_ASSERT_U32(4U, exec_ref->access_width);
  M68K_C_ASSERT(custom_ref != NULL);
  M68K_C_ASSERT_U32(M68K_ABSOLUTE_MEMORY_OWNER_HARDWARE_REGISTER, custom_ref->owner_kind);
  M68K_C_ASSERT_U32(M68K_SIM_ACCESS_MEMORY_WRITE, custom_ref->access_kind);
  M68K_C_ASSERT_U32(2U, custom_ref->access_width);
  M68K_C_ASSERT(absolute_ref != NULL);
  M68K_C_ASSERT_U32(M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY, absolute_ref->owner_kind);
  M68K_C_ASSERT_U32(M68K_SIM_ACCESS_COMPUTE_ADDRESS, absolute_ref->access_kind);
  M68K_C_ASSERT_U32(0U, absolute_ref->access_width);
  M68K_C_ASSERT(code_ref != NULL);
  M68K_C_ASSERT_U32(M68K_ABSOLUTE_MEMORY_OWNER_CPU_VECTOR, code_ref->owner_kind);
  M68K_C_ASSERT_U32(1U, code_ref->conflicted);
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&source_analysis, &analysis_json, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(analysis_json != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"memory_layout_record_count\":4") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"record_kind\":\"absolute_memory_ref\",\"memory_kind\":\"execbase_literal\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"record_kind\":\"absolute_memory_ref\",\"memory_kind\":\"hardware_register\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"owner_symbol\":\"intena\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"range_space_kind\":3,\"range_space\":\"absolute\",\"range_start\":14676122,\"range_size\":2,"
    "\"range_end\":14676124") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"record_kind\":\"absolute_memory_ref\",\"memory_kind\":\"absolute_memory\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json,
    "\"range_space_kind\":3,\"range_space\":\"absolute\",\"range_start\":458752,\"range_size\":0,"
    "\"range_end\":458752") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"conflict_state\":\"clean\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"conflict_state_id\":1,\"conflict_state\":\"code_overlap\"") != NULL);
  M68K_C_ASSERT(strstr(analysis_json, "\"conflict_state\":\"code_overlap\"") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  free(analysis_json);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_copper_bitmap_pointers_render_display_layout_comment(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  const M68kRuntimeAddressRefIR *first_bitmap = NULL;
  const M68kRuntimeAddressRefIR *second_bitmap = NULL;
  size_t index;
  uint8_t bytes[32] = {
    0x23u, 0xFCu, 0x00u, 0x00u, 0x00u, 0x0Cu, 0x00u, 0xDFu, 0xF0u, 0x80u,
    0x4Eu, 0x75u,
    0x00u, 0xE0u, 0x00u, 0x01u,
    0x00u, 0xE2u, 0x00u, 0x00u,
    0x00u, 0xE4u, 0x00u, 0x01u,
    0x00u, 0xE6u, 0x20u, 0x00u,
    0xFFu, 0xFFu, 0xFFu, 0xFEu
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = (uint32_t)sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "bitmap_00010000\tEQU\t$10000\n") != NULL);
  M68K_C_ASSERT(strstr(source, "bitmap_00012000\tEQU\t$12000\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "loc_0_0000000C:\n"
    "    ; display layout 2 bitmap planes $00010000..$00012000 step $2000\n"
    "\tdc.w bplpt,bitmap_00010000_hi\t; bitmap pointer $00010000\n"
    "\tdc.w bplpt+$02,bitmap_00010000_lo\n"
    "\tdc.w bplpt+$04,bitmap_00012000_hi\t; bitmap pointer $00012000\n"
    "\tdc.w bplpt+$06,bitmap_00012000_lo\n") != NULL);
  for (index = 0U; index < source_analysis.sections[0].runtime_address_ref_count; ++index) {
    const M68kRuntimeAddressRefIR *ref = &source_analysis.sections[0].runtime_address_refs[index];
    if (ref->data_class == NULL || strcmp(ref->data_class, "bitmap") != 0) continue;
    if (ref->offset == 0x0CU) first_bitmap = ref;
    if (ref->offset == 0x14U) second_bitmap = ref;
  }
  M68K_C_ASSERT(first_bitmap != NULL);
  M68K_C_ASSERT_U32(0x10000U, first_bitmap->runtime_address);
  M68K_C_ASSERT_U32(0x2000U, first_bitmap->size);
  M68K_C_ASSERT_U32(0U, first_bitmap->has_target);
  M68K_C_ASSERT(second_bitmap != NULL);
  M68K_C_ASSERT_U32(0x12000U, second_bitmap->runtime_address);
  M68K_C_ASSERT_U32(0x2000U, second_bitmap->size);
  M68K_C_ASSERT_U32(0U, second_bitmap->has_target);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_copper_bitmap_memory_uses_are_commented(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  char *source = NULL;
  uint32_t bitmap_use_refs = 0U;
  size_t index;
  uint8_t bytes[40] = {
    0x23u, 0xFCu, 0x00u, 0x00u, 0x00u, 0x14u, 0x00u, 0xDFu, 0xF0u, 0x80u,
    0x41u, 0xF9u, 0x00u, 0x01u, 0x00u, 0x10u,
    0x30u, 0x10u,
    0x4Eu, 0x75u,
    0x00u, 0xE0u, 0x00u, 0x01u,
    0x00u, 0xE2u, 0x00u, 0x00u,
    0x00u, 0xE4u, 0x00u, 0x01u,
    0x00u, 0xE6u, 0x20u, 0x00u,
    0xFFu, 0xFFu, 0xFFu, 0xFEu
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = (uint32_t)sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tlea.l $00010010.l,a0\t; bitmap memory plane 0 +$10 ($00010010)\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.w (a0),d0\t; bitmap memory plane 0 +$10 ($00010010)\n") != NULL);
  for (index = 0U; index < source_analysis.sections[0].runtime_address_ref_count; ++index) {
    const M68kRuntimeAddressRefIR *ref = &source_analysis.sections[0].runtime_address_refs[index];
    if (ref->data_class != NULL && strcmp(ref->data_class, "bitmap") == 0 &&
        ref->has_runtime_address && ref->runtime_address == 0x10010U) {
      ++bitmap_use_refs;
      M68K_C_ASSERT_U32(0U, ref->size);
    }
  }
  M68K_C_ASSERT_U32(2U, bitmap_use_refs);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_palette_upload_auto_classifies_source_table(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  size_t index;
  uint8_t bytes[80] = {
    0x43u, 0xF9u, 0x00u, 0xDFu, 0xF1u, 0x80u,
    0x41u, 0xF9u, 0x00u, 0x00u, 0x00u, 0x10u,
    0x32u, 0xD8u,
    0x4Eu, 0x75u,
    0x00u, 0x00u, 0x01u, 0x11u, 0x02u, 0x22u, 0x03u, 0x33u,
    0x04u, 0x44u, 0x05u, 0x55u, 0x06u, 0x66u, 0x07u, 0x77u,
    0x08u, 0x88u, 0x09u, 0x99u, 0x0Au, 0xAAu, 0x0Bu, 0xBBu,
    0x0Cu, 0xCCu, 0x0Du, 0xDDu, 0x0Eu, 0xEEu, 0x0Fu, 0xFFu,
    0x00u, 0x10u, 0x01u, 0x20u, 0x02u, 0x30u, 0x03u, 0x40u,
    0x04u, 0x50u, 0x05u, 0x60u, 0x06u, 0x70u, 0x07u, 0x80u,
    0x08u, 0x90u, 0x09u, 0xA0u, 0x0Au, 0xB0u, 0x0Bu, 0xC0u,
    0x0Cu, 0xD0u, 0x0Du, 0xE0u, 0x0Eu, 0xF0u, 0x0Fu, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w (a0)+,(a1)+\t; palette upload 32 colors\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w $0000,$0111,$0222,$0333") != NULL);
  M68K_C_ASSERT(strstr(source, "\t; palette\n") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && item->offset == 16U &&
        strcmp(item->semantic_role, "palette") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(64U, auto_item->size);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_WORDS, auto_item->kind);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_palette_upload_allows_internal_word_label(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  size_t index;
  uint8_t bytes[80] = {
    0x43u, 0xF9u, 0x00u, 0xDFu, 0xF1u, 0x80u,
    0x41u, 0xF9u, 0x00u, 0x00u, 0x00u, 0x10u,
    0x32u, 0xD8u,
    0x4Eu, 0x75u,
    0x00u, 0x00u, 0x01u, 0x11u, 0x02u, 0x22u, 0x03u, 0x33u,
    0x04u, 0x44u, 0x05u, 0x55u, 0x06u, 0x66u, 0x07u, 0x77u,
    0x08u, 0x88u, 0x09u, 0x99u, 0x0Au, 0xAAu, 0x0Bu, 0xBBu,
    0x0Cu, 0xCCu, 0x0Du, 0xDDu, 0x0Eu, 0xEEu, 0x0Fu, 0xFFu,
    0x00u, 0x10u, 0x01u, 0x20u, 0x02u, 0x30u, 0x03u, 0x40u,
    0x04u, 0x50u, 0x05u, 0x60u, 0x06u, 0x70u, 0x07u, 0x80u,
    0x08u, 0x90u, 0x09u, 0xA0u, 0x0Au, 0xB0u, 0x0Bu, 0xC0u,
    0x0Cu, 0xD0u, 0x0Du, 0xE0u, 0x0Eu, 0xF0u, 0x0Fu, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.named_label_count = 1U;
  policy.named_labels[0].has_section_index = 1U;
  policy.named_labels[0].section_index = 0U;
  policy.named_labels[0].offset = 46U;
  snprintf(policy.named_labels[0].name, sizeof(policy.named_labels[0].name), "palette_patch");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w (a0)+,(a1)+\t; palette upload 32 colors\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\t; palette\n") != NULL);
  M68K_C_ASSERT(strstr(source, "palette_patch:\n\tdc.w $0FFF") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && item->offset == 16U &&
        strcmp(item->semantic_role, "palette") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(64U, auto_item->size);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_WORDS, auto_item->kind);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_palette_upload_survives_movem_saved_call(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  size_t index;
  uint8_t bytes[94] = {
    0x43u, 0xF9u, 0x00u, 0xDFu, 0xF1u, 0x80u,
    0x41u, 0xF9u, 0x00u, 0x00u, 0x00u, 0x1Eu,
    0x48u, 0xE7u, 0x00u, 0xE0u,
    0x61u, 0x00u, 0x00u, 0x08u,
    0x4Cu, 0xDFu, 0x07u, 0x00u,
    0x32u, 0xD8u,
    0x4Eu, 0x75u,
    0x4Eu, 0x75u,
    0x00u, 0x00u, 0x01u, 0x11u, 0x02u, 0x22u, 0x03u, 0x33u,
    0x04u, 0x44u, 0x05u, 0x55u, 0x06u, 0x66u, 0x07u, 0x77u,
    0x08u, 0x88u, 0x09u, 0x99u, 0x0Au, 0xAAu, 0x0Bu, 0xBBu,
    0x0Cu, 0xCCu, 0x0Du, 0xDDu, 0x0Eu, 0xEEu, 0x0Fu, 0xFFu,
    0x00u, 0x10u, 0x01u, 0x20u, 0x02u, 0x30u, 0x03u, 0x40u,
    0x04u, 0x50u, 0x05u, 0x60u, 0x06u, 0x70u, 0x07u, 0x80u,
    0x08u, 0x90u, 0x09u, 0xA0u, 0x0Au, 0xB0u, 0x0Bu, 0xC0u,
    0x0Cu, 0xD0u, 0x0Du, 0xE0u, 0x0Eu, 0xF0u, 0x0Fu, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w (a0)+,(a1)+\t; palette upload 32 colors\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w $0000,$0111,$0222,$0333") != NULL);
  M68K_C_ASSERT(strstr(source, "\t; palette\n") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && item->offset == 30U &&
        strcmp(item->semantic_role, "palette") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(64U, auto_item->size);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_WORDS, auto_item->kind);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_palette_upload_survives_address_preserving_local_call(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  size_t index;
  uint8_t bytes[88] = {
    0x43u, 0xF9u, 0x00u, 0xDFu, 0xF1u, 0x80u,
    0x41u, 0xF9u, 0x00u, 0x00u, 0x00u, 0x18u,
    0x61u, 0x00u, 0x00u, 0x06u,
    0x32u, 0xD8u,
    0x4Eu, 0x75u,
    0x70u, 0x00u,
    0x4Eu, 0x75u,
    0x00u, 0x00u, 0x01u, 0x11u, 0x02u, 0x22u, 0x03u, 0x33u,
    0x04u, 0x44u, 0x05u, 0x55u, 0x06u, 0x66u, 0x07u, 0x77u,
    0x08u, 0x88u, 0x09u, 0x99u, 0x0Au, 0xAAu, 0x0Bu, 0xBBu,
    0x0Cu, 0xCCu, 0x0Du, 0xDDu, 0x0Eu, 0xEEu, 0x0Fu, 0xFFu,
    0x00u, 0x10u, 0x01u, 0x20u, 0x02u, 0x30u, 0x03u, 0x40u,
    0x04u, 0x50u, 0x05u, 0x60u, 0x06u, 0x70u, 0x07u, 0x80u,
    0x08u, 0x90u, 0x09u, 0xA0u, 0x0Au, 0xB0u, 0x0Bu, 0xC0u,
    0x0Cu, 0xD0u, 0x0Du, 0xE0u, 0x0Eu, 0xF0u, 0x0Fu, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w (a0)+,(a1)+\t; palette upload 32 colors\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w $0000,$0111,$0222,$0333") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && item->offset == 24U &&
        strcmp(item->semantic_role, "palette") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(64U, auto_item->size);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_WORDS, auto_item->kind);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_genam_palette_upload_uses_runtime_translated_source_table(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  size_t index;
  uint8_t bytes[80] = {
    0x43u, 0xF9u, 0x00u, 0xDFu, 0xF1u, 0x80u,
    0x41u, 0xF9u, 0x00u, 0x00u, 0x10u, 0x10u,
    0x32u, 0xD8u,
    0x4Eu, 0x75u,
    0x00u, 0x00u, 0x01u, 0x11u, 0x02u, 0x22u, 0x03u, 0x33u,
    0x04u, 0x44u, 0x05u, 0x55u, 0x06u, 0x66u, 0x07u, 0x77u,
    0x08u, 0x88u, 0x09u, 0x99u, 0x0Au, 0xAAu, 0x0Bu, 0xBBu,
    0x0Cu, 0xCCu, 0x0Du, 0xDDu, 0x0Eu, 0xEEu, 0x0Fu, 0xFFu,
    0x00u, 0x10u, 0x01u, 0x20u, 0x02u, 0x30u, 0x03u, 0x40u,
    0x04u, 0x50u, 0x05u, 0x60u, 0x06u, 0x70u, 0x07u, 0x80u,
    0x08u, 0x90u, 0x09u, 0xA0u, 0x0Au, 0xB0u, 0x0Bu, 0xC0u,
    0x0Cu, 0xD0u, 0x0Du, 0xE0u, 0x0Eu, 0xF0u, 0x0Fu, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = (uint32_t)sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0x1000U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w (a0)+,(a1)+\t; palette upload 32 colors\n") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && item->offset == 16U &&
        strcmp(item->semantic_role, "palette") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(64U, auto_item->size);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_WORDS, auto_item->kind);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_palette_upload_uses_source_section_accepted_bytes(void) {
  M68kObject object;
  M68kSection code_section;
  M68kSection data_section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  size_t index;
  uint8_t code_bytes[16] = {
    0x43u, 0xF9u, 0x00u, 0xDFu, 0xF1u, 0x80u,
    0x41u, 0xF9u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x32u, 0xD8u,
    0x4Eu, 0x75u
  };
  uint8_t data_bytes[64] = {
    0x4Eu, 0x75u, 0x01u, 0x11u, 0x02u, 0x22u, 0x03u, 0x33u,
    0x04u, 0x44u, 0x05u, 0x55u, 0x06u, 0x66u, 0x07u, 0x77u,
    0x08u, 0x88u, 0x09u, 0x99u, 0x0Au, 0xAAu, 0x0Bu, 0xBBu,
    0x0Cu, 0xCCu, 0x0Du, 0xDDu, 0x0Eu, 0xEEu, 0x0Fu, 0xFFu,
    0x00u, 0x10u, 0x01u, 0x20u, 0x02u, 0x30u, 0x03u, 0x40u,
    0x04u, 0x50u, 0x05u, 0x60u, 0x06u, 0x70u, 0x07u, 0x80u,
    0x08u, 0x90u, 0x09u, 0xA0u, 0x0Au, 0xB0u, 0x0Bu, 0xC0u,
    0x0Cu, 0xD0u, 0x0Du, 0xE0u, 0x0Eu, 0xF0u, 0x0Fu, 0x00u
  };
  memset(&code_section, 0, sizeof(code_section));
  memset(&data_section, 0, sizeof(data_section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  code_section.kind = M68K_SECTION_CODE;
  code_section.size = sizeof(code_bytes);
  code_section.data_size = sizeof(code_bytes);
  code_section.data = code_bytes;
  added = m68k_object_add_section(&object, &code_section);
  M68K_C_ASSERT(added.ok);
  data_section.kind = M68K_SECTION_DATA;
  data_section.size = sizeof(data_bytes);
  data_section.data_size = sizeof(data_bytes);
  data_section.data = data_bytes;
  added = m68k_object_add_section(&object, &data_section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 8U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 1U;
  fixup.has_target_section = 1;
  fixup.platform_relocation_record_kind = AMIGA_HUNK_FILE_META_RECORD_KIND_HUNK_RELOC32;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w (a0)+,(a1)+\t; palette upload 32 colors\n") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 1U && item->offset == 0U &&
        strcmp(item->semantic_role, "palette") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(64U, auto_item->size);
  M68K_C_ASSERT_U32(M68K_ANALYSIS_STRUCTURED_DATA_WORDS, auto_item->kind);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_copper_pointer_renders_combined_display_setup_comment(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[88] = {
    0x33u, 0xFCu, 0x42u, 0x00u, 0x00u, 0xDFu, 0xF1u, 0x00u,
    0x33u, 0xFCu, 0x00u, 0x00u, 0x00u, 0xDFu, 0xF1u, 0x08u,
    0x33u, 0xFCu, 0x00u, 0x00u, 0x00u, 0xDFu, 0xF1u, 0x0Au,
    0x33u, 0xFCu, 0x00u, 0x38u, 0x00u, 0xDFu, 0xF0u, 0x92u,
    0x33u, 0xFCu, 0x00u, 0xD0u, 0x00u, 0xDFu, 0xF0u, 0x94u,
    0x33u, 0xFCu, 0x37u, 0x81u, 0x00u, 0xDFu, 0xF0u, 0x8Eu,
    0x33u, 0xFCu, 0xFFu, 0xC1u, 0x00u, 0xDFu, 0xF0u, 0x90u,
    0x23u, 0xFCu, 0x00u, 0x00u, 0x00u, 0x44u, 0x00u, 0xDFu, 0xF0u, 0x80u,
    0x4Eu, 0x75u,
    0x00u, 0xE0u, 0x00u, 0x07u,
    0x00u, 0xE2u, 0x00u, 0x00u,
    0x00u, 0xE4u, 0x00u, 0x07u,
    0x00u, 0xE6u, 0x20u, 0x00u,
    0xFFu, 0xFFu, 0xFFu, 0xFEu
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = (uint32_t)sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source,
    "display layout 2 bitmap planes $00070000..$00072000 step $2000") != NULL);
  M68K_C_ASSERT(strstr(source,
    "display setup 4 bitplanes lores color window v=$37..$FF h=$81..$C1 rows 200 "
    "fetch $38..$D0 row 40 bytes/plane mod 0/0 span $1F40/plane") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_audio_pointer_and_length_auto_classifies_sound_sample(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
  const M68kAnalysisStructuredDataItem *auto_item = NULL;
  char *source = NULL;
  uint16_t index;
  uint8_t bytes[28] = {
    0x23u, 0xFCu, 0x00u, 0x00u, 0x00u, 0x14u, 0x00u, 0xDFu, 0xF0u, 0xA0u,
    0x33u, 0xFCu, 0x00u, 0x04u, 0x00u, 0xDFu, 0xF0u, 0xA4u,
    0x4Eu, 0x75u,
    0x11u, 0x22u, 0x33u, 0x44u, 0x55u, 0x66u, 0x77u, 0x88u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = (uint32_t)sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.l #loc_0_00000014,_custom+aud0+ac_ptr.l\t; sound_sample pointer\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.w #$4,_custom+aud0+ac_len.l\t; sound sample length 8 bytes\n") != NULL);
  for (index = 0U; index < source_analysis.policy.structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &source_analysis.policy.structured_data_items[index];
    if (item->has_section_index && item->section_index == 0U && item->offset == 0x14U &&
        strcmp(item->semantic_role, "sound_sample") == 0) {
      auto_item = item;
      break;
    }
  }
  M68K_C_ASSERT(auto_item != NULL);
  M68K_C_ASSERT_U32(8U, auto_item->size);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_audio_length_register_source_comment(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[14] = {
    0x32u, 0x28u, 0xFFu, 0xFEu,
    0xE2u, 0x49u,
    0x33u, 0xC1u, 0x00u, 0xDFu, 0xF0u, 0xA4u,
    0x4Eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = (uint32_t)sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.w d1,_custom+aud0+ac_len.l\t; audio sample length derived from -$0002(a0) header word\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_genam_audio_pointer_preserves_dynamic_source_provenance(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[112];
  memset(bytes, 0, sizeof(bytes));
  bytes[0] = 0x41u; bytes[1] = 0xF9u; bytes[2] = 0x00u; bytes[3] = 0x00u;
  bytes[4] = 0x00u; bytes[5] = 0x30u;
  bytes[6] = 0xD0u; bytes[7] = 0xFBu; bytes[8] = 0x00u; bytes[9] = 0x20u;
  bytes[10] = 0x30u; bytes[11] = 0x3Bu; bytes[12] = 0x00u; bytes[13] = 0x1Eu;
  bytes[14] = 0x41u; bytes[15] = 0xE8u; bytes[16] = 0x00u; bytes[17] = 0x30u;
  bytes[18] = 0xE5u; bytes[19] = 0x80u;
  bytes[20] = 0x23u; bytes[21] = 0xC8u; bytes[22] = 0x00u; bytes[23] = 0xDFu;
  bytes[24] = 0xF0u; bytes[25] = 0xA0u;
  bytes[26] = 0x33u; bytes[27] = 0xC0u; bytes[28] = 0x00u; bytes[29] = 0xDFu;
  bytes[30] = 0xF0u; bytes[31] = 0xA6u;
  bytes[32] = 0x4Eu; bytes[33] = 0x75u;
  bytes[40] = 0x00u; bytes[41] = 0x04u;
  bytes[42] = 0x01u; bytes[43] = 0x23u;
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = (uint32_t)sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tadda.w loc_0_00000028(pc,d0.w),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l $0030(a0),a0\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.l a0,_custom+aud0+ac_ptr.l\t"
    "; source loc_0_00000060 + dynamic offset from loc_0_00000028 | sound_sample pointer\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.w d0,_custom+aud0+ac_per.l\t; period from loc_0_0000002A transformed | audio period\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_absolute_slot_reload_tracks_runtime_sink_pointer(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[56] = {
    0x23u, 0xFCu, 0x00u, 0x06u, 0x7Du, 0x00u, 0x00u, 0x00u, 0x00u, 0x30u,
    0x22u, 0x79u, 0x00u, 0x00u, 0x00u, 0x30u,
    0x23u, 0xC9u, 0x00u, 0xDFu, 0xF0u, 0x20u,
    0x4Eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u,
    0xDEu, 0xADu, 0xBEu, 0xEFu
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "disk_buffer_00067D00\tEQU\t$67D00\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l #disk_buffer_00067D00,$00000030.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmovea.l $00000030.l,a1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l a1,_custom+dskpt.l\t; disk_buffer pointer $00067D00\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_external_runtime_sink_address_renders_pointer_comment(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[12] = {
    0x23u, 0xFCu, 0x00u, 0x06u, 0x7Du, 0x00u, 0x00u, 0xDFu, 0xF0u, 0x20u,
    0x4Eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "disk_buffer_00067D00\tEQU\t$67D00\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.l #disk_buffer_00067D00,_custom+dskpt.l\t; disk_buffer pointer $00067D00\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_copper_storage_sink_origin_renders_bitmap_symbol(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[52] = {
    0x41u, 0xF9u, 0x00u, 0x00u, 0x00u, 0x24u,
    0x20u, 0x3Cu, 0x00u, 0x06u, 0x00u, 0x00u,
    0x31u, 0x40u, 0x00u, 0x06u,
    0x23u, 0xFCu, 0x00u, 0x06u, 0x00u, 0x00u, 0x00u, 0x00u, 0x01u, 0x30u,
    0x4Eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0xE0u, 0x00u, 0x00u, 0x00u, 0xE2u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x06u, 0x00u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = (uint32_t)sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0x100U;
  policy.runtime_entry_point_count = 1U;
  policy.runtime_entry_points[0].has_section_index = 1U;
  policy.runtime_entry_points[0].section_index = 0U;
  policy.runtime_entry_points[0].runtime_address = 0x100U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "bitmap_00060000\tEQU\t$60000\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l #bitmap_00060000,d0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l #bitmap_00060000,abs_0_00000130.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w d0,$0006(a0)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_copper_storage_sink_preserves_branch_distinct_bitmap_origins(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[34] = {
    0x41u, 0xF9u, 0x00u, 0x00u, 0x00u, 0x1Au,
    0x20u, 0x3Cu, 0x00u, 0x06u, 0x00u, 0x00u,
    0x66u, 0x06u,
    0x20u, 0x3Cu, 0x00u, 0x06u, 0x7Du, 0x00u,
    0x31u, 0x40u, 0x00u, 0x02u,
    0x4Eu, 0x75u,
    0x00u, 0xE0u, 0x00u, 0x00u, 0x00u, 0xE2u, 0x00u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.runtime_range_count = 1U;
  policy.runtime_ranges[0].has_section_index = 1U;
  policy.runtime_ranges[0].section_index = 0U;
  policy.runtime_ranges[0].offset = 0U;
  policy.runtime_ranges[0].size = (uint32_t)sizeof(bytes);
  policy.runtime_ranges[0].runtime_address = 0U;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "bitmap_00060000\tEQU\t$60000\n") != NULL);
  M68K_C_ASSERT(strstr(source, "bitmap_00067D00\tEQU\t$67D00\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l #bitmap_00060000,d0\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l #bitmap_00067D00,d0\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_copper_storage_sink_rejects_low_scalar_origin(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[28] = {
    0x41u, 0xF9u, 0x00u, 0x00u, 0x00u, 0x14u,
    0x20u, 0x3Cu, 0x00u, 0x00u, 0x00u, 0xBAu,
    0x31u, 0x40u, 0x00u, 0x06u,
    0x4Eu, 0x75u,
    0x00u, 0x00u,
    0x00u, 0xE0u, 0x00u, 0x00u, 0x00u, 0xE2u, 0x00u, 0x00u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "bitmap_000000BA") == NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l #$BA,d0\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_dsklen_write_renders_dma_size_comment(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[10] = {
    0x33u, 0xFCu, 0x9Fu, 0x40u, 0x00u, 0xDFu, 0xF0u, 0x24u,
    0x4Eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #$9F40,_custom+dsklen.l\t; disk DMA read 16000 bytes\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_marks_structured_data_code_overlap(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[4] = {0x4Au, 0xFCu, 0x4Eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.structured_data_item_count = 1U;
  policy.structured_data_items[0].has_section_index = 1U;
  policy.structured_data_items[0].section_index = 0U;
  policy.structured_data_items[0].offset = 0U;
  policy.structured_data_items[0].size = 2U;
  policy.structured_data_items[0].kind = M68K_ANALYSIS_STRUCTURED_DATA_WORDS;
  snprintf(policy.structured_data_items[0].struct_name,
    sizeof(policy.structured_data_items[0].struct_name), "header");
  snprintf(policy.structured_data_items[0].field_name,
    sizeof(policy.structured_data_items[0].field_name), "header_word");
  snprintf(policy.structured_data_items[0].field_type,
    sizeof(policy.structured_data_items[0].field_type), "UWORD");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "invalid overlap: decoded code at $0000 starts at structured data") != NULL);
  M68K_C_ASSERT(strstr(source, "\tillegal\n") == NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w $4AFC\t; UWORD header_word") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.accepted_instructions);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_renders_call_input_domain_immediate(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  const AmigaOsLibraryVectorInfo *alert_vector = amiga_os_find_library_vector_by_symbol_name("_LVOAlert");
  int32_t an_icon_lib = 0;
  int32_t ag_open_lib = 0;
  int32_t ao_dos_lib = 0;
  uint32_t alert_value;
  int16_t alert_lvo;
  uint8_t bytes[14];
  M68K_C_ASSERT(alert_vector != NULL);
  M68K_C_ASSERT(amiga_os_find_constant_value("AN_IconLib", &an_icon_lib));
  M68K_C_ASSERT(amiga_os_find_constant_value("AG_OpenLib", &ag_open_lib));
  M68K_C_ASSERT(amiga_os_find_constant_value("AO_DOSLib", &ao_dos_lib));
  alert_value = (uint32_t)(an_icon_lib | ag_open_lib | ao_dos_lib);
  alert_lvo = alert_vector->lvo;
  bytes[0] = 0x2Eu;
  bytes[1] = 0x3Cu;
  bytes[2] = (uint8_t)(alert_value >> 24);
  bytes[3] = (uint8_t)(alert_value >> 16);
  bytes[4] = (uint8_t)(alert_value >> 8);
  bytes[5] = (uint8_t)alert_value;
  bytes[6] = 0x2Cu;
  bytes[7] = 0x78u;
  bytes[8] = 0x00u;
  bytes[9] = 0x04u;
  bytes[10] = 0x4Eu;
  bytes[11] = 0xAEu;
  bytes[12] = (uint8_t)((uint16_t)alert_lvo >> 8);
  bytes[13] = (uint8_t)alert_lvo;
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  object.platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "    INCLUDE \"exec/alerts.i\"\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l #AN_IconLib|AG_OpenLib|AO_DOSLib,d7\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr _LVOAlert(a6)\n") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_inline_return_string_call_skips_payload(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[46] = {
    0x61u, 0x00u, 0x00u, 0x1eu,
    0x48u, 0x65u, 0x6cu, 0x6cu, 0x6fu, 0x00u,
    0x4eu, 0x71u, 0x4eu, 0x75u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u,
    0x00u, 0x00u,
    0x2fu, 0x0bu,
    0x26u, 0x6fu, 0x00u, 0x04u,
    0x2fu, 0x4bu, 0x00u, 0x04u,
    0x26u, 0x5fu,
    0x4eu, 0x75u
  };
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "bsr.w loc_0_00000020") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.b $48,$65,$6C,$6C,$6F,$00") != NULL);
  M68K_C_ASSERT(strstr(source, "\tnop") != NULL);
  M68K_C_ASSERT(strstr(source, "eori") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.required_instruction_failures);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_scopes_external_fpu_coprocessor_id(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[4] = {0xFBu, 0x54u, 0x4Eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.max_cpu = M68K_ASM_CPU_68020;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tFPU     5\n") != NULL || strstr(source, "    FPU     5\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tfrestore (a4)") != NULL || strstr(source, "    frestore (a4)") != NULL);
  M68K_C_ASSERT(strstr(source, "\tFPU     1\n") != NULL || strstr(source, "    FPU     1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "cprestore") == NULL);
  M68K_C_ASSERT(strstr(source, "dc.b $FB,$54") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.unsupported_instruction_demotes);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_uses_default_fpu_mnemonic(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[4] = {0xF3u, 0x56u, 0x4Eu, 0x75u};
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  policy.max_cpu = M68K_ASM_CPU_68040;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tfrestore (a6)") != NULL || strstr(source, "    frestore (a6)") != NULL);
  M68K_C_ASSERT(strstr(source, "cprestore") == NULL);
  M68K_C_ASSERT(strstr(source, "FPU") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_demotes_opcode_relocation_to_data_expr(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[6] = {0x00u, 0x00u, 0x00u, 0x00u, 0x4eu, 0x75u};
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 0U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "dc.l loc_0_00000000") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(1U, profile.opcode_relocation_conflicts_resolved_by_demote);
  M68K_C_ASSERT_U32(0U, profile.first_opcode_relocation_conflict_section);
  M68K_C_ASSERT_U32(0U, profile.first_opcode_relocation_conflict_offset);
  M68K_C_ASSERT_U32(0U, profile.first_opcode_relocation_conflict_aux_offset);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_relocation_failures);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_alloc_returns_text(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[8] = {0x00u, 0x00u, 0x00u, 0x04u, 0xdeu, 0xadu, 0xbeu, 0xefu};
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 0U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "    SECTION section,data") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000004:") != NULL);
  M68K_C_ASSERT(strstr(source, "dc.l loc_0_00000004") != NULL);
  M68K_C_ASSERT_U32(1U, profile.asm_source_enabled);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(1U, profile.asm_source_relocation_exprs);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_collapses_repeated_present_data(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[32];
  memset(bytes, 0, sizeof(bytes));
  memset(&section, 0, sizeof(section));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_DATA;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "\tdcb.b $20,$00\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.b $00,$00,$00,$00,$00,$00,$00,$00") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  m68k_facts_v2_free_text(source);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_render_asm_source_alloc_fails_on_invalid_relocation(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[10] = {0x4eu, 0x71u, 0x4eu, 0x75u, 0x00u, 0x00u, 0x00u, 0x00u, 0xffu, 0xffu};
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(bytes);
  section.data_size = sizeof(bytes);
  section.data = bytes;
  added = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(added.ok);
  fixup.section_index = 0U;
  fixup.offset = 6U;
  fixup.kind = M68K_FIXUP_ABS;
  fixup.width = M68K_FIXUP_WIDTH_32;
  fixup.addend = 2;
  fixup.target_section_index = 0U;
  fixup.has_target_section = 1;
  added = m68k_object_add_fixup(&object, &fixup);
  M68K_C_ASSERT(added.ok);
  m68k_analysis_policy_init_default(&policy);
  M68K_C_ASSERT_INT(-1, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source == NULL);
  M68K_C_ASSERT_U32(1U, profile.asm_source_enabled);
  M68K_C_ASSERT_U32(1U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(1U, profile.relocation_failures);
  M68K_C_ASSERT_U32(M68K_FACTS_V2_RELOCATION_FAILURE_TARGET_OUT_OF_RANGE,
    profile.first_relocation_failure_reason);
  m68k_object_destroy(&object);
  return 0;
}

int m68k_c_ir_tests(void) {
  static const M68kCTestCase cases[] = {
    {"render_policy_defaults", test_render_policy_defaults},
    {"source_statement_renderer_renders_single_statement", test_source_statement_renderer_renders_single_statement},
    {"parse_syntax_mode_name", test_parse_syntax_mode_name},
    {"generated_cpu_vector_metadata_marks_interrupt_autovectors",
      test_generated_cpu_vector_metadata_marks_interrupt_autovectors},
    {"generated_call_ea_metadata_marks_control_target",
      test_generated_call_ea_metadata_marks_control_target},
    {"render_index_scale_uses_scale_value_not_bits", test_render_index_scale_uses_scale_value_not_bits},
    {"68030_pmmu_fc_forms_roundtrip_from_kb", test_68030_pmmu_fc_forms_roundtrip_from_kb},
    {"movec_control_register_cpu_mask_from_kb", test_movec_control_register_cpu_mask_from_kb},
    {"coprocessor_id_roundtrips_from_kb_id_field", test_coprocessor_id_roundtrips_from_kb_id_field},
    {"analysis_defaults_and_inits", test_analysis_defaults_and_inits},
    {"instruction_mnemonic_helpers_use_id", test_instruction_mnemonic_helpers_use_id},
    {"section_append_statement_copies_data", test_section_append_statement_copies_data},
    {"section_analysis_label_dedupes", test_section_analysis_label_dedupes},
    {"source_analysis_append_section_copies_recovered_dispatches",
      test_source_analysis_append_section_copies_recovered_dispatches},
    {"source_analysis_append_section_rehydrates_platform_name_refs",
      test_source_analysis_append_section_rehydrates_platform_name_refs},
    {"source_analysis_append_section_copies_ref_only_platform_names",
      test_source_analysis_append_section_copies_ref_only_platform_names},
    {"section_analysis_records_typed_global_slot_effects",
      test_section_analysis_records_typed_global_slot_effects},
    {"source_model_symbol_index_preserves_lookup_semantics",
      test_source_model_symbol_index_preserves_lookup_semantics},
    {"section_many_interleaved_labels_and_data", test_section_many_interleaved_labels_and_data},
    {"section_many_interleaved_labels_and_expr_data", test_section_many_interleaved_labels_and_expr_data},
    {"arena_mark_rewind_reuses_same_block_range", test_arena_mark_rewind_reuses_same_block_range},
    {"arena_rewind_discards_later_blocks", test_arena_rewind_discards_later_blocks},
    {"arena_reset_poisons_head_block_range", test_arena_reset_poisons_head_block_range},
    {"arena_rejects_overflow_allocations", test_arena_rejects_overflow_allocations},
    {"decode_ir_decodes_aligned_candidates", test_decode_ir_decodes_aligned_candidates},
    {"decode_ir_treats_cpu_policy_as_ceiling", test_decode_ir_treats_cpu_policy_as_ceiling},
    {"source_parse_treats_cpu_policy_as_ceiling", test_source_parse_treats_cpu_policy_as_ceiling},
    {"source_fpu_directive_encodes_external_coprocessor_id",
      test_source_fpu_directive_encodes_external_coprocessor_id},
    {"source_fpu_directive_uses_external_id_under_cpu_ceiling",
      test_source_fpu_directive_uses_external_id_under_cpu_ceiling},
    {"source_fpu_zero_disables_fpu_alias_instruction",
      test_source_fpu_zero_disables_fpu_alias_instruction},
    {"source_org_sets_logical_pc_without_padding", test_source_org_sets_logical_pc_without_padding},
    {"decode_ir_negative_cache_preserves_higher_cpu_decode",
      test_decode_ir_negative_cache_preserves_higher_cpu_decode},
    {"decode_ir_records_branch_target_candidate", test_decode_ir_records_branch_target_candidate},
    {"decode_ir_branch_word_target_uses_opcode_pc", test_decode_ir_branch_word_target_uses_opcode_pc},
    {"decode_ir_records_pc_relative_data_target_candidate",
      test_decode_ir_records_pc_relative_data_target_candidate},
    {"decode_ir_records_pc_index_data_target_candidate",
      test_decode_ir_records_pc_index_data_target_candidate},
    {"facts_v2_pc_index_data_target_auto_classifies_lookup_scalar",
      test_facts_v2_pc_index_data_target_auto_classifies_lookup_scalar},
    {"facts_v2_pc_index_data_target_auto_classifies_lookup_span",
      test_facts_v2_pc_index_data_target_auto_classifies_lookup_span},
    {"facts_v2_indexed_postincrement_reads_auto_classify_word_table",
      test_facts_v2_indexed_postincrement_reads_auto_classify_word_table},
    {"facts_v2_genam_byte_postincrement_table_stays_byte_data",
      test_facts_v2_genam_byte_postincrement_table_stays_byte_data},
    {"facts_v2_indexed_local_base_auto_classifies_scalar_table",
      test_facts_v2_indexed_local_base_auto_classifies_scalar_table},
    {"facts_v2_genam_indexed_word_read_stays_unclassified_data",
      test_facts_v2_genam_indexed_word_read_stays_unclassified_data},
    {"facts_v2_indexed_local_base_auto_classifies_pointer_table",
      test_facts_v2_indexed_local_base_auto_classifies_pointer_table},
    {"decode_ir_keeps_odd_branch_target_for_analysis", test_decode_ir_keeps_odd_branch_target_for_analysis},
    {"fact_ir_label_creation_dedupes", test_fact_ir_label_creation_dedupes},
    {"facts_v2_profile_collects_decode_and_label_facts", test_facts_v2_profile_collects_decode_and_label_facts},
    {"facts_v2_implicit_entry_only_first_code_section",
      test_facts_v2_implicit_entry_only_first_code_section},
    {"facts_v2_implicit_entry_does_not_scan_to_later_code_section",
      test_facts_v2_implicit_entry_does_not_scan_to_later_code_section},
    {"facts_v2_required_entry_without_decode_is_hard_failure",
      test_facts_v2_required_entry_without_decode_is_hard_failure},
    {"facts_v2_work_queue_dedupes_same_confidence_starts",
      test_facts_v2_work_queue_dedupes_same_confidence_starts},
    {"facts_v2_work_queue_dedupes_same_runtime_view_starts",
      test_facts_v2_work_queue_dedupes_same_runtime_view_starts},
    {"facts_v2_records_mid_instruction_required_label", test_facts_v2_records_mid_instruction_required_label},
    {"facts_v2_odd_code_target_is_hard_failure", test_facts_v2_odd_code_target_is_hard_failure},
    {"facts_v2_direct_rebuild_profile_marks_source_refusal_without_rendering",
      test_facts_v2_direct_rebuild_profile_marks_source_refusal_without_rendering},
    {"facts_v2_rejects_tool_inferred_interior_target_label",
      test_facts_v2_rejects_tool_inferred_interior_target_label},
    {"facts_v2_materializes_required_data_boundary_label",
      test_facts_v2_materializes_required_data_boundary_label},
    {"facts_v2_relocation_uses_payload_target_before_addend",
      test_facts_v2_relocation_uses_payload_target_before_addend},
    {"facts_v2_invalid_relocation_payload_records_violation",
      test_facts_v2_invalid_relocation_payload_records_violation},
    {"facts_v2_atari_relocation_uses_platform_normalized_addend",
      test_facts_v2_atari_relocation_uses_platform_normalized_addend},
    {"facts_v2_atari_bss_image_relocation_renders_symbolic_instruction",
      test_facts_v2_atari_bss_image_relocation_renders_symbolic_instruction},
    {"facts_v2_render_asm_source_recovers_atari_trap_call",
      test_facts_v2_render_asm_source_recovers_atari_trap_call},
    {"facts_v2_atari_invalid_image_relocation_refuses_source",
      test_facts_v2_atari_invalid_image_relocation_refuses_source},
    {"facts_v2_asm_source_preserves_atari_program_flags",
      test_facts_v2_asm_source_preserves_atari_program_flags},
    {"facts_v2_classifies_hunk_positive_relocation_anchor",
      test_facts_v2_classifies_hunk_positive_relocation_anchor},
    {"facts_v2_classifies_hunk_positive_data_relocation_anchor",
      test_facts_v2_classifies_hunk_positive_data_relocation_anchor},
    {"facts_v2_classifies_hunk_negative_relocation_anchor",
      test_facts_v2_classifies_hunk_negative_relocation_anchor},
    {"facts_v2_asm_source_renders_valid_relocation_expr",
      test_facts_v2_asm_source_renders_valid_relocation_expr},
    {"facts_v2_hunk_relocation_target_inside_relocation_payload_is_numeric",
      test_facts_v2_hunk_relocation_target_inside_relocation_payload_is_numeric},
    {"amiga_hunk_writer_preserves_reloc32_group_shape",
      test_amiga_hunk_writer_preserves_reloc32_group_shape},
    {"facts_v2_asm_source_allows_demoted_interior_label", test_facts_v2_asm_source_allows_demoted_interior_label},
    {"facts_v2_asm_source_hashes_clean_byte_source", test_facts_v2_asm_source_hashes_clean_byte_source},
    {"facts_v2_render_asm_source_renders_symbolic_branch",
      test_facts_v2_render_asm_source_renders_symbolic_branch},
    {"facts_v2_render_asm_source_renders_symbolic_pc_relative_data_target",
      test_facts_v2_render_asm_source_renders_symbolic_pc_relative_data_target},
    {"facts_v2_render_asm_source_accepts_reachable_68030_pmmu",
      test_facts_v2_render_asm_source_accepts_reachable_68030_pmmu},
    {"facts_v2_render_asm_source_keeps_unrelocated_abs_call_numeric",
      test_facts_v2_render_asm_source_keeps_unrelocated_abs_call_numeric},
    {"facts_v2_render_asm_source_symbolizes_local_abs_word_call",
      test_facts_v2_render_asm_source_symbolizes_local_abs_word_call},
    {"facts_v2_prefers_lower_cpu_fallthrough_over_inferred_interior_target",
      test_facts_v2_prefers_lower_cpu_fallthrough_over_inferred_interior_target},
    {"facts_v2_prefers_same_cpu_fallthrough_over_inferred_interior_target",
      test_facts_v2_prefers_same_cpu_fallthrough_over_inferred_interior_target},
    {"facts_v2_detects_runtime_copy_jump_target", test_facts_v2_detects_runtime_copy_jump_target},
    {"facts_v2_traced_indirect_call_promotes_known_target",
      test_facts_v2_traced_indirect_call_promotes_known_target},
    {"facts_v2_traced_displacement_indirect_jump_promotes_runtime_copy_target",
      test_facts_v2_traced_displacement_indirect_jump_promotes_runtime_copy_target},
    {"facts_v2_unmaterialized_runtime_copy_code_address_renders_equ_symbol",
      test_facts_v2_unmaterialized_runtime_copy_code_address_renders_equ_symbol},
    {"facts_v2_absolute_stack_top_load_renders_equ_symbol",
      test_facts_v2_absolute_stack_top_load_renders_equ_symbol},
    {"facts_v2_records_unresolved_indirect_jump_site",
      test_facts_v2_records_unresolved_indirect_jump_site},
    {"facts_v2_records_rejected_indirect_table_bounds",
      test_facts_v2_records_rejected_indirect_table_bounds},
    {"facts_v2_resolved_platform_call_not_unresolved_indirect_site",
      test_facts_v2_resolved_platform_call_not_unresolved_indirect_site},
    {"facts_v2_open_library_d0_movea_promotes_a6_base",
      test_facts_v2_open_library_d0_movea_promotes_a6_base},
    {"facts_v2_open_library_cross_section_name_promotes_a6_base",
      test_facts_v2_open_library_cross_section_name_promotes_a6_base},
    {"facts_v2_stack_stored_callback_vector_promotes_target",
      test_facts_v2_stack_stored_callback_vector_promotes_target},
    {"facts_v2_traced_indirect_jump_promotes_long_table_targets",
      test_facts_v2_traced_indirect_jump_promotes_long_table_targets},
    {"facts_v2_long_jump_table_base_renders_label_addend",
      test_facts_v2_long_jump_table_base_renders_label_addend},
    {"facts_v2_traced_indirect_jump_keeps_later_table_state",
      test_facts_v2_traced_indirect_jump_keeps_later_table_state},
    {"facts_v2_runtime_mapped_long_dispatch_promotes_table_targets",
      test_facts_v2_runtime_mapped_long_dispatch_promotes_table_targets},
    {"facts_v2_long_dispatch_promotes_targets_beyond_small_trace_set",
      test_facts_v2_long_dispatch_promotes_targets_beyond_small_trace_set},
    {"facts_v2_traced_indirect_jump_promotes_word_relative_table_targets",
      test_facts_v2_traced_indirect_jump_promotes_word_relative_table_targets},
    {"facts_v2_word_dispatch_promotes_far_relative_targets",
      test_facts_v2_word_dispatch_promotes_far_relative_targets},
    {"source_analysis_table_record_marks_code_overlap_conflict",
      test_source_analysis_table_record_marks_code_overlap_conflict},
    {"facts_v2_word_dispatch_stops_far_table_at_zero_boundary",
      test_facts_v2_word_dispatch_stops_far_table_at_zero_boundary},
    {"facts_v2_pc_word_dispatch_renders_labels_across_saved_register",
      test_facts_v2_pc_word_dispatch_renders_labels_across_saved_register},
    {"facts_v2_pc_word_dispatch_renders_labels_across_address_preserving_local_call",
      test_facts_v2_pc_word_dispatch_renders_labels_across_address_preserving_local_call},
    {"facts_v2_runtime_mapped_word_dispatch_renders_lookup_table",
      test_facts_v2_runtime_mapped_word_dispatch_renders_lookup_table},
    {"facts_v2_amiga_execbase_load_does_not_use_runtime_alias",
      test_facts_v2_amiga_execbase_load_does_not_use_runtime_alias},
    {"facts_v2_word_dispatch_renders_bounded_unaccepted_lookup_table",
      test_facts_v2_word_dispatch_renders_bounded_unaccepted_lookup_table},
    {"facts_v2_adjacent_runtime_ranges_do_not_org_back_to_storage",
      test_facts_v2_adjacent_runtime_ranges_do_not_org_back_to_storage},
    {"facts_v2_contained_runtime_range_does_not_emit_second_org",
      test_facts_v2_contained_runtime_range_does_not_emit_second_org},
    {"facts_v2_mid_section_runtime_stub_does_not_org_back_to_storage",
      test_facts_v2_mid_section_runtime_stub_does_not_org_back_to_storage},
    {"facts_v2_detects_interrupt_vector_store_target",
      test_facts_v2_detects_interrupt_vector_store_target},
    {"facts_v2_detects_traced_register_interrupt_vector_store_target",
      test_facts_v2_detects_traced_register_interrupt_vector_store_target},
    {"facts_v2_detects_register_copied_interrupt_vector_store_target",
      test_facts_v2_detects_register_copied_interrupt_vector_store_target},
    {"facts_v2_traced_interrupt_vector_bad_target_does_not_refuse_source",
      test_facts_v2_traced_interrupt_vector_bad_target_does_not_refuse_source},
    {"facts_v2_detects_interrupt_vector_fill_target",
      test_facts_v2_detects_interrupt_vector_fill_target},
    {"facts_v2_maps_copied_runtime_vector_target_to_source_offset",
      test_facts_v2_maps_copied_runtime_vector_target_to_source_offset},
    {"facts_v2_maps_copied_runtime_absolute_call_to_source_offset",
      test_facts_v2_maps_copied_runtime_absolute_call_to_source_offset},
    {"facts_v2_unmapped_absolute_jump_inside_copied_source_stays_numeric",
      test_facts_v2_unmapped_absolute_jump_inside_copied_source_stays_numeric},
    {"facts_v2_runtime_trampoline_copy_does_not_force_low_org",
      test_facts_v2_runtime_trampoline_copy_does_not_force_low_org},
    {"facts_v2_policy_runtime_entrypoint_maps_absolute_load",
      test_facts_v2_policy_runtime_entrypoint_maps_absolute_load},
    {"facts_v2_full_policy_load_view_materializes_without_runtime_entrypoint",
      test_facts_v2_full_policy_load_view_materializes_without_runtime_entrypoint},
    {"facts_v2_full_load_view_does_not_label_alternate_copied_address_with_addend",
      test_facts_v2_full_load_view_does_not_label_alternate_copied_address_with_addend},
    {"facts_v2_runtime_ref_inside_accepted_instruction_stays_numeric",
      test_facts_v2_runtime_ref_inside_accepted_instruction_stays_numeric},
    {"facts_v2_pointer_table_storage_value_stays_numeric_under_runtime_org",
      test_facts_v2_pointer_table_storage_value_stays_numeric_under_runtime_org},
    {"facts_v2_pointer_table_runtime_data_targets_get_labels",
      test_facts_v2_pointer_table_runtime_data_targets_get_labels},
    {"facts_v2_absolute_long_lookup_table_renders_labels_and_nulls",
      test_facts_v2_absolute_long_lookup_table_renders_labels_and_nulls},
    {"facts_v2_word_lookup_table_mixes_labels_and_raw_without_duplicate_fallback",
      test_facts_v2_word_lookup_table_mixes_labels_and_raw_without_duplicate_fallback},
    {"facts_v2_policy_runtime_range_uses_first_class_labels",
      test_facts_v2_policy_runtime_range_uses_first_class_labels},
    {"facts_v2_runtime_alias_refs_emit_first_class_labels",
      test_facts_v2_runtime_alias_refs_emit_first_class_labels},
    {"facts_v2_policy_runtime_entrypoint_starts_inside_view",
      test_facts_v2_policy_runtime_entrypoint_starts_inside_view},
    {"facts_v2_runtime_range_conflict_fails_instead_of_last_map",
      test_facts_v2_runtime_range_conflict_fails_instead_of_last_map},
    {"facts_v2_tool_inferred_runtime_copy_conflict_does_not_abort",
      test_facts_v2_tool_inferred_runtime_copy_conflict_does_not_abort},
    {"facts_v2_policy_runtime_range_wins_over_inferred_copy_conflict",
      test_facts_v2_policy_runtime_range_wins_over_inferred_copy_conflict},
    {"facts_v2_render_asm_source_preserves_exact_byte_immediate_word",
      test_facts_v2_render_asm_source_preserves_exact_byte_immediate_word},
    {"facts_v2_render_asm_source_preserves_move_byte_immediate_high_word",
      test_facts_v2_render_asm_source_preserves_move_byte_immediate_high_word},
    {"facts_v2_render_asm_source_formats_all_bits_set_long_immediate_as_hex",
      test_facts_v2_render_asm_source_formats_all_bits_set_long_immediate_as_hex},
    {"facts_v2_render_asm_source_refuses_unmapped_code_relocation",
      test_facts_v2_render_asm_source_refuses_unmapped_code_relocation},
    {"facts_v2_render_asm_source_maps_immediate_code_relocation",
      test_facts_v2_render_asm_source_maps_immediate_code_relocation},
    {"facts_v2_render_asm_source_maps_relocation_after_imm_operand",
      test_facts_v2_render_asm_source_maps_relocation_after_imm_operand},
    {"facts_v2_render_asm_source_maps_bss_relocation_label",
      test_facts_v2_render_asm_source_maps_bss_relocation_label},
    {"facts_v2_render_asm_source_renders_pure_bss_as_ds_reserve",
      test_facts_v2_render_asm_source_renders_pure_bss_as_ds_reserve},
    {"facts_v2_render_asm_source_symbols_amiga_loadseg_segment_link",
      test_facts_v2_render_asm_source_symbols_amiga_loadseg_segment_link},
    {"facts_v2_demotes_speculative_unencodable_instruction",
      test_facts_v2_demotes_speculative_unencodable_instruction},
    {"facts_v2_demotes_speculative_reserved_full_extension",
      test_facts_v2_demotes_speculative_reserved_full_extension},
    {"facts_v2_required_unencodable_instruction_is_hard_failure",
      test_facts_v2_required_unencodable_instruction_is_hard_failure},
    {"facts_v2_render_asm_source_reencodes_restricted_ea_instruction",
      test_facts_v2_render_asm_source_reencodes_restricted_ea_instruction},
    {"facts_v2_render_asm_source_renders_policy_entry_comment",
      test_facts_v2_render_asm_source_renders_policy_entry_comment},
    {"facts_v2_render_asm_source_renders_policy_register_seed_comment",
      test_facts_v2_render_asm_source_renders_policy_register_seed_comment},
    {"facts_v2_render_asm_source_renders_seeded_lvo_symbol",
      test_facts_v2_render_asm_source_renders_seeded_lvo_symbol},
    {"facts_v2_render_asm_source_symbols_amiga_hardware_registers",
      test_facts_v2_render_asm_source_symbols_amiga_hardware_registers},
    {"facts_v2_analysis_records_absolute_memory_refs",
      test_facts_v2_analysis_records_absolute_memory_refs},
    {"amiga_runtime_address_sinks_are_generated_from_hardware_metadata",
      test_amiga_runtime_address_sinks_are_generated_from_hardware_metadata},
    {"amiga_runtime_struct_id_none_is_zero_safe",
      test_amiga_runtime_struct_id_none_is_zero_safe},
    {"amiga_runtime_resolves_recursive_struct_fields",
      test_amiga_runtime_resolves_recursive_struct_fields},
    {"listing_json_header_collection_stops_at_first_section",
      test_listing_json_header_collection_stops_at_first_section},
    {"listing_json_header_collection_uses_typed_plan_rows",
      test_listing_json_header_collection_uses_typed_plan_rows},
    {"listing_json_typed_plan_emits_expected_rows",
      test_listing_json_typed_plan_emits_expected_rows},
    {"listing_navigation_reports_orphan_code_signals",
      test_listing_navigation_reports_orphan_code_signals},
    {"listing_navigation_reports_runtime_views",
      test_listing_navigation_reports_runtime_views},
    {"listing_json_uses_render_plan_statement_provenance",
      test_listing_json_uses_render_plan_statement_provenance},
    {"listing_json_uses_render_plan_source_range_provenance",
      test_listing_json_uses_render_plan_source_range_provenance},
    {"listing_json_uses_plan_statement_metadata_without_source_file",
      test_listing_json_uses_plan_statement_metadata_without_source_file},
    {"listing_json_classifies_org_subline_as_directive", test_listing_json_classifies_org_subline_as_directive},
    {"render_plan_marks_emitted_org_subline_as_directive",
      test_render_plan_marks_emitted_org_subline_as_directive},
    {"listing_json_uses_render_plan_data_class", test_listing_json_uses_render_plan_data_class},
    {"listing_json_uses_render_plan_data_class_flags", test_listing_json_uses_render_plan_data_class_flags},
    {"listing_navigation_uses_render_plan_data_class", test_listing_navigation_uses_render_plan_data_class},
    {"listing_json_window_matches_full_render_plan_slice",
      test_listing_json_window_matches_full_render_plan_slice},
    {"listing_json_indexed_window_does_not_reemit_headers",
      test_listing_json_indexed_window_does_not_reemit_headers},
    {"listing_json_emits_rsset_layout_regions_from_platform_api_inputs",
      test_listing_json_emits_rsset_layout_regions_from_platform_api_inputs},
    {"listing_json_tracks_app_slot_address_through_lea_copy",
      test_listing_json_tracks_app_slot_address_through_lea_copy},
    {"listing_json_reports_untyped_app_slot_api_args",
      test_listing_json_reports_untyped_app_slot_api_args},
    {"listing_json_tracks_app_slot_address_immediate_adjust",
      test_listing_json_tracks_app_slot_address_immediate_adjust},
    {"listing_json_clears_app_slot_address_source_on_register_clobber",
      test_listing_json_clears_app_slot_address_source_on_register_clobber},
    {"facts_v2_render_asm_source_applies_entry_register_seed_without_seed_offset",
      test_facts_v2_render_asm_source_applies_entry_register_seed_without_seed_offset},
    {"facts_v2_render_asm_source_defines_private_lvo_symbol",
      test_facts_v2_render_asm_source_defines_private_lvo_symbol},
    {"facts_v2_render_asm_source_preserves_base_across_movem_save",
      test_facts_v2_render_asm_source_preserves_base_across_movem_save},
    {"facts_v2_render_asm_source_uses_policy_label_for_branch",
      test_facts_v2_render_asm_source_uses_policy_label_for_branch},
    {"facts_v2_render_asm_source_uses_policy_label_for_data_relocation",
      test_facts_v2_render_asm_source_uses_policy_label_for_data_relocation},
    {"facts_v2_relocation_backed_data_longs_auto_classify_pointer_table",
      test_facts_v2_relocation_backed_data_longs_auto_classify_pointer_table},
    {"facts_v2_render_asm_source_uses_object_symbol_label",
      test_facts_v2_render_asm_source_uses_object_symbol_label},
    {"facts_v2_render_asm_source_infers_lvo_from_object_base_symbol",
      test_facts_v2_render_asm_source_infers_lvo_from_object_base_symbol},
    {"facts_v2_render_asm_source_infers_global_base_slot_from_lvo_set",
      test_facts_v2_render_asm_source_infers_global_base_slot_from_lvo_set},
    {"facts_v2_render_asm_source_app_slot_overlap_uses_rsset_alias",
      test_facts_v2_render_asm_source_app_slot_overlap_uses_rsset_alias},
    {"facts_v2_render_asm_source_does_not_infer_app_slot_from_unknown_a6_custom_offset",
      test_facts_v2_render_asm_source_does_not_infer_app_slot_from_unknown_a6_custom_offset},
    {"facts_v2_render_asm_source_uses_observed_app_slot_widths",
      test_facts_v2_render_asm_source_uses_observed_app_slot_widths},
    {"facts_v2_analysis_keeps_untyped_app_slot_untyped",
      test_facts_v2_analysis_keeps_untyped_app_slot_untyped},
    {"facts_v2_render_asm_source_uses_policy_rsset_layout_region_symbol",
      test_facts_v2_render_asm_source_uses_policy_rsset_layout_region_symbol},
    {"facts_v2_render_asm_source_supports_named_rsset_layouts",
      test_facts_v2_render_asm_source_supports_named_rsset_layouts},
    {"facts_v2_render_asm_source_infers_lvo_from_base_field_slot",
      test_facts_v2_render_asm_source_infers_lvo_from_base_field_slot},
    {"facts_v2_render_asm_source_infers_openlibrary_base_field_slot",
      test_facts_v2_render_asm_source_infers_openlibrary_base_field_slot},
    {"facts_v2_render_asm_source_infers_openlibrary_unowned_base_slot",
      test_facts_v2_render_asm_source_infers_openlibrary_unowned_base_slot},
    {"facts_v2_render_asm_source_infers_openlibrary_helper_unowned_base_slot",
      test_facts_v2_render_asm_source_infers_openlibrary_helper_unowned_base_slot},
    {"facts_v2_render_asm_source_infers_openlibrary_global_base_slot",
      test_facts_v2_render_asm_source_infers_openlibrary_global_base_slot},
    {"facts_v2_render_asm_source_infers_openlibrary_helper_output_global_base_slot",
      test_facts_v2_render_asm_source_infers_openlibrary_helper_output_global_base_slot},
    {"facts_v2_render_asm_source_infers_opendevice_base_field_slot",
      test_facts_v2_render_asm_source_infers_opendevice_base_field_slot},
    {"facts_v2_render_asm_source_renders_typed_app_slot_field_region",
      test_facts_v2_render_asm_source_renders_typed_app_slot_field_region},
    {"facts_v2_render_asm_source_keeps_typed_app_slot_interior_out_of_flat_rsset",
      test_facts_v2_render_asm_source_keeps_typed_app_slot_interior_out_of_flat_rsset},
    {"facts_v2_render_asm_source_keeps_app_slot_aliases_in_rs_region",
      test_facts_v2_render_asm_source_keeps_app_slot_aliases_in_rs_region},
    {"facts_v2_render_asm_source_propagates_typed_base_through_stack_slot",
      test_facts_v2_render_asm_source_propagates_typed_base_through_stack_slot},
    {"facts_v2_render_asm_source_propagates_typed_base_through_absolute_slot",
      test_facts_v2_render_asm_source_propagates_typed_base_through_absolute_slot},
    {"facts_v2_render_asm_source_propagates_api_output_type_to_access",
      test_facts_v2_render_asm_source_propagates_api_output_type_to_access},
    {"facts_v2_render_asm_source_uses_makelibrary_output_type",
      test_facts_v2_render_asm_source_uses_makelibrary_output_type},
    {"facts_v2_analysis_records_unresolved_typed_field_without_rendering_field",
      test_facts_v2_analysis_records_unresolved_typed_field_without_rendering_field},
    {"facts_v2_analysis_classifies_unique_prefix_extension_without_rendering_field",
      test_facts_v2_analysis_classifies_unique_prefix_extension_without_rendering_field},
    {"facts_v2_analysis_refines_ambiguous_prefix_by_exact_access_size",
      test_facts_v2_analysis_refines_ambiguous_prefix_by_exact_access_size},
    {"facts_v2_analysis_propagates_prefix_output_through_base_slot",
      test_facts_v2_analysis_propagates_prefix_output_through_base_slot},
    {"facts_v2_analysis_refines_prefix_storage_from_api_input",
      test_facts_v2_analysis_refines_prefix_storage_from_api_input},
    {"facts_v2_analysis_promotes_unique_prefix_type_through_base_slot",
      test_facts_v2_analysis_promotes_unique_prefix_type_through_base_slot},
    {"facts_v2_analysis_refines_rexxmsg_prefix_by_exact_field_size",
      test_facts_v2_analysis_refines_rexxmsg_prefix_by_exact_field_size},
    {"facts_v2_analysis_refines_textfont_common_prefix_by_exact_field_size",
      test_facts_v2_analysis_refines_textfont_common_prefix_by_exact_field_size},
    {"facts_v2_render_asm_source_propagates_api_output_type_through_lea_copy",
      test_facts_v2_render_asm_source_propagates_api_output_type_through_lea_copy},
    {"facts_v2_analysis_propagates_api_output_type_through_global_slot",
      test_facts_v2_analysis_propagates_api_output_type_through_global_slot},
    {"facts_v2_analysis_propagates_global_slot_reload_through_data_register_copy",
      test_facts_v2_analysis_propagates_global_slot_reload_through_data_register_copy},
    {"facts_v2_analysis_reports_lookup_storage_write_site_provenance",
      test_facts_v2_analysis_reports_lookup_storage_write_site_provenance},
    {"facts_v2_render_asm_source_propagates_api_output_type_through_base_slot",
      test_facts_v2_render_asm_source_propagates_api_output_type_through_base_slot},
    {"facts_v2_render_asm_source_merges_api_output_base_slots_at_join",
      test_facts_v2_render_asm_source_merges_api_output_base_slots_at_join},
    {"facts_v2_render_asm_source_keeps_typed_base_only_across_platform_preserved_regs",
      test_facts_v2_render_asm_source_keeps_typed_base_only_across_platform_preserved_regs},
    {"facts_v2_render_asm_source_propagates_local_helper_api_output_type",
      test_facts_v2_render_asm_source_propagates_local_helper_api_output_type},
    {"facts_v2_render_asm_source_propagates_helper_return_alias_type",
      test_facts_v2_render_asm_source_propagates_helper_return_alias_type},
    {"facts_v2_render_asm_source_propagates_nested_helper_return_alias_type",
      test_facts_v2_render_asm_source_propagates_nested_helper_return_alias_type},
    {"facts_v2_render_asm_source_propagates_api_output_type_through_app_slot",
      test_facts_v2_render_asm_source_propagates_api_output_type_through_app_slot},
    {"facts_v2_render_asm_source_propagates_field_pointer_type_through_app_slot",
      test_facts_v2_render_asm_source_propagates_field_pointer_type_through_app_slot},
    {"facts_v2_analysis_tracks_app_slot_address_through_data_register_copy",
      test_facts_v2_analysis_tracks_app_slot_address_through_data_register_copy},
    {"facts_v2_analysis_propagates_direct_field_pointer_store_through_app_slot",
      test_facts_v2_analysis_propagates_direct_field_pointer_store_through_app_slot},
    {"facts_v2_analysis_propagates_api_output_type_through_stack_slot",
      test_facts_v2_analysis_propagates_api_output_type_through_stack_slot},
    {"facts_v2_analysis_propagates_direct_field_pointer_store_through_stack_and_global_slots",
      test_facts_v2_analysis_propagates_direct_field_pointer_store_through_stack_and_global_slots},
    {"facts_v2_analysis_propagates_lea_substructure_type_through_stack_slot",
      test_facts_v2_analysis_propagates_lea_substructure_type_through_stack_slot},
    {"facts_v2_analysis_propagates_api_output_type_through_data_base_slot_after_call",
      test_facts_v2_analysis_propagates_api_output_type_through_data_base_slot_after_call},
    {"facts_v2_typed_flow_node_visit_guard_preserves_source_rendering",
      test_facts_v2_typed_flow_node_visit_guard_preserves_source_rendering},
    {"facts_v2_typed_flow_worklist_reaches_seed_after_untyped_root",
      test_facts_v2_typed_flow_worklist_reaches_seed_after_untyped_root},
    {"facts_v2_render_asm_source_conflicts_untyped_app_slot_write",
      test_facts_v2_render_asm_source_conflicts_untyped_app_slot_write},
    {"facts_v2_render_asm_source_conflicts_untyped_absolute_slot_write",
      test_facts_v2_render_asm_source_conflicts_untyped_absolute_slot_write},
    {"facts_v2_render_asm_source_unknown_call_clobbers_stack_slot_type",
      test_facts_v2_render_asm_source_unknown_call_clobbers_stack_slot_type},
    {"facts_v2_render_asm_source_propagates_zero_offset_field_pointer_type",
      test_facts_v2_render_asm_source_propagates_zero_offset_field_pointer_type},
    {"facts_v2_render_asm_source_propagates_typed_base_across_branch_target",
      test_facts_v2_render_asm_source_propagates_typed_base_across_branch_target},
    {"facts_v2_render_asm_source_drops_conflicting_typed_base_at_branch_merge",
      test_facts_v2_render_asm_source_drops_conflicting_typed_base_at_branch_merge},
    {"facts_v2_data_ascii_span_auto_classifies_ff_string",
      test_facts_v2_data_ascii_span_auto_classifies_ff_string},
    {"facts_v2_data_ascii_span_respects_accepted_code_overlap",
      test_facts_v2_data_ascii_span_respects_accepted_code_overlap},
    {"facts_v2_data_ascii_span_rejects_length_prefixed_text",
      test_facts_v2_data_ascii_span_rejects_length_prefixed_text},
    {"facts_v2_data_ascii_span_rejects_printable_length_sequence",
      test_facts_v2_data_ascii_span_rejects_printable_length_sequence},
    {"facts_v2_adjacent_short_ascii_spans_auto_classify_string_sequence",
      test_facts_v2_adjacent_short_ascii_spans_auto_classify_string_sequence},
    {"facts_v2_two_short_ascii_spans_remain_raw_data",
      test_facts_v2_two_short_ascii_spans_remain_raw_data},
    {"facts_v2_label_bounded_ascii_span_auto_classifies_string",
      test_facts_v2_label_bounded_ascii_span_auto_classifies_string},
    {"facts_v2_length_prefixed_ascii_sequence_renders_strings",
      test_facts_v2_length_prefixed_ascii_sequence_renders_strings},
    {"facts_v2_length_prefixed_ascii_sequence_respects_code_overlap",
      test_facts_v2_length_prefixed_ascii_sequence_respects_code_overlap},
    {"facts_v2_source_analysis_caps_many_auto_structured_strings",
      test_facts_v2_source_analysis_caps_many_auto_structured_strings},
    {"facts_v2_render_asm_source_infers_lvo_immediate_for_indexed_wrapper",
      test_facts_v2_render_asm_source_infers_lvo_immediate_for_indexed_wrapper},
    {"facts_v2_render_asm_source_ignores_ambiguous_wrapper_stack_arg",
      test_facts_v2_render_asm_source_ignores_ambiguous_wrapper_stack_arg},
    {"facts_v2_reports_orphan_terminal_code_signal_without_promoting",
      test_facts_v2_reports_orphan_terminal_code_signal_without_promoting},
    {"facts_v2_orphan_signal_records_label_context",
      test_facts_v2_orphan_signal_records_label_context},
    {"facts_v2_orphan_signal_classifies_adjacent_pointer_table_as_callback",
      test_facts_v2_orphan_signal_classifies_adjacent_pointer_table_as_callback},
    {"facts_v2_orphan_signal_records_minimum_decode_cpu",
      test_facts_v2_orphan_signal_records_minimum_decode_cpu},
    {"facts_v2_reached_terminal_island_is_not_orphan_signal",
      test_facts_v2_reached_terminal_island_is_not_orphan_signal},
    {"facts_v2_render_asm_source_tracks_cross_section_local_wrapper_without_inline_comment",
      test_facts_v2_render_asm_source_tracks_cross_section_local_wrapper_without_inline_comment},
    {"facts_v2_render_asm_source_tracks_non_wrapper_local_helper_without_inline_comment",
      test_facts_v2_render_asm_source_tracks_non_wrapper_local_helper_without_inline_comment},
    {"facts_v2_render_asm_source_annotates_wrapper_stack_args_without_wrapper_comment",
      test_facts_v2_render_asm_source_annotates_wrapper_stack_args_without_wrapper_comment},
    {"facts_v2_relocated_absolute_jsr_seeds_cross_section_code_target",
      test_facts_v2_relocated_absolute_jsr_seeds_cross_section_code_target},
    {"facts_v2_relocated_absolute_jmp_stub_table_promotes_sibling_entry",
      test_facts_v2_relocated_absolute_jmp_stub_table_promotes_sibling_entry},
    {"facts_v2_render_asm_source_renders_structured_data_comment",
      test_facts_v2_render_asm_source_renders_structured_data_comment},
    {"render_ir_suppresses_orphan_structured_field_label",
      test_render_ir_suppresses_orphan_structured_field_label},
    {"facts_v2_render_asm_source_resident_sizeof_defines_app_sizeof_without_slots",
      test_facts_v2_render_asm_source_resident_sizeof_defines_app_sizeof_without_slots},
    {"facts_v2_render_asm_source_resident_lib_size_omits_empty_app_sizeof",
      test_facts_v2_render_asm_source_resident_lib_size_omits_empty_app_sizeof},
    {"facts_v2_render_asm_source_renders_copper_list_structured_data",
      test_facts_v2_render_asm_source_renders_copper_list_structured_data},
    {"facts_v2_runtime_copper_pointer_auto_classifies_copper_list",
      test_facts_v2_runtime_copper_pointer_auto_classifies_copper_list},
    {"facts_v2_register_runtime_sink_auto_classifies_copper_list",
      test_facts_v2_register_runtime_sink_auto_classifies_copper_list},
    {"facts_v2_copper_bitmap_pointers_render_display_layout_comment",
      test_facts_v2_copper_bitmap_pointers_render_display_layout_comment},
    {"facts_v2_copper_bitmap_memory_uses_are_commented",
      test_facts_v2_copper_bitmap_memory_uses_are_commented},
    {"facts_v2_palette_upload_auto_classifies_source_table",
      test_facts_v2_palette_upload_auto_classifies_source_table},
    {"facts_v2_palette_upload_allows_internal_word_label",
      test_facts_v2_palette_upload_allows_internal_word_label},
    {"facts_v2_palette_upload_survives_movem_saved_call",
      test_facts_v2_palette_upload_survives_movem_saved_call},
    {"facts_v2_palette_upload_survives_address_preserving_local_call",
      test_facts_v2_palette_upload_survives_address_preserving_local_call},
    {"facts_v2_genam_palette_upload_uses_runtime_translated_source_table",
      test_facts_v2_genam_palette_upload_uses_runtime_translated_source_table},
    {"facts_v2_palette_upload_uses_source_section_accepted_bytes",
      test_facts_v2_palette_upload_uses_source_section_accepted_bytes},
    {"facts_v2_copper_pointer_renders_combined_display_setup_comment",
      test_facts_v2_copper_pointer_renders_combined_display_setup_comment},
    {"facts_v2_audio_pointer_and_length_auto_classifies_sound_sample",
      test_facts_v2_audio_pointer_and_length_auto_classifies_sound_sample},
    {"facts_v2_audio_length_register_source_comment",
      test_facts_v2_audio_length_register_source_comment},
    {"facts_v2_genam_audio_pointer_preserves_dynamic_source_provenance",
      test_facts_v2_genam_audio_pointer_preserves_dynamic_source_provenance},
    {"facts_v2_absolute_slot_reload_tracks_runtime_sink_pointer",
      test_facts_v2_absolute_slot_reload_tracks_runtime_sink_pointer},
    {"facts_v2_external_runtime_sink_address_renders_pointer_comment",
      test_facts_v2_external_runtime_sink_address_renders_pointer_comment},
    {"facts_v2_copper_storage_sink_origin_renders_bitmap_symbol",
      test_facts_v2_copper_storage_sink_origin_renders_bitmap_symbol},
    {"facts_v2_copper_storage_sink_preserves_branch_distinct_bitmap_origins",
      test_facts_v2_copper_storage_sink_preserves_branch_distinct_bitmap_origins},
    {"facts_v2_copper_storage_sink_rejects_low_scalar_origin",
      test_facts_v2_copper_storage_sink_rejects_low_scalar_origin},
    {"facts_v2_dsklen_write_renders_dma_size_comment",
      test_facts_v2_dsklen_write_renders_dma_size_comment},
    {"facts_v2_render_asm_source_marks_structured_data_code_overlap",
      test_facts_v2_render_asm_source_marks_structured_data_code_overlap},
    {"facts_v2_render_asm_source_renders_call_input_domain_immediate",
      test_facts_v2_render_asm_source_renders_call_input_domain_immediate},
    {"facts_v2_inline_return_string_call_skips_payload",
      test_facts_v2_inline_return_string_call_skips_payload},
    {"facts_v2_render_asm_source_scopes_external_fpu_coprocessor_id",
      test_facts_v2_render_asm_source_scopes_external_fpu_coprocessor_id},
    {"facts_v2_render_asm_source_uses_default_fpu_mnemonic",
      test_facts_v2_render_asm_source_uses_default_fpu_mnemonic},
    {"facts_v2_demotes_opcode_relocation_to_data_expr",
      test_facts_v2_demotes_opcode_relocation_to_data_expr},
    {"facts_v2_render_asm_source_alloc_returns_text", test_facts_v2_render_asm_source_alloc_returns_text},
    {"facts_v2_render_asm_source_collapses_repeated_present_data",
      test_facts_v2_render_asm_source_collapses_repeated_present_data},
    {"facts_v2_render_asm_source_alloc_fails_on_invalid_relocation",
      test_facts_v2_render_asm_source_alloc_fails_on_invalid_relocation},
  };
  return m68k_c_test_run_suite("m68k_ir", cases, sizeof(cases) / sizeof(cases[0]));
}
