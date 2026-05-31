#include "m68k_source_quality.h"

#include "m68k_fact_ir.h"

#include <string.h>

static uint8_t code_origin_class_from_reason(uint32_t reason) {
  switch (reason) {
    case M68K_FACT_CODE_START_REASON_SECTION_ENTRY:
    case M68K_FACT_CODE_START_REASON_POLICY_ENTRY_OFFSET:
    case M68K_FACT_CODE_START_REASON_POLICY_ENTRY_POINT:
      return M68K_CODE_ORIGIN_STRONG_ENTRY;
    case M68K_FACT_CODE_START_REASON_LINKAGE_API_ENTRY:
    case M68K_FACT_CODE_START_REASON_PLATFORM_LOADSEG_ENTRY:
    case M68K_FACT_CODE_START_REASON_BOUNDARY_API_ENTRY:
      return M68K_CODE_ORIGIN_PLATFORM_SEMANTIC_ENTRY;
    case M68K_FACT_CODE_START_REASON_RUNTIME_VIEW_ENTRY:
      return M68K_CODE_ORIGIN_CONDITIONAL_RUNTIME_ALIAS;
    case M68K_FACT_CODE_START_REASON_FALLTHROUGH:
      return M68K_CODE_ORIGIN_PROVEN_FALLTHROUGH;
    case M68K_FACT_CODE_START_REASON_CONTROL_TARGET:
    case M68K_FACT_CODE_START_REASON_INLINE_RESUME:
    case M68K_FACT_CODE_START_REASON_STACK_CONTINUATION:
      return M68K_CODE_ORIGIN_PROVEN_CONTROL_TARGET;
    default:
      return M68K_CODE_ORIGIN_UNKNOWN;
  }
}

static int code_origin_class_is_executable_proof(uint8_t origin_class) {
  return origin_class == M68K_CODE_ORIGIN_STRONG_ENTRY ||
    origin_class == M68K_CODE_ORIGIN_PROVEN_CONTROL_TARGET ||
    origin_class == M68K_CODE_ORIGIN_PLATFORM_SEMANTIC_ENTRY ||
    origin_class == M68K_CODE_ORIGIN_MANUAL_SEED ||
    origin_class == M68K_CODE_ORIGIN_CONDITIONAL_TABLE_TARGET ||
    origin_class == M68K_CODE_ORIGIN_CONDITIONAL_RUNTIME_ALIAS;
}

static int append_code_origins_for_section(M68kSectionAnalysisIR *section) {
  size_t index;
  if (section == NULL) return -1;
  for (index = 0U; index < section->code_start_ref_count; ++index) {
    const M68kCodeStartRefIR *ref = &section->code_start_refs[index];
    M68kCodeOriginIR origin;
    memset(&origin, 0, sizeof(origin));
    origin.offset = ref->offset;
    origin.length = ref->size;
    origin.source_section_index = (uint32_t)ref->source_section_index;
    origin.source_offset = ref->source_offset;
    origin.runtime_address = ref->runtime_address;
    origin.reason = ref->reason;
    origin.evidence_kind = ref->reason;
    origin.origin_class = code_origin_class_from_reason(ref->reason);
    origin.confidence = ref->confidence;
    origin.has_runtime_address = ref->has_runtime_address;
    if (m68k_ir_section_analysis_append_code_origin(section, &origin) != 0) return -1;
  }
  return 0;
}

static int accepted_run_has_origin(const M68kSectionAnalysisIR *section, uint32_t start, uint32_t end) {
  size_t index;
  if (section == NULL) return 0;
  for (index = 0U; index < section->code_start_ref_count; ++index) {
    uint32_t offset = section->code_start_refs[index].offset;
    if (offset >= start && offset < end) return 1;
  }
  return 0;
}

static int accepted_run_has_executable_origin(const M68kSectionAnalysisIR *section, uint32_t start, uint32_t end) {
  size_t index;
  if (section == NULL) return 0;
  for (index = 0U; index < section->code_start_ref_count; ++index) {
    const M68kCodeStartRefIR *ref = &section->code_start_refs[index];
    if (ref->offset >= start && ref->offset < end &&
        code_origin_class_is_executable_proof(code_origin_class_from_reason(ref->reason))) {
      return 1;
    }
  }
  return 0;
}

static int classify_run_end_from_cfg(const M68kSectionAnalysisIR *section, uint32_t start, uint32_t end,
    M68kAcceptedCodeRunIR *run) {
  size_t block_index;
  if (section == NULL || run == NULL) return 0;
  for (block_index = 0U; block_index < section->block_count; ++block_index) {
    const M68kCfgBlockIR *block = &section->blocks[block_index];
    size_t edge_index;
    if (block->start_offset < start || block->end_offset != end) continue;
    for (edge_index = 0U; edge_index < block->edge_count; ++edge_index) {
      const M68kCfgEdgeIR *edge;
      size_t absolute_edge_index = block->edge_start + edge_index;
      if (absolute_edge_index >= section->edge_count) return -1;
      edge = &section->edges[absolute_edge_index];
      if (edge->kind == M68K_CFG_EDGE_RETURN) {
        run->end_kind = M68K_ACCEPTED_CODE_RUN_END_TERMINAL;
        run->terminal_offset = edge->source_offset;
        run->has_terminal_offset = 1U;
        return 1;
      }
      if (edge->kind == M68K_CFG_EDGE_JUMP) {
        run->end_kind = M68K_ACCEPTED_CODE_RUN_END_PROVEN_TRANSFER;
        run->terminal_offset = edge->source_offset;
        run->has_terminal_offset = 1U;
        return 1;
      }
    }
  }
  return 0;
}

static int append_run_diagnostic(M68kSectionAnalysisIR *section, const M68kAcceptedCodeRunIR *run, uint8_t kind,
    uint8_t severity, uint8_t blocker, const char *summary) {
  M68kSourceQualityDiagnosticIR diagnostic;
  if (section == NULL || run == NULL) return -1;
  memset(&diagnostic, 0, sizeof(diagnostic));
  diagnostic.kind = kind;
  diagnostic.severity = severity;
  diagnostic.blocker = blocker;
  diagnostic.origin = M68K_SOURCE_QUALITY_DIAGNOSTIC_ORIGIN_AUTO_ANALYSIS;
  diagnostic.has_section_index = 1U;
  diagnostic.section_index = (uint32_t)section->section_index;
  diagnostic.has_offset = 1U;
  diagnostic.offset = run->start_offset;
  diagnostic.has_related_range = 1U;
  diagnostic.related_start = run->start_offset;
  diagnostic.related_end = run->end_offset;
  diagnostic.summary = (char *)summary;
  diagnostic.evidence_source = "accepted_code_run";
  return m68k_ir_section_analysis_append_source_quality_diagnostic(section, &diagnostic);
}

static int append_accepted_runs_for_section(M68kSectionAnalysisIR *section) {
  uint32_t cursor;
  if (section == NULL || section->certain_code_byte == NULL || section->certain_code_size == 0U) return 0;
  cursor = 0U;
  while ((size_t)cursor < section->certain_code_size) {
    M68kAcceptedCodeRunIR run;
    uint32_t start;
    if (section->certain_code_byte[cursor] == 0U) {
      ++cursor;
      continue;
    }
    start = cursor;
    while ((size_t)cursor < section->certain_code_size && section->certain_code_byte[cursor] != 0U) ++cursor;
    memset(&run, 0, sizeof(run));
    run.start_offset = start;
    run.end_offset = cursor;
    run.end_kind = (size_t)cursor >= section->certain_code_size ?
      M68K_ACCEPTED_CODE_RUN_END_SECTION_BOUNDARY : M68K_ACCEPTED_CODE_RUN_END_ACCEPTED_GAP;
    run.has_origin = (uint8_t)accepted_run_has_origin(section, start, cursor);
    if (classify_run_end_from_cfg(section, start, cursor, &run) < 0) return -1;
    if (section->certain_code_start != NULL) {
      uint32_t offset;
      for (offset = start; offset < cursor && (size_t)offset < section->certain_code_size; ++offset) {
        if (section->certain_code_start[offset] != 0U) ++run.instruction_count;
      }
    }
    if (m68k_ir_section_analysis_append_accepted_code_run(section, &run) != 0) return -1;
    if (!accepted_run_has_executable_origin(section, start, cursor)) {
      if (append_run_diagnostic(section, &run,
          M68K_SOURCE_QUALITY_DIAGNOSTIC_ACCEPTED_CODE_WITHOUT_EXECUTABLE_ORIGIN,
          M68K_SOURCE_QUALITY_DIAGNOSTIC_SEVERITY_ERROR, 1U,
          "accepted code run lacks non-fallthrough executable origin") != 0) {
        return -1;
      }
    } else if (run.end_kind == M68K_ACCEPTED_CODE_RUN_END_ACCEPTED_GAP) {
      if (append_run_diagnostic(section, &run,
          M68K_SOURCE_QUALITY_DIAGNOSTIC_UNTERMINATED_OR_INVALID_CODE_RANGE,
          M68K_SOURCE_QUALITY_DIAGNOSTIC_SEVERITY_WARNING, 0U,
          "accepted code run ends before section boundary without terminal or proven transfer edge") != 0) {
        return -1;
      }
    }
  }
  return 0;
}

int m68k_source_quality_analyze(M68kSourceAnalysisIR *source_analysis) {
  size_t section_index;
  if (source_analysis == NULL) return -1;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    if (append_code_origins_for_section(section) != 0) return -1;
    if (append_accepted_runs_for_section(section) != 0) return -1;
  }
  return 0;
}
