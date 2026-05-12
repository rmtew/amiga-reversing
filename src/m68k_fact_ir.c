#include "m68k_fact_ir.h"

#include <string.h>

static void count_fact(M68kFactIR *ir, uint8_t kind) {
  switch (kind) {
    case M68K_FACT_CODE_START: ++ir->code_start_count; break;
    case M68K_FACT_CODE_ACCEPTED: ++ir->code_accepted_count; break;
    case M68K_FACT_LABEL_REQUIRED: ++ir->label_required_count; break;
    case M68K_FACT_LABEL_CREATED: ++ir->label_created_count; break;
    case M68K_FACT_XREF: ++ir->xref_count; break;
    case M68K_FACT_RELOCATION_REF: ++ir->relocation_ref_count; break;
    case M68K_FACT_RELOCATION_ANCHOR: ++ir->relocation_anchor_count; break;
    case M68K_FACT_RUNTIME_ADDRESS_REF: ++ir->runtime_address_ref_count; break;
    case M68K_FACT_RUNTIME_ADDRESS_RANGE: ++ir->runtime_address_range_count; break;
    case M68K_FACT_DATA_SPAN: ++ir->data_span_count; break;
    case M68K_FACT_VIOLATION: ++ir->violation_count; break;
    default: break;
  }
}

void m68k_fact_ir_init(M68kFactIR *ir) {
  if (ir == NULL) return;
  memset(ir, 0, sizeof(*ir));
  ir->arena = arena_create(4096U);
}

void m68k_fact_ir_destroy(M68kFactIR *ir) {
  Arena *arena;
  if (ir == NULL) return;
  arena = ir->arena;
  memset(ir, 0, sizeof(*ir));
  arena_destroy(arena);
}

int m68k_fact_ir_append(M68kFactIR *ir, const M68kFact *fact) {
  M68kFact *grown;
  size_t next_capacity;
  if (ir == NULL || fact == NULL) return -1;
  if (ir->arena == NULL) return -1;
  if (ir->fact_count == ir->fact_capacity) {
    next_capacity = ir->fact_capacity == 0U ? 64U : ir->fact_capacity * 2U;
    grown = (M68kFact *)arena_realloc_copy(ir->arena, ir->facts,
      ir->fact_capacity * sizeof(*grown), next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    ir->facts = grown;
    ir->fact_capacity = next_capacity;
  }
  ir->facts[ir->fact_count++] = *fact;
  count_fact(ir, fact->kind);
  return 0;
}

int m68k_fact_ir_require_label(M68kFactIR *ir, size_t section_index, uint32_t offset, uint8_t confidence) {
  M68kFact fact;
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_LABEL_REQUIRED;
  fact.confidence = confidence;
  fact.section_index = section_index;
  fact.offset = offset;
  return m68k_fact_ir_append(ir, &fact);
}

int m68k_fact_ir_create_label(M68kFactIR *ir, size_t section_index, uint32_t offset, uint8_t confidence) {
  M68kFact fact;
  if (m68k_fact_ir_has_label(ir, section_index, offset)) return 0;
  memset(&fact, 0, sizeof(fact));
  fact.kind = M68K_FACT_LABEL_CREATED;
  fact.confidence = confidence;
  fact.section_index = section_index;
  fact.offset = offset;
  return m68k_fact_ir_append(ir, &fact);
}

int m68k_fact_ir_has_label(const M68kFactIR *ir, size_t section_index, uint32_t offset) {
  size_t index;
  if (ir == NULL) return 0;
  for (index = 0U; index < ir->fact_count; ++index) {
    const M68kFact *fact = &ir->facts[index];
    if (fact->kind == M68K_FACT_LABEL_CREATED && fact->section_index == section_index && fact->offset == offset)
      return 1;
  }
  return 0;
}
