/* Internal object conversion implementation for platform_file_lib. */
#include "platform_file_internal.h"

int populate_source_ir_from_object(const M68kBackend *backend, const M68kObject *object,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy, M68kSourceFileIR *out_source_file,
    char *error_buf, size_t error_buf_size) {
  M68kAnalysisFindings findings;
  Arena *scratch_arena;
  ArenaMark scratch_mark;
  size_t section_index;
  m68k_analysis_findings_init(&findings);
  if (m68k_ir_source_file_create(out_source_file) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, "out of memory");
    return -1;
  }
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
    m68k_platform_set_error(error_buf, error_buf_size, "failed creating source scratch arena");
    m68k_ir_source_file_destroy(out_source_file);
    return -1;
  }
  scratch_mark = arena_mark(scratch_arena);
  for (section_index = 0; section_index < object->section_count; ++section_index) {
    M68kSectionIR section_ir;
    M68kSectionAnalysisIR section_analysis;
    int append_result;
    arena_rewind(scratch_arena, scratch_mark);
    if (build_section_analysis(object, section_index, &object->sections[section_index], scratch_arena, analysis_policy,
          &findings, &section_analysis, error_buf, error_buf_size) != 0 ||
        build_section_ir(object, &object->sections[section_index], &section_analysis, analysis_policy, &findings,
          policy, &section_ir, error_buf, error_buf_size) != 0) {
      if (error_buf != NULL && error_buf_size != 0U && error_buf[0] == '\0')
        m68k_platform_set_error(error_buf, error_buf_size, "failed building source ir");
      m68k_ir_section_analysis_destroy(&section_analysis);
      m68k_ir_source_file_destroy(out_source_file);
      arena_destroy(scratch_arena);
      return -1;
    }
    append_result = m68k_ir_source_file_append_section(out_source_file, &section_ir);
    m68k_ir_section_destroy(&section_ir);
    if (append_result != 0) {
      m68k_platform_set_error(error_buf, error_buf_size, "failed building source ir");
      m68k_ir_section_analysis_destroy(&section_analysis);
      m68k_ir_source_file_destroy(out_source_file);
      arena_destroy(scratch_arena);
      return -1;
    }
    m68k_ir_section_analysis_destroy(&section_analysis);
  }
  arena_destroy(scratch_arena);
  if (error_buf != NULL && error_buf_size != 0U) error_buf[0] = '\0';
  return 0;
}

int populate_source_analysis_from_object(const M68kObject *object, const M68kAnalysisPolicy *analysis_policy,
    M68kSourceAnalysisIR *out_source_analysis, char *error_buf, size_t error_buf_size) {
  Arena *scratch_arena;
  ArenaMark scratch_mark;
  size_t section_index;
  if (m68k_ir_source_analysis_create(out_source_analysis) != 0) {
    m68k_platform_set_error(error_buf, error_buf_size, "out of memory");
    return -1;
  }
  out_source_analysis->policy = *analysis_policy;
  out_source_analysis->file_kind = object->platform_file_kind;
  m68k_analysis_findings_init(&out_source_analysis->findings);
  scratch_arena = arena_create(65536U);
  if (scratch_arena == NULL) {
    m68k_platform_set_error(error_buf, error_buf_size, "failed creating analysis scratch arena");
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
          &scratch_findings, &section_analysis, error_buf, error_buf_size) != 0 ||
        finalize_section_analysis(&object->sections[section_index], analysis_policy, &section_analysis,
          &section_findings) != 0 ||
        m68k_ir_source_analysis_append_section(out_source_analysis, &section_analysis) != 0) {
      if (error_buf != NULL && error_buf_size != 0U && error_buf[0] == '\0')
        m68k_platform_set_error(error_buf, error_buf_size, "failed building cfg analysis");
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
  if (error_buf != NULL && error_buf_size != 0U) error_buf[0] = '\0';
  return 0;
}
