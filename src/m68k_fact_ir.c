#include "m68k_fact_ir.h"

#include <string.h>

static void count_fact(M68kFactIR *ir, uint8_t kind) {
  switch (kind) {
    case M68K_FACT_CODE_START: ++ir->code_start_count; break;
    case M68K_FACT_CODE_ACCEPTED: ++ir->code_accepted_count; break;
    case M68K_FACT_XREF: ++ir->xref_count; break;
    case M68K_FACT_RELOCATION_REF: ++ir->relocation_ref_count; break;
    case M68K_FACT_RELOCATION_ANCHOR: ++ir->relocation_anchor_count; break;
    case M68K_FACT_RUNTIME_ADDRESS_REF: ++ir->runtime_address_ref_count; break;
    case M68K_FACT_RUNTIME_ADDRESS_RANGE: ++ir->runtime_address_range_count; break;
    case M68K_FACT_PLATFORM_MEDIA_TRANSFER: ++ir->platform_media_transfer_count; break;
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

int m68k_fact_ir_append_label_request(M68kFactIR *ir, size_t section_index, uint32_t offset, uint8_t confidence) {
  M68kLabelRequest *grown;
  size_t next_capacity;
  if (ir == NULL || ir->arena == NULL) return -1;
  if (ir->label_request_count == ir->label_request_capacity) {
    next_capacity = ir->label_request_capacity == 0U ? 64U : ir->label_request_capacity * 2U;
    grown = (M68kLabelRequest *)arena_realloc_copy(ir->arena, ir->label_requests,
      ir->label_request_capacity * sizeof(*grown), next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    ir->label_requests = grown;
    ir->label_request_capacity = next_capacity;
  }
  ir->label_requests[ir->label_request_count].section_index = section_index;
  ir->label_requests[ir->label_request_count].offset = offset;
  ir->label_requests[ir->label_request_count].confidence = confidence;
  ++ir->label_request_count;
  return 0;
}

int m68k_fact_ir_append_relative_dispatch(M68kFactIR *ir, const M68kRelativeDispatchFact *fact) {
  if (ir == NULL || ir->arena == NULL || fact == NULL || fact->entry_size != 2U ||
      fact->table_size < 4U || (fact->table_size & 1U) != 0U) return -1;
  for (size_t i = 0U; i < ir->relative_dispatch_count; ++i) {
    const M68kRelativeDispatchFact *old = &ir->relative_dispatches[i];
    if (old->table_section_index == fact->table_section_index && old->table_offset == fact->table_offset &&
        old->table_size == fact->table_size && old->base_section_index == fact->base_section_index &&
        old->base_offset == fact->base_offset && old->consumer_section_index == fact->consumer_section_index &&
        old->consumer_offset == fact->consumer_offset && old->has_producer == fact->has_producer &&
        (!fact->has_producer || (old->producer_section_index == fact->producer_section_index &&
          old->producer_offset == fact->producer_offset &&
          old->producer_operand_index == fact->producer_operand_index))) return 0;
  }
  if (ir->relative_dispatch_count == ir->relative_dispatch_capacity) {
    if (ir->relative_dispatch_capacity > SIZE_MAX / 2U / sizeof(M68kRelativeDispatchFact)) return -1;
    size_t capacity = ir->relative_dispatch_capacity ? ir->relative_dispatch_capacity * 2U : 16U;
    M68kRelativeDispatchFact *grown = (M68kRelativeDispatchFact *)arena_realloc_copy(ir->arena,
      ir->relative_dispatches, ir->relative_dispatch_count * sizeof(*grown), capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    ir->relative_dispatches = grown;
    ir->relative_dispatch_capacity = capacity;
  }
  ir->relative_dispatches[ir->relative_dispatch_count++] = *fact;
  return 0;
}
