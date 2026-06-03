#ifndef M68K_SOURCE_QUALITY_H
#define M68K_SOURCE_QUALITY_H

#include "m68k_decode_ir.h"
#include "m68k_fact_ir.h"
#include "m68k_ir.h"

typedef struct M68kSourceQualityHardwareBaseSeed {
  size_t section_index;
  uint32_t offset;
  uint8_t reg_index;
  uint8_t conflicted;
  uint16_t hardware_base_id;
} M68kSourceQualityHardwareBaseSeed;

int m68k_source_quality_analyze(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, const M68kFactIR *facts, uint8_t *const *accepted_start,
    uint8_t *const *accepted_bytes);
int m68k_source_quality_analyze_with_policy(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, const M68kFactIR *facts, uint8_t *const *accepted_start,
    uint8_t *const *accepted_bytes, const M68kAnalysisPolicy *policy);
int m68k_source_quality_analyze_with_policy_and_hardware_base_seeds(M68kSourceAnalysisIR *source_analysis,
    const M68kDecodeIR *decode, const M68kFactIR *facts, uint8_t *const *accepted_start,
    uint8_t *const *accepted_bytes, const M68kAnalysisPolicy *policy,
    const M68kSourceQualityHardwareBaseSeed *hardware_base_seeds, size_t hardware_base_seed_count);
int m68k_source_quality_analyze_rendered_symbol_accesses(M68kSourceAnalysisIR *source_analysis,
    const M68kRenderEvidenceIR *render_evidence);

#endif
