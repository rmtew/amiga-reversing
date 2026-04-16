/* Internal object conversion implementation for platform_file_lib. */
#include "platform_file_internal.h"

#include <time.h>

static uint32_t count_set_bytes(const uint8_t *values, size_t count) {
  size_t index;
  uint32_t total = 0;
  if (values == NULL) return 0;
  for (index = 0; index < count; ++index) {
    if (values[index] != 0) ++total;
  }
  return total;
}

static uint32_t count_unique_platform_base_slot_effects(const M68kSectionAnalysisIR *section_analysis) {
  uint32_t total = 0;
  size_t index;
  if (section_analysis == NULL) return 0;
  for (index = 0; index < section_analysis->recovered_platform_effect_count; ++index) {
    const M68kRecoveredPlatformEffectIR *effect = &section_analysis->recovered_platform_effects[index];
    size_t prev_index;
    int seen = 0;
    if (effect->kind != M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT) continue;
    for (prev_index = 0; prev_index < index; ++prev_index) {
      const M68kRecoveredPlatformEffectIR *prev = &section_analysis->recovered_platform_effects[prev_index];
      if (prev->kind != M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT) continue;
      if (prev->displacement == effect->displacement) {
        seen = 1;
        break;
      }
    }
    if (!seen) ++total;
  }
  return total;
}

static int append_run_metrics_section(PlatformFileRunMetrics *metrics, const M68kSectionAnalysisIR *section_analysis,
    const M68kAnalysisFindings *section_findings) {
  PlatformFileRunSectionMetrics *section_metrics;
  if (metrics == NULL || section_analysis == NULL) return 0;
  if (metrics->section_count == metrics->section_capacity) {
    size_t new_capacity = metrics->section_capacity == 0U ? 4U : metrics->section_capacity * 2U;
    PlatformFileRunSectionMetrics *new_sections = (PlatformFileRunSectionMetrics *)realloc(metrics->sections,
      new_capacity * sizeof(*new_sections));
    if (new_sections == NULL) return -1;
    metrics->sections = new_sections;
    metrics->section_capacity = new_capacity;
  }
  section_metrics = &metrics->sections[metrics->section_count++];
  memset(section_metrics, 0, sizeof(*section_metrics));
  if (section_analysis->section_name != NULL) {
    strncpy_s(section_metrics->name, sizeof(section_metrics->name), section_analysis->section_name, _TRUNCATE);
  }
  section_metrics->kind = (uint8_t)section_analysis->section_kind;
  section_metrics->size = section_analysis->section_size;
  section_metrics->certain_code_bytes = count_set_bytes(section_analysis->certain_code_byte,
    section_analysis->certain_code_size);
  section_metrics->label_count = (uint32_t)section_analysis->label_count;
  section_metrics->block_count = (uint32_t)section_analysis->block_count;
  section_metrics->edge_count = (uint32_t)section_analysis->edge_count;
  section_metrics->violation_count = (uint32_t)section_analysis->violation_count;

  metrics->section_bytes += section_analysis->section_size;
  metrics->certain_code_bytes += section_metrics->certain_code_bytes;
  metrics->label_count += section_metrics->label_count;
  metrics->block_count += section_metrics->block_count;
  metrics->edge_count += section_metrics->edge_count;
  metrics->violation_count += section_metrics->violation_count;
  metrics->recovered_word_dispatch_count += (uint32_t)section_analysis->recovered_word_dispatch_count;
  metrics->recovered_inline_dispatch_count += (uint32_t)section_analysis->recovered_inline_dispatch_count;
  metrics->recovered_string_dispatch_count += (uint32_t)section_analysis->recovered_string_dispatch_count;
  metrics->recovered_platform_base_slot_count += count_unique_platform_base_slot_effects(section_analysis);
  metrics->recovered_platform_effect_count += (uint32_t)section_analysis->recovered_platform_effect_count;
  metrics->recovered_platform_call_count += (uint32_t)section_analysis->recovered_platform_call_count;
  metrics->generated_label_count += count_set_bytes(section_analysis->generated_label_flags,
    section_analysis->generated_label_size);
  if (section_findings != NULL) {
    if (section_findings->required_cpu > metrics->findings.required_cpu)
      metrics->findings.required_cpu = section_findings->required_cpu;
    metrics->findings.cpu_violation_count += section_findings->cpu_violation_count;
  }
  switch (section_analysis->section_kind) {
    case M68K_SECTION_CODE:
      metrics->code_section_bytes += section_analysis->section_size;
      break;
    case M68K_SECTION_DATA:
      metrics->data_section_bytes += section_analysis->section_size;
      break;
    case M68K_SECTION_BSS:
      metrics->bss_section_bytes += section_analysis->section_size;
      break;
    default:
      break;
  }
  return 0;
}

static void collect_section_render_metrics(PlatformFileRunMetrics *metrics, size_t section_index,
    const M68kSectionIR *section_ir) {
  size_t statement_index;
  PlatformFileRunSectionMetrics *section_metrics;
  if (metrics == NULL || section_ir == NULL || section_index >= metrics->section_count) return;
  section_metrics = &metrics->sections[section_index];
  metrics->statement_count += (uint32_t)section_ir->statement_count;
  for (statement_index = 0; statement_index < section_ir->statement_count; ++statement_index) {
    const M68kStatementIR *statement = &section_ir->statements[statement_index];
    size_t operand_index;
    switch (statement->kind) {
      case M68K_STATEMENT_LABEL:
        ++metrics->label_statement_count;
        ++section_metrics->emitted_label_count;
        if (statement->label_is_generated) ++metrics->generated_label_statement_count;
        break;
      case M68K_STATEMENT_INSTRUCTION:
        ++metrics->instruction_statement_count;
        ++section_metrics->emitted_instruction_count;
        metrics->instruction_bytes += (uint32_t)statement->u.instruction.byte_count;
        for (operand_index = 0; operand_index < statement->u.instruction.operand_count; ++operand_index) {
          const M68kSymbolRefIR *symbol_ref = &statement->u.instruction.operands[operand_index].symbol_ref;
          if (!symbol_ref->has_name) continue;
          ++metrics->symbol_ref_count;
          switch (symbol_ref->kind) {
            case M68K_IR_SYMBOL_REF_ABS:
              ++metrics->symbol_ref_abs_count;
              break;
            case M68K_IR_SYMBOL_REF_PC_REL:
              ++metrics->symbol_ref_pc_relative_count;
              break;
            case M68K_IR_SYMBOL_REF_SECTION_REL:
              ++metrics->symbol_ref_section_relative_count;
              break;
            default:
              break;
          }
        }
        break;
      case M68K_STATEMENT_DATA:
        ++metrics->data_statement_count;
        ++section_metrics->emitted_data_count;
        metrics->data_bytes += (uint32_t)statement->u.data.size;
        break;
      case M68K_STATEMENT_ALIGN:
        ++metrics->align_statement_count;
        break;
      default:
        break;
    }
    if (statement->comment != NULL &&
        strstr(statement->comment, "vasm-normalized from exact immediate word") != NULL) {
      ++metrics->vasm_normalized_count;
    }
  }
}

int populate_source_ir_from_object(const M68kBackend *backend, const M68kObject *object,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy, M68kSourceFileIR *out_source_file,
    M68kDiagSink diagnostics) {
  return populate_source_ir_from_object_with_metrics(backend, object, policy, analysis_policy, out_source_file, NULL,
    diagnostics);
}

int populate_source_ir_from_object_with_metrics(const M68kBackend *backend, const M68kObject *object,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy, M68kSourceFileIR *out_source_file,
    PlatformFileRunMetrics *out_metrics, M68kDiagSink diagnostics) {
  M68kAnalysisFindings findings;
  Arena *scratch_arena;
  ArenaMark scratch_mark;
  size_t section_index;
  clock_t analysis_ticks = 0;
  clock_t ir_ticks = 0;
  m68k_analysis_findings_init(&findings);
  if (m68k_ir_source_file_create(out_source_file) != 0) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
    return -1;
  }
  if (out_metrics != NULL) out_metrics->file_kind = object->platform_file_kind;
  out_source_file->file_kind = object->platform_file_kind;
  if (strcmp(backend->name, "amiga-hunk") == 0) out_source_file->platform_backend_kind = M68K_PLATFORM_BACKEND_AMIGA_HUNK;
  else if (strcmp(backend->name, "atari-st") == 0) out_source_file->platform_backend_kind = M68K_PLATFORM_BACKEND_ATARI_ST;
  if (strcmp(backend->name, "atari-st") == 0) {
    uint32_t program_flags = 0;
    if (m68k_atari_st_get_program_flags(object, &program_flags) == 0) {
      out_source_file->has_atari_st_program_flags = 1U;
      out_source_file->atari_st_program_flags = program_flags;
    }
  }
  scratch_arena = arena_create(65536U);
  if (scratch_arena == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY,
      "failed creating source scratch arena");
    m68k_ir_source_file_destroy(out_source_file);
    return -1;
  }
  scratch_mark = arena_mark(scratch_arena);
  for (section_index = 0; section_index < object->section_count; ++section_index) {
    M68kSectionIR section_ir;
    M68kSectionAnalysisIR section_analysis;
    M68kAnalysisFindings section_findings;
    clock_t phase_start, phase_end;
    int append_result;
    m68k_analysis_findings_init(&section_findings);
    arena_rewind(scratch_arena, scratch_mark);
    phase_start = clock();
    if (build_section_analysis(object, section_index, &object->sections[section_index], scratch_arena,
          analysis_policy, &findings, &section_analysis, diagnostics) != 0 ||
        (out_metrics != NULL && finalize_section_analysis(&object->sections[section_index], analysis_policy,
          &section_analysis, &section_findings) != 0)) {
      if (!m68k_diag_has_errors(diagnostics.list))
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
          "failed building source ir");
      if (section_analysis.arena != NULL) m68k_ir_section_analysis_destroy(&section_analysis);
      m68k_ir_source_file_destroy(out_source_file);
      arena_destroy(scratch_arena);
      return -1;
    }
    phase_end = clock();
    analysis_ticks += (phase_end - phase_start);
    if (out_metrics != NULL && append_run_metrics_section(out_metrics, &section_analysis, &section_findings) != 0) {
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
      m68k_ir_section_analysis_destroy(&section_analysis);
      m68k_ir_source_file_destroy(out_source_file);
      arena_destroy(scratch_arena);
      return -1;
    }
    phase_start = clock();
    if (build_section_ir(object, &object->sections[section_index], &section_analysis, analysis_policy, &findings,
          policy, &section_ir, diagnostics) != 0) {
      if (!m68k_diag_has_errors(diagnostics.list))
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
          "failed building source ir");
      m68k_ir_section_analysis_destroy(&section_analysis);
      m68k_ir_source_file_destroy(out_source_file);
      arena_destroy(scratch_arena);
      return -1;
    }
    phase_end = clock();
    ir_ticks += (phase_end - phase_start);
    if (out_metrics != NULL) collect_section_render_metrics(out_metrics, section_index, &section_ir);
    phase_start = clock();
    append_result = m68k_ir_source_file_append_section(out_source_file, &section_ir);
    phase_end = clock();
    ir_ticks += (phase_end - phase_start);
    m68k_ir_section_destroy(&section_ir);
    if (append_result != 0) {
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
        "failed building source ir");
      m68k_ir_section_analysis_destroy(&section_analysis);
      m68k_ir_source_file_destroy(out_source_file);
      arena_destroy(scratch_arena);
      return -1;
    }
    m68k_ir_section_analysis_destroy(&section_analysis);
  }
  arena_destroy(scratch_arena);
  if (out_metrics != NULL) {
    out_metrics->analysis_seconds = ((double)analysis_ticks) / (double)CLOCKS_PER_SEC;
    out_metrics->ir_build_seconds = ((double)ir_ticks) / (double)CLOCKS_PER_SEC;
  }
  return 0;
}

int populate_source_analysis_from_object(const M68kObject *object, const M68kAnalysisPolicy *analysis_policy,
    M68kSourceAnalysisIR *out_source_analysis, M68kDiagSink diagnostics) {
  Arena *scratch_arena;
  ArenaMark scratch_mark;
  size_t section_index;
  if (m68k_ir_source_analysis_create(out_source_analysis) != 0) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
    return -1;
  }
  out_source_analysis->policy = *analysis_policy;
  out_source_analysis->file_kind = object->platform_file_kind;
  m68k_analysis_findings_init(&out_source_analysis->findings);
  scratch_arena = arena_create(65536U);
  if (scratch_arena == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY,
      "failed creating analysis scratch arena");
    m68k_ir_source_analysis_destroy(out_source_analysis);
    return -1;
  }
  scratch_mark = arena_mark(scratch_arena);
  for (section_index = 0; section_index < object->section_count; ++section_index) {
    M68kSectionAnalysisIR section_analysis;
    M68kAnalysisFindings scratch_findings;
    M68kAnalysisFindings section_findings;
    m68k_analysis_findings_init(&scratch_findings);
    m68k_analysis_findings_init(&section_findings);
    arena_rewind(scratch_arena, scratch_mark);
    if (build_section_analysis(object, section_index, &object->sections[section_index], scratch_arena, analysis_policy,
          &scratch_findings, &section_analysis, diagnostics) != 0 ||
        finalize_section_analysis(&object->sections[section_index], analysis_policy, &section_analysis,
          &section_findings) != 0 ||
        m68k_ir_source_analysis_append_section(out_source_analysis, &section_analysis) != 0) {
      if (!m68k_diag_has_errors(diagnostics.list))
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
          "failed building cfg analysis");
      m68k_ir_section_analysis_destroy(&section_analysis);
      m68k_ir_source_analysis_destroy(out_source_analysis);
      arena_destroy(scratch_arena);
      return -1;
    }
    if (section_findings.required_cpu > out_source_analysis->findings.required_cpu)
      out_source_analysis->findings.required_cpu = section_findings.required_cpu;
    out_source_analysis->findings.cpu_violation_count += section_findings.cpu_violation_count;
    m68k_ir_section_analysis_destroy(&section_analysis);
  }
  arena_destroy(scratch_arena);
  return 0;
}
