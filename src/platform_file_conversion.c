/* Internal object conversion implementation for platform_file_lib. */
#include "platform_file_internal.h"

#include <string.h>
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

static void destroy_cached_section_analyses(M68kSectionAnalysisIR *section_analyses,
    const uint8_t *section_analysis_built, size_t count) {
  size_t index;
  if (section_analyses == NULL || section_analysis_built == NULL) return;
  for (index = 0U; index < count; ++index) {
    if (section_analysis_built[index]) m68k_ir_section_analysis_destroy(&section_analyses[index]);
  }
}

static int append_run_metrics_section(PlatformFileRunMetrics *metrics, const M68kSectionAnalysisIR *section_analysis,
    const M68kAnalysisFindings *section_findings) {
  PlatformFileRunSectionMetrics *section_metrics;
  size_t violation_index;
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
  for (violation_index = 0U; violation_index < section_analysis->violation_count; ++violation_index) {
    const M68kViolationIR *violation = &section_analysis->violations[violation_index];
    const char *message = violation->message != NULL ? violation->message : "";
    switch (violation->kind) {
    case M68K_VIOLATION_CPU_POLICY:
      ++section_metrics->cpu_policy_violation_count;
      ++metrics->cpu_policy_violation_count;
      break;
    case M68K_VIOLATION_DECODE_FAILED_REACHABLE:
      ++section_metrics->decode_failed_reachable_violation_count;
      ++metrics->decode_failed_reachable_violation_count;
      break;
    case M68K_VIOLATION_INVALID_INTERIOR_REFERENCE:
      ++section_metrics->invalid_interior_reference_violation_count;
      ++metrics->invalid_interior_reference_violation_count;
      if (strstr(message, "pc-relative target") != NULL &&
          strstr(message, "rendered as data-span label") != NULL) {
        ++section_metrics->pc_relative_data_span_anchor_violation_count;
        ++metrics->pc_relative_data_span_anchor_violation_count;
      } else if (strstr(message, "pc-relative target") != NULL &&
          strstr(message, "inside data span") != NULL &&
          strstr(message, "marked as code") != NULL) {
        ++section_metrics->pc_relative_data_code_overlap_violation_count;
        ++metrics->pc_relative_data_code_overlap_violation_count;
      } else if (strstr(message, "absolute in-section address") != NULL &&
          strstr(message, "no relocation") != NULL) {
        ++section_metrics->absolute_in_section_without_relocation_violation_count;
        ++metrics->absolute_in_section_without_relocation_violation_count;
      } else if (strstr(message, "without structured span proof") != NULL) {
        ++section_metrics->unproven_label_addend_violation_count;
        ++metrics->unproven_label_addend_violation_count;
      } else if (strstr(message, "unresolved relocation symbol") != NULL) {
        ++section_metrics->unresolved_relocation_symbol_violation_count;
        ++metrics->unresolved_relocation_symbol_violation_count;
      } else if (strstr(message, "has no stable label") != NULL) {
        ++section_metrics->branch_target_unstable_violation_count;
        ++metrics->branch_target_unstable_violation_count;
      }
      break;
    case M68K_VIOLATION_UNRESOLVED_INDIRECT:
      ++section_metrics->unresolved_indirect_violation_count;
      ++metrics->unresolved_indirect_violation_count;
      break;
    case M68K_VIOLATION_ORPHANED_CODE:
      ++section_metrics->orphaned_code_violation_count;
      ++metrics->orphaned_code_violation_count;
      break;
    default:
      break;
    }
  }

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

static void set_section_analysis_timing(PlatformFileRunMetrics *metrics, size_t section_index,
    double cache_seconds, double finalize_seconds, double rebuild_seconds) {
  PlatformFileRunSectionMetrics *section_metrics;
  if (metrics == NULL || section_index >= metrics->section_count) return;
  section_metrics = &metrics->sections[section_index];
  section_metrics->analysis_cache_seconds = cache_seconds;
  section_metrics->analysis_finalize_seconds = finalize_seconds;
  section_metrics->analysis_rebuild_seconds = rebuild_seconds;
}

static void set_section_ir_timing(PlatformFileRunMetrics *metrics, size_t section_index,
    double build_seconds, double append_seconds) {
  PlatformFileRunSectionMetrics *section_metrics;
  if (metrics == NULL || section_index >= metrics->section_count) return;
  section_metrics = &metrics->sections[section_index];
  section_metrics->ir_build_seconds = build_seconds;
  section_metrics->ir_append_seconds = append_seconds;
}

int populate_source_ir_from_object(const M68kBackend *backend, const M68kObject *object,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy, M68kSourceFileIR *out_source_file,
    M68kDiagSink diagnostics) {
  return populate_source_ir_from_object_with_metrics(backend, object, policy, analysis_policy, out_source_file, NULL,
    NULL, diagnostics);
}

int populate_source_ir_from_object_with_metrics(const M68kBackend *backend, const M68kObject *object,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy, M68kSourceFileIR *out_source_file,
    PlatformFileRunMetrics *out_metrics, M68kSourceAnalysisIR *out_source_analysis, M68kDiagSink diagnostics) {
  M68kAnalysisFindings findings;
  Arena *scratch_arena;
  ArenaMark scratch_mark;
  M68kSectionAnalysisIR *section_analyses = NULL;
  uint8_t *section_analysis_built = NULL;
  double *section_cache_seconds = NULL;
  size_t section_index;
  clock_t analysis_ticks = 0;
  clock_t ir_ticks = 0;
  m68k_analysis_findings_init(&findings);
  if (m68k_ir_source_file_create(out_source_file) != 0) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
    return -1;
  }
  if (out_source_analysis != NULL) {
    if (m68k_ir_source_analysis_create(out_source_analysis) != 0) {
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
      m68k_ir_source_file_destroy(out_source_file);
      return -1;
    }
    out_source_analysis->policy = *analysis_policy;
    out_source_analysis->file_kind = object->platform_file_kind;
    m68k_analysis_findings_init(&out_source_analysis->findings);
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
  section_analyses = (M68kSectionAnalysisIR *)calloc(object->section_count != 0U ? object->section_count : 1U,
    sizeof(*section_analyses));
  section_analysis_built = (uint8_t *)calloc(object->section_count != 0U ? object->section_count : 1U,
    sizeof(*section_analysis_built));
  section_cache_seconds = (double *)calloc(object->section_count != 0U ? object->section_count : 1U,
    sizeof(*section_cache_seconds));
  if (section_analyses == NULL || section_analysis_built == NULL || section_cache_seconds == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY,
      "failed creating section analysis cache");
    free(section_analyses);
    free(section_analysis_built);
    free(section_cache_seconds);
    m68k_ir_source_file_destroy(out_source_file);
    arena_destroy(scratch_arena);
    return -1;
  }
  for (section_index = 0; section_index < object->section_count; ++section_index) {
    M68kSectionAnalysisIR section_analysis;
    M68kAnalysisFindings scratch_findings;
    clock_t phase_start, phase_end;
    m68k_analysis_findings_init(&scratch_findings);
    arena_rewind(scratch_arena, scratch_mark);
    phase_start = clock();
    if (build_section_analysis(object, section_index, &object->sections[section_index], section_analyses,
          section_index, scratch_arena, analysis_policy, &scratch_findings, &section_analysis, diagnostics) != 0) {
      if (!m68k_diag_has_errors(diagnostics.list))
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
          "failed building source ir");
      if (section_analysis.arena != NULL) m68k_ir_section_analysis_destroy(&section_analysis);
      if (out_source_analysis != NULL) m68k_ir_source_analysis_destroy(out_source_analysis);
      m68k_ir_source_file_destroy(out_source_file);
      destroy_cached_section_analyses(section_analyses, section_analysis_built, section_index);
      free(section_analyses);
      free(section_analysis_built);
      free(section_cache_seconds);
      arena_destroy(scratch_arena);
      return -1;
    }
    section_analyses[section_index] = section_analysis;
    section_analysis_built[section_index] = 1U;
    phase_end = clock();
    analysis_ticks += (phase_end - phase_start);
    section_cache_seconds[section_index] = ((double)(phase_end - phase_start)) / (double)CLOCKS_PER_SEC;
  }
  if (analysis_policy != NULL && analysis_policy->skip_platform_facts != 0U) {
    for (section_index = 0; section_index < object->section_count; ++section_index) {
      M68kAnalysisFindings section_findings;
      clock_t phase_start, phase_end;
      double finalize_seconds;
      m68k_analysis_findings_init(&section_findings);
      phase_start = clock();
      if (finalize_section_analysis(&object->sections[section_index], analysis_policy,
          &section_analyses[section_index], &section_findings) != 0) {
        if (!m68k_diag_has_errors(diagnostics.list))
          m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
            "failed building source ir");
        if (out_source_analysis != NULL) m68k_ir_source_analysis_destroy(out_source_analysis);
        m68k_ir_source_file_destroy(out_source_file);
        destroy_cached_section_analyses(section_analyses, section_analysis_built, object->section_count);
        free(section_analyses);
        free(section_analysis_built);
        arena_destroy(scratch_arena);
        return -1;
      }
      phase_end = clock();
      finalize_seconds = ((double)(phase_end - phase_start)) / (double)CLOCKS_PER_SEC;
      if (out_metrics != NULL && append_run_metrics_section(out_metrics, &section_analyses[section_index],
          &section_findings) != 0) {
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
        if (out_source_analysis != NULL) m68k_ir_source_analysis_destroy(out_source_analysis);
        m68k_ir_source_file_destroy(out_source_file);
        destroy_cached_section_analyses(section_analyses, section_analysis_built, object->section_count);
        free(section_analyses);
        free(section_analysis_built);
        arena_destroy(scratch_arena);
        return -1;
      }
      set_section_analysis_timing(out_metrics, section_index, section_cache_seconds[section_index],
        finalize_seconds, 0.0);
      if (out_source_analysis != NULL) {
        if (m68k_ir_source_analysis_append_section(out_source_analysis, &section_analyses[section_index]) != 0) {
          m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
          m68k_ir_source_analysis_destroy(out_source_analysis);
          m68k_ir_source_file_destroy(out_source_file);
          destroy_cached_section_analyses(section_analyses, section_analysis_built, object->section_count);
          free(section_analyses);
          free(section_analysis_built);
          free(section_cache_seconds);
          arena_destroy(scratch_arena);
          return -1;
        }
        if (section_findings.required_cpu > out_source_analysis->findings.required_cpu)
          out_source_analysis->findings.required_cpu = section_findings.required_cpu;
        out_source_analysis->findings.cpu_violation_count += section_findings.cpu_violation_count;
      }
    }
    goto build_ir_sections;
  }
  for (section_index = 0; section_index < object->section_count; ++section_index) {
    M68kSectionAnalysisIR section_analysis;
    M68kAnalysisFindings scratch_findings;
    M68kAnalysisFindings section_findings;
    clock_t phase_start, phase_end;
    double finalize_seconds = 0.0;
    double rebuild_seconds = 0.0;
    size_t prior_section_analysis_count = object->section_count > 1U ? object->section_count : section_index;
    m68k_analysis_findings_init(&scratch_findings);
    m68k_analysis_findings_init(&section_findings);
    if (object->section_count == 1U && section_analysis_built[section_index]) {
      phase_start = clock();
      if (finalize_section_analysis(&object->sections[section_index], analysis_policy,
          &section_analyses[section_index], &section_findings) != 0) {
        if (!m68k_diag_has_errors(diagnostics.list))
          m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
            "failed building source ir");
        if (out_source_analysis != NULL) m68k_ir_source_analysis_destroy(out_source_analysis);
        m68k_ir_source_file_destroy(out_source_file);
        destroy_cached_section_analyses(section_analyses, section_analysis_built, object->section_count);
        free(section_analyses);
        free(section_analysis_built);
        free(section_cache_seconds);
        arena_destroy(scratch_arena);
        return -1;
      }
      phase_end = clock();
      finalize_seconds = ((double)(phase_end - phase_start)) / (double)CLOCKS_PER_SEC;
      if (out_metrics != NULL && append_run_metrics_section(out_metrics, &section_analyses[section_index],
          &section_findings) != 0) {
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
        if (out_source_analysis != NULL) m68k_ir_source_analysis_destroy(out_source_analysis);
        m68k_ir_source_file_destroy(out_source_file);
        destroy_cached_section_analyses(section_analyses, section_analysis_built, object->section_count);
        free(section_analyses);
        free(section_analysis_built);
        free(section_cache_seconds);
        arena_destroy(scratch_arena);
        return -1;
      }
      set_section_analysis_timing(out_metrics, section_index, section_cache_seconds[section_index],
        finalize_seconds, 0.0);
      if (out_source_analysis != NULL) {
        if (m68k_ir_source_analysis_append_section(out_source_analysis, &section_analyses[section_index]) != 0) {
          m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
          m68k_ir_source_analysis_destroy(out_source_analysis);
          m68k_ir_source_file_destroy(out_source_file);
          destroy_cached_section_analyses(section_analyses, section_analysis_built, object->section_count);
          free(section_analyses);
          free(section_analysis_built);
          free(section_cache_seconds);
          arena_destroy(scratch_arena);
          return -1;
        }
        if (section_findings.required_cpu > out_source_analysis->findings.required_cpu)
          out_source_analysis->findings.required_cpu = section_findings.required_cpu;
        out_source_analysis->findings.cpu_violation_count += section_findings.cpu_violation_count;
      }
      continue;
    }
    arena_rewind(scratch_arena, scratch_mark);
    phase_start = clock();
    if (build_section_analysis(object, section_index, &object->sections[section_index], section_analyses,
          prior_section_analysis_count, scratch_arena, analysis_policy, &scratch_findings, &section_analysis,
          diagnostics) != 0) {
      if (!m68k_diag_has_errors(diagnostics.list))
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
          "failed building source ir");
      if (section_analysis.arena != NULL) m68k_ir_section_analysis_destroy(&section_analysis);
      if (out_source_analysis != NULL) m68k_ir_source_analysis_destroy(out_source_analysis);
      m68k_ir_source_file_destroy(out_source_file);
      destroy_cached_section_analyses(section_analyses, section_analysis_built, object->section_count);
      free(section_analyses);
      free(section_analysis_built);
      free(section_cache_seconds);
      arena_destroy(scratch_arena);
      return -1;
    }
    phase_end = clock();
    rebuild_seconds = ((double)(phase_end - phase_start)) / (double)CLOCKS_PER_SEC;
    analysis_ticks += (phase_end - phase_start);
    phase_start = clock();
    if (finalize_section_analysis(&object->sections[section_index], analysis_policy, &section_analysis,
        &section_findings) != 0) {
      if (!m68k_diag_has_errors(diagnostics.list))
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
          "failed building source ir");
      if (section_analysis.arena != NULL) m68k_ir_section_analysis_destroy(&section_analysis);
      if (out_source_analysis != NULL) m68k_ir_source_analysis_destroy(out_source_analysis);
      m68k_ir_source_file_destroy(out_source_file);
      destroy_cached_section_analyses(section_analyses, section_analysis_built, object->section_count);
      free(section_analyses);
      free(section_analysis_built);
      free(section_cache_seconds);
      arena_destroy(scratch_arena);
      return -1;
    }
    phase_end = clock();
    finalize_seconds = ((double)(phase_end - phase_start)) / (double)CLOCKS_PER_SEC;
    analysis_ticks += (phase_end - phase_start);
    if (out_metrics != NULL && append_run_metrics_section(out_metrics, &section_analysis, &section_findings) != 0) {
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
      if (section_analysis.arena != NULL) m68k_ir_section_analysis_destroy(&section_analysis);
      if (out_source_analysis != NULL) m68k_ir_source_analysis_destroy(out_source_analysis);
      m68k_ir_source_file_destroy(out_source_file);
      destroy_cached_section_analyses(section_analyses, section_analysis_built, object->section_count);
      free(section_analyses);
      free(section_analysis_built);
      free(section_cache_seconds);
      arena_destroy(scratch_arena);
      return -1;
    }
    set_section_analysis_timing(out_metrics, section_index, section_cache_seconds[section_index],
      finalize_seconds, rebuild_seconds);
    if (out_source_analysis != NULL) {
      if (m68k_ir_source_analysis_append_section(out_source_analysis, &section_analysis) != 0) {
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY, "out of memory");
        if (section_analysis.arena != NULL) m68k_ir_section_analysis_destroy(&section_analysis);
        m68k_ir_source_analysis_destroy(out_source_analysis);
        m68k_ir_source_file_destroy(out_source_file);
        destroy_cached_section_analyses(section_analyses, section_analysis_built, object->section_count);
        free(section_analyses);
        free(section_analysis_built);
        free(section_cache_seconds);
        arena_destroy(scratch_arena);
        return -1;
      }
      if (section_findings.required_cpu > out_source_analysis->findings.required_cpu)
        out_source_analysis->findings.required_cpu = section_findings.required_cpu;
      out_source_analysis->findings.cpu_violation_count += section_findings.cpu_violation_count;
    }
    m68k_ir_section_analysis_destroy(&section_analyses[section_index]);
    section_analyses[section_index] = section_analysis;
    section_analysis_built[section_index] = 1U;
  }
build_ir_sections:
  for (section_index = 0; section_index < object->section_count; ++section_index) {
    M68kSectionIR section_ir;
    clock_t phase_start, phase_end;
    double ir_build_seconds, ir_append_seconds;
    int append_result;
    phase_start = clock();
    if (build_section_ir(object, &object->sections[section_index], section_analyses, object->section_count,
          &section_analyses[section_index],
          analysis_policy, &findings, policy, &section_ir,
          out_metrics != NULL && section_index < out_metrics->section_count ? &out_metrics->sections[section_index] : NULL,
          diagnostics) != 0) {
      if (!m68k_diag_has_errors(diagnostics.list))
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
          "failed building source ir");
      if (out_source_analysis != NULL) m68k_ir_source_analysis_destroy(out_source_analysis);
      m68k_ir_source_file_destroy(out_source_file);
      destroy_cached_section_analyses(section_analyses, section_analysis_built, object->section_count);
      free(section_analyses);
      free(section_analysis_built);
      free(section_cache_seconds);
      arena_destroy(scratch_arena);
      return -1;
    }
    phase_end = clock();
    ir_ticks += (phase_end - phase_start);
    ir_build_seconds = ((double)(phase_end - phase_start)) / (double)CLOCKS_PER_SEC;
    if (out_metrics != NULL) collect_section_render_metrics(out_metrics, section_index, &section_ir);
    phase_start = clock();
    append_result = m68k_ir_source_file_append_section(out_source_file, &section_ir);
    phase_end = clock();
    ir_ticks += (phase_end - phase_start);
    ir_append_seconds = ((double)(phase_end - phase_start)) / (double)CLOCKS_PER_SEC;
    set_section_ir_timing(out_metrics, section_index, ir_build_seconds, ir_append_seconds);
    m68k_ir_section_destroy(&section_ir);
    if (append_result != 0) {
      m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
        "failed building source ir");
      if (out_source_analysis != NULL) m68k_ir_source_analysis_destroy(out_source_analysis);
      m68k_ir_source_file_destroy(out_source_file);
      destroy_cached_section_analyses(section_analyses, section_analysis_built, object->section_count);
      free(section_analyses);
      free(section_analysis_built);
      free(section_cache_seconds);
      arena_destroy(scratch_arena);
      return -1;
    }
  }
  destroy_cached_section_analyses(section_analyses, section_analysis_built, object->section_count);
  free(section_analyses);
  free(section_analysis_built);
  free(section_cache_seconds);
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
  M68kSectionAnalysisIR *section_analyses = NULL;
  uint8_t *section_analysis_built = NULL;
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
  section_analyses = (M68kSectionAnalysisIR *)calloc(object->section_count != 0U ? object->section_count : 1U,
    sizeof(*section_analyses));
  section_analysis_built = (uint8_t *)calloc(object->section_count != 0U ? object->section_count : 1U,
    sizeof(*section_analysis_built));
  if (section_analyses == NULL || section_analysis_built == NULL) {
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_OUT_OF_MEMORY,
      "failed creating section analysis cache");
    free(section_analyses);
    free(section_analysis_built);
    m68k_ir_source_analysis_destroy(out_source_analysis);
    arena_destroy(scratch_arena);
    return -1;
  }
  for (section_index = 0; section_index < object->section_count; ++section_index) {
    M68kSectionAnalysisIR section_analysis;
    M68kAnalysisFindings scratch_findings;
    m68k_analysis_findings_init(&scratch_findings);
    arena_rewind(scratch_arena, scratch_mark);
    if (build_section_analysis(object, section_index, &object->sections[section_index], section_analyses,
          section_index, scratch_arena, analysis_policy, &scratch_findings, &section_analysis, diagnostics) != 0) {
      if (!m68k_diag_has_errors(diagnostics.list))
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
          "failed building cfg analysis");
      if (section_analysis.arena != NULL) m68k_ir_section_analysis_destroy(&section_analysis);
      m68k_ir_source_analysis_destroy(out_source_analysis);
      destroy_cached_section_analyses(section_analyses, section_analysis_built, section_index);
      free(section_analyses);
      free(section_analysis_built);
      arena_destroy(scratch_arena);
      return -1;
    }
    section_analyses[section_index] = section_analysis;
    section_analysis_built[section_index] = 1U;
  }
  for (section_index = 0; section_index < object->section_count; ++section_index) {
    M68kSectionAnalysisIR section_analysis;
    M68kAnalysisFindings scratch_findings;
    M68kAnalysisFindings section_findings;
    size_t prior_section_analysis_count = object->section_count > 1U ? object->section_count : section_index;
    m68k_analysis_findings_init(&scratch_findings);
    m68k_analysis_findings_init(&section_findings);
    if (object->section_count == 1U && section_analysis_built[section_index]) {
      if (finalize_section_analysis(&object->sections[section_index], analysis_policy,
          &section_analyses[section_index], &section_findings) != 0 ||
          m68k_ir_source_analysis_append_section(out_source_analysis, &section_analyses[section_index]) != 0) {
        if (!m68k_diag_has_errors(diagnostics.list))
          m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
            "failed building cfg analysis");
        m68k_ir_source_analysis_destroy(out_source_analysis);
        destroy_cached_section_analyses(section_analyses, section_analysis_built, object->section_count);
        free(section_analyses);
        free(section_analysis_built);
        arena_destroy(scratch_arena);
        return -1;
      }
      if (section_findings.required_cpu > out_source_analysis->findings.required_cpu)
        out_source_analysis->findings.required_cpu = section_findings.required_cpu;
      out_source_analysis->findings.cpu_violation_count += section_findings.cpu_violation_count;
      continue;
    }
    arena_rewind(scratch_arena, scratch_mark);
    if (build_section_analysis(object, section_index, &object->sections[section_index], section_analyses,
          prior_section_analysis_count, scratch_arena, analysis_policy, &scratch_findings, &section_analysis,
          diagnostics) != 0 ||
        finalize_section_analysis(&object->sections[section_index], analysis_policy, &section_analysis,
          &section_findings) != 0 ||
        m68k_ir_source_analysis_append_section(out_source_analysis, &section_analysis) != 0) {
      if (!m68k_diag_has_errors(diagnostics.list))
        m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_FILE_FAILED,
          "failed building cfg analysis");
      if (section_analysis.arena != NULL) m68k_ir_section_analysis_destroy(&section_analysis);
      m68k_ir_source_analysis_destroy(out_source_analysis);
      destroy_cached_section_analyses(section_analyses, section_analysis_built, object->section_count);
      free(section_analyses);
      free(section_analysis_built);
      arena_destroy(scratch_arena);
      return -1;
    }
    if (section_findings.required_cpu > out_source_analysis->findings.required_cpu)
      out_source_analysis->findings.required_cpu = section_findings.required_cpu;
    out_source_analysis->findings.cpu_violation_count += section_findings.cpu_violation_count;
    m68k_ir_section_analysis_destroy(&section_analyses[section_index]);
    section_analyses[section_index] = section_analysis;
    section_analysis_built[section_index] = 1U;
  }
  destroy_cached_section_analyses(section_analyses, section_analysis_built, object->section_count);
  free(section_analyses);
  free(section_analysis_built);
  arena_destroy(scratch_arena);
  return 0;
}
