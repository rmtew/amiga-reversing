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
#include "m68k_source_model.h"
#include "m68k_source_pipeline.h"
#include "platform_common.h"
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
  uint8_t out_bytes[4];
  const uint8_t bytes[2] = {0xFBu, 0x54u};
  decoded = m68k_ir_decode_one(bytes, sizeof(bytes), M68K_ASM_CPU_68020, m68k_diag_sink(NULL));
  M68K_C_ASSERT_U32(2U, (uint32_t)decoded.byte_count);
  M68K_C_ASSERT_U32(M68K_ASM_MNEMONIC_CPRESTORE, decoded.mnemonic_id);
  M68K_C_ASSERT_U32(1U, decoded.has_coprocessor_id);
  M68K_C_ASSERT_U32(5U, decoded.coprocessor_id);
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
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
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
  M68K_C_ASSERT(strstr(source, "dc.l $00007FFE") != NULL);
  M68K_C_ASSERT(strstr(source, "HUNK_RELOC32 numeric") != NULL);
  M68K_C_ASSERT(strstr(source, "base(hunk 1)+$00007FFE") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(1U, profile.asm_source_lossy_numeric_hunk_relocations);
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
  M68kSection section;
  M68kObjectAddResult added;
  M68kFixup fixup;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[8] = {0x4eu, 0x71u, 0x4eu, 0x75u, 0xffu, 0xffu, 0xffu, 0xfcu};
  memset(&section, 0, sizeof(section));
  memset(&fixup, 0, sizeof(fixup));
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
  M68K_C_ASSERT(strstr(source, "dc.l $FFFFFFFC") != NULL);
  M68K_C_ASSERT(strstr(source, "HUNK_RELOC32 numeric") != NULL);
  M68K_C_ASSERT(strstr(source, "base(hunk 0)-$00000004") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(1U, profile.asm_source_lossy_numeric_hunk_relocations);
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
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "    SECTION section,code") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000004:") != NULL);
  M68K_C_ASSERT(strstr(source, "bra") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000004") != NULL);
  M68K_C_ASSERT(strstr(source, "facts_v2 instruction bytes") == NULL);
  M68K_C_ASSERT_U32(2U, profile.asm_source_symbolic_instructions);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_render_failures);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_byte_mismatches);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_relocation_failures);
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
  M68K_C_ASSERT(strstr(source, "loc_0_00000006:") != NULL);
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

static int test_facts_v2_detects_runtime_copy_jump_target(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  M68kSourceAnalysisIR source_analysis;
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
  M68K_C_ASSERT(strstr(source, "\tjmp loc_0_00000100.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $100\nloc_0_00000100:\n\tnop\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000020:\n\tdc.b $4E,$71,$4E,$75") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_facts_v2_free_text(source);
  source = NULL;
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object, &policy, &source,
    &profile, &source_analysis, 1U, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "runtime_") == NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000100:\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp loc_0_00000100.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjmp $00000100.l\n") == NULL);
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
  M68K_C_ASSERT(strstr(source, "loc_0_00000020:\n    ORG $100\nloc_0_00000100:\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $20\n") == NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $80\n") == NULL);
  M68K_C_ASSERT(strstr(source, "src_0_") == NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000020 EQU") == NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $100\nloc_0_00000100:\n\tnop\n\trts\n") != NULL);
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
  M68K_C_ASSERT(strstr(source, "loc_0_00000020:\n    ORG $100\nloc_0_00000100:\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $20\n") == NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $80\n") == NULL);
  M68K_C_ASSERT(strstr(source, "src_0_") == NULL);
  M68K_C_ASSERT_U32(1U, profile.asm_source_numeric_runtime_refs);
  m68k_facts_v2_free_text(source);
  m68k_ir_source_analysis_destroy(&source_analysis);
  m68k_object_destroy(&object);
  return 0;
}

static int test_facts_v2_detects_interrupt_vector_store_target(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
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
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000010:\n\tnop\n\trte\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000010:\n\tdc.b $4E,$71,$4E,$73") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
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
    "\tmove.l #loc_0_00000110,m68k_vector_level_2_interrupt_autovector.w\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $100\nloc_0_00000100:\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000110:\n\tnop\n\trte\n") != NULL);
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
  M68K_C_ASSERT(strstr(source, "\tjsr loc_0_00000110.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $100\nloc_0_00000100:\n\tjsr loc_0_00000110.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000110:\n\tnop\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr $00000110.l\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_facts_v2_free_text(source);
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
  M68K_C_ASSERT(strstr(source, "\tjsr loc_0_00000410.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $400\nloc_0_00000400:\n\tjsr loc_0_00000410.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000410:\n\tnop\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr $00000410.l\n") == NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.interior_conflicts_unresolved);
  m68k_facts_v2_free_text(source);
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
  M68K_C_ASSERT(strstr(source, "\tjsr loc_0_00000410.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $400\nloc_0_00000400:\n\tjsr loc_0_00000410.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000410:\n\tnop\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr $00000410.l\n") == NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000010+$") == NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000010+1024") == NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000410 EQU") == NULL);
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
  M68K_C_ASSERT(strstr(source, "\tjsr loc_0_00000410.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tjsr loc_0_00000810.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "    ORG $810\nloc_0_00000810:\n    ORG $410\nloc_0_00000410:\n\tnop\n\trts\n") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000010+$") == NULL);
  M68K_C_ASSERT(strstr(source, "loc_0_00000810 EQU") == NULL);
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
  M68K_C_ASSERT(strstr(source, "loc_0_00000410:\n\tnop\n\trts\n") != NULL);
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
  M68K_C_ASSERT(strstr(source, "DS.B $4") != NULL);
  M68K_C_ASSERT(strstr(source, "loc_1_00000004:") != NULL);
  M68K_C_ASSERT(strstr(source, "DS.B $C") != NULL);
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT_U32(0U, profile.relocation_failures);
  M68K_C_ASSERT_U32(0U, profile.asm_source_instruction_relocation_failures);
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
  _putenv_s("AMIGA_REVERSING_FACTS_V2_ASM_SOURCE", "1");
  M68K_C_ASSERT_INT(0, m68k_facts_v2_collect_profile(&object, &policy, &profile, m68k_diag_sink(NULL)));
  _putenv_s("AMIGA_REVERSING_FACTS_V2_ASM_SOURCE", "");
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
  uint8_t bytes[86] = {
    0x41u, 0xF9u, 0x00u, 0xDFu, 0xF0u, 0x00u,
    0x31u, 0x7Cu, 0x7Fu, 0xFFu, 0x00u, 0x9Au,
    0x31u, 0x7Cu, 0xC0u, 0x00u, 0x00u, 0x9Au,
    0x31u, 0x7Cu, 0x82u, 0x00u, 0x00u, 0x96u,
    0x31u, 0x7Cu, 0x7Fu, 0xFFu, 0x00u, 0x96u,
    0x31u, 0x7Cu, 0x7Fu, 0xFFu, 0x00u, 0x9Eu,
    0x31u, 0x7Cu, 0x00u, 0x40u, 0x00u, 0xA4u,
    0x33u, 0xFCu, 0x12u, 0x34u, 0x00u, 0xDFu, 0xF0u, 0xA4u,
    0x33u, 0xFCu, 0x42u, 0x00u, 0x00u, 0xDFu, 0xF1u, 0x00u,
    0x21u, 0xFCu, 0x12u, 0x34u, 0x56u, 0x78u, 0x00u, 0x6Cu,
    0x33u, 0xC0u, 0x00u, 0xDFu, 0xF1u, 0x9Eu,
    0x31u, 0x40u, 0x00u, 0xE2u,
    0x31u, 0x40u, 0x01u, 0x3Eu,
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
  M68K_C_ASSERT(strstr(source, "\tmove.w #$40,aud0+ac_len(a0)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #$1234,_custom+aud0+ac_len.l\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w #(4<<PLNCNTSHFT)|COLORON,_custom+bplcon0.l\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "\tmove.l #$12345678,m68k_vector_level_3_interrupt_autovector.w\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.w d0,_custom+color+$1E.l\n") != NULL);
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
  const AmigaOsHardwareRegisterInfo *cop1lc =
    amiga_os_find_hardware_register_by_cpu_address(0x00DFF080U);
  const AmigaOsHardwareRegisterInfo *intena =
    amiga_os_find_hardware_register_by_cpu_address(0x00DFF09AU);
  const AmigaOsHardwareRegisterInfo *dskpt =
    amiga_os_find_hardware_register_by_cpu_address(0x00DFF020U);
  const AmigaOsHardwareRegisterFieldInfo *aud0_len =
    amiga_os_find_hardware_register_field_by_cpu_address(0x00DFF0A4U);
  const AmigaOsHardwareRegisterFieldInfo *aud0_len_by_base =
    amiga_os_find_hardware_register_field_by_base_offset("_custom", 0x00A4U);
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
  M68K_C_ASSERT(intena != NULL);
  M68K_C_ASSERT(aud0_len != NULL);
  M68K_C_ASSERT(aud0_len_by_base == aud0_len);
  M68K_C_ASSERT_STR("aud0", aud0_len->register_symbol);
  M68K_C_ASSERT_STR("ac_len", aud0_len->field_symbol);
  M68K_C_ASSERT(bplpt_tail != NULL);
  M68K_C_ASSERT(sprpt_tail != NULL);
  M68K_C_ASSERT_STR("bplpt", bplpt_tail->symbol_name);
  M68K_C_ASSERT_STR("sprpt", sprpt_tail->symbol_name);
  M68K_C_ASSERT(bplpt_past_end == NULL);
  M68K_C_ASSERT(sprpt_past_end == NULL);
  M68K_C_ASSERT(aud0_len_as_range == NULL);
  M68K_C_ASSERT_STR("copper_list", cop1lc->runtime_target_role);
  M68K_C_ASSERT((cop1lc->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) != 0U);
  M68K_C_ASSERT((dskpt->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) != 0U);
  M68K_C_ASSERT((intena->flags & AMIGA_OS_HARDWARE_REGISTER_FLAG_RUNTIME_ADDRESS_SINK) == 0U);
  M68K_C_ASSERT_STR("copper_list",
    platform_facts_v2_runtime_address_sink_data_class(M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x00DFF080U));
  M68K_C_ASSERT(platform_facts_v2_runtime_address_sink_data_class(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
    0x00DFF020U) == NULL);
  M68K_C_ASSERT(platform_facts_v2_is_runtime_address_sink(M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x00DFF080U));
  M68K_C_ASSERT(platform_facts_v2_is_runtime_address_sink(M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x00DFF020U));
  M68K_C_ASSERT(!platform_facts_v2_is_runtime_address_sink(M68K_PLATFORM_BACKEND_AMIGA_HUNK, 0x00DFF09AU));
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
  snprintf(policy.register_seeds[0].name, sizeof(policy.register_seeds[0].name), "exec.library");
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

static int test_facts_v2_render_asm_source_app_slot_overlap_uses_equ_alias(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
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
  M68K_C_ASSERT_INT(0, m68k_facts_v2_render_asm_source_alloc(&object, &policy, &source, &profile,
    m68k_diag_sink(NULL)));
  M68K_C_ASSERT(source != NULL);
  M68K_C_ASSERT(strstr(source, "app_000C RS.L 1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "app_000E EQU $000E\n") != NULL);
  M68K_C_ASSERT(strstr(source, "RS.B 0") == NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.l d0,app_000C(a6)\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tmove.b d1,app_000E(a6)\n") != NULL);
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

static int test_facts_v2_render_asm_source_infers_opendevice_base_field_slot(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[53] = {
    0x41u, 0xf9u, 0x00u, 0x00u, 0x00u, 0x28u,
    0x43u, 0xeeu, 0x00u, 0x40u,
    0x2fu, 0x0eu,
    0x2cu, 0x78u, 0x00u, 0x04u,
    0x4eu, 0xaeu, 0xfeu, 0x44u,
    0x2cu, 0x5fu,
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
  M68K_C_ASSERT(strstr(source, "app_timer_device_iorequest RS.L 1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "app_TimerBase RS.L 1\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tlea.l app_timer_device_iorequest(a6),a1\n") != NULL);
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
  M68K_C_ASSERT_U32(0U, profile.asm_source_refused);
  M68K_C_ASSERT(profile.accepted_instructions >= 4U);
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

static int test_facts_v2_render_asm_source_renders_copper_list_structured_data(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[28] = {
    0x01u, 0x00u, 0x42u, 0x00u,
    0x00u, 0xE0u, 0x12u, 0x34u,
    0x00u, 0xE2u, 0x56u, 0x78u,
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
  policy.named_labels[1].offset = 4U;
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
  M68K_C_ASSERT(strstr(source, "\tdc.w bplcon0,(4<<PLNCNTSHFT)|COLORON\n") != NULL);
  M68K_C_ASSERT(strstr(source, "copper_patch:\n\tdc.w bplpt,$1234\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w bplpt,$1234\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w bplpt+$02,$5678\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w sprpt+$1E,$0000\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w intreq,INTF_SETCLR|INTF_COPER\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tdc.w COPPER_WAIT|$2C06,$FFFE\n") != NULL);
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
  M68K_C_ASSERT(strstr(source, "\tmove.l #loc_0_0000000C,_custom+cop1lc.l\n") != NULL);
  M68K_C_ASSERT(strstr(source,
    "loc_0_0000000C:\n\tdc.w bplcon0,(4<<PLNCNTSHFT)|COLORON\n\tdc.w bplpt,$1234\n"
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

static int test_facts_v2_render_asm_source_scopes_nondefault_fpu_id(void) {
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult added;
  M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;
  char *source = NULL;
  uint8_t bytes[6] = {0x19u, 0x21u, 0xFBu, 0x54u, 0x4Eu, 0x75u};
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
  M68K_C_ASSERT(strstr(source, "\tFPU     5\n") != NULL || strstr(source, "    FPU     5\n") != NULL);
  M68K_C_ASSERT(strstr(source, "\tfrestore (a4)") != NULL || strstr(source, "    frestore (a4)") != NULL);
  M68K_C_ASSERT(strstr(source, "\tFPU     1\n") != NULL || strstr(source, "    FPU     1\n") != NULL);
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
    {"parse_syntax_mode_name", test_parse_syntax_mode_name},
    {"generated_cpu_vector_metadata_marks_interrupt_autovectors",
      test_generated_cpu_vector_metadata_marks_interrupt_autovectors},
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
    {"source_model_symbol_index_preserves_lookup_semantics",
      test_source_model_symbol_index_preserves_lookup_semantics},
    {"section_many_interleaved_labels_and_data", test_section_many_interleaved_labels_and_data},
    {"section_many_interleaved_labels_and_expr_data", test_section_many_interleaved_labels_and_expr_data},
    {"arena_mark_rewind_reuses_same_block_range", test_arena_mark_rewind_reuses_same_block_range},
    {"arena_rewind_discards_later_blocks", test_arena_rewind_discards_later_blocks},
    {"arena_reset_poisons_head_block_range", test_arena_reset_poisons_head_block_range},
    {"decode_ir_decodes_aligned_candidates", test_decode_ir_decodes_aligned_candidates},
    {"decode_ir_treats_cpu_policy_as_ceiling", test_decode_ir_treats_cpu_policy_as_ceiling},
    {"source_parse_treats_cpu_policy_as_ceiling", test_source_parse_treats_cpu_policy_as_ceiling},
    {"source_org_sets_logical_pc_without_padding", test_source_org_sets_logical_pc_without_padding},
    {"decode_ir_negative_cache_preserves_higher_cpu_decode",
      test_decode_ir_negative_cache_preserves_higher_cpu_decode},
    {"decode_ir_records_branch_target_candidate", test_decode_ir_records_branch_target_candidate},
    {"decode_ir_branch_word_target_uses_opcode_pc", test_decode_ir_branch_word_target_uses_opcode_pc},
    {"decode_ir_records_pc_relative_data_target_candidate",
      test_decode_ir_records_pc_relative_data_target_candidate},
    {"decode_ir_keeps_odd_branch_target_for_analysis", test_decode_ir_keeps_odd_branch_target_for_analysis},
    {"fact_ir_label_creation_dedupes", test_fact_ir_label_creation_dedupes},
    {"facts_v2_profile_collects_decode_and_label_facts", test_facts_v2_profile_collects_decode_and_label_facts},
    {"facts_v2_work_queue_dedupes_same_confidence_starts",
      test_facts_v2_work_queue_dedupes_same_confidence_starts},
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
    {"facts_v2_prefers_lower_cpu_fallthrough_over_inferred_interior_target",
      test_facts_v2_prefers_lower_cpu_fallthrough_over_inferred_interior_target},
    {"facts_v2_detects_runtime_copy_jump_target", test_facts_v2_detects_runtime_copy_jump_target},
    {"facts_v2_adjacent_runtime_ranges_do_not_org_back_to_storage",
      test_facts_v2_adjacent_runtime_ranges_do_not_org_back_to_storage},
    {"facts_v2_detects_interrupt_vector_store_target",
      test_facts_v2_detects_interrupt_vector_store_target},
    {"facts_v2_detects_interrupt_vector_fill_target",
      test_facts_v2_detects_interrupt_vector_fill_target},
    {"facts_v2_maps_copied_runtime_vector_target_to_source_offset",
      test_facts_v2_maps_copied_runtime_vector_target_to_source_offset},
    {"facts_v2_maps_copied_runtime_absolute_call_to_source_offset",
      test_facts_v2_maps_copied_runtime_absolute_call_to_source_offset},
    {"facts_v2_policy_runtime_entrypoint_maps_absolute_load",
      test_facts_v2_policy_runtime_entrypoint_maps_absolute_load},
    {"facts_v2_runtime_ref_inside_accepted_instruction_stays_numeric",
      test_facts_v2_runtime_ref_inside_accepted_instruction_stays_numeric},
    {"facts_v2_policy_runtime_range_uses_first_class_labels",
      test_facts_v2_policy_runtime_range_uses_first_class_labels},
    {"facts_v2_runtime_alias_refs_emit_first_class_labels",
      test_facts_v2_runtime_alias_refs_emit_first_class_labels},
    {"facts_v2_policy_runtime_entrypoint_starts_inside_view",
      test_facts_v2_policy_runtime_entrypoint_starts_inside_view},
    {"facts_v2_runtime_range_conflict_fails_instead_of_last_map",
      test_facts_v2_runtime_range_conflict_fails_instead_of_last_map},
    {"facts_v2_render_asm_source_preserves_exact_byte_immediate_word",
      test_facts_v2_render_asm_source_preserves_exact_byte_immediate_word},
    {"facts_v2_render_asm_source_preserves_move_byte_immediate_high_word",
      test_facts_v2_render_asm_source_preserves_move_byte_immediate_high_word},
    {"facts_v2_render_asm_source_refuses_unmapped_code_relocation",
      test_facts_v2_render_asm_source_refuses_unmapped_code_relocation},
    {"facts_v2_render_asm_source_maps_immediate_code_relocation",
      test_facts_v2_render_asm_source_maps_immediate_code_relocation},
    {"facts_v2_render_asm_source_maps_relocation_after_imm_operand",
      test_facts_v2_render_asm_source_maps_relocation_after_imm_operand},
    {"facts_v2_render_asm_source_maps_bss_relocation_label",
      test_facts_v2_render_asm_source_maps_bss_relocation_label},
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
    {"amiga_runtime_address_sinks_are_generated_from_hardware_metadata",
      test_amiga_runtime_address_sinks_are_generated_from_hardware_metadata},
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
    {"facts_v2_render_asm_source_uses_object_symbol_label",
      test_facts_v2_render_asm_source_uses_object_symbol_label},
    {"facts_v2_render_asm_source_infers_lvo_from_object_base_symbol",
      test_facts_v2_render_asm_source_infers_lvo_from_object_base_symbol},
    {"facts_v2_render_asm_source_infers_global_base_slot_from_lvo_set",
      test_facts_v2_render_asm_source_infers_global_base_slot_from_lvo_set},
    {"facts_v2_render_asm_source_app_slot_overlap_uses_equ_alias",
      test_facts_v2_render_asm_source_app_slot_overlap_uses_equ_alias},
    {"facts_v2_render_asm_source_infers_lvo_from_base_field_slot",
      test_facts_v2_render_asm_source_infers_lvo_from_base_field_slot},
    {"facts_v2_render_asm_source_infers_openlibrary_base_field_slot",
      test_facts_v2_render_asm_source_infers_openlibrary_base_field_slot},
    {"facts_v2_render_asm_source_infers_opendevice_base_field_slot",
      test_facts_v2_render_asm_source_infers_opendevice_base_field_slot},
    {"facts_v2_render_asm_source_infers_lvo_immediate_for_indexed_wrapper",
      test_facts_v2_render_asm_source_infers_lvo_immediate_for_indexed_wrapper},
    {"facts_v2_render_asm_source_ignores_ambiguous_wrapper_stack_arg",
      test_facts_v2_render_asm_source_ignores_ambiguous_wrapper_stack_arg},
    {"facts_v2_render_asm_source_tracks_cross_section_local_wrapper_without_inline_comment",
      test_facts_v2_render_asm_source_tracks_cross_section_local_wrapper_without_inline_comment},
    {"facts_v2_render_asm_source_tracks_non_wrapper_local_helper_without_inline_comment",
      test_facts_v2_render_asm_source_tracks_non_wrapper_local_helper_without_inline_comment},
    {"facts_v2_render_asm_source_annotates_wrapper_stack_args_without_wrapper_comment",
      test_facts_v2_render_asm_source_annotates_wrapper_stack_args_without_wrapper_comment},
    {"facts_v2_relocated_absolute_jsr_seeds_cross_section_code_target",
      test_facts_v2_relocated_absolute_jsr_seeds_cross_section_code_target},
    {"facts_v2_render_asm_source_renders_structured_data_comment",
      test_facts_v2_render_asm_source_renders_structured_data_comment},
    {"facts_v2_render_asm_source_renders_copper_list_structured_data",
      test_facts_v2_render_asm_source_renders_copper_list_structured_data},
    {"facts_v2_runtime_copper_pointer_auto_classifies_copper_list",
      test_facts_v2_runtime_copper_pointer_auto_classifies_copper_list},
    {"facts_v2_render_asm_source_marks_structured_data_code_overlap",
      test_facts_v2_render_asm_source_marks_structured_data_code_overlap},
    {"facts_v2_render_asm_source_renders_call_input_domain_immediate",
      test_facts_v2_render_asm_source_renders_call_input_domain_immediate},
    {"facts_v2_inline_return_string_call_skips_payload",
      test_facts_v2_inline_return_string_call_skips_payload},
    {"facts_v2_render_asm_source_scopes_nondefault_fpu_id",
      test_facts_v2_render_asm_source_scopes_nondefault_fpu_id},
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

