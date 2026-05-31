/* Append-only fact store for facts_v2 analysis. */
#ifndef M68K_FACT_IR_H
#define M68K_FACT_IR_H

#include <stddef.h>
#include <stdint.h>

#include "util_arena.h"

typedef enum M68kFactKind {
  M68K_FACT_CODE_START = 1,
  M68K_FACT_CODE_ACCEPTED = 2,
  M68K_FACT_LABEL_REQUIRED = 3,
  M68K_FACT_LABEL_CREATED = 4,
  M68K_FACT_XREF = 5,
  M68K_FACT_RELOCATION_REF = 6,
  M68K_FACT_DATA_SPAN = 7,
  M68K_FACT_VIOLATION = 8,
  M68K_FACT_RELOCATION_ANCHOR = 9,
  M68K_FACT_RUNTIME_ADDRESS_REF = 10,
  M68K_FACT_RUNTIME_ADDRESS_RANGE = 11,
  M68K_FACT_PLATFORM_MEDIA_TRANSFER = 12
} M68kFactKind;

typedef enum M68kFactConfidence {
  M68K_FACT_CONFIDENCE_SPECULATIVE = 1,
  M68K_FACT_CONFIDENCE_TOOL_INFERRED = 2,
  M68K_FACT_CONFIDENCE_REQUIRED = 3,
  M68K_FACT_CONFIDENCE_VERIFIED = 4
} M68kFactConfidence;

#define M68K_FACT_RUNTIME_RANGE_KIND_POLICY 1U
#define M68K_FACT_RUNTIME_RANGE_KIND_DISCOVERED_COPY 2U
#define M68K_FACT_RUNTIME_RANGE_KIND_CONFLICTING_DISCOVERED_COPY 3U

typedef enum M68kFactCodeStartReason {
  M68K_FACT_CODE_START_REASON_UNKNOWN = 0,
  M68K_FACT_CODE_START_REASON_SECTION_ENTRY = 1,
  M68K_FACT_CODE_START_REASON_POLICY_ENTRY_OFFSET = 2,
  M68K_FACT_CODE_START_REASON_POLICY_ENTRY_POINT = 3,
  M68K_FACT_CODE_START_REASON_CONTROL_TARGET = 4,
  M68K_FACT_CODE_START_REASON_FALLTHROUGH = 5,
  M68K_FACT_CODE_START_REASON_INLINE_RESUME = 6,
  M68K_FACT_CODE_START_REASON_RUNTIME_VIEW_ENTRY = 7,
  M68K_FACT_CODE_START_REASON_LINKAGE_API_ENTRY = 8,
  M68K_FACT_CODE_START_REASON_PLATFORM_LOADSEG_ENTRY = 9,
  M68K_FACT_CODE_START_REASON_STACK_CONTINUATION = 10,
  M68K_FACT_CODE_START_REASON_BOUNDARY_API_ENTRY = 11
} M68kFactCodeStartReason;

typedef struct M68kFact {
  uint8_t kind;
  uint8_t confidence;
  size_t section_index;
  uint32_t offset;
  uint32_t reason;
  uint32_t code_start_evidence_kind;
  uint8_t has_runtime_address;
  uint8_t has_sink_address;
  uint8_t runtime_kind;
  uint8_t reserved;
  uint32_t runtime_address;
  uint32_t sink_address;
  size_t source_section_index;
  uint32_t source_offset;
  size_t target_section_index;
  uint32_t target_offset;
  int64_t target_addend;
  uint32_t size;
  uint32_t platform_record_kind;
  uint32_t anchor_kind;
} M68kFact;

typedef struct M68kFactIR {
  Arena *arena;
  M68kFact *facts;
  size_t fact_count;
  size_t fact_capacity;
  uint32_t code_start_count;
  uint32_t code_accepted_count;
  uint32_t label_required_count;
  uint32_t label_created_count;
  uint32_t xref_count;
  uint32_t relocation_ref_count;
  uint32_t relocation_anchor_count;
  uint32_t runtime_address_ref_count;
  uint32_t runtime_address_range_count;
  uint32_t platform_media_transfer_count;
  uint32_t data_span_count;
  uint32_t violation_count;
} M68kFactIR;

void m68k_fact_ir_init(M68kFactIR *ir);
void m68k_fact_ir_destroy(M68kFactIR *ir);
int m68k_fact_ir_append(M68kFactIR *ir, const M68kFact *fact);
int m68k_fact_ir_require_label(M68kFactIR *ir, size_t section_index, uint32_t offset, uint8_t confidence);
int m68k_fact_ir_create_label(M68kFactIR *ir, size_t section_index, uint32_t offset, uint8_t confidence);
int m68k_fact_ir_has_label(const M68kFactIR *ir, size_t section_index, uint32_t offset);

#endif
