#ifndef PLATFORM_FILE_INTERNAL_H
#define PLATFORM_FILE_INTERNAL_H

#include "platform_file_lib.h"
#include "json_builder.h"
#include "m68k_assembler.h"
#include "m68k_backend.h"
#include "m68k_instruction_spec.h"
#include "m68k_ir_codec.h"
#include "m68k_object.h"
#include "m68k_parse_util.h"
#include "m68k_plain_parse.h"
#include "m68k_simulator.h"
#include "m68k_source_ir_render.h"
#include "platform_atari_st.h"
#include "platform_common.h"
#include "util_arena.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int build_section_analysis(const M68kObject *object, size_t section_index, const M68kSection *section,
    Arena *scratch_arena,
    const M68kAnalysisPolicy *analysis_policy, M68kAnalysisFindings *findings, M68kSectionAnalysisIR *out_analysis,
    char *out_error, size_t out_error_size);
int build_section_ir(const M68kObject *object, const M68kSection *section, M68kSectionAnalysisIR *section_analysis,
    const M68kAnalysisPolicy *analysis_policy, M68kAnalysisFindings *findings, const M68kRenderPolicy *policy,
    M68kSectionIR *out_section_ir, char *out_error, size_t out_error_size);
int finalize_section_analysis(const M68kSection *section, const M68kAnalysisPolicy *analysis_policy,
    M68kSectionAnalysisIR *section_analysis, M68kAnalysisFindings *out_findings);

int inspect_object_json(const M68kBackend *backend, const M68kObject *object, char **out_json);
int source_analysis_to_json(const M68kSourceAnalysisIR *source_analysis, char **out_json, char *error_buf,
    size_t error_buf_size);
int populate_source_ir_from_object(const M68kBackend *backend, const M68kObject *object,
    const M68kRenderPolicy *policy, const M68kAnalysisPolicy *analysis_policy, M68kSourceFileIR *out_source_file,
    char *error_buf, size_t error_buf_size);
int populate_source_analysis_from_object(const M68kObject *object, const M68kAnalysisPolicy *analysis_policy,
    M68kSourceAnalysisIR *out_source_analysis, char *error_buf, size_t error_buf_size);

#endif
